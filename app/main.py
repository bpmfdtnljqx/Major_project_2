"""FastAPI 应用入口。

- 初始化题目存储（启动时播种 seed 题目并加载进内存）；
- 挂载各模块路由；
- 注册全局异常处理器，保证所有响应均为 {code, msg, data} 且状态码与 code 一致。

启动命令：uvicorn app.main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

from app.core.access_log_store import AccessLogStore
from app.core.ai_store import AIStore
from app.core.language_store import LanguageStore
from app.core.rate_limit import RateLimiter
from app.core.response import AppError, error_response
from app.core.storage import ProblemStore
from app.core.submission_store import SubmissionStore
from app.core.user_store import UserStore
from app.routers import ai, languages, logs, problems, submissions, system, users

# 项目根目录（app/ 的上一级）
BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> FastAPI:
    app = FastAPI(title="OJ System")

    # 初始化题目存储：problems/ 为空时从 seed/ 播种
    app.state.problem_store = ProblemStore(
        problems_dir=BASE_DIR / "problems",
        seed_dir=BASE_DIR / "seed",
    )

    # 初始化语言存储：内置默认语言 + 动态注册语言
    app.state.language_store = LanguageStore(BASE_DIR / "data" / "languages.json")

    # 初始化提交存储（SQLite）与频率限制
    app.state.submission_store = SubmissionStore(BASE_DIR / "data" / "oj.db")
    app.state.user_store = UserStore(BASE_DIR / "data" / "oj.db")
    app.state.access_log_store = AccessLogStore(BASE_DIR / "data" / "oj.db")
    app.state.ai_store = AIStore(BASE_DIR / "data" / "oj.db")
    app.state.rate_limiter = RateLimiter()
    app.state.judge_tasks = set()  # 持有后台评测任务引用，防被 GC
    app.state.ai_tasks = set()  # 持有后台 AI 命题任务引用，防被 GC

    # 挂载路由
    app.include_router(problems.router, prefix="/api")
    app.include_router(languages.router, prefix="/api")
    app.include_router(submissions.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(logs.router, prefix="/api")
    app.include_router(ai.router, prefix="/api")
    app.include_router(system.router, prefix="/api")

    _register_exception_handlers(app)
    return app


def _register_exception_handlers(app: FastAPI) -> None:
    """统一异常处理：业务异常 / 参数校验 / 框架异常。"""

    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return error_response(exc.code, exc.msg)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError):
        # FastAPI 默认将参数校验错误返回 422，按 api.md 要求统一为 400
        return error_response(400, "invalid parameters")

    @app.exception_handler(HTTPException)
    async def _http_error(request: Request, exc: HTTPException):
        return error_response(exc.status_code, str(exc.detail))


app = create_app()
