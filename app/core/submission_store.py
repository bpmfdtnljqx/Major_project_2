"""提交记录存储层（SQLite）。

提交记录是 Step 2/3/5 的公共数据源。架构决策：题目用 JSON 一题一文件，
用户 / 提交 / 日志用 SQLite。存储层为同步实现（标准库 sqlite3），
异步由调用方通过 asyncio.to_thread 包装。

为线程安全，每个操作使用短连接（独立连接，用完即关）。
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

# 需要 JSON 序列化 / 反序列化的字段（表内存储为 TEXT）
_JSON_FIELDS = {"compile_info", "run_info", "details"}


class SubmissionStore:
    """提交记录存储：建表 + 增查改。"""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ---- 内部 ----
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS submissions (
                    submission_id TEXT PRIMARY KEY,
                    problem_id   TEXT NOT NULL,
                    language     TEXT NOT NULL,
                    code         TEXT NOT NULL,
                    user_id      TEXT,
                    status       TEXT NOT NULL DEFAULT 'pending',
                    score        INTEGER,
                    counts       INTEGER,
                    compile_info TEXT,
                    run_info     TEXT,
                    error_info   TEXT,
                    details      TEXT,
                    created_at   TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict:
        d = dict(row)
        for key in _JSON_FIELDS:
            if d.get(key) is not None:
                d[key] = json.loads(d[key])
        return d

    # ---- 写 ----
    def create(self, submission_id: str, problem_id: str, language: str, code: str, user_id: str | None = None) -> None:
        """新建一条 pending 状态的提交记录。"""
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO submissions "
                "(submission_id, problem_id, language, code, user_id, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, 'pending', ?)",
                (submission_id, problem_id, language, code, user_id, self._now()),
            )
            conn.commit()
        finally:
            conn.close()

    def update(self, submission_id: str, **fields) -> None:
        """更新提交字段，JSON 字段自动序列化。"""
        if not fields:
            return
        cleaned = {k: (json.dumps(v) if k in _JSON_FIELDS and v is not None else v) for k, v in fields.items()}
        cols = ", ".join(f"{k} = ?" for k in cleaned)
        vals = list(cleaned.values()) + [submission_id]
        conn = self._connect()
        try:
            conn.execute(f"UPDATE submissions SET {cols} WHERE submission_id = ?", vals)
            conn.commit()
        finally:
            conn.close()

    # ---- 读 ----
    def get(self, submission_id: str) -> dict | None:
        """按 id 查询提交，不存在返回 None。"""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM submissions WHERE submission_id = ?", (submission_id,)
            ).fetchone()
            return self._row_to_dict(row) if row else None
        finally:
            conn.close()

    def list(self, user_id=None, problem_id=None, status=None, page=None, page_size=None):
        """按条件查询提交列表，返回 (total, submissions)。

        - 过滤条件均为可选，None 表示不限制；
        - page / page_size：同时为 None 查全部；同时非 None 分页（page 从 1 开始）。
        """
        conditions = []
        params = []
        if user_id is not None:
            conditions.append("user_id = ?")
            params.append(user_id)
        if problem_id is not None:
            conditions.append("problem_id = ?")
            params.append(problem_id)
        if status is not None:
            conditions.append("status = ?")
            params.append(status)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

        conn = self._connect()
        try:
            total = conn.execute(f"SELECT COUNT(*) FROM submissions{where}", params).fetchone()[0]
            query_params = list(params)
            limit_sql = ""
            if page is not None and page_size is not None:
                limit_sql = " LIMIT ? OFFSET ?"
                query_params.extend([page_size, (page - 1) * page_size])
            rows = conn.execute(
                f"SELECT * FROM submissions{where} ORDER BY rowid DESC{limit_sql}", query_params
            ).fetchall()
            return total, [self._row_to_dict(r) for r in rows]
        finally:
            conn.close()

    def clear(self) -> None:
        """清空所有提交记录（用于系统重置）。"""
        conn = self._connect()
        try:
            conn.execute("DELETE FROM submissions")
            conn.commit()
        finally:
            conn.close()
