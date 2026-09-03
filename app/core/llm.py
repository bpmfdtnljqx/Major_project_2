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

# 生成题目的 prompt 模板
_PROMPT = """你是 OJ 出题助手。请根据以下需求生成一道编程题，并严格只输出 JSON（不要输出任何 JSON 以外的文字或代码块标记），字段如下：
{{
  "title": "题目标题",
  "description": "题目描述",
  "input_description": "输入格式说明",
  "output_description": "输出格式说明",
  "samples": [{{"input": "样例输入", "output": "样例输出"}}],
  "constraints": "数据范围与限制",
  "testcases": [{{"input": "测试输入", "output": "测试输出"}}],
  "hint": "提示",
  "tags": ["标签"],
  "time_limit": 1.0,
  "memory_limit": 128,
  "difficulty": "难度"
}}

需求：{requirement}
"""


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
            "messages": [{"role": "user", "content": _PROMPT.format(requirement=requirement)}],
            "temperature": 0.7,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"].strip()
    # 若模型输出被代码块包裹，剥离 ``` 标记
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
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
