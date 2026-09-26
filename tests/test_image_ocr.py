"""
Backend tests for the OCR/image extension.
Run: uv run pytest tests/ -v

Engine/session setup is in conftest.py.

Tests:
  1. Text-only complaint — existing pipeline, no regression
  2. Image with text — OCR extracts text, combined context reaches JEV
  3. Image with no text — complaint processes normally with ocr_text=None
  4. Invalid image type/size — 400 error, no crash
  5. OCR failure — graceful fallback, complaint still processed
"""

import io
from unittest.mock import patch

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ── Minimal valid 1×1 PNG ─────────────────────────────────────────────────────

TINY_PNG = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
    0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
    0x00, 0x00, 0x02, 0x00, 0x01, 0xE2, 0x21, 0xBC,
    0x33, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
    0x44, 0xAE, 0x42, 0x60, 0x82,
])

JEV_RESULT = {"department": "Water", "confidence_score": 88.0, "urgency_score": 72.0}


# ── Test 1 ────────────────────────────────────────────────────────────────────

@patch("backend.services.jev_rlcd_service.analyze_complaint", return_value=JEV_RESULT)
def test_text_only_complaint(mock_jev):
    response = client.post(
        "/api/complaints/",
        json={
            "complaint_text": "Water pipeline burst near Chinchwad school.",
            "source": "whatsapp",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["department"] == "Water"
    assert data["confidence_score"] == 88.0
    assert data["image_path"] is None
    assert data["ocr_text"] is None
    assert data["ocr_confidence"] is None


# ── Test 2 ────────────────────────────────────────────────────────────────────

@patch("backend.services.jev_rlcd_service.analyze_complaint", return_value=JEV_RESULT)
@patch(
    "backend.services.ocr_service.run_ocr",
    return_value={"ocr_text": "WARD 12\nWATER SUPPLY", "ocr_confidence": 94.0},
)
@patch("backend.services.ocr_service.save_image", return_value="uploads/test.png")
def test_image_with_text(mock_save, mock_ocr, mock_jev):
    response = client.post(
        "/api/complaints/with-image",
        data={"complaint_text": "Pipeline leaking near school.", "source": "manual"},
        files={"image": ("ward12.png", io.BytesIO(TINY_PNG), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["ocr_text"] == "WARD 12\nWATER SUPPLY"
    assert data["ocr_confidence"] == 94.0

    # Combined context must have reached JEV
    call_arg = mock_jev.call_args[0][0]
    assert "Pipeline leaking near school." in call_arg
    assert "WARD 12" in call_arg

    assert "12" in data["ward"]


# ── Test 3 ────────────────────────────────────────────────────────────────────

@patch("backend.services.jev_rlcd_service.analyze_complaint", return_value=JEV_RESULT)
@patch(
    "backend.services.ocr_service.run_ocr",
    return_value={"ocr_text": None, "ocr_confidence": None},
)
@patch("backend.services.ocr_service.save_image", return_value="uploads/pothole.png")
def test_image_no_text(mock_save, mock_ocr, mock_jev):
    response = client.post(
        "/api/complaints/with-image",
        data={"complaint_text": "Large pothole on Kothrud main road.", "source": "social_media"},
        files={"image": ("pothole.png", io.BytesIO(TINY_PNG), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ocr_text"] is None
    assert data["department"] is not None


# ── Test 4 ────────────────────────────────────────────────────────────────────

def test_invalid_image_type():
    response = client.post(
        "/api/complaints/with-image",
        data={"complaint_text": "Pothole.", "source": "manual"},
        files={"image": ("document.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]


def test_oversized_image():
    big_data = b"x" * (11 * 1024 * 1024)
    response = client.post(
        "/api/complaints/with-image",
        data={"complaint_text": "Pothole.", "source": "manual"},
        files={"image": ("big.jpg", io.BytesIO(big_data), "image/jpeg")},
    )
    assert response.status_code == 400
    assert "maximum" in response.json()["detail"].lower()


# ── Test 5 ────────────────────────────────────────────────────────────────────

@patch("backend.services.jev_rlcd_service.analyze_complaint", return_value=JEV_RESULT)
@patch(
    "backend.services.ocr_service.run_ocr",
    return_value={"ocr_text": None, "ocr_confidence": None},
)
@patch("backend.services.ocr_service.save_image", return_value="uploads/fail.png")
def test_ocr_failure_fallback(mock_save, mock_ocr, mock_jev):
    response = client.post(
        "/api/complaints/with-image",
        data={"complaint_text": "Sewage overflow near market.", "source": "whatsapp"},
        files={"image": ("fail.png", io.BytesIO(TINY_PNG), "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["department"] is not None
    assert data["ocr_text"] is None
