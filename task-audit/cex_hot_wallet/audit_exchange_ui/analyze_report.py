"""
审核报告统计分析工具
"""
import json
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any


def load_audit_report(report_file: str) -> List[Dict[str, Any]]:
    """加载审核报告"""
    report_path = Path(report_file)
    if not report_path.exists():
        raise FileNotFoundError(f"报告文件不存在: {report_file}")
    
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def analyze_report(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """分析审核报告"""
    total = len(reports)
    if total == 0:
        return {}
    
    # 总体统计
    overall_stats = {
        "total": total,
        "pass": 0,
        "fail": 0,
        "unknown": 0,
    }
    
    # 各项检查统计
    check_stats = defaultdict(lambda: {"pass": 0, "fail": 0, "unknown": 0})
    
    # 按交易所统计
    exchange_stats = defaultdict(lambda: {"total": 0, "pass": 0, "fail": 0, "unknown": 0})
    
    # 按交易类型统计
    type_stats = defaultdict(lambda: {"total": 0, "pass": 0, "fail": 0, "unknown": 0})
    
    # 失败原因统计
    failure_reasons = defaultdict(int)
    
    # 失败记录详情
    failed_records = []
    
    # 遍历所有报告
    for report in reports:
        overall_result = report.get("overall_result", "unknown")
        overall_stats[overall_result] = overall_stats.get(overall_result, 0) + 1
        
        # 统计各项检查
        for check in report.get("checks", []):
            check_name = check.get("check_name", "unknown")
            check_result = check.get("result", "unknown")
            check_stats[check_name][check_result] = check_stats[check_name].get(check_result, 0) + 1
        
        # 按交易所统计
        exchange_name = report.get("record", {}).get("exchange_name", "unknown")
        exchange_stats[exchange_name]["total"] += 1
        exchange_stats[exchange_name][overall_result] = exchange_stats[exchange_name].get(overall_result, 0) + 1
        
        # 按交易类型统计
        record_type = report.get("record", {}).get("type", "unknown")
        type_stats[record_type]["total"] += 1
        type_stats[record_type][overall_result] = type_stats[record_type].get(overall_result, 0) + 1
        
        # 统计失败原因和记录失败详情
        if overall_result == "fail":
            submission_id = report.get("submission_id", "unknown")
            record = report.get("record", {})
            exchange_name = record.get("exchange_name", "unknown")
            record_type = record.get("type", "unknown")
            
            failed_checks = []
            for check in report.get("checks", []):
                if check.get("result") == "fail":
                    check_name = check.get("check_name", "unknown")
                    failure_reasons[check_name] += 1
                    failed_checks.append(check_name)
            
            failed_records.append({
                "submission_id": submission_id,
                "exchange_name": exchange_name,
                "type": record_type,
                "failed_checks": failed_checks,
            })
    
    return {
        "overall": overall_stats,
        "checks": dict(check_stats),
        "by_exchange": dict(exchange_stats),
        "by_type": dict(type_stats),
        "failure_reasons": dict(failure_reasons),
        "failed_records": failed_records,
    }


def generate_report(analysis: Dict[str, Any]) -> str:
    """生成报告文本"""
    lines = []
    lines.append("=" * 80)
    lines.append("审核报告统计分析")
    lines.append("=" * 80)
    lines.append("")
    
    # 总体统计
    overall = analysis.get("overall", {})
    total = overall.get("total", 0)
    if total > 0:
        lines.append("【总体统计】")
        lines.append(f"  总记录数: {total}")
        pass_count = overall.get("pass", 0)
        fail_count = overall.get("fail", 0)
        unknown_count = overall.get("unknown", 0)
        lines.append(f"  通过: {pass_count} ({pass_count/total*100:.1f}%)")
        lines.append(f"  失败: {fail_count} ({fail_count/total*100:.1f}%)")
        lines.append(f"  未知: {unknown_count} ({unknown_count/total*100:.1f}%)")
        lines.append("")
    
    # 各项检查统计
    checks = analysis.get("checks", {})
    if checks:
        lines.append("【各项检查统计】")
        check_names_cn = {
            "is_exchange_record": "交易所记录验证",
            "exchange_verification": "交易所身份验证",
            "transaction_date_match": "交易日期匹配",
            "transaction_info_match": "其他交易信息匹配",
        }
        for check_name, stats in checks.items():
            check_total = sum(stats.values())
            if check_total > 0:
                check_display = check_names_cn.get(check_name, check_name)
                pass_count = stats.get("pass", 0)
                fail_count = stats.get("fail", 0)
                unknown_count = stats.get("unknown", 0)
                lines.append(f"  {check_display} ({check_name}):")
                lines.append(f"    通过: {pass_count} ({pass_count/check_total*100:.1f}%)")
                lines.append(f"    失败: {fail_count} ({fail_count/check_total*100:.1f}%)")
                lines.append(f"    未知: {unknown_count} ({unknown_count/check_total*100:.1f}%)")
        lines.append("")
    
    # 按交易所统计
    by_exchange = analysis.get("by_exchange", {})
    if by_exchange:
        lines.append("【按交易所统计】")
        for exchange, stats in sorted(by_exchange.items()):
            exchange_total = stats.get("total", 0)
            if exchange_total > 0:
                pass_count = stats.get("pass", 0)
                fail_count = stats.get("fail", 0)
                unknown_count = stats.get("unknown", 0)
                lines.append(f"  {exchange}:")
                lines.append(f"    总数: {exchange_total}")
                lines.append(f"    通过: {pass_count} ({pass_count/exchange_total*100:.1f}%)")
                lines.append(f"    失败: {fail_count} ({fail_count/exchange_total*100:.1f}%)")
                lines.append(f"    未知: {unknown_count} ({unknown_count/exchange_total*100:.1f}%)")
        lines.append("")
    
    # 按交易类型统计
    by_type = analysis.get("by_type", {})
    if by_type:
        lines.append("【按交易类型统计】")
        type_names_cn = {
            "deposit": "入金",
            "withdrawal": "提现",
        }
        for record_type, stats in sorted(by_type.items()):
            type_total = stats.get("total", 0)
            if type_total > 0:
                type_display = type_names_cn.get(record_type, record_type)
                pass_count = stats.get("pass", 0)
                fail_count = stats.get("fail", 0)
                unknown_count = stats.get("unknown", 0)
                lines.append(f"  {type_display} ({record_type}):")
                lines.append(f"    总数: {type_total}")
                lines.append(f"    通过: {pass_count} ({pass_count/type_total*100:.1f}%)")
                lines.append(f"    失败: {fail_count} ({fail_count/type_total*100:.1f}%)")
                lines.append(f"    未知: {unknown_count} ({unknown_count/type_total*100:.1f}%)")
        lines.append("")
    
    # 失败原因统计
    failure_reasons = analysis.get("failure_reasons", {})
    if failure_reasons:
        lines.append("【失败原因统计】")
        check_names_cn = {
            "is_exchange_record": "交易所记录验证",
            "exchange_verification": "交易所身份验证",
            "transaction_date_match": "交易日期匹配",
            "transaction_info_match": "其他交易信息匹配",
        }
        for check_name, count in sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True):
            check_display = check_names_cn.get(check_name, check_name)
            lines.append(f"  {check_display}: {count} 次")
        lines.append("")
    
    # 失败记录详情
    failed_records = analysis.get("failed_records", [])
    if failed_records:
        lines.append("【失败记录详情】")
        check_names_cn = {
            "is_exchange_record": "交易所记录验证",
            "exchange_verification": "交易所身份验证",
            "transaction_date_match": "交易日期匹配",
            "transaction_info_match": "其他交易信息匹配",
        }
        type_names_cn = {
            "deposit": "入金",
            "withdrawal": "提现",
        }
        for record in failed_records:
            submission_id = record.get("submission_id", "unknown")
            exchange_name = record.get("exchange_name", "unknown")
            record_type = record.get("type", "unknown")
            failed_checks = record.get("failed_checks", [])
            
            type_display = type_names_cn.get(record_type, record_type)
            failed_checks_display = [check_names_cn.get(c, c) for c in failed_checks]
            
            lines.append(f"  Submission ID: {submission_id}")
            lines.append(f"    交易所: {exchange_name}")
            lines.append(f"    类型: {type_display}")
            lines.append(f"    失败项: {', '.join(failed_checks_display)}")
            lines.append("")
    
    lines.append("=" * 80)
    
    return "\n".join(lines)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="审核报告统计分析工具")
    parser.add_argument(
        "--report",
        type=str,
        default="output/audit_exchange_ui/audit_report.json",
        help="审核报告文件路径（默认: output/audit_exchange_ui/audit_report.json）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="输出报告文件路径（可选，不指定则打印到控制台）"
    )
    
    args = parser.parse_args()
    
    # 加载报告
    print(f"正在加载审核报告: {args.report}")
    reports = load_audit_report(args.report)
    print(f"加载了 {len(reports)} 条记录")
    
    # 分析报告
    print("正在分析...")
    analysis = analyze_report(reports)
    
    # 生成报告
    report_text = generate_report(analysis)
    
    # 输出报告
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"\n报告已保存到: {output_path}")
    else:
        print("\n" + report_text)


if __name__ == "__main__":
    main()
