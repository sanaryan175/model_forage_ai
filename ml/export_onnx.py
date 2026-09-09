"""Export the trained TorchScript checkpoint to ONNX.

    python export_onnx.py
"""

import argparse
from pathlib import Path

import torch

from dataset import IMAGE_SIZE, NUM_CHANNELS

CHECKPOINT_DIR = Path(__file__).parent / "checkpoints"


def export(checkpoint_path: Path, output_path: Path, batch_size: int) -> None:
    model = torch.jit.load(str(checkpoint_path), map_location="cpu")
    model.eval()

    dummy_input = torch.randn(batch_size, NUM_CHANNELS, IMAGE_SIZE, IMAGE_SIZE)
    torch.onnx.export(
        model,
        dummy_input,
        str(output_path),
        input_names=["input"],
        output_names=["output"],
        opset_version=17,
        dynamo=False,
    )
    print(f"Exported ONNX model to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default=str(CHECKPOINT_DIR / "best_model.pt"))
    parser.add_argument("--output", default=str(CHECKPOINT_DIR / "model.onnx"))
    parser.add_argument("--batch-size", type=int, default=1)
    args = parser.parse_args()
    export(Path(args.checkpoint), Path(args.output), args.batch_size)
