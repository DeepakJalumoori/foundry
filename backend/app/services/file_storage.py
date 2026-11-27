from dataclasses import dataclass
from pathlib import Path
import uuid

from fastapi import UploadFile

PDF_MAGIC_BYTES = b"%PDF-"
DEFAULT_CHUNK_SIZE = 65536


class ResumeValidationError(Exception):
    """Raised when an uploaded resume fails validation."""

    status_code: int = 422

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


class ResumeTooLargeError(ResumeValidationError):
    """Raised when an uploaded resume exceeds the configured size limit."""

    status_code: int = 413


@dataclass(frozen=True, slots=True)
class StoredResume:
    """Metadata for a validated and locally stored resume PDF."""

    original_filename: str
    content_type: str | None
    size_bytes: int
    storage_key: str


def sanitize_pdf_filename(filename: str | None) -> str:
    """Extract a safe basename and verify the .pdf extension."""
    if not filename or not filename.strip():
        raise ResumeValidationError("INVALID_RESUME_FILENAME", "Resume filename is required.")

    basename = Path(filename).name.strip()
    if not basename or basename in {".", ".."}:
        raise ResumeValidationError("INVALID_RESUME_FILENAME", "Resume filename is invalid.")

    if not basename.lower().endswith(".pdf"):
        raise ResumeValidationError(
            "INVALID_RESUME_EXTENSION",
            "Only PDF files (.pdf) are supported.",
        )

    return basename[:255]


def validate_pdf_content_type(content_type: str | None) -> str | None:
    """Validate MIME type when supplied by the client."""
    if content_type is None or not content_type.strip():
        return None

    normalized = content_type.split(";", 1)[0].strip().lower()
    if normalized != "application/pdf":
        raise ResumeValidationError(
            "INVALID_RESUME_CONTENT_TYPE",
            "Resume content type must be application/pdf.",
        )
    return normalized


async def save_validated_pdf(
    upload: UploadFile,
    upload_dir: Path,
    max_size_bytes: int,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> StoredResume:
    """Stream-validate and persist an uploaded PDF under upload_dir."""
    original_filename = sanitize_pdf_filename(upload.filename)
    content_type = validate_pdf_content_type(upload.content_type)

    resolved_dir = upload_dir.resolve()
    resolved_dir.mkdir(parents=True, exist_ok=True)

    storage_key = f"{uuid.uuid4().hex}.pdf"
    target_path = (resolved_dir / storage_key).resolve()
    if target_path.parent != resolved_dir:
        raise ResumeValidationError("INVALID_STORAGE_PATH", "Invalid storage path.")

    total_bytes = 0
    header_buffer = bytearray()

    try:
        with target_path.open("xb") as out_file:
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break

                total_bytes += len(chunk)
                if total_bytes > max_size_bytes:
                    raise ResumeTooLargeError(
                        "RESUME_TOO_LARGE",
                        f"Resume PDF exceeds the maximum allowed size of {max_size_bytes // (1024 * 1024)} MB.",
                    )

                if len(header_buffer) < len(PDF_MAGIC_BYTES):
                    needed = len(PDF_MAGIC_BYTES) - len(header_buffer)
                    header_buffer.extend(chunk[:needed])
                    if len(header_buffer) == len(PDF_MAGIC_BYTES) and bytes(header_buffer) != PDF_MAGIC_BYTES:
                        raise ResumeValidationError(
                            "INVALID_PDF_MAGIC_BYTES",
                            "Uploaded file is not a valid PDF document.",
                        )

                out_file.write(chunk)

        if total_bytes == 0:
            raise ResumeValidationError("EMPTY_RESUME_FILE", "Uploaded PDF file is empty.")

        if bytes(header_buffer) != PDF_MAGIC_BYTES:
            raise ResumeValidationError(
                "INVALID_PDF_MAGIC_BYTES",
                "Uploaded file is not a valid PDF document.",
            )
    except Exception:
        target_path.unlink(missing_ok=True)
        raise

    return StoredResume(
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=total_bytes,
        storage_key=storage_key,
    )


def delete_stored_file(upload_dir: Path, storage_key: str) -> None:
    """Remove a previously stored file by its opaque storage key."""
    safe_key = Path(storage_key).name
    if not safe_key:
        return
    resolved_dir = upload_dir.resolve()
    target_path = (resolved_dir / safe_key).resolve()
    if target_path.parent == resolved_dir:
        target_path.unlink(missing_ok=True)
