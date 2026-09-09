from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ConversionConfig:
    optimization: str  # "fp32" | "fp16" | "int8"
    batch_size: int = 1
    target_device: str = "cpu"
    input_shape: list[int] | None = None
    calibration_dataset_path: str | None = None


@dataclass
class ConversionResult:
    success: bool
    output_path: str | None = None
    logs: list[str] = field(default_factory=list)
    error: str | None = None
    is_environment_limited: bool = False
    """True when the failure is caused by a missing platform capability
    (e.g. no NVIDIA GPU for TensorRT, no macOS Core ML runtime) rather than a bug."""


@dataclass
class OptimizationResult:
    applied: bool
    optimization: str
    note: str | None = None
    """Explains why an optimization could not be applied, if `applied` is False."""


@dataclass
class BenchmarkResult:
    model_size_bytes: int | None = None
    latency_mean_ms: float | None = None
    latency_median_ms: float | None = None
    latency_p95_ms: float | None = None
    throughput_ips: float | None = None
    accuracy_pct: float | None = None
    memory_usage_mb: float | None = None
    device: str = "cpu"
    unsupported_metrics: list[str] = field(default_factory=list)
    """Metrics that could not be measured in this environment; reported as N/A, never fabricated."""


class ModelConverter(ABC):
    """Common interface every format-specific converter (TFLite, TensorRT, Core ML) must implement."""

    format_name: str

    @abstractmethod
    def is_supported(self) -> tuple[bool, str | None]:
        """Return (supported, reason). `reason` explains why not, when unsupported."""

    @abstractmethod
    def validate(self, onnx_model_path: str, config: ConversionConfig) -> None:
        """Raise ValueError with a clear message if the ONNX model cannot be converted."""

    @abstractmethod
    def convert(self, onnx_model_path: str, output_dir: str, config: ConversionConfig) -> ConversionResult:
        """Convert the ONNX model into this converter's target format."""

    @abstractmethod
    def optimize(self, converted_path: str, config: ConversionConfig) -> OptimizationResult:
        """Apply the requested optimization (FP16/INT8) if supported for this format."""

    @abstractmethod
    def benchmark(self, converted_path: str, onnx_model_path: str, config: ConversionConfig) -> BenchmarkResult:
        """Run real inference benchmarks. Never invent numbers for metrics that can't be measured."""

    def cleanup(self, paths: list[str]) -> None:
        import os

        for path in paths:
            try:
                if path and os.path.exists(path) and os.path.isfile(path):
                    os.remove(path)
            except OSError:
                pass
