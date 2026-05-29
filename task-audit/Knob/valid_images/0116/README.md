# 图片审核系统

用于审核 `旋钮_交付.csv` 中的 `annotated_image` 图片。

## 功能特点

- 显示待审核的图片
- 通过/拒绝按钮
- 键盘快捷键支持（1/Enter 通过，0/Space 拒绝）
- 实时统计信息
- 自动记录审核结果
- 已审核的图片不会重复显示

## 使用方法

1. 安装依赖：
```bash
pip3.10 install Flask
```

2. 启动服务：
```bash
cd /Users/sky/WorkProject/Knob/valid_images/0116
python3.10 app.py
```

3. 访问页面：
打开浏览器访问 `http://127.0.0.1:5002`

## 自定义端口

```bash
python3.10 app.py --port 5003
```

## 审核结果

审核结果保存在 `result/review_results.csv` 文件中，包含以下字段：
- `submission_id`: 提交ID
- `review_result`: 审核结果（1=通过，0=拒绝）
- `review_time`: 审核时间

## 快捷键

- `1` 或 `Enter`: 通过
- `0` 或 `Space`: 拒绝
