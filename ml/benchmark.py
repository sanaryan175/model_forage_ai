"""Standalone ONNX Runtime latency/size benchmark for the exported model.

    python benchmark.py
"""

import argparse
import statistics
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort

CHECKPOINT_DIR = Path(__file__).parent / "checkpoints"


def benchmark(onnx_path: Path, iterations: int, warmup: int) -> None:
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    input_meta = session.get_inputs()[0]
    input_shape = [d if isinstance(d, int) else 1 for d in input_meta.shape]
    dummy_input = np.random.default_rng(0).standard_normal(input_shape).astype(np.float32)

    for _ in range(warmup):
        session.run(None, {input_meta.name: dummy_input})

    samples_ms = []
    for _ in range(iterations):
        start = time.perf_counter()
        session.run(None, {input_meta.name: dummy_input})
        samples_ms.append((time.perf_counter() - start) * 1000)

    samples_ms.sort()
    p95 = samples_ms[int(round(0.95 * (len(samples_ms) - 1)))]

    print(f"Model size:     {onnx_path.stat().st_size / 1024:.1f} KB")
    print(f"Mean latency:   {statistics.fmean(samples_ms):.3f} ms")
    print(f"Median latency: {statistics.median(samples_ms):.3f} ms")
    print(f"P95 latency:    {p95:.3f} ms")
    print(f"Throughput:     {1000 / statistics.fmean(samples_ms):.1f} inferences/sec")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx-path", default=str(CHECKPOINT_DIR / "model.onnx"))
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=10)
    args = parser.parse_args()
    benchmark(Path(args.onnx_path), args.iterations, args.warmup)
