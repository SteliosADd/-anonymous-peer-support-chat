"""
Database models for the Anonymous Mental Health Support Chat.

We keep models small and focused. Users stay anonymous: only a chosen
username and avatar identify them — no email or real name is stored.
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """An anonymous user account.

    `username` is the only public identifier. `password_hash` is bcrypt'd
    (see auth.py). We track moderation state with `is_blocked` / `is_muted`.
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    # VARCHAR(16) is plenty for any single emoji + variation selectors
    avatar = db.Column(db.String(16), default="🌱", nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_blocked = db.Column(db.Boolean, default=False, nullable=False)
    is_muted = db.Column(db.Boolean, default=False, nullable=False)
    is_online = db.Column(db.Boolean, default=False, nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "avatar": self.avatar,
            "is_admin": self.is_admin,
            "is_blocked": self.is_blocked,
            "is_muted": self.is_muted,
            "is_online": self.is_online,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class MoodEntry(db.Model):
    """One private mood check-in per user per day (1 = very low, 5 = great).

    `day` is the user's local date as YYYY-MM-DD, so "today" matches what
    they see on their own clock. No free text is stored on purpose.
    """
    __tablename__ = "mood_entries"
    __table_args__ = (db.UniqueConstraint("user_id", "day", name="uq_mood_user_day"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    day = db.Column(db.String(10), nullable=False)
    mood = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {"day": self.day, "mood": self.mood}


class Message(db.Model):
    """A one-to-one chat message between two users."""
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    is_flagged = db.Column(db.Boolean, default=False, nullable=False, index=True)
    flag_reason = db.Column(db.String(200), nullable=True)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    # Set when the recipient opens the conversation; drives "Seen" and unread counts.
    read_at = db.Column(db.DateTime, nullable=True)

    sender =db.relationship("User", foreign_keys=[sender_id])
    recipient = db.relationship("User", foreign_keys=[recipient_id])

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_username": self.sender.username if self.sender else None,
            "sender_avatar": self.sender.avatar if self.sender else None,
            "recipient_id": self.recipient_id,
            "recipient_username": self.recipient.username if self.recipient else None,
            "content": "[deleted by moderator]" if self.is_deleted else self.content,
            "is_flagged": self.is_flagged,
            "flag_reason": self.flag_reason,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat(),
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }
