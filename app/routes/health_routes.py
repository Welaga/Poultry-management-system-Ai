"""Health and vaccination endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.health import HealthRecord, Vaccination
from app.utils.schemas import (
    HealthCreate, HealthOut, VaccinationCreate, VaccinationOut
)
from app.utils.security import get_current_user

router = APIRouter()


# ----- Disease records -----
@router.post("/disease", response_model=HealthOut)
def add_disease(payload: HealthCreate, db: Session = Depends(get_db),
                current=Depends(get_current_user)):
    record = HealthRecord(
        batch_id=payload.batch_id,
        disease_name=payload.disease_name,
        symptoms=payload.symptoms,
        diagnosis_date=payload.diagnosis_date,
        affected_count=payload.affected_count,
        treatment=payload.treatment,
        medication=payload.medication,
        cost=payload.cost,
        status=payload.status,
        notes=payload.notes,
        recorded_by=current.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/disease", response_model=List[HealthOut])
def list_diseases(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return db.query(HealthRecord).order_by(HealthRecord.diagnosis_date.desc()).limit(200).all()


@router.put("/disease/{did}", response_model=HealthOut)
def update_disease(did: int, payload: HealthCreate, db: Session = Depends(get_db),
                   current=Depends(get_current_user)):
    r = db.query(HealthRecord).filter(HealthRecord.id == did).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in payload.model_dump().items():
        setattr(r, k, v)
    db.commit()
    db.refresh(r)
    return r


@router.delete("/disease/{did}")
def delete_disease(did: int, db: Session = Depends(get_db),
                   current=Depends(get_current_user)):
    r = db.query(HealthRecord).filter(HealthRecord.id == did).first()
    if not r:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(r)
    db.commit()
    return {"success": True}


# ----- Vaccinations -----
@router.post("/vaccination", response_model=VaccinationOut)
def add_vaccination(payload: VaccinationCreate, db: Session = Depends(get_db),
                    current=Depends(get_current_user)):
    v = Vaccination(
        batch_id=payload.batch_id,
        vaccine_name=payload.vaccine_name,
        scheduled_date=payload.scheduled_date,
        administered=payload.administered,
        administered_date=payload.administered_date,
        administered_by=payload.administered_by,
        dosage=payload.dosage,
        cost=payload.cost,
        notes=payload.notes,
        recorded_by=current.id,
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


@router.get("/vaccination", response_model=List[VaccinationOut])
def list_vaccinations(db: Session = Depends(get_db), current=Depends(get_current_user)):
    return db.query(Vaccination).order_by(Vaccination.scheduled_date.desc()).limit(200).all()


@router.put("/vaccination/{vid}", response_model=VaccinationOut)
def update_vaccination(vid: int, payload: VaccinationCreate, db: Session = Depends(get_db),
                       current=Depends(get_current_user)):
    v = db.query(Vaccination).filter(Vaccination.id == vid).first()
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    for k, val in payload.model_dump().items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    return v


@router.delete("/vaccination/{vid}")
def delete_vaccination(vid: int, db: Session = Depends(get_db),
                       current=Depends(get_current_user)):
    v = db.query(Vaccination).filter(Vaccination.id == vid).first()
    if not v:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(v)
    db.commit()
    return {"success": True}
