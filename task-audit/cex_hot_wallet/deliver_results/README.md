deliver_results 模块说明
=========================

`deliver_results` 负责把审核与评级结果，转换为对外交付用的 CSV 文件。

> 注意：面向最终客户的字段含义说明文档在  
> `output/deliver_results/README.md`，  
> 当前这个 README 主要面向开发者，解释代码结构与数据流。

### 1. 核心文件

- `csv_generator.py`
  - 输入：
    - `output/main_audit/rating_results.json`（按 submission 的最终评级结果）
    - `output/main_audit/comprehensive_audit_results.json`（包含 `detected_date` 等细节）
  - 处理流程概览：
    1. 读取所有评级结果，仅保留评分为 **4 分** 或 **5 分** 的记录
    2. 按照评分拆分成两类：
       - 5 分 → `delivery_results_rating_5.csv`
       - 4 分 → `delivery_results_rating_4.csv`
    3. 结合综合审核结果：
       - 优先使用 `detected_date` 作为日期（格式 `YYYY-MM-DD`），无则回退到原始报送日期
       - 从原始 submission 中抽取 `chain` / `address` / `entities` / `token` / `amount` 等字段
       - 为 `deposit` / `withdrawal` 分别构造 `deposit_address` / `withdraw_address`
       - 只保留有 `outgoing_tx_to_address` 的 `deposit` 记录
    4. 将所有截图 URL 汇总为一个 JSON 字符串写入 `screenshot_link` 字段
  - 输出：
    - `output/deliver_results/delivery_results_rating_5.csv`
    - `output/deliver_results/delivery_results_rating_4.csv`

### 2. 主要字段规则（开发视角）

- **筛选规则**
  - 仅接收 `rating in {4, 5}` 的记录
  - `deposit` 类型若缺少 `outgoing_tx_to_address`，整条记录会被丢弃

- **日期来源**
  - 优先：`comprehensive_audit_results.json` 中 UI 审核抽取的 `detected_date`（已归一化为 `YYYY-MM-DD`）
  - 备选：原始 submission 中的 `date`

- **extensions 字段**
  - 永远是一个 JSON 字符串，代码中按字典构造后 `json.dumps`
  - 统一包含：
    - `date` / `token` / `amount` / `submission_id`
    - `deposit_address`（仅 `deposit`）
    - `withdraw_address`（仅 `withdrawal`）

- **screenshot_link 字段**
  - 也是 JSON 字符串，key 与原始字段名保持一致：
    - `exchange_ui_screenshot_url`
    - `explorer_screenshot_url`
    - `outgoing_transaction_screenshot_url`
    - `outgoing_tx_screenshot_url`

### 3. 运行方式（示意）

通常通过命令行运行，例如：

```bash
cd cex_hot_wallet
python -m deliver_results.csv_generator \
  --rating-results-path output/main_audit/rating_results.json \
  --comprehensive-results-path output/main_audit/comprehensive_audit_results.json \
  --output-dir output/deliver_results
```

在实际项目中已内置好默认路径，一般只需在仓库根目录按约定命令执行即可。

"""
交付 CSV 文件说明（给客户）
===========================

本说明文档仅针对以下两个交付文件，方便直接对接使用（两者唯一区别在于最终评级分数不同）：

- `delivery_results_rating_5.csv`：最终评级为 **5 分** 的高置信度记录  
  - 含义：所有审核子项均通过，且 **交易时间在最近 30 天内** 的记录  
  - 建议用途：可作为「高置信度、可直接投产使用」的地址列表
- `delivery_results_rating_4.csv`：最终评级为 **4 分** 的高置信度记录  
  - 含义：除 **交易日期** 外，其余审核子项均满足要求，且 **交易日期距离当前时间超过 30 天**  
  - 建议用途：推荐作为「历史交易时间较久，但整体证据完备」的高置信度地址，适合作为人工复核 / 辅助参考

两份文件的列结构完全一致，仅记录的置信度不同。

一、字段说明
------------

每一行代表一个被标注为「CEX 热钱包」的区块链地址，字段含义如下：

1. `chain`
   - 区块链网络的标准化标识（枚举值），例如：
     - `bitcoin_mainnet`
     - `ethereum_mainnet`
     - `bnb_chain_mainnet`
     - `polygon_mainnet`
     - `solana`
     - `tron_mainnet`

2. `address`
   - 被标注的区块链地址，即 CEX 热钱包地址。
   - 对于提现 (`trace_type = "withdrawal"`): 交易所对外转出的 **发送地址**。
   - 对于入金 (`trace_type = "deposit"`): outgoing 交易中，资金最终流入的 **交易所热钱包地址**。

3. `entities`
   - 交易所名称，例如：`Binance`、`OKX`。

4. `labels`
   - 固定值：`Exchange Hot Wallet, CEX`。
   - 表示该地址被标注为中心化交易所的热钱包地址。

5. `source_type`
   - 固定值：`ground_truth`。
   - 表示标签基于截图 + 链上验证后的「事实数据」，而非启发式推断。

6. `website_link`
   - 目前为空，预留字段，如需可填交易所官网链接。

7. `description`
   - 目前为空，预留字段，可用于自由文本描述。

8. `provider`
   - 固定值：`Codatta`。
   - 数据提供方标识。

9. `provider_source`
   - 固定值：`User Report`。
   - 表示原始线索来自用户报送，后续经过审核与验证。

10. `screenshot_link`
    - 字符串形式的 JSON，对应多种截图 URL，key 含义如下：
      - `exchange_ui_screenshot_url`:
        - 交易所前端界面的截图链接
        - 一般是「充值记录 / 提现记录 / 资金流水」页面，用于证明账号侧确实存在该笔记录
      - `explorer_screenshot_url`:
        - 区块链浏览器上，`exchange_ui_screenshot_url` 中这笔交易的 **交易详情页截图**
        - 展示 txid、from/to 地址、金额、时间等链上字段
      - `outgoing_transaction_screenshot_url`（仅 deposit 场景）:
        - 在区块链浏览器上，证明「用户入金地址存在有效转出记录」的截图
        - 一般是地址交易列表或某一条转出记录的列表视图
      - `outgoing_tx_screenshot_url`（仅 deposit 场景）:
        - 来自区块链浏览器，`outgoing_transaction_screenshot_url` 所指那条「有效转出记录」对应的 **交易详情页截图**
    - 示例（为便于阅读，此处使用格式化 JSON）：
      ```json
      {
        "exchange_ui_screenshot_url": "https://file.example.com/ui.png",
        "explorer_screenshot_url": "https://file.example.com/explorer_tx.png",
        "outgoing_transaction_screenshot_url": "https://file.example.com/outgoing_list.png",
        "outgoing_tx_screenshot_url": "https://file.example.com/outgoing_tx.png"
      }
      ```

11. `txid`
    - 区块链上的交易哈希（transaction hash），与截图和链上验证对应。

12. `trace_type`
    - 交易类型：
      - `deposit`：用户向交易所入金
      - `withdrawal`：交易所向外部地址提现

13. `extensions`
    - 字符串形式的 JSON，包含便于使用的补充字段：
      - `date`：审核后确认的交易日期，优先为标准化格式 `YYYY-MM-DD`
      - `token`：资产符号，如 `BTC`、`ETH`、`USDT`、`SOL`
      - `amount`：交易金额（字符串，与证据中保持一致）
      - `submission_id`：内部用的案件 / 提交 ID
      - `deposit_address`（仅 `trace_type = "deposit"` 时存在）：
        - 入金交易中的 **接收地址**（用户 → 交易所）
      - `withdraw_address`（仅 `trace_type = "withdrawal"` 时存在）：
        - 提现交易中的 **目标地址**（交易所 → 外部地址）

    - 示例（withdrawal）：
      ```json
      {
        "date": "2026-01-24",
        "token": "SOL",
        "amount": "0.046",
        "submission_id": "2026012401201500100588",
        "withdraw_address": "97fbDxtZSepnY8LYBbvndyF1acuuCopKgcFu7yND91SM"
      }
      ```

    - 示例（deposit）：
      ```json
      {
        "date": "2026-01-05",
        "token": "BTC",
        "amount": "0.00080342",
        "submission_id": "2026011901313900109575",
        "deposit_address": "151oeNRvVrn4stssbK4pR8DV6XmBB7Vtan"
      }
      ```

二、简单示例
------------

以 `delivery_results_rating_4.csv` 中的一条记录为例（格式化后）：

```text
chain: bitcoin_mainnet
address: bc1qgzrva028eym96uax90j28qj3aqhh3dy8gk6qvp
entities: Binance
labels: Exchange Hot Wallet, CEX
source_type: ground_truth
website_link:
description:
provider: Codatta
provider_source: User Report
screenshot_link:
{
  "explorer_screenshot_url": "https://file.b18a.io/162384258547712_705481_.png",
  "exchange_ui_screenshot_url": "https://file.b18a.io/162384258547712_974381_.png",
  "outgoing_tx_screenshot_url": "https://file.b18a.io/162384258547712_903326_.png",
  "outgoing_transaction_screenshot_url": "https://file.b18a.io/162384258547712_704976_.png"
}
txid: 60612bf54991651ce8bc31a310bf2405675c31df963c4545b2ffe237ef10bd64
trace_type: deposit
extensions:
{
  "date": "2026-01-05",
  "token": "BTC",
  "amount": "0.00080342",
  "submission_id": "2026011901313900109575",
  "deposit_address": "151oeNRvVrn4stssbK4pR8DV6XmBB7Vtan"
}
```

根据上述字段含义，你可以在无需了解任何代码实现的前提下，直接解析并使用这两份 CSV 文件。
"""
