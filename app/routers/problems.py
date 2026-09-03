"""题目管理路由（Step 1）。

提供题目的增删改查接口，路径与 api.md 保持一致：
- GET    /api/problems/
- POST   /api/problems/
- GET    /api/problems/{problem_id}
- PUT    /api/problems/{problem_id}
- DELETE /api/problems/{problem_id}

注意：鉴权（401/403）在 Step 4 统一补充，当前暂不校验。
"""

from fastapi import APIRouter, Request

from app.core.response import AppError, ok
from app.models import Problem

router = APIRouter()


def _store(request: Request):
    """从应用状态中取出题目存储实例。"""
    return request.app.state.store


@router.get("/problems/")
async def list_problems(request: Request):
    """查看题目列表：返回全部题目的简要信息（id + title）。"""
    store = _store(request)
    data = [{"id": p.id, "title": p.title} for p in store.list_all()]
    return ok(data=data)


@router.post("/problems/")
async def create_problem(request: Request, problem: Problem):
    """添加题目：校验字段完整性后保存，id 已存在返回 409。"""
    store = _store(request)
    if store.exists(problem.id):
        raise AppError(409, "problem already exists")
    store.add(problem)
    return ok(data={"id": problem.id}, msg="add success")


@router.get("/problems/{problem_id}")
async def get_problem(request: Request, problem_id: str):
    """查看题目详情：返回完整题目配置。"""
    store = _store(request)
    problem = store.get(problem_id)
    if problem is None:
        raise AppError(404, "problem not found")
    return ok(data=problem.model_dump())


@router.put("/problems/{problem_id}")
async def update_problem(request: Request, problem_id: str, problem: Problem):
    """编辑题目：校验完整配置后覆盖，请求体 id 须与路径一致。"""
    store = _store(request)
    if problem.id != problem_id:
        raise AppError(400, "problem id mismatch")
    if not store.exists(problem_id):
        raise AppError(404, "problem not found")
    store.update(problem)
    return ok(data={"id": problem_id}, msg="update success")


@router.delete("/problems/{problem_id}")
async def delete_problem(request: Request, problem_id: str):
    """删除题目：按 id 删除对应配置。"""
    store = _store(request)
    if not store.exists(problem_id):
        raise AppError(404, "problem not found")
    store.delete(problem_id)
    return ok(data={"id": problem_id}, msg="delete success")
