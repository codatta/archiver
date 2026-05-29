"""
Device configuration — CPU / GPU mode via environment variable.

Environment variable:
    DEVICE_MODE = "gpu" (default) | "cpu"

GPU mode:
    - YOLO models loaded on CUDA with FP16 half-precision
    - Larger input size (imgsz=640) for better accuracy
    - Requires CUDA-capable PyTorch (see requirements.txt)

CPU mode:
    - YOLO models loaded on CPU with FP32 full-precision
    - Smaller input size (imgsz=320) for speed
    - Install via: pip install -r requirements-cpu.txt
"""

import os
import logging

logger = logging.getLogger(__name__)

DEVICE_MODE = os.environ.get("DEVICE_MODE", "gpu").lower().strip()

# Validate
if DEVICE_MODE not in ("cpu", "gpu"):
    logger.warning("Invalid DEVICE_MODE=%r, falling back to 'gpu'", DEVICE_MODE)
    DEVICE_MODE = "gpu"

# Check CUDA availability when GPU mode is requested
_CUDA_AVAILABLE = False
if DEVICE_MODE == "gpu":
    try:
        import torch
        _CUDA_AVAILABLE = torch.cuda.is_available()
        if not _CUDA_AVAILABLE:
            logger.warning("DEVICE_MODE=gpu but CUDA not available, falling back to CPU")
            DEVICE_MODE = "cpu"
    except ImportError:
        logger.warning("DEVICE_MODE=gpu but torch not installed, falling back to CPU")
        DEVICE_MODE = "cpu"

IS_GPU = DEVICE_MODE == "gpu"

# Inference parameters
DEVICE = "cuda" if IS_GPU else "cpu"
HALF = IS_GPU                        # FP16 on GPU, FP32 on CPU
IMGSZ = 640 if IS_GPU else 320       # GPU: higher res → better accuracy
IMGSZ_POSE = 640 if IS_GPU else 320

# GPU: use yolov8m (medium, more accurate); CPU: yolov8s (small, faster)
DEFAULT_YOLO_MODEL_FOR_DEVICE = "yolov8m.pt" if IS_GPU else "yolov8s.pt"

# torch.compile() speeds up repeated inference on GPU (~10-30%),
# but adds ~30s cold-start compilation time on first use.
# Enable only when running long-lived server processes.
TORCH_COMPILE = IS_GPU and os.environ.get("TORCH_COMPILE", "0") == "1"

logger.info(
    "Device config: mode=%s device=%s half=%s imgsz=%d model=%s compile=%s",
    DEVICE_MODE, DEVICE, HALF, IMGSZ, DEFAULT_YOLO_MODEL_FOR_DEVICE, TORCH_COMPILE,
)
