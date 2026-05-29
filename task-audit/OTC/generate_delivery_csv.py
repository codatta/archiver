from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _iter_rows(results: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, str]]:
    for item in results:
        extracted = item.get("extracted") or {}
        extensions = item.get("extensions")
        if extensions is None:
            extensions = extracted.get("extensions")

        yield {
            "chain": _as_text(extracted.get("chain")),
            "address": _as_text(extracted.get("address")),
            "entities": _as_text(extracted.get("entities")),
            "labels": "otc_desk",
            "source_type": "ground_truth",
            "website_link": _as_text(extracted.get("website_link")),
            "provider": "codatta",
            "provider_source": "osint",
            "screenshot_link": _as_text(extracted.get("screenshot_link")),
            "txid": _as_text(extracted.get("txid")),
            "trace_type": _as_text(extracted.get("trace_type")),
            "extensions": _as_text(extensions if isinstance(extensions, (dict, list)) else extensions),
        }


def _latest_rating_file(output_rating_dir: Path) -> Optional[Path]:
    candidates = sorted(output_rating_dir.glob("rating_results_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def _load_rated_submission_ids(rating_file: Path, target_scores: Set[int]) -> Tuple[Set[str], Dict[str, int]]:
    payload = json.loads(rating_file.read_text(encoding="utf-8-sig"))
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError(f"评级文件格式不正确（缺少 rows 数组）: {rating_file}")

    ids: Set[str] = set()
    score_by_id: Dict[str, int] = {}
    for r in rows:
        if not isinstance(r, dict):
            continue
        sid = r.get("submission_id")
        score = r.get("result")
        if not sid or not isinstance(sid, str):
            continue
        if not isinstance(score, int):
            continue
        score_by_id[sid] = score
        if score in target_scores:
            ids.add(sid)
    return ids, score_by_id


def generate_delivery_csv(
    input_json_path: Path,
    output_dir: Path,
    output_name: Optional[str] = None,
    only_submission_ids: Optional[Set[str]] = None,
) -> Path:
    raw = json.loads(input_json_path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, list):
        raise ValueError(f"输入JSON不是数组: {input_json_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    if not output_name:
        output_name = "otc_delivery.csv"
    output_path = output_dir / output_name

    fieldnames: List[str] = [
        "chain",
        "address",
        "entities",
        "labels",
        "source_type",
        "website_link",
        "provider",
        "provider_source",
        "screenshot_link",
        "txid",
        "trace_type",
        "extensions",
    ]

    with output_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in raw:
            if only_submission_ids is not None:
                sid = item.get("submission_id")
                if not isinstance(sid, str) or sid not in only_submission_ids:
                    continue
            for row in _iter_rows([item]):
                writer.writerow(row)

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="生成 OTC 交付 CSV（从 otc_audit_results.json）")
    parser.add_argument(
        "--input",
        default=str(Path(__file__).resolve().parent / "output" / "otc_audit" / "otc_audit_results.json"),
        help="识别输出 JSON 路径（默认: OTC/output/otc_audit/otc_audit_results.json）",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "output" / "delivery"),
        help="交付输出目录（默认: OTC/output/delivery）",
    )
    parser.add_argument(
        "--output-name",
        default="otc_delivery.csv",
        help="输出文件名（默认: otc_delivery.csv）",
    )
    parser.add_argument(
        "--timestamp",
        action="store_true",
        help="为输出文件名追加时间戳，避免覆盖",
    )
    parser.add_argument(
        "--rating-file",
        default="",
        help="评级汇总 JSON（rating_results_*.json）。不填则自动取 output/output_rating/ 下最新文件",
    )
    parser.add_argument(
        "--score",
        type=int,
        default=0,
        help="只导出指定分数（4 或 5）。=0 表示不按分数过滤",
    )
    parser.add_argument(
        "--split-4-5",
        action="store_true",
        help="同时生成两份：仅5分与仅4分（文件名自动追加 _rating5/_rating4）",
    )
    args = parser.parse_args()

    base_output_name = args.output_name
    if args.timestamp:
        stem = Path(base_output_name).stem
        suffix = Path(base_output_name).suffix or ".csv"
        base_output_name = f"{stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"

    rating_file = Path(args.rating_file) if args.rating_file else _latest_rating_file(
        Path(__file__).resolve().parent / "output" / "output_rating"
    )

    if args.split_4_5:
        if not rating_file:
            raise ValueError("找不到 rating_results_*.json，无法按分数拆分导出")
        ids5, _ = _load_rated_submission_ids(rating_file, {5})
        ids4, _ = _load_rated_submission_ids(rating_file, {4})

        stem = Path(base_output_name).stem
        suffix = Path(base_output_name).suffix or ".csv"
        out5 = generate_delivery_csv(
            input_json_path=Path(args.input),
            output_dir=Path(args.output_dir),
            output_name=f"{stem}_rating5{suffix}",
            only_submission_ids=ids5,
        )
        out4 = generate_delivery_csv(
            input_json_path=Path(args.input),
            output_dir=Path(args.output_dir),
            output_name=f"{stem}_rating4{suffix}",
            only_submission_ids=ids4,
        )
        print(f"[OTC] 已生成交付CSV(仅5分): {out5}")
        print(f"[OTC] 已生成交付CSV(仅4分): {out4}")
        return

    only_ids: Optional[Set[str]] = None
    if args.score in (4, 5):
        if not rating_file:
            raise ValueError("找不到 rating_results_*.json，无法按分数过滤导出")
        only_ids, _ = _load_rated_submission_ids(rating_file, {args.score})

    out_path = generate_delivery_csv(
        input_json_path=Path(args.input),
        output_dir=Path(args.output_dir),
        output_name=base_output_name,
        only_submission_ids=only_ids,
    )
    print(f"[OTC] 已生成交付CSV: {out_path}")


if __name__ == "__main__":
    main()

