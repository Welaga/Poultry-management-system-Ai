"""Egg collection, storage, and sales models."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class EggRecord(Base):
    """Daily egg collection log."""
    __tablename__ = "egg_records"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("bird_batches.id"), nullable=True)
    collection_date = Column(Date, nullable=False, index=True)
    total_eggs = Column(Integer, nullable=False)
    broken_eggs = Column(Integer, default=0)
    good_eggs = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    batch = relationship("BirdBatch", back_populates="egg_records")


class EggStorage(Base):
    """Current egg inventory."""
    __tablename__ = "egg_storage"

    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Integer, default=0)
    storage_location = Column(String(80), default="Main Cold Room")
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class EggSale(Base):
    """Egg sales records."""
    __tablename__ = "egg_sales"

    id = Column(Integer, primary_key=True, index=True)
    sale_date = Column(Date, nullable=False, index=True)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)  # price per egg
    total_amount = Column(Float, nullable=False)
    customer_name = Column(String(120), nullable=True)
    payment_status = Column(String(20), default="paid")  # paid, pending
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
