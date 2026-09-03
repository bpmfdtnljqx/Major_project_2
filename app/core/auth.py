"""鉴权依赖（Step 4）。

基于 Session Cookie：
- get_current_user：读 cookie 中的 session → 查会话 → 得到用户；banned 返回 403。
- get_admin：在 get_current_user 基础上校验 admin 角色。

依赖会把当前用户写入 request.state，供业务层使用（如提交频率限制按用户）。
"""

from fastapi import Request

from app.core.response import AppError


async def get_current_user(request: Request) -> dict:
    """从会话解析当前登录用户；未登录返回 401，被禁用返回 403。"""
    session_id = request.cookies.get("session")
    if not session_id:
        raise AppError(401, "not logged in")

    store = request.app.state.user_store
    session = store.get_session(session_id)
    if session is None:
        raise AppError(401, "not logged in")

    user = store.get_by_id(session["user_id"])
    if user is None:
        raise AppError(401, "not logged in")
    if user["role"] == "banned":
        raise AppError(403, "user is banned")

    request.state.user_id = user["user_id"]
    request.state.user = user
    return user


async def get_admin(request: Request) -> dict:
    """校验当前用户为管理员，否则返回 403。"""
    user = await get_current_user(request)
    if user["role"] != "admin":
        raise AppError(403, "permission denied")
    return user
