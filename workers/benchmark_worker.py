"""Benchmarking is not a separate queue/worker in this implementation.

Each format worker (tflite_worker.py, tensorrt_worker.py, coreml_worker.py) runs the
BENCHMARKING stage itself immediately after OPTIMIZING, via the shared pipeline in
backend/app/workers/conversion_worker.py and the measurement primitives in
backend/app/benchmark/engine.py. Splitting benchmarking into its own SQS queue would
mean re-fetching the converted artifact from S3 into a second container for no benefit,
since the format worker already holds the artifact on local disk right after conversion.

This file exists to document that decision explicitly, per the project's workers/
layout, rather than silently omitting the module.
"""
