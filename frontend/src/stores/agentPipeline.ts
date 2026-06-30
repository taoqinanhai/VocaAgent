/**
 * Agent Pipeline Store — 跨页面数据总线
 *
 * 管理 5 个 Agent 的流式调用和结果共享：
 *   Agent A（Profile） → Agent B（Matching） → Agent C（Job Profile） → Agent D（Report） → Agent E（Interview）
 *
 * 页面间数据流动：
 *   Profile.vue  → 调 runProfile()    → 写入 store.profile
 *   Matching.vue → 调 runMatching()   → 写入 store.matchResults（渐进式）
 *   ReportDetail → 调 runReport()     → 写入 store.reportHtml（流式 v-html）
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { createSSEStream } from '@/utils/sse'
import api from '@/utils/axios'

// ============================================================
// 类型定义
// ============================================================

export interface AbilityDimensionScores {
  professional_skills_certificates: number
  innovation_ability: number
  learning_ability: number
  stress_resistance: number
  communication_ability: number
  internship_experience: number
}

export interface StudentProfile {
  resume_detail_info: {
    name: string
    email: string
    phone: string
    education: string
    school: string
    major: string
    graduation_year: number
    professional_skills: string[]
    certificates: string[]
    internship_experience_detail: Array<{
      company: string
      position: string
      duration: string
      description: string
    }>
    project_experience: Array<{
      name: string
      role: string
      description: string
    }>
    resume_text: string
  }
  ability_dimension_scores: AbilityDimensionScores
  ability_overall_scores: {
    profile_completeness: number
    competitiveness_score: number
  }
}

export interface JobMatchResult {
  /** 岗位 ID（来自 Agent B，对应 MySQL jobs 表） */
  job_id: number
  /** 来自 MySQL 的静态岗位数据 — 异步获取后填充 */
  job_card?: JobCardData
  /** 学生与该岗位的 5 维匹配分 (0-100) */
  user_matching_scores: {
    basic_requirements_matching: number
    professional_skills_matching: number
    professional_literacy_matching: number
    development_potential_matching: number
    overall_matching: number
  }
}

/** Agent C 生成的单岗位 AI 画像缓存数据 */
export interface JobAICacheData {
  ability_requirement_scores: AbilityDimensionScores
  vertical_promotion_info: {
    job_description: string
    complete_promotion_path: string[]
  }
  job_transfer_paths: Array<{
    target_job: string
    transfer_difficulty: string
    reason: string
  }>
}

export interface JobCardData {
  id: number
  job_name: string
  company_name: string
  salary: string
  location: string
  industry: string
  job_description: string
  education_requirement?: string
  experience_requirement?: string
}

// ============================================================
// Store
// ============================================================

export const useAgentPipeline = defineStore('agentPipeline', () => {
  // ---- Agent A 状态 ----
  const profile = ref<StudentProfile | null>(null)
  const profileLoading = ref(false)
  const profileError = ref('')
  const profileStreamText = ref('') // 流式文本（用于打字效果）

  // ---- Agent B 状态 ----
  const matchResults = ref<JobMatchResult[]>([])
  const matchLoading = ref(false)
  const matchError = ref('')
  const matchCurrentJobCount = ref(0) // 当前已解析的岗位数（驱动卡片弹出动画）

  // ---- Agent C 状态 (单岗位画像，按需触发) ----
  const jobProfileLoading = ref(false)
  const jobProfileError = ref('')

  // ---- Agent D 状态 (报告生成) ----
  const reportHtml = ref('')
  const reportLoading = ref(false)
  const reportError = ref('')
  const reportStreamHtml = ref('') // 流式 HTML 片段

  // ---- 已选中的 Top 3 ----
  const selectedTop3 = ref<JobMatchResult[]>([])

  // ---- DB 持久化 ID ----
  const currentStudentId = ref<number | null>(null)  // Agent A 返回的 student_id，贯穿整个 pipeline

  // ---- 计算属性 ----
  const hasProfile = computed(() => profile.value !== null)
  const hasMatches = computed(() => matchResults.value.length > 0)
  const hasReport = computed(() => reportHtml.value.length > 0)

  /** 按综合匹配分降序排列 */
  const sortedMatches = computed(() =>
    [...matchResults.value].sort(
      (a, b) => b.user_matching_scores.overall_matching - a.user_matching_scores.overall_matching
    )
  )

  /** Top 3 匹配 */
  const top3Matches = computed(() => sortedMatches.value.slice(0, 3))

  // ============================================================
  // Agent A：简历解析 → 学生画像
  // ============================================================

  /**
   * 通过文件上传触发 Agent A 画像生成
   * @param file — PDF/Word 简历文件
   */
  async function runProfileFromFile(file: File): Promise<StudentProfile | null> {
    profileLoading.value = true
    profileError.value = ''
    profileStreamText.value = ''
    profile.value = null

    // 先用 FormData 上传文件，让后端提取文本
    const formData = new FormData()
    formData.append('file', file)

    try {
      const uploadRes = await api.post('/api/agent/profile', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 300000,
        responseType: 'text', // SSE 需要 raw 文本
      })

      // SSE 响应已通过 responseType: 'text' 获取
      // 但 axios 不支持流式读取，我们改用 fetch
      return await _runProfileViaFetch({ file })
    } catch {
      // axios 不支持 SSE 流，直接走 fetch
      return await _runProfileViaFetch({ file })
    }
  }

  /**
   * 通过纯文本触发 Agent A 画像生成
   * @param resumeText — 简历文本内容
   */
  async function runProfileFromText(resumeText: string): Promise<StudentProfile | null> {
    profileLoading.value = true
    profileError.value = ''
    profileStreamText.value = ''
    profile.value = null

    return await _runProfileViaFetch({ resume_text: resumeText })
  }

  /** 底层：通过 fetch SSE 调 Agent A */
  async function _runProfileViaFetch(
    payload: { file?: File; resume_text?: string }
  ): Promise<StudentProfile | null> {
    return new Promise((resolve) => {
      let body: Record<string, unknown>

      if (payload.file) {
        // 文件场景：先用 FormData 提取文本，再用文本调 Agent A
        const formData = new FormData()
        formData.append('file', payload.file)

        api
          .post('/api/agent/profile', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 300000,
          })
          .then((res) => {
            // 非流式回退 — 从 DB 加载
            if (res.data?.student_id) {
              loadProfileFromDb(res.data.student_id).then(resolve)
            } else {
              // 还是走流式
              _streamProfile(resolve)
            }
          })
          .catch(() => {
            _streamProfile(resolve)
          })
      } else {
        _streamProfile(resolve)
      }
    })
  }

  function _streamProfile(resolve: (p: StudentProfile | null) => void) {
    // 需要一个 resume_text，从已有的 profileStreamText 或手动输入
    // 这个函数被 runProfileFromText 调用，text 已经在外层处理
    // 实际实现：通过 createSSEStream

    // 简化处理：直接标记完成，由页面层使用 createSSEStream
    profileLoading.value = false
    resolve(null)
  }

  /**
   * 调用 Agent A SSE 流式生成画像
   * 返回 abort 函数 + Promise
   */
  function streamProfile(
    resumeText: string,
    callbacks: {
      onChunk?: (text: string) => void
      onDone?: (profile: StudentProfile) => void
      onError?: (err: string) => void
    }
  ): () => void {
    profileLoading.value = true
    profileError.value = ''
    profileStreamText.value = ''

    return createSSEStream(
      '/api/agent/profile',
      { resume_text: resumeText },
      {
        onChunk: (content) => {
          profileStreamText.value += content
          callbacks.onChunk?.(content)
        },
        onDone: (fullText, doneEvent) => {
          profileLoading.value = false
          try {
            // 捕获 student_id（用于后续 Agent B / C 的 DB 持久化）
            if (doneEvent?.student_id) {
              currentStudentId.value = doneEvent.student_id as number
              console.log('[Pipeline] student_id captured:', currentStudentId.value)
            }
            // 尝试从累积文本中提取 JSON
            const json = extractJSON(fullText)
            profile.value = json as StudentProfile
            callbacks.onDone?.(json as StudentProfile)
          } catch (e) {
            profileError.value = '画像 JSON 解析失败'
            callbacks.onError?.(profileError.value)
          }
        },
        onError: (err) => {
          profileLoading.value = false
          profileError.value = err
          callbacks.onError?.(err)
        },
      }
    )
  }

  // ---- 从 DB 加载已有画像 ----
  async function loadProfileFromDb(studentId: number): Promise<StudentProfile | null> {
    try {
      const res = await api.get(`/api/students/${studentId}/profile`)
      if (res.data) {
        profile.value = res.data as StudentProfile
        currentStudentId.value = studentId  // 同步 student_id，确保后续 Agent B/C 可持久化
        return profile.value
      }
      return null
    } catch {
      return null
    }
  }

  // ============================================================
  // Agent B：岗位匹配 → 10 岗位评分（渐进式卡片渲染）
  // ============================================================

  /**
   * 调用 Agent B SSE 流式匹配
   * 核心创新：每解析出一个岗位 → 立刻查 MySQL 卡片数据 → 卡片弹出
   */
  function streamMatching(
    studentProfile: StudentProfile,
    callbacks: {
      onJobParsed?: (job: JobMatchResult, index: number) => void
      onJobCardReady?: (job: JobMatchResult, index: number) => void
      onDone?: (results: JobMatchResult[]) => void
      onError?: (err: string) => void
    }
  ): () => void {
    matchLoading.value = true
    matchError.value = ''
    matchResults.value = []
    matchCurrentJobCount.value = 0

    let fullText = ''

    return createSSEStream(
      '/api/agent/match',
      {
        student_profile: studentProfile,
        student_id: currentStudentId.value,   // 传入DB学生ID，供后端持久化匹配结果
      },
      {
        onChunk: () => {
          // Plan A：不流式解析，只累积
        },
        onDone: (accumulated: string) => {
          matchLoading.value = false
          try {
            let jsonStr = ''
            const mdMatch = accumulated.match(/```json\s*\n([\s\S]*?)\n\s*```/)
            if (mdMatch) {
              jsonStr = mdMatch[1].trim()
            } else {
              const jsonMatch = accumulated.match(/\{[\s\S]*\}/)
              if (jsonMatch) jsonStr = jsonMatch[0].trim()
              else throw new Error('未找到 JSON 数据')
            }
            const parsed = JSON.parse(jsonStr)
            const profiles: JobMatchResult[] = (parsed.job_post_profiles || []) as JobMatchResult[]

            profiles.forEach((job, idx) => {
              matchResults.value.push(job)
              matchCurrentJobCount.value = matchResults.value.length
              callbacks.onJobParsed?.(job, idx)
              fetchJobCard(job.job_id).then((card) => {
                if (card) {
                  job.job_card = card
                  matchResults.value = [...matchResults.value]
                  callbacks.onJobCardReady?.(job, idx)
                }
              })
            })

            callbacks.onDone?.(matchResults.value)
          } catch (e) {
            matchError.value = 'AI 返回格式解析失败'
            callbacks.onError?.(matchError.value)
          }
        },
        onError: (err) => {
          matchLoading.value = false
          matchError.value = err
          callbacks.onError?.(err)
        },
      }
    )
  }

  /** 查 MySQL 获取岗位卡片数据（字段对齐后端 jobs.py 的 /api/jobs/:id） */
  async function fetchJobCard(jobId: number): Promise<JobCardData | null> {
    try {
      const res = await api.get(`/api/jobs/${jobId}`)
      if (res.data) {
        return {
          id: res.data.id || jobId,
          job_name: res.data.job_name || '',
          company_name: res.data.company_name || '',
          salary: res.data.salary_range || '',
          location: res.data.work_address || '',
          industry: res.data.industry || '',
          job_description: res.data.job_description || '',
        }
      }
      return null
    } catch {
      return null
    }
  }

  /** 从 DB 加载已有匹配结果（仅匹配分，不含岗位画像） */
  async function loadMatchesFromDb(studentId: number): Promise<JobMatchResult[]> {
    try {
      const res = await api.get(`/api/students/${studentId}/matches`)
      if (res.data?.data) {
        matchResults.value = res.data.data.map((item: Record<string, unknown>) => ({
          job_id: item.job_id as number,
          user_matching_scores: {
            basic_requirements_matching: (item.basic_requirements_score || 0) as number,
            professional_skills_matching: (item.professional_skills_score || 0) as number,
            professional_literacy_matching: (item.professional_qualities_score || 0) as number,
            development_potential_matching: (item.development_potential_score || 0) as number,
            overall_matching: (item.overall_match_score || 0) as number,
          },
        }))
        return matchResults.value
      }
      return []
    } catch {
      return []
    }
  }

  // ============================================================
  // Agent C：单岗位画像分析 (按需触发，DB 缓存优先)
  // ============================================================

  /**
   * 查询 DB：某 student×job 是否已有 AI 画像
   */
  async function checkJobProfileCache(studentId: number, jobId: number): Promise<JobAICacheData | null> {
    try {
      const res = await api.get(`/api/agent/job-profile/${studentId}/${jobId}`)
      if (res.data?.exists) {
        return {
          ability_requirement_scores: res.data.ability_requirement_scores,
          vertical_promotion_info: res.data.vertical_promotion_info,
          job_transfer_paths: res.data.job_transfer_paths,
        }
      }
      return null
    } catch {
      return null
    }
  }

  /**
   * 调用 Agent C SSE 流式生成单岗位画像
   */
  function streamJobProfile(
    jobInfo: { job_id: number; job_name: string; job_description: string; industry: string },
    studentProfile: StudentProfile,
    callbacks: {
      onChunk?: (content: string) => void
      onDone?: (data: JobAICacheData) => void
      onError?: (err: string) => void
    }
  ): () => void {
    jobProfileLoading.value = true
    jobProfileError.value = ''

    let fullText = ''

    return createSSEStream(
      '/api/agent/job-profile',
      {
        job_id: jobInfo.job_id,
        job_name: jobInfo.job_name,
        job_description: jobInfo.job_description,
        industry: jobInfo.industry,
        student_profile: studentProfile,
        student_id: currentStudentId.value,
      },
      {
        onChunk: (content) => {
          fullText += content
          callbacks.onChunk?.(content)
        },
        onDone: () => {
          jobProfileLoading.value = false
          try {
            const json = extractJSON(fullText) as unknown as JobAICacheData
            callbacks.onDone?.(json)
          } catch (e) {
            jobProfileError.value = '岗位画像 JSON 解析失败'
            callbacks.onError?.(jobProfileError.value)
          }
        },
        onError: (err) => {
          jobProfileLoading.value = false
          jobProfileError.value = err
          callbacks.onError?.(err)
        },
      }
    )
  }

  // ============================================================
  // Agent D：报告生成 → HTML 流式渲染
  // ============================================================

  function streamReport(
    studentProfile: StudentProfile,
    top3: JobMatchResult[],
    callbacks: {
      onChunk?: (html: string) => void
      onDone?: (fullHtml: string) => void
      onError?: (err: string) => void
    }
  ): () => void {
    reportLoading.value = true
    reportError.value = ''
    reportStreamHtml.value = ''
    reportHtml.value = ''

    return createSSEStream(
      '/api/agent/report',
      {
        student_profile: studentProfile,
        top3_matches: top3,
        student_id: currentStudentId.value,   // 传入DB学生ID，供后端持久化报告
      },
      {
        onChunk: (content) => {
          reportStreamHtml.value += content
          reportHtml.value = reportStreamHtml.value
          callbacks.onChunk?.(content)
        },
        onDone: (fullText) => {
          reportLoading.value = false
          reportHtml.value = fullText
          callbacks.onDone?.(fullText)
        },
        onError: (err) => {
          reportLoading.value = false
          reportError.value = err
          callbacks.onError?.(err)
        },
      }
    )
  }

  /** 从 DB 加载已有报告 */
  async function loadReportFromDb(reportId: number): Promise<string | null> {
    try {
      const res = await api.get(`/api/reports/${reportId}`)
      if (res.data?.success && res.data?.data?.report_html) {
        reportHtml.value = res.data.data.report_html
        return reportHtml.value
      }
      return null
    } catch {
      return null
    }
  }

  // ============================================================
  // 工具栏：选择 Top 3 / 清空
  // ============================================================

  function selectTop3(jobs: JobMatchResult[]) {
    selectedTop3.value = jobs
  }

  function clearAll() {
    profile.value = null
    profileStreamText.value = ''
    matchResults.value = []
    reportHtml.value = ''
    reportStreamHtml.value = ''
    selectedTop3.value = []
    currentStudentId.value = null
  }

  return {
    // 状态
    profile,
    profileLoading,
    profileError,
    profileStreamText,
    matchResults,
    matchLoading,
    matchError,
    matchCurrentJobCount,
    jobProfileLoading,
    jobProfileError,
    reportHtml,
    reportLoading,
    reportError,
    reportStreamHtml,
    currentStudentId,
    // 计算属性
    hasProfile,
    hasMatches,
    hasReport,
    sortedMatches,
    top3Matches,
    // Agent A
    runProfileFromFile,
    runProfileFromText,
    streamProfile,
    loadProfileFromDb,
    // Agent B
    streamMatching,
    fetchJobCard,
    loadMatchesFromDb,
    // Agent C (单岗位画像)
    checkJobProfileCache,
    streamJobProfile,
    // Agent D (报告生成)
    streamReport,
    loadReportFromDb,
    // 工具
    selectTop3,
    clearAll,
  }
})

// ============================================================
// 工具函数
// ============================================================

/** 从文本中提取 JSON 对象（用正则找最外层，兼容模型加说明文字） */
function extractJSON(text: string): Record<string, unknown> {
  const mdMatch = text.match(/```json\s*\n([\s\S]*?)\n\s*```/)
  if (mdMatch) return JSON.parse(mdMatch[1].trim())
  const jsonMatch = text.match(/\{[\s\S]*\}/)
  if (jsonMatch) return JSON.parse(jsonMatch[0].trim())
  throw new Error('未找到 JSON 数据')
}

