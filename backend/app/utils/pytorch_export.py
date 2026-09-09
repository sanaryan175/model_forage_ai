"""Exports an uploaded PyTorch model to ONNX at conversion time.

Arbitrary `.pt` files saved via `torch.save(model.state_dict())` cannot be reconstructed
without the original model class, so this platform requires TorchScript (`torch.jit.save`)
for standalone `.pt` uploads — the same constraint most MLOps platforms impose. The
ml/export_onnx.py script exports straight from Python objects during training and is the
recommended path when you own the model code.
"""


class PyTorchExportError(ValueError):
    pass


def export_pytorch_to_onnx(pt_path: str, input_shape: list[int] | None, output_path: str) -> None:
    if not input_shape:
        raise PyTorchExportError(
            "Converting a PyTorch (.pt) model requires an input shape. "
            "Provide one in the conversion's advanced options (e.g. [1, 3, 224, 224])."
        )

    try:
        import torch
    except ImportError as exc:
        raise PyTorchExportError("The 'torch' package is not installed on the server") from exc

    try:
        model = torch.jit.load(pt_path, map_location="cpu")
    except Exception as exc:
        raise PyTorchExportError(
            "This .pt file is not a TorchScript module (torch.jit.save output). Raw "
            f"state_dict checkpoints cannot be converted without the original model class: {exc}"
        ) from exc

    model.eval()
    dummy_input = torch.randn(*input_shape)
    try:
        torch.onnx.export(
            model,
            dummy_input,
            output_path,
            input_names=["input"],
            output_names=["output"],
            opset_version=17,
            dynamo=False,
        )
    except Exception as exc:
        raise PyTorchExportError(f"torch.onnx.export failed: {exc}") from exc
