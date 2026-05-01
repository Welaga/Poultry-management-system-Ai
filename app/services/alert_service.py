"""Smart alert generation service."""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.models.alert import Alert
from app.models.bird import BirdBatch, MortalityRecord
from app.models.feed import FeedInventory


class AlertService:
    @staticmethod
    def create(db: Session, alert_type: str, severity: str, title: str, message: str) -> Alert:
        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def check_mortality_alert(db: Session, batch_id: int):
        """Trigger an alert if today's mortality is unusually high."""
        today = date.today()
        record = (
            db.query(func.sum(MortalityRecord.count))
            .filter(MortalityRecord.batch_id == batch_id, MortalityRecord.death_date == today)
            .scalar()
            or 0
        )
        batch = db.query(BirdBatch).filter(BirdBatch.id == batch_id).first()
        if not batch:
            return

        if record >= settings.MAX_DAILY_DEATHS_ABSOLUTE:
            AlertService.create(
                db,
                alert_type="mortality",
                severity="critical",
                title="High mortality detected",
                message=f"Batch {batch.batch_code}: {record} deaths recorded today (absolute threshold).",
            )
            return

        if batch.current_count > 0:
            rate = (record / (batch.current_count + record)) * 100
            if rate >= settings.HIGH_MORTALITY_THRESHOLD_PERCENT:
                AlertService.create(
                    db,
                    alert_type="mortality",
                    severity="warning",
                    title="Elevated mortality rate",
                    message=f"Batch {batch.batch_code}: daily mortality rate is {rate:.2f}%.",
                )

    @staticmethod
    def check_feed_alert(db: Session):
        """Trigger an alert if any feed type is below threshold."""
        low_items = (
            db.query(FeedInventory)
            .filter(FeedInventory.quantity_kg < settings.LOW_FEED_THRESHOLD_KG)
            .all()
        )
        for item in low_items:
            # Avoid duplicate alerts within a day
            existing = (
                db.query(Alert)
                .filter(
                    Alert.alert_type == "feed",
                    Alert.title.like(f"%{item.feed_type}%"),
                    Alert.is_resolved == False,
                )
                .first()
            )
            if existing:
                continue

            AlertService.create(
                db,
                alert_type="feed",
                severity="warning",
                title=f"Low feed stock: {item.feed_type}",
                message=f"Only {item.quantity_kg:.1f} kg of {item.feed_type} left (threshold {settings.LOW_FEED_THRESHOLD_KG} kg).",
            )

    @staticmethod
    def get_unresolved(db: Session, limit: int = 20):
        return (
            db.query(Alert)
            .filter(Alert.is_resolved == False)
            .order_by(Alert.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def mark_resolved(db: Session, alert_id: int):
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.is_resolved = True
            alert.is_read = True
            db.commit()
        return alert
