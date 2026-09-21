"""Tests for chat safety features: reports, read receipts, blocked users."""
import pytest

from app import app as flask_app, socketio
from config import Config
from extensions import limiter
from models import db, Message


@pytest.fixture(autouse=True)
def _no_rate_limit():
    """These tests register several users each; auth is limited to 10/min."""
    limiter.enabled = False
    yield
    limiter.enabled = True


def register(client):
    reg = client.post(
        "/api/auth/register", json={"password": "testpass123", "avatar": "🌱"}
    ).get_json()
    return reg["token"], reg["user"]["id"]


def admin_token(client):
    return client.post(
        "/api/auth/login",
        json={
            "username": Config.DEFAULT_ADMIN_USERNAME,
            "password": Config.DEFAULT_ADMIN_PASSWORD,
        },
    ).get_json()["token"]


def sio(token):
    return socketio.test_client(flask_app, auth={"token": token})


def send(sender_sio, recipient_id, text):
    sender_sio.emit("send_message", {"recipient_id": recipient_id, "content": text})


def test_recipient_can_report_message_and_admin_is_notified(client):
    a_tok, a_id = register(client)
    b_tok, b_id = register(client)
    admin = sio(admin_token(client))
    a, b = sio(a_tok), sio(b_tok)

    send(a, b_id, "you are worthless")
    msg_id = b.get_received()[-1]["args"][0]["id"]
    admin.get_received()  # discard earlier events

    ack = b.emit("report_message", {"message_id": msg_id}, callback=True)
    assert ack == {"ok": True}

    with flask_app.app_context():
        msg = db.session.get(Message, msg_id)
        assert msg.is_flagged
        assert "Reported by user" in msg.flag_reason
    assert any(e["name"] == "new_flag" for e in admin.get_received())


def test_sender_cannot_report_own_message(client):
    a_tok, _ = register(client)
    _, b_id = register(client)
    a = sio(a_tok)

    send(a, b_id, "hello")
    msg_id = a.get_received()[-1]["args"][0]["id"]
    ack = a.emit("report_message", {"message_id": msg_id}, callback=True)
    assert ack["ok"] is False


def test_mark_read_sets_read_at_and_notifies_sender(client):
    a_tok, a_id = register(client)
    b_tok, b_id = register(client)
    a, b = sio(a_tok), sio(b_tok)

    send(a, b_id, "hi")
    msg_id = a.get_received()[-1]["args"][0]["id"]

    b.emit("mark_read", {"other_id": a_id})

    with flask_app.app_context():
        assert db.session.get(Message, msg_id).read_at is not None
    assert any(e["name"] == "messages_read" for e in a.get_received())


def test_users_endpoint_reports_unread_counts(client):
    a_tok, a_id = register(client)
    b_tok, b_id = register(client)
    a = sio(a_tok)

    send(a, b_id, "one")
    send(a, b_id, "two")

    users = client.get(
        "/api/chat/users", headers={"Authorization": f"Bearer {b_tok}"}
    ).get_json()["users"]
    assert next(u for u in users if u["id"] == a_id)["unread"] == 2


def test_cannot_message_or_read_history_of_blocked_user(client):
    a_tok, _ = register(client)
    _, b_id = register(client)
    a = sio(a_tok)

    client.post(
        f"/api/admin/users/{b_id}/block",
        headers={"Authorization": f"Bearer {admin_token(client)}"},
    )

    send(a, b_id, "hello?")
    assert any(e["name"] == "error_message" for e in a.get_received())

    res = client.get(
        f"/api/chat/history/{b_id}", headers={"Authorization": f"Bearer {a_tok}"}
    )
    assert res.status_code == 403
