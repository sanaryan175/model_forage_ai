"""Small helpers for building real, valid test fixtures — never mocked-out fakes."""

import io

import onnx
from onnx import TensorProto, helper


def make_valid_onnx_bytes(input_shape: list[int] | None = None) -> bytes:
    shape = input_shape or [1, 3, 4, 4]
    input_tensor = helper.make_tensor_value_info("input", TensorProto.FLOAT, shape)
    output_tensor = helper.make_tensor_value_info("output", TensorProto.FLOAT, shape)
    node = helper.make_node("Relu", ["input"], ["output"])
    graph = helper.make_graph([node], "test-graph", [input_tensor], [output_tensor])
    model = helper.make_model(graph, producer_name="modelforge-test", opset_imports=[helper.make_opsetid("", 17)])
    model.ir_version = 9
    onnx.checker.check_model(model)

    buffer = io.BytesIO()
    buffer.write(model.SerializeToString())
    return buffer.getvalue()


def make_invalid_onnx_bytes() -> bytes:
    return b"this is not a valid onnx file"
