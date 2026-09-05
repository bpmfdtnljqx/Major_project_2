"""用户页面组：当前用户信息展示 + 用户管理（管理员）。"""

import streamlit as st

import api_client
import i18n

st.set_page_config(page_title=i18n.t("user.title"))

i18n.render_lang_selector()

st.title(i18n.t("user.title"))

if not api_client.is_logged_in():
    # 跨页面消息（如重置完成）在登录态失效后展示
    if "global_msg" in st.session_state:
        st.success(st.session_state["global_msg"])
        del st.session_state["global_msg"]
    st.warning(i18n.t("login_required"))
    st.stop()

user = api_client.current_user()

# ---- 我的信息 ----
st.subheader(i18n.t("user.my_info"))
status, body = api_client.request("GET", f"/api/users/{user['user_id']}")
if status == 200:
    info = body["data"]
    st.write(f"{i18n.t('username')}：{info['username']}")
    role_txt = {"admin": i18n.t("admin"), "user": "user", "banned": "banned"}.get(info["role"], info["role"])
    st.write(f"{i18n.t('user.role')}：{role_txt}")
    st.write(f"{i18n.t('user.join_time')}：{info['join_time']}")
    st.write(
        f"{i18n.t('user.submits', n=info['submit_count'])}　"
        f"{i18n.t('user.resolved', n=info['resolve_count'])}"
    )
else:
    st.error(body.get("msg", i18n.t("error_occurred")))

# ---- 用户管理（仅管理员） ----
if user["role"] == "admin":
    st.divider()
    st.subheader(i18n.t("user.manage"))

    status, body = api_client.request("GET", "/api/users/")
    if status == 200:
        data = body["data"]
        st.write(i18n.t("user.total", n=data["total"]))
        roles = ["admin", "user", "banned"]
        for u in data["users"]:
            with st.expander(f"{u['username']}（{u['role']}）"):
                st.write(f"user_id：{u['user_id']}")
                st.write(f"{i18n.t('user.join_time')}：{u['join_time']}")
                st.write(
                    f"{i18n.t('user.submits', n=u['submit_count'])}　"
                    f"{i18n.t('user.resolved', n=u['resolve_count'])}"
                )
                col1, col2 = st.columns([2, 1])
                with col1:
                    new_role = st.selectbox(
                        i18n.t("user.role"), roles,
                        index=roles.index(u["role"]), key=f"role_{u['user_id']}",
                    )
                with col2:
                    if st.button(i18n.t("user.update_role"), key=f"btn_{u['user_id']}"):
                        s2, b2 = api_client.request(
                            "PUT", f"/api/users/{u['user_id']}/role", json_body={"role": new_role}
                        )
                        if s2 == 200:
                            st.success(i18n.t("user.role_updated"))
                            st.rerun()
                        else:
                            st.error(b2.get("msg", i18n.t("error_occurred")))
    else:
        st.error(body.get("msg", i18n.t("error_occurred")))

    st.divider()
    st.subheader(i18n.t("user.create_admin"))
    with st.form("create_admin"):
        username = st.text_input(i18n.t("username"))
        password = st.text_input(i18n.t("password"), type="password")
        if st.form_submit_button(i18n.t("user.create_btn")):
            s2, b2 = api_client.request(
                "POST", "/api/users/admin", json_body={"username": username, "password": password}
            )
            if s2 == 200:
                st.success(i18n.t("user.create_ok"))
            else:
                st.error(b2.get("msg", i18n.t("error_occurred")))

    # ---- 系统重置（仅管理员，带二次确认） ----
    st.divider()
    st.subheader(i18n.t("user.system_reset"))
    st.caption(i18n.t("user.reset_hint"))
    reset_label = st.session_state.get("confirm_reset") and i18n.t("user.reset_confirm_btn") or i18n.t("user.reset_btn")
    if st.button(reset_label):
        # 二次确认：首次点击显示确认，再次点击真正执行
        if not st.session_state.get("confirm_reset"):
            st.session_state["confirm_reset"] = True
            st.rerun()
        else:
            s, b = api_client.request("POST", "/api/reset/")
            if s == 200:
                # 后端已清空会话，前端退出登录态并回到登录页提示
                api_client.logout()
                st.session_state.pop("confirm_reset", None)
                st.session_state["global_msg"] = i18n.t("user.reset_done")
                st.rerun()
            else:
                st.error(b.get("msg", i18n.t("error_occurred")))
                st.session_state.pop("confirm_reset", None)
