"""评测提交页面组：代码提交 + 提交记录 + 评测状态。"""

import streamlit as st

import api_client

st.set_page_config(page_title="评测提交")

st.title("评测提交")

if not api_client.is_logged_in():
    st.warning("请先登录")
    st.stop()

user = api_client.current_user()

# 提交成功提示（rerun 后显示一次）
if "submit_msg" in st.session_state:
    st.success(st.session_state["submit_msg"])
    del st.session_state["submit_msg"]

# ---- 代码提交 ----
st.subheader("提交代码")

status, body = api_client.request("GET", "/api/problems/")
problems = body["data"] if status == 200 else []
status, body = api_client.request("GET", "/api/languages/")
languages = body["data"]["name"] if status == 200 else []

if not problems:
    st.warning("暂无题目可提交")
else:
    def _title_of(pid: str) -> str:
        for p in problems:
            if p["id"] == pid:
                return p["title"]
        return pid

    with st.form("submit_code"):
        problem_id = st.selectbox("题目", [p["id"] for p in problems], format_func=_title_of)
        language = st.selectbox("语言", languages)
        code = st.text_area("代码", height=220, placeholder="在此输入代码……")
        if st.form_submit_button("提交评测"):
            if not code.strip():
                st.error("代码不能为空")
            else:
                s, b = api_client.request(
                    "POST", "/api/submissions/",
                    json_body={"problem_id": problem_id, "language": language, "code": code},
                )
                if s == 200:
                    st.session_state["submit_msg"] = f"提交成功，submission_id：{b['data']['submission_id']}"
                    st.rerun()
                else:
                    st.error(b.get("msg", "提交失败"))

# ---- 我的提交记录 ----
st.divider()
st.subheader("我的提交记录")

status, body = api_client.request("GET", "/api/submissions/", params={"user_id": user["user_id"]})
if status != 200:
    st.error(body.get("msg", "获取提交记录失败"))
else:
    subs = body["data"]["submissions"]
    if not subs:
        st.info("暂无提交记录")
    else:
        st.write(f"共 {body['data']['total']} 条提交")
        sub_ids = [s["submission_id"] for s in subs]
        selected_sub = st.selectbox("选择提交记录", sub_ids, format_func=lambda x: x[:12])

        s2, b2 = api_client.request("GET", f"/api/submissions/{selected_sub}")
        if s2 == 200:
            d = b2["data"]
            col1, col2, col3 = st.columns(3)
            col1.metric("状态", d["status"])
            col2.metric("得分", d["score"] if d["score"] is not None else "-")
            col3.metric("总分", d["counts"] if d["counts"] is not None else "-")
            if d["compile_info"]:
                st.info(f"编译结果：{d['compile_info']['result']}　{d['compile_info']['message']}")
            if d["run_info"]:
                st.info(f"运行结果：{d['run_info']['result']}　{d['run_info']['message']}")
            if d["error_info"]:
                st.error(f"错误信息：{d['error_info']}")

            # 测试点明细（可见时展示）
            s3, b3 = api_client.request("GET", f"/api/submissions/{selected_sub}/log")
            if s3 == 200 and b3["data"].get("details"):
                st.write("测试点明细：")
                for det in b3["data"]["details"]:
                    st.write(f"　#{det['id']}　{det['result']}　时间 {det['time']}s　内存 {det['memory']}MB")

        if st.button("刷新状态"):
            st.rerun()
