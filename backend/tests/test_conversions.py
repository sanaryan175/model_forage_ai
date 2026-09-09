import time

from tests.factories import make_valid_onnx_bytes


def _upload_ready_model(client, auth_headers, name="Model"):
    response = client.post(
        "/api/models/upload",
        params={"name": name},
        files={"file": ("model.onnx", make_valid_onnx_bytes(), "application/octet-stream")},
        headers=auth_headers,
    )
    return response.json()


def _wait_for_terminal_status(client, job_id, auth_headers, timeout=15):
    terminal = {"completed", "failed", "cancelled"}
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/api/conversions/{job_id}", headers=auth_headers).json()
        if job["status"] in terminal:
            return job
        time.sleep(0.2)
    raise TimeoutError(f"Job {job_id} did not reach a terminal status in {timeout}s")


def test_create_conversion_requires_ready_model(client, auth_headers):
    upload = client.post(
        "/api/models/upload",
        params={"name": "Bad"},
        files={"file": ("model.onnx", b"not valid onnx", "application/octet-stream")},
        headers=auth_headers,
    )
    model_id = upload.json()["id"]
    response = client.post(
        "/api/conversions",
        json={"model_id": model_id, "target_formats": ["tflite"], "optimization": "fp32"},
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_create_conversion_starts_queued_and_reaches_terminal_state(client, auth_headers):
    model = _upload_ready_model(client, auth_headers)
    response = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["tflite"], "optimization": "fp32"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["status"] == "queued"

    job = _wait_for_terminal_status(client, jobs[0]["id"], auth_headers)
    # Environment may or may not have tensorflow/onnx2tf installed; either way the job
    # must resolve to a real terminal state, never stay stuck or fake a result.
    assert job["status"] in {"completed", "failed"}


def test_create_conversion_for_unsupported_format_reports_environment_limitation(client, auth_headers):
    model = _upload_ready_model(client, auth_headers)
    response = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["tensorrt"], "optimization": "fp32"},
        headers=auth_headers,
    )
    job = _wait_for_terminal_status(client, response.json()[0]["id"], auth_headers)
    assert job["status"] == "failed"
    assert "tensorrt" in job["error_message"].lower() or "cuda" in job["error_message"].lower()


def test_conversion_logs_are_recorded(client, auth_headers):
    model = _upload_ready_model(client, auth_headers)
    response = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["tflite"], "optimization": "fp32"},
        headers=auth_headers,
    )
    job_id = response.json()[0]["id"]
    _wait_for_terminal_status(client, job_id, auth_headers)

    logs = client.get(f"/api/conversions/{job_id}/logs", headers=auth_headers).json()
    assert len(logs["items"]) > 0


def test_cancel_completed_job_is_rejected(client, auth_headers):
    model = _upload_ready_model(client, auth_headers)
    response = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["tensorrt"], "optimization": "fp32"},
        headers=auth_headers,
    )
    job_id = response.json()[0]["id"]
    _wait_for_terminal_status(client, job_id, auth_headers)

    cancel_response = client.post(f"/api/conversions/{job_id}/cancel", headers=auth_headers)
    assert cancel_response.status_code == 400


def test_retry_failed_job_requeues_it(client, auth_headers):
    model = _upload_ready_model(client, auth_headers)
    response = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["tensorrt"], "optimization": "fp32"},
        headers=auth_headers,
    )
    job_id = response.json()[0]["id"]
    job = _wait_for_terminal_status(client, job_id, auth_headers)
    assert job["status"] == "failed"

    retry_response = client.post(f"/api/conversions/{job_id}/retry", headers=auth_headers)
    assert retry_response.status_code == 200
    assert retry_response.json()["status"] in {"queued", "validating", "failed"}
