"""用户与会话存储层（SQLite）。

架构决策：用户 / 提交 / 日志用 SQLite（同一 data/oj.db）。
- users 表：user_id / username / password_hash / role / join_time
- sessions 表：session_id / user_id / created_at
- 密码用 pbkdf2_hmac 加盐哈希，不存明文。
- 系统启动时自动创建初始管理员 admin / admintestpassword。
"""

import hashlib
import secrets
import sqlite3
import uuid
from datetime import date, datetime
from pathlib import Path

_PBKDF2_ITERATIONS = 100000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
    return f"{salt}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed = stored.split("$", 1)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PBKDF2_ITERATIONS)
        return secrets.compare_digest(dk.hex(), hashed)
    except (ValueError, TypeError):
        return False


class UserStore:
    """用户与会话存储：建表 + 增查改 + 登录校验 + 会话管理。"""

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
                CREATE TABLE IF NOT EXISTS users (
                    user_id       TEXT PRIMARY KEY,
                    username      TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role          TEXT NOT NULL DEFAULT 'user',
                    join_time     TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id    TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
                conn.execute(
                    "INSERT INTO users (user_id, username, password_hash, role, join_time) "
                    "VALUES ('1', 'admin', ?, 'admin', ?)",
                    (hash_password("admintestpassword"), date.today().isoformat()),
                )
            conn.commit()
        finally:
            conn.close()

    # ---- 内部：统计字段 ----
    def _with_stats(self, conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
        d = dict(row)
        d.pop("password_hash", None)  # 不返回密码哈希
        d["submit_count"] = conn.execute(
            "SELECT COUNT(*) FROM submissions WHERE user_id = ?", (d["user_id"],)
        ).fetchone()[0]
        d["resolve_count"] = conn.execute(
            "SELECT COUNT(DISTINCT problem_id) FROM submissions "
            "WHERE user_id = ? AND status = 'success' AND score = counts",
            (d["user_id"],),
        ).fetchone()[0]
        return d

    # ---- 用户 ----
    def create_user(self, username: str, password: str, role: str = "user") -> dict | None:
        """创建用户，username 重复返回 None。"""
        conn = self._connect()
        try:
            if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
                return None
            user_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO users (user_id, username, password_hash, role, join_time) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, username, hash_password(password), role, date.today().isoformat()),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return self._with_stats(conn, row)
        finally:
            conn.close()

    def get_by_id(self, user_id: str) -> dict | None:
        """按 id 查询用户（含统计，不含密码）。"""
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return self._with_stats(conn, row) if row else None
        finally:
            conn.close()

    def get_by_username(self, username: str) -> dict | None:
        """按用户名查询（含 password_hash，仅用于登录校验）。"""
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def verify_login(self, username: str, password: str) -> dict | None:
        """校验用户名密码，成功返回用户（不含密码），失败返回 None。"""
        user = self.get_by_username(username)
        if user is None or not verify_password(password, user["password_hash"]):
            return None
        return self.get_by_id(user["user_id"])

    def update_role(self, user_id: str, role: str) -> None:
        conn = self._connect()
        try:
            conn.execute("UPDATE users SET role = ? WHERE user_id = ?", (role, user_id))
            conn.commit()
        finally:
            conn.close()

    def list_users(self, page=None, page_size=None) -> tuple[int, list[dict]]:
        """分页查询用户列表（含统计）。"""
        conn = self._connect()
        try:
            total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            params: list = []
            limit_sql = ""
            if page is not None and page_size is not None:
                limit_sql = " LIMIT ? OFFSET ?"
                params = [page_size, (page - 1) * page_size]
            rows = conn.execute(f"SELECT * FROM users ORDER BY rowid{limit_sql}", params).fetchall()
            return total, [self._with_stats(conn, r) for r in rows]
        finally:
            conn.close()

    # ---- 会话 ----
    def create_session(self, session_id: str, user_id: str) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO sessions (session_id, user_id, created_at) VALUES (?, ?, ?)",
                (session_id, user_id, datetime.now().isoformat(timespec="seconds")),
            )
            conn.commit()
        finally:
            conn.close()

    def get_session(self, session_id: str) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def delete_session(self, session_id: str) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            conn.commit()
        finally:
            conn.close()
