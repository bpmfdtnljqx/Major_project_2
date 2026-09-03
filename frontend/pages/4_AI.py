"""AI 智能命题页面（仅管理员 / 教师助教可见）。"""

import streamlit as st

import api_client

st.set_page_config(page_title="AI 命题")

st.title("AI 智能命题")

if not api_client.is_logged_in():
    st.warning("请先登录")
    st.stop()

if api_client.current_user()["role"] != "admin":
    st.error("该功能仅教师 / 助教（管理员）可用")
    st.stop()

# 提交成功提示
if "ai_msg" in st.session_state:
    st.success(st.session_state["ai_msg"])
    del st.session_state["ai_msg"]

# ---- 生成新题目 ----
st.subheader("生成新题目")
with st.form("ai_task"):
    requirement = st.text_area(
        "命题需求",
        placeholder="例如：生成一道求两个整数最大公约数的题，难度入门，含 3 个测试点",
    )
    if st.form_submit_button("生成题目"):
        if not requirement.strip():
            st.error("需求不能为空")
        else:
            s, b = api_client.request(
                "POST", "/api/ai/problem-tasks/", json_body={"requirement": requirement}
            )
            if s == 200:
                st.session_state["ai_task_id"] = b["data"]["task_id"]
                st.session_state["ai_msg"] = "任务已创建，正在生成……"
                st.rerun()
            else:
                st.error(b.get("msg", "创建失败"))

# ---- 任务状态与结果 ----
if "ai_task_id" in st.session_state:
    st.divider()
    st.subheader("任务状态")
    task_id = st.session_state["ai_task_id"]
    s, b = api_client.request("GET", f"/api/ai/problem-tasks/{task_id}")
    if s == 200:
        d = b["data"]
        st.write(f"任务：{d['task_id'][:12]}")
        st.write(f"状态：{d['status']}")
        if d.get("progress"):
            st.write(f"进度：{d['progress']}")
        if d.get("usage"):
            u = d["usage"]
            st.caption(
                f"Token 用量：输入 {u['input_tokens']} / 输出 {u['output_tokens']} / 总计 {u['total_tokens']}，"
                f"费用 {u['cost']} {u['currency']}"
            )
        if d.get("result"):
            st.write("生成的题目（已自动加入题库）：")
            st.json(d["result"])
        col1, col2 = st.columns(2)
        with col1:
            if st.button("刷新状态"):
                st.rerun()
        with col2:
            if st.button("清除此任务"):
                st.session_state.pop("ai_task_id", None)
                st.rerun()
    else:
        st.error(b.get("msg", "查询任务失败"))

st.divider()
st.info("生成的题目会自动加入「题目」页面的题库，可直接用于评测。")
