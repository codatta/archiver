from __future__ import annotations

import os
import sys
from pathlib import Path

import pymysql
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")


def run_query(cursor, title: str, sql: str) -> None:
    print(f"=== {title} ===")
    try:
        cursor.execute(sql)
        rows = cursor.fetchall()
        if not rows:
            print("(empty)")
        for row in rows:
            print(row)
    except Exception as exc:
        print(f"ERROR: {exc}")
    print()


def main() -> None:
    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", 20)),
        charset="utf8mb4",
    )
    sql_from_env = os.getenv("DB_SUBMISSIONS_SQL", "")

    with conn.cursor() as cur:
        run_query(
            cur,
            "Configured DB_SUBMISSIONS_SQL row count",
            f"SELECT COUNT(*) FROM ({sql_from_env}) t",
        )
        run_query(
            cur,
            "ROBSTIC001 by status",
            """
            SELECT status, COUNT(*) AS cnt
            FROM cfp_task_submission
            WHERE frontier_id = 'ROBSTIC001'
            GROUP BY status
            ORDER BY cnt DESC
            """,
        )
        run_query(
            cur,
            "frontier_id LIKE ROBSTIC%",
            """
            SELECT frontier_id, status, COUNT(*) AS cnt
            FROM cfp_task_submission
            WHERE frontier_id LIKE 'ROBSTIC%'
            GROUP BY frontier_id, status
            ORDER BY frontier_id, cnt DESC
            LIMIT 30
            """,
        )
        run_query(
            cur,
            "frontier_id LIKE ROB%",
            """
            SELECT frontier_id, COUNT(*) AS cnt
            FROM cfp_task_submission
            WHERE frontier_id LIKE 'ROB%'
            GROUP BY frontier_id
            ORDER BY cnt DESC
            LIMIT 20
            """,
        )
        run_query(
            cur,
            "Recent ROBSTIC001 rows (any status)",
            """
            SELECT submission_id, status, user_id, gmt_create
            FROM cfp_task_submission
            WHERE frontier_id = 'ROBSTIC001'
            ORDER BY gmt_create DESC
            LIMIT 5
            """,
        )

    conn.close()


if __name__ == "__main__":
    main()
