"""
OTC 一键执行入口：截图识别 + 自动评级 + 交付CSV生成

执行顺序：
1. OTC.main_from_db.main()        从数据库读取 data_submission，调用 Qwen 识别截图
2. OTC.otc_rating.main.main()     读取识别结果 + DB，自动更新 status/result 与 txid
3. OTC.generate_delivery_csv      基于识别结果 + 最新 rating_results_*.json 生成交付 CSV（4分/5分各一份）
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

_otc_root = Path(__file__).resolve().parent
if str(_otc_root.parent) not in sys.path:
    sys.path.insert(0, str(_otc_root.parent))

from OTC import main_from_db  # type: ignore[import-error]
from OTC.otc_rating import main as rating_main  # type: ignore[import-error]
from OTC import generate_delivery_csv as deliver  # type: ignore[import-error]


def main() -> None:
    parser = argparse.ArgumentParser(description="OTC 一键执行：识别 + 评级 + 交付CSV")
    parser.add_argument("--skip-recognition", action="store_true", help="跳过识别阶段（复用已有 otc_audit_results.json）")
    parser.add_argument("--skip-rating", action="store_true", help="跳过评级阶段（不写回DB，也不生成新的 rating_results_*.json）")
    parser.add_argument("--skip-delivery", action="store_true", help="跳过交付CSV生成阶段")
    parser.add_argument(
        "--results",
        type=str,
        default=str(_otc_root / "output" / "otc_audit" / "otc_audit_results.json"),
        help="识别结果 JSON 路径（默认: OTC/output/otc_audit/otc_audit_results.json）",
    )
    args = parser.parse_args()

    if not args.skip_recognition:
        print("[RUN_ALL] Step 1/3: 截图识别（Qwen 审核）...")
        main_from_db.main()
    else:
        print("[RUN_ALL] Step 1/3: 已跳过识别阶段。")

    if not args.skip_rating:
        print("[RUN_ALL] Step 2/3: 自动评级写回数据库...")
        rating_main.main()
    else:
        print("[RUN_ALL] Step 2/3: 已跳过评级阶段。")

    if not args.skip_delivery:
        print("[RUN_ALL] Step 3/3: 生成交付 CSV（仅4分/仅5分）...")
        # 直接复用脚本逻辑：按最新 rating_results_*.json 拆分导出
        deliver.generate_delivery_csv  # ensure module loaded
        # 调用其 main() 会解析 sys.argv，不适合这里；直接调用其核心函数组合导出
        rating_file = deliver._latest_rating_file(_otc_root / "output" / "output_rating")  # type: ignore[attr-defined]
        if not rating_file:
            raise ValueError("找不到 rating_results_*.json，无法生成按4/5分拆分的交付CSV")
        ids5, _ = deliver._load_rated_submission_ids(rating_file, {5})  # type: ignore[attr-defined]
        ids4, _ = deliver._load_rated_submission_ids(rating_file, {4})  # type: ignore[attr-defined]
        out_dir = _otc_root / "output" / "delivery"
        deliver.generate_delivery_csv(Path(args.results), out_dir, "otc_delivery_rating5.csv", ids5)
        deliver.generate_delivery_csv(Path(args.results), out_dir, "otc_delivery_rating4.csv", ids4)
        print("[RUN_ALL] 交付 CSV 已生成到 OTC/output/delivery/")
    else:
        print("[RUN_ALL] Step 3/3: 已跳过交付CSV生成阶段。")

    print("[RUN_ALL] 全部完成。")


if __name__ == "__main__":
    main()

