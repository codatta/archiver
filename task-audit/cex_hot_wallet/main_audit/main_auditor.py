"""
综合审核主入口
整合 audit_exchange_ui 和 audit_txhash 两个审核模块
"""
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime
import os

from audit_exchange_ui.qwen_auditors import DepositQwenAuditor, WithdrawQwenAuditor
from audit_exchange_ui.models import TransactionRecord, TransactionType
from audit_txhash.txhash_auditor import TxHashAuditor
from utils import load_json, save_json, parse_submission_data
from db_client import SubmissionDBClient


class MainAuditor:
    """综合审核器"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化综合审核器
        
        Args:
            api_key: Qwen API密钥（可选，优先使用环境变量）
            base_url: Qwen API基础URL（可选，优先使用环境变量）
        """
        self._init_ui_auditors(api_key, base_url)
        self.txhash_auditor = TxHashAuditor()
        print("✓ 综合审核器初始化完成")
    
    def _init_ui_auditors(self, api_key: Optional[str], base_url: Optional[str]):
        """初始化交易所界面审核器"""
        try:
            self.deposit_ui_auditor = DepositQwenAuditor(api_key=api_key, base_url=base_url)
            self.withdraw_ui_auditor = WithdrawQwenAuditor(api_key=api_key, base_url=base_url)
        except ValueError as e:
            print(f"警告: 交易所界面审核器初始化失败: {e}")
            self.deposit_ui_auditor = None
            self.withdraw_ui_auditor = None
    
    def _build_transaction_record(self, submission_id: str, submission_data: Dict) -> TransactionRecord:
        """构建 TransactionRecord 对象"""
        record_type = TransactionType.DEPOSIT if submission_data.get("type", "").lower() == "deposit" else TransactionType.WITHDRAWAL
        
        return TransactionRecord(
            submission_id=submission_id,
            date=submission_data.get("date") or submission_data.get("transaction_date", ""),
            type=record_type,
            token=submission_data.get("token") or submission_data.get("coin", ""),
            amount=submission_data.get("amount", ""),
            network=submission_data.get("network", ""),
            exchange_name=submission_data.get("exchange_name", ""),
            exchange_ui_screenshot_url=submission_data.get("exchange_ui_screenshot_url", ""),
            raw_data=submission_data
        )
    
    def _build_txhash_record(self, submission_id: str, submission_data: Dict) -> Dict:
        """构建交易哈希审核用的 record 对象"""
        return {
            "submission_id": submission_id,
            "type": submission_data.get("type"),
            "tx_hash": submission_data.get("tx_hash"),
            "network": submission_data.get("network"),
            "date": submission_data.get("date") or submission_data.get("transaction_date")
        }
    
    def _audit_ui(self, record: TransactionRecord) -> Optional[Dict]:
        """执行交易所界面审核"""
        if self.deposit_ui_auditor is None or self.withdraw_ui_auditor is None:
            return None
        
        auditor = self.deposit_ui_auditor if record.type == TransactionType.DEPOSIT else self.withdraw_ui_auditor
        report = auditor.audit(record)
        return report.to_dict()
    
    def _audit_txhash(self, record: Dict, submission_data: Dict) -> Optional[Dict]:
        """执行交易哈希审核"""
        return self.txhash_auditor.verify_record(record, submission_data)
    
    def audit_submission(self, submission: Dict, submission_data: Dict) -> Dict[str, Any]:
        """
        审核单条提交记录
        
        Args:
            submission: 提交记录（包含 submission_id 和 data_submission）
            submission_data: 解析后的 data_submission JSON
            
        Returns:
            综合审核结果字典
        """
        submission_id = submission.get("submission_id")
        if not submission_id:
            return {"submission_id": None, "error": "缺少 submission_id"}
        
        result = {
            "submission_id": submission_id,
            "timestamp": datetime.now().isoformat(),
            "ui_audit": None,
            "txhash_audit": None,
            "errors": []
        }
        
        # 交易所界面审核
        try:
            record = self._build_transaction_record(submission_id, submission_data)
            ui_result = self._audit_ui(record)
            if ui_result:
                result["ui_audit"] = ui_result
                print(f"  ✓ UI审核: {ui_result.get('overall_result', 'unknown')}")
            else:
                result["errors"].append("交易所界面审核器未初始化")
        except Exception as e:
            result["errors"].append(f"UI审核失败: {str(e)}")
            print(f"  ✗ UI审核失败: {str(e)}")
        
        # 交易哈希审核
        try:
            txhash_record = self._build_txhash_record(submission_id, submission_data)
            txhash_result = self._audit_txhash(txhash_record, submission_data)
            if txhash_result:
                result["txhash_audit"] = txhash_result
                print(f"  ✓ 交易哈希审核: {txhash_result.get('result', 'unknown')}")
        except Exception as e:
            result["errors"].append(f"交易哈希审核失败: {str(e)}")
            print(f"  ✗ 交易哈希审核失败: {str(e)}")
        
        return result
    
    def _audit_submissions_list(
        self,
        submissions: List[Dict],
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        审核给定的 submissions 列表（公共逻辑，供文件/数据库两种来源复用）
        """
        if not submissions:
            return {"result": "error", "error": "没有可审核的 submissions 记录"}

        print(f"找到 {len(submissions)} 条提交记录，开始综合审核...")

        # 加载已有结果（用于增量处理）
        existing_results = {}
        if output_path:
            from utils import load_existing_results_by_id, save_single_result
            existing_results = load_existing_results_by_id(output_path, id_key="submission_id")
            if existing_results:
                print(f"发现 {len(existing_results)} 条已审核的记录")

        audit_results = []
        new_count = 0
        skipped_count = 0

        for i, sub in enumerate(submissions, 1):
            submission_id = sub.get("submission_id")

            # 检查是否已处理过
            if submission_id and submission_id in existing_results:
                skipped_count += 1
                print(f"[{i}/{len(submissions)}] 跳过已审核: {submission_id}")
                audit_results.append(existing_results[submission_id])
                continue

            result = self._process_submission(sub, i, len(submissions))
            if result:
                audit_results.append(result)
                new_count += 1

                # 立即保存单条结果
                if output_path:
                    from utils import save_single_result
                    save_single_result(
                        result,
                        output_path,
                        id_key="submission_id",
                        list_key="audit_results",
                        summary_keys=["total", "success", "with_errors"],
                    )

        if skipped_count > 0:
            print(f"\n跳过 {skipped_count} 条已审核的记录")
        if new_count > 0:
            print(f"\n本次新增审核: {new_count} 条记录")

        return self._build_final_result(audit_results, output_path)

    def audit_from_submissions_file(
        self,
        submissions_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从 submissions.json 文件读取并审核所有记录（支持增量处理）
        
        Args:
            submissions_path: submissions.json 文件路径
            output_path: 输出结果文件路径（可选）
            
        Returns:
            综合审核结果字典
        """
        submissions = self._load_submissions(submissions_path)
        if not submissions:
            return {"result": "error", "error": "无法加载 submissions.json"}

        return self._audit_submissions_list(submissions, output_path)
    
    def _load_submissions(self, submissions_path: str) -> list:
        """加载 submissions.json"""
        result = load_json(submissions_path)
        return result if result else []

    def _load_submissions_from_db(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        submission_ids: Optional[List[str]] = None,
    ) -> list:
        """从 MySQL 数据库加载 submissions"""
        client = SubmissionDBClient()
        submissions = client.fetch_submissions(
            limit=limit,
            offset=offset,
            submission_ids=submission_ids,
        )
        if not submissions:
            print("警告: 数据库中没有找到任何 submissions 记录")
        return submissions

    def audit_from_database(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        submission_ids: Optional[List[str]] = None,
        output_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        直接从数据库读取 submissions 并执行综合审核。

        Args:
            limit: 本次最多审核的记录数（None 表示不限制）
            offset: 起始偏移量，用于分页
            submission_ids: 仅审核给定的 submission_id 列表（可选），会与 DB_* 过滤条件共同生效
            output_path: 输出结果文件路径
        """
        submissions = self._load_submissions_from_db(
            limit=limit,
            offset=offset,
            submission_ids=submission_ids,
        )
        if not submissions:
            return {"result": "error", "error": "数据库中没有可审核的 submissions 记录"}

        return self._audit_submissions_list(submissions, output_path)
    
    def _process_submission(self, sub: Dict, index: int, total: int) -> Optional[Dict]:
        """处理单条提交记录"""
        submission_id = sub.get("submission_id")
        if not submission_id:
            print(f"[{index}/{total}] 跳过：缺少 submission_id")
            return None
        
        data_submission = parse_submission_data(sub)
        if not data_submission:
            print(f"[{index}/{total}] 跳过 {submission_id}：data_submission 解析失败")
            return None
        
        print(f"\n[{index}/{total}] 审核: {submission_id} ({data_submission.get('type', 'unknown')})")
        return self.audit_submission(sub, data_submission)
    
    def _build_final_result(self, audit_results: list, output_path: Optional[str]) -> Dict[str, Any]:
        """构建最终结果（汇总信息从文件重新加载，确保包含所有记录）"""
        # 如果已有输出文件，从文件重新加载汇总信息
        if output_path:
            from utils import load_json
            existing_data = load_json(output_path)
            if existing_data and "summary" in existing_data:
                summary = existing_data["summary"]
            else:
                summary = {
                    "total": len(audit_results),
                    "success": sum(1 for r in audit_results if not r.get("errors")),
                    "with_errors": sum(1 for r in audit_results if r.get("errors"))
                }
        else:
            summary = {
                "total": len(audit_results),
                "success": sum(1 for r in audit_results if not r.get("errors")),
                "with_errors": sum(1 for r in audit_results if r.get("errors"))
            }
        
        final_result = {
            "result": "success",
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "audit_results": audit_results
        }
        
        return final_result
    
    def _save_results(self, result: Dict, output_path: str):
        """保存审核结果到文件"""
        if save_json(result, output_path):
            print(f"\n结果已保存到: {output_path}")
    
    def close(self):
        """关闭所有审核器连接"""
        if hasattr(self, 'txhash_auditor'):
            self.txhash_auditor.close()


def _load_env_config(cex_hot_wallet_dir: Path):
    """加载环境变量配置"""
    try:
        from dotenv import load_dotenv
        env_file = cex_hot_wallet_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    except ImportError:
        pass


def _print_summary(summary: Dict):
    """打印审核摘要"""
    print(f"\n{'='*60}")
    print("综合审核完成")
    print(f"{'='*60}")
    print(f"总计: {summary.get('total', 0)}")
    print(f"成功: {summary.get('success', 0)}")
    print(f"有错误: {summary.get('with_errors', 0)}")


def main():
    """主函数"""
    import argparse
    
    script_dir = Path(__file__).parent.absolute()
    cex_hot_wallet_dir = script_dir.parent
    
    parser = argparse.ArgumentParser(description="综合审核工具（整合交易所界面审核和交易哈希审核）")
    parser.add_argument(
        "--submissions",
        default=str(cex_hot_wallet_dir / "raw_data" / "submissions.json"),
        help="submissions.json 文件路径（默认: raw_data/submissions.json；当 --use-db 未指定时生效）",
    )
    parser.add_argument(
        "--output",
        default=str(script_dir.parent / "output" / "main_audit" / "comprehensive_audit_results.json"),
        help="输出结果文件路径（默认: output/main_audit/comprehensive_audit_results.json）"
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
    parser.add_argument(
        "--use-db",
        action="store_true",
        help="从数据库读取 submissions（使用 db_client.py 和环境变量 DB_* 配置）",
    )
    parser.add_argument(
        "--db-limit",
        type=int,
        default=None,
        help="从数据库读取的最大记录数（可选；仅在 --use-db 时生效）",
    )
    parser.add_argument(
        "--db-offset",
        type=int,
        default=0,
        help="从数据库读取的起始偏移量（默认 0；仅在 --use-db 时生效）",
    )
    parser.add_argument(
        "--submission-ids",
        type=str,
        default="",
        help="仅审核指定的 submission_id（逗号分隔，示例: id1,id2,id3；仅在 --use-db 时生效）",
    )
    
    args = parser.parse_args()
    _load_env_config(cex_hot_wallet_dir)
    
    auditor = MainAuditor(api_key=args.api_key, base_url=args.base_url)

    # 解析 submission_ids：
    # - 优先使用命令行 --submission-ids
    # - 如果未提供，则尝试从环境变量 DB_SUBMISSION_IDS 中读取（逗号分隔）
    submission_ids: Optional[List[str]] = None
    raw_ids_arg = getattr(args, "submission_ids", "")
    if raw_ids_arg:
        raw_ids = [v.strip() for v in raw_ids_arg.split(",") if v.strip()]
        if raw_ids:
            submission_ids = raw_ids
    else:
        raw_ids_env = os.getenv("DB_SUBMISSION_IDS", "")
        if raw_ids_env:
            env_ids = [v.strip() for v in raw_ids_env.split(",") if v.strip()]
            if env_ids:
                submission_ids = env_ids

    # 是否使用数据库：
    # - 显式传了 --use-db 时优先生效
    # - 否则，如果配置了 DB_SUBMISSIONS_SQL，则自动走数据库模式
    use_db_env = bool(os.getenv("DB_SUBMISSIONS_SQL"))
    use_db = bool(args.use_db) or use_db_env

    # DB 分页参数：
    # - 优先使用命令行 --db-limit / --db-offset
    # - 如果未提供，再尝试从环境变量 DB_LIMIT / DB_OFFSET 读取
    db_limit: Optional[int] = args.db_limit
    if db_limit is None:
        env_limit = os.getenv("DB_LIMIT")
        if env_limit:
            try:
                db_limit = int(env_limit)
            except ValueError:
                print(f"警告: 无法解析 DB_LIMIT='{env_limit}'，将忽略该环境变量")

    db_offset: int = args.db_offset if args.db_offset is not None else 0
    env_offset = os.getenv("DB_OFFSET")
    if env_offset is not None:
        try:
            db_offset = int(env_offset)
        except ValueError:
            print(f"警告: 无法解析 DB_OFFSET='{env_offset}'，将忽略该环境变量")

    try:
        if use_db:
            result = auditor.audit_from_database(
                limit=db_limit,
                offset=db_offset,
                submission_ids=submission_ids,
                output_path=args.output,
            )
        else:
            result = auditor.audit_from_submissions_file(
                submissions_path=args.submissions,
                output_path=args.output,
            )
        
        if result.get("result") == "success":
            _print_summary(result.get("summary", {}))
        else:
            print(f"审核失败: {result.get('error', '未知错误')}")
    finally:
        auditor.close()


if __name__ == "__main__":
    main()
