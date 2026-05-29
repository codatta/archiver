#!/bin/bash

GIT_REPO="git@github.com:codatta/labeling-vision-engine.git"
GIT_BRANCH="main"
PROJECT_DIR="/opt/labeling-vision-engine"
CONDA_DIR="/opt/miniconda"
CONDA_ENV="vision"
SERVICE_NAME="labeling-vision-engine"

set -e

log_info() { echo -e "\033[0;32m[INFO]\033[0m $1"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $1"; }

# 1. 安装 Miniconda（如果未安装）
if [ ! -d "$CONDA_DIR" ]; then
    log_info "安装 Miniconda..."
    curl -L https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o /tmp/miniconda.sh
    bash /tmp/miniconda.sh -b -u -p "$CONDA_DIR"
    rm /tmp/miniconda.sh
fi

# 初始化 conda
export PATH="$CONDA_DIR/bin:$PATH"
source "$CONDA_DIR/etc/profile.d/conda.sh"

# 写入配置文件，使用 conda-forge 避免 Anaconda ToS 限制
cat > ~/.condarc << 'CONDARC'
channels:
  - conda-forge
channel_priority: strict
show_channel_urls: true
always_yes: true
CONDARC

# 2. 创建 conda 环境（如果不存在）
if ! conda env list | grep -q "^$CONDA_ENV "; then
    log_info "创建 Python 3.10 环境..."
    conda create -y -n "$CONDA_ENV" python=3.10 --override-channels -c conda-forge
fi

conda activate "$CONDA_ENV"

# 3. 安装 PyTorch CUDA
log_info "安装 PyTorch CUDA..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# 4. 拉取代码
log_info "拉取代码（分支: $GIT_BRANCH）..."
if [ ! -d "$PROJECT_DIR/.git" ]; then
    git clone -b "$GIT_BRANCH" "$GIT_REPO" "$PROJECT_DIR"
else
    cd "$PROJECT_DIR"
    git fetch origin
    git checkout "$GIT_BRANCH"
    git pull origin "$GIT_BRANCH"
fi

# 5. 安装项目依赖
log_info "安装项目依赖..."
cd "$PROJECT_DIR"
pip install -r requirements.txt
# ultralytics 会把 opencv-python（需要 X11）作为依赖装进来，在无头服务器上会崩溃
# 强制替换为 headless 版本
log_info "修复 opencv headless..."
pip uninstall opencv-python -y 2>/dev/null || true
pip install opencv-python-headless==4.10.0.84 --force-reinstall -q

# 6. 创建启动脚本
log_info "创建启动脚本..."
cat > "$PROJECT_DIR/start.sh" << 'EOF'
#!/bin/bash
export PATH="/opt/miniconda/bin:$PATH"
source /opt/miniconda/etc/profile.d/conda.sh
conda activate vision
cd /opt/labeling-vision-engine
exec uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1
EOF

chmod +x "$PROJECT_DIR/start.sh"
mkdir -p "$PROJECT_DIR/models" "/tmp/labeling-vision-engine"

# 7. 创建 systemd 服务
log_info "创建 systemd 服务..."
sudo tee "/etc/systemd/system/$SERVICE_NAME.service" > /dev/null << EOF
[Unit]
Description=Labeling Vision Engine GPU Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$CONDA_DIR/envs/$CONDA_ENV/bin:$CONDA_DIR/bin:/usr/bin"
Environment="CUDA_VISIBLE_DEVICES=0"
Environment="TEMP_DIR=/tmp/labeling-vision-engine"
ExecStart=$PROJECT_DIR/start.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 8. 启动服务
log_info "启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

sleep 3
if curl -s http://localhost:8001/health > /dev/null; then
    log_info "✅ 服务启动成功！"
    curl http://localhost:8001/health
else
    log_warn "❌ 请检查日志: sudo journalctl -u $SERVICE_NAME -f"
    exit 1
fi