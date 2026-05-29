from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pymysql
from pymysql.cursors import DictCursor

from robotics_audit.models import grade_to_result_score, grade_to_status


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        root = Path(__file__).resolve().parent
        env_file = root / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
    except Exception:
        pass


class SubmissionDBClient:
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        _load_env()
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", "3306"))
        self.user = user or os.getenv("DB_USER", "")
        self.password = password or os.getenv("DB_PASSWORD", "")
        self.database = database or os.getenv("DB_NAME", "")
        self.fetch_sql = os.getenv("DB_SUBMISSIONS_SQL", "")
        self.meta_table = (os.getenv("DB_META_TABLE") or "cfp_task_submission").strip()
        self.connect_timeout = int(os.getenv("DB_CONNECT_TIMEOUT", "20"))

        if not self.user or not self.database:
            raise ValueError("请在 .env 中配置 DB_USER 与 DB_NAME")

    def _get_connection(self):
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            cursorclass=DictCursor,
            autocommit=False,
            charset="utf8mb4",
            connect_timeout=self.connect_timeout,
        )

    def fetch_submissions(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        if not self.fetch_sql:
            raise ValueError("请在 .env 中配置 DB_SUBMISSIONS_SQL")
        sql = self.fetch_sql
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = list(cursor.fetchall())
        finally:
            conn.close()

        if offset:
            rows = rows[offset:]
        if limit is not None:
            rows = rows[:limit]
        return rows

    def update_submission_grade(
        self,
        submission_id: str,
        audit_grade: str,
        *,
        reason: str = "",
    ) -> bool:
        status = grade_to_status(audit_grade)
        result = grade_to_result_score(audit_grade)
        custom_sql = os.getenv("DB_UPDATE_SQL")
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                if custom_sql:
                    cursor.execute(
                        custom_sql,
                        {
                            "submission_id": submission_id,
                            "audit_grade": audit_grade,
                            "status": status,
                            "result": result,
                            "reason": reason,
                        },
                    )
                else:
                    cursor.execute(
                        f"""
                        UPDATE {self.meta_table}
                        SET status = %s, result = %s
                        WHERE submission_id = %s
                        """,
                        (status, result, submission_id),
                    )
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def write_audit_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        stats: Dict[str, Any] = {
            "attempted": 0,
            "success": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

        for item in results:
            submission_id = str(item.get("submission_id") or "").strip()
            if not submission_id:
                stats["skipped"] += 1
                continue

            stats["attempted"] += 1
            reason = "；".join(v.get("message", "") for v in (item.get("violations") or [])[:3])
            try:
                ok = self.update_submission_grade(
                    submission_id,
                    str(item.get("audit_grade") or "A"),
                    reason=reason,
                )
                if ok:
                    stats["success"] += 1
                    print(
                        f"[db] 已写回 submission_id={submission_id} "
                        f"grade={item.get('audit_grade')} status={item.get('status')} result={item.get('result')}"
                    )
                else:
                    stats["failed"] += 1
                    stats["errors"].append(
                        {"submission_id": submission_id, "error": "update_submission_grade 返回 False"}
                    )
            except Exception as exc:
                stats["failed"] += 1
                stats["errors"].append({"submission_id": submission_id, "error": str(exc)})
                print(f"[db] 写回失败 submission_id={submission_id}: {exc}")

        return stats
