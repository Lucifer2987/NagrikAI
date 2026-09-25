# NagrikAI — AI-Powered Civic Complaint Intelligence System

NagrikAI converts unstructured citizen complaints into structured, prioritized, location-aware work for municipal teams.

## How it works

```
Citizen Complaint
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

### 3. Seed sample data

```bash
uv run python -m backend.data.seed
```

### 4. Start the server

```bash
uv run uvicorn main:app --reload
```

API docs available at: http://localhost:8000/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/complaints/` | Submit and process a new complaint |
| GET | `/api/complaints/` | List all complaints ordered by urgency |
| GET | `/api/complaints/{id}` | Get details of a single complaint |
| GET | `/api/complaints/{id}/related` | Find related/duplicate complaints |
| PATCH | `/api/complaints/{id}/status` | Update complaint status |
| GET | `/api/complaints/review-queue` | Get complaints flagged for human review |
| GET | `/api/complaints/ward-stats` | Ward-level aggregated civic intelligence |

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
│   └── complaints.py       # FastAPI routes
├── services/
│   ├── complaint_service.py    # Pipeline orchestration
│   ├── jev_rlcd_service.py     # TypeSafe Jev integration
│   ├── duplicate_service.py    # Related complaint detection
│   ├── geocoding_service.py    # Address → ward/lat/lng
│   └── analytics_service.py   # Ward-level aggregation
├── models/
│   └── complaint.py        # SQLAlchemy ORM model
├── data/
│   └── seed.py             # Sample complaints
└── database.py             # SQLite setup
main.py                     # FastAPI app entry point
```
