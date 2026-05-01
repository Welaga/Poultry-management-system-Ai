"""Dashboard summary endpoints."""
from datetime import date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.bird import BirdBatch, MortalityRecord
from app.models.egg import EggRecord, EggSale, EggStorage
from app.models.feed import FeedInventory
from app.models.health import HealthRecord
from app.models.detection import CameraDetection
from app.utils.security import get_current_user
from app.services.alert_service import AlertService
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), current=Depends(get_current_user)):
    today = date.today()
    week_ago = today - timedelta(days=7)

    total_birds = db.query(func.sum(BirdBatch.initial_count)).scalar() or 0
    live_birds = db.query(func.sum(BirdBatch.current_count)).scalar() or 0
    dead_birds = total_birds - live_birds

    total_batches = db.query(func.count(BirdBatch.id)).scalar() or 0

    eggs_today = db.query(func.sum(EggRecord.good_eggs)).filter(
        EggRecord.collection_date == today).scalar() or 0
    eggs_week = db.query(func.sum(EggRecord.good_eggs)).filter(
        EggRecord.collection_date >= week_ago).scalar() or 0

    sales_today = db.query(func.sum(EggSale.total_amount)).filter(
        EggSale.sale_date == today).scalar() or 0
    sales_week = db.query(func.sum(EggSale.total_amount)).filter(
        EggSale.sale_date >= week_ago).scalar() or 0

    total_feed_kg = db.query(func.sum(FeedInventory.quantity_kg)).scalar() or 0

    active_diseases = db.query(func.count(HealthRecord.id)).filter(
        HealthRecord.status == "ongoing").scalar() or 0

    egg_storage = db.query(func.sum(EggStorage.quantity)).scalar() or 0

    # Latest camera detection
    latest_detection = db.query(CameraDetection).order_by(
        CameraDetection.detection_time.desc()).first()
    detection_data = None
    if latest_detection:
        detection_data = {
            "live": latest_detection.live_birds_count,
            "dead": latest_detection.dead_birds_count,
            "eggs": latest_detection.eggs_count,
            "time": latest_detection.detection_time.isoformat() if latest_detection.detection_time else None,
        }

    return {
        "total_birds": int(total_birds),
        "live_birds": int(live_birds),
        "dead_birds": int(dead_birds),
        "total_batches": int(total_batches),
        "eggs_today": int(eggs_today),
        "eggs_week": int(eggs_week),
        "egg_storage": int(egg_storage),
        "sales_today": float(sales_today),
        "sales_week": float(sales_week),
        "feed_stock_kg": float(total_feed_kg),
        "active_diseases": int(active_diseases),
        "mortality_rate": round((dead_birds / total_birds * 100), 2) if total_birds > 0 else 0,
        "latest_detection": detection_data,
    }


@router.get("/charts/eggs-trend")
def eggs_trend(days: int = 14, db: Session = Depends(get_db),
               current=Depends(get_current_user)):
    end = date.today()
    start = end - timedelta(days=days)
    rows = (
        db.query(EggRecord.collection_date, func.sum(EggRecord.good_eggs))
        .filter(EggRecord.collection_date >= start)
        .group_by(EggRecord.collection_date)
        .order_by(EggRecord.collection_date)
        .all()
    )
    by_day = {str(d): int(c or 0) for d, c in rows}
    out = []
    for i in range(days + 1):
        d = (start + timedelta(days=i)).isoformat()
        out.append({"date": d, "eggs": by_day.get(d, 0)})
    return {"data": out}


@router.get("/charts/mortality-trend")
def mortality_trend(days: int = 14, db: Session = Depends(get_db),
                    current=Depends(get_current_user)):
    end = date.today()
    start = end - timedelta(days=days)
    rows = (
        db.query(MortalityRecord.death_date, func.sum(MortalityRecord.count))
        .filter(MortalityRecord.death_date >= start)
        .group_by(MortalityRecord.death_date)
        .order_by(MortalityRecord.death_date)
        .all()
    )
    by_day = {str(d): int(c or 0) for d, c in rows}
    out = []
    for i in range(days + 1):
        d = (start + timedelta(days=i)).isoformat()
        out.append({"date": d, "deaths": by_day.get(d, 0)})
    return {"data": out}


@router.get("/charts/feed-stock")
def feed_stock(db: Session = Depends(get_db), current=Depends(get_current_user)):
    rows = db.query(FeedInventory).all()
    return {"data": [{"feed_type": r.feed_type, "quantity_kg": r.quantity_kg} for r in rows]}


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db), current=Depends(get_current_user)):
    AlertService.check_feed_alert(db)
    items = AlertService.get_unresolved(db)
    return {
        "alerts": [
            {
                "id": a.id, "type": a.alert_type, "severity": a.severity,
                "title": a.title, "message": a.message,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            } for a in items
        ]
    }


@router.post("/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db),
                  current=Depends(get_current_user)):
    a = AlertService.mark_resolved(db, alert_id)
    if not a:
        return {"success": False, "message": "Alert not found"}
    return {"success": True}


@router.get("/insights")
def insights(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return {"insights": AnalyticsService.insights(db)}
