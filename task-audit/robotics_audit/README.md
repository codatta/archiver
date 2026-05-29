# ROBSTIC001 机器人标注批量审核系统

面向 Codatta `ROBSTIC001` frontier 的自动化审核流水线。从 MySQL 拉取 `PENDING` 提交，逐条审核，输出 JSON / CSV 报告。**默认只读库、不写库**。

---

## 目录

1. [系统定位与设计原则](#1-系统定位与设计原则)
2. [支持的任务类型](#2-支持的任务类型)
3. [整体架构](#3-整体架构)
4. [审核流水线详解](#4-审核流水线详解)
5. [视频、帧序号与参考 JSON](#5-视频帧序号与参考-json)
6. [项目结构](#6-项目结构)
7. [环境配置](#7-环境配置)
8. [安装与启动](#8-安装与启动)
9. [命令行参数](#9-命令行参数)
10. [输出说明](#10-输出说明)
11. [等级体系](#11-等级体系)
12. [规则配置](#12-规则配置)
13. [成本模型](#13-成本模型)
14. [测试](#14-测试)
15. [辅助脚本](#15-辅助脚本)
16. [常见问题](#16-常见问题)
17. [设计决策 FAQ（为什么这样设计）](#17-设计决策-faq为什么这样设计)

---

## 1. 系统定位与设计原则

### 做什么

对 `ROBSTIC001` frontier 下用户提交的机器人视频标注数据进行批量质检，自动给出等级（S/A/B/C/D），并输出可追踪的驳回原因。

### 不做什么

- **不使用** `cfp_frontier_task.data_requirements` 作为标准答案（该字段不是 ground truth）
- **默认不写回** 数据库（需显式开启）
- **不替代** 人工终审，目标是拦截明显乱填和低质量提交，减轻人工负担

### 核心设计原则

| 原则 | 说明 |
|------|------|
| **先规则、后模型** | 明显乱填/格式错误用零 API 成本的纯规则拦截 |
| **视频为准** | 语义参考来自视觉大模型分析 GIF，不是数据库里的 requirements |
| **task 级缓存** | 同一 `task_id` 视觉分析只做一次，所有 submission 共用 |
| **硬/软分流** | 硬违规直接驳回；不确定项交给大模型结合视频参考裁定 |
| **宽松语义** | 默认「偏差不大即通过」，同义词、合并分段、帧号偏差均可接受 |
| **帧序号对齐** | 000001 任务的 start/end 是**帧号**（1/N），不是秒 |

---

## 2. 支持的任务类型

同一 `frontier_id` 下有两种 template，通过 `template_id` 自动路由：

| template_id | 任务类型 | 用户提交结构 |
|-------------|----------|--------------|
| `ROBOTICS_TPL_000001` | 视频时序分段 + 描述 | `data: [{ start, end, des }]` |
| `ROBOTICS_TPL_000003` | 结构化元数据标注 | `data: { objects, environment, agent_type, view, relations, task }` |

---

## 3. 整体架构

```
main.py
  └── AuditPipeline（编排）
        ├── AuditRouter（按 template_id 分发）
        │     ├── SegmentAuditor（000001 分段）
        │     └── MetadataAuditor（000003 元数据）
        │
        ├── TaskReferenceManager（task 级视频参考）
        │     ├── TaskInfoLoader（查库拿 gif_resource）
        │     ├── TaskReferenceGenerator（qwen-vl-max 视觉分析）
        │     └── TaskReferenceStore（磁盘缓存 JSON）
        │
        └── LLMTextValidator（qwen-plus 文本语义比对）
```

### 数据流

```
MySQL cfp_task_submission (PENDING)
        │
        ▼
┌─────────────────────────────────────────┐
│ Phase 1：前置纯规则（零 API 成本）        │
│  - 硬违规 → 直接驳回，不调 API           │
│  - 软疑点 → 放行给 Phase 2              │
└─────────────────────────────────────────┘
        │
        ▼（--enable-llm-text-check）
┌─────────────────────────────────────────┐
│ Phase 2a：视觉参考（每个 task_id 一次）   │
│  下载 GIF → 抽帧 → qwen-vl-max → 缓存   │
└─────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────┐
│ Phase 2b：文本语义比对（每条一次）        │
│  用户提交 vs 视频参考 JSON → qwen-plus   │
└─────────────────────────────────────────┘
        │
        ▼
output/audit_results.json + audit_results.csv
```

---

## 4. 审核流水线详解

### Phase 1：前置纯规则

**目标**：零成本拦截明显不合格数据。

#### 000001 分段任务检查项

- 时间为空、`end <= start`、时间重叠、超出视频帧数上限
- 占位符时间（如 `1-1` 且描述为空）
- 描述为空、过短、乱填（`fsfs`、`aaa`）
- 英文描述是否像有效语句（动词 + 对象，非 gibberish）
- 四要素检测（主体/动作/对象/结果），含**中英文词表**
- 段数、重复段、完全相同描述

#### 000003 元数据任务检查项

- `objects` / `task` / `environment` / `view` / `agent_type` / `relations` 必填
- 枚举合法性（environment、view、armCount 等）
- 乱填检测

#### 硬/软违规分流（phase_gate）

配置在 `audit_config.json` / `audit_config.metadata.json` 的 `phase_gate` 字段：

| 类型 | 行为 | 示例 |
|------|------|------|
| **hard_reject_codes** | 直接驳回，不进大模型 | 时间重叠、乱填、空描述 |
| **llm_defer_codes** | 放行给大模型裁定 | 四要素不足、描述略短 |

实现见 `robotics_audit/common/phase_gate.py`。

### Phase 2：视觉参考 + 文本语义比对

启用 `--enable-llm-text-check` 时：

1. **批次开始前**：收集本批所有唯一 `task_id`，逐个生成/加载视频参考 JSON
2. **每条 submission**：
   - 若 Phase 1 硬违规 → 跳过
   - 否则取该 `task_id` 的参考 JSON，调用文本大模型比对

#### 宽松语义模式（LLM_LENIENT_MODE=1，默认开启）

- **默认通过（S）**
- 仅当明显乱填或与视频场景**完全无关**时才 D
- 以下差异**不驳回**：cup/bottle 同义词、分段合并、帧号偏差、措辞差异

---

## 5. 视频、帧序号与参考 JSON

### 网页播放器「1/N」是什么

提交页面左下角 `1/83` 表示：**当前第 1 帧 / 共 83 帧**，不是秒。

- 用户填写的 `start` / `end` 是 **1-based 帧序号**
- 每个 GIF 帧数**不同**（83、120、45…），系统动态探测，不假定固定值

### 视频 URL 怎么拼

```
{TASK_MEDIA_BASE_URL}/{frontier_id}/{gif_resource}
```

示例：

```
https://codatta-frontier-resource.oss-ap-southeast-1.aliyuncs.com/ROBSTIC001/task-pick_water_50_4_7th_gifs_episode-44.gif
```

`gif_resource` 来自 `cfp_frontier_task.data_display.gif_resource`，通过 `task_id` 查库获得。

### 抽帧策略

| 步骤 | 说明 |
|------|------|
| 探测元数据 | 读取 GIF 总帧数 `frame_count`、时长 `duration_sec` |
| 采样间隔 | 000001：**3 帧/秒**；000003：**1 帧/秒**（可分别配置） |
| 环境变量 | `TASK_MEDIA_FRAMES_PER_SECOND_SEGMENT=3`、`TASK_MEDIA_FRAMES_PER_SECOND_METADATA=1` |
| 采样上限 | `TASK_MEDIA_MAX_FRAMES=0` 表示不封顶，按间隔采满 |
| 大 GIF 处理 | 超 8MB 跳 OSS 压缩，本地下载 + Pillow 抽帧 |
| 送视觉模型 | **全部抽帧结果**，不设张数上限（十几秒视频通常 ≤50 张） |

### 参考 JSON 缓存路径

```
output/task_reference/{frontier_id}/{template_id}/{task_id}.json
```

示例结构：

```json
{
  "task_id": "6459383089000101956",
  "source": "llm_vision",
  "model": "qwen-vl-max",
  "media_url": "https://.../ROBSTIC001/task-pick_water_....gif",
  "media_meta": {
    "frame_count": 83,
    "duration_sec": 16.6,
    "time_unit": "frame",
    "index_base": 1
  },
  "reference": {
    "time_unit": "frame",
    "segments": [
      { "start": 1, "end": 15, "description": "robot arm picks up the cup" }
    ],
    "visible_objects": ["water dispenser", "cup", "robot arm"],
    "actions": ["pick up", "place under", "put back"],
    "environment": "Indoor"
  }
}
```

**同一 `task_id` 下所有 submission 共用此 JSON，视觉 API 只调用一次。**

---

## 6. 项目结构

```
robotics audit/
├── main.py                          # CLI 入口
├── db_client.py                     # MySQL 读写
├── audit_config.json                # 000001 分段规则 + 英文词表 + phase_gate
├── audit_config.metadata.json       # 000003 元数据规则 + phase_gate
├── requirements.txt
├── .env                             # 环境变量（勿提交密钥）
├── env.sample                       # 环境变量模板
│
├── robotics_audit/
│   ├── pipeline.py                  # 两阶段编排、硬/软分流、LLM 调用
│   ├── router.py                    # 按 template_id 路由
│   ├── models.py                    # 数据模型、等级映射
│   ├── llm_text_validator.py        # 文本语义比对（宽松模式）
│   │
│   ├── common/
│   │   ├── phase_gate.py            # 硬/软违规分流
│   │   ├── description_utils.py     # 英文句子/乱填判断
│   │   ├── text_utils.py            # 乱填检测、token 重叠
│   │   └── row_utils.py             # 解析 submission 字段
│   │
│   ├── segment/                     # ROBOTICS_TPL_000001
│   │   ├── auditor.py
│   │   ├── parser.py                # 解析 start/end/des
│   │   ├── rules.py                 # 时间、四要素、乱填规则
│   │   └── reference_match.py       # 本地 token 对照（可选）
│   │
│   ├── metadata/                    # ROBOTICS_TPL_000003
│   │   ├── auditor.py
│   │   ├── parser.py
│   │   ├── rules.py
│   │   └── reference_match.py
│   │
│   └── task_reference/              # 视频参考生成与缓存
│       ├── loader.py                # 查库、拼 media_url
│       ├── manager.py               # get_or_create、批次预热
│       ├── generator.py             # qwen-vl-max 视觉分析
│       ├── store.py                 # 磁盘 JSON 读写
│       ├── media_compress.py        # GIF 抽帧、probe 帧数
│       └── media_download.py        # 下载、重试、大文件处理
│
├── sample_data/
│   └── submissions_sample.json      # 本地测试样本
│
├── tests/
│   ├── test_auditor.py
│   ├── test_media_url.py
│   ├── test_phase_and_description.py
│   └── test_lenient_validator.py
│
├── scripts/                         # 诊断工具
│   ├── diagnose_db.py
│   ├── inspect_task_fields.py
│   └── probe_media_url.py
│
└── output/                          # 运行产物（gitignore 建议）
    ├── audit_results.json
    ├── audit_results.csv
    └── task_reference/
```

---

## 7. 环境配置

复制 `env.sample` 为 `.env` 并填写：

```env
# Qwen API
QWEN_API_KEY=
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
QWEN_TEXT_MODEL=qwen-plus
QWEN_VL_MODEL=qwen-vl-max

# MySQL
DB_HOST=
DB_PORT=3306
DB_USER=
DB_PASSWORD=
DB_NAME=

# 拉取 PENDING submission（无需联表 data_requirements）
DB_SUBMISSIONS_SQL=select s.submission_id, s.frontier_id, s.template_id, s.task_id, s.data_submission ->> '$.data' as data_submission, s.user_id from cfp_task_submission s where s.frontier_id in ('ROBSTIC001') and s.status='PENDING' order by s.submission_id

# 视频 URL
TASK_MEDIA_BASE_URL=https://codatta-frontier-resource.oss-ap-southeast-1.aliyuncs.com
DEFAULT_FRONTIER_ID=ROBSTIC001

# 下载与抽帧
TASK_MEDIA_DOWNLOAD_TIMEOUT=300
TASK_MEDIA_DOWNLOAD_RETRIES=3
TASK_MEDIA_LARGE_GIF_BYTES=8388608
TASK_MEDIA_MAX_FRAMES=0              # 0=不封顶，按 FPS 采满
TASK_MEDIA_FRAMES_PER_SECOND=3
TASK_MEDIA_FRAMES_PER_SECOND_SEGMENT=3    # 000001 分段任务
TASK_MEDIA_FRAMES_PER_SECOND_METADATA=1   # 000003 元数据任务
# 送视觉模型：全部抽帧，不设 QWEN_VL_MAX_FRAMES 上限

# 文本语义：1=宽松（默认通过，仅乱填/完全无关才 D）
LLM_LENIENT_MODE=1

# 写库表名（仅 --write-db 时使用）
DB_META_TABLE=cfp_task_submission
DB_CONNECT_TIMEOUT=20
```

---

## 8. 安装与启动

### 安装依赖

```bash
pip install -r requirements.txt
```

依赖：`pymysql`、`python-dotenv`、`requests`、`Pillow`

### 两种推荐运行方式

**方式 1：完整审核 + 不写回数据库（测试/验证用）**

```bash
python main.py --limit 100 --enable-llm-text-check
```

流程：前置规则 → 视觉大模型生成参考 JSON → 大模型文本语义比对 → JSON 参考 token 对比。  
结果仅输出到 `output/audit_results.json` 与 `output/audit_results.csv`。

**方式 2：完整审核 + 写回数据库（正式落库）**

```bash
python main.py --limit 100 --enable-llm-text-check --write-db
```

写回字段（默认 SQL）：

```sql
UPDATE cfp_task_submission SET status = ?, result = ? WHERE submission_id = ?
```

| audit_grade | status | result |
|-------------|--------|--------|
| S | ADOPT | 5 |
| A~D | REFUSED | 4~1 |

### 其他常用命令

```bash
# 仅前置纯规则（零 API 成本，推荐先跑一批看分布）
python main.py --limit 100

# 跳过前面一批，从 offset 开始
python main.py --limit 100 --offset 500 --enable-llm-text-check

# 本地 JSON 样本测试（不连库）
python main.py --input sample_data/submissions_sample.json --enable-llm-text-check

# 完整流程但跳过 JSON token 对比（仅规则 + 视觉 + LLM 文本）
python main.py --limit 100 --enable-llm-text-check --skip-json-reference-check
```

### 重新生成视频参考缓存

若更新了抽帧/帧序号逻辑，需删除旧缓存：

```powershell
# PowerShell：删除某 task 的缓存
Remove-Item "output\task_reference\ROBSTIC001\ROBOTICS_TPL_000001\{task_id}.json"

# 或清空整个 frontier 缓存
Remove-Item -Recurse -Force "output\task_reference\ROBSTIC001"
```

---

## 9. 命令行参数

| 参数 | 说明 |
|------|------|
| `--input` | 本地 JSON 输入（跳过数据库） |
| `--limit` | 最多处理条数 |
| `--offset` | 跳过前 N 条 |
| `--output` | 结果 JSON 路径（默认 `output/audit_results.json`） |
| `--csv` | 摘要 CSV 路径 |
| `--reference-dir` | 视频参考缓存目录 |
| `--enable-llm-text-check` | 完整审核：视觉分析 + LLM 文本 + JSON 参考对比（**推荐**） |
| `--skip-json-reference-check` | 跳过 JSON 参考 token 对比 |
| `--enable-local-reference-check` | 仅规则 + 本地 token 重叠（不含 LLM，不推荐） |
| `--enable-vision-llm` | 仅预热视频参考 JSON，不做文本比对 |
| `--write-db` | 审核后将 status/result 写回数据库 |
| `--segment-config` | 自定义 000001 规则文件路径 |
| `--metadata-config` | 自定义 000003 规则文件路径 |

---

## 10. 输出说明

### audit_results.json

每条 submission 包含：

| 字段 | 说明 |
|------|------|
| `submission_id` | 提交 ID |
| `task_id` | 任务 ID（同 task 共用视频参考） |
| `template_id` | 模板 ID |
| `audit_grade` | 最终等级 S/A/B/C/D |
| `passed` | 是否通过（仅 S 为 true） |
| `status` | `ADOPT` / `REFUSED` |
| `result` | 分数 1~5（S=5, D=1） |
| `rule_phase_grade` | Phase 1 硬规则等级 |
| `reference_check` | 语义校验状态（见下表） |
| `reference_path` | 视频参考 JSON 路径 |
| `violations` | 违规明细（**驳回原因**） |
| `segment_details` | 000001 各段四要素分析 |

**reference_check 取值：**

| 值 | 含义 |
|----|------|
| `skipped_pre_reject` | Phase 1 硬违规，未进语义校验 |
| `skipped` | 未启用语义校验 |
| `rule_soft_pass+vision_ref+llm_text+json_ref_ok` | 前置通过 + 视频参考 + 文本比对 + JSON 对比通过 |
| `rule_soft_pass+vision_ref+llm_text+json_ref_mismatch` | 前置通过 + 视频参考 + 文本比对，但 JSON token 对比未通过 |
| `rule_deferred+vision_ref+llm_text+json_ref_ok` | 前置有软疑点，大模型 + JSON 对比均完成 |
| `vision_missing` | 无法从视频生成参考 |

**violations 单条结构：**

```json
{
  "code": "garbage_description",
  "grade": "D",
  "message": "第 1 段描述疑似乱填: fsfs",
  "segment_index": 0,
  "field": null
}
```

### audit_results.csv

摘要表，含 `violation_summary`（前 5 条违规 message 拼接），便于 Excel 快速浏览。

---

## 11. 等级体系

| 等级 | status | result | 含义 |
|------|--------|--------|------|
| **S** | ADOPT | 5 | 通过 |
| A | REFUSED | 4 | 轻微问题 |
| B | REFUSED | 3 | 中等问题 |
| C | REFUSED | 2 | 较严重 |
| D | REFUSED | 1 | 严重/乱填 |

**规则：任一段/一字段有问题，整单取最严重等级。仅 S 级 `passed=true`。**

---

## 12. 规则配置

### audit_config.json（000001）

- 时间：`end > start`、不允许重叠、不允许占位符
- 描述：乱填检测、英文句子合理性、四要素（含**中英文词表**）
- `phase_gate`：硬/软违规代码列表

### audit_config.metadata.json（000003）

- 必填字段、枚举合法性、乱填检测
- `phase_gate`：硬/软违规代码列表

修改 JSON 即可调规则，无需改代码。

---

## 13. 成本模型

| 环节 | API 调用 | 说明 |
|------|----------|------|
| Phase 1 纯规则 | **0 次** | 本地执行 |
| 视觉参考（qwen-vl-max） | **每个唯一 task_id 1 次** | 结果缓存复用 |
| 文本语义（qwen-plus） | **每条通过硬规则的 submission 1 次** | 乱填在 Phase 1 被拦截则不调用 |

**优化点：**

- 硬违规不调 API
- 同 task_id 视觉分析只一次
- 软疑点才进文本模型

---

## 14. 测试

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

测试覆盖：分段规则、媒体 URL 拼接、英文描述判断、硬/软分流、宽松语义模式。

---

## 15. 辅助脚本

| 脚本 | 用途 |
|------|------|
| `scripts/diagnose_db.py` | 检查 PENDING 数量 |
| `scripts/inspect_task_fields.py` | 查看 task 表字段 |
| `scripts/probe_media_url.py` | 验证 GIF URL 是否可访问 |

---

## 16. 常见问题

**Q: 会从数据库读数据吗？**  
A: 会。默认读 `PENDING` submission；加 `--input` 则用本地 JSON。

**Q: 会写回数据库吗？**  
A: 默认不会。加 `--write-db` 即写库；不加则只输出本地 JSON/CSV。输出 JSON 顶层含 `write_db` 与 `db_write` 汇总。

**Q: data_requirements 是标准答案吗？**  
A: **不是。** 语义参考来自视觉大模型分析 GIF 的结果。

**Q: 同一 task_id 视觉分析几次？**  
A: **一次。** 缓存在 `output/task_reference/`，同 task 所有 submission 共用。

**Q: start/end 是秒还是帧？**  
A: **帧序号（1-based）。** 网页 `1/N` 中 N 是该 GIF 总帧数，每个视频不同。

**Q: 为什么我的合理提交被驳回了？**  
A: 检查是否用了旧缓存（秒制参考）。删除对应 task JSON 重跑；确认 `LLM_LENIENT_MODE=1`。

**Q: 两种 template 会混在一起吗？**  
A: 会一起拉取，`router.py` 按 `template_id` 分发，互不影响。

---

## 17. 设计决策 FAQ（为什么这样设计）

### 为什么不用 data_requirements 做标准答案？

该字段是任务配置/展示用途，不代表视频中实际发生的内容。用户标注应与**视频真实内容**一致，因此用视觉大模型「看一遍视频」生成参考 JSON，再与用户提交比对。

### 为什么要 Phase 1 + Phase 2 两阶段？

- Phase 1 零成本拦截 `fsfs`、`good`、时间重叠等，避免对每条都调 API
- Phase 2 处理需要语义理解的场景（同义词、英文描述、内容是否与视频一致）
- 硬/软分流：规则能确定的直接判，不确定的交给模型

### 为什么 task_id 级缓存视觉结果？

同一 task 的 GIF 相同，100 条 submission 不应调用 100 次视觉 API。缓存后每条只需一次便宜的文本比对。

### 为什么 start/end 用帧号而不是秒？

Codatta 提交页播放器显示 `当前帧/总帧数`，用户按帧标注。若系统按秒理解会产生数量级偏差（如 45 帧 vs 45 秒）。每个 GIF 动态探测 `frame_count`，参考 JSON 的 `media_meta.time_unit=frame`。

### 为什么宽松语义（LLM_LENIENT_MODE）？

标注允许合理措辞差异（cup/bottle、合并分段、时序不精确）。过严会导致正确标注被误杀。默认 S，仅乱填或完全无关才 D。

### 为什么 000001 要中英文词表 + 句子判断？

数据以英文为主。纯中文四要素词表无法覆盖英文描述。补充英文词表 + `is_plausible_description()` 判断是否能组成合理动作句，同时把「四要素不足」设为软疑点交给 LLM。

### 为什么大 GIF 要本地下载抽帧？

部分 GIF 达 10~25MB，OSS 图片处理返回 400，直传视觉模型超大小限制。本地下载 + Pillow 按 3fps 抽帧再上传。

### 为什么默认不写库？

批量审核应先本地验证通过率和误杀率，确认规则稳定后再开启写回，避免污染生产数据。

---

## 快速上手（TL;DR）

```bash
# 1. 配置
cp env.sample .env
# 编辑 .env 填入 DB_* 和 QWEN_API_KEY

# 2. 安装
pip install -r requirements.txt

# 3. 跑一批（推荐）
python main.py --limit 50 --enable-llm-text-check

# 4. 看结果
# output/audit_results.json  — 完整明细 + violations 驳回原因
# output/audit_results.csv   — 摘要
# output/task_reference/       — 每个 task 的视频参考 JSON
```
