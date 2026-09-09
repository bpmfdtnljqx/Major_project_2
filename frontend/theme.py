"""前端设计系统（暗 / 亮双主题）。

设计原则（经用户多轮确认后定型）：
- 直接展开成具体 hex 颜色，不依赖 CSS 变量 / color-mix，确保 base=dark/light
  任一状态下都能稳定生效。
- 高级、克制、精致但不简陋：低饱和、单点暖琥珀强调，无霓虹、无玻璃拟态、
  无大面积发光渐变。
- 暗色 = 炭蓝黑底 + 琥珀强调；亮色 = 暖白纸感 + 琥珀强调（绝不用雪白配近白字）。
- 不隐藏 Streamlit 内部 SVG（会破坏折叠/部署/密码眼睛等图标，导致 aria-label
  fallback 文字乱码）。圆点问题改用 st.pills 原生控件解决，不再靠 CSS 抹掉。
"""

import html
import streamlit as st

# ============================ 调色板 ============================
# 暗色：炭蓝黑 + 单点琥珀
DARK = dict(
    bg_top="#141b24", bg_mid="#0e141b", bg_bottom="#0b0f14",
    surface="#161e27", surface_hi="#1c2631",
    border="#26313d", border_hi="#33404e",
    text="#e8edf3", dim="#9aa7b6", faint="#6f7d8c",
    accent="#e6b47a", accent_dim="#c9965a",
    accent_soft="rgba(230,180,122,0.14)", accent_line="rgba(230,180,122,0.35)",
    ok="#7ec8a3", ok_soft="rgba(126,200,163,0.14)",
    err="#e07b6a", err_soft="rgba(224,123,106,0.14)",
    info="#7aa2d8", info_soft="rgba(122,162,216,0.14)",
    warn="#d9b36a", warn_soft="rgba(217,179,106,0.14)",
    neu_soft="rgba(154,167,182,0.14)",
    input_bg="#121a23", code_bg="#0d1218",
)

# 亮色：暖白纸感 + 琥珀
LIGHT = dict(
    bg_top="#f2eee6", bg_mid="#f6f3ec", bg_bottom="#faf8f3",
    surface="#ffffff", surface_hi="#f4efe6",
    border="#e4dccc", border_hi="#cfc4ae",
    text="#26201a", dim="#4a4238", faint="#7a7062",
    accent="#a8651f", accent_dim="#8a5318",
    accent_soft="rgba(168,101,31,0.10)", accent_line="rgba(168,101,31,0.30)",
    ok="#2f8a57", ok_soft="rgba(47,138,87,0.10)",
    err="#bd4335", err_soft="rgba(189,67,53,0.10)",
    info="#3c639b", info_soft="rgba(60,99,155,0.10)",
    warn="#a9761f", warn_soft="rgba(169,118,31,0.10)",
    neu_soft="rgba(74,66,56,0.08)",
    input_bg="#ffffff", code_bg="#f4efe6",
)


def _mode() -> str:
    return st.session_state.get("ui_theme", "dark")


def current_mode() -> str:
    """公开的当前主题（"dark" / "light"）。"""
    return _mode()


def _pal() -> dict:
    return LIGHT if _mode() == "light" else DARK


def toggle() -> None:
    st.session_state["ui_theme"] = "light" if _mode() == "dark" else "dark"


def mode_label() -> str:
    """返回「切换到另一主题」的按钮文案（当前模式 → 目标模式）。"""
    return "🌙 暗色" if _mode() == "light" else "☀️ 亮色"


# ============================ CSS 注入 ============================
def inject() -> None:
    p = _pal()
    # f-string 里 CSS 的花括号需写 {{ }}；颜色占位用 {p['...']}
    css = f"""
<style id="wb-theme">
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded&display=block');

/* ============ 关键说明 ============
   1. 必须加载 'Material Symbols Rounded'（Streamlit 1.63 iconFont 默认名），不能用 'Material Icons'。
      DynamicIcon 用 font-feature-settings:'liga' 渲染 ligature，字体名不匹配会 fallback 成纯文字。
   2. 不要隐藏整个 stToolbar！它包含侧栏折叠(stSidebarCollapseButton)/展开(stExpandSidebarButton)按钮。
      只隐藏 Deploy 按钮(stAppDeployButton)。 */
[data-testid="stAppDeployButton"] {{ display: none !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}
#MainMenu {{ display: none !important; }}
footer {{ display: none !important; }}
header[data-testid="stHeader"] {{ background: transparent !important; }}
/* 侧栏折叠/展开按钮：保留，仅调整颜色，让侧栏能正常折叠和恢复 */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="stExpandSidebarButton"] button {{
    color: {p['dim']} !important;
}}
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="stExpandSidebarButton"] button:hover {{
    color: {p['accent']} !important;
}}

/* ============ 全局 Material Symbols Rounded 字体（让密码 reveal、expander 箭头等图标正常） ============
   Streamlit 把图标渲染成 <span data-testid="stIconMaterial" translate="no">visibility</span>，
   用 font-feature: 'liga' ligature 解析。字体名必须严格匹配 Material Symbols Rounded。 */
[data-baseweb="icon"], [data-testid="stIconMaterial"],
[class*="material-icons"], [class*="MaterialSymbols"] {{
    font-family: 'Material Symbols Rounded' !important;
    font-weight: normal !important; font-style: normal !important;
    line-height: 1; letter-spacing: normal; word-wrap: normal;
    white-space: nowrap; direction: ltr; display: inline-block;
    font-feature-settings: 'liga';
    -webkit-font-feature-settings: 'liga';
    -webkit-font-smoothing: antialiased;
}}

/* ============ 全局背景 / 文字 ============ */
.stApp, [data-testid="stAppViewContainer"], .main {{
    background: linear-gradient(180deg, {p['bg_top']} 0%, {p['bg_mid']} 55%, {p['bg_bottom']} 100%) !important;
    color: {p['text']} !important;
}}
[data-testid="stAppViewBlockContainer"] {{
    padding-top: 1.2rem !important; max-width: 1200px !important;
}}
.stApp h1, .stApp h2, .stApp h3, .stApp h4 {{
    color: {p['text']} !important;
    letter-spacing: -0.01em;
}}
.stApp p, .stApp span, .stApp label, .stApp li, .stApp td, .stApp th {{
    color: {p['text']};
}}
.stApp a {{ color: {p['info']}; text-decoration: none; }}
.stApp a:hover {{ text-decoration: underline; }}
.stApp hr {{ border-color: {p['border']}; }}
.stMarkdown code:not([class]) {{
    background: {p['code_bg']} !important; color: {p['accent']} !important;
    padding: .1rem .35rem; border-radius: 5px; font-size: .88em;
}}
.stMarkdown pre {{
    background: {p['code_bg']} !important; color: {p['text']} !important;
    border: 1px solid {p['border']} !important; border-radius: 10px !important;
}}
.stMarkdown pre code {{ color: {p['text']} !important; background: transparent !important; }}

/* ============ 控件标签 ============ */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] span,
[data-testid="stWidgetLabel"] label {{
    color: {p['dim']} !important;
    font-weight: 600; font-size: .88rem !important;
}}

/* ============ 输入控件（Streamlit 1.63 真实 testid，不再用 data-baseweb） ============
   Streamlit 1.63 内部没有 data-baseweb 属性，input 框/+/−按钮等用 emotion hash class。
   真实 testid：stTextInputField / stNumberInputField / stNumberInputStepUp/Down /
   stSelectbox / stCheckbox / stTextArea。用 testid + 后代选择器精准覆盖。 */

/* text input 真正输入框 */
[data-testid="stTextInputField"],
[data-testid="stTextInput"] input,
.stTextInput input {{
    background: {p['input_bg']} !important;
    border: 1px solid {p['border_hi']} !important;
    border-radius: 9px !important;
    color: {p['text']} !important;
    -webkit-text-fill-color: {p['text']} !important;
    box-shadow: none !important;
}}
/* text input 根元素（包裹层，透明避免深色漏出） */
[data-testid="stTextInputRootElement"] {{ background: transparent !important; }}
/* 密码框 reveal 按钮（stTextInput 内部 button） */
[data-testid="stTextInput"] button {{
    background: transparent !important;
    color: {p['dim']} !important;
    box-shadow: none !important; border: none !important;
}}
[data-testid="stTextInput"] button:hover {{ color: {p['accent']} !important; }}
/* number input 输入框 */
[data-testid="stNumberInputField"],
[data-testid="stNumberInput"] input,
.stNumberInput input {{
    background: {p['input_bg']} !important;
    border: 1px solid {p['border_hi']} !important;
    border-radius: 9px !important;
    color: {p['text']} !important;
    -webkit-text-fill-color: {p['text']} !important;
    box-shadow: none !important;
}}
/* number input +/- 按钮（真实 testid：StepUp / StepDown） */
[data-testid="stNumberInputStepUp"],
[data-testid="stNumberInputStepDown"] {{
    background: {p['surface_hi']} !important;
    color: {p['dim']} !important;
    border: 1px solid {p['border']} !important;
    box-shadow: none !important;
}}
[data-testid="stNumberInputStepUp"]:hover,
[data-testid="stNumberInputStepDown"]:hover {{
    color: {p['accent']} !important;
    background: {p['accent_soft']} !important;
}}
/* selectbox 容器 + 内部文字 */
[data-testid="stSelectbox"] {{ background: {p['input_bg']} !important; }}
[data-testid="stSelectbox"] > div {{
    background: {p['input_bg']} !important;
    border: 1px solid {p['border_hi']} !important;
    border-radius: 9px !important;
    color: {p['text']} !important;
    box-shadow: none !important;
}}
[data-testid="stSelectbox"] * {{
    color: {p['text']} !important;
    -webkit-text-fill-color: {p['text']} !important;
}}
/* text area */
[data-testid="stTextArea"] textarea,
.stTextArea textarea {{
    background: {p['input_bg']} !important;
    border: 1px solid {p['border_hi']} !important;
    border-radius: 9px !important;
    color: {p['text']} !important;
    -webkit-text-fill-color: {p['text']} !important;
    box-shadow: none !important;
}}
/* checkbox 方块（stCheckbox 内部 role=checkbox / input） */
[data-testid="stCheckbox"] {{ background: transparent !important; }}
[data-testid="stCheckbox"] [role="checkbox"],
[data-testid="stCheckbox"] input[type="checkbox"] {{
    background: {p['input_bg']} !important;
    border: 1.5px solid {p['border_hi']} !important;
    border-radius: 4px !important;
}}
/* placeholder */
[data-testid="stTextInputField"]::placeholder,
[data-testid="stTextArea"] textarea::placeholder,
.stTextInput input::placeholder, .stTextArea textarea::placeholder {{
    color: {p['faint']} !important;
    -webkit-text-fill-color: {p['faint']} !important;
}}
/* 聚焦状态 */
[data-testid="stTextInputField"]:focus,
[data-testid="stNumberInputField"]:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: {p['accent']} !important;
    box-shadow: 0 0 0 2px {p['accent_soft']} !important;
}}
/* selectbox 下拉展开的 popover */
[data-testid="stSelectboxVirtualDropdown"] {{
    background: {p['surface']} !important;
    color: {p['text']} !important;
    border: 1px solid {p['border_hi']};
    border-radius: 10px !important;
}}

/* ============ 按钮 ============ */
.stButton > button, .stFormSubmitButton > button,
[data-testid="stBaseButton-secondary"] {{
    background: {p['surface_hi']} !important;
    color: {p['text']} !important;
    border: 1px solid {p['border_hi']} !important;
    border-radius: 9px !important; font-weight: 600;
    transition: all .15s ease;
}}
.stButton > button:hover {{ border-color: {p['accent']} !important; color: {p['accent']} !important; }}
[data-testid="stBaseButton-primary"], button[kind="primary"] {{
    background: linear-gradient(180deg, {p['accent']}, {p['accent_dim']}) !important;
    color: #fff !important;
    border: none !important; font-weight: 650;
    border-radius: 9px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,.2);
}}
[data-testid="stBaseButton-primary"]:hover, button[kind="primary"]:hover {{
    filter: brightness(1.07);
}}

/* ============ stButtonGroup（pills + segmented_control 共用，Streamlit 1.63 真实 testid） ============ */
/* 注：st.pills 与 st.segmented_control 前端共用 ButtonGroup 组件，testid 都是 stButtonGroup。
   选择器：[aria-checked="true"] / [aria-pressed="true"] 双覆盖。 */
[data-testid="stButtonGroup"] {{ gap: .3rem; }}
[data-testid="stButtonGroup"] button {{
    background: transparent !important;
    color: {p['dim']} !important;
    border: 1px solid transparent !important;
    border-radius: 999px !important;
    padding: .38rem 1.05rem !important;
    font-weight: 600; font-size: .92rem !important;
    transition: all .15s ease;
}}
[data-testid="stButtonGroup"] button:hover {{
    color: {p['text']} !important; background: {p['surface_hi']} !important;
}}
[data-testid="stButtonGroup"] [aria-checked="true"],
[data-testid="stButtonGroup"] [aria-pressed="true"] {{
    background: {p['accent_soft']} !important;
    color: {p['accent']} !important;
    border-color: {p['accent_line']} !important;
    font-weight: 700 !important;
}}

/* ============ segmented_control 容器（语言切换）：浅底圆角分隔 ============ */
[data-testid="stButtonGroup"]:has(button[aria-checked="true"]) {{
    background: {p['surface_hi']};
    border: 1px solid {p['border']};
    border-radius: 9px; padding: 2px;
}}

/* ============ Tabs（登录页用） ============ */
.stTabs [data-baseweb="tab-list"] {{ gap: .25rem; border-bottom: 1px solid {p['border']}; }}
.stTabs [data-baseweb="tab"] {{
    background: transparent !important;
    color: {p['dim']} !important;
    padding: .45rem .95rem; border-radius: 8px 8px 0 0; font-weight: 600;
}}
.stTabs [aria-selected="true"] {{
    color: {p['accent']} !important;
    border-bottom: 2px solid {p['accent']} !important;
}}
[data-baseweb="tab-panel"], [data-testid="stTabBody"] {{ background: transparent !important; }}

/* ============ Expander 卡片 ============ */
.stExpander, details[data-testid="stExpander"] {{
    background: {p['surface']} !important;
    border: 1px solid {p['border']} !important;
    border-radius: 12px !important; overflow: hidden;
}}
.stExpander summary, [data-testid="stExpanderToggle"] summary {{
    background: {p['surface']} !important;
    color: {p['text']} !important; border: none !important;
    font-weight: 600;
}}
/* Expander summary 里的图标用主题色（避免 fallback 文字与正文混在一起） */
.stExpander summary [data-testid="stIconMaterial"],
[data-testid="stExpanderToggle"] summary [data-testid="stIconMaterial"] {{
    color: {p['dim']} !important;
    font-size: 1rem !important;
}}
.stExpander [data-testid="stExpanderDetails"] {{
    background: {p['surface']} !important;
    color: {p['text']} !important; border-top: 1px solid {p['border']};
}}

/* ============ st.code 代码块 ============ */
[data-testid="stCodeBlock"], .stCodeBlock,
[data-testid="stCodeBlock"] pre, .stCodeBlock pre {{
    background: {p['code_bg']} !important;
    color: {p['text']} !important;
    border: 1px solid {p['border']} !important;
    border-radius: 10px !important;
}}
[data-testid="stCodeBlock"] code, .stCodeBlock code {{ color: {p['text']} !important; }}
/* streamlit-ace 代码编辑器：让 iframe 容器+iframe 自身都跟主题走
   （亮色下也要有明确浅底色，不要下方露出 baseweb panel 的深色） */
iframe[title*="streamlit_ace"] {{
    border: 1px solid {p['border_hi']} !important;
    border-radius: 10px !important;
    min-height: 360px !important;
    background: {p['input_bg']} !important;
    color-scheme: light dark;
    display: block !important;
}}
/* streamlit-ace 外层 div：靠属性匹配透明化 */
div:has(> iframe[title*="streamlit_ace"]) {{
    background: transparent !important;
    padding: 0 !important;
}}

/* ============ Form 容器 ============ */
[data-testid="stForm"] {{
    background: {p['surface']} !important;
    border: 1px solid {p['border']} !important;
    border-radius: 12px !important; padding: 1rem 1.2rem;
}}

/* ============ Metric 卡片 ============ */
[data-testid="stMetric"] {{
    background: {p['surface']}; border: 1px solid {p['border']};
    border-radius: 12px; padding: .9rem 1rem;
}}
[data-testid="stMetricLabel"] {{ color: {p['dim']}; }}
[data-testid="stMetricValue"] {{ color: {p['text']}; font-weight: 720; }}

/* ============ 表格（st.table 是 HTML table，可精准覆盖） ============ */
[data-testid="stTable"] {{
    border: 1px solid {p['border']}; border-radius: 12px; overflow: hidden;
    background: {p['surface']};
}}
[data-testid="stTable"] table {{
    background: {p['surface']} !important;
    border-collapse: collapse; width: 100%;
}}
[data-testid="stTable"] thead th,
[data-testid="stTable"] thead tr th {{
    background: {p['surface_hi']} !important;
    color: {p['dim']} !important;
    font-weight: 600;
    border-bottom: 1px solid {p['border']} !important;
    padding: .5rem .75rem;
}}
[data-testid="stTable"] tbody tr td {{
    background: {p['surface']} !important;
    color: {p['text']} !important;
    border-bottom: 1px solid {p['border']} !important;
    padding: .45rem .75rem;
}}
[data-testid="stTable"] tbody tr:nth-child(even) td {{
    background: {p['surface_hi']} !important;
}}

/* ============ 侧边栏（干净，不黑块） ============ */
section[data-testid="stSidebar"], [data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {p['surface']}, {p['bg_mid']}) !important;
    border-right: 1px solid {p['border']} !important;
}}
[data-testid="stSidebar"] > div:first-child {{ background: transparent !important; }}
[data-testid="stSidebar"] * {{ color: {p['text']}; }}
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {{ color: {p['dim']} !important; }}
[data-testid="stSidebar"] .stButton > button {{
    background: {p['surface_hi']} !important;
    border: 1px solid {p['border_hi']} !important; color: {p['text']} !important;
    border-radius: 9px !important;
}}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {{
    background: linear-gradient(180deg, {p['accent']}, {p['accent_dim']}) !important;
    color: #fff !important; border: none !important;
}}

/* ============ 滚动条 ============ */
::-webkit-scrollbar {{ width: 9px; height: 9px; }}
::-webkit-scrollbar-thumb {{ background: {p['border_hi']}; border-radius: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}

/* ============ caption / 小字 ============ */
.stCaption, [data-testid="stCaptionContainer"] p, .stMarkdown small {{
    color: {p['dim']} !important;
}}

/* ============ 提示框 ============ */
[data-testid="stAlert"] {{ border-radius: 12px; border: 1px solid {p['border']}; }}

/* ============ 高级 HTML 卡片工具类 ============ */
/* 品牌区（登录页左栏） */
.brand {{
    padding: 2.4rem 2rem; height: 100%;
    display: flex; flex-direction: column; justify-content: center;
}}
.brand-mark {{ font-size: .78rem; letter-spacing: .18em; text-transform: uppercase;
    color: {p['accent']}; font-weight: 700; }}
.brand-title {{ font-size: 2.6rem; font-weight: 800; color: {p['text']};
    letter-spacing: -0.03em; line-height: 1.1; margin: .6rem 0 .8rem; }}
.brand-sub {{ color: {p['dim']}; font-size: 1.05rem; line-height: 1.6; }}
.brand-rule {{ width: 3rem; height: 3px; background: {p['accent']};
    border-radius: 2px; margin: 1.4rem 0; }}
.brand-feat {{ color: {p['dim']}; font-size: .95rem; margin: .35rem 0; }}
.brand-feat b {{ color: {p['text']}; font-weight: 650; }}

/* 顶栏品牌 logo */
.topbar-brand {{ display: flex; align-items: center; gap: .55rem; }}
.topbar-brand .tb-mark {{
    width: 30px; height: 30px; border-radius: 8px; flex: none;
    background: linear-gradient(180deg, {p['accent']}, {p['accent_dim']});
    display: flex; align-items: center; justify-content: center;
    color: #fff; font-weight: 800; font-size: .82rem;
    letter-spacing: -0.02em; box-shadow: 0 1px 3px rgba(0,0,0,.2);
}}
.topbar-brand .tb-name {{ font-weight: 800; font-size: 1.2rem; color: {p['text']};
    letter-spacing: -0.02em; }}
.topbar-brand .tb-sub {{ font-size: .7rem; color: {p['faint']};
    letter-spacing: .06em; margin-top: -2px; }}

/* 页面 hero 标题区 */
.hero {{ padding: .2rem .1rem .6rem; }}
.hero-chip {{
    display: inline-block; font-size: .72rem; letter-spacing: .12em;
    text-transform: uppercase; color: {p['accent']};
    background: {p['accent_soft']}; border: 1px solid {p['accent_line']};
    border-radius: 999px; padding: .18rem .7rem; margin-bottom: .6rem; font-weight: 700;
}}
.hero-title {{ font-size: 1.85rem; font-weight: 800; color: {p['text']};
    letter-spacing: -0.02em; }}
.hero-sub {{ color: {p['dim']}; margin-top: .35rem; font-size: 1rem; }}

/* 统计卡片 */
.stat-card {{
    background: linear-gradient(180deg, {p['surface_hi']}, {p['surface']});
    border: 1px solid {p['border']}; border-radius: 12px;
    padding: 1rem 1.15rem; min-height: 98px;
}}
.stat-label {{ color: {p['dim']}; font-size: .78rem; letter-spacing: .04em; }}
.stat-value {{ color: {p['text']}; font-size: 1.75rem; font-weight: 760;
    margin: .2rem 0 .05rem; letter-spacing: -0.02em; }}
.stat-hint {{ color: {p['faint']}; font-size: .74rem; }}

/* 区块标题 */
.sec-title {{
    font-size: 1.12rem; font-weight: 720; color: {p['text']};
    padding-left: .65rem; border-left: 3px solid {p['accent']};
    margin: .8rem 0 .6rem; letter-spacing: -0.01em;
}}

/* 题目卡片（列表选择） */
.pb-card {{
    background: {p['surface']}; border: 1px solid {p['border']};
    border-radius: 12px; padding: .95rem 1.1rem; margin-bottom: .55rem;
    transition: all .15s ease; cursor: pointer;
}}
.pb-card:hover {{ border-color: {p['accent_line']}; }}
.pb-id {{ font-family: "JetBrains Mono", Consolas, monospace; color: {p['faint']};
    font-size: .78rem; letter-spacing: .04em; }}
.pb-title {{ color: {p['text']}; font-weight: 700; font-size: 1.05rem; margin: .15rem 0 .4rem; }}
.pb-meta {{ display: flex; gap: .4rem; flex-wrap: wrap; align-items: center; }}

/* 难度徽章 */
.diff {{ display: inline-block; border-radius: 999px; padding: .1rem .65rem;
    font-size: .74rem; font-weight: 650; background: {p['neu_soft']}; color: {p['dim']}; }}
.diff-0 {{ color: {p['ok']}; background: {p['ok_soft']}; }}
.diff-1 {{ color: {p['info']}; background: {p['info_soft']}; }}
.diff-2 {{ color: {p['accent']}; background: {p['accent_soft']}; }}
.diff-3 {{ color: {p['err']}; background: {p['err_soft']}; }}

/* 标签 chip */
.chip {{
    display: inline-block; border-radius: 6px; padding: .08rem .5rem; font-size: .74rem;
    background: {p['surface_hi']}; color: {p['dim']}; border: 1px solid {p['border']};
}}

/* 状态徽章 */
.badge {{ display: inline-block; border-radius: 999px; padding: .1rem .6rem;
    font-size: .76rem; font-weight: 650; }}
.badge-ok {{ background: {p['ok_soft']}; color: {p['ok']}; }}
.badge-err {{ background: {p['err_soft']}; color: {p['err']}; }}
.badge-warn {{ background: {p['warn_soft']}; color: {p['warn']}; }}
.badge-info {{ background: {p['info_soft']}; color: {p['info']}; }}
.badge-neu {{ background: {p['neu_soft']}; color: {p['dim']}; }}

/* 自定义代码块（样例输入/输出） */
.code-block {{
    background: {p['code_bg']}; border: 1px solid {p['border']};
    border-radius: 10px; margin: .5rem 0; overflow: hidden;
}}
.code-block-head {{
    display: flex; align-items: center; gap: .5rem;
    padding: .4rem .8rem; border-bottom: 1px solid {p['border']};
    background: {p['surface']};
}}
.code-block-label {{ font-size: .72rem; letter-spacing: .08em; text-transform: uppercase;
    color: {p['accent']}; font-weight: 700; }}
.code-block pre {{
    margin: 0; padding: .7rem .9rem; background: transparent !important;
    border: none !important; color: {p['text']} !important;
    font-family: "JetBrains Mono", Consolas, Menlo, monospace !important;
    font-size: .86rem; line-height: 1.55; overflow-x: auto;
    white-space: pre;
}}
.code-block code {{ color: {p['text']} !important; background: transparent !important; }}

/* 字体 */
.stApp, .stApp * {{
    font-family: "Inter", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei",
                 "Segoe UI", sans-serif;
}}
code, pre, .stCodeBlock, .code-block pre {{
    font-family: "JetBrains Mono", "SFMono-Regular", Consolas, Menlo, monospace !important;
}}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


# ============================ 卡片工具函数 ============================
def topbar_brand(name: str, mark: str = "OJ", sub: str = "") -> None:
    """顶栏品牌 logo。"""
    sub_html = f'<div class="tb-sub">{html.escape(sub)}</div>' if sub else ""
    st.markdown(
        f'<div class="topbar-brand">'
        f'<div class="tb-mark">{html.escape(mark)}</div>'
        f'<div><div class="tb-name">{html.escape(name)}</div>{sub_html}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str = "", chip: str = "") -> None:
    chip_html = f'<span class="hero-chip">{html.escape(chip)}</span>' if chip else ""
    st.markdown(
        f'<div class="hero">{chip_html}'
        f'<div class="hero-title">{html.escape(title)}</div>'
        f'<div class="hero-sub">{html.escape(subtitle)}</div></div>',
        unsafe_allow_html=True,
    )


def brand_panel(title: str, sub: str, feats: list) -> None:
    """登录页左侧品牌区（左右分栏的左栏）。"""
    feats_html = "".join(
        f'<div class="brand-feat">— {html.escape(f)}</div>' for f in feats
    )
    st.markdown(
        f'<div class="brand">'
        f'<div class="brand-mark">Online Judge</div>'
        f'<div class="brand-title">{html.escape(title)}</div>'
        f'<div class="brand-sub">{html.escape(sub)}</div>'
        f'<div class="brand-rule"></div>'
        f'{feats_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def stat_cards(items: list) -> None:
    n = max(len(items), 1)
    cols = st.columns(n)
    for i, col in enumerate(cols):
        it = items[i] if i < len(items) else {"label": "", "value": "", "hint": ""}
        with col:
            st.markdown(
                f'<div class="stat-card">'
                f'<div class="stat-label">{html.escape(str(it.get("label", "")))}</div>'
                f'<div class="stat-value">{html.escape(str(it.get("value", "")))}</div>'
                f'<div class="stat-hint">{html.escape(str(it.get("hint", "")))}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def section(title: str) -> None:
    st.markdown(f'<div class="sec-title">{html.escape(title)}</div>', unsafe_allow_html=True)


def difficulty(d) -> None:
    d = (d or "").strip()
    if not d:
        return
    low = d.lower()
    lvl = (3 if any(x in low for x in ["困难", "hard", "高级", "advanced", "较难"]) else
           2 if any(x in low for x in ["中等", "medium"]) else
           1 if any(x in low for x in ["入门", "简单", "easy", "beginner"]) else 0)
    st.markdown(f'<span class="diff diff-{lvl}">{html.escape(d)}</span>', unsafe_allow_html=True)


def chip(text: str) -> str:
    return f'<span class="chip">{html.escape(text)}</span>'


_STATUS = {
    "ac": "ok", "success": "ok", "completed": "ok", "passed": "ok",
    "wa": "err", "error": "err", "ce": "err", "re": "err", "failed": "err",
    "tle": "warn", "mle": "warn", "pending": "neu", "queued": "neu",
    "running": "info", "cancelled": "neu",
}


def status_badge(s) -> str:
    k = str(s or "").lower()
    return f'<span class="badge badge-{_STATUS.get(k, "info")}">{html.escape(str(s))}</span>'


def code_block(label: str, code: str) -> None:
    """渲染一个带「输入 / 输出」标签的样例代码块（浅底深字，克制美观）。"""
    st.markdown(
        f'<div class="code-block">'
        f'<div class="code-block-head"><span class="code-block-label">{html.escape(label)}</span></div>'
        f'<pre><code>{html.escape(str(code))}</code></pre>'
        f'</div>',
        unsafe_allow_html=True,
    )
