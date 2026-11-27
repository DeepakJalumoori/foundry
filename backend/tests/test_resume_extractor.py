from pathlib import Path

import pymupdf
import pytest

from app.services.resume_extractor import ResumeExtractionError, extract_resume_text


def _create_text_pdf(target: Path, pages_text: list[str]) -> None:
    doc = pymupdf.open()
    for text in pages_text:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(target)
    doc.close()


def test_extract_valid_single_page_pdf(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    _create_text_pdf(
        upload_dir / "valid.pdf",
        ["Alex Mercer\n\nSenior   Backend   Engineer\nPython   FastAPI   SQLite"],
    )

    result = extract_resume_text(upload_dir, "valid.pdf")
    assert result.status == "extracted"
    assert result.page_count == 1
    assert len(result.pages) == 1
    assert result.pages[0].page_number == 1
    assert "Alex Mercer" in result.extracted_text
    assert "Senior Backend Engineer" in result.extracted_text
    assert "[Page 1]" in result.extracted_text
    assert result.warnings == []


def test_extract_multi_page_pdf_preserves_page_numbers(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    _create_text_pdf(
        upload_dir / "multi.pdf",
        [
            "Page one candidate summary with Python experience",
            "Page two project details with FastAPI and PostgreSQL",
        ],
    )

    result = extract_resume_text(upload_dir, "multi.pdf")
    assert result.status == "extracted"
    assert result.page_count == 2
    assert result.pages[0].page_number == 1
    assert result.pages[1].page_number == 2
    assert "[Page 1]" in result.extracted_text
    assert "[Page 2]" in result.extracted_text
    assert "Page one candidate summary" in result.pages[0].text
    assert "Page two project details" in result.pages[1].text


def test_extract_image_only_pdf_marked_requires_manual_review(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    doc = pymupdf.open()
    doc.new_page()
    doc.save(upload_dir / "scanned.pdf")
    doc.close()

    result = extract_resume_text(upload_dir, "scanned.pdf")
    assert result.status == "requires_manual_review"
    assert result.page_count == 1
    assert result.extracted_text == ""
    assert any("OCR or manual review" in w for w in result.warnings)


def test_extract_empty_zero_page_pdf_raises(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    # A minimal PDF with an empty /Pages /Count 0
    (upload_dir / "zero.pdf").write_bytes(
        b"%PDF-1.4\n1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n"
        b"2 0 obj<< /Type /Pages /Kids [] /Count 0 >>endobj\n"
        b"xref\n0 3\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
        b"trailer<< /Size 3 /Root 1 0 R >>\nstartxref\n110\n%%EOF\n"
    )

    with pytest.raises(ResumeExtractionError) as exc_info:
        extract_resume_text(upload_dir, "zero.pdf")
    assert exc_info.value.code in {"EMPTY_PDF_DOCUMENT", "INVALID_OR_CORRUPTED_PDF"}


def test_extract_corrupted_pdf_raises(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    (upload_dir / "corrupt.pdf").write_bytes(b"%PDF-1.4\nnot-valid-pdf-objects")

    with pytest.raises(ResumeExtractionError) as exc_info:
        extract_resume_text(upload_dir, "corrupt.pdf")
    assert exc_info.value.code == "INVALID_OR_CORRUPTED_PDF"


def test_extract_encrypted_pdf_raises(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Secret resume content")
    doc.save(
        upload_dir / "encrypted.pdf",
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        owner_pw="owner-secret",
        user_pw="user-secret",
    )
    doc.close()

    with pytest.raises(ResumeExtractionError) as exc_info:
        extract_resume_text(upload_dir, "encrypted.pdf")
    assert exc_info.value.code == "ENCRYPTED_PDF"


def test_extract_missing_file_raises_404(tmp_path: Path) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    with pytest.raises(ResumeExtractionError) as exc_info:
        extract_resume_text(upload_dir, "does_not_exist.pdf")
    assert exc_info.value.code == "RESUME_FILE_MISSING"
    assert exc_info.value.status_code == 404


@pytest.mark.parametrize(
    "bad_key",
    [
        "",
        "   ",
        ".",
        "..",
        "../secret.pdf",
        "..\\secret.pdf",
        "subdir/resume.pdf",
        "C:\\Windows\\System32\\drivers\\etc\\hosts",
    ],
)
def test_extract_rejects_invalid_keys_and_path_traversal(tmp_path: Path, bad_key: str) -> None:
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()

    with pytest.raises(ResumeExtractionError) as exc_info:
        extract_resume_text(upload_dir, bad_key)
    assert exc_info.value.code == "INVALID_STORAGE_KEY"
