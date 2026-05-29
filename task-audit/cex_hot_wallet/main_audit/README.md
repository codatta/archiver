# 综合审核模块

整合 `audit_exchange_ui`（交易所界面审核）和 `audit_txhash`（交易哈希审核）两个审核模块，提供统一的审核入口和评级功能。

## 功能特性

1. **综合审核流程**：
   - 遍历 `cex_hot_wallet/raw_data/submissions.json` 中的所有数据
   - 首先调用 `audit_exchange_ui` 进行交易所界面审核
   - 然后调用 `audit_txhash` 进行交易哈希审核

2. **审核结果记录**：
   - 将综合审核结果保存到 `output/main_audit` 目录下
   - 包含 UI 审核结果和交易哈希审核结果

3. **增量处理**：
   - 支持增量处理，已处理的记录自动跳过
   - 每处理一条记录立即保存，支持断点续传

4. **评级计算**：
   - 根据综合审核结果计算每条数据的最终评级（1-5分）
   - 评级规则详见下方说明

## 项目结构

```
cex_hot_wallet/
├── main_audit/
│   ├── __init__.py          # 模块初始化
│   ├── main_auditor.py      # 综合审核器主入口
│   ├── rating.py            # 评级计算模块
│   └── README.md           # 本文档
├── audit_exchange_ui/       # 交易所界面审核模块
├── audit_txhash/            # 交易哈希审核模块
└── raw_data/                # 原始数据目录
```

## 使用方法

### 综合审核

#### 基本用法

```bash
cd cex_hot_wallet
python3.10 -m main_audit.main_auditor
```

#### 指定参数

```bash
python3.10 -m main_audit.main_auditor \
  --submissions raw_data/submissions.json \
  --output output/main_audit/comprehensive_audit_results.json \
  --api-key YOUR_QWEN_API_KEY
```

#### 参数说明

- `--submissions`: submissions.json 文件路径（默认: `raw_data/submissions.json`）
- `--output`: 输出结果文件路径（默认: `output/main_audit/comprehensive_audit_results.json`）
- `--api-key`: Qwen API密钥（可选，优先使用环境变量）
- `--base-url`: Qwen API基础URL（可选，优先使用环境变量）

### 评级计算

#### 基本用法

```bash
cd cex_hot_wallet
python3.10 -m main_audit.rating
```

#### 指定参数

```bash
python3.10 -m main_audit.rating \
  --comprehensive-results output/main_audit/comprehensive_audit_results.json \
  --output output/main_audit/rating_results.json
```

#### 参数说明

- `--comprehensive-results`: 综合审核结果文件路径（默认: `output/main_audit/comprehensive_audit_results.json`）
- `--output`: 输出评级结果文件路径（默认: `output/main_audit/rating_results.json`）

## 评级规则

根据综合审核结果，每条记录会被评为 1-5 分：

评级模块 `main_audit/rating.py` 根据综合审核结果中的各检查项，对每条 submission 打 1–5 分，规则如下：

| 条件 | 得分 |
|------|------|
| `is_exchange_record` 不通过 | 1 分 |
| `exchange_verification` 不通过 | 2 分 |
| 仅有 `transaction_date_match` 不通过，其余检查项均通过 | 4 分 |
| 全部检查项通过 | 5 分 |
| 其他情况 | 3 分 |

其中「不通过」指该检查项结果为 `false` 或等效未通过；「通过」指结果为 `true` 或等效通过。评分理由由 `_generate_rating_reason()` 根据上述规则生成简要说明。


## 输出结果格式

### 综合审核结果 (`output/main_audit/comprehensive_audit_results.json`)

```json
{
  "result": "success",
  "timestamp": "2026-01-27T15:16:31.874527",
  "summary": {
    "total": 10,
    "success": 8,
    "with_errors": 2
  },
  "audit_results": [
    {
      "submission_id": "2026011505290000108860",
      "timestamp": "2026-01-27T15:16:31.874527",
      "ui_audit": {
        "submission_id": "2026011505290000108860",
        "overall_result": "pass",
        "checks": [...]
      },
      "txhash_audit": {
        "submission_id": "2026011505290000108860",
        "result": "pass",
        "checks": [...]
      },
      "errors": []
    }
  ]
}
```

### 评级结果 (`output/main_audit/rating_results.json`)

```json
{
  "result": "success",
  "timestamp": "2026-01-27T15:16:31.874527",
  "summary": {
    "total": 10,
    "rating_distribution": {
      "1": 0,
      "2": 1,
      "3": 2,
      "4": 3,
      "5": 4
    }
  },
  "rated_results": [
    {
      "submission_id": "2026011505290000108860",
      "type": "deposit",
      "rating": 4,
      "reason": "UI审核全部通过，但交易哈希审核不通过: main_tx_to_address_match, outgoing_tx_to_address_match",
      "checks": {
        "ui_audit": {
          "is_exchange_record": "pass",
          "exchange_verification": "pass",
          "transaction_date_match": "pass",
          "transaction_info_match": "pass"
        },
        "txhash_audit": {
          "has_outgoing_transaction_field": "pass",
          "main_tx_from_address_match": "pass",
          "main_tx_to_address_match": "fail",
          "main_tx_date_match": "pass",
          "to_address_equals_outgoing_from_address": "pass",
          "outgoing_tx_from_address_match": "pass",
          "outgoing_tx_to_address_match": "fail"
        }
      }
    }
  ]
}
```

**输出格式说明：**
- `submission_id`: 提交ID
- `type`: 交易类型（"deposit" 或 "withdraw"）
- `rating`: 评级分数（1-5）
- `reason`: 简短的理由说明
- `checks`: 各模块检查项结果汇总
  - `ui_audit`: UI审核检查项结果
  - `txhash_audit`: 交易哈希审核检查项结果

## 工作流程

### 完整流程

1. **综合审核**
   ```bash
   python3.10 -m main_audit.main_auditor
   ```
   - 读取 `raw_data/submissions.json`
   - 执行 UI 审核和交易哈希审核
   - 输出结果到 `output/main_audit/comprehensive_audit_results.json`

2. **评级计算**
   ```bash
   python3.10 -m main_audit.rating
   ```
   - 读取综合审核结果
   - 计算每条记录的评级
   - 输出结果到 `output/main_audit/rating_results.json`

## 注意事项

1. **增量处理**：综合审核支持增量处理，已处理的记录会自动跳过
2. **评级依赖**：评级计算需要先完成综合审核
3. **结果文件**：所有结果文件保存在 `output/main_audit/` 目录下
