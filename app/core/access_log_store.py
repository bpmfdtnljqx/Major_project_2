"""访问审计日志存储层（SQLite）。

记录 view_logs 访问（谁在何时访问了哪道题的评测日志，结果如何）。
审计与提交共用同一 data/oj.db。
"""

import sqlite3
from datetime import datetime
from pathlib import Path


class AccessLogStore:
    """访问审计日志：建表 + 记录 + 查询。"""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS access_logs (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id    TEXT NOT NULL,
                    problem_id TEXT NOT NULL,
                    action     TEXT NOT NULL,
                    time       TEXT NOT NULL,
                    status     TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def record(self, user_id: str, problem_id: str, action: str, status: str) -> None:
        """写入一条访问审计记录。"""
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO access_logs (user_id, problem_id, action, time, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, problem_id, action, datetime.now().isoformat(timespec="seconds"), status),
            )
            conn.commit()
        finally:
            conn.close()

    def list(self, user_id=None, problem_id=None, page=None, page_size=None) -> list[dict]:
        """按条件查询审计记录（最新在前），返回记录数组。"""
        conditions = []
        params = []
        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)
        if problem_id is not None:
            conditions.append("problem_id = ?")
            params.append(problem_id)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        conn = self._connect()
        try:
            query_params = list(params)
            limit_sql = ""
            if page is not None and page_size is not None:
                limit_sql = " LIMIT ? OFFSET ?"
                query_params.extend([page_size, (page - 1) * page_size])
            rows = conn.execute(
                f"SELECT user_id, problem_id, action, time, status "
                f"FROM access_logs{where} ORDER BY id DESC{limit_sql}",
                query_params,
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
