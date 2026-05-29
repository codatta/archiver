#!/bin/bash
export PATH="/opt/miniconda/bin:$PATH"
source /opt/miniconda/etc/profile.d/conda.sh
conda activate vision
cd /opt/labeling-vision-engine
exec uvicorn main:app --host 0.0.0.0 --port 8001 --workers 1
