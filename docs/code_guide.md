# OJ 系统代码解读

> 在线评测系统（实验二）源码结构说明 · 项目根目录 `major_project_2`

---

## 一、整体架构

系统是前后端分离的三层结构：

```
浏览器（Streamlit 页面）
   |  HTTP + session cookie
   v
FastAPI 后端（app/）
   +-- 路由层  app/routers/   —— 定义接口，做鉴权、参数校验
   +-- 核心层  app/core/      —— 存储、评测、鉴权等可复用逻辑
   +-- 数据模型 app/models.py —— Pydantic 请求/响应模型
   |
   +-- 题目：JSON 一题一文件（problems/ 目录）
   +-- 其余：SQLite 单库（data/oj.db）存用户/提交/日志/AI 任务
```

- **前端只做展示和交互**，权限判断全在后端。
- 后端所有接口用 `async def`，统一返回 `{code, msg, data}`，HTTP 状态码与 `code` 一致。
- 评测和 AI 命题是阻塞的，都扔到后台 `asyncio.create_task` 异步执行，接口先返回 pending，前端轮询。

数据流举例（一次提交评测）：

```
前端做题页提交代码
  -> POST /api/submissions/  （创建 pending 记录，立刻返回）
  -> 后台 _judge_task 跑 judge()（编译/运行/比对/限制资源）
  -> 回写 SQLite（status/score/details）
  -> 前端轮询 GET /api/submissions/{id} 看到结果
```

---

## 二、后端 app/（FastAPI）

### 1. app/main.py —— 应用入口

- `create_app()`：构建 FastAPI 实例。依次初始化六个存储层（题目、语言、提交、用户、日志、AI）和频率限制器，把它们挂到 `app.state` 上供各路由取用；再挂载七个路由模块，注册异常处理器。
- `_register_exception_handlers(app)`：把三类异常统一成 `{code,msg,data}` 响应——业务异常 `AppError` 直接用它的 code；`RequestValidationError`（FastAPI 默认 422）转成 400；`HTTPException` 透传状态码。

### 2. app/models.py —— Pydantic 数据模型

- `TestCase`：单个测试点/样例，含 `input` 和 `output` 两个字段。
- `Problem`：完整题目模型。必填 `id`、`title`；`description`/`samples`/`testcases` 等有默认值；`time_limit`/`memory_limit` 是 Optional（None 表示未配置，评测时回退）。
- `Language`：语言配置，含 `name`、编译命令、运行命令（`{src}`/`{exe}` 占位符）、时间/内存限制等。
- `SubmissionCreate`：提交请求体（problem_id + language + code）。
- `Credentials`：用户名密码（登录/注册共用），`min_length=1` 拒绝空串。
- `RoleUpdate`：改角色的请求体。
- `LogVisibility`：日志可见性配置请求体。
- `ModelConfigBody` / `AITaskCreate`：AI 模型配置 / 命题任务请求体。

### 3. app/core/ —— 核心层

**storage.py（题目存储，JSON）**
- `ProblemStore`：题目的内存存储。启动时 `load()` 把 problems/ 目录里的 JSON 全读进内存；`_seed_if_empty()` 在目录为空时从 seed/ 复制初始题目。增删改查都在内存里做，写操作即时落盘（`_write`）。
- `list_all` / `get` / `exists` / `add` / `update` / `delete`：标准增删改查。
- `update_public_cases`：改某题日志公开与否。
- `reset`：清空并重新播种（系统重置用）。

**user_store.py（用户与会话，SQLite）**
- `hash_password` / `verify_password`：密码哈希与校验（sha256 加盐）。
- `UserStore`：管 users 表（用户）和 sessions 表（会话）。
- `create_user`：注册，用户名重复返回 None。
- `get_by_id` / `get_by_username`：查用户；前者不含密码，后者含密码哈希仅登录用。
- `verify_login`：校验用户名密码，通过返回用户（不含密码）。
- `update_role` / `delete`：改角色、删用户（内置 admin 即 user_id='1' 不可删）。
- `list_users`：分页用户列表（带提交数/通过数统计）。
- `create_session` / `get_session` / `delete_session` / `delete_sessions_of_user`：会话管理。
- `reset`：清空重建初始管理员。

**submission_store.py（提交记录，SQLite）**
- `SubmissionStore`：管 submissions 表。
- `create`：建一条 pending 提交。
- `update`：回写评测结果（score/counts/details 等 JSON 字段自动序列化）。
- `get` / `list`：单查 / 按 user_id、problem_id、status 条件分页查。
- `clear` / `delete_by_problem` / `delete_by_user`：清空 / 按题目级联删 / 按用户级联删。

**access_log_store.py（访问审计，SQLite）**
- `AccessLogStore`：管 access_logs 表，记录谁在什么时候以什么身份访问了哪道题的日志。
- `record`：写一条审计记录（含 user_id、problem_id、action、status）。
- `list`：按条件查审计记录。
- `clear` / `delete_by_problem` / `delete_by_user`：清空 / 级联删。

**ai_store.py（AI 配置与任务，SQLite）**
- `AIStore`：管模型配置和命题任务两张表。
- `get_config` / `set_config`：读 / 写模型配置（provider_url、model、api_key、单价）。
- `create_task` / `get_task` / `update_task`：建任务 / 查任务 / 更新任务（result、usage 自动 JSON 序列化）。
- `clear`：清空（系统重置用）。

**judge.py（评测沙箱）**
- `normalize_output(text)`：规范化输出，忽略行末空格和最后一行多余换行（避免"多了个换行"误判 WA）。
- `_compile`：编译源码，返回是否成功 + 编译信息。
- `_run_one`：跑单个测试点，返回状态、stdout、耗时、峰值内存。
- `judge`：评测入口。先编译（编译型），再逐个测试点运行并比对，汇总每个测试点的 result/time/memory，返回 score 和 details。含时间/内存限制（三级回退：题目 → 语言 → 默认）。

**llm.py（大模型调用）**
- `generate_problem`：生成题目，有真实调用和 mock 两条路径。
- `_real_generate`：调 OpenAI 兼容接口，让模型只输出题目 JSON，剥围栏后解析，返回 (题目, 用量)。
- `_mock_generate`：无密钥时返回一个结构完整的示例题。
- `new_problem_id`：给 AI 题目生成唯一 id。

**rate_limit.py（频率限制）**
- `RateLimiter`：滑动窗口计数。`check` 在窗口内计数超限时拒绝（返回 False），否则记录并放行。`_make_key` 按"单人单题"组合做 key。

**auth.py（鉴权依赖）**
- `get_current_user`：从 cookie 读 session 解析用户；未登录 401，banned 403。
- `get_admin`：在 `get_current_user` 基础上校验 admin，否则 403。

**response.py（统一响应）**
- `ok`：成功响应体 `{code:200, msg, data}`。
- `AppError`：业务异常，带 code 和 msg，由全局处理器转成 JSONResponse。
- `error_response`：构造错误响应（状态码与 code 一致）。

**language_store.py（语言配置）**
- `LanguageStore`：内置 Python/C++，支持动态注册。`list_names` 返回语言名列表，`get` 取配置，`add` 新增（校验 run_cmd 含占位符），`_save` 落盘，`clear` 重置为内置。

### 4. app/routers/ —— 路由层

**problems.py（题目，Step1）**
- `list_problems`：返回全部题目的 id + title。
- `create_problem`：新增，id 已存在 409。
- `get_problem`：题目详情。
- `update_problem`：编辑（请求体 id 须与路径一致）。
- `delete_problem`：删除（仅 admin），级联删该题提交和日志。
- `update_log_visibility`：改日志可见性（仅 admin）。

**languages.py（语言，Step2）**
- `list_languages`：语言列表（公开）。
- `register_language`：动态注册新语言（仅 admin，run_cmd 必须含 `{src}`/`{exe}`）。

**submissions.py（提交，Step2/3/5）**
- `create_submission`：提交代码。先过频率限制（429），再建 pending 记录，后台异步评测。
- `get_submission`：查单条评测结果（本人或 admin）。
- `list_submissions`：列表查询，支持 user_id / username / problem_id / status 过滤。
- `rejudge_submission`：重新评测（仅 admin），重置 pending 后异步重跑。
- `get_submission_log`：评测日志（Step5），本人 / admin / 题目公开时可见 details。
- `_judge_task`：后台任务，跑 judge 并回写。

**users.py（用户，Step4）**
- `login` / `logout`：登录（下发 session cookie）/ 登出。
- `register`：注册，默认 role=user。
- `create_admin`：建管理员（仅 admin）。
- `list_users` / `get_user`：用户列表 / 查用户信息。
- `delete_user`：删用户（仅 admin，不能删自己/其他 admin/内置 admin，级联清理）。
- `update_role`：改角色（仅 admin，不能改自己/其他 admin）。

**logs.py（日志，Step5）**
- `list_access_logs`：访问审计日志查询（仅 admin）。

**ai.py（AI 命题，Advance）**
- `get_model_config` / `set_model_config`：读 / 写模型配置（密钥打码，只显示后 4 位）。
- `create_ai_task`：建命题任务，后台异步执行。
- `_run_ai_task`：后台执行——调 LLM → 校验结果 → 加入题库 → 更新状态。
- `get_ai_task`：查任务状态/结果（创建者或 admin）。
- `cancel_ai_task`：中断任务（创建者或 admin）。
- `_authorized`：判断任务创建者或 admin；`_mask`：密钥打码。

**system.py（系统）**
- `reset_system`：系统重置，清空测试数据，重建初始 admin。

---

## 三、前端 frontend/（Streamlit）

### 1. app.py —— 入口与导航

- `main()`：总入口。未登录显示登录/注册卡片；登录后渲染顶栏（品牌 + 语言/主题切换）+ 侧边栏（用户卡 + 登出）+ 导航 pills，按选中项分发到对应 render 函数。
- `_auth_screen()`：未登录的左右分栏（品牌区 + 登录/注册表单）。
- `_prelogin_toolbar()`：登录页右上角的语言/主题切换。
- `_toggle_theme()`：主题切换的回调。

### 2. views.py —— 各页面渲染

- `_require_login()`：未登录则提示并停止。
- `_go_solve(problem_id)`：点"去做题"按钮的回调，记录待做题并切导航。
- `_problem_meta(d)`：渲染题目元信息（难度徽章 + 标签 chips）。
- `_problem_statement(d)`：渲染题面（描述/输入输出/样例/限制），题目页和做题页共用。
- `_esc(s)` / `_diff_lvl(d)`：HTML 转义 / 难度分级。
- `render_profile()`：「我的」页，本人统计 + 管理员面板。
- `_profile_admin_panel(user)`：管理员面板——用户列表（改角色/删除）、创建管理员、提交记录查询、系统重置。
- `render_problems()`：「题目」页，浏览 + 详情；admin 可增删改。
- `render_solve()`：「做题」页，左题面右编辑器，支持文件上传，下方本人提交记录 + 详情 + 重新评测。
- `render_ai()`：「AI 命题」页（仅 admin），模型配置 + 生成 + 任务状态/中断/清除记录。
- `_render_ai_result(result)`：卡片化预览 AI 生成的题目。

### 3. theme.py —— 设计系统

- `_mode()` / `current_mode()` / `_pal()`：读当前主题 / 取对应调色板（DARK/LIGHT 两套）。
- `toggle()` / `mode_label()`：切换主题 / 主题切换按钮文案。
- `inject()`：注入整套 CSS（字体、调色板、各组件覆盖），核心是把 Streamlit 真实的 testid 映射到自定义样式。
- 视觉组件：`topbar_brand`（顶栏 logo）、`hero`（页头）、`brand_panel`（登录页品牌区）、`stat_cards`（统计卡片）、`section`（区块标题）、`difficulty`（难度徽章）、`chip`（标签）、`status_badge`（状态徽章）、`code_block`（样例代码块）。

### 4. i18n.py —— 中英文案

- `_STRINGS`：全站文案字典，每个 key 有 zh/en 两版。
- `get_lang()` / `set_lang()`：读 / 写当前语言。
- `t(key, **kw)`：按当前语言取文案，支持占位符，缺失回退。
- `render_lang_bar()`：顶部语言切换按钮。

### 5. api_client.py —— HTTP 封装

- `get_session()`：共享 requests.Session，自动维护 cookie。
- `request()`：统一请求，返回 (status_code, body)。
- `login()` / `logout()`：登录 / 登出，管理前端登录态。
- `is_logged_in()` / `current_user()`：读登录态 / 当前用户。

---

## 四、两条关键链路

**提交评测链路**：做题页 `render_solve` 提交 → `api_client.request POST /api/submissions/` → 路由 `create_submission` 过限流、建 pending → `_judge_task` 异步调 `judge()` 编译运行比对 → 回写 SQLite → 前端轮询 `get_submission` 展示结果和日志。

**AI 命题链路**：AI 页 `render_ai` 提交需求 → `POST /api/ai/problem-tasks` 建任务 → `_run_ai_task` 异步调 `generate_problem`（真实或 mock）→ 校验题目 JSON → `ProblemStore.add` 入库 → 更新任务状态/用量/费用 → 前端轮询展示。

**权限贯穿**：所有写操作和敏感读操作都通过 `get_admin` / `get_current_user` 依赖鉴权；异常按 401 > 403 > 400 > 429 > 409 > 404 > 500 优先级由 `AppError` 统一抛出。
