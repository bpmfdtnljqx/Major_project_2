"""用户管理路由（Step 4）。

- POST /api/auth/login              登录（设置 session cookie）
- POST /api/auth/logout             登出（清除 session）
- POST /api/users/                  注册
- POST /api/users/admin             创建管理员（仅管理员）
- GET  /api/users/                  用户列表（仅管理员）
- GET  /api/users/{user_id}         查询用户信息（本人或管理员）
- PUT  /api/users/{user_id}/role    变更角色（仅管理员）
"""

import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.core.auth import get_admin, get_current_user
from app.core.response import AppError, ok
from app.models import Credentials, RoleUpdate

router = APIRouter()


@router.post("/auth/login")
async def login(request: Request, body: Credentials):
    """登录：校验凭证，创建会话并下发 session cookie。"""
    store = request.app.state.user_store
    user = store.verify_login(body.username, body.password)
    if user is None:
        raise AppError(401, "username or password incorrect")
    if user["role"] == "banned":
        raise AppError(403, "user is banned")

    session_id = uuid.uuid4().hex
    store.create_session(session_id, user["user_id"])

    resp = JSONResponse(content={
        "code": 200, "msg": "login success",
        "data": {"user_id": user["user_id"], "username": user["username"], "role": user["role"]},
    })
    resp.set_cookie("session", session_id, httponly=True)
    return resp


@router.post("/auth/logout")
async def logout(request: Request):
    """登出：删除会话并清除 cookie。"""
    store = request.app.state.user_store
    session_id = request.cookies.get("session")
    if not session_id or store.get_session(session_id) is None:
        raise AppError(401, "not logged in")
    store.delete_session(session_id)

    resp = JSONResponse(content={"code": 200, "msg": "logout success", "data": None})
    resp.delete_cookie("session")
    return resp


@router.post("/users/")
async def register(request: Request, body: Credentials):
    """注册新用户（默认 role=user）。"""
    user = request.app.state.user_store.create_user(body.username, body.password)
    if user is None:
        raise AppError(400, "username already exists")
    return ok(data={
        "user_id": user["user_id"],
        "username": user["username"],
        "join_time": user["join_time"],
        "role": user["role"],
        "submit_count": user["submit_count"],
        "resolve_count": user["resolve_count"],
    }, msg="register success")


@router.post("/users/admin")
async def create_admin(request: Request, body: Credentials, _: dict = Depends(get_admin)):
    """创建管理员账户（仅管理员）。"""
    user = request.app.state.user_store.create_user(body.username, body.password, role="admin")
    if user is None:
        raise AppError(400, "username already exists")
    return ok(data={"user_id": user["user_id"], "username": user["username"]})


@router.get("/users/")
async def list_users(
    request: Request,
    page: int | None = None,
    page_size: int | None = None,
    _: dict = Depends(get_admin),
):
    """用户列表（仅管理员，分页规则与评测列表一致）。"""
    if page is not None and page_size is None:
        raise AppError(400, "page_size required")
    if page is None and page_size is not None:
        page = 1
    total, users = request.app.state.user_store.list_users(page, page_size)
    return ok(data={"total": total, "users": users})


@router.get("/users/{user_id}")
async def get_user(request: Request, user_id: str, current: dict = Depends(get_current_user)):
    """查询用户信息（仅本人或管理员）。"""
    if current["user_id"] != user_id and current["role"] != "admin":
        raise AppError(403, "permission denied")
    user = request.app.state.user_store.get_by_id(user_id)
    if user is None:
        raise AppError(404, "user not found")
    return ok(data={
        "user_id": user["user_id"],
        "username": user["username"],
        "join_time": user["join_time"],
        "role": user["role"],
        "submit_count": user["submit_count"],
        "resolve_count": user["resolve_count"],
    })


@router.put("/users/{user_id}/role")
async def update_role(
    request: Request, user_id: str, body: RoleUpdate, _: dict = Depends(get_admin)
):
    """变更用户角色（仅管理员）。"""
    if body.role not in ("admin", "user", "banned"):
        raise AppError(400, "invalid role")
    if request.app.state.user_store.get_by_id(user_id) is None:
        raise AppError(404, "user not found")
    request.app.state.user_store.update_role(user_id, body.role)
    return ok(data={"user_id": user_id, "role": body.role}, msg="role updated")
