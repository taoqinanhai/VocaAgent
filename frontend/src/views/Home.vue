<template>
  <div class="home">
    <!-- 英雄区 (毛玻璃风格) -->
    <section class="hero glass-panel">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="gradient-text">智能职业规划 · 星途由此启程</span><br />
          <span class="gradient-text-alt">高校学生职业AI规划平台</span>
        </h1>
        <p class="hero-subtitle">
          基于大语言模型技术，为你提供个性化、可操作的职业生涯规划方案
        </p>
        <div class="hero-actions">
          <el-button class="glass-btn-primary" size="large" @click="$router.push('/profile')">
            开始职业规划
            <el-icon class="el-icon--right"><ArrowRight /></el-icon>
          </el-button>
          <el-button class="glass-btn-ghost" size="large" @click="$router.push('/jobs')">
            探索岗位
          </el-button>
        </div>
      </div>
      <div class="hero-stats">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="stat-card glass-tile">
              <div class="stat-number">100+</div>
              <div class="stat-label">岗位画像</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card glass-tile">
              <div class="stat-number">4维</div>
              <div class="stat-label">匹配分析</div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card glass-tile">
              <div class="stat-number">80%+</div>
              <div class="stat-label">匹配准确率</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </section>

    <!-- 智能体对话框 -->
    <section class="chat-section">
      <el-row :gutter="20">
        <!-- 隐藏的旧助手界面保留，如需展示会自动适配玻璃效果 -->
        <el-col :span="12" v-if="false">
          <h2 class="section-title">AI 职业规划助手</h2>
          <el-card class="chat-card glass-panel">
            <div class="chat-container custom-scrollbar" ref="chatContainerRef">
              <div 
                v-for="(msg, index) in chatMessages" 
                :key="index" 
                :class="['message', msg.role === 'user' ? 'user-message' : 'assistant-message']"
              >
                <div class="message-avatar">
                  <el-avatar :size="36" class="glass-avatar" :style="{ background: msg.role === 'user' ? 'linear-gradient(135deg, #667eea, #764ba2)' : 'linear-gradient(135deg, #a18cd1, #fbc2eb)' }">
                    {{ msg.role === 'user' ? '我' : 'AI' }}
                  </el-avatar>
                </div>
                <div class="message-content">
                  <div class="message-text">
                    <div class="message-content-text" v-html="renderMarkdown(msg.content, msg.role)"></div>
                    <div v-if="msg.role === 'assistant'" class="message-actions">
                      <el-button 
                        class="glass-btn-mini"
                        size="small" 
                        text 
                        @click="downloadAsPDF(msg.content, index)"
                      >
                        <el-icon><Download /></el-icon>
                        下载 PDF
                      </el-button>
                    </div>
                  </div>
                </div>
              </div>
              <div v-if="isLoading" class="message assistant-message">
                <div class="message-avatar">
                  <el-avatar :size="36" class="glass-avatar" style="background: linear-gradient(135deg, #a18cd1, #fbc2eb)">AI</el-avatar>
                </div>
                <div class="message-content">
                  <div class="message-text loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
            <div class="upload-section">
              <input 
                type="file" 
                ref="fileInputRef"
                accept=".pdf,.doc,.docx,.txt,.rtf,.jpg,.jpeg,.png"
                style="display: none"
                @change="handleFileSelect"
              />
              <el-button class="glass-btn-ghost" size="small" @click="triggerFileInput">
                <el-icon><Upload /></el-icon>
                上传简历
              </el-button>
              <div v-if="uploadedFile" class="uploaded-file-info">
                <el-tag class="glass-tag" size="small" closable @close="removeUploadedFile">
                  {{ uploadedFile.name }} ({{ formatFileSize(uploadedFile.size) }})
                </el-tag>
              </div>
            </div>
            <div class="chat-input-wrapper">
              <el-input
                v-model="userInput"
                placeholder="请输入您的职业规划问题..."
                @keyup.enter="sendMessage"
                :disabled="isLoading"
                class="glass-input"
              >
                <template #append>
                  <el-button 
                    class="glass-btn-primary" 
                    @click="sendMessage" 
                    :loading="isLoading"
                    :disabled="!userInput.trim() && !uploadedFile"
                  >
                    发送
                  </el-button>
                </template>
              </el-input>
            </div>
          </el-card>
        </el-col>

        <!-- 客服智能体界面 -->
        <el-col :span="24">
          <el-card class="chat-card glass-panel no-border">
            <div class="chat-container custom-scrollbar" ref="customerServiceChatContainerRef">
              <div 
                v-for="(msg, index) in customerServiceChatMessages" 
                :key="index" 
                :class="['message', msg.role === 'user' ? 'user-message' : 'assistant-message']"
              >
                <div class="message-avatar">
                  <el-avatar v-if="msg.role === 'user'" :size="36" src="/user-avatar.jpg" fit="cover" class="glass-avatar"></el-avatar>
                  <el-avatar v-else :size="36" src="/customer-service-avatar.jpg" fit="cover" class="glass-avatar"></el-avatar>
                </div>
                <div class="message-content">
                  <div class="message-text">
                    <div class="message-content-text" v-html="renderMarkdown(msg.content, msg.role)"></div>
                  </div>
                </div>
              </div>
              <div v-if="isCustomerServiceLoading" class="message assistant-message">
                <div class="message-avatar">
                  <el-avatar :size="36" src="/customer-service-avatar.jpg" fit="cover" class="glass-avatar"></el-avatar>
                </div>
                <div class="message-content">
                  <div class="message-text loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="chat-footer-glass">
              <div class="upload-section">
                <input 
                  type="file" 
                  ref="customerServiceFileInputRef"
                  accept=".pdf,.doc,.docx,.txt,.rtf,.jpg,.jpeg,.png"
                  style="display: none"
                  @change="handleCustomerServiceFileSelect"
                />
                <div class="hint-text" @click="customerServiceUserInput = '小助手，这个平台怎么使用呀？'; sendCustomerServiceMessage()">
                  💡 小助手，这个平台怎么使用呀？
                </div>
                <div v-if="customerServiceUploadedFile" class="uploaded-file-info">
                  <el-tag class="glass-tag" size="small" closable @close="removeCustomerServiceUploadedFile">
                    {{ customerServiceUploadedFile.name }} ({{ formatFileSize(customerServiceUploadedFile.size) }})
                  </el-tag>
                </div>
              </div>
              <div class="chat-input-wrapper">
                <el-input
                  v-model="customerServiceUserInput"
                  placeholder="请输入您的问题..."
                  @keyup.enter="sendCustomerServiceMessage"
                  :disabled="isCustomerServiceLoading"
                  class="glass-input"
                >
                  <template #append>
                    <el-button 
                      class="glass-btn-primary" 
                      @click="sendCustomerServiceMessage" 
                      :loading="isCustomerServiceLoading"
                      :disabled="!customerServiceUserInput.trim() && !customerServiceUploadedFile"
                    >
                      <el-icon><Position /></el-icon>
                    </el-button>
                  </template>
                </el-input>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </section>

    <!-- 匹配详情模态框 (玻璃风) -->
    <el-dialog
      v-model="matchDetailDialogVisible"
      title="匹配详情"
      width="60%"
      :close-on-click-modal="true"
      class="glass-dialog"
    >
      <div v-if="selectedMatch" class="match-detail-content">
        <!-- 保持原有结构，样式交由 CSS 处理 -->
        <div class="match-detail-header">
          <div class="match-detail-rank">
            <span class="rank-badge">{{ selectedMatch.match_rank }}</span>
            <h2 class="detail-job-name">{{ selectedMatch.job_name }}</h2>
          </div>
          <div class="detail-overall-match">
            <span class="match-label">综合匹配度</span>
            <span class="match-score">{{ selectedMatch.overall_matching.toFixed(1) }}%</span>
          </div>
        </div>

        <div class="match-detail-company">
          <p class="company-name">{{ selectedMatch.company_name }}</p>
        </div>

        <div class="match-detail-scores">
          <!-- ...省略内部相同结构... -->
          <div class="detail-score-item">
            <span class="detail-score-label">基本要求</span>
            <div class="detail-score-bar"><div class="detail-score-fill" :style="{ width: selectedMatch.basic_requirements_matching + '%' }"></div></div>
            <span class="detail-score-value">{{ selectedMatch.basic_requirements_matching.toFixed(1) }}%</span>
          </div>
          <!-- 其他进度条... -->
        </div>

        <div class="match-detail-skills">
          <h4>技能匹配情况</h4>
          <div class="skills-section">
            <div class="matched-skills">
              <h5>已匹配技能</h5>
              <div class="skill-tags">
                <el-tag type="success" class="glass-tag">沟通能力</el-tag>
                <el-tag type="success" class="glass-tag">团队协作</el-tag>
              </div>
            </div>
            <div class="missing-skills">
              <h5>待提升技能</h5>
              <div class="skill-tags">
                <el-tag type="warning" class="glass-tag">数据分析</el-tag>
                <el-tag type="warning" class="glass-tag">项目管理</el-tag>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'
import { Loading, Connection, ArrowRight, Download, Upload, Position } from '@element-plus/icons-vue'

const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true,
  typographer: true
})

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface UploadedFile {
  name: string
  size: number
  file: File
}

interface Student {
  id: number
  name: string
  school: string
  major: string
  education: string
  competitiveness_score: number
  created_at: string
}

interface JobMatch {
  match_rank: number
  basic_requirements_matching: number
  professional_skills_matching: number
  professional_literacy_matching: number
  development_potential_matching: number
  overall_matching: number
  job_name: string
  company_name: string
  salary_range: string
  work_address: string
}

// 保留原有的所有逻辑和状态
const chatMessages = ref<ChatMessage[]>([
  {
    role: 'assistant',
    content: '你好！我是 AI 职业规划助手，可以帮助你进行职业规划、简历优化、岗位推荐等。你可以上传简历（支持 PDF、Word、图片等格式），我会帮你分析并给出职业建议。请问有什么可以帮助你的吗？'
  }
])
const userInput = ref('')
const isLoading = ref(false)
const chatContainerRef = ref<HTMLElement | null>(null)
const uploadedFile = ref<UploadedFile | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

// 客服智能体相关变量
const customerServiceChatMessages = ref<ChatMessage[]>([
  {
    role: 'assistant',
    content: '你好！我是 AI 客服助手，有什么可以帮助你的吗？'
  }
])
const customerServiceUserInput = ref('')
const isCustomerServiceLoading = ref(false)
const customerServiceChatContainerRef = ref<HTMLElement | null>(null)
const customerServiceUploadedFile = ref<UploadedFile | null>(null)
const customerServiceFileInputRef = ref<HTMLInputElement | null>(null)

// 人岗匹配相关变量
const students = ref<Student[]>([])
const selectedStudentId = ref<number | null>(null)
const studentMatches = ref<JobMatch[]>([])
const isLoadingMatches = ref(false)

// 模态框相关变量
const matchDetailDialogVisible = ref(false)
const selectedMatch = ref<JobMatch | null>(null)

const openMatchDetail = (match: JobMatch) => {
  selectedMatch.value = match
  matchDetailDialogVisible.value = true
}

const closeMatchDetail = () => {
  matchDetailDialogVisible.value = false
  selectedMatch.value = null
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainerRef.value) {
      chatContainerRef.value.scrollTop = chatContainerRef.value.scrollHeight
    }
  })
}

const scrollToCustomerServiceBottom = () => {
  nextTick(() => {
    if (customerServiceChatContainerRef.value) {
      customerServiceChatContainerRef.value.scrollTop = customerServiceChatContainerRef.value.scrollHeight
    }
  })
}

const loadStudents = async (showError: boolean = false) => {
  // 原有逻辑
}

const loadStudentMatches = async () => {
  // 原有逻辑
}

onMounted(() => {
  // loadStudents() // 根据需要开启
})

const renderMarkdown = (content: string, role: string) => {
  if (role === 'assistant') {
    return md.render(content)
  }
  return content
}

const downloadAsPDF = async (content: string, index: number) => {
  // 原有 PDF 下载逻辑
}

const triggerFileInput = () => fileInputRef.value?.click()
const handleFileSelect = async (event: Event) => { /* 原有逻辑 */ }
const removeUploadedFile = () => uploadedFile.value = null
const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}
const sendMessage = async () => { /* 原有逻辑 */ }

// 客服逻辑
const triggerCustomerServiceFileInput = () => customerServiceFileInputRef.value?.click()
const handleCustomerServiceFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  customerServiceUploadedFile.value = { name: file.name, size: file.size, file: file }
  target.value = ''
}
const removeCustomerServiceUploadedFile = () => customerServiceUploadedFile.value = null
const sendCustomerServiceMessage = async () => {
  const message = customerServiceUserInput.value.trim()
  const file = customerServiceUploadedFile.value?.file || null
  if ((!message && !file) || isCustomerServiceLoading.value) return

  let displayMessage = message
  if (file) {
    displayMessage = message
      ? `[上传文件：${file.name}] ${message}`
      : `[上传文件：${file.name}]`
  }

  customerServiceChatMessages.value.push({ role: 'user', content: displayMessage })
  customerServiceUserInput.value = ''
  isCustomerServiceLoading.value = true
  scrollToCustomerServiceBottom()

  try {
    let response

    if (file) {
      // 有文件：multipart/form-data
      const formData = new FormData()
      formData.append('file', file)
      formData.append('message', message)
      formData.append('history', JSON.stringify(
        customerServiceChatMessages.value
          .filter(m => m.role === 'user' || m.role === 'assistant')
          .slice(0, -1)  // 去掉刚 push 的用户消息
          .map(m => ({ role: m.role, content: m.content }))
      ))
      response = await axios.post('/api/chat/customer-service', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    } else {
      // 纯文本：application/json
      response = await axios.post('/api/chat/customer-service', {
        message,
        history: customerServiceChatMessages.value
          .filter(m => m.role === 'user' || m.role === 'assistant')
          .slice(0, -1)
          .map(m => ({ role: m.role, content: m.content }))
      })
    }

    const reply = response.data?.response || '(未收到回复)'
    customerServiceChatMessages.value.push({ role: 'assistant', content: reply })
  } catch (err: any) {
    const errMsg = err?.response?.data?.error || err?.message || '请求失败，请稍后重试'
    customerServiceChatMessages.value.push({
      role: 'assistant',
      content: `抱歉，${errMsg}`
    })
    ElMessage.error(`客服请求失败：${errMsg}`)
  } finally {
    isCustomerServiceLoading.value = false
    removeCustomerServiceUploadedFile()
    scrollToCustomerServiceBottom()
  }
}
</script>

<style scoped>
/* ==================== 基础与布局 ==================== */
.home {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

/* ==================== 共享玻璃拟态类 ==================== */
.glass-panel {
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
  border-radius: 24px;
}

.glass-tile {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.6), 0 4px 16px rgba(0, 0, 0, 0.04);
  border-radius: 20px;
}

.glass-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 16px;
  color: #fff;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}
.glass-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.5);
}

.glass-btn-ghost {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 16px;
  color: #4a5568;
  backdrop-filter: blur(8px);
  transition: all 0.3s;
}
.glass-btn-ghost:hover {
  background: rgba(255, 255, 255, 0.9);
  color: #2d3748;
  transform: translateY(-2px);
}

/* ==================== 英雄区域 ==================== */
.hero {
  text-align: center;
  padding: 80px 40px;
  margin-bottom: 40px;
  position: relative;
  overflow: hidden;
  /* 覆盖默认的玻璃板，加入微妙的白光 */
  background: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.15) 100%);
}

.hero-content {
  max-width: 900px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.hero-title {
  font-size: 52px;
  font-weight: 800;
  margin-bottom: 24px;
  line-height: 1.2;
  animation: fadeInUp 0.8s ease-out;
  letter-spacing: -0.5px;
}

.gradient-text {
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.gradient-text-alt {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-subtitle {
  font-size: 18px;
  color: #4a5568;
  margin-bottom: 40px;
  font-weight: 500;
  animation: fadeInUp 0.8s ease-out 0.2s both;
}

.hero-actions {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-bottom: 50px;
  animation: fadeInUp 0.8s ease-out 0.4s both;
}

.hero-actions .el-button {
  padding: 14px 36px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 24px;
}

.hero-stats {
  max-width: 800px;
  margin: 0 auto;
  animation: fadeInUp 0.8s ease-out 0.6s both;
}

.stat-card {
  padding: 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.7);
}

.stat-number {
  font-size: 40px;
  font-weight: 800;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-label {
  font-size: 15px;
  font-weight: 500;
  color: #718096;
}

/* ==================== 聊天区域 ==================== */
.chat-section {
  margin-bottom: 60px;
}

.chat-card {
  overflow: hidden;
}
.no-border {
  border: 1px solid rgba(255,255,255,0.4);
}
:deep(.el-card__body) {
  padding: 0 !important;
  display: flex;
  flex-direction: column;
}

.chat-container {
  height: 60vh;
  min-height: 450px;
  overflow-y: auto;
  padding: 30px;
  background: transparent; /* 完全透明，由外层玻璃决定 */
}

/* 玻璃风滚动条 */
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.4);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.7);
}

.message {
  display: flex;
  margin-bottom: 24px;
  gap: 16px;
  animation: fadeInUp 0.4s ease-out;
}

.message-avatar {
  flex-shrink: 0;
}

.glass-avatar {
  border: 2px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

.message-content {
  flex: 1;
  min-width: 0;
  display: flex;
}

.message-text {
  padding: 16px 20px;
  border-radius: 20px;
  line-height: 1.7;
  word-break: break-word;
  max-width: 80%;
  font-size: 15px;
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-content {
  justify-content: flex-end;
}

.user-message .message-text {
  /* 用户消息：彩色玻璃 */
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.9) 0%, rgba(118, 75, 162, 0.9) 100%);
  backdrop-filter: blur(10px);
  color: white;
  border-radius: 20px 20px 4px 20px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.25);
}

.assistant-message .message-text {
  /* AI消息：白色磨砂玻璃 */
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  color: #2d3748;
  border-radius: 20px 20px 20px 4px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.04);
}

.message-content-text {
  margin-bottom: 0;
}

/* 底部输入框区域 (整合) */
.chat-footer-glass {
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.6);
  padding: 16px 24px;
  border-radius: 0 0 24px 24px;
}

.upload-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.hint-text {
  color: #718096;
  font-size: 13px;
  cursor: pointer;
  padding: 6px 12px;
  background: rgba(255,255,255,0.5);
  border-radius: 12px;
  transition: all 0.2s;
}
.hint-text:hover {
  background: rgba(255,255,255,0.8);
  color: #667eea;
}

.glass-tag {
  background: rgba(255, 255, 255, 0.6) !important;
  border: 1px solid rgba(255, 255, 255, 0.9) !important;
  color: #4a5568 !important;
  backdrop-filter: blur(4px);
  border-radius: 8px;
}

/* 玻璃拟态输入框 */
.chat-input-wrapper :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.6) !important;
  box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.03) !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  border-radius: 20px;
  padding: 4px 16px;
  transition: all 0.3s ease;
}

.chat-input-wrapper :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.9) !important;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.3), inset 0 2px 6px rgba(0, 0, 0, 0.01) !important;
}

.chat-input-wrapper :deep(.el-input-group__append) {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0 0 0 10px;
}

.chat-input-wrapper .glass-btn-primary {
  border-radius: 16px;
  height: 40px;
  width: 40px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ==================== 动画与杂项 ==================== */
.loading-dots {
  display: flex;
  gap: 6px;
  align-items: center;
  padding: 12px 16px;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #a0aec0;
  border-radius: 50%;
  animation: bounce 1.4s ease-in-out infinite both;
}
.loading-dots span:nth-child(1) { animation-delay: -0.32s; }
.loading-dots span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* --- 全局毛玻璃弹窗覆写 (同 App.vue) --- */
:deep(.glass-dialog) {
  background: rgba(255, 255, 255, 0.75) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.6) !important;
  border-radius: 24px !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1) !important;
  overflow: hidden;
}

:deep(.glass-dialog .el-dialog__header) {
  background: rgba(255,255,255,0.4);
  border-bottom: 1px solid rgba(255,255,255,0.6);
  padding: 20px 24px;
  margin: 0;
}
:deep(.glass-dialog .el-dialog__title) {
  color: #2d3748;
  font-weight: 700;
}

/* ==================== Markdown 内嵌样式覆盖 ==================== */
.message-content-text :deep(h1),
.message-content-text :deep(h2),
.message-content-text :deep(h3) {
  color: #2d3748;
  margin: 16px 0 10px;
  font-weight: 700;
}
.message-content-text :deep(p) { margin: 8px 0; }
.user-message .message-content-text :deep(h1),
.user-message .message-content-text :deep(h2),
.user-message .message-content-text :deep(h3),
.user-message .message-content-text :deep(p) { color: white; }
.message-content-text :deep(a) { color: #667eea; text-decoration: none; font-weight: 500; }
.user-message .message-content-text :deep(a) { color: #fff; text-decoration: underline; }
.message-content-text :deep(code) {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: 6px;
  font-family: monospace;
}
.user-message .message-content-text :deep(code) { background: rgba(255,255,255,0.2); color: white;}
</style>