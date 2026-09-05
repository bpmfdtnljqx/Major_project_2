"""题目页面组：题目列表 / 详情 / 新增 / 编辑 / 删除。"""

import json

import streamlit as st

import api_client

st.set_page_config(page_title="题目")

st.title("题目")

if not api_client.is_logged_in():
    st.warning("请先登录")
    st.stop()

user = api_client.current_user()

status, body = api_client.request("GET", "/api/problems/")
if status != 200:
    st.error(body.get("msg", "获取题目列表失败"))
    st.stop()
problems = body["data"]


def _title_of(pid: str) -> str:
    for p in problems:
        if p["id"] == pid:
            return p["title"]
    return pid


# ---- 列表 + 详情 ----
st.subheader("题目列表")
if problems:
    problem_ids = [p["id"] for p in problems]
    selected = st.selectbox("选择题目", problem_ids, format_func=_title_of)
    s2, b2 = api_client.request("GET", f"/api/problems/{selected}")
    if s2 == 200:
        d = b2["data"]
        with st.expander(f"{d['id']} - {d['title']}", expanded=True):
            st.markdown(f"**描述**：{d['description']}")
            st.markdown(f"**输入格式**：{d['input_description']}")
            st.markdown(f"**输出格式**：{d['output_description']}")
            st.markdown("**样例**：")
            for smp in d["samples"]:
                st.code(f"输入：{smp['input']}\n输出：{smp['output']}")
            st.markdown(f"**限制**：{d['constraints']}")
            st.markdown(f"**时间 / 内存限制**：{d['time_limit']}s / {d['memory_limit']}MB")
            if d["tags"]:
                st.markdown(f"**标签**：{', '.join(d['tags'])}")
            if d.get("public_cases"):
                st.caption("🔓 该题测试点日志对所有人公开")
            # 去做题（跳到评测页并自动选中此题）
            if st.button("去做题 / 提交", key=f"go_{d['id']}", type="primary"):
                st.session_state["pending_problem"] = d["id"]
                st.switch_page("pages/3_Submissions.py")
            if user["role"] == "admin":
                if st.button("删除此题", key=f"del_{d['id']}"):
                    s3, b3 = api_client.request("DELETE", f"/api/problems/{d['id']}")
                    if s3 == 200:
                        st.success("已删除")
                        st.rerun()
                    else:
                        st.error(b3.get("msg", "删除失败"))
else:
    st.info("暂无题目")

# ---- 题目管理（新增/编辑，仅管理员可见；后端保持文档合规） ----
if user["role"] != "admin":
    st.divider()
    st.caption("仅教师 / 助教可新增或编辑题目；如需要请联系管理员。")
    st.stop()

# ---- 新增题目 ----
st.divider()
st.subheader("新增题目")
with st.form("add_problem"):
    pid = st.text_input("题目 id（必填）")
    title = st.text_input("标题（必填）")
    description = st.text_area("描述（必填）")
    input_desc = st.text_area("输入格式说明（必填）")
    output_desc = st.text_area("输出格式说明（必填）")
    constraints = st.text_input("数据范围与限制（必填）")
    samples = st.text_area("样例（JSON 数组）", value='[{"input": "1 2", "output": "3"}]')
    testcases = st.text_area("测试点（JSON 数组）", value='[{"input": "1 2", "output": "3"}]')
    with st.expander("可选字段"):
        hint = st.text_input("提示")
        source = st.text_input("来源")
        tags = st.text_input("标签（逗号分隔）")
        time_limit = st.number_input("时间限制(s)", min_value=0.1, value=3.0, step=0.5)
        memory_limit = st.number_input("内存限制(MB)", min_value=1, value=128)
        author = st.text_input("作者")
        difficulty = st.text_input("难度")
        public_cases = st.checkbox("公开测试点评测日志（所有人都能看该题提交的测试点明细）")
    if st.form_submit_button("新增"):
        try:
            samples_json = json.loads(samples)
            testcases_json = json.loads(testcases)
        except json.JSONDecodeError:
            st.error("样例 / 测试点的 JSON 格式错误")
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
                st.success("新增成功")
                st.rerun()
            else:
                st.error(b3.get("msg", "新增失败"))

# ---- 编辑题目 ----
st.divider()
st.subheader("编辑题目")
if problems:
    edit_id = st.selectbox("选择要编辑的题目", problem_ids, key="edit_select")
    s2, b2 = api_client.request("GET", f"/api/problems/{edit_id}")
    if s2 == 200:
        d = b2["data"]
        with st.form(f"edit_{edit_id}"):
            title = st.text_input("标题", value=d["title"])
            description = st.text_area("描述", value=d["description"])
            input_desc = st.text_area("输入格式说明", value=d["input_description"])
            output_desc = st.text_area("输出格式说明", value=d["output_description"])
            constraints = st.text_input("数据范围与限制", value=d["constraints"])
            samples = st.text_area("样例（JSON）", value=json.dumps(d["samples"], ensure_ascii=False))
            testcases = st.text_area("测试点（JSON）", value=json.dumps(d["testcases"], ensure_ascii=False))
            time_limit = st.number_input("时间限制(s)", value=float(d["time_limit"]), step=0.5)
            memory_limit = st.number_input("内存限制(MB)", value=int(d["memory_limit"]))
            public_cases = st.checkbox(
                "公开测试点评测日志（所有人都能看该题提交的测试点明细）",
                value=bool(d.get("public_cases", False)),
            )
            if st.form_submit_button("保存修改"):
                try:
                    samples_json = json.loads(samples)
                    testcases_json = json.loads(testcases)
                except json.JSONDecodeError:
                    st.error("样例 / 测试点的 JSON 格式错误")
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
                        st.success("已保存")
                        st.rerun()
                    else:
                        st.error(b3.get("msg", "保存失败"))
else:
    st.info("暂无题目可编辑")
