"""题目页面组：题目列表 / 详情 / 新增 / 编辑 / 删除。"""

import json

import streamlit as st

import api_client
import i18n

st.set_page_config(page_title=i18n.t("problem.title"))

i18n.render_lang_selector()

st.title(i18n.t("problem.title"))

if not api_client.is_logged_in():
    st.warning(i18n.t("login_required"))
    st.stop()

user = api_client.current_user()

status, body = api_client.request("GET", "/api/problems/")
if status != 200:
    st.error(body.get("msg", i18n.t("error_occurred")))
    st.stop()
problems = body["data"]


def _title_of(pid: str) -> str:
    for p in problems:
        if p["id"] == pid:
            return p["title"]
    return pid


# ---- 列表 + 详情 ----
st.subheader(i18n.t("problem.list"))
if problems:
    problem_ids = [p["id"] for p in problems]
    selected = st.selectbox(i18n.t("problem.select"), problem_ids, format_func=_title_of)
    s2, b2 = api_client.request("GET", f"/api/problems/{selected}")
    if s2 == 200:
        d = b2["data"]
        with st.expander(f"{d['id']} - {d['title']}", expanded=True):
            st.markdown(f"**{i18n.t('problem.desc')}**：{d['description']}")
            st.markdown(f"**{i18n.t('problem.input_desc')}**：{d['input_description']}")
            st.markdown(f"**{i18n.t('problem.output_desc')}**：{d['output_description']}")
            st.markdown(f"**{i18n.t('problem.samples')}**：")
            for smp in d["samples"]:
                st.code(
                    f"{i18n.t('solve.input_label')}：{smp['input']}\n"
                    f"{i18n.t('solve.output_label')}：{smp['output']}"
                )
            st.markdown(f"**{i18n.t('problem.constraints')}**：{d['constraints']}")
            st.caption(i18n.t("problem.limit", t=d["time_limit"], m=d["memory_limit"]))
            if d.get("tags"):
                st.markdown(f"**{i18n.t('problem.tags')}**：{', '.join(d['tags'])}")
            if d.get("public_cases"):
                st.caption(i18n.t("problem.public_log"))
            # 去做题（跳到评测页并自动选中此题）
            if st.button(i18n.t("problem.solve_btn"), key=f"go_{d['id']}", type="primary"):
                st.session_state["pending_problem"] = d["id"]
                st.switch_page("pages/3_Submissions.py")
            if user["role"] == "admin":
                if st.button(i18n.t("problem.delete_btn"), key=f"del_{d['id']}"):
                    s3, b3 = api_client.request("DELETE", f"/api/problems/{d['id']}")
                    if s3 == 200:
                        st.success(i18n.t("problem.deleted"))
                        st.rerun()
                    else:
                        st.error(b3.get("msg", i18n.t("error_occurred")))
else:
    st.info(i18n.t("problem.none"))

# ---- 题目管理（新增/编辑，仅管理员可见；后端保持文档合规） ----
if user["role"] != "admin":
    st.divider()
    st.caption(i18n.t("user.only_admin_manage"))
    st.stop()

# ---- 新增题目 ----
st.divider()
st.subheader(i18n.t("problem.add"))
with st.form("add_problem"):
    pid = st.text_input(i18n.t("problem.id"))
    title = st.text_input(i18n.t("problem.title_req"))
    description = st.text_area(i18n.t("problem.desc"))
    input_desc = st.text_area(i18n.t("problem.input_desc"))
    output_desc = st.text_area(i18n.t("problem.output_desc"))
    constraints = st.text_input(i18n.t("problem.constraints"))
    samples = st.text_area(i18n.t("problem.samples") + " (JSON)", value='[{"input": "1 2", "output": "3"}]')
    testcases = st.text_area("Testcases (JSON)", value='[{"input": "1 2", "output": "3"}]')
    with st.expander(i18n.t("problem.optional")):
        hint = st.text_input(i18n.t("problem.hint"))
        source = st.text_input(i18n.t("problem.source"))
        tags = st.text_input(i18n.t("problem.tags_input"))
        time_limit = st.number_input(i18n.t("problem.time_limit"), min_value=0.1, value=3.0, step=0.5)
        memory_limit = st.number_input(i18n.t("problem.memory_limit"), min_value=1, value=128)
        author = st.text_input(i18n.t("problem.author"))
        difficulty = st.text_input(i18n.t("problem.difficulty"))
        public_cases = st.checkbox(i18n.t("problem.public_log_toggle"))
    if st.form_submit_button(i18n.t("problem.add_btn")):
        try:
            samples_json = json.loads(samples)
            testcases_json = json.loads(testcases)
        except json.JSONDecodeError:
            st.error("JSON format error")
        else:
            payload = {
                "id": pid, "title": title, "description": description,
                "input_description": input_desc, "output_description": output_desc,
                "samples": samples_json, "constraints": constraints,
                "testcases": testcases_json, "hint": hint, "source": source,
                "tags": [t.strip() for t in tags.split(",") if t.strip()],
                "time_limit": time_limit, "memory_limit": int(memory_limit),
                "author": author, "difficulty": difficulty,
                "public_cases": public_cases,
            }
            s3, b3 = api_client.request("POST", "/api/problems/", json_body=payload)
            if s3 == 200:
                st.success(i18n.t("problem.add_ok"))
                st.rerun()
            else:
                st.error(b3.get("msg", i18n.t("error_occurred")))

# ---- 编辑题目 ----
st.divider()
st.subheader(i18n.t("problem.edit"))
if problems:
    edit_id = st.selectbox(i18n.t("problem.edit_select"), problem_ids, key="edit_select")
    s2, b2 = api_client.request("GET", f"/api/problems/{edit_id}")
    if s2 == 200:
        d = b2["data"]
        with st.form(f"edit_{edit_id}"):
            title = st.text_input(i18n.t("problem.title_req"), value=d["title"])
            description = st.text_area(i18n.t("problem.desc"), value=d["description"])
            input_desc = st.text_area(i18n.t("problem.input_desc"), value=d["input_description"])
            output_desc = st.text_area(i18n.t("problem.output_desc"), value=d["output_description"])
            constraints = st.text_input(i18n.t("problem.constraints"), value=d["constraints"])
            samples = st.text_area(i18n.t("problem.samples") + " (JSON)", value=json.dumps(d["samples"], ensure_ascii=False))
            testcases = st.text_area("Testcases (JSON)", value=json.dumps(d["testcases"], ensure_ascii=False))
            time_limit = st.number_input(i18n.t("problem.time_limit"), value=float(d["time_limit"]), step=0.5)
            memory_limit = st.number_input(i18n.t("problem.memory_limit"), value=int(d["memory_limit"]))
            public_cases = st.checkbox(
                i18n.t("problem.public_log_toggle"), value=bool(d.get("public_cases", False))
            )
            if st.form_submit_button(i18n.t("problem.save_btn")):
                try:
                    samples_json = json.loads(samples)
                    testcases_json = json.loads(testcases)
                except json.JSONDecodeError:
                    st.error("JSON format error")
                else:
                    payload = {
                        "id": edit_id, "title": title, "description": description,
                        "input_description": input_desc, "output_description": output_desc,
                        "samples": samples_json, "constraints": constraints,
                        "testcases": testcases_json,
                        "hint": d.get("hint", ""), "source": d.get("source", ""),
                        "tags": d.get("tags", []), "time_limit": time_limit,
                        "memory_limit": int(memory_limit),
                        "author": d.get("author", ""), "difficulty": d.get("difficulty", ""),
                        "public_cases": public_cases,
                    }
                    s3, b3 = api_client.request("PUT", f"/api/problems/{edit_id}", json_body=payload)
                    if s3 == 200:
                        st.success(i18n.t("problem.saved"))
                        st.rerun()
                    else:
                        st.error(b3.get("msg", i18n.t("error_occurred")))
else:
    st.info(i18n.t("problem.none_edit"))
