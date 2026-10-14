import time

import pytest

from app.converters.registry import get_converter
from tests.factories import make_valid_onnx_bytes


def _upload_ready_model(client, auth_headers, name="Model"):
    response = client.post(
        "/api/models/upload",
        params={"name": name},
        files={"file": ("model.onnx", make_valid_onnx_bytes(), "application/octet-stream")},
        headers=auth_headers,
    )
    return response.json()


def _wait_for_terminal_status(client, job_id, auth_headers, timeout=60):  # jobs run one at a time; first TF import is slow
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
    assert [j["target_format"] for j in jobs] == ["tflite", "onnx"]  # requested format + auto ONNX baseline
    # The worker may already have picked up the first job by the time the response is built.
    assert all(j["status"] in {"queued", "validating"} for j in jobs)

    job = _wait_for_terminal_status(client, jobs[0]["id"], auth_headers)
    # Environment may or may not have tensorflow/onnx2tf installed; either way the job
    # must resolve to a real terminal state, never stay stuck or fake a result.
    assert job["status"] in {"completed", "failed"}


def test_create_conversion_for_unsupported_format_reports_environment_limitation(client, auth_headers):
    model = _upload_ready_model(client, auth_headers)
    response = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["coreml"], "optimization": "fp32"},
        headers=auth_headers,
    )
    job = _wait_for_terminal_status(client, response.json()[0]["id"], auth_headers)
    assert job["status"] == "failed"
    assert "core ml" in job["error_message"].lower()


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
        json={"model_id": model["id"], "target_formats": ["coreml"], "optimization": "fp32"},
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
        json={"model_id": model["id"], "target_formats": ["coreml"], "optimization": "fp32"},
        headers=auth_headers,
    )
    job_id = response.json()[0]["id"]
    job = _wait_for_terminal_status(client, job_id, auth_headers)
    assert job["status"] == "failed"

    retry_response = client.post(f"/api/conversions/{job_id}/retry", headers=auth_headers)
    assert retry_response.status_code == 200
    assert retry_response.json()["status"] in {"queued", "validating", "failed"}


def test_onnx_baseline_is_added_once_per_model_and_benchmarked(client, auth_headers):
    model = _upload_ready_model(client, auth_headers)
    first = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["coreml"], "optimization": "fp32"},
        headers=auth_headers,
    ).json()
    baseline = next(j for j in first if j["target_format"] == "onnx")
    assert baseline["optimization"] == "fp32"
    assert _wait_for_terminal_status(client, baseline["id"], auth_headers)["status"] == "completed"

    second = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["coreml"], "optimization": "fp32"},
        headers=auth_headers,
    ).json()
    assert [j["target_format"] for j in second] == ["coreml"]

    benchmarks = client.get("/api/benchmarks", headers=auth_headers).json()["items"]
    row = next(b for b in benchmarks if b["job_id"] == baseline["id"])
    assert row["latency_mean_ms"] > 0 and row["model_size_bytes"] > 0

    # The baseline is the user's own upload, so it must not show up as a generated model.
    artifacts = client.get("/api/artifacts", headers=auth_headers).json()["items"]
    assert all(a["job_id"] != baseline["id"] for a in artifacts)
    # Timestamps must carry a timezone, or browsers read UTC as local time.
    assert baseline["created_at"].endswith(("Z", "+00:00"))


# Without TensorFlow (e.g. CI, which installs only requirements.txt) the job fails earlier with "not installed".
@pytest.mark.skipif(not get_converter("tflite").is_supported()[0], reason="needs tensorflow + onnx2tf")
def test_unapplied_optimization_fails_instead_of_mislabelling(client, auth_headers):
    model = _upload_ready_model(client, auth_headers)
    jobs = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["tflite"], "optimization": "int8"},
        headers=auth_headers,
    ).json()
    job = _wait_for_terminal_status(client, jobs[0]["id"], auth_headers)
    assert job["status"] == "failed"
    assert "INT8" in job["error_message"]


def test_cancel_flag_is_ignored_when_no_thread_is_running():
    # A stale flag would instantly cancel the next retry of the same job.
    from app.workers.conversion_worker import _is_cancelled, request_cancel

    request_cancel("job-without-thread")
    assert not _is_cancelled("job-without-thread")


def test_job_waiting_for_another_job_can_be_cancelled(client, auth_headers):
    # Jobs run one at a time; a queued job must stay cancellable while it waits.
    from app.workers.conversion_worker import _pipeline_lock

    model = _upload_ready_model(client, auth_headers)
    with _pipeline_lock:  # simulate another job holding the CPU
        job_id = client.post(
            "/api/conversions",
            json={"model_id": model["id"], "target_formats": ["tflite"], "optimization": "fp32"},
            headers=auth_headers,
        ).json()[0]["id"]
        time.sleep(0.3)
        assert client.get(f"/api/conversions/{job_id}", headers=auth_headers).json()["status"] == "queued"
        assert client.post(f"/api/conversions/{job_id}/cancel", headers=auth_headers).status_code == 200
    assert _wait_for_terminal_status(client, job_id, auth_headers)["status"] == "cancelled"


def test_finished_job_delivered_again_is_not_reconverted(client, auth_headers):
    # SQS is at-least-once: a second delivery of a completed job must be a no-op.
    from app.workers.conversion_worker import run_conversion_job

    model = _upload_ready_model(client, auth_headers)
    jobs = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["onnx"], "optimization": "fp32"},
        headers=auth_headers,
    ).json()
    job_id = jobs[0]["id"]
    assert _wait_for_terminal_status(client, job_id, auth_headers)["status"] == "completed"
    benchmarks_before = client.get("/api/benchmarks", headers=auth_headers).json()["total"]

    run_conversion_job(job_id)

    assert client.get("/api/benchmarks", headers=auth_headers).json()["total"] == benchmarks_before


def test_aws_executor_routes_tensorrt_to_gpu_queue_and_the_rest_to_cpu(client, auth_headers):
    from app.workers.job_executor import AWSJobExecutor

    class RecordingQueue:
        def __init__(self):
            self.published = []

        def publish(self, queue_name, message):
            self.published.append((queue_name, message["job_id"]))

        def subscribe(self, queue_name, handler):
            raise NotImplementedError

    model = _upload_ready_model(client, auth_headers)
    jobs = client.post(
        "/api/conversions",
        json={"model_id": model["id"], "target_formats": ["tensorrt", "tflite", "coreml"], "optimization": "fp32"},
        headers=auth_headers,
    ).json()
    for job in jobs:
        _wait_for_terminal_status(client, job["id"], auth_headers)

    queue = RecordingQueue()
    executor = AWSJobExecutor(queue)
    for job in jobs:
        executor.submit(job["id"])

    queue_by_format = {j["target_format"]: q for (q, job_id), j in zip(queue.published, jobs, strict=True)}
    assert queue_by_format == {
        "tensorrt": "modelforge-tensorrt",
        "tflite": "modelforge-cpu",
        "coreml": "modelforge-cpu",
        "onnx": "modelforge-cpu",
    }
