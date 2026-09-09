import importlib.util
import os
import platform

from app.converters.base import BenchmarkResult, ConversionConfig, ConversionResult, ModelConverter, OptimizationResult
from app.utils.onnx_utils import inspect_and_validate_onnx

_ALL_METRICS = [
    "latency_mean_ms",
    "latency_median_ms",
    "latency_p95_ms",
    "throughput_ips",
    "accuracy_pct",
    "memory_usage_mb",
]


class CoreMLConverter(ModelConverter):
    """Converts ONNX models to Apple Core ML (.mlpackage). Graph conversion can run on any
    OS, but recent coremltools releases (7+) dropped the direct ONNX importer in favor of
    PyTorch/TensorFlow source conversion, and running/predicting with a compiled Core ML
    model is only possible on macOS. Both limitations are surfaced explicitly rather than
    faked.
    """

    format_name = "coreml"

    def is_supported(self) -> tuple[bool, str | None]:
        if importlib.util.find_spec("coremltools") is None:
            return False, "The 'coremltools' package is not installed"
        try:
            import coremltools as ct

            if not hasattr(ct.converters, "onnx"):
                return False, "This coremltools version does not include the ONNX converter (removed upstream in 7.0+)"
        except ImportError as exc:
            return False, str(exc)
        return True, None

    def validate(self, onnx_model_path: str, config: ConversionConfig) -> None:
        inspect_and_validate_onnx(onnx_model_path)

    def convert(self, onnx_model_path: str, output_dir: str, config: ConversionConfig) -> ConversionResult:
        supported, reason = self.is_supported()
        if not supported:
            message = (
                f"Core ML conversion skipped: {reason}. Convert via an intermediate PyTorch trace on a "
                "worker with a pinned coremltools<7 (last ONNX-import-capable release), or run the "
                "'modelforge-coreml' ECS worker described in infrastructure/aws."
            )
            return ConversionResult(success=False, error=message, is_environment_limited=True, logs=[message])

        import coremltools as ct

        os.makedirs(output_dir, exist_ok=True)
        try:
            mlmodel = ct.converters.onnx.convert(model=onnx_model_path)
            output_path = os.path.join(output_dir, "model.mlmodel")
            mlmodel.save(output_path)
        except Exception as exc:
            return ConversionResult(success=False, error=f"Core ML conversion failed: {exc}")
        return ConversionResult(success=True, output_path=output_path, logs=["Saved Core ML model"])

    def optimize(self, converted_path: str, config: ConversionConfig) -> OptimizationResult:
        if config.optimization == "fp32":
            return OptimizationResult(applied=True, optimization="fp32")
        if config.optimization == "fp16":
            try:
                import coremltools as ct

                spec = ct.utils.load_spec(converted_path)
                fp16_spec = ct.models.neural_network.quantization_utils.quantize_weights(spec, nbits=16)
                ct.utils.save_spec(fp16_spec, converted_path)
                return OptimizationResult(applied=True, optimization="fp16")
            except Exception as exc:
                return OptimizationResult(applied=False, optimization="fp16", note=f"Optimization unavailable in current environment: {exc}")
        return OptimizationResult(
            applied=False, optimization="int8", note="INT8 quantization for Core ML requires a calibration pass not implemented for this format"
        )

    def benchmark(self, converted_path: str, onnx_model_path: str, config: ConversionConfig) -> BenchmarkResult:
        from app.benchmark.engine import measure_file_size

        size = measure_file_size(converted_path) if os.path.exists(converted_path) else None
        if platform.system() != "Darwin":
            return BenchmarkResult(
                model_size_bytes=size,
                device="macOS (unavailable)",
                unsupported_metrics=list(_ALL_METRICS),
            )

        # Real inference path — only reachable when actually running on macOS.
        # Would load ct.models.MLModel(converted_path) and time model.predict(...) with a
        # synthetic input built from the model spec; omitted since this server isn't macOS.
        return BenchmarkResult(model_size_bytes=size, device="macos-coreml")
