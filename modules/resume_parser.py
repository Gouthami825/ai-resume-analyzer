"""Extract plain text from PDF and DOCX resume uploads."""

from __future__ import annotations

import io
from typing import BinaryIO

from docx import Document
from pypdf import PdfReader


class ResumeParseError(Exception):
    """Raised when resume text cannot be extracted."""


ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_FILE_SIZE_MB = 10


def _validate_upload(filename: str | None, file_bytes: bytes) -> None:
    if not filename:
        raise ResumeParseError("No file name provided.")

    name_lower = filename.lower()
    if not any(name_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise ResumeParseError(
            f"Unsupported file type. Please upload a PDF or DOCX file "
            f"(allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))})."
        )

    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ResumeParseError(
            f"File is too large ({size_mb:.1f} MB). Maximum size is {MAX_FILE_SIZE_MB} MB."
        )

    if len(file_bytes) < 50:
        raise ResumeParseError("File appears empty or corrupted.")


def extract_text_from_pdf(source: BinaryIO) -> str:
    """Read all pages from a PDF and return joined text."""
    try:
        reader = PdfReader(source)
    except Exception as exc:
        raise ResumeParseError(f"Could not read PDF: {exc}") from exc

    if reader.is_encrypted:
        raise ResumeParseError(
            "This PDF is password-protected. Please export an unprotected copy."
        )

    parts: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            parts.append(text)

    if not parts:
        raise ResumeParseError(
            "No text could be extracted from the PDF. "
            "Scanned image-only PDFs may need OCR (not included in this app)."
        )

    return "\n".join(parts)


def extract_text_from_docx(source: BinaryIO) -> str:
    """Read paragraphs from a DOCX file."""
    try:
        document = Document(source)
    except Exception as exc:
        raise ResumeParseError(f"Could not read DOCX: {exc}") from exc

    paragraphs = [p.text.strip() for p in document.paragraphs if p.text.strip()]
    # Include text from tables (common in resume templates)
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    paragraphs.append(cell.text.strip())

    if not paragraphs:
        raise ResumeParseError("No text found in the DOCX document.")

    return "\n".join(paragraphs)


def extract_text_from_upload(filename: str | None, file_bytes: bytes) -> str:
    """
    Main entry: validate upload and return resume text.

    Args:
        filename: Original file name (used to detect PDF vs DOCX).
        file_bytes: Raw file content.

    Returns:
        Extracted plain text.
    """
    _validate_upload(filename, file_bytes)
    buffer = io.BytesIO(file_bytes)
    name_lower = (filename or "").lower()

    if name_lower.endswith(".pdf"):
        return extract_text_from_pdf(buffer)
    if name_lower.endswith(".docx"):
        return extract_text_from_docx(buffer)

    raise ResumeParseError("Unsupported file format.")
