"""OJ 前端主入口：登录 / 注册。

Streamlit 多页应用：其余功能页面位于 pages/ 目录。
"""

import streamlit as st

import api_client
import i18n

st.set_page_config(page_title=i18n.t("app.title"))

i18n.render_lang_selector()

st.title(i18n.t("app.title"))

if api_client.is_logged_in():
    user = api_client.current_user()
    st.success(i18n.t("auth.logged_in_as", name=user["username"], role=user["role"]))
    if st.button(i18n.t("logout")):
        api_client.logout()
        st.rerun()
    st.info(i18n.t("not_logged_tip"))
else:
    # 显示一次跨页面携带的消息（如系统重置完成提示），然后清除
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
                    st.success(i18n.t("auth.login_ok"))
                    st.rerun()
                else:
                    # 账号被封禁时给醒目提示，与普通密码错误区分
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
