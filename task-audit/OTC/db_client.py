"""
OTC 数据库交互模块
从 MySQL 读取 submissions，使用 OTC 目录下的 .env 配置。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Optional

import pymysql
from pymysql.cursors import DictCursor

# 优先加载 OTC 目录下的 .env
def _load_otc_env() -> None:
    try:
        from dotenv import load_dotenv
        otc_root = Path(__file__).resolve().parent
        env_file = otc_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    except Exception:
        pass


class SubmissionDBClient:
    """
    从 MySQL 读取 OTC 相关 submissions。
    要求 .env 中配置：DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_SUBMISSIONS_SQL。
    SQL 需返回：submission_id, data_submission（JSON 字符串，内含截图 URL 等）。
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        _load_otc_env()
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", "3306"))
        self.user = user or os.getenv("DB_USER", "")
        self.password = password or os.getenv("DB_PASSWORD", "")
        self.database = database or os.getenv("DB_NAME", "")
        self.custom_sql = os.getenv("DB_SUBMISSIONS_SQL") or os.getenv("DB_OTC_SUBMISSIONS_SQL")

        if not self.user or not self.database:
            raise ValueError(
                "数据库配置不完整，请在 OTC/.env 中设置 DB_USER 和 DB_NAME "
                "（以及 DB_PASSWORD、DB_HOST、DB_PORT）"
            )

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
        )

    def fetch_submissions(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        submission_ids: Optional[List[str]] = None,
    ) -> List[Dict]:
        """返回 [{"submission_id": "...", "data_submission": "<JSON字符串>"}, ...]"""
        if not self.custom_sql:
            raise ValueError(
                "请在 OTC/.env 中设置 DB_SUBMISSIONS_SQL 或 DB_OTC_SUBMISSIONS_SQL，"
                "查询需返回 submission_id 与 data_submission。"
            )
        sql = self.custom_sql.replace("{limit}", "" if limit is None else str(int(limit)))
        sql = sql.replace("{offset}", str(int(offset)))
        rows: List[Dict] = []
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = list(cursor.fetchall())
        finally:
            conn.close()
        if submission_ids:
            id_set = set(str(sid) for sid in submission_ids)
            rows = [r for r in rows if str(r.get("submission_id")) in id_set]
        return rows

    def fetch_adopted_submissions(self) -> List[Dict]:
        """
        拉取本任务下已采纳（status='ADOPT'）的提交，用于去重：同一 task 内
        txid/address 已被采纳过的，不再通过。
        要求 .env 中可选配置 DB_ADOPTED_SUBMISSIONS_SQL，需返回 submission_id, data_submission。
        未配置则返回空列表（仅做当次批次内去重）。
        """
        adopted_sql = os.getenv("DB_ADOPTED_SUBMISSIONS_SQL")
        if not adopted_sql or not adopted_sql.strip():
            return []
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(adopted_sql)
                return list(cursor.fetchall())
        finally:
            conn.close()


__all__ = ["SubmissionDBClient"]
