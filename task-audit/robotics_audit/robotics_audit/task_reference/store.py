from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class TaskReferenceRecord:
    frontier_id: str
    template_id: str
    task_id: str
    reference: Dict[str, Any]
    task_name: str = ""
    media_resource: str = ""
    media_url: str = ""
    source: str = "manual"
    model: str = ""
    generated_at: str = ""
    media_meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "frontier_id": self.frontier_id,
            "template_id": self.template_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "media_resource": self.media_resource,
            "media_url": self.media_url,
            "source": self.source,
            "model": self.model,
            "generated_at": self.generated_at or datetime.now().isoformat(),
            "reference": self.reference,
        }
        if self.media_meta:
            payload["media_meta"] = self.media_meta
        return payload

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TaskReferenceRecord":
        return cls(
            frontier_id=str(payload.get("frontier_id") or ""),
            template_id=str(payload.get("template_id") or ""),
            task_id=str(payload.get("task_id") or ""),
            task_name=str(payload.get("task_name") or ""),
            media_resource=str(payload.get("media_resource") or ""),
            media_url=str(payload.get("media_url") or ""),
            source=str(payload.get("source") or "manual"),
            model=str(payload.get("model") or ""),
            generated_at=str(payload.get("generated_at") or ""),
            reference=dict(payload.get("reference") or {}),
            media_meta=dict(payload.get("media_meta") or {}),
        )


class TaskReferenceStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, frontier_id: str, template_id: str, task_id: str) -> Path:
        return self.base_dir / frontier_id / template_id / f"{task_id}.json"

    def exists(self, frontier_id: str, template_id: str, task_id: str) -> bool:
        return self.path_for(frontier_id, template_id, task_id).is_file()

    def load(self, frontier_id: str, template_id: str, task_id: str) -> Optional[TaskReferenceRecord]:
        path = self.path_for(frontier_id, template_id, task_id)
        if not path.is_file():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return TaskReferenceRecord.from_dict(json.load(f))

    def save(self, record: TaskReferenceRecord) -> Path:
        path = self.path_for(record.frontier_id, record.template_id, record.task_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = record.to_dict()
        if not payload.get("generated_at"):
            payload["generated_at"] = datetime.now().isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return path
