<template>
  <div class="interview-page">
    <!-- 顶部导航 -->
    <div class="interview-header">
      <el-button text @click="$router.back()" class="back-btn">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <span class="header-title">虚拟行业大佬 1V1 访谈</span>
      <el-button text type="danger" size="small" @click="handleClearHistory" :disabled="messages.length === 0 || streaming">
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
      <div v-if="messages.length === 0 && !streaming" class="empty-chat">
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
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import MarkdownIt from 'markdown-it'
import { ArrowLeft, Promotion } from '@element-plus/icons-vue'
import { createSSEStream } from '../utils/sse'
import { useAgentPipeline } from '../stores/agentPipeline'

const pipeline = useAgentPipeline()

const md = new MarkdownIt({ html: true, breaks: true, linkify: true })

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
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) headers['Authorization'] = `Bearer ${token}`

  // 加载历史对话
  try {
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
    student_profile: pipeline.profile,
  }, {
    onChunk: (chunk: string) => {
      streamingText.value += chunk
      scrollToBottom()
    },
    onDone: (fullText: string) => {
      messages.value.push({
        role: 'assistant',
        content: fullText,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      })
      streamingText.value = ''
      streaming.value = false
      scrollToBottom()
    },
    onError: (err: string) => {
      console.error('Agent E 调用失败:', err)
      messages.value.push({
        role: 'assistant',
        content: '🙇 抱歉老弟，刚才走神了。你再说一遍？',
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
      })
      streamingText.value = ''
      streaming.value = false
    },
    onEvent: (event: any) => {
      if (event.type === 'reset') {
        messages.value = []
        streamingText.value = ''
        console.log('[Interview] 对话已达50轮上限，已自动重置')
      }
    },
  })
}

async function handleClearHistory() {
  try {
    const headers: Record<string, string> = {}
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
  background-clip: text;
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
  flex-shrink: 0;
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
  background: #667eea;
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
  flex-shrink: 0;
}

.message-input :deep(.el-input__wrapper) {
  border-radius: 24px;
  background: #f5f7fa !important;
  box-shadow: none !important;
}
.message-input :deep(.el-input__inner) {
  background: #f5f7fa !important;
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
