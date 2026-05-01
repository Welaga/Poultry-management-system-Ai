"""Authentication endpoints."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.utils.schemas import UserCreate, UserOut, Token, UserLogin
from app.utils.security import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_admin,
)
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=UserOut)
def register(payload: UserCreate, db: Session = Depends(get_db),
             current=Depends(require_admin)):
    """Only admin can create new users."""
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if payload.role not in ("admin", "worker"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'worker'")

    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_access_token(
        {"sub": user.username, "role": user.role, "id": user.id},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/token", response_model=Token)
def login_form(form_data: OAuth2PasswordRequestForm = Depends(),
               db: Session = Depends(get_db)):
    """OAuth2-compatible endpoint for Swagger UI."""
    return login(UserLogin(username=form_data.username, password=form_data.password), db)


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), current=Depends(require_admin)):
    return db.query(User).all()


@router.post("/logout")
def logout(current: User = Depends(get_current_user)):
    """Stateless JWT — client should drop token."""
    return {"message": "Logged out", "user": current.username}
