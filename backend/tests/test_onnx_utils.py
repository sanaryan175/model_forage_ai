import tempfile
from pathlib import Path

import pytest

from app.utils.onnx_utils import OnnxValidationError, inspect_and_validate_onnx
from tests.factories import make_invalid_onnx_bytes, make_valid_onnx_bytes


def _write_temp(contents: bytes) -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".onnx", delete=False)
    tmp.write(contents)
    tmp.close()
    return tmp.name


def test_inspect_and_validate_onnx_returns_shapes_and_names():
    path = _write_temp(make_valid_onnx_bytes(input_shape=[1, 3, 8, 8]))
    try:
        info = inspect_and_validate_onnx(path)
        assert info.input_names == ["input"]
        assert info.output_names == ["output"]
        assert info.input_shape == [1, 3, 8, 8]
    finally:
        Path(path).unlink()


def test_inspect_and_validate_onnx_rejects_garbage_file():
    path = _write_temp(make_invalid_onnx_bytes())
    try:
        with pytest.raises(OnnxValidationError):
            inspect_and_validate_onnx(path)
    finally:
        Path(path).unlink()
