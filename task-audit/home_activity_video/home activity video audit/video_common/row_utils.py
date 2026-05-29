"""数据库行字段解析（视频路径、任务 ID）。"""

from __future__ import annotations

import json
from typing import Any, Dict


def resolve_video_path(row: Dict[str, Any]) -> str:
    for key in ("video_path", "video_url", "local_path", "file_path", "path"):
        v = row.get(key)
        if v:
            return str(v).strip()
    raw = row.get("data_submission")
    if raw:
        try:
            payload = raw if isinstance(raw, dict) else json.loads(str(raw))
            data = (payload or {}).get("data") or {}
            # 兼容 data.video.url（单对象）结构
            video_obj = data.get("video") or {}
            if isinstance(video_obj, dict):
                single_url = video_obj.get("url")
                if single_url:
                    return str(single_url).strip()
            # 兼容 data.videos[0].url（数组）结构
            videos = data.get("videos") or []
            if isinstance(videos, list) and videos:
                first = videos[0] or {}
                url = first.get("url")
                if url:
                    return str(url).strip()
        except Exception:
            pass
    raise ValueError(
        "记录缺少视频路径列（需 video_path / video_url / local_path / file_path / path，"
        "或 data_submission.data.videos[0].url）"
    )


def resolve_task_id(row: Dict[str, Any]) -> str:
    tid = row.get("task_id") or row.get("frontier_id") or row.get("template_id")
    if tid:
        return str(tid).strip()
    return "_default"


def resolve_video_hash(row: Dict[str, Any]) -> str:
    """
    从 data_submission JSON 中解析视频 hash。

    兼容常见结构：
      - { "data": { "video": { "hash": "..." } } }
      - { "data": { "videos": [ { "hash": "..." } ] } }
    """
    raw = row.get("data_submission")
    if not raw:
        raise ValueError("记录缺少 data_submission，无法解析视频 hash")

    payload = raw if isinstance(raw, dict) else json.loads(str(raw))
    data = (payload or {}).get("data") or {}

    # 单视频对象：data.video.hash
    video_obj = data.get("video") or {}
    if isinstance(video_obj, dict):
        h = video_obj.get("hash") or video_obj.get("video_hash") or video_obj.get("md5") or video_obj.get("sha256")
        if h:
            return str(h).strip()

    # 多视频数组：data.videos[0].hash
    videos = data.get("videos") or []
    if isinstance(videos, list) and videos:
        first = videos[0] or {}
        h = first.get("hash") or first.get("video_hash") or first.get("md5") or first.get("sha256")
        if h:
            return str(h).strip()

    raise ValueError("data_submission 中未找到 video.hash 字段")
