"""OJ 前端主入口：登录 / 注册。

Streamlit 多页应用：其余功能页面位于 pages/ 目录。
"""

import streamlit as st

import api_client

st.set_page_config(page_title="OJ 在线评测系统")

st.title("在线评测系统")

if api_client.is_logged_in():
    user = api_client.current_user()
    st.success(f"已登录：{user['username']}（{user['role']}）")
    if st.button("登出"):
        api_client.logout()
        st.rerun()
    st.info("请在左侧导航选择「用户」「题目」或「评测提交」页面进行操作。")
else:
    tab_login, tab_register = st.tabs(["登录", "注册"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            if st.form_submit_button("登录"):
                status, body = api_client.login(username, password)
                if status == 200:
                    st.success("登录成功")
                    st.rerun()
                else:
                    st.error(body.get("msg", "登录失败"))

    with tab_register:
        with st.form("register_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            if st.form_submit_button("注册"):
                status, body = api_client.request(
                    "POST", "/api/users/", json_body={"username": username, "password": password}
                )
                if status == 200:
                    st.success("注册成功，请切换到「登录」标签页登录")
                else:
                    st.error(body.get("msg", "注册失败"))
