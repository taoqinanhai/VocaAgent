<template>
  <div class="page-wrapper">
    <!-- 优化后的富有设计感的背景流体光效，色彩更柔和高级 -->
    <div class="bg-shape shape-1"></div>
    <div class="bg-shape shape-2"></div>
    <div class="bg-shape shape-3"></div>

    <div class="job-detail-container">
      <!-- 重新定制的头部：解决原生的对齐和样式问题，完美适配玻璃拟态 -->
      <div class="glass-page-header fade-in-up">
        <div class="custom-header-content" @click="handleBack">
          <div class="back-action">
            <el-icon><Back /></el-icon>
            <span>返回岗位列表</span>
          </div>
          <div class="header-divider"></div>
          <div class="title-action">
            <span>岗位全景画像</span>
          </div>
        </div>
      </div>
      
      <div v-if="job" class="detail-content">
        <!-- 岗位基本信息 -->
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

          <el-button
            type="warning"
            size="large"
            class="interview-entry-btn"
            @click="goToInterview"
          >
            🚪 敲总监办公室大门
          </el-button>

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
            <div class="meta-item glass-item hover-lift" v-if="job.update_date">
              <div class="meta-icon"><el-icon><Calendar /></el-icon></div>
              <div class="meta-content">
                <span class="meta-label">更新日期</span>
                <span class="meta-value">{{ job.update_date }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 岗位画像主体内容 -->
        <div class="glass-panel profile-card fade-in-up" style="animation-delay: 0.2s;">
          <div class="panel-header">
            <h2 class="header-title">岗位能力画像分析</h2>
          </div>
          
          <!-- AI 正在流式生成中 — 动态状态提示 -->
          <div v-if="aiProfileLoading" class="ai-loading-overlay">
            <div class="ai-loading-card">
              <div class="ai-loading-icon">
                <el-icon class="is-loading" :size="32"><Loading /></el-icon>
              </div>
              <h3 class="ai-loading-title">AI 正在分析岗位画像</h3>
              <p class="ai-loading-status">{{ loadingStatus }}</p>
              <div class="ai-loading-steps">
                <div class="step" :class="{ active: loadingStep >= 1, done: loadingStep > 1 }">
                  <span class="step-dot"></span>
                  <span class="step-label">分析能力要求</span>
                </div>
                <div class="step" :class="{ active: loadingStep >= 2, done: loadingStep > 2 }">
                  <span class="step-dot"></span>
                  <span class="step-label">规划晋升路径</span>
                </div>
                <div class="step" :class="{ active: loadingStep >= 3, done: loadingStep > 3 }">
                  <span class="step-dot"></span>
                  <span class="step-label">分析换岗方向</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 画像内容 — 生成完成后才显示 -->
          <template v-if="!aiProfileLoading">
            <el-row :gutter="32">
            <el-col :xs="24" :lg="24">
              <!-- 能力雷达图 -->
              <div class="radar-chart glass-inner-panel">
                <v-chart class="chart" :option="radarOption" autoresize />
              </div>
              
              <!-- 公司详情 -->
              <div v-if="job.company_description" class="content-section">
                <h3 class="section-title">公司详情</h3>
                <div class="description-box glass-inner-panel company-desc">
                  {{ job.company_description }}
                </div>
              </div>
              
              <!-- 技能要求 -->
              <div class="content-section">
                <h3 class="section-title">专业技能要求</h3>
                <div class="skill-tags">
                  <span
                    v-for="skill in job.profile.professional_skills"
                    :key="skill"
                    class="glass-tag skill-tag"
                  >
                    {{ skill }}
                  </span>
                </div>
              </div>
              
              <!-- 证书要求 -->
              <div v-if="job.profile.certificate_requirements?.length > 0" class="content-section">
                <h3 class="section-title">证书要求</h3>
                <div class="cert-tags">
                  <span
                    v-for="cert in job.profile.certificate_requirements"
                    :key="cert"
                    class="glass-tag cert-tag"
                  >
                    {{ cert }}
                  </span>
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
              <div v-if="job.job_source_url" class="content-section">
                <h3 class="section-title">岗位来源</h3>
                <a :href="job.job_source_url" target="_blank" class="glass-source-link">
                  <el-icon><Link /></el-icon>
                  <span>查看原始招聘信息</span>
                </a>
              </div>
              
              <!-- 职业发展路径 -->
              <div class="content-section">
                <h3 class="section-title">职业发展路径</h3>
                
                <el-row :gutter="24">
                  <!-- 垂直晋升路径 -->
                  <el-col :xs="24" :md="8" :lg="8">
                    <div class="path-container glass-inner-panel">
                      <h4 class="sub-title">垂直晋升路径</h4>
                      <el-timeline class="custom-timeline">
                        <el-timeline-item
                          v-for="(path, index) in careerPaths.vertical_paths"
                          :key="index"
                          :type="index === 0 ? 'primary' : ''"
                          :hollow="index !== 0"
                        >
                          <div class="timeline-glass-content">
                            <h5>{{ path.level }}</h5>
                            <p class="path-title">{{ path.title }}</p>
                            <p class="path-time">{{ path.years }}</p>
                          </div>
                        </el-timeline-item>
                      </el-timeline>
                    </div>
                  </el-col>
                  
                  <!-- 换岗路径 -->
                  <el-col :xs="24" :md="16" :lg="16">
                    <div class="path-container glass-inner-panel">
                      <h4 class="sub-title">横向换岗发展路径</h4>
                      <div class="job-relation-chart">
                        <v-chart class="chart" :option="jobRelationOption" autoresize />
                      </div>
                    </div>
                  </el-col>
                </el-row>
              </div>
            </el-col>
          </el-row>
          </template>
        </div>
      </div>

      <!-- 骨架屏 (毛玻璃适配) -->
      <div v-else class="glass-panel skeleton-panel fade-in-up">
        <el-skeleton :rows="12" animated class="glass-skeleton" />
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { RadarChart, GraphChart } from 'echarts/charts'
import { TitleComponent, LegendComponent, TooltipComponent } from 'echarts/components'
import VChart from 'vue-echarts'
import axios from '@/utils/axios'
import { useAgentPipeline } from '@/stores/agentPipeline'
import type { JobAICacheData } from '@/stores/agentPipeline'
import { ElMessage } from 'element-plus'
// 新增引入 Back 图标用于自定义头部
import {
  Location, School, Timer, Document, OfficeBuilding, PriceTag, Calendar, Link, Back, Loading
} from '@element-plus/icons-vue'

const agentPipeline = useAgentPipeline()

use([CanvasRenderer, RadarChart, GraphChart, TitleComponent, LegendComponent, TooltipComponent])

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
const careerPaths = ref<any>({
  vertical_paths: [],
  horizontal_paths: []
})

// ---- Agent C 状态 (单岗位 AI 画像，按需触发) ----
const aiProfileLoading = ref(false)
const aiProfileExists = ref(false)
const loadingStatus = ref('正在连接 AI 服务...')
const loadingStep = ref(0)  // 0=初始, 1=分析能力, 2=晋升路径, 3=换岗方向
const studentId = ref<number | null>(null)

const hasStudentContext = computed(() => !!route.query.studentId)

const jobId = computed(() => parseInt(route.params.id as string))

// 精心设计的雷达图配置，高度还原设计稿并适配毛玻璃环境
const radarOption = computed(() => {
  if (!job.value) return {}
  
  const profile = job.value.profile
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
      shape: 'polygon', // 六边形网格
      indicator: [
        { name: '专业技能和证书', max: 100 },
        { name: '实习能力', max: 100 },
        { name: '沟通能力', max: 100 },
        { name: '抗压能力', max: 100 },
        { name: '学习能力', max: 100 },
        { name: '创新能力', max: 100 }
      ],
      radius: '65%',
      axisName: {
        color: '#374151',
        fontWeight: 700,
        fontSize: 14,
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
          color: 'rgba(102, 126, 234, 0.2)',
          width: 1,
          type: 'dashed'
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(102, 126, 234, 0.2)'
        }
      }
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          (profile.professional_skills_certificates || 0) * 10,
          (profile.internship_ability || 0) * 10,
          (profile.communication_ability || 0) * 10,
          (profile.stress_resistance || 0) * 10,
          (profile.learning_ability || 0) * 10,
          (profile.innovation_ability || 0) * 10
        ],
        name: '岗位要求',
        symbol: 'circle',
        symbolSize: 8,
        label: {
          show: true,
          color: '#4f46e5',
          fontSize: 13,
          fontWeight: 800,
          formatter: '{c}%', // 显示具体百分比
          position: 'top',
          distance: 4
        },
        areaStyle: {
          color: 'rgba(102, 126, 234, 0.25)' // 还原轻柔蓝色填充
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

// 换岗发展路径关系图
const jobRelationOption = computed(() => {
  if (!job.value || !careerPaths.value.horizontal_paths.length) return {}
  
  const currentJob = job.value.job_name || '当前岗位'
  const horizontalPaths = careerPaths.value.horizontal_paths
  
  const nodes = [
    {
      id: 0,
      name: currentJob,
      symbolSize: 100,
      itemStyle: {
        color: 'rgba(102, 126, 234, 0.9)',
        borderColor: '#ffffff',
        borderWidth: 3,
        shadowBlur: 15,
        shadowColor: 'rgba(102, 126, 234, 0.4)'
      },
      label: {
        show: true,
        fontSize: 16,
        fontWeight: 'bold',
        color: '#fff'
      }
    }
  ]
  
  const links = []
  let maxJobNameLength = 0
  horizontalPaths.forEach((path) => {
    const jobNameParts = path.target_job.split('，')
    const jobName = jobNameParts[0] || path.target_job
    maxJobNameLength = Math.max(maxJobNameLength, jobName.length)
  })
  
  const baseSize = 80
  const uniformSize = Math.max(baseSize, 30 + maxJobNameLength * 8)
  
  horizontalPaths.forEach((path, index) => {
    const nodeId = index + 1
    const jobNameParts = path.target_job.split('，')
    const jobName = jobNameParts[0] || path.target_job
    const difficulty = jobNameParts[1] || path.difficulty || '中等'
    const estimatedTime = jobNameParts[2] || path.estimated_time || '1-2年'
    const successRate = jobNameParts[3] || path.success_rate || '75%'
    
    nodes.push({
      id: nodeId,
      name: jobName,
      symbolSize: uniformSize,
      itemStyle: {
        color: 'rgba(43, 203, 186, 0.9)',
        borderColor: '#ffffff',
        borderWidth: 2,
        shadowBlur: 10,
        shadowColor: 'rgba(43, 203, 186, 0.3)'
      },
      label: {
        show: true,
        fontSize: 14,
        fontWeight: 'bold',
        color: '#fff',
        position: 'inside',
        align: 'center',
        verticalAlign: 'middle'
      }
    })
    
    links.push({
      source: 0,
      target: nodeId,
      lineStyle: {
        color: 'rgba(102, 126, 234, 0.5)',
        width: 3,
        curveness: 0.2
      },
      label: {
        show: true,
        formatter: `${estimatedTime}\n${successRate}`,
        fontSize: 12,
        color: '#4b5563',
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        padding: [4, 6],
        borderRadius: 4
      }
    })
  })
  
  const centerX = 50
  const centerY = 50
  const radius = 35
  
  nodes.forEach((node, index) => {
    if (index === 0) {
      node.x = centerX
      node.y = centerY
    } else {
      const angle = (index - 1) * (360 / horizontalPaths.length)
      const radian = angle * Math.PI / 180
      node.x = centerX + radius * Math.cos(radian)
      node.y = centerY + radius * Math.sin(radian)
    }
  })
  
  return {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      backdropFilter: 'blur(10px)',
      borderColor: 'rgba(255, 255, 255, 0.8)',
      textStyle: { color: '#1f2937' },
      padding: [12, 16],
      borderRadius: 12,
      boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
      formatter: function(params) {
        if (params.dataType === 'node') {
          if (params.data.id === 0) {
            return params.data.name
          } else {
            const path = horizontalPaths[params.data.id - 1]
            const jobNameParts = path.target_job.split('，')
            const difficulty = jobNameParts[1] || path.difficulty || '中等'
            const estimatedTime = jobNameParts[2] || path.estimated_time || '1-2年'
            const successRate = jobNameParts[3] || path.success_rate || '75%'
            const description = jobNameParts[4] || ''
            
            let tooltipContent = `<div style="font-weight:bold;margin-bottom:8px;font-size:15px;">${params.data.name}</div>
              <div style="font-size:13px;color:#4b5563;margin-bottom:4px;">难度: <span style="color:#e67e22;font-weight:600;">${difficulty}</span></div>
              <div style="font-size:13px;color:#4b5563;margin-bottom:4px;">预计时间: <span style="font-weight:600;">${estimatedTime}</span></div>
              <div style="font-size:13px;color:#4b5563;">成功率: <span style="color:#059669;font-weight:600;">${successRate}</span></div>`
            if (description) {
              tooltipContent += `<div style="font-size:13px;color:#6b7280;margin-top:6px;border-top:1px solid #eee;padding-top:6px;">描述: ${description}</div>`
            }
            return tooltipContent
          }
        }
        return ''
      }
    },
    series: [{
      type: 'graph',
      layout: 'none',
      data: nodes,
      links: links,
      roam: true,
      label: {
        show: true,
        position: 'inside',
        formatter: '{b}'
      },
      lineStyle: {
        color: '#999',
        width: 2,
        curveness: 0.2
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4 }
      }
    }]
  }
})

onMounted(async () => {
  // 从路由 query 获取 studentId
  const sid = route.query.studentId
  if (sid) studentId.value = Number(sid)

  await loadJobDetail()
  loadCareerPaths()
  // 如果从匹配页进入（带 studentId），检查 AI 画像缓存
  if (sid && jobId.value) {
    await checkAndLoadAiProfile(Number(sid), jobId.value)
  }
})

const loadJobDetail = async () => {
  try {
    let basicResponse
    const studentId = route.query.studentId

    // 始终用 job_id 查岗位，不依赖 matchRank（DB 中的 match_rank 是 LLM 输出顺序，
    // 前端传的 matchRank 是按分数排序后的显示顺序，两者可能不一致导致查出错岗位）
    basicResponse = await axios.get(`http://localhost:5000/api/jobs/${jobId.value}`)
    
    const processValue = (value) => {
      return value === 'nan' || value === null || value === undefined ? '无' : value
    }
    
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
      vertical_promotion_info: basicResponse.data.vertical_promotion_info,
      transfer_paths: basicResponse.data.transfer_paths,
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

const loadCareerPaths = async () => {
  try {
    // --- 垂直晋升路径 ---
    let vpData = job.value?.vertical_promotion_info
    if (vpData) {
      // Agent C 格式：{ complete_promotion_path: ["初级", "中级", ...] }
      let paths: string[] = []
      if (vpData.complete_promotion_path && Array.isArray(vpData.complete_promotion_path)) {
        paths = vpData.complete_promotion_path
      } else if (Array.isArray(vpData)) {
        paths = vpData.map((p: any) => typeof p === 'string' ? p : (p.title || p.level || ''))
      }
      careerPaths.value.vertical_paths = paths.map((title: string, i: number) => ({
        level: `Level ${i + 1}`,
        title: title,
        years: `${i + 1}-${i + 3}年`
      }))
    } else {
      careerPaths.value.vertical_paths = []
    }

    // --- 横向换岗路径 ---
    let hpData = job.value?.transfer_paths
    if (hpData && Array.isArray(hpData)) {
      careerPaths.value.horizontal_paths = hpData.map((path: any) => ({
        target_job: path.target_job || '',
        difficulty: path.difficulty || path.transfer_difficulty || '中等',
        estimated_time: path.estimated_time || '',
        success_rate: path.success_rate || '',
        required_skills: path.required_skills || []
      }))
    } else {
      careerPaths.value.horizontal_paths = []
    }
  } catch (error) {
    console.error('loadCareerPaths 失败:', error)
    careerPaths.value = { vertical_paths: [], horizontal_paths: [] }
  }
}

// ============================================================
// Agent C：单岗位 AI 画像（按需触发 + DB 缓存优先）
// ============================================================

const checkAndLoadAiProfile = async (studentId: number, jobId: number) => {
  const cached = await agentPipeline.checkJobProfileCache(studentId, jobId)
  if (cached) {
    aiProfileExists.value = true
    applyAiProfileToJob(cached)
  } else {
    // 无缓存 → 自动触发 Agent C
    await triggerAgentC()
  }
}

const triggerAgentC = async () => {
  const studentId = Number(route.query.studentId)
  if (!studentId || !job.value) return

  aiProfileLoading.value = true
  loadingStatus.value = '正在连接 AI 服务...'
  loadingStep.value = 0
  let jobProfileWarning = ''   // DB 写入警告（避免"成功+警告"矛盾提示）

  // 获取学生画像
  let profile = agentPipeline.profile
  if (!profile) {
    try {
      const res = await axios.get(`/api/students/${studentId}/profile`)
      profile = res.data
    } catch {
      ElMessage.error('无法加载学生画像')
      aiProfileLoading.value = false
      return
    }
  }

  const token = localStorage.getItem('token')
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'text/event-stream',
  }
  if (token) headers['Authorization'] = `Bearer ${token}`

  try {
    const response = await fetch('http://localhost:5000/api/agent/job-profile', {
      method: 'POST',
      headers,
      body: JSON.stringify({
        job_id: job.value.id,
        job_name: job.value.job_name,
        job_description: job.value.job_description,
        industry: job.value.industry || '',
        student_profile: profile,
        student_id: studentId,
      }),
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body?.getReader()
    if (!reader) throw new Error('浏览器不支持流式读取')

    const decoder = new TextDecoder('utf-8')
    let fullText = ''
    let rawBuffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      rawBuffer += decoder.decode(value, { stream: true })
      const events = rawBuffer.split('\n\n')
      rawBuffer = events.pop() || ''
      for (const event of events) {
        if (!event.trim()) continue
        const lines = event.split('\n')
        for (const line of lines) {
          if (!line.trim().startsWith('data: ')) continue
          try {
            const sseEvent = JSON.parse(line.trim().slice(6))
            if (sseEvent.type === 'chunk' && sseEvent.content) {
              fullText += sseEvent.content
              // 根据已生成的内容推断当前步骤
              if (fullText.includes('"job_transfer_paths"')) {
                loadingStatus.value = '正在分析横向换岗方向...'
                loadingStep.value = 3
              } else if (fullText.includes('"vertical_promotion_info"')) {
                loadingStatus.value = '正在规划纵向晋升路径...'
                loadingStep.value = 2
              } else if (fullText.includes('"ability_requirement_scores"')) {
                loadingStatus.value = '正在评估六维能力要求...'
                loadingStep.value = 1
              }
            } else if (sseEvent.type === 'error') {
              throw new Error(sseEvent.message || 'AI 服务错误')
            } else if (sseEvent.type === 'done') {
              jobProfileWarning = sseEvent.warning || ''
              if (sseEvent.warning) ElMessage.warning(sseEvent.warning)
            }
          } catch (e) {
            if (e instanceof Error && e.message !== 'AI 服务错误') continue
            throw e
          }
        }
      }
    }

    // 解析 JSON
    let jsonStr = ''
    const mdMatch = fullText.match(/```json\s*\n([\s\S]*?)\n\s*```/)
    if (mdMatch) {
      jsonStr = mdMatch[1].trim()
    } else {
      const jsonMatch = fullText.match(/\{[\s\S]*\}/)
      if (jsonMatch) jsonStr = jsonMatch[0].trim()
      else throw new Error('未找到 JSON 数据')
    }

    const parsed = JSON.parse(jsonStr) as JobAICacheData
    aiProfileExists.value = true
    applyAiProfileToJob(parsed)
    if (!jobProfileWarning) ElMessage.success('AI 岗位画像生成完成')
  } catch (err: any) {
    ElMessage.error('AI 岗位画像生成失败：' + (err.message || '网络错误'))
  } finally {
    aiProfileLoading.value = false
  }
}

const applyAiProfileToJob = (data: JobAICacheData) => {
  if (!job.value) return
  // 覆盖岗位要求分（雷达图用）
  job.value.ability_requirement_scores = data.ability_requirement_scores
  // 覆盖晋升路径
  job.value.vertical_promotion_info = data.vertical_promotion_info
  // 覆盖换岗路径
  job.value.transfer_paths = data.job_transfer_paths
  // 覆盖 profile 中雷达图各维度
  const scores = data.ability_requirement_scores
  job.value.profile = {
    ...job.value.profile,
    professional_skills_certificates: scores.professional_skills_certificates,
    innovation_ability: scores.innovation_ability,
    learning_ability: scores.learning_ability,
    stress_resistance: scores.stress_resistance,
    communication_ability: scores.communication_ability,
    internship_ability: scores.internship_experience,
  }
  // 重新加载职业路径
  loadCareerPaths()
}

function goToInterview() {
  const jobIdVal = Number(route.params.id)
  const sid = studentId.value
  if (sid && jobIdVal) {
    router.push(`/interview/${sid}/${jobIdVal}`)
  } else {
    ElMessage.warning('请先从匹配结果页或画像页进入')
  }
}

const handleBack = () => {
  const studentId = route.query.studentId
  const matchRank = route.query.matchRank
  if (studentId && matchRank) {
    router.push({ path: '/matching', query: { studentId: studentId } })
  } else {
    router.back()
  }
}
</script>

<style scoped>
/* =========== 整体页面背景与流体光晕 =========== */
.page-wrapper {
  min-height: 100%;
  position: relative;
  /* 【重点修改】移除固定的#f0f4f8背景色，改为透明，彻底消除正方形的生硬分界线 */
  background: transparent; 
  overflow: hidden;
  border-radius: 16px; 
}

.bg-shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px); /* 进一步增加模糊度，光晕更柔和、无边界感 */
  z-index: 0;
  opacity: 0.45; /* 略微降低透明度，更显高级 */
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
.job-detail-container {
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
  /* 【提升通透感】降低头部面板不透明度 */
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
  /* 【提升通透感】降低主卡片白底不透明度，移除生硬的单侧粗边框 */
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

/* =========== 基本信息卡片 =========== */
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

/* 弱化分割线 */
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

/* =========== 详情内容区域 =========== */
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

/* 图表容器 */
.radar-chart {
  height: 400px;
  margin: 0 36px 44px;
  padding: 24px;
}

.job-relation-chart {
  height: 500px;
  padding: 24px 0;
}

.chart {
  width: 100%;
  height: 100%;
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

/* 标签样式 (Tags) */
.skill-tags, .cert-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
}

.glass-tag {
  padding: 10px 22px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 14px;
  backdrop-filter: blur(12px);
  transition: all 0.3s ease;
  cursor: default;
}

.skill-tag {
  color: #4338ca;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.1) 0%, rgba(99, 102, 241, 0.05) 100%);
  border: 1px solid rgba(79, 70, 229, 0.2);
}

.skill-tag:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(79, 70, 229, 0.1);
  background: rgba(255, 255, 255, 0.6);
}

.cert-tag {
  color: #047857;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.cert-tag:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.1);
  background: rgba(255, 255, 255, 0.6);
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

/* =========== 职业发展路径区 =========== */
.path-container {
  padding: 28px;
  height: 100%;
}

.sub-title {
  font-size: 17px;
  font-weight: 800;
  margin-bottom: 28px;
  color: #1f2937;
  display: flex;
  align-items: center;
}

.sub-title::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 18px;
  background: linear-gradient(180deg, #667eea, #764ba2);
  border-radius: 2px;
  margin-right: 12px;
}

.timeline-glass-content {
  padding: 18px;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  border-radius: 14px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.02);
  transition: transform 0.3s ease, background 0.3s ease;
}

.timeline-glass-content:hover {
  transform: translateX(6px);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.04);
}

.custom-timeline :deep(.el-timeline-item__node) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15);
  border: 2px solid rgba(255, 255, 255, 0.8);
}

.custom-timeline :deep(.el-timeline-item__tail) {
  border-left: 2px dashed rgba(102, 126, 234, 0.3);
}

.timeline-glass-content h5 {
  font-size: 16px;
  font-weight: 800;
  margin: 0 0 10px 0;
  color: #4f46e5;
}

.path-title {
  font-size: 15px;
  color: #1f2937;
  margin: 0 0 10px 0;
  font-weight: 700;
}

.path-time {
  font-size: 13px;
  color: #4b5563;
  margin: 0;
  display: inline-flex;
  align-items: center;
  background: rgba(0,0,0,0.05);
  padding: 5px 12px;
  border-radius: 10px;
  font-weight: 600;
}

/* ==================== 骨架屏 ==================== */
.skeleton-panel {
  padding: 36px;
}

/* ==================== AI 加载状态 ==================== */
.ai-loading-overlay {
  margin: 0 36px 24px;
  padding: 40px 24px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: rgba(255,255,255,0.15);
  backdrop-filter: blur(12px);
  border-radius: 20px;
  border: 1px solid rgba(255,255,255,0.3);
}
.ai-loading-card {
  text-align: center;
}
.ai-loading-icon {
  margin-bottom: 16px;
  color: #667eea;
}
.ai-loading-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 700;
  color: #1f2937;
}
.ai-loading-status {
  margin: 0 0 24px;
  font-size: 14px;
  color: #667eea;
  animation: pulse-text 2s ease-in-out infinite;
}
.ai-loading-steps {
  display: flex;
  gap: 32px;
  justify-content: center;
}
.ai-loading-steps .step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  opacity: 0.35;
  transition: all 0.5s ease;
}
.ai-loading-steps .step.active {
  opacity: 1;
}
.ai-loading-steps .step.done {
  opacity: 0.6;
}
.ai-loading-steps .step .step-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #c0c4cc;
  transition: all 0.5s ease;
}
.ai-loading-steps .step.active .step-dot {
  background: #667eea;
  box-shadow: 0 0 12px rgba(102, 126, 234, 0.6);
  animation: pulse-dot 1s ease-in-out infinite;
}
.ai-loading-steps .step.done .step-dot {
  background: #67c23a;
}
.ai-loading-steps .step .step-label {
  font-size: 12px;
  color: #6b7280;
  white-space: nowrap;
}
.ai-loading-steps .step.active .step-label {
  color: #667eea;
  font-weight: 600;
}
@keyframes pulse-text {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
@keyframes pulse-dot {
  0%, 100% { box-shadow: 0 0 8px rgba(102, 126, 234, 0.4); }
  50% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.8); }
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
  .job-detail-container {
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
  
  .content-section, .radar-chart {
    padding: 0 24px;
    margin: 0 0 32px 0;
  }
  
  .radar-chart {
    height: 320px;
  }
  
  .job-relation-chart {
    height: 400px;
  }
}

/* =========== 玻璃拟态确认弹窗 (参考 Matching/Admin 风格) =========== */
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

.interview-entry-btn {
  margin-top: 12px;
  border-radius: 24px;
  font-weight: 600;
}
</style>