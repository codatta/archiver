"""
数据库交互模块
用于从 MySQL 中读取 submissions 原始数据，替代本地 JSON 文件。
"""

from __future__ import annotations

import os
from typing import List, Dict, Optional

import pymysql
from pymysql.cursors import DictCursor


class SubmissionDBClient:
    """
    submissions 表的简单访问封装。

    约定（完全由配置的 SQL 决定）：
    - 数据库类型：MySQL / MariaDB
    - 仅通过环境变量 `DB_SUBMISSIONS_SQL` 配置一条完整的查询语句：
        - 要求返回列至少包含：
            - submission_id
            - data_submission（JSON 字符串或已截取出的 $.data）
        - 可以使用 Python 格式占位符 {limit} 和 {offset}，用于分页

    默认配置通过环境变量提供：
    - DB_HOST（默认 localhost）
    - DB_PORT（默认 3306）
    - DB_USER
    - DB_PASSWORD
    - DB_NAME
    - DB_SUBMISSIONS_SQL（必填）：查询原始 submissions 的 SQL
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        table: Optional[str] = None,
    ) -> None:
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", "3306"))
        self.user = user or os.getenv("DB_USER", "")
        self.password = password or os.getenv("DB_PASSWORD", "")
        self.database = database or os.getenv("DB_NAME", "")
        # 仅通过自定义 SQL 控制过滤逻辑
        # 优先从环境变量读取，如果没有则尝试从文件读取
        self.custom_sql = os.getenv("DB_SUBMISSIONS_SQL") or None
        if not self.custom_sql:
            sql_file = os.getenv("DB_SUBMISSIONS_SQL_FILE")
            if sql_file:
                try:
                    with open(sql_file, 'r', encoding='utf-8') as f:
                        self.custom_sql = f.read().strip()
                except Exception as e:
                    raise ValueError(f"无法读取 SQL 文件 {sql_file}: {e}")

        if not self.user or not self.database:
            raise ValueError(
                "数据库配置不完整，请在环境变量中设置 DB_USER 和 DB_NAME "
                "(必要时还需要 DB_PASSWORD、DB_HOST、DB_PORT)"
            )

    def _get_connection(self):
        """获取一个新的数据库连接。"""
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
        """
        从数据库中读取 submissions 列表。

        Args:
            limit: 限制返回条数（None 表示不限制）
            offset: 起始偏移量，用于分页

        Returns:
            与 raw_data/submissions.json 格式一致的列表：
            [{"submission_id": "...", "data_submission": "<JSON字符串>", ...}, ...]
        """
        if not self.custom_sql:
            raise ValueError(
                "DB_SUBMISSIONS_SQL 未配置：当前仅支持通过 SQL 方式获取原始提交数据，"
                "请在 .env 中设置 DB_SUBMISSIONS_SQL。"
            )

        # 使用 DB_SUBMISSIONS_SQL 作为模板，支持 {limit} / {offset}
        sql = self.custom_sql.format(
            limit="" if limit is None else int(limit),
            offset=int(offset or 0),
        )

        rows: List[Dict] = []
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rows = list(cursor.fetchall())
        finally:
            conn.close()

        # 如果调用侧还指定了 submission_ids，则在内存中再过滤一层
        if submission_ids:
            id_set = set(str(sid) for sid in submission_ids)
            rows = [r for r in rows if str(r.get("submission_id")) in id_set]

        return rows


__all__ = ["SubmissionDBClient"]

