"""
网络名称映射配置
统一管理网络名称到链标识、标准枚举值的映射
"""

# 网络名称到链标识的映射（用于 get_txhash_info）
NETWORK_TO_CHAIN = {
    'BNB': 'bsc',
    'BASE': 'base',
    'ARB': 'arb',
    'BTC': 'btc',
    'ETH': 'eth',
    'TRON': 'tron',
    'SOL': 'sol',
    'OP': 'op',
    'Polygon': 'polygon',
    'POLYGON': 'polygon',
    'ETC': 'etc',
    'BCH': 'bch',
}

# 网络名称到标准链枚举值的映射（用于 CSV 生成）
NETWORK_TO_ENUM = {
    # 主流链映射
    'BNB': 'bnb_chain_mainnet',
    'BSC': 'bnb_chain_mainnet',
    'BTC': 'bitcoin_mainnet',
    'BASE': 'base_mainnet',
    'ARB': 'arbitrum_one',
    'ARBITRUM': 'arbitrum_one',
    'ETH': 'ethereum_mainnet',
    'ETHEREUM': 'ethereum_mainnet',
    'TRON': 'tron_mainnet',
    'SOL': 'solana',
    'SOLANA': 'solana',
    'OP': 'optimism_mainnet',
    'OPTIMISM': 'optimism_mainnet',
    'POLYGON': 'polygon_mainnet',
    'MATIC': 'polygon_mainnet',
    'ETC': 'ethereum_mainnet',  # ETC使用ethereum_mainnet
    'BCH': 'bitcoin_mainnet',  # BCH使用bitcoin_mainnet
    # 其他链映射
    'LTC': 'litecoin_mainnet',
    'AVAX': 'avalanche_c_chain',
    'AVALANCHE': 'avalanche_c_chain',
    'FTM': 'fantom_mainnet',
    'FANTOM': 'fantom_mainnet',
    'DOGE': 'dogechain_mainnet',
    'XRP': 'xrp_mainnet',
    'ZEC': 'zcash_mainnet',
    'XMR': 'monero_mainnet',
    'CELO': 'celo_mainnet',
    'GNOSIS': 'gnosis_mainnet',
    'HARMONY': 'harmony_mainnet_shard_0',
    'MOONBEAM': 'moonbeam',
    'MOONRIVER': 'moonriver',
    'NEAR': 'near_mainnet',
    'AURORA': 'aurora_mainnet',
    'CRO': 'cronos',
    'FLARE': 'flare_mainnet',
    'STORY': 'story_mainnet',
    'CANTON': 'canton_mainnet',
    'PLASMA': 'plasma_mainnet',
}


def get_chain_from_network(network: str) -> str:
    """
    获取网络对应的链标识
    
    Args:
        network: 网络名称
        
    Returns:
        链标识（如 'bsc', 'eth'），找不到返回空字符串
    """
    return NETWORK_TO_CHAIN.get(network.upper(), '')


def get_enum_from_network(network: str) -> str:
    """
    获取网络对应的标准链枚举值
    
    Args:
        network: 网络名称
        
    Returns:
        标准链枚举值，找不到返回空字符串
    """
    if not network:
        return ''
    return NETWORK_TO_ENUM.get(network.strip().upper(), '')
