<template>
  <div class="page-wrapper">
    <!-- 极具设计感的背景流体光效，高度模糊与主系统背景融合 -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    <div class="bg-shape shape-3"></div>

    <div class="matching-container">
      <!-- 页面标题区域 -->
      <div class="glass-page-header fade-in-up">
        <div class="header-content">
          <h1 class="gradient-text page-title">人岗智能匹配</h1>
          <p class="subtitle">AI 深度解析您的能力画像，精准匹配优质岗位</p>
        </div>
      </div>
      
      <!-- 匹配控制区 (玻璃拟态适配) -->
      <div class="control-section glass-panel fade-in-up" style="animation-delay: 0.1s;">
        <el-row :gutter="20" align="middle">
          <el-col :xs="24" :sm="12" :md="8">
            <el-select
              v-model="selectedStudent"
              placeholder="请选择需要匹配的学生"
              style="width: 100%"
              class="glass-select"
              @change="handleStudentChange"
            >
              <el-option
                v-for="student in students"
                :key="student.id"
                :label="student.name"
                :value="student.id"
              >
                <template #default="{ selected }">
                  <div class="student-option">
                    <span>{{ student.name }}</span>
                  </div>
                </template>
              </el-option>
            </el-select>
          </el-col>
          <el-col :xs="24" :sm="12" :md="8">
            <el-button class="glass-primary-btn hover-lift" @click="viewMatching" :loading="matching">
              <el-icon><Search /></el-icon>
              <span>{{ matching ? '智能匹配中...' : '查看岗位匹配' }}</span>
            </el-button>
          </el-col>
        </el-row>
      </div>
      
      <!-- Agent B 流式生成进度 -->
      <div v-if="streamLoading" class="glass-panel streaming-banner fade-in-up" style="animation-delay: 0.1s;">
        <div class="streaming-banner-content">
          <div class="stream-badge">
            <el-icon class="is-loading" :size="20"><Loading /></el-icon>
            <span>{{ streamProgress }}</span>
          </div>
          <div class="stream-status">
            <span v-if="streamPhase === 'connecting'" class="phase-tag connecting">连接 AI 引擎...</span>
            <span v-if="streamPhase === 'streaming'" class="phase-tag streaming">
              实时流式匹配中
              <span class="dot-anim">
                <span class="dot">.</span><span class="dot">.</span><span class="dot">.</span>
              </span>
            </span>
            <span v-if="streamPhase === 'done'" class="phase-tag done">✓ 匹配完成</span>
          </div>
          <el-progress
            v-if="streamPhase === 'streaming'"
            :percentage="Math.min(streamJobCount * 10, 95)"
            :show-text="false"
            :stroke-width="4"
            class="stream-progress-bar"
            color="linear-gradient(90deg, #667eea, #764ba2)"
          />
        </div>
      </div>

      <!-- 匹配结果 -->
      <div v-if="matchResults.length > 0" class="results-container fade-in-up" style="animation-delay: 0.2s;">
        <div class="section-header">
          <h2 class="section-title">匹配结果 <span class="subtitle-light">按匹配度由高到低为您排列</span></h2>
          <!-- 生成报告按钮 -->
          <el-button
            v-if="matchResults.length >= 3"
            class="generate-report-btn hover-lift"
            @click="goToReport"
          >
            <el-icon><Document /></el-icon> 生成职业报告
          </el-button>
        </div>
        
        <!-- 所有匹配结果列表 -->
        <el-row :gutter="24">
          <el-col
            v-for="(match, index) in sortedMatchResults"
            :key="match.job_id"
            :xs="24"
            :sm="12"
            :md="8"
          >
            <!-- 自定义玻璃拟态卡片，废弃 el-card -->
            <div 
              class="match-card glass-item hover-lift" 
              :class="{ 'best-match-glass': index === 0 }" 
              @click="openMatchDetail(match)"
            >
              <div class="match-card-header">
                <div class="header-left">
                  <div class="rank-badge" :class="getRankClass(index)">
                    {{ index + 1 }}
                  </div>
                  <h4 :title="match.job_name">{{ match.job_name }}</h4>
                </div>
                <div class="header-right">
                  <span class="match-score-text" :class="getMatchScoreClass(match.overall_match_score)">
                    {{ match.overall_match_score.toFixed(1) }}%
                  </span>
                </div>
              </div>
              
              <div class="company-name-wrapper">
                <p class="company-name" :title="match.company_name">{{ match.company_name }}</p>
                <div class="match-level-tag">
                  <el-tag :type="getMatchLevelType(match.match_level)" size="small" effect="light" class="glass-tag">
                    {{ getMatchLevelText(match.match_level) }}
                  </el-tag>
                </div>
              </div>

              <div class="match-dimensions">
                <div class="dimension-row">
                  <span class="dimension-label">基础要求</span>
                  <el-progress
                    :percentage="match.basic_requirements_score"
                    :color="getProgressColor(match.basic_requirements_score)"
                    :stroke-width="6"
                    class="glass-progress"
                    :show-text="false"
                  />
                </div>
                <div class="dimension-row">
                  <span class="dimension-label">职业技能</span>
                  <el-progress
                    :percentage="match.professional_skills_score"
                    :color="getProgressColor(match.professional_skills_score)"
                    :stroke-width="6"
                    class="glass-progress"
                    :show-text="false"
                  />
                </div>
                <div class="dimension-row">
                  <span class="dimension-label">职业素养</span>
                  <el-progress
                    :percentage="match.professional_qualities_score"
                    :color="getProgressColor(match.professional_qualities_score)"
                    :stroke-width="6"
                    class="glass-progress"
                    :show-text="false"
                  />
                </div>
                <div class="dimension-row">
                  <span class="dimension-label">发展潜力</span>
                  <el-progress
                    :percentage="match.development_potential_score"
                    :color="getProgressColor(match.development_potential_score)"
                    :stroke-width="6"
                    class="glass-progress"
                    :show-text="false"
                  />
                </div>
              </div>
              
              <div class="card-actions">
                <div class="action-link" @click.stop="viewJobDetail(match.job_id)">
                  <span>查看画像详情</span>
                  <div class="arrow-icon">→</div>
                </div>
                <el-button
                  text
                  size="small"
                  type="warning"
                  class="interview-card-btn"
                  @click.stop="$router.push(`/interview/${selectedStudent}/${match.job_id}`)"
                >
                  💬 问大佬
                </el-button>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="empty-state glass-panel fade-in-up" style="animation-delay: 0.2s;">
        <el-empty description="请选择学生并开始智能匹配" class="glass-empty">
          <template #image>
            <el-icon :size="80" color="rgba(102, 126, 234, 0.5)"><Connection /></el-icon>
          </template>
        </el-empty>
      </div>

      <!-- 匹配详情模态框 (玻璃拟态适配) -->
      <el-dialog
        v-model="matchDetailDialogVisible"
        title="岗位匹配深度解析"
        width="65%"
        :close-on-click-modal="true"
        class="match-detail-dialog glass-dialog"
      >
        <div v-if="selectedMatch" class="match-detail-content">
          <div class="match-detail-header">
            <div class="match-detail-rank">
              <span class="rank-badge-large" :class="getRankClass(sortedMatchResults.findIndex(m => m.job_id === selectedMatch.job_id))">
                TOP {{ sortedMatchResults.findIndex(m => m.job_id === selectedMatch.job_id) + 1 }}
              </span>
              <div class="job-title-group">
                <h2 class="detail-job-name gradient-text">{{ selectedMatch.job_name }}</h2>
                <p class="company-name">{{ selectedMatch.company_name }}</p>
              </div>
            </div>
            <div class="detail-overall-match glass-inner-panel">
              <span class="match-label">综合匹配度</span>
              <span class="match-score gradient-text-green">{{ selectedMatch.overall_match_score.toFixed(1) }}%</span>
              <el-tag :type="getMatchLevelType(selectedMatch.match_level)" size="small" effect="plain" class="mt-1">
                {{ getMatchLevelText(selectedMatch.match_level) }}
              </el-tag>
            </div>
          </div>

          <div class="match-detail-scores glass-item">
            <h4 class="glass-section-title">维度匹配度分析</h4>
            <div class="scores-grid">
              <div class="detail-score-item">
                <span class="detail-score-label">基础要求</span>
                <div class="detail-score-bar">
                  <div class="detail-score-fill fill-blue" :style="{ width: selectedMatch.basic_requirements_score + '%' }"></div>
                </div>
                <span class="detail-score-value">{{ selectedMatch.basic_requirements_score.toFixed(1) }}%</span>
              </div>
              <div class="detail-score-item">
                <span class="detail-score-label">职业技能</span>
                <div class="detail-score-bar">
                  <div class="detail-score-fill fill-purple" :style="{ width: selectedMatch.professional_skills_score + '%' }"></div>
                </div>
                <span class="detail-score-value">{{ selectedMatch.professional_skills_score.toFixed(1) }}%</span>
              </div>
              <div class="detail-score-item">
                <span class="detail-score-label">职业素养</span>
                <div class="detail-score-bar">
                  <div class="detail-score-fill fill-orange" :style="{ width: selectedMatch.professional_qualities_score + '%' }"></div>
                </div>
                <span class="detail-score-value">{{ selectedMatch.professional_qualities_score.toFixed(1) }}%</span>
              </div>
              <div class="detail-score-item">
                <span class="detail-score-label">发展潜力</span>
                <div class="detail-score-bar">
                  <div class="detail-score-fill fill-green" :style="{ width: selectedMatch.development_potential_score + '%' }"></div>
                </div>
                <span class="detail-score-value">{{ selectedMatch.development_potential_score.toFixed(1) }}%</span>
              </div>
            </div>
          </div>

          <div class="match-detail-bottom">
            <div class="match-detail-skills glass-item">
              <h4 class="glass-section-title">技能匹配画像</h4>
              <div class="skills-section">
                <div class="matched-skills">
                  <h5><el-icon color="#10b981"><Select /></el-icon> 已掌握能力</h5>
                  <div class="skill-tags">
                    <el-tag type="success" effect="light" class="glass-tag">沟通能力</el-tag>
                    <el-tag type="success" effect="light" class="glass-tag">团队协作</el-tag>
                    <el-tag type="success" effect="light" class="glass-tag">问题解决</el-tag>
                  </div>
                </div>
                <div class="missing-skills">
                  <h5><el-icon color="#f59e0b"><Warning /></el-icon> 待提升能力</h5>
                  <div class="skill-tags">
                    <el-tag type="warning" effect="light" class="glass-tag">数据分析</el-tag>
                    <el-tag type="warning" effect="light" class="glass-tag">项目管理</el-tag>
                  </div>
                </div>
              </div>
            </div>

            <div class="match-detail-recommendations glass-item">
              <h4 class="glass-section-title">AI 专属提升建议</h4>
              <el-timeline class="glass-timeline">
                <el-timeline-item type="primary" :hollow="true">
                  <div class="timeline-glass-content">提升数据分析能力，学习相关工具如Excel、Python等</div>
                </el-timeline-item>
                <el-timeline-item type="primary" :hollow="true">
                  <div class="timeline-glass-content">积累项目管理经验，参与更多团队项目</div>
                </el-timeline-item>
                <el-timeline-item type="primary" :hollow="true">
                  <div class="timeline-glass-content">加强专业技能学习，获取相关认证</div>
                </el-timeline-item>
              </el-timeline>
            </div>
          </div>

          <div class="match-detail-actions">
            <el-button class="glass-primary-btn hover-lift" size="large" @click="viewJobDetail(selectedMatch.job_id)">
              查看完整岗位画像
            </el-button>
          </div>
        </div>
      </el-dialog>

      <!-- 确认匹配弹窗 (Admin 玻璃拟态风格) -->
      <el-dialog
        v-model="showConfirmDialog"
        width="480px"
        class="glass-confirm-dialog"
        :show-close="false"
      >
        <div class="dialog-inner">
          <h3 class="dialog-title">确认岗位匹配</h3>
          <p class="dialog-message">{{ confirmMessage }}</p>
        </div>
        <template #footer>
          <div class="dialog-footer">
            <el-button class="glass-btn-ghost" @click="showConfirmDialog = false">取消</el-button>
            <el-button class="glass-btn-primary" @click="doStartMatching" :loading="matching">开始匹配</el-button>
          </div>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from '@/utils/axios'
import { useUserStore } from '@/stores/user'
import { useAgentPipeline } from '@/stores/agentPipeline'
import type { JobMatchResult } from '@/stores/agentPipeline'
// 统一引入图标
import { Search, Connection, Select, Warning, Loading, Right, Top, Document } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const agentPipeline = useAgentPipeline()

const selectedStudent = ref<number | null>(null)
const students = ref<any[]>([])
const matching = ref(false)
const matchResults = ref<any[]>([])

// ---- SSE 流式状态 ----
const streamLoading = ref(false)          // Agent B 是否在流式生成
const streamProgress = ref('')            // 进度提示文本
const streamJobCount = ref(0)             // 已解析的岗位数
const streamPhase = ref<'idle' | 'connecting' | 'streaming' | 'done'>('idle')
const hasCheckedDb = ref(false)           // 是否已查过 DB（避免重复弹窗）


// 按匹配度从高到低排序的匹配结果
const sortedMatchResults = computed(() => {
  return [...matchResults.value].sort((a, b) => b.overall_match_score - a.overall_match_score)
})

// 模态框相关变量
const matchDetailDialogVisible = ref(false)
const selectedMatch = ref<any>(null)

// 确认匹配弹窗
const showConfirmDialog = ref(false)
const confirmMessage = ref('')
const pendingStudentId = ref<number | null>(null)

// 打开匹配详情模态框
const openMatchDetail = (match: any) => {
  selectedMatch.value = match
  matchDetailDialogVisible.value = true
}

// 关闭匹配详情模态框
const closeMatchDetail = () => {
  matchDetailDialogVisible.value = false
  selectedMatch.value = null
}

// 初始化：加载学生列表 + 处理 URL 参数
onMounted(async () => {
  if (students.value.length === 0) {
    loadStudents()
  }

  // 检查URL中是否有studentId参数 → 预选学生并自动查DB
  const studentIdParam = route.query.studentId
  if (studentIdParam) {
    const studentId = parseInt(studentIdParam as string)
    if (!isNaN(studentId)) {
      selectedStudent.value = studentId
      agentPipeline.currentStudentId = studentId
      // 自动查 DB（但不再自动调 Agent B）
      await nextTick()
      await checkAndShowMatches()
    }
  }
})

// 监听路由参数变化
watch(() => route.query.studentId, (newStudentId) => {
  if (newStudentId) {
    const studentId = parseInt(newStudentId as string)
    if (!isNaN(studentId)) {
      selectedStudent.value = studentId
      agentPipeline.currentStudentId = studentId
      checkAndShowMatches()
    }
  }
})

// 获取排名样式
const getRankClass = (index: number) => {
  if (index === 0) return 'rank-1'
  if (index === 1) return 'rank-2'
  if (index === 2) return 'rank-3'
  return 'rank-other'
}

const getMatchScoreClass = (score: number) => {
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  return 'score-normal'
}

// 加载学生列表
const loadStudents = async () => {
  try {
    const response = await axios.get('http://localhost:5000/api/students/list', {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (response.data.success) {
      students.value = response.data.data.map((s: any) => ({
        id: s.id,
        name: s.name
      }))
    }
  } catch (error) {
    console.error('加载学生列表失败', error)
    ElMessage.error('加载学生列表失败')
  }
}

const handleStudentChange = (studentId: number) => {
  selectedStudent.value = studentId
  agentPipeline.currentStudentId = studentId  // 同步 student_id 用于 DB 持久化
  hasCheckedDb.value = false                    // 换了学生，重置查DB标记
  matchResults.value = []
}

/**
 * 核心：通过 fetch + SSE 流式匹配，卡片逐个弹出
 */
const startStreamMatching = async (profileData: Record<string, unknown>) => {
  streamLoading.value = true
  streamPhase.value = 'connecting'
  streamJobCount.value = 0
  streamProgress.value = 'AI 正在分析您的能力画像...'
  matchResults.value = []

  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  try {
    const response = await fetch('http://localhost:5000/api/agent/match', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        student_profile: profileData,
        student_id: agentPipeline.currentStudentId,  // DB持久化：Agent B 写 student_job_matches
      }),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    streamPhase.value = 'streaming'
    streamProgress.value = '正在匹配岗位...'

    const reader = response.body?.getReader()
    if (!reader) throw new Error('浏览器不支持流式读取')

    const decoder = new TextDecoder('utf-8')
    let fullText = ''      // 累积 AI 输出的纯 JSON 文本
    let rawBuffer = ''     // SSE 协议原始 buffer

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      rawBuffer += decoder.decode(value, { stream: true })

      // 解析 SSE 协议：每遇到 \n\n 代表一个事件结束
      const events = rawBuffer.split('\n\n')
      rawBuffer = events.pop() || ''  // 最后一段可能不完整

      for (const event of events) {
        if (!event.trim()) continue
        const lines = event.split('\n')
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data: ')) continue
          try {
            const sseEvent = JSON.parse(trimmed.slice(6))
            if (sseEvent.type === 'chunk' && sseEvent.content) {
              fullText += sseEvent.content   // ★ 只累积 AI 输出的内容
            } else if (sseEvent.type === 'done') {
              // DB 持久化结果通知
              if (sseEvent.warning) {
                console.warn('[Matching] DB 写入警告:', sseEvent.warning)
                ElMessage.warning(sseEvent.warning)
              }
              if (sseEvent.saved_matches) {
                console.log('[Matching] 已保存', sseEvent.saved_matches, '条匹配结果到数据库')
              }
            } else if (sseEvent.type === 'error') {
              throw new Error(sseEvent.message || 'AI 服务错误')
            }
          } catch (e) {
            if (e instanceof Error && e.message !== 'AI 服务错误') continue
            throw e
          }
        }
      }

      streamProgress.value = `正在接收 AI 数据... (${Math.round(fullText.length / 1024)} KB)`
    }

    // ★ Plan A：全部接收完成后，一次性解析完整 JSON
    //   模型可能在 JSON 前后加说明文字或 markdown 包裹，用正则提取
    streamProgress.value = '正在解析匹配结果...'
    let parsed: any
    try {
      let jsonStr = ''

      // 方式1：提取 ```json ... ``` 代码块的内容
      const mdMatch = fullText.match(/```json\s*\n([\s\S]*?)\n\s*```/)
      if (mdMatch) {
        jsonStr = mdMatch[1].trim()
      } else {
        // 方式2：提取最外层 { ... } JSON 对象
        const jsonMatch = fullText.match(/\{[\s\S]*\}/)
        if (jsonMatch) {
          jsonStr = jsonMatch[0].trim()
        } else {
          throw new Error('未找到 JSON 数据')
        }
      }

      parsed = JSON.parse(jsonStr)
    } catch (e: any) {
      // 打印前 500 字符帮助调试
      const preview = fullText.slice(0, 500)
      console.error('Agent B 返回内容前500字:', preview)
      console.error('解析错误:', e.message)
      throw new Error(
        e.message === '未找到 JSON 数据'
          ? 'AI 返回中未找到有效数据，请重试'
          : `AI 返回格式解析失败：${e.message.slice(0, 60)}`
      )
    }

    const jobProfiles: any[] = parsed.job_post_profiles || []
    if (jobProfiles.length === 0) {
      throw new Error('AI 未返回有效匹配结果，请确认 MySQL 中有岗位数据')
    }

    // 批量构建卡片 + 异步查 MySQL
    const seenIds = new Set<number>()
    for (const job of jobProfiles) {
      if (!job.id || seenIds.has(job.id)) continue
      seenIds.add(job.id)

      const matchItem: any = {
        job_id: job.id,
        job_name: `岗位 #${job.id}`,
        company_name: '',
        overall_match_score: job.user_matching_scores?.overall_matching || 0,
        match_level:
          (job.user_matching_scores?.overall_matching || 0) >= 80
            ? 'excellent'
            : (job.user_matching_scores?.overall_matching || 0) >= 60
              ? 'good'
              : (job.user_matching_scores?.overall_matching || 0) >= 40
                ? 'moderate'
                : 'poor',
        basic_requirements_score: job.user_matching_scores?.basic_requirements_matching || 0,
        professional_skills_score: job.user_matching_scores?.professional_skills_matching || 0,
        professional_qualities_score: job.user_matching_scores?.professional_literacy_matching || 0,
        development_potential_score: job.user_matching_scores?.development_potential_matching || 0,
        match_rank: matchResults.value.length + 1,
      }

      matchResults.value.push(matchItem)
      streamJobCount.value = matchResults.value.length

      // 异步查 MySQL 卡片数据
      fetchJobCardForMatch(job.id, matchItem)
    }

    streamPhase.value = 'done'
    streamProgress.value = `匹配完成，共 ${matchResults.value.length} 个岗位`
    ElMessage.success(`匹配完成！已为您找到 ${matchResults.value.length} 个匹配岗位`)
  } catch (err: any) {
    ElMessage.error('匹配失败：' + (err.message || '网络错误'))
    streamPhase.value = 'idle'
  } finally {
    streamLoading.value = false
    matching.value = false
  }
}

/** 查 MySQL 获取岗位卡片基本信息并更新 matchResult */
const fetchJobCardForMatch = async (jobId: number, matchItem: any) => {
  try {
    const res = await axios.get(`/api/jobs/${jobId}`)
    if (res.data) {
      matchItem.job_name = res.data.job_name || matchItem.job_name
      matchItem.company_name = res.data.company_name || ''
      matchItem.salary = res.data.salary_range || ''
      matchItem.location = res.data.work_address || ''
      // 触发响应式更新
      const idx = matchResults.value.findIndex((m) => m.job_id === jobId)
      if (idx >= 0) {
        matchResults.value[idx] = { ...matchResults.value[idx] }
      }
    }
  } catch {
    // MySQL 数据获取失败不影响匹配结果
  }
}

/**
 * 按钮点击 → 先查 DB，有数据直接展示，无数据弹窗确认
 */
const viewMatching = async () => {
  if (!selectedStudent.value) {
    ElMessage.warning('请先选择学生')
    return
  }
  await checkAndShowMatches()
}

/**
 * 查 DB：有匹配 → 直接展示；无匹配 → 弹窗确认是否调 Agent B
 */
const checkAndShowMatches = async () => {
  const studentId = selectedStudent.value
  if (!studentId) return

  if (hasCheckedDb.value && matchResults.value.length > 0) {
    return  // 已查过且有结果，不重复请求
  }

  try {
    const res = await axios.get(`/api/agent/match/${studentId}`)
    if (res.data.exists) {
      // ★ DB 中已有匹配结果 → 直接展示
      matchResults.value = res.data.data.map((item: any) => ({
        job_id: item.job_id,
        job_name: item.job_name || `岗位 #${item.job_id}`,
        company_name: item.company_name || '',
        overall_match_score: item.overall_match_score || 0,
        match_level: item.match_level || 'moderate',
        basic_requirements_score: item.basic_requirements_score || 0,
        professional_skills_score: item.professional_skills_score || 0,
        professional_qualities_score: item.professional_qualities_score || 0,
        development_potential_score: item.development_potential_score || 0,
      }))
      hasCheckedDb.value = true
      ElMessage.success(`已加载「${res.data.student_name}」的岗位匹配结果`)
      return
    }

    // ★ DB 中无匹配 → 弹窗确认（Admin 玻璃拟态风格）
    const studentName = res.data.student_name || '该学生'
    hasCheckedDb.value = true
    pendingStudentId.value = studentId
    confirmMessage.value = `「${studentName}」的简历尚未进行岗位匹配，是否调用 AI 生成岗位推荐？`
    showConfirmDialog.value = true
  } catch (err: any) {
    ElMessage.error('查询匹配结果失败：' + (err.message || '未知错误'))
  }
}

/**
 * 用户在确认弹窗中点击"开始匹配" → 加载画像 → 调 Agent B
 */
const doStartMatching = async () => {
  const studentId = pendingStudentId.value
  if (!studentId) return

  showConfirmDialog.value = false
  matching.value = true

  let profileData = agentPipeline.profile
  if (!profileData) {
    agentPipeline.currentStudentId = studentId
    try {
      const profileRes = await axios.get(`/api/students/${studentId}/profile`)
      profileData = profileRes.data
    } catch {
      ElMessage.error('无法加载学生画像，请先在"能力画像"页面上传简历')
      matching.value = false
      return
    }
  }

  try {
    await startStreamMatching(profileData as Record<string, unknown>)
  } catch (err: any) {
    ElMessage.error('匹配失败：' + (err.message || '未知错误'))
    matching.value = false
  }
}

const goToReport = () => {
  const sorted = [...matchResults.value].sort(
    (a, b) => b.overall_match_score - a.overall_match_score
  )
  // 只传匹配数据，岗位画像由 Agent C 按需提供
  agentPipeline.selectTop3(
    sorted.slice(0, 3).map((m: any) => ({
      job_id: m.job_id,
      user_matching_scores: {
        basic_requirements_matching: m.basic_requirements_score,
        professional_skills_matching: m.professional_skills_score,
        professional_literacy_matching: m.professional_qualities_score,
        development_potential_matching: m.development_potential_score,
        overall_matching: m.overall_match_score,
      },
    }))
  )
  router.push('/report')
}

onUnmounted(() => {
  // 页面离开时 SSE 连接会自动断开
})

const getMatchLevelType = (level: string) => {
  const types: Record<string, string> = {
    'excellent': 'success',
    'good': 'primary',
    'moderate': 'warning',
    'poor': 'info'
  }
  return types[level] || 'info'
}

const getMatchLevelText = (level: string) => {
  const texts: Record<string, string> = {
    'excellent': '极度匹配',
    'good': '良好匹配',
    'moderate': '一般匹配',
    'poor': '匹配度较低'
  }
  return texts[level] || '未知'
}

const getProgressColor = (score: number) => {
  if (score >= 80) return '#10b981' // emerald-500
  if (score >= 60) return '#6366f1' // indigo-500
  if (score >= 40) return '#f59e0b' // amber-500
  return '#ef4444' // red-500
}

const generateReport = (jobId: number) => {
  if (!selectedStudent.value) return
  
  router.push({
    path: '/report',
    query: {
      studentId: selectedStudent.value.toString(),
      jobId: jobId.toString()
    }
  })
}

const viewJobDetail = (jobId: number) => {
  const match = matchResults.value.find(m => m.job_id === jobId)
  const rank = match ? (sortedMatchResults.value.findIndex(m => m.job_id === jobId) + 1) : 0

  router.push({
    path: `/jobs/${jobId}`,
    query: {
      from: 'matching',
      studentId: selectedStudent.value?.toString(),
      ...(rank > 0 ? { matchRank: String(rank) } : {}),
    }
  })
}
</script>

<style scoped>
/* =========== 整体页面背景与流体光晕 =========== */
.page-wrapper {
  min-height: 100%;
  position: relative;
  background: transparent;
  overflow: hidden;
  border-radius: 16px;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  z-index: 0;
  opacity: 0.45;
  animation: float 18s ease-in-out infinite;
}

.shape-1 {
  top: -10%;
  left: -5%;
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
}

.shape-2 {
  bottom: -10%;
  right: -5%;
  width: 700px;
  height: 700px;
  background: linear-gradient(135deg, #c2e9fb 0%, #a1c4fd 100%);
  animation-delay: -5s;
}

.shape-3 {
  top: 40%;
  left: 50%;
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #fbc2eb 0%, #e6dee9 100%);
  animation-delay: -10s;
}

@keyframes float {
  0% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(40px, -60px) scale(1.1); }
  66% { transform: translate(-30px, 30px) scale(0.9); }
  100% { transform: translate(0, 0) scale(1); }
}

/* =========== 主体内容区 =========== */
.matching-container {
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px 24px;
}

/* =========== 玻璃拟态基础样式 =========== */
.glass-panel {
  background: rgba(255, 255, 255, 0.4) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.4) !important;
  border-radius: 24px !important;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
  overflow: hidden;
}

.glass-inner-panel {
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
}

.glass-item {
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.hover-lift:hover {
  background: rgba(255, 255, 255, 0.7);
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.12);
  border-color: rgba(255, 255, 255, 0.9);
}

/* =========== 页面头部 =========== */
.glass-page-header {
  margin-bottom: 32px;
  padding-left: 12px;
}

.header-content {
  position: relative;
}

.gradient-text {
  font-size: 38px;
  font-weight: 800;
  margin: 0 0 8px 0;
  background: linear-gradient(120deg, #1f2937, #3730a3);
  -webkit-background-clip: text;
  color: transparent;
  letter-spacing: -0.5px;
}

.gradient-text-green {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text;
  color: transparent;
}

.subtitle {
  color: #6b7280;
  font-size: 16px;
  margin: 0;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.subtitle-light {
  font-size: 14px;
  color: #9ca3af;
  font-weight: 400;
  margin-left: 12px;
}

/* =========== 控制区 (搜索/选择) =========== */
.control-section {
  padding: 24px 32px;
  margin-bottom: 36px;
}

/* 深度覆盖 Element Plus 选择器样式 */
.glass-select :deep(.el-select__wrapper) {
  background: rgba(255, 255, 255, 0.6);
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 14px;
  padding: 12px 18px;
  min-height: 52px;
  font-size: 15px;
  transition: all 0.3s ease;
}

.glass-select :deep(.el-select__wrapper:hover),
.glass-select :deep(.el-select__wrapper.is-focused) {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(255, 255, 255, 1);
  box-shadow: 0 4px 16px rgba(0,0,0,0.04) !important;
}

.glass-primary-btn {
  height: 52px;
  width: 100%;
  border-radius: 14px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: white !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.glass-primary-btn:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.student-option {
  display: flex;
  align-items: center;
  font-size: 15px;
  font-weight: 500;
}

/* =========== 匹配结果区域 =========== */
.section-header {
  margin-bottom: 24px;
}

.section-title {
  font-size: 22px;
  font-weight: 800;
  color: #1f2937;
  display: flex;
  align-items: baseline;
}

.match-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  height: 100%;
  margin-bottom: 24px;
  cursor: pointer;
  position: relative;
}

/* 最佳匹配特殊高亮 */
.best-match-glass {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.8) 0%, rgba(220, 252, 231, 0.6) 100%);
  border-color: rgba(167, 243, 208, 0.8);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.1);
}

.best-match-glass:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.95) 0%, rgba(220, 252, 231, 0.8) 100%);
  border-color: rgba(110, 231, 183, 1);
  box-shadow: 0 12px 32px rgba(16, 185, 129, 0.2);
}

.match-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.header-left h4 {
  font-size: 18px;
  font-weight: 800;
  margin: 0;
  color: #1f2937;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
  transition: color 0.3s ease;
}

.match-card:hover .header-left h4 {
  color: #5a67d8;
}

.rank-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 800;
  color: #fff;
  flex-shrink: 0;
  margin-top: 2px;
}

.rank-1 { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); box-shadow: 0 4px 10px rgba(245, 158, 11, 0.3); }
.rank-2 { background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%); box-shadow: 0 4px 10px rgba(156, 163, 175, 0.3); }
.rank-3 { background: linear-gradient(135deg, #d97706 0%, #92400e 100%); box-shadow: 0 4px 10px rgba(217, 119, 6, 0.3); }
.rank-other { background: linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%); }

.header-right {
  margin-left: 12px;
  flex-shrink: 0;
}

.match-score-text {
  font-size: 20px;
  font-weight: 800;
}
.score-excellent { color: #10b981; }
.score-good { color: #6366f1; }
.score-normal { color: #f59e0b; }

.company-name-wrapper {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.company-name {
  color: #6b7280;
  font-size: 14px;
  font-weight: 600;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.glass-tag {
  border: none;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(4px);
  border-radius: 8px;
  font-weight: 600;
}

.match-dimensions {
  margin-bottom: 20px;
  background: rgba(255, 255, 255, 0.3);
  padding: 16px;
  border-radius: 12px;
}

.dimension-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  gap: 12px;
}

.dimension-row:last-child {
  margin-bottom: 0;
}

.dimension-label {
  font-size: 12px;
  color: #4b5563;
  width: 60px;
  flex-shrink: 0;
  font-weight: 600;
}

.glass-progress {
  flex: 1;
}

.glass-progress :deep(.el-progress-bar__outer) {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 6px;
}

.glass-progress :deep(.el-progress-bar__inner) {
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.card-actions {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.interview-card-btn {
  font-weight: 600;
}

.action-link {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #667eea;
  font-weight: 700;
  font-size: 14px;
  transition: all 0.3s ease;
}

.arrow-icon {
  background: rgba(102, 126, 234, 0.1);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: transform 0.3s ease, background 0.3s ease;
}

.match-card:hover .action-link {
  color: #4f46e5;
}

.match-card:hover .arrow-icon {
  transform: translateX(4px);
  background: rgba(102, 126, 234, 0.2);
}

/* =========== 空状态 =========== */
.empty-state {
  padding: 60px 20px;
  margin-top: 24px;
}

.glass-empty :deep(.el-empty__description) {
  font-size: 16px;
  font-weight: 600;
  color: #6b7280;
}

/* =========== 模态框 (深度覆盖 Element Plus Dialog) =========== */
.glass-dialog :deep(.el-dialog) {
  background: rgba(255, 255, 255, 0.8) !important;
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 24px;
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.glass-dialog :deep(.el-dialog__header) {
  padding: 24px 32px;
  margin: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.5) 0%, rgba(255, 255, 255, 0.2) 100%);
}

.glass-dialog :deep(.el-dialog__title) {
  font-size: 20px;
  font-weight: 800;
  color: #1f2937;
}

.match-detail-content {
  padding: 10px 16px;
}

.match-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.match-detail-rank {
  display: flex;
  align-items: center;
  gap: 20px;
}

.rank-badge-large {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 40px;
  border-radius: 20px;
  font-size: 18px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  box-shadow: 0 8px 20px rgba(245, 158, 11, 0.3);
}

.detail-job-name {
  font-size: 28px;
  margin: 0 0 8px 0;
}

.detail-overall-match {
  padding: 16px 24px;
  text-align: center;
  min-width: 140px;
}

.match-score {
  font-size: 42px;
  font-weight: 800;
  line-height: 1.1;
  margin: 8px 0;
  display: block;
}

.glass-section-title {
  font-size: 18px;
  font-weight: 800;
  color: #1f2937;
  margin-bottom: 20px;
  position: relative;
  display: inline-block;
}

.glass-section-title::after {
  content: '';
  position: absolute;
  bottom: -6px;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, #667eea, transparent);
  border-radius: 2px;
}

.match-detail-scores {
  padding: 24px;
  margin-bottom: 24px;
}

.scores-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.detail-score-item {
  display: flex;
  align-items: center;
  gap: 16px;
}

.detail-score-label {
  width: 70px;
  color: #4b5563;
  font-weight: 600;
  font-size: 14px;
}

.detail-score-bar {
  flex: 1;
  height: 12px;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 6px;
  overflow: hidden;
  box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
}

.detail-score-fill {
  height: 100%;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

.fill-blue { background: linear-gradient(90deg, #60a5fa, #3b82f6); }
.fill-purple { background: linear-gradient(90deg, #a78bfa, #8b5cf6); }
.fill-orange { background: linear-gradient(90deg, #fbbf24, #f59e0b); }
.fill-green { background: linear-gradient(90deg, #34d399, #10b981); }

.detail-score-value {
  width: 50px;
  text-align: right;
  font-weight: 800;
  color: #1f2937;
}

.match-detail-bottom {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.match-detail-skills,
.match-detail-recommendations {
  padding: 24px;
  height: 100%;
}

.skills-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.matched-skills h5,
.missing-skills h5 {
  font-size: 15px;
  color: #374151;
  margin-bottom: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6px;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.glass-timeline :deep(.el-timeline-item__content) {
  color: #4b5563;
  font-size: 14px;
}

.timeline-glass-content {
  background: rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.9);
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
  line-height: 1.6;
}

.match-detail-actions {
  display: flex;
  justify-content: center;
  padding-top: 24px;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
}

.match-detail-actions .glass-primary-btn {
  width: 240px;
}

/* ==================== 动画 ==================== */
.fade-in-up {
  animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(30px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* =========== 流式匹配横幅 =========== */
.streaming-banner {
  margin-bottom: 24px;
  border: 1px solid rgba(102, 126, 234, 0.25) !important;
}

.streaming-banner-content {
  padding: 20px 32px;
}

.stream-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 16px;
  font-weight: 700;
  color: #3730a3;
  margin-bottom: 12px;
}

.stream-status {
  margin-bottom: 16px;
}

.phase-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 8px;
}

.phase-tag.connecting {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}

.phase-tag.streaming {
  background: rgba(102, 126, 234, 0.12);
  color: #4f46e5;
}

.phase-tag.done {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}

.dot-anim .dot {
  animation: dotPulse 1.2s ease-in-out infinite;
}
.dot-anim .dot:nth-child(2) { animation-delay: 0.2s; }
.dot-anim .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes dotPulse {
  0%, 60%, 100% { opacity: 0.3; }
  30% { opacity: 1; }
}

.stream-progress-bar :deep(.el-progress-bar__outer) {
  background: rgba(102, 126, 234, 0.08);
  border-radius: 4px;
}

/* =========== 生成报告按钮 =========== */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.generate-report-btn {
  height: 44px;
  border-radius: 12px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: white !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  padding: 0 24px !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.generate-report-btn:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  transform: translateY(-3px);
}

/* =========== 卡片渐进动画 =========== */
.results-container .el-col {
  animation: cardPopIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* 每个卡片依次延迟 */
.results-container .el-col:nth-child(1)  { animation-delay: 0.00s; }
.results-container .el-col:nth-child(2)  { animation-delay: 0.08s; }
.results-container .el-col:nth-child(3)  { animation-delay: 0.16s; }
.results-container .el-col:nth-child(4)  { animation-delay: 0.24s; }
.results-container .el-col:nth-child(5)  { animation-delay: 0.32s; }
.results-container .el-col:nth-child(6)  { animation-delay: 0.40s; }
.results-container .el-col:nth-child(7)  { animation-delay: 0.48s; }
.results-container .el-col:nth-child(8)  { animation-delay: 0.56s; }
.results-container .el-col:nth-child(9)  { animation-delay: 0.64s; }
.results-container .el-col:nth-child(10) { animation-delay: 0.72s; }

@keyframes cardPopIn {
  0% {
    opacity: 0;
    transform: translateY(28px) scale(0.92);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* =========== 响应式适配 =========== */
@media (max-width: 992px) {
  .scores-grid {
    grid-template-columns: 1fr;
  }
  
  .match-detail-bottom {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .matching-container {
    padding: 20px 16px;
  }
  
  .glass-select :deep(.el-select__wrapper) {
    margin-bottom: 16px;
  }
  
  .match-detail-header {
    flex-direction: column;
    gap: 20px;
  }
  
  .detail-overall-match {
    width: 100%;
  }
}

/* =========== 玻璃拟态确认弹窗 (参考 Admin 风格) =========== */
:deep(.glass-confirm-dialog) {
  background: rgba(255, 255, 255, 0.75) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.6) !important;
  border-radius: 24px !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1) !important;
  overflow: hidden;
}

:deep(.glass-confirm-dialog .el-dialog__header) {
  display: none;
}

:deep(.glass-confirm-dialog .el-dialog__body) {
  padding: 0;
}

.dialog-inner {
  padding: 32px 32px 10px;
}

.dialog-title {
  margin: 0 0 16px;
  font-size: 20px;
  color: #2d3748;
  text-align: center;
  font-weight: 700;
}

.dialog-message {
  text-align: center;
  color: #4a5568;
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
}

.dialog-footer {
  padding: 0 32px 32px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.glass-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-weight: 600;
  padding: 10px 24px;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}
.glass-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.glass-btn-ghost {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  color: #4a5568;
  font-weight: 600;
  transition: all 0.3s;
  padding: 10px 24px;
}
.glass-btn-ghost:hover {
  background: rgba(255, 255, 255, 0.9);
  color: #2d3748;
  transform: translateY(-1px);
}
</style>