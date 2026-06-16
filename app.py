"""
Anonymous Mental Health Support Chat

Main Flask application: wires up the database, JWT auth, REST blueprints,
Socket.IO real-time chat, and serves the frontend templates.

Run with:  python app.py
"""
import sys
from datetime import datetime

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_cors import CORS
from flask_jwt_extended import JWTManager, decode_token
from sqlalchemy.exc import OperationalError

from config import Config
from models import db, User, Message
from auth import auth_bp, bcrypt
from chat import chat_bp
from admin import admin_bp
from moderation import analyze_message


def _init_database(app):
    """Create tables and seed the default admin.

    Wraps the call so we can show a friendly error if MySQL isn't
    reachable, instead of a stack trace.
    """
    try:
        with app.app_context():
            db.create_all()
            existing = User.query.filter_by(
                username=Config.DEFAULT_ADMIN_USERNAME
            ).first()
            if not existing:
                admin_user = User(
                    username=Config.DEFAULT_ADMIN_USERNAME,
                    password_hash=bcrypt.generate_password_hash(
                        Config.DEFAULT_ADMIN_PASSWORD
                    ).decode("utf-8"),
                    avatar="🛡️",
                    is_admin=True,
                )
                db.session.add(admin_user)
                db.session.commit()
    except OperationalError as e:
        print("\n❌ Could not connect to the database.", file=sys.stderr)
        print(f"   URI: {Config.SQLALCHEMY_DATABASE_URI}", file=sys.stderr)
        print(f"   Error: {e.orig}\n", file=sys.stderr)
        print("Tips:", file=sys.stderr)
        print(" • Default is SQLite — just run `python app.py`, no setup needed.", file=sys.stderr)
        print(" • If you set USE_MYSQL=1, make sure MySQL is running:", file=sys.stderr)
        print("     sudo service mysql start", file=sys.stderr)
        print(" • And that you've created the database + user:", file=sys.stderr)
        print("     mysql -u root -p < schema.sql", file=sys.stderr)
        print(" • Check your .env file (copy from .env.example).\n", file=sys.stderr)
        raise SystemExit(1)


def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    JWTManager(app)
    CORS(app)

    # Register API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)

    # Frontend page routes — Flask just renders the templates,
    # all data flows through the API + Socket.IO.
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/chat")
    def chat_page():
        return render_template("chat.html")

    @app.route("/resources")
    def resources_page():
        return render_template("resources.html")

    @app.route("/admin")
    def admin_page():
        return render_template("admin.html")

    _init_database(app)
    return app


app = create_app()
# `threading` async mode is the most portable: no eventlet/gevent native
# build needed, works the same on Linux / macOS / Windows.
socketio = SocketIO(
    app,
    cors_allowed_origins=Config.CORS_ALLOWED_ORIGINS,
    async_mode="threading",
)


# ---------------------------------------------------------------------------
# Socket.IO real-time chat
# ---------------------------------------------------------------------------
#
# Each connected user joins a personal room named "user_<id>". To send
# a direct message we emit into the recipient's room. This avoids
# tracking socket-id-to-user mappings manually.
# ---------------------------------------------------------------------------

# Map socket session id -> user id, so we know who disconnected.
_sid_to_user = {}


def _auth_socket(token):
    """Decode a JWT from the Socket.IO connect query and return the User."""
    if not token:
        return None
    try:
        decoded = decode_token(token)
        uid = int(decoded["sub"])
        return User.query.get(uid)
    except Exception:
        return None


@socketio.on("connect")
def on_connect(auth):
    """Authenticate the Socket.IO connection using the JWT token."""
    token = (auth or {}).get("token") if isinstance(auth, dict) else None
    if not token:
        token = request.args.get("token")

    user = _auth_socket(token)
    if not user or user.is_blocked:
        disconnect()
        return False

    _sid_to_user[request.sid] = user.id
    join_room(f"user_{user.id}")

    # Mark online and notify everyone — UI can update the user list.
    user.is_online = True
    user.last_seen = datetime.utcnow()
    db.session.commit()
    emit("user_status", {"user_id": user.id, "is_online": True}, broadcast=True)


@socketio.on("disconnect")
def on_disconnect():
    uid = _sid_to_user.pop(request.sid, None)
    if uid is None:
        return
    user = User.query.get(uid)
    if user:
        user.is_online = False
        user.last_seen = datetime.utcnow()
        db.session.commit()
        emit("user_status", {"user_id": user.id, "is_online": False}, broadcast=True)


@socketio.on("send_message")
def on_send_message(data):
    """Handle an outgoing message from a client."""
    sender_id = _sid_to_user.get(request.sid)
    if not sender_id:
        return

    sender = User.query.get(sender_id)
    if not sender or sender.is_blocked:
        emit("error_message", {"error": "You are not allowed to send messages"})
        return
    if sender.is_muted:
        emit("error_message", {"error": "You are currently muted by moderators"})
        return

    recipient_id = data.get("recipient_id")
    content = (data.get("content") or "").strip()

    if not recipient_id or not content:
        return
    if len(content) > 2000:
        emit("error_message", {"error": "Message is too long (max 2000 chars)"})
        return

    recipient = User.query.get(recipient_id)
    if not recipient:
        return

    # Run the message through the moderation module.
    mod = analyze_message(content)

    msg = Message(
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=content,
        is_flagged=mod["flagged"],
        flag_reason=mod["reason"],
    )
    db.session.add(msg)
    db.session.commit()

    payload = msg.to_dict()
    # Send to both sender and recipient rooms so all open tabs sync.
    emit("new_message", payload, room=f"user_{recipient_id}")
    emit("new_message", payload, room=f"user_{sender_id}")

    # If a crisis keyword was hit, the sender's UI should show the
    # supportive popup with crisis hotline information.
    if mod["crisis"]:
        emit(
            "crisis_warning",
            {"message_id": msg.id, "matched": mod["matched"]},
            room=f"user_{sender_id}",
        )

    # If flagged at all, push a real-time notification to all admins
    # so the dashboard updates without a manual refresh.
    if mod["flagged"]:
        for admin_user in User.query.filter_by(is_admin=True).all():
            emit("new_flag", payload, room=f"user_{admin_user.id}")


@socketio.on("typing")
def on_typing(data):
    """Forward typing indicators to the recipient."""
    sender_id = _sid_to_user.get(request.sid)
    recipient_id = data.get("recipient_id")
    if not sender_id or not recipient_id:
        return
    emit(
        "typing",
        {"user_id": sender_id, "is_typing": bool(data.get("is_typing"))},
        room=f"user_{recipient_id}",
    )


if __name__ == "__main__":
    import os
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f"\n🌿 Anonymous Mental Health Support Chat starting on http://{host}:{port}")
    print(f"   Database: {Config.SQLALCHEMY_DATABASE_URI.split('@')[-1] if '@' in Config.SQLALCHEMY_DATABASE_URI else Config.SQLALCHEMY_DATABASE_URI}")
    print(f"   Default admin: {Config.DEFAULT_ADMIN_USERNAME} / {Config.DEFAULT_ADMIN_PASSWORD}\n")
    # `allow_unsafe_werkzeug` lets us use the dev server with threading
    # mode in newer Werkzeug versions.
    socketio.run(
        app,
        host=host,
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True,
    )
