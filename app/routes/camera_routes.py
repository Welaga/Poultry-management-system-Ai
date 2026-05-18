"""AI Camera detection endpoints — image upload, webcam stream, and live counts."""
import base64
from datetime import datetime
from typing import Optional

import cv2
import numpy as np
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.detection import CameraDetection
from app.ml.detector import get_detector
from app.utils.security import get_current_user, decode_token
from app.models.user import User

router = APIRouter()


def _get_stream_user(
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Accept JWT from ?token= query param (needed for <img src> MJPEG streams)."""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(token)
        username: str = payload.get("sub", "")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Shared latest-frame state for streaming
_camera_state = {
    "active": False,
    "live": 0,
    "dead": 0,
    "eggs": 0,
    "last_update": None,
}


@router.post("/detect-image")
async def detect_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
):
    """Upload an image and run detection."""
    contents = await file.read()
    npimg = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Invalid image")

    detector = get_detector()
    result = detector.detect(frame)

    record = CameraDetection(
        live_birds_count=result.live_birds,
        dead_birds_count=result.dead_birds,
        eggs_count=result.eggs,
        confidence_avg=int(result.confidence * 100),
        source="upload",
    )
    db.add(record)
    db.commit()

    # Encode annotated frame as base64
    annotated_b64 = ""
    if result.annotated_frame is not None:
        ok, buf = cv2.imencode(".jpg", result.annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ok:
            annotated_b64 = base64.b64encode(buf.tobytes()).decode("ascii")

    return {
        "live_birds": result.live_birds,
        "dead_birds": result.dead_birds,
        "eggs": result.eggs,
        "confidence": round(result.confidence, 3),
        "boxes": result.boxes,
        "annotated_image": f"data:image/jpeg;base64,{annotated_b64}" if annotated_b64 else None,
        "model": detector.model_type,
    }


def _gen_stream(db_factory):
    """Generator that yields MJPEG frames from the webcam with detection overlays."""
    cap = cv2.VideoCapture(settings.CAMERA_DEVICE_INDEX)
    if not cap.isOpened():
        # Provide a placeholder frame
        placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(placeholder, "Camera not available", (40, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        ok, buf = cv2.imencode(".jpg", placeholder)
        if ok:
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
        return

    detector = get_detector()
    _camera_state["active"] = True
    frame_count = 0
    last_save = datetime.utcnow()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            # Run detection every 5 frames to save CPU
            frame_count += 1
            if frame_count % 5 == 0:
                result = detector.detect(frame)
                _camera_state["live"] = result.live_birds
                _camera_state["dead"] = result.dead_birds
                _camera_state["eggs"] = result.eggs
                _camera_state["last_update"] = datetime.utcnow().isoformat()
                annotated = result.annotated_frame if result.annotated_frame is not None else frame

                # Persist every ~30 seconds
                if (datetime.utcnow() - last_save).total_seconds() > 30:
                    try:
                        db = db_factory()
                        rec = CameraDetection(
                            live_birds_count=result.live_birds,
                            dead_birds_count=result.dead_birds,
                            eggs_count=result.eggs,
                            confidence_avg=int(result.confidence * 100),
                            source="webcam",
                        )
                        db.add(rec)
                        db.commit()
                        db.close()
                        last_save = datetime.utcnow()
                    except Exception as e:
                        print(f"[camera_routes] save failed: {e}")
            else:
                annotated = frame
                # Re-overlay last counts
                cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 32), (30, 30, 30), -1)
                text = f"Live: {_camera_state['live']}   Dead: {_camera_state['dead']}   Eggs: {_camera_state['eggs']}"
                cv2.putText(annotated, text, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

            ok2, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if not ok2:
                continue
            yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n")
    finally:
        cap.release()
        _camera_state["active"] = False


@router.get("/stream")
def stream(current=Depends(_get_stream_user)):
    """MJPEG live stream with on-the-fly detection. Auth via ?token= query param."""
    from app.database import SessionLocal
    return StreamingResponse(
        _gen_stream(SessionLocal),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={"Cache-Control": "no-cache, no-store"},
    )


@router.get("/live-counts")
def live_counts(current=Depends(get_current_user)):
    return _camera_state


@router.get("/history")
def detection_history(limit: int = 50, db: Session = Depends(get_db),
                      current=Depends(get_current_user)):
    rows = (
        db.query(CameraDetection)
        .order_by(CameraDetection.detection_time.desc())
        .limit(limit)
        .all()
    )
    return {
        "history": [
            {
                "id": r.id,
                "time": r.detection_time.isoformat() if r.detection_time else None,
                "live": r.live_birds_count,
                "dead": r.dead_birds_count,
                "eggs": r.eggs_count,
                "confidence": r.confidence_avg,
                "source": r.source,
            } for r in rows
        ]
    }
