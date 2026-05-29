# phase2_scene_cut_check — Phase 2 剪辑点扫描（B 级）

在 **Phase 0、1 均已通过** 后执行：用 **PySceneDetect** 检测内容切换，切点过多则 **B 级**。

## 核心文件

| 文件 | 说明 |
|------|------|
| `scene_cut_auditor.py` | `count_scene_cuts`：`ContentDetector` 跑全片；`run_scene_cut_check`：与阈值比较并组装 `scene_cut_audit` |

## 规则说明

- **检测器**：`ContentDetector(threshold=27.0)`（阈值可通过 `run_scene_cut_check(..., detector_threshold=...)` 调整）  
- **切点数**：`cut_count = max(0, len(scene_list) - 1)`（场景段数 N → 中间切点 N−1）  
- **拦截条件**：`cut_count > max_cuts`，其中 `max_cuts` 来自环境变量 `PHASE2_MAX_CUTS`（默认 `30`；即 **cut_count ≥ 31** 失败为 B 级）

## 与编排器的关系

- 仅依赖本地 `video_path`；由 `main_audit/video_auditor.py` 在元数据通过后调用  
- 通过时 `db_update` 内带 `Pending_AI` 及 `cut_count` 等，由编排器调用 `db_client.update_video_status`  
- **工具链失败**（未安装 opencv、视频无法解码等）：返回 `audit_grade=Error`，编排器不写 B 级

## 修改指引

- **更敏感/更迟钝**：调 `detector_threshold`（官方文档：阈值越低切点越多）  
- **允许更多剪辑**：调 `run_scene_cut_check` 的 `max_cuts` 参数（在 `main_audit/video_auditor.py` 调用处改）

## 依赖

- `scenedetect`、`opencv-python-headless`（或带 OpenCV 的环境）
