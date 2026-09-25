from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from backend.database import Base


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaint_text = Column(Text, nullable=False)
    source = Column(String(50), nullable=False)  # social_media | whatsapp | grievance_portal | manual
    timestamp = Column(DateTime, default=datetime.utcnow)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    ward = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)

    department = Column(String(50), nullable=True)      # Water | Roads | Electricity | Sanitation | Drainage | Other
    confidence_score = Column(Float, nullable=True)     # 0–100
    urgency_score = Column(Float, nullable=True)        # 0–100

    status = Column(String(50), default="open")         # open | resolved | in_progress
    duplicate_of = Column(Integer, nullable=True)       # id of original complaint if duplicate
    similarity_score = Column(Float, nullable=True)     # 0–100

    needs_human_review = Column(Boolean, default=False)
    review_reason = Column(String(255), nullable=True)
