"""Feed inventory, purchases, and consumption models."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.sql import func

from app.database import Base


class FeedPurchase(Base):
    """Records of feed purchases."""
    __tablename__ = "feed_purchases"

    id = Column(Integer, primary_key=True, index=True)
    feed_type = Column(String(80), nullable=False)  # starter, grower, layer-mash, etc.
    supplier = Column(String(120), nullable=True)
    quantity_kg = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    purchase_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FeedConsumption(Base):
    """Daily feed consumption log."""
    __tablename__ = "feed_consumption"

    id = Column(Integer, primary_key=True, index=True)
    feed_type = Column(String(80), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    consumption_date = Column(Date, nullable=False, index=True)
    batch_id = Column(Integer, ForeignKey("bird_batches.id"), nullable=True)
    notes = Column(Text, nullable=True)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FeedInventory(Base):
    """Current feed stock by type."""
    __tablename__ = "feed_inventory"

    id = Column(Integer, primary_key=True, index=True)
    feed_type = Column(String(80), unique=True, nullable=False)
    quantity_kg = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
