import re

USERNAME_PATTERN = re.compile(r"^[a-z]+_[a-z]+\d+$")


def register(client, password="testpass123", avatar="🌱", **extra):
    payload = {"password": password, "avatar": avatar, **extra}
    return client.post("/api/auth/register", json=payload)


def test_suggest_username_returns_generated_style_name(client):
    res = client.get("/api/auth/suggest-username")
    assert res.status_code == 200
    assert USERNAME_PATTERN.match(res.get_json()["username"])


def test_register_assigns_an_auto_generated_username(client):
    res = register(client)
    assert res.status_code == 201
    body = res.get_json()
    assert "token" in body
    assert USERNAME_PATTERN.match(body["user"]["username"])


def test_register_ignores_client_supplied_username(client):
    """The whole point of the anonymous flow: no one can pick a name
    that might identify them, even by calling the API directly."""
    res = register(client, username="my_real_name_2004")
    assert res.status_code == 201
    assert res.get_json()["user"]["username"] != "my_real_name_2004"


def test_register_rejects_short_password(client):
    res = register(client, password="short")
    assert res.status_code == 400


def test_register_falls_back_to_random_avatar_for_invalid_choice(client):
    res = register(client, avatar="not-a-real-avatar")
    assert res.status_code == 201
    assert res.get_json()["user"]["avatar"] != "not-a-real-avatar"


def test_login_succeeds_with_correct_credentials(client):
    reg = register(client, password="correcthorse1").get_json()
    username = reg["user"]["username"]

    res = client.post(
        "/api/auth/login",
        json={"username": username, "password": "correcthorse1"},
    )
    assert res.status_code == 200
    assert "token" in res.get_json()


def test_login_fails_with_wrong_password(client):
    reg = register(client, password="correcthorse1").get_json()
    username = reg["user"]["username"]

    res = client.post(
        "/api/auth/login",
        json={"username": username, "password": "wrong-password"},
    )
    assert res.status_code == 401


def test_me_requires_auth(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_me_returns_current_user_with_valid_token(client):
    reg = register(client).get_json()
    res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {reg['token']}"},
    )
    assert res.status_code == 200
    assert res.get_json()["user"]["username"] == reg["user"]["username"]
