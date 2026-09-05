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
import i18n

st.set_page_config(page_title=i18n.t("solve.title"), layout="wide")

i18n.render_lang_selector()

st.title(i18n.t("solve.title"))

if not api_client.is_logged_in():
    st.warning(i18n.t("login_required"))
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
    st.warning(i18n.t("problem.no_solve"))
    st.stop()

ids = [p["id"] for p in problems]
idx = ids.index(default_problem) if default_problem in ids else 0
problem_id = st.selectbox(
    i18n.t("solve.select_problem"), ids, index=idx,
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
    st.markdown(f"**{i18n.t('problem.desc')}**")
    st.markdown(detail.get("description", "（—）"))
    st.markdown(f"**{i18n.t('problem.input_desc')}**")
    st.markdown(detail.get("input_description", ""))
    st.markdown(f"**{i18n.t('problem.output_desc')}**")
    st.markdown(detail.get("output_description", ""))
    if detail.get("samples"):
        st.markdown(f"**{i18n.t('problem.samples')}**")
        for smp in detail["samples"]:
            st.code(
                f"{i18n.t('solve.input_label')}：\n{smp.get('input', '')}\n\n"
                f"{i18n.t('solve.output_label')}：\n{smp.get('output', '')}"
            )
    if detail.get("constraints"):
        st.markdown(f"**{i18n.t('problem.constraints')}**：{detail['constraints']}")
    st.caption(i18n.t("problem.limit", t=detail.get("time_limit", 3), m=detail.get("memory_limit", 128)))
    if detail.get("tags"):
        st.caption(f"{i18n.t('problem.tags')}：{'、'.join(detail['tags'])}")

with right:
    st.subheader(i18n.t("solve.submit_code"))
    if not languages:
        st.warning(i18n.t("solve.no_lang"))
    else:
        language = st.selectbox(i18n.t("solve.language"), languages, key="sub_lang")
        # 语言 → Ace 高亮模式
        ace_mode = {"python": "python", "cpp": "c_cpp"}.get(language, "plain_text")
        # 代码编辑器（Ace，支持 Tab 缩进与语法高亮）
        # auto_update=True：输入停止后自动同步，不显示 st_ace 自带的 "Apply" 按钮，
        # 页面上只有一个"提交评测"按钮；st_ace 内部 200ms 防抖，不会逐键刷新。
        code = st_ace(
            value=st.session_state.get(f"draft_{problem_id}", ""),
            language=ace_mode,
            theme="monokai",
            keybinding="vscode",
            font_size=14,
            tab_size=4,
            min_lines=12,
            auto_update=True,
            key=f"ace_{problem_id}",
        )

        if st.button(i18n.t("solve.submit_btn"), type="primary"):
            if not code.strip():
                st.error(i18n.t("solve.code_empty"))
            else:
                # 保留草稿，便于重提交
                st.session_state[f"draft_{problem_id}"] = code
                s2, b2 = api_client.request(
                    "POST", "/api/submissions/",
                    json_body={"problem_id": problem_id, "language": language, "code": code},
                )
                if s2 == 200:
                    st.session_state["submit_msg"] = i18n.t(
                        "solve.submitted", id=b2["data"]["submission_id"]
                    )
                    st.rerun()
                elif s2 == 429:
                    st.error(i18n.t("solve.rate_limit"))
                else:
                    st.error(b2.get("msg", i18n.t("error_occurred")))

# ---- 提交成功提示 ----
if "submit_msg" in st.session_state:
    st.success(st.session_state["submit_msg"])
    del st.session_state["submit_msg"]

# ---- 我的提交记录 ----
st.divider()
st.subheader(i18n.t("solve.my_records"))

status, body = api_client.request("GET", "/api/submissions/", params={"user_id": user["user_id"]})
if status != 200:
    st.error(body.get("msg", i18n.t("error_occurred")))
else:
    subs = body["data"]["submissions"]
    if not subs:
        st.info(i18n.t("solve.records_none"))
    else:
        st.write(i18n.t("solve.total", n=body["data"]["total"]))

        # 概览表格
        rows = []
        for s in subs[:50]:
            t = next((p["title"] for p in problems if p["id"] == s.get("problem_id")), s.get("problem_id"))
            rows.append({
                i18n.t("solve.col_id"): s["submission_id"][:10],
                i18n.t("solve.col_problem"): t,
                i18n.t("solve.col_status"): s.get("status", "-"),
                i18n.t("solve.col_score"): s.get("score", "-"),
                i18n.t("solve.col_total"): s.get("counts", "-"),
            })
        st.dataframe(rows, use_container_width=True, hide_index=True)

        # 选中一条查看详细
        sub_ids = [s["submission_id"] for s in subs]
        sel_short = st.selectbox(i18n.t("solve.select_sub"), [x[:10] for x in sub_ids], key="sub_select")
        sel_id = next(s for s in sub_ids if s.startswith(sel_short))

        s2, b2 = api_client.request("GET", f"/api/submissions/{sel_id}")
        if s2 == 200:
            d = b2["data"]
            c1, c2, c3 = st.columns(3)
            c1.metric(i18n.t("solve.col_status"), d["status"])
            c2.metric(i18n.t("solve.col_score"), d["score"] if d["score"] is not None else "-")
            c3.metric(i18n.t("solve.col_total"), d["counts"] if d["counts"] is not None else "-")
            if d.get("compile_info"):
                st.info(
                    f"{i18n.t('solve.compile')}：{d['compile_info'].get('result')}　"
                    f"{d['compile_info'].get('message', '')}"
                )
            if d.get("run_info"):
                st.info(
                    f"{i18n.t('solve.run')}：{d['run_info'].get('result')}　"
                    f"{d['run_info'].get('message', '')}"
                )
            if d.get("error_info"):
                st.error(f"{i18n.t('solve.error')}：{d['error_info']}")

            # 测试点明细（可见时展示）
            s3, b3 = api_client.request("GET", f"/api/submissions/{sel_id}/log")
            if s3 == 200 and b3["data"].get("details"):
                st.write(i18n.t("solve.details"))
                det_rows = []
                for det in b3["data"]["details"]:
                    det_rows.append({
                        "#": det.get("id"),
                        i18n.t("solve.col_status"): det.get("result"),
                        i18n.t("solve.col_time"): det.get("time"),
                        i18n.t("solve.col_mem"): det.get("memory"),
                    })
                st.dataframe(det_rows, use_container_width=True, hide_index=True)

        if st.button(i18n.t("refresh")):
            st.rerun()
