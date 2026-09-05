"""AI 智能命题页面（仅管理员 / 教师助教可见）。"""

import streamlit as st

import api_client
import i18n

st.set_page_config(page_title=i18n.t("ai.title"))

i18n.render_lang_selector()

st.title(i18n.t("ai.title"))

if not api_client.is_logged_in():
    st.warning(i18n.t("login_required"))
    st.stop()

if api_client.current_user()["role"] != "admin":
    st.error(i18n.t("teacher_only"))
    st.stop()

# 提交成功提示
if "ai_msg" in st.session_state:
    st.success(st.session_state["ai_msg"])
    del st.session_state["ai_msg"]

# ---- 模型配置 ----
with st.expander(i18n.t("ai.model_config"), expanded=False):
    # 读取当前生效配置
    sc, bc = api_client.request("GET", "/api/ai/model-config")
    if sc == 200:
        cfg = bc["data"]
        src_map = {"db": i18n.t("ai.src_db"), "env": i18n.t("ai.src_env"), "none": i18n.t("ai.src_none")}
        src_label = src_map.get(cfg["source"], cfg["source"])
        key_state = (i18n.t("ai.key_configured", hint=cfg.get("key_hint", ""))
                     if cfg.get("key_configured") else i18n.t("ai.key_missing"))
        mode_txt = i18n.t("ai.mock_warn") if cfg.get("use_mock") else i18n.t("ai.real_enabled")
        st.caption(i18n.t(
            "ai.cur_config",
            url=cfg["provider_url"], model=cfg["model"], src=src_label, key=key_state, mode=mode_txt,
        ))
        with st.form("ai_config"):
            provider_url = st.text_input(i18n.t("ai.provider_url"), value=cfg.get("provider_url", ""))
            model = st.text_input(i18n.t("ai.model"), value=cfg.get("model", ""))
            api_key = st.text_input(
                i18n.t("ai.api_key"), type="password", placeholder=i18n.t("ai.api_key_ph"),
            )
            c1, c2 = st.columns(2)
            with c1:
                input_price = st.number_input(
                    i18n.t("ai.in_price"), value=float(cfg.get("input_price") or 0.0), step=0.1, format="%.6f"
                )
                output_price = st.number_input(
                    i18n.t("ai.out_price"), value=float(cfg.get("output_price") or 0.0), step=0.1, format="%.6f"
                )
            with c2:
                price_unit = st.number_input(
                    i18n.t("ai.price_unit"), value=int(cfg.get("price_unit") or 1000000), min_value=1, step=100000
                )
            if st.form_submit_button(i18n.t("ai.save_config")):
                payload = {
                    "provider_url": provider_url.strip(),
                    "model": model.strip(),
                    "api_key": api_key or None,
                    "input_price": input_price, "output_price": output_price, "price_unit": int(price_unit),
                }
                ss, bs = api_client.request("PUT", "/api/ai/model-config", json_body=payload)
                if ss == 200:
                    st.session_state["ai_msg"] = i18n.t("ai.config_saved")
                    st.rerun()
                else:
                    st.error(bs.get("msg", i18n.t("error_occurred")))
    else:
        st.error(bc.get("msg", i18n.t("error_occurred")))

# ---- 生成新题目 ----
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

# ---- 任务状态与结果 ----
if "ai_task_id" in st.session_state:
    st.divider()
    st.subheader(i18n.t("ai.task_status"))
    task_id = st.session_state["ai_task_id"]
    s, b = api_client.request("GET", f"/api/ai/problem-tasks/{task_id}")
    if s == 200:
        d = b["data"]
        st.write(i18n.t("ai.task", id=d["task_id"][:12]))
        st.write(i18n.t("ai.status", s=d["status"]))
        if d.get("progress"):
            st.write(i18n.t("ai.progress", p=d["progress"]))
        if d.get("usage"):
            u = d["usage"]
            st.caption(i18n.t(
                "ai.usage",
                i=u["input_tokens"], o=u["output_tokens"], t=u["total_tokens"],
                c=u["cost"], cur=u["currency"],
            ))
        if d.get("result"):
            st.write(i18n.t("ai.result_ok"))
            st.json(d["result"])
        col1, col2 = st.columns(2)
        with col1:
            if st.button(i18n.t("refresh")):
                st.rerun()
        with col2:
            if st.button(i18n.t("ai.clear_task")):
                st.session_state.pop("ai_task_id", None)
                st.rerun()
    else:
        st.error(b.get("msg", i18n.t("error_occurred")))

st.divider()
st.info(i18n.t("ai.auto_add_hint"))
