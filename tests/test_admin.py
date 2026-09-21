from config import Config


def register_and_login(client):
    reg = client.post(
        "/api/auth/register", json={"password": "testpass123", "avatar": "🌱"}
    ).get_json()
    return reg["token"]


def admin_token(client):
    res = client.post(
        "/api/auth/login",
        json={
            "username": Config.DEFAULT_ADMIN_USERNAME,
            "password": Config.DEFAULT_ADMIN_PASSWORD,
        },
    )
    return res.get_json()["token"]


def test_admin_endpoint_rejects_regular_user(client):
    token = register_and_login(client)
    res = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_admin_endpoint_rejects_no_auth(client):
    res = client.get("/api/admin/stats")
    assert res.status_code == 401


def test_admin_endpoint_allows_admin(client):
    token = admin_token(client)
    res = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "total_users" in res.get_json()


def test_admin_can_block_a_user_and_they_can_no_longer_login(client):
    reg = client.post(
        "/api/auth/register", json={"password": "testpass123", "avatar": "🌱"}
    ).get_json()
    user_id = reg["user"]["id"]
    username = reg["user"]["username"]

    token = admin_token(client)
    res = client.post(
        f"/api/admin/users/{user_id}/block",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.get_json()["user"]["is_blocked"] is True

    login_res = client.post(
        "/api/auth/login",
        json={"username": username, "password": "testpass123"},
    )
    assert login_res.status_code == 403


def test_admin_cannot_be_blocked(client):
    token = admin_token(client)
    admin_res = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    ).get_json()
    admin_id = admin_res["user"]["id"]

    res = client.post(
        f"/api/admin/users/{admin_id}/block",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
