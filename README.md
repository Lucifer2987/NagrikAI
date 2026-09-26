# NagrikAI — AI-Powered Civic Complaint Intelligence System

NagrikAI converts unstructured citizen complaints into structured, prioritized, location-aware work for municipal teams.

## How it works

```
Citizen Complaint (text + optional image)
    ↓
[If image] OCR → extracted text
    ↓
Combined context (user text + OCR text)
    ↓
JEV/RLCD Analysis  (TypeSafe Jev)
    ↓
Department Classification + Confidence Score
    ↓
Urgency Score
    ↓
Duplicate / Related Complaint Detection
    ↓
Geocoding → Ward
    ↓
Ward-level Aggregation
    ↓
Human Review Queue
```

## Setup

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure API key

Copy `.env.example` to `.env` and add your TypeSafe API key:

```bash
cp .env.example .env
# Edit .env and set TYPESAFE_API_KEY
```

### 3. Migrate existing database (if upgrading)

If you have an existing `nagrik_ai.db`, run this once to add the new image/OCR columns:

```bash
uv run python -m backend.data.migrate_add_image_ocr
```

New installations skip this — columns are created automatically on first start.

### 4. Seed sample data

```bash
uv run python -m backend.data.seed
```

### 5. Start the server

```bash
uv run uvicorn main:app --reload
```

API docs available at: http://localhost:8000/docs

### 6. Run tests

```bash
uv run pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/complaints/` | Submit a complaint (JSON) |
| POST | `/api/complaints/with-image` | Submit a complaint with optional image (multipart) |
| GET | `/api/complaints/` | List all complaints ordered by urgency |
| GET | `/api/complaints/{id}` | Get details of a single complaint |
| GET | `/api/complaints/{id}/related` | Find related/duplicate complaints |
| PATCH | `/api/complaints/{id}/status` | Update complaint status |
| GET | `/api/complaints/review-queue` | Get complaints flagged for human review |
| GET | `/api/complaints/ward-stats` | Ward-level aggregated civic intelligence |

### Image upload (multipart/form-data)

```
POST /api/complaints/with-image

complaint_text  (required)
source          (required)
address         (optional)
image           (optional — JPG, JPEG, PNG, WEBP, max 10 MB)
```

When an image is provided:
- Image is validated and saved to `uploads/`
- EasyOCR extracts text from the image
- User text + OCR text are combined into a single context for JEV/RLCD
- OCR result (`ocr_text`, `ocr_confidence`) is stored with the complaint
- If OCR finds no text or fails, the complaint continues with user text only

## Complaint Sources

- `social_media`
- `whatsapp`
- `grievance_portal`
- `manual`

## JEV/RLCD Integration

NagrikAI uses [TypeSafe Jev](https://typesafe.ai) for:

- **Department classification** (Choice) — selects from Water, Roads, Electricity, Sanitation, Drainage, Other
- **Confidence score** — derived directly from Jev's RLCD-calibrated probabilities (not hardcoded)
- **Urgency scoring** (Score) — rates complaint severity on a 4-level scale
- **Safety risk detection** (Noul) — boosts urgency for public safety hazards

## Project Structure

```
backend/
├── api/
│   └── complaints.py           # FastAPI routes
├── services/
│   ├── complaint_service.py    # Pipeline orchestration
│   ├── jev_rlcd_service.py     # TypeSafe Jev integration
│   ├── ocr_service.py          # EasyOCR image processing
│   ├── duplicate_service.py    # Related complaint detection
│   ├── geocoding_service.py    # Address → ward/lat/lng
│   └── analytics_service.py   # Ward-level aggregation
├── models/
│   └── complaint.py            # SQLAlchemy ORM model
├── data/
│   ├── seed.py                 # Sample complaints
│   └── migrate_add_image_ocr.py  # DB migration for image/OCR columns
└── database.py                 # SQLite setup
main.py                         # FastAPI app entry point
tests/
└── test_image_ocr.py           # Backend tests
```

