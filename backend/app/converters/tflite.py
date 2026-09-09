import importlib.util
import os

from app.benchmark.engine import (
    generate_synthetic_inputs,
    measure_file_size,
    measure_process_memory_mb,
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

        import onnx2tf

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

        output_path = os.path.join(output_dir, min(tflite_files))
        logs.append(f"Produced {output_path}")
        return ConversionResult(success=True, output_path=output_path, logs=logs)

    def optimize(self, converted_path: str, config: ConversionConfig) -> OptimizationResult:
        if config.optimization == "fp32":
            return OptimizationResult(applied=True, optimization="fp32", note="No quantization requested")

        if config.optimization == "fp16":
            return self._reconvert_with_quantization(converted_path, config, quantize="fp16")

        if config.optimization == "int8":
            if not config.calibration_dataset_path:
                return OptimizationResult(
                    applied=False,
                    optimization="int8",
                    note="INT8 quantization requires a calibration dataset, which was not provided",
                )
            return self._reconvert_with_quantization(converted_path, config, quantize="int8")

        return OptimizationResult(applied=False, optimization=config.optimization, note="Unknown optimization type")

    def _reconvert_with_quantization(
        self, converted_path: str, config: ConversionConfig, quantize: str
    ) -> OptimizationResult:
        """TFLite quantization must be applied by TFLiteConverter at conversion time, not
        post-hoc on the FlatBuffer, so we re-run the saved-model -> tflite step with the
        appropriate converter flags set.
        """
        try:
            import tensorflow as tf
        except ImportError:
            return OptimizationResult(
                applied=False, optimization=quantize, note="TensorFlow is not installed in this environment"
            )

        saved_model_dir = os.path.dirname(converted_path)
        try:
            converter = tf.lite.TFLiteConverter.from_saved_model(saved_model_dir)
            converter.optimizations = [tf.lite.Optimize.DEFAULT]
            if quantize == "fp16":
                converter.target_spec.supported_types = [tf.float16]
            elif quantize == "int8":
                converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
                converter.inference_input_type = tf.int8
                converter.inference_output_type = tf.int8
            quantized = converter.convert()
            with open(converted_path, "wb") as f:
                f.write(quantized)
            return OptimizationResult(applied=True, optimization=quantize)
        except Exception as exc:
            return OptimizationResult(
                applied=False, optimization=quantize, note=f"Quantization unavailable in current environment: {exc}"
            )

    def benchmark(self, converted_path: str, onnx_model_path: str, config: ConversionConfig) -> BenchmarkResult:
        try:
            import tensorflow as tf
        except ImportError:
            return BenchmarkResult(
                model_size_bytes=measure_file_size(converted_path) if os.path.exists(converted_path) else None,
                unsupported_metrics=["latency_mean_ms", "latency_median_ms", "latency_p95_ms", "throughput_ips", "accuracy_pct", "memory_usage_mb"],
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
        memory_mb = measure_process_memory_mb(lambda: run_once(inputs[0]))

        tflite_outputs = [run_once(sample) for sample in inputs]
        onnx_outputs = run_onnx_inference(onnx_model_path, inputs)
        accuracy = top1_agreement_pct(onnx_outputs, tflite_outputs)

        return BenchmarkResult(
            model_size_bytes=measure_file_size(converted_path),
            latency_mean_ms=stats["mean_ms"],
            latency_median_ms=stats["median_ms"],
            latency_p95_ms=stats["p95_ms"],
            throughput_ips=stats["throughput_ips"],
            accuracy_pct=accuracy,
            memory_usage_mb=memory_mb,
            device="cpu",
            unsupported_metrics=[] if memory_mb is not None else ["memory_usage_mb"],
        )
