"""
OCR service backed by EasyOCR.

EasyOCR is loaded lazily on first use so the server starts quickly.
The reader is module-level once loaded — EasyOCR is not thread-safe for concurrent
reads on the same Reader object, but that is acceptable for the MVP's serial SQLite workload.
"""

import io
import logging
import os
import uuid
from pathlib import Path

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB

UPLOAD_DIR = Path(os.getenv("IMAGE_UPLOAD_DIR", "uploads"))
UPLOAD_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

_ocr_reader = None


def _get_reader():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        _ocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _ocr_reader


def validate_image(filename: str, content_type: str, size: int) -> None:
    """Raises ValueError with a user-facing message if the image is not acceptable."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}")
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported content type '{content_type}'.")
    if size > MAX_FILE_BYTES:
        raise ValueError(f"Image exceeds maximum allowed size of {MAX_FILE_BYTES // (1024 * 1024)} MB.")


def save_image(data: bytes, original_filename: str) -> str:
    """Persists the image bytes to UPLOAD_DIR and returns the relative file path."""
    ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest = UPLOAD_DIR / unique_name
    dest.write_bytes(data)
    return str(dest)


def run_ocr(image_bytes: bytes) -> dict:
    """
    Runs EasyOCR on raw image bytes.
    Returns {"ocr_text": str | None, "ocr_confidence": float | None}.
    ocr_text is None when no text is detected — this is not an error.
    """
    try:
        reader = _get_reader()
        results = reader.readtext(image_bytes)
    except Exception as exc:
        logger.warning("OCR processing failed: %s", exc)
        return {"ocr_text": None, "ocr_confidence": None}

    if not results:
        return {"ocr_text": None, "ocr_confidence": None}

    texts = [text for (_, text, _) in results if text.strip()]
    confidences = [conf for (_, _, conf) in results if conf is not None]

    if not texts:
        return {"ocr_text": None, "ocr_confidence": None}

    return {
        "ocr_text": "\n".join(texts),
        "ocr_confidence": round(sum(confidences) / len(confidences) * 100, 1),
    }


def build_combined_context(complaint_text: str, ocr_text: str | None) -> str:
    """
    Merges user complaint text with OCR-extracted text into a single context string
    for the JEV/RLCD pipeline. Falls back to complaint_text when OCR yielded nothing.
    """
    if not ocr_text or not ocr_text.strip():
        return complaint_text

    return (
        f"User complaint:\n{complaint_text}\n\n"
        f"Information extracted from attached image:\n{ocr_text}"
    )
