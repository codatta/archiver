"""
OTC 截图审核核心模块
从数据库或 JSON 读取任务，使用 Qwen 视觉模型进行图片质量检查、关键字段提取、上下文分析。
"""

from .models import OTCSubmission, OTCAuditResult
from .otc_qwen_auditor import OTCQwenAuditor

__all__ = ["OTCSubmission", "OTCAuditResult", "OTCQwenAuditor"]
