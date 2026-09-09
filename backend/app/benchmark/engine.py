"""Shared benchmarking primitives used by every format converter.

Every function here performs a real measurement. When a metric cannot be measured in the
current environment (missing runtime, missing hardware), callers must report it as N/A via
`BenchmarkResult.unsupported_metrics` instead of inventing a number.
"""

import os
import statistics
import time
from collections.abc import Callable

import numpy as np


def measure_file_size(path: str) -> int:
    return os.path.getsize(path)


def timed_inference_stats(run_once: Callable[[], None], iterations: int = 50, warmup: int = 5) -> dict[str, float]:
    """Run `run_once` repeatedly and return mean/median/p95 latency in milliseconds."""
    for _ in range(warmup):
        run_once()

    samples_ms: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        run_once()
        samples_ms.append((time.perf_counter() - start) * 1000.0)

    samples_ms.sort()
    p95_index = min(len(samples_ms) - 1, int(round(0.95 * (len(samples_ms) - 1))))
    return {
        "mean_ms": statistics.fmean(samples_ms),
        "median_ms": statistics.median(samples_ms),
        "p95_ms": samples_ms[p95_index],
        "throughput_ips": 1000.0 / statistics.fmean(samples_ms) if statistics.fmean(samples_ms) > 0 else 0.0,
    }


def measure_process_memory_mb(run_once: Callable[[], None]) -> float | None:
    """Best-effort resident memory delta while running `run_once`, using psutil if installed."""
    try:
        import psutil
    except ImportError:
        return None

    process = psutil.Process(os.getpid())
    before = process.memory_info().rss
    run_once()
    after = process.memory_info().rss
    return max(after - before, 0) / (1024 * 1024)


def top1_agreement_pct(reference_outputs: list[np.ndarray], candidate_outputs: list[np.ndarray]) -> float:
    """Fidelity metric: % of samples where the converted model's top-1 class matches the
    original ONNX model's top-1 class on the same synthetic inputs. This is the
    "compare original model and converted model" accuracy check from the spec, and
    does not require ground-truth labels.
    """
    if not reference_outputs or len(reference_outputs) != len(candidate_outputs):
        return 0.0
    matches = 0
    for ref, cand in zip(reference_outputs, candidate_outputs, strict=True):
        if np.argmax(ref.flatten()) == np.argmax(cand.flatten()):
            matches += 1
    return 100.0 * matches / len(reference_outputs)


def generate_synthetic_inputs(input_shape: list[int], count: int = 20, seed: int = 42) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    return [rng.standard_normal(input_shape).astype(np.float32) for _ in range(count)]
