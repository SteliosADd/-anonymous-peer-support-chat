"""
Simple AI-assisted moderation module.

This uses keyword and phrase matching to flag messages that may indicate
self-harm, crisis, or distress. It's intentionally simple and beginner-
friendly — a real production system would use ML models, but for a
university project this clearly demonstrates the concept.

When a message is flagged, the chat UI shows a supportive popup with
crisis hotline info, and the message is logged to the admin dashboard.
"""
import re


# Phrases that suggest crisis-level risk — these trigger a supportive popup
# and admin flagging. Lowercased; we match as whole words / phrases.
CRISIS_KEYWORDS = [
    "suicide",
    "kill myself",
    "kill me",
    "end my life",
    "want to die",
    "hurt myself",
    "harm myself",
    "self harm",
    "self-harm",
    "cutting myself",
    "no reason to live",
    "better off dead",
]

# Lower-severity distress signals — flagged for moderation review but
# we don't show the crisis popup for these alone.
DISTRESS_KEYWORDS = [
    "depressed",
    "depression",
    "hopeless",
    "worthless",
    "can't go on",
    "give up",
    "alone",
    "anxious",
    "anxiety attack",
    "panic attack",
]


def _matches_any(text: str, keywords: list) -> list:
    """Return the list of keywords found in `text` (case-insensitive)."""
    lowered = text.lower()
    hits = []
    for kw in keywords:
        # \b only works for word boundaries; for multi-word phrases just substring-match
        if " " in kw or "-" in kw:
            if kw in lowered:
                hits.append(kw)
        else:
            if re.search(rf"\b{re.escape(kw)}\b", lowered):
                hits.append(kw)
    return hits


def analyze_message(content: str) -> dict:
    """Analyze a message and return moderation info.

    Returns a dict:
        {
            "flagged": bool,         — should this go to admin dashboard?
            "crisis": bool,          — show the supportive crisis popup?
            "matched": [str, ...],   — the keywords that triggered flags
            "reason": str | None,    — short reason text
        }
    """
    crisis_hits = _matches_any(content, CRISIS_KEYWORDS)
    distress_hits = _matches_any(content, DISTRESS_KEYWORDS)

    flagged = bool(crisis_hits or distress_hits)
    crisis = bool(crisis_hits)

    reason = None
    if crisis_hits:
        reason = f"Crisis keywords: {', '.join(crisis_hits)}"
    elif distress_hits:
        reason = f"Distress keywords: {', '.join(distress_hits)}"

    return {
        "flagged": flagged,
        "crisis": crisis,
        "matched": crisis_hits + distress_hits,
        "reason": reason,
    }
