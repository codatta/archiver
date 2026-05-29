from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import pymysql

from robotics_audit.task_reference.store import TaskReferenceRecord


class TaskInfoLoader:
    def __init__(self) -> None:
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", "3306"))
        self.user = os.getenv("DB_USER", "")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "")

    def _connect(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", "20")),
        )

    def fetch_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        if not task_id:
            return None
        sql = """
            SELECT frontier_id, task_id, template_id, name, data_display, data_requirements
            FROM cfp_frontier_task
            WHERE task_id = %s
            LIMIT 1
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, (task_id,))
                row = cur.fetchone()
                if not row:
                    return None
                frontier_id, tid, template_id, name, data_display, data_requirements = row
                display = _safe_json(data_display)
                requirements = _safe_json(data_requirements)
                media_resource = str((display or {}).get("gif_resource") or "")
                frontier = str(frontier_id or "")
                media_url = build_media_url(media_resource, frontier_id=frontier)
                return {
                    "frontier_id": str(frontier_id or ""),
                    "task_id": str(tid or ""),
                    "template_id": str(template_id or ""),
                    "task_name": str(name or ""),
                    "media_resource": media_resource,
                    "media_url": media_url,
                    "data_display": display or {},
                    "data_requirements": requirements or {},
                }
        finally:
            conn.close()


def _safe_json(raw: Any) -> Dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def build_media_url(media_resource: str, *, frontier_id: str = "") -> str:
    resource = (media_resource or "").strip()
    if not resource:
        return ""
    if resource.startswith(("http://", "https://")):
        return resource
    base = (os.getenv("TASK_MEDIA_BASE_URL") or "").strip().rstrip("/")
    if not base:
        return ""
    frontier = (frontier_id or os.getenv("DEFAULT_FRONTIER_ID") or "ROBSTIC001").strip().strip("/")
    return f"{base}/{frontier}/{resource.lstrip('/')}"


def build_vision_download_url(media_url: str) -> tuple[str, str]:
    """为视觉模型准备可下载 URL。大 GIF 通过 OSS 图片处理压缩为 JPEG。"""
    url = (media_url or "").strip()
    if not url:
        return "", ""
    lower = url.lower()
    is_gif = lower.endswith(".gif") or ".gif?" in lower
    if is_gif and "x-oss-process" not in lower:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}x-oss-process=image/resize,w_512/format,jpg"
        return url, "image/jpeg"
    if is_gif:
        return url, "image/gif"
    if lower.endswith(".png"):
        return url, "image/png"
    return url, "image/jpeg"


def bootstrap_reference_from_task(task_info: Dict[str, Any]) -> Dict[str, Any]:
    template_id = str(task_info.get("template_id") or "")
    requirements = task_info.get("data_requirements") or {}
    data = requirements.get("data")
    reference: Dict[str, Any] = {
        "segments": [],
        "visible_objects": [],
        "actions": [],
        "objects": [],
        "environment": "",
        "view": [],
        "relations": [],
        "task": [],
        "agent_type": {},
    }

    if isinstance(data, list):
        segments = []
        for item in data:
            if not isinstance(item, dict):
                continue
            desc = str(item.get("des") or item.get("description") or "").strip()
            segments.append(
                {
                    "start": item.get("start"),
                    "end": item.get("end"),
                    "description": desc,
                }
            )
            if desc:
                reference["actions"].append(desc)
        reference["segments"] = segments

    if isinstance(data, dict):
        reference.update(
            {
                "objects": _as_str_list(data.get("objects")),
                "environment": str(data.get("environment") or "").strip(),
                "view": _as_str_list(data.get("view")),
                "relations": _normalize_relations(data.get("relations")),
                "task": _as_str_list(data.get("task")),
                "agent_type": _first_dict(data.get("agent_type")),
                "raw": data,
            }
        )
        reference["visible_objects"] = list(reference["objects"])
        reference["actions"] = list(reference["task"])

    return reference


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _first_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return dict(value[0])
    if isinstance(value, dict):
        return dict(value)
    return {}


def _normalize_relations(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _metadata_hint_from_actions(actions: list[str]) -> Dict[str, Any]:
    joined = " ".join(actions).lower()
    objects = []
    for word in ("cube", "cup", "glass", "table", "arm", "button", "dispenser", "bottle"):
        if word in joined:
            objects.append(word)
    return {
        "objects": objects,
        "task": actions,
        "environment": "Indoor",
    }


def build_bootstrap_record(task_info: Dict[str, Any]) -> TaskReferenceRecord:
    return TaskReferenceRecord(
        frontier_id=str(task_info.get("frontier_id") or ""),
        template_id=str(task_info.get("template_id") or ""),
        task_id=str(task_info.get("task_id") or ""),
        task_name=str(task_info.get("task_name") or ""),
        media_resource=str(task_info.get("media_resource") or ""),
        media_url=str(task_info.get("media_url") or ""),
        source="task_requirements",
        reference=bootstrap_reference_from_task(task_info),
    )
