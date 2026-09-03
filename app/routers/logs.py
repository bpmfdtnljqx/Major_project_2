"""访问审计路由（Step 5）。

GET /api/logs/access/ —— 查询访问审计日志（仅管理员）。
"""

from fastapi import APIRouter, Depends, Request

from app.core.auth import get_admin
from app.core.response import AppError, ok

router = APIRouter()


@router.get("/logs/access/")
async def list_access_logs(
    request: Request,
    user_id: str | None = None,
    problem_id: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    _: dict = Depends(get_admin),
):
    """查询访问审计日志（仅管理员，分页规则与评测列表一致）。"""
    if page is not None and page_size is None:
        raise AppError(400, "page_size required")
    if page is None and page_size is not None:
        page = 1
    logs = request.app.state.access_log_store.list(user_id, problem_id, page, page_size)
    return ok(data=logs)
