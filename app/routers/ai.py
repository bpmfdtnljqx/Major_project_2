"""AI 智能命题路由（Advance）。

- GET  /api/ai/model-config               查询当前生效的模型配置
- PUT  /api/ai/model-config                配置模型
- POST /api/ai/problem-tasks/              创建命题任务（异步）
- GET  /api/ai/problem-tasks/{task_id}     查询任务状态 / 结果
- PUT  /api/ai/problem-tasks/{task_id}/cancel  中断任务
"""

import asyncio
import uuid

from fastapi import APIRouter, Depends, Request

from app.core.auth import get_current_user
from app.core.llm import generate_problem, new_problem_id
from app.core.response import AppError, ok
from app.models import AITaskCreate, ModelConfigBody, Problem

router = APIRouter()


def _authorized(task: dict, current: dict) -> bool:
    """任务创建者或管理员可见。"""
    return current["role"] == "admin" or task.get("user_id") == current["user_id"]


def _mask(key: str | None) -> str | None:
    """密钥打码：仅显示后 4 位，避免明文泄露。"""
    if not key:
        return None
    return "****" + key[-4:]


@router.get("/ai/model-config")
async def get_model_config(request: Request, _: dict = Depends(get_current_user)):
    """查询当前生效的模型配置（不含明文密钥）。

    DB 已保存配置则优先展示 DB，否则回退到 .env 环境变量默认值。
    """
    from app.core import llm  # 局部导入避免循环

    db = request.app.state.ai_store.get_config() or {}
    effective_key = db.get("api_key") or llm.REAL_API_KEY
    source = "db" if db.get("api_key") else ("env" if llm.REAL_API_KEY else "none")

    return ok(data={
        "provider_url": db.get("provider_url") or llm.REAL_BASE_URL,
        "model": db.get("model") or llm.REAL_MODEL,
        "input_price": db.get("input_price"),
        "output_price": db.get("output_price"),
        "price_unit": db.get("price_unit"),
        "key_configured": bool(effective_key),
        "key_hint": _mask(effective_key),
        "source": source,
        "use_mock": llm.USE_MOCK,
    })


@router.put("/ai/model-config")
async def set_model_config(request: Request, body: ModelConfigBody, _: dict = Depends(get_current_user)):
    """配置模型（api_key 不通过查询接口返回明文；留空则沿用当前密钥）。"""
    from app.core import llm  # 局部导入避免循环

    store = request.app.state.ai_store
    current = store.get_config() or {}

    if body.api_key:
        # 显式提供新密钥：直接保存（覆盖）
        api_key = body.api_key
    elif current.get("api_key"):
        # 留空但有已存密钥：沿用 DB 密钥，仅更新其余字段
        api_key = current["api_key"]
    else:
        # 留空且 DB 无密钥：不落库，保持 .env 回退，仅提示
        api_key = llm.REAL_API_KEY or ""
        return ok(data={
            "provider_url": body.provider_url,
            "model": body.model,
            "input_price": body.input_price,
            "output_price": body.output_price,
            "price_unit": body.price_unit,
            "key_configured": bool(api_key),
            "note": "未保存 api_key，将沿用 .env 环境变量配置",
        }, msg="using env config (key not changed)")

    store.set_config(
        body.provider_url, body.model, api_key,
        body.input_price, body.output_price, body.price_unit,
    )
    return ok(data={
        "provider_url": body.provider_url,
        "model": body.model,
        "api_key_configured": bool(api_key),
        "input_price": body.input_price,
        "output_price": body.output_price,
        "price_unit": body.price_unit,
    }, msg="model config updated")


@router.post("/ai/problem-tasks/")
async def create_ai_task(request: Request, body: AITaskCreate, current: dict = Depends(get_current_user)):
    """创建命题任务，异步执行。"""
    problem_store = request.app.state.problem_store
    ai_store = request.app.state.ai_store

    if body.problem_id is not None and problem_store.get(body.problem_id) is None:
        raise AppError(404, "problem not found")

    task_id = uuid.uuid4().hex
    ai_store.create_task(task_id, body.requirement, body.problem_id, current["user_id"])

    task = asyncio.create_task(_run_ai_task(request.app, task_id, body.requirement))
    request.app.state.ai_tasks.add(task)
    task.add_done_callback(request.app.state.ai_tasks.discard)

    return ok(data={"task_id": task_id, "status": "pending"}, msg="task created")


async def _run_ai_task(app, task_id: str, requirement: str):
    """后台执行命题任务：调 LLM → 自动加入题库 → 更新状态。"""
    ai_store = app.state.ai_store
    problem_store = app.state.problem_store
    try:
        ai_store.update_task(task_id, status="running", progress="正在生成题目")
        if ai_store.get_task(task_id)["status"] == "cancelled":
            return

        config = ai_store.get_config()
        problem, usage = await asyncio.to_thread(generate_problem, requirement, config)

        if ai_store.get_task(task_id)["status"] == "cancelled":
            return

        # 自动加入题库（体验优先，教师/助教无需手动导入）
        problem["id"] = new_problem_id()
        problem_store.add(Problem(**problem))

        ai_store.update_task(
            task_id, status="completed", progress="已完成并加入题库",
            result=problem, usage=usage,
        )
    except Exception as exc:  # noqa: BLE001
        ai_store.update_task(task_id, status="failed", progress=f"生成失败：{exc}")


@router.get("/ai/problem-tasks/{task_id}")
async def get_ai_task(request: Request, task_id: str, current: dict = Depends(get_current_user)):
    """查询任务状态 / 结果（任务创建者或管理员）。"""
    task = request.app.state.ai_store.get_task(task_id)
    if task is None:
        raise AppError(404, "task not found")
    if not _authorized(task, current):
        raise AppError(403, "permission denied")
    return ok(data={
        "task_id": task["task_id"],
        "status": task["status"],
        "progress": task["progress"],
        "result": task["result"],
        "usage": task["usage"],
    })


@router.put("/ai/problem-tasks/{task_id}/cancel")
async def cancel_ai_task(request: Request, task_id: str, current: dict = Depends(get_current_user)):
    """中断任务（任务创建者或管理员）。"""
    ai_store = request.app.state.ai_store
    task = ai_store.get_task(task_id)
    if task is None:
        raise AppError(404, "task not found")
    if not _authorized(task, current):
        raise AppError(403, "permission denied")
    if task["status"] in ("completed", "failed", "cancelled"):
        raise AppError(409, "task already finished")
    ai_store.update_task(task_id, status="cancelled", progress="已中断")
    return ok(data={"task_id": task_id, "status": "cancelled"}, msg="task cancelled")
