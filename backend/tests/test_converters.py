import pytest

from app.converters.registry import get_converter, list_supported_formats
from app.converters.tensorrt import TensorRTConverter


def test_registry_lists_all_three_formats():
    assert set(list_supported_formats()) == {"tflite", "tensorrt", "coreml"}


@pytest.mark.parametrize("format_name", ["tflite", "tensorrt", "coreml"])
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
