"""Standalone ONNX validation: graph check, shape/name inspection, and a real inference
smoke test. Mirrors the checks ModelForge's upload endpoint performs
(backend/app/utils/onnx_utils.py), reimplemented here so ml/ has no dependency on the
backend package.

    python validate_onnx.py
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort

CHECKPOINT_DIR = Path(__file__).parent / "checkpoints"


def validate(onnx_path: Path) -> bool:
    print(f"Loading {onnx_path}")
    model = onnx.load(str(onnx_path))

    print("Checking graph validity...")
    onnx.checker.check_model(model)

    input_info = model.graph.input[0]
    output_info = model.graph.output[0]
    input_shape = [d.dim_value or 1 for d in input_info.type.tensor_type.shape.dim]
    output_shape = [d.dim_value or 1 for d in output_info.type.tensor_type.shape.dim]
    print(f"Input:  name={input_info.name!r}  shape={input_shape}")
    print(f"Output: name={output_info.name!r}  shape={output_shape}")

    print("Running ONNX Runtime inference smoke test...")
    session = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    dummy_input = np.random.default_rng(0).standard_normal(input_shape).astype(np.float32)
    outputs = session.run([output_info.name], {input_info.name: dummy_input})

    print(f"Inference succeeded. Output shape: {outputs[0].shape}")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--onnx-path", default=str(CHECKPOINT_DIR / "model.onnx"))
    args = parser.parse_args()
    try:
        validate(Path(args.onnx_path))
        print("VALID")
    except Exception as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        sys.exit(1)
