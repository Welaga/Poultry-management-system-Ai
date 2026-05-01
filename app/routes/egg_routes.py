"""Egg collection, storage, sales endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.egg import EggRecord, EggStorage, EggSale
from app.utils.schemas import EggCreate, EggOut, EggSaleCreate, EggSaleOut
from app.utils.security import get_current_user

router = APIRouter()


def _ensure_storage(db: Session) -> EggStorage:
    s = db.query(EggStorage).first()
    if not s:
        s = EggStorage(quantity=0)
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.post("/collection", response_model=EggOut)
def add_collection(payload: EggCreate, db: Session = Depends(get_db),
                   current=Depends(get_current_user)):
    if payload.broken_eggs > payload.total_eggs:
        raise HTTPException(status_code=400, detail="Broken cannot exceed total")
    good = payload.total_eggs - payload.broken_eggs
    record = EggRecord(
        batch_id=payload.batch_id,
        collection_date=payload.collection_date,
        total_eggs=payload.total_eggs,
        broken_eggs=payload.broken_eggs,
        good_eggs=good,
        notes=payload.notes,
        recorded_by=current.id,
    )
    db.add(record)
    storage = _ensure_storage(db)
    storage.quantity += good
    db.commit()
    db.refresh(record)
    return record


@router.get("/collection", response_model=List[EggOut])
def list_collections(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return db.query(EggRecord).order_by(EggRecord.collection_date.desc()).limit(200).all()


@router.delete("/collection/{record_id}")
def delete_collection(record_id: int, db: Session = Depends(get_db),
                      current=Depends(get_current_user)):
    r = db.query(EggRecord).filter(EggRecord.id == record_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    storage = _ensure_storage(db)
    storage.quantity = max(0, storage.quantity - r.good_eggs)
    db.delete(r)
    db.commit()
    return {"success": True}


@router.get("/storage")
def get_storage(db: Session = Depends(get_db), current=Depends(get_current_user)):
    s = _ensure_storage(db)
    return {
        "quantity": s.quantity,
        "storage_location": s.storage_location,
        "last_updated": s.last_updated.isoformat() if s.last_updated else None,
    }


@router.post("/sales", response_model=EggSaleOut)
def add_sale(payload: EggSaleCreate, db: Session = Depends(get_db),
             current=Depends(get_current_user)):
    storage = _ensure_storage(db)
    if payload.quantity > storage.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot sell {payload.quantity}; only {storage.quantity} in storage.",
        )
    total = payload.quantity * payload.price_per_unit
    sale = EggSale(
        sale_date=payload.sale_date,
        quantity=payload.quantity,
        price_per_unit=payload.price_per_unit,
        total_amount=total,
        customer_name=payload.customer_name,
        payment_status=payload.payment_status,
        notes=payload.notes,
        recorded_by=current.id,
    )
    db.add(sale)
    storage.quantity -= payload.quantity
    db.commit()
    db.refresh(sale)
    return sale


@router.get("/sales", response_model=List[EggSaleOut])
def list_sales(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return db.query(EggSale).order_by(EggSale.sale_date.desc()).limit(200).all()


@router.delete("/sales/{sale_id}")
def delete_sale(sale_id: int, db: Session = Depends(get_db),
                current=Depends(get_current_user)):
    s = db.query(EggSale).filter(EggSale.id == sale_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Not found")
    storage = _ensure_storage(db)
    storage.quantity += s.quantity
    db.delete(s)
    db.commit()
    return {"success": True}
