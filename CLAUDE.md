# VocaAgent-2.0

面向大学生的 AI 职业规划平台。学生上传简历 → 5 个 LLM Agent 流水线协作（简历解析 → 岗位匹配 → 深度分析 → 职业报告 → 大佬访谈）。

## 项目知识库（Obsidian）

完整文档在 Obsidian vault，路径：

```
D:\obsidian\VocaAgent-2.0\VocaAgent-2.0\
```

| 文档 | 内容 |
|------|------|
| [[00-项目总览]] | 技术栈、目录结构、5 个 Agent 职责、启动命令 |
| [[01-架构全景图]] | Agent Pipeline 数据流、三条用户路径、核心设计约束、调用参数 |
| [[02-数据库-Schema]] | 13 张表完整 DDL、JSON 字段结构、外键关系图 |
| [[03-API-端点清单]] | 全量 API 端点（含请求格式、SSE 事件类型、done 事件字段） |
| [[04-百炼配置速查]] | APP_ID、temperature、System Prompt 要点、DashScope 调用方式 |
| [[05-已知坑点与注意事项]] | 15 条已知问题（按严重度分级：🔴严重 🟡中等 🟢低） |
| [[06-前端状态管理]] | Pinia Store（15 状态 + 14 方法）、路由表、SSE 工具、跨页面数据流 |

> **使用方式**：在 Claude Code 对话中说「打开 Obsidian 笔记」或直接让我读取该路径下的文件。笔记之间通过 `[[双向链接]]` 互相关联，在 Obsidian 中可查看图谱视图。

## 技术栈

- **后端**：Flask + MySQL (pymysql) + 阿里云百炼 DashScope（SSE 流式，`incremental_output=True`）
- **前端**：Vue 3 (Composition API) + TypeScript + Element Plus + ECharts + Pinia
- **文件处理**：PyPDF2 / pdfplumber / PyMuPDF / python-docx / pandas + xlrd
- **构建**：Vite（前端），`python app.py`（后端）

## 本地环境

- **OS**：Windows 11 Home China
- **MySQL**：`mysql -u root -p vocaagent`（密码在 `backend/.env`）
- **后端端口**：5000（`http://localhost:5000`）
- **前端端口**：5173（`http://localhost:5173`）
- **百炼配置**：API Key + 5 个 APP_ID 在 `backend/.env`，启动时自动校验

## 当前状态

- **后端**：Flask 正常运行，5 个 Agent 全部联通（Agent E 已于 2026-06-20 测试通过）
- **前端**：Vite dev 正常，全部路由就绪（含 Interview 页），Vue 3 + Element Plus + ECharts
- **数据库**：13 张表，MySQL 本地 `vocaagent`
- **待处理**：无阻塞项

## 修改日志

| 日期 | 变更 | 影响文件 | 备注 |
|------|------|---------|------|
| 2026-06-19 | Agent E 访谈功能开发完成 | `routes/agent.py`, `services/agent_orchestrator.py`, `config/settings.py`, `init_database.py`, `router/index.ts`, `views/Interview.vue` | 新增 `interview_sessions` 表，3 个 API 端点，1 个前端页面 |
| 2026-06-20 | Agent E 测试通过 | — | 全部 5 个 Agent 已联通 |
| 2026-06-20 | CLAUDE.md 重写 | `CLAUDE.md` | 4→5 Agent，10→12 表，补全 API 端点 |
| 2026-06-30 | 过时注释全面修复 | 8 个文件 | 3→5 Agent 计数修正 |
| 2026-06-30 | Agent 路由拆分 | `routes/agent.py` → 6 个文件 | 1390 行拆为 agent_utils/a/b/c/d/e.py，URL 不变，13 Blueprint |
| 2026-07-21 | 规则引擎 + 技能痛点 + Bug 修复 | `utils/skill_analyzer.py`, `routes/agent_b/c/d/e.py`, `services/agent_orchestrator.py`, 前端 Matching/JobDetail/Report | 新增规则引擎粗筛 Top10 + 技能差距注入；match_rank 错位/Agent C 加载态/Report 页修复 |
| 2026-07-25 | 偏差修正 + Obsidian 知识库建立 | `init_database.py`, `CLAUDE.md`, Obsidian vault | "14 张表"→13；建立 7 份项目知识文档；CLAUDE.md 精简（详细内容迁移至 Obsidian） |
| 2026-07-25 | populate_skills 增量模式 + 空表警告 | `utils/skill_analyzer.py`, `init_database.py` | `populate_job_skills()` 默认增量（--force 全量）；建库末尾检测空表并警告；Obsidian 笔记同步更新 |
| 2026-08-03 | Conda 环境隔离 + 启动脚本 | `backend/run.ps1`, `CLAUDE.md`, Obsidian [[00-项目总览]] | 项目改为使用 Conda 环境 `vocaagent`，不依赖全局 Python；新增 `run.ps1` 启动脚本；Obsidian 笔记同步更新 |
| 2026-10-13 | 第一批代码修复（26 项，P0–P3） | 22 个文件改动 + 3 个删除（逐条见桌面 `修复记录.md`） | 安全：密码改走请求体、改密码清 Token、3 处接口补归属校验、登出带 Token；数据：`skill_details` 落库、修正 `promotion_path` 读错、匹配写库加事务；稳定性：DBUtils 连接池、Agent A 不再回传简历原文省 token；清理：删 3 个无引用文件 |
| 2026-10-14 | 第二批修复（7 项）+ 确定只跑本地 | `utils/db.py`, `utils/auth.py`, `routes/agent_b.py`, `utils/axios.ts`, 前端 4 个 view, `CLAUDE.md`, Obsidian [[02-数据库-Schema]] + [[05-已知坑点与注意事项]] | 连接池失败不再导致应用起不来；鉴权热路径泄漏、AI 字符串分数致整批匹配不落库、401 不跳登录页等修复；**云端部署废弃，今后仅本地运行**（`app.py` 绑 `127.0.0.1` 属正确改动）。Obsidian 补 `skill_details` 字段与 20–30 条坑点。已推送 GitHub `603f665` |

## 编码约定 & Claude 规则

- **查阅文档优先** → 遇到架构/DB/API/配置/前端状态等问题，先读 `D:\obsidian\VocaAgent-2.0\VocaAgent-2.0\` 下对应笔记
- **「记住」/「保存记忆」的判断** → 项目事实（Bug、新端点、架构变更）→ 更新 Obsidian 对应笔记；个人偏好（习惯、决策理由、非代码约定）→ 写 Claude memory（`C:\Users\myqf8\.claude\projects\C--Users-myqf8\memory\`）
- **新增路由** → 同步更新 Obsidian [[03-API-端点清单]]
- **新增/改 DB 表** → 同步更新 Obsidian [[02-数据库-Schema]]，并更新 `init_database.py`
- **新增 Agent** → 同步更新 Obsidian [[00-项目总览]] + [[01-架构全景图]] + [[04-百炼配置速查]] + `settings.py` 校验
- **前端新页面** → 注册路由 (`router/index.ts`) + 更新 Obsidian [[06-前端状态管理]]
- **发现新坑** → 记录到 Obsidian [[05-已知坑点与注意事项]]
- **所有 AI 调用** → 统一走 `services/agent_orchestrator.py`
- **修改后验证** → `python app.py` 确认后端不报错；`npm run dev` 确认前端不报错
- **CLAUDE.md 自身修改** → 在修改日志里记一笔

## 开发命令

```bash
# ★ 本项目使用 Conda 环境，不依赖全局 Python
# Conda Python: C:\Users\myqf8\.conda\envs\vocaagent\python.exe

# 后端（方式一：直接调用 Conda Python）
cd backend
C:\Users\myqf8\.conda\envs\vocaagent\Scripts\pip.exe install -r requirements.txt
C:\Users\myqf8\.conda\envs\vocaagent\python.exe init_database.py              # 建库（13 张表）
C:\Users\myqf8\.conda\envs\vocaagent\python.exe init_database.py --import-excel  # 建库 + 导入岗位
C:\Users\myqf8\.conda\envs\vocaagent\python.exe init_database.py --populate-skills  # ★ 提取岗位技能
C:\Users\myqf8\.conda\envs\vocaagent\python.exe app.py                        # 启动 http://localhost:5000

# 后端（方式二：使用启动脚本）
cd backend
.\run.ps1                                      # 启动 http://localhost:5000
.\run.ps1 init_database.py                     # 建库
.\run.ps1 init_database.py --populate-skills   # 提取岗位技能

# 前端
cd frontend
npm install
npm run dev                                    # 启动 http://localhost:5173
npm run build                                  # 生产构建 → dist/

# 数据库
mysql -u root -p vocaagent
```

## 已知问题

- `routes/reports.py` 1266 行，偏胖，后续可考虑拆分
- `routes/chat.py` 系列端点标注"旧版兼容"，确认是否可以清理
- 详见 Obsidian [[05-已知坑点与注意事项]]（30 条，按严重度分级；#20 起为 2026-10 修复批次新增）
