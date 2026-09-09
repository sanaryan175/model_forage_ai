from tests.factories import make_invalid_onnx_bytes, make_valid_onnx_bytes


def test_upload_valid_onnx_model_becomes_ready(client, auth_headers):
    response = client.post(
        "/api/models/upload",
        params={"name": "Test Model"},
        files={"file": ("model.onnx", make_valid_onnx_bytes(), "application/octet-stream")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["framework"] == "onnx"
    assert body["input_shape"] == "[1, 3, 4, 4]"


def test_upload_invalid_onnx_model_marked_invalid(client, auth_headers):
    response = client.post(
        "/api/models/upload",
        params={"name": "Broken Model"},
        files={"file": ("model.onnx", make_invalid_onnx_bytes(), "application/octet-stream")},
        headers=auth_headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "invalid"
    assert body["validation_error"] is not None


def test_upload_rejects_unsupported_extension(client, auth_headers):
    response = client.post(
        "/api/models/upload",
        params={"name": "Bad Extension"},
        files={"file": ("model.txt", b"hello", "text/plain")},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_upload_requires_authentication(client):
    response = client.post(
        "/api/models/upload",
        params={"name": "Test"},
        files={"file": ("model.onnx", make_valid_onnx_bytes(), "application/octet-stream")},
    )
    assert response.status_code == 401


def test_list_models_only_returns_own_models(client, auth_headers):
    client.post(
        "/api/models/upload",
        params={"name": "Mine"},
        files={"file": ("model.onnx", make_valid_onnx_bytes(), "application/octet-stream")},
        headers=auth_headers,
    )
    client.post(
        "/api/auth/register",
        json={"name": "Other", "email": "other@example.com", "password": "password123"},
    )
    other_login = client.post(
        "/api/auth/login", json={"email": "other@example.com", "password": "password123"}
    )
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

    mine = client.get("/api/models", headers=auth_headers).json()
    others = client.get("/api/models", headers=other_headers).json()
    assert mine["total"] == 1
    assert others["total"] == 0


def test_delete_model(client, auth_headers):
    upload = client.post(
        "/api/models/upload",
        params={"name": "To Delete"},
        files={"file": ("model.onnx", make_valid_onnx_bytes(), "application/octet-stream")},
        headers=auth_headers,
    )
    model_id = upload.json()["id"]
    delete_response = client.delete(f"/api/models/{model_id}", headers=auth_headers)
    assert delete_response.status_code == 204
    assert client.get(f"/api/models/{model_id}", headers=auth_headers).status_code == 404
