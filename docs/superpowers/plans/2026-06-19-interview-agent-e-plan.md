# 虚拟行业大佬 1V1 深度访谈 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 Agent E（行业大佬角色扮演），学生可在独立页面与 AI 模拟的"10 年行业老炮"进行多轮对话，零成本消灭行业信息差。

**Architecture:** 在现有 4-Agent Pipeline 基础上新增 Agent E，复用了 `_call_agent()` 底层流式调用和 `job_ai_profiles` 的 Agent C 串联逻辑。对话历史通过 `interview_sessions` 表持久化，用 user_message 嵌入历史（不改 `_call_agent` 的 messages 结构）。

**Tech Stack:** Flask + MySQL (pymysql) + 阿里云百炼 DashScope + Vue 3 + TypeScript + Element Plus

**新增文件:** backend 0 个（全部在现有文件中扩展），frontend 1 个（Interview.vue）
**修改文件:** 7 个后端 + 3 个前端 = 10 个文件

---

### Task 1: 配置层 — 加 APP_ID_E

**Files:**
- Modify: `backend/.env`
- Modify: `backend/config/settings.py:44-89`

- [ ] **Step 1: 在 .env 中添加 Agent E 的 APP_ID 占位**

在 `backend/.env` 末尾追加：

```bash
# ========== Agent E：虚拟行业大佬 1v1 访谈 ==========
APP_ID_E=
```

- [ ] **Step 2: 在 settings.py 中加载 APP_ID_E 并加入启动校验**

修改 `backend/config/settings.py`：

```python
# 在 APP_ID_D 之后（第 45 行附近）添加：
# ==================== Agent E：虚拟行业大佬 1v1 访谈 ====================
APP_ID_E = os.getenv('APP_ID_E')

# 在启动校验 MISSING 块中（第 75 行附近，APP_ID_D 的 if 块之后）添加：
if not APP_ID_E:
    MISSING.append("APP_ID_E     (Agent E：虚拟行业大佬访谈)")
```

- [ ] **Step 3: 验证配置加载**

```bash
cd backend && python -c "from config.settings import APP_ID_E; print('APP_ID_E:', APP_ID_E)"
```

Expected: `APP_ID_E:` (空字符串，因为尚未配置实际 APP_ID，但不会报错，因为启动校验只在 app.py 启动时触发)

---

### Task 2: 数据库 — 加 interview_sessions 表

**Files:**
- Modify: `backend/init_database.py`

- [ ] **Step 1: 在 init_database.py 的 tables_to_drop 列表中加入新表名**

找到 `tables_to_drop` 列表（约第 33 行），在 `'job_ai_profiles'` 之前插入：

```python
tables_to_drop = [
    'resume_job_matches', 'student_job_matches',
    'resume_analyses', 'resumes',
    'career_reports', 'job_ai_profiles',
    'interview_sessions',        # ← 新增
    'students', 'jobs',
    'industries', 'user_tokens', 'users'
]
```

- [ ] **Step 2: 在 init_database.py 的 create_tables() 中添加建表语句**

找到 `job_ai_profiles` 建表语句块（约第 200 行附近，在它之后添加）：

```python
    # ===================== interview_sessions =====================
    cursor.execute("""
        CREATE TABLE interview_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            job_id INT NOT NULL,
            messages JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_student_job (student_id, job_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] interview_sessions")
```

- [ ] **Step 3: 验证建表**

```bash
cd backend && python init_database.py
```

Expected: 输出中包含 `[OK] interview_sessions`

---

### Task 3: 编排器 — 加 Agent E System Prompt + run_agent_e()

**Files:**
- Modify: `backend/services/agent_orchestrator.py`

- [ ] **Step 1: 在 __init__ 中注册 APP_ID_E**

修改 `__init__` 方法（约第 364 行），在 `self.app_ids` 字典中添加 `'E'`：

```python
def __init__(self, api_key=None):
    self.api_key = api_key or API_KEY
    self.app_ids = {
        'A': APP_ID_A,
        'B': APP_ID_B,
        'C': APP_ID_C,
        'D': APP_ID_D,
        'E': APP_ID_E,   # 新增：虚拟行业大佬 1v1 访谈
    }
```

同时更新文件顶部的 import（约第 13 行）：

```python
from config.settings import API_KEY, APP_ID_A, APP_ID_B, APP_ID_C, APP_ID_D, APP_ID_E, KNOWLEDGE_BASE_IDS
```

- [ ] **Step 2: 添加 SYSTEM_PROMPT_E**

在 `SYSTEM_PROMPT_D` 定义之后（约第 350 行附近），添加：

```python
SYSTEM_PROMPT_E = """你是一位在特定行业干了 12 年的老炮，现在是某大厂的总监，带过 30 人团队，面试过 500+ 候选人。

## 你的说话风格
- 毒舌但真诚，不画饼不灌鸡汤，说的话都是真金白银的经验
- 爱用行业黑话和真实案例，能举出具体的公司名、岗位名
- 像在烧烤摊跟后辈聊天一样接地气，不端着
- 敢于说行业潜规则和残酷真相（薪资天花板、加班文化、35岁危机、裁员套路）
- 每条回复控制在 200 字以内，不要长篇大论
- 多用"老弟/老妹"开头，营造亲切感

## 你需要了解的学生背景
用户消息中会包含学生的能力画像、目标岗位的详细信息和岗位AI画像。请根据这些信息给出针对性的、个性化的建议。

## 对话规则
1. 被问到薪资、加班、内卷、35岁危机时，如实回答不回避、不美化
2. 如果学生当前能力与岗位要求差距明显，直接指出来，但立刻给出可操作的补救建议
3. 尽量引用真实的行业数据、技术栈、公司和趋势
4. 对于学生没意识到的重要问题，可以主动点出来（比如"你问了A，但我必须提醒你B"）
5. 保持幽默感，偶尔可以自嘲（"我当年也踩过这个坑，代价是三个月的年终奖"）
"""
```

- [ ] **Step 3: 添加 run_agent_e() 方法**

在 `run_agent_d()` 方法之后（约第 709 行，`# 全局单例` 之前），添加：

```python
    # ========================================================
    # Agent E：虚拟行业大佬 1v1 访谈
    # ========================================================

    def run_agent_e(self, student_profile_json, job_info, agent_c_data, chat_history, user_message_text):
        """
        输入：
          - student_profile_json: Agent A 输出的学生画像 JSON 字符串
          - job_info: dict with id, job_name, company_name, salary_range, industry, job_description
          - agent_c_data: Agent C 输出的岗位 AI 画像 dict（或 None）
          - chat_history: list of {role, content, time}，历史对话记录
          - user_message_text: 用户当前发送的问题
        输出：SSE 流 → "行业大佬"角色的回复文本
        """
        # 构建 Agent C 数据段
        c_section = ""
        if agent_c_data:
            c_section = f"""

## 岗位 AI 画像（你对该岗位的内部分析）

**六维要求分**:
{json.dumps(agent_c_data.get('ability_requirement_scores', {}), ensure_ascii=False, indent=2)}

**晋升路径**:
{json.dumps(agent_c_data.get('vertical_promotion_info', {}), ensure_ascii=False, indent=2)}

**换岗路径**:
{json.dumps(agent_c_data.get('job_transfer_paths', []), ensure_ascii=False, indent=2)}
"""

        # 构建历史对话段
        history_section = ""
        if chat_history:
            history_section = "\n## 历史对话\n\n"
            for msg in chat_history:
                role_label = "学生" if msg['role'] == 'user' else "你"
                history_section += f"{role_label}: {msg['content']}\n\n"

        full_message = f"""## 学生能力画像

{student_profile_json}

## 目标岗位信息

岗位名称: {job_info.get('job_name', '未知')}
公司: {job_info.get('company_name', '未知')}
薪资范围: {job_info.get('salary_range', '未知')}
行业: {job_info.get('industry', '未知')}
岗位描述: {job_info.get('job_description', '暂无描述')}
{c_section}
{history_section}
## 学生最新问题

{user_message_text}

请以你"行业老炮/大厂总监"的角色，针对上面这个问题给出真实、接地气的回答。记住你的说话风格：毒舌真诚、用黑话、像烧烤摊聊天。200 字以内。"""

        return self._call_agent(
            app_id=self.app_ids['E'],
            system_prompt=SYSTEM_PROMPT_E,
            user_message=full_message,
            temperature=0.9  # 略高温度让回复更自然、更有"人味"
        )
```

- [ ] **Step 4: 验证语法**

```bash
cd backend && python -c "from services.agent_orchestrator import orchestrator; print('Agent E app_id:', orchestrator.app_ids.get('E'))"
```

Expected: `Agent E app_id:` (空或 None，因为 APP_ID_E 尚未配置)

---

### Task 4: 路由 — 加 3 个 Agent E 端点

**Files:**
- Modify: `backend/routes/agent.py`

- [ ] **Step 1: 添加 POST /api/agent/interview（SSE 流式对话端点）**

在文件末尾（约第 1066 行）添加：

```python
# ============================================================
# Agent E：虚拟行业大佬 1v1 访谈
# ============================================================

@agent_bp.route('/api/agent/interview', methods=['POST'])
def agent_interview():
    """
    输入：student_id, job_id, message
    输出：SSE 流 → "行业大佬"角色的回复文本

    请求格式（application/json）:
      {
        "student_id": 1,
        "job_id": 5,
        "message": "老哥，这行35岁后大家都去哪了？"
      }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        student_id = data.get('student_id')
        job_id = data.get('job_id')
        message = data.get('message', '').strip()

        if not student_id or not job_id:
            return jsonify({"error": "student_id 和 job_id 不能为空"}), 400
        if not message:
            return jsonify({"error": "消息不能为空"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. 查学生画像
        cursor.execute("""
            SELECT name, resume_detail_info, ability_dimension_scores,
                   ability_overall_scores, profile_completeness, competitiveness_score
            FROM students WHERE id = %s
        """, (student_id,))
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            return jsonify({"error": "学生不存在"}), 404

        student_profile = {
            "resume_detail_info": json.loads(student['resume_detail_info']) if isinstance(student['resume_detail_info'], str) else student['resume_detail_info'],
            "ability_dimension_scores": json.loads(student['ability_dimension_scores']) if isinstance(student['ability_dimension_scores'], str) else student['ability_dimension_scores'],
            "ability_overall_scores": json.loads(student['ability_overall_scores']) if isinstance(student['ability_overall_scores'], str) else student['ability_overall_scores'],
        }
        student_name = student.get('name', '未知')

        # 2. 查岗位详情
        cursor.execute("""
            SELECT id, job_name, company_name, salary_range, industry, job_description
            FROM jobs WHERE id = %s
        """, (job_id,))
        job = cursor.fetchone()
        if not job:
            cursor.close()
            conn.close()
            return jsonify({"error": "岗位不存在"}), 404

        job_info = {
            'id': job['id'],
            'job_name': job['job_name'],
            'company_name': job.get('company_name', ''),
            'salary_range': job.get('salary_range', ''),
            'industry': job.get('industry', ''),
            'job_description': job.get('job_description', ''),
        }

        # 3. 查 Agent C 岗位 AI 画像（自动串联：未命中则同步调 Agent C）
        cursor.execute("""
            SELECT ability_requirement_scores, vertical_promotion_info, job_transfer_paths
            FROM job_ai_profiles
            WHERE student_id = %s AND job_id = %s
            ORDER BY created_at DESC LIMIT 1
        """, (student_id, job_id))
        c_row = cursor.fetchone()

        agent_c_data = None
        if c_row:
            agent_c_data = {
                'ability_requirement_scores': json.loads(c_row['ability_requirement_scores']) if isinstance(c_row['ability_requirement_scores'], str) else c_row['ability_requirement_scores'],
                'vertical_promotion_info': json.loads(c_row['vertical_promotion_info']) if isinstance(c_row['vertical_promotion_info'], str) else c_row['vertical_promotion_info'],
                'job_transfer_paths': json.loads(c_row['job_transfer_paths']) if isinstance(c_row['job_transfer_paths'], str) else c_row['job_transfer_paths'],
                'job_name': job_info['job_name'],
            }
        else:
            # 自动触发 Agent C 同步版
            print(f"[Agent E] job_ai_profiles 缓存未命中 (sid={student_id}, jid={job_id})，自动调 Agent C...")
            student_profile_str = json.dumps(student_profile, ensure_ascii=False)
            c_result = orchestrator.run_agent_c_sync(job_info, student_profile_str)
            if c_result:
                agent_c_data = {
                    'ability_requirement_scores': c_result.get('ability_requirement_scores', {}),
                    'vertical_promotion_info': c_result.get('vertical_promotion_info', {}),
                    'job_transfer_paths': c_result.get('job_transfer_paths', []),
                    'job_name': job_info['job_name'],
                }
                # 入库
                try:
                    cursor.execute("""
                        INSERT INTO job_ai_profiles
                            (job_id, student_id, ability_requirement_scores,
                             vertical_promotion_info, job_transfer_paths)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            ability_requirement_scores = VALUES(ability_requirement_scores),
                            vertical_promotion_info = VALUES(vertical_promotion_info),
                            job_transfer_paths = VALUES(job_transfer_paths)
                    """, (
                        job_id, student_id,
                        json.dumps(agent_c_data['ability_requirement_scores'], ensure_ascii=False),
                        json.dumps(agent_c_data['vertical_promotion_info'], ensure_ascii=False),
                        json.dumps(agent_c_data['job_transfer_paths'], ensure_ascii=False),
                    ))
                    conn.commit()
                    print(f"[Agent E] Agent C 数据已入库 (sid={student_id}, jid={job_id})")
                except Exception as e:
                    print(f"[Agent E] Agent C 入库失败: {e}")

        # 4. 查历史对话
        cursor.execute("""
            SELECT messages FROM interview_sessions
            WHERE student_id = %s AND job_id = %s
        """, (student_id, job_id))
        session_row = cursor.fetchone()

        chat_history = []
        if session_row:
            messages_raw = session_row['messages']
            chat_history = json.loads(messages_raw) if isinstance(messages_raw, str) else messages_raw

        cursor.close()
        conn.close()

        student_profile_str = json.dumps(student_profile, ensure_ascii=False)

        def generate():
            nonlocal chat_history

            # 流式调用 Agent E
            full_response = ""
            for event in orchestrator.run_agent_e(
                student_profile_str, job_info, agent_c_data,
                chat_history, message
            ):
                if event["type"] == "chunk":
                    full_response += event["content"]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': event['content']}, ensure_ascii=False)}\n\n"
                elif event["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event['message']}, ensure_ascii=False)}\n\n"
                    return

            # 持久化：追加本轮对话到 interview_sessions
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            chat_history.append({"role": "user", "content": message, "time": now_str})
            chat_history.append({"role": "assistant", "content": full_response, "time": now_str})

            try:
                conn2 = get_db_connection()
                cur2 = conn2.cursor()
                messages_json = json.dumps(chat_history, ensure_ascii=False)
                cur2.execute("""
                    INSERT INTO interview_sessions (student_id, job_id, messages)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE messages = VALUES(messages)
                """, (student_id, job_id, messages_json))
                conn2.commit()
                cur2.close()
                conn2.close()
            except Exception as e:
                print(f"[Agent E] 对话保存失败: {e}")

            yield f"data: {json.dumps({'type': 'done', 'result': full_response}, ensure_ascii=False)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        return jsonify({"error": f"服务器内部错误：{str(e)}"}), 500
```

- [ ] **Step 2: 添加 GET /api/agent/interview/<sid>/<jid>（查历史对话）**

在 Step 1 代码之后添加：

```python
@agent_bp.route('/api/agent/interview/<int:student_id>/<int:job_id>', methods=['GET'])
def get_interview_history(student_id, job_id):
    """
    查询某学生对某岗位的历史对话记录
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, student_id, job_id, messages, created_at, updated_at
            FROM interview_sessions
            WHERE student_id = %s AND job_id = %s
        """, (student_id, job_id))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            messages_raw = row['messages']
            messages = json.loads(messages_raw) if isinstance(messages_raw, str) else messages_raw
            return jsonify({
                "exists": True,
                "session_id": row['id'],
                "student_id": row['student_id'],
                "job_id": row['job_id'],
                "messages": messages,
                "created_at": row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
                "updated_at": row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if row['updated_at'] else '',
            })
        else:
            return jsonify({
                "exists": False,
                "messages": []
            })
    except Exception as e:
        return jsonify({"error": f"查询失败：{str(e)}"}), 500
```

- [ ] **Step 3: 添加 DELETE /api/agent/interview/<sid>/<jid>（清空对话历史）**

在 Step 2 代码之后添加：

```python
@agent_bp.route('/api/agent/interview/<int:student_id>/<int:job_id>', methods=['DELETE'])
def delete_interview_history(student_id, job_id):
    """
    清空某学生对某岗位的对话历史（重新开始访谈）
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM interview_sessions
            WHERE student_id = %s AND job_id = %s
        """, (student_id, job_id))
        deleted = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "deleted": deleted > 0,
            "message": "对话历史已清空" if deleted else "没有可清空的记录"
        })
    except Exception as e:
        return jsonify({"error": f"清空失败：{str(e)}"}), 500
```

- [ ] **Step 4: 验证路由注册**

```bash
cd backend && python -c "from routes.agent import agent_bp; print([r.rule for r in agent_bp.deferred_functions if 'interview' in r.rule])"
```

---

### Task 5: 前端 — Interview.vue 新页面

**Files:**
- Create: `frontend/src/views/Interview.vue`

- [ ] **Step 1: 创建 Interview.vue**

新建 `frontend/src/views/Interview.vue`：

```vue
<template>
  <div class="interview-page">
    <!-- 顶部导航 -->
    <div class="interview-header">
      <el-button text @click="$router.back()" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <span class="header-title">虚拟行业大佬 1V1 访谈</span>
      <el-button text type="danger" size="small" @click="handleClearHistory" :disabled="messages.length === 0">
        重新开始
      </el-button>
    </div>

    <!-- 大佬人设卡 -->
    <div class="persona-card glass-panel" v-if="jobInfo">
      <div class="persona-avatar">🧓</div>
      <div class="persona-info">
        <div class="persona-name">
          行业老炮 · 大厂总监
          <span class="online-dot">🟢 在线</span>
        </div>
        <div class="persona-bio">
          "我在{{ jobInfo.industry || '互联网' }}行业干了12年，从P6爬到P9，现在带30人团队。
          关于「{{ jobInfo.job_name }}」这个岗位，想问啥直接说，别绕弯子。"
        </div>
      </div>
    </div>

    <!-- 对话区 -->
    <div class="chat-area custom-scrollbar" ref="chatAreaRef">
      <!-- 空状态 -->
      <div v-if="messages.length === 0" class="empty-chat">
        <div class="empty-icon">🚪</div>
        <p>你已敲开总监办公室的大门</p>
        <p class="empty-hint">别紧张，想问什么随便问</p>
      </div>

      <!-- 消息列表 -->
      <div v-for="(msg, idx) in messages" :key="idx"
           :class="['message-row', msg.role === 'user' ? 'user-row' : 'assistant-row']">
        <div class="message-bubble" :class="msg.role">
          <div class="message-avatar">{{ msg.role === 'user' ? '👤' : '🧓' }}</div>
          <div class="message-content">
            <div class="message-text" v-html="renderMarkdown(msg.content)"></div>
            <div class="message-time">{{ msg.time }}</div>
          </div>
        </div>
      </div>

      <!-- 流式输出中的气泡 -->
      <div v-if="streaming" class="message-row assistant-row">
        <div class="message-bubble assistant">
          <div class="message-avatar">🧓</div>
          <div class="message-content">
            <div class="message-text" v-html="renderMarkdown(streamingText)"></div>
            <span class="typing-cursor">|</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷提问 -->
    <div class="quick-questions" v-if="messages.length === 0 && !streaming">
      <span class="quick-label">💡 试试这么问：</span>
      <el-button
        v-for="q in quickQuestions"
        :key="q"
        size="small"
        class="quick-btn"
        @click="sendMessage(q)"
      >{{ q }}</el-button>
    </div>

    <!-- 输入区 -->
    <div class="input-area">
      <el-input
        v-model="inputText"
        placeholder="输入你的问题，按 Enter 发送..."
        :disabled="streaming"
        @keyup.enter="sendMessage()"
        class="message-input"
      >
        <template #append>
          <el-button
            type="primary"
            @click="sendMessage()"
            :disabled="!inputText.trim() || streaming"
            :loading="streaming"
          >
            <el-icon><Promotion /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'
import { ArrowLeft, Promotion } from '@element-plus/icons-vue'

const md = new MarkdownIt({ html: true, breaks: true, linkify: true })
import { createSSEStream } from '../utils/sse'

const route = useRoute()
const studentId = Number(route.params.student_id)
const jobId = Number(route.params.job_id)

const API_BASE = 'http://localhost:5000'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  time: string
}

const messages = ref<ChatMessage[]>([])
const inputText = ref('')
const streaming = ref(false)
const streamingText = ref('')
const chatAreaRef = ref<HTMLDivElement | null>(null)
const jobInfo = ref<any>(null)

const quickQuestions = [
  '这行新人第一年最该学什么？',
  '加班到底多严重？说实话',
  '做几年跳槽性价比最高？',
]

function getToken(): string | null {
  return localStorage.getItem('token')
}

async function loadData() {
  // 加载历史对话
  try {
    const headers: Record<string, string> = {}
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`

    const res = await fetch(`${API_BASE}/api/agent/interview/${studentId}/${jobId}`, { headers })
    const data = await res.json()
    if (data.exists && data.messages) {
      messages.value = data.messages
    }
  } catch (e) {
    console.error('加载历史对话失败:', e)
  }

  // 加载岗位信息
  try {
    const headers: Record<string, string> = {}
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`

    const res = await fetch(`${API_BASE}/api/jobs/${jobId}`, { headers })
    if (res.ok) {
      jobInfo.value = await res.json()
    }
  } catch (e) {
    console.error('加载岗位信息失败:', e)
  }
}

function sendMessage(text?: string) {
  const msg = (text || inputText.value).trim()
  if (!msg || streaming.value || !studentId || !jobId) return

  inputText.value = ''
  streaming.value = true
  streamingText.value = ''

  messages.value.push({
    role: 'user',
    content: msg,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
  })

  scrollToBottom()

  createSSEStream('/api/agent/interview', {
    student_id: studentId,
    job_id: jobId,
    message: msg,
  }, {
    onChunk: (chunk) => {
      streamingText.value += chunk
      scrollToBottom()
    },
    onDone: (fullText) => {
      messages.value.push({
        role: 'assistant',
        content: fullText,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      })
      streamingText.value = ''
      streaming.value = false
      scrollToBottom()
    },
    onError: (err) => {
      console.error('Agent E 调用失败:', err)
      messages.value.push({
        role: 'assistant',
        content: '🙇 抱歉老弟，刚才走神了。你再说一遍？',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      })
      streamingText.value = ''
      streaming.value = false
    },
  })
}

async function handleClearHistory() {
  try {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const token = getToken()
    if (token) headers['Authorization'] = `Bearer ${token}`

    await fetch(`${API_BASE}/api/agent/interview/${studentId}/${jobId}`, {
      method: 'DELETE',
      headers,
    })
    messages.value = []
  } catch (e) {
    console.error('清空失败:', e)
  }
}

function renderMarkdown(text: string): string {
  if (!text) return ''
  return md.render(text)
}

function scrollToBottom() {
  nextTick(() => {
    if (chatAreaRef.value) {
      chatAreaRef.value.scrollTop = chatAreaRef.value.scrollHeight
    }
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.interview-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
}

.interview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.header-title {
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* 人设卡 */
.persona-card {
  display: flex;
  gap: 16px;
  padding: 20px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(102,126,234,0.1), rgba(118,75,162,0.1));
  border: 1px solid rgba(102,126,234,0.2);
  margin-bottom: 16px;
}

.persona-avatar {
  font-size: 48px;
  line-height: 1;
}

.persona-name {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 8px;
}

.online-dot {
  font-size: 12px;
  margin-left: 8px;
  color: #67c23a;
}

.persona-bio {
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
  font-style: italic;
}

/* 对话区 */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 0;
  margin-bottom: 12px;
}

.empty-chat {
  text-align: center;
  padding: 60px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-hint {
  font-size: 13px;
  margin-top: 8px;
}

/* 消息气泡 */
.message-row {
  margin-bottom: 16px;
}

.message-bubble {
  display: flex;
  gap: 10px;
  max-width: 85%;
}

.user-row .message-bubble {
  margin-left: auto;
  flex-direction: row-reverse;
}

.message-avatar {
  font-size: 28px;
  flex-shrink: 0;
}

.message-content {
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 16px;
  border-top-left-radius: 4px;
}

.user-row .message-content {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-radius: 16px;
  border-top-right-radius: 4px;
}

.message-text {
  font-size: 14px;
  line-height: 1.7;
}

.user-row .message-text {
  color: #fff;
}

.message-time {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 4px;
}

.user-row .message-time {
  color: rgba(255,255,255,0.7);
}

/* 打字光标 */
.typing-cursor {
  animation: blink 1s infinite;
  color: #764ba2;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 快捷问题 */
.quick-questions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.quick-label {
  font-size: 13px;
  color: #909399;
  white-space: nowrap;
}

.quick-btn {
  font-size: 12px;
  border-radius: 20px;
}

/* 输入区 */
.input-area {
  padding-bottom: 8px;
}

.message-input :deep(.el-input__wrapper) {
  border-radius: 24px;
}

/* Markdown 渲染样式 */
.message-text :deep(p) {
  margin: 4px 0;
}
.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 4px 0;
  padding-left: 20px;
}
.message-text :deep(code) {
  background: rgba(0,0,0,0.06);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 13px;
}
.message-text :deep(strong) {
  font-weight: 700;
}
.message-text :deep(blockquote) {
  border-left: 3px solid #667eea;
  padding-left: 12px;
  margin: 8px 0;
  color: #606266;
}

/* 滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}
</style>
```

- [ ] **Step 2: 验证文件语法**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1 | grep -i "Interview" || echo "No Interview.vue specific errors"
```

（允许已存在的项目级类型错误，只关注 Interview.vue 相关的错误）

---

### Task 6: 前端 — 加路由

**Files:**
- Modify: `frontend/src/router/index.ts`

- [ ] **Step 1: 在路由表中添加 Interview 路由**

在 `frontend/src/router/index.ts` 的 routes 数组中，`/report/:id` 路由之后（约第 62 行）添加：

```typescript
    {
      path: '/interview/:student_id/:job_id',
      name: 'Interview',
      component: () => import('../views/Interview.vue'),
      meta: { requiresAuth: true }
    },
```

- [ ] **Step 2: 验证路由**

```bash
cd frontend && npx vue-tsc --noEmit 2>&1 | grep -i "interview" || echo "No interview-related errors"
```

---

### Task 7: 前端 — JobDetail 页加入口按钮

**Files:**
- Modify: `frontend/src/views/JobDetail.vue`

- [ ] **Step 1: 在岗位名称下方添加入口按钮**

在 `JobDetail.vue` 中找到岗位标题区域（岗位名字附近），在合适位置添加按钮。查找模板中岗位名的渲染位置，在其后添加：

```vue
<el-button
  type="warning"
  size="large"
  class="interview-entry-btn"
  @click="$router.push(`/interview/${studentId}/${jobId}`)"
>
  🚪 敲总监办公室大门
</el-button>
```

其中 `studentId` 需要从当前页面已有的 store/props 中获取。检查 JobDetail.vue 是否已有 `studentId` 变量——如果有，直接使用；如果没有，从 `route.query` 或 store 中获取：

```typescript
// 在 <script setup> 中添加（如果尚不存在）：
import { useAgentPipelineStore } from '../stores/agentPipeline'
const pipelineStore = useAgentPipelineStore()
const studentId = pipelineStore.currentStudentId || route.query.student_id
const jobId = Number(route.params.id)
```

- [ ] **Step 2: 添加按钮样式**

在 `<style scoped>` 中添加：

```css
.interview-entry-btn {
  margin-top: 12px;
  border-radius: 24px;
  font-weight: 600;
}
```

---

### Task 8: 前端 — Matching 页加入口按钮

**Files:**
- Modify: `frontend/src/views/Matching.vue`

- [ ] **Step 1: 在每张岗位卡片上添加入口**

在 `Matching.vue` 中找到岗位卡片模板的循环体，在卡片底部操作区（可能在 `is_favorite` 按钮附近）添加小型入口：

```vue
<el-button
  text
  size="small"
  type="warning"
  class="interview-card-btn"
  @click="$router.push(`/interview/${studentId}/${job.id}`)"
>
  💬 问大佬
</el-button>
```

其中 `studentId` 从 store/props 获取，`job.id` 来自卡片循环变量。Matching.vue 中通常已有 `pipelineStore.currentStudentId` 或从 route 传入的 `student_id`。

- [ ] **Step 2: 检查 Matching.vue 是否已有 studentId**

在 Matching.vue 的 `<script setup>` 中搜索 `studentId` 或 `student_id`。如果没有，从 store 或 route 中获取：

```typescript
import { useRoute } from 'vue-router'
const route = useRoute()
const studentId = route.query.student_id || pipelineStore.currentStudentId
```

---

### Task 9: 集成测试 — 端到端验证

- [ ] **Step 1: 启动后端**

```bash
cd backend && python app.py
```

Expected: Flask 启动在 `http://localhost:5000`，无报错，无 APP_ID_E 相关的 MISSING 警告（如果 APP_ID_E 未填，启动校验会拦截，此时可先填入临时值如 `test`）

- [ ] **Step 2: 测试 GET 查历史（空状态）**

```bash
curl -s http://localhost:5000/api/agent/interview/1/1 | python -m json.tool
```

Expected: `{"exists": false, "messages": []}`

- [ ] **Step 3: 测试 DELETE**

```bash
curl -s -X DELETE http://localhost:5000/api/agent/interview/1/1 | python -m json.tool
```

Expected: `{"success": true, "deleted": false, "message": "没有可清空的记录"}`

- [ ] **Step 4: 启动前端**

```bash
cd frontend && npm run dev
```

Expected: Vite 启动在 `http://localhost:5173`

- [ ] **Step 5: 手动端到端测试**

1. 浏览器打开 `http://localhost:5173/login`，登录
2. 上传简历 → 生成画像 → 进入 Matching 页
3. 在 Matching 页点击岗位卡片上的 "💬 问大佬" 按钮 → 跳转到 `/interview/:sid/:jid`
4. 验证：大佬人设卡显示正确、快捷问题显示
5. 输入问题发送 → 验证 SSE 流式输出
6. 多轮对话 → 验证历史记录加载（刷新页面后对话仍在）
7. 点 "重新开始" → 验证清空

---

### Task 10: 百炼平台 — 创建 Agent E App

**注：此任务需要在阿里云百炼控制台手动操作**

- [ ] **Step 1: 登录百炼控制台** → 应用管理 → 创建新应用
- [ ] **Step 2: 将 `SYSTEM_PROMPT_E`（来自 Task 3 Step 2）粘贴到应用配置的 System Prompt 字段**
- [ ] **Step 3: 模型选择**：推荐 `qwen-plus` 或 `qwen-max`（需要较好的角色扮演能力）
- [ ] **Step 4: 获取 APP_ID，填入 `backend/.env` 的 `APP_ID_E=`**

---

## 文件变更总览

| 文件 | 操作 | 行数 |
|------|------|------|
| `backend/.env` | 加 3 行 | +3 |
| `backend/config/settings.py` | 加 4 行 | +4 |
| `backend/init_database.py` | 加 1 个表名 + 12 行 SQL | +13 |
| `backend/services/agent_orchestrator.py` | 加 import + dict + System Prompt + run_agent_e() | +100 |
| `backend/routes/agent.py` | 加 3 个端点 | +200 |
| `frontend/src/views/Interview.vue` | **新建** | +280 |
| `frontend/src/router/index.ts` | 加 1 条路由 | +6 |
| `frontend/src/views/JobDetail.vue` | 加按钮 + 样式 | +15 |
| `frontend/src/views/Matching.vue` | 加按钮 | +10 |
| **合计** | 9 改 + 1 新 | ~630 行 |
