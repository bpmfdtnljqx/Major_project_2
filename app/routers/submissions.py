"""提交评测路由（Step 2 / Step 3）。

POST /api/submissions/                        —— 提交代码，异步评测，立即返回 pending。
GET  /api/submissions/                        —— 查询评测列表（过滤 + 分页）。
GET  /api/submissions/{submission_id}         —— 查询评测结果。
PUT  /api/submissions/{submission_id}/rejudge —— 重新评测（覆盖原结果）。
GET  /api/submissions/{submission_id}/log     —— 查询评测日志（测试点明细）。
评测任务在后台通过 asyncio.to_thread 运行阻塞的 judge，完成后回写 SQLite。
"""

import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, Request

from app.core.auth import get_admin, get_current_user
from app.core.judge import judge
from app.core.response import AppError, ok
from app.models import SubmissionCreate

router = APIRouter()

# 评测工作目录（写入用户代码、编译产物）
JUDGE_DIR = Path(__file__).resolve().parent.parent.parent / "tmp" / "judge"


def _stores(request: Request):
    return (
        request.app.state.problem_store,
        request.app.state.language_store,
        request.app.state.submission_store,
    )


@router.post("/submissions/")
async def create_submission(request: Request, body: SubmissionCreate, current: dict = Depends(get_current_user)):
    problem_store, language_store, submission_store = _stores(request)

    # 校验题目与语言存在
    problem = problem_store.get(body.problem_id)
    if problem is None:
        raise AppError(404, "problem not found")
    language = language_store.get(body.language)
    if language is None:
        raise AppError(404, "language not found")

    # 频率限制（按用户）
    user_id = current["user_id"]
    if not request.app.state.rate_limiter.check(user_id):
        raise AppError(429, "too many submissions")

    # 写入 pending 记录
    submission_id = uuid.uuid4().hex
    submission_store.create(submission_id, body.problem_id, body.language, body.code, user_id)

    # 启动异步评测
    task = asyncio.create_task(
        _judge_task(submission_store, problem, language, body.code, submission_id)
    )
    request.app.state.judge_tasks.add(task)
    task.add_done_callback(request.app.state.judge_tasks.discard)

    return ok(data={"submission_id": submission_id, "status": "pending"})


@router.get("/submissions/{submission_id}")
async def get_submission(request: Request, submission_id: str, current: dict = Depends(get_current_user)):
    """查询评测结果（Step 3，本人或管理员）。"""
    store = request.app.state.submission_store
    sub = store.get(submission_id)
    if sub is None:
        raise AppError(404, "submission not found")
    if current["role"] != "admin" and sub["user_id"] != current["user_id"]:
        raise AppError(403, "permission denied")
    data = {
        "submission_id": sub["submission_id"],
        "status": sub["status"],
        "score": sub["score"],
        "counts": sub["counts"],
        "compile_info": sub["compile_info"],
        "run_info": sub["run_info"],
        "error_info": sub["error_info"],
    }
    return ok(data=data)


@router.get("/submissions/")
async def list_submissions(
    request: Request,
    user_id: str | None = None,
    problem_id: str | None = None,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    current: dict = Depends(get_current_user),
):
    """查询评测列表（Step 3，本人或管理员）。"""
    # 权限：普通用户只能查自己的提交
    if current["role"] != "admin":
        if user_id is not None and user_id != current["user_id"]:
            raise AppError(403, "permission denied")
        user_id = current["user_id"]
    # 一级条件不可同时为空
    if user_id is None and problem_id is None:
        raise AppError(400, "user_id or problem_id required")
    # 分页规则：page 非空但 page_size 空 → 400；page 空但 page_size 非空 → 取第一页
    if page is not None and page_size is None:
        raise AppError(400, "page_size required")
    if page is None and page_size is not None:
        page = 1

    store = request.app.state.submission_store
    total, submissions = store.list(user_id, problem_id, status, page, page_size)

    items = []
    for s in submissions:
        if s["status"] in ("error", "pending"):
            items.append({"submission_id": s["submission_id"], "status": s["status"]})
        else:
            items.append({
                "submission_id": s["submission_id"],
                "status": s["status"],
                "score": s["score"],
                "counts": s["counts"],
            })
    return ok(data={"total": total, "submissions": items})


@router.put("/submissions/{submission_id}/rejudge")
async def rejudge_submission(request: Request, submission_id: str, _: dict = Depends(get_admin)):
    """重新评测（Step 3，仅管理员）：覆盖原结果，异步重跑。"""
    problem_store = request.app.state.problem_store
    language_store = request.app.state.language_store
    submission_store = request.app.state.submission_store

    sub = submission_store.get(submission_id)
    if sub is None:
        raise AppError(404, "submission not found")
    problem = problem_store.get(sub["problem_id"])
    if problem is None:
        raise AppError(404, "problem not found")
    language = language_store.get(sub["language"])
    if language is None:
        raise AppError(404, "language not found")

    # 覆盖原结果：重置为 pending
    submission_store.update(
        submission_id,
        status="pending", score=None, counts=None,
        compile_info=None, run_info=None, error_info=None, details=None,
    )

    # 启动异步评测
    task = asyncio.create_task(
        _judge_task(submission_store, problem, language, sub["code"], submission_id)
    )
    request.app.state.judge_tasks.add(task)
    task.add_done_callback(request.app.state.judge_tasks.discard)

    return ok(data={"submission_id": submission_id, "status": "pending"}, msg="rejudge started")


@router.get("/submissions/{submission_id}/log")
async def get_submission_log(request: Request, submission_id: str, current: dict = Depends(get_current_user)):
    """查询评测日志（Step 5）：本人 / 管理员 / 题目公开时可见。"""
    store = request.app.state.submission_store
    sub = store.get(submission_id)
    if sub is None:
        raise AppError(404, "submission not found")

    problem = request.app.state.problem_store.get(sub["problem_id"])
    public_cases = problem.public_cases if problem else False

    is_admin = current["role"] == "admin"
    is_owner = sub["user_id"] == current["user_id"]
    if not (is_admin or is_owner or public_cases):
        raise AppError(403, "permission denied")

    return ok(data={"details": sub["details"], "score": sub["score"], "counts": sub["counts"]})


async def _judge_task(submission_store, problem, language, code, submission_id):
    """后台评测任务：运行 judge 并将结果回写存储。"""
    work_dir = JUDGE_DIR / submission_id
    try:
        compile_result, details = await asyncio.to_thread(
            judge, code, language, problem.testcases,
            problem.time_limit, problem.memory_limit, work_dir,
        )
        counts = len(problem.testcases) * 10
        score = sum(10 for d in details if d["result"] == "AC")
        run_info = {"result": "finished", "message": f"{len(details)} test cases finished"}
        submission_store.update(
            submission_id,
            status="success",
            score=score,
            counts=counts,
            compile_info=compile_result,
            run_info=run_info,
            details=details,
            error_info="",
        )
    except Exception as exc:  # noqa: BLE001
        submission_store.update(submission_id, status="error", error_info=str(exc))
