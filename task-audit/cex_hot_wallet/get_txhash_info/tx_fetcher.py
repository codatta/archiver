"""
交易信息获取器
使用web3.py从区块链获取交易信息
"""
from typing import Optional, List
import requests
import base58
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.exceptions import TransactionNotFound, BlockNotFound

from .models import TransactionInfo, ChainType, timestamp_to_date
from .chain_config import ChainConfig


class TransactionFetcher:
    """交易信息获取器"""
    
    def __init__(self, chain: str):
        """
        初始化
        
        Args:
            chain: 'bsc', 'btc', 'base', 'sol', 'arb', 'eth', 'tron', 'op', 'polygon', 'etc', 'bch'
        """
        self.chain = chain.lower()
        
        # 检查链是否支持
        try:
            ChainConfig.get_config(self.chain)
        except ValueError:
            raise ValueError(f"不支持的链: {chain}. 支持的链: {list(ChainConfig.CHAIN_CONFIGS.keys())}")
        
        # 设置链类型
        chain_type_map = {
            'bsc': ChainType.BSC,
            'btc': ChainType.BTC,
            'base': ChainType.BASE,
            'sol': ChainType.SOL,
            'arb': ChainType.ARB,
            'eth': ChainType.ETH,
            'tron': ChainType.TRON,
            'op': ChainType.OP,
            'polygon': ChainType.POLYGON,
            'etc': ChainType.ETC,
            'bch': ChainType.BCH
        }
        self.chain_type = chain_type_map.get(self.chain, ChainType.ETH)
        
        # 检查是否为EVM兼容链
        self.is_evm = ChainConfig.is_evm_chain(self.chain)
        self.web3 = None
        self.rpc_urls = []  # 存储所有可用的RPC URL
        
        if self.is_evm:
            # EVM兼容链：使用web3.py
            config = ChainConfig.get_config(self.chain)
            rpc_url = config.get('rpc_url')
            rpc_urls = config.get('rpc_urls', [])
            
            # 构建RPC URL列表（主RPC + 备用RPC）
            if rpc_url:
                self.rpc_urls = [rpc_url] + [url for url in rpc_urls if url != rpc_url]
            else:
                self.rpc_urls = rpc_urls
            
            # 尝试连接RPC节点（允许失败，在实际使用时再重试）
            connected = False
            last_error = None
            for rpc_url in self.rpc_urls:
                try:
                    self.web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                    
                    # POA链需要添加POA中间件
                    if ChainConfig.is_poa_chain(self.chain):
                        self.web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                    
                    # 检查连接（使用更宽松的检查，只验证RPC是否响应）
                    try:
                        # 尝试获取链ID来验证连接
                        chain_id = self.web3.eth.chain_id
                        if chain_id:
                            connected = True
                            break
                    except:
                        # 如果chain_id获取失败，尝试简单的连接检查
                        if self.web3.is_connected():
                            connected = True
                            break
                except Exception as e:
                    last_error = e
                    continue
            
            # 如果所有RPC都失败，仍然创建web3实例（使用第一个RPC），在实际使用时再重试
            if not connected:
                # 使用第一个RPC创建web3实例，但不抛出错误
                try:
                    self.web3 = Web3(Web3.HTTPProvider(self.rpc_urls[0], request_kwargs={'timeout': 10}))
                    if ChainConfig.is_poa_chain(self.chain):
                        self.web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                except:
                    pass
                # 不抛出错误，让实际使用时再尝试连接
        else:
            # 非EVM链：需要特殊处理
            if self.chain == 'btc':
                # BTC使用blockstream.info API
                self.api_base_url = 'https://blockstream.info/api'
            elif self.chain == 'bch':
                # BCH使用blockchair API
                self.api_base_url = 'https://api.blockchair.com/bitcoin-cash'
            elif self.chain == 'tron':
                # TRON使用TronGrid API
                self.api_base_url = 'https://api.trongrid.io'
            elif self.chain == 'sol':
                # SOL使用Solana RPC API
                config = ChainConfig.get_config(self.chain)
                self.api_base_url = config.get('rpc_url', 'https://api.mainnet-beta.solana.com')
    
    def normalize_tx_hash(self, tx_hash: str) -> str:
        """
        规范化交易哈希格式
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            规范化后的交易哈希
        """
        tx_hash = tx_hash.strip()
        if self.is_evm:
            # EVM链：添加0x前缀并转小写
            if not tx_hash.startswith('0x'):
                tx_hash = '0x' + tx_hash
            return tx_hash.lower()
        elif self.chain == 'sol':
            # Solana：保持原样（Base58编码，大小写敏感）
            return tx_hash
        else:
            # BTC等：保持原样（小写）
            return tx_hash.lower()
    
    def _get_btc_transaction_info(self, tx_hash: str) -> Optional[TransactionInfo]:
        """
        获取BTC交易信息（使用blockstream.info API）
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            TransactionInfo 对象或 None
        """
        # 重置临时变量
        self._btc_from_addresses = []
        self._btc_to_addresses = []
        
        try:
            # 获取交易信息
            tx_url = f"{self.api_base_url}/tx/{tx_hash}"
            response = requests.get(tx_url, timeout=10)
            response.raise_for_status()
            tx_data = response.json()
            
            # 获取交易状态（通过检查是否在区块中）
            status = 'success' if tx_data.get('status', {}).get('block_hash') else 'pending'
            
            # 提取输入地址（from地址）
            vin = tx_data.get('vin', [])
            from_addresses = []
            for input_tx in vin:
                prevout = input_tx.get('prevout', {})
                addr = prevout.get('scriptpubkey_address')
                if addr:
                    from_addresses.append(addr)
            
            # 提取输出地址（to地址）
            vout = tx_data.get('vout', [])
            to_addresses = []
            total_value = 0
            for output in vout:
                addr = output.get('scriptpubkey_address')
                if addr:
                    to_addresses.append(addr)
                value = output.get('value', 0)  # 单位：satoshi
                total_value += value
            
            # BTC交易可能有多个输入和输出
            # 保存所有地址（用于后续返回）
            # 对于from地址，如果有多个，用逗号连接；如果只有一个，直接使用
            if from_addresses:
                from_address = from_addresses[0] if len(from_addresses) == 1 else ", ".join(from_addresses)
            else:
                from_address = "未知"
            
            # 对于to地址，如果有多个，用逗号连接；如果只有一个，直接使用
            if to_addresses:
                to_address = to_addresses[0] if len(to_addresses) == 1 else ", ".join(to_addresses)
            else:
                to_address = None
            
            # 保存原始地址列表（用于get_from_to_addresses方法）
            self._btc_from_addresses = from_addresses
            self._btc_to_addresses = to_addresses
            
            # 获取区块信息
            block_height = tx_data.get('status', {}).get('block_height')
            block_hash = tx_data.get('status', {}).get('block_hash')
            
            timestamp = None
            # 方法1: 尝试从交易数据中直接获取 block_time（blockstream.info API可能直接返回）
            status = tx_data.get('status', {})
            if status:
                # blockstream.info API可能在status中直接返回block_time
                block_time = status.get('block_time')
                if block_time:
                    timestamp = block_time
            
            # 方法2: 如果方法1失败，尝试通过区块API获取
            if timestamp is None and block_hash:
                # 获取区块信息以获取时间戳
                block_url = f"{self.api_base_url}/block/{block_hash}"
                try:
                    block_response = requests.get(block_url, timeout=10)
                    block_response.raise_for_status()
                    block_data = block_response.json()
                    timestamp = block_data.get('timestamp')
                except Exception as e:
                    # 打印错误信息以便调试
                    print(f"[警告] 获取BTC区块信息失败 {block_hash}: {str(e)[:100]}")
            
            # 方法3: 如果还是失败，尝试使用区块高度获取区块信息
            if timestamp is None and block_height:
                try:
                    block_url = f"{self.api_base_url}/block-height/{block_height}"
                    block_response = requests.get(block_url, timeout=10)
                    block_response.raise_for_status()
                    block_hash_from_height = block_response.text.strip()  # 返回的是block hash字符串
                    if block_hash_from_height:
                        block_url2 = f"{self.api_base_url}/block/{block_hash_from_height}"
                        block_response2 = requests.get(block_url2, timeout=10)
                        block_response2.raise_for_status()
                        block_data = block_response2.json()
                        timestamp = block_data.get('timestamp')
                except Exception as e:
                    print(f"[警告] 通过区块高度获取BTC区块信息失败 {block_height}: {str(e)[:100]}")
            
            date = timestamp_to_date(timestamp)
            
            return TransactionInfo(
                chain=self.chain_type,
                tx_hash=tx_hash,
                from_address=from_address,
                to_address=to_address,
                value=str(total_value),  # satoshi
                gas="0",  # BTC没有gas概念
                gas_price="0",  # BTC没有gas price概念
                block_number=block_height if block_height else 0,
                timestamp=timestamp,
                status=status,
                date=date
            )
        except requests.RequestException as e:
            print(f"获取BTC交易信息失败 {tx_hash}: {str(e)}")
            return None
        except Exception as e:
            print(f"解析BTC交易信息失败 {tx_hash}: {str(e)}")
            return None
    
    def _get_bch_transaction_info(self, tx_hash: str) -> Optional[TransactionInfo]:
        """
        获取BCH交易信息（使用blockchair API）
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            TransactionInfo 对象或 None
        """
        # 重置临时变量
        self._bch_from_addresses = []
        self._bch_to_addresses = []
        
        try:
            # 获取交易信息
            tx_url = f"{self.api_base_url}/raw/transaction/{tx_hash}"
            response = requests.get(tx_url, timeout=10)
            response.raise_for_status()
            tx_data = response.json()
            
            if 'data' not in tx_data or not tx_data['data']:
                print(f"BCH交易未找到: {tx_hash}")
                return None
            
            tx_info = tx_data['data'][tx_hash]
            
            # 提取输入地址（from地址）
            inputs = tx_info.get('inputs', [])
            from_addresses = []
            for input_tx in inputs:
                # BCH的输入地址在output_script中
                recipient = input_tx.get('recipient')
                if recipient:
                    from_addresses.append(recipient)
            
            # 提取输出地址（to地址）
            outputs = tx_info.get('outputs', [])
            to_addresses = []
            total_value = 0
            for output in outputs:
                recipient = output.get('recipient')
                if recipient:
                    to_addresses.append(recipient)
                value = output.get('value', 0)  # 单位：satoshi
                total_value += value
            
            # 保存所有地址
            if from_addresses:
                from_address = from_addresses[0] if len(from_addresses) == 1 else ", ".join(from_addresses)
            else:
                from_address = "未知"
            
            if to_addresses:
                to_address = to_addresses[0] if len(to_addresses) == 1 else ", ".join(to_addresses)
            else:
                to_address = None
            
            self._bch_from_addresses = from_addresses
            self._bch_to_addresses = to_addresses
            
            # 获取区块信息
            block_id = tx_info.get('block_id')
            block_time = tx_info.get('time')
            
            timestamp = None
            if block_time:
                timestamp = block_time
            
            date = timestamp_to_date(timestamp)
            status = 'success' if block_id else 'pending'
            
            return TransactionInfo(
                chain=self.chain_type,
                tx_hash=tx_hash,
                from_address=from_address,
                to_address=to_address,
                value=str(total_value),  # satoshi
                gas="0",
                gas_price="0",
                block_number=block_id if block_id else 0,
                timestamp=timestamp,
                status=status,
                date=date
            )
        except requests.RequestException as e:
            print(f"获取BCH交易信息失败 {tx_hash}: {str(e)}")
            return None
        except Exception as e:
            print(f"解析BCH交易信息失败 {tx_hash}: {str(e)}")
            return None
    
    def _get_tron_transaction_info(self, tx_hash: str) -> Optional[TransactionInfo]:
        """
        获取TRON交易信息（使用TronGrid API）
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            TransactionInfo 对象或 None
        """
        try:
            # TRON交易哈希不需要0x前缀
            if tx_hash.startswith('0x'):
                tx_hash = tx_hash[2:]
            
            # 获取交易信息（使用gettransactionbyid）
            tx_url = f"{self.api_base_url}/wallet/gettransactionbyid"
            payload = {"value": tx_hash}
            response = requests.post(tx_url, json=payload, timeout=10)
            response.raise_for_status()
            tx_data = response.json()
            
            if not tx_data or 'ret' not in tx_data:
                print(f"TRON交易未找到: {tx_hash}")
                return None
            
            # 同时获取详细的交易信息（包含内部交易）
            tx_info_url = f"{self.api_base_url}/wallet/gettransactioninfobyid"
            tx_info_payload = {"value": tx_hash}
            tx_info_data = None
            try:
                info_response = requests.post(tx_info_url, json=tx_info_payload, timeout=10)
                info_response.raise_for_status()
                tx_info_data = info_response.json()
            except:
                pass  # 如果获取失败，继续使用基本交易信息
            
            # 检查交易状态
            ret = tx_data.get('ret', [{}])[0]
            status = 'success' if ret.get('contractRet') == 'SUCCESS' else 'failed'
            
            # 提取地址信息
            # TRON交易可能有多个contract，需要遍历所有contract
            raw_data = tx_data.get('raw_data', {})
            contracts = raw_data.get('contract', [])
            
            from_address = None
            to_address = None
            amount = 0
            
            # 遍历所有contract查找地址信息
            for contract in contracts:
                contract_type = contract.get('type')
                parameter = contract.get('parameter', {})
                value = parameter.get('value', {})
                
                # 获取from地址（owner_address）
                if not from_address:
                    owner_address = value.get('owner_address', '')
                    if owner_address:
                        from_address = self._tron_hex_to_base58(owner_address)
                
                # 根据不同的contract类型提取to地址
                if contract_type == 'TransferContract':
                    # 普通转账
                    to_address_hex = value.get('to_address', '')
                    if to_address_hex:
                        to_address = self._tron_hex_to_base58(to_address_hex)
                    amount = value.get('amount', 0)
                    break  # TransferContract通常只有一个，找到后可以退出
                elif contract_type == 'TriggerSmartContract':
                    # 智能合约调用 - contract_address是合约地址，不是接收地址
                    # 需要从内部交易中获取真正的接收地址
                    contract_address = value.get('contract_address', '')
                    
                    # 优先从tx_info_data中获取内部交易
                    if tx_info_data:
                        # 从internal_transactions中提取接收地址
                        internal_transactions = tx_info_data.get('internal_transactions', [])
                        for itx in internal_transactions:
                            # 查找transferTo_address字段（这是内部交易的接收地址）
                            transfer_to = itx.get('transferTo_address', '')
                            if not transfer_to:
                                # 尝试其他可能的字段
                                transfer_to = itx.get('to_address', '') or itx.get('to', '')
                            
                            if transfer_to:
                                to_address = self._tron_hex_to_base58(transfer_to)
                                # 获取转账金额
                                call_value_info = itx.get('callValueInfo', [{}])
                                if call_value_info and call_value_info[0].get('callValue', 0) > 0:
                                    amount = call_value_info[0].get('callValue', 0)
                                break
                        
                        # 如果internal_transactions中没有找到，尝试从log中解析
                        if not to_address and 'log' in tx_info_data:
                            # log中可能包含Transfer事件的信息
                            for log in tx_info_data.get('log', []):
                                # 尝试从log的topics中解析地址（TRC20 Transfer事件）
                                topics = log.get('topics', [])
                                if len(topics) >= 3:
                                    # Transfer(address,address,uint256) - topics[1]是from, topics[2]是to
                                    # 但topics是hex格式，需要解析
                                    try:
                                        # topics[2]是接收地址（去掉0x前缀，取后40个字符）
                                        to_hex = topics[2] if len(topics) > 2 else ''
                                        if to_hex and len(to_hex) >= 42:
                                            to_hex = '41' + to_hex[-40:]  # 添加TRON地址前缀
                                            to_address = self._tron_hex_to_base58(to_hex)
                                            break
                                    except:
                                        pass
                    
                    # 如果还没有找到，尝试从事件中获取
                    if not to_address:
                        internal_tx = self._get_tron_internal_transactions(tx_hash)
                        if internal_tx:
                            # 从内部交易中提取接收地址
                            for itx in internal_tx:
                                # 查找Transfer事件中的接收地址
                                transfer_to = itx.get('transferTo_address', '') or itx.get('to', '') or itx.get('to_address', '')
                                if transfer_to:
                                    to_address = self._tron_hex_to_base58(transfer_to)
                                    # 获取转账金额
                                    call_value_info = itx.get('callValueInfo', [{}])
                                    if call_value_info and call_value_info[0].get('callValue', 0) > 0:
                                        amount = call_value_info[0].get('callValue', 0)
                                    break
                    
                    # 如果还是没有找到，对于合约调用，to_address应该是None
                    # 因为contract_address不是真正的接收地址
                    
                    # 对于合约调用，可能还需要从call_value获取金额
                    call_value = value.get('call_value', 0)
                    if call_value > 0 and amount == 0:
                        amount = call_value
                elif contract_type == 'TransferAssetContract':
                    # 代币转账
                    to_address_hex = value.get('to_address', '')
                    if to_address_hex:
                        to_address = self._tron_hex_to_base58(to_address_hex)
                    amount = value.get('amount', 0)
                    break
            
            # 如果还是没有找到to_address，且不是TriggerSmartContract，尝试从第一个contract获取
            if not to_address and contracts:
                first_contract = contracts[0]
                contract_type = first_contract.get('type')
                # 对于非TriggerSmartContract类型，可以尝试获取to_address
                if contract_type != 'TriggerSmartContract':
                    first_value = first_contract.get('parameter', {}).get('value', {})
                    # 尝试多种可能的字段名
                    for field in ['to_address', 'receiver_address']:
                        addr_hex = first_value.get(field, '')
                        if addr_hex:
                            to_address = self._tron_hex_to_base58(addr_hex)
                            break
            
            # 调试信息：如果to_address仍为None，打印contract类型
            if not to_address and contracts:
                contract_types = [c.get('type', 'Unknown') for c in contracts]
                if 'TriggerSmartContract' in contract_types:
                    print(f"[调试] TRON智能合约调用，未找到内部交易中的接收地址")
                else:
                    print(f"[调试] TRON交易contract类型: {contract_types}, 未找到to_address")
            
            # 获取区块信息
            block_number = tx_data.get('blockNumber', 0)
            block_timestamp = tx_data.get('block_timestamp', 0)
            timestamp = block_timestamp // 1000 if block_timestamp else None  # TRON使用毫秒
            
            date = timestamp_to_date(timestamp)
            
            return TransactionInfo(
                chain=self.chain_type,
                tx_hash=tx_hash,
                from_address=from_address or "未知",
                to_address=to_address,
                value=str(amount),
                gas=str(tx_data.get('ret', [{}])[0].get('fee', 0)),
                gas_price="0",
                block_number=block_number,
                timestamp=timestamp,
                status=status,
                date=date
            )
        except requests.RequestException as e:
            print(f"获取TRON交易信息失败 {tx_hash}: {str(e)}")
            return None
        except Exception as e:
            print(f"解析TRON交易信息失败 {tx_hash}: {str(e)}")
            return None
    
    def _get_tron_internal_transactions(self, tx_hash: str) -> Optional[List]:
        """
        获取TRON交易的内部交易（用于找到真正的接收地址）
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            内部交易列表或None
        """
        try:
            # 方法1: 尝试从事件中获取
            try:
                events_url = f"{self.api_base_url}/v1/transactions/{tx_hash}/events"
                response = requests.get(events_url, timeout=10)
                response.raise_for_status()
                events_data = response.json()
                
                # 提取transfer事件
                internal_transactions = []
                if 'data' in events_data:
                    for event in events_data['data']:
                        # 查找Transfer事件
                        if event.get('event_name') == 'Transfer':
                            internal_transactions.append(event)
                        # 也检查是否有to字段
                        if 'to' in event or 'to_address' in event or 'transferTo_address' in event:
                            internal_transactions.append(event)
                
                if internal_transactions:
                    return internal_transactions
            except:
                pass
            
            # 方法2: 尝试从gettransactioninfobyid获取内部交易信息
            try:
                info_url = f"{self.api_base_url}/wallet/gettransactioninfobyid"
                payload = {"value": tx_hash}
                response = requests.post(info_url, json=payload, timeout=10)
                response.raise_for_status()
                info_data = response.json()
                
                # 从log中提取内部交易信息
                internal_transactions = []
                if 'log' in info_data:
                    for log in info_data['log']:
                        # log中包含地址信息
                        if 'address' in log:
                            internal_transactions.append(log)
                
                # 也检查internal_transactions字段
                if 'internal_transactions' in info_data:
                    internal_transactions.extend(info_data['internal_transactions'])
                
                if internal_transactions:
                    return internal_transactions
            except:
                pass
            
            return None
        except Exception as e:
            # 如果获取内部交易失败，返回None
            return None
    
    def _tron_hex_to_base58(self, hex_address: str) -> str:
        """
        将TRON的hex地址转换为base58格式（T开头）
        
        Args:
            hex_address: hex格式的地址（带或不带0x前缀）
            
        Returns:
            base58格式的地址（T开头），如果转换失败则返回hex地址
        """
        try:
            # 移除0x前缀
            if hex_address.startswith('0x'):
                hex_address = hex_address[2:]
            
            # 如果已经是base58格式（T开头），直接返回
            if hex_address.startswith('T'):
                return hex_address
            
            # 转换为bytes
            try:
                address_bytes = bytes.fromhex(hex_address)
            except ValueError:
                # 如果转换失败，可能已经是base58格式
                return hex_address
            
            # TRON地址应该是21字节（包括0x41前缀）
            if len(address_bytes) != 21:
                # 如果长度不对，尝试添加0x41前缀
                if len(address_bytes) == 20:
                    address_bytes = b'\x41' + address_bytes
                else:
                    return hex_address  # 无法转换，返回原值
            
            # 计算校验和（取前4字节的double SHA256）
            import hashlib
            hash1 = hashlib.sha256(address_bytes).digest()
            hash2 = hashlib.sha256(hash1).digest()
            checksum = hash2[:4]
            
            # 组合地址+校验和
            address_with_checksum = address_bytes + checksum
            
            # 转换为base58
            base58_address = base58.b58encode(address_with_checksum).decode('utf-8')
            
            return base58_address
        except Exception as e:
            # 转换失败，返回原值
            print(f"[警告] TRON地址转换失败: {hex_address}, 错误: {e}")
            return hex_address
    
    def _get_sol_transaction_info(self, tx_hash: str) -> Optional[TransactionInfo]:
        """
        获取Solana交易信息（使用Solana RPC API）
        
        Args:
            tx_hash: 交易签名（Solana使用签名而不是哈希）
            
        Returns:
            TransactionInfo 对象或 None
        """
        try:
            # Solana RPC使用JSON-RPC格式
            # 调用getTransaction方法，使用jsonParsed编码以便解析指令
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTransaction",
                "params": [
                    tx_hash,
                    {
                        "encoding": "jsonParsed",
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }
            
            response = requests.post(
                self.api_base_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # 检查是否有错误
            if "error" in result:
                error_msg = result["error"].get("message", "未知错误")
                if "not found" in error_msg.lower():
                    print(f"Solana交易未找到: {tx_hash}")
                    return None
                raise Exception(f"Solana RPC错误: {error_msg}")
            
            tx_data = result.get("result")
            if not tx_data:
                print(f"Solana交易未找到: {tx_hash}")
                return None
            
            # 提取交易信息
            transaction = tx_data.get("transaction", {})
            message = transaction.get("message", {})
            meta = tx_data.get("meta", {})
            
            # 获取账户列表（accounts）
            accounts = message.get("accountKeys", [])
            
            # 获取签名者（signers）- 这些是from地址
            signers = []
            signer_pubkeys = set()
            for account_info in accounts:
                if isinstance(account_info, dict):
                    pubkey = account_info.get("pubkey")
                    is_signer = account_info.get("signer", False)
                else:
                    pubkey = account_info
                    is_signer = False
                
                if pubkey:
                    if is_signer:
                        signers.append(pubkey)
                        signer_pubkeys.add(pubkey)
                    # 如果没有signer字段，尝试从header判断
                    elif not signers and len(signers) == 0:
                        # 第一个账户通常是签名者
                        header = message.get("header", {})
                        num_required_signatures = header.get("numRequiredSignatures", 0)
                        if len(signers) < num_required_signatures:
                            signers.append(pubkey)
                            signer_pubkeys.add(pubkey)
            
            from_address = signers[0] if signers else "未知"
            
            # 获取to地址
            to_address = None
            
            # 方法1: 从parsed instructions中提取（使用jsonParsed编码）
            instructions = message.get("instructions", [])
            for instruction in instructions:
                parsed = instruction.get("parsed", {})
                if parsed:
                    # 查找Transfer指令
                    if parsed.get("type") == "transfer":
                        info = parsed.get("info", {})
                        destination = info.get("destination")
                        if destination:
                            to_address = destination
                            break
                    # 查找其他可能的转账类型
                    elif parsed.get("type") == "transferChecked":
                        info = parsed.get("info", {})
                        destination = info.get("destination")
                        if destination:
                            to_address = destination
                            break
            
            # 方法2: 从余额变化中提取（余额增加的账户是接收者）
            if not to_address:
                pre_balances = meta.get("preBalances", [])
                post_balances = meta.get("postBalances", [])
                
                if pre_balances and post_balances and len(pre_balances) == len(post_balances):
                    # 找到余额增加的账户（接收者）
                    for i in range(len(pre_balances)):
                        balance_change = post_balances[i] - pre_balances[i]
                        if balance_change > 0:  # 余额增加
                            if i < len(accounts):
                                account_info = accounts[i]
                                if isinstance(account_info, dict):
                                    pubkey = account_info.get("pubkey")
                                else:
                                    pubkey = account_info
                                
                                # 确保不是签名者（发送者）
                                if pubkey and pubkey not in signer_pubkeys:
                                    to_address = pubkey
                                    break
            
            # 方法3: 从账户列表中找非签名者账户（作为备选）
            if not to_address:
                for account_info in accounts:
                    if isinstance(account_info, dict):
                        pubkey = account_info.get("pubkey")
                        is_signer = account_info.get("signer", False)
                    else:
                        pubkey = account_info
                        is_signer = False
                    
                    # 跳过签名者账户
                    if pubkey and not is_signer and pubkey not in signer_pubkeys:
                        to_address = pubkey
                        break
            
            # 获取交易金额（从preBalances和postBalances计算）
            pre_balances = meta.get("preBalances", [])
            post_balances = meta.get("postBalances", [])
            
            # 计算金额变化（lamports，1 SOL = 1,000,000,000 lamports）
            value = 0
            if pre_balances and post_balances and len(pre_balances) == len(post_balances):
                # 找到发送者的余额变化（余额减少）
                for i in range(len(pre_balances)):
                    balance_change = post_balances[i] - pre_balances[i]
                    if balance_change < 0:  # 发送者余额减少
                        value = abs(balance_change)
                        break
                
                # 如果没找到，尝试从parsed instructions中提取金额
                if value == 0:
                    for instruction in instructions:
                        parsed = instruction.get("parsed", {})
                        if parsed and parsed.get("type") in ["transfer", "transferChecked"]:
                            info = parsed.get("info", {})
                            lamports = info.get("lamports") or info.get("amount")
                            if lamports:
                                value = lamports
                                break
            
            # 获取区块信息
            slot = tx_data.get("slot")
            block_time = tx_data.get("blockTime")
            timestamp = block_time if block_time else None
            
            # 获取交易状态
            err = meta.get("err")
            status = 'success' if err is None else 'failed'
            
            date = timestamp_to_date(timestamp)
            
            return TransactionInfo(
                chain=self.chain_type,
                tx_hash=tx_hash,
                from_address=from_address,
                to_address=to_address,
                value=str(value),  # lamports
                gas=str(meta.get("fee", 0)),  # Solana交易费用
                gas_price="0",  # Solana没有gas price概念
                block_number=slot if slot else 0,
                timestamp=timestamp,
                status=status,
                date=date
            )
        except requests.RequestException as e:
            print(f"获取Solana交易信息失败 {tx_hash}: {str(e)}")
            return None
        except Exception as e:
            print(f"解析Solana交易信息失败 {tx_hash}: {str(e)}")
            return None

    @staticmethod
    def _decode_evm_erc20_transfer_to(tx_data: dict) -> Optional[str]:
        """
        从 EVM 交易的 input 中解析 ERC20/BEP20 transfer 或 transferFrom 的实际收款人地址。
        若 input 为 transfer(address,uint256) 或 transferFrom(address,address,uint256)，返回 to 地址；
        否则返回 None。
        """
        raw = tx_data.get('input') or tx_data.get('data') or ''
        if not raw:
            return None
        if isinstance(raw, bytes):
            s = ('0x' + raw.hex()).lower()
        else:
            s = raw.lower() if raw.startswith('0x') else '0x' + raw.lower()
        if len(s) < 10:
            return None
        # transfer(address,uint256): selector 0xa9059cbb，to 为第 1 个参数（32 字节，右对齐）
        if s.startswith('0xa9059cbb') and len(s) >= 74:
            to_hex = s[34:74]
            if len(to_hex) == 40 and all(c in '0123456789abcdef' for c in to_hex):
                return '0x' + to_hex
        # transferFrom(address,address,uint256): selector 0x23b872dd，to 为第 2 个参数
        if s.startswith('0x23b872dd') and len(s) >= 138:
            to_hex = s[98:138]
            if len(to_hex) == 40 and all(c in '0123456789abcdef' for c in to_hex):
                return '0x' + to_hex
        return None

    def get_transaction_info(self, tx_hash: str) -> Optional[TransactionInfo]:
        """
        获取完整交易信息
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            TransactionInfo 对象或 None（如果交易不存在）
        """
        # 规范化交易哈希
        tx_hash = self.normalize_tx_hash(tx_hash)
        
        # 非EVM链使用特殊方法
        if self.chain == 'btc':
            return self._get_btc_transaction_info(tx_hash)
        elif self.chain == 'bch':
            return self._get_bch_transaction_info(tx_hash)
        elif self.chain == 'tron':
            return self._get_tron_transaction_info(tx_hash)
        elif self.chain == 'sol':
            return self._get_sol_transaction_info(tx_hash)
        
        # EVM链使用web3
        if not self.is_evm:
            raise NotImplementedError(f"{self.chain.upper()} 链暂未实现交易信息获取功能")
        
        try:
            # 先检查 RPC 连接，如果断开则尝试重新连接
            if not self.web3.is_connected():
                # 尝试重新连接
                connected = False
                for rpc_url in self.rpc_urls:
                    try:
                        self.web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                        if ChainConfig.is_poa_chain(self.chain):
                            self.web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                        if self.web3.is_connected():
                            connected = True
                            break
                    except:
                        continue
                
                if not connected:
                    raise ConnectionError(f"RPC连接已断开，无法重新连接。已尝试: {', '.join(self.rpc_urls)}")
            
            # 获取交易详情（如果失败，尝试其他RPC）
            tx_data = None
            last_error = None
            tried_rpc = set()  # 记录已尝试的RPC
            
            # 先尝试当前连接的RPC
            try:
                tx_data = self.web3.eth.get_transaction(tx_hash)
            except TransactionNotFound:
                # 交易未找到，不尝试其他RPC（因为交易确实不存在）
                print(f"交易未找到: {tx_hash}")
                print(f"提示: 请确认交易哈希是否正确，以及是否在 {self.chain.upper()} 链上")
                return None
            except Exception as e:
                # 当前RPC失败，记录错误并尝试其他RPC
                last_error = e
                tried_rpc.add(self.rpc_urls[0] if self.rpc_urls else '')
                
                # 尝试其他RPC
                for rpc_url in self.rpc_urls[1:]:  # 跳过第一个（已尝试）
                    if rpc_url in tried_rpc:
                        continue
                    tried_rpc.add(rpc_url)
                    try:
                        # 创建新的web3实例
                        temp_web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                        if ChainConfig.is_poa_chain(self.chain):
                            temp_web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                        
                        if temp_web3.is_connected():
                            tx_data = temp_web3.eth.get_transaction(tx_hash)
                            # 成功，更新当前web3实例
                            self.web3 = temp_web3
                            break
                    except TransactionNotFound:
                        # 交易未找到，不尝试其他RPC
                        print(f"交易未找到: {tx_hash}")
                        print(f"提示: 请确认交易哈希是否正确，以及是否在 {self.chain.upper()} 链上")
                        return None
                    except Exception:
                        continue  # 尝试下一个RPC
            
            if tx_data is None:
                error_msg = f"获取交易失败"
                if last_error:
                    error_msg += f": {str(last_error)}"
                print(error_msg)
                print(f"已尝试RPC: {', '.join(tried_rpc)}")
                return None
            
            # 获取交易收据（用于获取状态）
            try:
                tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                status = 'success' if tx_receipt.status == 1 else 'failed'
            except TransactionNotFound:
                status = None
            
            # 解析交易信息
            from_address = tx_data['from']
            to_address = tx_data.get('to')  # 可能是None（合约创建）
            # 若为 ERC20/BEP20 transfer，tx.to 是合约地址，实际收款人在 input 中
            evm_token_to = self._decode_evm_erc20_transfer_to(tx_data)
            if evm_token_to is not None:
                to_address = evm_token_to

            # 转换数值（从wei转换为字符串）
            value = str(tx_data.get('value', 0))
            gas = str(tx_data.get('gas', 0))
            gas_price = str(tx_data.get('gasPrice', 0))
            
            block_number = tx_data.get('blockNumber')
            if block_number is None:
                # 如果交易还在pending状态，blockNumber可能为None
                return TransactionInfo(
                    chain=self.chain_type,
                    tx_hash=tx_hash,
                    from_address=from_address,
                    to_address=to_address,
                    value=value,
                    gas=gas,
                    gas_price=gas_price,
                    block_number=0,
                    status=status,
                    date=None  # pending交易没有日期
                )
            
            # 获取区块时间戳
            timestamp = None
            try:
                block = self.web3.eth.get_block(block_number)
                timestamp = block.get('timestamp')
            except BlockNotFound:
                pass
            
            # 将时间戳转换为日期格式
            date = timestamp_to_date(timestamp)
            
            return TransactionInfo(
                chain=self.chain_type,
                tx_hash=tx_hash,
                from_address=from_address,
                to_address=to_address,
                value=value,
                gas=gas,
                gas_price=gas_price,
                block_number=block_number,
                timestamp=timestamp,
                status=status,
                date=date
            )
        
        except Exception as e:
            print(f"获取交易信息失败 {tx_hash}: {str(e)}")
            return None
    
    def get_from_to_addresses(self, tx_hash: str) -> Optional[dict]:
        """
        简化版：仅获取 from 和 to 地址，以及交易日期
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            {'from': '0x...' 或 ['0x...', '0x...'], 'to': '0x...' 或 ['0x...', '0x...'], 'chain': 'bsc/eth', 'tx_hash': '...', 'date': 'YYYY-MM-DD'} 或 None
            对于BTC链，如果有多个地址，from和to会是列表格式
        """
        tx_info = self.get_transaction_info(tx_hash)
        if tx_info:
            result = {
                'chain': self.chain,
                'tx_hash': tx_info.tx_hash
            }
            
            # 对于BTC和BCH链，如果有多个地址，返回列表
            if self.chain in ['btc', 'bch']:
                from_attr = f'_btc_from_addresses' if self.chain == 'btc' else f'_bch_from_addresses'
                to_attr = f'_btc_to_addresses' if self.chain == 'btc' else f'_bch_to_addresses'
                
                if hasattr(self, from_attr) and hasattr(self, to_attr):
                    from_addresses = getattr(self, from_attr, [])
                    to_addresses = getattr(self, to_attr, [])
                    
                    if len(from_addresses) > 1:
                        result['from'] = from_addresses
                    else:
                        result['from'] = from_addresses[0] if from_addresses else "未知"
                    
                    if len(to_addresses) > 1:
                        result['to'] = to_addresses
                    else:
                        result['to'] = to_addresses[0] if to_addresses else None
            else:
                # EVM链或其他链，使用单个地址
                result['from'] = tx_info.from_address
                result['to'] = tx_info.to_address
            
            if tx_info.date:
                result['date'] = tx_info.date
            return result
        return None
    
    def is_connected(self) -> bool:
        """检查RPC连接状态"""
        if self.is_evm and self.web3:
            return self.web3.is_connected()
        return False
