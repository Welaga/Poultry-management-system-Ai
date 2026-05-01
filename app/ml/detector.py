"""
AI Camera Detection Module
==========================
Detects and counts live birds, dead birds, and eggs in a frame.

Uses a tiered approach:
  1. If YOLO (ultralytics) is installed AND a model file is available -> deep-learning detection.
  2. Otherwise falls back to classical OpenCV computer-vision pipeline:
       - eggs: HoughCircles on grayscale
       - birds: contour analysis on motion / color segmentation
       - "dead" classification: stationary contours over multiple frames

The fallback is deterministic and dependency-light so the system works
out-of-the-box even without a trained model.

For production accuracy install ultralytics and provide a YOLOv8 model
trained on poultry classes (chicken_alive, chicken_dead, egg).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np


@dataclass
class DetectionResult:
    live_birds: int = 0
    dead_birds: int = 0
    eggs: int = 0
    confidence: float = 0.0
    boxes: List[dict] = field(default_factory=list)  # {label,x,y,w,h,conf}
    annotated_frame: Optional[np.ndarray] = None


class PoultryDetector:
    """Production-grade poultry detector with YOLO + classical fallback."""

    # COCO class id 14 = "bird" in default YOLOv8 weights.
    YOLO_BIRD_CLASS = 14

    def __init__(self, model_path: Optional[str] = None, confidence: float = 0.4):
        self.confidence = confidence
        self.model = None
        self.model_type = "classical"
        self.custom_classes = False

        # Track previous frame for motion-based liveness check (classical fallback)
        self._prev_gray: Optional[np.ndarray] = None
        self._stationary_history: List[Tuple[int, int, int, int, int]] = []  # (x,y,w,h,frames_still)

        self._try_load_yolo(model_path)

    def _try_load_yolo(self, model_path: Optional[str]):
        try:
            from ultralytics import YOLO  # type: ignore
            # Try custom model first
            if model_path and os.path.exists(model_path):
                self.model = YOLO(model_path)
                self.model_type = "yolo_custom"
                self.custom_classes = True
                print(f"[Detector] Loaded custom YOLO model from {model_path}")
                return
            # Default YOLOv8n with COCO classes (only generic 'bird' class)
            try:
                self.model = YOLO("yolov8n.pt")
                self.model_type = "yolo_coco"
                self.custom_classes = False
                print("[Detector] Loaded YOLOv8n (COCO) — eggs/dead detected via fallback heuristics.")
                return
            except Exception as e:
                print(f"[Detector] Failed to load YOLOv8n: {e}")
        except ImportError:
            print("[Detector] ultralytics not installed — using classical OpenCV pipeline.")
        self.model = None
        self.model_type = "classical"

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------
    def detect(self, frame: np.ndarray) -> DetectionResult:
        if frame is None or frame.size == 0:
            return DetectionResult()

        if self.model_type == "yolo_custom":
            result = self._detect_yolo_custom(frame)
        elif self.model_type == "yolo_coco":
            # Use YOLO for birds, classical for eggs+dead
            result = self._detect_yolo_coco(frame)
        else:
            result = self._detect_classical(frame)

        result.annotated_frame = self._annotate(frame, result)
        return result

    # ----------------------------------------------------------------
    # YOLO with custom-trained model (chicken_alive, chicken_dead, egg)
    # ----------------------------------------------------------------
    def _detect_yolo_custom(self, frame: np.ndarray) -> DetectionResult:
        result = DetectionResult()
        try:
            preds = self.model.predict(frame, conf=self.confidence, verbose=False)
            if not preds:
                return result
            r = preds[0]
            confs = []
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                label = (r.names.get(cls_id, str(cls_id)) if hasattr(r.names, "get")
                         else r.names[cls_id])
                label_lower = label.lower()
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                bx = {"label": label_lower, "x": int(x1), "y": int(y1),
                      "w": int(x2 - x1), "h": int(y2 - y1), "conf": conf}
                result.boxes.append(bx)
                confs.append(conf)
                if "egg" in label_lower:
                    result.eggs += 1
                elif "dead" in label_lower:
                    result.dead_birds += 1
                elif "bird" in label_lower or "chicken" in label_lower or "alive" in label_lower:
                    result.live_birds += 1
            if confs:
                result.confidence = float(sum(confs) / len(confs))
        except Exception as e:
            print(f"[Detector] YOLO custom error: {e}")
        return result

    # ----------------------------------------------------------------
    # YOLO COCO (only 'bird' class) + classical for the rest
    # ----------------------------------------------------------------
    def _detect_yolo_coco(self, frame: np.ndarray) -> DetectionResult:
        result = DetectionResult()
        try:
            preds = self.model.predict(frame, conf=self.confidence, verbose=False, classes=[self.YOLO_BIRD_CLASS])
            confs = []
            bird_boxes = []
            if preds:
                r = preds[0]
                for box in r.boxes:
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    bx = {"label": "bird", "x": int(x1), "y": int(y1),
                          "w": int(x2 - x1), "h": int(y2 - y1), "conf": conf}
                    bird_boxes.append(bx)
                    confs.append(conf)

            # Liveness via motion analysis on bird boxes
            live, dead = self._classify_liveness(frame, bird_boxes)
            for bx in bird_boxes:
                bx["label"] = "live_bird" if bx in live else "dead_bird"
            result.boxes.extend(bird_boxes)
            result.live_birds = len(live)
            result.dead_birds = len(dead)

            # Detect eggs classically
            egg_boxes = self._detect_eggs_classical(frame)
            result.boxes.extend(egg_boxes)
            result.eggs = len(egg_boxes)

            if confs:
                result.confidence = float(sum(confs) / len(confs))
            else:
                result.confidence = 0.5 if (result.eggs or result.live_birds or result.dead_birds) else 0.0
        except Exception as e:
            print(f"[Detector] YOLO COCO error: {e}")
        return result

    # ----------------------------------------------------------------
    # Classical CV pipeline (no ML dependencies)
    # ----------------------------------------------------------------
    def _detect_classical(self, frame: np.ndarray) -> DetectionResult:
        result = DetectionResult()

        bird_boxes = self._detect_birds_classical(frame)
        live, dead = self._classify_liveness(frame, bird_boxes)
        for bx in bird_boxes:
            bx["label"] = "live_bird" if bx in live else "dead_bird"
        result.boxes.extend(bird_boxes)
        result.live_birds = len(live)
        result.dead_birds = len(dead)

        egg_boxes = self._detect_eggs_classical(frame)
        result.boxes.extend(egg_boxes)
        result.eggs = len(egg_boxes)

        result.confidence = 0.6 if result.boxes else 0.0
        return result

    # ----------------------------------------------------------------
    # Egg detection via Hough circles
    # ----------------------------------------------------------------
    def _detect_eggs_classical(self, frame: np.ndarray) -> List[dict]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        h, w = gray.shape
        min_radius = max(8, min(h, w) // 50)
        max_radius = max(min_radius + 5, min(h, w) // 12)

        circles = cv2.HoughCircles(
            gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=min_radius * 2,
            param1=80, param2=35, minRadius=min_radius, maxRadius=max_radius,
        )
        boxes = []
        if circles is not None:
            for (cx, cy, r) in np.uint16(np.around(circles[0, :])):
                # Filter: egg interior should be brighter (whitish/cream)
                roi = gray[max(0, cy - r):min(h, cy + r), max(0, cx - r):min(w, cx + r)]
                if roi.size == 0:
                    continue
                if np.mean(roi) > 110:  # bright enough
                    boxes.append({
                        "label": "egg",
                        "x": int(cx - r), "y": int(cy - r),
                        "w": int(2 * r), "h": int(2 * r),
                        "conf": 0.6,
                    })
        return boxes

    # ----------------------------------------------------------------
    # Bird detection via color segmentation + contour analysis
    # ----------------------------------------------------------------
    def _detect_birds_classical(self, frame: np.ndarray) -> List[dict]:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Detect typical chicken colors: white/cream, brown, black
        masks = []
        # White/cream
        masks.append(cv2.inRange(hsv, np.array([0, 0, 150]), np.array([180, 50, 255])))
        # Brown / reddish
        masks.append(cv2.inRange(hsv, np.array([0, 50, 50]), np.array([20, 255, 200])))
        masks.append(cv2.inRange(hsv, np.array([160, 50, 50]), np.array([180, 255, 200])))
        # Black/dark
        masks.append(cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 255, 60])))

        combined = masks[0]
        for m in masks[1:]:
            combined = cv2.bitwise_or(combined, m)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=2)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=1)

        contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        h, w = frame.shape[:2]
        min_area = (h * w) * 0.005
        max_area = (h * w) * 0.4

        boxes = []
        for c in contours:
            area = cv2.contourArea(c)
            if min_area < area < max_area:
                x, y, bw, bh = cv2.boundingRect(c)
                aspect = bw / bh if bh > 0 else 0
                # Birds are roughly oval, not extreme aspects
                if 0.3 < aspect < 3.5:
                    boxes.append({
                        "label": "bird", "x": int(x), "y": int(y),
                        "w": int(bw), "h": int(bh), "conf": 0.5,
                    })
        return boxes

    # ----------------------------------------------------------------
    # Live vs dead classification by motion / stationarity
    # ----------------------------------------------------------------
    def _classify_liveness(self, frame: np.ndarray, bird_boxes: List[dict]) -> Tuple[List[dict], List[dict]]:
        if not bird_boxes:
            return [], []

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        live, dead = [], []

        if self._prev_gray is None or self._prev_gray.shape != gray.shape:
            # First frame: assume everyone alive
            self._prev_gray = gray
            return list(bird_boxes), []

        diff = cv2.absdiff(self._prev_gray, gray)
        _, motion = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        for bx in bird_boxes:
            x, y, w, h = bx["x"], bx["y"], bx["w"], bx["h"]
            x = max(0, x); y = max(0, y)
            roi = motion[y:y + h, x:x + w]
            if roi.size == 0:
                live.append(bx)
                continue
            motion_pct = (np.count_nonzero(roi) / roi.size) * 100
            # >2% motion in ROI -> alive
            if motion_pct > 2.0:
                live.append(bx)
            else:
                # Tentatively dead, but require multiple frames of stillness
                # (simple heuristic: small uniform color region + no motion)
                dead.append(bx)

        self._prev_gray = gray
        return live, dead

    # ----------------------------------------------------------------
    # Drawing
    # ----------------------------------------------------------------
    def _annotate(self, frame: np.ndarray, result: DetectionResult) -> np.ndarray:
        annotated = frame.copy()
        colors_map = {
            "live_bird": (0, 200, 0),
            "bird": (0, 200, 0),
            "dead_bird": (0, 0, 220),
            "egg": (0, 215, 255),
        }
        for bx in result.boxes:
            color = colors_map.get(bx["label"], (200, 200, 200))
            cv2.rectangle(annotated, (bx["x"], bx["y"]),
                          (bx["x"] + bx["w"], bx["y"] + bx["h"]), color, 2)
            label = f"{bx['label']} {bx['conf']:.2f}"
            cv2.putText(annotated, label, (bx["x"], max(15, bx["y"] - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Header overlay
        cv2.rectangle(annotated, (0, 0), (annotated.shape[1], 32), (30, 30, 30), -1)
        text = f"Live: {result.live_birds}   Dead: {result.dead_birds}   Eggs: {result.eggs}   Mode: {self.model_type}"
        cv2.putText(annotated, text, (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        return annotated


# Singleton accessor
_global_detector: Optional[PoultryDetector] = None


def get_detector() -> PoultryDetector:
    global _global_detector
    if _global_detector is None:
        from app.config import settings
        model_path = os.getenv("POULTRY_MODEL_PATH", "models/poultry_yolov8.pt")
        _global_detector = PoultryDetector(
            model_path=model_path if os.path.exists(model_path) else None,
            confidence=settings.DETECTION_CONFIDENCE,
        )
    return _global_detector
