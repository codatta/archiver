"""
数据模型定义
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class TransactionType(str, Enum):
    """交易类型"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class AuditResult(str, Enum):
    """审核结果"""
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


@dataclass
class TransactionRecord:
    """交易记录数据模型"""
    submission_id: str
    date: str
    type: TransactionType
    token: str
    amount: str
    network: str
    exchange_name: str
    exchange_ui_screenshot_url: str
    raw_data: Dict[str, Any]  # 原始数据，用于扩展
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "submission_id": self.submission_id,
            "date": self.date,
            "type": self.type.value,
            "token": self.token,
            "amount": self.amount,
            "network": self.network,
            "exchange_name": self.exchange_name,
            "exchange_ui_screenshot_url": self.exchange_ui_screenshot_url,
        }
        
        # 根据交易类型添加特定字段
        if self.type == TransactionType.WITHDRAWAL:
            # 提现记录：添加 address 和 tx_hash
            result["address"] = self.raw_data.get("address", "")
            result["tx_hash"] = self.raw_data.get("tx_hash", "")
        else:
            # 入金记录：添加 tx_hash
            result["tx_hash"] = self.raw_data.get("tx_hash", "")
        
        return result


@dataclass
class AuditCheckResult:
    """单个审核检查项的结果"""
    check_name: str
    result: AuditResult
    reason: str
    confidence: Optional[float] = None  # 置信度 0-1
    llm_response: Optional[Dict[str, Any]] = None  # LLM返回的原始完整数据


@dataclass
class AuditReport:
    """完整的审核报告"""
    submission_id: str
    record: TransactionRecord
    checks: list[AuditCheckResult]
    overall_result: AuditResult
    timestamp: str
    reason: Optional[str] = None  # 失败原因概述
    llm_raw_response: Optional[Dict[str, Any]] = None  # LLM返回的完整原始响应
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "submission_id": self.submission_id,
            "overall_result": self.overall_result.value,
            "timestamp": self.timestamp,
            "record": self.record.to_dict(),
            "checks": [
                {
                    "check_name": check.check_name,
                    "result": check.result.value,
                    "llm_response": check.llm_response,  # 保留LLM返回的完整原始数据（包含reason和confidence）
                }
                for check in self.checks
            ],
        }
        # 如果有失败原因，添加reason字段
        if self.reason:
            result["reason"] = self.reason
        # 如果有LLM的完整原始响应，也保存下来
        if self.llm_raw_response:
            result["llm_raw_response"] = self.llm_raw_response
        return result
