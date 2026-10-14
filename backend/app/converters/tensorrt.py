import importlib.util
import os

import numpy as np

from app.benchmark.engine import generate_synthetic_inputs, measure_file_size, timed_inference_stats, top1_agreement_pct
from app.converters.base import BenchmarkResult, ConversionConfig, ConversionResult, ModelConverter, OptimizationResult
from app.utils.onnx_utils import inspect_and_validate_onnx, run_onnx_inference

_ALL_METRICS = [
    "latency_mean_ms",
    "latency_median_ms",
    "latency_p95_ms",
    "throughput_ips",
    "fidelity_pct",
]


def _cuda_check(result):
    """cuda-python returns (error, *values); raise on error, return the value(s)."""
    from cuda.bindings import runtime as cudart

    err, *values = result if isinstance(result, tuple) else (result,)
    if err != cudart.cudaError_t.cudaSuccess:
        raise RuntimeError(f"CUDA error: {err}")
    return values[0] if len(values) == 1 else values


class _EngineRunner:
    """Runs a serialized TensorRT engine on the GPU: one input, one output, fixed shapes."""

    def __init__(self, engine_path: str):
        import tensorrt as trt
        from cuda.bindings import runtime as cudart

        self._cudart = cudart
        self._trt_logger = trt.Logger(trt.Logger.WARNING)
        self._runtime = trt.Runtime(self._trt_logger)  # must outlive the engine
        with open(engine_path, "rb") as f:
            self.engine = self._runtime.deserialize_cuda_engine(f.read())
        self.context = self.engine.create_execution_context()

        names = [self.engine.get_tensor_name(i) for i in range(self.engine.num_io_tensors)]
        self.input_name = next(n for n in names if self.engine.get_tensor_mode(n) == trt.TensorIOMode.INPUT)
        output_name = next(n for n in names if self.engine.get_tensor_mode(n) == trt.TensorIOMode.OUTPUT)
        self.input_shape = list(self.engine.get_tensor_shape(self.input_name))
        self.input_dtype = trt.nptype(self.engine.get_tensor_dtype(self.input_name))
        self._output = np.empty(
            tuple(self.engine.get_tensor_shape(output_name)), dtype=trt.nptype(self.engine.get_tensor_dtype(output_name))
        )
        input_bytes = int(np.prod(self.input_shape)) * np.dtype(self.input_dtype).itemsize

        self._d_input = _cuda_check(cudart.cudaMalloc(input_bytes))
        self._d_output = _cuda_check(cudart.cudaMalloc(self._output.nbytes))
        self._stream = _cuda_check(cudart.cudaStreamCreate())
        self.context.set_tensor_address(self.input_name, self._d_input)
        self.context.set_tensor_address(output_name, self._d_output)

    def run(self, sample: np.ndarray) -> np.ndarray:
        cudart = self._cudart
        sample = np.ascontiguousarray(sample, dtype=self.input_dtype)
        _cuda_check(cudart.cudaMemcpyAsync(
            self._d_input, sample.ctypes.data, sample.nbytes, cudart.cudaMemcpyKind.cudaMemcpyHostToDevice, self._stream
        ))
        self.context.execute_async_v3(self._stream)
        _cuda_check(cudart.cudaMemcpyAsync(
            self._output.ctypes.data, self._d_output, self._output.nbytes,
            cudart.cudaMemcpyKind.cudaMemcpyDeviceToHost, self._stream,
        ))
        _cuda_check(cudart.cudaStreamSynchronize(self._stream))
        return self._output.copy()

    def close(self) -> None:
        self._cudart.cudaFree(self._d_input)
        self._cudart.cudaFree(self._d_output)
        self._cudart.cudaStreamDestroy(self._stream)


class TensorRTConverter(ModelConverter):
    """Builds a TensorRT engine from an ONNX model and benchmarks it on the local NVIDIA GPU.

    TensorRT 10+ networks are strongly typed: precision comes from the model's own data
    types, not from builder flags. So FP16 = convert the ONNX graph to float16 first, then
    build. Engines only run on the GPU model + TensorRT version they were built with.
    """

    format_name = "tensorrt"

    def is_supported(self) -> tuple[bool, str | None]:
        if importlib.util.find_spec("tensorrt") is None:
            return False, "The 'tensorrt' Python package (NVIDIA TensorRT SDK) is not installed"
        if importlib.util.find_spec("cuda") is None:
            return False, "The 'cuda-python' package is not installed (needed to run engines on the GPU)"
        try:
            from cuda.bindings import runtime as cudart

            if _cuda_check(cudart.cudaGetDeviceCount()) < 1:
                return False, "No NVIDIA CUDA GPU was detected on this machine"
        except Exception as exc:
            return False, f"No usable NVIDIA CUDA GPU: {exc}"
        return True, None

    def validate(self, onnx_model_path: str, config: ConversionConfig) -> None:
        inspect_and_validate_onnx(onnx_model_path)

    def convert(self, onnx_model_path: str, output_dir: str, config: ConversionConfig) -> ConversionResult:
        supported, reason = self.is_supported()
        if not supported:
            message = (
                f"TensorRT conversion skipped: {reason}. TensorRT engines can only be built on a host "
                "with an NVIDIA GPU, a recent driver, and the 'tensorrt' + 'cuda-python' packages."
            )
            return ConversionResult(success=False, error=message, is_environment_limited=True, logs=[message])
        if config.optimization == "int8":
            # Fail before the slow build: INT8 needs calibration data the platform doesn't collect yet.
            return ConversionResult(
                success=False, error="INT8 TensorRT engines need a calibration dataset, which this platform does not collect yet"
            )

        import tensorrt as trt

        os.makedirs(output_dir, exist_ok=True)
        logs: list[str] = []
        source_path = onnx_model_path
        if config.optimization == "fp16":
            import onnx
            from onnxruntime.transformers.float16 import convert_float_to_float16

            source_path = os.path.join(output_dir, "model_fp16.onnx")
            # keep_io_types: the engine still takes/returns float32, so callers don't change.
            onnx.save(convert_float_to_float16(onnx.load(onnx_model_path), keep_io_types=True), source_path)
            logs.append("Converted ONNX weights and activations to float16")

        logger = trt.Logger(trt.Logger.WARNING)
        builder = trt.Builder(logger)
        network = builder.create_network(0)
        parser = trt.OnnxParser(network, logger)
        with open(source_path, "rb") as f:
            if not parser.parse(f.read()):
                errors = "; ".join(str(parser.get_error(i)) for i in range(parser.num_errors))
                return ConversionResult(success=False, error=f"TensorRT ONNX parsing failed: {errors}", logs=logs)

        build_config = builder.create_builder_config()
        # ponytail: 1 GB workspace fits a 4 GB laptop GPU; raise it for big models on bigger cards.
        build_config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 30)

        # Dynamic dims (e.g. batch = -1) need an optimization profile; build for size 1, like the benchmarks.
        model_input = network.get_input(0)
        if any(d < 0 for d in model_input.shape):
            fixed = [d if d > 0 else 1 for d in model_input.shape]
            profile = builder.create_optimization_profile()
            profile.set_shape(model_input.name, fixed, fixed, fixed)
            build_config.add_optimization_profile(profile)
            logs.append(f"Dynamic input shape resolved to {fixed}")

        serialized_engine = builder.build_serialized_network(network, build_config)
        if serialized_engine is None:
            return ConversionResult(success=False, error="TensorRT engine build failed (see server log)", logs=logs)

        stem = os.path.splitext(os.path.basename(onnx_model_path))[0]
        output_path = os.path.join(output_dir, f"{stem}_{config.optimization}.engine")
        with open(output_path, "wb") as f:
            f.write(serialized_engine)
        logs.append(f"Built TensorRT {config.optimization.upper()} engine")
        return ConversionResult(success=True, output_path=output_path, logs=logs)

    def optimize(self, converted_path: str, config: ConversionConfig) -> OptimizationResult:
        if config.optimization in ("fp32", "fp16"):
            # Already applied in convert(): precision is baked into the engine at build time.
            return OptimizationResult(applied=True, optimization=config.optimization)
        return OptimizationResult(
            applied=False, optimization=config.optimization, note="INT8 needs a calibration dataset"
        )

    def benchmark(self, converted_path: str, onnx_model_path: str, config: ConversionConfig) -> BenchmarkResult:
        supported, _ = self.is_supported()
        if not supported:
            return BenchmarkResult(device="nvidia-gpu (unavailable)", unsupported_metrics=list(_ALL_METRICS))

        from cuda.bindings import runtime as cudart

        gpu_name = _cuda_check(cudart.cudaGetDeviceProperties(0)).name.decode(errors="ignore").strip("\x00")
        runner = _EngineRunner(converted_path)
        try:
            inputs = generate_synthetic_inputs(runner.input_shape, count=20)
            stats = timed_inference_stats(lambda: runner.run(inputs[0]), iterations=50)
            engine_outputs = [runner.run(sample) for sample in inputs]
        finally:
            runner.close()

        fidelity = top1_agreement_pct(run_onnx_inference(onnx_model_path, inputs), engine_outputs)
        return BenchmarkResult(
            model_size_bytes=measure_file_size(converted_path),
            latency_mean_ms=stats["mean_ms"],
            latency_median_ms=stats["median_ms"],
            latency_p95_ms=stats["p95_ms"],
            throughput_ips=stats["throughput_ips"],
            fidelity_pct=fidelity,
            device=f"cuda ({gpu_name})",
        )
