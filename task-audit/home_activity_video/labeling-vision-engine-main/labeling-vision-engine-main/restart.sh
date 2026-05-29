#!/bin/bash

SERVICE_NAME="labeling-vision-engine"
PROJECT_DIR="/opt/labeling-vision-engine"
GIT_BRANCH="main"

echo "========================================"
echo "重启 Labeling Vision Engine 服务"
echo "========================================"

# 可选：拉取最新代码
read -p "是否拉取最新代码? (y/n): " update_code
if [ "$update_code" = "y" ]; then
    echo "拉取最新代码..."
    cd "$PROJECT_DIR"
    git fetch origin
    git checkout "$GIT_BRANCH"
    git pull origin "$GIT_BRANCH"
    echo "代码更新完成"
fi

# 重启服务
echo "正在重启服务..."
sudo systemctl restart "$SERVICE_NAME"

sleep 3

# 检查状态
if systemctl is-active --quiet "$SERVICE_NAME"; then
    echo "✅ 服务重启成功"
    echo "健康检查:"
    curl -s http://localhost:8001/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:8001/health
else
    echo "❌ 服务启动失败，查看日志："
    sudo journalctl -u "$SERVICE_NAME" -n 20 --no-pager
    exit 1
fi