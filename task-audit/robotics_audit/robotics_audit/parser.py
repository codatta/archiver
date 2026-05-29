from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from robotics_audit.models import Segment


def parse_json_payload(raw: Any) -> Union[Dict[str, Any], List[Any]]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        return {"data": raw}
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            return {}
        if isinstance(parsed, list):
            return {"data": parsed}
        if isinstance(parsed, dict):
            return parsed
    return {}


def _unwrap_data(payload: Dict[str, Any]) -> Any:
    inner = payload.get("data")
    if isinstance(inner, (dict, list)):
        return inner
    return payload


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("，", ".").replace(",", ".")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", text):
        return None
    return float(text)


def _pick_time_pair(item: Dict[str, Any]) -> Tuple[Optional[float], Optional[float]]:
    start_keys = ("start", "startTime", "start_time", "timeStart", "from", "begin", "t0")
    end_keys = ("end", "endTime", "end_time", "timeEnd", "to", "finish", "t1")

    start_val = None
    end_val = None
    for key in start_keys:
        if key in item:
            start_val = _coerce_float(item.get(key))
            break
    for key in end_keys:
        if key in item:
            end_val = _coerce_float(item.get(key))
            break

    if start_val is None and end_val is None:
        time_range = item.get("time") or item.get("timeRange") or item.get("range")
        if isinstance(time_range, dict):
            start_val = _coerce_float(time_range.get("start") or time_range.get("from"))
            end_val = _coerce_float(time_range.get("end") or time_range.get("to"))
        elif isinstance(time_range, (list, tuple)) and len(time_range) >= 2:
            start_val = _coerce_float(time_range[0])
            end_val = _coerce_float(time_range[1])
        elif isinstance(time_range, str):
            parts = re.split(r"[-~–—]", time_range.strip())
            if len(parts) == 2:
                start_val = _coerce_float(parts[0])
                end_val = _coerce_float(parts[1])

    return start_val, end_val


def _pick_description(item: Dict[str, Any]) -> str:
    for key in ("description", "desc", "des", "text", "content", "label", "caption", "summary"):
        val = item.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def _find_segment_list(payload: Dict[str, Any], list_keys: List[str]) -> List[Dict[str, Any]]:
    data = _unwrap_data(payload)
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if not isinstance(data, dict):
        return []

    for key in list_keys:
        val = data.get(key)
        if isinstance(val, list) and val:
            return [x for x in val if isinstance(x, dict)]
    for key in list_keys:
        val = payload.get(key)
        if isinstance(val, list) and val:
            return [x for x in val if isinstance(x, dict)]
    return []


def extract_video_duration(payload: Dict[str, Any]) -> Optional[float]:
    data = _unwrap_data(payload)
    if not isinstance(data, dict):
        data = payload if isinstance(payload, dict) else {}
    candidates = [
        data.get("videoDuration"),
        data.get("duration"),
        payload.get("videoDuration"),
        payload.get("duration"),
    ]
    video = data.get("video") or payload.get("video")
    if isinstance(video, dict):
        candidates.extend([video.get("duration"), video.get("videoDuration"), video.get("length")])
    for val in candidates:
        num = _coerce_float(val)
        if num is not None and num > 0:
            return num
    return None


def parse_segments(payload: Dict[str, Any], list_keys: List[str]) -> List[Segment]:
    items = _find_segment_list(payload, list_keys)
    segments: List[Segment] = []
    for idx, item in enumerate(items):
        start, end = _pick_time_pair(item)
        desc = _pick_description(item)
        if start is None or end is None:
            segments.append(
                Segment(
                    index=idx,
                    start=start if start is not None else float("nan"),
                    end=end if end is not None else float("nan"),
                    description=desc,
                    raw=item,
                )
            )
        else:
            segments.append(
                Segment(index=idx, start=start, end=end, description=desc, raw=item)
            )
    return segments
