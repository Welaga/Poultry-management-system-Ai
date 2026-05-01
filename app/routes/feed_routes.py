"""Feed purchase, consumption, and inventory endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.feed import FeedPurchase, FeedConsumption, FeedInventory
from app.utils.schemas import (
    FeedPurchaseCreate, FeedPurchaseOut,
    FeedConsumptionCreate, FeedConsumptionOut,
    FeedInventoryOut,
)
from app.utils.security import get_current_user
from app.services.alert_service import AlertService

router = APIRouter()


def _get_or_create_inventory(db: Session, feed_type: str) -> FeedInventory:
    inv = db.query(FeedInventory).filter(FeedInventory.feed_type == feed_type).first()
    if not inv:
        inv = FeedInventory(feed_type=feed_type, quantity_kg=0.0)
        db.add(inv)
        db.commit()
        db.refresh(inv)
    return inv


@router.post("/purchase", response_model=FeedPurchaseOut)
def add_purchase(payload: FeedPurchaseCreate, db: Session = Depends(get_db),
                 current=Depends(get_current_user)):
    total = payload.quantity_kg * payload.price_per_kg
    purchase = FeedPurchase(
        feed_type=payload.feed_type,
        supplier=payload.supplier,
        quantity_kg=payload.quantity_kg,
        price_per_kg=payload.price_per_kg,
        total_cost=total,
        purchase_date=payload.purchase_date,
        notes=payload.notes,
        recorded_by=current.id,
    )
    db.add(purchase)
    inv = _get_or_create_inventory(db, payload.feed_type)
    inv.quantity_kg += payload.quantity_kg
    db.commit()
    db.refresh(purchase)
    return purchase


@router.get("/purchase", response_model=List[FeedPurchaseOut])
def list_purchases(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return db.query(FeedPurchase).order_by(FeedPurchase.purchase_date.desc()).limit(200).all()


@router.delete("/purchase/{pid}")
def delete_purchase(pid: int, db: Session = Depends(get_db),
                    current=Depends(get_current_user)):
    p = db.query(FeedPurchase).filter(FeedPurchase.id == pid).first()
    if not p:
        raise HTTPException(status_code=404, detail="Not found")
    inv = db.query(FeedInventory).filter(FeedInventory.feed_type == p.feed_type).first()
    if inv:
        inv.quantity_kg = max(0.0, inv.quantity_kg - p.quantity_kg)
    db.delete(p)
    db.commit()
    return {"success": True}


@router.post("/consumption", response_model=FeedConsumptionOut)
def add_consumption(payload: FeedConsumptionCreate, db: Session = Depends(get_db),
                    current=Depends(get_current_user)):
    inv = _get_or_create_inventory(db, payload.feed_type)
    if payload.quantity_kg > inv.quantity_kg:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock: only {inv.quantity_kg:.2f} kg of {payload.feed_type}.",
        )
    record = FeedConsumption(
        feed_type=payload.feed_type,
        quantity_kg=payload.quantity_kg,
        consumption_date=payload.consumption_date,
        batch_id=payload.batch_id,
        notes=payload.notes,
        recorded_by=current.id,
    )
    db.add(record)
    inv.quantity_kg -= payload.quantity_kg
    db.commit()
    db.refresh(record)
    AlertService.check_feed_alert(db)
    return record


@router.get("/consumption", response_model=List[FeedConsumptionOut])
def list_consumption(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return db.query(FeedConsumption).order_by(
        FeedConsumption.consumption_date.desc()
    ).limit(200).all()


@router.delete("/consumption/{cid}")
def delete_consumption(cid: int, db: Session = Depends(get_db),
                       current=Depends(get_current_user)):
    r = db.query(FeedConsumption).filter(FeedConsumption.id == cid).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    inv = db.query(FeedInventory).filter(FeedInventory.feed_type == r.feed_type).first()
    if inv:
        inv.quantity_kg += r.quantity_kg
    db.delete(r)
    db.commit()
    return {"success": True}


@router.get("/inventory", response_model=List[FeedInventoryOut])
def get_inventory(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return db.query(FeedInventory).order_by(FeedInventory.feed_type).all()
