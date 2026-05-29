raw_data 目录说明
=================

`raw_data` 目录用于存放所有「原始输入数据」，是整个审核流程的起点。

### 1. 文件说明

- `submissions.json`
  - 主入口数据文件，记录用户报送的所有案件 / 线索
  - 每一条记录通常包含：
    - 基础信息：`submission_id`、`exchange_name`、`network`、`type`（deposit / withdrawal）等
    - 交易信息：`tx_hash`、`from_address`、`to_address`、`date`、`token`、`amount`
    - outgoing 信息（主要用于 deposit）：
      - `has_outgoing_transaction`
      - `outgoing_transaction_hash`
      - `outgoing_tx_from_address`
      - `outgoing_tx_to_address`
    - 截图链接：
      - `exchange_ui_screenshot_url`
      - `explorer_screenshot_url`
      - `outgoing_transaction_screenshot_url`
      - `outgoing_tx_screenshot_url`
  - 被以下模块消费：
    - `audit_exchange_ui`：用于 UI 截图与文字信息审核
    - `get_txhash_info`：根据其中的 `network`、`tx_hash` 等字段去链上抓取交易详情
    - `audit_txhash`：对比链上真实数据与报送数据
    - `main_audit`：统一编排与综合结果聚合

- `submissions copy.json`
  - 作为备份或中间版本存在，不参与正式流程
  - 建议保留原始导出格式，避免被后续脚本修改

### 2. 使用约定

- 原则上，所有审核和转换脚本都应只「读取」该目录，不在此写入结果  
- 若需要生成中间结果或缓存文件，请放在 `output/` 下对应子目录中  
- 更新 `submissions.json` 后，通常需要重新运行：
  - `get_txhash_info`（如新增链或大量新 tx_hash）
  - `audit_exchange_ui`
  - `audit_txhash`
  - `main_audit`（生成新的综合审核与评级结果）
  - `deliver_results`（重新生成交付 CSV）

