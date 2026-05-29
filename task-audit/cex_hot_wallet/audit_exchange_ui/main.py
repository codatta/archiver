"""
数据审核主程序
"""
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List

from .data_loader import DataLoader
from .qwen_auditors import DepositQwenAuditor, WithdrawQwenAuditor
from .models import AuditReport, AuditResult, TransactionType


def load_config():
    """加载配置"""
    from dotenv import load_dotenv
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
    else:
        print("警告: 未找到.env文件，将使用环境变量")


def load_existing_reports(output_file: str) -> tuple[dict[str, AuditReport], List[AuditReport]]:
    """
    加载已有的审核报告
    
    Args:
        output_file: 报告文件路径
        
    Returns:
        (已审核记录的字典 {submission_id: AuditReport}, 所有已有报告的列表) 元组
    """
    output_path = Path(output_file)
    if not output_path.exists():
        return {}, []
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            reports_data = json.load(f)
        
        existing_reports = []
        existing_dict = {}
        
        for report_data in reports_data:
            # 从字典重建 AuditReport 对象
            from .models import TransactionRecord, TransactionType, AuditCheckResult
            
            record_data = report_data.get("record", {})
            record = TransactionRecord(
                submission_id=record_data.get("submission_id", ""),
                date=record_data.get("date", ""),
                type=TransactionType(record_data.get("type", "deposit")),
                token=record_data.get("token", ""),
                amount=record_data.get("amount", ""),
                network=record_data.get("network", ""),
                exchange_name=record_data.get("exchange_name", ""),
                exchange_ui_screenshot_url=record_data.get("exchange_ui_screenshot_url", ""),
                raw_data=record_data,  # 保存原始数据
            )
            
            checks = []
            for check_data in report_data.get("checks", []):
                check = AuditCheckResult(
                    check_name=check_data.get("check_name", ""),
                    result=AuditResult(check_data.get("result", "unknown")),
                    reason=check_data.get("reason", ""),
                    confidence=check_data.get("confidence"),
                    llm_response=check_data.get("llm_response"),
                )
                checks.append(check)
            
            report = AuditReport(
                submission_id=report_data.get("submission_id", ""),
                record=record,
                checks=checks,
                overall_result=AuditResult(report_data.get("overall_result", "unknown")),
                timestamp=report_data.get("timestamp", ""),
                reason=report_data.get("reason"),  # 加载失败原因
                llm_raw_response=report_data.get("llm_raw_response"),
            )
            
            existing_reports.append(report)
            existing_dict[report.submission_id] = report
        
        return existing_dict, existing_reports
    except Exception as e:
        print(f"加载已有报告时出错: {e}，将重新开始审核")
        return {}, []


def save_single_report(report: AuditReport, output_file: str):
    """
    保存单条审核报告到文件（增量写入）
    
    Args:
        report: 审核报告
        output_file: 输出文件路径
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 加载已有报告
    existing_dict, _ = load_existing_reports(output_file)
    
    # 更新或添加新报告
    existing_dict[report.submission_id] = report
    
    # 转换为列表并保存
    all_reports = list(existing_dict.values())
    reports_dict = [r.to_dict() for r in all_reports]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(reports_dict, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 已保存: {report.submission_id} ({report.overall_result.value})")


def save_reports(reports: List[AuditReport], output_file: str, merge_with_existing: bool = True):
    """
    保存审核报告到文件（批量保存，用于最终汇总）
    
    Args:
        reports: 审核报告列表
        output_file: 输出文件路径
        merge_with_existing: 是否与已有报告合并
    """
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if merge_with_existing:
        # 加载已有报告
        existing_dict, existing_reports = load_existing_reports(output_file)
        
        # 合并报告：新报告覆盖已有报告
        merged_dict = existing_dict.copy()
        for report in reports:
            merged_dict[report.submission_id] = report
        
        # 转换为列表
        all_reports = list(merged_dict.values())
    else:
        all_reports = reports
    
    reports_dict = [report.to_dict() for report in all_reports]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(reports_dict, f, ensure_ascii=False, indent=2)
    
    print(f"审核报告已保存到: {output_path} (共 {len(all_reports)} 条记录)")


def print_summary(reports: List[AuditReport]):
    """
    打印审核摘要
    
    Args:
        reports: 审核报告列表
    """
    total = len(reports)
    passed = sum(1 for r in reports if r.overall_result == AuditResult.PASS)
    failed = sum(1 for r in reports if r.overall_result == AuditResult.FAIL)
    unknown = sum(1 for r in reports if r.overall_result == AuditResult.UNKNOWN)
    
    print("\n" + "="*60)
    print("审核摘要")
    print("="*60)
    print(f"总记录数: {total}")
    print(f"通过: {passed} ({passed/total*100:.1f}%)")
    print(f"失败: {failed} ({failed/total*100:.1f}%)")
    print(f"未知: {unknown} ({unknown/total*100:.1f}%)")
    print("="*60)
    
    # 打印失败的记录
    if failed > 0:
        print("\n失败的记录:")
        for report in reports:
            if report.overall_result == AuditResult.FAIL:
                print(f"  - {report.submission_id}")
                for check in report.checks:
                    if check.result == AuditResult.FAIL:
                        print(f"    × {check.check_name}: {check.reason}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="交易所数据审核工具")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="raw_data",
        help="原始数据目录（默认: raw_data）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output/audit_exchange_ui/audit_report.json",
        help="输出文件路径（默认: output/audit_exchange_ui/audit_report.json）"
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["deposit", "withdraw", "all"],
        default="all",
        help="审核类型: deposit(入金), withdraw(提现), all(全部，默认)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="Qwen API密钥（可选，优先使用环境变量）"
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=None,
        help="Qwen API基础URL（可选，优先使用环境变量）"
    )
    
    args = parser.parse_args()
    
    # 加载配置
    load_config()
    
    # 加载数据
    print("正在加载数据...")
    loader = DataLoader(args.data_dir)
    
    # 先统计输入文件的总记录数
    import json
    from pathlib import Path
    submissions_file = Path(args.data_dir) / "submissions.json"
    total_in_file = 0
    if submissions_file.exists():
        with open(submissions_file, 'r', encoding='utf-8') as f:
            total_in_file = len(json.load(f))
    
    if args.type == "deposit":
        records, input_file = loader.load_deposit_records()
        print(f"输入文件: {input_file}")
        if total_in_file > 0:
            print(f"文件总记录数: {total_in_file} 条")
        print(f"成功加载: {len(records)} 条入金记录")
    elif args.type == "withdraw":
        records, input_file = loader.load_withdraw_records()
        print(f"输入文件: {input_file}")
        if total_in_file > 0:
            print(f"文件总记录数: {total_in_file} 条")
        print(f"成功加载: {len(records)} 条提现记录")
    else:
        records, input_files = loader.load_all_records()
        if len(input_files) == 1:
            print(f"输入文件: {input_files[0]}")
            if total_in_file > 0:
                print(f"文件总记录数: {total_in_file} 条")
        else:
            print(f"输入文件: {', '.join(input_files)}")
        print(f"成功加载: {len(records)} 条记录（入金+提现）")
    
    if not records:
        print("没有找到需要审核的记录")
        return
    
    # 加载已有报告，检查哪些记录已经审核过
    print(f"检查已有审核报告: {args.output}")
    existing_dict, existing_reports = load_existing_reports(args.output)
    already_audited_count = len(existing_dict)
    
    if already_audited_count > 0:
        print(f"发现 {already_audited_count} 条已审核的记录")
    
    # 过滤出需要审核的记录
    records_to_audit = [r for r in records if r.submission_id not in existing_dict]
    skipped_count = len(records) - len(records_to_audit)
    
    if skipped_count > 0:
        print(f"跳过 {skipped_count} 条已审核的记录")
    
    if not records_to_audit:
        print("所有记录都已审核过，无需重新审核")
        # 打印已有报告的摘要
        print_summary(existing_reports)
        return
    
    # 初始化审核器
    print("正在初始化审核器...")
    try:
        deposit_auditor = DepositQwenAuditor(api_key=args.api_key, base_url=args.base_url)
        withdraw_auditor = WithdrawQwenAuditor(api_key=args.api_key, base_url=args.base_url)
        print("✓ 审核器初始化成功（入金和提现审核器）")
    except ValueError as e:
        print(f"错误: {e}")
        print("请设置 QWEN_API_KEY 环境变量或使用 --api-key 参数")
        return
    
    # 执行审核（根据记录类型选择合适的审核器）
    print(f"\n开始审核 {len(records_to_audit)} 条新记录...")
    print("这可能需要一些时间，请耐心等待...\n")
    
    reports = []
    for i, record in enumerate(records_to_audit, 1):
        try:
            print(f"[{i}/{len(records_to_audit)}] 正在审核: {record.submission_id}...")
            
            # 根据记录类型选择审核器
            if record.type == TransactionType.DEPOSIT:
                auditor = deposit_auditor
            else:  # TransactionType.WITHDRAWAL
                auditor = withdraw_auditor
            
            report = auditor.audit(record)
            reports.append(report)
            
            # 立即保存单条结果
            save_single_report(report, args.output)
            
        except Exception as e:
            print(f"✗ 审核记录失败: {record.submission_id}, 错误: {e}")
            # 创建失败的审核报告
            failed_report = AuditReport(
                submission_id=record.submission_id,
                record=record,
                checks=[],
                overall_result=AuditResult.UNKNOWN,
                timestamp=datetime.now().isoformat(),
                reason=f"审核过程出错: {str(e)}",
            )
            reports.append(failed_report)
            # 立即保存失败的结果
            save_single_report(failed_report, args.output)
    
    # 加载合并后的所有报告用于显示摘要
    _, all_reports = load_existing_reports(args.output)
    
    # 打印摘要（包含所有记录）
    print_summary(all_reports)
    
    if len(reports) > 0:
        print(f"\n本次新增审核: {len(reports)} 条记录")
    print("\n审核完成！")


if __name__ == "__main__":
    main()
