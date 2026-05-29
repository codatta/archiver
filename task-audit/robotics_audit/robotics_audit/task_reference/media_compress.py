from __future__ import annotations

import io
import os
from typing import Dict, List, Optional, Tuple

from PIL import Image

MAX_VISION_BYTES = 4 * 1024 * 1024
FRAME_WIDTH = 512
DEFAULT_MAX_FRAMES = int(os.getenv("TASK_MEDIA_MAX_FRAMES", "60"))


def _frame_interval_sec(*, fps: Optional[float] = None) -> float:
    if os.getenv("TASK_MEDIA_FRAME_INTERVAL_SEC"):
        return float(os.getenv("TASK_MEDIA_FRAME_INTERVAL_SEC", "0.333"))
    rate = fps if fps is not None else float(os.getenv("TASK_MEDIA_FRAMES_PER_SECOND", "3"))
    return 1.0 / max(rate, 0.1)


DEFAULT_FRAME_INTERVAL_SEC = _frame_interval_sec()


def frames_per_second_for_template(template_id: str) -> float:
    """000001 默认 3fps；000003 默认 1fps。可通过环境变量覆盖。"""
    from robotics_audit.models import TEMPLATE_METADATA, TEMPLATE_SEGMENT

    if template_id == TEMPLATE_METADATA:
        return float(os.getenv("TASK_MEDIA_FRAMES_PER_SECOND_METADATA", "1"))
    if template_id == TEMPLATE_SEGMENT:
        return float(os.getenv("TASK_MEDIA_FRAMES_PER_SECOND_SEGMENT", os.getenv("TASK_MEDIA_FRAMES_PER_SECOND", "3")))
    return float(os.getenv("TASK_MEDIA_FRAMES_PER_SECOND", "3"))


def frame_interval_for_template(template_id: str) -> float:
    return _frame_interval_sec(fps=frames_per_second_for_template(template_id))


def probe_gif_meta(content: bytes) -> Dict[str, float]:
    img = Image.open(io.BytesIO(content))
    frame_count = int(getattr(img, "n_frames", 1) or 1)
    total_ms = 0.0
    for index in range(frame_count):
        img.seek(index)
        total_ms += float(img.info.get("duration") or 100)
    return {
        "frame_count": frame_count,
        "duration_sec": round(total_ms / 1000.0, 2),
    }


def compress_image_bytes(content: bytes, *, max_width: int = FRAME_WIDTH) -> Tuple[bytes, str]:
    img = Image.open(io.BytesIO(content))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.thumbnail((max_width, max_width))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue(), "image/jpeg"


def extract_gif_frames(
    content: bytes,
    *,
    max_frames: Optional[int] = None,
    interval_sec: float = DEFAULT_FRAME_INTERVAL_SEC,
) -> List[Tuple[bytes, int]]:
    """返回 (jpeg_bytes, frame_index_1based) 列表。max_frames=0 表示按间隔采满整段 GIF。"""
    img = Image.open(io.BytesIO(content))
    frame_count = int(getattr(img, "n_frames", 1) or 1)
    if frame_count <= 1:
        frame = img.convert("RGB")
        frame.thumbnail((FRAME_WIDTH, FRAME_WIDTH))
        return [(_encode_jpeg(frame), 1)]

    if max_frames is None:
        env_cap = int(os.getenv("TASK_MEDIA_MAX_FRAMES", "0"))
        max_frames = env_cap if env_cap > 0 else frame_count
    else:
        max_frames = max_frames if max_frames > 0 else frame_count

    # 按 GIF 实际帧数动态上限，不假定固定 83 或其他值
    max_frames = min(max_frames, frame_count)

    durations_ms: List[float] = []
    for index in range(frame_count):
        img.seek(index)
        durations_ms.append(float(img.info.get("duration") or 100))

    cumulative = [0.0]
    for duration_ms in durations_ms:
        cumulative.append(cumulative[-1] + duration_ms / 1000.0)
    total_duration = cumulative[-1]

    if total_duration <= 0:
        indices = _indices_evenly(frame_count, max_frames=max_frames)
    else:
        indices = _indices_for_interval(cumulative, total_duration, interval_sec, max_frames)

    return _encode_indices(img, indices)


def _indices_evenly(frame_count: int, *, max_frames: int) -> List[int]:
    if frame_count <= max_frames:
        return list(range(frame_count))
    step = max(1, frame_count // max_frames)
    return list(range(0, frame_count, step))[:max_frames]


def _indices_for_interval(
    cumulative: List[float],
    total_duration: float,
    interval_sec: float,
    max_frames: int,
) -> List[int]:
    target_times: List[float] = []
    current = 0.0
    while current < total_duration and len(target_times) < max_frames:
        target_times.append(current)
        current += max(interval_sec, 0.1)

    indices: List[int] = []
    for target in target_times:
        frame_index = 0
        for idx in range(len(cumulative) - 1):
            if cumulative[idx] <= target < cumulative[idx + 1]:
                frame_index = idx
                break
        else:
            frame_index = len(cumulative) - 2
        indices.append(max(0, frame_index))

    deduped = sorted(set(indices))
    if len(deduped) > max_frames:
        step = max(1, len(deduped) // max_frames)
        deduped = deduped[::step][:max_frames]
    return deduped


def _encode_indices(img: Image.Image, indices: List[int]) -> List[Tuple[bytes, int]]:
    frames: List[Tuple[bytes, int]] = []
    for index in indices:
        img.seek(index)
        frame = img.convert("RGB")
        frame.thumbnail((FRAME_WIDTH, FRAME_WIDTH))
        frames.append((_encode_jpeg(frame), index + 1))
    return frames


def _encode_jpeg(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def needs_local_compress(content: bytes, mime: str) -> bool:
    if len(content) > MAX_VISION_BYTES:
        return True
    return mime == "image/gif"
