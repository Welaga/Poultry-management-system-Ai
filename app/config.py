"""Application configuration."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings:
    APP_NAME = "Poultry Management System"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # Database (SQLite default; switch DATABASE_URL to MySQL/PostgreSQL in .env)
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'database' / 'poultry.db'}",
    )

    # JWT
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "change-me-in-production-use-a-long-random-string-32chars-min",
    )
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

    # Uploads
    UPLOAD_DIR = BASE_DIR / "static" / "uploads"
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".gif", ".webp",
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv",
    }

    # Alerts
    LOW_FEED_THRESHOLD_KG = 50.0
    HIGH_MORTALITY_THRESHOLD_PERCENT = 2.0  # daily mortality rate
    MAX_DAILY_DEATHS_ABSOLUTE = 20

    # Camera / AI
    CAMERA_DEVICE_INDEX = 0
    DETECTION_CONFIDENCE = 0.4

    # Default admin (created on first init)
    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ADMIN_PASSWORD = "admin123"
    DEFAULT_ADMIN_EMAIL = "admin@poultry.local"


settings = Settings()
