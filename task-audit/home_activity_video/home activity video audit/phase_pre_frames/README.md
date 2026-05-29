# phase_pre_frames — 前置抽帧（YOLO 输入准备）

本阶段位于 Phase 0/1/2 之前，目标是把视频转成可直接喂给 YOLO 的图片批次，并生成结构化清单（manifest）。

## 目标（基于当前约束）

- GPU 推理充裕：单图约 2ms，可采用高密度抽帧
- 抽帧频率：`15 FPS`
- 压缩尺寸：长边压缩到 `640px`（保留纵横比）
- 输出形态：**本地文件**（图片 + `manifest.json`），不是 URL

## 推荐输出结构

```text
output/pre_frames/
  └── {submission_id}/
      └── {batch_ts}/
          ├── frames/
          │   ├── {submission_id}_{ms}.jpg
          │   └── ...
          ├── manifest.json
          └── summary.json
```

> 说明：`batch_ts` 便于同一视频多次重跑留痕与回滚。

## manifest 建议字段

- `submission_id`
- `video_path`
- `extract_fps`（默认 15）
- `resize_max_side`（默认 640）
- `image_format`（默认 jpg）
- `total_frames`
- `frames[]`
  - `frame_id`
  - `timestamp_sec`
  - `timestamp_ms`
  - `file_path`（本地绝对或相对路径）
  - `width` / `height`
  - `sha256`（可选）

## 建议执行流程

1. 读取 DB 待审视频列表
2. 先建输出目录与 batch 子目录
3. 调 ffmpeg 按 15fps 抽帧并压缩到 640
4. 扫描输出目录生成 manifest
5. （可选）触发 YOLO 批处理
6. 根据清理策略删除或归档历史抽帧批次

## 清理与保留策略（推荐）

- 默认模式：`hybrid`
  - TTL：仅保留最近 72 小时
  - 同时每个 submission 保留最近 2 个批次
- 对重点任务：支持“先归档再删除源文件”
- 归档目录建议：`output/pre_frames_archive/`

## 与现有流水线的衔接方式

- 方案 A（推荐）：在 `main.py` 中 Phase 0 前调用 `pre_frame_runner.run(...)`
- 方案 B：拆成独立脚本（如 `pre_frames_main.py`）由调度系统先执行

## 注意事项

- 抽帧是磁盘 I/O 密集，不是内存密集；重点监控磁盘占用和 inode 数
- Windows/ Linux 路径差异需在 manifest 里统一（建议都用 POSIX 相对路径）
- 若后续要转 URL，建议由独立上传服务读取 manifest 后回写 URL 字段
