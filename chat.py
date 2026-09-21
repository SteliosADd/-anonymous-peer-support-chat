"""
Chat-related HTTP routes.

Real-time messaging itself goes through Socket.IO (see sockets.py / app.py).
These routes serve helper data: lists of users, message history, etc.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_, and_, desc, func

from models import db, User, Message

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


@chat_bp.route("/users", methods=["GET"])
@jwt_required()
def list_users():
    """Return all users other than the current one — used to start chats."""
    me_id = int(get_jwt_identity())
    users = User.query.filter(User.id != me_id, User.is_blocked == False).all()
    # Sort: online first, then by username
    users.sort(key=lambda u: (not u.is_online, u.username.lower()))

    # Unread message count per sender, for the badges in the sidebar.
    unread = dict(
        db.session.query(Message.sender_id, func.count(Message.id))
        .filter(Message.recipient_id == me_id, Message.read_at.is_(None))
        .group_by(Message.sender_id)
        .all()
    )
    result = []
    for u in users:
        d = u.to_dict()
        d["unread"] = unread.get(u.id, 0)
        result.append(d)
    return jsonify({"users": result})


@chat_bp.route("/history/<int:other_id>", methods=["GET"])
@jwt_required()
def conversation_history(other_id):
    """Return the message history between current user and `other_id`."""
    me_id = int(get_jwt_identity())

    messages = (
        Message.query.filter(
            or_(
                and_(Message.sender_id == me_id, Message.recipient_id == other_id),
                and_(Message.sender_id == other_id, Message.recipient_id == me_id),
            )
        )
        .order_by(Message.created_at.asc())
        .limit(200)
        .all()
    )

    other = User.query.get_or_404(other_id)
    if other.is_blocked:
        return jsonify({"error": "This user is no longer available"}), 403
    return jsonify({
        "other_user": other.to_dict(),
        "messages": [m.to_dict() for m in messages],
    })
