from app.converters.base import ModelConverter
from app.converters.coreml import CoreMLConverter
from app.converters.tensorrt import TensorRTConverter
from app.converters.tflite import TFLiteConverter

_REGISTRY: dict[str, type[ModelConverter]] = {
    "tflite": TFLiteConverter,
    "tensorrt": TensorRTConverter,
    "coreml": CoreMLConverter,
}


def get_converter(format_name: str) -> ModelConverter:
    converter_cls = _REGISTRY.get(format_name)
    if converter_cls is None:
        raise ValueError(f"No converter registered for format '{format_name}'")
    return converter_cls()


def list_supported_formats() -> list[str]:
    return list(_REGISTRY.keys())
