# 家务视频审核系统（Home Activity Video Audit）

本项目是面向 Web3 DApp 任务场景的视频审核流水线，目标是把 `PENDING` 视频从数据库拉取后，按固定阶段进行自动审核，并将结果回写数据库与产出审计 JSON。

当前支持三类任务模板：

- `Kitchen Cooking`
- `Home Cleaning`
- `Household Tidying`

系统设计原则：

- **分阶段可解释**：每一阶段有明确输入/输出与等级影响。
- **规则可配置**：核心阈值通过 `.env` 管理，便于快速调参。
- **模型可解耦**：YOLO 推理通过 Vision Engine API 调用，审核编排不绑定具体模型实现。
- **支持批量**：一次运行可处理多条视频，逐条产出结构化结果。

## 1. 审核架构

完整执行链路：

1. `main.py` 加载 `.env`（强覆盖）并从数据库拉取待审数据
2. `main_audit/video_auditor.py` 对每条记录执行 Phase0 -> Phase1 -> Phase2 -> Phase3
3. `db_client.py` 回写 `status/result/audit_grade` 等字段
4. 输出 `output/comprehensive_audit_results.json` 与 `output/rating_results.json`

阶段定义：

- **Phase0 重复检测**：基于 `data_submission.video.hash` 做批次内 + 数据库历史重复判定
- **Phase1 元数据检测**：分辨率、时长、横竖屏
- **Phase2 剪辑点检测**：`scenedetect` 计算切点数量
- **Phase3 AI 检测（YOLO）**：实时抽帧 + Vision Engine 推理，输出双手、第一视角、视频类型等指标

## 2. Phase3 当前业务规则（重要）

当前版本已按业务诉求调整：

- 默认对当前视频**实时抽帧**后调用 YOLO API，不依赖预抽帧结果
- “明确处理对象”指标仅保留为观测字段，不再作为强门槛
- 视频类型优先使用 `task_id` 映射（业务主判定）：
  - `10398675743500103337` -> `Kitchen Cooking`
  - `10399444893000104677` -> `Home Cleaning`
  - `10399440080300104655` -> `Household Tidying`
- 若 YOLO 类型与任务映射类型冲突，且 YOLO 类型置信度高于 `PHASE3_TYPE_MISMATCH_REVIEW_CONFIDENCE`（默认 `0.80`），则进入人工审核 `A/PENDING`
- 第一视角由多特征融合：
  - 手部空间分布规则（下半区/上下分布）
  - 双手区域占比
  - 时间连续性加分
  - 前景占比辅助分

## 3. 目录说明

```text
home activity video audit/
├── README.md
├── main.py
├── db_client.py
├── env.sample
├── requirements.txt
├── video_common/
├── phase0_duplicate_check/
├── phase1_metadata_check/
├── phase2_scene_cut_check/
├── phase3_yolo_audit/
├── phase_pre_frames/
├── main_audit/
└── output/
```

关键模块职责：

- `main.py`：CLI 入口、参数解析、环境加载、结果落盘
- `db_client.py`：数据库查询/回写、容错回写策略
- `main_audit/video_auditor.py`：阶段编排、下载/清理临时视频
- `main_audit/output_builder.py`：构建综合与评级输出 JSON
- `phase3_yolo_audit/yolo_auditor.py`：实时抽帧、YOLO API 调用、AI规则映射

## 4. 快速启动

### 4.1 环境准备

1. 复制配置：
   - `copy env.sample .env`（Windows）
2. 安装依赖：
   - `pip install -r requirements.txt`
3. 确保可用：
   - Python 3.10+
   - `ffmpeg` / `ffprobe`
   - Vision Engine 服务（默认 `http://127.0.0.1:8001`）
   - MySQL 可连通

### 4.2 核心配置

至少确认以下变量：

- `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME`
- `DB_PENDING_VIDEOS_SQL`（返回 `submission_id` + `data_submission`，建议包含 `gmt_create`）
- `DB_VIDEO_META_TABLE`（或 `DB_HASH_CHECK_TABLE`）用于 Phase0 历史 hash 去重
- `PHASE3_YOLO_ENABLED=1`
- `PHASE3_YOLO_CALL_API=1`
- `PHASE3_YOLO_API_URL=http://127.0.0.1:8001`
- `PHASE3_TYPE_MISMATCH_REVIEW_CONFIDENCE=0.80`

### 4.3 运行命令

```bash
python main.py --db-limit 20
```

调试单条：

```bash
python main.py --db-limit 1
```

## 5. 输出文件说明

- `output/comprehensive_audit_results.json`
  - 每条视频的完整阶段输出（包含各阶段详情与 `yolo_audit` 指标）
- `output/rating_results.json`
  - 业务侧友好汇总（`audit_grade/result/status/reason/checks`）

等级与状态映射：

- `S` -> `ADOPT`, `result=5`
- `A` -> `PENDING`, `result=4`
- `B/C/D` -> `REFUSED`, `result=3/2/1`

## 6. 常见优化入口

- 调整第一视角灵敏度：`.env` 中 `PHASE3_FIRST_PERSON_*`
- 调整冲突进人工阈值：`PHASE3_TYPE_MISMATCH_REVIEW_CONFIDENCE`
- 调整抽样帧数：`PHASE3_REALTIME_SAMPLE_FRAMES`
- 调整剪辑点阈值：`PHASE2_MAX_CUTS`
- 调整输出文案：`main_audit/output_builder.py`

## 7. 常见问题

- **Q: YOLO 类型置信度高但错分怎么办？**  
  A: 业务类型以 `task_id` 映射为主，YOLO 类型作为冲突信号；高置信冲突进入人工审核。

- **Q: 为什么状态是 `PENDING` 不是 `REFUSED`？**  
  A: `A` 级定义为人工复核待处理，不是拒绝。

- **Q: 大视频会不会占满磁盘？**  
  A: 审核使用临时下载和临时抽帧目录，流程末尾会自动清理。
