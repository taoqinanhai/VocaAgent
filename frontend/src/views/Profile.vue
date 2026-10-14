<template>
  <div class="page-wrapper">
    <!-- 极具设计感的背景流体光效，高度模糊与主系统背景融合 -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    <div class="bg-shape shape-3"></div>

    <div class="profile-container">
      <!-- 页面标题区域 -->
      <div class="glass-page-header fade-in-up">
        <div class="header-content">
          <h1 class="gradient-text page-title">我的能力画像</h1>
          <p class="subtitle">全面解析个人能力维度，获取 AI 专属职业规划建议</p>
        </div>
      </div>
      
      <!-- 已有学生画像列表 -->
      <div class="glass-panel students-list-panel fade-in-up" style="animation-delay: 0.1s;">
        <div class="panel-header">
          <h2 class="header-title">已有学生画像</h2>
          <el-button class="glass-btn-small hover-lift" @click="loadStudentsList(true)">
            <el-icon><RefreshRight /></el-icon> 刷新列表
          </el-button>
        </div>
        
        <div class="glass-table-wrapper">
          <el-table :data="studentsList" style="width: 100%" class="glass-table" :empty-text="'暂无数据'">
            <el-table-column type="index" label="序号" width="70" align="center" />
            <el-table-column prop="name" label="姓名" min-width="120" />
            <el-table-column prop="school" label="学校" min-width="180" />
            <el-table-column prop="major" label="专业" min-width="160" />
            <el-table-column prop="education" label="学历" width="100" />
            <el-table-column prop="competitiveness_score" label="竞争力评分" width="140" align="center">
              <template #default="scope">
                <span class="score-text" :class="getScoreClass(scope.row.competitiveness_score)">
                  {{ scope.row.competitiveness_score?.toFixed(1) || '0.0' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right" align="center">
              <template #default="scope">
                <div class="table-actions">
                  <el-button 
                    class="action-btn view-btn"
                    link
                    @click="viewStudentProfile(scope.row.id)"
                  >
                    查看画像
                  </el-button>
                  <span class="action-divider"></span>
                  <el-button 
                    class="action-btn delete-btn"
                    link
                    @click="deleteStudent(scope.row.id, scope.row.name)"
                  >
                    删除
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      
      <el-row :gutter="32">
        <!-- 左侧/上部：创建与建议 -->
        <el-col :xs="24" :lg="24">
          <div class="glass-panel upload-panel fade-in-up" style="animation-delay: 0.2s;">
            <div class="panel-header">
              <h2 class="header-title">创建能力画像</h2>
            </div>
            
            <div class="glass-tabs-wrapper">
              <el-tabs v-model="activeTab" class="glass-tabs">
                <el-tab-pane label="上传简历智能解析" name="upload">
                  <input 
                    type="file" 
                    ref="fileInputRef"
                    accept=".pdf,.doc,.docx,.txt,.rtf,.jpg,.jpeg,.png"
                    style="display: none"
                    @change="handleFileSelect"
                  />
                  <div 
                    class="upload-area-custom glass-item hover-lift"
                    @click="triggerFileInput"
                    @dragover.prevent
                    @drop.prevent="handleDrop"
                  >
                    <div class="upload-icon-wrapper">
                      <el-icon class="el-icon--upload" :size="36"><UploadFilled /></el-icon>
                    </div>
                    <div class="upload-text-main">
                      拖拽文件到此处或 <span class="highlight-text">点击上传</span>
                    </div>
                    <div class="upload-text-sub">
                      只支持 PDF 格式文件
                    </div>
                  </div>
                </el-tab-pane>
                
                <el-tab-pane label="手动填写个人信息" name="manual">
                  <div class="manual-input-section">
                    <el-input
                      v-model="manualInput"
                      type="textarea"
                      :rows="8"
                      placeholder="请输入个人信息，包括姓名、学校、专业、技能、经历等，越详细越好..."
                      class="glass-textarea"
                    />
                    <el-button class="glass-primary-btn hover-lift mt-4" @click="submitManualInput" :loading="submitting">
                      {{ submitting ? 'AI 正在生成中...' : '一键生成能力画像' }}
                    </el-button>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </div>
          </div>
          
          <!-- Agent A 流式生成进度 -->
          <div v-if="streamingActive" class="glass-panel streaming-panel fade-in-up" style="animation-delay: 0.15s;">
            <div class="panel-header">
              <h2 class="header-title">
                <el-icon class="is-loading" :size="20"><Loading /></el-icon>
                AI 正在深度解析简历...
              </h2>
            </div>
            <div class="streaming-content">
              <div class="streaming-text glass-inner-panel">
                <div class="streaming-raw">{{ streamingText || '等待 AI 响应...' }}</div>
                <span class="streaming-cursor">▌</span>
              </div>
            </div>
          </div>

          <!-- 提升建议 -->
          <div v-if="improvementSuggestions.length > 0" class="glass-panel suggestions-panel fade-in-up" style="animation-delay: 0.3s;">
            <div class="panel-header">
              <h2 class="header-title">AI 专属能力提升建议</h2>
            </div>
            <div class="suggestions-content">
              <el-timeline class="glass-timeline">
                <el-timeline-item
                  v-for="(suggestion, index) in improvementSuggestions"
                  :key="index"
                  :type="suggestion.priority === 'high' ? 'danger' : suggestion.priority === 'medium' ? 'warning' : 'primary'"
                  :hollow="true"
                >
                  <div class="timeline-glass-content">
                    <div class="suggestion-header">
                      <h4>{{ suggestion.dimension }}</h4>
                      <el-tag 
                        :type="suggestion.priority === 'high' ? 'danger' : suggestion.priority === 'medium' ? 'warning' : 'info'"
                        effect="light"
                        size="small"
                        class="glass-tag-small"
                      >
                        {{ suggestion.priority === 'high' ? '高优先级' : suggestion.priority === 'medium' ? '中优先级' : '低优先级' }}
                      </el-tag>
                    </div>
                    <p>{{ suggestion.suggestion }}</p>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>
          </div>
        </el-col>
        
        <!-- 下部：能力画像展示 -->
        <el-col :xs="24" :lg="24">
          <div v-if="studentProfile" class="glass-panel profile-display-panel fade-in-up" style="animation-delay: 0.4s;">
            <div class="panel-header profile-header">
              <h2 class="header-title">画像详细分析</h2>
              <div class="competitiveness-badge">
                <span class="label">综合竞争力</span>
                <span class="value" :class="getScoreClass(studentProfile.scores.competitiveness_score)">
                  {{ studentProfile.scores.competitiveness_score.toFixed(1) }}
                </span>
              </div>
              <!-- 新生成画像 → 跳转匹配 -->
              <el-button
                v-if="profileGenerated"
                class="go-matching-btn hover-lift"
                @click="router.push('/matching')"
              >
                前往岗位匹配 <el-icon><Right /></el-icon>
              </el-button>
            </div>
            
            <el-row :gutter="32">
              <el-col :xs="24" :md="10">
                <!-- 雷达图 -->
                <div class="radar-chart glass-inner-panel">
                  <v-chart class="chart" :option="radarOption" autoresize />
                </div>
              </el-col>
              <el-col :xs="24" :md="14">
                <!-- 基本信息 -->
                <div class="profile-section">
                  <h3 class="glass-section-title">基本信息</h3>
                  <div class="glass-descriptions">
                    <el-descriptions :column="2" border class="custom-glass-desc">
                      <el-descriptions-item label="姓名">{{ studentProfile.name }}</el-descriptions-item>
                      <el-descriptions-item label="学校">{{ studentProfile.basic_info.school }}</el-descriptions-item>
                      <el-descriptions-item label="专业">{{ studentProfile.basic_info.major }}</el-descriptions-item>
                      <el-descriptions-item label="学历">{{ studentProfile.basic_info.education }}</el-descriptions-item>
                    </el-descriptions>
                  </div>
                </div>

                <!-- 技能标签 -->
                <div class="profile-section">
                  <h3 class="glass-section-title">专业技能</h3>
                  <div class="skill-tags">
                    <span
                      v-for="skill in studentProfile.ability_profile.professional_skills"
                      :key="skill"
                      class="glass-skill-tag"
                    >
                      {{ skill }}
                    </span>
                  </div>
                </div>
                
                <!-- 证书 -->
                <div v-if="studentProfile.ability_profile.certificates?.length > 0" class="profile-section">
                  <h3 class="glass-section-title">获得证书</h3>
                  <div class="cert-tags">
                    <span
                      v-for="cert in studentProfile.ability_profile.certificates"
                      :key="cert"
                      class="glass-cert-tag"
                    >
                      <el-icon><Medal /></el-icon> {{ cert }}
                    </span>
                  </div>
                </div>
              </el-col>
            </el-row>

            <el-row :gutter="32" class="mt-4">
              <!-- 项目经历 -->
              <el-col :xs="24" :md="12">
                <div class="experience-section glass-inner-panel">
                  <h3 class="glass-section-title">项目经历</h3>
                  <el-timeline v-if="studentProfile.experience.project_experience?.length > 0" class="glass-timeline">
                    <el-timeline-item
                      v-for="(project, index) in studentProfile.experience.project_experience"
                      :key="index"
                      :hollow="true"
                      type="primary"
                    >
                      <div class="timeline-glass-content">
                        <h4>{{ project.name || project.title }}</h4>
                        <div class="exp-meta">
                          <span v-if="project.role" class="role"><el-icon><User /></el-icon> {{ project.role }}</span>
                          <span v-if="project.duration" class="time"><el-icon><Calendar /></el-icon> {{ project.duration }}</span>
                        </div>
                        <p class="exp-desc">{{ project.description }}</p>
                      </div>
                    </el-timeline-item>
                  </el-timeline>
                  <el-empty v-else description="暂无项目经历" class="glass-empty-small" />
                </div>
              </el-col>
              
              <!-- 实习经历 -->
              <el-col :xs="24" :md="12">
                <div class="experience-section glass-inner-panel">
                  <h3 class="glass-section-title">实习经历</h3>
                  <el-timeline v-if="studentProfile.experience.internship_experience?.length > 0" class="glass-timeline">
                    <el-timeline-item
                      v-for="(intern, index) in studentProfile.experience.internship_experience"
                      :key="index"
                      :hollow="true"
                      type="success"
                    >
                      <div class="timeline-glass-content">
                        <h4>{{ intern.position }} <span class="at-text">@</span> {{ intern.company }}</h4>
                        <div class="exp-meta">
                          <span class="time"><el-icon><Calendar /></el-icon> {{ intern.duration }}</span>
                        </div>
                        <p class="exp-desc">{{ intern.description }}</p>
                      </div>
                    </el-timeline-item>
                  </el-timeline>
                  <el-empty v-else description="暂无实习经历" class="glass-empty-small" />
                </div>
              </el-col>
            </el-row>
          </div>
          
          <div v-else class="glass-panel empty-state fade-in-up" style="animation-delay: 0.4s;">
            <el-empty description="您还没有生成任何能力画像" class="glass-empty">
              <template #image>
                <el-icon :size="80" color="rgba(102, 126, 234, 0.5)"><Document /></el-icon>
              </template>
              <el-button class="glass-primary-btn hover-lift" @click="activeTab = 'upload'">
                立即去创建
              </el-button>
            </el-empty>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart } from 'echarts/charts'
import { TitleComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import api from '@/utils/axios'
import { useUserStore } from '@/stores/user'
import { useAgentPipeline } from '@/stores/agentPipeline'
// 统一引入所需的图标
import { UploadFilled, RefreshRight, Document, Medal, User, Calendar, Loading, Right } from '@element-plus/icons-vue'

use([CanvasRenderer, RadarChart, TitleComponent, LegendComponent, TooltipComponent])

const userStore = useUserStore()
const agentPipeline = useAgentPipeline()
const router = useRouter()

const loading = ref(false)

const activeTab = ref('upload')
const submitting = ref(false)
const studentProfile = ref<any>(null)
const improvementSuggestions = ref<any[]>([])
const fileInputRef = ref<HTMLInputElement | null>(null)
const studentsList = ref<any[]>([])

const manualInput = ref('')

// ---- SSE 流式状态 ----
const streamingActive = ref(false)        // 是否正在流式接收
const streamingText = ref('')            // 实时累积的流式文本
const streamingAbort = ref<(() => void) | null>(null)  // 中断函数
const profileGenerated = ref(false)      // 画像是否刚生成完成（用于显示跳转按钮）
let fullResponse = ''                    // 非响应式的完整累积文本
let profileWarning = ''                  // DB 写入警告（避免"成功+警告"矛盾提示）

const commonSkills = [
  'Java', 'Python', 'JavaScript', 'Vue.js', 'React', 'Node.js',
  'MySQL', 'Redis', 'MongoDB', 'Docker', 'Kubernetes',
  '数据分析', '机器学习', '深度学习', 'NLP',
  '产品设计', 'UI设计', '用户体验'
]

// 拟态风格的雷达图配置
const radarOption = computed(() => {
  if (!studentProfile.value) return {}
  
  const abilities = studentProfile.value.ability_profile
  return {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: 'rgba(255, 255, 255, 0.5)',
      textStyle: { color: '#1f2937' },
      backdropFilter: 'blur(10px)',
      padding: [12, 16],
      borderRadius: 12,
      boxShadow: '0 8px 32px rgba(0,0,0,0.1)'
    },
    radar: {
      shape: 'polygon',
      indicator: [
        { name: '专业技能与证书', max: 10 },
        { name: '创新能力', max: 10 },
        { name: '学习能力', max: 10 },
        { name: '抗压能力', max: 10 },
        { name: '沟通能力', max: 10 },
        { name: '实习经历', max: 10 }
      ],
      radius: '65%',
      axisName: {
        color: '#374151',
        fontWeight: 700,
        fontSize: 13,
        padding: [3, 5]
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(255,255,255,0.4)', 'rgba(255,255,255,0.1)']
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(102, 126, 234, 0.15)',
          width: 1,
          type: 'dashed'
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(102, 126, 234, 0.15)'
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          Math.min(studentProfile.value.ability_profile.professional_skills.length * 2, 10),
          abilities.innovation_ability,
          abilities.learning_ability,
          abilities.stress_resistance,
          abilities.communication_ability,
          abilities.internship_experience
        ],
        name: '能力评估',
        symbol: 'circle',
        symbolSize: 8,
        label: {
          show: true,
          color: '#4f46e5',
          fontSize: 12,
          fontWeight: 700,
          formatter: function(params) {
            // 将 1-10 分制转换为 10%-100% 并显示具体分数
            return (params.value * 10) + '%';
          },
          position: 'top',
          distance: 4
        },
        areaStyle: {
          color: 'rgba(102, 126, 234, 0.25)'
        },
        lineStyle: {
          color: '#667eea',
          width: 2
        },
        itemStyle: {
          color: '#667eea',
          borderColor: '#fff',
          borderWidth: 2,
          shadowColor: 'rgba(102, 126, 234, 0.5)',
          shadowBlur: 6
        }
      }]
    }]
  }
})

const getScoreClass = (score: number) => {
  if (!score) return 'score-normal'
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  return 'score-normal'
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  
  await parseResume(file)
  target.value = ''
}

const handleDrop = async (event: DragEvent) => {
  const file = event.dataTransfer?.files?.[0]
  if (!file) return
  
  await parseResume(file)
}

/**
 * 核心：通过 fetch 调 Agent A SSE 流式生成画像
 * 支持文件（FormData）和纯文本（JSON）两种输入
 */
const startProfileStream = async (payload: { file?: File; resume_text?: string }) => {
  profileWarning = ''   // 每次运行重置：上次的警告不能残留到这次
  const token = localStorage.getItem('token')
  const headers: Record<string, string> = { Accept: 'text/event-stream' }
  if (token) headers['Authorization'] = `Bearer ${token}`

  let body: FormData | string
  if (payload.file) {
    const fd = new FormData()
    fd.append('file', payload.file)
    body = fd
    // FormData 不设 Content-Type，让浏览器自动带 boundary
  } else {
    headers['Content-Type'] = 'application/json'
    body = JSON.stringify({ resume_text: payload.resume_text })
  }

  const response = await fetch('http://localhost:5000/api/agent/profile', {
    method: 'POST',
    headers,
    body,
  })

  if (!response.ok) {
    const errText = await response.text().catch(() => 'Unknown')
    throw new Error(`HTTP ${response.status}: ${errText}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('浏览器不支持流式读取')

  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const part of parts) {
        if (!part.trim()) continue
        const lines = part.split('\n')
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith('data: ')) continue
          try {
            const event = JSON.parse(trimmed.slice(6))
            if (event.type === 'chunk' && event.content) {
              fullResponse += event.content
              streamingText.value = fullResponse
            } else if (event.type === 'error') {
              throw new Error(event.message || 'AI 服务错误')
            } else if (event.type === 'done') {
              if (event.result) fullResponse = event.result
              // 捕获 student_id，供后续 Agent B/C 的 DB 持久化
              if (event.student_id) {
                agentPipeline.currentStudentId = event.student_id
                console.log('[Profile] student_id captured:', event.student_id)
              }
              // 显示 DB 写入警告（如果有）
              profileWarning = event.warning || ''
              if (event.warning) {
                console.warn('[Profile] DB 写入警告:', event.warning)
                ElMessage.warning(event.warning)
              }
              return fullResponse
            }
          } catch (e) {
            if (e instanceof Error && e.message !== 'AI 服务错误') continue
            throw e
          }
        }
      }
    }
    return fullResponse
  } finally {
    reader.cancel().catch(() => {})
  }
}

const parseResume = async (file: File) => {
  if (!userStore.isLoggedIn) {
    ElMessage.error('请先登录后再上传简历')
    return
  }

  submitting.value = true
  streamingActive.value = true
  streamingText.value = ''
  profileGenerated.value = false
  fullResponse = ''

  try {
    fullResponse = await startProfileStream({ file })
    handleProfileComplete(fullResponse)
    if (!profileWarning) ElMessage.success('简历解析成功！')
    await loadStudentsList()
  } catch (error: any) {
    ElMessage.error('AI 解析失败：' + (error.message || '网络连接失败'))
  } finally {
    submitting.value = false
    streamingActive.value = false
  }
}

/**
 * 画像完成后的处理：解析 JSON → 写入 store → 转换格式给页面渲染
 */
const handleProfileComplete = (rawText: string) => {
  profileGenerated.value = true
  console.log('Agent A 返回长度:', rawText.length, 'chars')
  console.log('Agent A 前300字:', rawText.slice(0, 300))

  try {
    // 方式0：直接就是纯净 JSON
    let jsonStr = rawText.trim()
    let parsed: any
    try {
      parsed = JSON.parse(jsonStr)
    } catch {
      // 方式1：提取 ```json ... ``` 代码块
      const mdMatch = rawText.match(/```json\s*\n([\s\S]*?)\n\s*```/)
      if (mdMatch) {
        jsonStr = mdMatch[1].trim()
        parsed = JSON.parse(jsonStr)
      } else {
        // 方式2：正则找最外层 { ... }
        const jsonMatch = rawText.match(/\{[\s\S]*\}/)
        if (jsonMatch) {
          jsonStr = jsonMatch[0].trim()
          parsed = JSON.parse(jsonStr)
        } else {
          throw new Error('未找到 JSON')
        }
      }
    }

    console.log('Agent A 解析成功，字段:', Object.keys(parsed))

    // 写入跨页面 store（供 Matching 页面使用）
    agentPipeline.profile = parsed

    // 转换为页面旧的 studentProfile 格式
    studentProfile.value = {
      name: parsed.resume_detail_info?.name || '',
      basic_info: {
        school: parsed.resume_detail_info?.school || '',
        major: parsed.resume_detail_info?.major || '',
        education: parsed.resume_detail_info?.education || '',
      },
      ability_profile: {
        professional_skills: parsed.resume_detail_info?.professional_skills || [],
        certificates: parsed.resume_detail_info?.certificates || [],
        ...parsed.ability_dimension_scores,
      },
      experience: {
        project_experience: parsed.resume_detail_info?.project_experience || [],
        internship_experience: parsed.resume_detail_info?.internship_experience_detail || [],
      },
      scores: {
        competitiveness_score: parsed.ability_overall_scores?.competitiveness_score || 0,
        profile_completeness: parsed.ability_overall_scores?.profile_completeness || 0,
      },
    }
  } catch (e: any) {
    console.error('Profile 解析失败:', e.message)
    console.error('原始文本前500字:', rawText.slice(0, 500))
    ElMessage.error('画像格式解析失败：' + (e.message || '未知错误'))
    // 保留原始文本在流式面板中展示
    streamingText.value = rawText
    streamingActive.value = false
  }
}

const submitManualInput = async () => {
  if (!manualInput.value.trim()) {
    ElMessage.warning('请输入个人信息')
    return
  }

  if (!userStore.isLoggedIn) {
    ElMessage.error('请先登录后再生成画像')
    return
  }

  submitting.value = true
  streamingActive.value = true
  streamingText.value = ''
  profileGenerated.value = false
  fullResponse = ''

  try {
    fullResponse = await startProfileStream({ resume_text: manualInput.value })
    handleProfileComplete(fullResponse)
    if (!profileWarning) ElMessage.success('画像生成成功！')
    await loadStudentsList()
    manualInput.value = ''
  } catch (error: any) {
    ElMessage.error('AI 解析失败：' + (error.message || '网络连接失败'))
  } finally {
    submitting.value = false
    streamingActive.value = false
  }
}

// 页面离开时中断流
onUnmounted(() => {
  if (streamingAbort.value) {
    streamingAbort.value()
  }
})

const loadStudentProfile = async (studentId: number) => {
  try {
    const response = await api.get(`/api/students/${studentId}/profile`)
    if (response.data) {
      studentProfile.value = response.data
      await loadImprovementSuggestions(studentId)
    }
  } catch (error) {
    console.error('加载画像失败', error)
  }
}

const loadImprovementSuggestions = async (studentId: number) => {
  try {
    const response = await api.get(`/api/students/${studentId}/improvement-suggestions`)
    if (response.data.success) {
      improvementSuggestions.value = response.data.data
    }
  } catch (error) {
    console.error('加载建议失败', error)
  }
}

const loadStudentsList = async (showError: boolean = false) => {
  try {
    const response = await api.get('/api/students/list')
    if (response.data.success) {
      studentsList.value = response.data.data
      if (showError && studentsList.value.length === 0) {
        ElMessage.warning('暂无数据')
      } else if (showError) {
        ElMessage.success('列表已刷新')
      }
    }
  } catch (error) {
    console.error('加载学生列表失败', error)
    if (showError) {
      ElMessage.error('加载学生列表失败')
    }
  }
}

const viewStudentProfile = async (studentId: number) => {
  agentPipeline.currentStudentId = studentId  // 同步，确保后续匹配/报告可持久化
  await loadStudentProfile(studentId)
  ElMessage.success('已加载该学生画像')
  // 滚动到画像区域
  window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
}

const deleteStudent = async (studentId: number, studentName: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${studentName}" 的能力画像吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
        customClass: 'glass-msg-box'
      }
    )
    
    const response = await api.delete(`/api/students/${studentId}`)
    if (response.data.success) {
      ElMessage.success('画像已成功删除')
      await loadStudentsList()
      if (studentProfile.value?.id === studentId) {
        studentProfile.value = null
        improvementSuggestions.value = []
      }
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除失败', error)
      ElMessage.error('删除失败')
    }
  }
}

onMounted(async () => {
  loading.value = true
  try {
    await loadStudentsList()
    const studentResponse = await api.get('/api/students/current')
    if (studentResponse.data.success && studentResponse.data.student_id) {
      await loadStudentProfile(studentResponse.data.student_id)
    } else if (studentsList.value.length > 0) {
      await loadStudentProfile(studentsList.value[0].id)
    }
  } catch (error) {
    console.error('初始化数据失败', error)
    if (studentsList.value.length > 0) {
      try {
        await loadStudentProfile(studentsList.value[0].id)
      } catch (e) {}
    }
  } finally {
    loading.value = false
  }
})
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
.profile-container {
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px 24px;
}

/* =========== 页面头部 =========== */
.glass-page-header {
  margin-bottom: 32px;
  padding-left: 12px;
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

.subtitle {
  color: #6b7280;
  font-size: 16px;
  margin: 0;
  font-weight: 500;
  letter-spacing: 0.5px;
}

/* =========== 玻璃拟态基础面板 =========== */
.glass-panel {
  background: rgba(255, 255, 255, 0.4) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.4) !important;
  border-radius: 24px !important;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
  overflow: hidden;
  margin-bottom: 32px;
}

.glass-inner-panel {
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
  padding: 24px;
  height: 100%;
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
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(102, 126, 234, 0.12);
  border-color: rgba(255, 255, 255, 0.9);
}

.panel-header {
  padding: 24px 32px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.1) 100%);
}

.header-title {
  font-size: 20px;
  font-weight: 800;
  color: #1f2937;
  margin: 0;
}

/* =========== 按钮与标签 =========== */
.glass-btn-small {
  background: rgba(255, 255, 255, 0.5) !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  color: #4b5563 !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
}

.glass-btn-small:hover {
  background: rgba(255, 255, 255, 0.9) !important;
  color: #667eea !important;
}

.glass-primary-btn {
  height: 48px;
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

/* =========== 表格区域定制 (彻底去除白底) =========== */
.glass-table-wrapper {
  padding: 16px 32px 32px;
}

.glass-table {
  background: transparent !important;
  --el-table-border-color: rgba(255,255,255,0.2);
  --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(255,255,255,0.5);
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
}

.glass-table :deep(th.el-table__cell) {
  background: rgba(255,255,255,0.3) !important;
  color: #374151;
  font-weight: 700;
  border-bottom: 1px solid rgba(0,0,0,0.05);
}

.glass-table :deep(td.el-table__cell) {
  background: transparent !important;
  border-bottom: 1px solid rgba(255,255,255,0.3);
  color: #4b5563;
  font-weight: 500;
}

.glass-table :deep(.el-table__inner-wrapper::before) {
  display: none;
}

.score-text {
  font-weight: 800;
  font-size: 16px;
}
.score-excellent { color: #10b981; }
.score-good { color: #f59e0b; }
.score-normal { color: #ef4444; }

.table-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.action-btn {
  font-weight: 600 !important;
  font-size: 14px !important;
  padding: 4px 8px !important;
}

.view-btn { color: #667eea !important; }
.view-btn:hover { color: #4f46e5 !important; }

.delete-btn { color: #ef4444 !important; }
.delete-btn:hover { color: #dc2626 !important; }

.action-divider {
  width: 1px;
  height: 14px;
  background-color: rgba(0,0,0,0.1);
}

/* =========== 选项卡与上传区 =========== */
.glass-tabs-wrapper {
  padding: 24px 32px;
}

.glass-tabs :deep(.el-tabs__header) {
  margin-bottom: 24px;
  border-bottom: none;
}
.glass-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: rgba(0,0,0,0.06);
}
.glass-tabs :deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 600;
  color: #6b7280;
  outline: none !important;
  box-shadow: none !important;
}
.glass-tabs :deep(.el-tabs__item.is-active) {
  color: #3730a3;
}
.glass-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, #667eea, #764ba2);
  height: 3px;
  border-radius: 3px;
}

.upload-area-custom {
  width: 100%;
  height: 240px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.upload-icon-wrapper {
  width: 72px;
  height: 72px;
  background: linear-gradient(135deg, rgba(102,126,234,0.2) 0%, rgba(118,75,162,0.2) 100%);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: #667eea;
  transition: transform 0.3s ease;
}

.upload-area-custom:hover .upload-icon-wrapper {
  transform: scale(1.1);
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
}

.upload-text-main {
  font-size: 16px;
  color: #374151;
  font-weight: 600;
  margin-bottom: 8px;
}

.highlight-text {
  color: #667eea;
}

.upload-text-sub {
  font-size: 13px;
  color: #9ca3af;
}

.glass-textarea :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.5) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 14px;
  padding: 16px;
  font-size: 15px;
  transition: all 0.3s ease;
}

.glass-textarea :deep(.el-textarea__inner:hover),
.glass-textarea :deep(.el-textarea__inner:focus) {
  background: rgba(255, 255, 255, 0.8) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.04) !important;
  border-color: rgba(255, 255, 255, 1);
}

/* =========== 建议区域 =========== */
.suggestions-content {
  padding: 32px;
}

.glass-timeline :deep(.el-timeline-item__node) {
  background: transparent;
}
.glass-timeline :deep(.el-timeline-item__tail) {
  border-left: 2px dashed rgba(0,0,0,0.1);
}

.timeline-glass-content {
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.8);
  padding: 16px 20px;
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02);
  transition: transform 0.3s ease, background 0.3s ease;
}

.timeline-glass-content:hover {
  transform: translateX(4px);
  background: rgba(255, 255, 255, 0.8);
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.suggestion-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: #1f2937;
}

.glass-tag-small {
  border: none;
  background: rgba(255,255,255,0.8);
  border-radius: 6px;
  font-weight: 600;
}

/* =========== 画像详情区 =========== */
.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.competitiveness-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.5);
  padding: 8px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.8);
}

.competitiveness-badge .label {
  font-size: 14px;
  font-weight: 600;
  color: #4b5563;
}

.competitiveness-badge .value {
  font-size: 22px;
  font-weight: 800;
}

.radar-chart {
  height: 400px;
}

.profile-section {
  margin-bottom: 32px;
}

.glass-section-title {
  font-size: 18px;
  font-weight: 800;
  color: #1f2937;
  margin-bottom: 20px;
  position: relative;
  display: inline-flex;
  align-items: center;
}

.glass-section-title::before {
  content: '';
  width: 4px;
  height: 18px;
  background: linear-gradient(180deg, #667eea, #764ba2);
  border-radius: 2px;
  margin-right: 10px;
}

/* Descriptions (深度重写) */
.glass-descriptions :deep(.el-descriptions__body) {
  background: transparent;
}
.glass-descriptions :deep(.el-descriptions__table) {
  border: none;
}
.glass-descriptions :deep(td), .glass-descriptions :deep(th) {
  border: 1px solid rgba(255,255,255,0.6) !important;
  background: rgba(255,255,255,0.4) !important;
}
.glass-descriptions :deep(.el-descriptions__label) {
  background: rgba(255,255,255,0.2) !important;
  font-weight: 700;
  color: #4b5563;
  width: 100px;
}
.glass-descriptions :deep(.el-descriptions__content) {
  color: #1f2937;
  font-weight: 600;
}

/* Tags */
.skill-tags, .cert-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.glass-skill-tag {
  padding: 8px 18px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  color: #4f46e5;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  backdrop-filter: blur(4px);
}

.glass-cert-tag {
  padding: 8px 18px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.25);
  color: #059669;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6px;
  backdrop-filter: blur(4px);
}

.experience-section {
  height: 100%;
}

.exp-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 8px;
  font-size: 13px;
  color: #6b7280;
  font-weight: 500;
}

.exp-meta span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.role { color: #667eea; font-weight: 600; }
.at-text { color: #9ca3af; font-weight: normal; margin: 0 4px; }
.exp-desc { color: #4b5563; font-size: 14px; line-height: 1.6; margin: 0; }

.empty-state {
  padding: 60px 20px;
}
.glass-empty :deep(.el-empty__description) {
  font-size: 16px;
  font-weight: 600;
  color: #6b7280;
}
.glass-empty-small {
  padding: 20px;
}

/* ==================== 动画 ==================== */
.fade-in-up {
  animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(30px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* =========== Loading 覆盖 =========== */
:deep(.glass-loading) {
  background: rgba(255, 255, 255, 0.6) !important;
  backdrop-filter: blur(10px);
}

:deep(.glass-loading .el-loading-text) {
  color: #3730a3 !important;
  font-weight: 700;
  font-size: 16px;
  white-space: pre-line;
  line-height: 1.6;
}

:deep(.glass-loading .el-loading-spinner .path) {
  stroke: #667eea !important;
}

/* =========== MessageBox 覆盖 =========== */
:deep(.glass-msg-box) {
  background: rgba(255, 255, 255, 0.85) !important;
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.9);
}

.profile-header {
  flex-direction: row;
  flex-wrap: wrap;
  gap: 16px;
}

/* =========== 流式生成进度面板 =========== */
.streaming-panel {
  margin-bottom: 24px;
  border: 1px solid rgba(102, 126, 234, 0.3) !important;
}

.streaming-content {
  padding: 24px 32px;
}

.streaming-text {
  padding: 20px 24px;
  max-height: 320px;
  overflow-y: auto;
  font-family: 'SF Mono', 'Cascadia Code', 'Fira Code', monospace;
  font-size: 14px;
  line-height: 1.8;
  color: #4b5563;
  white-space: pre-wrap;
  word-break: break-word;
  position: relative;
}

.streaming-raw {
  display: inline;
}

.streaming-cursor {
  display: inline;
  color: #667eea;
  font-weight: 700;
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* =========== 跳转匹配按钮 =========== */
.go-matching-btn {
  height: 44px;
  border-radius: 12px !important;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  border: none !important;
  color: white !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  padding: 0 24px !important;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.go-matching-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.4);
  transform: translateY(-3px);
}

/* =========== 响应式适配 =========== */
@media (max-width: 768px) {
  .profile-container {
    padding: 20px 16px;
  }
  
  .glass-page-header {
    margin-bottom: 24px;
  }

  .glass-table-wrapper {
    padding: 16px;
    overflow-x: auto;
  }

  .radar-chart {
    height: 300px;
    margin-bottom: 24px;
  }
  
  .profile-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
}
</style>