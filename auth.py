"""
Authentication routes — register, login, and current-user info.

Uses JWT for stateless auth. Passwords are hashed with bcrypt before
storage; we never store anything that could deanonymize a user.
"""
import random
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from flask_bcrypt import Bcrypt

from models import db, User

bcrypt = Bcrypt()
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# Calming nature-themed avatar emojis users can pick from
AVATARS = ["🌱", "🌸", "🌿", "🌊", "☁️", "🌙", "✨", "🍃", "🌻", "🦋", "🐬", "🕊️"]


@auth_bp.route("/register", methods=["POST"])
def register():
    """Create a new anonymous account."""
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    avatar = data.get("avatar") or random.choice(AVATARS)

    # Basic validation
    if len(username) < 3 or len(username) > 30:
        return jsonify({"error": "Username must be 3-30 characters"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if avatar not in AVATARS:
        avatar = random.choice(AVATARS)

    # Username uniqueness
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken"}), 409

    # Hash the password — never store it in plain text
    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, password_hash=pw_hash, avatar=avatar)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in to an existing anonymous account."""
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401

    if user.is_blocked:
        return jsonify({"error": "This account has been blocked by moderators"}), 403

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()})


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    """Return the currently logged-in user's info."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()})


@auth_bp.route("/avatars", methods=["GET"])
def avatars():
    """Return the list of available avatars for the registration UI."""
    return jsonify({"avatars": AVATARS})
