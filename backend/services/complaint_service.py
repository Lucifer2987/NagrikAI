from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.complaint import Complaint
from backend.services import jev_rlcd_service, geocoding_service, duplicate_service, ocr_service

HUMAN_REVIEW_CONFIDENCE_THRESHOLD = 60
HUMAN_REVIEW_URGENCY_THRESHOLD = 85


def _determine_review_flags(confidence: float, urgency: float, related: list) -> tuple[bool, str | None]:
    reasons = []
    if confidence < HUMAN_REVIEW_CONFIDENCE_THRESHOLD:
        reasons.append("Low classification confidence")
    if urgency >= HUMAN_REVIEW_URGENCY_THRESHOLD:
        reasons.append("High urgency complaint requires verification")
    if related and related[0]["relation_type"] == "Possibly Related":
        reasons.append("Duplicate detection is ambiguous")
    needs_review = bool(reasons)
    return needs_review, "; ".join(reasons) if reasons else None


def create_complaint(db: Session, complaint_text: str, source: str, address: str | None, timestamp: datetime | None) -> Complaint:
    ts = timestamp or datetime.utcnow()

    analysis = jev_rlcd_service.analyze_complaint(complaint_text)
    geo = geocoding_service.geocode_location(address, complaint_text)
    related = duplicate_service.find_related_complaints(
        db, complaint_text, analysis["department"], geo["ward"]
    )

    needs_review, review_reason = _determine_review_flags(
        analysis["confidence_score"], analysis["urgency_score"], related
    )

    # Mark as duplicate if the top related complaint is the same problem with high similarity
    duplicate_of = None
    similarity_score = None
    if related and related[0]["relation_type"] == "Same Problem" and related[0]["similarity_score"] >= 80:
        duplicate_of = related[0]["id"]
        similarity_score = related[0]["similarity_score"]

    complaint = Complaint(
        complaint_text=complaint_text,
        source=source,
        timestamp=ts,
        address=address,
        latitude=geo["latitude"],
        longitude=geo["longitude"],
        ward=geo["ward"],
        department=analysis["department"],
        confidence_score=analysis["confidence_score"],
        urgency_score=analysis["urgency_score"],
        status="open",
        duplicate_of=duplicate_of,
        similarity_score=similarity_score,
        needs_human_review=needs_review,
        review_reason=review_reason,
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def create_complaint_with_image(
    db: Session,
    complaint_text: str,
    source: str,
    address: str | None,
    timestamp: datetime | None,
    image_bytes: bytes,
    image_filename: str,
) -> Complaint:
    """
    Extends the base pipeline with an optional image.
    Saves the image, runs OCR, feeds the combined context into the existing
    JEV/RLCD pipeline, then stores OCR results alongside the complaint.
    """
    ts = timestamp or datetime.utcnow()

    image_path = ocr_service.save_image(image_bytes, image_filename)
    ocr_result = ocr_service.run_ocr(image_bytes)
    ocr_text = ocr_result["ocr_text"]
    ocr_confidence = ocr_result["ocr_confidence"]

    # OCR text enriches the geocoding search even when image has no user-facing text
    combined_address = f"{address or ''} {ocr_text or ''}".strip() or None
    combined_context = ocr_service.build_combined_context(complaint_text, ocr_text)

    analysis = jev_rlcd_service.analyze_complaint(combined_context)
    geo = geocoding_service.geocode_location(combined_address, combined_context)
    related = duplicate_service.find_related_complaints(
        db, complaint_text, analysis["department"], geo["ward"]
    )

    needs_review, review_reason = _determine_review_flags(
        analysis["confidence_score"], analysis["urgency_score"], related
    )

    duplicate_of = None
    similarity_score = None
    if related and related[0]["relation_type"] == "Same Problem" and related[0]["similarity_score"] >= 80:
        duplicate_of = related[0]["id"]
        similarity_score = related[0]["similarity_score"]

    complaint = Complaint(
        complaint_text=complaint_text,
        source=source,
        timestamp=ts,
        address=address,
        latitude=geo["latitude"],
        longitude=geo["longitude"],
        ward=geo["ward"],
        department=analysis["department"],
        confidence_score=analysis["confidence_score"],
        urgency_score=analysis["urgency_score"],
        status="open",
        duplicate_of=duplicate_of,
        similarity_score=similarity_score,
        needs_human_review=needs_review,
        review_reason=review_reason,
        image_path=image_path,
        ocr_text=ocr_text,
        ocr_confidence=ocr_confidence,
    )

    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def get_complaints(db: Session, skip: int = 0, limit: int = 100) -> list[Complaint]:
    return (
        db.query(Complaint)
        .order_by(Complaint.urgency_score.desc(), Complaint.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_complaint(db: Session, complaint_id: int) -> Complaint | None:
    return db.query(Complaint).filter(Complaint.id == complaint_id).first()


def update_complaint_status(db: Session, complaint_id: int, status: str) -> Complaint | None:
    complaint = get_complaint(db, complaint_id)
    if complaint:
        complaint.status = status
        db.commit()
        db.refresh(complaint)
    return complaint


def get_human_review_queue(db: Session) -> list[Complaint]:
    return (
        db.query(Complaint)
        .filter(Complaint.needs_human_review == True)
        .filter(Complaint.status == "open")
        .order_by(Complaint.urgency_score.desc())
        .all()
    )
