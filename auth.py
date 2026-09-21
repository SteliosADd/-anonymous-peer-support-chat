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

from extensions import limiter
from models import db, User

bcrypt = Bcrypt()
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# Calming nature-themed avatar emojis users can pick from
AVATARS = ["🌱", "🌸", "🌿", "🌊", "☁️", "🌙", "✨", "🍃", "🌻", "🦋", "🐬", "🕊️"]

# Word banks for auto-generated anonymous usernames — no one types a name
# that could identify them, so we hand out a calming nature-themed handle.
_ADJECTIVES = [
    "quiet", "gentle", "calm", "soft", "still", "brave", "kind", "warm",
    "hopeful", "peaceful", "steady", "wandering", "silent", "bright", "misty",
]
_NOUNS = [
    "river", "forest", "meadow", "harbor", "willow", "cloud", "breeze",
    "ember", "shore", "valley", "moss", "lantern", "petal", "tide", "grove",
]


def _generate_username():
    """Pick a random adjective_noun#### handle, retrying on collision."""
    for _ in range(50):
        candidate = f"{random.choice(_ADJECTIVES)}_{random.choice(_NOUNS)}{random.randint(100, 9999)}"
        if not User.query.filter_by(username=candidate).first():
            return candidate
    # Astronomically unlikely, but fall back to a wider number range.
    return f"{random.choice(_ADJECTIVES)}_{random.choice(_NOUNS)}{random.randint(10000, 999999)}"


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per minute")
def register():
    """Create a new anonymous account.

    The username is never typed by the user — it's auto-generated
    server-side (see `_generate_username`) so no one can accidentally
    pick something that identifies them.
    """
    data = request.get_json() or {}
    password = data.get("password") or ""
    avatar = data.get("avatar") or random.choice(AVATARS)

    # Basic validation
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if avatar not in AVATARS:
        avatar = random.choice(AVATARS)

    username = _generate_username()

    # Hash the password — never store it in plain text
    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(username=username, password_hash=pw_hash, avatar=avatar)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.route("/suggest-username", methods=["GET"])
@limiter.limit("30 per minute")
def suggest_username():
    """Return a freshly generated anonymous handle for the registration UI preview."""
    return jsonify({"username": _generate_username()})


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
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
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()})


@auth_bp.route("/avatars", methods=["GET"])
def avatars():
    """Return the list of available avatars for the registration UI."""
    return jsonify({"avatars": AVATARS})
