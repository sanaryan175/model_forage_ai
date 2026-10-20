import importlib.util
import os
import shutil

from app.benchmark.engine import measure_file_size
from app.converters.base import BenchmarkResult, ConversionConfig, ConversionResult, ModelConverter, OptimizationResult
from app.utils.onnx_utils import inspect_and_validate_onnx

# Running a Core ML model needs Apple's Core ML framework (macOS/iOS only), so nothing that
# requires inference can be measured on the Linux worker. Size is a plain file measurement.
_NEEDS_MACOS = [
    "latency_mean_ms",
    "latency_median_ms",
    "latency_p95_ms",
    "throughput_ips",
    "fidelity_pct",
]


class CoreMLConverter(ModelConverter):
    """Converts a TorchScript .pt upload to an Apple Core ML ML Program (.mlpackage).

    coremltools 7+ converts from PyTorch, not ONNX, so this converter uses the original .pt
    (config.pytorch_model_path) and rejects ONNX uploads. Conversion runs on Linux (the ECS
    worker); running the model does not, so benchmarks report only the size.
    """

    format_name = "coreml"

    def is_supported(self) -> tuple[bool, str | None]:
        missing = [pkg for pkg in ("coremltools", "torch") if importlib.util.find_spec(pkg) is None]
        if missing:
            return False, f"Missing required packages for Core ML conversion: {', '.join(missing)} (installed in the cloud CPU worker)"
        return True, None

    def validate(self, onnx_model_path: str, config: ConversionConfig) -> None:
        inspect_and_validate_onnx(onnx_model_path)

    def convert(self, onnx_model_path: str, output_dir: str, config: ConversionConfig) -> ConversionResult:
        if not config.pytorch_model_path:
            return ConversionResult(
                success=False,
                error=(
                    "Core ML conversion needs a PyTorch upload (TorchScript .pt). coremltools 7+ no longer "
                    "converts from ONNX; upload the model as a .pt and choose Core ML again."
                ),
            )
        supported, reason = self.is_supported()
        if not supported:
            return ConversionResult(success=False, error=reason, is_environment_limited=True, logs=[reason])
        if config.optimization == "int8":
            return ConversionResult(success=False, error="INT8 Core ML needs a calibration dataset, which this platform does not collect yet")

        import coremltools as ct
        import torch

        os.makedirs(output_dir, exist_ok=True)
        model = torch.jit.load(config.pytorch_model_path, map_location="cpu").eval()
        precision = ct.precision.FLOAT16 if config.optimization == "fp16" else ct.precision.FLOAT32
        try:
            mlmodel = ct.convert(
                model,
                inputs=[ct.TensorType(name="input", shape=tuple(config.input_shape))],
                convert_to="mlprogram",  # the modern Core ML format; precision is set at conversion time
                compute_precision=precision,
                minimum_deployment_target=ct.target.iOS15,
            )
        except Exception as exc:
            return ConversionResult(success=False, error=f"coremltools conversion failed: {exc}")

        stem = os.path.splitext(os.path.basename(config.pytorch_model_path))[0]
        package_name = f"{stem}_{config.optimization}.mlpackage"
        mlmodel.save(os.path.join(output_dir, package_name))
        # An .mlpackage is a folder; zip it so it can be stored and downloaded as one file.
        zip_path = shutil.make_archive(os.path.join(output_dir, package_name), "zip", root_dir=output_dir, base_dir=package_name)
        return ConversionResult(
            success=True,
            output_path=zip_path,
            logs=[f"Converted TorchScript to Core ML {config.optimization.upper()} ML Program", f"Packaged {os.path.basename(zip_path)}"],
        )

    def optimize(self, converted_path: str, config: ConversionConfig) -> OptimizationResult:
        if config.optimization in ("fp32", "fp16"):
            # Already applied in convert() via compute_precision.
            return OptimizationResult(applied=True, optimization=config.optimization)
        return OptimizationResult(applied=False, optimization=config.optimization, note="INT8 needs a calibration dataset")

    def benchmark(self, converted_path: str, onnx_model_path: str, config: ConversionConfig) -> BenchmarkResult:
        return BenchmarkResult(
            model_size_bytes=measure_file_size(converted_path) if os.path.exists(converted_path) else None,
            device="macOS required",
            unsupported_metrics=list(_NEEDS_MACOS),
        )
