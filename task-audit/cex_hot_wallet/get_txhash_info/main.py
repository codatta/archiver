"""
交易哈希审核主程序
"""
import argparse
from typing import List, Optional
from .tx_fetcher import TransactionFetcher
from .models import ChainType


class TxHashAudit:
    """交易哈希审核主类"""
    
    def __init__(self):
        """初始化"""
        self.fetchers = {}
    
    def get_fetcher(self, chain: str) -> TransactionFetcher:
        """
        获取或创建指定链的fetcher
        
        Args:
            chain: 链名称 ('bsc' 或 'eth')
            
        Returns:
            TransactionFetcher 实例
        """
        chain = chain.lower()
        if chain not in self.fetchers:
            self.fetchers[chain] = TransactionFetcher(chain)
        return self.fetchers[chain]
    
    def get_tx_addresses(self, tx_hash: str, chain: str = 'eth') -> Optional[dict]:
        """
        获取单笔交易的from和to地址
        
        Args:
            tx_hash: 交易哈希
            chain: 链名称 ('bsc' 或 'eth')
            
        Returns:
            交易地址信息字典 {'from': '0x...', 'to': '0x...', 'chain': '...', 'tx_hash': '...'}
        """
        fetcher = self.get_fetcher(chain)
        return fetcher.get_from_to_addresses(tx_hash)
    
    def get_tx_full_info(self, tx_hash: str, chain: str = 'eth') -> Optional[dict]:
        """
        获取完整交易信息
        
        Args:
            tx_hash: 交易哈希
            chain: 链名称
            
        Returns:
            完整交易信息字典
        """
        fetcher = self.get_fetcher(chain)
        tx_info = fetcher.get_transaction_info(tx_hash)
        return tx_info.to_dict() if tx_info else None
    
    def batch_get_tx_addresses(self, tx_hashes: List[str], chain: str = 'eth') -> List[dict]:
        """
        批量获取交易地址
        
        Args:
            tx_hashes: 交易哈希列表
            chain: 链名称
            
        Returns:
            交易地址信息列表
        """
        results = []
        fetcher = self.get_fetcher(chain)
        
        for i, tx_hash in enumerate(tx_hashes, 1):
            print(f"[{i}/{len(tx_hashes)}] 正在获取: {tx_hash}...")
            result = fetcher.get_from_to_addresses(tx_hash)
            if result:
                results.append(result)
                # 处理多个地址的情况（BTC链）
                from_addr = result['from']
                if isinstance(from_addr, list):
                    print(f"  ✓ From ({len(from_addr)} 个地址):")
                    for i, addr in enumerate(from_addr, 1):
                        print(f"      {i}. {addr}")
                else:
                    print(f"  ✓ From: {from_addr}")
                
                to_addr = result['to']
                if isinstance(to_addr, list):
                    print(f"    To ({len(to_addr)} 个地址):")
                    for i, addr in enumerate(to_addr, 1):
                        print(f"      {i}. {addr}")
                else:
                    print(f"    To: {to_addr}")
                
                if result.get('date'):
                    print(f"    日期: {result['date']}")
            else:
                print(f"  ✗ 获取失败")
        
        return results
    
    def close(self):
        """关闭所有连接"""
        self.fetchers.clear()


def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(description="根据交易hash获取from和to地址")
    parser.add_argument(
        "tx_hash",
        type=str,
        help="交易哈希"
    )
    parser.add_argument(
        "--chain",
        type=str,
        choices=["bsc", "btc", "base", "sol", "arb", "eth", "tron", "op", "polygon", "etc", "bch"],
        default="eth",
        help="区块链类型 (默认: eth)"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="显示完整交易信息"
    )
    parser.add_argument(
        "--batch",
        type=str,
        help="批量处理：指定包含交易哈希的文件（每行一个）"
    )
    
    args = parser.parse_args()
    
    audit = TxHashAudit()
    
    try:
        if args.batch:
            # 批量处理模式
            print(f"批量处理模式，链: {args.chain}")
            with open(args.batch, 'r', encoding='utf-8') as f:
                tx_hashes = [line.strip() for line in f if line.strip()]
            
            print(f"共 {len(tx_hashes)} 笔交易\n")
            results = audit.batch_get_tx_addresses(tx_hashes, args.chain)
            print(f"\n成功获取 {len(results)}/{len(tx_hashes)} 笔交易信息")
        else:
            # 单笔交易模式
            print(f"链: {args.chain.upper()}")
            print(f"交易哈希: {args.tx_hash}\n")
            
            if args.full:
                # 显示完整信息
                info = audit.get_tx_full_info(args.tx_hash, args.chain)
                if info:
                    print("完整交易信息:")
                    for key, value in info.items():
                        print(f"  {key}: {value}")
                else:
                    print("✗ 获取交易信息失败")
            else:
                # 仅显示from和to
                result = audit.get_tx_addresses(args.tx_hash, args.chain)
                if result:
                    print("交易地址信息:")
                    # 处理多个地址的情况（BTC链）
                    from_addr = result['from']
                    if isinstance(from_addr, list):
                        print(f"  From ({len(from_addr)} 个地址):")
                        for i, addr in enumerate(from_addr, 1):
                            print(f"    {i}. {addr}")
                    else:
                        print(f"  From: {from_addr}")
                    
                    to_addr = result['to']
                    if isinstance(to_addr, list):
                        print(f"  To ({len(to_addr)} 个地址):")
                        for i, addr in enumerate(to_addr, 1):
                            print(f"    {i}. {addr}")
                    else:
                        print(f"  To: {to_addr}")
                    
                    if result.get('date'):
                        print(f"  日期: {result['date']}")
                else:
                    print("✗ 获取交易信息失败")
    
    finally:
        audit.close()


if __name__ == "__main__":
    main()
