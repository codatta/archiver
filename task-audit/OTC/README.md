# OTC 审核子系统

本目录实现 **OTC 地址截图审核** 全流程：从数据库读取提交 → Qwen 视觉识别截图 → 自动评级（含 txid/address 去重）→ 写回数据库 → 生成交付 CSV（4 分/5 分拆分）。

代码位置：`OTC/`

## 环境准备

1. 配置 `OTC/.env`：
   - **Qwen**：`QWEN_API_KEY`、`QWEN_BASE_URL`
   - **数据库**：`DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME`
   - **待审核 SQL**：`DB_SUBMISSIONS_SQL`，需返回 `submission_id`、`data_submission`（可选 `user_id` 用于导出）
   - **去重（可选）**：`DB_ADOPTED_SUBMISSIONS_SQL`，拉取本任务内已采纳记录，用于 txid/address 跨 user_id 唯一校验；不配则仅做当次批次内去重
2. 安装依赖：

```bash
pip install -r OTC/requirements.txt
```

### 分步执行（推荐调试时使用）

- **第一阶段：截图识别（Qwen 审核）**

```bash
cd d:\codatta\task-audit-main
python -m OTC.main_from_db
```

输出：`OTC/output/otc_audit/otc_audit_results.json`

- **第二阶段：自动评级 + 写回数据库**

```bash
cd d:\codatta\task-audit-main
python -m OTC.otc_rating.main
```

行为：
- 读取 `otc_audit_results.json` 与数据库中的 `data_submission`
- **最高优先级**：同任务内 txid/address 重复（含跨 user_id）→ REFUSED、result=1，原因 `txid/address已被提交过`
- 再按图片质量、字段缺失、字段匹配、hash 格式给出 1~5 分
- 回写数据库并更新 `otc_audit_results.json` 中的 `txid` 等字段

**评级 result 含义**：1 = 重复或图片质量不通过，2 = 关键字段缺失≥2，3 = 关键字段缺失 1 个，4 = 字段与 DB 不一致或 hash 不合法，5 = 通过。

### 交付 CSV（4分/5分拆分）

评级完成后，可生成交付 CSV（仅收录对应评分的数据）：

```bash
python d:\codatta\task-audit-main\OTC\generate_delivery_csv.py --split-4-5
```

输出：

- `OTC/output/delivery/otc_delivery_rating5.csv`（仅 5 分）
- `OTC/output/delivery/otc_delivery_rating4.csv`（仅 4 分）

### 一键执行（识别 + 评级 + 交付 CSV）

如果你希望从“读取数据库 → Qwen 截图识别 → 自动评级 → 生成交付 CSV”一条龙执行，可以直接在仓库根目录运行：

```bash
cd d:\codatta\task-audit-main
python -m OTC.run_all
```

这会顺序执行：
1. `OTC.main_from_db.main()`：从数据库拉取数据并调用 Qwen 审核截图；
2. `OTC.otc_rating.main.main()`：对审核结果自动评级并写回数据库。
3. `OTC.generate_delivery_csv`：基于最新 `rating_results_*.json` 拆分导出 4分/5分两份交付 CSV。


可选参数（如 DB 不可达时可跳过某步）：

- `--skip-recognition`：跳过识别，复用已有 `otc_audit_results.json`
- `--skip-rating`：跳过评级（不写 DB、不生成新 rating 快照）
- `--skip-delivery`：跳过交付 CSV 生成

## 代码结构

| 路径 | 说明 |
|------|------|
| `main_from_db.py` | 识别入口：从 DB 拉取提交，调用 Qwen 识别，写出 `otc_audit_results.json` |
| `otc_audit/` | 识别层：模型定义、Qwen 审核器（见 `otc_audit/README.md`） |
| `otc_rating/main.py` | 评级入口：读识别结果 + DB 真值，按规则打分并写回 DB（见 `otc_rating/README.md`） |
| `generate_delivery_csv.py` | 交付：按最新 `rating_results_*.json` 生成 4 分/5 分两份 CSV |
| `run_all.py` | 一键入口：识别 → 评级 → 交付 |
| `db_client.py` | DB 连接与拉取（含 `fetch_adopted_submissions` 用于去重） |
| `output/` | 所有产物目录（见 `output/README.md`） |

## 文档索引

- 输出说明：`OTC/output/README.md`
- 识别层：`OTC/otc_audit/README.md`
- 评级层：`OTC/otc_rating/README.md`

