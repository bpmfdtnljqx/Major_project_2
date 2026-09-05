"""OJ 前端主入口（单页 + 顶栏导航）。

登录后主区顶部为横向导航（题目 / 做题 / AI / 我的），语言切换也放在顶部（右上角）。
侧边栏仅保留当前用户与登出。所有文案走 i18n。
"""

import streamlit as st

import api_client
import i18n
import theme
import views

st.set_page_config(page_title=i18n.t("app.title"), layout="wide")

# 注入全局高级感主题
theme.inject()


def _auth_screen():
    """未登录时显示登录 / 注册。"""
    st.title(i18n.t("app.title"))
    if "global_msg" in st.session_state:
        st.success(st.session_state["global_msg"])
        del st.session_state["global_msg"]
    tab_login, tab_register = st.tabs([i18n.t("auth.tab_login"), i18n.t("auth.tab_register")])
    with tab_login:
        with st.form("login_form"):
            username = st.text_input(i18n.t("username"))
            password = st.text_input(i18n.t("password"), type="password")
            if st.form_submit_button(i18n.t("auth.login_btn")):
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
            if st.form_submit_button(i18n.t("auth.register_btn")):
                status, body = api_client.request(
                    "POST", "/api/users/", json_body={"username": username, "password": password}
                )
                if status == 200:
                    st.success(i18n.t("auth.register_ok"))
                else:
                    st.error(body.get("msg", i18n.t("auth.register_fail")))


def _top_lang() -> None:
    """顶部右上角语言切换（未登录时单独一行）。"""
    i18n.render_lang_bar()


def main():
    if not api_client.is_logged_in():
        # 未登录：顶部语言切换 + 登录/注册
        _top_lang()
        _auth_screen()
        return

    user = api_client.current_user()
    role = user["role"]

    # ---- 侧边栏：仅当前用户 + 登出 ----
    with st.sidebar:
        st.caption(i18n.t("sidebar.user"))
        st.markdown(f"**{user['username']}** 　`{role}`")
        if st.button(i18n.t("logout"), use_container_width=True):
            api_client.logout()
            st.rerun()

    # ---- 顶栏导航（按角色过滤）+ 语言切换同行 ----
    all_views = ["problems", "solve", "profile"]
    if role == "admin":
        all_views = ["problems", "solve", "ai", "profile"]
    labels = {
        "problems": i18n.t("nav.problems"),
        "solve": i18n.t("nav.solve"),
        "ai": i18n.t("nav.ai"),
        "profile": i18n.t("nav.profile"),
    }
    if "main_nav" not in st.session_state:
        st.session_state["main_nav"] = "problems"
    if st.session_state["main_nav"] not in all_views:
        st.session_state["main_nav"] = all_views[0]

    col_nav, col_lang = st.columns([8, 2])
    with col_nav:
        chosen = st.radio(
            "nav", all_views, horizontal=True,
            format_func=lambda v: labels[v], label_visibility="collapsed",
            index=all_views.index(st.session_state["main_nav"]), key="main_nav",
        )
    with col_lang:
        i18n.render_lang_bar()
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
