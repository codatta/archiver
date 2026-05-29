# phase0_duplicate_check（Phase 0 重复检测）

本阶段是阻断式第一关：命中重复直接给 `D`，后续阶段不再执行。

## 当前规则

1. 批次内重复（`video_hash_batch_match`）
   - 使用 `data_submission.data.video.hash`
   - 在当前导入批次内查同 hash 的其他 `submission_id`
   - 命中 -> `D`

2. 数据库历史 hash 命中检测（`video_hash_history_match`）
   - 默认启用（无需全局开关）
   - 优先执行 `PHASE0_DB_HASH_EXISTS_SQL`
   - 若未配置该 SQL，则使用默认查询：
     - 目标表：`DB_HASH_CHECK_TABLE`（若未配置则回退 `DB_VIDEO_META_TABLE`）
     - 字段：`JSON_EXTRACT(data_submission, '$.data.video.hash')`
   - 命中 -> `D`，阻断后续流程并回写数据库

## 可配项

- `DB_HASH_CHECK_TABLE`
- `PHASE0_DB_HASH_EXISTS_SQL`
  - 可用占位符：`{video_hash}`、`{submission_id}`、`{task_id}`
  - 返回任意一行即视为历史重复命中

## 与编排器关系

- 由 `main_audit/video_auditor.py` 调用 `run_duplicate_check(...)`
- 若 `stop=True`，编排器直接结束该条视频并回写数据库
