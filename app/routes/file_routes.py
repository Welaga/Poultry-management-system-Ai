"""File upload and management endpoints."""
import os
import uuid
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.file_record import FileRecord
from app.utils.security import get_current_user

router = APIRouter()

settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    description: str = Form(""),
    category: str = Form("general"),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")

    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest = settings.UPLOAD_DIR / safe_name

    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    with open(dest, "wb") as f:
        f.write(contents)

    file_type = "image" if ext in {".jpg", ".jpeg", ".png", ".gif", ".webp"} else "document"

    record = FileRecord(
        filename=safe_name,
        original_name=file.filename,
        file_path=str(dest),
        file_type=file_type,
        file_size=len(contents),
        description=description,
        category=category,
        uploaded_by=current.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "filename": record.filename,
        "original_name": record.original_name,
        "url": f"/static/uploads/{safe_name}",
        "file_type": file_type,
        "size": len(contents),
    }


@router.get("/list")
def list_files(category: str | None = None, db: Session = Depends(get_db),
               current=Depends(get_current_user)):
    q = db.query(FileRecord)
    if category:
        q = q.filter(FileRecord.category == category)
    files = q.order_by(FileRecord.uploaded_at.desc()).limit(500).all()
    return {
        "files": [
            {
                "id": f.id,
                "filename": f.filename,
                "original_name": f.original_name,
                "url": f"/static/uploads/{f.filename}",
                "file_type": f.file_type,
                "category": f.category,
                "description": f.description,
                "size": f.file_size,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
            } for f in files
        ]
    }


@router.delete("/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db),
                current=Depends(get_current_user)):
    f = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        if os.path.exists(f.file_path):
            os.remove(f.file_path)
    except Exception:
        pass
    db.delete(f)
    db.commit()
    return {"success": True}


@router.get("/download/{file_id}")
def download_file(file_id: int, db: Session = Depends(get_db),
                  current=Depends(get_current_user)):
    f = db.query(FileRecord).filter(FileRecord.id == file_id).first()
    if not f or not os.path.exists(f.file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(f.file_path, filename=f.original_name)
