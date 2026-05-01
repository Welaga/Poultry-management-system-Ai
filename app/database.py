"""Database engine, session, and initialization."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

from app.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    poolclass=StaticPool if settings.DATABASE_URL.startswith("sqlite") else None,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables and seed default admin if missing."""
    # Import models so Base sees them before create_all
    from app.models import (
        user, bird, egg, feed, health, file_record, alert, detection
    )  # noqa: F401

    Base.metadata.create_all(bind=engine)

    # Seed default admin
    from app.models.user import User
    from app.utils.security import hash_password

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == settings.DEFAULT_ADMIN_USERNAME).first()
        if not existing:
            admin = User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                email=settings.DEFAULT_ADMIN_EMAIL,
                hashed_password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
                role="admin",
                full_name="Farm Administrator",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"[DB] Created default admin: {settings.DEFAULT_ADMIN_USERNAME} / {settings.DEFAULT_ADMIN_PASSWORD}")
    finally:
        db.close()
