"""Export the teammate-trained ResNet-18 (CIFAR-10, 224x224) state_dict to ONNX.

The platform can't rebuild a raw state_dict without the model class, so we rebuild it
here with torchvision and upload the resulting .onnx instead.

    python export_resnet18_onnx.py
"""

import argparse
from pathlib import Path

import torch
from torchvision.models import resnet18

CHECKPOINT_DIR = Path(__file__).parent / "checkpoints"


def export(checkpoint_path: Path, output_path: Path) -> None:
    model = resnet18(num_classes=10)
    model.load_state_dict(torch.load(checkpoint_path, map_location="cpu", weights_only=True))
    model.eval()

    torch.onnx.export(
        model,
        torch.randn(1, 3, 224, 224),
        str(output_path),
        input_names=["input"],
        output_names=["output"],
        opset_version=17,
        dynamo=False,
    )
    print(f"Exported ONNX model to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", default=str(CHECKPOINT_DIR / "best_resnet18_cifar10.pth"))
    parser.add_argument("--output", default=str(CHECKPOINT_DIR / "resnet18_cifar10.onnx"))
    args = parser.parse_args()
    export(Path(args.checkpoint), Path(args.output))
