"""语言管理路由（Step 2）。

- GET  /api/languages/  查询支持的语言列表
- POST /api/languages/  动态注册新语言
"""

from fastapi import APIRouter, Depends, Request

from app.core.auth import get_current_user
from app.core.response import AppError, ok
from app.models import Language

router = APIRouter()


def _store(request: Request):
    return request.app.state.language_store


@router.get("/languages/")
async def list_languages(request: Request):
    """查询支持的语言列表（公开）。"""
    store = _store(request)
    return ok(data={"name": store.list_names()})


@router.post("/languages/")
async def register_language(request: Request, language: Language, _: dict = Depends(get_current_user)):
    """动态注册新语言（配置安全：run_cmd 必须含 {src} 或 {exe} 占位符）。"""
    if "{src}" not in language.run_cmd and "{exe}" not in language.run_cmd:
        raise AppError(400, "run_cmd must contain {src} or {exe}")
    store = _store(request)
    store.add(language)
    return ok(data={"name": language.name}, msg="language registered")
