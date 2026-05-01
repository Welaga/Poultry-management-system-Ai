"""Health, disease and vaccination models."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class HealthRecord(Base):
    """Disease cases."""
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("bird_batches.id"), nullable=True)
    disease_name = Column(String(120), nullable=False)
    symptoms = Column(Text, nullable=True)
    diagnosis_date = Column(Date, nullable=False)
    affected_count = Column(Integer, default=0)
    treatment = Column(Text, nullable=True)
    medication = Column(String(255), nullable=True)
    cost = Column(Float, default=0.0)
    status = Column(String(20), default="ongoing")  # ongoing, resolved
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batch = relationship("BirdBatch", back_populates="health_records")


class Vaccination(Base):
    """Vaccination schedule and records."""
    __tablename__ = "vaccinations"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("bird_batches.id"), nullable=True)
    vaccine_name = Column(String(120), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    administered_date = Column(Date, nullable=True)
    administered = Column(Boolean, default=False)
    administered_by = Column(String(120), nullable=True)
    dosage = Column(String(80), nullable=True)
    cost = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
