"""
数据加载器
负责从JSON文件加载和解析交易记录
"""
import json
import os
from typing import List
from pathlib import Path

from .models import TransactionRecord, TransactionType


class DataLoader:
    """数据加载器"""
    
    def __init__(self, raw_data_dir: str = "raw_data"):
        """
        初始化数据加载器
        
        Args:
            raw_data_dir: 原始数据目录路径
        """
        self.raw_data_dir = Path(raw_data_dir)
    
    def load_deposit_records(self) -> tuple[List[TransactionRecord], str]:
        """加载入金记录"""
        # 优先尝试从submissions.json加载，如果不存在则尝试deposit.json
        submissions_file = self.raw_data_dir / "submissions.json"
        if submissions_file.exists():
            records = self._load_records_from_submissions(submissions_file, TransactionType.DEPOSIT)
            return records, str(submissions_file)
        else:
            deposit_file = self.raw_data_dir / "deposit.json"
            records = self._load_records_from_file(deposit_file, TransactionType.DEPOSIT)
            return records, str(deposit_file)
    
    def load_withdraw_records(self) -> tuple[List[TransactionRecord], str]:
        """加载提现记录"""
        # 优先尝试从submissions.json加载，如果不存在则尝试withdraw.json
        submissions_file = self.raw_data_dir / "submissions.json"
        if submissions_file.exists():
            records = self._load_records_from_submissions(submissions_file, TransactionType.WITHDRAWAL)
            return records, str(submissions_file)
        else:
            withdraw_file = self.raw_data_dir / "withdraw.json"
            records = self._load_records_from_file(withdraw_file, TransactionType.WITHDRAWAL)
            return records, str(withdraw_file)
    
    def load_all_records(self) -> tuple[List[TransactionRecord], List[str]]:
        """加载所有记录"""
        # 优先尝试从submissions.json加载
        submissions_file = self.raw_data_dir / "submissions.json"
        if submissions_file.exists():
            records = self._load_records_from_submissions(submissions_file, None)  # None表示加载所有类型
            return records, [str(submissions_file)]
        else:
            # 兼容旧格式：分别从deposit.json和withdraw.json加载
            records = []
            files_used = []
            deposit_records, deposit_file = self.load_deposit_records()
            records.extend(deposit_records)
            if deposit_file:
                files_used.append(deposit_file)
            withdraw_records, withdraw_file = self.load_withdraw_records()
            records.extend(withdraw_records)
            if withdraw_file:
                files_used.append(withdraw_file)
            return records, files_used
    
    def _load_records_from_submissions(self, file_path: Path, filter_type: TransactionType = None) -> List[TransactionRecord]:
        """
        从submissions.json文件加载记录（支持deposit和withdrawal混合）
        
        Args:
            file_path: submissions.json文件路径
            filter_type: 如果指定，只加载该类型的记录；如果为None，加载所有类型
            
        Returns:
            交易记录列表
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            try:
                submission_id = item.get("submission_id", "")
                data_submission_str = item.get("data_submission", "{}")
                data_submission = json.loads(data_submission_str)
                
                # 从data_submission中获取type字段
                record_type_str = data_submission.get("type", "").lower()
                
                # 确定交易类型
                if record_type_str == "deposit":
                    transaction_type = TransactionType.DEPOSIT
                elif record_type_str == "withdrawal":
                    transaction_type = TransactionType.WITHDRAWAL
                else:
                    print(f"未知的交易类型: {record_type_str}, submission_id: {submission_id}")
                    continue
                
                # 如果指定了过滤类型，只加载匹配的记录
                if filter_type is not None and transaction_type != filter_type:
                    continue
                
                # 提取关键字段
                if transaction_type == TransactionType.DEPOSIT:
                    date = data_submission.get("date", "")
                    token = data_submission.get("token", "")
                    amount = data_submission.get("amount", "")
                    network = data_submission.get("network", "")
                else:  # withdrawal
                    date = data_submission.get("transaction_date", "")
                    coin = data_submission.get("coin", "")
                    # 处理类似 "BSC-USDT" 的格式
                    token = coin.split("-")[-1] if "-" in coin else coin
                    amount = data_submission.get("amount", "")
                    network = data_submission.get("network", "")
                
                exchange_name = data_submission.get("exchange_name", "")
                exchange_ui_screenshot_url = data_submission.get("exchange_ui_screenshot_url", "")
                
                # 验证必要字段（如果缺少字段，标记在raw_data中，后续审核时会判定为失败）
                required_fields = {
                    "submission_id": submission_id,
                    "date": date,
                    "token": token,
                    "amount": amount,
                    "network": network,
                    "exchange_name": exchange_name,
                    "exchange_ui_screenshot_url": exchange_ui_screenshot_url,
                }
                missing_fields = [k for k, v in required_fields.items() if not v]
                if missing_fields:
                    # 标记缺失字段，但继续创建记录（使用默认值）
                    data_submission["_missing_fields"] = missing_fields
                    print(f"警告: 记录 {submission_id} 缺少必要字段 - {', '.join(missing_fields)}，将判定为失败")
                    # 使用默认值避免创建记录时出错
                    exchange_name = exchange_name or "未知"
                    exchange_ui_screenshot_url = exchange_ui_screenshot_url or ""
                
                record = TransactionRecord(
                    submission_id=submission_id,
                    date=date or "",
                    type=transaction_type,
                    token=token or "",
                    amount=amount or "",
                    network=network or "",
                    exchange_name=exchange_name,
                    exchange_ui_screenshot_url=exchange_ui_screenshot_url,
                    raw_data=data_submission,
                )
                records.append(record)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"解析记录失败: {item.get('submission_id', 'unknown')}, 错误: {e}")
                continue
        
        return records
    
    def _load_records_from_file(self, file_path: Path, transaction_type: TransactionType) -> List[TransactionRecord]:
        """
        从文件加载记录
        
        Args:
            file_path: JSON文件路径
            transaction_type: 交易类型
            
        Returns:
            交易记录列表
        """
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        records = []
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            try:
                submission_id = item.get("submission_id", "")
                data_submission_str = item.get("data_submission", "{}")
                data_submission = json.loads(data_submission_str)
                
                # 提取关键字段
                if transaction_type == TransactionType.DEPOSIT:
                    date = data_submission.get("date", "")
                    token = data_submission.get("token", "")
                    amount = data_submission.get("amount", "")
                    network = data_submission.get("network", "")
                else:  # withdrawal
                    date = data_submission.get("transaction_date", "")
                    coin = data_submission.get("coin", "")
                    # 处理类似 "BSC-USDT" 的格式
                    token = coin.split("-")[-1] if "-" in coin else coin
                    amount = data_submission.get("amount", "")
                    network = data_submission.get("network", "")
                
                exchange_name = data_submission.get("exchange_name", "")
                exchange_ui_screenshot_url = data_submission.get("exchange_ui_screenshot_url", "")
                
                # 验证必要字段（如果缺少字段，标记在raw_data中，后续审核时会判定为失败）
                required_fields = {
                    "submission_id": submission_id,
                    "date": date,
                    "token": token,
                    "amount": amount,
                    "network": network,
                    "exchange_name": exchange_name,
                    "exchange_ui_screenshot_url": exchange_ui_screenshot_url,
                }
                missing_fields = [k for k, v in required_fields.items() if not v]
                if missing_fields:
                    # 标记缺失字段，但继续创建记录（使用默认值）
                    data_submission["_missing_fields"] = missing_fields
                    print(f"警告: 记录 {submission_id} 缺少必要字段 - {', '.join(missing_fields)}，将判定为失败")
                    # 使用默认值避免创建记录时出错
                    exchange_name = exchange_name or "未知"
                    exchange_ui_screenshot_url = exchange_ui_screenshot_url or ""
                
                record = TransactionRecord(
                    submission_id=submission_id,
                    date=date or "",
                    type=transaction_type,
                    token=token or "",
                    amount=amount or "",
                    network=network or "",
                    exchange_name=exchange_name,
                    exchange_ui_screenshot_url=exchange_ui_screenshot_url,
                    raw_data=data_submission,
                )
                records.append(record)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"解析记录失败: {item.get('submission_id', 'unknown')}, 错误: {e}")
                continue
        
        return records
