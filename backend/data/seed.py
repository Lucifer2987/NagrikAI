"""
Seed script: loads realistic Indian civic complaints into the database
to demonstrate the full NagrikAI pipeline.

The complaints are intentionally clustered around the same incidents
(Ward 12 water pipeline burst) to showcase duplicate/related detection.

Run: uv run python -m backend.data.seed
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta
from backend.database import SessionLocal, engine, Base
from backend.models.complaint import Complaint  # registers the model with Base
from backend.services.complaint_service import create_complaint

Base.metadata.create_all(bind=engine)

SAMPLE_COMPLAINTS = [
    # Cluster 1: Water pipeline burst near Ward 12 school (3 reports of same incident)
    {
        "complaint_text": "Water pipeline has burst near the government school in Chinchwad. Water is flooding the entire road.",
        "source": "whatsapp",
        "address": "Near Government School, Chinchwad",
        "timestamp": datetime.utcnow() - timedelta(hours=3),
    },
    {
        "complaint_text": "There is water flooding the road outside the school in Ward 12. Very dangerous for children.",
        "source": "social_media",
        "address": "Ward 12, Chinchwad",
        "timestamp": datetime.utcnow() - timedelta(hours=2, minutes=30),
    },
    {
        "complaint_text": "Pipeline leakage has caused severe waterlogging near Ward 12 school. Road is submerged.",
        "source": "grievance_portal",
        "address": "Chinchwad ward 12",
        "timestamp": datetime.utcnow() - timedelta(hours=2),
    },
    # Cluster 2: Sewage overflow in Hadapsar (high urgency)
    {
        "complaint_text": "Sewage is overflowing on the main road in Hadapsar near the market. Unbearable smell and health hazard.",
        "source": "whatsapp",
        "address": "Hadapsar Market",
        "timestamp": datetime.utcnow() - timedelta(hours=5),
    },
    {
        "complaint_text": "Open manhole on the main road in Hadapsar. Very dangerous especially at night. Someone could fall in.",
        "source": "social_media",
        "address": "Hadapsar",
        "timestamp": datetime.utcnow() - timedelta(hours=4),
    },
    # Pothole complaints in Kothrud
    {
        "complaint_text": "Large pothole on the main road in Kothrud near the petrol pump. Caused two accidents last week.",
        "source": "grievance_portal",
        "address": "Kothrud, near petrol pump",
        "timestamp": datetime.utcnow() - timedelta(days=1),
    },
    {
        "complaint_text": "The road in Kothrud is badly damaged after rain. Multiple potholes causing traffic issues.",
        "source": "manual",
        "address": "Kothrud main road",
        "timestamp": datetime.utcnow() - timedelta(hours=20),
    },
    # Electricity outage in Aundh
    {
        "complaint_text": "Street lights in Aundh sector 4 are not working for the past 10 days. The area is completely dark at night.",
        "source": "whatsapp",
        "address": "Aundh Sector 4",
        "timestamp": datetime.utcnow() - timedelta(days=2),
    },
    {
        "complaint_text": "Electricity transformer is sparking and making noise in Aundh. Dangerous situation near residential buildings.",
        "source": "social_media",
        "address": "Aundh",
        "timestamp": datetime.utcnow() - timedelta(hours=10),
    },
    # Garbage collection in Deccan
    {
        "complaint_text": "Garbage has not been collected from our colony in Deccan Gymkhana for 5 days. Stray dogs are spreading waste everywhere.",
        "source": "grievance_portal",
        "address": "Deccan Gymkhana colony",
        "timestamp": datetime.utcnow() - timedelta(days=3),
    },
    # Drainage issue in Yerawada
    {
        "complaint_text": "The drain near Yerawada bus stop is blocked and overflowing onto the road. Water is stagnant and breeding mosquitoes.",
        "source": "manual",
        "address": "Yerawada bus stop",
        "timestamp": datetime.utcnow() - timedelta(hours=36),
    },
    # Water supply problem in Baner
    {
        "complaint_text": "No water supply in Baner housing society for 3 days. Residents are suffering especially elderly people.",
        "source": "whatsapp",
        "address": "Baner housing society",
        "timestamp": datetime.utcnow() - timedelta(hours=18),
    },
    # Illegal dumping in Shivajinagar
    {
        "complaint_text": "Construction debris has been illegally dumped on the footpath near Shivajinagar bus stand. Pedestrians cannot walk.",
        "source": "social_media",
        "address": "Shivajinagar bus stand",
        "timestamp": datetime.utcnow() - timedelta(hours=8),
    },
]


def seed():
    db = SessionLocal()
    existing = db.query(Complaint).count()
    if existing > 0:
        print(f"Database already has {existing} complaints. Skipping seed.")
        db.close()
        return

    print(f"Seeding {len(SAMPLE_COMPLAINTS)} complaints...")
    for i, data in enumerate(SAMPLE_COMPLAINTS, 1):
        print(f"  [{i}/{len(SAMPLE_COMPLAINTS)}] Processing: {data['complaint_text'][:60]}...")
        complaint = create_complaint(
            db=db,
            complaint_text=data["complaint_text"],
            source=data["source"],
            address=data.get("address"),
            timestamp=data.get("timestamp"),
        )
        print(f"    -> #{complaint.id} | {complaint.department} | Confidence: {complaint.confidence_score}% | Urgency: {complaint.urgency_score}/100 | Review: {complaint.needs_human_review}")

    db.close()
    print("\nSeed complete.")


if __name__ == "__main__":
    seed()
