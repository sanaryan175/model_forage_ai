import importlib.util
import os

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


class TensorRTConverter(ModelConverter):
    """Converts ONNX models to a TensorRT engine. Requires an NVIDIA GPU, CUDA, and the
    TensorRT SDK — none of which are assumed to exist on a developer laptop. When absent,
    this converter reports the job as environment-limited rather than fabricating a
    ".engine" file or benchmark numbers, per the platform's "never fake it" rule.
    """

    format_name = "tensorrt"

    def is_supported(self) -> tuple[bool, str | None]:
        if importlib.util.find_spec("tensorrt") is None:
            return False, "The 'tensorrt' Python package (NVIDIA TensorRT SDK) is not installed"
        try:
            import pycuda.driver as cuda  # noqa: F401
        except ImportError:
            return False, "PyCUDA / an accessible NVIDIA CUDA GPU was not detected on this machine"
        return True, None

    def validate(self, onnx_model_path: str, config: ConversionConfig) -> None:
        inspect_and_validate_onnx(onnx_model_path)

    def convert(self, onnx_model_path: str, output_dir: str, config: ConversionConfig) -> ConversionResult:
        supported, reason = self.is_supported()
        if not supported:
            message = (
                f"TensorRT conversion skipped: {reason}. This is a hardware/platform limitation of the "
                "current machine, not a defect - TensorRT engines can only be built on a host with an "
                "NVIDIA GPU, CUDA, and the TensorRT SDK installed. Deploy this job to the "
                "'modelforge-tensorrt' ECS+GPU worker (see infrastructure/) to run a real conversion."
            )
            return ConversionResult(success=False, error=message, is_environment_limited=True, logs=[message])

        # Real path — only reached on a host with TensorRT + CUDA available.
        import tensorrt as trt

        os.makedirs(output_dir, exist_ok=True)
        logger = trt.Logger(trt.Logger.WARNING)
        builder = trt.Builder(logger)
        network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
        parser = trt.OnnxParser(network, logger)
        with open(onnx_model_path, "rb") as f:
            if not parser.parse(f.read()):
                errors = "; ".join(str(parser.get_error(i)) for i in range(parser.num_errors))
                return ConversionResult(success=False, error=f"TensorRT ONNX parsing failed: {errors}")

        build_config = builder.create_builder_config()
        if config.optimization == "fp16" and builder.platform_has_fast_fp16:
            build_config.set_flag(trt.BuilderFlag.FP16)
        serialized_engine = builder.build_serialized_network(network, build_config)
        output_path = os.path.join(output_dir, "model.engine")
        with open(output_path, "wb") as f:
            f.write(serialized_engine)
        return ConversionResult(success=True, output_path=output_path, logs=["Built TensorRT engine"])

    def optimize(self, converted_path: str, config: ConversionConfig) -> OptimizationResult:
        if config.optimization == "int8":
            return OptimizationResult(
                applied=False,
                optimization="int8",
                note="INT8 calibration for TensorRT requires a GPU build step; unavailable in current environment",
            )
        return OptimizationResult(
            applied=config.optimization == "fp16",
            optimization=config.optimization,
            note=None if config.optimization in ("fp32", "fp16") else "Optimization unavailable in current environment",
        )

    def benchmark(self, converted_path: str, onnx_model_path: str, config: ConversionConfig) -> BenchmarkResult:
        supported, _ = self.is_supported()
        if not supported:
            return BenchmarkResult(device="nvidia-gpu (unavailable)", unsupported_metrics=list(_ALL_METRICS))

        # Real GPU benchmarking path (only reached with TensorRT + CUDA present).
        from app.benchmark.engine import measure_file_size

        return BenchmarkResult(model_size_bytes=measure_file_size(converted_path), device="nvidia-gpu")
