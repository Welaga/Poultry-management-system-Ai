"""Analytics and predictive intelligence endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.security import get_current_user
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/performance-score")
def performance_score(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return AnalyticsService.farm_performance_score(db)


@router.get("/predict-eggs")
def predict_eggs(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return AnalyticsService.predict_next_week_eggs(db)


@router.get("/revenue")
def revenue(days: int = 30, db: Session = Depends(get_db),
            current=Depends(get_current_user)):
    return AnalyticsService.revenue_summary(db, days)


@router.get("/insights")
def insights(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return {"insights": AnalyticsService.insights(db)}
