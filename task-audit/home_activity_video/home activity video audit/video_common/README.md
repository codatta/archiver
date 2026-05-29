# video_common — 共用媒体与行解析工具

本目录存放 **各审核阶段复用** 的底层能力，避免在 Phase 0/1/2 中重复实现。

## 文件说明

| 文件 | 职责 |
|------|------|
| `ffprobe_utils.py` | 调用 `ffprobe` 输出 JSON，解析视频流、时长 |
| `frame_extract.py` | `ffmpeg` 按时间戳抽单帧 PNG；`imagehash.phash` 与汉明距离 |
| `row_utils.py` | 从 DB 行解析 `video_path`、`task_id`（兼容多列名） |

## 被谁引用

- `phase0_duplicate_check`：时长用于 lightweight_hash；50% 抽帧做 pHash  
- `phase1_metadata_check`：复用同一次 `ffprobe` 的宽高与时长（由 `main_audit/video_auditor.py` 拉取后传入）  
- `main_audit/video_auditor.py`：统一调用 `ffprobe_json` 与 `row_utils`

## 修改指引

- **更换抽帧策略**（例如不用 50% 而用固定秒数）：改 `frame_extract.compute_phash_midframe`  
- **兼容更多路径列名**：改 `row_utils.resolve_video_path`  
- **ffprobe 参数**（例如增加 `-read_intervals`）：改 `ffprobe_utils.ffprobe_json`

## 依赖

- 系统 `PATH` 中需有 `ffprobe`、`ffmpeg`  
- Python 包：`Pillow`、`ImageHash`（仅 pHash 相关函数需要）
