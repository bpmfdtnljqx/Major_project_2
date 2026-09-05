"""前端高级感主题 CSS。

在 app.py 顶部调用 theme.inject()，一次性注入全局样式，
让所有视图（题目/做题/我的/AI）质感统一：炭蓝黑底 + 柔和渐变 + 单点暖色强调，
克制、精致、非塑料（不依赖霓虹渐变/发光按钮）。
"""

import streamlit as st

# ---- 设计令牌（集中定义，方便整体换肤） ----
_BG0 = "#0b0f14"        # 页面底色（炭蓝黑）
_BG1 = "#0f151d"        # 渐变浅层
_BG_CARD = "#141b24"    # 卡片底色
_BG_RAISED = "#1a232e"  # 悬浮/强调容器
_LINE = "#222c37"       # 分隔线/描边（低对比）
_LINE_HI = "#2c3947"
_TEXT = "#e6ebf2"       # 主文字
_TEXT_DIM = "#9aa7b6"   # 次要文字
_TEXT_FAINT = "#6b7887"
_ACCENT = "#e6b47a"     # 单点暖色强调（琥珀，克制）
_ACCENT_DIM = "#c99a58"
_OK = "#7ec8a3"         # 语义绿（通过/AC）
_WARN = "#e6b47a"       # 警告/部分
_ERR = "#e07b6a"        # 错误/失败
_INFO = "#79a8e0"       # 信息（低饱和蓝）

_CSS = f"""
<style>
/* ============ 根/背景：柔和炭蓝渐变 ============ */
.stApp {{
    background:
        radial-gradient(1200px 600px at 15% -10%, rgba(38,52,66,.45), transparent 60%),
        radial-gradient(1000px 500px at 100% 0%, rgba(35,46,60,.32), transparent 55%),
        linear-gradient(180deg, {_BG0} 0%, {_BG1} 100%) !important;
    color: {_TEXT};
}}
[data-testid="stAppViewContainer"] {{
    background: transparent !important;
}}

/* ============ 全局字体与排版 ============ */
html, body, [class*="css"], .stMarkdown, .stText, .stCaption, p, span, div, label {{
    font-family: "Inter", -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}}
code, pre, .stCodeBlock, textarea {{
    font-family: "SF Mono", "JetBrains Mono", Consolas, "Menlo", monospace !important;
}}

/* 主区留白更从容 */
[data-testid="stMain"] {{ padding-top: 1.2rem; }}
.block-container {{ max-width: 1200px; padding-top: 1.5rem; padding-bottom: 4rem; }}

/* ============ 标题层级 ============ */
h1 {{ font-weight: 750; letter-spacing: -0.02em; font-size: 1.85rem; color: {_TEXT}; }}
h2, .stTitle {{ font-weight: 700; letter-spacing: -0.01em; }}
h3 {{ font-weight: 650; color: {_TEXT}; }}
h1, h2, h3 {{ margin-bottom: .3rem; }}

/* ============ 精致卡片容器 ============ */
div[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius: 14px; }}
.stExpander {{
    border: 1px solid {_LINE} !important;
    border-radius: 14px !important;
    background: {_BG_CARD};
    box-shadow: 0 1px 2px rgba(0,0,0,.3);
    overflow: hidden;
}}
.stExpander:hover {{ border-color: {_LINE_HI} !important; }}
.stExpander details > summary {{ background: {_BG_CARD}; }}
.stExpander [data-testid="stExpanderDetails"] {{
    background: linear-gradient(180deg, {_BG_RAISED}, {_BG_CARD});
    border-top: 1px solid {_LINE};
}}

/* ============ 按钮：克制但精致 ============ */
.stButton > button, .stFormSubmitButton > button, [data-testid="stBaseButton-primary"] {{
    border-radius: 10px !important;
    font-weight: 600 !important;
    letter-spacing: .01em;
    transition: all .15s ease;
    border: 1px solid {_LINE_HI} !important;
    background: {_BG_RAISED} !important;
    color: {_TEXT} !important;
}}
.stButton > button:hover {{
    border-color: {_ACCENT_DIM} !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,.35);
}}
[data-testid="stBaseButton-primary"] {{
    background: linear-gradient(180deg, {_ACCENT} 0%, {_ACCENT_DIM} 100%) !important;
    border-color: transparent !important;
    color: #1a1308 !important;
    box-shadow: 0 1px 0 rgba(255,255,255,.15) inset, 0 2px 6px rgba(0,0,0,.3);
}}
[data-testid="stBaseButton-primary"]:hover {{
    filter: brightness(1.05);
    box-shadow: 0 6px 16px rgba(0,0,0,.35);
}}

/* ============ radio 导航（顶栏）：胶囊高亮 ============ */
div[data-testid="stRadio"] > div {{ gap: .25rem; }}
div[data-testid="stRadio"] label {{
    padding: .4rem .95rem;
    border-radius: 999px;
    color: {_TEXT_DIM};
    transition: all .15s ease;
}}
div[data-testid="stRadio"] label:hover {{ color: {_TEXT}; background: {_BG_RAISED}; }}
div[data-testid="stRadio"] [aria-checked="true"] {{
    background: {_BG_RAISED} !important;
    color: {_ACCENT} !important;
    box-shadow: inset 0 0 0 1px {_ACCENT_DIM};
    font-weight: 600;
}}
div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p {{ font-size: .95rem; }}

/* ============ selectbox / input / textarea ============ */
[data-baseweb="select"] > div, .stTextInput input, .stNumberInput input, .stTextArea textarea {{
    background: {_BG_RAISED} !important;
    border: 1px solid {_LINE} !important;
    border-radius: 10px !important;
    color: {_TEXT} !important;
}}
[data-baseweb="select"]:hover > div, .stTextInput input:focus,
.stTextArea textarea:focus {{
    border-color: {_ACCENT_DIM} !important;
    box-shadow: 0 0 0 1px rgba(230,180,122,.25) !important;
}}
[data-baseweb="popover"] [role="listbox"] {{ background: {_BG_CARD}; border-radius: 10px; border:1px solid {_LINE}; }}

/* ============ 表格 ============ */
[data-testid="stDataFrame"] {{
    border: 1px solid {_LINE};
    border-radius: 12px;
    overflow: hidden;
}}
[data-testid="stDataFrame"] thead tr th {{
    background: {_BG_RAISED} !important;
    color: {_TEXT_DIM};
    font-weight: 600;
    font-size: .8rem;
    letter-spacing: .02em;
}}

/* ============ metric：精致数据卡 ============ */
[data-testid="stMetric"] {{
    background: {_BG_CARD};
    border: 1px solid {_LINE};
    border-radius: 14px;
    padding: .9rem 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,.25);
}}
[data-testid="stMetricLabel"] {{ color: {_TEXT_DIM}; font-weight: 600; }}
[data-testid="stMetricValue"] {{ color: {_TEXT}; font-weight: 700; font-size: 1.4rem; }}

/* ============ 分割线 ============ */
hr {{ border-color: {_LINE} !important; }}

/* ============ 侧边栏：深底、无突兀 ============ */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {_BG0}, #0d1218) !important;
    border-right: 1px solid {_LINE};
}}
[data-testid="stSidebar"] * {{ color: {_TEXT_DIM}; }}

/* ============ tabs ============ */
.stTabs [data-baseweb="tab-list"] {{ gap: .3rem; }}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: {_TEXT_DIM} !important;
    border-radius: 8px !important;
    padding: .4rem .9rem;
}}
.stTabs [aria-selected="true"] {{
    color: {_ACCENT} !important;
    border-bottom: 2px solid {_ACCENT_DIM} !important;
    font-weight: 600;
}}

/* ============ 提示/状态（去饱和、克制的语义色） ============ */
[data-testid="stAlert"] {{ border-radius: 12px; border-left-width: 3px; }}
[data-testid="stAlert"] > div:first-child {{ background: {_BG_CARD} !important; }}
div[data-baseweb="notification"] {{ background: {_BG_CARD} !important; border-radius: 12px; }}

/* ============ 滚动条 ============ */
::-webkit-scrollbar {{ width: 10px; height: 10px; }}
::-webkit-scrollbar-thumb {{ background: {_LINE_HI}; border-radius: 6px; }}
::-webkit-scrollbar-thumb:hover {{ background: #38485a; }}
::-webkit-scrollbar-track {{ background: transparent; }}

/* ============ 自定义高颜值小工具 ============ */
.stCodeBlock {{ border: 1px solid {_LINE}; border-radius: 12px; overflow: hidden; }}
.stCodeBlock pre {{ background: #0d1218 !important; }}

/* 分页/链接点击无恼人下划线 */
a {{ color: {_INFO}; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
</style>
"""


def inject() -> None:
    """在应用最顶部调用一次，注入全局主题样式。"""
    st.markdown(_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str = "", chip: str | None = None) -> None:
    """页面顶部的精致欢迎区。"""
    chip_html = f'<span class="hero-chip">{chip}</span>' if chip else ""
    html = f"""
    <div class="hero">
        {chip_html}
        <div class="hero-title">{title}</div>
        <div class="hero-sub">{subtitle}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        .hero { padding: .6rem .2rem 1rem .2rem; }
        .hero-chip {
            display:inline-block; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase;
            color:#c99a58; background:rgba(230,180,122,.10);
            border:1px solid rgba(230,180,122,.28); border-radius:999px; padding:.18rem .7rem; margin-bottom:.7rem;
        }
        .hero-title { font-size:2rem; font-weight:780; letter-spacing:-.02em; line-height:1.1; }
        .hero-sub { color:#9aa7b6; margin-top:.5rem; font-size:1rem; max-width:56rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def stat_cards(items: list[dict]) -> None:
    """渲染一行统计卡片。item: {label, value, hint?}"""
    n = max(len(items), 1)
    cols = st.columns(n)
    # 每张卡单独放一列，便于对齐
    for i, col in enumerate(cols):
        it = items[i] if i < len(items) else {"label": "", "value": ""}
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-label">{it.get('label', '')}</div>
                <div class="stat-value">{it.get('value', '')}</div>
                <div class="stat-hint">{it.get('hint', '')}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown(
        """
        <style>
        .stat-card {
            background: linear-gradient(180deg, #161e28, #111820);
            border:1px solid #222c37; border-radius:14px; padding:1rem 1.1rem;
            box-shadow: 0 1px 2px rgba(0,0,0,.25); min-height: 96px;
        }
        .stat-label { color:#8b98a8; font-size:.78rem; letter-spacing:.04em; }
        .stat-value { color:#e6ebf2; font-size:1.7rem; font-weight:750; margin:.25rem 0 .1rem; letter-spacing:-.01em;}
        .stat-hint { color:#5f6b79; font-size:.75rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
