<template>
  <div class="page-wrapper">
    <!-- 极具设计感的背景流体光效，高度模糊与主系统背景融合 -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    <div class="bg-shape shape-3"></div>

    <div class="jobs-container">
      <!-- 页面标题区域 -->
      <div class="glass-page-header fade-in-up">
        <div class="header-content">
          <h1 class="gradient-text page-title">岗位探索</h1>
          <p class="subtitle">发现海量优质岗位，开启你的职业旅程</p>
        </div>
      </div>
      
      <!-- 搜索栏 (玻璃拟态适配) -->
      <div class="search-section glass-panel fade-in-up" style="animation-delay: 0.1s;">
        <el-row :gutter="20">
          <el-col :xs="24">
            <el-input
              v-model="searchQuery"
              placeholder="搜索岗位名称、公司、技能..."
              clearable
              class="glass-search-input"
              @keyup.enter="handleSearch"
            >
              <template #append>
                <el-button class="glass-search-btn" @click="handleSearch">
                  <el-icon><Search /></el-icon>
                  <span class="btn-text">搜索</span>
                </el-button>
              </template>
            </el-input>
          </el-col>
        </el-row>
      </div>
      
      <!-- 岗位列表 -->
      <div class="job-list-section fade-in-up" style="animation-delay: 0.2s;">
        <el-row :gutter="24">
          <el-col
            v-for="job in paginatedJobs"
            :key="job.id"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
            class="job-col"
          >
            <!-- 替换el-card为自定义的玻璃拟态卡片 -->
            <div class="job-card glass-item hover-lift" @click="viewJobDetail(job.id)">
              <div class="job-header">
                <h3 class="job-title" :title="job.job_name">{{ job.job_name }}</h3>
              </div>
              
              <div class="job-salary">
                <span class="glass-salary-tag">{{ job.salary_range }}</span>
              </div>
              
              <div class="job-company">
                <span class="company-name" :title="job.company_name">{{ job.company_name }}</span>
              </div>
              
              <div class="job-location">
                <el-icon><Location /></el-icon>
                <span>{{ job.work_address }}</span>
              </div>
              
              <div class="job-footer">
                <div class="action-link">
                  <span>查看详情</span>
                  <div class="arrow-icon">→</div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <!-- 分页 (玻璃拟态适配) -->
      <div v-if="total > 0" class="pagination-wrapper glass-panel fade-in-up" style="animation-delay: 0.3s;">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[48, 100, 500, 1000]"
          layout="total, sizes, prev, pager, next"
          class="glass-pagination"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
      
      <!-- 空状态 -->
      <div v-if="jobs.length === 0 && !loading" class="empty-state glass-panel fade-in-up">
        <el-empty description="暂无岗位数据" class="glass-empty" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
// 明确引入所需要的 Element Plus 图标，防止报错
import { Search, Location } from '@element-plus/icons-vue'

const router = useRouter()

const searchQuery = ref('')
const jobs = ref<any[]>([])
const currentPage = ref(1)
const pageSize = ref(48)
const total = ref(0)
const loading = ref(false)

// 前端分页计算属性
const paginatedJobs = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return jobs.value.slice(start, end)
})

onMounted(() => {
  loadJobs()
})

const loadJobs = async () => {
  loading.value = true
  try {
    console.log('开始加载岗位数据...')
    const response = await axios.get('/api/jobs/list', {
      params: {
        skip: 0,
        limit: 1000
      }
    })
    console.log('岗位数据加载成功:', response.data.length, '条记录')
    jobs.value = response.data
    total.value = response.data.length
  } catch (error: any) {
    console.error('加载岗位失败', error)
    if (error.response) {
      console.error('响应错误:', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('请求错误:', error.request)
    } else {
      console.error('其他错误:', error.message)
    }
  } finally {
    loading.value = false
  }
}

const handleSearch = async () => {
  if (!searchQuery.value) {
    loadJobs()
    return
  }
  
  try {
    const response = await axios.get('/api/jobs/search', {
      params: { query: searchQuery.value }
    })
    if (response.data.success) {
      jobs.value = response.data.data
      total.value = response.data.data.length
      currentPage.value = 1 // 搜索后重置回第一页
    }
  } catch (error) {
    console.error('搜索失败', error)
  }
}

const handleSizeChange = (val: number) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val: number) => {
  currentPage.value = val
  // 切换页码时平滑滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const viewJobDetail = (jobId: number) => {
  router.push(`/job-explore/${jobId}`)
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
.jobs-container {
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

.subtitle {
  color: #6b7280;
  font-size: 16px;
  margin: 0;
  font-weight: 500;
  letter-spacing: 0.5px;
}

/* =========== 搜索区域 =========== */
.search-section {
  padding: 24px 32px;
  margin-bottom: 36px;
}

.glass-search-input {
  height: 52px;
}

/* 深度覆盖 Element Plus 输入框样式实现玻璃拟态 */
.glass-search-input :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.6);
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-right: none;
  border-radius: 16px 0 0 16px;
  padding-left: 20px;
  font-size: 16px;
  transition: all 0.3s ease;
}

.glass-search-input :deep(.el-input__wrapper:hover),
.glass-search-input :deep(.el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.9);
}

.glass-search-input :deep(.el-input-group__append) {
  background: transparent;
  box-shadow: none !important;
  border: none;
  padding: 0;
}

.glass-search-btn {
  height: 100%;
  border-radius: 0 16px 16px 0 !important;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  color: white !important;
  padding: 0 32px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  transition: opacity 0.3s ease !important;
}

.glass-search-btn:hover {
  opacity: 0.9;
}

.glass-search-btn .btn-text {
  margin-left: 6px;
}

/* =========== 岗位列表区域 =========== */
.job-col {
  margin-bottom: 24px;
}

.job-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  height: 100%;
  cursor: pointer;
  position: relative;
}

.job-header {
  margin-bottom: 12px;
}

.job-title {
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

.job-card:hover .job-title {
  color: #5a67d8;
}

.job-salary {
  margin-bottom: 16px;
}

.glass-salary-tag {
  display: inline-block;
  padding: 6px 14px;
  border-radius: 12px;
  font-weight: 800;
  font-size: 15px;
  color: #059669;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.job-company {
  margin-bottom: 12px;
}

.company-name {
  color: #4b5563;
  font-size: 14px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.job-location {
  color: #6b7280;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 20px;
  font-weight: 500;
}

.job-location :deep(.el-icon) {
  font-size: 15px;
  color: #9ca3af;
}

.job-footer {
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
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

.job-card:hover .action-link {
  color: #4f46e5;
}

.job-card:hover .arrow-icon {
  transform: translateX(4px);
  background: rgba(102, 126, 234, 0.2);
}

/* =========== 分页区域 =========== */
.pagination-wrapper {
  padding: 16px 32px;
  display: flex;
  justify-content: center;
  margin-top: 12px;
}

.glass-pagination :deep(.el-pagination__total),
.glass-pagination :deep(.el-pagination__sizes .el-input__wrapper) {
  background: transparent;
  box-shadow: none;
  font-weight: 500;
}

.glass-pagination :deep(.btn-prev),
.glass-pagination :deep(.btn-next),
.glass-pagination :deep(.el-pager li) {
  background: rgba(255, 255, 255, 0.5) !important;
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 10px;
  margin: 0 4px;
  backdrop-filter: blur(4px);
  color: #4b5563;
  font-weight: 600;
  transition: all 0.3s ease;
}

.glass-pagination :deep(.el-pager li:hover),
.glass-pagination :deep(.btn-prev:hover),
.glass-pagination :deep(.btn-next:hover) {
  background: rgba(255, 255, 255, 0.9) !important;
  color: #667eea;
}

.glass-pagination :deep(.el-pager li.is-active) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  border: none;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
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
  .jobs-container {
    padding: 20px 16px;
  }
  
  .gradient-text {
    font-size: 28px;
  }
  
  .search-section {
    padding: 16px;
  }
  
  .glass-search-btn .btn-text {
    display: none;
  }
  
  .glass-search-btn {
    padding: 0 20px !important;
  }
  
  .pagination-wrapper {
    padding: 16px;
    overflow-x: auto;
  }
}
</style>