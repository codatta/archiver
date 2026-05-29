## OTC 截图审核评级模块（`otc_rating`）

本目录负责 **OTC 截图审核的评级阶段（rating）**：读取识别阶段产物 `otc_audit_results.json`，再从数据库拉取每条 `submission_id` 对应的 `data_submission` 作为“真值”，按规则给出 1~5 分，并将结果写回数据库。

## 目录结构

- `OTC/otc_rating/main.py`
  - 评级入口（命令行可直接运行）
  - 负责：读取识别结果 → 拉 DB 真值 → 评分 → 写回 DB → 输出评级快照

## 输入与输出

### 输入

- **识别结果文件**：`OTC/output/otc_audit/otc_audit_results.json`
  - 由 `python -m OTC.main_from_db` 生成
  - 关键字段（每条）：
    - `submission_id`
    - `image_quality.clear/tampered/text_readable`
    - `extracted.chain/address/entities/labels/website_link/txid/screenshot_link/trace_type`
    - `extensions`

- **数据库真值**（MySQL 表 `cfp_task_submission`）
  - 通过 `OTC/.env` 中的 `DB_*` 连接
  - 通过 `DB_SUBMISSIONS_SQL` 拉取（至少需要返回 `submission_id` 与 `data_submission`；可选 `user_id`）
  - 真值字段来自 `data_submission.data`（或 `data_submission` 本身）：`chain`、`address`、`otcDesk`、`hash`
  - **去重**：可选配置 `DB_ADOPTED_SUBMISSIONS_SQL`，用于拉取本任务内已采纳（status=ADOPT）记录，构建 txid/address 已占用集合；未配置则仅做当次批次内去重

### 输出

- **数据库写回**：
  - `cfp_task_submission.status`：`REFUSED` / `ADOPT`
  - `cfp_task_submission.result`：1~5

- **文件写回**：
  - 覆盖写回 `OTC/output/otc_audit/otc_audit_results.json`
  - 当判定通过（5分）时：回填 `extracted.txid = data_submission.hash`

- **评级快照文件**（每次运行生成一个）：
  - `OTC/output/output_rating/rating_results_YYYYMMDD_HHMMSS.json`

## 评级规则（运行原理）

代码实现位于 `OTC/otc_rating/main.py`，整体是“短路式”规则：任何一步失败立即 REFUSED 并写回对应 result。**规则 1 优先级最高**，最先执行。

1. **【最高优先级】txid/address 重复 → REFUSED, result=1**
   - 同一任务（task）内，任意 user_id 下已采纳过的 `txid`（即 `data_submission.hash`）或 `address` 不得再次通过。
   - 先加载 DB 中已采纳记录（`DB_ADOPTED_SUBMISSIONS_SQL`）与当批已通过记录，构建“已占用”集合；若当前条目的 txid 或 address 已在集合中，则 **status=REFUSED, result=1**，原因栏写入：`txid/address已被提交过`。
   - 若未配置 `DB_ADOPTED_SUBMISSIONS_SQL`，仅做当次运行批次内去重。

2. **图片质量不满足 → REFUSED, result=1**
   - `image_quality.clear is True`
   - `image_quality.tampered is False`
   - `image_quality.text_readable is True`

3. **关键字段缺失 → REFUSED, result=2/3**
   - 检查 `extracted` 的 4 个字段：`chain/address/entities/labels`
   - 缺失判定：`None` / `""` / `[]`
   - 缺失 ≥ 2 个 → `result=2`
   - 缺失 = 1 个 → `result=3`
     - 若缺失 `address`：追加原因 `Address missing`
     - 若缺失 `entities` 或 `labels`：追加原因 `Unknown identity`

4. **与 DB 真值不一致 → REFUSED, result=4**
   - `data_submission.chain` 会先映射到统一链枚举（`_normalize_chain_enum`），再与 `extracted.chain` 比较
   - `address` 大小写不敏感比较
   - `labels` 与 `data_submission.otcDesk` 比较（同样大小写不敏感）
   - 任意不一致 → `result=4` 并记录 mismatch 原因

5. **hash 不合法/缺失 → REFUSED, result=4**
   - 当字段一致后，再校验 `data_submission.hash`
   - 当前为格式校验（64 位 hex 或带 `0x` 前缀）
   - 不合法也归入 `result=4`（按你的要求）

6. **全部通过 → ADOPT, result=5 + 回填 txid**
   - 字段一致且 hash 合法：
     - 写回 `extracted.txid = data_submission.hash`
     - DB 写回：`status=ADOPT, result=5`

> 说明：目前 `entities` 不做“与 DB 真值严格比对”，仅参与缺失判断（后续如需要可扩展）。

## 使用方法

### 1）前置：准备识别结果

先跑识别阶段生成/更新 `otc_audit_results.json`：

```bash
cd d:\codatta\task-audit-main
python -m OTC.main_from_db
```

### 2）单独执行评级

```bash
cd d:\codatta\task-audit-main
python -m OTC.otc_rating.main
```

指定识别结果路径：

```bash
python -m OTC.otc_rating.main --results "d:\codatta\task-audit-main\OTC\output\otc_audit\otc_audit_results.json"
```

### 3）一键执行（识别 + 评级）

```bash
cd d:\codatta\task-audit-main
python -m OTC.run_all
```

`OTC.run_all` 默认会执行 3 步：

1. 识别：生成/更新 `OTC/output/otc_audit/otc_audit_results.json`
2. 评级：写回 DB，并输出 `OTC/output/output_rating/rating_results_*.json`
3. 交付：基于最新 `rating_results_*.json` 生成交付 CSV：
   - `OTC/output/delivery/otc_delivery_rating5.csv`（仅 5 分）
   - `OTC/output/delivery/otc_delivery_rating4.csv`（仅 4 分）

## 输出示例

### 1）`rating_results_*.json`

示例结构如下（节选）：

```json
{
  "generated_at": "2026-03-18T17:08:44.464947",
  "source_results_file": "D:\\codatta\\task-audit-main\\OTC\\output\\otc_audit\\otc_audit_results.json",
  "count": 12,
  "rows": [
    {
      "submission_id": "2026031303351400103139",
      "status": "REFUSED",
      "result": 1,
      "passed": false,
      "reasons": ["txid/address已被提交过"]
    },
    {
      "submission_id": "2026031303371700103140",
      "status": "REFUSED",
      "result": 1,
      "passed": false,
      "reasons": ["Image quality mismatch", "clear=False, tampered=False, text_readable=False"]
    }
  ]
}
```

### 2）与交付 CSV 的衔接（4分/5分拆分导出）

评分完成后（本地已有 `rating_results_*.json`），可生成交付 CSV：

```bash
python d:\codatta\task-audit-main\OTC\generate_delivery_csv.py --split-4-5
```

输出：

- `OTC/output/delivery/otc_delivery_rating5.csv`（仅 5 分）
- `OTC/output/delivery/otc_delivery_rating4.csv`（仅 4 分）

## 常见问题（排查）

### 1）MySQL 连接超时（家庭网络常见）

如果你看到类似：`Can't connect to MySQL server ... (timed out)`，说明不是账号密码问题，而是 **网络无法到达 DB**（路由/安全组/VPC/运营商链路等）。

建议排查顺序：

- **确认 RDS 外网地址/端口**是否开启并允许访问（通常 3306）
- **确认白名单是你当前出口公网 IP**（家庭宽带可能变化）
- 若 DB 仅允许内网/VPC：需要 **跳板机/堡垒机/SSH 隧道/VPN** 才能访问

### 2）`DB row not found for submission_id`

说明你的 `DB_SUBMISSIONS_SQL` 没有覆盖到当前 `otc_audit_results.json` 里这些 `submission_id`（筛选条件不一致）。请让 SQL 能返回这些 submission。