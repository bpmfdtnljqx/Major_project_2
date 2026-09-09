"""提交频率限制（Step 2）。

按 (user_id, problem_id) 二元组统计提交频率：1 分钟内超过 max_requests 次则拒绝。
即 FAQ 答疑所说的「单人单题」限制（同一用户在同一题上的提交频率）。
- 登录用户 + 具体题目：按 (user_id, problem_id) 限制
- 匿名 / 无 problem_id：按 user 自身限制（兜底）
"""

import time


class RateLimiter:
    def __init__(self, max_requests: int = 3, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: dict[str, list[float]] = {}

    def _make_key(self, user_id: str | None, problem_id: str | None) -> str:
        # 单人单题：(user_id, problem_id) 组合
        if user_id is not None and problem_id is not None:
            return f"{user_id}:{problem_id}"
        # 仅有 user_id：按用户全局（兜底）
        if user_id is not None:
            return f"{user_id}:__global__"
        # 匿名 / 兜底
        return "anonymous"

    def check(self, user_id: str | None, problem_id: str | None = None) -> bool:
        """检查是否允许提交；允许则记录本次提交并返回 True。"""
        key = self._make_key(user_id, problem_id)
        now = time.monotonic()
        stamps = [t for t in self._timestamps.get(key, []) if now - t <= self.window_seconds]
        if len(stamps) >= self.max_requests:
            self._timestamps[key] = stamps
            return False
        stamps.append(now)
        self._timestamps[key] = stamps
        return True
