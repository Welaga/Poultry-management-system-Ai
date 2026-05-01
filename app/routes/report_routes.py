"""PDF report endpoints."""
from datetime import date as dt_date
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO

from app.database import get_db
from app.utils.security import get_current_user
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/daily")
def daily_report(target_date: str | None = Query(None, description="YYYY-MM-DD"),
                 db: Session = Depends(get_db), current=Depends(get_current_user)):
    target = dt_date.fromisoformat(target_date) if target_date else dt_date.today()
    pdf_bytes = ReportService.daily_report(db, target)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=daily_report_{target.isoformat()}.pdf"},
    )


@router.get("/weekly")
def weekly_report(db: Session = Depends(get_db), current=Depends(get_current_user)):
    pdf_bytes = ReportService.weekly_report(db)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=weekly_report_{dt_date.today().isoformat()}.pdf"},
    )


@router.get("/financial")
def financial_report(days: int = 30, db: Session = Depends(get_db),
                     current=Depends(get_current_user)):
    pdf_bytes = ReportService.financial_summary(db, days)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=financial_summary_{days}d_{dt_date.today().isoformat()}.pdf"},
    )
