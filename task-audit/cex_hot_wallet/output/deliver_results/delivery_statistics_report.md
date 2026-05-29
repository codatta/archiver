# 交付结果统计报告

**生成时间**: 2026-01-29 10:25:58

---

## 📁 输出文件

本次交付生成了以下文件：

### 主要交付文件

1. **[`delivery_results_rating_5.csv`](./delivery_results_rating_5.csv)** - 5分记录（去重后）
   - 所有审核子项均通过的高置信度记录
   - 建议作为「高置信度、可直接交付需求方使用」的地址列表

2. **[`delivery_results_rating_4.csv`](./delivery_results_rating_4.csv)** - 4分记录（去重后）
   - 除交易日期外，其余审核子项均满足要求
   - 建议作为「历史交易时间较久（超过30天），但整体证据完备」的高置信度地址

3. **[`delivery_results_duplicate.csv`](./delivery_results_duplicate.csv)** - 重复记录
   - 按 `address` 去重时被过滤的重复有效记录
   - 保留 `submission_id` 最小的记录（最早的提交）

### 字段说明文档

📖 **[查看字段含义说明 →](./README.md)**

详细字段说明请参考 `README.md`，包含：
- 各字段的详细含义和取值说明
- 不同交易类型（withdrawal/deposit）的字段差异
- `extensions` JSON 字段的结构说明
- 使用建议和注意事项

---

## 📊 总体统计

| 指标 | 数量 |
|------|------|
| 原始记录总数 | 25 |
| 去重后记录数 | 15 |
| 重复记录数 | 10 |
| 去重率 | 40.0% |

---

## ⭐ 按评分统计

| 评分 | 原始数量 | 去重后数量 | 重复数量 |
|------|---------|-----------|---------|
| 5分 | 24 | 14 | 10 |
| 4分 | 1 | 1 | 0 |

---

## 🔗 按链（Chain）统计

### 去重后记录

| 链 | 数量 |
|----|------|
| bnb_chain_mainnet | 8 |
| polygon_mainnet | 2 |
| solana | 2 |
| ethereum_mainnet | 1 |
| bitcoin_mainnet | 1 |
| base_mainnet | 1 |

### 5分记录

| 链 | 数量 |
|----|------|
| bnb_chain_mainnet | 8 |
| polygon_mainnet | 2 |
| ethereum_mainnet | 1 |
| bitcoin_mainnet | 1 |
| base_mainnet | 1 |
| solana | 1 |

### 4分记录

| 链 | 数量 |
|----|------|
| solana | 1 |

### 重复记录

| 链 | 数量 |
|----|------|
| bnb_chain_mainnet | 7 |
| solana | 1 |
| base_mainnet | 1 |
| polygon_mainnet | 1 |

---

## 📝 按交易类型（Trace Type）统计

### 去重后记录

| 交易类型 | 数量 |
|---------|------|
| withdrawal | 13 |
| deposit | 2 |

### 5分记录

| 交易类型 | 数量 |
|---------|------|
| withdrawal | 12 |
| deposit | 2 |

### 4分记录

| 交易类型 | 数量 |
|---------|------|
| withdrawal | 1 |

### 重复记录

| 交易类型 | 数量 |
|---------|------|
| withdrawal | 6 |
| deposit | 4 |

---

## 🏢 按交易所（Entities）统计

### 去重后记录

| 交易所 | 数量 |
|--------|------|
| Binance | 11 |
| OKX | 3 |
| Gate.io | 1 |

### 5分记录

| 交易所 | 数量 |
|--------|------|
| Binance | 11 |
| OKX | 2 |
| Gate.io | 1 |

### 4分记录

| 交易所 | 数量 |
|--------|------|
| OKX | 1 |

### 重复记录

| 交易所 | 数量 |
|--------|------|
| Binance | 8 |
| OKX | 1 |
| Gate.io | 1 |

---

*报告生成时间: 2026-01-29 10:25:58*