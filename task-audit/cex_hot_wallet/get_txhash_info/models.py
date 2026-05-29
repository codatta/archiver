"""
数据模型定义
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


def timestamp_to_date(timestamp: Optional[int]) -> Optional[str]:
    """
    将时间戳转换为日期字符串（YYYY-MM-DD格式）
    
    Args:
        timestamp: Unix时间戳
        
    Returns:
        日期字符串，格式：YYYY-MM-DD，如果timestamp为None则返回None
    """
    if timestamp is None:
        return None
    try:
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d')
    except (ValueError, OSError):
        return None


class ChainType(str, Enum):
    """支持的区块链类型"""
    BSC = "bsc"  # Binance Smart Chain
    BTC = "btc"  # Bitcoin
    BASE = "base"  # Base
    SOL = "sol"  # Solana
    ARB = "arb"  # Arbitrum
    ETH = "eth"  # Ethereum
    TRON = "tron"  # TRON
    OP = "op"  # Optimism
    POLYGON = "polygon"  # Polygon
    ETC = "etc"  # Ethereum Classic
    BCH = "bch"  # Bitcoin Cash


@dataclass
class TransactionInfo:
    """交易信息数据类"""
    chain: ChainType
    tx_hash: str
    from_address: str
    to_address: Optional[str]
    value: str  # 交易金额（wei，字符串格式）
    gas: str  # gas使用量
    gas_price: str  # gas价格
    block_number: int
    timestamp: Optional[int] = None
    status: Optional[str] = None  # success 或 failed
    date: Optional[str] = None  # 交易日期，格式：YYYY-MM-DD
    
    def to_dict(self):
        """转换为字典"""
        result = {
            'chain': self.chain.value,
            'tx_hash': self.tx_hash,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'value': self.value,
            'gas': self.gas,
            'gas_price': self.gas_price,
            'block_number': self.block_number,
        }
        if self.timestamp:
            result['timestamp'] = self.timestamp
        if self.status:
            result['status'] = self.status
        if self.date:
            result['date'] = self.date
        return result
