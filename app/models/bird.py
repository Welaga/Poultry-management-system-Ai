"""Bird batch and mortality tracking models."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class BirdBatch(Base):
    """A batch of birds purchased / hatched together."""
    __tablename__ = "bird_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_code = Column(String(50), unique=True, nullable=False, index=True)
    breed = Column(String(80), nullable=False)
    bird_type = Column(String(40), default="layer")  # layer, broiler, breeder
    initial_count = Column(Integer, nullable=False)
    current_count = Column(Integer, nullable=False)  # auto-updated on mortality
    arrival_date = Column(Date, nullable=False)
    growth_stage = Column(String(40), default="chick")  # chick, grower, layer, finisher
    age_weeks = Column(Integer, default=0)
    cost_per_bird = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    mortality_records = relationship("MortalityRecord", back_populates="batch", cascade="all, delete-orphan")
    egg_records = relationship("EggRecord", back_populates="batch")
    health_records = relationship("HealthRecord", back_populates="batch")


class MortalityRecord(Base):
    """Records of bird deaths."""
    __tablename__ = "mortality_records"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("bird_batches.id"), nullable=False)
    death_date = Column(Date, nullable=False)
    count = Column(Integer, nullable=False)
    cause = Column(String(120), nullable=True)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batch = relationship("BirdBatch", back_populates="mortality_records")
