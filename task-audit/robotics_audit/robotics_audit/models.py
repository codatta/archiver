from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

GRADE_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4, "Error": 5}

TEMPLATE_SEGMENT = "ROBOTICS_TPL_000001"
TEMPLATE_METADATA = "ROBOTICS_TPL_000003"


@dataclass
class Segment:
    index: int
    start: float
    end: float
    description: str
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Violation:
    code: str
    grade: str
    message: str
    segment_index: Optional[int] = None
    field: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "grade": self.grade,
            "message": self.message,
            "segment_index": self.segment_index,
            "field": self.field,
        }


@dataclass
class ElementAnalysis:
    subject: bool = False
    action: bool = False
    object: bool = False
    result: bool = False

    @property
    def count(self) -> int:
        return sum([self.subject, self.action, self.object, self.result])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "subject": self.subject,
            "action": self.action,
            "object": self.object,
            "result": self.result,
            "count": self.count,
        }


@dataclass
class SegmentAuditDetail:
    segment_index: int
    start: float
    end: float
    description: str
    elements: ElementAnalysis
    violations: List[Violation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_index": self.segment_index,
            "start": self.start,
            "end": self.end,
            "description": self.description,
            "elements": self.elements.to_dict(),
            "violations": [v.to_dict() for v in self.violations],
        }


@dataclass
class AuditResult:
    submission_id: str
    user_id: str = ""
    frontier_id: str = ""
    template_id: str = ""
    task_id: str = ""
    audit_grade: str = "S"
    passed: bool = True
    violations: List[Violation] = field(default_factory=list)
    segment_details: List[SegmentAuditDetail] = field(default_factory=list)
    video_duration: Optional[float] = None
    segment_count: int = 0
    reference_check: str = "skipped"
    reference_path: Optional[str] = None
    rule_phase_grade: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "user_id": self.user_id,
            "frontier_id": self.frontier_id,
            "template_id": self.template_id,
            "task_id": self.task_id,
            "audit_grade": self.audit_grade,
            "passed": self.passed,
            "status": grade_to_status(self.audit_grade),
            "result": grade_to_result_score(self.audit_grade),
            "segment_count": self.segment_count,
            "video_duration": self.video_duration,
            "reference_check": self.reference_check,
            "reference_path": self.reference_path,
            "rule_phase_grade": self.rule_phase_grade,
            "violations": [v.to_dict() for v in self.violations],
            "segment_details": [d.to_dict() for d in self.segment_details],
            "error": self.error,
        }


def grade_to_status(grade: str) -> str:
    g = str(grade or "").upper()
    if g == "S":
        return "ADOPT"
    if g in {"A", "B", "C", "D"}:
        return "REFUSED"
    return "PENDING"


def grade_to_result_score(grade: str) -> int:
    mapping = {"D": 1, "C": 2, "B": 3, "A": 4, "S": 5}
    return mapping.get(str(grade or "").upper(), 0)


def worst_grade(grades: List[str]) -> str:
    if not grades:
        return "S"
    return max(grades, key=lambda g: GRADE_ORDER.get(g, 99))
