"""OJ 前端主入口（单页 + 顶栏导航）。

登录后：侧边栏只放语言切换 / 当前用户 / 登出；主区顶部用横向 radio 做导航
（题目 / 做题 / 我的 / AI），选中项决定渲染哪个视图。所有文案走 i18n。
"""

import streamlit as st

import api_client
import i18n
import views

st.set_page_config(page_title=i18n.t("app.title"), layout="wide")

# 侧边栏：语言切换
i18n.render_lang_selector()


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


def main():
    if not api_client.is_logged_in():
        _auth_screen()
        return

    user = api_client.current_user()
    role = user["role"]

    # ---- 侧边栏：当前用户 + 登出 ----
    with st.sidebar:
        st.caption(i18n.t("sidebar.user"))
        st.markdown(f"**{user['username']}** 　`{role}`")
        if st.button(i18n.t("logout"), use_container_width=True):
            api_client.logout()
            st.rerun()

    # ---- 顶栏导航（按角色过滤） ----
    all_views = ["problems", "solve", "profile"]
    if role == "admin":
        all_views = ["problems", "solve", "ai", "profile"]
    labels = {
        "problems": i18n.t("nav.problems"),
        "solve": i18n.t("nav.solve"),
        "ai": i18n.t("nav.ai"),
        "profile": i18n.t("nav.profile"),
    }
    # 首次进入默认"题目"；后续以 st.radio 的 widget 状态(main_nav)为准，
    # "去做题"等内部跳转通过写 session_state["main_nav"] 实现。
    if "main_nav" not in st.session_state:
        st.session_state["main_nav"] = "problems"
    chosen = st.radio(
        "nav", all_views, horizontal=True,
        format_func=lambda v: labels[v], label_visibility="collapsed",
        index=all_views.index(st.session_state["main_nav"]), key="main_nav",
    )
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
