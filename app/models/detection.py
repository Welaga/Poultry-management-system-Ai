"""AI camera detection records."""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from app.database import Base


class CameraDetection(Base):
    __tablename__ = "camera_detections"

    id = Column(Integer, primary_key=True, index=True)
    detection_time = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    live_birds_count = Column(Integer, default=0)
    dead_birds_count = Column(Integer, default=0)
    eggs_count = Column(Integer, default=0)
    confidence_avg = Column(Integer, default=0)  # store *100
    source = Column(String(40), default="webcam")  # webcam, upload, ipcam
    image_path = Column(String(500), nullable=True)
