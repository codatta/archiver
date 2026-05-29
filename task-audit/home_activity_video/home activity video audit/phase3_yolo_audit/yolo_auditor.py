"""
Phase 3 — yolo_audit

本模块负责读取 YOLO 推理结果并映射为结构化审核结论。
默认不直接在这里跑模型，便于与离线/异步推理服务解耦。
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import uuid
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path
from math import ceil
from typing import Any, Dict, List, Optional

import httpx
from video_common.ffmpeg_bin import resolve_fftool
from video_common.ffprobe_utils import ffprobe_json, parse_duration_seconds


def _is_enabled() -> bool:
    raw = str(os.getenv("PHASE3_YOLO_ENABLED", "0")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _resolve_threshold() -> float:
    raw = os.getenv("PHASE3_YOLO_RISK_THRESHOLD", "")
    if not str(raw).strip():
        # 与双指标阈值联动：min_conf 越高，允许的 risk 越低
        return max(0.0, 1.0 - _resolve_min_confidence())
    try:
        return float(raw)
    except ValueError:
        return max(0.0, 1.0 - _resolve_min_confidence())


def _resolve_fallback_result_path(submission_id: str) -> Optional[Path]:
    base = os.getenv("PRE_FRAME_OUTPUT_DIR", "output/pre_frames")
    p = Path(base) / submission_id / "latest_yolo_result.json"
    return p if p.exists() else None


def _resolve_pre_frame_root() -> Path:
    return Path(os.getenv("PRE_FRAME_OUTPUT_DIR", "output/pre_frames"))


def _is_api_call_enabled() -> bool:
    raw = str(os.getenv("PHASE3_YOLO_CALL_API", "1")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _resolve_api_url() -> str:
    return str(os.getenv("PHASE3_YOLO_API_URL", "http://127.0.0.1:8001")).rstrip("/")


def _resolve_detector() -> str:
    return str(os.getenv("PHASE3_YOLO_DETECTOR", "pose")).strip() or "pose"


def _resolve_model() -> str:
    return str(os.getenv("PHASE3_YOLO_MODEL", "yolov8s.pt")).strip() or "yolov8s.pt"


def _resolve_hands_pass_threshold() -> float:
    raw = str(os.getenv("PHASE3_HANDS_MIN_CONFIDENCE", "")).strip()
    if not raw:
        return _resolve_min_confidence()
    try:
        return float(raw)
    except ValueError:
        return _resolve_min_confidence()


def _resolve_object_pass_threshold() -> float:
    raw = str(os.getenv("PHASE3_OBJECT_MIN_CONFIDENCE", "")).strip()
    if not raw:
        return _resolve_min_confidence()
    try:
        return float(raw)
    except ValueError:
        return _resolve_min_confidence()


def _resolve_type_mismatch_review_confidence() -> float:
    raw = str(os.getenv("PHASE3_TYPE_MISMATCH_REVIEW_CONFIDENCE", "0.80")).strip()
    try:
        v = float(raw)
    except ValueError:
        return 0.80
    return max(0.0, min(1.0, v))


def _resolve_row_video_type_confidence() -> float:
    raw = str(os.getenv("PHASE3_ROW_VIDEO_TYPE_CONFIDENCE", "0.95")).strip()
    try:
        v = float(raw)
    except ValueError:
        return 0.95
    return max(0.0, min(1.0, v))


def _resolve_min_confidence() -> float:
    raw = str(os.getenv("PHASE3_MIN_CONFIDENCE", "0.60")).strip()
    try:
        return float(raw)
    except ValueError:
        return 0.60


def _resolve_s_grade() -> str:
    return str(os.getenv("PHASE3_PASS_GRADE", "S")).strip() or "S"


def _resolve_a_grade() -> str:
    return str(os.getenv("PHASE3_REVIEW_GRADE", "A")).strip() or "A"


def _resolve_object_conf_threshold() -> float:
    raw = str(os.getenv("PHASE3_YOLO_OBJECT_CONF_THRESHOLD", "0.35")).strip()
    try:
        return float(raw)
    except ValueError:
        return 0.35


def _resolve_first_person_pass_threshold() -> float:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_MIN_CONFIDENCE", "0.60")).strip()
    try:
        return float(raw)
    except ValueError:
        return 0.60


def _resolve_first_person_x_min() -> float:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_X_MIN", "0.20")).strip()
    try:
        return float(raw)
    except ValueError:
        return 0.20


def _resolve_first_person_x_max() -> float:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_X_MAX", "0.80")).strip()
    try:
        return float(raw)
    except ValueError:
        return 0.80


def _resolve_first_person_y_lower() -> float:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_Y_LOWER", "0.55")).strip()
    try:
        return float(raw)
    except ValueError:
        return 0.55


def _resolve_first_person_y_upper() -> float:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_Y_UPPER", "0.45")).strip()
    try:
        return float(raw)
    except ValueError:
        return 0.45


def _resolve_first_person_y_span() -> float:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_Y_SPAN", "0.22")).strip()
    try:
        return float(raw)
    except ValueError:
        return 0.22


def _resolve_first_person_area_target() -> float:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_AREA_TARGET", "0.06")).strip()
    try:
        return max(0.001, float(raw))
    except ValueError:
        return 0.06


def _resolve_first_person_area_min() -> float:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_AREA_MIN", "0.025")).strip()
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.025


def _resolve_first_person_temporal_window() -> int:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_TEMPORAL_WINDOW", "5")).strip()
    try:
        v = int(raw)
    except ValueError:
        return 5
    return max(1, v)


def _resolve_first_person_temporal_bonus_max() -> float:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_TEMPORAL_BONUS_MAX", "0.10")).strip()
    try:
        v = float(raw)
    except ValueError:
        return 0.10
    return max(0.0, min(0.5, v))


def _resolve_first_person_foreground_weight() -> float:
    raw = str(os.getenv("PHASE3_FIRST_PERSON_FOREGROUND_WEIGHT", "0.30")).strip()
    try:
        v = float(raw)
    except ValueError:
        return 0.30
    return max(0.0, min(1.0, v))


def _resolve_require_first_person() -> bool:
    raw = str(os.getenv("PHASE3_REQUIRE_FIRST_PERSON", "0")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _resolve_object_coexist_weight() -> float:
    raw = str(os.getenv("PHASE3_OBJECT_COEXIST_WEIGHT", "0.80")).strip()
    try:
        v = float(raw)
    except ValueError:
        return 0.80
    if v < 0.0:
        return 0.0
    if v > 1.0:
        return 1.0
    return v


def _resolve_max_frames() -> int:
    raw = str(os.getenv("PHASE3_YOLO_API_MAX_FRAMES", "120")).strip()
    try:
        v = int(raw)
    except ValueError:
        return 120
    return max(1, v)


def _resolve_realtime_frames() -> int:
    raw = str(os.getenv("PHASE3_REALTIME_SAMPLE_FRAMES", "24")).strip()
    try:
        v = int(raw)
    except ValueError:
        return 24
    return max(1, v)


def _resolve_runtime_frame_root() -> Path:
    base = str(os.getenv("PHASE3_RUNTIME_FRAME_DIR", "")).strip()
    if base:
        return Path(base)
    return Path(tempfile.gettempdir()) / "phase3_runtime_frames"


def _pick_latest_frame_dir(submission_id: str) -> Optional[Path]:
    root = _resolve_pre_frame_root() / submission_id
    if not root.exists():
        return None
    direct_frames = root / "frames"
    if direct_frames.is_dir():
        return direct_frames
    batch_dirs = [p for p in root.iterdir() if p.is_dir()]
    if not batch_dirs:
        return None
    latest = max(batch_dirs, key=lambda p: p.stat().st_mtime)
    frames_dir = latest / "frames"
    return frames_dir if frames_dir.is_dir() else None


def _collect_frame_paths(frames_dir: Path) -> List[Path]:
    exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    all_files = [p for p in frames_dir.iterdir() if p.is_file() and p.suffix.lower() in exts]
    all_files.sort(key=lambda p: p.name)
    return all_files


def _sample_frame_paths(frame_paths: List[Path], max_frames: int) -> List[Path]:
    if len(frame_paths) <= max_frames:
        return frame_paths
    step = ceil(len(frame_paths) / max_frames)
    sampled = frame_paths[::step]
    return sampled[:max_frames]


def _save_latest_result(submission_id: str, payload: Dict[str, Any]) -> Path:
    target = _resolve_pre_frame_root() / submission_id / "latest_yolo_result.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return target


def _extract_runtime_frames(video_path: str, submission_id: str) -> Path:
    probe = ffprobe_json(video_path)
    duration = parse_duration_seconds(probe)
    sample_n = _resolve_realtime_frames()
    root = _resolve_runtime_frame_root() / submission_id / str(uuid.uuid4())
    root.mkdir(parents=True, exist_ok=True)

    ffmpeg_exe = resolve_fftool("ffmpeg")
    # 均匀抽样，避开首尾各 2%
    start = max(0.0, duration * 0.02)
    end = max(start, duration * 0.98)
    span = max(0.001, end - start)
    for i in range(sample_n):
        t = start + span * (float(i) / float(max(1, sample_n - 1)))
        out_img = root / f"{i:06d}.jpg"
        cmd = [
            ffmpeg_exe,
            "-hide_banner",
            "-loglevel",
            "error",
            "-ss",
            f"{t:.3f}",
            "-i",
            video_path,
            "-frames:v",
            "1",
            "-q:v",
            "4",
            str(out_img),
            "-y",
        ]
        proc = subprocess.run(cmd, capture_output=True)
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""
            raise RuntimeError(f"实时抽帧失败: {err}")
    return root


def _point_near_box(px: float, py: float, box: List[float], expand: float = 0.03) -> bool:
    if len(box) != 4:
        return False
    x1, y1, x2, y2 = box
    return (x1 - expand) <= px <= (x2 + expand) and (y1 - expand) <= py <= (y2 + expand)


def _classify_video_type(label_scores: Dict[str, float]) -> Dict[str, Any]:
    # 关键词可按业务持续扩展
    kitchen_keys = {
        "bowl", "cup", "fork", "knife", "spoon", "bottle", "wine glass", "dish", "plate",
        "microwave", "oven", "refrigerator", "sink", "kettle", "pot", "pan",
    }
    cleaning_keys = {
        "broom", "mop", "bucket", "vacuum", "sponge", "brush", "duster", "spray bottle",
    }
    tidying_keys = {
        "book", "remote", "cell phone", "laptop", "keyboard", "mouse", "tv",
        "chair", "couch", "bed", "toilet", "potted plant", "clock", "toaster",
    }

    typed = {
        "Kitchen Cooking": 0.0,
        "Home Cleaning": 0.0,
        "Household Tidying": 0.0,
    }
    for label, score in label_scores.items():
        lk = label.lower().strip()
        if lk in kitchen_keys:
            typed["Kitchen Cooking"] += score
        if lk in cleaning_keys:
            typed["Home Cleaning"] += score
        if lk in tidying_keys:
            typed["Household Tidying"] += score

    top_type = max(typed, key=lambda k: typed[k])
    total = sum(typed.values())
    confidence = (typed[top_type] / total) if total > 0 else 0.0
    return {
        "video_type": top_type if total > 0 else "Unknown",
        "video_type_confidence": confidence,
        "video_type_scores": typed,
    }


def _infer_video_type_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
    task_id = str(row.get("task_id") or "").strip()
    explicit_map = {
        "10398675743500103337": "Kitchen Cooking",
        "10399444893000104677": "Home Cleaning",
        "10399440080300104655": "Household Tidying",
    }
    if task_id in explicit_map:
        return {
            "video_type": explicit_map[task_id],
            "video_type_confidence": 1.0,
            "source": "task_id_map",
        }
    text_fields = [
        row.get("template_id"),
        row.get("task_name"),
        row.get("task_title"),
        row.get("task_type"),
        row.get("task_id"),
    ]
    combined = " ".join(str(v or "") for v in text_fields).lower()
    if not combined.strip():
        return {"video_type": "Unknown", "video_type_confidence": 0.0, "source": "row_fields"}
    if any(k in combined for k in {"clean", "cleaning", "house-clean", "home-clean", "tidyup-clean"}):
        return {
            "video_type": "Home Cleaning",
            "video_type_confidence": _resolve_row_video_type_confidence(),
            "source": "row_fields",
        }
    if any(k in combined for k in {"kitchen", "cooking", "cook", "recipe", "meal"}):
        return {
            "video_type": "Kitchen Cooking",
            "video_type_confidence": _resolve_row_video_type_confidence(),
            "source": "row_fields",
        }
    if any(k in combined for k in {"tidy", "tidying", "organize", "organise", "declutter", "household"}):
        return {
            "video_type": "Household Tidying",
            "video_type_confidence": _resolve_row_video_type_confidence(),
            "source": "row_fields",
        }
    return {"video_type": "Unknown", "video_type_confidence": 0.0, "source": "row_fields"}


def _run_yolo_api_on_frames(submission_id: str, frames_dir: Path, source_tag: str) -> Dict[str, Any]:
    frame_paths = _collect_frame_paths(frames_dir)
    if not frame_paths:
        raise RuntimeError(f"抽帧目录为空: {frames_dir}")
    selected = _sample_frame_paths(frame_paths, _resolve_max_frames())
    api_url = f"{_resolve_api_url()}/tasks/detect-persons"
    form_data = {
        "detector": _resolve_detector(),
        "yolo_model": _resolve_model(),
        "arm_conf_threshold": "0.30",
        "detect_objects": "true",
        "object_conf_threshold": str(_resolve_object_conf_threshold()),
    }

    with ExitStack() as stack:
        files = []
        for p in selected:
            fp = stack.enter_context(open(p, "rb"))
            files.append(("files", (p.name, fp, "image/jpeg")))
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(api_url, data=form_data, files=files)
        resp.raise_for_status()
        body = resp.json()

    detections = body.get("detections")
    if not isinstance(detections, dict):
        raise RuntimeError("YOLO API 返回缺少 detections")

    total = len(selected)
    hands_pass_threshold = _resolve_hands_pass_threshold()
    object_pass_threshold = _resolve_object_pass_threshold()
    first_person_pass_threshold = _resolve_first_person_pass_threshold()
    both_hands_frames = 0
    interacting_frames = 0
    coexist_frames = 0
    max_object_count = 0
    object_label_scores: Dict[str, float] = {}
    # 第一人称视角：使用手腕关键点的空间位置做启发式聚合
    first_person_score_sum = 0.0
    first_person_hit_frames = 0
    first_person_lower_hit_frames = 0
    first_person_vertical_hit_frames = 0
    first_person_area_hit_frames = 0
    first_person_area_score_sum = 0.0
    first_person_frame_hits: List[int] = []
    x_min = _resolve_first_person_x_min()
    x_max = _resolve_first_person_x_max()
    y_lower = _resolve_first_person_y_lower()
    y_upper = _resolve_first_person_y_upper()
    y_span = _resolve_first_person_y_span()
    area_target = _resolve_first_person_area_target()
    area_min = _resolve_first_person_area_min()
    fg_weight = _resolve_first_person_foreground_weight()
    temporal_window = _resolve_first_person_temporal_window()
    temporal_bonus_max = _resolve_first_person_temporal_bonus_max()
    for fp in selected:
        rec = detections.get(fp.name) or {}
        if not isinstance(rec, dict):
            continue
        hands = rec.get("hand_keypoints") or []
        objects = rec.get("object_boxes") or []
        hand_count = len(hands) if isinstance(hands, list) else 0
        obj_count = len(objects) if isinstance(objects, list) else 0
        if hand_count >= 2:
            both_hands_frames += 1
        if hand_count > 0 and obj_count > 0:
            coexist_frames += 1
        if obj_count > max_object_count:
            max_object_count = obj_count
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            label = str(obj.get("label") or "").strip()
            conf = float(obj.get("conf") or 0.0)
            if not label:
                continue
            object_label_scores[label] = object_label_scores.get(label, 0.0) + conf
        if hand_count > 0 and obj_count > 0:
            interact = False
            for hk in hands:
                if not (isinstance(hk, list) and len(hk) >= 2):
                    continue
                hx, hy = float(hk[0]), float(hk[1])
                for obj in objects:
                    if not isinstance(obj, dict):
                        continue
                    bbox = obj.get("bbox")
                    if isinstance(bbox, list) and _point_near_box(hx, hy, bbox):
                        interact = True
                        break
                if interact:
                    break
            if interact:
                interacting_frames += 1

        # first-person heuristic (双通道):
        # 1) 下半区模式：至少两只手腕在下半区（y >= y_lower）
        # 2) 上下分布模式：同帧同时出现上部手腕(y <= y_upper)与下部手腕(y >= y_lower)，且纵向跨度足够
        filtered_wrists: List[List[float]] = []
        for hk in hands:
            if not (isinstance(hk, list) and len(hk) >= 3):
                continue
            x, y, c = float(hk[0]), float(hk[1]), float(hk[2])
            if x_min <= x <= x_max:
                filtered_wrists.append([x, y, max(0.0, min(1.0, c))])
        frame_first_person_score = 0.0
        frame_hand_area_ratio = 0.0
        frame_hit = 0
        if len(filtered_wrists) >= 2:
            xs = [v[0] for v in filtered_wrists]
            ys = [v[1] for v in filtered_wrists]
            cs = [v[2] for v in filtered_wrists]
            frame_hand_area_ratio = max(0.0, (max(xs) - min(xs)) * (max(ys) - min(ys)))
            lower_count = sum(1 for y in ys if y >= y_lower)
            upper_count = sum(1 for y in ys if y <= y_upper)
            has_lower_mode = lower_count >= 2
            has_vertical_mode = upper_count >= 1 and lower_count >= 1 and (max(ys) - min(ys) >= y_span)
            area_ratio_score = min(1.0, frame_hand_area_ratio / area_target)
            area_mode_hit = frame_hand_area_ratio >= area_min
            pose_mode_score = (sum(cs) / float(len(cs))) if (has_lower_mode or has_vertical_mode) else 0.0
            # 主判定：双手区域占比；辅判定：空间位姿（上下/下半区）
            base_score = max(area_ratio_score, pose_mode_score)
            # 前景占比辅助：面积越大越接近第一视角，但权重受控，避免误抬分
            frame_first_person_score = min(1.0, base_score + fg_weight * area_ratio_score)
            if area_mode_hit:
                first_person_area_hit_frames += 1
            if has_lower_mode:
                first_person_lower_hit_frames += 1
            if has_vertical_mode:
                first_person_vertical_hit_frames += 1
            first_person_area_score_sum += area_ratio_score
            if area_mode_hit or has_lower_mode or has_vertical_mode:
                first_person_hit_frames += 1
                frame_hit = 1
        first_person_score_sum += frame_first_person_score
        first_person_frame_hits.append(frame_hit)

    both_hands_confidence = float(both_hands_frames) / float(total) if total > 0 else 0.0
    near_interaction_confidence = float(interacting_frames) / float(total) if total > 0 else 0.0
    coexist_confidence = float(coexist_frames) / float(total) if total > 0 else 0.0
    # 交互置信度稳健化：保留“手靠近物体”的强规则，同时引入“同帧共现”的弱证据
    object_interaction_confidence = max(
        near_interaction_confidence,
        coexist_confidence * _resolve_object_coexist_weight(),
    )
    risk_score = 1.0 - min(both_hands_confidence, object_interaction_confidence)
    first_person_confidence = float(first_person_score_sum) / float(total) if total > 0 else 0.0
    # 时间连续性加分：连续命中窗口越长，给予额外奖励
    longest_run = 0
    cur_run = 0
    for h in first_person_frame_hits:
        if h:
            cur_run += 1
            if cur_run > longest_run:
                longest_run = cur_run
        else:
            cur_run = 0
    temporal_ratio = min(1.0, float(longest_run) / float(max(1, temporal_window)))
    temporal_bonus = temporal_bonus_max * temporal_ratio
    first_person_confidence = min(1.0, first_person_confidence + temporal_bonus)
    video_type_info = _classify_video_type(object_label_scores)
    hit_labels: List[str] = []
    if both_hands_confidence >= hands_pass_threshold:
        hit_labels.append("both_hands_present")
    if object_interaction_confidence >= object_pass_threshold:
        hit_labels.append("active_object_present")
    if first_person_confidence >= first_person_pass_threshold:
        hit_labels.append("first_person_view_present")
    payload: Dict[str, Any] = {
        "risk_score": risk_score,
        "hit_labels": hit_labels,
        "both_hands_confidence": both_hands_confidence,
        "object_interaction_confidence": object_interaction_confidence,
        "first_person_confidence": first_person_confidence,
        "video_type": video_type_info["video_type"],
        "video_type_confidence": video_type_info["video_type_confidence"],
        "video_type_scores": video_type_info["video_type_scores"],
        "both_hands_pass": both_hands_confidence >= hands_pass_threshold,
        "object_interaction_pass": object_interaction_confidence >= object_pass_threshold,
        "first_person_pass": first_person_confidence >= first_person_pass_threshold,
        "metrics": {
            "total_frames": total,
            "both_hands_frames": both_hands_frames,
            "interacting_frames": interacting_frames,
            "coexist_frames": coexist_frames,
            "near_interaction_confidence": near_interaction_confidence,
            "coexist_confidence": coexist_confidence,
            "max_object_count": max_object_count,
            "first_person_hit_frames": first_person_hit_frames,
            "first_person_lower_hit_frames": first_person_lower_hit_frames,
            "first_person_vertical_hit_frames": first_person_vertical_hit_frames,
            "first_person_area_hit_frames": first_person_area_hit_frames,
            "first_person_area_score": (float(first_person_area_score_sum) / float(total) if total > 0 else 0.0),
            "first_person_longest_run": longest_run,
            "first_person_temporal_window": temporal_window,
            "first_person_temporal_bonus": temporal_bonus,
        },
        "source": "phase3.inline_yolo_hands_objects",
        "source_tag": source_tag,
        "api_url": api_url,
        "frames_dir": str(frames_dir),
    }
    out_path = _save_latest_result(submission_id, payload)
    payload["result_json_path"] = str(out_path)
    return payload


def _run_yolo_api_on_pre_frames(submission_id: str) -> Dict[str, Any]:
    frames_dir = _pick_latest_frame_dir(submission_id)
    if not frames_dir:
        raise RuntimeError("未找到抽帧目录，无法调用 YOLO API")
    return _run_yolo_api_on_frames(submission_id, frames_dir, "pre_frames")


def _run_yolo_api_on_video(video_path: str, submission_id: str) -> Dict[str, Any]:
    frames_dir = _extract_runtime_frames(video_path, submission_id)
    try:
        return _run_yolo_api_on_frames(submission_id, frames_dir, "runtime_video_sampling")
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)


def _load_result_from_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("YOLO 结果 JSON 必须是对象")
    return data


@dataclass
class YoloAuditOutcome:
    yolo_audit: Dict[str, Any]
    stop: bool
    audit_grade: Optional[str] = None
    db_update: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


def run_yolo_audit(
    row: Dict[str, Any],
    *,
    submission_id: str,
    video_path: Optional[str],
    task_id: str,
    lightweight_hash: str,
    phash_hex: str,
    cut_count: int,
) -> YoloAuditOutcome:
    if not _is_enabled():
        return YoloAuditOutcome(
            yolo_audit={"overall_result": "skipped", "reason": "PHASE3_YOLO_ENABLED=0"},
            stop=False,
        )

    threshold = _resolve_threshold()
    risk_score: Optional[float] = None
    hit_labels: List[str] = []
    source = "unknown"
    both_hands_confidence: Optional[float] = None
    object_interaction_confidence: Optional[float] = None
    first_person_confidence: Optional[float] = None
    video_type: Optional[str] = None
    video_type_confidence: Optional[float] = None

    if row.get("yolo_risk_score") is not None:
        source = "row.yolo_risk_score"
        try:
            risk_score = float(row["yolo_risk_score"])
        except Exception as e:
            return YoloAuditOutcome(
                yolo_audit={"overall_result": "fail", "reason": f"yolo_risk_score 解析失败: {e}"},
                stop=True,
                audit_grade="Error",
                errors=[f"YOLO 风险分解析失败: {e}"],
            )
        labels_raw = row.get("yolo_hit_labels")
        if labels_raw:
            if isinstance(labels_raw, str):
                hit_labels = [v.strip() for v in labels_raw.split(",") if v.strip()]
            elif isinstance(labels_raw, list):
                hit_labels = [str(v) for v in labels_raw]
    else:
        if _is_api_call_enabled():
            try:
                if video_path:
                    payload = _run_yolo_api_on_video(video_path, submission_id)
                else:
                    payload = _run_yolo_api_on_pre_frames(submission_id)
                risk_score = float(payload.get("risk_score"))
                if payload.get("both_hands_confidence") is not None:
                    both_hands_confidence = float(payload.get("both_hands_confidence"))
                if payload.get("object_interaction_confidence") is not None:
                    object_interaction_confidence = float(payload.get("object_interaction_confidence"))
                if payload.get("video_type") is not None:
                    video_type = str(payload.get("video_type"))
                if payload.get("video_type_confidence") is not None:
                    video_type_confidence = float(payload.get("video_type_confidence"))
                if payload.get("first_person_confidence") is not None:
                    first_person_confidence = float(payload.get("first_person_confidence"))
                labels_raw = payload.get("hit_labels") or []
                if isinstance(labels_raw, list):
                    hit_labels = [str(v) for v in labels_raw]
                elif isinstance(labels_raw, str):
                    hit_labels = [v.strip() for v in labels_raw.split(",") if v.strip()]
                source = "phase3.inline_yolo_api"
            except Exception:
                # API 调用失败时，继续尝试读取 row/fallback 结果文件，保持兼容。
                risk_score = None

        result_path = row.get("yolo_result_json")
        if risk_score is None and not result_path:
            fallback = _resolve_fallback_result_path(submission_id)
            result_path = str(fallback) if fallback else ""
            if fallback:
                source = "fallback.latest_yolo_result.json"
        elif result_path:
            source = "row.yolo_result_json"

        if risk_score is None and not result_path:
            return YoloAuditOutcome(
                yolo_audit={
                    "overall_result": "fail",
                    "reason": "未提供 YOLO 结果（缺少 yolo_risk_score / yolo_result_json）",
                },
                stop=True,
                audit_grade="Error",
                errors=["YOLO 阶段启用但未找到结果输入"],
            )

        if risk_score is None:
            try:
                payload = _load_result_from_file(str(result_path))
                risk_score = float(payload.get("risk_score"))
                if payload.get("both_hands_confidence") is not None:
                    both_hands_confidence = float(payload.get("both_hands_confidence"))
                if payload.get("object_interaction_confidence") is not None:
                    object_interaction_confidence = float(payload.get("object_interaction_confidence"))
                if payload.get("video_type") is not None:
                    video_type = str(payload.get("video_type"))
                if payload.get("video_type_confidence") is not None:
                    video_type_confidence = float(payload.get("video_type_confidence"))
                if payload.get("first_person_confidence") is not None:
                    first_person_confidence = float(payload.get("first_person_confidence"))
                labels_raw = payload.get("hit_labels") or []
                if isinstance(labels_raw, list):
                    hit_labels = [str(v) for v in labels_raw]
                elif isinstance(labels_raw, str):
                    hit_labels = [v.strip() for v in labels_raw.split(",") if v.strip()]
            except Exception as e:
                return YoloAuditOutcome(
                    yolo_audit={"overall_result": "fail", "reason": f"YOLO 结果读取失败: {e}"},
                    stop=True,
                    audit_grade="Error",
                    errors=[f"YOLO 结果读取失败: {e}"],
                )

    if risk_score is None:
        return YoloAuditOutcome(
            yolo_audit={"overall_result": "fail", "reason": "risk_score 缺失"},
            stop=True,
            audit_grade="Error",
            errors=["YOLO 结果缺少 risk_score"],
        )

    row_type = _infer_video_type_from_row(row)
    row_video_type = str(row_type.get("video_type") or "Unknown")
    row_video_type_confidence = float(row_type.get("video_type_confidence") or 0.0)
    yolo_video_type = str(video_type or "Unknown")
    yolo_video_type_confidence = float(video_type_confidence or 0.0)
    type_mismatch_review_conf = _resolve_type_mismatch_review_confidence()

    mismatch_high_conf = (
        row_video_type.lower() != "unknown"
        and yolo_video_type.lower() != "unknown"
        and row_video_type.lower() != yolo_video_type.lower()
        and yolo_video_type_confidence >= type_mismatch_review_conf
    )

    # 业务规则：默认以 task_id/template 信息映射的视频类型为准
    if row_video_type.lower() != "unknown":
        video_type = row_video_type
        video_type_confidence = row_video_type_confidence
        source = f"{source}+row_type_as_primary"
    elif yolo_video_type.lower() != "unknown":
        video_type = yolo_video_type
        video_type_confidence = yolo_video_type_confidence

    hands_ok = (both_hands_confidence or 0.0) >= _resolve_hands_pass_threshold()
    first_ok = (first_person_confidence or 0.0) >= _resolve_first_person_pass_threshold()
    require_first_person = _resolve_require_first_person()
    is_unknown = str(video_type or "").strip().lower() == "unknown"
    s_grade = _resolve_s_grade()
    a_grade = _resolve_a_grade()
    if mismatch_high_conf:
        reason = (
            "YOLO 视频类型与任务映射类型冲突且置信度较高，进入人工审核 "
            f"(task_type={row_video_type}, yolo_type={yolo_video_type}, yolo_conf={yolo_video_type_confidence:.4f})"
        )
        return YoloAuditOutcome(
            yolo_audit={
                "overall_result": "manual_review",
                "reason": reason,
                "risk_score": risk_score,
                "threshold": threshold,
                "both_hands_confidence": both_hands_confidence,
                "object_interaction_confidence": object_interaction_confidence,
                "first_person_confidence": first_person_confidence,
                "video_type": video_type,
                "video_type_confidence": video_type_confidence,
                "yolo_video_type": yolo_video_type,
                "yolo_video_type_confidence": yolo_video_type_confidence,
                "status": "PENDING",
                "result": 4,
                "hit_labels": hit_labels,
                "source": source,
            },
            stop=True,
            audit_grade=a_grade,
            db_update={
                "lightweight_hash": lightweight_hash,
                "phash_hex": phash_hex,
                "cut_count": cut_count,
                "audit_grade": a_grade,
                "task_id": task_id,
            },
        )

    if hands_ok and (first_ok or not require_first_person) and not is_unknown:
        return YoloAuditOutcome(
            yolo_audit={
                "overall_result": "pass",
                "reason": "双手、第一视角与任务类型一致",
                "risk_score": risk_score,
                "threshold": threshold,
                "both_hands_confidence": both_hands_confidence,
                "object_interaction_confidence": object_interaction_confidence,
                "first_person_confidence": first_person_confidence,
                "video_type": video_type,
                "video_type_confidence": video_type_confidence,
                "yolo_video_type": yolo_video_type,
                "yolo_video_type_confidence": yolo_video_type_confidence,
                "status": "ADOPT",
                "result": 5,
                "hit_labels": hit_labels,
                "source": source,
            },
            stop=True,
            audit_grade=s_grade,
            db_update={
                "lightweight_hash": lightweight_hash,
                "phash_hex": phash_hex,
                "cut_count": cut_count,
                "audit_grade": s_grade,
                "task_id": task_id,
            },
        )

    reason = "视频类型为 Unknown，降级为人工审核"
    if not is_unknown:
        reason = (
            "未达到自动通过阈值 "
            f"(hands={both_hands_confidence or 0.0:.4f}, "
            f"object={object_interaction_confidence or 0.0:.4f}, "
            f"first={first_person_confidence or 0.0:.4f}, "
            f"require_first_person={require_first_person}, "
            f"video_type={video_type})"
        )
    return YoloAuditOutcome(
        yolo_audit={
            "overall_result": "manual_review",
            "reason": reason,
            "risk_score": risk_score,
            "threshold": threshold,
            "both_hands_confidence": both_hands_confidence,
            "object_interaction_confidence": object_interaction_confidence,
            "first_person_confidence": first_person_confidence,
            "video_type": video_type,
            "video_type_confidence": video_type_confidence,
            "status": "PENDING",
            "result": 4,
            "hit_labels": hit_labels,
            "source": source,
        },
        stop=True,
        audit_grade=a_grade,
        db_update={
            "lightweight_hash": lightweight_hash,
            "phash_hex": phash_hex,
            "cut_count": cut_count,
            "audit_grade": a_grade,
            "task_id": task_id,
        },
    )

