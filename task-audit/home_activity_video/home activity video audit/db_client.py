"""
视频审核流水线 — 数据库访问模块。
连接方式与 cex_hot_wallet/db_client.py 保持一致：pymysql + DictCursor，
从环境变量 / .env 读取 DB_* 配置。
"""

from __future__ import annotations

import os
import pymysql.err
from typing import Any, Dict, List, Optional

import pymysql
from pymysql.cursors import DictCursor


class VideoAuditDBClient:
    """
    待审核视频列表与指纹回写。

    环境变量（与参考项目一致，由 main 侧 load_dotenv 加载）：
    - DB_HOST（默认 localhost）
    - DB_PORT（默认 3306）
    - DB_USER
    - DB_PASSWORD
    - DB_NAME
    - DB_PENDING_VIDEOS_SQL（必填）：待审核列表，支持 {limit} / {offset} 占位符

    查重与回写依赖同一张「指纹/状态」业务表，表名由 DB_VIDEO_META_TABLE 指定
    （需包含 submission_id、task_id、lightweight_hash、phash_hex、audit_grade、
    updated_at 等列；若未设置表名，则 Phase 0 的数据库侧查重会跳过并打印警告）。

    可选：DB_PENDING_VIDEOS_SQL_FILE — 从文件读取 SQL（UTF-8），与参考 db_client 行为类似。
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ) -> None:
        self.host = host or os.getenv("DB_HOST", "localhost")
        self.port = port or int(os.getenv("DB_PORT", "3306"))
        self.user = user or os.getenv("DB_USER", "")
        self.password = password or os.getenv("DB_PASSWORD", "")
        self.database = database or os.getenv("DB_NAME", "")

        self.pending_sql = os.getenv("DB_PENDING_VIDEOS_SQL")
        if not self.pending_sql:
            sql_file = os.getenv("DB_PENDING_VIDEOS_SQL_FILE")
            if sql_file:
                try:
                    with open(sql_file, "r", encoding="utf-8") as f:
                        self.pending_sql = f.read().strip()
                except Exception as e:
                    raise ValueError(f"无法读取 SQL 文件 {sql_file}: {e}") from e

        if not self.user or not self.database:
            raise ValueError(
                "数据库配置不完整，请在环境变量中设置 DB_USER 和 DB_NAME "
                "(必要时还需要 DB_PASSWORD、DB_HOST、DB_PORT)"
            )

        self.meta_table = (os.getenv("DB_VIDEO_META_TABLE") or "").strip()
        self.meta_enabled = bool(self.meta_table)

    def _disable_meta_table(self, reason: str) -> None:
        if self.meta_enabled:
            print(f"警告: 已自动停用 DB_VIDEO_META_TABLE({self.meta_table}): {reason}")
        self.meta_enabled = False

    def _grade_to_status_result(self, audit_grade: str) -> tuple[Optional[str], Optional[int]]:
        """
        将内部 audit_grade 映射到业务表的 status / result。

        约定（来自你前面的描述）：
        - result: D/C/B/A/S => 1/2/3/4/5
        - status: D/C/B => REFUSED；A/S => ADOPT/PENDING（S=ADOPT，A/人工=>PENDING）
        - Pending_AI 视作 A（PENDING）
        """
        g = str(audit_grade or "").strip().upper()
        if not g:
            return None, None
        if g == "D":
            return "REFUSED", 1
        if g == "C":
            return "REFUSED", 2
        if g == "B":
            return "REFUSED", 3
        if g in {"A"}:
            return "PENDING", 4
        if g in {"S"}:
            return "ADOPT", 5
        if g in {"PENDING_AI", "PENDING"}:
            return "PENDING", 4
        if g in {"MANUAL_REVIEW"}:
            return "PENDING", 4
        if g in {"ERROR"}:
            return "PENDING", 0
        return None, None

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

    def fetch_pending_videos(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        读取待审核视频行。SQL 由 DB_PENDING_VIDEOS_SQL 提供，需至少返回：
        - submission_id
        - video_path（本地可访问的视频文件路径）
        建议同时返回：
        - file_size_bytes（可省略，省略时由审核器 os.path.getsize）
        - task_id（用于 pHash 同任务 15 天窗口；可省略，默认为 '_default'）
        """
        if not self.pending_sql:
            raise ValueError(
                "DB_PENDING_VIDEOS_SQL 未配置：请在 .env 中设置 DB_PENDING_VIDEOS_SQL "
                "或 DB_PENDING_VIDEOS_SQL_FILE。"
            )

        sql = self.pending_sql.format(
            limit="" if limit is None else int(limit),
            offset=int(offset or 0),
        )
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                return list(cursor.fetchall())
        finally:
            conn.close()

    def _require_meta_table(self) -> str:
        if not self.meta_table:
            raise ValueError(
                "未设置 DB_VIDEO_META_TABLE：无法在库内做 lightweight_hash / pHash 查重与状态回写。"
            )
        # 仅允许字母数字下划线，防止 SQL 注入
        t = self.meta_table
        if not t.replace("_", "").isalnum():
            raise ValueError(f"DB_VIDEO_META_TABLE 含有非法字符: {t!r}")
        return t

    def lightweight_hash_exists(
        self,
        lightweight_hash: str,
        exclude_submission_id: str,
    ) -> bool:
        """逻辑 A：是否已有其他提交占用相同 lightweight_hash。"""
        if not self.meta_table or not self.meta_enabled:
            return False

        table = self._require_meta_table()
        sql = (
            f"SELECT 1 AS `hit` FROM `{table}` "
            "WHERE `lightweight_hash` = %s AND `submission_id` <> %s LIMIT 1"
        )
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, (lightweight_hash, exclude_submission_id))
                except pymysql.err.ProgrammingError as e:
                    # 1054: Unknown column, 1146: table doesn't exist
                    if getattr(e, "args", None) and e.args and e.args[0] in (1054, 1146):
                        self._disable_meta_table(str(e))
                        return False
                    raise
                row = cursor.fetchone()
                return row is not None
        finally:
            conn.close()

    def fetch_recent_phashes_for_task(
        self,
        task_id: str,
        exclude_submission_id: str,
        days: int = 15,
    ) -> List[str]:
        """逻辑 B：最近 days 天内同 task_id 的 pHash 十六进制字符串列表。"""
        if not self.meta_table or not self.meta_enabled:
            return []

        table = self._require_meta_table()
        sql = (
            f"SELECT `phash_hex` FROM `{table}` "
            "WHERE `task_id` = %s AND `submission_id` <> %s "
            "AND `updated_at` >= (NOW() - INTERVAL %s DAY) "
            "AND `phash_hex` IS NOT NULL AND `phash_hex` <> ''"
        )
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, (task_id, exclude_submission_id, int(days)))
                except pymysql.err.ProgrammingError as e:
                    if getattr(e, "args", None) and e.args and e.args[0] in (1054, 1146):
                        self._disable_meta_table(str(e))
                        return []
                    raise
                rows = cursor.fetchall()
            out: List[str] = []
            for r in rows:
                h = r.get("phash_hex")
                if h:
                    out.append(str(h).strip())
            return out
        finally:
            conn.close()

    def video_hash_exists_in_history(
        self,
        *,
        video_hash: str,
        exclude_submission_id: str,
        task_id: str,
    ) -> bool:
        """
        历史去重：检查数据库中是否已存在相同 video.hash。

        优先使用 PHASE0_DB_HASH_EXISTS_SQL（支持占位符：{video_hash}/{submission_id}/{task_id}）。
        若未配置，则使用默认 SQL（基于 DB_VIDEO_META_TABLE 或 DB_HASH_CHECK_TABLE）。
        """
        if not str(video_hash or "").strip():
            return False

        sql_tpl = (os.getenv("PHASE0_DB_HASH_EXISTS_SQL") or "").strip()
        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                if sql_tpl:
                    sql = sql_tpl.format(
                        video_hash=str(video_hash).replace("'", "''"),
                        submission_id=str(exclude_submission_id).replace("'", "''"),
                        task_id=str(task_id).replace("'", "''"),
                    )
                    cursor.execute(sql)
                    row = cursor.fetchone()
                    return row is not None

                table = (os.getenv("DB_HASH_CHECK_TABLE") or self.meta_table or "").strip()
                if not table:
                    return False
                if not table.replace("_", "").isalnum():
                    raise ValueError(f"DB_HASH_CHECK_TABLE 含有非法字符: {table!r}")

                sql = (
                    f"SELECT 1 AS `hit` FROM `{table}` "
                    "WHERE `submission_id` <> %s "
                    "AND JSON_UNQUOTE(JSON_EXTRACT(`data_submission`, '$.data.video.hash')) = %s "
                    "LIMIT 1"
                )
                cursor.execute(sql, (exclude_submission_id, video_hash))
                row = cursor.fetchone()
                return row is not None
        finally:
            conn.close()

    def update_video_status(
        self,
        submission_id: str,
        *,
        lightweight_hash: Optional[str] = None,
        phash_hex: Optional[str] = None,
        audit_grade: Optional[str] = None,
        cut_count: Optional[int] = None,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        result: Optional[int] = None,
        extra_columns: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        将审核等级映射后的 status/result 等回写到 DB_VIDEO_META_TABLE 指向的表。
        仅对非 None 的字段生成 SET 子句；至少应有一项非 None，否则立即返回。
        """
        if not self.meta_table:
            print("警告: 未设置 DB_VIDEO_META_TABLE，跳过 update_video_status")
            return

        table = self._require_meta_table()
        cols: List[str] = []
        params: List[Any] = []

        # 兼容旧阶段传参：lightweight_hash/phash_hex/cut_count/task_id 本轮只用于兼容，不写入 UPDATE。
        _ = lightweight_hash, phash_hex, cut_count, task_id

        mapped_status: Optional[str] = status
        mapped_result: Optional[int] = result
        if (mapped_status is None or mapped_result is None) and audit_grade:
            ms, mr = self._grade_to_status_result(audit_grade)
            if mapped_status is None:
                mapped_status = ms
            if mapped_result is None:
                mapped_result = mr

        # 仅写入业务表关心的字段：status / result（以及可选 extra_columns）
        mapping = [
            [
                ("status", mapped_status),
                ("result", mapped_result),
            ]
        ][0]
        for col, val in mapping:
            if val is None:
                continue
            if not col.replace("_", "").isalnum():
                raise ValueError(f"非法列名: {col}")
            cols.append(f"`{col}`=%s")
            params.append(val)

        if extra_columns:
            for col, val in extra_columns.items():
                if not str(col).replace("_", "").isalnum():
                    raise ValueError(f"非法列名: {col}")
                cols.append(f"`{col}`=%s")
                params.append(val)

        if not cols:
            return

        sql = f"UPDATE `{table}` SET {', '.join(cols)} WHERE `submission_id`=%s"
        params.append(submission_id)

        conn = self._get_connection()
        try:
            with conn.cursor() as cursor:
                try:
                    cursor.execute(sql, params)
                except pymysql.err.ProgrammingError as e:
                    if getattr(e, "args", None) and e.args and e.args[0] in (1054, 1146):
                        # 这里不直接终止整个流程：status/result 可能仍可用
                        # 若是轻量字段缺失，会导致 meta_enabled=false 逻辑已经生效。
                        self._disable_meta_table(str(e))
                        print(f"警告: 元表回写字段不兼容，已停用该表的元字段写入: {e}")
                        conn.rollback()
                        # 重试：只写 status/result（以及 extra_columns）
                        cols_retry: List[str] = []
                        params_retry: List[Any] = []
                        mapping_retry: List[tuple[str, Any]] = [
                            ("status", mapped_status),
                            ("result", mapped_result),
                        ]
                        for col, val in mapping_retry:
                            if val is None:
                                continue
                            if not col.replace("_", "").isalnum():
                                raise ValueError(f"非法列名: {col}")
                            cols_retry.append(f"`{col}`=%s")
                            params_retry.append(val)

                        if extra_columns:
                            for col, val in extra_columns.items():
                                if not str(col).replace("_", "").isalnum():
                                    raise ValueError(f"非法列名: {col}")
                                cols_retry.append(f"`{col}`=%s")
                                params_retry.append(val)

                        if not cols_retry:
                            return

                        sql_retry = f"UPDATE `{table}` SET {', '.join(cols_retry)} WHERE `submission_id`=%s"
                        params_retry.append(submission_id)
                        cursor.execute(sql_retry, params_retry)
                        conn.commit()
                        return
                    raise
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


__all__ = ["VideoAuditDBClient"]
