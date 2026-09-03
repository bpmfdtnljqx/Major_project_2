"""系统管理路由：系统重置（供自动测试恢复环境）。"""

from fastapi import APIRouter, Depends, Request

from app.core.auth import get_admin
from app.core.response import ok

router = APIRouter()


@router.post("/reset/")
async def reset_system(request: Request, _: dict = Depends(get_admin)):
    """系统重置：清空测试产生的用户、题目、提交、日志等，重建初始管理员，退出登录。"""
    request.app.state.problem_store.reset()
    request.app.state.user_store.reset()
    request.app.state.submission_store.clear()
    request.app.state.access_log_store.clear()
    request.app.state.ai_store.clear()
    request.app.state.language_store.clear()
    request.app.state.judge_tasks.clear()
    request.app.state.ai_tasks.clear()
    return ok(data=None, msg="system reset successfully")
