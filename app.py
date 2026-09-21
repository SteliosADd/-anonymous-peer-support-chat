"""
Anonymous Mental Health Support Chat

Main Flask application: wires up the database, JWT auth, REST blueprints,
Socket.IO real-time chat, and serves the frontend templates.

Run with:  python app.py
"""
import sys
from datetime import datetime, timezone

# Reconfigure stdout/stderr to UTF-8 on Windows so emoji in print() don't crash.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
from flask_cors import CORS
from flask_jwt_extended import JWTManager, decode_token
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError

from config import Config
from extensions import limiter
from models import db, User, Message
from auth import auth_bp, bcrypt
from chat import chat_bp
from admin import admin_bp
from mood import mood_bp
from moderation import analyze_message


def _ensure_read_at_column():
    """Add messages.read_at to databases created before read receipts existed.

    create_all() only creates missing tables, never missing columns.
    """
    cols = [c["name"] for c in inspect(db.engine).get_columns("messages")]
    if "read_at" not in cols:
        db.session.execute(text("ALTER TABLE messages ADD COLUMN read_at DATETIME NULL"))
        db.session.commit()


def _init_database(app):
    """Create tables and seed the default admin.

    Wraps the call so we can show a friendly error if MySQL isn't
    reachable, instead of a stack trace.
    """
    try:
        with app.app_context():
            db.create_all()
            _ensure_read_at_column()
            # Reset stale online flags left over from a previous run.
            User.query.filter_by(is_online=True).update({"is_online": False})
            db.session.commit()
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
    limiter.init_app(app)

    # Register API blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(mood_bp)

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

    @app.route("/mood")
    def mood_page():
        return render_template("mood.html")

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
# Count of active sockets per user — so closing one tab of many doesn't mark the user offline.
_user_socket_count = {}


def _auth_socket(token):
    """Decode a JWT from the Socket.IO connect query and return the User."""
    if not token:
        return None
    try:
        decoded = decode_token(token)
        uid = int(decoded["sub"])
        return db.session.get(User, uid)
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
    _user_socket_count[user.id] = _user_socket_count.get(user.id, 0) + 1
    join_room(f"user_{user.id}")

    # Only broadcast online when this is the user's FIRST socket (first tab/device).
    if _user_socket_count[user.id] == 1:
        user.is_online = True
        user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        emit("user_status", {"user_id": user.id, "is_online": True}, broadcast=True)


@socketio.on("disconnect")
def on_disconnect():
    uid = _sid_to_user.pop(request.sid, None)
    if uid is None:
        return
    _user_socket_count[uid] = max(0, _user_socket_count.get(uid, 1) - 1)
    # Only mark offline when ALL of the user's tabs/devices have disconnected.
    if _user_socket_count[uid] == 0:
        user = db.session.get(User, uid)
        if user:
            user.is_online = False
            user.last_seen = datetime.now(timezone.utc)
            db.session.commit()
            emit("user_status", {"user_id": user.id, "is_online": False}, broadcast=True)


@socketio.on("send_message")
def on_send_message(data):
    """Handle an outgoing message from a client."""
    sender_id = _sid_to_user.get(request.sid)
    if not sender_id:
        return

    sender = db.session.get(User, sender_id)
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

    recipient = db.session.get(User, recipient_id)
    if not recipient or recipient.id == sender_id:
        return
    if recipient.is_blocked:
        emit("error_message", {"error": "This user is no longer available"})
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


@socketio.on("report_message")
def on_report_message(data):
    """A user reports a message they received. It goes into the same
    flagged queue moderators already review, and admins get a live ping.

    Returns an ack dict so the client can show a confirmation.
    """
    reporter_id = _sid_to_user.get(request.sid)
    msg_id = (data or {}).get("message_id")
    if not reporter_id or not msg_id:
        return {"ok": False, "error": "Invalid request"}

    msg = db.session.get(Message, msg_id)
    # Only the recipient can report; you can't report your own messages
    # or conversations you aren't part of.
    if not msg or msg.recipient_id != reporter_id:
        return {"ok": False, "error": "Message not found"}

    tag = "Reported by user"
    if not msg.is_flagged:
        msg.flag_reason = tag
    elif tag not in (msg.flag_reason or ""):
        msg.flag_reason = f"{msg.flag_reason} · {tag}"[:200]
    msg.is_flagged = True
    db.session.commit()

    payload = msg.to_dict()
    for admin_user in User.query.filter_by(is_admin=True).all():
        emit("new_flag", payload, room=f"user_{admin_user.id}")
    return {"ok": True}


@socketio.on("mark_read")
def on_mark_read(data):
    """The user opened a conversation: stamp its unread messages as read
    and tell the sender so their UI can show "Seen"."""
    reader_id = _sid_to_user.get(request.sid)
    other_id = (data or {}).get("other_id")
    if not reader_id or not other_id:
        return
    now = datetime.utcnow()
    unread = Message.query.filter_by(
        sender_id=other_id, recipient_id=reader_id, read_at=None
    ).all()
    if not unread:
        return
    for m in unread:
        m.read_at = now
    db.session.commit()
    emit(
        "messages_read",
        {"reader_id": reader_id, "read_at": now.isoformat()},
        room=f"user_{other_id}",
    )


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
