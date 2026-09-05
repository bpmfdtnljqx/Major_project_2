"""用户页面组：当前用户信息展示 + 用户管理（管理员）。"""

import streamlit as st

import api_client

st.set_page_config(page_title="用户")

st.title("用户")

if not api_client.is_logged_in():
    if "global_msg" in st.session_state:
        st.success(st.session_state["global_msg"])
        del st.session_state["global_msg"]
    st.warning("请先登录")
    st.stop()

user = api_client.current_user()

# ---- 我的信息 ----
st.subheader("我的信息")
status, body = api_client.request("GET", f"/api/users/{user['user_id']}")
if status == 200:
    info = body["data"]
    st.write(f"用户名：{info['username']}")
    st.write(f"角色：{info['role']}")
    st.write(f"注册时间：{info['join_time']}")
    st.write(f"提交数：{info['submit_count']}　通过题数：{info['resolve_count']}")
else:
    st.error(body.get("msg", "获取用户信息失败"))

# ---- 用户管理（仅管理员） ----
if user["role"] == "admin":
    st.divider()
    st.subheader("用户管理")

    status, body = api_client.request("GET", "/api/users/")
    if status == 200:
        data = body["data"]
        st.write(f"共 {data['total']} 个用户")
        roles = ["admin", "user", "banned"]
        for u in data["users"]:
            with st.expander(f"{u['username']}（{u['role']}）"):
                st.write(f"user_id：{u['user_id']}")
                st.write(f"注册时间：{u['join_time']}")
                st.write(f"提交数：{u['submit_count']}　通过题数：{u['resolve_count']}")
                col1, col2 = st.columns([2, 1])
                with col1:
                    new_role = st.selectbox(
                        "角色", roles, index=roles.index(u["role"]), key=f"role_{u['user_id']}"
                    )
                with col2:
                    if st.button("更新角色", key=f"btn_{u['user_id']}"):
                        s2, b2 = api_client.request(
                            "PUT", f"/api/users/{u['user_id']}/role", json_body={"role": new_role}
                        )
                        if s2 == 200:
                            st.success("已更新")
                            st.rerun()
                        else:
                            st.error(b2.get("msg", "更新失败"))
    else:
        st.error(body.get("msg", "获取用户列表失败"))

    st.divider()
    st.subheader("创建管理员")
    with st.form("create_admin"):
        username = st.text_input("用户名")
        password = st.text_input("密码", type="password")
        if st.form_submit_button("创建"):
            s2, b2 = api_client.request(
                "POST", "/api/users/admin", json_body={"username": username, "password": password}
            )
            if s2 == 200:
                st.success("创建成功")
            else:
                st.error(b2.get("msg", "创建失败"))

    # ---- 系统重置（仅管理员，带二次确认） ----
    st.divider()
    st.subheader("系统重置")
    st.caption("清空所有用户 / 题目 / 提交 / 日志数据，恢复种子题目，重建初始管理员账户，并退出当前登录。此操作不可恢复！")
    if st.button("一键重置系统"):
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
                st.session_state["global_msg"] = "系统已重置，请用初始管理员账户（admin / admintestpassword）重新登录。"
                st.rerun()
            else:
                st.error(b.get("msg", "重置失败"))
                st.session_state.pop("confirm_reset", None)
