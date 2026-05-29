"""视频审核综合入口（编排 + 输出结构）。"""

from .output_builder import build_rating_results, final_grade_from_result, summarize_comprehensive
from .video_auditor import VideoAuditor

__all__ = [
    "VideoAuditor",
    "summarize_comprehensive",
    "build_rating_results",
    "final_grade_from_result",
]
