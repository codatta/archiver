from __future__ import annotations

from typing import Any, Dict, Optional, Set

from robotics_audit.models import TEMPLATE_SEGMENT
from robotics_audit.task_reference.generator import TaskReferenceGenerator
from robotics_audit.task_reference.loader import TaskInfoLoader
from robotics_audit.task_reference.store import TaskReferenceRecord, TaskReferenceStore


class TaskReferenceManager:
    def __init__(
        self,
        store: TaskReferenceStore,
        *,
        enable_llm: bool = False,
    ) -> None:
        self.store = store
        self.enable_llm = enable_llm
        self.loader = TaskInfoLoader()
        self.generator = TaskReferenceGenerator()
        self._prepared: Set[str] = set()

    def get_or_create(
        self,
        frontier_id: str,
        template_id: str,
        task_id: str,
    ) -> Optional[TaskReferenceRecord]:
        if not task_id:
            return None

        cached = self.store.load(frontier_id, template_id, task_id)
        if cached and cached.reference and cached.source in ("llm_vision", "llm"):
            if template_id != TEMPLATE_SEGMENT or cached.media_meta.get("time_unit") == "frame":
                return cached

        task_info = self.loader.fetch_task_info(task_id)
        if not task_info:
            return None

        if self.enable_llm and self.generator.enabled:
            record = self.generator.generate(task_info)
        else:
            return None

        if record.reference:
            self.store.save(record)
        return record

    def get_media_meta(
        self,
        frontier_id: str,
        template_id: str,
        task_id: str,
    ) -> Dict[str, Any]:
        """只读缓存中的 media_meta，不触发视觉 API。"""
        cached = self.store.load(frontier_id, template_id, task_id)
        if cached and cached.media_meta:
            return dict(cached.media_meta)
        return {}

    def prepare_for_tasks(self, task_keys: Dict[str, Dict[str, str]]) -> int:
        prepared = 0
        for task_id, meta in task_keys.items():
            key = f"{meta.get('frontier_id')}|{meta.get('template_id')}|{task_id}"
            if key in self._prepared:
                continue
            record = self.get_or_create(
                str(meta.get("frontier_id") or ""),
                str(meta.get("template_id") or ""),
                task_id,
            )
            self._prepared.add(key)
            if record and record.reference:
                prepared += 1
        return prepared
