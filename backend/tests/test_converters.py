import pytest

from app.converters.registry import get_converter, list_supported_formats
from app.converters.tensorrt import TensorRTConverter


def test_registry_lists_all_formats():
    assert set(list_supported_formats()) == {"tflite", "tensorrt", "coreml", "onnx"}


@pytest.mark.parametrize("format_name", ["tflite", "tensorrt", "coreml", "onnx"])
def test_get_converter_returns_matching_type(format_name):
    converter = get_converter(format_name)
    assert converter.format_name == format_name


def test_get_converter_raises_for_unknown_format():
    with pytest.raises(ValueError):
        get_converter("not-a-real-format")


def test_tensorrt_reports_unsupported_without_gpu():
    """CI runners and most developer laptops have no NVIDIA GPU/CUDA/TensorRT SDK.
    The converter must say so explicitly rather than attempting (and silently faking)
    a conversion.
    """
    supported, reason = TensorRTConverter().is_supported()
    if not supported:
        assert reason  # a real, human-readable explanation must be present
    # If this ever runs on a GPU-equipped CI runner with TensorRT installed, supported
    # may legitimately be True — that's fine, we just never assert a fake negative.


def test_every_converter_is_supported_check_returns_a_reason_when_false():
    for format_name in list_supported_formats():
        converter = get_converter(format_name)
        supported, reason = converter.is_supported()
        if not supported:
            assert isinstance(reason, str) and len(reason) > 0


@pytest.mark.skipif(not TensorRTConverter().is_supported()[0], reason="needs an NVIDIA GPU with TensorRT")
@pytest.mark.parametrize("optimization", ["fp32", "fp16"])
def test_tensorrt_builds_and_benchmarks_a_real_engine(tmp_path, optimization):
    from app.converters.base import ConversionConfig
    from tests.factories import make_valid_onnx_bytes

    onnx_path = tmp_path / "model.onnx"
    onnx_path.write_bytes(make_valid_onnx_bytes())
    converter = TensorRTConverter()
    config = ConversionConfig(optimization=optimization)

    result = converter.convert(str(onnx_path), str(tmp_path / "out"), config)
    assert result.success, result.error
    assert result.output_path.endswith(f"_{optimization}.engine")
    assert converter.optimize(result.output_path, config).applied

    bench = converter.benchmark(result.output_path, str(onnx_path), config)
    assert bench.latency_mean_ms > 0
    assert bench.fidelity_pct == 100.0
    assert bench.device.startswith("cuda")


def test_tensorrt_int8_fails_early_with_a_reason(tmp_path):
    from app.converters.base import ConversionConfig

    result = TensorRTConverter().convert("unused.onnx", str(tmp_path), ConversionConfig(optimization="int8"))
    assert not result.success and result.error


@pytest.mark.skipif(not get_converter("tflite").is_supported()[0], reason="needs tensorflow + onnx2tf")
def test_tflite_fidelity_handles_channels_last_outputs(tmp_path):
    # onnx2tf turns a 4D NCHW output into NHWC; fidelity must compare the same elements.
    from app.converters.base import ConversionConfig
    from tests.factories import make_valid_onnx_bytes

    onnx_path = tmp_path / "model.onnx"
    onnx_path.write_bytes(make_valid_onnx_bytes([1, 3, 32, 32]))
    converter = get_converter("tflite")
    config = ConversionConfig(optimization="fp32")

    result = converter.convert(str(onnx_path), str(tmp_path / "out"), config)
    assert result.success, result.error
    assert converter.benchmark(result.output_path, str(onnx_path), config).fidelity_pct == 100.0
