"""评测提交页面：题目做题（题面 + 代码编辑器 + 提交）+ 我的提交记录。

布局参考经典 OJ（题面在左，编辑器/提交在右）：
- 顶部：题目选择（可被"题目"页的"去做题"自动带过来）
- 左侧：题目详情（描述/输入输出/样例/限制/标签）
- 右侧：代码编辑器（Ace，支持 Tab 缩进/高亮）+ 语言选择 + 提交按钮
- 下方：我的提交记录（含评测状态 / 编译运行信息 / 测试点明细）
"""

import streamlit as st
from streamlit_ace import st_ace

import api_client

st.set_page_config(page_title="评测提交", layout="wide")

st.title("做题")

if not api_client.is_logged_in():
    st.warning("请先登录")
    st.stop()

user = api_client.current_user()

# 若从"题目"页跳转而来，自动选中对应题目（一次性）
default_problem = st.session_state.pop("pending_problem", None)

# ---- 拉取题目与语言 ----
status, body = api_client.request("GET", "/api/problems/")
problems = body["data"] if status == 200 else []
status, body = api_client.request("GET", "/api/languages/")
languages = body["data"]["name"] if status == 200 else []

if not problems:
    st.warning("暂无题目可提交")
    st.stop()

ids = [p["id"] for p in problems]
idx = ids.index(default_problem) if default_problem in ids else 0
problem_id = st.selectbox(
    "选择题目", ids, index=idx,
    format_func=lambda pid: next((p["title"] for p in problems if p["id"] == pid), pid),
    key="sub_problem",
)

# 取题目详情
detail = {}
s, b = api_client.request("GET", f"/api/problems/{problem_id}")
if s == 200:
    detail = b["data"]

# ---- 布局：左题面 + 右编辑器 ----
left, right = st.columns([5, 4], gap="large")

with left:
    st.subheader(f"{detail.get('id', problem_id)} · {detail.get('title', '')}")
    st.markdown("**题目描述**")
    st.markdown(detail.get("description", "（无）"))
    st.markdown("**输入格式**")
    st.markdown(detail.get("input_description", ""))
    st.markdown("**输出格式**")
    st.markdown(detail.get("output_description", ""))
    if detail.get("samples"):
        st.markdown("**样例**")
        for smp in detail["samples"]:
            st.code(f"输入：\n{smp.get('input', '')}\n\n输出：\n{smp.get('output', '')}")
    if detail.get("constraints"):
        st.markdown(f"**数据范围**：{detail['constraints']}")
    st.caption(f"时间限制 {detail.get('time_limit', 3)}s ／ 内存限制 {detail.get('memory_limit', 128)}MB")
    if detail.get("tags"):
        st.caption(f"标签：{'、'.join(detail['tags'])}")

with right:
    st.subheader("提交代码")
    if not languages:
        st.warning("无可用语言")
    else:
        language = st.selectbox("语言", languages, key="sub_lang")
        # 语言 → Ace 高亮模式
        ace_mode = {"python": "python", "cpp": "c_cpp"}.get(language, "plain_text")
        # 代码编辑器（Ace，支持 Tab 缩进与语法高亮；auto_update=False 避免逐键闪烁）
        code = st_ace(
            value=st.session_state.get(f"draft_{problem_id}", ""),
            language=ace_mode,
            theme="monokai",
            keybinding="vscode",
            font_size=14,
            tab_size=4,
            min_lines=12,
            auto_update=False,
            key=f"ace_{problem_id}",
        )

        if st.button("提交评测", type="primary"):
            if not code.strip():
                st.error("代码不能为空")
            else:
                # 保留草稿，便于重提交
                st.session_state[f"draft_{problem_id}"] = code
                s2, b2 = api_client.request(
                    "POST", "/api/submissions/",
                    json_body={"problem_id": problem_id, "language": language, "code": code},
                )
                if s2 == 200:
                    st.session_state["submit_msg"] = (
                        f"已提交，submission_id：{b2['data']['submission_id']}，可查看下方记录"
                    )
                    st.rerun()
                elif s2 == 429:
                    st.error("提交过于频繁，请稍后再试（1 分钟内最多 3 次）")
                else:
                    st.error(b2.get("msg", "提交失败"))

# ---- 提交成功提示 ----
if "submit_msg" in st.session_state:
    st.success(st.session_state["submit_msg"])
    del st.session_state["submit_msg"]

# ---- 我的提交记录 ----
st.divider()
st.subheader("我的提交记录")

status, body = api_client.request("GET", "/api/submissions/", params={"user_id": user["user_id"]})
if status != 200:
    st.error(body.get("msg", "获取提交记录失败"))
else:
    subs = body["data"]["submissions"]
    if not subs:
        st.info("暂无提交记录，去上面选一道题开始吧")
    else:
        st.write(f"共 {body['data']['total']} 条提交")

        # 概览表格
        rows = []
        for s in subs[:50]:
            t = next((p["title"] for p in problems if p["id"] == s.get("problem_id")), s.get("problem_id"))
            rows.append({
                "submission_id": s["submission_id"][:10],
                "题目": t,
                "状态": s.get("status", "-"),
                "得分": s.get("score", "-"),
                "总分": s.get("counts", "-"),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

        # 选中一条查看详细
        sub_ids = [s["submission_id"] for s in subs]
        sel_short = st.selectbox("选择提交查看详情", [x[:10] for x in sub_ids], key="sub_select")
        sel_id = next(s for s in sub_ids if s.startswith(sel_short))

        s2, b2 = api_client.request("GET", f"/api/submissions/{sel_id}")
        if s2 == 200:
            d = b2["data"]
            c1, c2, c3 = st.columns(3)
            c1.metric("状态", d["status"])
            c2.metric("得分", d["score"] if d["score"] is not None else "-")
            c3.metric("总分", d["counts"] if d["counts"] is not None else "-")
            if d.get("compile_info"):
                st.info(f"编译结果：{d['compile_info'].get('result')}　{d['compile_info'].get('message', '')}")
            if d.get("run_info"):
                st.info(f"运行结果：{d['run_info'].get('result')}　{d['run_info'].get('message', '')}")
            if d.get("error_info"):
                st.error(f"错误信息：{d['error_info']}")

            # 测试点明细（可见时展示）
            s3, b3 = api_client.request("GET", f"/api/submissions/{sel_id}/log")
            if s3 == 200 and b3["data"].get("details"):
                st.write("测试点明细：")
                det_rows = []
                for det in b3["data"]["details"]:
                    det_rows.append({
                        "#": det.get("id"),
                        "结果": det.get("result"),
                        "时间(s)": det.get("time"),
                        "内存(MB)": det.get("memory"),
                    })
                st.dataframe(det_rows, use_container_width=True, hide_index=True)

        if st.button("刷新状态"):
            st.rerun()
