"""OJ 前端主入口（单页 + 顶栏导航）。

登录前：左右分栏（左品牌区 + 右登录/注册卡片），右上角语言/主题切换。
登录后：顶栏（品牌 logo + st.pills 导航 + 语言/主题切换），侧边栏只留用户卡与登出。
所有文案走 i18n；权限判断全在后端，前端仅展示。
"""

import streamlit as st

import api_client
import i18n
import theme
import views

st.set_page_config(page_title=i18n.t("app.title"), layout="wide")

# 注入全局设计系统
theme.inject()


def _auth_screen() -> None:
    """未登录：左右分栏的登录 / 注册卡片。"""
    left, right = st.columns([11, 9], gap="large")

    with left:
        theme.brand_panel(
            title=i18n.t("app.title"),
            sub=i18n.t("auth.brand_sub"),
            feats=[
                i18n.t("auth.brand_feat_1"),
                i18n.t("auth.brand_feat_2"),
                i18n.t("auth.brand_feat_3"),
                i18n.t("auth.brand_feat_4"),
            ],
        )

    with right:
        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
        if "global_msg" in st.session_state:
            st.success(st.session_state["global_msg"])
            del st.session_state["global_msg"]

        tab_login, tab_register = st.tabs(
            [i18n.t("auth.tab_login"), i18n.t("auth.tab_register")]
        )
        with tab_login:
            with st.form("login_form"):
                username = st.text_input(i18n.t("username"))
                password = st.text_input(i18n.t("password"), type="password")
                if st.form_submit_button(i18n.t("auth.login_btn"), type="primary",
                                         use_container_width=True):
                    status, body = api_client.login(username, password)
                    if status == 200:
                        st.rerun()
                    else:
                        msg = body.get("msg", "")
                        if status == 403 and ("banned" in str(msg).lower() or "禁用" in str(msg)):
                            st.error(i18n.t("auth.banned"), icon="🚫")
                        else:
                            st.error(body.get("msg", i18n.t("auth.login_fail")))
        with tab_register:
            with st.form("register_form"):
                username = st.text_input(i18n.t("username"))
                password = st.text_input(i18n.t("password"), type="password")
                if st.form_submit_button(i18n.t("auth.register_btn"), type="primary",
                                         use_container_width=True):
                    status, body = api_client.request(
                        "POST", "/api/users/",
                        json_body={"username": username, "password": password},
                    )
                    if status == 200:
                        st.success(i18n.t("auth.register_ok"))
                    else:
                        st.error(body.get("msg", i18n.t("auth.register_fail")))


def _prelogin_toolbar() -> None:
    """登录页右上角：语言切换 + 主题切换。"""
    c_lang, c_theme = st.columns([1, 1], gap="small")
    with c_lang:
        i18n.render_lang_bar()
    with c_theme:
        st.button(theme.mode_label(), key="theme_toggle_prelogin",
                  on_click=theme.toggle, use_container_width=True)


def _toggle_theme() -> None:
    """切换主题 on_click 回调（不显式 rerun，靠 session_state 变更自动 rerun）。"""
    theme.toggle()


def main() -> None:
    if not api_client.is_logged_in():
        # 未登录：右上角语言/主题 + 左右分栏登录卡片
        _, tools = st.columns([7, 3])
        with tools:
            _prelogin_toolbar()
        st.divider()
        _auth_screen()
        return

    user = api_client.current_user()
    role = user["role"]

    # ---- 侧边栏：用户卡 + 登出（精简，主题/语言都移到顶栏） ----
    with st.sidebar:
        st.caption(i18n.t("sidebar.user"))
        st.markdown(f"**{user['username']}**")
        st.markdown(
            f"<span class='badge badge-{'info' if role == 'admin' else 'neu'}'>"
            f"{i18n.t('admin') if role == 'admin' else 'user'}</span>",
            unsafe_allow_html=True,
        )
        st.divider()
        if st.button(i18n.t("logout"), use_container_width=True):
            api_client.logout()
            st.rerun()

    # ---- 顶栏：品牌 + 语言/主题 ----
    all_views = ["problems", "solve", "profile"]
    if role == "admin":
        all_views = ["problems", "solve", "ai", "profile"]
    labels = {
        "problems": i18n.t("nav.problems"),
        "solve": i18n.t("nav.solve"),
        "ai": i18n.t("nav.ai"),
        "profile": i18n.t("nav.profile"),
    }

    col_brand, col_tools = st.columns([7, 3])
    with col_brand:
        theme.topbar_brand(i18n.t("app.title"), mark="OJ", sub="Online Judge")
    with col_tools:
        c_lang, c_theme = st.columns([1, 1], gap="small")
        with c_lang:
            i18n.render_lang_bar()
        with c_theme:
            st.button(theme.mode_label(), key="theme_toggle",
                      on_click=_toggle_theme, use_container_width=True)

    st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)

    # ---- 导航（st.pills 原生，无 radio 圆点） ----
    if "main_nav" not in st.session_state or st.session_state["main_nav"] not in all_views:
        st.session_state["main_nav"] = all_views[0]

    # 注意：key 已绑定 session_state["main_nav"]，不要再传 default，否则
    # Streamlit 会报「default 与 Session State API 同时设置」冲突。
    chosen = st.pills(
        "nav", all_views,
        format_func=lambda v: labels[v],
        label_visibility="collapsed", key="main_nav",
    )
    if chosen is None:
        chosen = all_views[0]
    st.divider()

    # ---- 分发 ----
    if chosen == "problems":
        views.render_problems()
    elif chosen == "solve":
        views.render_solve()
    elif chosen == "ai":
        views.render_ai()
    elif chosen == "profile":
        views.render_profile()


main()
