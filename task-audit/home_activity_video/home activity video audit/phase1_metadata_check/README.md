# phase1_metadata_check — Phase 1 元数据校验（C 级）

在 **Phase 0 已通过** 后执行：用 ffprobe 已解析的 **宽、高、时长** 做硬规则校验；不通过则 **C 级** 并跳过 Phase 2。

## 核心文件

| 文件 | 说明 |
|------|------|
| `metadata_auditor.py` | `run_metadata_check(...)`：分辨率 / 时长 / 横屏三项 `checks` |

## 当前阈值（修改入口）

均在 `metadata_auditor.py` 内：

| 规则 | 条件 |
|------|------|
| 分辨率 | `width >= 1920` 且 `height >= 1080` |
| 时长 | `duration_sec >= 600.0` |
| 横屏 | `width > height` |

## 与编排器的关系

- **不负责** 调用 `ffprobe`：`main_audit/video_auditor.py` 先调 `video_common.ffprobe_utils`，再把数值传入本阶段  
- 失败时 `db_update` 中含 `lightweight_hash`、`phash_hex`（来自 Phase 0）、`audit_grade=C`、`task_id`，由编排器写库  

## 依赖

- 无额外 Python 包（纯数值逻辑）
