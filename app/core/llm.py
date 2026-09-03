"""AI 智能命题：调用 LLM 生成题目（Advance）。

当前默认使用 mock（不调用真实模型），先把流程跑通；
要接入真实模型时，填写下方 REAL_API_KEY，并将 USE_MOCK 改为 False。
"""

import json
import uuid

import requests

# ============================================================
# 真实 LLM 配置（接入真实模型时填写）
# ============================================================
USE_MOCK = True  # 改为 False 时启用真实模型调用
REAL_API_KEY = ""  # TODO: 在这里填入你的 API Key
REAL_BASE_URL = "https://api.openai.com/v1"  # 或 DeepSeek / 智谱等 OpenAI 兼容地址
REAL_MODEL = "gpt-4o-mini"  # 模型名称

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


def _mock_generate(requirement: str) -> dict:
    """mock：生成一个结构完整的示例题目（不含 id）。"""
    return {
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


def _real_generate(requirement: str, config: dict) -> dict:
    """真实调用 OpenAI 兼容 API 生成题目。"""
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
    content = resp.json()["choices"][0]["message"]["content"].strip()
    # 若模型输出被代码块包裹，剥离 ``` 标记
    if content.startswith("```"):
        content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(content)


def generate_problem(requirement: str, config: dict | None = None) -> dict:
    """生成题目（mock 或真实），返回题目 dict（不含 id，由上层生成）。

    config：模型配置（含 provider_url / model / api_key），为 None 或未配置 key 时走 mock。
    """
    if USE_MOCK or not config or not config.get("api_key"):
        return _mock_generate(requirement)
    return _real_generate(requirement, config)


def new_problem_id() -> str:
    """为 AI 生成的题目生成唯一 id。"""
    return "ai_" + uuid.uuid4().hex[:12]
