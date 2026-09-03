"""统一响应封装。

所有接口的响应体统一为 {code, msg, data} 三元组，且 HTTP 状态码与 code 一致。

- ok()：成功响应（状态码固定 200）；
- AppError：业务异常，携带 HTTP 状态码与提示信息，由全局异常处理器
  统一转换为 JSONResponse，保证状态码与 code 一致。
"""

from fastapi.responses import JSONResponse


def ok(data=None, msg: str = "success") -> dict:
    """构造成功响应体（FastAPI 默认返回 200，与 code 一致）。"""
    return {"code": 200, "msg": msg, "data": data}


class AppError(Exception):
    """业务异常：携带 HTTP 状态码与提示信息。"""

    def __init__(self, code: int, msg: str):
        self.code = code
        self.msg = msg
        super().__init__(msg)


def error_response(code: int, msg: str) -> JSONResponse:
    """构造错误 JSONResponse（状态码与 code 一致，data 为 null）。"""
    return JSONResponse(status_code=code, content={"code": code, "msg": msg, "data": None})
