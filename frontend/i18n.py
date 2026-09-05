"""前端 i18n：中英双语文案字典。

用法：
    import i18n
    i18n.t("login.title")            # 按当前语言返回文案
    i18n.t("problem.limit", t=3, m=128)   # 支持 {t} 占位符

语言存于 st.session_state["lang"]（"zh"/"en"），默认中文。
切换语言后在页面顶部调用 i18n.render_lang_selector()（放侧边栏）。
"""

import streamlit as st

LANG_LABELS = {"zh": "中文 / Chinese", "en": "English / 英文"}

_STRINGS = {
    # ================= 通用 =================
    "app.title": {"zh": "在线评测系统", "en": "Online Judge"},
    "nav.problems": {"zh": "题目", "en": "Problems"},
    "nav.solve": {"zh": "做题", "en": "Solve"},
    "nav.profile": {"zh": "我的", "en": "Profile"},
    "nav.ai": {"zh": "AI 命题", "en": "AI Generate"},
    "sidebar.user": {"zh": "当前用户", "en": "Signed in as"},
    "login_required": {"zh": "请先登录", "en": "Please log in first"},
    "not_logged_tip": {
        "zh": "请在左侧导航选择「用户」「题目」或「做题」页面进行操作。",
        "en": "Use the sidebar to go to Users, Problems, or Solve pages.",
    },
    "logout": {"zh": "登出", "en": "Log out"},
    "submit": {"zh": "提交", "en": "Submit"},
    "refresh": {"zh": "刷新状态", "en": "Refresh"},
    "back": {"zh": "返回", "en": "Back"},
    "username": {"zh": "用户名", "en": "Username"},
    "password": {"zh": "密码", "en": "Password"},
    "error_occurred": {"zh": "出错了", "en": "Error"},
    "no_data": {"zh": "暂无数据", "en": "No data"},
    "admin": {"zh": "管理员", "en": "Admin"},
    "teacher_only": {"zh": "仅教师 / 助教可用", "en": "Teachers / TAs only"},

    # ================= 登录 / 注册 =================
    "auth.tab_login": {"zh": "登录", "en": "Sign in"},
    "auth.tab_register": {"zh": "注册", "en": "Sign up"},
    "auth.login_btn": {"zh": "登录", "en": "Sign in"},
    "auth.login_ok": {"zh": "登录成功", "en": "Signed in"},
    "auth.login_fail": {"zh": "登录失败", "en": "Sign in failed"},
    "auth.banned": {"zh": "该账号已被封禁，请联系管理员。", "en": "This account is banned. Please contact the administrator."},
    "auth.register_btn": {"zh": "注册", "en": "Sign up"},
    "auth.register_ok": {"zh": "注册成功，请切换到「登录」标签页登录", "en": "Registered. Switch to the Sign in tab to log in."},
    "auth.register_fail": {"zh": "注册失败", "en": "Registration failed"},
    "auth.logged_in_as": {"zh": "已登录：{name}（{role}）", "en": "Signed in: {name} ({role})"},

    # ================= 用户 =================
    "user.title": {"zh": "用户", "en": "Users"},
    "user.my_info": {"zh": "我的信息", "en": "My Info"},
    "user.role": {"zh": "角色", "en": "Role"},
    "user.join_time": {"zh": "注册时间", "en": "Joined"},
    "user.submits": {"zh": "提交数：{n}", "en": "Submissions: {n}"},
    "user.resolved": {"zh": "通过题数：{n}", "en": "Solved: {n}"},
    "user.manage": {"zh": "用户管理", "en": "User Management"},
    "user.total": {"zh": "共 {n} 个用户", "en": "{n} users"},
    "user.update_role": {"zh": "更新角色", "en": "Update role"},
    "user.role_updated": {"zh": "已更新", "en": "Updated"},
    "user.create_admin": {"zh": "创建管理员", "en": "Create Admin"},
    "user.create_btn": {"zh": "创建", "en": "Create"},
    "user.create_ok": {"zh": "创建成功", "en": "Created"},
    "user.system_reset": {"zh": "系统重置", "en": "System Reset"},
    "user.reset_hint": {
        "zh": "清空所有用户 / 题目 / 提交 / 日志数据，恢复种子题目，重建初始管理员账户，并退出当前登录。此操作不可恢复！",
        "en": "Clear all users / problems / submissions / logs, restore seed problems, recreate the initial admin, and sign out. This cannot be undone!",
    },
    "user.reset_btn": {"zh": "一键重置系统", "en": "Reset System"},
    "user.reset_confirm_btn": {"zh": "⚠️ 确认重置？此操作不可恢复，再次点击执行", "en": "⚠️ Confirm reset? Click again to proceed"},
    "user.reset_done": {
        "zh": "系统已重置，请用初始管理员账户（admin / admintestpassword）重新登录。",
        "en": "System reset. Sign in again with the initial admin (admin / admintestpassword).",
    },
    "user.only_admin_manage": {
        "zh": "仅教师 / 助教可新增或编辑题目；如需要请联系管理员。",
        "en": "Only teachers / TAs can create or edit problems. Contact an admin if needed.",
    },

    # ================= 题目 =================
    "problem.title": {"zh": "题目", "en": "Problems"},
    "problem.list": {"zh": "题目列表", "en": "Problem List"},
    "problem.select": {"zh": "选择题目", "en": "Select problem"},
    "problem.desc": {"zh": "描述", "en": "Description"},
    "problem.input_desc": {"zh": "输入格式", "en": "Input"},
    "problem.output_desc": {"zh": "输出格式", "en": "Output"},
    "problem.samples": {"zh": "样例", "en": "Samples"},
    "problem.constraints": {"zh": "数据范围", "en": "Constraints"},
    "problem.tags": {"zh": "标签", "en": "Tags"},
    "problem.limit": {"zh": "时间限制 {t}s ／ 内存限制 {m}MB", "en": "Time {t}s ／ Memory {m}MB"},
    "problem.public_log": {"zh": "该题测试点日志对所有人公开", "en": "Test-case logs are public for this problem"},
    "problem.solve_btn": {"zh": "去做题 / 提交", "en": "Solve / Submit"},
    "problem.delete_btn": {"zh": "删除此题", "en": "Delete"},
    "problem.deleted": {"zh": "已删除", "en": "Deleted"},
    "problem.none": {"zh": "暂无题目", "en": "No problems yet"},
    "problem.add": {"zh": "新增题目", "en": "Add Problem"},
    "problem.id": {"zh": "题目 id（必填）", "en": "Problem id (required)"},
    "problem.title_req": {"zh": "标题（必填）", "en": "Title (required)"},
    "problem.optional": {"zh": "可选字段", "en": "Optional fields"},
    "problem.hint": {"zh": "提示", "en": "Hint"},
    "problem.source": {"zh": "来源", "en": "Source"},
    "problem.tags_input": {"zh": "标签（逗号分隔）", "en": "Tags (comma separated)"},
    "problem.time_limit": {"zh": "时间限制(s)", "en": "Time limit (s)"},
    "problem.memory_limit": {"zh": "内存限制(MB)", "en": "Memory limit (MB)"},
    "problem.author": {"zh": "作者", "en": "Author"},
    "problem.difficulty": {"zh": "难度", "en": "Difficulty"},
    "problem.public_log_toggle": {
        "zh": "公开测试点评测日志（所有人都能看该题提交的测试点明细）",
        "en": "Make test-case logs public (everyone can see this problem's judge details)",
    },
    "problem.add_btn": {"zh": "新增", "en": "Add"},
    "problem.add_ok": {"zh": "新增成功", "en": "Added"},
    "problem.edit": {"zh": "编辑题目", "en": "Edit Problem"},
    "problem.edit_select": {"zh": "选择要编辑的题目", "en": "Select problem to edit"},
    "problem.save_btn": {"zh": "保存修改", "en": "Save"},
    "problem.saved": {"zh": "已保存", "en": "Saved"},
    "problem.none_edit": {"zh": "暂无题目可编辑", "en": "No problems to edit"},
    "problem.no_solve": {"zh": "暂无题目可提交", "en": "No problems to solve"},

    # ================= 做题 / 评测 =================
    "solve.title": {"zh": "做题", "en": "Solve"},
    "solve.select_problem": {"zh": "选择题目", "en": "Select problem"},
    "solve.submit_code": {"zh": "提交代码", "en": "Submit code"},
    "solve.language": {"zh": "语言", "en": "Language"},
    "solve.no_lang": {"zh": "无可用语言", "en": "No available language"},
    "solve.submit_btn": {"zh": "提交评测", "en": "Submit"},
    "solve.code_empty": {"zh": "代码不能为空", "en": "Code cannot be empty"},
    "solve.rate_limit": {"zh": "提交过于频繁，请稍后再试（1 分钟内最多 3 次）", "en": "Too many submissions. Please wait (max 3 per minute)."},
    "solve.submitted": {"zh": "已提交，submission_id：{id}，可查看下方记录", "en": "Submitted. submission_id: {id}. See records below."},
    "solve.my_records": {"zh": "我的提交记录", "en": "My Submissions"},
    "solve.records_none": {"zh": "暂无提交记录，去上面选一道题开始吧", "en": "No submissions yet. Pick a problem above."},
    "solve.total": {"zh": "共 {n} 条提交", "en": "{n} submissions"},
    "solve.col_id": {"zh": "提交号", "en": "ID"},
    "solve.col_problem": {"zh": "题目", "en": "Problem"},
    "solve.col_status": {"zh": "状态", "en": "Status"},
    "solve.col_score": {"zh": "得分", "en": "Score"},
    "solve.col_total": {"zh": "总分", "en": "Full"},
    "solve.select_sub": {"zh": "选择提交查看详情", "en": "Select a submission to view details"},
    "solve.compile": {"zh": "编译结果", "en": "Compile"},
    "solve.run": {"zh": "运行结果", "en": "Run"},
    "solve.error": {"zh": "错误信息", "en": "Error"},
    "solve.details": {"zh": "测试点明细", "en": "Case Details"},
    "solve.col_time": {"zh": "时间(s)", "en": "Time(s)"},
    "solve.col_mem": {"zh": "内存(MB)", "en": "Mem(MB)"},
    "solve.input_label": {"zh": "输入", "en": "Input"},
    "solve.output_label": {"zh": "输出", "en": "Output"},

    # ================= AI =================
    "ai.title": {"zh": "AI 智能命题", "en": "AI Problem Generation"},
    "ai.model_config": {"zh": "模型配置（可导入 / 更换 API Key）", "en": "Model Config (import / change API key)"},
    "ai.cur_config": {
        "zh": "当前生效：{url} · 模型 {model} ｜ 密钥来源：{src}（{key}）｜ {mode}",
        "en": "Current: {url} · model {model} ｜ key source: {src} ({key}) ｜ {mode}",
    },
    "ai.src_db": {"zh": "已保存（数据库）", "en": "Saved (database)"},
    "ai.src_env": {"zh": "环境变量 .env", "en": "Environment .env"},
    "ai.src_none": {"zh": "未配置", "en": "Not configured"},
    "ai.key_configured": {"zh": "已配置 {hint}", "en": "Configured {hint}"},
    "ai.key_missing": {"zh": "未配置", "en": "Not configured"},
    "ai.mock_warn": {"zh": "⚠️ 当前为 Mock 模式（不会调用真实模型）", "en": "⚠️ Mock mode (no real model calls)"},
    "ai.real_enabled": {"zh": "真实模型调用已启用", "en": "Real model calls enabled"},
    "ai.provider_url": {"zh": "提供商 URL", "en": "Provider URL"},
    "ai.model": {"zh": "模型名称", "en": "Model name"},
    "ai.api_key": {
        "zh": "API Key（留空则沿用当前已配置的密钥）", "en": "API Key (leave blank to keep current)",
    },
    "ai.api_key_ph": {"zh": "sk-……（仅在你需要更换时填写）", "en": "sk-… (only fill to change)"},
    "ai.in_price": {"zh": "输入单价", "en": "Input price"},
    "ai.out_price": {"zh": "输出单价", "en": "Output price"},
    "ai.price_unit": {"zh": "计价单位(token)", "en": "Price unit (tokens)"},
    "ai.save_config": {"zh": "保存模型配置", "en": "Save config"},
    "ai.config_saved": {"zh": "模型配置已更新", "en": "Model config updated"},
    "ai.gen_title": {"zh": "生成新题目", "en": "Generate Problem"},
    "ai.requirement": {"zh": "命题需求", "en": "Requirement"},
    "ai.requirement_ph": {
        "zh": "例如：生成一道求两个整数最大公约数的题，难度入门，含 3 个测试点",
        "en": "e.g. Generate a GCD problem, easy difficulty, 3 test cases",
    },
    "ai.gen_btn": {"zh": "生成题目", "en": "Generate"},
    "ai.req_empty": {"zh": "需求不能为空", "en": "Requirement cannot be empty"},
    "ai.task_created": {"zh": "任务已创建，正在生成……", "en": "Task created, generating..."},
    "ai.task_status": {"zh": "任务状态", "en": "Task Status"},
    "ai.task": {"zh": "任务：{id}", "en": "Task: {id}"},
    "ai.status": {"zh": "状态：{s}", "en": "Status: {s}"},
    "ai.progress": {"zh": "进度：{p}", "en": "Progress: {p}"},
    "ai.usage": {
        "zh": "Token 用量：输入 {i} / 输出 {o} / 总计 {t}，费用 {c} {cur}",
        "en": "Tokens: in {i} / out {o} / total {t}, cost {c} {cur}",
    },
    "ai.result_ok": {"zh": "生成的题目（已自动加入题库）：", "en": "Generated problem (auto-added to bank):"},
    "ai.clear_task": {"zh": "清除此任务", "en": "Clear task"},
    "ai.auto_add_hint": {"zh": "生成的题目会自动加入「题目」页面的题库，可直接用于评测。", "en": "Generated problems are auto-added to the Problems page and ready for judging."},
}


def get_lang() -> str:
    """返回当前语言（zh/en），并确保会话中已初始化。"""
    lang = st.session_state.get("lang", "zh")
    if lang not in LANG_LABELS:
        lang = "zh"
    st.session_state["lang"] = lang
    return lang


def set_lang(lang: str) -> None:
    st.session_state["lang"] = lang if lang in LANG_LABELS else "zh"


def t(key: str, **kw) -> str:
    """按当前语言返回文案；缺失则回退中文/英文或返回 key。"""
    lang = get_lang()
    entry = _STRINGS.get(key, {})
    text = entry.get(lang) or entry.get("zh") or key
    if kw:
        try:
            text = text.format(**kw)
        except (KeyError, IndexError):
            pass
    return text


def render_lang_selector() -> None:
    """在侧边栏渲染语言切换控件。放在每页开头调用一次。"""
    cur = get_lang()
    label = {"zh": "🌐 语言 / Language", "en": "🌐 Language / 语言"}[cur]
    chosen = st.sidebar.selectbox(
        label, list(LANG_LABELS.keys()),
        format_func=lambda k: LANG_LABELS[k],
        index=list(LANG_LABELS.keys()).index(cur),
        key="lang_sel",
    )
    if chosen != cur:
        set_lang(chosen)
        st.rerun()
