"""
综合视频审核编排器：按 Phase 0 → 1 → 2 → 3 顺序调用各阶段包，并回写数据库。
"""

from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime
from typing import Any, Dict, List

import httpx

from db_client import VideoAuditDBClient
from phase0_duplicate_check.duplicate_auditor import run_duplicate_check
from phase1_metadata_check.metadata_auditor import run_metadata_check
from phase2_scene_cut_check.scene_cut_auditor import run_scene_cut_check
from phase3_yolo_audit.yolo_auditor import run_yolo_audit
from video_common.ffprobe_utils import ffprobe_json, parse_duration_seconds, pick_video_stream
from video_common.row_utils import resolve_task_id, resolve_video_path, resolve_video_hash


class VideoAuditor:
    """串联 phase0_duplicate_check / phase1_metadata_check / phase2_scene_cut_check / phase3_yolo_audit。"""

    def __init__(
        self,
        db: VideoAuditDBClient,
        *,
        batch_video_hash_index: Dict[str, List[str]],
        batch_first_submission_by_hash: Dict[str, str],
    ) -> None:
        self.db = db
        self.batch_video_hash_index = batch_video_hash_index
        self.batch_first_submission_by_hash = batch_first_submission_by_hash

    def _download_video_to_temp(self, url: str, submission_id: str) -> str:
        temp_root = os.getenv("VIDEO_DOWNLOAD_TEMP_DIR") or tempfile.gettempdir()
        out_dir = os.path.join(temp_root, "video_audit_downloads")
        os.makedirs(out_dir, exist_ok=True)
        ext = os.path.splitext(url.split("?")[0])[1] or ".mp4"
        out_path = os.path.join(out_dir, f"{submission_id}{ext}")
        with httpx.stream("GET", url, timeout=180.0, follow_redirects=True) as resp:
            resp.raise_for_status()
            with open(out_path, "wb") as f:
                for chunk in resp.iter_bytes():
                    if chunk:
                        f.write(chunk)
        return out_path

    def _cleanup_temp_video(self, path: str) -> None:
        if not path:
            return
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass

    def _cleanup_pre_frames_if_needed(self, submission_id: str) -> None:
        raw = str(os.getenv("POST_AUDIT_DELETE_PRE_FRAMES", "0")).strip().lower()
        enabled = raw in {"1", "true", "yes", "on"}
        if not enabled:
            return
        base = os.getenv("PRE_FRAME_OUTPUT_DIR", "output/pre_frames")
        target = os.path.join(base, submission_id)
        try:
            if os.path.isdir(target):
                shutil.rmtree(target, ignore_errors=True)
        except Exception:
            pass

    def audit_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = str(row.get("submission_id") or "").strip()
        ts = datetime.now().isoformat()
        base: Dict[str, Any] = {
            "submission_id": submission_id,
            "timestamp": ts,
            "errors": [],
            "yolo_audit": {"overall_result": "skipped"},
        }

        if not submission_id:
            base["errors"].append("缺少 submission_id")
            base["duplicate_audit"] = {"overall_result": "skipped", "checks": []}
            base["metadata_audit"] = {"overall_result": "skipped", "checks": []}
            base["scene_cut_audit"] = {"overall_result": "skipped"}
            base["audit_grade"] = "Error"
            return base

        temp_video_path = ""
        try:
            video_path = resolve_video_path(row)
            if str(video_path).startswith(("http://", "https://")):
                temp_video_path = self._download_video_to_temp(video_path, submission_id)
                video_path = temp_video_path
        except ValueError as e:
            base["errors"].append(str(e))
            base["duplicate_audit"] = {"overall_result": "skipped", "checks": []}
            base["metadata_audit"] = {"overall_result": "skipped", "checks": []}
            base["scene_cut_audit"] = {"overall_result": "skipped"}
            base["audit_grade"] = "Error"
            return base

        try:
            if not os.path.isfile(video_path):
                base["errors"].append(f"视频文件不存在: {video_path}")
                base["duplicate_audit"] = {"overall_result": "skipped", "checks": []}
                base["metadata_audit"] = {"overall_result": "skipped", "checks": []}
                base["scene_cut_audit"] = {"overall_result": "skipped"}
                base["audit_grade"] = "Error"
                return base

            task_id = resolve_task_id(row)
            try:
                video_hash = resolve_video_hash(row)
            except Exception:
                video_hash = None

            try:
                fp = ffprobe_json(video_path)
                duration = parse_duration_seconds(fp)
                vstream = pick_video_stream(fp)
                if not vstream:
                    raise RuntimeError("未找到视频流")
                width = int(vstream.get("width") or 0)
                height = int(vstream.get("height") or 0)
            except Exception as e:
                base["errors"].append(f"ffprobe 失败: {e}")
                base["duplicate_audit"] = {"overall_result": "skipped", "checks": []}
                base["metadata_audit"] = {"overall_result": "skipped", "checks": []}
                base["scene_cut_audit"] = {"overall_result": "skipped"}
                base["audit_grade"] = "Error"
                return base

            try:
                size_b = (
                    int(row["file_size_bytes"])
                    if row.get("file_size_bytes") is not None
                    else os.path.getsize(video_path)
                )
            except Exception:
                size_b = os.path.getsize(video_path)

            lightweight_hash = video_hash or f"{size_b}_{duration:.3f}"

            dup_out = run_duplicate_check(
                self.db,
                submission_id=submission_id,
                task_id=task_id,
                video_path=video_path,
                lightweight_hash=lightweight_hash,
                duration_sec=duration,
                video_hash=video_hash,
                batch_video_hash_index=self.batch_video_hash_index,
                batch_first_submission_by_hash=self.batch_first_submission_by_hash,
            )
            base["duplicate_audit"] = dup_out.duplicate_audit
            base["errors"].extend(dup_out.errors)
            if dup_out.stop:
                base["metadata_audit"] = {"overall_result": "skipped", "checks": []}
                base["scene_cut_audit"] = {"overall_result": "skipped"}
                base["audit_grade"] = dup_out.audit_grade or "Error"
                if dup_out.db_update:
                    self._safe_update(submission_id, base, dup_out.db_update)
                return base

            phash_hex = dup_out.phash_hex

            meta_out = run_metadata_check(
                width=width,
                height=height,
                duration_sec=duration,
                lightweight_hash=lightweight_hash,
                phash_hex=phash_hex,
                task_id=task_id,
            )
            base["metadata_audit"] = meta_out.metadata_audit
            if meta_out.stop:
                base["scene_cut_audit"] = {"overall_result": "skipped"}
                base["audit_grade"] = meta_out.audit_grade or "C"
                if meta_out.db_update:
                    self._safe_update(submission_id, base, meta_out.db_update)
                return base

            try:
                phase2_max_cuts = int(os.getenv("PHASE2_MAX_CUTS", "30"))
            except ValueError:
                phase2_max_cuts = 30

            sc_out = run_scene_cut_check(
                video_path,
                lightweight_hash=lightweight_hash,
                phash_hex=phash_hex,
                task_id=task_id,
                max_cuts=phase2_max_cuts,
            )
            base["scene_cut_audit"] = sc_out.scene_cut_audit
            base["errors"].extend(sc_out.errors)
            if sc_out.stop:
                base["yolo_audit"] = {"overall_result": "skipped"}
                base["audit_grade"] = sc_out.audit_grade or "Error"
                if sc_out.db_update and sc_out.audit_grade != "Error":
                    self._safe_update(submission_id, base, sc_out.db_update)
                return base

            yolo_out = run_yolo_audit(
                row,
                submission_id=submission_id,
                video_path=video_path,
                task_id=task_id,
                lightweight_hash=lightweight_hash,
                phash_hex=phash_hex,
                cut_count=sc_out.cut_count,
            )
            base["yolo_audit"] = yolo_out.yolo_audit
            base["errors"].extend(yolo_out.errors)
            if yolo_out.stop:
                base["audit_grade"] = yolo_out.audit_grade or "Error"
                if yolo_out.db_update and yolo_out.audit_grade != "Error":
                    self._safe_update(submission_id, base, yolo_out.db_update)
                return base

            base["audit_grade"] = yolo_out.audit_grade or "A"
            if sc_out.db_update:
                # fallback：当 YOLO 未给出回写字段时，沿用 Phase 2 回写。
                self._safe_update(submission_id, base, sc_out.db_update)
            return base
        finally:
            self._cleanup_temp_video(temp_video_path)
            self._cleanup_pre_frames_if_needed(submission_id)

    def _safe_update(self, submission_id: str, base: Dict[str, Any], fields: Dict[str, Any]) -> None:
        try:
            self.db.update_video_status(submission_id, **fields)
        except Exception as ue:
            base["errors"].append(f"回写数据库失败: {ue}")


__all__ = ["VideoAuditor"]
