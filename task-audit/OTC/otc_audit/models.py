"""
OTC 审核数据模型
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional, List


@dataclass
class OTCSubmission:
    """单条 OTC 提交任务（来自 DB 或 JSON）"""
    submission_id: str
    screenshot_url: str
    chain: str = ""
    address: str = ""
    otc_desk: str = ""
    raw_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.raw_data is None:
            self.raw_data = {}


@dataclass
class OTCAuditResult:
    """
    单条审核结果：图片质量检查 + 关键字段提取 + 扩展信息

    关键字段规范：
    - chain: 需映射为标准枚举（如 ethereum_mainnet、tron_mainnet 等）
    - address: 截图中识别到的地址（或基于截图确认的地址）
    - entities: OTC 实体名称
    - labels: 对实体的标签，如 Crypto OTC
    - website_link: 标准化后的 http(s) 链接或 null
    - txid: 截图中识别到的交易哈希
    - extensions: 额外信息（phone/country/city/fiat/token 等）
    """

    submission_id: str
    # 1. 图片质量检查
    image_quality_clear: Optional[bool] = None
    image_quality_tampered: Optional[bool] = None
    image_quality_text_readable: Optional[bool] = None
    image_quality_notes: str = ""
    # 2. 关键字段提取（规范化命名）
    chain: Optional[str] = None
    address: Optional[str] = None
    entities: Optional[str] = None
    labels: Optional[str] = None
    website_link: Optional[str] = None
    txid: Optional[str] = None
    screenshot_link: Optional[str] = None
    trace_type: Optional[str] = None
    # 3. 扩展字段
    extensions: Optional[Dict[str, Any]] = None

    raw_llm_response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "submission_id": self.submission_id,
            "image_quality": {
                "clear": self.image_quality_clear,
                "tampered": self.image_quality_tampered,
                "text_readable": self.image_quality_text_readable,
                "notes": self.image_quality_notes,
            },
            "extracted": {
                "chain": self.chain,
                "address": self.address,
                "entities": self.entities,
                "labels": self.labels,
                "website_link": self.website_link,
                "txid": self.txid,
                "screenshot_link": self.screenshot_link,
                "trace_type": self.trace_type,
            },
            "extensions": self.extensions or {},
            "raw_llm_response": self.raw_llm_response,
            "error": self.error,
        }
