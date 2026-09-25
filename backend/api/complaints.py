from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services import complaint_service, duplicate_service, analytics_service

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


class ComplaintCreate(BaseModel):
    complaint_text: str
    source: str
    address: Optional[str] = None
    timestamp: Optional[datetime] = None


class StatusUpdate(BaseModel):
    status: str


@router.post("/", summary="Submit and process a new complaint")
def submit_complaint(payload: ComplaintCreate, db: Session = Depends(get_db)):
    valid_sources = {"social_media", "whatsapp", "grievance_portal", "manual"}
    if payload.source not in valid_sources:
        raise HTTPException(status_code=400, detail=f"source must be one of {valid_sources}")

    complaint = complaint_service.create_complaint(
        db=db,
        complaint_text=payload.complaint_text,
        source=payload.source,
        address=payload.address,
        timestamp=payload.timestamp,
    )
    return complaint


@router.get("/", summary="List all complaints ordered by urgency")
def list_complaints(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return complaint_service.get_complaints(db, skip=skip, limit=limit)


@router.get("/review-queue", summary="Get complaints flagged for human review")
def review_queue(db: Session = Depends(get_db)):
    return complaint_service.get_human_review_queue(db)


@router.get("/ward-stats", summary="Get ward-level aggregated civic intelligence")
def ward_stats(db: Session = Depends(get_db)):
    return analytics_service.get_ward_statistics(db)


@router.get("/{complaint_id}", summary="Get details of a single complaint")
def get_complaint(complaint_id: int, db: Session = Depends(get_db)):
    complaint = complaint_service.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


@router.get("/{complaint_id}/related", summary="Find related complaints")
def related_complaints(complaint_id: int, db: Session = Depends(get_db)):
    complaint = complaint_service.get_complaint(db, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    related = duplicate_service.find_related_complaints(
        db=db,
        new_text=complaint.complaint_text,
        department=complaint.department,
        ward=complaint.ward,
        exclude_id=complaint_id,
    )
    return related


@router.patch("/{complaint_id}/status", summary="Update the status of a complaint")
def update_status(complaint_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    valid_statuses = {"open", "in_progress", "resolved"}
    if payload.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"status must be one of {valid_statuses}")

    complaint = complaint_service.update_complaint_status(db, complaint_id, payload.status)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint
