# Labeling Vision Engine

视觉算法引擎（无状态）— 视频/序列帧分析、YOLO/Pose 人体检测、光流运动分析。

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

## 说明

- 接收源文件 → 分析 → 返回 JSON 结果 → 清理临时文件
- 不持久化任何数据
- YOLO 模型文件会自动下载到 `models/` 目录
