"""
评级模块
根据综合审核结果计算每条数据的最终评级
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import csv

from utils import load_json, save_json


class RatingCalculator:
    """评级计算器"""
    
    def __init__(self):
        """初始化评级计算器"""
        pass
    
    def _generate_rating_reason(self, audit_result: Dict[str, Any], rating: int) -> str:
        """
        生成评级理由
        
        Args:
            audit_result: 审核结果字典
            rating: 评级分数
            
        Returns:
            简短的理由说明
        """
        ui_audit = audit_result.get("ui_audit")
        txhash_audit = audit_result.get("txhash_audit")
        
        if not ui_audit:
            return "缺少UI审核结果"
        
        ui_checks = ui_audit.get("checks", [])
        ui_check_dict = {check.get("check_name"): check.get("result") for check in ui_checks}
        
        if rating == 1:
            return "交易所记录验证不通过"
        elif rating == 2:
            return "交易所身份验证不通过"
        elif rating == 3:
            # 找出不通过的UI检查项
            failed_ui_checks = [name for name, result in ui_check_dict.items() if result != "pass"]
            if failed_ui_checks:
                return f"UI审核部分不通过: {', '.join(failed_ui_checks)}"
            return "其他情况"
        elif rating == 4:
            # 只有 transaction_date_match（ui_audit 和 txhash_audit）不通过，其他都通过
            return "只有交易日期匹配不通过（UI审核和交易哈希审核），其他检查项均通过"
        elif rating == 5:
            return "所有审核子项均通过"
        
        return "未知原因"
    
    def _extract_check_results(self, audit_result: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """
        提取所有检查项的结果
        
        Args:
            audit_result: 审核结果字典
            
        Returns:
            {"模块名": {"check_name": "result"}} 格式的字典
        """
        checks_summary = {}
        
        # UI 审核检查项
        ui_audit = audit_result.get("ui_audit")
        if ui_audit:
            ui_checks = ui_audit.get("checks", [])
            checks_summary["ui_audit"] = {
                check.get("check_name"): check.get("result", "unknown")
                for check in ui_checks
            }
        
        # 交易哈希审核检查项
        txhash_audit = audit_result.get("txhash_audit")
        if txhash_audit:
            txhash_checks = txhash_audit.get("checks", [])
            checks_summary["txhash_audit"] = {
                check.get("check_name"): check.get("result", "unknown")
                for check in txhash_checks
            }
        
        return checks_summary
    
    def calculate_rating(self, audit_result: Dict[str, Any]) -> int:
        """
        计算单条记录的评级
        
        评级规则（按优先级顺序）：
        1. is_exchange_record 如果不通过的话，评分为1
        2. exchange_verification 如果不通过的话，评分为2
        3. 只有 transaction_date_match（ui_audit 和 txhash_audit）不通过，其他都通过的话，评分为4
        4. 所有都通过的，评分为5
        5. 其他，评分为3
        
        Args:
            audit_result: 单条审核结果字典
            
        Returns:
            评级分数 (1-5)
        """
        ui_audit = audit_result.get("ui_audit")
        txhash_audit = audit_result.get("txhash_audit")
        
        # 如果没有 UI 审核结果，无法评级
        if not ui_audit:
            return 3  # 默认 3 分
        
        # 获取 UI 审核的检查项结果
        ui_checks = ui_audit.get("checks", [])
        ui_check_dict = {check.get("check_name"): check.get("result") for check in ui_checks}
        
        # 规则 1: is_exchange_record 如果不通过的话，评分为1
        is_exchange_record_result = ui_check_dict.get("is_exchange_record")
        if is_exchange_record_result != "pass":
            return 1
        
        # 规则 2: exchange_verification 如果不通过的话，评分为2
        exchange_verification_result = ui_check_dict.get("exchange_verification")
        if exchange_verification_result != "pass":
            return 2
        
        # 检查所有 UI 审核子项是否都通过
        all_ui_passed = all(
            check.get("result") == "pass" 
            for check in ui_checks
        )
        
        # 检查所有 txhash 审核子项是否都通过
        all_txhash_passed = True
        if txhash_audit:
            txhash_checks = txhash_audit.get("checks", [])
            all_txhash_passed = all(
                check.get("result") == "pass"
                for check in txhash_checks
            )
        else:
            # 如果没有 txhash 审核结果，认为都通过（不影响评级）
            all_txhash_passed = True
        
        # 规则 4: 所有都通过的，评分为5
        if all_ui_passed and all_txhash_passed:
            return 5
        
        # 规则 3: 只有 transaction_date_match（ui_audit 和 txhash_audit）不通过，其他都通过的话，评分为4
        ui_transaction_date_match_result = ui_check_dict.get("transaction_date_match")
        
        # 获取 txhash_audit 中的 transaction_date_match 结果
        txhash_transaction_date_match_result = None
        if txhash_audit:
            txhash_checks = txhash_audit.get("checks", [])
            txhash_check_dict = {check.get("check_name"): check.get("result") for check in txhash_checks}
            txhash_transaction_date_match_result = txhash_check_dict.get("transaction_date_match")
        
        # 检查两个 transaction_date_match 是否都不通过
        ui_date_match_failed = ui_transaction_date_match_result != "pass"
        txhash_date_match_failed = txhash_transaction_date_match_result is not None and txhash_transaction_date_match_result != "pass"
        
        # 如果两个日期匹配都不通过
        if ui_date_match_failed and txhash_date_match_failed:
            # 检查其他所有 UI 检查项是否都通过
            other_ui_passed = all(
                check.get("result") == "pass"
                for check in ui_checks
                if check.get("check_name") != "transaction_date_match"
            )
            # 检查其他所有 txhash 检查项是否都通过
            other_txhash_passed = True
            if txhash_audit:
                txhash_checks = txhash_audit.get("checks", [])
                other_txhash_passed = all(
                    check.get("result") == "pass"
                    for check in txhash_checks
                    if check.get("check_name") != "transaction_date_match"
                )
            # 如果其他所有检查项都通过，则返回 4 分
            if other_ui_passed and other_txhash_passed:
                return 4
        
        # 规则 5: 其他，评分为3
        return 3
    
    def calculate_ratings_from_file(
        self,
        comprehensive_results_path: str,
        output_path: Optional[str] = None,
        csv_output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        从综合审核结果文件计算所有记录的评级
        
        Args:
            comprehensive_results_path: 综合审核结果文件路径
            output_path: 输出评级结果文件路径（可选）
            
        Returns:
            评级结果字典
        """
        # 加载综合审核结果
        comprehensive_data = load_json(comprehensive_results_path)
        if not comprehensive_data:
            return {
                "result": "error",
                "error": f"无法加载综合审核结果文件: {comprehensive_results_path}"
            }
        
        audit_results = comprehensive_data.get("audit_results", [])
        if not audit_results:
            return {
                "result": "error",
                "error": "综合审核结果文件中没有审核结果"
            }
        
        print(f"找到 {len(audit_results)} 条审核记录，开始计算评级...")
        
        # 计算每条记录的评级
        rated_results = []
        rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for audit_result in audit_results:
            submission_id = audit_result.get("submission_id")
            rating = self.calculate_rating(audit_result)
            reason = self._generate_rating_reason(audit_result, rating)
            checks_summary = self._extract_check_results(audit_result)
            
            # 获取交易类型（优先从 txhash_audit 获取，否则从 ui_audit 获取）
            transaction_type = None
            txhash_audit = audit_result.get("txhash_audit")
            if txhash_audit and txhash_audit.get("type"):
                transaction_type = txhash_audit.get("type")
            else:
                ui_audit = audit_result.get("ui_audit")
                if ui_audit:
                    record = ui_audit.get("record", {})
                    transaction_type = record.get("type")
            
            rated_result = {
                "submission_id": submission_id,
                "type": transaction_type or "unknown",
                "rating": rating,
                "reason": reason,
                "checks": checks_summary
            }
            rated_results.append(rated_result)
            rating_counts[rating] = rating_counts.get(rating, 0) + 1
            
            print(f"  {submission_id} ({transaction_type or 'unknown'}): {rating}分 - {reason}")
        
        # 构建结果
        result = {
            "result": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(rated_results),
                "rating_distribution": rating_counts
            },
            "rated_results": rated_results
        }
        
        # 保存 JSON 结果
        if output_path:
            if save_json(result, output_path):
                print(f"\n评级结果已保存到: {output_path}")

        # 额外产出一个只包含 submission_id 和 rating 的 CSV 文件
        if csv_output_path:
            csv_path = Path(csv_output_path)
        elif output_path:
            # 如果未指定 csv_output_path，则在 JSON 同目录下生成一个默认文件
            json_path = Path(output_path)
            csv_path = json_path.with_name("rating_results_simple.csv")
        else:
            csv_path = None

        if csv_path:
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # 只写两列：submission_id 和 rating
                writer.writerow(["submission_id", "rating"])
                for item in rated_results:
                    writer.writerow([item.get("submission_id", ""), item.get("rating", "")])
            print(f"简单评级CSV已生成: {csv_path}")
        
        # 打印汇总
        self._print_summary(result["summary"])
        
        return result
    
    def _print_summary(self, summary: Dict):
        """打印评级汇总"""
        total = summary.get("total", 0)
        distribution = summary.get("rating_distribution", {})
        
        print("\n" + "="*60)
        print("评级汇总")
        print("="*60)
        print(f"总记录数: {total}")
        for rating in sorted(distribution.keys()):
            count = distribution[rating]
            percentage = (count / total * 100) if total > 0 else 0
            print(f"{rating}分: {count} ({percentage:.1f}%)")
        print("="*60)


def main():
    """主函数"""
    import argparse
    
    script_dir = Path(__file__).parent.absolute()
    cex_hot_wallet_dir = script_dir.parent
    
    parser = argparse.ArgumentParser(description="评级计算工具")
    parser.add_argument(
        "--comprehensive-results",
        type=str,
        default=str(cex_hot_wallet_dir / "output" / "main_audit" / "comprehensive_audit_results.json"),
        help="综合审核结果文件路径（默认: output/main_audit/comprehensive_audit_results.json）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(cex_hot_wallet_dir / "output" / "main_audit" / "rating_results.json"),
        help="输出评级结果 JSON 文件路径（默认: output/main_audit/rating_results.json）",
    )
    parser.add_argument(
        "--csv-output",
        type=str,
        default=None,
        help="输出简单评级 CSV 文件路径（只包含 submission_id 和 rating；默认与 JSON 同目录生成 rating_results_simple.csv）",
    )
    
    args = parser.parse_args()
    
    calculator = RatingCalculator()
    result = calculator.calculate_ratings_from_file(
        comprehensive_results_path=args.comprehensive_results,
        output_path=args.output,
        csv_output_path=args.csv_output,
    )
    
    if result.get("result") != "success":
        print(f"评级计算失败: {result.get('error', '未知错误')}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
