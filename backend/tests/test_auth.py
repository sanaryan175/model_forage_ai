def test_register_creates_user_and_returns_token(client):
    response = client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "ada@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    assert "access_token" in response.json()


def test_register_rejects_duplicate_email(client):
    payload = {"name": "Ada", "email": "ada@example.com", "password": "password123"}
    client.post("/api/auth/register", json=payload)
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


def test_login_with_correct_credentials(client):
    client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "ada@example.com", "password": "password123"},
    )
    response = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_fails(client):
    client.post(
        "/api/auth/register",
        json={"name": "Ada", "email": "ada@example.com", "password": "password123"},
    )
    response = client.post("/api/auth/login", json={"email": "ada@example.com", "password": "wrong"})
    assert response.status_code == 401


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_api_key_lifecycle(client, auth_headers):
    create = client.post("/api/auth/api-keys", json={"name": "CI"}, headers=auth_headers)
    assert create.status_code == 201
    key_id = create.json()["id"]
    assert create.json()["key"].startswith("mfk_")

    listing = client.get("/api/auth/api-keys", headers=auth_headers)
    assert len(listing.json()) == 1
    assert "key" not in listing.json()[0]

    revoke = client.delete(f"/api/auth/api-keys/{key_id}", headers=auth_headers)
    assert revoke.status_code == 204
    assert client.get("/api/auth/api-keys", headers=auth_headers).json() == []
