"""ONNX inspection and validation helpers, shared by the upload pipeline and every converter.

Implements the validation checklist from the spec: graph validity, input/output names and
shapes, and an actual ONNX Runtime inference test (not just a schema check).
"""

from dataclasses import dataclass

import numpy as np


class OnnxValidationError(ValueError):
    pass


@dataclass
class OnnxModelInfo:
    input_names: list[str]
    output_names: list[str]
    input_shape: list[int]
    output_shape: list[int]


def _resolve_dynamic_dims(shape: list) -> list[int]:
    """Replace dynamic axes (None / string symbols, e.g. batch size) with 1 for benchmarking."""
    return [dim if isinstance(dim, int) and dim > 0 else 1 for dim in shape]


def inspect_and_validate_onnx(model_path: str) -> OnnxModelInfo:
    """Load an ONNX model, validate its graph, and run a real inference smoke test.

    Raises OnnxValidationError with a specific, actionable message on any failure.
    """
    try:
        import onnx
    except ImportError as exc:
        raise OnnxValidationError("The 'onnx' package is not installed on the server") from exc

    try:
        model = onnx.load(model_path)
    except Exception as exc:
        raise OnnxValidationError(f"Model file could not be loaded as ONNX: {exc}") from exc

    try:
        onnx.checker.check_model(model)
    except Exception as exc:
        raise OnnxValidationError(f"ONNX graph is invalid: {exc}") from exc

    graph_inputs = [i for i in model.graph.input if i.name not in {init.name for init in model.graph.initializer}]
    if not graph_inputs:
        raise OnnxValidationError("Model graph has no external inputs")
    if not model.graph.output:
        raise OnnxValidationError("Model graph has no outputs")

    input_names = [i.name for i in graph_inputs]
    output_names = [o.name for o in model.graph.output]
    input_shape = _resolve_dynamic_dims([d.dim_value or d.dim_param for d in graph_inputs[0].type.tensor_type.shape.dim])
    output_shape = _resolve_dynamic_dims(
        [d.dim_value or d.dim_param for d in model.graph.output[0].type.tensor_type.shape.dim]
    )

    try:
        import onnxruntime as ort
    except ImportError as exc:
        raise OnnxValidationError("The 'onnxruntime' package is not installed on the server") from exc

    try:
        session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        dummy_input = np.random.default_rng(0).standard_normal(input_shape).astype(np.float32)
        session.run(output_names, {input_names[0]: dummy_input})
    except Exception as exc:
        raise OnnxValidationError(f"ONNX Runtime inference test failed (operator incompatibility?): {exc}") from exc

    return OnnxModelInfo(
        input_names=input_names,
        output_names=output_names,
        input_shape=input_shape,
        output_shape=output_shape,
    )


def run_onnx_inference(model_path: str, inputs: list[np.ndarray]) -> list[np.ndarray]:
    import onnxruntime as ort

    session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
    input_name = session.get_inputs()[0].name
    output_name = session.get_outputs()[0].name
    return [session.run([output_name], {input_name: sample})[0] for sample in inputs]
