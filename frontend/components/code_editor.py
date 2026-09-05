"""内嵌代码编辑器（支持 Tab 缩进）——Streamlit 自定义组件。

用 st.components.declare_component 加载 frontend/components/editor/index.html，
在 iframe 内渲染一个等宽 <textarea>，拦截 Tab 键实现缩进/反缩进，
并通过组件协议把值实时回传给 Python（返回值即最新代码）。

用法（在 streamlit 页面里）：
    code = code_editor("print('hi')", height=240, key="editor")
"""
from pathlib import Path

import streamlit.components.v1 as components

_EDITOR_DIR = str(Path(__file__).resolve().parent / "editor")
_code_editor = components.declare_component("code_editor", path=_EDITOR_DIR)


def code_editor(code: str = "", height: int = 220, key=None) -> str:
    """渲染代码编辑器，返回当前文本。Tab 缩进、input 即回传。"""
    return _code_editor(code=code, height=height, key=key, default=code)
