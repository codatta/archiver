"""
Vision Engine — 视觉算法引擎（无状态）

视频/序列帧分析、YOLO/Pose 人体检测、光流运动分析。
接收源文件 → 分析 → 返回 JSON 结果 → 清理临时文件。
不持久化任何数据。

Start:
    cd vision-engine
    pip install -r requirements.txt
    uvicorn main:app --host 0.0.0.0 --port 8001
"""

import os
import shutil
import threading
import logging
import tempfile
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from device_config import DEVICE_MODE, DEVICE, IS_GPU, TORCH_COMPILE
from video_processor import process_video, FFMPEG_AVAILABLE, YOLO_AVAILABLE, get_frame_annotations
from image_sequence_processor import process_sequence

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("vision-engine")

app = FastAPI(title="Vision Engine", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Temp dir for processing (cleaned up after each task)
TEMP_BASE = Path(os.environ.get("TEMP_DIR", tempfile.gettempdir())) / "vision-engine"
TEMP_BASE.mkdir(parents=True, exist_ok=True)

# In-memory task store (progress only, results forwarded via callback then discarded)
tasks: dict[str, dict[str, Any]] = {}


# ─── Health ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "ok",
        "ffmpeg": FFMPEG_AVAILABLE,
        "yolo": YOLO_AVAILABLE,
        "device_mode": DEVICE_MODE,
        "device": DEVICE,
        "gpu": IS_GPU,
        "torch_compile": TORCH_COMPILE,
    }


# ─── Process task (async, stateless) ─────────────────────────────────────────

class ProcessRequest(BaseModel):
    task_id: str
    input_type: str                 # "video" | "sequence"
    filter_humans: bool = False
    detector: str = "yolo"
    yolo_model: str = "yolov8s.pt"
    detection_strategy: str = "single"
    require_center: bool = False
    center_margin: float = 0.20
    require_arms: bool = False
    arm_conf_threshold: float = 0.30
    motion_threshold: float = 0.015
    low_action_threshold: float = 0.04
    hand_activity_threshold: float = 0.0
    smooth_window: int = 5
    frame_sample_step: int = 1
    continuity_gap_frames: int = 5
    compress_px: int = 0
    callback_url: Optional[str] = None


@app.post("/tasks/process")
async def submit_process(
    file: UploadFile = File(...),
    task_id: str = Form(...),
    input_type: str = Form(default="sequence"),
    filter_humans: bool = Form(default=False),
    detector: str = Form(default="yolo"),
    yolo_model: str = Form(default="yolov8s.pt"),
    detection_strategy: str = Form(default="single"),
    require_center: bool = Form(default=False),
    center_margin: float = Form(default=0.20),
    require_arms: bool = Form(default=False),
    arm_conf_threshold: float = Form(default=0.30),
    motion_threshold: float = Form(default=0.015),
    low_action_threshold: float = Form(default=0.04),
    hand_activity_threshold: float = Form(default=0.0),
    smooth_window: int = Form(default=5),
    frame_sample_step: int = Form(default=1),
    continuity_gap_frames: int = Form(default=5),
    compress_px: int = Form(default=0),
    callback_url: str = Form(default=""),
):
    """
    Receive source file + params, run analysis in background.
    Returns immediately. Results sent via callback_url when done.
    Temp files cleaned up after completion.
    """
    if task_id in tasks and tasks[task_id].get("status") == "running":
        raise HTTPException(status_code=409, detail="Task already running")

    # Save uploaded file to temp dir
    task_dir = TEMP_BASE / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "upload").suffix.lower()
    source_path = task_dir / f"source{ext}"
    clips_dir = task_dir / "clips"
    clips_dir.mkdir(exist_ok=True)

    content = await file.read()
    with open(source_path, "wb") as f:
        f.write(content)
    logger.info("Task %s: received %s (%d bytes)", task_id, file.filename, len(content))

    tasks[task_id] = {
        "task_id": task_id,
        "status": "accepted",
        "step": "",
        "step_pct": 0,
        "result": None,
        "error": None,
    }

    def on_progress(step: str, pct: int):
        tasks[task_id]["status"] = "running"
        tasks[task_id]["step"] = step
        tasks[task_id]["step_pct"] = pct

    def on_done(job_id, total_duration_ms, clips_data, culled_data=None, all_segments=None):
        # Strip file paths from results — only keep metadata
        # (API server will organize its own frame files)
        clean_clips = _strip_file_paths(clips_data)
        clean_culled = _strip_frame_urls(culled_data or [])
        clean_all = _strip_frame_urls(all_segments or [])

        result = {
            "total_duration_ms": total_duration_ms,
            "clips_data": clean_clips,
            "culled_segments": clean_culled,
            "all_segments": clean_all,
        }
        tasks[task_id]["status"] = "done"
        tasks[task_id]["step"] = "done"
        tasks[task_id]["step_pct"] = 100
        tasks[task_id]["result"] = result
        logger.info("Task %s done — %d clips, %d culled, %d all",
                     task_id, len(clean_clips), len(clean_culled), len(clean_all))

        # Send result to API server
        _notify_callback(callback_url, task_id)

        # Cleanup temp files (keep task in memory briefly for polling)
        _cleanup_task_dir(task_id)
        _free_gpu_memory()

    def on_error(msg):
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = msg
        logger.error("Task %s failed: %s", task_id, msg)
        _notify_callback(callback_url, task_id)
        _cleanup_task_dir(task_id)
        _free_gpu_memory()

    def run():
        try:
            if input_type == "sequence":
                process_sequence(
                    task_id, str(source_path), str(clips_dir),
                    on_done, lambda _job_id, step, pct: on_progress(step, pct),
                    filter_humans=filter_humans,
                    detector=detector,
                    yolo_model=yolo_model,
                    detection_strategy=detection_strategy,
                    require_center=require_center,
                    center_margin=center_margin,
                    require_arms=require_arms,
                    arm_conf_threshold=arm_conf_threshold,
                    motion_threshold=motion_threshold,
                    low_action_threshold=low_action_threshold,
                    hand_activity_threshold=hand_activity_threshold,
                    smooth_window=smooth_window,
                    frame_sample_step=frame_sample_step,
                    continuity_gap_frames=continuity_gap_frames,
                    compress_px=compress_px,
                )
            else:
                process_video(
                    task_id, str(source_path), str(clips_dir),
                    on_done, lambda _job_id, step, pct: on_progress(step, pct),
                    filter_humans=filter_humans,
                    detector=detector,
                )
        except Exception as e:
            on_error(str(e))

    threading.Thread(target=run, daemon=True).start()
    return {"task_id": task_id, "status": "accepted"}


# ─── Task progress ───────────────────────────────────────────────────────────

@app.get("/tasks/{task_id}/progress")
def get_progress(task_id: str):
    t = tasks.get(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return t


# ─── Single-frame annotation (sync) ──────────────────────────────────────────
# Accepts file upload directly — no stored state needed.

@app.post("/tasks/annotate-frame")
async def annotate_frame(
    file: UploadFile = File(...),
    detector: str = Form(default="yolo"),
    yolo_model: str = Form(default="yolov8s.pt"),
    arm_conf_threshold: float = Form(default=0.30),
    detect_objects: bool = Form(default=False),
    object_conf_threshold: float = Form(default=0.35),
):
    """Run person detection on a single uploaded frame image."""
    tmp = TEMP_BASE / f"_annotate_{file.filename}"
    content = await file.read()
    with open(tmp, "wb") as f:
        f.write(content)
    try:
        result = get_frame_annotations(
            str(tmp), detector=detector, yolo_model=yolo_model,
            arm_conf_threshold=arm_conf_threshold,
            detect_objects=detect_objects,
            object_conf_threshold=object_conf_threshold,
        )
        return result
    finally:
        tmp.unlink(missing_ok=True)


# ─── Batch person detection (sync) ───────────────────────────────────────────

@app.post("/tasks/detect-persons")
async def detect_persons(
    files: list[UploadFile] = File(...),
    detector: str = Form(default="yolo"),
    yolo_model: str = Form(default="yolov8s.pt"),
    arm_conf_threshold: float = Form(default=0.30),
    detect_objects: bool = Form(default=False),
    object_conf_threshold: float = Form(default=0.35),
):
    """Run person detection on multiple uploaded frame images."""
    tmp_dir = TEMP_BASE / f"_detect_{id(files)}"
    tmp_dir.mkdir(exist_ok=True)
    detections: dict = {}
    try:
        for f in files:
            tmp_path = tmp_dir / (f.filename or "frame.jpg")
            content = await f.read()
            with open(tmp_path, "wb") as fout:
                fout.write(content)
            anno = get_frame_annotations(
                str(tmp_path),
                detector=detector,
                yolo_model=yolo_model,
                arm_conf_threshold=arm_conf_threshold,
                detect_objects=detect_objects,
                object_conf_threshold=object_conf_threshold,
            )
            detections[f.filename or ""] = {
                "person_boxes": anno["person_boxes"],
                "hand_keypoints": anno.get("hand_keypoints", []),
                "object_boxes": anno.get("object_boxes", []),
                "width": anno["width"],
                "height": anno["height"],
            }
        return {"detections": detections}
    finally:
        shutil.rmtree(str(tmp_dir), ignore_errors=True)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _strip_file_paths(clips_data: list) -> list:
    """Remove local file system paths from clips, keep only index-based metadata."""
    cleaned = []
    for c in clips_data:
        cleaned.append({
            "id": c["id"],
            "start_ms": c["start_ms"],
            "end_ms": c["end_ms"],
            "start_ns": c.get("start_ns"),
            "end_ns": c.get("end_ns"),
            "start_idx": c.get("start_idx"),
            "end_idx": c.get("end_idx"),
            "fps": c.get("fps"),
            "blur_score": c.get("blur_score"),
            "brightness": c.get("brightness"),
            "actions": c.get("actions", []),
            # Frame indices only — API server will build URLs from its own files
            "frame_indices": _extract_indices(c.get("frame_filenames", [])),
        })
    return cleaned


def _extract_indices(frame_filenames: list) -> list[int]:
    """Extract frame indices from filenames like 'frames/xxx/000123.jpg'."""
    indices = []
    for fn in (frame_filenames or []):
        try:
            stem = Path(fn).stem
            indices.append(int(stem))
        except (ValueError, TypeError):
            pass
    return sorted(indices)


def _strip_frame_urls(segments: list) -> list:
    """Replace frame URLs with index-only info in segments."""
    for seg in segments:
        seg.pop("thumb_url", None)
        for frame in seg.get("frames", []):
            frame.pop("url", None)  # Remove local file path
    return segments


def _free_gpu_memory():
    """Release unused GPU memory back to the pool after each task."""
    if IS_GPU:
        try:
            import torch
            torch.cuda.empty_cache()
        except Exception:
            pass


def _cleanup_task_dir(task_id: str):
    """Remove temp files for a completed task."""
    task_dir = TEMP_BASE / task_id
    if task_dir.exists():
        try:
            shutil.rmtree(str(task_dir))
            logger.info("Cleaned up temp dir for task %s", task_id)
        except Exception as e:
            logger.warning("Failed to cleanup task %s: %s", task_id, e)


def _notify_callback(callback_url: str, task_id: str):
    if not callback_url:
        return
    t = tasks.get(task_id, {})
    try:
        import httpx
        with httpx.Client(trust_env=False, timeout=30.0) as c:
            c.post(callback_url, json={
                "task_id": task_id,
                "status": t.get("status", "failed"),
                "result": t.get("result"),
                "error": t.get("error"),
            })
        logger.info("Callback sent for task %s", task_id)
    except Exception as e:
        logger.warning("Callback failed for task %s: %s", task_id, e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
