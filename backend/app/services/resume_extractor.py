from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Literal

import pymupdf

ExtractionStatus = Literal["extracted", "requires_manual_review", "failed"]

MIN_MEANINGFUL_TEXT_CHARS = 20


class ResumeExtractionError(Exception):
    """Raised when a stored PDF resume cannot be safely resolved or read."""

    def __init__(self, code: str, detail: str, status_code: int = 422) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class ExtractedPage:
    """Extracted and normalized text for a single PDF page (1-based)."""

    page_number: int
    text: str


@dataclass(frozen=True, slots=True)
class ResumeExtractionResult:
    """Structured result of PDF text extraction."""

    extracted_text: str
    page_count: int
    pages: list[ExtractedPage]
    status: ExtractionStatus
    warnings: list[str] = field(default_factory=list)


def resolve_stored_resume_path(upload_dir: Path, storage_key: str) -> Path:
    """Safely resolve a stored resume key inside the configured upload directory."""
    if not storage_key or not storage_key.strip():
        raise ResumeExtractionError("INVALID_STORAGE_KEY", "Resume storage key is required.")

    cleaned_key = storage_key.strip()
    if "/" in cleaned_key or "\\" in cleaned_key or ".." in cleaned_key:
        raise ResumeExtractionError("INVALID_STORAGE_KEY", "Resume storage key is invalid.")

    if Path(cleaned_key).name != cleaned_key or cleaned_key in {".", ".."}:
        raise ResumeExtractionError("INVALID_STORAGE_KEY", "Resume storage key is invalid.")

    resolved_dir = upload_dir.resolve()
    target_path = (resolved_dir / cleaned_key).resolve()

    if target_path.parent != resolved_dir or not target_path.is_relative_to(resolved_dir):
        raise ResumeExtractionError("INVALID_STORAGE_PATH", "Resolved resume path is outside upload directory.")

    if not target_path.exists() or not target_path.is_file():
        raise ResumeExtractionError(
            "RESUME_FILE_MISSING",
            "Stored resume file could not be found.",
            status_code=404,
        )

    return target_path


def _normalize_page_text(raw_text: str) -> str:
    """Normalize excessive whitespace while preserving line and paragraph boundaries."""
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in normalized.split("\n")]
    joined = "\n".join(lines)
    joined = re.sub(r"\n{3,}", "\n\n", joined)
    return joined.strip()


def extract_resume_text(upload_dir: Path, storage_key: str) -> ResumeExtractionResult:
    """Extract page-numbered text from a stored PDF resume using PyMuPDF."""
    pdf_path = resolve_stored_resume_path(upload_dir, storage_key)

    try:
        doc = pymupdf.open(pdf_path)
    except Exception as exc:
        raise ResumeExtractionError(
            "INVALID_OR_CORRUPTED_PDF",
            "Stored resume could not be opened as a valid PDF document.",
        ) from exc

    try:
        if getattr(doc, "is_encrypted", False) or getattr(doc, "needs_pass", False):
            raise ResumeExtractionError(
                "ENCRYPTED_PDF",
                "Encrypted or password-protected PDFs are not supported.",
            )

        page_count = doc.page_count
        if page_count == 0:
            raise ResumeExtractionError(
                "EMPTY_PDF_DOCUMENT",
                "The PDF document contains zero pages.",
            )

        pages: list[ExtractedPage] = []
        warnings: list[str] = []

        for idx in range(page_count):
            page = doc.load_page(idx)
            raw_text = page.get_text("text") or ""
            cleaned = _normalize_page_text(raw_text)
            pages.append(ExtractedPage(page_number=idx + 1, text=cleaned))
            if not cleaned:
                warnings.append(f"Page {idx + 1} contains no extractable text.")

        non_empty_pages = [p for p in pages if p.text]
        total_non_whitespace = sum(len(re.sub(r"\s+", "", p.text)) for p in non_empty_pages)

        if total_non_whitespace < MIN_MEANINGFUL_TEXT_CHARS:
            return ResumeExtractionResult(
                extracted_text="",
                page_count=page_count,
                pages=pages,
                status="requires_manual_review",
                warnings=[
                    "No meaningful text could be extracted from this PDF. "
                    "It appears to be scanned or image-only and requires OCR or manual review."
                ],
            )

        combined_text = "\n\n".join(f"[Page {p.page_number}]\n{p.text}" for p in non_empty_pages)

        return ResumeExtractionResult(
            extracted_text=combined_text,
            page_count=page_count,
            pages=pages,
            status="extracted",
            warnings=warnings,
        )
    except ResumeExtractionError:
        raise
    except Exception as exc:
        raise ResumeExtractionError(
            "PDF_EXTRACTION_FAILED",
            "Failed to extract text from the stored PDF resume.",
        ) from exc
    finally:
        doc.close()
