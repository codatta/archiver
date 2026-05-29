# OTC 输出目录说明（`OTC/output/`）

本目录存放 OTC 流水线的**所有产物**，包括识别结果、评级快照、交付 CSV。

## 目录结构

- `OTC/output/otc_audit/`
  - **识别阶段产物**（Qwen 视觉识别结果）
  - 典型文件：
    - `otc_audit_results.json`

- `OTC/output/output_rating/`
  - **评级阶段产物**（每次运行都会生成一份快照）
  - 典型文件：
    - `rating_results_YYYYMMDD_HHMMSS.json`

- `OTC/output/delivery/`
  - **交付产物**（按评分拆分的 CSV）
  - 典型文件：
    - `otc_delivery_rating5.csv`（仅收录 5 分数据）
    - `otc_delivery_rating4.csv`（仅收录 4 分数据）

## 产物生成方式（命令）

### 一键执行（识别 + 评级 + 交付）

在仓库根目录运行：

```bash
cd d:\codatta\task-audit-main
python -m OTC.run_all
```

会依次生成/更新：

- `OTC/output/otc_audit/otc_audit_results.json`
- `OTC/output/output_rating/rating_results_*.json`
- `OTC/output/delivery/otc_delivery_rating5.csv`
- `OTC/output/delivery/otc_delivery_rating4.csv`

### 分步执行

- 识别阶段：

```bash
python -m OTC.main_from_db
```

- 评级阶段：

```bash
python -m OTC.otc_rating.main
```

- 交付 CSV（从最新 `rating_results_*.json` 拆分 4/5 分）：

```bash
python d:\codatta\task-audit-main\OTC\generate_delivery_csv.py --split-4-5
```

## 文件字段概览

### 1）`otc_audit_results.json`

每条记录至少包含：

- `submission_id`
- `image_quality`：`clear/tampered/text_readable/notes`
- `extracted`：`chain/address/entities/labels/website_link/txid/screenshot_link/trace_type`
- `extensions`：扩展字段（如 `phone/country/city/fiat/token` 等）

### 2）`rating_results_*.json`

每条记录包含：

- `submission_id`
- `status`：`REFUSED` / `ADOPT`
- `result`：1~5
- `reasons`：拒绝原因（数组），例如：
  - 重复拦截：`["txid/address已被提交过"]`
  - 图片质量：`["Image quality mismatch", "clear=..., tampered=..., text_readable=..."]`
  - 关键字段缺失：`["Key fields missing >=2: ..."]` 或 `["Key field missing: address", "Address missing"]`
  - 字段不匹配：`["chain mismatch: ...", "address mismatch"]`、`["Invalid hash format"]`

### 3）交付 CSV（`otc_delivery_rating4.csv` / `otc_delivery_rating5.csv`）

字段固定为：

`chain,address,entities,labels,source_type,website_link,provider,provider_source,screenshot_link,txid,trace_type,extensions`

其中：

- `source_type=ground_truth`
- `provider=codatta`
- `provider_source=osint`

