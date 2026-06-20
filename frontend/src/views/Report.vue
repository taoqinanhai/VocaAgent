<template>
  <div class="page-wrapper">
    <!-- 极具设计感的背景流体光效，高度模糊与主系统背景融合 -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    <div class="bg-shape shape-3"></div>

    <div class="report-container">
      <!-- 页面标题区域 -->
      <div class="glass-page-header fade-in-up">
        <div class="header-content">
          <h1 class="gradient-text page-title">职业生涯发展报告</h1>
          <p class="subtitle">基于 AI 深度分析，生成专属您的职业规划与提升指南</p>
        </div>
      </div>
      
      <!-- 报告生成控制区 (玻璃拟态适配) -->
      <div class="control-section glass-panel fade-in-up" style="animation-delay: 0.1s;">
        <el-form :model="reportForm" label-position="top" class="glass-form">
          <el-row :gutter="24" align="bottom">
            <el-col :xs="24" :sm="9" :md="8">
              <el-form-item label="选择学生">
                <el-select
                  v-model="reportForm.studentId"
                  placeholder="请选择学生"
                  style="width: 100%"
                  class="glass-select"
                  @change="onStudentChange"
                >
                  <el-option
                    v-for="student in students"
                    :key="student.id"
                    :label="student.name"
                    :value="student.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="9" :md="8">
              <el-form-item label="选择岗位">
                <el-select
                  v-model="reportForm.jobId"
                  placeholder="请先选择学生"
                  style="width: 100%"
                  class="glass-select"
                  :disabled="!reportForm.studentId || matchJobs.length === 0"
                >
                  <el-option
                    v-for="job in matchJobs"
                    :key="job.job_id"
                    :label="`${job.job_name} — 匹配度 ${job.overall_match_score}%`"
                    :value="job.job_id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="6" :md="8">
              <el-form-item>
                <div class="btn-group">
                  <el-button
                    class="glass-btn-small hover-lift"
                    @click="viewStudentReport"
                    :disabled="!reportForm.studentId || !reportForm.jobId"
                  >
                    <el-icon><Search /></el-icon>
                    <span>查看报告</span>
                  </el-button>
                  <el-button
                    class="glass-primary-btn hover-lift"
                    @click="generateStudentReport"
                    :loading="generating"
                    :disabled="!reportForm.studentId || !reportForm.jobId"
                  >
                    <el-icon><Document /></el-icon>
                    <span>{{ generating ? 'AI 撰写中...' : '生成报告' }}</span>
                  </el-button>
                </div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>
      
      <!-- Agent D 流式报告生成 -->
      <div v-if="streamingReport || streamingHtml" class="report-display fade-in-up" style="animation-delay: 0.15s;">
        <div class="glass-panel report-card">
          <div class="panel-header report-header">
            <h2 class="header-title">
              <el-icon v-if="streamingReport" class="is-loading" :size="20"><Loading /></el-icon>
              {{ streamingReport ? 'AI 正在撰写职业报告...' : 'AI 智能职业规划报告' }}
            </h2>
            <div class="header-actions">
              <el-button v-if="!streamingReport && streamingHtml" class="glass-btn-small hover-lift" @click="exportReportPdf">
                <el-icon><Download /></el-icon> 导出PDF
              </el-button>
              <el-button v-if="!streamingReport && streamingHtml" class="glass-btn-small highlight-btn hover-lift" @click="polishReport" :loading="polishing" :disabled="polishing">
                <el-icon><MagicStick /></el-icon> {{ polishing ? '润色中...' : '智能润色' }}
              </el-button>
            </div>
          </div>
          <div v-if="streamingReport" class="streaming-hint glass-inner-panel" style="margin: 24px 36px; padding: 12px 20px;">
            <span class="hint-text">报告内容实时生成中，无需等待即可阅读...</span>
          </div>
          <div class="report-content-wrapper glass-inner-panel" style="margin: 36px;">
            <div class="report-html streaming-html" v-html="streamingHtml || '<p style=\'color:#9ca3af;text-align:center;padding:60px 0;\'>等待 AI 生成报告内容...</p>'"></div>
          </div>
        </div>
      </div>

      <!-- 历史报告 -->
      <div v-if="reportHistory.length > 0" class="glass-panel history-panel fade-in-up" style="animation-delay: 0.3s;">
        <div class="panel-header">
          <h2 class="header-title">历史报告归档</h2>
        </div>
        <div class="glass-table-wrapper p-6">
          <el-table :data="reportHistory" style="width: 100%" class="glass-table" :empty-text="'暂无历史记录'">
            <el-table-column prop="student_name" label="学生姓名" min-width="100" />
            <el-table-column prop="report_title" label="报告标题" min-width="200" />
            <el-table-column prop="created_at" label="生成时间" min-width="180" />
            <el-table-column label="操作" width="350" fixed="right" align="center">
              <template #default="scope">
                <div class="table-actions">
                  <el-button class="action-btn view-btn" link @click="viewReport(scope.row.id)">查看</el-button>
                  <span class="action-divider"></span>
                  <el-button class="action-btn html-btn" link @click="exportReportById(scope.row.id)">导出 HTML</el-button>
                  <span class="action-divider"></span>
                  <el-button class="action-btn pdf-btn" link @click="exportReportPdfById(scope.row.id)">导出 PDF</el-button>
                  <span class="action-divider"></span>
                  <el-button class="action-btn delete-btn" link @click="deleteReport(scope.row.id)">删除</el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      
      <!-- 确认生成报告弹窗 (Admin 玻璃拟态风格) -->
      <el-dialog
        v-model="showConfirmDialog"
        width="480px"
        class="glass-confirm-dialog"
        :show-close="false"
      >
        <div class="dialog-inner">
          <h3 class="dialog-title">确认生成报告</h3>
          <p class="dialog-message">{{ confirmMessage }}</p>
        </div>
        <template #footer>
          <div class="dialog-footer">
            <el-button class="glass-btn-ghost" @click="showConfirmDialog = false">取消</el-button>
            <el-button class="glass-btn-primary" @click="doGenerateReport" :loading="generating">生成报告</el-button>
          </div>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from '@/utils/axios'
import { useAgentPipeline } from '@/stores/agentPipeline'
// 统一引入所需的图标
import { Document, Download, MagicStick, Loading } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const agentPipeline = useAgentPipeline()

// ---- Agent D SSE 流式状态 ----
const streamingReport = ref(false)
const streamingHtml = ref('')
const currentStreamReportId = ref<number | null>(null)  // Agent D SSE 返回的 report_id，供导出PDF使用
const reportStreamError = ref('')

const reportForm = ref({
  studentId: null as number | null,
  jobId: null as number | null
})

const students = ref<any[]>([])
const matchJobs = ref<any[]>([])
const generating = ref(false)
const reportHistory = ref<any[]>([])
const polishing = ref(false)

// 确认生成报告弹窗
const showConfirmDialog = ref(false)
const confirmMessage = ref('')
const pendingReportStudentId = ref<number | null>(null)

/**
 * 核心：通过 fetch + SSE 调 Agent D 流式生成报告
 */
const triggerAgentDStream = async (profile: Record<string, unknown>, top3: any[], targetJobId: number) => {
  streamingReport.value = true
  reportStreamError.value = ''
  streamingHtml.value = ''
  currentStreamReportId.value = null  // 重置，等 done 事件返回新 ID

  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  try {
    const response = await fetch('http://localhost:5000/api/agent/report', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        student_profile: profile,
        top3_matches: top3,
        student_id: agentPipeline.currentStudentId,
        target_job_id: targetJobId,
      }),
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body?.getReader()
    if (!reader) throw new Error('浏览器不支持流式读取')

    const decoder = new TextDecoder('utf-8')
    let buffer = ''

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
              streamingHtml.value += event.content
            } else if (event.type === 'status') {
              // Agent C 自动串联状态提示
              console.log('[Report]', event.message)
            } else if (event.type === 'error') {
              throw new Error(event.message || 'AI 服务错误')
            } else if (event.type === 'done') {
              // DB 持久化结果通知
              if (event.warning) {
                console.warn('[Report] DB 写入警告:', event.warning)
                ElMessage.warning(event.warning)
              }
              if (event.report_id) {
                currentStreamReportId.value = event.report_id
                console.log('[Report] 报告已保存到数据库, report_id:', event.report_id)
              }
              // ★ 显式关闭加载状态，不依赖 finally
              streamingReport.value = false
              agentPipeline.reportHtml = streamingHtml.value
              ElMessage.success('职业报告生成完成！')
              return
            }
          } catch (e) {
            if (e instanceof Error && e.message !== 'AI 服务错误') continue
            throw e
          }
        }
      }
    }

    // ★ while 正常结束（reader done 但没收到 done 事件）→ 兜底
    streamingReport.value = false
    agentPipeline.reportHtml = streamingHtml.value
    if (streamingHtml.value) {
      ElMessage.success('报告生成完成')
    }
  } catch (err: any) {
    streamingReport.value = false
    reportStreamError.value = err.message || '网络错误'
    ElMessage.error('报告生成失败：' + reportStreamError.value)
  } finally {
    streamingReport.value = false
  }
}

// 初始化
onMounted(async () => {
  // 从URL参数获取 → 预选学生+岗位并自动查DB
  const studentId = route.query.studentId
  const jobId = route.query.jobId
  if (studentId) {
    reportForm.value.studentId = parseInt(studentId as string)
    // 先加载学生列表 + 岗位列表
    await loadStudents()
    await onStudentChange(reportForm.value.studentId)
    if (jobId) {
      reportForm.value.jobId = parseInt(jobId as string)
    }
    await nextTick()
    if (reportForm.value.jobId) {
      await checkAndShowReport()
    }
    return
  }

  loadStudents()
})

onUnmounted(() => {
  // 页面离开时流式连接会自动断开
})

const loadStudents = async () => {
  try {
    const response = await axios.get('/api/students/list')
    if (response.data.success) {
      students.value = response.data.data.map((s: any) => ({
        id: s.id,
        name: s.name
      }))
    }
  } catch (error) {
    console.error('加载学生列表失败', error)
  }
}

/**
 * 选学生 → 加载该生的匹配岗位列表
 */
const onStudentChange = async (studentId: number | null) => {
  reportForm.value.jobId = null
  matchJobs.value = []
  if (!studentId) return
  try {
    const res = await axios.get(`/api/agent/match/${studentId}`)
    if (res.data.exists && res.data.data?.length > 0) {
      matchJobs.value = res.data.data
    } else {
      ElMessage.warning('该学生尚未完成岗位匹配，请先在"岗位匹配"页面生成匹配结果')
    }
  } catch (e) {
    console.error('加载岗位列表失败', e)
  }
}

/**
 * 「查看报告」按钮 → 只查 DB，不生成
 */
const viewStudentReport = async () => {
  if (!reportForm.value.studentId) {
    ElMessage.warning('请先选择学生')
    return
  }
  if (!reportForm.value.jobId) {
    ElMessage.warning('请先选择岗位')
    return
  }
  await checkAndShowReport()
}

/**
 * 「生成报告」按钮 → 弹窗确认 → 调 Agent D 新增报告
 */
const generateStudentReport = async () => {
  const studentId = reportForm.value.studentId
  const jobId = reportForm.value.jobId
  if (!studentId || !jobId) {
    ElMessage.warning('请先选择学生和岗位')
    return
  }
  if (matchJobs.value.length === 0) {
    ElMessage.warning('该学生尚未完成岗位匹配，请先在"岗位匹配"页面生成匹配结果')
    return
  }

  // 获取学生姓名和岗位名用于弹窗提示
  let studentName = ''
  try {
    const studentRes = await axios.get(`/api/agent/match/${studentId}`)
    studentName = studentRes.data.student_name || '该学生'
  } catch { studentName = '该学生' }
  const selectedJob = matchJobs.value.find(j => j.job_id === jobId)
  const jobName = selectedJob?.job_name || `岗位 #${jobId}`

  pendingReportStudentId.value = studentId
  confirmMessage.value = `「${studentName}」在「${jobName}」将生成一份新的职业报告，是否调用 AI 生成？`
  showConfirmDialog.value = true
}

/**
 * 查 DB（student × job）：有报告 → 直接展示 HTML；无报告 → 提示用户点「生成报告」
 */
const checkAndShowReport = async () => {
  const studentId = reportForm.value.studentId
  const jobId = reportForm.value.jobId
  if (!studentId || !jobId) return

  try {
    const res = await axios.get(`/api/agent/report/${studentId}?job_id=${jobId}`)
    if (res.data.exists) {
      // ★ DB 中已有报告 → 直接展示
      streamingHtml.value = res.data.report_html || ''
      streamingReport.value = false
      currentStreamReportId.value = res.data.report_id || null
      agentPipeline.currentStudentId = studentId
      ElMessage.success(`已加载「${res.data.student_name}」的报告 —「${res.data.report_title || ''}」`)
      await loadReportHistory(studentId)
      return
    }

    // ★ DB 中无报告 → 提示用户使用「生成报告」按钮
    const selectedJob = matchJobs.value.find(j => j.job_id === jobId)
    const jobName = selectedJob?.job_name || `岗位 #${jobId}`
    ElMessage.warning(`「${res.data.student_name}」在「${jobName}」暂无报告，请点击右侧「生成报告」按钮创建`)
  } catch (err: any) {
    ElMessage.error('查询报告失败：' + (err.message || '未知错误'))
  }
}

/**
 * 用户在确认弹窗中点击"生成报告" → 加载画像+Top3 → 调 Agent D
 */
const doGenerateReport = async () => {
  const studentId = pendingReportStudentId.value
  const jobId = reportForm.value.jobId
  if (!studentId || !jobId) return

  showConfirmDialog.value = false
  generating.value = true
  agentPipeline.currentStudentId = studentId

  // 加载画像
  let profile = agentPipeline.profile as unknown as Record<string, unknown> | null
  if (!profile) {
    try {
      const profileRes = await axios.get(`/api/students/${studentId}/profile`)
      profile = profileRes.data
    } catch {
      ElMessage.error('无法加载学生画像')
      generating.value = false
      return
    }
  }

  // 加载 Top3 匹配（优先用 store 里的，否则从 DB 查）
  let top3 = agentPipeline.selectedTop3
  if (!top3 || top3.length === 0) {
    try {
      const matchRes = await axios.get(`/api/agent/match/${studentId}`)
      if (matchRes.data.exists && matchRes.data.data?.length > 0) {
        top3 = matchRes.data.data.slice(0, 3)
      } else {
        ElMessage.error('未找到匹配数据，请先在"岗位匹配"页面完成匹配')
        generating.value = false
        return
      }
    } catch {
      ElMessage.error('加载匹配数据失败')
      generating.value = false
      return
    }
  }

  try {
    await triggerAgentDStream(profile!, top3, jobId)
  } catch (err: any) {
    ElMessage.error('报告生成失败：' + (err.message || '未知错误'))
  } finally {
    streamingReport.value = false
    generating.value = false
  }
  // 历史列表异步刷新，不阻塞按钮恢复
  loadReportHistory(studentId).then(() => {
    if (!currentStreamReportId.value && reportHistory.value.length > 0) {
      currentStreamReportId.value = reportHistory.value[0].id
      console.log('[Report] report_id 从历史记录兜底获取:', currentStreamReportId.value)
    }
  })
}

const loadReportHistory = async (studentId: number) => {
  try {
    const response = await axios.get(`/api/reports/student/${studentId}`)
    if (response.data.success) {
      reportHistory.value = response.data.data
    }
  } catch (error) {
    console.error('加载历史报告失败', error)
  }
}

// 获取Token
const getToken = () => {
  return localStorage.getItem('token')
}

const exportReportPdf = async () => {
  const reportId = currentStreamReportId.value
  if (!reportId || isNaN(reportId)) {
    ElMessage.error('报告ID无效，请刷新页面重试');
    return;
  }

  const studentName = students.value.find(s => s.id === reportForm.value.studentId)?.name || '学生'

  try {
    const token = getToken();

    if (!token) {
      ElMessage.error('请先登录');
      return;
    }

    const url = `http://localhost:5000/api/reports/${reportId}/download/pdf`;

    const res = await axios.get(url, {
      headers: { Authorization: 'Bearer ' + token },
      responseType: 'blob',
    });

    const blob = new Blob([res.data], { type: 'application/pdf' });
    const downloadUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `${studentName}_职业发展报告.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(downloadUrl);

    ElMessage.success('PDF报告导出成功！');
  } catch (err: any) {
    console.error('PDF下载失败：', err);
    ElMessage.error('导出PDF报告失败，请稍后重试');
  }
}

const exportReportById = async (reportId: number) => {
  try {
    const token = getToken();

    if (!token) {
      ElMessage.error('请先登录');
      return;
    }

    const url = `http://localhost:5000/api/reports/${reportId}/download`;

    const res = await axios.get(url, {
      headers: { Authorization: 'Bearer ' + token },
      responseType: 'blob', 
    });

    const blob = new Blob([res.data]);
    const downloadUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = `职业规划报告_${reportId}.html`; 
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(downloadUrl);

    ElMessage.success('报告导出成功！');
  } catch (err: any) {
    console.error('下载失败：', err);
    ElMessage.error('导出报告失败');
  }
}

const exportReportPdfById = async (reportId: number) => {
  try {
    const token = getToken();

    if (!token) {
      ElMessage.error('请先登录');
      return;
    }

    const url = `http://localhost:5000/api/reports/${reportId}/download/pdf`;

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Authorization': 'Bearer ' + token,
        'Accept': 'application/pdf'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = `职业规划报告_${reportId}.pdf`;
    document.body.appendChild(link);
    link.click();

    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    }, 1000);

    ElMessage.success('PDF报告导出成功！');
  } catch (err: any) {
    console.error('PDF下载失败：', err);
    ElMessage.error('导出PDF报告失败：' + err.message);
  }
}

const polishReport = async () => {
  const reportId = currentStreamReportId.value
  if (!reportId) {
    ElMessage.warning('请先生成或加载一份报告')
    return
  }

  polishing.value = true
  try {
    const response = await axios.post(`/api/reports/${reportId}/polish`)
    if (response.data.success) {
      const newId = response.data.new_report_id
      ElMessage.success(response.data.message || '报告润色完成')
      // 加载润色版报告到展示区
      if (newId) {
        const res = await axios.get(`/api/reports/${newId}`)
        if (res.data.success) {
          streamingHtml.value = res.data.data.report_html || ''
          streamingReport.value = false
          currentStreamReportId.value = newId
        }
      }
      // 刷新历史报告列表
      if (reportForm.value.studentId) {
        await loadReportHistory(reportForm.value.studentId)
      }
    } else {
      ElMessage.error('润色失败: ' + (response.data.error || '未知错误'))
    }
  } catch (error: any) {
    console.error('润色失败错误:', error)
    ElMessage.error('润色失败')
  } finally {
    polishing.value = false
  }
}

/**
 * 流式模式下重新从 DB 拉取报告 HTML（润色后调用）
 */

const viewReport = async (reportId: number) => {
  try {
    const res = await axios.get(`/api/reports/${reportId}`)
    if (res.data.success) {
      const report = res.data.data
      // ★ 渲染 report_html 到流式布局（和历史报告"查看"共用同一展示区）
      streamingHtml.value = report.report_html || ''
      streamingReport.value = false
      currentStreamReportId.value = reportId
      window.scrollTo({ top: 0, behavior: 'smooth' })
      ElMessage.success('已加载历史报告')
    }
  } catch (e) {
    console.error('加载报告失败', e)
    ElMessage.error('加载报告失败')
  }
}

const deleteReport = async (reportId: number) => {
  try {
    await ElMessageBox.confirm('确定要删除这份报告吗？删除后无法恢复。', '确认删除', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning',
      customClass: 'glass-msg-box'
    })
    
    const token = localStorage.getItem('token')
    const response = await fetch(`http://localhost:5000/api/reports/${reportId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    const data = await response.json()
    if (data.success) {
      ElMessage.success('报告删除成功')
      if (reportForm.value.studentId) {
        await loadReportHistory(reportForm.value.studentId)
      }
    } else {
      ElMessage.error('删除失败')
    }
  } catch (error: any) {
    // cancelled
  }
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
.report-container {
  position: relative;
  z-index: 1;
  max-width: 1200px;
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

/* =========== 玻璃拟态基础样式 =========== */
.glass-panel {
  background: rgba(255, 255, 255, 0.45) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.5) !important;
  border-radius: 24px !important;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
  overflow: hidden;
  margin-bottom: 32px;
}

.glass-inner-panel {
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
}

.hover-lift:hover {
  background: rgba(255, 255, 255, 0.7);
  transform: translateY(-4px);
  box-shadow: 0 10px 24px rgba(102, 126, 234, 0.1);
  border-color: rgba(255, 255, 255, 0.9);
}

.panel-header {
  padding: 24px 32px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, rgba(255,255,255,0.5) 0%, rgba(255,255,255,0.2) 100%);
}

.header-title {
  font-size: 20px;
  font-weight: 800;
  color: #1f2937;
  margin: 0;
}

/* =========== 按钮与表单覆盖 =========== */
.glass-primary-btn {
  height: 50px;
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

.glass-btn-small {
  background: rgba(255, 255, 255, 0.5) !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  color: #4b5563 !important;
  border-radius: 10px !important;
  font-weight: 600 !important;
  padding: 8px 16px !important;
}
.glass-btn-small:hover {
  background: rgba(255, 255, 255, 0.9) !important;
  color: #667eea !important;
}
.highlight-btn {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.15) 100%) !important;
  border-color: rgba(16, 185, 129, 0.4) !important;
  color: #059669 !important;
}
.highlight-btn:hover {
  background: rgba(16, 185, 129, 0.8) !important;
  color: white !important;
}

.w-full { width: 100%; }
.btn-group { display: flex; gap: 8px; }
.btn-group .el-button { flex: 1; }

.control-section {
  padding: 24px 32px;
}
.glass-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #374151;
  font-size: 15px;
}

.glass-select :deep(.el-select__wrapper) {
  background: rgba(255, 255, 255, 0.5);
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 14px;
  min-height: 50px;
  font-size: 15px;
  transition: all 0.3s ease;
}
.glass-select :deep(.el-select__wrapper:hover),
.glass-select :deep(.el-select__wrapper.is-focused) {
  background: rgba(255, 255, 255, 0.85);
  border-color: rgba(255, 255, 255, 1);
  box-shadow: 0 4px 16px rgba(0,0,0,0.04) !important;
}

/* 表格定制化 */
.glass-table-wrapper {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.6);
}
.glass-table {
  background: transparent !important;
  --el-table-border-color: rgba(255,255,255,0.4);
  --el-table-header-bg-color: rgba(255,255,255,0.6);
  --el-table-row-hover-bg-color: rgba(255,255,255,0.6);
  --el-table-bg-color: rgba(255,255,255,0.3);
  --el-table-tr-bg-color: transparent;
}
.glass-table :deep(th.el-table__cell) {
  color: #374151;
  font-weight: 700;
}
.glass-table :deep(td.el-table__cell) {
  color: #4b5563;
  font-weight: 500;
}
/* =========== 历史报告表格定制 =========== */
.history-panel {
  padding-bottom: 10px;
}
.table-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}
.action-btn {
  font-weight: 600 !important;
  font-size: 14px !important;
}
.view-btn { color: #667eea !important; }
.html-btn { color: #10b981 !important; }
.pdf-btn { color: #f59e0b !important; }
.delete-btn { color: #ef4444 !important; }
.action-divider {
  width: 1px;
  height: 14px;
  background-color: rgba(0,0,0,0.1);
}

/* ==================== 动画 ==================== */
.fade-in-up {
  animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(30px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* =========== MessageBox 覆盖 =========== */
:deep(.glass-msg-box) {
  background: rgba(255, 255, 255, 0.85) !important;
  backdrop-filter: blur(20px);
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.9);
}

/* =========== 响应式 =========== */
@media (max-width: 768px) {
  .report-container {
    padding: 20px 16px;
  }
  .table-actions {
    flex-direction: column;
    gap: 8px;
  }
  .action-divider {
    display: none;
  }
}

/* =========== Agent D 流式报告样式 =========== */
.streaming-hint {
  display: flex;
  align-items: center;
  justify-content: center;
}

.hint-text {
  font-size: 14px;
  color: #667eea;
  font-weight: 600;
}

.report-content-wrapper {
  padding: 40px;
}

.report-html {
  line-height: 1.9;
  color: #374151;
  font-size: 16px;
  letter-spacing: 0.3px;
}

.report-html :deep(h1),
.report-html :deep(h2),
.report-html :deep(h3),
.report-html :deep(h4) {
  color: #1f2937;
  font-weight: 800;
  margin-top: 1.5em;
  margin-bottom: 0.8em;
}

.report-html :deep(h1) { font-size: 24px; border-bottom: 2px solid rgba(102,126,234,0.3); padding-bottom: 8px; }
.report-html :deep(h2) { font-size: 20px; color: #3730a3; }
.report-html :deep(h3) { font-size: 18px; color: #4f46e5; }

.report-html :deep(p) { margin-bottom: 1em; }
.report-html :deep(strong), .report-html :deep(b) { color: #111827; }
.report-html :deep(ul), .report-html :deep(ol) { padding-left: 24px; margin-bottom: 1em; }
.report-html :deep(li) { margin-bottom: 0.5em; }

.report-html :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5em 0;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.6);
}

.report-html :deep(th), .report-html :deep(td) {
  border: 1px solid rgba(255,255,255,0.4);
  padding: 12px 16px;
  text-align: left;
}

.report-html :deep(th) {
  background: rgba(255,255,255,0.6);
  font-weight: 700;
  color: #1f2937;
}

.report-html :deep(tr:nth-child(even)) {
  background: rgba(255,255,255,0.2);
}

.streaming-html {
  min-height: 200px;
}

.streaming-html::after {
  content: '';
  display: block;
  height: 60px;
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