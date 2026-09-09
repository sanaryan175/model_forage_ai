import re
import uuid
from pathlib import PurePosixPath

ALLOWED_MODEL_EXTENSIONS = {".pt", ".onnx"}
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]")


class InvalidFileError(ValueError):
    pass


def sanitize_filename(filename: str) -> str:
    """Strip directory components and disallowed characters from a user-supplied filename."""
    name = PurePosixPath(filename).name
    name = _SAFE_NAME_RE.sub("_", name)
    if not name or name in {".", ".."}:
        raise InvalidFileError("Invalid filename")
    return name


def validate_model_extension(filename: str) -> str:
    safe_name = sanitize_filename(filename)
    ext = PurePosixPath(safe_name).suffix.lower()
    if ext not in ALLOWED_MODEL_EXTENSIONS:
        raise InvalidFileError(
            f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_MODEL_EXTENSIONS))}"
        )
    return ext


def generate_storage_key(user_id: str, model_id: str, subfolder: str, filename: str) -> str:
    """Build an S3-style key: models/{user_id}/{model_id}/{subfolder}/{filename}."""
    safe_name = sanitize_filename(filename)
    return f"models/{user_id}/{model_id}/{subfolder}/{safe_name}"


def new_model_id() -> str:
    return str(uuid.uuid4())
