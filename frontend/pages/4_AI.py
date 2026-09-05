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

# ---- 模型配置 ----
with st.expander("模型配置（可导入 / 更换 API Key）", expanded=False):
    # 读取当前生效配置
    sc, bc = api_client.request("GET", "/api/ai/model-config")
    if sc == 200:
        cfg = bc["data"]
        src_label = {"db": "已保存（数据库）", "env": "环境变量 .env", "none": "未配置"}.get(cfg["source"], cfg["source"])
        st.caption(
            f"当前生效：{cfg['provider_url']} · 模型 {cfg['model']} ｜ 密钥来源：{src_label}"
            f"（{'已配置 ' + cfg.get('key_hint', '') if cfg.get('key_configured') else '未配置'}）"
            f" ｜ {'⚠️ 当前为 Mock 模式（不会调用真实模型）' if cfg.get('use_mock') else '真实模型调用已启用'}"
        )
        with st.form("ai_config"):
            provider_url = st.text_input("提供商 URL", value=cfg.get("provider_url", ""))
            model = st.text_input("模型名称", value=cfg.get("model", ""))
            api_key = st.text_input(
                "API Key（留空则沿用当前已配置的密钥）", type="password",
                placeholder="sk-……（仅在你需要更换时填写）",
            )
            c1, c2 = st.columns(2)
            with c1:
                input_price = st.number_input("输入单价", value=float(cfg.get("input_price") or 0.0), step=0.1, format="%.6f")
                output_price = st.number_input("输出单价", value=float(cfg.get("output_price") or 0.0), step=0.1, format="%.6f")
            with c2:
                price_unit = st.number_input("计价单位(token)", value=int(cfg.get("price_unit") or 1000000), min_value=1, step=100000)
            if st.form_submit_button("保存模型配置"):
                payload = {
                    "provider_url": provider_url.strip(),
                    "model": model.strip(),
                    "api_key": api_key or None,
                    "input_price": input_price, "output_price": output_price, "price_unit": int(price_unit),
                }
                ss, bs = api_client.request("PUT", "/api/ai/model-config", json_body=payload)
                if ss == 200:
                    st.session_state["ai_msg"] = "模型配置已更新"
                    st.rerun()
                else:
                    st.error(bs.get("msg", "保存配置失败"))
    else:
        st.error(bc.get("msg", "获取模型配置失败"))

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
