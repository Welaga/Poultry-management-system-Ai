"""Bird batch and mortality endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.bird import BirdBatch, MortalityRecord
from app.utils.schemas import (
    BatchCreate, BatchOut, MortalityCreate, MortalityOut
)
from app.utils.security import get_current_user
from app.services.alert_service import AlertService

router = APIRouter()


# -------- Batches --------
@router.post("/batches", response_model=BatchOut)
def create_batch(payload: BatchCreate, db: Session = Depends(get_db),
                 current=Depends(get_current_user)):
    if db.query(BirdBatch).filter(BirdBatch.batch_code == payload.batch_code).first():
        raise HTTPException(status_code=400, detail="Batch code already exists")
    batch = BirdBatch(
        batch_code=payload.batch_code,
        breed=payload.breed,
        bird_type=payload.bird_type,
        initial_count=payload.initial_count,
        current_count=payload.initial_count,
        arrival_date=payload.arrival_date,
        growth_stage=payload.growth_stage,
        age_weeks=payload.age_weeks,
        cost_per_bird=payload.cost_per_bird,
        notes=payload.notes,
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/batches", response_model=List[BatchOut])
def list_batches(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return db.query(BirdBatch).order_by(BirdBatch.created_at.desc()).all()


@router.get("/batches/{batch_id}", response_model=BatchOut)
def get_batch(batch_id: int, db: Session = Depends(get_db),
              current=Depends(get_current_user)):
    b = db.query(BirdBatch).filter(BirdBatch.id == batch_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Batch not found")
    return b


@router.put("/batches/{batch_id}", response_model=BatchOut)
def update_batch(batch_id: int, payload: BatchCreate, db: Session = Depends(get_db),
                 current=Depends(get_current_user)):
    b = db.query(BirdBatch).filter(BirdBatch.id == batch_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Batch not found")
    for k, v in payload.model_dump().items():
        if k != "initial_count":  # cannot reduce initial count below dead+live
            setattr(b, k, v)
    db.commit()
    db.refresh(b)
    return b


@router.delete("/batches/{batch_id}")
def delete_batch(batch_id: int, db: Session = Depends(get_db),
                 current=Depends(get_current_user)):
    b = db.query(BirdBatch).filter(BirdBatch.id == batch_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Batch not found")
    db.delete(b)
    db.commit()
    return {"success": True}


# -------- Mortality --------
@router.post("/mortality", response_model=MortalityOut)
def add_mortality(payload: MortalityCreate, db: Session = Depends(get_db),
                  current=Depends(get_current_user)):
    batch = db.query(BirdBatch).filter(BirdBatch.id == payload.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if payload.count > batch.current_count:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot record {payload.count} deaths; only {batch.current_count} live birds.",
        )
    record = MortalityRecord(
        batch_id=payload.batch_id,
        death_date=payload.death_date,
        count=payload.count,
        cause=payload.cause,
        notes=payload.notes,
        recorded_by=current.id,
    )
    batch.current_count -= payload.count
    db.add(record)
    db.commit()
    db.refresh(record)

    # Smart alert
    AlertService.check_mortality_alert(db, batch.id)
    return record


@router.get("/mortality", response_model=List[MortalityOut])
def list_mortality(batch_id: int | None = None, db: Session = Depends(get_db),
                   current=Depends(get_current_user)):
    q = db.query(MortalityRecord)
    if batch_id:
        q = q.filter(MortalityRecord.batch_id == batch_id)
    return q.order_by(MortalityRecord.death_date.desc()).limit(200).all()


@router.delete("/mortality/{record_id}")
def delete_mortality(record_id: int, db: Session = Depends(get_db),
                     current=Depends(get_current_user)):
    record = db.query(MortalityRecord).filter(MortalityRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    batch = db.query(BirdBatch).filter(BirdBatch.id == record.batch_id).first()
    if batch:
        batch.current_count += record.count
    db.delete(record)
    db.commit()
    return {"success": True}
