"""
Mood check-in routes.

A user records one mood (1-5) per day and reads back their recent history.
Entries are private: nobody but the owner, not even admins, can read them
through the API.
"""
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from models import db, MoodEntry

mood_bp = Blueprint("mood", __name__, url_prefix="/api/mood")

HISTORY_DAYS = 30


@mood_bp.route("", methods=["GET"])
@jwt_required()
def list_moods():
    """The current user's entries for the last 30 days, oldest first."""
    me_id = int(get_jwt_identity())
    since = (date.today() - timedelta(days=HISTORY_DAYS + 1)).isoformat()
    entries = (
        MoodEntry.query.filter(MoodEntry.user_id == me_id, MoodEntry.day >= since)
        .order_by(MoodEntry.day.asc())
        .all()
    )
    return jsonify({"entries": [e.to_dict() for e in entries]})


@mood_bp.route("", methods=["POST"])
@jwt_required()
def save_mood():
    """Create or replace today's entry. Body: {"mood": 1-5, "day": "YYYY-MM-DD"}."""
    me_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    mood = data.get("mood")
    if not isinstance(mood, int) or isinstance(mood, bool) or not 1 <= mood <= 5:
        return jsonify({"error": "mood must be a whole number from 1 to 5"}), 400

    # The client sends its own local date. Accept it only if it is within a
    # day of the server's UTC date, so nobody can backfill or pre-fill.
    try:
        day = datetime.strptime(str(data.get("day", "")), "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "day must look like YYYY-MM-DD"}), 400
    if abs((day - datetime.utcnow().date()).days) > 1:
        return jsonify({"error": "day is out of range"}), 400

    day_str = day.isoformat()
    entry = MoodEntry.query.filter_by(user_id=me_id, day=day_str).first()
    if entry:
        entry.mood = mood
        entry.updated_at = datetime.utcnow()
    else:
        entry = MoodEntry(user_id=me_id, day=day_str, mood=mood)
        db.session.add(entry)
    db.session.commit()
    return jsonify({"ok": True, "entry": entry.to_dict()})
