"""
区块链配置
"""
from typing import Dict, Optional


class ChainConfig:
    """区块链配置"""
    
    CHAIN_CONFIGS = {
        'bsc': {
            'name': 'Binance Smart Chain',
            'rpc_url': 'https://bsc-dataseed1.binance.org',
            'explorer': 'https://bscscan.com',
            'chain_id': 56,
            'is_evm': True,
            'is_poa': True  # BSC是POA链
        },
        'btc': {
            'name': 'Bitcoin',
            'rpc_url': None,  # BTC需要特殊处理，不使用标准RPC
            'explorer': 'https://blockstream.info',
            'chain_id': None,
            'is_evm': False,
            'is_poa': False
        },
        'base': {
            'name': 'Base',
            'rpc_url': 'https://mainnet.base.org',
            'explorer': 'https://basescan.org',
            'chain_id': 8453,
            'is_evm': True,
            'is_poa': False
        },
        'sol': {
            'name': 'Solana',
            'rpc_url': 'https://api.mainnet-beta.solana.com',
            'explorer': 'https://solscan.io',
            'chain_id': None,
            'is_evm': False,
            'is_poa': False
        },
        'arb': {
            'name': 'Arbitrum',
            'rpc_url': 'https://arb1.arbitrum.io/rpc',
            'explorer': 'https://arbiscan.io',
            'chain_id': 42161,
            'is_evm': True,
            'is_poa': False
        },
        # 保留ETH作为兼容
        'eth': {
            'name': 'Ethereum',
            'rpc_url': 'https://eth.llamarpc.com',
            'explorer': 'https://etherscan.io',
            'chain_id': 1,
            'is_evm': True,
            'is_poa': False
        },
        'tron': {
            'name': 'TRON',
            'rpc_url': 'https://api.trongrid.io',
            'explorer': 'https://tronscan.org',
            'chain_id': None,
            'is_evm': False,
            'is_poa': False
        },
        'op': {
            'name': 'Optimism',
            'rpc_url': 'https://rpc.ankr.com/optimism',
            'rpc_urls': [  # 备用RPC URL列表
                'https://rpc.ankr.com/optimism',
                'https://optimism-mainnet.public.blastapi.io',
                'https://mainnet.optimism.io',
                'https://optimism.llamarpc.com'
            ],
            'explorer': 'https://optimistic.etherscan.io',
            'chain_id': 10,
            'is_evm': True,
            'is_poa': False
        },
        'polygon': {
            'name': 'Polygon',
            'rpc_url': 'https://polygon-rpc.com',
            'rpc_urls': [  # 备用RPC URL列表
                'https://polygon-rpc.com',
                'https://rpc.ankr.com/polygon',
                'https://polygon-mainnet.public.blastapi.io',
                'https://polygon.llamarpc.com'
            ],
            'explorer': 'https://polygonscan.com',
            'chain_id': 137,
            'is_evm': True,
            'is_poa': True  # Polygon是POA链
        },
        'etc': {
            'name': 'Ethereum Classic',
            'rpc_url': 'https://etc.etcdesktop.com',
            'rpc_urls': [  # 备用RPC URL列表
                'https://etc.etcdesktop.com',
                'https://rpc.ankr.com/etc',
                'https://ethereumclassic.network',
                'https://www.ethercluster.com/etc',
                'https://etc.rpc.thirdweb.com'
            ],
            'explorer': 'https://blockscout.com/etc/mainnet',
            'chain_id': 61,
            'is_evm': True,
            'is_poa': False
        },
        'bch': {
            'name': 'Bitcoin Cash',
            'rpc_url': None,  # BCH需要特殊处理，类似BTC
            'explorer': 'https://blockchair.com/bitcoin-cash',
            'chain_id': None,
            'is_evm': False,
            'is_poa': False
        }
    }
    
    @classmethod
    def get_config(cls, chain: str) -> Dict:
        """
        获取链配置
        
        Args:
            chain: 链名称 ('bsc', 'btc', 'base', 'sol', 'arb', 'eth', 'tron', 'op', 'polygon', 'etc', 'bch')
            
        Returns:
            链配置字典
        """
        chain = chain.lower()
        if chain not in cls.CHAIN_CONFIGS:
            raise ValueError(f"不支持的链: {chain}. 支持的链: {list(cls.CHAIN_CONFIGS.keys())}")
        return cls.CHAIN_CONFIGS[chain]
    
    @classmethod
    def is_evm_chain(cls, chain: str) -> bool:
        """
        判断是否为EVM兼容链
        
        Args:
            chain: 链名称
            
        Returns:
            是否为EVM兼容链
        """
        config = cls.get_config(chain)
        return config.get('is_evm', False)
    
    @classmethod
    def is_poa_chain(cls, chain: str) -> bool:
        """
        判断是否为POA链
        
        Args:
            chain: 链名称
            
        Returns:
            是否为POA链
        """
        config = cls.get_config(chain)
        return config.get('is_poa', False)
    
    @classmethod
    def get_rpc_url(cls, chain: str) -> Optional[str]:
        """
        获取RPC URL
        
        Args:
            chain: 链名称
            
        Returns:
            RPC URL，如果链不支持RPC则返回None
        """
        config = cls.get_config(chain)
        return config.get('rpc_url')
    
    @classmethod
    def get_explorer_url(cls, chain: str, tx_hash: str) -> str:
        """
        获取浏览器URL
        
        Args:
            chain: 链名称
            tx_hash: 交易哈希
            
        Returns:
            浏览器URL
        """
        config = cls.get_config(chain)
        return f"{config['explorer']}/tx/{tx_hash}"
