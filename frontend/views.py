"""单页化的各视图渲染函数。

主程序 app.py 依据顶栏导航选中项调用对应 render_*()。
所有文案走 i18n；管理员门控在各自函数内处理。
"""

import json

import streamlit as st
from streamlit_ace import st_ace

import api_client
import i18n
import theme


def _require_login() -> bool:
    """未登录则提示并停止，返回是否继续。"""
    if not api_client.is_logged_in():
        if "global_msg" in st.session_state:
            st.success(st.session_state["global_msg"])
            del st.session_state["global_msg"]
        st.warning(i18n.t("login_required"))
        st.stop()
        return False
    return True


# ================= 用户 / 我的 =================
def render_profile():
    st.title(i18n.t("user.title"))

    if not _require_login():
        return
    user = api_client.current_user()

    st.subheader(i18n.t("user.my_info"))
    status, body = api_client.request("GET", f"/api/users/{user['user_id']}")
    if status == 200:
        info = body["data"]
        st.write(f"{i18n.t('username')}：{info['username']}")
        role_txt = {"admin": i18n.t("admin"), "user": "user", "banned": "banned"}.get(
            info["role"], info["role"]
        )
        st.write(f"{i18n.t('user.role')}：{role_txt}")
        st.write(f"{i18n.t('user.join_time')}：{info['join_time']}")
        st.write(
            f"{i18n.t('user.submits', n=info['submit_count'])}　"
            f"{i18n.t('user.resolved', n=info['resolve_count'])}"
        )
    else:
        st.error(body.get("msg", i18n.t("error_occurred")))

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
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        new_role = st.selectbox(
                            i18n.t("user.role"), roles,
                            index=roles.index(u["role"]), key=f"role_{u['user_id']}",
                        )
                    with c2:
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
                st.success(i18n.t("user.create_ok")) if s2 == 200 else st.error(
                    b2.get("msg", i18n.t("error_occurred"))
                )

        st.divider()
        st.subheader(i18n.t("user.system_reset"))
        st.caption(i18n.t("user.reset_hint"))
        if st.button(
            st.session_state.get("confirm_reset")
            and i18n.t("user.reset_confirm_btn") or i18n.t("user.reset_btn")
        ):
            if not st.session_state.get("confirm_reset"):
                st.session_state["confirm_reset"] = True
                st.rerun()
            else:
                s, b = api_client.request("POST", "/api/reset/")
                if s == 200:
                    api_client.logout()
                    st.session_state.pop("confirm_reset", None)
                    st.session_state["global_msg"] = i18n.t("user.reset_done")
                    st.rerun()
                else:
                    st.error(b.get("msg", i18n.t("error_occurred")))
                    st.session_state.pop("confirm_reset", None)


# ================= 题目（浏览 + 管理） =================
def render_problems():
    st.title(i18n.t("problem.title"))

    if not _require_login():
        return
    user = api_client.current_user()

    status, body = api_client.request("GET", "/api/problems/")
    if status != 200:
        st.error(body.get("msg", i18n.t("error_occurred")))
        return
    problems = body["data"]

    def _title_of(pid):
        for p in problems:
            if p["id"] == pid:
                return p["title"]
        return pid

    st.subheader(i18n.t("problem.list"))
    if problems:
        selected = st.selectbox(i18n.t("problem.select"), [p["id"] for p in problems],
                                format_func=_title_of, key="pb_select")
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

                c1, c2, c3 = st.columns([2, 1, 1])
                with c1:
                    if st.button(i18n.t("problem.solve_btn"), key=f"go_{d['id']}", type="primary"):
                        st.session_state["pending_problem"] = d["id"]
                        st.session_state["main_nav"] = "solve"
                        st.rerun()
                if user["role"] == "admin":
                    with c2:
                        if st.button(i18n.t("problem.delete_btn"), key=f"del_{d['id']}"):
                            s3, b3 = api_client.request("DELETE", f"/api/problems/{d['id']}")
                            if s3 == 200:
                                st.success(i18n.t("problem.deleted"))
                                st.rerun()
                            else:
                                st.error(b3.get("msg", i18n.t("error_occurred")))
    else:
        st.info(i18n.t("problem.none"))

    # ---- 管理（仅 admin） ----
    if user["role"] != "admin":
        st.divider()
        st.caption(i18n.t("user.only_admin_manage"))
        return

    st.divider()
    st.subheader(i18n.t("problem.add"))
    with st.form("add_problem"):
        pid = st.text_input(i18n.t("problem.id"))
        title = st.text_input(i18n.t("problem.title_req"))
        description = st.text_area(i18n.t("problem.desc"))
        input_desc = st.text_area(i18n.t("problem.input_desc"))
        output_desc = st.text_area(i18n.t("problem.output_desc"))
        constraints = st.text_input(i18n.t("problem.constraints"))
        samples = st.text_area(i18n.t("problem.samples") + " (JSON)",
                               value='[{"input": "1 2", "output": "3"}]')
        testcases = st.text_area("Testcases (JSON)",
                                 value='[{"input": "1 2", "output": "3"}]')
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
                sj = json.loads(samples)
                tj = json.loads(testcases)
            except json.JSONDecodeError:
                st.error("JSON format error")
            else:
                payload = {
                    "id": pid, "title": title, "description": description,
                    "input_description": input_desc, "output_description": output_desc,
                    "samples": sj, "constraints": constraints, "testcases": tj,
                    "hint": hint, "source": source,
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "time_limit": time_limit, "memory_limit": int(memory_limit),
                    "author": author, "difficulty": difficulty, "public_cases": public_cases,
                }
                s3, b3 = api_client.request("POST", "/api/problems/", json_body=payload)
                st.success(i18n.t("problem.add_ok")) if s3 == 200 else st.error(
                    b3.get("msg", i18n.t("error_occurred"))
                )
                if s3 == 200:
                    st.rerun()

    st.divider()
    st.subheader(i18n.t("problem.edit"))
    if problems:
        edit_id = st.selectbox(i18n.t("problem.edit_select"), [p["id"] for p in problems],
                               key="pb_edit_select")
        s2, b2 = api_client.request("GET", f"/api/problems/{edit_id}")
        if s2 == 200:
            d = b2["data"]
            with st.form(f"edit_{edit_id}"):
                title = st.text_input(i18n.t("problem.title_req"), value=d["title"])
                description = st.text_area(i18n.t("problem.desc"), value=d["description"])
                input_desc = st.text_area(i18n.t("problem.input_desc"), value=d["input_description"])
                output_desc = st.text_area(i18n.t("problem.output_desc"), value=d["output_description"])
                constraints = st.text_input(i18n.t("problem.constraints"), value=d["constraints"])
                samples = st.text_area(i18n.t("problem.samples") + " (JSON)",
                                       value=json.dumps(d["samples"], ensure_ascii=False))
                testcases = st.text_area("Testcases (JSON)",
                                         value=json.dumps(d["testcases"], ensure_ascii=False))
                time_limit = st.number_input(i18n.t("problem.time_limit"),
                                             value=float(d["time_limit"]), step=0.5)
                memory_limit = st.number_input(i18n.t("problem.memory_limit"),
                                               value=int(d["memory_limit"]))
                public_cases = st.checkbox(i18n.t("problem.public_log_toggle"),
                                           value=bool(d.get("public_cases", False)))
                if st.form_submit_button(i18n.t("problem.save_btn")):
                    try:
                        sj = json.loads(samples)
                        tj = json.loads(testcases)
                    except json.JSONDecodeError:
                        st.error("JSON format error")
                    else:
                        payload = {
                            "id": edit_id, "title": title, "description": description,
                            "input_description": input_desc, "output_description": output_desc,
                            "samples": sj, "constraints": constraints, "testcases": tj,
                            "hint": d.get("hint", ""), "source": d.get("source", ""),
                            "tags": d.get("tags", []), "time_limit": time_limit,
                            "memory_limit": int(memory_limit), "author": d.get("author", ""),
                            "difficulty": d.get("difficulty", ""), "public_cases": public_cases,
                        }
                        s3, b3 = api_client.request("PUT", f"/api/problems/{edit_id}", json_body=payload)
                        if s3 == 200:
                            st.success(i18n.t("problem.saved"))
                            st.rerun()
                        else:
                            st.error(b3.get("msg", i18n.t("error_occurred")))
    else:
        st.info(i18n.t("problem.none_edit"))


# ================= 做题 =================
def render_solve():
    st.title(i18n.t("solve.title"))

    if not _require_login():
        return
    user = api_client.current_user()

    # 从"题目"跳转自动选中
    default_problem = st.session_state.pop("pending_problem", None)

    status, body = api_client.request("GET", "/api/problems/")
    problems = body["data"] if status == 200 else []
    status, body = api_client.request("GET", "/api/languages/")
    languages = body["data"]["name"] if status == 200 else []

    if not problems:
        st.warning(i18n.t("problem.no_solve"))
        return

    ids = [p["id"] for p in problems]
    idx = ids.index(default_problem) if default_problem in ids else 0
    problem_id = st.selectbox(
        i18n.t("solve.select_problem"), ids, index=idx,
        format_func=lambda pid: next((p["title"] for p in problems if p["id"] == pid), pid),
        key="sub_problem",
    )

    detail = {}
    s, b = api_client.request("GET", f"/api/problems/{problem_id}")
    if s == 200:
        detail = b["data"]

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
        st.caption(i18n.t("problem.limit", t=detail.get("time_limit", 3),
                          m=detail.get("memory_limit", 128)))
        if detail.get("tags"):
            st.caption(f"{i18n.t('problem.tags')}：{'、'.join(detail['tags'])}")

    with right:
        st.subheader(i18n.t("solve.submit_code"))
        if not languages:
            st.warning(i18n.t("solve.no_lang"))
        else:
            language = st.selectbox(i18n.t("solve.language"), languages, key="sub_lang")
            ace_mode = {"python": "python", "cpp": "c_cpp"}.get(language, "plain_text")
            # 代码编辑器跟随亮/暗主题（避免亮色页面里嵌一大块深色编辑器过于突兀）
            ace_theme = "chrome" if theme.current_mode() == "light" else "monokai"
            code = st_ace(
                value=st.session_state.get(f"draft_{problem_id}", ""),
                language=ace_mode, theme=ace_theme, keybinding="vscode",
                font_size=14, tab_size=4, min_lines=12, auto_update=True,
                key=f"ace_{problem_id}",
            )
            if st.button(i18n.t("solve.submit_btn"), type="primary"):
                if not code.strip():
                    st.error(i18n.t("solve.code_empty"))
                else:
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

    if "submit_msg" in st.session_state:
        st.success(st.session_state["submit_msg"])
        del st.session_state["submit_msg"]

    # ---- 我的提交记录 ----
    st.divider()
    st.subheader(i18n.t("solve.my_records"))
    status, body = api_client.request("GET", "/api/submissions/",
                                      params={"user_id": user["user_id"]})
    if status != 200:
        st.error(body.get("msg", i18n.t("error_occurred")))
        return
    subs = body["data"]["submissions"]
    if not subs:
        st.info(i18n.t("solve.records_none"))
        return

    st.write(i18n.t("solve.total", n=body["data"]["total"]))
    rows = []
    for s in subs[:50]:
        t = next((p["title"] for p in problems if p["id"] == s.get("problem_id")),
                 s.get("problem_id"))
        rows.append({
            i18n.t("solve.col_id"): s["submission_id"][:10],
            i18n.t("solve.col_problem"): t,
            i18n.t("solve.col_status"): s.get("status", "-"),
            i18n.t("solve.col_score"): s.get("score", "-"),
            i18n.t("solve.col_total"): s.get("counts", "-"),
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    sub_ids = [s["submission_id"] for s in subs]
    sel_short = st.selectbox(i18n.t("solve.select_sub"), [x[:10] for x in sub_ids],
                             key="sub_select")
    sel_id = next(s for s in sub_ids if s.startswith(sel_short))
    s2, b2 = api_client.request("GET", f"/api/submissions/{sel_id}")
    if s2 == 200:
        d = b2["data"]
        c1, c2, c3 = st.columns(3)
        c1.metric(i18n.t("solve.col_status"), d["status"])
        c2.metric(i18n.t("solve.col_score"), d["score"] if d["score"] is not None else "-")
        c3.metric(i18n.t("solve.col_total"), d["counts"] if d["counts"] is not None else "-")
        if d.get("compile_info"):
            st.info(f"{i18n.t('solve.compile')}：{d['compile_info'].get('result')}　"
                    f"{d['compile_info'].get('message', '')}")
        if d.get("run_info"):
            st.info(f"{i18n.t('solve.run')}：{d['run_info'].get('result')}　"
                    f"{d['run_info'].get('message', '')}")
        if d.get("error_info"):
            st.error(f"{i18n.t('solve.error')}：{d['error_info']}")
        s3, b3 = api_client.request("GET", f"/api/submissions/{sel_id}/log")
        if s3 == 200 and b3["data"].get("details"):
            st.write(i18n.t("solve.details"))
            det_rows = [{
                "#": det.get("id"),
                i18n.t("solve.col_status"): det.get("result"),
                i18n.t("solve.col_time"): det.get("time"),
                i18n.t("solve.col_mem"): det.get("memory"),
            } for det in b3["data"]["details"]]
            st.dataframe(det_rows, use_container_width=True, hide_index=True)
    if st.button(i18n.t("refresh")):
        st.rerun()


# ================= AI =================
def render_ai():
    st.title(i18n.t("ai.title"))

    if not _require_login():
        return
    if api_client.current_user()["role"] != "admin":
        st.error(i18n.t("teacher_only"))
        return

    if "ai_msg" in st.session_state:
        st.success(st.session_state["ai_msg"])
        del st.session_state["ai_msg"]

    with st.expander(i18n.t("ai.model_config"), expanded=False):
        sc, bc = api_client.request("GET", "/api/ai/model-config")
        if sc == 200:
            cfg = bc["data"]
            src_map = {"db": i18n.t("ai.src_db"), "env": i18n.t("ai.src_env"),
                       "none": i18n.t("ai.src_none")}
            src_label = src_map.get(cfg["source"], cfg["source"])
            key_state = (i18n.t("ai.key_configured", hint=cfg.get("key_hint", ""))
                         if cfg.get("key_configured") else i18n.t("ai.key_missing"))
            mode_txt = i18n.t("ai.mock_warn") if cfg.get("use_mock") else i18n.t("ai.real_enabled")
            st.caption(i18n.t("ai.cur_config", url=cfg["provider_url"], model=cfg["model"],
                              src=src_label, key_state=key_state, mode=mode_txt))
            with st.form("ai_config"):
                provider_url = st.text_input(i18n.t("ai.provider_url"), value=cfg.get("provider_url", ""))
                model = st.text_input(i18n.t("ai.model"), value=cfg.get("model", ""))
                api_key = st.text_input(i18n.t("ai.api_key"), type="password",
                                        placeholder=i18n.t("ai.api_key_ph"))
                c1, c2 = st.columns(2)
                with c1:
                    in_p = st.number_input(i18n.t("ai.in_price"),
                                           value=float(cfg.get("input_price") or 0.0),
                                           step=0.1, format="%.6f")
                    out_p = st.number_input(i18n.t("ai.out_price"),
                                            value=float(cfg.get("output_price") or 0.0),
                                            step=0.1, format="%.6f")
                with c2:
                    unit = st.number_input(i18n.t("ai.price_unit"),
                                           value=int(cfg.get("price_unit") or 1000000),
                                           min_value=1, step=100000)
                if st.form_submit_button(i18n.t("ai.save_config")):
                    payload = {
                        "provider_url": provider_url.strip(), "model": model.strip(),
                        "api_key": api_key or None,
                        "input_price": in_p, "output_price": out_p, "price_unit": int(unit),
                    }
                    ss, bs = api_client.request("PUT", "/api/ai/model-config", json_body=payload)
                    if ss == 200:
                        st.session_state["ai_msg"] = i18n.t("ai.config_saved")
                        st.rerun()
                    else:
                        st.error(bs.get("msg", i18n.t("error_occurred")))
        else:
            st.error(bc.get("msg", i18n.t("error_occurred")))

    st.subheader(i18n.t("ai.gen_title"))
    with st.form("ai_task"):
        requirement = st.text_area(i18n.t("ai.requirement"), placeholder=i18n.t("ai.requirement_ph"))
        if st.form_submit_button(i18n.t("ai.gen_btn")):
            if not requirement.strip():
                st.error(i18n.t("ai.req_empty"))
            else:
                s, b = api_client.request(
                    "POST", "/api/ai/problem-tasks/", json_body={"requirement": requirement}
                )
                if s == 200:
                    st.session_state["ai_task_id"] = b["data"]["task_id"]
                    st.session_state["ai_msg"] = i18n.t("ai.task_created")
                    st.rerun()
                else:
                    st.error(b.get("msg", i18n.t("error_occurred")))

    if "ai_task_id" in st.session_state:
        st.divider()
        st.subheader(i18n.t("ai.task_status"))
        s, b = api_client.request("GET", f"/api/ai/problem-tasks/{st.session_state['ai_task_id']}")
        if s == 200:
            d = b["data"]
            st.write(i18n.t("ai.task", id=d["task_id"][:12]))
            st.write(i18n.t("ai.status", s=d["status"]))
            if d.get("progress"):
                st.write(i18n.t("ai.progress", p=d["progress"]))
            if d.get("usage"):
                u = d["usage"]
                st.caption(i18n.t("ai.usage", i=u["input_tokens"], o=u["output_tokens"],
                                  t=u["total_tokens"], c=u["cost"], cur=u["currency"]))
            if d.get("result"):
                st.write(i18n.t("ai.result_ok"))
                st.json(d["result"])
            c1, c2 = st.columns(2)
            with c1:
                if st.button(i18n.t("refresh")):
                    st.rerun()
            with c2:
                if st.button(i18n.t("ai.clear_task")):
                    st.session_state.pop("ai_task_id", None)
                    st.rerun()
        else:
            st.error(b.get("msg", i18n.t("error_occurred")))

    st.divider()
    st.info(i18n.t("ai.auto_add_hint"))
