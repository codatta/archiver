"""视频抽帧与感知哈希（Phase 0B）。"""

from __future__ import annotations

import io
import subprocess
from typing import Optional

from .ffmpeg_bin import resolve_fftool

try:
    import imagehash
    from PIL import Image
except ImportError:
    imagehash = None  # type: ignore
    Image = None  # type: ignore


def extract_frame_png_at(video_path: str, t_sec: float) -> bytes:
    cmd = [
        resolve_fftool("ffmpeg"),
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{t_sec:.3f}",
        "-i",
        video_path,
        "-frames:v",
        "1",
        "-f",
        "image2pipe",
        "-vcodec",
        "png",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0 or not proc.stdout:
        err = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""
        raise RuntimeError(f"ffmpeg 抽帧失败: {err}")
    return proc.stdout


def compute_phash_midframe(video_path: str, duration_sec: float) -> str:
    if imagehash is None or Image is None:
        raise RuntimeError("请安装依赖: pip install pillow imagehash")
    t = max(0.0, duration_sec * 0.5)
    png = extract_frame_png_at(video_path, t)
    im = Image.open(io.BytesIO(png)).convert("RGB")
    h = imagehash.phash(im)
    return str(h)


def phash_distance_hex(a_hex: str, b_hex: str) -> Optional[int]:
    if imagehash is None:
        return None
    try:
        ha = imagehash.hex_to_hash(a_hex)
        hb = imagehash.hex_to_hash(b_hex)
        return ha - hb
    except Exception:
        return None
