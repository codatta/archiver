"""
视频自动化审核流水线 — 主入口。
参考 cex_hot_wallet/main_audit/main_auditor.py：从项目根加载 .env，支持命令行分页参数，输出 JSON。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from db_client import VideoAuditDBClient
from main_audit import VideoAuditor, build_rating_results, summarize_comprehensive
from video_common.row_utils import resolve_video_hash


def _load_env(project_root: Path) -> None:
    try:
        from dotenv import dotenv_values, load_dotenv

        env_file = project_root / ".env"
        if env_file.exists():
            # 先常规加载，再强制覆盖（包括空值），防止旧终端环境变量污染。
            load_dotenv(env_file, override=True)
            parsed = dotenv_values(env_file)
            for k, v in parsed.items():
                if not k:
                    continue
                os.environ[k] = "" if v is None else str(v)
    except ImportError:
        pass


def _save_json(data: Dict[str, Any], path: Path) -> bool:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"错误: 保存 JSON 失败 {path}: {e}")
        return False


def run_audit(
    *,
    limit: Optional[int],
    offset: int,
    comprehensive_path: Path,
    rating_path: Path,
) -> int:
    if not os.getenv("DB_PENDING_VIDEOS_SQL") and not os.getenv("DB_PENDING_VIDEOS_SQL_FILE"):
        print("错误: 请配置 DB_PENDING_VIDEOS_SQL（或 DB_PENDING_VIDEOS_SQL_FILE）")
        return 2

    if not os.getenv("DB_VIDEO_META_TABLE"):
        print(
            "警告: 未设置 DB_VIDEO_META_TABLE，Phase 0 将无法在库内比对 lightweight_hash / pHash；"
            "仅依赖本地 ffprobe / 抽帧逻辑。"
        )

    db = VideoAuditDBClient()
    rows = db.fetch_pending_videos(limit=limit, offset=offset)
    if not rows:
        print("没有待审核视频记录。")
        comp = {
            "result": "success",
            "audit_results": [],
            "summary": {"total": 0, "success": 0, "with_errors": 0},
        }
        _save_json(comp, comprehensive_path)
        _save_json(
            {
                "result": "success",
                "timestamp": datetime.now().isoformat(),
                "summary": {"total": 0, "audit_grade_distribution": {}},
                "rated_results": [],
            },
            rating_path,
        )
        return 0

    # 批次内重复检测索引：video.hash -> [submission_id...]
    # 同时记录该 hash 在本批次最早提交的 submission_id（按 gmt_create）。
    batch_hash_index: Dict[str, List[str]] = {}
    batch_hash_first_submission: Dict[str, str] = {}
    batch_hash_first_key: Dict[str, tuple] = {}
    for r in rows:
        sid = str(r.get("submission_id") or "").strip()
        if not sid:
            continue
        try:
            h = resolve_video_hash(r)
            batch_hash_index[h] = batch_hash_index.get(h, []) + [sid]
            raw_time = str(r.get("gmt_create") or "").strip()
            try:
                dt = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
                sort_key = (0, dt, sid)
            except Exception:
                # gmt_create 缺失/异常时，降级到 submission_id 字典序，确保行为稳定
                sort_key = (1, datetime.max, sid)
            prev = batch_hash_first_key.get(h)
            if prev is None or sort_key < prev:
                batch_hash_first_key[h] = sort_key
                batch_hash_first_submission[h] = sid
        except Exception:
            # 缺少 hash 不影响后续流程，但 Phase0 会把它当作无法去重的错误
            continue

    auditor = VideoAuditor(
        db,
        batch_video_hash_index=batch_hash_index,
        batch_first_submission_by_hash=batch_hash_first_submission,
    )

    print(f"共 {len(rows)} 条待审核，开始流水线…")
    audit_results: List[Dict[str, Any]] = []
    for i, row in enumerate(rows, 1):
        sid = row.get("submission_id", "")
        print(f"[{i}/{len(rows)}] {sid}")
        audit_results.append(auditor.audit_row(row))

    summary = summarize_comprehensive(audit_results)
    comprehensive: Dict[str, Any] = {
        "result": "success",
        "audit_results": audit_results,
        "summary": summary,
    }
    if not _save_json(comprehensive, comprehensive_path):
        return 1

    rating_doc = build_rating_results(audit_results)
    if not _save_json(rating_doc, rating_path):
        return 1

    print(f"\n已写入:\n  - {comprehensive_path}\n  - {rating_path}")
    print(
        f"汇总: total={summary['total']} success={summary['success']} "
        f"with_errors={summary['with_errors']}"
    )
    return 0


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    _load_env(script_dir)

    default_out = script_dir / "output"
    parser = argparse.ArgumentParser(description="视频自动化审核（Phase 0-3）")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(default_out),
        help="输出目录（默认: 项目下 output/）",
    )
    parser.add_argument(
        "--db-limit",
        type=int,
        default=None,
        help="待审核列表 limit（传给 SQL 的 {limit}）",
    )
    parser.add_argument(
        "--db-offset",
        type=int,
        default=0,
        help="待审核列表 offset（传给 SQL 的 {offset}）",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    comprehensive_path = out_dir / "comprehensive_audit_results.json"
    rating_path = out_dir / "rating_results.json"

    lim = args.db_limit
    if lim is None and os.getenv("DB_LIMIT"):
        try:
            lim = int(os.getenv("DB_LIMIT", ""))
        except ValueError:
            print("警告: DB_LIMIT 无法解析为整数，将忽略")

    off = args.db_offset
    if os.getenv("DB_OFFSET"):
        try:
            off = int(os.getenv("DB_OFFSET", str(off)))
        except ValueError:
            pass

    code = run_audit(
        limit=lim,
        offset=off,
        comprehensive_path=comprehensive_path,
        rating_path=rating_path,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
