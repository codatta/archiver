audit_txhash 模块说明
======================

`audit_txhash` 负责基于链上交易哈希，对用户报送的数据进行「链上核验」。

### 1. 核心文件

- `txhash_auditor.py`  
  - 从 `raw_data/submissions.json` 读取结构化报送数据（由 `main_audit` 统一驱动）  
  - 调用 `get_txhash_info` 模块，根据不同链类型获取交易详情（from、to、时间等）  
  - 按照 `audit_check_config.json` 中的配置，对每条记录逐项执行审核：
    - **withdrawal 场景**
      - 校验 `tx_hash` 的 `from` / `to` 地址
      - 校验交易日期
      - 校验 `receiver_address` 与 `address` 是否一致
    - **deposit 场景**
      - 校验入金 `tx_hash` 的 `from` / `to` 地址与日期
      - 当 `has_outgoing_transaction = true` 时：
        - 校验 `outgoing_transaction_hash` 的 `from` / `to` 地址
        - 校验 `to_address` 与 `outgoing_tx_from_address` 一致性
      - `has_outgoing_transaction` 本身也是一个独立审核项，必须为 `true` 才能通过
  - 输出结构化审核结果（按 submission 维度记录各个 check 的 `expected` / `actual` / `result` / `errors`），供 `main_audit` 汇总使用

### 2. 使用方式

- 本模块通常不会单独运行，而是由 `main_audit/main_auditor.py` 统一调度：  
  1. 先执行 `audit_exchange_ui`（截图 + 文本信息审核）  
  2. 再执行 `audit_txhash`（链上哈希审核）  
  3. 将结果写入 `output/main_audit/comprehensive_audit_results.json`

### 3. 设计要点

- 所有审核项的元信息（名称、含义、实现位置等）统一维护在 `cex_hot_wallet/audit_check_config.json` 中，便于扩展和统一展示  
- 审核逻辑尽量保持「幂等」：同一条 submission 多次审核，结果应一致  
- 对 BTC / SOL / TRON 等多地址或特殊结构的链做了专门适配，保证 from/to 提取的正确性

