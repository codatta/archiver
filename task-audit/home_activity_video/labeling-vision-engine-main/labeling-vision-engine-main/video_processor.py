import cv2
import numpy as np
import subprocess
import shutil
import uuid
import os
import logging
from pathlib import Path
from typing import Callable, Optional

from device_config import DEVICE, HALF, IMGSZ, IMGSZ_POSE, IS_GPU, DEFAULT_YOLO_MODEL_FOR_DEVICE, TORCH_COMPILE

logger = logging.getLogger(__name__)

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None

# ─── Video info ────────────────────────────────────────────────────────────────

def get_video_info(video_path: str) -> dict:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    duration_ms = int(total_frames / fps * 1000)
    return {
        "fps": fps,
        "total_frames": total_frames,
        "duration_ms": duration_ms,
        "width": width,
        "height": height,
    }


# ─── Quality scoring ───────────────────────────────────────────────────────────

def compute_blur_score(frame: np.ndarray) -> float:
    """Laplacian variance — higher = sharper image."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def compute_brightness(frame: np.ndarray) -> float:
    """Mean V channel in HSV (0–255)."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    return float(np.mean(hsv[:, :, 2]))


def score_clip(video_path: str, start_ms: int, end_ms: int, sample_count: int = 5) -> dict:
    """Sample frames from the clip and return avg blur + brightness."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    duration_ms = end_ms - start_ms
    step_ms = duration_ms / (sample_count + 1)

    blurs, brights = [], []
    for i in range(1, sample_count + 1):
        ts = start_ms + int(step_ms * i)
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(ts / 1000 * fps))
        ret, frame = cap.read()
        if ret:
            blurs.append(compute_blur_score(frame))
            brights.append(compute_brightness(frame))

    cap.release()
    return {
        "blur_score": round(float(np.mean(blurs)), 1) if blurs else 0.0,
        "brightness": round(float(np.mean(brights)), 1) if brights else 0.0,
    }


# ─── Thumbnail extraction ──────────────────────────────────────────────────────

def extract_thumbnail(
    video_path: str,
    ts_ms: int,
    output_path: str,
    size: tuple = (320, 180),
) -> bool:
    """Extract the frame at ts_ms, resize and save as JPEG thumbnail."""
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(ts_ms / 1000 * fps))
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return False
    resized = cv2.resize(frame, size)
    return cv2.imwrite(output_path, resized, [cv2.IMWRITE_JPEG_QUALITY, 82])


# ─── Person detection ────────────────────────────────────────────────────────

# ── HOG detector ──────────────────────────────────────────────────────────────

_hog: Optional[cv2.HOGDescriptor] = None

def _get_hog() -> cv2.HOGDescriptor:
    """Lazy-init the HOG+SVM pedestrian detector (shared instance)."""
    global _hog
    if _hog is None:
        _hog = cv2.HOGDescriptor()
        _hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    return _hog


def _hog_has_person(frame: np.ndarray) -> bool:
    h, w = frame.shape[:2]
    scale = 480 / max(h, w)
    if scale < 1.0:
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
    rects, _ = _get_hog().detectMultiScale(
        frame,
        hitThreshold=-0.5,   # lower = more sensitive; catches partial/occluded persons
        winStride=(8, 8),
        padding=(16, 16),    # larger padding detects persons near frame edges
        scale=1.05,
    )
    return len(rects) > 0


# ── YOLOv8 detector ───────────────────────────────────────────────────────────

try:
    from ultralytics import YOLO as _YOLO_cls
    YOLO_AVAILABLE = True
except ImportError:
    _YOLO_cls = None  # type: ignore
    YOLO_AVAILABLE = False

_MODELS_DIR = Path(__file__).parent / "models"
_MODELS_DIR.mkdir(parents=True, exist_ok=True)

# Default model is chosen by device: yolov8m on GPU (more accurate),
# yolov8s on CPU (faster); auto-downloads if not cached locally.
DEFAULT_YOLO_MODEL = DEFAULT_YOLO_MODEL_FOR_DEVICE

_yolo_model = None
_yolo_model_loaded: Optional[str] = None   # track which model file is active


def _get_yolo(model_name: str = DEFAULT_YOLO_MODEL):
    """Lazy-init YOLO detection model, reloads if model_name changes."""
    global _yolo_model, _yolo_model_loaded
    if _yolo_model is None or _yolo_model_loaded != model_name:
        if not YOLO_AVAILABLE:
            raise RuntimeError("ultralytics not installed — run: pip install ultralytics")
        local_path = _MODELS_DIR / model_name
        logger.info("Loading YOLO model: %s (device=%s)", local_path, DEVICE)
        _yolo_model = _YOLO_cls(str(local_path))
        _yolo_model.to(DEVICE)
        if TORCH_COMPILE:
            import torch
            _yolo_model.model = torch.compile(_yolo_model.model)
            logger.info("YOLO model compiled with torch.compile()")
        # Warmup: eliminates CUDA JIT cold-start on first real inference
        if IS_GPU:
            _dummy = np.zeros((320, 320, 3), dtype=np.uint8)
            _yolo_model.predict(_dummy, classes=[0], conf=0.5, verbose=False, half=HALF)
            logger.info("YOLO model warmed up")
        _yolo_model_loaded = model_name
    return _yolo_model


def _yolo_has_person(frame: np.ndarray, conf: float = 0.35,
                     model_name: str = DEFAULT_YOLO_MODEL) -> bool:
    results = _get_yolo(model_name).predict(
        frame, classes=[0], conf=conf, verbose=False, half=HALF, imgsz=IMGSZ
    )
    return len(results[0].boxes) > 0


# ── YOLOv8-Pose detector ──────────────────────────────────────────────────────
# Uses yolov8n-pose (nano-pose) by default — lightweight, auto-downloads.
# Pose models detect people via skeleton keypoints, which is more robust
# for non-standard poses (crouching, bending, partial occlusion) than
# regular object-detection models.

DEFAULT_POSE_MODEL = "yolov8n-pose.pt"

_pose_model = None


def _get_pose_model(model_name: str = DEFAULT_POSE_MODEL):
    """Lazy-init YOLOv8-pose model, shared instance."""
    global _pose_model
    if _pose_model is None:
        if not YOLO_AVAILABLE:
            raise RuntimeError("ultralytics not installed — run: pip install ultralytics")
        local_path = _MODELS_DIR / model_name
        logger.info("Loading pose model: %s (device=%s)", local_path, DEVICE)
        _pose_model = _YOLO_cls(str(local_path))
        _pose_model.to(DEVICE)
        if TORCH_COMPILE:
            import torch
            _pose_model.model = torch.compile(_pose_model.model)
            logger.info("Pose model compiled with torch.compile()")
        if IS_GPU:
            _dummy = np.zeros((320, 320, 3), dtype=np.uint8)
            _pose_model.predict(_dummy, conf=0.5, verbose=False, half=HALF)
            logger.info("Pose model warmed up")
    return _pose_model


def _pose_has_person(frame: np.ndarray, conf: float = 0.30) -> bool:
    """
    Detect a person via pose estimation (skeleton keypoints).
    More robust than HOG for crouching/bending/occluded persons.
    Returns True if at least one skeleton is detected above confidence.
    """
    results = _get_pose_model().predict(frame, conf=conf, verbose=False, half=HALF, imgsz=IMGSZ_POSE)
    return len(results[0].boxes) > 0


# ── Unified dispatcher ────────────────────────────────────────────────────────

def detect_person_in_clip(
    video_path: str,
    start_ms: int,
    end_ms: int,
    detector: str = "hog",
    sample_count: int = 3,
) -> bool:
    """
    Sample `sample_count` frames from the clip and return True if a person
    is detected in any frame.

    detector: 'hog' (OpenCV HOG+SVM), 'yolo' (YOLOv8s), or 'pose' (YOLOv8n-pose).
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    step_ms = (end_ms - start_ms) / (sample_count + 1)
    found = False

    if detector == "yolo":
        detect_fn = _yolo_has_person
    elif detector == "pose":
        detect_fn = _pose_has_person
    else:
        detect_fn = _hog_has_person

    for i in range(1, sample_count + 1):
        ts = start_ms + int(step_ms * i)
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(ts / 1000 * fps))
        ret, frame = cap.read()
        if not ret:
            continue
        if detect_fn(frame):
            found = True
            break

    cap.release()
    return found


# ── Fine-grained person detector factory ──────────────────────────────────────
#
# Return values (str):
#   'keep'    – person present and all configured spatial/pose filters passed
#   'review'  – person detected but fails a filter  OR  motion present but no
#               person detected by any stage (possible occlusion / crouching)
#   'discard' – no person found and no ambiguity (HOG single mode only)
#
# Three-class cascade design:
#   Stage-1 (coarse HOG, ~1 ms):
#     • person in centre zone  → 'keep' fast path (skip Stage-2)
#     • person at edge only    → run Stage-2 (HOG may have missed a centre person)
#     • no person              → run Stage-2
#   Stage-2 (YOLO/Pose, full filters):
#     • person + all filters   → 'keep'
#     • person + fails filter  → 'review' (edge / no arms)
#     • no person detected     → 'review' (motion present but unverifiable;
#                                possible crouching / obstructed / unusual pose)

def make_person_detector(
    detector: str = "hog",
    yolo_model: str = DEFAULT_YOLO_MODEL,
    require_center: bool = False,
    center_margin: float = 0.20,
    require_arms: bool = False,
    arm_conf_threshold: float = 0.30,
    detection_strategy: str = "single",
) -> "Callable[[np.ndarray], tuple]":
    """
    Return a frame → str classifier.  See module-level docstring for details.
    """

    def _in_center(cx: float, cy: float) -> bool:
        return (center_margin <= cx <= 1 - center_margin
                and center_margin <= cy <= 1 - center_margin)

    # ── Stage-1: coarse HOG with centre check (cascade only) ─────────────────
    # Returns 'centre' | 'edge' | 'miss'
    def _coarse_hog_classify(frame: np.ndarray) -> str:
        h, w = frame.shape[:2]
        scale = 480 / max(h, w)
        if scale < 1.0:
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
            h, w = frame.shape[:2]
        rects, _ = _get_hog().detectMultiScale(
            frame,
            hitThreshold=-1.0,
            winStride=(16, 16),
            padding=(8, 8),
            scale=1.1,
        )
        if len(rects) == 0:
            return "miss"
        if not require_center:
            return "centre"   # any detection counts as centre if no spatial filter
        for (rx, ry, rw, rh) in rects:
            if _in_center((rx + rw / 2) / w, (ry + rh / 2) / h):
                return "centre"
        return "edge"         # person found but only outside centre zone

    # ── Fine HOG (single mode) ────────────────────────────────────────────────
    def _detect_hog(frame: np.ndarray) -> tuple:
        h, w = frame.shape[:2]
        scale = 480 / max(h, w)
        if scale < 1.0:
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
            h, w = frame.shape[:2]
        rects, _ = _get_hog().detectMultiScale(
            frame,
            hitThreshold=-0.5,
            winStride=(8, 8),
            padding=(16, 16),
            scale=1.05,
        )
        if len(rects) == 0:
            return ("discard", "")   # HOG is high-recall; miss = likely no person
        if not require_center:
            return ("keep", "")
        for (rx, ry, rw, rh) in rects:
            if _in_center((rx + rw / 2) / w, (ry + rh / 2) / h):
                return ("keep", "")
        return ("review", "edge")    # person exists but only at edge

    # ── Fine YOLO ─────────────────────────────────────────────────────────────
    def _detect_yolo(frame: np.ndarray) -> tuple:
        results = _get_yolo(yolo_model).predict(
            frame, classes=[0], conf=0.35, verbose=False, half=HALF, imgsz=IMGSZ
        )
        if not results or len(results[0].boxes) == 0:
            return ("review", "no_person")   # YOLO may miss crouching/obstructed persons
        if not require_center:
            return ("keep", "")
        h, w = frame.shape[:2]
        for box in results[0].boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            if _in_center((x1 + x2) / 2 / w, (y1 + y2) / 2 / h):
                return ("keep", "")
        return ("review", "edge")    # person found but only at edge

    # ── Fine Pose ─────────────────────────────────────────────────────────────
    # COCO keypoints: 5=L-shoulder 6=R-shoulder 7=L-elbow 8=R-elbow
    #                 9=L-wrist   10=R-wrist
    _ARM_KP_IDX = [5, 6, 7, 8, 9, 10]

    def _detect_pose(frame: np.ndarray) -> tuple:
        results = _get_pose_model().predict(frame, conf=0.30, verbose=False, half=HALF, imgsz=IMGSZ_POSE)
        if not results or len(results[0].boxes) == 0:
            return ("review", "no_person")   # Pose may miss unusual postures
        h, w = frame.shape[:2]
        last_reason = "no_person"
        for i, box in enumerate(results[0].boxes):
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            centre_ok = (not require_center) or _in_center(
                (x1 + x2) / 2 / w, (y1 + y2) / 2 / h
            )
            if not centre_ok:
                last_reason = "edge"
                continue
            if require_arms:
                kps_obj = results[0].keypoints
                if kps_obj is None or i >= len(kps_obj.data):
                    last_reason = "no_arms"
                    continue
                kps = kps_obj.data[i]
                if not bool((kps[_ARM_KP_IDX, 2] > arm_conf_threshold).any()):
                    last_reason = "no_arms"   # person in centre but arms not visible
                    continue
            return ("keep", "")    # this person passes all filters
        return ("review", last_reason)   # person detected but no candidate passed

    # ── Assemble final callable ───────────────────────────────────────────────
    if detector == "pose":
        fine_fn = _detect_pose
    elif detector == "yolo":
        fine_fn = _detect_yolo
    else:
        fine_fn = _detect_hog

    if detection_strategy == "cascade" and detector in ("yolo", "pose"):
        def _cascade(frame: np.ndarray) -> tuple:
            # Stage-1: coarse HOG with centre check
            coarse = _coarse_hog_classify(frame)
            if coarse == "centre":
                return ("keep", "")   # fast path: obvious centre person confirmed
            # Stage-2: accurate fine detector (coarse found edge person OR nothing)
            fine_result, fine_reason = fine_fn(frame)
            if fine_result == "keep":
                return ("keep", "")
            # coarse found edge person → definitely review with edge/no_arms reason
            # coarse found nothing but fine also found nothing → possible occlusion
            if coarse == "edge":
                return ("review", fine_reason or "edge")
            return ("review", "no_person")
        return _cascade

    return fine_fn


# ─── Single-frame annotation helper ───────────────────────────────────────────

_ANNO_ARM_KP_IDX = [5, 6, 7, 8, 9, 10]   # COCO: L/R shoulder, elbow, wrist


def get_frame_annotations(
    frame_path: str,
    detector: str = "yolo",
    yolo_model: str = DEFAULT_YOLO_MODEL,
    arm_conf_threshold: float = 0.30,
    detect_objects: bool = False,
    object_conf_threshold: float = 0.35,
) -> dict:
    """
    Run person detection on a single frame and return normalised coordinates.

    detector : 'yolo' → person bboxes only (fast, GPU optional)
               'pose' → person bboxes + arm keypoints
               'hog'  → person bboxes only (CPU, no GPU needed)

    Returns
    -------
    {
      "person_boxes"  : [[x1, y1, x2, y2, conf], …],  # float 0-1, normalised
      "arm_keypoints" : [[x, y, conf], …],             # float 0-1, normalised
      "hand_keypoints": [[x, y, conf], …],             # wrists only, float 0-1
      "object_boxes"  : [{"label": str, "conf": float, "bbox": [x1,y1,x2,y2]}, …],
      "width"  : int,
      "height" : int,
    }
    """
    frame = cv2.imread(frame_path)
    if frame is None:
        return {
            "person_boxes": [],
            "arm_keypoints": [],
            "hand_keypoints": [],
            "object_boxes": [],
            "width": 0,
            "height": 0,
        }

    h, w = frame.shape[:2]
    person_boxes: list = []
    arm_keypoints: list = []
    hand_keypoints: list = []
    object_boxes: list = []

    if detector == "hog":
        scale = 480 / max(h, w)
        small = cv2.resize(frame, (int(w * scale), int(h * scale))) if scale < 1.0 else frame.copy()
        sh, sw = small.shape[:2]
        rects, _ = _get_hog().detectMultiScale(
            small, hitThreshold=-0.5, winStride=(8, 8), padding=(16, 16),
            scale=1.05,
        )
        for (rx, ry, rw, rh) in rects:
            person_boxes.append([rx / sw, ry / sh, (rx + rw) / sw, (ry + rh) / sh, 1.0])

    elif detector == "yolo":
        results = _get_yolo(yolo_model).predict(
            frame, classes=[0], conf=0.35, verbose=False, half=HALF, imgsz=IMGSZ
        )
        if results and len(results[0].boxes) > 0:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                person_boxes.append([x1 / w, y1 / h, x2 / w, y2 / h, float(box.conf[0])])

        if detect_objects:
            obj_results = _get_yolo(yolo_model).predict(
                frame, conf=object_conf_threshold, verbose=False, half=HALF, imgsz=IMGSZ
            )
            if obj_results and len(obj_results[0].boxes) > 0:
                names = obj_results[0].names or {}
                for box in obj_results[0].boxes:
                    cls_id = int(box.cls[0])
                    if cls_id == 0:
                        continue
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    object_boxes.append(
                        {
                            "label": str(names.get(cls_id, f"class_{cls_id}")),
                            "conf": float(box.conf[0]),
                            "bbox": [x1 / w, y1 / h, x2 / w, y2 / h],
                        }
                    )

    elif detector == "pose":
        results = _get_pose_model().predict(frame, conf=0.30, verbose=False, half=HALF, imgsz=IMGSZ_POSE)
        if results and len(results[0].boxes) > 0:
            for i, box in enumerate(results[0].boxes):
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                person_boxes.append([x1 / w, y1 / h, x2 / w, y2 / h, float(box.conf[0])])
                kps_obj = results[0].keypoints
                if kps_obj is not None and i < len(kps_obj.data):
                    kps = kps_obj.data[i]
                    for ki in _ANNO_ARM_KP_IDX:
                        kx = float(kps[ki][0])
                        ky = float(kps[ki][1])
                        kc = float(kps[ki][2])
                        if kc > arm_conf_threshold:
                            arm_keypoints.append([kx / w, ky / h, kc])
                    # wrists only: 9=left wrist, 10=right wrist
                    for wi in [9, 10]:
                        kx = float(kps[wi][0])
                        ky = float(kps[wi][1])
                        kc = float(kps[wi][2])
                        if kc > arm_conf_threshold:
                            hand_keypoints.append([kx / w, ky / h, kc])

        if detect_objects:
            obj_results = _get_yolo(yolo_model).predict(
                frame, conf=object_conf_threshold, verbose=False, half=HALF, imgsz=IMGSZ
            )
            if obj_results and len(obj_results[0].boxes) > 0:
                names = obj_results[0].names or {}
                for box in obj_results[0].boxes:
                    cls_id = int(box.cls[0])
                    if cls_id == 0:
                        continue
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    object_boxes.append(
                        {
                            "label": str(names.get(cls_id, f"class_{cls_id}")),
                            "conf": float(box.conf[0]),
                            "bbox": [x1 / w, y1 / h, x2 / w, y2 / h],
                        }
                    )

    return {
        "person_boxes": person_boxes,
        "arm_keypoints": arm_keypoints,
        "hand_keypoints": hand_keypoints,
        "object_boxes": object_boxes,
        "width": w,
        "height": h,
    }


# ─── Motion / scene detection ──────────────────────────────────────────────────

def _histogram_diff(frame_a: np.ndarray, frame_b: np.ndarray) -> float:
    """Bhattacharyya distance between HSV-H histograms; high value = scene cut."""
    def hue_hist(f):
        hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV)
        h = cv2.calcHist([hsv], [0], None, [64], [0, 180])
        cv2.normalize(h, h)
        return h
    return float(cv2.compareHist(hue_hist(frame_a), hue_hist(frame_b), cv2.HISTCMP_BHATTACHARYYA))


def detect_motion_segments(
    video_path: str,
    sample_fps: float = 5.0,
    motion_threshold: float = 0.015,
    scene_cut_threshold: float = 0.45,
    min_duration_ms: int = 2000,
    max_duration_ms: int = 15000,
    merge_gap_ms: int = 1500,
    padding_ms: int = 500,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> tuple:
    """
    Detect motion segments using MOG2 background subtraction.
    Scene cuts (histogram jump) force a segment boundary.
    Returns (segments: list[tuple[int,int]], total_duration_ms: int).
    """
    cap = cv2.VideoCapture(video_path)
    original_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_duration_ms = int(total_frames / original_fps * 1000)

    if total_frames == 0:
        cap.release()
        return _equal_segments(total_duration_ms, 8000), total_duration_ms

    frame_skip = max(1, int(original_fps / sample_fps))
    fgbg = cv2.createBackgroundSubtractorMOG2(
        history=300, varThreshold=40, detectShadows=False
    )

    motion_events: list[tuple[int, bool]] = []  # (timestamp_ms, is_motion)
    frame_idx = 0
    prev_small: Optional[np.ndarray] = None
    last_reported = -1

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_skip == 0:
            ts_ms = int(frame_idx / original_fps * 1000)
            small = cv2.resize(frame, (320, 180))

            # Scene cut detection
            scene_cut = False
            if prev_small is not None:
                scene_cut = _histogram_diff(prev_small, small) > scene_cut_threshold

            # MOG2 foreground ratio
            fg_mask = fgbg.apply(small)
            ratio = float(np.count_nonzero(fg_mask > 127)) / (320 * 180)
            is_motion = ratio > motion_threshold and not scene_cut

            motion_events.append((ts_ms, is_motion))
            prev_small = small

            if progress_cb:
                pct = int(frame_idx / total_frames * 100)
                if pct != last_reported:
                    progress_cb(pct)
                    last_reported = pct

        frame_idx += 1

    cap.release()

    if not any(m for _, m in motion_events):
        logger.warning("[detect] No motion detected — falling back to equal splits")
        return _equal_segments(total_duration_ms, 8000), total_duration_ms

    # Merge consecutive motion timestamps into raw segments
    raw_segments: list[tuple[int, int]] = []
    seg_start: Optional[int] = None
    seg_end: Optional[int] = None

    for ts_ms, is_motion in motion_events:
        if is_motion:
            if seg_start is None:
                seg_start = ts_ms
            seg_end = ts_ms
        else:
            if seg_start is not None:
                gap = ts_ms - seg_end
                if gap <= merge_gap_ms:
                    seg_end = ts_ms  # extend across short quiet gap
                else:
                    raw_segments.append((seg_start, seg_end))
                    seg_start = None
                    seg_end = None

    if seg_start is not None and seg_end is not None:
        raw_segments.append((seg_start, seg_end))

    # Filter minimum duration
    raw_segments = [(s, e) for s, e in raw_segments if e - s >= min_duration_ms]

    if not raw_segments:
        logger.warning("[detect] All segments below min_duration — falling back")
        return _equal_segments(total_duration_ms, 8000), total_duration_ms

    # Add padding
    padded = [
        (max(0, s - padding_ms), min(total_duration_ms, e + padding_ms))
        for s, e in raw_segments
    ]

    # Split oversized segments evenly
    final: list[tuple[int, int]] = []
    for s, e in padded:
        if e - s <= max_duration_ms:
            final.append((s, e))
        else:
            n = max(2, int((e - s) / max_duration_ms) + 1)
            sub = (e - s) / n
            cur = s
            for _ in range(n):
                nxt = min(e, int(cur + sub))
                if nxt - cur >= min_duration_ms:
                    final.append((cur, nxt))
                cur = nxt

    logger.info("[detect] %d raw → %d final segments", len(raw_segments), len(final))
    return final, total_duration_ms


def _equal_segments(total_duration_ms: int, segment_ms: int = 8000) -> list:
    segments = []
    cur = 0
    while cur < total_duration_ms:
        end = min(cur + segment_ms, total_duration_ms)
        if end - cur >= 2000:
            segments.append((cur, end))
        cur = end
    return segments


# ─── FFmpeg clip cutting ───────────────────────────────────────────────────────

def cut_clip_ffmpeg(video_path: str, start_ms: int, end_ms: int, output_path: str) -> bool:
    cmd = [
        "ffmpeg", "-y",
        "-ss", f"{start_ms / 1000:.3f}",
        "-i", video_path,
        "-t", f"{(end_ms - start_ms) / 1000:.3f}",
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-movflags", "+faststart",
        "-an",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("FFmpeg error: %s", result.stderr[-600:])
        return False
    return True


# ─── Main entry point ─────────────────────────────────────────────────────────

def process_video(
    video_id: str,
    video_path: str,
    clips_dir: str,
    on_done: Callable,
    on_progress: Optional[Callable[[str, str, int], None]] = None,
    filter_humans: bool = False,
    detector: str = "hog",
) -> None:
    """
    Full pipeline:
      1. decode  — read video metadata
      2. motion  — detect motion segments (MOG2 + scene cut)
      3. cut     — extract clips via FFmpeg + thumbnails + quality scores
                   if filter_humans=True, clips without a detected person are excluded
                   detector: 'hog' (fast, no deps) | 'yolo' (accurate, requires ultralytics)
      4. done    — call on_done with results

    on_progress(video_id, step, pct) is called at key points.
    """

    def progress(step: str, pct: int) -> None:
        if on_progress:
            on_progress(video_id, step, pct)
        logger.info("[%s] step=%s pct=%d", video_id, step, pct)

    try:
        # Step 1 — decode
        progress("decode", 0)
        info = get_video_info(video_path)
        logger.info("[%s] info: %s", video_id, info)
        progress("decode", 100)

        # Step 2 — motion detection
        progress("motion", 0)
        segments, total_duration_ms = detect_motion_segments(
            video_path,
            progress_cb=lambda pct: progress("motion", pct),
        )
        if not segments:
            raise RuntimeError("No motion segments detected")
        progress("motion", 100)

        # Step 3 — cut clips
        os.makedirs(clips_dir, exist_ok=True)
        thumbs_dir = Path(clips_dir) / "thumbs"
        thumbs_dir.mkdir(exist_ok=True)

        clips_data = []
        total = len(segments)

        for i, (start_ms, end_ms) in enumerate(segments):
            progress("cut", int(i / total * 100))

            clip_id = str(uuid.uuid4())
            clip_filename: Optional[str] = None
            thumb_filename: Optional[str] = None

            # Thumbnail at midpoint
            mid_ms = (start_ms + end_ms) // 2
            thumb_path = str(thumbs_dir / f"{clip_id}.jpg")
            if extract_thumbnail(video_path, mid_ms, thumb_path):
                thumb_filename = f"thumbs/{clip_id}.jpg"

            # Quality metrics
            quality = score_clip(video_path, start_ms, end_ms)

            # Optional person filter
            person_detected: Optional[bool] = None
            if filter_humans:
                person_detected = detect_person_in_clip(
                    video_path, start_ms, end_ms, detector=detector
                )
                if not person_detected:
                    logger.info(
                        "[%s] clip %d/%d skipped — no person detected (%s)",
                        video_id, i + 1, total, detector,
                    )
                    continue

            # FFmpeg clip
            if FFMPEG_AVAILABLE:
                clip_filename = f"{clip_id}.mp4"
                ok = cut_clip_ffmpeg(
                    video_path, start_ms, end_ms,
                    os.path.join(clips_dir, clip_filename)
                )
                if not ok:
                    clip_filename = None

            clips_data.append({
                "id": clip_id,
                "clip_filename": clip_filename,
                "thumb_filename": thumb_filename,
                "start_ms": start_ms,
                "end_ms": end_ms,
                "order": i,
                "has_person": person_detected,
                **quality,
            })
            logger.info(
                "[%s] clip %d/%d (%d–%d ms) blur=%.1f bright=%.1f",
                video_id, i + 1, total, start_ms, end_ms,
                quality["blur_score"], quality["brightness"],
            )

        progress("cut", 100)
        progress("done", 100)
        on_done(video_id, total_duration_ms, clips_data)
        logger.info("[%s] done — %d clips", video_id, len(clips_data))

    except Exception as e:
        logger.exception("[%s] processing failed: %s", video_id, e)
        raise
