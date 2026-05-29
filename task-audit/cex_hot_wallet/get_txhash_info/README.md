# 交易哈希审核模块

用于根据交易hash获取from和to地址，支持BSC和ETH两条链。

## 功能特性

1. **交易信息获取**: 根据交易hash获取from和to地址
2. **多链支持**: 支持BSC（Binance Smart Chain）和ETH（Ethereum）
3. **完整信息**: 可获取完整的交易信息（金额、gas、区块号、时间戳等）
4. **批量处理**: 支持批量查询多笔交易

## 项目结构

```
get_txhash_info/
├── __init__.py              # 模块初始化
├── models.py                # 数据模型定义
├── chain_config.py          # 区块链配置
├── tx_fetcher.py            # 交易信息获取器
├── main.py                  # 主程序入口
├── example_usage.py         # 使用示例
└── README.md                # 本文档
```

## 安装依赖

```bash
pip3.10 install -r requirements.txt
```

## 使用方法

### 1. Python代码使用

#### 基本用法：获取from和to地址

```python
from get_txhash_info import TransactionFetcher

# 创建BSC链的fetcher
bsc_fetcher = TransactionFetcher("bsc")

# 获取交易地址
tx_hash = "0xe698fb3ff8ec46b1ee0b10cbf4795c8267e7f8fb38ea1b63012c5448852b215a"
result = bsc_fetcher.get_from_to_addresses(tx_hash)

if result:
    print(f"From: {result['from']}")
    print(f"To: {result['to']}")
```

#### 获取完整交易信息

```python
from get_txhash_info import TransactionFetcher

fetcher = TransactionFetcher("eth")
tx_info = fetcher.get_transaction_info(tx_hash)

if tx_info:
    print(f"From: {tx_info.from_address}")
    print(f"To: {tx_info.to_address}")
    print(f"Value: {tx_info.value}")
    print(f"Block: {tx_info.block_number}")
    print(f"Status: {tx_info.status}")
```

### 2. 命令行使用

#### 查询单笔交易

```bash
# 查询BSC链上的交易
python3.10 -m get_txhash_info.main 0xe698fb3ff8ec46b1ee0b10cbf4795c8267e7f8fb38ea1b63012c5448852b215a --chain bsc

# 查询ETH链上的交易
python3.10 -m get_txhash_info.main 0x1234... --chain eth

# 显示完整信息
python3.10 -m get_txhash_info.main <tx_hash> --chain bsc --full
```

#### 实际调用示例

以下是一些实际交易哈希的调用示例，展示不同链的使用方式：

```bash
# BSC链示例
python3.10 -m get_txhash_info.main 0x6870cdd18a1c1126af6e97312bfb7e1e72e80f4e27e0353cbecf7b090c68130b --chain bsc

# ETH链示例
python3.10 -m get_txhash_info.main 0xe6872d032f0ad82e4e10e33fca395fe7074331d2941bfd12997015be704bc001 --chain eth

# BTC链示例
python3.10 -m get_txhash_info.main 60612bf54991651ce8bc31a310bf2405675c31df963c4545b2ffe237ef10bd64 --chain btc

# Base链示例
python3.10 -m get_txhash_info.main 0xe6872d032f0ad82e4e10e33fca395fe7074331d2941bfd12997015be704bc001 --chain base

# Arbitrum链示例
python3.10 -m get_txhash_info.main 0x2731c76d799c9a273d0e27080238abafe938a412fba17fefee99b44c7e4c458c --chain arb

# TRON链示例
python3.10 -m get_txhash_info.main ebe919f390ef6c9b4c4cd045cf3345d11c121add63cb6ea7d71f9962c23c997e --chain tron

# SOL链示例
python3.10 -m get_txhash_info.main 4FugSL5i5HbDHZJ8373X57jcAU67WR759GzyMmfiSyxKJAcfCanibmr538xdw37NoDPgZyQr62LYi3ig1KfNv8Ah --chain sol
```

#### 批量查询

创建一个文件 `tx_hashes.txt`，每行一个交易哈希：

```
0xe698fb3ff8ec46b1ee0b10cbf4795c8267e7f8fb38ea1b63012c5448852b215a
0xf6d1a22ce906dfc67710000ee83341c349345fce89b380bc3955292948a572b9
```

然后运行：

```bash
python3.10 -m get_txhash_info.main dummy --chain bsc --batch tx_hashes.txt
```

### 3. 使用TxHashAudit类（推荐）

```python
from get_txhash_info.main import TxHashAudit

audit = TxHashAudit()

# 获取单笔交易地址
result = audit.get_tx_addresses("0x...", chain="bsc")

# 获取完整信息
full_info = audit.get_tx_full_info("0x...", chain="eth")

# 批量获取
tx_hashes = ["0x...", "0x..."]
results = audit.batch_get_tx_addresses(tx_hashes, chain="bsc")

# 关闭连接
audit.close()
```

## 支持的链

- **BSC (Binance Smart Chain)**: `chain="bsc"`
- **ETH (Ethereum)**: `chain="eth"`
- **BTC (Bitcoin)**: `chain="btc"`
- **BASE**: `chain="base"`
- **ARB (Arbitrum)**: `chain="arb"`
- **TRON**: `chain="tron"`
- **OP (Optimism)**: `chain="op"`
- **Polygon**: `chain="polygon"`
- **ETC (Ethereum Classic)**: `chain="etc"`
- **BCH (Bitcoin Cash)**: `chain="bch"`

## 数据模型

### TransactionInfo

```python
@dataclass
class TransactionInfo:
    chain: ChainType           # 链类型
    tx_hash: str               # 交易哈希
    from_address: str          # 发送地址
    to_address: Optional[str]  # 接收地址（合约创建时为None）
    value: str                 # 交易金额（wei，字符串格式）
    gas: str                   # gas使用量
    gas_price: str             # gas价格
    block_number: int          # 区块号
    timestamp: Optional[int]   # 时间戳
    status: Optional[str]      # 状态（success/failed）
```

## 配置

默认使用公共RPC节点：

- **BSC**: `https://bsc-dataseed1.binance.org`
- **ETH**: `https://eth.llamarpc.com`

如需使用自定义RPC节点，可以修改 `chain_config.py` 中的配置。

## 注意事项

1. 网络连接：需要稳定的网络连接访问区块链RPC节点
2. 交易状态：pending状态的交易可能无法获取完整信息
3. 合约创建：合约创建交易的`to_address`为`None`
4. RPC限制：公共RPC节点可能有速率限制，建议使用自己的节点或API服务

## 故障排除

### 连接失败

- 检查网络连接
- 确认RPC节点URL是否正确
- 尝试使用其他RPC节点

### 交易未找到

- 确认交易哈希是否正确
- 确认交易是否在指定链上
- 检查交易是否已确认（pending交易可能查询不到）

### 性能问题

- 批量查询时建议添加延迟
- 考虑使用自己的RPC节点
- 使用异步方式处理大量交易

## 示例

运行示例代码：

```bash
python3.10 get_txhash_info/example_usage.py
```
