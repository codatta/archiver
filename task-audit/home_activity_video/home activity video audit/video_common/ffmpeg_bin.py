"""Resolve ffmpeg/ffprobe executable paths robustly on Windows."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def _env_exe(name: str) -> str:
    key = "FFPROBE_EXE" if name == "ffprobe" else "FFMPEG_EXE"
    return str(os.getenv(key, "")).strip()


def _env_bin_dir() -> str:
    return str(os.getenv("FFMPEG_BIN_DIR", "")).strip()


def _candidate_from_winget(name: str) -> str:
    local = os.getenv("LOCALAPPDATA", "")
    if not local:
        return ""
    root = Path(local) / "Microsoft" / "WinGet" / "Packages"
    if not root.exists():
        return ""
    # Match installed ffmpeg package directories.
    for pkg_dir in root.glob("BtbN.FFmpeg.GPL_*"):
        for build_dir in pkg_dir.glob("ffmpeg-*"):
            exe = build_dir / "bin" / f"{name}.exe"
            if exe.exists():
                return str(exe)
    return ""


def resolve_fftool(name: str) -> str:
    """Return executable path for 'ffmpeg' or 'ffprobe'."""
    if name not in {"ffmpeg", "ffprobe"}:
        raise ValueError(f"Unsupported ff tool: {name}")

    by_name = shutil.which(name)
    if by_name:
        return by_name

    by_env_exe = _env_exe(name)
    if by_env_exe and Path(by_env_exe).exists():
        return by_env_exe

    bin_dir = _env_bin_dir()
    if bin_dir:
        exe = Path(bin_dir) / f"{name}.exe"
        if exe.exists():
            return str(exe)

    by_winget = _candidate_from_winget(name)
    if by_winget:
        return by_winget

    return name

