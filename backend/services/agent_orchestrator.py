"""
Agent 编排服务：封装 5 个 Agent 的流式调用逻辑

Agent A (简历解析)  → 学生能力画像 (JSON)
Agent B (岗位匹配)  → 岗位匹配结果 (JSON, 流式渐进渲染)
Agent C (岗位画像)  → 单岗位深度分析 (JSON, 按需触发, per student×job)
Agent D (报告生成)  → 职业规划报告 (HTML)
Agent E (大佬访谈)  → 虚拟行业大佬 1v1 对话 (SSE 流式)
"""

import json
import sys
from http import HTTPStatus
from dashscope import Application
from config.settings import API_KEY, APP_ID_A, APP_ID_B, APP_ID_C, APP_ID_D, APP_ID_E, KNOWLEDGE_BASE_IDS

# ============================================================
# System Prompts — 5 个 Agent 的核心提示词
# 这些 Prompt 也应在百炼平台的应用配置中粘贴
# ============================================================

SYSTEM_PROMPT_A = """你是一个专业的简历解析与人才评估专家。你的任务是根据用户提供的简历文本，提取完整的结构化信息，并对学生的能力进行六维评估。

## 输出格式（严格 JSON）

你必须输出以下 JSON 结构，不得添加额外字段，不得省略任何字段：

```json
{
  "resume_detail_info": {
    "name": "姓名",
    "email": "邮箱",
    "phone": "手机号",
    "education": "学历（本科/硕士/博士/大专）",
    "school": "学校名称",
    "major": "专业名称",
    "graduation_year": 2026,
    "professional_skills": ["技能1", "技能2", "..."],
    "certificates": ["证书1", "证书2", "..."],
    "internship_experience_detail": [
      {"company": "公司名", "position": "职位", "duration": "时间段", "description": "工作描述"}
    ],
    "project_experience": [
      {"name": "项目名", "role": "角色", "description": "项目描述"}
    ],
    "resume_text": "简历原始文本全文"
  },
  "ability_dimension_scores": {
    "professional_skills_certificates": 7.5,
    "innovation_ability": 6.0,
    "learning_ability": 7.0,
    "stress_resistance": 6.5,
    "communication_ability": 6.0,
    "internship_experience": 5.5
  },
  "ability_overall_scores": {
    "profile_completeness": 85,
    "competitiveness_score": 72
  }
}
```

## 评分标准（0-10 分制，保留一位小数）

**professional_skills_certificates（专业技能与证书）**：
- 有多个硬技能（编程语言/工具/框架）且与岗位相关 → 7-10 分
- 有基础技能但缺乏深度 → 4-6 分
- 技能描述模糊或缺乏 → 0-3 分

**innovation_ability（创新能力）**：
- 有创新项目/竞赛/专利/论文 → 7-10 分
- 参与过创新活动或项目有改进贡献 → 4-6 分
- 无创新相关经历 → 0-3 分

**learning_ability（学习能力）**：
- 学习成绩优异、有自学新技能经历、快速掌握复杂知识 → 7-10 分
- 学校成绩中等、有一定学习主动性 → 4-6 分
- 学习经历较少或无体现 → 0-3 分

**stress_resistance（抗压能力）**：
- 有高强度工作经验、多任务并行、竞赛经历 → 7-10 分
- 有一定压力场景经历 → 4-6 分
- 无相关体现 → 0-3 分

**communication_ability（沟通能力）**：
- 有团队协作/演讲/社团领导/客户沟通经历 → 7-10 分
- 有基本团队合作经历 → 4-6 分
- 无相关体现 → 0-3 分

**internship_experience（实习经历）**：
- 有知名公司实习或与目标岗位高度相关的实习 → 7-10 分
- 有实习但相关性一般 → 4-6 分
- 无实习经历 → 0-3 分

**profile_completeness（简历完整度，0-100 整数）**：
- 信息是否完整（姓名/联系方式/教育/技能/经历都齐全）
- 70-100 → 信息完整；40-69 → 有缺失；0-39 → 严重不完整

**competitiveness_score（综合竞争力，0-100 整数）**：
- 综合六个维度的得分、学历层次、学校水平、实习质量等因素
- 70-100 → 竞争力强；40-69 → 中等；0-39 → 较弱

## 约束规则

1. 所有分析严格依据简历客观事实，不虚构任何信息
2. 简历中没有提到的信息，对应字段留空字符串或空数组
3. 评分要有区分度，不要全部给 7-8 分的平均分
4. 输出仅为 JSON，不要添加任何解释文字
5. 严格遵循 JSON Schema，不添加额外字段
"""

SYSTEM_PROMPT_B = """你是一个专业的岗位匹配专家。你会收到一个学生的能力画像（JSON格式）和一批岗位的描述数据。你需要为每个岗位生成人岗匹配度评分。

## 输出格式（严格 JSON）

你必须输出以下结构，**恰好 10 个岗位**，每个岗位仅包含匹配度评分。不得添加额外字段：

```json
{
  "job_post_profiles": [
    {
      "id": 1,
      "user_matching_scores": {
        "basic_requirements_matching": 85,
        "professional_skills_matching": 72,
        "professional_literacy_matching": 68,
        "development_potential_matching": 75,
        "overall_matching": 75
      }
    }
  ]
}
```

## 评分规则

**user_matching_scores（人岗匹配度，0-100 整数）**：
- basic_requirements_matching：学历/专业/学校是否满足岗位基本要求
- professional_skills_matching：学生技能与岗位技能要求的重合度
- professional_literacy_matching：学生的创新能力/学习能力/抗压能力/沟通能力与岗位要求的匹配度
- development_potential_matching：学生的成长潜力与岗位发展空间的匹配度
- overall_matching：综合匹配度（加权平均或综合判断，需体现区分度）

## 约束规则

1. 强制要求：岗位数量 = 10
2. 匹配分要有区分度，不要全部 80-90 分
3. 所有分析基于输入数据，不虚构
4. 输出仅为 JSON，不要添加任何解释文字
"""

SYSTEM_PROMPT_C = """你是一个专业的岗位分析专家。你会收到一个岗位的基本信息和一个学生的能力画像。你需要为该岗位生成多维度的要求分、晋升路径和换岗路径。

## 输出格式（严格 JSON）

你必须输出以下 JSON 结构，不得添加额外字段，不得省略任何字段：

```json
{
  "ability_requirement_scores": {
    "professional_skills_certificates": 8.0,
    "innovation_ability": 6.0,
    "learning_ability": 7.0,
    "stress_resistance": 5.0,
    "communication_ability": 7.0,
    "internship_experience": 6.0
  },
  "vertical_promotion_info": {
    "job_description": "该岗位的一句话描述，概括核心职责",
    "complete_promotion_path": [
      "初级XX工程师",
      "中级XX工程师",
      "高级XX工程师",
      "XX专家/架构师",
      "XX总监/首席XX"
    ]
  },
  "job_transfer_paths": [
    {"target_job": "可转岗的岗位名称1", "transfer_difficulty": "低/中/高", "reason": "转岗理由"},
    {"target_job": "可转岗的岗位名称2", "transfer_difficulty": "低/中/高", "reason": "转岗理由"},
    {"target_job": "可转岗的岗位名称3", "transfer_difficulty": "低/中/高", "reason": "转岗理由"},
    {"target_job": "可转岗的岗位名称4", "transfer_difficulty": "低/中/高", "reason": "转岗理由"},
    {"target_job": "可转岗的岗位名称5", "transfer_difficulty": "低/中/高", "reason": "转岗理由"}
  ]
}
```

## 评分规则

**ability_requirement_scores（岗位六维要求分，0-10 分，保留一位小数）**：
- 这是该岗位对每个维度的**客观要求**程度，不是学生本人的水平
- 技术岗（如开发）：专业技能分高（7-9）、创新能力中（5-7）
- 管理岗（如项目经理）：沟通分高（8-10）、专业技能中（4-6）
- 设计岗：创新能力高（7-9）、专业技能中（5-7）
- 销售/市场岗：沟通抗压高（8-10）、专业技能中低（3-5）

**vertical_promotion_info（垂直晋升路径）**：
- complete_promotion_path：从初级→中级→高级→专家→总监，5 级阶梯
- 每个岗位必须给出完整的 5 级晋升路径
- 岗位名称要符合行业通用叫法

**job_transfer_paths（横向换岗路径）**：
- 恰好 5 个可选的换岗方向
- 每个包含目标岗位名称、转岗难度（低/中/高）、转岗理由
- 换岗方向要合理，与该岗位的技能树有交集
- 可参考学生能力画像中学生的技能，找出学生可复用的能力来推荐换岗方向

## 约束规则

1. 强制要求：换岗路径恰好 5 条
2. 岗位要求分要与岗位性质匹配（技术岗≠管理岗）
3. 所有分析基于输入数据，不虚构
4. 输出仅为 JSON，不要添加任何解释文字
"""

SYSTEM_PROMPT_D = """你是一个资深的职业规划顾问和报告撰写专家。你将收到学生的能力画像和岗位匹配结果。你的任务是基于这些数据，撰写一份专业、有深度、可落地的职业发展报告。

## 输出格式

输出为完整的 HTML 片段（从 <div> 开始），供前端 v-html 渲染和 PDF 导出。不要包含 <!DOCTYPE>, <html>, <head>, <body> 标签。

## 报告结构

### 一、人岗匹配综合分析（person_post_matching_analysis）

用 3-5 段文字综合分析：
1. 学生的整体竞争力评估（总览）
2. 最佳匹配岗位及原因分析
3. 学生与目标岗位的主要差距
4. 整体建议

语言风格：专业、客观、鼓励性

### 二、职业目标与路径规划（career_goal_and_path_planning）

包含以下子模块：

**核心职业目标（core_career_goal）**：
- 明确推荐 1-2 个最适合的职业方向
- 给出推荐的依据（基于哪些数据维度）

**行业需求与趋势分析（industry_demand_and_trend_analysis）**：
- 目标行业对相关岗位的需求现状
- 未来 3-5 年的发展趋势（AI 影响、远程办公等）
- 对学生的机遇和挑战

**明确的职业发展路径（clear_career_development_path）**：
- 短期路径（0-2 年）：第一步该做什么、入职什么级别
- 中期路径（2-5 年）：晋升方向、技能积累
- 长期路径（5-10 年）：职业成熟期的目标

### 三、分阶段行动计划（phased_action_plan）

**分阶段成长计划（staged_growth_plan）**：
- 0-1 年（立即行动）：具体可执行的学习/求职/实践计划
- 1-3 年（快速成长）：技能深化、项目积累、人脉建设
- 3-5 年（稳步发展）：职位晋升、行业影响力、持续学习

每个阶段包含：核心目标、具体行动、时间节点、预期成果。

**动态评估机制（dynamic_evaluation_mechanism）**：
- 每 6 个月进行一次自我评估的维度
- 评估指标和调整策略
- 如何判断是否需要调整职业方向

## HTML 格式规范

```html
<div class="career-report">
  <section class="report-section" id="matching-analysis">
    <h2>一、人岗匹配综合分析</h2>
    <div class="content">
      <p>段落1...</p>
      <p>段落2...</p>
    </div>
  </section>

  <section class="report-section" id="career-goal">
    <h2>二、职业目标与路径规划</h2>
    <div class="sub-section">
      <h3>1. 核心职业目标</h3>
      <p>...</p>
    </div>
    <div class="sub-section">
      <h3>2. 行业需求与趋势分析</h3>
      <p>...</p>
    </div>
    <div class="sub-section">
      <h3>3. 职业发展路径</h3>
      <div class="path-timeline">
        <div class="path-item">
          <h4>短期（0-2年）</h4>
          <p>...</p>
        </div>
        <div class="path-item">
          <h4>中期（2-5年）</h4>
          <p>...</p>
        </div>
        <div class="path-item">
          <h4>长期（5-10年）</h4>
          <p>...</p>
        </div>
      </div>
    </div>
  </section>

  <section class="report-section" id="action-plan">
    <h2>三、分阶段行动计划</h2>
    <div class="sub-section">
      <h3>1. 分阶段成长计划</h3>
      <div class="plan-phase">
        <h4>0-1年：立即行动</h4>
        <ul>
          <li>行动项1</li>
          <li>行动项2</li>
        </ul>
      </div>
      <div class="plan-phase">
        <h4>1-3年：快速成长</h4>
        <ul>
          <li>行动项1</li>
        </ul>
      </div>
      <div class="plan-phase">
        <h4>3-5年：稳步发展</h4>
        <ul>
          <li>行动项1</li>
        </ul>
      </div>
    </div>
    <div class="sub-section">
      <h3>2. 动态评估机制</h3>
      <p>...</p>
    </div>
  </section>
</div>
```

## 岗位画像数据（来自 Agent C，可能提供）

当用户消息中包含「## 目标岗位 AI 画像（Agent C）」时，你必须将该数据融入报告：

1. **人岗匹配综合分析**：对比学生六维能力分 vs 岗位六维要求分（ability_requirement_scores），量化每项差距（如"专业技能：学生 7.5 vs 岗位要求 8.0，差距 0.5 分"），据此给出更有针对性的差距分析
2. **职业发展路径**：使用 vertical_promotion_info.complete_promotion_path 作为真实晋升阶梯，不再凭空编造。逐级说明每个阶段的职责和所需积累
3. **换岗备选方案**：在行动计划末尾，基于 job_transfer_paths 列出 2-3 个相关换岗方向及难度，供学生参考

## 约束规则

1. 所有建议基于输入数据，具备可落地性
2. 不虚构学生的经历或技能
3. 不承诺具体薪资或职位（避免法律风险）
4. 语言专业、严谨、通俗易懂，避免学术黑话
5. HTML 结构清晰，class 命名规范，方便前端渲染和 PDF 导出
6. 报告长度控制在 2000-4000 字之间（如果提供了 Agent C 数据，可适当扩展到 3000-5000 字以容纳更详细的分析）
7. 每个板块必须都有实质内容，不能敷衍跳过
"""

SYSTEM_PROMPT_E = """你是一位在特定行业干了 12 年的老炮，现在是某大厂的总监，带过 30 人团队，面试过 500+ 候选人。

## 你的说话风格
- 毒舌但真诚，不画饼不灌鸡汤，说的话都是真金白银的经验
- 爱用行业黑话和真实案例，能举出具体的公司名、岗位名
- 像在烧烤摊跟后辈聊天一样接地气，不端着
- 敢于说行业潜规则和残酷真相（薪资天花板、加班文化、35岁危机、裁员套路）
- 每条回复控制在 200 字以内，不要长篇大论
- 多用"老弟/老妹"开头，营造亲切感

## 你需要了解的学生背景
用户消息中会包含学生的能力画像、目标岗位的详细信息和岗位AI画像。请根据这些信息给出针对性的、个性化的建议。

## 对话规则
1. 被问到薪资、加班、内卷、35岁危机时，如实回答不回避、不美化
2. 如果学生当前能力与岗位要求差距明显，直接指出来，但立刻给出可操作的补救建议
3. 尽量引用真实的行业数据、技术栈、公司和趋势
4. 对于学生没意识到的重要问题，可以主动点出来（比如"你问了A，但我必须提醒你B"）
5. 保持幽默感，偶尔可以自嘲（"我当年也踩过这个坑，代价是三个月的年终奖"）
"""


# ============================================================
# Agent 编排器
# ============================================================

class AgentOrchestrator:
    """五个 Agent 的编排调用器"""

    def __init__(self, api_key=None):
        self.api_key = api_key or API_KEY
        self.app_ids = {
            'A': APP_ID_A,
            'B': APP_ID_B,
            'C': APP_ID_C,   # 新增：单岗位画像
            'D': APP_ID_D,   # 原 C：报告生成
            'E': APP_ID_E,
        }

    def _call_agent(self, app_id, system_prompt, user_message, stream=True,
                    max_tokens=None, temperature=None):
        """底层调用：发送消息到指定 Agent，返回流式响应生成器

        Args:
            max_tokens: 最大输出 token 数，None 使用百炼平台默认值
            temperature: 采样温度 (0~2)，None 使用百炼平台默认值
        """
        if not self.api_key or not app_id:
            yield {"type": "error", "message": "Agent 配置未完成，请检查 API_KEY 和 APP_ID"}
            return

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ]

        call_params = {
            'api_key': self.api_key,
            'app_id': app_id,
            'messages': messages,
            'stream': True,
            'incremental_output': True
        }

        if max_tokens is not None:
            call_params['max_tokens'] = max_tokens
        if temperature is not None:
            call_params['temperature'] = temperature

        if KNOWLEDGE_BASE_IDS:
            call_params['rag_options'] = {
                'pipeline_ids': KNOWLEDGE_BASE_IDS
            }

        print(f"[AgentOrchestrator] Calling app_id={app_id[:8]}...")
        sys.stdout.flush()

        try:
            response = Application.call(**call_params)
            for chunk in response:
                if chunk.status_code == HTTPStatus.OK:
                    yield {"type": "chunk", "content": chunk.output.text}
                else:
                    yield {
                        "type": "error",
                        "message": f"API 调用失败：{chunk.message} (code={chunk.status_code})"
                    }
                    return
        except Exception as e:
            yield {"type": "error", "message": f"API 调用异常：{str(e)}"}

    # ========================================================
    # Agent A：简历解析 → 学生能力画像
    # ========================================================

    def run_agent_a(self, resume_text):
        """
        输入：简历文本（从 PDF/Word 提取）
        输出：SSE 流 → 最终累积为 JSON
        """
        user_message = f"""你必须严格按照以下 JSON Schema 输出，字段名必须使用英文，不得使用中文键名，不得添加额外字段。仅输出 JSON，不要解释。

Required JSON format:
{{
  "resume_detail_info": {{
    "name": "姓名",
    "email": "邮箱",
    "phone": "手机号",
    "education": "学历（本科/硕士/博士/大专）",
    "school": "学校名称",
    "major": "专业名称",
    "graduation_year": 2025,
    "professional_skills": ["技能1", "技能2"],
    "certificates": ["证书1", "证书2"],
    "internship_experience_detail": [{{"company": "公司名", "position": "职位", "duration": "时间段", "description": "工作描述"}}],
    "project_experience": [{{"name": "项目名", "role": "角色", "description": "项目描述"}}],
    "resume_text": "简历原始文本全文"
  }},
  "ability_dimension_scores": {{
    "professional_skills_certificates": 7.5,
    "innovation_ability": 6.0,
    "learning_ability": 7.0,
    "stress_resistance": 6.5,
    "communication_ability": 6.0,
    "internship_experience": 5.5
  }},
  "ability_overall_scores": {{
    "profile_completeness": 85,
    "competitiveness_score": 72
  }}
}}

评分标准：专业能力/创新/学习/抗压/沟通/实习 六维各0-10分（一位小数）。完整度和竞争力各0-100整数。

简历内容如下：
{resume_text}"""
        return self._call_agent(
            app_id=self.app_ids['A'],
            system_prompt=SYSTEM_PROMPT_A,
            user_message=user_message,
            max_tokens=4000
        )

    # ========================================================
    # Agent B：岗位匹配 → 10 岗位评分
    # ========================================================

    def run_agent_b(self, student_profile_json, job_descriptions):
        """
        输入：
          - student_profile_json: Agent A 输出的学生画像 JSON
          - job_descriptions: 从 MySQL 查询的岗位描述列表
            格式: [{"id": 1, "job_name": "...", "job_description": "..."}, ...]
        输出：SSE 流 → 最终累积为 job_post_profiles JSON
        """
        jobs_text = ""
        for job in job_descriptions:
            jobs_text += f"""
---
岗位 ID: {job['id']}
岗位名称: {job['job_name']}
行业: {job.get('industry', '未知')}
岗位描述: {job.get('job_description', '暂无描述')}
"""

        user_message = f"""你必须严格按照以下 JSON Schema 输出，字段名必须使用英文，不得使用中文键名，不得添加额外字段。仅输出 JSON，不要解释。

Required JSON format (恰好 {len(job_descriptions)} 个岗位):
{{
  "job_post_profiles": [
    {{
      "id": 1,
      "user_matching_scores": {{
        "basic_requirements_matching": 85,
        "professional_skills_matching": 72,
        "professional_literacy_matching": 68,
        "development_potential_matching": 75,
        "overall_matching": 75
      }}
    }}
  ]
}}

每个岗位 ID 必须与下面输入数据中的 ID 一致。user_matching_scores 每维 0-100 整数。匹配分要有区分度。

## 学生能力画像

{student_profile_json}

## 待匹配的岗位 ({len(job_descriptions)} 个)

{jobs_text}"""
        return self._call_agent(
            app_id=self.app_ids['B'],
            system_prompt=SYSTEM_PROMPT_B,
            user_message=user_message,
            max_tokens=3000
        )

    # ========================================================
    # Agent C：单岗位画像分析（按需触发）
    # ========================================================

    def run_agent_c(self, job_info, student_profile_json):
        """
        输入：
          - job_info: dict with id, job_name, job_description, industry
          - student_profile_json: Agent A 输出的学生画像 JSON 字符串
        输出：SSE 流 → ability_requirement_scores + vertical_promotion_info + job_transfer_paths
        """
        user_message = f"""你必须严格按照以下 JSON Schema 输出，字段名必须使用英文，不得使用中文键名，不得添加额外字段。仅输出 JSON，不要解释。

Required JSON format:
{{
  "ability_requirement_scores": {{
    "professional_skills_certificates": 8.0,
    "innovation_ability": 6.0,
    "learning_ability": 7.0,
    "stress_resistance": 5.0,
    "communication_ability": 7.0,
    "internship_experience": 6.0
  }},
  "vertical_promotion_info": {{
    "job_description": "该岗位的一句话描述",
    "complete_promotion_path": ["初级", "中级", "高级", "专家", "总监"]
  }},
  "job_transfer_paths": [
    {{"target_job": "目标岗位名", "transfer_difficulty": "低/中/高", "reason": "转岗理由"}},
    ...恰好5个
  ]
}}

ability_requirement_scores 每维 0-10 分（一位小数）。job_transfer_paths 恰好 5 个。换岗方向参考学生技能画像，给出与学生能力相关的合理转岗建议。

## 待分析岗位

岗位 ID: {job_info['id']}
岗位名称: {job_info['job_name']}
行业: {job_info.get('industry', '未知')}
岗位描述: {job_info.get('job_description', '暂无描述')}

## 学生能力画像（用于转岗路径分析时参考学生的可复用技能）

{student_profile_json}"""
        return self._call_agent(
            app_id=self.app_ids['C'],
            system_prompt=SYSTEM_PROMPT_C,
            user_message=user_message,
            temperature=0.5   # 单岗位画像分析需要稳定输出
        )

    def run_agent_c_sync(self, job_info, student_profile_json):
        """
        Agent C 同步版：内部调用，收集完整响应后返回解析后的 JSON dict。
        用于 Agent D 自动串联时无需前端参与。

        返回：dict 或 None（失败时）
        """
        full_response = ""
        try:
            for event in self.run_agent_c(job_info, student_profile_json):
                if event["type"] == "chunk":
                    full_response += event["content"]
                elif event["type"] == "error":
                    print(f"[Agent C sync] 调用失败: {event['message']}")
                    return None
        except Exception as e:
            print(f"[Agent C sync] 异常: {str(e)}")
            return None

        if not full_response.strip():
            print("[Agent C sync] 空响应")
            return None

        # 提取 JSON（与 agent.py _extract_json 等价，避免循环导入）
        import re
        # 方式1：markdown 代码块
        md_match = re.search(r'```json\n([\s\S]*?)\n```', full_response)
        if md_match:
            try:
                return json.loads(md_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        # 方式2：直接 JSON
        try:
            return json.loads(full_response.strip())
        except json.JSONDecodeError:
            pass
        # 方式3：正则找最外层 {}
        json_match = re.search(r'\{[\s\S]*\}', full_response.strip())
        if json_match:
            try:
                return json.loads(json_match.group(0).strip())
            except json.JSONDecodeError:
                pass
        return None

    # ========================================================
    # Agent D：报告生成 → 职业规划报告 HTML
    # ========================================================

    def run_agent_d(self, student_profile_json, top3_matches_json, agent_c_data=None):
        """
        输入：
          - student_profile_json: Agent A 输出的学生画像
          - top3_matches_json: Agent B 输出的 Top 3 匹配结果
          - agent_c_data: (可选) Agent C 输出的单岗位画像 dict，包含：
              ability_requirement_scores, vertical_promotion_info, job_transfer_paths, job_name
        输出：SSE 流 → 最终累积为 HTML 报告
        """
        # 构建 Agent C 数据段（如果有）
        c_section = ""
        if agent_c_data:
            c_section = f"""

## 目标岗位 AI 画像（Agent C）

这是你本次报告的目标岗位，由 Agent C 深度分析生成。请务必将以下数据融入报告各板块：

**目标岗位**: {agent_c_data.get('job_name', '未知')}

**岗位六维要求分 (ability_requirement_scores)**:
{json.dumps(agent_c_data.get('ability_requirement_scores', {}), ensure_ascii=False, indent=2)}

**晋升路径 (vertical_promotion_info)**:
{json.dumps(agent_c_data.get('vertical_promotion_info', {}), ensure_ascii=False, indent=2)}

**换岗路径 (job_transfer_paths)**:
{json.dumps(agent_c_data.get('job_transfer_paths', []), ensure_ascii=False, indent=2)}

使用以上数据时：
- 在「一、人岗匹配综合分析」中，逐项对比学生六维分 vs 岗位要求分，量化差距
- 在「二、职业发展路径」中，用 vertical_promotion_info.complete_promotion_path 作为真实晋升阶梯
- 在「三、分阶段行动计划」末尾，增加「换岗备选方案」小节，列出 2-3 个相关方向及难度
"""

        user_message = f"""你必须严格按照以下 HTML 格式输出职业发展报告，从 <div class="career-report"> 开始。每个板块都要有实质内容。

Required HTML structure:
<div class="career-report">
  <section class="report-section" id="matching-analysis">
    <h2>一、人岗匹配综合分析</h2>
    <p>3-5段综合分析：竞争力评估、最佳匹配岗位、主要差距、整体建议</p>
  </section>
  <section class="report-section" id="career-goal">
    <h2>二、职业目标与路径规划</h2>
    <div class="sub-section"><h3>1. 核心职业目标</h3><p>推荐1-2个最适合的职业方向及依据</p></div>
    <div class="sub-section"><h3>2. 行业需求与趋势分析</h3><p>行业现状、3-5年趋势、机遇挑战</p></div>
    <div class="sub-section"><h3>3. 明确的发展路径</h3>
      <div class="path-item"><h4>短期(0-2年)</h4><p>...</p></div>
      <div class="path-item"><h4>中期(2-5年)</h4><p>...</p></div>
      <div class="path-item"><h4>长期(5-10年)</h4><p>...</p></div>
    </div>
  </section>
  <section class="report-section" id="action-plan">
    <h2>三、分阶段行动计划</h2>
    <div class="sub-section"><h3>1. 分阶段成长计划</h3>
      <div class="plan-phase"><h4>0-1年：立即行动</h4><ul><li>...</li></ul></div>
      <div class="plan-phase"><h4>1-3年：快速成长</h4><ul><li>...</li></ul></div>
      <div class="plan-phase"><h4>3-5年：稳步发展</h4><ul><li>...</li></ul></div>
    </div>
    <div class="sub-section"><h3>2. 动态评估机制</h3><p>6个月一次自评维度、评估指标、调整策略</p></div>
  </section>
</div>

要求：专业严谨通俗易懂，建议可落地，2000-4000字，不虚构信息。

## 学生能力画像

{student_profile_json}

## Top 3 岗位匹配结果

{top3_matches_json}
{c_section}"""
        return self._call_agent(
            app_id=self.app_ids['D'],
            system_prompt=SYSTEM_PROMPT_D,
            user_message=user_message,
            max_tokens=8000  # HTML 报告 2000-4000 字 + 标签，需要足够 token 防止截断
        )

    # ========================================================
    # Agent E：虚拟行业大佬 1v1 访谈
    # ========================================================

    def _summarize_history(self, messages_to_summarize, existing_summary=""):
        """将旧对话压缩为摘要（同步调用 Agent E）

        Args:
            messages_to_summarize: list of {role, content, time} 需要压缩的消息
            existing_summary: 已有的摘要字符串，会合并进去
        Returns:
            新的摘要字符串
        """
        old_text = ""
        for msg in messages_to_summarize:
            role = "学生" if msg['role'] == 'user' else "大佬"
            old_text += f"{role}: {msg['content']}\n"

        summary_prompt = f"""把以下对话压缩成一段 100 字以内的摘要，只记录关键事实（问了什么、答了什么、做了哪些建议）。

{"已有摘要：" + existing_summary + chr(10) + chr(10) if existing_summary else ""}新增对话：
{old_text}

直接输出摘要，不要加任何前缀。"""

        result = ""
        try:
            for event in self._call_agent(
                app_id=self.app_ids['E'],
                system_prompt="你是对话摘要助手，把对话压缩成精炼的事实摘要。",
                user_message=summary_prompt,
                temperature=0.3,
                stream=True
            ):
                if event["type"] == "chunk":
                    result += event["content"]
                elif event["type"] == "error":
                    print(f"[Summary] 摘要生成失败: {event['message']}")
                    return existing_summary or "（历史对话摘要不可用）"
        except Exception as e:
            print(f"[Summary] 摘要异常: {e}")
            return existing_summary or "（历史对话摘要不可用）"

        return result.strip() or (existing_summary or "（历史对话摘要不可用）")

    # ========================================================

    def run_agent_e(self, student_profile_json, job_info, agent_c_data, chat_history, user_message_text):
        """
        输入：
          - student_profile_json: Agent A 输出的学生画像 JSON 字符串
          - job_info: dict with id, job_name, company_name, salary_range, industry, job_description
          - agent_c_data: Agent C 输出的岗位 AI 画像 dict（或 None）
          - chat_history: list of {role, content, time}，可能含 {"role":"summary"} 摘要
          - user_message_text: 用户当前发送的问题
        输出：SSE 流 → "行业大佬"角色的回复文本
        """
        RECENT_MSG_COUNT = 6  # 保留最近 3 轮（6 条消息）

        # 分离摘要和实际消息
        summary = ""
        actual_history = []
        for msg in (chat_history or []):
            if msg.get('role') == 'summary':
                summary = msg['content']
            else:
                actual_history.append(msg)

        # 只保留最近 3 轮给 Agent 做上下文
        recent_history = actual_history[-RECENT_MSG_COUNT:] if len(actual_history) > RECENT_MSG_COUNT else actual_history

        # 构建 Agent C 数据段
        c_section = ""
        if agent_c_data:
            c_section = f"""

## 岗位 AI 画像（你对该岗位的内部分析）

**六维要求分**:
{json.dumps(agent_c_data.get('ability_requirement_scores', {}), ensure_ascii=False, indent=2)}

**晋升路径**:
{json.dumps(agent_c_data.get('vertical_promotion_info', {}), ensure_ascii=False, indent=2)}

**换岗路径**:
{json.dumps(agent_c_data.get('job_transfer_paths', []), ensure_ascii=False, indent=2)}
"""

        # 构建历史对话段
        history_section = ""
        if summary:
            history_section += f"\n## 更早的对话摘要（已压缩）\n{summary}\n"
        if recent_history:
            history_section += "\n## 最近对话\n\n"
            for msg in recent_history:
                role_label = "学生" if msg['role'] == 'user' else "你"
                history_section += f"{role_label}: {msg['content']}\n\n"

        full_message = f"""## 学生能力画像

{student_profile_json}

## 目标岗位信息

岗位名称: {job_info.get('job_name', '未知')}
公司: {job_info.get('company_name', '未知')}
薪资范围: {job_info.get('salary_range', '未知')}
行业: {job_info.get('industry', '未知')}
岗位描述: {job_info.get('job_description', '暂无描述')}
{c_section}
{history_section}
## 学生最新问题

{user_message_text}

请以你"行业老炮/大厂总监"的角色，针对上面这个问题给出真实、接地气的回答。记住你的说话风格：毒舌真诚、用黑话、像烧烤摊聊天。200 字以内。"""

        return self._call_agent(
            app_id=self.app_ids['E'],
            system_prompt=SYSTEM_PROMPT_E,
            user_message=full_message,
            temperature=0.9
        )


# 全局单例
orchestrator = AgentOrchestrator()
