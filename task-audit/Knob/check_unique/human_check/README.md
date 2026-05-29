# 图片审核系统

简单的Web界面用于审核图片。

## 功能特点

- 展示 `clean_data.csv` 中的图片
- 通过/拒绝按钮进行审核
- 审核后自动显示下一张图片
- 记录审核结果到 `files/review_results.csv`（通过=1，拒绝=0）
- 已审核的图片不再显示

## 安装依赖

```bash
pip3.10 install -r ../requirements.txt
```

## 使用方法

### 启动服务器

```bash
cd check_unique/human_check
python3.10 app.py
```

### 访问审核页面

在浏览器中打开：`http://localhost:5000`

### 操作说明

1. **审核图片**：点击"通过"或"拒绝"按钮
2. **键盘快捷键**：
   - `1` 或 `Enter`：通过
   - `0` 或 `空格`：拒绝
3. **自动跳转**：审核完成后自动加载下一张图片
4. **统计信息**：页面顶部显示审核进度和统计

## 输出文件

审核结果保存在：`check_unique/human_check/result/review_results.csv`

包含以下列：
- `submission_id`: 提交ID
- `review_result`: 审核结果（1=通过，0=拒绝）
- `review_time`: 审核时间

## 注意事项

- 确保 `clean_data.csv` 文件存在
- 图片路径必须正确，否则无法显示
- 审核结果会实时保存，刷新页面不会丢失进度

