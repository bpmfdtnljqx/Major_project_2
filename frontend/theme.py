"""前端高级感主题（CSS 变量驱动，支持亮/暗双模式）。

配色架构：
- 所有颜色以 CSS 变量定义在 :root（默认 = 暗色 palette）。
- 亮色模式通过追加一段 <style> 重定义 :root 变量实现（同优先级后者生效，
  由浏览器在绘制时读取，故可即时切换自定义内容与绝大多数被覆盖的原生控件）。
- 克制、精致、非塑料：炭蓝黑底 + 单点暖琥珀强调（暗色）；暖白纸感 + 琥珀强调（亮色）。

用法：
    theme.inject()                      # app.py 顶部调用，按 session 模式注入
    theme.current_mode() -> "dark"|"light"
    theme.toggle()                       # 切换并 st.rerun（放顶栏）
"""

import streamlit as st

# ---- 暗色 palette（默认） ----
DARK = {
    "bg0": "#0b0f14", "bg1": "#10161e",
    "card": "#141b24", "raised": "#1a232e",
    "line": "#222c37", "line_hi": "#2e3b4a",
    "text": "#e6ebf2", "dim": "#9aa7b6", "faint": "#66727f",
    "accent": "#e6b47a", "accent_dim": "#c08f4e",
    "ok": "#7ec8a3", "err": "#e07b6a", "info": "#7aa2d8",
}

# ---- 亮色 palette ----
LIGHT = {
    "bg0": "#f6f4ef", "bg1": "#ffffff",
    "card": "#ffffff", "raised": "#f1eee8",
    "line": "#e4dfd6", "line_hi": "#cfc8bb",
    "text": "#23201c", "dim": "#6b655b", "faint": "#9b9487",
    "accent": "#a86f2c", "accent_dim": "#8a5a22",
    "ok": "#2f8f5b", "err": "#c14436", "info": "#38639e",
}


def _vars(p: dict) -> str:
    return "\n".join(f"  --{k}: {v};" for k, v in p.items())


def current_mode() -> str:
    return st.session_state.get("ui_theme", "dark")


def toggle() -> str:
    """切换亮/暗，返回新模式。调用后由调用方 st.rerun。"""
    nxt = "light" if current_mode() == "dark" else "dark"
    st.session_state["ui_theme"] = nxt
    return nxt


def inject() -> None:
    """注入主题。:root 始终定义暗色 palette；亮色模式追加覆盖。"""
    root_dark = f"<style>:root{{{_vars(DARK)}}}</style>"
    st.markdown(_BASE_CSS, unsafe_allow_html=True)
    st.markdown(root_dark, unsafe_allow_html=True)
    if current_mode() == "light":
        st.markdown(f"<style>:root{{{_vars(LIGHT)}}}</style>", unsafe_allow_html=True)


# =====================================================================
# 全局基础样式（所有颜色走 var()）
# =====================================================================
_BASE_CSS = """
<style>
/* ============ 根/背景 ============ */
.stApp {
    background:
        radial-gradient(1200px 600px at 15% -10%, var(--bg0), transparent 60%),
        radial-gradient(1000px 500px at 100% 0%, var(--bg1), transparent 55%),
        linear-gradient(180deg, var(--bg0) 0%, var(--bg1) 100%) !important;
    color: var(--text);
}
[data-testid="stAppViewContainer"] { background: transparent !important; }

/* ============ 字体 ============ */
html, body, [class*="css"], .stMarkdown, .stText, .stCaption, p, span, div, label {
    font-family: "Inter", -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}
code, pre, .stCodeBlock, textarea { font-family: "SF Mono","JetBrains Mono",Consolas,monospace !important; }
[data-testid="stMain"] { padding-top: 1.1rem; }
.block-container { max-width: 1200px; padding-top: 1.4rem; padding-bottom: 4rem; }

/* ============ 标题 ============ */
h1 { font-weight: 760; letter-spacing: -.02em; font-size: 1.8rem; color: var(--text); }
h2 { font-weight: 720; letter-spacing: -.01em; color: var(--text); }
h3 { font-weight: 660; color: var(--text); }
h1,h2,h3 { margin-bottom: .3rem; }

/* ============ 卡片容器 ============ */
.stExpander {
    border: 1px solid var(--line) !important; border-radius: 14px !important;
    background: var(--card); box-shadow: 0 1px 2px rgba(0,0,0,.18); overflow: hidden;
}
.stExpander:hover { border-color: var(--line_hi) !important; }
.stExpander [data-testid="stExpanderDetails"] {
    background: linear-gradient(180deg, var(--raised), var(--card));
    border-top: 1px solid var(--line);
}

/* ============ 按钮 ============ */
.stButton > button, .stFormSubmitButton > button, [data-testid="stBaseButton-secondary"] {
    border-radius: 10px !important; font-weight: 600 !important;
    transition: all .15s ease;
    border: 1px solid var(--line_hi) !important;
    background: var(--raised) !important; color: var(--text) !important;
}
.stButton > button:hover {
    border-color: var(--accent_dim) !important; transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,.18);
}
[data-testid="stBaseButton-primary"] {
    background: linear-gradient(180deg, var(--accent) 0%, var(--accent_dim) 100%) !important;
    border: none !important; color: #fff !important; font-weight: 650 !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 0 rgba(255,255,255,.2) inset, 0 2px 6px rgba(0,0,0,.18);
}
[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.06); }

/* ============ radio 导航胶囊 ============ */
div[data-testid="stRadio"] > div { gap: .2rem; }
div[data-testid="stRadio"] label { padding: .4rem .9rem; border-radius: 999px; color: var(--dim); transition: all .15s ease; }
div[data-testid="stRadio"] label:hover { color: var(--text); background: var(--raised); }
div[data-testid="stRadio"] [aria-checked="true"] {
    background: var(--raised) !important; color: var(--accent) !important;
    box-shadow: inset 0 0 0 1px var(--accent_dim); font-weight: 600;
}

/* ============ 输入类 ============ */
[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input, .stTextArea textarea {
    background: var(--raised) !important; border: 1px solid var(--line) !important;
    border-radius: 10px !important; color: var(--text) !important;
}
[data-baseweb="select"]:hover > div, .stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent_dim) !important;
    box-shadow: 0 0 0 1px color-mix(in srgb, var(--accent) 30%, transparent) !important;
}
[data-baseweb="popover"] [role="listbox"] { background: var(--card); border-radius: 10px; border: 1px solid var(--line); }

/* ============ 表格 ============ */
[data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
[data-testid="stDataFrame"] thead tr th {
    background: var(--raised) !important; color: var(--dim) !important;
    font-weight: 600; font-size: .8rem;
}

/* ============ metric ============ */
[data-testid="stMetric"] {
    background: var(--card); border: 1px solid var(--line); border-radius: 14px;
    padding: .9rem 1rem; box-shadow: 0 1px 2px rgba(0,0,0,.15);
}
[data-testid="stMetricLabel"] { color: var(--dim); font-weight: 600; }
[data-testid="stMetricValue"] { color: var(--text); font-weight: 720; font-size: 1.4rem; }

/* ============ 侧边栏 ============ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, var(--bg0), var(--bg1)) !important;
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] * { color: var(--dim); }

/* ============ tabs ============ */
.stTabs [data-baseweb="tab-list"] { gap: .3rem; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--dim) !important; border-radius: 8px !important; padding: .4rem .9rem; }
.stTabs [aria-selected="true"] { color: var(--accent) !important; border-bottom: 2px solid var(--accent_dim) !important; font-weight: 600; }

/* ============ 提示 ============ */
[data-testid="stAlert"] { border-radius: 12px; border-left-width: 3px; }
[data-testid="stAlert"] > div:first-child { background: var(--card) !important; }
div[data-baseweb="notification"] { background: var(--card) !important; border-radius: 12px; }

/* ============ 分隔线 / 滚动条 ============ */
hr { border-color: var(--line) !important; }
::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-thumb { background: var(--line_hi); border-radius: 6px; }
::-webkit-scrollbar-track { background: transparent; }

/* 代码块 */
.stCodeBlock { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.stCodeBlock pre { background: color-mix(in srgb, var(--raised) 92%, #000 8%) !important; }

/* 链接 */
a { color: var(--info); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ============ 高级卡片组件 ============ */
.hero { padding: .5rem .2rem 1rem .2rem; }
.hero-chip {
    display:inline-block; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase;
    color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent);
    border:1px solid color-mix(in srgb, var(--accent) 30%, transparent);
    border-radius:999px; padding:.18rem .7rem; margin-bottom:.7rem;
}
.hero-title { font-size:2rem; font-weight:780; letter-spacing:-.02em; line-height:1.1; color: var(--text); }
.hero-sub { color: var(--dim); margin-top:.5rem; font-size:1rem; max-width:56rem; }

.stat-card {
    background: linear-gradient(180deg, var(--raised), var(--card));
    border:1px solid var(--line); border-radius:14px; padding:1rem 1.1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,.12); min-height: 96px;
}
.stat-label { color: var(--dim); font-size:.78rem; letter-spacing:.04em; }
.stat-value { color: var(--text); font-size:1.7rem; font-weight:750; margin:.25rem 0 .1rem; letter-spacing:-.01em; }
.stat-hint { color: var(--faint); font-size:.75rem; }

/* 状态色小徽章 */
.badge { display:inline-block; border-radius:999px; padding:.1rem .6rem; font-size:.76rem; font-weight:600; }
.badge-ok { background: color-mix(in srgb, var(--ok) 16%, transparent); color: var(--ok); }
.badge-err { background: color-mix(in srgb, var(--err) 16%, transparent); color: var(--err); }
.badge-warn { background: color-mix(in srgb, var(--accent) 16%, transparent); color: var(--accent); }
.badge-info { background: color-mix(in srgb, var(--info) 16%, transparent); color: var(--info); }
</style>
"""


def hero(title: str, subtitle: str = "", chip: str | None = None) -> None:
    chip_html = f'<span class="hero-chip">{chip}</span>' if chip else ""
    st.markdown(
        f'<div class="hero">{chip_html}<div class="hero-title">{title}</div>'
        f'<div class="hero-sub">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def stat_cards(items: list[dict]) -> None:
    """一行统计卡片。item: {label, value, hint?}"""
    n = max(len(items), 1)
    cols = st.columns(n)
    for i, col in enumerate(cols):
        it = items[i] if i < len(items) else {"label": "", "value": ""}
        with col:
            st.markdown(
                f'<div class="stat-card"><div class="stat-label">{it.get("label","")}</div>'
                f'<div class="stat-value">{it.get("value","")}</div>'
                f'<div class="stat-hint">{it.get("hint","")}</div></div>',
                unsafe_allow_html=True,
            )


def badge(text: str, kind: str = "info") -> None:
    """状态徽章。kind: ok / err / warn / info"""
    st.markdown(f'<span class="badge badge-{kind}">{text}</span>', unsafe_allow_html=True)
