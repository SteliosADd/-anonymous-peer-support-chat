from datetime import datetime, timedelta

import pytest

from extensions import limiter


@pytest.fixture(autouse=True)
def _no_rate_limit():
    limiter.enabled = False
    yield
    limiter.enabled = True


def register(client):
    return client.post(
        "/api/auth/register", json={"password": "testpass123", "avatar": "🌱"}
    ).get_json()["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def today():
    return datetime.utcnow().date().isoformat()


def test_mood_requires_login(client):
    assert client.get("/api/mood").status_code == 401
    assert client.post("/api/mood", json={"mood": 3, "day": today()}).status_code == 401


def test_save_and_list_mood(client):
    token = register(client)
    res = client.post("/api/mood", json={"mood": 4, "day": today()}, headers=auth(token))
    assert res.status_code == 200

    entries = client.get("/api/mood", headers=auth(token)).get_json()["entries"]
    assert entries == [{"day": today(), "mood": 4}]


def test_second_checkin_same_day_replaces_the_first(client):
    token = register(client)
    client.post("/api/mood", json={"mood": 2, "day": today()}, headers=auth(token))
    client.post("/api/mood", json={"mood": 5, "day": today()}, headers=auth(token))

    entries = client.get("/api/mood", headers=auth(token)).get_json()["entries"]
    assert entries == [{"day": today(), "mood": 5}]


@pytest.mark.parametrize("bad", [0, 6, "3", 3.5, True, None])
def test_rejects_invalid_mood(client, bad):
    token = register(client)
    res = client.post("/api/mood", json={"mood": bad, "day": today()}, headers=auth(token))
    assert res.status_code == 400


def test_rejects_backfilled_or_malformed_day(client):
    token = register(client)
    old = (datetime.utcnow().date() - timedelta(days=5)).isoformat()
    assert client.post("/api/mood", json={"mood": 3, "day": old}, headers=auth(token)).status_code == 400
    assert client.post("/api/mood", json={"mood": 3, "day": "yesterday"}, headers=auth(token)).status_code == 400


def test_entries_are_private_per_user(client):
    a, b = register(client), register(client)
    client.post("/api/mood", json={"mood": 1, "day": today()}, headers=auth(a))
    assert client.get("/api/mood", headers=auth(b)).get_json()["entries"] == []
