import importlib.util
import os

from app.benchmark.engine import (
    generate_synthetic_inputs,
    measure_file_size,
    timed_inference_stats,
    top1_agreement_pct,
)
from app.converters.base import BenchmarkResult, ConversionConfig, ConversionResult, ModelConverter, OptimizationResult
from app.utils.onnx_utils import inspect_and_validate_onnx, run_onnx_inference


class TFLiteConverter(ModelConverter):
    """Converts ONNX models to TensorFlow Lite via onnx2tf, then to a .tflite FlatBuffer.
    Runs fully on CPU, so this is the format most likely to produce a real, working
    conversion + benchmark on a typical developer laptop without a GPU.
    """

    format_name = "tflite"

    def is_supported(self) -> tuple[bool, str | None]:
        missing = [pkg for pkg in ("tensorflow", "onnx2tf") if importlib.util.find_spec(pkg) is None]
        if missing:
            return False, f"Missing required packages for TFLite conversion: {', '.join(missing)}"
        return True, None

    def validate(self, onnx_model_path: str, config: ConversionConfig) -> None:
        inspect_and_validate_onnx(onnx_model_path)

    def convert(self, onnx_model_path: str, output_dir: str, config: ConversionConfig) -> ConversionResult:
        supported, reason = self.is_supported()
        if not supported:
            return ConversionResult(success=False, error=reason, is_environment_limited=True, logs=[reason])

        import importlib

        import numpy as np
        import onnx2tf

        # onnx2tf downloads a sample-image .npy from a GitHub release on every conversion (only to
        # sanity-check outputs; we never use its INT8 calibration). That download breaks offline and
        # in containers, so hand it the same-shaped zeros instead.
        # ponytail: patches an onnx2tf internal; re-check after upgrading onnx2tf.
        importlib.import_module("onnx2tf.onnx2tf").download_test_image_data = (
            lambda: np.zeros((20, 128, 128, 3), dtype=np.float32)
        )

        logs: list[str] = []
        os.makedirs(output_dir, exist_ok=True)
        try:
            logs.append("Running onnx2tf to produce an intermediate TensorFlow SavedModel")
            onnx2tf.convert(
                input_onnx_file_path=onnx_model_path,
                output_folder_path=output_dir,
                copy_onnx_input_output_names_to_tflite=True,
                non_verbose=True,
            )
        except Exception as exc:
            return ConversionResult(success=False, error=f"onnx2tf conversion failed: {exc}", logs=logs)

        tflite_files = [f for f in os.listdir(output_dir) if f.endswith(".tflite")]
        if not tflite_files:
            return ConversionResult(
                success=False, error="onnx2tf did not produce a .tflite output file", logs=logs
            )

        # onnx2tf writes both *_float32.tflite and *_float16.tflite; FP16 is just picking the second one.
        wanted = "float16" if config.optimization == "fp16" else "float32"
        output_path = os.path.join(output_dir, next((f for f in tflite_files if wanted in f), tflite_files[0]))
        logs.append(f"Produced {output_path}")
        return ConversionResult(success=True, output_path=output_path, logs=logs)

    def optimize(self, converted_path: str, config: ConversionConfig) -> OptimizationResult:
        if config.optimization in ("fp32", "fp16"):
            # Already applied in convert(): onnx2tf emits both precisions.
            return OptimizationResult(applied=True, optimization=config.optimization)
        return OptimizationResult(
            applied=False,
            optimization=config.optimization,
            note="INT8 TFLite quantization needs a representative calibration dataset, which this platform does not collect yet",
        )

    def benchmark(self, converted_path: str, onnx_model_path: str, config: ConversionConfig) -> BenchmarkResult:
        try:
            import tensorflow as tf
        except ImportError:
            return BenchmarkResult(
                model_size_bytes=measure_file_size(converted_path) if os.path.exists(converted_path) else None,
                unsupported_metrics=["latency_mean_ms", "latency_median_ms", "latency_p95_ms", "throughput_ips", "fidelity_pct"],
            )

        interpreter = tf.lite.Interpreter(model_path=converted_path)
        interpreter.allocate_tensors()
        input_details = interpreter.get_input_details()[0]
        output_details = interpreter.get_output_details()[0]
        input_shape = list(input_details["shape"])

        inputs = generate_synthetic_inputs(input_shape, count=20)

        def run_once(sample=None):
            sample = sample if sample is not None else inputs[0]
            interpreter.set_tensor(input_details["index"], sample.astype(input_details["dtype"]))
            interpreter.invoke()
            return interpreter.get_tensor(output_details["index"])

        stats = timed_inference_stats(lambda: run_once(inputs[0]), iterations=50)

        tflite_outputs = [run_once(sample) for sample in inputs]
        onnx_outputs = run_onnx_inference(onnx_model_path, inputs)
        # onnx2tf makes 4D outputs channels-last (NHWC) while ONNX is NCHW. Put them back in ONNX
        # layout, otherwise the flattened argmax compares different elements and fidelity reads 0%.
        tflite_outputs = [
            out.transpose(0, 3, 1, 2) if out.ndim == 4 and out.transpose(0, 3, 1, 2).shape == ref.shape != out.shape else out
            for out, ref in zip(tflite_outputs, onnx_outputs, strict=True)
        ]
        fidelity = top1_agreement_pct(onnx_outputs, tflite_outputs)

        return BenchmarkResult(
            model_size_bytes=measure_file_size(converted_path),
            latency_mean_ms=stats["mean_ms"],
            latency_median_ms=stats["median_ms"],
            latency_p95_ms=stats["p95_ms"],
            throughput_ips=stats["throughput_ips"],
            fidelity_pct=fidelity,
            device="cpu",
        )
