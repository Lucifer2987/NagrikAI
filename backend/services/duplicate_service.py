"""
Duplicate/related complaint detection.

Strategy:
1. Filter existing complaints to the same department (same civic problem type).
2. Compute text similarity using SequenceMatcher (good enough for an MVP).
3. Boost similarity when both complaints are in the same ward (location overlap).

Thresholds:
  ≥ 75 → Same Problem
  ≥ 50 → Possibly Related
  <  50 → Different
"""

from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from backend.models.complaint import Complaint


SAME_PROBLEM_THRESHOLD = 75
RELATED_THRESHOLD = 50


def _text_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio() * 100


def find_related_complaints(
    db: Session,
    new_text: str,
    department: str,
    ward: str | None,
    exclude_id: int | None = None,
) -> list[dict]:
    """
    Returns a ranked list of existing complaints that may be related to the new one.
    Each result contains: id, similarity_score, relation_type.
    """
    candidates = (
        db.query(Complaint)
        .filter(Complaint.department == department)
        .filter(Complaint.status != "resolved")
        .all()
    )

    results = []
    for candidate in candidates:
        if exclude_id and candidate.id == exclude_id:
            continue

        text_sim = _text_similarity(new_text, candidate.complaint_text)

        # Location bonus: same ward signals a higher chance it's the same incident
        location_bonus = 10 if (ward and ward == candidate.ward) else 0
        similarity = min(100, text_sim + location_bonus)

        if similarity >= RELATED_THRESHOLD:
            relation = "Same Problem" if similarity >= SAME_PROBLEM_THRESHOLD else "Possibly Related"
            results.append({
                "id": candidate.id,
                "similarity_score": round(similarity, 1),
                "relation_type": relation,
                "complaint_text": candidate.complaint_text[:120],
                "ward": candidate.ward,
            })

    results.sort(key=lambda x: x["similarity_score"], reverse=True)
    return results[:5]
