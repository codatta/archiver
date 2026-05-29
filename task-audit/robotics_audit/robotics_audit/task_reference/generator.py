from __future__ import annotations

import base64
import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import requests

from robotics_audit.models import TEMPLATE_METADATA, TEMPLATE_SEGMENT
from robotics_audit.task_reference.loader import build_vision_download_url
from robotics_audit.task_reference.media_compress import (
    DEFAULT_FRAME_INTERVAL_SEC,
    compress_image_bytes,
    extract_gif_frames,
    frame_interval_for_template,
    frames_per_second_for_template,
    needs_local_compress,
    probe_gif_meta,
)
from robotics_audit.task_reference.media_download import (
    download_bytes,
    is_large_gif_url,
)
from robotics_audit.task_reference.store import TaskReferenceRecord


@dataclass
class VisionFrame:
    image_b64: str
    mime: str
    frame_index: int


class TaskReferenceGenerator:
    def __init__(self, model: Optional[str] = None) -> None:
        self.api_key = os.getenv("QWEN_API_KEY", "")
        self.base_url = os.getenv(
            "QWEN_BASE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
        )
        self.model = model or os.getenv("QWEN_VL_MODEL", "qwen-vl-max")
        self._last_media_meta: Dict[str, Any] = {}

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def generate(self, task_info: Dict[str, Any]) -> TaskReferenceRecord:
        media_url = str(task_info.get("media_url") or "")
        template_id = str(task_info.get("template_id") or "")
        task_id = str(task_info.get("task_id") or "")
        base_record = TaskReferenceRecord(
            frontier_id=str(task_info.get("frontier_id") or ""),
            template_id=template_id,
            task_id=task_id,
            task_name=str(task_info.get("task_name") or ""),
            media_resource=str(task_info.get("media_resource") or ""),
            media_url=media_url,
            source="vision_failed",
            reference={},
        )

        if not self.enabled:
            print(f"[task_reference] 跳过 task_id={task_id}: 未配置 QWEN_API_KEY")
            return base_record
        if not media_url:
            print(f"[task_reference] 跳过 task_id={task_id}: 无法构建视频 URL")
            return base_record

        print(f"[task_reference] 分析视频 task_id={task_id}")
        print(f"  media_url={media_url}")

        frames = self._download_media(media_url, template_id=template_id)
        if not frames:
            return base_record

        media_meta = dict(self._last_media_meta)
        media_meta["sample_fps"] = frames_per_second_for_template(template_id)
        llm_frames = frames
        print(f"[task_reference] 送视觉模型 {len(llm_frames)} 张")

        prompt = self._build_prompt(
            template_id,
            task_info,
            media_meta=media_meta,
            sampled_frames=llm_frames,
        )
        parsed = self._call_qwen(prompt, llm_frames)
        if not parsed:
            return base_record

        reference = parsed.get("reference") if isinstance(parsed.get("reference"), dict) else parsed
        if isinstance(reference, dict) and template_id == TEMPLATE_SEGMENT:
            reference.setdefault("time_unit", "frame")

        return TaskReferenceRecord(
            frontier_id=str(task_info.get("frontier_id") or ""),
            template_id=template_id,
            task_id=task_id,
            task_name=str(task_info.get("task_name") or ""),
            media_resource=str(task_info.get("media_resource") or ""),
            media_url=media_url,
            source="llm_vision",
            model=self.model,
            reference=reference if isinstance(reference, dict) else {},
            media_meta=media_meta,
        )

    def _build_prompt(
        self,
        template_id: str,
        task_info: Dict[str, Any],
        *,
        media_meta: Dict[str, Any],
        sampled_frames: List[VisionFrame],
    ) -> str:
        task_name = task_info.get("task_name") or ""
        frame_count = int(media_meta.get("frame_count") or 0)
        frame_labels = [f.frame_index for f in sampled_frames]

        if template_id == TEMPLATE_SEGMENT:
            schema = {
                "reference": {
                    "time_unit": "frame",
                    "segments": [
                        {
                            "start": 1,
                            "end": 10,
                            "description": "action description",
                        }
                    ],
                    "visible_objects": ["object"],
                    "actions": ["action phrase"],
                    "environment": "Indoor",
                }
            }
            focus = f"""
This GIF has {frame_count or "unknown"} frames total (UI shows current/total frame counter).
The annotation UI uses 1-based FRAME INDEX for start/end, NOT seconds.
Each task video has a different frame count — use this GIF's actual total: {frame_count or "unknown"}.
Sampled frame indices sent to you: {frame_labels}

Infer a coarse timeline using FRAME NUMBERS (1 to {frame_count or "total frames"}) for start/end.
Example: {{"start": 1, "end": 15, "description": "robot arm picks up the cup"}}
Do NOT output seconds.
"""
        elif template_id == TEMPLATE_METADATA:
            schema = {
                "reference": {
                    "objects": ["object touching agent"],
                    "environment": "Indoor/Outdoor/Office/Kitchen/Bedroom/Factory/Other",
                    "agent_type": {"status": "static/mobile", "armCount": "1/2", "handCount": "1-5"},
                    "view": ["first_person_view/third_person_view/bird_eye_view/static/dynamic"],
                    "relations": [{"targetA": "", "relation": "", "targetB": ""}],
                    "task": ["overall action description"],
                    "visible_objects": ["object"],
                    "actions": ["action phrase"],
                }
            }
            focus = (
                "Focus on objects, environment, agent type, camera view, relations and overall task. "
                f"Sampled at ~{media_meta.get('sample_fps', 1)} frame(s) per second (scene-level, no timeline needed)."
            )
        else:
            schema = {"reference": {}}
            focus = "Describe the scene and actions."

        return f"""Analyze this robotics task media and output ONE JSON object only.
Task name: {task_name}
Template: {template_id}
{focus}
Use this JSON schema shape:
{json.dumps(schema, ensure_ascii=False)}

Rules:
- Use English phrases unless the scene text is clearly Chinese.
- Do not include markdown or explanation.
- Fill all keys that you can infer from the media.
"""

    def _download_media(self, url: str, *, template_id: str = "") -> List[VisionFrame]:
        if not url:
            return []

        raw_mime = "image/gif" if url.lower().endswith(".gif") else "image/jpeg"
        interval_sec = frame_interval_for_template(template_id)
        fps = frames_per_second_for_template(template_id)

        if url.lower().endswith(".gif") and is_large_gif_url(url):
            print(f"[task_reference] 检测到大体积 GIF，跳过 OSS 压缩，直接下载原始文件并本地抽帧（{fps}fps）")
            return self._fetch_frames(url, raw_mime, allow_local=True, interval_sec=interval_sec)

        download_url, expected_mime = build_vision_download_url(url)
        if download_url and download_url != url:
            frames = self._fetch_frames(
                download_url,
                expected_mime,
                allow_local=False,
                oss_fallback=False,
                interval_sec=interval_sec,
            )
            if frames:
                return frames
            print("[task_reference] OSS 压缩不可用，改用原始 GIF 下载并本地抽帧")

        return self._fetch_frames(url, raw_mime, allow_local=True, interval_sec=interval_sec)

    def _fetch_frames(
        self,
        download_url: str,
        mime: str,
        *,
        allow_local: bool = False,
        oss_fallback: bool = True,
        interval_sec: Optional[float] = None,
    ) -> List[VisionFrame]:
        try:
            timeout = 60 if not allow_local else None
            content = download_bytes(download_url, timeout=timeout)
            is_gif = download_url.lower().endswith(".gif") or ".gif?" in download_url.lower()

            if is_gif:
                self._last_media_meta = {
                    **probe_gif_meta(content),
                    "time_unit": "frame",
                    "index_base": 1,
                }
                print(
                    f"[task_reference] GIF 共 {self._last_media_meta['frame_count']} 帧，"
                    f"时长约 {self._last_media_meta['duration_sec']}s（标注用帧序号）"
                )

            if allow_local and (is_gif or needs_local_compress(content, mime)):
                sample_interval = interval_sec if interval_sec is not None else DEFAULT_FRAME_INTERVAL_SEC
                frame_items = extract_gif_frames(content, interval_sec=sample_interval)
                print(
                    f"[task_reference] 本地抽帧 {len(frame_items)} 张（间隔 {sample_interval:.2f}s），"
                    f"原大小 {len(content) / 1024:.1f} KB"
                )
                return [
                    VisionFrame(
                        image_b64=base64.b64encode(frame).decode("utf-8"),
                        mime="image/jpeg",
                        frame_index=frame_index,
                    )
                    for frame, frame_index in frame_items
                ]

            if needs_local_compress(content, mime):
                content, mime = compress_image_bytes(content)

            size_kb = len(content) / 1024
            print(f"[task_reference] 已下载媒体 {size_kb:.1f} KB ({mime})")
            self._last_media_meta = self._last_media_meta or {"time_unit": "frame", "index_base": 1}
            return [
                VisionFrame(
                    image_b64=base64.b64encode(content).decode("utf-8"),
                    mime=mime,
                    frame_index=1,
                )
            ]
        except Exception as exc:
            if oss_fallback and not allow_local:
                return []
            print(f"[task_reference] 下载媒体失败 {download_url}: {exc}")
            return []

    def _call_qwen(self, prompt: str, frames: List[VisionFrame]) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        for frame in frames:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{frame.mime};base64,{frame.image_b64}"},
                }
            )
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.1,
            "max_tokens": int(os.getenv("QWEN_VL_MAX_TOKENS", "4096")),
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            content = (resp.json().get("choices") or [{}])[0].get("message", {}).get("content", "")
            return self._parse_json(content)
        except Exception as exc:
            print(f"[task_reference] LLM 调用失败: {exc}")
            return None

    def _parse_json(self, content: str) -> Optional[Dict[str, Any]]:
        text = (content or "").strip()
        if not text:
            return None
        fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if fence:
            text = fence.group(1).strip()
        for candidate in (text, self._balance_json_braces(text)):
            try:
                parsed = json.loads(candidate)
                return parsed if isinstance(parsed, dict) else None
            except json.JSONDecodeError:
                continue
        print("[task_reference] 视觉模型 JSON 解析失败")
        return None

    @staticmethod
    def _balance_json_braces(text: str) -> str:
        start = text.find("{")
        if start < 0:
            return text
        body = text[start:]
        missing = body.count("{") - body.count("}")
        if missing > 0:
            body += "}" * missing
        return body
