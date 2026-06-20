# VocaAgent-2.0

## 4-Agent Pipeline 架构

```
Agent A (简历解析→学生能力画像)
    │
    ▼
Agent B (10岗位匹配分：id + 4维度分 + 综合分)  ← 轻量，必跑
    │
    ├──→ 用户点击某岗位卡片 →
    │       Agent C (单岗位画像：6维要求分 + 晋升路径 + 换岗路径)  ← 按需触发（前端 JobDetail 页）
    │            │
    │            ├── 查DB有？→ 直接返回 (per student×job)
    │            └── 无 → 调AI → 入库 → 返回
    │
    ├────────────────────┼──────────────────→ Agent D (职业报告HTML)
    │                    │                      前置：A+B 必须存在
    │                    │                      ★ Agent D 内部自动串联 Agent C：
    │                    │                         ① 查 job_ai_profiles 缓存
    │                    │                         ② 未命中 → 自动调 Agent C → 入库
    │                    │                         ③ 将 C 数据注入 D 的 prompt（6维要求分对比、晋升路径、换岗方案）
    A────────────────────┘
```

## 四个 Agent 职责

| Agent | 作用 | 百炼 APP_ID |
|-------|------|-------------|
| **A** | 简历→学生能力画像 JSON（基本信息 + 6维能力分 + 完整度/竞争力） | `your-app-id-a` |
| **B** | 画像→10岗位匹配分（只返回id + 4项维度分 + 综合分） | `your-app-id-b` |
| **C** | 单岗位详细画像（6维要求分 + 晋升 + 换岗），按需触发，per student×job 缓存 | `your-app-id-c` |
| **D** | 画像 + 匹配分 → HTML 职业报告（内部自动串联 Agent C） | `your-app-id-d` |

- API Key 统一：在 `backend/.env` 中配置 `API_KEY`

## 核心约束

- **Agent B 只输出匹配分**，不输出 6维要求分/晋升/换岗（瘦身，快速响应）
- **Agent C 双重触发**：① 用户点击 JobDetail 时触发（前端）② Agent D 生成报告时自动触发（后端内部，对用户透明）
- **Agent C DB 缓存 per student×job**：`job_ai_profiles` 表，UNIQUE KEY `unique_student_job(student_id, job_id)`，不同学生同一岗位分析不同；Agent D 优先读缓存，避免重复调用
- **Agent D 前置**：A+B 必须存在；C 自动串联（先查缓存 → 未命中则调 AI → 入库 → 注入 D 的 prompt）
- **按钮交互**：Matching/Report 页都是「先查 DB → 有则展示 → 无则弹窗确认是否调 AI」
- **Agent D 报告润色**：报告生成后可调 `/api/reports/<id>/polish` 进行 AI 润色优化

## 技术栈

- **后端**：Flask + MySQL (pymysql) + 阿里云百炼 DashScope
- **前端**：Vue 3 (Composition API) + TypeScript + Element Plus + ECharts + Pinia
- **AI**：DashScope Application API（SSE 流式，`incremental_output=True`）
- **文件处理**：PyPDF2 / python-docx（本地提取文字后发给 Agent）
- **构建**：Vite（前端），python app.py（后端直接运行）

---

## 后端结构

```
backend/
├── app.py                          # Flask 主入口（极薄：CORS + 上传配置 + 注册路由）
├── .env                            # 环境变量（API_KEY + 4 个 APP_ID + 知识库）
├── requirements.txt                # Python 依赖
├── init_database.py                # 一键建库脚本：10 张表 + Excel 导入
├── config/
│   └── settings.py                 # 配置中心（DB / 文件上传 / API Key / APP_ID）
├── routes/
│   ├── __init__.py                 # 注册 8 个 Blueprint
│   ├── agent.py                    # ★ 4-Agent SSE 端点 + DB 查询端点（1066 行）
│   ├── auth.py                     # 注册/登录/登出/个人信息
│   ├── students.py                 # 学生管理 + 简历解析 + 匹配查询
│   ├── jobs.py                     # 岗位列表/搜索/详情/行业
│   ├── reports.py                  # 报告 CRUD + 导出 PDF/Word + 润色（1266 行）
│   ├── resumes.py                  # 简历上传/分析/管理
│   ├── admin.py                    # 用户管理 CRUD
│   └── chat.py                     # 通用对话 + 客服对话（旧版兼容）
├── services/
│   ├── agent_orchestrator.py       # ★ Agent 编排器：4 个 System Prompt + 流式调用 + C 同步版（718 行）
│   └── resume_parser.py            # 简历解析结果入库
└── utils/
    ├── db.py                       # 数据库连接池
    ├── auth.py                     # Token 认证 (get_current_user)
    └── file_processor.py           # 文件类型检测 + 内容提取（PDF/Word/TXT）
```

## 前端结构

```
frontend/
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
├── src/
│   ├── main.ts                     # 入口：注册 Element Plus / Pinia / Router
│   ├── App.vue                     # 根组件（动态光晕背景 + 导航 + 路由出口）
│   ├── style.css                   # 全局样式
│   ├── router/
│   │   └── index.ts                # 路由配置 + 守卫（认证 + 管理员）
│   ├── stores/
│   │   ├── index.ts                # Store 入口
│   │   ├── user.ts                 # 用户状态（登录/Token/权限）
│   │   └── agentPipeline.ts        # ★ Agent Pipeline 数据总线（跨页面共享画像/匹配/报告）
│   ├── utils/
│   │   ├── axios.ts                # Axios 封装（自动带 Token）
│   │   ├── sse.ts                  # ★ SSE 流式读取工具
│   │   ├── chinesePdf.ts           # PDF 中文字体
│   │   └── pdfFont.ts              # PDF 字体配置
│   └── views/
│       ├── Home.vue                # 首页（AI 对话 + 简历上传 + PDF 导出）
│       ├── Login.vue               # 登录页
│       ├── Profile.vue             # ★ 我的能力画像（Agent A 输出：雷达图 + 技能标签 + 时间线）
│       ├── Jobs.vue                # 岗位列表（卡片网格）
│       ├── JobDetail.vue           # ★ 岗位详情（Agent C 触发：雷达图 + 晋升阶梯 + 换岗关系图）
│       ├── JobExplore.vue          # 岗位探索
│       ├── Matching.vue            # ★ 人岗匹配（Agent B 流式渐进渲染 + 维度进度条）
│       ├── Report.vue              # ★ 职业报告列表
│       ├── ReportDetail.vue        # ★ 报告详情（Agent D v-html 渲染 + PDF 导出 + 润色）
│       ├── Admin.vue               # 管理后台
│       └── AccuracyEvaluation.vue  # AI 准确性评估（隐藏页，未注册路由）
├── public/
│   ├── tubiao.jpg                  # Logo
│   ├── beijingtu.jpg               # 背景图
│   ├── customer-service-avatar.jpg
│   └── user-avatar.jpg
└── dist/                           # 构建产物（npm run build）
```

---

## API 端点

### Agent Pipeline（核心）— Blueprint: `agent`

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/agent/profile` | Agent A SSE — 简历解析→学生画像（multipart 或 JSON） |
| `POST` | `/api/agent/match` | Agent B SSE — 画像→10 岗位匹配分 |
| `POST` | `/api/agent/job-profile` | Agent C SSE — 单岗位 AI 画像（6维要求分 + 晋升 + 换岗） |
| `POST` | `/api/agent/report` | Agent D SSE — 生成 HTML 职业报告 |
| `GET` | `/api/agent/match/<student_id>` | 查匹配结果缓存（`student_job_matches` 表） |
| `GET` | `/api/agent/job-profile/<student_id>/<job_id>` | 查岗位 AI 画像缓存（`job_ai_profiles` 表） |
| `GET` | `/api/agent/report/<student_id>` | 查报告缓存（支持 `?job_id=` 过滤） |

### 认证 — Blueprint: `auth`

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/auth/register` | 用户注册 |
| `POST` | `/api/auth/login` | 用户登录 → 返回 Token |
| `POST` | `/api/auth/logout` | 用户登出 |
| `GET` | `/api/auth/user` | 获取当前用户信息 |
| `PUT` | `/api/auth/profile` | 修改个人信息 |

### 岗位 — Blueprint: `jobs`

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/jobs/list` | 岗位列表（分页 + 行业/搜索筛选） |
| `GET` | `/api/jobs/search` | 岗位搜索 |
| `GET` | `/api/jobs/industries` | 行业列表 |
| `GET` | `/api/jobs/<job_id>` | 岗位详情（含静态数据：名称/公司/薪资/描述） |
| `GET` | `/api/students/<student_id>/matches/<match_rank>/job` | 根据匹配排名查岗位 |

### 学生 — Blueprint: `students`

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/parse-resume` | 旧版简历解析（兼容） |
| `GET` | `/api/students/list` | 学生列表 |
| `GET` | `/api/students/current` | 当前用户的学生画像 |
| `GET` | `/api/students/<student_id>/profile` | 学生完整能力画像（含 Agent A 输出） |
| `GET` | `/api/students/<student_id>/matches` | 学生匹配结果列表 |
| `GET` | `/api/students/<student_id>/improvement-suggestions` | 提升建议 |
| `DELETE` | `/api/students/<student_id>` | 删除学生 |

### 报告 — Blueprint: `reports`

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/reports/generate` | 生成报告（旧版兼容） |
| `GET` | `/api/reports/<report_id>` | 获取报告详情 |
| `GET` | `/api/reports/student/<student_id>` | 按学生查报告列表 |
| `DELETE` | `/api/reports/<report_id>` | 删除报告 |
| `POST` | `/api/reports/<report_id>/export` | 导出报告 |
| `GET` | `/api/reports/<report_id>/download` | 下载报告（Word/PDF） |
| `GET` | `/api/reports/<report_id>/download/pdf` | 下载 PDF |
| `POST` | `/api/reports/<report_id>/polish` | ★ AI 润色报告（Agent D 输出后优化） |

### 简历 — Blueprint: `resumes`

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/resumes/upload` | 上传简历文件 |
| `GET` | `/api/resumes` | 简历列表 |
| `GET` | `/api/resumes/<resume_id>` | 简历详情 |
| `POST` | `/api/resumes/<resume_id>/analyze` | AI 分析简历 |
| `GET` | `/api/resumes/analyses` | 分析记录列表 |
| `GET` | `/api/resumes/analyses/<analysis_id>` | 分析记录详情 |
| `DELETE` | `/api/resumes/<resume_id>` | 删除简历 |
| `PUT` | `/api/resumes/<resume_id>/default` | 设为默认简历 |

### 管理 — Blueprint: `admin`

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/admin/users` | 用户列表 |
| `POST` | `/api/admin/users` | 创建用户 |
| `PUT` | `/api/admin/users/<user_id>` | 修改用户 |
| `PUT` | `/api/admin/users/<user_id>/password` | 修改密码 |
| `DELETE` | `/api/admin/users/<user_id>` | 删除用户 |

### 通用 — Blueprint: `chat`

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 |
| `POST` | `/api/chat` | 通用 AI 对话（旧版兼容） |
| `POST` | `/api/chat/customer-service` | 客服对话（旧版兼容，暂未配置） |

---

## 数据库（10 张表）

| 表名 | 说明 | 关键字段 |
|------|------|----------|
| `users` | 用户表 | id, username, password, email, role(admin/user) |
| `user_tokens` | 登录令牌 | user_id → users.id, token, expires_at |
| `students` | 学生画像（Agent A 输出持久化） | 基本信息 + 6维能力分 + 完整度/竞争力 + resume_text |
| `jobs` | 岗位表（Excel 导入） | job_name, company_name, salary_range, industry, 6维要求分(int), job_description |
| `career_reports` | 职业报告（Agent D 输出） | student_id, target_job_id, report_html |
| `job_ai_profiles` | ★ Agent C 缓存（per student×job） | job_id, student_id, ability_requirement_scores(JSON), vertical_promotion_info(JSON), job_transfer_paths(JSON), UNIQUE(student_id, job_id) |
| `student_job_matches` | Agent B 匹配结果持久化 | job_id, student_id, match_rank, 5维匹配分, is_favorite |
| `industries` | 行业字典 | industry_name (UNIQUE) |
| `resumes` | 简历文件管理 | user_id, original_filename, file_path, resume_text, is_default |
| `resume_analyses` | 简历 AI 分析记录 | resume_id, analysis_type, analysis_content(JSON), ability_scores(JSON) |
| `resume_job_matches` | 简历-岗位匹配记录 | resume_id, job_id, match_score, UNIQUE(resume_id, job_id) |

---

## 数据流（完整链条）

```
1. 用户上传简历 PDF → 后端 file_processor 提取文字
2. POST /api/agent/profile (Agent A SSE) → 流式返回学生画像 JSON
3. 画像入库 students 表 → 前端跳转 Matching 页
4. POST /api/agent/match (Agent B SSE) → 后端从 MySQL jobs 表拼岗位描述进 Prompt
   → 流式返回 10 个 {id + 匹配分} → 前端逐 ID 查 /api/jobs/<id> 渲染卡片
5. 用户点击某岗位卡片 → 前端调 GET /api/agent/job-profile/<sid>/<jid> 查缓存
   → 有则直接渲染；无则 POST /api/agent/job-profile (Agent C SSE) → 入库 → 返回
6. 用户点击「生成报告」→ POST /api/agent/report (Agent D SSE)
   → 后端内部：查 job_ai_profiles → 未命中调 Agent C 同步版 → 入库
   → 将 C 数据注入 D 的 Prompt → 流式返回 HTML → 前端 v-html 渲染
7. 可选：POST /api/reports/<id>/polish → AI 润色优化报告
```

## 开发命令

```bash
# 后端
cd backend
pip install -r requirements.txt      # 安装依赖
python init_database.py               # 一键建库 + Excel 导入
python app.py                         # 启动 Flask (http://localhost:5000)

# 前端
cd frontend
npm install                           # 安装依赖
npm run dev                           # 启动 Vite (http://localhost:5173)
npm run build                         # 生产构建 → dist/

# 数据库
mysql -u root -p vocaagent             # 连接本地 MySQL
```
