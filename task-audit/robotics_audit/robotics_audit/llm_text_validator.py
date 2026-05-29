from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

import requests

from robotics_audit.models import TEMPLATE_METADATA, TEMPLATE_SEGMENT, Violation


class LLMTextValidator:
    """将用户提交与视觉大模型从视频提取的参考内容做纯文本语义比对（宽松模式）。"""

    def __init__(self, model: Optional[str] = None) -> None:
        self.api_key = os.getenv("QWEN_API_KEY", "")
        self.base_url = os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )
        self.model = model or os.getenv("QWEN_TEXT_MODEL", "qwen-plus")
        self.lenient_mode = str(os.getenv("LLM_LENIENT_MODE", "1")).strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def validate(
        self,
        *,
        template_id: str,
        reference_data: Any,
        submission_data: Any,
        media_url: str = "",
        media_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.enabled:
            return {
                "passed": False,
                "audit_grade": "A",
                "violations": [
                    Violation(
                        code="llm_disabled",
                        grade="A",
                        message="未配置 QWEN_API_KEY，无法执行大模型文本校验",
                    )
                ],
                "raw_response": None,
            }

        prompt = self._build_prompt(
            template_id,
            reference_data,
            submission_data,
            media_url,
            media_meta=media_meta or {},
        )
        parsed = self._call_qwen(prompt)
        if not parsed:
            return {
                "passed": False,
                "audit_grade": "A",
                "violations": [
                    Violation(
                        code="llm_parse_error",
                        grade="A",
                        message="大模型文本校验返回无法解析",
                    )
                ],
                "raw_response": None,
            }

        grade, violations = self._normalize_result(parsed)
        return {
            "passed": grade == "S",
            "audit_grade": grade,
            "violations": violations,
            "raw_response": parsed,
        }

    def _normalize_result(self, parsed: Dict[str, Any]) -> tuple[str, List[Violation]]:
        raw_grade = str(parsed.get("audit_grade") or ("S" if parsed.get("passed") else "B")).upper()
        violations: List[Violation] = []
        for item in parsed.get("violations") or []:
            if not isinstance(item, dict):
                continue
            violations.append(
                Violation(
                    code=str(item.get("code") or "llm_semantic_mismatch"),
                    grade=str(item.get("grade") or raw_grade).upper(),
                    message=str(item.get("message") or "与视频参考内容语义不一致"),
                    field=item.get("field"),
                    segment_index=item.get("segment_index"),
                )
            )

        if self.lenient_mode:
            grade = self._apply_lenient_grade(raw_grade, violations)
            if grade == "S":
                violations = []
            elif not violations:
                violations.append(
                    Violation(
                        code="llm_semantic_mismatch",
                        grade=grade,
                        message=str(parsed.get("reason") or "与视频参考内容语义偏差较大"),
                    )
                )
        else:
            grade = raw_grade
            if not violations and grade != "S":
                violations.append(
                    Violation(
                        code="llm_semantic_mismatch",
                        grade=grade,
                        message=str(parsed.get("reason") or "与视频参考内容语义不一致"),
                    )
                )

        return grade, violations

    def _apply_lenient_grade(self, grade: str, violations: List[Violation]) -> str:
        """宽松模式：只有明显乱填或与视频完全无关才驳回（D）。"""
        if grade == "D" and not self._is_severe_rejection(violations, grade):
            return "S"
        if grade in {"A", "B", "C"}:
            return "S"
        if grade == "D" and self._is_severe_rejection(violations, grade):
            return "D"
        return "S"

    @staticmethod
    def _is_severe_rejection(violations: List[Violation], grade: str) -> bool:
        if grade != "D":
            return False
        severe_codes = {
            "llm_garbage",
            "llm_completely_unrelated",
            "llm_empty_placeholder",
        }
        for item in violations:
            if item.code in severe_codes:
                return True
            msg = (item.message or "").lower()
            if any(
                keyword in msg
                for keyword in (
                    "乱填",
                    "完全无关",
                    "placeholder",
                    "gibberish",
                    "完全不符",
                    "毫无关联",
                    "空泛占位",
                )
            ):
                return True
        return False

    def _build_prompt(
        self,
        template_id: str,
        reference_data: Any,
        submission_data: Any,
        media_url: str = "",
        media_meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        media_meta = media_meta or {}
        ref_hint = _timeline_hint(reference_data, submission_data, media_meta)

        if template_id == TEMPLATE_SEGMENT:
            task_desc = "视频时序分段标注（start/end/description）"
            frame_count = media_meta.get("frame_count") or "unknown"
            extra = f"""
分段任务 — 宽松审核原则（默认应通过）:
- 重要：网页播放器左下角「当前帧/总帧数」（如 1/N）表示帧序号，start/end 是 1-based 帧号，不是秒。
- 本 GIF 共 {frame_count} 帧（每个 task 视频帧数不同，以 media_meta 为准）；用户 start/end 应理解为帧号。
- 视频参考 likewise 使用帧号（time_unit=frame），禁止把用户帧号与秒数比较。
- {ref_hint}
- 默认 audit_grade = S。只有明显乱填、或与视频场景/任务完全无关时才给 D。
- 以下差异一律视为可接受：cup/bottle 同义词、分段合并、帧范围与参考不完全对齐。
- 判断标准：整体动作链是否与视频大致一致？是 → S。
"""
        elif template_id == TEMPLATE_METADATA:
            task_desc = "结构化元数据标注（objects/environment/agent_type/view/relations/task）"
            extra = """
元数据任务 — 宽松审核原则（默认应通过）:
- 默认 audit_grade = S。只有明显乱填或与视频场景完全无关时才给 D。
- 允许同义词、近义表达、中英文差异、objects 数量不完全一致。
- environment 用 Indoor 而参考写 Office 等宽泛差异可接受。
- 判断标准：用户标注是否大致描述了同一机器人操作场景？是 → S。
"""
        else:
            task_desc = "机器人视频标注"
            extra = "默认 audit_grade = S，仅明显乱填或完全无关时给 D。"

        return f"""你是宽松的数据标注质检员。原则：语义偏差不大就应通过。

任务类型: {task_desc}
template_id: {template_id}
视频来源: {media_url or "unknown"}

核心要求:
1. 「视频参考内容」是 AI 对 GIF 的粗粒度理解，可能有误差，仅供参考。
2. 默认输出 audit_grade = "S", passed = true, violations = []。
3. 仅在用户提交明显乱填（无意义字符串）、或与视频场景/动作链完全无关时，才给 D。
4. 不要因为措辞、同义词、分段粒度、时间戳偏差而驳回。
5. 只输出一个 JSON 对象，不要 markdown。
{extra}
视频参考内容:
{json.dumps(reference_data, ensure_ascii=False)}

用户提交:
{json.dumps(submission_data, ensure_ascii=False)}

输出 JSON 格式:
{{
  "passed": true,
  "audit_grade": "S",
  "reason": "语义基本一致，通过",
  "violations": []
}}
"""

    def _call_qwen(self, prompt: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=90)
            resp.raise_for_status()
            content = (resp.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
            return self._parse_json(content)
        except Exception as exc:
            print(f"[llm_text] 调用失败: {exc}")
            return None

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        text = (content or "").strip()
        if not text:
            return None
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None


def _max_segment_end(data: Any) -> Optional[float]:
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("segments") or data.get("data") or []
        if isinstance(items, dict):
            items = [items]
    else:
        return None

    max_end: Optional[float] = None
    if not isinstance(items, list):
        return None
    for item in items:
        if not isinstance(item, dict):
            continue
        end = item.get("end")
        try:
            value = float(end)
        except (TypeError, ValueError):
            continue
        max_end = value if max_end is None else max(max_end, value)
    return max_end


def _timeline_hint(reference_data: Any, submission_data: Any, media_meta: Dict[str, Any]) -> str:
    frame_count = media_meta.get("frame_count")
    ref_end = _max_segment_end(reference_data)
    sub_end = _max_segment_end(submission_data)

    if frame_count:
        base = f"GIF 共 {int(frame_count)} 帧，start/end 均为 1-based 帧序号。"
        if sub_end is not None and sub_end <= int(frame_count):
            return base + " 用户帧范围合法，按帧号理解即可。"
        return base

    if ref_end is None or sub_end is None:
        return "若用户时间轴长于参考，以用户为准，不要因参考不完整而判错"
    if sub_end > ref_end + 5:
        return (
            f"用户最大 end={sub_end}，参考最大 end={ref_end}；"
            "参考可能未覆盖全片，禁止因不一致而驳回"
        )
    return "帧/时间戳允许较大偏差，不要求与参考精确对齐"
