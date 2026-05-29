from __future__ import annotations

import os
import time
from typing import Optional

import requests

DEFAULT_TIMEOUT = int(os.getenv("TASK_MEDIA_DOWNLOAD_TIMEOUT", "300"))
DEFAULT_RETRIES = int(os.getenv("TASK_MEDIA_DOWNLOAD_RETRIES", "3"))
LARGE_GIF_BYTES = int(os.getenv("TASK_MEDIA_LARGE_GIF_BYTES", str(8 * 1024 * 1024)))


def probe_content_length(url: str, *, timeout: int = 30) -> Optional[int]:
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            content_length = resp.headers.get("Content-Length")
            if content_length:
                return int(content_length)
    except Exception:
        pass
    return None


def is_large_gif_url(url: str) -> bool:
    if not url.lower().endswith(".gif"):
        return False
    size = probe_content_length(url)
    if size is None:
        return False
    return size > LARGE_GIF_BYTES


def download_bytes(
    url: str,
    *,
    timeout: Optional[int] = None,
    retries: Optional[int] = None,
) -> bytes:
    timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    retries = retries if retries is not None else DEFAULT_RETRIES
    last_exc: Optional[Exception] = None

    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, timeout=timeout, stream=True) as resp:
                resp.raise_for_status()
                chunks: list[bytes] = []
                for chunk in resp.iter_content(chunk_size=256 * 1024):
                    if chunk:
                        chunks.append(chunk)
                return b"".join(chunks)
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                wait = min(2**attempt, 10)
                print(
                    f"[task_reference] 下载重试 ({attempt}/{retries}) "
                    f"{_short_url(url)}: {exc}，{wait}s 后重试"
                )
                time.sleep(wait)

    if last_exc is not None:
        raise last_exc
    raise RuntimeError(f"下载失败: {url}")


def _short_url(url: str) -> str:
    if len(url) <= 100:
        return url
    return url[:80] + "..." + url[-15:]
