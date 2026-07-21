"""
Agent 路由工具函数
被 Agent B/C/D 端点调用：JSON 提取、HTML 校验、报告字段提取
"""
import re
import json


def _extract_json(text: str):
    """从 AI 返回的文本中提取 JSON 对象"""
    # 方式1：markdown 代码块
    md_match = re.search(r'```json\n([\s\S]*?)\n```', text)
    if md_match:
        try:
            return json.loads(md_match.group(1).strip())
        except json.JSONDecodeError:
            pass
    # 方式2：直接 JSON
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
    # 方式3：正则找最外层 {}
    json_match = re.search(r'\{[\s\S]*\}', text.strip())
    if json_match:
        try:
            return json.loads(json_match.group(0).strip())
        except json.JSONDecodeError:
            pass
    return None


def _validate_report_html(html: str) -> str:
    """
    校验 Agent D 生成的 HTML 报告完整性。
    返回空字符串表示正常，否则返回警告信息（可展示给用户）。
    """
    warnings = []

    if not html or not html.strip():
        return "报告 HTML 为空"

    stripped = html.strip()

    # 1. 检查 HTML 是否以 </div> 结尾（报告最外层容器）
    if not stripped.endswith('</div>'):
        last_tag = stripped[-80:]
        warnings.append(f"报告末尾可能不完整，末尾内容: ...{last_tag[-40:]}")

    # 2. 检查 <p> 标签配对
    open_ps = len(re.findall(r'<p[>\s]', stripped))
    close_ps = len(re.findall(r'</p>', stripped))
    if open_ps != close_ps:
        warnings.append(f"<p> 标签不配对 (开{open_ps}/闭{close_ps})，可能有段落被截断")

    # 3. 检查 <div> 标签配对
    open_divs = len(re.findall(r'<div[>\s]', stripped))
    close_divs = len(re.findall(r'</div>', stripped))
    if open_divs != close_divs:
        warnings.append(f"<div> 标签不配对 (开{open_divs}/闭{close_divs})")

    # 4. 检查 <section> 标签配对
    open_secs = len(re.findall(r'<section[>\s]', stripped))
    close_secs = len(re.findall(r'</section>', stripped))
    if open_secs != close_secs:
        warnings.append(f"<section> 标签不配对 (开{open_secs}/闭{close_secs})")

    # 5. 检查 <ul>/<ol> 标签配对
    open_uls = len(re.findall(r'<ul[>\s]', stripped)) + len(re.findall(r'<ol[>\s]', stripped))
    close_uls = len(re.findall(r'</ul>', stripped)) + len(re.findall(r'</ol>', stripped))
    if open_uls != close_uls:
        warnings.append(f"列表标签不配对 (开{open_uls}/闭{close_uls})")

    return '; '.join(warnings) if warnings else ''


def _extract_career_fields(html: str) -> dict:
    """
    从 Agent D 输出的 HTML 报告中提取 6 个职业规划文本字段，
    用于填充 students 表（配合 Agent A 的画像数据，完成整条学生记录）

    HTML 报告结构（Agent D System Prompt 定义）:
      <section id="matching-analysis"> → person_post_matching_analysis
      <section id="career-goal">
        <h3>1. 核心职业目标</h3> → core_career_goal
        <h3>2. 行业需求与趋势分析</h3> → industry_demand_and_trend_analysis
        <h3>3. 明确的发展路径</h3> → clear_career_development_path
      <section id="action-plan">
        <h3>1. 分阶段成长计划</h3> → staged_growth_plan
        <h3>2. 动态评估机制</h3> → dynamic_evaluation_mechanism
    """

    def _strip_tags(s: str) -> str:
        """去掉 HTML 标签，保留文本"""
        s = re.sub(r'<[^>]+>', '', s)
        s = re.sub(r'\n\s*\n', '\n\n', s)
        s = s.strip()
        return s

    def _extract_section(section_id: str) -> str:
        """提取指定 id 的 <section> 内容"""
        pattern = rf'<section[^>]*id="{section_id}"[^>]*>(.*?)</section>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            return _strip_tags(match.group(1))
        return ''

    def _extract_subsection(section_id: str, h3_label: str) -> str:
        """提取 section 内特定 h3 标签之后到下一个 h3 或 section 结束之间的内容"""
        section_html = ''
        pattern = rf'<section[^>]*id="{section_id}"[^>]*>(.*?)</section>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            section_html = match.group(1)

        h3_pattern = rf'<h3[^>]*>\s*{h3_label}[^<]*</h3>(.*?)(?:<h3|<div class="sub-section"|</section|$)'
        h3_match = re.search(h3_pattern, section_html, re.DOTALL)
        if h3_match:
            return _strip_tags(h3_match.group(1))
        return ''

    return {
        'person_post_matching_analysis': _extract_section('matching-analysis'),
        'core_career_goal': _extract_subsection('career-goal', r'1\.\s*核心职业目标'),
        'industry_demand_and_trend_analysis': _extract_subsection('career-goal', r'2\.\s*行业需求与趋势分析'),
        'clear_career_development_path': _extract_subsection('career-goal', r'3\.\s*(?:明确的|职业)发展路径'),
        'staged_growth_plan': _extract_subsection('action-plan', r'1\.\s*分阶段成长计划'),
        'dynamic_evaluation_mechanism': _extract_subsection('action-plan', r'2\.\s*动态评估机制'),
    }


def build_job_context(job_row: dict) -> dict:
    """
    从 DB 行构建统一的岗位上下文，供所有 Agent（B/C/D/E）使用。

    确保每个 Agent 看到的岗位数据一致，避免「Agent E 传了公司名但 B 没传」的问题。

    Args:
        job_row: pymysql 查询返回的 dict（至少包含 jobs 表核心列）

    Returns:
        {id, job_name, industry, job_description, company_name, salary_range,
         work_address, company_size, company_type, company_description}
    """
    return {
        'id': job_row['id'],
        'job_name': job_row.get('job_name', ''),
        'industry': job_row.get('industry', ''),
        'job_description': job_row.get('job_description', ''),
        'company_name': job_row.get('company_name', ''),
        'salary_range': job_row.get('salary_range', ''),
        'work_address': job_row.get('work_address', ''),
        'company_size': job_row.get('company_size', ''),
        'company_type': job_row.get('company_type', ''),
        'company_description': job_row.get('company_description', ''),
    }


# 所有 Agent 共用的岗位 SQL 查询列
JOB_CONTEXT_COLUMNS = (
    "id, job_name, industry, job_description, "
    "company_name, salary_range, work_address, "
    "company_size, company_type, company_description"
)
