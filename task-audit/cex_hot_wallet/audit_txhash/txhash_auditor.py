"""
交易哈希审核模块
用于验证提交数据中的交易哈希信息
直接对 submissions.json 中的所有数据进行审核
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from get_txhash_info.tx_fetcher import TransactionFetcher
from get_txhash_info.models import timestamp_to_date
from utils import (
    load_json, save_json, normalize_address, compare_addresses,
    check_address_in_list, parse_submission_data
)
from network_mapping import get_chain_from_network


class TxHashAuditor:
    """交易哈希审核器"""
    
    def __init__(self):
        """初始化审核器"""
        self.fetchers = {}  # 缓存fetcher实例
    
    def _get_fetcher(self, network: str) -> Optional[TransactionFetcher]:
        """获取交易获取器"""
        chain = get_chain_from_network(network)
        if not chain:
            print(f"[警告] 不支持的网络: {network}")
            return None
        
        if chain not in self.fetchers:
            try:
                self.fetchers[chain] = TransactionFetcher(chain)
            except Exception as e:
                print(f"[错误] 创建 {chain} 链的fetcher失败: {str(e)}")
                return None
        
        return self.fetchers[chain]
    
    # 使用公共工具函数，移除重复的地址处理方法
    _normalize_address = staticmethod(normalize_address)
    _compare_addresses = staticmethod(compare_addresses)
    _check_address_in_list = staticmethod(check_address_in_list)
    
    def _get_btc_addresses_from_fetcher(self, fetcher: TransactionFetcher) -> tuple:
        """从fetcher获取BTC的地址列表"""
        if hasattr(fetcher, '_btc_from_addresses') and hasattr(fetcher, '_btc_to_addresses'):
            return (
                getattr(fetcher, '_btc_from_addresses', []),
                getattr(fetcher, '_btc_to_addresses', [])
            )
        return ([], [])
    
    def _add_address_check(
        self,
        result: Dict,
        check_name: str,
        expected: str,
        actual: str | List[str],
        is_btc: bool = False,
        address_list: List[str] = None
    ):
        """添加地址验证检查项"""
        if is_btc and address_list:
            matched = self._check_address_in_list(expected, address_list)
            actual_display = address_list
        else:
            matched = self._compare_addresses(expected, actual) if actual else False
            actual_display = actual
        
        check = {
            "check_name": check_name,
            "expected": expected,
            "actual": actual_display,
            "result": "pass" if matched else "fail"
        }
        
        if check["result"] == "fail":
            if is_btc and not address_list:
                result["errors"].append(f"{check_name}: 地址列表为空")
            elif isinstance(actual_display, list):
                result["errors"].append(f"{check_name}: 期望 {expected}, 实际地址列表: {actual_display}")
            elif not actual_display:
                result["errors"].append(f"{check_name}: 期望 {expected}, 实际为None（可能是合约创建）")
            else:
                result["errors"].append(f"{check_name}: 期望 {expected}, 实际 {actual_display}")
        
        result["checks"].append(check)
    
    def _add_date_check(
        self,
        result: Dict,
        check_name: str,
        expected: str,
        actual: Optional[str]
    ):
        """添加日期验证检查项"""
        if actual:
            matched = self._compare_dates(expected, actual, tolerance_days=1)
            check = {
                "check_name": check_name,
                "expected": expected,
                "actual": actual,
                "result": "pass" if matched else "fail"
            }
            if not matched:
                result["errors"].append(f"{check_name}: 期望 {expected}, 实际 {actual}")
        else:
            check = {
                "check_name": check_name,
                "expected": expected,
                "actual": None,
                "result": "fail"
            }
            result["errors"].append(f"无法获取{check_name}日期")
        
        result["checks"].append(check)
    
    def _compare_dates(self, date1: str, date2: str, tolerance_days: int = 1) -> bool:
        """
        比较两个日期是否在允许误差范围内
        
        Args:
            date1: 日期1 (YYYY-MM-DD格式)
            date2: 日期2 (YYYY-MM-DD格式)
            tolerance_days: 允许的误差天数（默认1天）
            
        Returns:
            是否在误差范围内
        """
        try:
            d1 = datetime.strptime(date1, "%Y-%m-%d")
            d2 = datetime.strptime(date2, "%Y-%m-%d")
            diff = abs((d1 - d2).days)
            return diff <= tolerance_days
        except Exception as e:
            print(f"[错误] 日期比较失败: {date1} vs {date2}, 错误: {str(e)}")
            return False
    
    def _get_transaction_info_with_retry(
        self,
        fetcher: TransactionFetcher,
        tx_hash: str,
        network: str = None,
        max_retries: int = 3,
        retry_delay: float = None
    ):
        """
        获取交易信息，带重试机制
        
        Args:
            fetcher: TransactionFetcher 实例
            tx_hash: 交易哈希
            network: 网络名称（用于确定重试延迟，可选）
            max_retries: 最大重试次数（默认3次）
            retry_delay: 重试延迟（秒，如果为None则根据网络自动设置）
            
        Returns:
            TransactionInfo 对象或 None
        """
        import time
        
        # 根据网络类型设置重试延迟
        if retry_delay is None:
            if network and network.upper() == 'BTC':
                # BTC链容易失败，使用更长的重试间隔（3秒）
                retry_delay = 3.0
            else:
                # 其他链使用默认1秒
                retry_delay = 1.0
        
        last_error = None
        for attempt in range(max_retries):
            try:
                tx_info = fetcher.get_transaction_info(tx_hash)
                if tx_info:
                    return tx_info
                # 如果返回None，可能是交易不存在，不重试
                return None
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"[重试] 获取交易信息失败 (尝试 {attempt + 1}/{max_retries}): {tx_hash[:20]}..., 等待 {retry_delay} 秒后重试... 错误: {str(e)[:100]}")
                    time.sleep(retry_delay)
                else:
                    print(f"[失败] 获取交易信息失败 (已重试 {max_retries} 次): {tx_hash}, 错误: {str(e)}")
        
        return None
    
    def _validate_required_fields(self, result: Dict, fields: Dict[str, str]) -> bool:
        """验证必要字段，缺失则添加到错误列表并返回False"""
        missing = []
        for field_name, field_value in fields.items():
            if not field_value:
                missing.append(field_name)
        
        if missing:
            result["errors"].extend([f"缺少{name}" for name in missing])
            return False
        return True
    
    def _verify_withdrawal(self, record: Dict, submission_data: Dict) -> Dict[str, Any]:
        """验证提现交易"""
        result = {
            "submission_id": record.get("submission_id"),
            "type": "withdrawal",
            "result": "fail",
            "checks": [],
            "errors": []
        }
        
        # 获取并验证必要字段
        fields = {
            "交易哈希": record.get("tx_hash"),
            "网络信息": record.get("network"),
            "发送地址": submission_data.get("sender_address"),
            "接收地址": submission_data.get("receiver_address"),
            "address字段": submission_data.get("address"),
            "交易日期": submission_data.get("transaction_date")
        }
        
        tx_hash = fields["交易哈希"]
        network = fields["网络信息"]
        sender_address = fields["发送地址"]
        receiver_address = fields["接收地址"]
        address = fields["address字段"]
        transaction_date = fields["交易日期"]
        
        if not self._validate_required_fields(result, fields):
            return result
        
        # 验证 receiver_address 和 address 必须一致
        address_consistency = self._compare_addresses(receiver_address, address)
        consistency_check = {
            "check_name": "receiver_address_equals_address",
            "expected": f"receiver_address ({receiver_address}) == address ({address})",
            "actual": f"receiver_address: {receiver_address}, address: {address}",
            "result": "pass" if address_consistency else "fail"
        }
        if consistency_check["result"] == "fail":
            result["errors"].append(f"receiver_address ({receiver_address}) 与 address ({address}) 不一致")
        result["checks"].append(consistency_check)
        
        # 获取交易信息
        fetcher = self._get_fetcher(network)
        if not fetcher:
            result["errors"].append(f"无法创建 {network} 链的fetcher")
            return result
        
        tx_info = self._get_transaction_info_with_retry(fetcher, tx_hash, network=network, max_retries=3)
        if not tx_info:
            result["errors"].append(f"无法获取交易信息（已重试3次）: {tx_hash}")
            return result
        
        # 验证地址和日期
        is_btc = network.upper() == 'BTC'
        if is_btc:
            btc_from_addresses, btc_to_addresses = self._get_btc_addresses_from_fetcher(fetcher)
            self._add_address_check(result, "from_address_match", sender_address, tx_info.from_address, 
                                   is_btc=True, address_list=btc_from_addresses)
            self._add_address_check(result, "to_address_match", receiver_address, tx_info.to_address,
                                   is_btc=True, address_list=btc_to_addresses)
        else:
            self._add_address_check(result, "from_address_match", sender_address, tx_info.from_address)
            self._add_address_check(result, "to_address_match", receiver_address, tx_info.to_address)
        
        self._add_date_check(result, "transaction_date_match", transaction_date, tx_info.date)
        
        # 判断最终结果
        if all(check["result"] == "pass" for check in result["checks"]):
            result["result"] = "pass"
        
        return result
    
    def _verify_deposit(self, record: Dict, submission_data: Dict) -> Dict[str, Any]:
        """
        验证入金交易
        
        Args:
            record: 审核报告中的记录
            submission_data: 原始提交数据
            
        Returns:
            验证结果字典
        """
        result = {
            "submission_id": record.get("submission_id"),
            "type": "deposit",
            "result": "fail",
            "checks": [],
            "errors": []
        }
        
        # 获取并验证必要字段
        tx_hash = record.get("tx_hash")
        network = record.get("network")
        record_date = record.get("date")
        from_address = submission_data.get("from_address")
        to_address = submission_data.get("to_address")
        submission_date = submission_data.get("date")
        expected_date = record_date or submission_date
        
        fields = {
            "交易哈希": tx_hash,
            "网络信息": network,
            "from_address": from_address,
            "to_address": to_address,
            "交易日期": expected_date
        }
        
        if not self._validate_required_fields(result, fields):
            return result
        
        # 验证 has_outgoing_transaction 字段
        # 业务要求：**只有在 has_outgoing_transaction 为 True 时，该检查项才能通过**
        has_outgoing_raw = submission_data.get("has_outgoing_transaction")
        has_outgoing_exists = "has_outgoing_transaction" in submission_data
        has_outgoing_is_bool = isinstance(has_outgoing_raw, bool)
        
        has_outgoing_check = {
            "check_name": "has_outgoing_transaction_field",
            "expected": "has_outgoing_transaction 字段存在且为 True（布尔值）",
            "actual": f"字段存在: {has_outgoing_exists}, 值: {has_outgoing_raw}, 类型: {type(has_outgoing_raw).__name__ if has_outgoing_raw is not None else 'None'}",
            "result": "pass" if (has_outgoing_exists and has_outgoing_is_bool and has_outgoing_raw is True) else "fail"
        }
        if has_outgoing_check["result"] == "fail":
            if not has_outgoing_exists:
                result["errors"].append("has_outgoing_transaction 字段缺失")
            elif not has_outgoing_is_bool:
                result["errors"].append(f"has_outgoing_transaction 字段类型错误: 期望 bool，实际 {type(has_outgoing_raw).__name__}")
            elif has_outgoing_raw is False:
                # 字段存在且类型正确，但业务要求必须为 True
                result["errors"].append("has_outgoing_transaction 字段值为 False，不符合要求（需要 True）")
        result["checks"].append(has_outgoing_check)
        
        # 只有当字段存在且为布尔 True 时，才认为 has_outgoing 为 True；否则一律为 False
        has_outgoing = has_outgoing_raw is True if has_outgoing_exists and has_outgoing_is_bool else False
        
        # 获取 outgoing 交易相关字段（仅在 has_outgoing 为 True 时使用）
        outgoing_tx_hash = submission_data.get("outgoing_transaction_hash")
        outgoing_tx_from_address = submission_data.get("outgoing_tx_from_address")
        outgoing_tx_to_address = submission_data.get("outgoing_tx_to_address")
        
        # 获取主交易信息
        fetcher = self._get_fetcher(network)
        if not fetcher:
            result["errors"].append(f"无法创建 {network} 链的fetcher")
            return result
        
        tx_info = self._get_transaction_info_with_retry(fetcher, tx_hash, network=network, max_retries=3)
        if not tx_info:
            result["errors"].append(f"无法获取主交易信息（已重试3次）: {tx_hash}")
            return result
        
        # 验证主交易的地址和日期
        is_btc = network.upper() == 'BTC'
        if is_btc:
            btc_from_addresses, btc_to_addresses = self._get_btc_addresses_from_fetcher(fetcher)
            self._add_address_check(result, "main_tx_from_address_match", from_address, tx_info.from_address,
                                   is_btc=True, address_list=btc_from_addresses)
            self._add_address_check(result, "main_tx_to_address_match", to_address, tx_info.to_address,
                                   is_btc=True, address_list=btc_to_addresses)
        else:
            self._add_address_check(result, "main_tx_from_address_match", from_address, tx_info.from_address)
            self._add_address_check(result, "main_tx_to_address_match", to_address, tx_info.to_address)
        
        self._add_date_check(result, "main_tx_date_match", expected_date, tx_info.date)
        
        # 如果有outgoing交易，验证outgoing交易
        if has_outgoing:
            if not outgoing_tx_hash:
                result["errors"].append("has_outgoing_transaction为true但缺少outgoing_transaction_hash")
                outgoing_check = {
                    "check_name": "outgoing_tx_validation",
                    "result": "fail",
                    "error": "缺少outgoing_transaction_hash"
                }
                result["checks"].append(outgoing_check)
            elif not outgoing_tx_from_address or not outgoing_tx_to_address:
                result["errors"].append("has_outgoing_transaction为true但缺少outgoing_tx_from_address或outgoing_tx_to_address")
                outgoing_check = {
                    "check_name": "outgoing_tx_validation",
                    "result": "fail",
                    "error": "缺少outgoing交易地址信息"
                }
                result["checks"].append(outgoing_check)
            else:
                # 验证 to_address 和 outgoing_tx_from_address 必须一致
                # 对于BTC链，需要特殊处理
                if is_btc:
                    # BTC链：检查 to_address 和 outgoing_tx_from_address 是否是同一个地址
                    # 或者它们都在 btc_to_addresses 列表中（表示是同一个交易所地址的不同表示）
                    address_consistency = self._compare_addresses(to_address, outgoing_tx_from_address)
                    
                    # 如果直接比较不匹配，检查是否都在地址列表中（对于BTC，可能有多个to地址）
                    if not address_consistency and btc_to_addresses:
                        # 检查 to_address 和 outgoing_tx_from_address 是否都在 to_addresses 列表中
                        to_in_list = self._check_address_in_list(to_address, btc_to_addresses)
                        outgoing_from_in_list = self._check_address_in_list(outgoing_tx_from_address, btc_to_addresses)
                        # 如果都在列表中，且是同一个地址，则通过
                        address_consistency = to_in_list and outgoing_from_in_list and self._compare_addresses(to_address, outgoing_tx_from_address)
                else:
                    # 非BTC链：直接比较
                    address_consistency = self._compare_addresses(to_address, outgoing_tx_from_address)
                
                consistency_check = {
                    "check_name": "to_address_equals_outgoing_from_address",
                    "expected": f"to_address ({to_address}) == outgoing_tx_from_address ({outgoing_tx_from_address})",
                    "actual": f"to_address: {to_address}, outgoing_tx_from_address: {outgoing_tx_from_address}",
                    "result": "pass" if address_consistency else "fail"
                }
                if consistency_check["result"] == "fail":
                    result["errors"].append(f"to_address ({to_address}) 与 outgoing_tx_from_address ({outgoing_tx_from_address}) 不一致")
                result["checks"].append(consistency_check)
                
                # 获取outgoing交易信息（使用相同的网络，带重试）
                outgoing_tx_info = self._get_transaction_info_with_retry(fetcher, outgoing_tx_hash, max_retries=3)
                if not outgoing_tx_info:
                    result["errors"].append(f"无法获取outgoing交易信息（已重试3次）: {outgoing_tx_hash}")
                    outgoing_check = {
                        "check_name": "outgoing_tx_validation",
                        "result": "fail",
                        "error": f"无法获取outgoing交易信息（已重试3次）: {outgoing_tx_hash}"
                    }
                    result["checks"].append(outgoing_check)
                else:
                    # 验证outgoing交易的地址
                    if is_btc:
                        outgoing_btc_from_addresses, outgoing_btc_to_addresses = self._get_btc_addresses_from_fetcher(fetcher)
                        self._add_address_check(result, "outgoing_tx_from_address_match", outgoing_tx_from_address,
                                               outgoing_tx_info.from_address, is_btc=True, address_list=outgoing_btc_from_addresses)
                        self._add_address_check(result, "outgoing_tx_to_address_match", outgoing_tx_to_address,
                                               outgoing_tx_info.to_address, is_btc=True, address_list=outgoing_btc_to_addresses)
                    else:
                        self._add_address_check(result, "outgoing_tx_from_address_match", outgoing_tx_from_address,
                                               outgoing_tx_info.from_address)
                        self._add_address_check(result, "outgoing_tx_to_address_match", outgoing_tx_to_address,
                                               outgoing_tx_info.to_address)
        
        # 判断最终结果
        if all(check["result"] == "pass" for check in result["checks"]):
            result["result"] = "pass"
        
        return result
    
    def verify_record(self, record: Dict, submission_data: Dict) -> Dict[str, Any]:
        """
        验证单条记录
        
        Args:
            record: 审核报告中的记录
            submission_data: 原始提交数据
            
        Returns:
            验证结果字典
        """
        record_type = record.get("type", "").lower()
        
        if record_type == "withdrawal":
            return self._verify_withdrawal(record, submission_data)
        elif record_type == "deposit":
            return self._verify_deposit(record, submission_data)
        else:
            return {
                "submission_id": record.get("submission_id"),
                "type": record_type,
                "result": "fail",
                "errors": [f"未知的交易类型: {record_type}"]
            }
    
    def audit_from_files(
        self,
        submissions_path: str,
        output_path: Optional[str] = None,
        audit_report_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从文件读取并审核
        
        Args:
            submissions_path: 原始提交数据文件路径
            output_path: 输出结果文件路径（可选）
            audit_report_path: 审核报告文件路径（已废弃，保留以兼容旧代码）
            
        Returns:
            审核结果字典
        """
        # 读取原始提交数据
        submissions = load_json(submissions_path)
        if not submissions:
            return {
                "result": "error",
                "error": f"读取原始提交数据失败: {submissions_path}"
            }
        
        print(f"找到 {len(submissions)} 条提交记录，开始审核...")
        
        # 加载已有结果（用于增量处理）
        from utils import load_existing_results_by_id, save_single_result
        existing_results = {}
        if output_path:
            existing_results = load_existing_results_by_id(output_path, id_key="submission_id")
            if existing_results:
                print(f"发现 {len(existing_results)} 条已审核的记录")
        
        # 进行交易哈希审核
        verification_results = []
        new_count = 0
        skipped_count = 0
        
        for sub in submissions:
            submission_id = sub.get("submission_id")
            if not submission_id:
                print(f"[警告] 记录缺少submission_id，跳过")
                continue
            
            # 解析 data_submission
            data_submission = parse_submission_data(sub)
            if not data_submission:
                print(f"[警告] submission_id {submission_id} 的 data_submission 解析失败，跳过")
                continue
            
            # 从 data_submission 构建 record 对象
            record = {
                "submission_id": submission_id,
                "type": data_submission.get("type"),
                "tx_hash": data_submission.get("tx_hash"),
                "network": data_submission.get("network"),
                "date": data_submission.get("date") or data_submission.get("transaction_date")
            }
            
            # 检查必要字段
            if not record.get("type"):
                print(f"[警告] submission_id {submission_id} 缺少 type 字段，跳过")
                continue
            
            if not record.get("tx_hash"):
                print(f"[警告] submission_id {submission_id} 缺少 tx_hash 字段，跳过")
                continue
            
            if not record.get("network"):
                print(f"[警告] submission_id {submission_id} 缺少 network 字段，跳过")
                continue
            
            # 检查是否已处理过
            if submission_id in existing_results:
                skipped_count += 1
                print(f"跳过已审核记录: {submission_id}")
                verification_results.append(existing_results[submission_id])
                continue
            
            print(f"审核记录: {submission_id} ({record.get('type')})")
            verification_result = self.verify_record(record, data_submission)
            verification_results.append(verification_result)
            new_count += 1
            
            # 立即保存单条结果
            if output_path:
                save_single_result(
                    verification_result, 
                    output_path,
                    id_key="submission_id",
                    list_key="verifications",
                    summary_keys=["total", "pass", "fail", "pending"]
                )
            
            # 打印结果
            if verification_result["result"] == "pass":
                print(f"  ✓ 通过")
            elif verification_result["result"] == "pending":
                print(f"  ⏳ 待实现")
            else:
                print(f"  ✗ 失败: {', '.join(verification_result.get('errors', []))}")
        
        if skipped_count > 0:
            print(f"\n跳过 {skipped_count} 条已审核的记录")
        if new_count > 0:
            print(f"\n本次新增审核: {new_count} 条记录")
        
        # 汇总结果（从已有结果文件重新加载，确保包含所有记录）
        if output_path:
            final_data = load_json(output_path)
            if final_data and "summary" in final_data:
                summary = final_data["summary"]
            else:
                summary = {
                    "total": len(verification_results),
                    "pass": sum(1 for r in verification_results if r["result"] == "pass"),
                    "fail": sum(1 for r in verification_results if r["result"] == "fail"),
                    "pending": sum(1 for r in verification_results if r["result"] == "pending")
                }
        else:
            summary = {
                "total": len(verification_results),
                "pass": sum(1 for r in verification_results if r["result"] == "pass"),
                "fail": sum(1 for r in verification_results if r["result"] == "fail"),
                "pending": sum(1 for r in verification_results if r["result"] == "pending")
            }
        
        result = {
            "result": "success",
            "summary": summary,
            "verifications": verification_results
        }
        
        return result
    
    def close(self):
        """关闭所有fetcher连接"""
        for fetcher in self.fetchers.values():
            if hasattr(fetcher, 'web3') and fetcher.web3:
                # 清理web3连接
                pass
        self.fetchers.clear()


def main():
    """主函数"""
    import argparse
    import os
    
    # 获取脚本所在目录的父目录（cex_hot_wallet目录）
    script_dir = Path(__file__).parent.absolute()
    base_dir = script_dir.parent  # cex_hot_wallet目录
    
    # 设置默认路径
    default_submissions = base_dir / "raw_data" / "submissions.json"
    default_output = base_dir / "output" / "audit_txhash" / "txhash_verification_results.json"
    
    parser = argparse.ArgumentParser(description="交易哈希审核工具")
    parser.add_argument(
        "--submissions",
        default=str(default_submissions),
        help="原始提交数据文件路径（默认: raw_data/submissions.json）"
    )
    parser.add_argument(
        "--output",
        default=str(default_output),
        help="输出结果文件路径（默认: output/audit_txhash/txhash_verification_results.json）"
    )
    
    args = parser.parse_args()
    
    auditor = TxHashAuditor()
    try:
        result = auditor.audit_from_files(
            submissions_path=args.submissions,
            output_path=args.output
        )
        
        if result.get("result") == "success":
            summary = result.get("summary", {})
            print(f"\n审核完成:")
            print(f"  总计: {summary.get('total', 0)}")
            print(f"  通过: {summary.get('pass', 0)}")
            print(f"  失败: {summary.get('fail', 0)}")
            print(f"  待实现: {summary.get('pending', 0)}")
        else:
            print(f"审核失败: {result.get('error', '未知错误')}")
    finally:
        auditor.close()


if __name__ == "__main__":
    main()
