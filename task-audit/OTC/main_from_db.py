"""
OTC 从数据库读取提交并执行截图审核
使用 OTC/.env 中的 DB_* 与 QWEN_* 配置，从 MySQL 读取 data_submission，用 Qwen 视觉模型分析截图。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# 确保 OTC 目录在 path 中并优先加载 OTC/.env
_otc_root = Path(__file__).resolve().parent
if str(_otc_root) not in sys.path:
    sys.path.insert(0, str(_otc_root.parent))
try:
    from dotenv import load_dotenv
    _env = _otc_root / ".env"
    if _env.exists():
        load_dotenv(_env)
except Exception:
    pass

try:
    from OTC.db_client import SubmissionDBClient
    from OTC.otc_audit.models import OTCSubmission, OTCAuditResult
    from OTC.otc_audit.otc_qwen_auditor import OTCQwenAuditor
except ImportError:
    from db_client import SubmissionDBClient
    from otc_audit.models import OTCSubmission, OTCAuditResult
    from otc_audit.otc_qwen_auditor import OTCQwenAuditor


def _parse_data_submission(data_submission) -> dict:
    """data_submission 可能是 JSON 字符串或已是 dict。"""
    if data_submission is None:
        return {}
    if isinstance(data_submission, dict):
        return data_submission
    if isinstance(data_submission, str):
        try:
            return json.loads(data_submission)
        except json.JSONDecodeError:
            return {}
    return {}


def _get_screenshot_url(data: dict) -> str:
    """从 data_submission 中解析截图 URL。支持 data.screenshot.url 或 screenshot.url。"""
    data_inner = data.get("data") or data
    screenshot = (data_inner.get("screenshot") or {}) if isinstance(data_inner, dict) else {}
    url = screenshot.get("url") if isinstance(screenshot, dict) else None
    return (url or "").strip()


def _submission_from_row(row: dict) -> OTCSubmission | None:
    """将数据库一行转为 OTCSubmission。"""
    submission_id = str(row.get("submission_id") or "")
    data = _parse_data_submission(row.get("data_submission"))
    url = _get_screenshot_url(data)
    if not url:
        return None
    inner = data.get("data") or data
    if not isinstance(inner, dict):
        inner = {}
    return OTCSubmission(
        submission_id=submission_id,
        screenshot_url=url,
        chain=inner.get("chain") or "",
        address=inner.get("address") or "",
        otc_desk=inner.get("otcDesk") or "",
        raw_data=row,
    )


def main():
    import argparse
    parser = argparse.ArgumentParser(description="OTC 从数据库读取并审核交易所截图（Qwen 视觉）")
    parser.add_argument("--limit", type=int, default=None, help="最多读取条数")
    parser.add_argument("--offset", type=int, default=0, help="偏移量")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="结果 JSON 路径，默认 OTC/output/otc_audit/otc_audit_results.json",
    )
    args = parser.parse_args()

    out_path = Path(args.output or str(_otc_root / "output" / "otc_audit" / "otc_audit_results.json"))
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("[OTC] 从数据库加载提交...")
    client = SubmissionDBClient()
    rows = client.fetch_submissions(limit=args.limit, offset=args.offset)
    print(f"[OTC] 共读取 {len(rows)} 条")

    submissions: list[OTCSubmission] = []
    for row in rows:
        sub = _submission_from_row(row)
        if sub:
            submissions.append(sub)
        else:
            sid = row.get("submission_id", "?")
            print(f"[OTC] 跳过无截图 URL: submission_id={sid}")

    if not submissions:
        print("[OTC] 没有可审核的记录，退出")
        return

    auditor = OTCQwenAuditor()
    results: list[dict] = []
    for i, sub in enumerate(submissions, 1):
        print(f"[OTC] 审核 {i}/{len(submissions)} submission_id={sub.submission_id}")
        result = auditor.audit(sub)
        results.append(result.to_dict())

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[OTC] 结果已写入: {out_path}")


if __name__ == "__main__":
    main()
