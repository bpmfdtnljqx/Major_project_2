"""提交频率限制（Step 2）。

按用户统计提交频率：1 分钟内超过 max_requests 次则拒绝。
当前（Step 4 前）尚无登录用户，调用方以匿名（user_id=None）传入，
等价于全局计数；接入登录后传入真实 user_id 即自动变为按用户计数。
"""

import time


class RateLimiter:
    def __init__(self, max_requests: int = 3, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: dict[str, list[float]] = {}

    def check(self, user_id: str | None) -> bool:
        """检查是否允许提交；允许则记录本次提交并返回 True。"""
        key = user_id or "anonymous"
        now = time.monotonic()
        stamps = [t for t in self._timestamps.get(key, []) if now - t <= self.window_seconds]
        if len(stamps) >= self.max_requests:
            self._timestamps[key] = stamps
            return False
        stamps.append(now)
        self._timestamps[key] = stamps
        return True
