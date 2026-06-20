<template>
  <div class="page-wrapper">
    <!-- 极具设计感的背景流体光效，高度模糊与主系统背景融合 -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    <div class="bg-shape shape-3"></div>

    <div class="job-explore-container">
      <!-- 重新定制的头部：解决原生的对齐和样式问题，完美适配玻璃拟态 -->
      <div class="glass-page-header fade-in-up">
        <div class="custom-header-content" @click="handleBack">
          <div class="back-action">
            <el-icon><Back /></el-icon>
            <span>返回岗位列表</span>
          </div>
          <div class="header-divider"></div>
          <div class="title-action">
            <span>岗位探索详情</span>
          </div>
        </div>
      </div>
      
      <div v-if="job" class="detail-content">
        
        <!-- 岗位基本信息面板 -->
        <div class="glass-panel info-card fade-in-up" style="animation-delay: 0.1s;">
          <div class="job-header">
            <div class="job-title-section">
              <h1 class="gradient-text">{{ job.job_name }}</h1>
              <div class="company-info">
                <span class="glass-tag-info">{{ job.company_name }}</span>
                <span class="glass-tag-info">{{ job.company_industry }}</span>
                <span class="glass-tag-info">{{ job.company_size }}</span>
              </div>
            </div>
            <div class="salary-wrapper">
              <div class="glass-salary-badge">{{ job.salary_range }}</div>
            </div>
          </div>
          
          <div class="glass-divider"></div>
          
          <div class="job-meta">
            <div class="meta-item glass-item hover-lift">
              <div class="meta-icon"><el-icon><Location /></el-icon></div>
              <div class="meta-content">
                <span class="meta-label">工作地点</span>
                <span class="meta-value">{{ job.work_address }}</span>
              </div>
            </div>
            <div v-if="job.education_requirement" class="meta-item glass-item hover-lift">
              <div class="meta-icon"><el-icon><School /></el-icon></div>
              <div class="meta-content">
                <span class="meta-label">学历要求</span>
                <span class="meta-value">{{ job.education_requirement }}</span>
              </div>
            </div>
            <div v-if="job.experience_requirement" class="meta-item glass-item hover-lift">
              <div class="meta-icon"><el-icon><Timer /></el-icon></div>
              <div class="meta-content">
                <span class="meta-label">经验要求</span>
                <span class="meta-value">{{ job.experience_requirement }}</span>
              </div>
            </div>
            <div class="meta-item glass-item hover-lift">
              <div class="meta-icon"><el-icon><Document /></el-icon></div>
              <div class="meta-content">
                <span class="meta-label">岗位编码</span>
                <span class="meta-value">{{ job.job_code }}</span>
              </div>
            </div>
            <div class="meta-item glass-item hover-lift">
              <div class="meta-icon"><el-icon><OfficeBuilding /></el-icon></div>
              <div class="meta-content">
                <span class="meta-label">公司类型</span>
                <span class="meta-value">{{ job.company_nature || '未知' }}</span>
              </div>
            </div>
            <div class="meta-item glass-item hover-lift">
              <div class="meta-icon"><el-icon><PriceTag /></el-icon></div>
              <div class="meta-content">
                <span class="meta-label">所属行业</span>
                <span class="meta-value">{{ job.company_industry || '未知' }}</span>
              </div>
            </div>
            <div class="meta-item glass-item hover-lift">
              <div class="meta-icon"><el-icon><UserFilled /></el-icon></div>
              <div class="meta-content">
                <span class="meta-label">公司规模</span>
                <span class="meta-value">{{ job.company_size || '未知' }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 岗位详情与描述面板 -->
        <div class="glass-panel detail-card fade-in-up" style="animation-delay: 0.2s;">
          <div class="panel-header">
            <h2 class="header-title">探索详情</h2>
          </div>

          <!-- 公司详情 -->
          <div v-if="job.company_description" class="content-section">
            <h3 class="section-title">公司详情</h3>
            <div class="description-box glass-inner-panel company-desc">
              {{ job.company_description }}
            </div>
          </div>
          
          <!-- 岗位描述 -->
          <div class="content-section">
            <h3 class="section-title">岗位描述</h3>
            <div class="description-box glass-inner-panel">
              {{ job.job_description }}
            </div>
          </div>
          
          <!-- 岗位来源 -->
          <div v-if="job.job_source_url" class="content-section source-section">
            <h3 class="section-title">岗位来源</h3>
            <a :href="job.job_source_url" target="_blank" class="glass-source-link">
              <el-icon><Link /></el-icon>
              <span>查看原始招聘信息</span>
            </a>
          </div>
        </div>

      </div>
      
      <!-- 骨架屏 (毛玻璃适配) -->
      <div v-else class="glass-panel skeleton-panel fade-in-up">
        <el-skeleton :rows="10" animated class="glass-skeleton" />
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from '@/utils/axios'
// 统一引入所需图标，修复了 Building 不存在的报错，替换为 PriceTag
import {
  Location, School, Timer, Document, OfficeBuilding, PriceTag, UserFilled, Link, Back
} from '@element-plus/icons-vue'

// 岗位名称到技能要求的映射表
const jobSkillsMap = {
  // 技术类岗位
  '前端开发工程师': ['HTML', 'CSS', 'JavaScript', 'React', 'Vue', 'TypeScript', 'Webpack', 'Git'],
  '后端开发工程师': ['Java', 'Python', 'Node.js', 'Spring', 'Flask', 'Django', 'MySQL', 'PostgreSQL'],
  '全栈开发工程师': ['HTML', 'CSS', 'JavaScript', 'React', 'Vue', 'Node.js', 'Express', 'MongoDB', 'Git'],
  'Java开发工程师': ['Java', 'Spring', 'Spring Boot', 'MySQL', 'Maven', 'Git'],
  'Python开发工程师': ['Python', 'Django', 'Flask', 'MySQL', 'MongoDB', 'Git'],
  '测试工程师': ['Python', 'Selenium', 'Jest', 'Postman', 'MySQL', 'Git'],
  'DevOps工程师': ['Linux', 'Docker', 'Kubernetes', 'AWS', 'Git', 'CI/CD'],
  '数据工程师': ['Python', 'SQL', 'Hadoop', 'Spark', 'AWS', 'Git'],
  '数据分析师': ['Python', 'SQL', 'Excel', 'Tableau', 'Power BI', 'Statistics'],
  '机器学习工程师': ['Python', 'TensorFlow', 'PyTorch', 'Scikit-learn', 'SQL', 'Git'],
  '人工智能工程师': ['Python', 'TensorFlow', 'PyTorch', 'NLP', 'Computer Vision', 'Git'],
  '算法工程师': ['Python', 'C++', 'Machine Learning', 'Data Structures', 'Algorithms', 'Git'],
  '嵌入式开发工程师': ['C', 'C++', 'ARM', 'Linux', 'RTOS', 'Git'],
  '游戏开发工程师': ['C++', 'Unity', 'Unreal Engine', 'OpenGL', 'Git'],
  '移动开发工程师': ['Java', 'Kotlin', 'Swift', 'React Native', 'Flutter', 'Git'],
  'UI/UX设计师': ['Figma', 'Adobe XD', 'Sketch', 'Photoshop', 'Illustrator', 'User Research'],
  '产品经理': ['Product Management', 'User Stories', 'Agile', 'JIRA', 'Wireframing', 'Prototyping'],
  '项目经理/主管': ['Project Management', 'Agile', 'Scrum', 'JIRA', 'Risk Management', 'Communication'],
  '运维工程师': ['Linux', 'Networking', 'Docker', 'Kubernetes', 'AWS', 'Monitoring'],
  '网络工程师': ['Networking', 'Cisco', 'TCP/IP', 'Firewall', 'Security', 'Routing'],
  '安全工程师': ['Security', 'Network Security', 'Penetration Testing', 'Vulnerability Assessment', 'Firewall', 'Encryption'],
  
  // 非技术类岗位
  '销售经理': ['Sales', 'Customer Relationship', 'Negotiation', 'Communication', 'CRM', 'Market Research'],
  '市场营销专员': ['Marketing', 'Social Media', 'Content Creation', 'SEO', 'Analytics', 'Communication'],
  '人力资源专员': ['HR', 'Recruitment', 'Onboarding', 'Performance Management', 'Employee Relations', 'HRIS'],
  '财务专员': ['Accounting', 'Financial Analysis', 'Excel', 'Budgeting', 'Taxation', 'Financial Reporting'],
  '行政专员': ['Administration', 'Office Management', 'Organization', 'Communication', 'Problem Solving', 'Time Management'],
  '市场专员': ['Marketing', 'Social Media', 'Content Creation', 'Event Planning', 'Analytics', 'Communication'],
  '客服专员': ['Customer Service', 'Communication', 'Problem Solving', 'Patience', 'Active Listening', 'CRM'],
  '运营专员': ['Operations', 'Project Management', 'Data Analysis', 'Communication', 'Problem Solving', 'Process Improvement'],
  '商务专员': ['Business Development', 'Sales', 'Negotiation', 'Communication', 'Market Research', 'Relationship Management'],
  '公关专员': ['Public Relations', 'Communication', 'Media Relations', 'Content Creation', 'Event Planning', 'Crisis Management']
}

// 根据岗位名称获取技能要求
const getSkillsByJobName = (jobName: string): string[] => {
  for (const [key, skills] of Object.entries(jobSkillsMap)) {
    if (jobName.includes(key)) {
      return skills
    }
  }
  return ['沟通能力', '团队协作', '问题解决', '学习能力']
}

const route = useRoute()
const router = useRouter()

const job = ref<any>(null)

const jobId = computed(() => parseInt(route.params.id as string))

onMounted(async () => {
  await loadJobDetail()
})

const loadJobDetail = async () => {
  try {
    let basicResponse
    
    // 检查是否从匹配页面跳转过来
    const studentId = route.query.studentId
    const matchRank = route.query.matchRank
    
    if (studentId && matchRank) {
      // 使用新的API接口，通过学生ID和匹配排名获取岗位详情
      const apiUrl = `http://localhost:5000/api/students/${studentId}/matches/${matchRank}/job`
      basicResponse = await axios.get(apiUrl)
    } else {
      // 使用原始API接口
      basicResponse = await axios.get(`http://localhost:5000/api/jobs/${jobId.value}`)
    }
    
    // 处理数据，将nan替换为无
    const processValue = (value) => {
      return value === 'nan' || value === null || value === undefined ? '无' : value
    }
    
    // 处理数据结构
    job.value = {
      ...basicResponse.data,
      job_name: processValue(basicResponse.data.job_name),
      salary_range: processValue(basicResponse.data.salary_range),
      company_name: processValue(basicResponse.data.company_name),
      work_address: processValue(basicResponse.data.work_address),
      industry: processValue(basicResponse.data.industry),
      company_type: processValue(basicResponse.data.company_type),
      job_code: processValue(basicResponse.data.job_code),
      job_description: processValue(basicResponse.data.job_description),
      update_date: processValue(basicResponse.data.update_date),
      company_description: processValue(basicResponse.data.company_description),
      job_source_url: processValue(basicResponse.data.job_source_url),
      profile: {
        professional_skills: getSkillsByJobName(basicResponse.data.job_name),
        professional_skills_certificates: basicResponse.data.ability_requirement_scores?.professional_skills_certificates || 0,
        innovation_ability: basicResponse.data.profile?.innovation_ability || basicResponse.data.ability_requirement_scores?.innovation_ability || 0,
        learning_ability: basicResponse.data.profile?.learning_ability || basicResponse.data.ability_requirement_scores?.learning_ability || 0,
        stress_resistance: basicResponse.data.profile?.stress_resistance || basicResponse.data.ability_requirement_scores?.stress_resistance || 0,
        communication_ability: basicResponse.data.profile?.communication_ability || basicResponse.data.ability_requirement_scores?.communication_ability || 0,
        internship_ability: basicResponse.data.profile?.internship_ability || basicResponse.data.ability_requirement_scores?.internship_experience || 0,
        certificate_requirements: basicResponse.data.profile?.certificate_requirements || []
      },
      company_industry: processValue(basicResponse.data.company_industry || basicResponse.data.industry),
      company_size: processValue(basicResponse.data.company_size),
      company_nature: processValue(basicResponse.data.company_nature || basicResponse.data.company_type)
    }
    
  } catch (error) {
    console.error('加载岗位详情失败', error)
  }
}

const handleBack = () => {
  // 检查是否从匹配页面跳转过来
  const studentId = route.query.studentId
  const matchRank = route.query.matchRank
  
  if (studentId && matchRank) {
    // 返回到匹配页面，并带上studentId参数
    router.push({
      path: '/matching',
      query: { studentId: studentId }
    })
  } else {
    // 返回到岗位列表
    router.push('/jobs')
  }
}
</script>

<style scoped>
/* =========== 整体页面背景与流体光晕 =========== */
.page-wrapper {
  min-height: 100%;
  position: relative;
  /* 移除固定背景色，完全透明以融入主系统背景 */
  background: transparent;
  overflow: hidden;
  border-radius: 16px;
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px); /* 高度模糊让色彩更柔和 */
  z-index: 0;
  opacity: 0.45; /* 降低不透明度 */
  animation: float 18s ease-in-out infinite;
}

.shape-1 {
  top: -15%;
  left: -5%;
  width: 600px;
  height: 600px;
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
}

.shape-2 {
  bottom: -15%;
  right: -10%;
  width: 700px;
  height: 700px;
  background: linear-gradient(135deg, #c2e9fb 0%, #a1c4fd 100%);
  animation-delay: -5s;
}

.shape-3 {
  top: 35%;
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
.job-explore-container {
  position: relative;
  z-index: 1;
  max-width: 1280px;
  margin: 0 auto;
  padding: 30px 24px;
}

/* =========== 自定义头部 =========== */
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
  gap: 6px;
  color: #667eea;
  font-size: 15px;
  font-weight: 500;
  transition: color 0.3s;
}

.custom-header-content:hover .back-action {
  color: #5a67d8;
}

.header-divider {
  width: 1px;
  height: 16px;
  background-color: rgba(0, 0, 0, 0.08);
  margin: 0 16px;
}

.title-action {
  color: #1a202c;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

/* =========== 玻璃拟态基础样式 =========== */
.glass-panel {
  background: rgba(255, 255, 255, 0.4) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.4) !important;
  border-radius: 24px !important;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  overflow: hidden;
}

.glass-panel:hover {
  box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.08) !important;
}

.glass-inner-panel {
  background: rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
}

.glass-item {
  background: rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  border-radius: 16px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.hover-lift:hover {
  background: rgba(255, 255, 255, 0.55);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
}

/* =========== 基本信息面板 =========== */
.info-card {
  margin-bottom: 32px;
  padding-bottom: 24px;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 36px 36px 12px;
}

.gradient-text {
  font-size: 38px;
  font-weight: 800;
  margin: 0 0 18px 0;
  background: linear-gradient(120deg, #1f2937, #3730a3);
  -webkit-background-clip: text;
  color: transparent;
  letter-spacing: -0.5px;
}

.company-info {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 0;
}

.glass-tag-info {
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 10px;
  font-size: 14px;
  color: #4b5563;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.glass-salary-badge {
  padding: 12px 28px;
  border-radius: 18px;
  font-weight: 800;
  font-size: 26px;
  color: #059669;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.1);
  text-shadow: 0 1px 2px rgba(255,255,255,0.8);
}

.glass-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,0,0,0.05), transparent);
  margin: 20px 36px;
}

.job-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  padding: 12px 36px 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  padding: 16px 22px;
  gap: 14px;
  flex: 1 1 calc(25% - 16px);
  min-width: 240px;
}

.meta-icon {
  width: 42px;
  height: 42px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #5a67d8;
  font-size: 20px;
}

.meta-content {
  display: flex;
  flex-direction: column;
}

.meta-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 4px;
  font-weight: 500;
}

.meta-value {
  font-size: 15px;
  color: #1f2937;
  font-weight: 700;
}

/* =========== 详情与描述面板 =========== */
.panel-header {
  padding: 28px 36px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  margin-bottom: 32px;
  background: rgba(255,255,255,0.15);
}

.header-title {
  font-weight: 800;
  font-size: 22px;
  color: #111827;
  letter-spacing: 0.5px;
  margin: 0;
}

.content-section {
  padding: 0 36px;
  margin-bottom: 44px;
}

.section-title {
  font-size: 19px;
  font-weight: 800;
  margin-bottom: 24px;
  color: #1f2937;
  position: relative;
  padding-bottom: 12px;
  display: inline-block;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, #667eea, transparent);
  border-radius: 4px;
}

/* 文本描述块 */
.description-box {
  line-height: 1.9;
  color: #374151;
  font-size: 15px;
  padding: 28px;
  letter-spacing: 0.5px;
  white-space: pre-wrap;
}

.company-desc {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
}

/* 链接样式 */
.glass-source-link {
  color: #4f46e5;
  text-decoration: none;
  word-break: break-all;
  font-weight: 700;
  padding: 16px 28px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(0,0,0,0.02);
}

.glass-source-link:hover {
  background: rgba(255, 255, 255, 0.8);
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(79, 70, 229, 0.1);
  color: #3730a3;
}

/* ==================== 骨架屏 ==================== */
.skeleton-panel {
  padding: 36px;
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
  .job-explore-container {
    padding: 20px 16px;
  }
  
  .job-header {
    flex-direction: column;
    padding: 24px;
    gap: 20px;
  }
  
  .gradient-text {
    font-size: 28px;
  }
  
  .company-info {
    flex-direction: column;
    gap: 10px;
  }
  
  .job-meta {
    padding: 10px 24px 24px;
    grid-template-columns: 1fr;
    gap: 14px;
  }
  
  .meta-item {
    width: 100%;
    min-width: 100%;
  }
  
  .panel-header {
    padding: 20px 24px;
  }
  
  .content-section {
    padding: 0 24px;
    margin: 0 0 32px 0;
  }
}
</style>