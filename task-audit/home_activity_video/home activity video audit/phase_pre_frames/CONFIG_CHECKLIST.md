# 前置抽帧配置清单（.env）

下面是建议上线前必须确认的配置项。默认值已写入 `env.sample`。

## A. 基础开关与目录

- `PRE_FRAME_ENABLED`
  - `1` 启用 / `0` 关闭
- `PRE_FRAME_OUTPUT_DIR`
  - 抽帧输出目录（建议 `output/pre_frames`）
- `PRE_FRAME_ARCHIVE_DIR`
  - 归档输出目录（建议 `output/pre_frames_archive`）

## B. 抽帧与压缩参数

- `PRE_FRAME_FPS`
  - 默认 `15`
- `PRE_FRAME_MAX_SIDE`
  - 默认 `640`（长边）
- `PRE_FRAME_IMAGE_FORMAT`
  - `jpg`（推荐）/ `png`
- `PRE_FRAME_JPEG_QSCALE`
  - 默认 `4`（2~5 常用）
- `PRE_FRAME_KEEP_ASPECT`
  - `1` 保持比例，避免拉伸失真
- `PRE_FRAME_MAX_FRAMES_PER_VIDEO`
  - 默认 `0` 不限；建议生产设置硬上限防极端长视频

## C. 清理与归档

- `PRE_FRAME_CLEANUP_MODE`
  - `none` / `ttl` / `keep_last_n` / `hybrid`
- `PRE_FRAME_RETENTION_HOURS`
  - TTL 保留时长（默认 72）
- `PRE_FRAME_KEEP_LAST_N_BATCHES`
  - 每个 submission 保留批次数（默认 2）
- `PRE_FRAME_ARCHIVE_BEFORE_DELETE`
  - `1` 先归档再删源文件
- `PRE_FRAME_ARCHIVE_TASK_IDS`（可选）
  - 需长期保留任务白名单（逗号分隔）

## D. 输出形式说明

- 当前建议：**本地文件输出**
  - 图片：`*.jpg`
  - 清单：`manifest.json`
- 若要 URL：在后置上传服务中读取 manifest 后上传对象存储并回填 URL

## E. 服务器上线前检查

- [ ] `ffmpeg` 可用（`ffmpeg -version`）
- [ ] 输出目录有写权限
- [ ] 磁盘容量满足峰值估算（至少 3~7 天）
- [ ] 清理策略已启用（建议 `hybrid`）
- [ ] 归档目录与备份策略已确认
- [ ] 监控已配置（磁盘占用、抽帧失败率、处理耗时）
