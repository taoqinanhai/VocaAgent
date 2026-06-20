<template>
  <div class="page-wrapper">
    <!-- 极具设计感的背景流体光效 -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    <div class="bg-shape shape-3"></div>

    <div class="report-detail-container">
      <!-- 定制化玻璃拟态返回头部 -->
      <div class="glass-page-header fade-in-up">
        <div class="custom-header-content" @click="$router.back()">
          <div class="back-action">
            <el-icon><Back /></el-icon>
            <span>返回报告列表</span>
          </div>
        </div>
      </div>
      
      <div v-if="report" class="detail-content fade-in-up" style="animation-delay: 0.1s;">
        <div class="glass-panel report-card">
          <!-- 报告标题与操作区 -->
          <div class="panel-header report-header">
            <h1 class="header-title gradient-text">{{ report.report_title }}</h1>
            <div class="header-actions">
              <el-button class="glass-secondary-btn hover-lift" @click="exportHTML">
                <el-icon><Download /></el-icon>
                <span>导出 HTML</span>
              </el-button>
              <el-button class="glass-primary-btn hover-lift" @click="exportPDF">
                <el-icon><Document /></el-icon>
                <span>导出 PDF</span>
              </el-button>
            </div>
          </div>
          
          <!-- 报告富文本内容区 -->
          <div class="report-content-wrapper glass-inner-panel">
            <div class="report-html" v-html="report.report_html"></div>
          </div>
        </div>
      </div>
      
      <!-- 骨架屏 (玻璃拟态适配) -->
      <div v-else class="glass-panel skeleton-panel fade-in-up" style="animation-delay: 0.1s;">
        <el-skeleton :rows="15" animated class="glass-skeleton" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Download, Back, Document } from '@element-plus/icons-vue'

const route = useRoute()

const report = ref<any>(null)

// 获取Token
const getToken = () => {
  return localStorage.getItem('token')
}

// 通用Fetch请求函数
const fetchApi = async (url: string, options: RequestInit = {}) => {
  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const response = await fetch(`http://localhost:5000${url}`, {
    ...options,
    headers
  })
  
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  
  return response.json()
}

onMounted(() => {
  const reportId = route.params.id
  if (reportId) {
    loadReport(parseInt(reportId as string))
  }
})

const loadReport = async (reportId: number) => {
  try {
    const data = await fetchApi(`/api/reports/${reportId}`, {
      method: 'GET'
    })
    if (data.success) {
      report.value = data.data
    }
  } catch (error) {
    console.error('加载报告失败', error)
  }
}

const exportHTML = async () => {
  if (!report.value) return
  try {
    const token = getToken()
    const downloadResponse = await fetch(`http://localhost:5000/api/reports/${report.value.id}/download`, {
      method: 'GET',
      headers: {
        'Authorization': token ? `Bearer ${token}` : ''
      }
    })
    if (!downloadResponse.ok) throw new Error(`HTTP ${downloadResponse.status}`)
    const blob = await downloadResponse.blob()
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${report.value.report_title}.html`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(link.href)
  } catch (error) {
    console.error('导出HTML失败', error)
  }
}

const exportPDF = () => {
  if (!report.value) return
  const token = getToken()
  const url = `http://localhost:5000/api/reports/${report.value.id}/download/pdf?token=${encodeURIComponent(token || '')}`
  // 用 a 标签模拟点击，绕过弹窗拦截
  const a = document.createElement('a')
  a.href = url
  a.target = '_blank'
  a.rel = 'noopener'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
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
.report-detail-container {
  position: relative;
  z-index: 1;
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px 24px;
}

/* =========== 自定义返回头部 =========== */
.glass-page-header {
  margin-bottom: 24px;
  display: flex;
}

.custom-header-content {
  display: inline-flex;
  align-items: center;
  padding: 12px 24px;
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 16px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02);
  cursor: pointer;
  transition: all 0.3s ease;
}

.custom-header-content:hover {
  background: rgba(255, 255, 255, 0.6);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.04);
  transform: translateY(-1px);
}

.back-action {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #667eea;
  font-size: 15px;
  font-weight: 600;
  transition: color 0.3s;
}

.custom-header-content:hover .back-action {
  color: #5a67d8;
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
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
}

/* =========== 报告面板区 =========== */
.panel-header {
  padding: 28px 36px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.4);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0.1) 100%);
}

.gradient-text {
  background: linear-gradient(120deg, #1f2937, #3730a3);
  -webkit-background-clip: text;
  color: transparent;
}

.header-title {
  font-size: 26px;
  font-weight: 800;
  margin: 0;
  letter-spacing: 0.5px;
}

/* 玻璃拟态按钮 */
.glass-primary-btn {
  height: 44px;
  border-radius: 12px !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: white !important;
  font-size: 15px !important;
  font-weight: 600 !important;
  padding: 0 24px !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s ease;
}

.glass-primary-btn:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
  box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
}

/* =========== 富文本内容适配 =========== */
.report-content-wrapper {
  margin: 36px;
  padding: 40px;
}

.report-html {
  line-height: 1.9;
  color: #374151;
  font-size: 16px;
  letter-spacing: 0.3px;
}

/* 针对 v-html 中的常用标签进行玻璃拟态适配 */
.report-html :deep(h1),
.report-html :deep(h2),
.report-html :deep(h3),
.report-html :deep(h4) {
  color: #1f2937;
  font-weight: 800;
  margin-top: 1.5em;
  margin-bottom: 0.8em;
}

.report-html :deep(h1) { font-size: 24px; border-bottom: 2px solid rgba(102,126,234,0.3); padding-bottom: 8px;}
.report-html :deep(h2) { font-size: 20px; color: #3730a3;}
.report-html :deep(h3) { font-size: 18px; color: #4f46e5;}

.report-html :deep(p) {
  margin-bottom: 1em;
}

.report-html :deep(strong), 
.report-html :deep(b) {
  color: #111827;
}

.report-html :deep(ul),
.report-html :deep(ol) {
  padding-left: 24px;
  margin-bottom: 1em;
}

.report-html :deep(li) {
  margin-bottom: 0.5em;
}

/* 富文本中如果存在表格 */
.report-html :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5em 0;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.6);
}

.report-html :deep(th), 
.report-html :deep(td) {
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

/* ==================== 骨架屏 ==================== */
.skeleton-panel {
  padding: 40px;
}
.glass-skeleton :deep(.el-skeleton__item) {
  background: linear-gradient(90deg, rgba(255,255,255,0.3) 25%, rgba(255,255,255,0.6) 37%, rgba(255,255,255,0.3) 63%);
  background-size: 400% 100%;
}

/* ==================== 动画 ==================== */
.fade-in-up {
  animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(30px); }
  100% { opacity: 1; transform: translateY(0); }
}

/* =========== 响应式适配 =========== */
@media (max-width: 768px) {
  .report-detail-container {
    padding: 20px 16px;
  }
  
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 20px 24px;
  }
  
  .header-title {
    font-size: 22px;
  }
  
  .report-content-wrapper {
    margin: 20px 16px;
    padding: 20px;
  }
}
</style>