"""
OTC 截图审核评级入口

输入：
- OTC/output/otc_audit/otc_audit_results.json  （由 OTC.main_from_db + Qwen 生成）
- 数据库 cfp_task_submission 中对应 submission_id 的 data_submission

输出：
- 更新数据库中该 submission 的 status / result 字段
- 回写 otc_audit_results.json（补充 screenshot_link 已自动写入，必要时可扩展 txid）
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import pymysql
from pymysql.cursors import DictCursor

_otc_root = Path(__file__).resolve().parents[1]
if str(_otc_root.parent) not in sys.path:
    sys.path.insert(0, str(_otc_root.parent))

try:
    from dotenv import load_dotenv

    load_dotenv(_otc_root / ".env")
except Exception:
    pass

from OTC.db_client import SubmissionDBClient  # type: ignore[import-error]


def _normalize_chain_enum(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    c = str(raw).strip().lower()
    mapping = {
        "eth": "ethereum_mainnet",
        "ethereum": "ethereum_mainnet",
        "erc20": "ethereum_mainnet",
        "ethereum mainnet": "ethereum_mainnet",
        "ethereum_mainnet": "ethereum_mainnet",
        "tron": "tron_mainnet",
        "trx": "tron_mainnet",
        "tron mainnet": "tron_mainnet",
        "tron_mainnet": "tron_mainnet",
        "bnb": "bnb_chain_mainnet",
        "bsc": "bnb_chain_mainnet",
        "binance smart chain": "bnb_chain_mainnet",
        "bnb_chain_mainnet": "bnb_chain_mainnet",
        "btc": "bitcoin_mainnet",
        "bitcoin": "bitcoin_mainnet",
        "bitcoin mainnet": "bitcoin_mainnet",
        "bitcoin_mainnet": "bitcoin_mainnet",
        "sol": "solana_mainnet",
        "solana": "solana_mainnet",
        "solana mainnet": "solana_mainnet",
        "solana_mainnet": "solana_mainnet",
        "polygon": "polygon_mainnet",
        "matic": "polygon_mainnet",
        "polygon mainnet": "polygon_mainnet",
        "polygon_mainnet": "polygon_mainnet",
        "arb": "arbitrum_one",
        "arbitrum": "arbitrum_one",
        "arbitrum one": "arbitrum_one",
        "arbitrum_one": "arbitrum_one",
        "op": "optimism_mainnet",
        "optimism": "optimism_mainnet",
        "optimism mainnet": "optimism_mainnet",
        "optimism_mainnet": "optimism_mainnet",
        "avax": "avalanche_c_chain",
        "avalanche": "avalanche_c_chain",
        "avalanche c chain": "avalanche_c_chain",
        "avalanche_c_chain": "avalanche_c_chain",
        "base": "base_mainnet",
        "base mainnet": "base_mainnet",
        "base_mainnet": "base_mainnet",
        "ltc": "litecoin_mainnet",
        "litecoin": "litecoin_mainnet",
        "litecoin mainnet": "litecoin_mainnet",
        "litecoin_mainnet": "litecoin_mainnet",
    }
    # 处理类似 "TRON TRC20"、"BSC-USDT" 这种组合
    for key, val in mapping.items():
        if key in c:
            return val
    return None


def _parse_data_submission(data_submission: Any) -> Dict[str, Any]:
    if data_submission is None:
        return {}
    if isinstance(data_submission, dict):
        return data_submission
    if isinstance(data_submission, str):
        try:
            return json.loads(data_submission)
        except Exception:
            return {}
    return {}


def _extract_db_fields(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    从 data_submission 中提取用于比对的字段：
    - chain_raw
    - address
    - otcDesk（作为 labels 真值）
    - hash_raw
    """
    inner = data.get("data") or data
    if not isinstance(inner, dict):
        inner = {}
    chain_raw = inner.get("chain")
    address = inner.get("address")
    otc_desk = inner.get("otcDesk")
    hash_raw = inner.get("hash")
    if not hash_raw and isinstance(inner.get("screenshot"), dict):
        hash_raw = inner["screenshot"].get("hash")
    return chain_raw, address, otc_desk, hash_raw


def _valid_hash_format(hash_raw: Optional[str]) -> bool:
    if not hash_raw or not isinstance(hash_raw, str):
        return False
    h = hash_raw.strip()
    if h.startswith("0x"):
        h_body = h[2:]
    else:
        h_body = h
    if len(h_body) not in (64, 66):
        return False
    try:
        int(h_body, 16)
        return True
    except ValueError:
        return False


def _normalize_txid(hash_raw: Optional[str]) -> str:
    """用于去重比对的 txid 规范化（strip + lower）。"""
    if not hash_raw or not isinstance(hash_raw, str):
        return ""
    return hash_raw.strip().lower()


def _normalize_address_for_dedup(addr: Optional[str]) -> str:
    """用于去重比对的 address 规范化（strip + lower）。"""
    if not addr or not isinstance(addr, str):
        return ""
    return addr.strip().lower()


def _load_audit_results(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"未找到审核结果文件: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _update_db_status(conn, submission_id: str, status: str, result: int) -> None:
    with conn.cursor() as cursor:
        cursor.execute(
            "UPDATE cfp_task_submission SET status=%s, result=%s WHERE submission_id=%s",
            (status, result, submission_id),
        )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="OTC 截图审核结果评级写回数据库")
    parser.add_argument(
        "--results",
        type=str,
        default=str(_otc_root / "output" / "otc_audit" / "otc_audit_results.json"),
        help="审核结果 JSON 路径",
    )
    args = parser.parse_args()

    results_path = Path(args.results)
    print(f"[RATING] 读取审核结果: {results_path}")
    audit_results = _load_audit_results(results_path)

    # 构建 submission_id -> result 映射
    audit_map: Dict[str, Dict[str, Any]] = {}
    for item in audit_results:
        sid = str(item.get("submission_id") or "")
        if sid:
            audit_map[sid] = item

    submission_ids = list(audit_map.keys())
    if not submission_ids:
        print("[RATING] 没有可评级的记录，退出")
        return

    print(f"[RATING] 准备从数据库拉取 {len(submission_ids)} 条 data_submission")
    db_client = SubmissionDBClient()
    db_rows = db_client.fetch_submissions(limit=None, offset=0, submission_ids=submission_ids)
    db_map: Dict[str, Dict[str, Any]] = {str(r.get("submission_id")): r for r in db_rows}

    # 去重集合：本任务内已采纳的 txid / address（跨 user_id 唯一，优先级最高）
    committed_txids: set = set()
    committed_addresses: set = set()
    try:
        adopted_rows = db_client.fetch_adopted_submissions()
        for row in adopted_rows:
            data_obj = _parse_data_submission(row.get("data_submission"))
            _, addr_db, _, hash_raw = _extract_db_fields(data_obj)
            t = _normalize_txid(hash_raw)
            a = _normalize_address_for_dedup(addr_db)
            if t:
                committed_txids.add(t)
            if a:
                committed_addresses.add(a)
        if committed_txids or committed_addresses:
            print(f"[RATING] 已加载已采纳去重集合: txid={len(committed_txids)}, address={len(committed_addresses)}")
    except Exception as e:
        print(f"[RATING] 拉取已采纳记录失败，仅做当批去重: {e}")

    # DB 连接（复用 OTC/.env 中的 DB_*）
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3306"))
    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    database = os.getenv("DB_NAME", "")
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        cursorclass=DictCursor,
        autocommit=True,
        charset="utf8mb4",
    )

    rating_rows: List[Dict[str, Any]] = []

    def _record_rating(submission_id: str, status: str, result: int, reasons: List[str]) -> None:
        rating_rows.append(
            {
                "submission_id": submission_id,
                "status": status,
                "result": int(result),
                "passed": status == "ADOPT" and int(result) == 5,
                "reasons": reasons,
            }
        )

    try:
        for sid, rec in audit_map.items():
            extracted = rec.get("extracted") or {}

            # 0) 必须有 DB 行才能做后续校验（含去重）
            db_row = db_map.get(sid)
            if not db_row:
                print(f"[RATING] submission_id={sid} 未在 DB_SUBMISSIONS_SQL 结果中找到对应行，跳过对比")
                _update_db_status(conn, sid, "REFUSED", 4)
                _record_rating(sid, "REFUSED", 4, ["DB row not found for submission_id (not in DB_SUBMISSIONS_SQL result)"])
                continue

            data_obj = _parse_data_submission(db_row.get("data_submission"))
            chain_raw, addr_db, otc_desk, hash_raw = _extract_db_fields(data_obj)
            txid_norm = _normalize_txid(hash_raw)
            addr_norm = _normalize_address_for_dedup(addr_db)

            # 1) 【最高优先级】txid/address 重复拦截（跨 user_id 唯一）
            if (txid_norm and txid_norm in committed_txids) or (addr_norm and addr_norm in committed_addresses):
                reasons = ["txid/address已被提交过"]
                print(f"[RATING] submission_id={sid} txid/address 已被提交过 → REFUSED, result=1")
                _update_db_status(conn, sid, "REFUSED", 1)
                _record_rating(sid, "REFUSED", 1, reasons)
                continue

            # 2) 图片质量检查
            img_q = rec.get("image_quality") or {}
            clear = img_q.get("clear")
            tampered = img_q.get("tampered")
            readable = img_q.get("text_readable")
            if clear is not True or tampered is not False or readable is not True:
                reasons = [
                    "Image quality mismatch",
                    f"clear={clear}, tampered={tampered}, text_readable={readable}",
                ]
                print(f"[RATING] submission_id={sid} 图片质量不符合标准 → REFUSED, result=1")
                _update_db_status(conn, sid, "REFUSED", 1)
                _record_rating(sid, "REFUSED", 1, reasons)
                continue

            # 3) 字段缺失检查
            chain = extracted.get("chain")
            address = extracted.get("address")
            entities = extracted.get("entities")
            labels = extracted.get("labels")
            key_fields = {
                "chain": chain,
                "address": address,
                "entities": entities,
                "labels": labels,
            }
            missing = [k for k, v in key_fields.items() if v in (None, "", [])]
            if len(missing) >= 2:
                reasons = [f"Key fields missing >=2: {missing}"]
                print(f"[RATING] submission_id={sid} 关键字段缺失 >=2 ({missing}) → REFUSED, result=2")
                _update_db_status(conn, sid, "REFUSED", 2)
                _record_rating(sid, "REFUSED", 2, reasons)
                continue
            if len(missing) == 1:
                m = missing[0]
                reasons = [f"Key field missing: {m}"]
                if m == "address":
                    reasons.append("Address missing")
                if m in ("entities", "labels"):
                    reasons.append("Unknown identity")
                print(f"[RATING] submission_id={sid} 关键字段缺失 1 个 ({missing}) → REFUSED, result=3")
                _update_db_status(conn, sid, "REFUSED", 3)
                _record_rating(sid, "REFUSED", 3, reasons)
                continue

            # 4) 与 DB 中 data_submission 的字段对比
            chain_db_enum = _normalize_chain_enum(chain_raw)

            mismatch_reasons: List[str] = []

            # 链比对
            if chain is not None and chain_db_enum is not None and chain != chain_db_enum:
                mismatch_reasons.append(f"chain mismatch: audit={chain}, db={chain_db_enum}")

            # 地址比对（大小写忽略）
            if address and addr_db and str(address).strip().lower() != str(addr_db).strip().lower():
                mismatch_reasons.append("address mismatch")

            # entities vs otcDesk（审核结果中的 entities 与用户侧 otcDesk 比对）
            if entities and otc_desk and str(entities).strip().lower() != str(otc_desk).strip().lower():
                mismatch_reasons.append("entities (vs otcDesk) mismatch")

            if mismatch_reasons:
                print(f"[RATING] submission_id={sid} 字段不匹配 → REFUSED, result=4, 原因: {', '.join(mismatch_reasons)}")
                _update_db_status(conn, sid, "REFUSED", 4)
                _record_rating(sid, "REFUSED", 4, mismatch_reasons)
                continue

            # 5) hash 校验
            if not _valid_hash_format(hash_raw):
                print(f"[RATING] submission_id={sid} hash 格式不合法或缺失 → REFUSED, result=4")
                _update_db_status(conn, sid, "REFUSED", 4)
                _record_rating(sid, "REFUSED", 4, ["Invalid hash format"])
                continue

            # 6) 全部通过 → ADOPT, result=5，并将 hash 写入 txid，并加入去重集合
            print(f"[RATING] submission_id={sid} 所有检查通过 → ADOPT, result=5")
            extracted["txid"] = hash_raw
            if txid_norm:
                committed_txids.add(txid_norm)
            if addr_norm:
                committed_addresses.add(addr_norm)
            _update_db_status(conn, sid, "ADOPT", 5)
            _record_rating(sid, "ADOPT", 5, [])

        # 回写更新后的审核结果文件
        with results_path.open("w", encoding="utf-8") as f:
            json.dump(audit_results, f, ensure_ascii=False, indent=2)
        print(f"[RATING] 已回写更新后的审核结果到: {results_path}")

        # 额外输出：每次运行的评级结果快照
        out_dir = _otc_root / "output" / "output_rating"
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file = out_dir / f"rating_results_{ts}.json"
        payload = {
            "generated_at": datetime.now().isoformat(),
            "source_results_file": str(results_path),
            "count": len(rating_rows),
            "rows": rating_rows,
        }
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"[RATING] 评级输出已写入: {out_file}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

