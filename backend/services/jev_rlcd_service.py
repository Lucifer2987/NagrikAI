import os
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
from dotenv import load_dotenv

load_dotenv()

# Jev returns calibrated probabilities via RLCD training.
# The confidence score is derived directly from the model's returned probability
# for the chosen department, so it reflects real classification certainty.
client = TypeSafeClient(api_key=os.environ["TYPESAFE_API_KEY"])

DEPARTMENTS = {
    "Water": "Water supply problems, pipeline leakage, waterlogging caused by burst pipes, water shortage",
    "Roads": "Potholes, road damage, broken roads, road construction issues",
    "Electricity": "Power outages, street lights not working, electrical safety hazards, transformer issues",
    "Sanitation": "Garbage not collected, illegal dumping, overflowing dustbins, waste management",
    "Drainage": "Sewage overflow, blocked drains, drainage problems, open manholes",
    "Other": "Complaints that do not clearly fit any of the above civic departments",
}

URGENCY_CRITERIA = [
    "Minor issue with no immediate safety risk — small pothole, single streetlight, routine maintenance",
    "Moderate issue affecting daily life but not an emergency — garbage backlog, road damage, water disruption",
    "Serious issue with significant public impact — major road damage, extended power outage, waterlogging",
    "Critical emergency threatening public safety — sewage overflow in residential area, burst main pipeline, open manhole, electrical hazard",
]


def analyze_complaint(complaint_text: str) -> dict:
    """
    Calls Jev to classify department, score urgency, and detect public safety risk.
    Returns a dict with department, confidence_score (0-100), urgency_score (0-100).
    """
    state = f"Civic complaint received from an Indian city: {complaint_text}"

    response = client.system_one(
        state=state,
        questions={
            "department": Choice(
                instructions="Which municipal department should handle this complaint?",
                criteria=DEPARTMENTS,
            ),
            "urgency": Score(
                instructions="How urgent is this civic complaint based on public impact and safety risk?",
                criteria=URGENCY_CRITERIA,
            ),
            "is_safety_risk": Noul(
                instructions="Does this complaint involve an immediate public safety risk such as a dangerous open manhole, sewage flooding, or electrical hazard?",
            ),
        },
    )

    dept_answer = response.answers["department"]
    urgency_answer = response.answers["urgency"]
    safety_answer = response.answers["is_safety_risk"]

    department = dept_answer.choice
    # Jev's calibrated probability for the chosen department (RLCD-trained)
    confidence_score = round(dept_answer.probabilities[department] * 100, 1)

    # Map score index (0–3) to 0–100 range, boost if safety risk
    raw_urgency = urgency_answer.score / (len(URGENCY_CRITERIA) - 1)
    safety_boost = safety_answer.noul * 15  # up to +15 points for safety risks
    urgency_score = round(min(100, raw_urgency * 85 + safety_boost), 1)

    return {
        "department": department.capitalize(),
        "confidence_score": confidence_score,
        "urgency_score": urgency_score,
    }
