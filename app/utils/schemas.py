"""Pydantic schemas for request/response validation."""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ----- Auth -----
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None
    role: str = "worker"


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ----- Bird -----
class BatchCreate(BaseModel):
    batch_code: str
    breed: str
    bird_type: str = "layer"
    initial_count: int = Field(..., gt=0)
    arrival_date: date
    growth_stage: str = "chick"
    age_weeks: int = 0
    cost_per_bird: float = 0.0
    notes: Optional[str] = None


class BatchOut(BaseModel):
    id: int
    batch_code: str
    breed: str
    bird_type: str
    initial_count: int
    current_count: int
    arrival_date: date
    growth_stage: str
    age_weeks: int
    cost_per_bird: float
    notes: Optional[str]

    class Config:
        from_attributes = True


class MortalityCreate(BaseModel):
    batch_id: int
    death_date: date
    count: int = Field(..., gt=0)
    cause: Optional[str] = None
    notes: Optional[str] = None


class MortalityOut(BaseModel):
    id: int
    batch_id: int
    death_date: date
    count: int
    cause: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


# ----- Egg -----
class EggCreate(BaseModel):
    batch_id: Optional[int] = None
    collection_date: date
    total_eggs: int = Field(..., ge=0)
    broken_eggs: int = 0
    notes: Optional[str] = None


class EggOut(BaseModel):
    id: int
    batch_id: Optional[int]
    collection_date: date
    total_eggs: int
    broken_eggs: int
    good_eggs: int
    notes: Optional[str]

    class Config:
        from_attributes = True


class EggSaleCreate(BaseModel):
    sale_date: date
    quantity: int = Field(..., gt=0)
    price_per_unit: float = Field(..., gt=0)
    customer_name: Optional[str] = None
    payment_status: str = "paid"
    notes: Optional[str] = None


class EggSaleOut(BaseModel):
    id: int
    sale_date: date
    quantity: int
    price_per_unit: float
    total_amount: float
    customer_name: Optional[str]
    payment_status: str

    class Config:
        from_attributes = True


# ----- Feed -----
class FeedPurchaseCreate(BaseModel):
    feed_type: str
    supplier: Optional[str] = None
    quantity_kg: float = Field(..., gt=0)
    price_per_kg: float = Field(..., gt=0)
    purchase_date: date
    notes: Optional[str] = None


class FeedPurchaseOut(BaseModel):
    id: int
    feed_type: str
    supplier: Optional[str]
    quantity_kg: float
    price_per_kg: float
    total_cost: float
    purchase_date: date
    notes: Optional[str]

    class Config:
        from_attributes = True


class FeedConsumptionCreate(BaseModel):
    feed_type: str
    quantity_kg: float = Field(..., gt=0)
    consumption_date: date
    batch_id: Optional[int] = None
    notes: Optional[str] = None


class FeedConsumptionOut(BaseModel):
    id: int
    feed_type: str
    quantity_kg: float
    consumption_date: date
    batch_id: Optional[int]
    notes: Optional[str]

    class Config:
        from_attributes = True


class FeedInventoryOut(BaseModel):
    id: int
    feed_type: str
    quantity_kg: float

    class Config:
        from_attributes = True


# ----- Health -----
class HealthCreate(BaseModel):
    batch_id: Optional[int] = None
    disease_name: str
    symptoms: Optional[str] = None
    diagnosis_date: date
    affected_count: int = 0
    treatment: Optional[str] = None
    medication: Optional[str] = None
    cost: float = 0.0
    status: str = "ongoing"
    notes: Optional[str] = None


class HealthOut(BaseModel):
    id: int
    batch_id: Optional[int]
    disease_name: str
    symptoms: Optional[str]
    diagnosis_date: date
    affected_count: int
    treatment: Optional[str]
    medication: Optional[str]
    cost: float
    status: str

    class Config:
        from_attributes = True


class VaccinationCreate(BaseModel):
    batch_id: Optional[int] = None
    vaccine_name: str
    scheduled_date: date
    administered: bool = False
    administered_date: Optional[date] = None
    administered_by: Optional[str] = None
    dosage: Optional[str] = None
    cost: float = 0.0
    notes: Optional[str] = None


class VaccinationOut(BaseModel):
    id: int
    batch_id: Optional[int]
    vaccine_name: str
    scheduled_date: date
    administered: bool
    administered_date: Optional[date]
    administered_by: Optional[str]
    dosage: Optional[str]
    cost: float

    class Config:
        from_attributes = True


# ----- Chatbot -----
class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = []


# ----- Alert -----
class AlertOut(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    message: str
    is_read: bool
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True
