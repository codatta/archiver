# phase3_yolo_audit（Phase 3 AI审核）

本阶段负责对视频画面做 AI 审核，当前为“实时抽帧 + Vision Engine API”模式。

## 核心行为

- 输入：`submission_id`、`video_path`、数据库行信息
- 处理：实时抽样抽帧 -> 调用 `/tasks/detect-persons` -> 聚合为视频级指标
- 输出：`yolo_audit`（含 `overall_result/reason/confidence/video_type` 等）

## 输入来源优先级

当 `PHASE3_YOLO_ENABLED=1` 时，风险与指标按以下优先级获取：

1. `row.yolo_risk_score`（若上游已给定）
2. `PHASE3_YOLO_CALL_API=1` 时实时抽帧并调用 API（主路径）
3. `row.yolo_result_json`（本地 JSON）
4. fallback：`{PRE_FRAME_OUTPUT_DIR}/{submission_id}/latest_yolo_result.json`

## 主要指标

- `both_hands_confidence`：双手出现占比
- `object_interaction_confidence`：手-物体交互占比（保留观测，不再硬门槛）
- `first_person_confidence`：第一视角置信度（空间规则 + 手部区域占比 + 时间连续性 + 前景辅助）
- `video_type` / `video_type_confidence`：视频类型与置信度

额外输出（用于分析）：

- `yolo_video_type` / `yolo_video_type_confidence`（YOLO原始类型判断）
- `source`（结果来源链路）

## 视频类型判定规则（当前业务版）

优先使用业务任务映射类型（主判定）：

- `10398675743500103337` -> `Kitchen Cooking`
- `10399444893000104677` -> `Home Cleaning`
- `10399440080300104655` -> `Household Tidying`

冲突处理：

- 若 YOLO 类型与任务映射类型不一致，且 YOLO 置信度 `>= PHASE3_TYPE_MISMATCH_REVIEW_CONFIDENCE`（默认 `0.80`），进入人工审核 `A/PENDING`
- 否则以任务映射类型为准继续判定

## 通过规则（S）

当前版本下，S 级主要依赖：

- `both_hands_confidence` 达标
- 第一视角达标（若 `PHASE3_REQUIRE_FIRST_PERSON=1`）
- `video_type != Unknown`
- 不触发“高置信类型冲突人工审核”

说明：对象交互已从硬门槛中移除，仅作为观测字段保留。

## 关键配置

- API/抽帧：
  - `PHASE3_YOLO_CALL_API`
  - `PHASE3_YOLO_API_URL`
  - `PHASE3_REALTIME_SAMPLE_FRAMES`
  - `PHASE3_YOLO_API_MAX_FRAMES`
- 第一视角：
  - `PHASE3_FIRST_PERSON_MIN_CONFIDENCE`
  - `PHASE3_FIRST_PERSON_AREA_TARGET`
  - `PHASE3_FIRST_PERSON_AREA_MIN`
  - `PHASE3_FIRST_PERSON_FOREGROUND_WEIGHT`
  - `PHASE3_FIRST_PERSON_TEMPORAL_WINDOW`
  - `PHASE3_FIRST_PERSON_TEMPORAL_BONUS_MAX`
  - `PHASE3_REQUIRE_FIRST_PERSON`
- 类型冲突审核：
  - `PHASE3_TYPE_MISMATCH_REVIEW_CONFIDENCE`

