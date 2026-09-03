"""AI 智能命题存储层（SQLite）。

- model_config 表：单行模型配置（provider_url / model / api_key / 价格）。
- ai_tasks 表：AI 命题任务（状态 / 结果 / Token 用量）。
与其它存储共用同一 data/oj.db。
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


class AIStore:
    """AI 模型配置 + 命题任务的存储。"""

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
                CREATE TABLE IF NOT EXISTS model_config (
                    id           INTEGER PRIMARY KEY CHECK (id = 1),
                    provider_url TEXT NOT NULL,
                    model        TEXT NOT NULL,
                    api_key      TEXT NOT NULL,
                    input_price  REAL,
                    output_price REAL,
                    price_unit   INTEGER
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ai_tasks (
                    task_id     TEXT PRIMARY KEY,
                    user_id     TEXT,
                    requirement TEXT NOT NULL,
                    problem_id  TEXT,
                    status      TEXT NOT NULL DEFAULT 'pending',
                    progress    TEXT,
                    result      TEXT,
                    usage       TEXT,
                    created_at  TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    # ---- 模型配置 ----
    def get_config(self) -> dict | None:
        """获取模型配置，未设置返回 None。"""
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM model_config WHERE id = 1").fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def set_config(self, provider_url, model, api_key, input_price=None, output_price=None, price_unit=None) -> None:
        """保存（覆盖）模型配置。"""
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO model_config (id, provider_url, model, api_key, input_price, output_price, price_unit)
                VALUES (1, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    provider_url = excluded.provider_url,
                    model        = excluded.model,
                    api_key      = excluded.api_key,
                    input_price  = excluded.input_price,
                    output_price = excluded.output_price,
                    price_unit   = excluded.price_unit
                """,
                (provider_url, model, api_key, input_price, output_price, price_unit),
            )
            conn.commit()
        finally:
            conn.close()

    # ---- AI 任务 ----
    def create_task(self, task_id: str, requirement: str, problem_id: str | None = None, user_id: str | None = None) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO ai_tasks (task_id, user_id, requirement, problem_id, status, created_at) "
                "VALUES (?, ?, ?, ?, 'pending', ?)",
                (task_id, user_id, requirement, problem_id, datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
        finally:
            conn.close()

    def get_task(self, task_id: str) -> dict | None:
        """按 id 查询任务，result / usage 自动反序列化。"""
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM ai_tasks WHERE task_id = ?", (task_id,)).fetchone()
            if row is None:
                return None
            d = dict(row)
            for k in ("result", "usage"):
                if d.get(k) is not None:
                    d[k] = json.loads(d[k])
            return d
        finally:
            conn.close()

    def update_task(self, task_id: str, **fields) -> None:
        """更新任务字段，result / usage 自动序列化。"""
        if not fields:
            return
        cleaned = {k: (json.dumps(v) if k in ("result", "usage") and v is not None else v) for k, v in fields.items()}
        cols = ", ".join(f"{k} = ?" for k in cleaned)
        vals = list(cleaned.values()) + [task_id]
        conn = self._connect()
        try:
            conn.execute(f"UPDATE ai_tasks SET {cols} WHERE task_id = ?", vals)
            conn.commit()
        finally:
            conn.close()
