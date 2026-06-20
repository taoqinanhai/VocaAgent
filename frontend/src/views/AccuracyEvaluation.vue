1<template>
  <div class="accuracy-container">
    <div class="page-header">
      <h1 class="page-title">
        <span class="gradient-text">准确率评估</span>
      </h1>
      <p class="page-subtitle">AI 智能体人岗匹配与画像生成效果自动化分析</p>
    </div>
    
    <!-- 控制面板 (毛玻璃风格) -->
    <div class="control-panel glass-panel fade-in-up" style="animation-delay: 0.1s;">
      <div class="control-actions">
        <div class="input-group">
          <span class="input-label">抽样数量</span>
          <el-input-number
            v-model="sampleSize"
            :min="1"
            :max="10"
            :step="1"
            class="glass-input-number"
          />
        </div>
        <el-button class="glass-btn-primary" @click="startEvaluation" :loading="evaluating">
          <el-icon class="btn-icon"><DataAnalysis /></el-icon>
          开始评估
        </el-button>
      </div>
      
      <!-- 自定义毛玻璃 Alert -->
      <div 
        v-if="evaluationResult" 
        class="glass-alert"
        :class="evaluationResult.overall_valid ? 'alert-success' : 'alert-warning'"
      >
        <el-icon class="alert-icon">
          <CircleCheck v-if="evaluationResult.overall_valid" />
          <Warning v-else />
        </el-icon>
        <span class="alert-text">{{ evaluationResult.message }}</span>
      </div>
    </div>
    
    <!-- 评估结果展示区 -->
    <div v-if="evaluationResult" class="evaluation-results">
      <el-row :gutter="24">
        <!-- 技能匹配准确率 -->
        <el-col :xs="24" :md="12">
          <div class="result-card glass-panel fade-in-up" style="animation-delay: 0.2s;">
            <div class="card-header">
              <div class="header-title">
                <div class="icon-wrapper primary-gradient">
                  <el-icon><Connection /></el-icon>
                </div>
                <span>技能匹配准确率</span>
              </div>
              <span :class="['glass-tag', evaluationResult.skill_matching.is_valid ? 'tag-success' : 'tag-danger']">
                {{ evaluationResult.skill_matching.is_valid ? '已达标' : '未达标' }}
              </span>
            </div>
            
            <div class="metric-main">
              <div class="metric-header">
                <span class="metric-label">平均准确率</span>
                <span class="metric-value" :class="getAccuracyClass(evaluationResult.skill_matching.average_accuracy)">
                  {{ (evaluationResult.skill_matching.average_accuracy * 100).toFixed(2) }}<span class="percent">%</span>
                </span>
              </div>
              
              <el-progress
                :percentage="evaluationResult.skill_matching.average_accuracy * 100"
                :color="getProgressColor(evaluationResult.skill_matching.average_accuracy)"
                :stroke-width="14"
                class="glass-progress"
                :show-text="false"
              />
              <div class="threshold-info">
                <span>基准阈值</span>
                <span>{{ (evaluationResult.skill_matching.threshold * 100).toFixed(0) }}%</span>
              </div>
            </div>
            
            <div class="metric-stats">
              <div class="stat-box glass-tile">
                <span class="stat-label">最低准确率</span>
                <span class="stat-val">{{ (evaluationResult.skill_matching.min_accuracy * 100).toFixed(1) }}%</span>
              </div>
              <div class="stat-box glass-tile">
                <span class="stat-label">最高准确率</span>
                <span class="stat-val">{{ (evaluationResult.skill_matching.max_accuracy * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </el-col>
        
        <!-- 画像准确率 -->
        <el-col :xs="24" :md="12">
          <div class="result-card glass-panel fade-in-up" style="animation-delay: 0.3s;">
            <div class="card-header">
              <div class="header-title">
                <div class="icon-wrapper secondary-gradient">
                  <el-icon><User /></el-icon>
                </div>
                <span>画像生成准确率</span>
              </div>
              <span :class="['glass-tag', evaluationResult.profile_accuracy.is_valid ? 'tag-success' : 'tag-danger']">
                {{ evaluationResult.profile_accuracy.is_valid ? '已达标' : '未达标' }}
              </span>
            </div>
            
            <div class="metric-main">
              <div class="metric-header">
                <span class="metric-label">平均准确率</span>
                <span class="metric-value" :class="getAccuracyClass(evaluationResult.profile_accuracy.average_accuracy)">
                  {{ (evaluationResult.profile_accuracy.average_accuracy * 100).toFixed(2) }}<span class="percent">%</span>
                </span>
              </div>
              
              <el-progress
                :percentage="evaluationResult.profile_accuracy.average_accuracy * 100"
                :color="getProgressColor(evaluationResult.profile_accuracy.average_accuracy)"
                :stroke-width="14"
                class="glass-progress"
                :show-text="false"
              />
              <div class="threshold-info">
                <span>基准阈值</span>
                <span>{{ (evaluationResult.profile_accuracy.threshold * 100).toFixed(0) }}%</span>
              </div>
            </div>
            
            <div class="metric-stats">
              <div class="stat-box glass-tile">
                <span class="stat-label">最低准确率</span>
                <span class="stat-val">{{ (evaluationResult.profile_accuracy.min_accuracy * 100).toFixed(1) }}%</span>
              </div>
              <div class="stat-box glass-tile">
                <span class="stat-label">最高准确率</span>
                <span class="stat-val">{{ (evaluationResult.profile_accuracy.max_accuracy * 100).toFixed(1) }}%</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
      
      <!-- 抽样信息底部栏 -->
      <div class="sample-info-bar glass-panel fade-in-up" style="animation-delay: 0.4s;">
        <div class="info-item">
          <el-icon class="info-icon"><DocumentChecked /></el-icon>
          <span class="label">本次抽样数量：</span>
          <span class="value">{{ evaluationResult.sample_size }} 份数据</span>
        </div>
        <div class="info-item">
          <el-icon class="info-icon"><Timer /></el-icon>
          <span class="label">评估生成时间：</span>
          <span class="value">{{ new Date().toLocaleString() }}</span>
        </div>
      </div>
    </div>
    
    <!-- 空状态 (玻璃拟态) -->
    <div v-else class="empty-state glass-panel fade-in-up" style="animation-delay: 0.2s;">
      <el-empty description="系统就绪，请设置抽样数量并点击“开始评估”">
        <template #image>
          <div class="empty-icon-wrapper">
            <el-icon :size="64"><Odometer /></el-icon>
          </div>
        </template>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useUserStore } from '@/stores/user'
import { 
  DataAnalysis, 
  CircleCheck, 
  Warning, 
  Connection, 
  User, 
  DocumentChecked, 
  Timer,
  Odometer 
} from '@element-plus/icons-vue'

const userStore = useUserStore()
const sampleSize = ref(1)
const evaluating = ref(false)
const evaluationResult = ref<any>(null)

const startEvaluation = async () => {
  evaluating.value = true
  try {
    const response = await axios.post('/api/students/accuracy-evaluation', null, {
      params: { 
        sample_size: sampleSize.value,
        token: userStore.token
      }
    })
    if (response.data.success) {
      evaluationResult.value = response.data.data
      ElMessage.success('系统评估完成')
    }
  } catch (error) {
    ElMessage.error('评估请求失败，请检查网络或后端服务')
  } finally {
    evaluating.value = false
  }
}

const getAccuracyClass = (accuracy: number) => {
  if (accuracy >= 0.9) return 'color-excellent'
  if (accuracy >= 0.8) return 'color-good'
  if (accuracy >= 0.6) return 'color-moderate'
  return 'color-poor'
}

const getProgressColor = (accuracy: number) => {
  // 配合玻璃拟态的明亮颜色
  if (accuracy >= 0.9) return '#10b981' // emerald-500
  if (accuracy >= 0.8) return '#f59e0b' // amber-500
  return '#ef4444' // red-500
}
</script>

<style scoped>
/* ==================== 基础与排版 ==================== */
.accuracy-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  position: relative;
  z-index: 1;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 32px;
  font-weight: 800;
  margin-bottom: 12px;
  letter-spacing: 0.5px;
}

.page-subtitle {
  font-size: 16px;
  color: #4a5568;
  font-weight: 500;
}

.gradient-text {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

/* ==================== 共享玻璃拟态类 ==================== */
.glass-panel {
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05);
  border-radius: 20px;
  padding: 24px;
}

.glass-tile {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: inset 0 2px 4px rgba(255, 255, 255, 0.6), 0 4px 12px rgba(0, 0, 0, 0.03);
  border-radius: 16px;
}

/* ==================== 顶部控制面板 ==================== */
.control-panel {
  margin-bottom: 30px;
  padding: 24px 30px;
}

.control-actions {
  display: flex;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.input-label {
  font-weight: 600;
  color: #2d3748;
  font-size: 15px;
}

/* 穿透修改 Input Number 样式 */
:deep(.glass-input-number .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.6) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  border-radius: 12px;
  transition: all 0.3s;
}
:deep(.glass-input-number .el-input__wrapper.is-focus) {
  background: rgba(255, 255, 255, 0.9) !important;
  border-color: #667eea !important;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2) !important;
}
:deep(.glass-input-number .el-input-number__decrease),
:deep(.glass-input-number .el-input-number__increase) {
  background: rgba(255, 255, 255, 0.4);
  border: none;
  color: #4a5568;
}
:deep(.glass-input-number .el-input-number__decrease:hover),
:deep(.glass-input-number .el-input-number__increase:hover) {
  color: #667eea;
}

.glass-btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-weight: 600;
  padding: 10px 28px;
  height: 40px;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}
.glass-btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}
.btn-icon {
  margin-right: 6px;
  font-size: 16px;
}

/* 玻璃提示框 */
.glass-alert {
  display: flex;
  align-items: center;
  margin-top: 20px;
  padding: 16px 20px;
  border-radius: 14px;
  font-weight: 600;
  font-size: 14px;
  backdrop-filter: blur(8px);
}
.alert-icon {
  font-size: 18px;
  margin-right: 10px;
}
.alert-success {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: #059669;
}
.alert-warning {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.2);
  color: #d97706;
}

/* ==================== 结果卡片 ==================== */
.result-card {
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.result-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.6);
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}

.icon-wrapper {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 18px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}
.primary-gradient {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.secondary-gradient {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.glass-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  backdrop-filter: blur(4px);
}
.tag-success {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
  border: 1px solid rgba(16, 185, 129, 0.3);
}
.tag-danger {
  background: rgba(239, 68, 68, 0.15);
  color: #dc2626;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.metric-main {
  margin-bottom: 24px;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 12px;
}

.metric-label {
  font-size: 14px;
  color: #4a5568;
  font-weight: 600;
}

.metric-value {
  font-size: 32px;
  font-weight: 800;
  line-height: 1;
}
.metric-value .percent {
  font-size: 18px;
  margin-left: 2px;
}

/* 颜色体系 */
.color-excellent { color: #10b981; }
.color-good { color: #f59e0b; }
.color-moderate { color: #3b82f6; }
.color-poor { color: #ef4444; }

/* 穿透修改进度条样式 */
:deep(.glass-progress .el-progress-bar__outer) {
  background-color: rgba(255, 255, 255, 0.5) !important;
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05);
}
:deep(.glass-progress .el-progress-bar__inner) {
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.threshold-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 13px;
  color: #718096;
  font-weight: 500;
}

.metric-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: auto;
}

.stat-box {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 16px;
}

.stat-label {
  font-size: 12px;
  color: #718096;
  margin-bottom: 6px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-val {
  font-size: 20px;
  font-weight: 700;
  color: #2d3748;
}

/* ==================== 底部信息栏 ==================== */
.sample-info-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 32px;
  align-items: center;
  padding: 20px 30px;
}

.info-item {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.info-icon {
  font-size: 18px;
  color: #667eea;
  margin-right: 8px;
}

.info-item .label {
  color: #718096;
  margin-right: 6px;
}

.info-item .value {
  font-weight: 600;
  color: #2d3748;
}

/* ==================== 空状态 ==================== */
.empty-state {
  padding: 80px 20px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.empty-icon-wrapper {
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  margin: 0 auto;
}

:deep(.el-empty__description p) {
  color: #4a5568;
  font-weight: 500;
  font-size: 15px;
}

/* ==================== 动画 ==================== */
.fade-in-up {
  animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes fadeInUp {
  0% {
    opacity: 0;
    transform: translateY(20px);
  }
  100% {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ==================== 响应式适配 ==================== */
@media (max-width: 768px) {
  .control-actions {
    flex-direction: column;
    align-items: stretch;
  }
  .glass-btn-primary {
    width: 100%;
  }
  .sample-info-bar {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
}
</style>