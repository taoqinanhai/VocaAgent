# 虚拟行业大佬 1V1 深度访谈 — 设计文档

**日期**: 2026-06-19
**状态**: 已确认

---

## 一、功能概述

新增 **Agent E**（行业大佬角色扮演），让学生可以在独立页面与 AI 模拟的"10 年行业老炮/大厂总监"进行多轮对话，零成本消灭行业信息差。

---

## 二、架构总览

```
Agent E (新增百炼 App，专属 Role-play Prompt)
  ↑ SSE 流式
/api/agent/interview (新端点)
  ↑ 上下文注入：Agent A 画像 + 岗位详情 + Agent C 画像 + 对话历史
interview_sessions 表 (新增，per student×job)
```

**变更范围：**
- 百炼：新增 1 个 Agent App (Agent E)
- 后端：`agent_orchestrator.py` + `routes/agent.py` + `init_database.py`
- 前端：新页面 `Interview.vue` + 路由 + 2 处入口按钮
- DB：新增 `interview_sessions` 表

---

## 三、Agent E System Prompt

角色：在目标行业干了 12 年的老炮/大厂总监
风格：毒舌真诚、爱用黑话、烧烤摊聊天感、敢于说潜规则

上下文注入：
- 学生画像（Agent A 输出的 6 维能力分 + 完整度/竞争力）
- 岗位基本信息（名称、公司、薪资、JD）
- 岗位 AI 画像（Agent C 输出的 6 维要求分 + 晋升路径 + 换岗路径）

对话规则：
1. 每条回复 200 字以内
2. 多用"老弟/老妹"
3. 薪资/加班/35 岁危机如实回答
4. 能力差距直接指出并给补救建议

---

## 四、数据库

```sql
CREATE TABLE interview_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    job_id INT NOT NULL,
    messages JSON NOT NULL DEFAULT '[]',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_student_job (student_id, job_id),
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
);
```

messages 格式：`[{"role":"user|assistant","content":"...","time":"ISO8601"}, ...]`

---

## 五、API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| `POST` | `/api/agent/interview` | Agent E SSE — 发送问题，流式返回 |
| `GET` | `/api/agent/interview/<sid>/<jid>` | 查询历史对话 |
| `DELETE` | `/api/agent/interview/<sid>/<jid>` | 清空对话历史 |

**POST 请求体：** `{ "student_id": 1, "job_id": 5, "message": "..." }`

---

## 六、数据流

```
① 前端 POST /api/agent/interview
② 查 students 表 → 学生画像
③ 查 jobs 表 → 岗位详情
④ 查 job_ai_profiles → 命中？跳过；未命中？调 Agent C 同步版 → 入库
⑤ 查 interview_sessions → 获取历史对话
⑥ 拼装 Prompt → 调百炼 Agent E SSE → 流式返回
⑦ 本轮问答追加写入 interview_sessions.messages
```

---

## 七、前端页面 Interview.vue

路由：`/interview/:student_id/:job_id`

布局：
- 顶部：大佬人设卡（头像 + 自我介绍 + 🟢在线）
- 中部：聊天区（SSE 流式 Markdown，自动滚底）
- 快捷提问：3 个预置问题按钮
- 底部：输入框 + 发送按钮

入口：
- JobDetail 页：`🚪 敲总监办公室大门` 按钮
- Matching 页：每张岗位卡片 `💬 问大佬` 图标
