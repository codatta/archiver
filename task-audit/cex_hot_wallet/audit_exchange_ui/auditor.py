"""
审核器基类和接口
"""
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime

from .models import TransactionRecord, AuditReport, AuditCheckResult, AuditResult


class Auditor(ABC):
    """审核器基类"""
    
    def __init__(self):
        """初始化审核器"""
        pass
    
    @abstractmethod
    def audit(self, record: TransactionRecord) -> AuditReport:
        """
        审核单个交易记录
        
        Args:
            record: 交易记录
            
        Returns:
            审核报告
        """
        pass
    
    def audit_batch(self, records: List[TransactionRecord]) -> List[AuditReport]:
        """
        批量审核交易记录
        
        Args:
            records: 交易记录列表
            
        Returns:
            审核报告列表
        """
        reports = []
        for record in records:
            try:
                report = self.audit(record)
                reports.append(report)
            except Exception as e:
                print(f"审核记录失败: {record.submission_id}, 错误: {e}")
                # 创建失败的审核报告
                failed_report = AuditReport(
                    submission_id=record.submission_id,
                    record=record,
                    checks=[],
                    overall_result=AuditResult.UNKNOWN,
                    timestamp=datetime.now().isoformat(),
                )
                reports.append(failed_report)
        return reports
    
    def _determine_overall_result(self, checks: List[AuditCheckResult]) -> AuditResult:
        """
        根据各项检查结果确定总体结果
        
        Args:
            checks: 检查结果列表
            
        Returns:
            总体审核结果
        """
        if not checks:
            return AuditResult.UNKNOWN
        
        # 如果任何一项检查失败，则整体失败
        for check in checks:
            if check.result == AuditResult.FAIL:
                return AuditResult.FAIL
        
        # 如果所有检查都通过，则整体通过
        if all(check.result == AuditResult.PASS for check in checks):
            return AuditResult.PASS
        
        # 否则为未知状态
        return AuditResult.UNKNOWN
