from sqlalchemy import func
from sqlalchemy.orm import Session
from backend.models.complaint import Complaint


def get_ward_statistics(db: Session) -> list[dict]:
    wards = db.query(Complaint.ward).distinct().all()
    stats = []

    for (ward,) in wards:
        if not ward:
            continue
        complaints = db.query(Complaint).filter(Complaint.ward == ward).all()
        total = len(complaints)
        open_count = sum(1 for c in complaints if c.status == "open")
        high_urgency = sum(1 for c in complaints if c.urgency_score and c.urgency_score >= 70)
        duplicate_count = sum(1 for c in complaints if c.duplicate_of is not None)
        avg_urgency = (
            sum(c.urgency_score for c in complaints if c.urgency_score) / total
            if total else 0
        )
        avg_confidence = (
            sum(c.confidence_score for c in complaints if c.confidence_score) / total
            if total else 0
        )

        dept_dist: dict[str, int] = {}
        for c in complaints:
            if c.department:
                dept_dist[c.department] = dept_dist.get(c.department, 0) + 1

        stats.append({
            "ward": ward,
            "total_complaints": total,
            "open_complaints": open_count,
            "high_urgency_complaints": high_urgency,
            "duplicate_related_count": duplicate_count,
            "avg_urgency": round(avg_urgency, 1),
            "avg_confidence": round(avg_confidence, 1),
            "department_distribution": dept_dist,
        })

    stats.sort(key=lambda x: x["total_complaints"], reverse=True)
    return stats
