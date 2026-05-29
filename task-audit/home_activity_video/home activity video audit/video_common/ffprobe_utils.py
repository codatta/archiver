"""ffprobe JSON 解析：供 Phase 0（时长）与 Phase 1（分辨率/时长）共用。"""

from __future__ import annotations

import json
import subprocess
from typing import Any, Dict, Optional

from .ffmpeg_bin import resolve_fftool


def ffprobe_json(video_path: str) -> Dict[str, Any]:
    cmd = [
        resolve_fftool("ffprobe"),
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        video_path,
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or "ffprobe 执行失败")
    return json.loads(proc.stdout or "{}")


def pick_video_stream(ffprobe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for s in ffprobe_data.get("streams") or []:
        if s.get("codec_type") == "video":
            return s
    return None


def parse_duration_seconds(ffprobe_data: Dict[str, Any]) -> float:
    fmt = ffprobe_data.get("format") or {}
    d = fmt.get("duration")
    if d is None:
        raise RuntimeError("ffprobe 未返回 duration")
    return float(d)
