from typing import BinaryIO

from sqlalchemy.orm import Session

from app.models.model import Model, ModelFramework, ModelStatus
from app.repositories.model_repository import ModelRepository
from app.storage.factory import get_storage_provider
from app.utils.files import (
    InvalidFileError,
    generate_storage_key,
    new_model_id,
    sanitize_filename,
    validate_model_extension,
)
from app.utils.onnx_utils import OnnxValidationError, inspect_and_validate_onnx


class ModelUploadTooLargeError(ValueError):
    pass


class ModelService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ModelRepository(db)
        self.storage = get_storage_provider()

    def upload(
        self, user_id: str, name: str, filename: str, file: BinaryIO, size: int, max_size_bytes: int
    ) -> Model:
        if size > max_size_bytes:
            raise ModelUploadTooLargeError(
                f"File exceeds the maximum upload size of {max_size_bytes // (1024 * 1024)} MB"
            )
        ext = validate_model_extension(filename)  # raises InvalidFileError
        framework = ModelFramework.ONNX if ext == ".onnx" else ModelFramework.PYTORCH

        model_id = new_model_id()
        storage_key = generate_storage_key(user_id, model_id, "original", sanitize_filename(filename))
        self.storage.save(storage_key, file)

        model = Model(
            id=model_id,
            user_id=user_id,
            name=name,
            original_filename=sanitize_filename(filename),
            framework=framework,
            size=size,
            status=ModelStatus.VALIDATING,
            storage_path=storage_key,
        )
        model = self.repo.create(model)

        self._validate_uploaded_model(model)
        return model

    def _validate_uploaded_model(self, model: Model) -> None:
        if model.framework != ModelFramework.ONNX:
            # PyTorch models require an input shape (given at conversion time) before they
            # can be exported to ONNX and validated — see app/utils/pytorch_export.py.
            self._try_torchscript_load(model)
            return

        local_path = self.storage.open_path(model.storage_path)
        try:
            info = inspect_and_validate_onnx(local_path)
        except OnnxValidationError as exc:
            self.repo.update_status(model, ModelStatus.INVALID, error=str(exc))
            return

        model.input_shape = str(info.input_shape)
        model.output_shape = str(info.output_shape)
        model.input_names = ", ".join(info.input_names)
        model.output_names = ", ".join(info.output_names)
        self.repo.update_status(model, ModelStatus.READY)

    def _try_torchscript_load(self, model: Model) -> None:
        try:
            import torch
        except ImportError:
            self.repo.update_status(
                model, ModelStatus.INVALID, error="The 'torch' package is not installed on the server"
            )
            return

        local_path = self.storage.open_path(model.storage_path)
        try:
            torch.jit.load(local_path, map_location="cpu")
        except Exception as exc:
            self.repo.update_status(
                model,
                ModelStatus.INVALID,
                error=(
                    "This .pt file is not a TorchScript module (torch.jit.save output). "
                    f"Standalone .pt uploads must be TorchScript so the platform can load them "
                    f"without the original model class: {exc}"
                ),
            )
            return
        self.repo.update_status(model, ModelStatus.READY)

    def get(self, model_id: str) -> Model | None:
        return self.repo.get_by_id(model_id)

    def list_for_user(self, user_id: str, search: str | None, limit: int, offset: int) -> tuple[list[Model], int]:
        return self.repo.list_for_user(user_id, search=search, limit=limit, offset=offset)

    def delete(self, model: Model) -> None:
        self.storage.delete(model.storage_path)
        self.repo.delete(model)
