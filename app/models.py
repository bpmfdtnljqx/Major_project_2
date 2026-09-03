"""数据模型定义：题目（Problem）。

本模块定义 OJ 系统的核心数据模型，使用 Pydantic 进行字段校验，
字段定义严格对齐 api.md 中的题目数据模型。

- 8 个必填字段：缺失时 Pydantic 自动抛出校验错误；
- 7 个可选字段：给出默认值，与 api.md 中的默认值保持一致。
"""

from pydantic import BaseModel, Field


class TestCase(BaseModel):
    """单个测试点 / 样例：包含标准输入与预期输出。"""

    input: str = Field(..., description="标准输入")
    output: str = Field(..., description="预期输出")


class Problem(BaseModel):
    """题目完整数据模型。"""

    # ---- 必填字段 ----
    id: str = Field(..., description="题目唯一标识")
    title: str = Field(..., description="题目标题")
    description: str = Field(..., description="题目描述")
    input_description: str = Field(..., description="输入格式说明")
    output_description: str = Field(..., description="输出格式说明")
    samples: list[TestCase] = Field(..., description="样例输入输出")
    constraints: str = Field(..., description="数据范围与限制条件")
    testcases: list[TestCase] = Field(..., description="测试点")

    # ---- 可选字段（带默认值） ----
    hint: str = Field("", description="额外提示")
    source: str = Field("", description="题目来源")
    tags: list[str] = Field([], description="题目标签")
    time_limit: float = Field(3.0, description="时间限制（秒）")
    memory_limit: int = Field(128, description="内存限制（MB）")
    author: str = Field("", description="题目作者")
    difficulty: str = Field("", description="难度等级")
