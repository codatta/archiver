from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=True)
except Exception:
    pass

from db_client import SubmissionDBClient
from robotics_audit.pipeline import AuditPipeline


def _load_rows_from_json(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and isinstance(data.get("rows"), list):
        return data["rows"]
    raise ValueError("JSON 输入需为数组，或包含 rows 数组的对象")


def _write_csv(path: Path, results: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "submission_id",
        "task_id",
        "template_id",
        "user_id",
        "audit_grade",
        "passed",
        "status",
        "result",
        "reference_check",
        "rule_phase_grade",
        "segment_count",
        "violation_count",
        "violation_summary",
    ]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in results:
            violations = item.get("violations") or []
            writer.writerow(
                {
                    "submission_id": item.get("submission_id"),
                    "task_id": item.get("task_id"),
                    "template_id": item.get("template_id"),
                    "user_id": item.get("user_id"),
                    "audit_grade": item.get("audit_grade"),
                    "passed": item.get("passed"),
                    "status": item.get("status"),
                    "result": item.get("result"),
                    "reference_check": item.get("reference_check"),
                    "rule_phase_grade": item.get("rule_phase_grade"),
                    "segment_count": item.get("segment_count"),
                    "violation_count": len(violations),
                    "violation_summary": " | ".join(v.get("message", "") for v in violations[:5]),
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="ROBSTIC001 机器人任务批量审核")
    parser.add_argument("--input", type=str, default=None, help="本地 JSON 输入")
    parser.add_argument("--limit", type=int, default=None, help="最多处理条数")
    parser.add_argument("--offset", type=int, default=0, help="偏移量")
    parser.add_argument(
        "--output",
        type=str,
        default=str(ROOT / "output" / "audit_results.json"),
        help="完整结果 JSON 路径",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default=str(ROOT / "output" / "audit_results.csv"),
        help="摘要 CSV 路径",
    )
    parser.add_argument(
        "--reference-dir",
        type=str,
        default=str(ROOT / "output" / "task_reference"),
        help="task 参考 JSON 缓存目录",
    )
    parser.add_argument("--segment-config", type=str, default=None)
    parser.add_argument("--metadata-config", type=str, default=None)
    parser.add_argument(
        "--enable-llm-text-check",
        action="store_true",
        help="完整审核：前置规则 + 视觉参考 + 大模型文本比对 + JSON 参考对比",
    )
    parser.add_argument(
        "--skip-json-reference-check",
        action="store_true",
        help="与 --enable-llm-text-check 联用时，跳过后续 JSON 参考 token 对比",
    )
    parser.add_argument(
        "--enable-local-reference-check",
        action="store_true",
        help="使用本地 token 重叠对照（不推荐，不能识别同义词）",
    )
    parser.add_argument(
        "--enable-vision-llm",
        action="store_true",
        help="参考 JSON 缺失时，对每个 task_id 调用一次视觉大模型（可选）",
    )
    parser.add_argument(
        "--write-db",
        action="store_true",
        help="审核后将 status/result 写回数据库",
    )
    args = parser.parse_args()

    pipeline = AuditPipeline(
        reference_dir=Path(args.reference_dir),
        enable_llm_text_check=args.enable_llm_text_check,
        enable_json_reference_check=not args.skip_json_reference_check,
        enable_local_reference_check=args.enable_local_reference_check,
        enable_vision_llm=args.enable_vision_llm,
        segment_config=args.segment_config,
        metadata_config=args.metadata_config,
    )

    if args.input:
        rows = _load_rows_from_json(Path(args.input))
        print(f"[audit] 从本地 JSON 读取 {len(rows)} 条")
    else:
        client = SubmissionDBClient()
        rows = client.fetch_submissions(limit=args.limit, offset=args.offset)
        print(f"[audit] 从数据库读取 {len(rows)} 条")

    audit_results = pipeline.audit_rows(rows)
    results = [item.to_dict() for item in audit_results]

    db_write_stats = None
    if args.write_db:
        db_client = SubmissionDBClient()
        db_write_stats = db_client.write_audit_results(results)
        print(
            "[db] 写库汇总: "
            f"attempted={db_write_stats['attempted']} "
            f"success={db_write_stats['success']} "
            f"failed={db_write_stats['failed']} "
            f"skipped={db_write_stats['skipped']}"
        )
    else:
        print("[db] 未写回数据库（如需写库请加 --write-db）")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now().isoformat(),
        "total": len(results),
        "grade_distribution": dict(Counter(r["audit_grade"] for r in results)),
        "passed_count": sum(1 for r in results if r.get("passed")),
        "reference_dir": args.reference_dir,
        "write_db": bool(args.write_db),
        "db_write": db_write_stats,
        "results": results,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    _write_csv(Path(args.csv), results)

    print(f"[audit] 完成: 共 {len(results)} 条, S级通过 {payload['passed_count']} 条")
    print(f"[audit] 等级分布: {payload['grade_distribution']}")
    print(f"[audit] JSON: {out_path}")
    print(f"[audit] CSV:  {args.csv}")


if __name__ == "__main__":
    main()
