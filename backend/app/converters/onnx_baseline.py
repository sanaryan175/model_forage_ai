from app.benchmark.engine import generate_synthetic_inputs, measure_file_size, timed_inference_stats
from app.converters.base import BenchmarkResult, ConversionConfig, ConversionResult, ModelConverter, OptimizationResult
from app.utils.onnx_utils import inspect_and_validate_onnx


class OnnxBaselineConverter(ModelConverter):
    """The original ONNX model run through ONNX Runtime, unchanged. It is the reference that
    every converted format is compared against (size, latency) on the Compare page.
    """

    format_name = "onnx"

    def is_supported(self) -> tuple[bool, str | None]:
        return True, None  # onnxruntime is a core backend dependency

    def validate(self, onnx_model_path: str, config: ConversionConfig) -> None:
        inspect_and_validate_onnx(onnx_model_path)

    def convert(self, onnx_model_path: str, output_dir: str, config: ConversionConfig) -> ConversionResult:
        return ConversionResult(success=True, output_path=onnx_model_path, logs=["Using the original ONNX model as the baseline"])

    def optimize(self, converted_path: str, config: ConversionConfig) -> OptimizationResult:
        if config.optimization == "fp32":
            return OptimizationResult(applied=True, optimization="fp32")
        return OptimizationResult(applied=False, optimization=config.optimization, note="The ONNX baseline is always FP32")

    def benchmark(self, converted_path: str, onnx_model_path: str, config: ConversionConfig) -> BenchmarkResult:
        import onnxruntime as ort

        session = ort.InferenceSession(converted_path, providers=["CPUExecutionProvider"])
        input_meta = session.get_inputs()[0]
        shape = [d if isinstance(d, int) and d > 0 else 1 for d in input_meta.shape]
        sample = generate_synthetic_inputs(shape, count=1)[0]
        stats = timed_inference_stats(lambda: session.run(None, {input_meta.name: sample}), iterations=50)

        return BenchmarkResult(
            model_size_bytes=measure_file_size(converted_path),
            latency_mean_ms=stats["mean_ms"],
            latency_median_ms=stats["median_ms"],
            latency_p95_ms=stats["p95_ms"],
            throughput_ips=stats["throughput_ips"],
            # fidelity_pct stays None: this IS the reference the other formats are scored against.
            device="cpu",
        )
