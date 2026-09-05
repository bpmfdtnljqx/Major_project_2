"""前端高级感主题（CSS 覆盖暗/亮双模式）。

设计原则（经过用户截图验证后重写）：
- 直接给 Streamlit 控件明确的 CSS 选择器 + 具体 hex 色，**不依赖 CSS 变量/color-mix**，
  确保 base=dark/light 任一状态下都能生效。
- 暗色：炭蓝黑底 + 单点琥珀强调
- 亮色：暖白纸感底 + 琥珀强调（**绝不用纯白雪白配字**）
"""

import streamlit as st

# ---- 暗色 palette ----
DARK = dict(
    bg_grad_a="#15202c", bg_grad_b="#0b0f14", bg_grad_c="#10161e",
    card="#141b24", raised="#1a232e",
    line="#222c37", line_hi="#2e3b4a",
    text="#e6ebf2", dim="#9aa7b6", faint="#7c8896",
    accent="#e6b47a", accent_dim="#c08f4e",
    ok="#7ec8a3", err="#e07b6a", info="#7aa2d8",
    input_bg="#1a232e", code_bg="#0d1218",
)

# ---- 亮色 palette：暖白纸感，绝不用雪白配字 ----
LIGHT = dict(
    bg_grad_a="#ece7dd", bg_grad_b="#f5f2ec", bg_grad_c="#fbf9f4",
    card="#fbf9f4", raised="#efeae2",
    line="#d8d0c2", line_hi="#b9b0a0",
    text="#2a241d", dim="#5a5346", faint="#8a8172",
    accent="#b5712c", accent_dim="#8f5a22",
    ok="#2f8a57", err="#bd4335", info="#3c639b",
    input_bg="#fdfcf8", code_bg="#efeae2",
)


def _vars(p):
    return "\n".join(f"--{k}:{v};" for k, v in p.items())


def current_mode() -> str:
    return st.session_state.get("ui_theme", "dark")


def toggle():
    st.session_state["ui_theme"] = "light" if current_mode() == "dark" else "dark"


def inject() -> None:
    pal = LIGHT if current_mode() == "light" else DARK
    mood = "亮" if current_mode() == "light" else "暗"

    css = f"""
<style id="wb-theme">
/* ============ 关键：覆盖 Streamlit 默认背景/文字（不用变量，避免失效） ============ */
.stApp, [data-testid="stAppViewContainer"], .main {{
    background: linear-gradient(180deg, {pal['bg_grad_a']} 0%, {pal['bg_grad_b']} 60%, {pal['bg_grad_c']} 100%) !important;
    color: {pal['text']} !important;
}}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
    color: {pal['text']} !important;
}}
/* 文本类（含 markdown/正文/链接默认色）*/
.stApp p, .stApp span, .stApp div, .stApp label {{
    color: {pal['text']};
}}
.stApp a {{ color: {pal['info']}; }}

/* ============ 控件标签（统一字号/颜色） ============ */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
[data-testid="stWidgetLabel"] label {{
    color: {pal['dim']} !important;
    font-weight: 600; font-size: .9rem !important;
}}

/* ============ 输入控件（强化：覆盖 baseweb 多层） ============ */
.stTextInput input, .stTextArea textarea, .stNumberInput input {{
    background: {pal['input_bg']} !important;
    border: 1px solid {pal['line_hi']} !important;
    border-radius: 10px !important;
    color: {pal['text']} !important;
    -webkit-text-fill-color: {pal['text']} !important;
    box-shadow: none !important;
}}
/* Streamlit 在 input 外层加 data-baseweb="input"，里面有个 div 套 input */
[data-baseweb="input"], [data-baseweb="base-input"] {{
    background: {pal['input_bg']} !important;
    border-color: {pal['line_hi']} !important;
    border-radius: 10px !important;
}}
[data-baseweb="select"] > div,
[data-baseweb="select"] > div > div {{
    background: {pal['input_bg']} !important;
    border: 1px solid {pal['line_hi']} !important;
    border-radius: 10px !important;
    color: {pal['text']} !important;
    box-shadow: none !important;
}}
[data-baseweb="select"]:focus-within > div,
[data-baseweb="select"]:hover > div,
.stTextInput:focus-within > div,
.stTextInput:hover,
.stTextArea:focus-within > div,
.stNumberInput:focus-within > div {{
    border-color: {pal['accent']} !important;
    box-shadow: 0 0 0 2px {pal['accent']}33 !important;
}}
/* 去掉 baseweb 内部多余深色描边 */
[data-baseweb="select"] * {{ box-shadow: none !important; }}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {{
    color: {pal['faint']} !important;
    -webkit-text-fill-color: {pal['faint']} !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus,
[data-baseweb="select"]:focus-within > div,
[data-baseweb="select"]:hover > div {{
    border-color: {pal['accent']} !important;
    box-shadow: 0 0 0 2px {pal['accent']}33 !important;
}}
[data-baseweb="popover"] [role="listbox"] {{
    background: {pal['card']} !important;
    color: {pal['text']} !important;
    border: 1px solid {pal['line_hi']};
}}
[data-baseweb="popover"] [role="option"] {{ color: {pal['text']} !important; }}

/* ============ 按钮 ============ */
.stButton > button, .stFormSubmitButton > button,
[data-testid="stBaseButton-secondary"] {{
    background: {pal['raised']} !important;
    color: {pal['text']} !important;
    border: 1px solid {pal['line_hi']} !important;
    border-radius: 10px !important; font-weight: 600;
    transition: all .15s ease;
}}
.stButton > button:hover {{ border-color: {pal['accent']} !important; }}
[data-testid="stBaseButton-primary"] {{
    background: linear-gradient(180deg, {pal['accent']}, {pal['accent_dim']}) !important;
    color: #ffffff !important;
    border: none !important; font-weight: 650;
    border-radius: 10px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.25);
}}
[data-testid="stBaseButton-primary"]:hover {{ filter: brightness(1.08); }}

/* ============ radio / 顶部导航 ============ */
/* 去掉 Streamlit 默认的未选中黑圆点；自定义胶囊 */
div[data-testid="stRadio"] label > div:first-child,
div[data-testid="stRadio"] [role="radio"] > div,
div[data-testid="stRadio"] svg {{ display: none !important; }}
div[data-testid="stRadio"] label {{
    color: {pal['dim']} !important;
    padding: .35rem .95rem; border-radius: 999px;
    background: transparent !important;
    transition: all .15s ease;
    font-weight: 500;
}}
div[data-testid="stRadio"] label:hover {{
    color: {pal['text']} !important; background: {pal['raised']} !important;
}}
div[data-testid="stRadio"] [aria-checked="true"] {{
    background: {pal['accent']}22 !important;
    color: {pal['accent']} !important;
    box-shadow: inset 0 0 0 1px {pal['accent']} !important;
    font-weight: 700 !important;
}}
/* 顶部那一行 radio 不画背景框 */
div[data-testid="stRadio"]:not(:has(text)) {{ background: transparent !important; }}

/* ============ Tabs ============ */
.stTabs [data-baseweb="tab-list"] {{ gap: .25rem; }}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: {pal['dim']} !important;
    padding: .4rem .9rem; border-radius: 8px;
}}
.stTabs [aria-selected="true"] {{
    color: {pal['accent']} !important;
    border-bottom: 2px solid {pal['accent']} !important;
    font-weight: 700;
}}

/* ============ Expander 卡片（关键：解决"黑色大块"问题） ============ */
.stExpander, details[data-testid="stExpander"] {{
    background: {pal['card']} !important;
    border: 1px solid {pal['line']} !important;
    border-radius: 14px !important;
    overflow: hidden;
}}
.stExpander summary, [data-testid="stExpanderToggle"] summary {{
    background: {pal['card']} !important;
    color: {pal['text']} !important;
    border: none !important;
}}
.stExpander [data-testid="stExpanderDetails"],
[data-testid="stExpander"] > div:last-child {{
    background: {pal['card']} !important;
    color: {pal['text']} !important;
    border-top: 1px solid {pal['line']};
}}

/* ============ 关键修复：selectbox 下拉关闭时也是 input_bg（避免黑块） ============ */
[data-baseweb="select"] [data-baseweb="select-value],
[data-baseweb="select"] [data-baseweb="select-value] > div {{
    color: {pal['text']} !important;
}}

/* ============ 代码块（st.code + st_ace 容器；用 data-testid 精准匹配） ============ */
[data-testid="stCodeBlock"], .stCodeBlock,
[data-testid="stCodeBlock"] pre, .stCodeBlock pre {{
    background: {pal['code_bg']} !important;
    color: {pal['text']} !important;
    border: 1px solid {pal['line']} !important;
    border-radius: 10px !important;
}}
[data-testid="stCodeBlock"] code {{ color: {pal['text']} !important; }}
/* st_ace 自定义组件容器外框：让 ace 在亮色下用细边框替换它默认深框 */
iframe[title*="streamlit_ace"], [data-testid="stExpander"] iframe {{
    border: 1px solid {pal['line_hi']} !important;
    border-radius: 10px;
}}

/* ============ Tabs 面板内/外背景 ============ */
[data-baseweb="tab-panel"], [data-testid="stTabBody"] {{
    background: transparent !important;
}}

/* ============ Form 容器 ============ */
[data-testid="stForm"] {{
    background: {pal['card']} !important;
    border: 1px solid {pal['line']};
    border-radius: 14px; padding: 1rem 1.2rem;
}}

/* ============ Metric 卡片 ============ */
[data-testid="stMetric"] {{
    background: {pal['card']}; border: 1px solid {pal['line']};
    border-radius: 14px; padding: 1rem;
}}
[data-testid="stMetricLabel"] {{ color: {pal['dim']}; }}
[data-testid="stMetricValue"] {{ color: {pal['text']}; font-weight: 720; }}

/* ============ Dataframe 表格 ============ */
[data-testid="stDataFrame"] {{
    border: 1px solid {pal['line']};
    border-radius: 12px; overflow: hidden;
    background: {pal['card']};
}}
[data-testid="stDataFrame"] thead th {{
    background: {pal['raised']} !important;
    color: {pal['dim']} !important;
}}

/* ============ 侧边栏（柔和，不黑块） ============ */
section[data-testid="stSidebar"], [data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {pal['card']}, {pal['bg_grad_b']}) !important;
    border-right: 1px solid {pal['line']} !important;
    min-width: 0 !important;
    width: 280px !important;
}}
[data-testid="stSidebar"] > div:first-child {{ background: transparent !important; }}
[data-testid="stSidebar"] * {{ color: {pal['text']}; }}
/* 侧边栏里 caption/小字 */
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{
    color: {pal['dim']} !important;
}}
/* 侧边栏按钮 */
[data-testid="stSidebar"] .stButton > button {{
    background: {pal['raised']} !important;
    border: 1px solid {pal['line_hi']} !important;
    color: {pal['text']} !important;
    border-radius: 10px !important;
}}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {{
    background: linear-gradient(180deg, {pal['accent']}, {pal['accent_dim']}) !important;
    color: #fff !important; border: none !important;
}}

/* ============ 滚动条 ============ */
::-webkit-scrollbar-thumb {{ background: {pal['line_hi']}; border-radius: 6px; }}

/* ============ caption / 小字 ============ */
.stCaption, [data-testid="stCaptionContainer"] p,
.stMarkdown small {{ color: {pal['dim']} !important; }}

/* ============ 提示框 ============ */
[data-testid="stAlert"] {{ border-radius: 12px; }}
[data-testid="stAlert"] > div:first-child {{ background: {pal['card']} !important; }}

/* ============ 高级 HTML 卡片工具类 ============ */
.hero {{ padding: .4rem .2rem .8rem; }}
.hero-chip {{
    display:inline-block; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase;
    color: {pal['accent']}; background: {pal['accent']}1f;
    border:1px solid {pal['accent']}55; border-radius:999px; padding:.18rem .7rem;
    margin-bottom:.6rem;
}}
.hero-title {{ font-size:1.9rem; font-weight:780; color: {pal['text']}; letter-spacing:-.02em; }}
.hero-sub {{ color: {pal['dim']}; margin-top:.4rem; font-size:1rem; }}
.stat-card {{
    background: linear-gradient(180deg, {pal['raised']}, {pal['card']});
    border:1px solid {pal['line']}; border-radius:14px; padding:1rem 1.1rem;
    min-height: 96px;
}}
.stat-label {{ color: {pal['dim']}; font-size:.78rem; letter-spacing:.04em; }}
.stat-value {{ color: {pal['text']}; font-size:1.7rem; font-weight:750; margin:.25rem 0 .1rem; }}
.stat-hint {{ color: {pal['faint']}; font-size:.75rem; }}
.sec-title {{
    font-size:1.15rem; font-weight:720; color:{pal['text']};
    padding-left:.6rem; border-left:3px solid {pal['accent']};
    margin:1rem 0 .6rem; letter-spacing:-.01em;
}}
.diff {{ display:inline-block; border-radius:999px; padding:.12rem .7rem; font-size:.74rem; font-weight:650;
    background: {pal['dim']}22; color: {pal['dim']}; }}
.diff-0 {{ color:{pal['ok']}; background:{pal['ok']}1f; }}
.diff-1 {{ color:{pal['info']}; background:{pal['info']}1f; }}
.diff-2 {{ color:{pal['accent']}; background:{pal['accent']}1f; }}
.diff-3 {{ color:{pal['err']}; background:{pal['err']}1f; }}
.chip {{
    display:inline-block; border-radius:6px; padding:.1rem .55rem; font-size:.74rem;
    background: {pal['raised']}; color: {pal['dim']}; border:1px solid {pal['line']};
    margin-right:.35rem;
}}
.badge {{ display:inline-block; border-radius:999px; padding:.12rem .6rem; font-size:.76rem; font-weight:650; }}
.badge-ok {{ background: {pal['ok']}22; color: {pal['ok']}; }}
.badge-err {{ background: {pal['err']}22; color: {pal['err']}; }}
.badge-warn {{ background: {pal['accent']}22; color: {pal['accent']}; }}
.badge-info {{ background: {pal['info']}22; color: {pal['info']}; }}
.badge-neu {{ background: {pal['dim']}22; color: {pal['dim']}; }}

/* 字体 */
.stApp, .stApp *, code, pre {{ font-family: "Inter","PingFang SC","Microsoft YaHei",-apple-system,"Segoe UI",sans-serif; }}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


def hero(title, subtitle="", chip=None):
    chip_html = f'<span class="hero-chip">{chip}</span>' if chip else ""
    st.markdown(
        f'<div class="hero">{chip_html}<div class="hero-title">{title}</div>'
        f'<div class="hero-sub">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def stat_cards(items):
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


def section(title):
    st.markdown(f'<div class="sec-title">{title}</div>', unsafe_allow_html=True)


def difficulty(d):
    d = (d or "").strip()
    if not d: return
    low = d.lower()
    lvl = 3 if any(x in low for x in ["困难","hard","高级","advanced","较难"]) else \
          2 if any(x in low for x in ["中等","medium"]) else \
          1 if any(x in low for x in ["入门","简单","easy","beginner"]) else 0
    st.markdown(f'<span class="diff diff-{lvl}">{d}</span>', unsafe_allow_html=True)


_STATUS = {"ac":"ok","success":"ok","wa":"err","error":"err","ce":"err","failed":"err",
           "tle":"warn","mle":"warn","re":"err","pending":"neu","running":"info",
           "queued":"neu","cancelled":"neu","completed":"ok"}


def status_badge(s):
    k = str(s or "").lower()
    return f'<span class="badge badge-{_STATUS.get(k,"info")}">{s}</span>'
