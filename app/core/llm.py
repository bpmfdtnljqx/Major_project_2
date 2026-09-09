"""AI 智能命题：调用 LLM 生成题目（Advance）。

当前默认使用 mock（不调用真实模型），先把流程跑通；
要接入真实模型时，填写下方 REAL_API_KEY，并将 USE_MOCK 改为 False。
"""

import json
import os
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

# 加载项目根目录的 .env（存 API Key，已被 .gitignore 忽略，不会提交）
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

# ============================================================
# 真实 LLM 配置（在 .env 中填写，参考 .env.example 模板）
# ============================================================
USE_MOCK = os.getenv("AI_USE_MOCK", "true").lower() == "true"  # true 时用 mock，不调真实模型
REAL_API_KEY = os.getenv("AI_API_KEY", "")  # 你的 API Key
REAL_BASE_URL = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")  # OpenAI 兼容地址
REAL_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")  # 模型名称

# 生成题目的 prompt：system 强调出题质量，user 承载具体需求
_SYSTEM_PROMPT = """你是一位资深的算法竞赛命题专家，负责为在线评测系统（OJ）设计高质量编程题。
你需要独立完成题目设计、题目配置生成与测试点生成的全部环节，并严格只输出一个 JSON 对象（不要输出任何 JSON 以外的文字、解释或代码块标记）。

命题质量要求：
1. 题目描述清晰、无歧义，明确输入输出的数据含义与格式，可独立成题。
2. 必须紧扣用户给出的知识点与难度要求，不得生成无关内容。
3. 测试点（testcases）不少于 3 组，且必须覆盖关键边界条件：最小值、最大值、空输入、特殊值、大规模数据等。
4. 测试数据规模应能区分不同时间复杂度的算法（例如 O(n) 与 O(n^2) 在大数据点上产生差异）。
5. 样例（samples）给出 1~2 组，与测试点不重复。
6. 若题目是纯算法题（如图论、动态规划），不得要求真实运行外部程序或依赖第三方库，仅需通过标准输入输出判题。

输出 JSON 的字段结构（缺一不可）：
{
  "title": "题目标题",
  "description": "题目描述（含问题背景与任务要求）",
  "input_description": "输入格式说明",
  "output_description": "输出格式说明",
  "samples": [{"input": "样例输入", "output": "样例输出"}],
  "constraints": "数据范围与限制",
  "testcases": [{"input": "测试输入", "output": "测试输出"}],
  "hint": "解题提示（可为空字符串）",
  "tags": ["标签1", "标签2"],
  "time_limit": 1.0,
  "memory_limit": 128,
  "difficulty": "难度（入门/中等/困难）"
}"""

_USER_PROMPT = """请根据以下命题需求生成一道完整题目：\n\n{requirement}"""


def _mock_generate(requirement: str) -> tuple[dict, dict]:
    """mock：生成一个结构完整的示例题目（不含 id），返回 (problem, usage)。"""
    problem = {
        "title": requirement[:30] + ("……" if len(requirement) > 30 else ""),
        "description": requirement or "（由 AI 生成的题目描述）",
        "input_description": "每行一个测试用例，具体格式见题目描述。",
        "output_description": "对每个测试用例输出对应结果。",
        "samples": [{"input": "示例输入", "output": "示例输出"}],
        "constraints": "1 <= n <= 1000",
        "testcases": [{"input": "示例输入", "output": "示例输出"}],
        "hint": "",
        "source": "AI 生成",
        "tags": ["AI生成"],
        "time_limit": 1.0,
        "memory_limit": 128,
        "author": "AI",
        "difficulty": "入门",
    }
    usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost": 0.0, "currency": "USD"}
    return problem, usage


def _real_generate(requirement: str, config: dict) -> tuple[dict, dict]:
    """真实调用 OpenAI 兼容 API 生成题目，返回 (problem, usage)。"""
    resp = requests.post(
        f"{config['provider_url'].rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {config['api_key']}"},
        json={
            "model": config["model"],
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _USER_PROMPT.format(requirement=requirement)},
            ],
            "temperature": 0.6,
        },
        timeout=220,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    # 若模型输出被代码块包裹，剥离 ``` 标记
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    # 部分模型会在 JSON 前后附少量说明文字，取首个 { 到最后一个 } 之间的内容
    start, end = content.find("{"), content.rfind("}")
    if start != -1 and end != -1 and end > start:
        content = content[start : end + 1]
    problem = json.loads(content)

    # Token 用量与费用计算
    u = data.get("usage", {})
    input_tokens = u.get("prompt_tokens", 0) or 0
    output_tokens = u.get("completion_tokens", 0) or 0
    total_tokens = u.get("total_tokens", input_tokens + output_tokens) or 0
    price_unit = config.get("price_unit") or 1000000
    input_price = config.get("input_price") or 0.0
    output_price = config.get("output_price") or 0.0
    cost = round(input_tokens / price_unit * input_price + output_tokens / price_unit * output_price, 6)
    usage = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "cost": cost,
        "currency": "USD",
    }
    return problem, usage


def generate_problem(requirement: str, config: dict | None = None) -> tuple[dict, dict]:
    """生成题目，返回 (problem_dict, usage_dict)。

    config：模型配置（含 provider_url / model / api_key / 价格）；为 None 时用 .env 环境变量。
    USE_MOCK 或未配置 key 时走 mock。
    """
    if config is None:
        config = {"provider_url": REAL_BASE_URL, "model": REAL_MODEL, "api_key": REAL_API_KEY}
    if USE_MOCK or not config.get("api_key"):
        return _mock_generate(requirement)
    return _real_generate(requirement, config)


def new_problem_id() -> str:
    """为 AI 生成的题目生成唯一 id。"""
    return "ai_" + uuid.uuid4().hex[:12]
