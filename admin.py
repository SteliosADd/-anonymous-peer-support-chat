"""
Admin / moderator routes.

These power the admin dashboard: view flagged messages, delete messages,
block or mute users, and see basic chat activity stats.

All endpoints require both a valid JWT and `is_admin=True` on the user.
"""
from functools import wraps
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc

from models import db, User, Message

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def admin_required(fn):
    """Decorator: require the JWT user to be an admin."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


@admin_bp.route("/flagged", methods=["GET"])
@admin_required
def list_flagged():
    """All messages flagged by moderation, newest first."""
    msgs = (
        Message.query.filter_by(is_flagged=True)
        .order_by(desc(Message.created_at))
        .limit(200)
        .all()
    )
    return jsonify({"messages": [m.to_dict() for m in msgs]})


@admin_bp.route("/messages/<int:msg_id>", methods=["DELETE"])
@admin_required
def delete_message(msg_id):
    """Soft-delete a message (mark as deleted, hide its content)."""
    msg = Message.query.get_or_404(msg_id)
    msg.is_deleted = True
    db.session.commit()
    return jsonify({"ok": True, "message": msg.to_dict()})


@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    """List all users, with their moderation flags."""
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify({"users": [u.to_dict() for u in users]})


@admin_bp.route("/users/<int:user_id>/block", methods=["POST"])
@admin_required
def toggle_block(user_id):
    """Toggle the block state on a user (blocks login + chat)."""
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        return jsonify({"error": "Cannot block an admin"}), 400
    user.is_blocked = not user.is_blocked
    db.session.commit()
    return jsonify({"ok": True, "user": user.to_dict()})


@admin_bp.route("/users/<int:user_id>/mute", methods=["POST"])
@admin_required
def toggle_mute(user_id):
    """Toggle mute — user can still log in but messages are blocked."""
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        return jsonify({"error": "Cannot mute an admin"}), 400
    user.is_muted = not user.is_muted
    db.session.commit()
    return jsonify({"ok": True, "user": user.to_dict()})


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def stats():
    """High-level chat activity stats for the dashboard."""
    return jsonify({
        "total_users": User.query.count(),
        "online_users": User.query.filter_by(is_online=True).count(),
        "blocked_users": User.query.filter_by(is_blocked=True).count(),
        "muted_users": User.query.filter_by(is_muted=True).count(),
        "total_messages": Message.query.count(),
        "flagged_messages": Message.query.filter_by(is_flagged=True).count(),
        "deleted_messages": Message.query.filter_by(is_deleted=True).count(),
    })
