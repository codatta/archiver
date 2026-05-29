from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from robotics_audit.common.phase_gate import is_llm_eligible
from robotics_audit.common.row_utils import resolve_submission_data
from robotics_audit.llm_text_validator import LLMTextValidator
from robotics_audit.metadata.parser import extract_metadata
from robotics_audit.metadata.reference_match import check_metadata_reference
from robotics_audit.metadata.rules import load_metadata_config
from robotics_audit.models import TEMPLATE_METADATA, TEMPLATE_SEGMENT, AuditResult, Violation, worst_grade
from robotics_audit.router import AuditRouter
from robotics_audit.segment.parser import parse_json_payload, parse_segments
from robotics_audit.segment.reference_match import check_reference_match
from robotics_audit.segment.rules import load_audit_config
from robotics_audit.task_reference.manager import TaskReferenceManager
from robotics_audit.task_reference.store import TaskReferenceRecord, TaskReferenceStore


class AuditPipeline:
    def __init__(
        self,
        *,
        reference_dir: Path,
        enable_llm_text_check: bool = False,
        enable_json_reference_check: bool = True,
        enable_local_reference_check: bool = False,
        enable_vision_llm: bool = False,
        segment_config: Optional[str] = None,
        metadata_config: Optional[str] = None,
    ) -> None:
        self.router = AuditRouter(segment_config=segment_config, metadata_config=metadata_config)
        self.segment_config_path = segment_config
        self.metadata_config_path = metadata_config
        use_vision = enable_vision_llm or enable_llm_text_check
        self.reference_manager = TaskReferenceManager(
            TaskReferenceStore(reference_dir),
            enable_llm=use_vision,
        )
        self.text_validator = LLMTextValidator()
        self.enable_llm_text_check = enable_llm_text_check
        self.enable_json_reference_check = enable_json_reference_check
        self.enable_local_reference_check = enable_local_reference_check

    def audit_rows(self, rows: List[Dict[str, Any]]) -> List[AuditResult]:
        if self.enable_llm_text_check:
            task_map = self._collect_task_map(rows)
            prepared = self.reference_manager.prepare_for_tasks(task_map)
            print(f"[pipeline] 已生成/加载视频参考 JSON: {prepared} 个 task_id")
        elif self.enable_local_reference_check:
            task_map = self._collect_task_map(rows)
            prepared = self.reference_manager.prepare_for_tasks(task_map)
            print(f"[pipeline] 已准备 task 参考 JSON: {prepared} 个 task_id")

        total = len(rows)
        results: List[AuditResult] = []
        for index, row in enumerate(rows, 1):
            result = self._audit_single_row(row)
            results.append(result)
            _print_row_result(index, total, row, result)
        return results

    def _collect_task_map(self, rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, str]]:
        task_map: Dict[str, Dict[str, str]] = {}
        for row in rows:
            task_id = str(row.get("task_id") or "")
            if not task_id:
                continue
            task_map[task_id] = {
                "frontier_id": str(row.get("frontier_id") or ""),
                "template_id": str(row.get("template_id") or ""),
            }
        return task_map

    def _load_template_config(self, template_id: str) -> Dict[str, Any]:
        if template_id == TEMPLATE_SEGMENT:
            return load_audit_config(self.segment_config_path)
        if template_id == TEMPLATE_METADATA:
            return load_metadata_config(self.metadata_config_path)
        return {}

    def _audit_single_row(self, row: Dict[str, Any]) -> AuditResult:
        task_id = str(row.get("task_id") or "")
        frontier_id = str(row.get("frontier_id") or "")
        template_id = str(row.get("template_id") or "")

        rule_result = self.router.audit_row(
            row,
            reference=None,
            enable_reference_check=False,
            frame_count_limit=self._resolve_frame_count_limit(frontier_id, template_id, task_id),
        )

        if self.enable_llm_text_check:
            if not self._can_enter_llm(rule_result, template_id):
                rule_result.reference_check = "skipped_pre_reject"
                rule_result.audit_grade = rule_result.rule_phase_grade or rule_result.audit_grade
                rule_result.passed = False
                return rule_result
            return self._apply_llm_text_check(row, rule_result, frontier_id, template_id, task_id)

        if rule_result.rule_phase_grade != "S":
            rule_result.reference_check = "skipped_pre_reject"
            rule_result.audit_grade = rule_result.rule_phase_grade or rule_result.audit_grade
            rule_result.passed = False
            return rule_result

        if self.enable_local_reference_check and task_id:
            reference = self.reference_manager.get_or_create(frontier_id, template_id, task_id)
            if reference is None or not reference.reference:
                rule_result.reference_check = "missing"
                return rule_result
            final_result = self.router.audit_row(
                row,
                reference=reference,
                enable_reference_check=True,
            )
            final_result.reference_path = str(
                self.reference_manager.store.path_for(frontier_id, template_id, task_id)
            )
            return final_result

        rule_result.reference_check = "skipped"
        return rule_result

    def _resolve_frame_count_limit(
        self,
        frontier_id: str,
        template_id: str,
        task_id: str,
    ) -> Optional[float]:
        if template_id != TEMPLATE_SEGMENT or not task_id:
            return None
        meta = self.reference_manager.get_media_meta(frontier_id, template_id, task_id)
        frame_count = meta.get("frame_count")
        if frame_count:
            return float(frame_count)
        return None

    def _can_enter_llm(self, rule_result: AuditResult, template_id: str) -> bool:
        config = self._load_template_config(template_id)
        if not config:
            return rule_result.rule_phase_grade == "S"
        return is_llm_eligible(
            rule_result.violations,
            config=config,
            template_id=template_id,
        )

    def _apply_llm_text_check(
        self,
        row: Dict[str, Any],
        rule_result: AuditResult,
        frontier_id: str,
        template_id: str,
        task_id: str,
    ) -> AuditResult:
        submission_data = resolve_submission_data(row)

        if not task_id:
            rule_result.reference_check = "missing"
            rule_result.audit_grade = "A"
            rule_result.passed = False
            rule_result.violations.append(
                Violation(code="reference_missing", grade="A", message="缺少 task_id，无法关联视频")
            )
            return rule_result

        reference = self.reference_manager.get_or_create(frontier_id, template_id, task_id)
        ref_path = str(self.reference_manager.store.path_for(frontier_id, template_id, task_id))
        rule_result.reference_path = ref_path

        if reference is None or not reference.reference:
            rule_result.reference_check = "vision_missing"
            rule_result.audit_grade = "A"
            rule_result.passed = False
            msg = "无法从视频生成参考内容"
            if reference and reference.media_url:
                msg += f"（media_url={reference.media_url}）"
            rule_result.violations.append(
                Violation(code="vision_reference_missing", grade="A", message=msg)
            )
            return rule_result

        llm_result = self.text_validator.validate(
            template_id=template_id,
            reference_data=reference.reference,
            submission_data=submission_data,
            media_url=reference.media_url,
            media_meta=getattr(reference, "media_meta", None) or {},
        )
        rule_result.reference_check = "rule_soft_pass+vision_ref+llm_text"
        if rule_result.rule_phase_grade == "S" and any(
            v.code in (self._load_template_config(template_id).get("phase_gate", {}).get("llm_defer_codes") or [])
            for v in rule_result.violations
        ):
            rule_result.reference_check = "rule_deferred+vision_ref+llm_text"
        rule_result.violations.extend(llm_result.get("violations") or [])
        grades = [rule_result.rule_phase_grade or "S", llm_result.get("audit_grade") or "A"]

        if self.enable_json_reference_check:
            json_violations = self._apply_json_reference_check(row, template_id, reference)
            rule_result.violations.extend(json_violations)
            if json_violations:
                rule_result.reference_check += "+json_ref_mismatch"
                grades.append(worst_grade([v.grade for v in json_violations]))
            else:
                rule_result.reference_check += "+json_ref_ok"

        rule_result.audit_grade = worst_grade(grades)
        rule_result.passed = rule_result.audit_grade == "S"
        return rule_result

    def _apply_json_reference_check(
        self,
        row: Dict[str, Any],
        template_id: str,
        reference: TaskReferenceRecord,
    ) -> List[Violation]:
        config = self._load_template_config(template_id)
        min_overlap = float(config.get("thresholds", {}).get("reference_min_overlap", 0.12))
        submission_data = resolve_submission_data(row)

        if template_id == TEMPLATE_SEGMENT:
            payload = parse_json_payload(submission_data)
            list_keys = config.get("segment_list_keys", [])
            segments = parse_segments(payload, list_keys)
            return check_reference_match(segments, reference, min_overlap=min_overlap)

        if template_id == TEMPLATE_METADATA:
            payload = parse_json_payload(submission_data)
            data = extract_metadata(payload)
            return check_metadata_reference(data, reference, min_overlap=min_overlap)

        return []


def _print_row_result(index: int, total: int, row: Dict[str, Any], result: AuditResult) -> None:
    submission_id = str(row.get("submission_id") or result.submission_id or "?")
    task_id = str(row.get("task_id") or result.task_id or "")
    template_id = str(row.get("template_id") or result.template_id or "")
    user_id = str(row.get("user_id") or result.user_id or "")

    status_text = "通过" if result.passed else "驳回"
    rule_grade = result.rule_phase_grade or result.audit_grade

    lines = [
        f"[audit] ({index}/{total}) submission_id={submission_id}",
        f"  task_id={task_id}  template_id={template_id}  user_id={user_id}",
        f"  前置规则={rule_grade}  最终等级={result.audit_grade}  {status_text}  reference_check={result.reference_check}",
    ]

    if result.reference_path:
        lines.append(f"  reference_path={result.reference_path}")

    if result.segment_count:
        lines.append(f"  分段数={result.segment_count}")

    if result.violations:
        lines.append("  违规明细:")
        for violation in result.violations[:5]:
            seg = ""
            if violation.segment_index is not None:
                seg = f" [段{violation.segment_index + 1}]"
            field = f" [{violation.field}]" if violation.field else ""
            lines.append(f"    - [{violation.grade}] {violation.message}{seg}{field}")
        if len(result.violations) > 5:
            lines.append(f"    - ... 还有 {len(result.violations) - 5} 条")
    else:
        lines.append("  违规明细: 无")

    if result.error:
        lines.append(f"  错误: {result.error}")

    print("\n".join(lines), flush=True)
