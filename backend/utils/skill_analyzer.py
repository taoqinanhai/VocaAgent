"""
技能分析引擎 — 纯 Python 规则引擎，零 AI 调用
职责：
  1. 从岗位描述中提取技能要求（关键词匹配）
  2. 批量填充 job_skill_requirements 表
  3. 比对学生技能 vs 岗位要求，输出差距清单
"""

import re
from utils.db import get_db_connection

# ============================================================
# 技能关键词字典
# 格式：{ 技能名: (类别, 基准权重) }
# 权重越高 = 该技能在大多数岗位中越核心
# ============================================================

SKILL_KEYWORDS = {
    # ---- Java 体系 ----
    'Java': ('后端', 0.30),
    'J2EE': ('后端', 0.25),
    'Spring Boot': ('后端', 0.25),
    'Spring Cloud': ('后端', 0.22),
    'Spring MVC': ('后端', 0.20),
    'Spring': ('后端', 0.22),
    'MyBatis': ('后端', 0.15),
    'Hibernate': ('后端', 0.12),
    'JPA': ('后端', 0.10),
    'Maven': ('后端', 0.08),
    'Gradle': ('后端', 0.06),
    'Tomcat': ('后端', 0.08),
    'Netty': ('后端', 0.10),

    # ---- Python 体系 ----
    'Python': ('后端', 0.28),
    'Django': ('后端', 0.18),
    'Flask': ('后端', 0.15),
    'FastAPI': ('后端', 0.15),
    'Tornado': ('后端', 0.08),

    # ---- C/C++/C# 体系 ----
    'C++': ('后端', 0.25),
    'C#': ('后端', 0.22),
    '.NET': ('后端', 0.20),
    'Qt': ('后端', 0.12),
    'MFC': ('后端', 0.06),

    # ---- Go/Rust 体系 ----
    'Go': ('后端', 0.20),
    'Golang': ('后端', 0.20),
    'Rust': ('后端', 0.12),

    # ---- Node.js 体系 ----
    'Node.js': ('后端', 0.18),
    'Express': ('后端', 0.10),

    # ---- PHP 体系 ----
    'PHP': ('后端', 0.18),
    'Laravel': ('后端', 0.12),

    # ---- 前端 ----
    'JavaScript': ('前端', 0.25),
    'TypeScript': ('前端', 0.22),
    'Vue': ('前端', 0.22),
    'React': ('前端', 0.22),
    'Angular': ('前端', 0.18),
    'HTML': ('前端', 0.18),
    'HTML5': ('前端', 0.18),
    'CSS': ('前端', 0.15),
    'CSS3': ('前端', 0.15),
    'Sass': ('前端', 0.08),
    'Less': ('前端', 0.06),
    'Webpack': ('前端', 0.10),
    'Vite': ('前端', 0.08),
    'jQuery': ('前端', 0.05),
    'Bootstrap': ('前端', 0.06),
    'Element UI': ('前端', 0.06),
    'ECharts': ('前端', 0.06),
    '微信小程序': ('前端', 0.12),
    'UniApp': ('前端', 0.08),

    # ---- 数据库 ----
    'MySQL': ('数据库', 0.18),
    'PostgreSQL': ('数据库', 0.15),
    'Oracle': ('数据库', 0.15),
    'SQL Server': ('数据库', 0.15),
    'MongoDB': ('数据库', 0.12),
    'Redis': ('数据库', 0.15),
    'Elasticsearch': ('数据库', 0.12),
    'SQL': ('数据库', 0.15),
    'NoSQL': ('数据库', 0.08),

    # ---- 大数据 ----
    'Hadoop': ('大数据', 0.15),
    'Spark': ('大数据', 0.15),
    'Flink': ('大数据', 0.12),
    'Kafka': ('大数据', 0.15),
    'Hive': ('大数据', 0.10),
    'HBase': ('大数据', 0.08),
    '数据仓库': ('大数据', 0.10),
    'ETL': ('大数据', 0.10),

    # ---- AI/ML ----
    '机器学习': ('AI', 0.15),
    '深度学习': ('AI', 0.15),
    'TensorFlow': ('AI', 0.12),
    'PyTorch': ('AI', 0.12),
    'NLP': ('AI', 0.10),
    '计算机视觉': ('AI', 0.10),

    # ---- DevOps/云 ----
    'Docker': ('运维', 0.12),
    'Kubernetes': ('运维', 0.15),
    'K8s': ('运维', 0.15),
    'Jenkins': ('运维', 0.10),
    'Git': ('运维', 0.10),
    'GitLab': ('运维', 0.08),
    'CI/CD': ('运维', 0.10),
    'Linux': ('运维', 0.12),
    'Unix': ('运维', 0.08),
    'Shell': ('运维', 0.08),
    'AWS': ('运维', 0.10),
    '阿里云': ('运维', 0.10),
    'Azure': ('运维', 0.08),
    'Nginx': ('运维', 0.10),
    'Zabbix': ('运维', 0.06),
    'Prometheus': ('运维', 0.08),
    'Grafana': ('运维', 0.06),

    # ---- 架构/通用 ----
    '微服务': ('架构', 0.18),
    '分布式': ('架构', 0.15),
    '架构设计': ('架构', 0.12),
    '设计模式': ('架构', 0.08),
    '高并发': ('架构', 0.12),
    'RESTful': ('架构', 0.08),
    'API': ('架构', 0.08),
    'Socket': ('架构', 0.06),
    'TCP/IP': ('架构', 0.08),
    'HTTP': ('架构', 0.06),
    '多线程': ('架构', 0.08),
    'JVM': ('架构', 0.10),

    # ---- 测试 ----
    '自动化测试': ('测试', 0.12),
    'Selenium': ('测试', 0.08),
    'JUnit': ('测试', 0.06),
    'TestNG': ('测试', 0.05),
    'JMeter': ('测试', 0.08),
    'Appium': ('测试', 0.06),

    # ---- 移动端 ----
    'Android': ('移动', 0.20),
    'iOS': ('移动', 0.20),
    'Swift': ('移动', 0.18),
    'Kotlin': ('移动', 0.18),
    'Flutter': ('移动', 0.15),
    'React Native': ('移动', 0.12),

    # ---- 通用技能 ----
    '数据分析': ('通用', 0.10),
    'Tableau': ('通用', 0.08),
    'Excel': ('通用', 0.06),
    'Power BI': ('通用', 0.08),
    '项目管理': ('通用', 0.08),
    'Scrum': ('通用', 0.06),
    'JIRA': ('通用', 0.05),
    'Confluence': ('通用', 0.04),
    'Figma': ('通用', 0.06),
    'Photoshop': ('通用', 0.06),
    'Blender': ('通用', 0.04),
}

# 需要精确匹配（避免子串误伤）的技能名
_EXACT_MATCH_SKILLS = {
    'Go', 'C++', 'C#', 'PHP', 'CSS', 'SQL', 'API', 'JPA',
    'HTML', 'AWS', 'Qt', 'NLP', 'ETL', 'iOS', 'JVM', 'K8s',
    'Nginx', 'Vite', 'Sass', 'Less', 'Shell', 'Git',
}


def extract_skills_from_text(text: str) -> list[dict]:
    """
    从文本中提取技能关键词及其权重。

    Args:
        text: 岗位描述文本

    Returns:
        [{name: 'Java', category: '后端', weight: 0.30}, ...]
        按权重降序排列，去重。

    匹配规则：
        - 大多数技能用子串匹配（'Java' 匹配 '需要Java开发经验'）
        - _EXACT_MATCH_SKILLS 中的技能用词边界匹配，避免子串误伤
          （比如 'Go' 不应匹配 'Google', 'C++' 不应匹配 'C+++')
    """
    if not text:
        return []

    text_lower = text.lower()
    found = {}

    for skill_name, (category, weight) in SKILL_KEYWORDS.items():
        skill_lower = skill_name.lower()

        if skill_name in _EXACT_MATCH_SKILLS:
            # 词边界匹配：避免 'Go' 匹配 'Google'、'CSS' 匹配 'CSS3'
            pattern = re.compile(r'\b' + re.escape(skill_name) + r'\b', re.IGNORECASE)
            if pattern.search(text):
                found[skill_name] = {'name': skill_name, 'category': category, 'weight': weight}
        else:
            # 子串匹配
            if skill_lower in text_lower:
                # 额外检查：'Java' 不应匹配 'JavaScript'（除非也明确出现 Java）
                if skill_name == 'Java' and 'javascript' in text_lower:
                    # 检查纯 Java 是否出现（不在 Script 前）
                    if not re.search(r'\bJava\b(?!\s*Script)', text, re.IGNORECASE):
                        continue
                if skill_name == 'Python' and 'python' not in text_lower:
                    continue
                found[skill_name] = {'name': skill_name, 'category': category, 'weight': weight}

    # 按权重降序
    result = sorted(found.values(), key=lambda x: x['weight'], reverse=True)
    return result


def populate_job_skills(batch_size: int = 500, force: bool = False) -> int:
    """
    从 jobs 表提取技能要求，写入 job_skill_requirements。

    默认增量模式：只处理 jobs 表中尚未在 job_skill_requirements 里的新岗位。
    force=True：清空旧数据，全量重建。

    Returns:
        写入的技能记录总数
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if force:
        cursor.execute("DELETE FROM job_skill_requirements")
        print("[skill_analyzer] force=True，已清空 job_skill_requirements 旧数据")
        cursor.execute("SELECT id, job_description FROM jobs")
    else:
        cursor.execute("SELECT id, job_description FROM jobs WHERE id NOT IN (SELECT job_id FROM job_skill_requirements)")

    jobs = cursor.fetchall()

    if not jobs:
        print("[skill_analyzer] 没有新岗位需要处理，跳过")
        cursor.close()
        conn.close()
        return 0

    total_jobs = len(jobs)
    print(f"[skill_analyzer] 共 {total_jobs} 条新岗位，开始提取技能...")

    total_skills = 0
    buffer = []

    for idx, job in enumerate(jobs):
        job_id = job['id']
        jd = job.get('job_description') or ''
        skills = extract_skills_from_text(jd)

        for skill in skills:
            buffer.append((
                job_id,
                skill['name'],
                skill['weight'],
                3.0  # 默认要求熟练度：3 = 熟练
            ))

        if len(buffer) >= batch_size:
            _batch_insert(cursor, buffer)
            total_skills += len(buffer)
            buffer = []
            if (idx + 1) % 1000 == 0:
                print(f"  已处理 {idx + 1}/{total_jobs} 条岗位, {total_skills} 条技能记录")

    # 剩余
    if buffer:
        _batch_insert(cursor, buffer)
        total_skills += len(buffer)

    conn.commit()
    cursor.close()
    conn.close()

    avg = total_skills / total_jobs if total_jobs > 0 else 0
    print(f"[skill_analyzer] 完成！{total_jobs} 条岗位 → {total_skills} 条技能记录 (平均 {avg:.1f} 技能/岗位)")
    return total_skills


def _batch_insert(cursor, rows: list[tuple]):
    """批量插入 job_skill_requirements"""
    sql = """
        INSERT INTO job_skill_requirements (job_id, skill_name, weight, required_level)
        VALUES (%s, %s, %s, %s)
    """
    cursor.executemany(sql, rows)


def analyze_skill_gap(student_skill_details: list[dict], job_id: int) -> dict:
    """
    比对学生技能清单 vs 岗位技能要求，输出差距分析。

    Args:
        student_skill_details: [{"name": "Java", "proficiency": 4.5}, ...]
        job_id: 岗位 ID

    Returns:
        {
            "matched": [{"name": "Java", "student": 4.5, "required": 3.0, "gap": +1.5}, ...],
            "insufficient": [{"name": "SQL", "student": 2.0, "required": 3.5, "gap": -1.5}, ...],
            "missing": [{"name": "Redis", "required": 3.0, "weight": 0.15}, ...],
            "job_skill_count": 8,
            "match_rate": 0.625    # 匹配率 (matched / total job skills)
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT skill_name, weight, required_level FROM job_skill_requirements WHERE job_id = %s",
        (job_id,)
    )
    job_skills = cursor.fetchall()
    cursor.close()
    conn.close()

    if not job_skills:
        return {
            "matched": [],
            "insufficient": [],
            "missing": [],
            "job_skill_count": 0,
            "match_rate": 0.0
        }

    # 学生技能名 → proficiency 映射
    student_map = {s['name'].lower(): s.get('proficiency', 3.0) for s in student_skill_details}

    matched = []
    insufficient = []
    missing = []

    for js in job_skills:
        skill_name = js['skill_name']
        required_level = float(js['required_level'])
        weight = float(js['weight'])
        student_level = student_map.get(skill_name.lower())

        if student_level is not None:
            gap = round(student_level - required_level, 1)
            if gap >= 0:
                matched.append({
                    "name": skill_name,
                    "student": student_level,
                    "required": required_level,
                    "gap": gap
                })
            else:
                insufficient.append({
                    "name": skill_name,
                    "student": student_level,
                    "required": required_level,
                    "gap": gap,
                    "weight": weight
                })
        else:
            missing.append({
                "name": skill_name,
                "required": required_level,
                "weight": weight
            })

    # 排序：insufficient 按差距降序（差距越大越紧急），missing 按权重降序
    insufficient.sort(key=lambda x: x['gap'])
    missing.sort(key=lambda x: x['weight'], reverse=True)

    total_job_skills = len(job_skills)
    match_rate = len(matched) / total_job_skills if total_job_skills > 0 else 0.0

    return {
        "matched": matched,
        "insufficient": insufficient,
        "missing": missing,
        "job_skill_count": total_job_skills,
        "match_rate": round(match_rate, 3)
    }


def select_top_jobs(student_skill_details: list[dict], job_ids: list[int] = None,
                    top_n: int = 10) -> list[tuple]:
    """
    规则引擎粗筛：根据学生技能对所有岗位做匹配打分，返回 Top N 岗位。

    用于 Agent B 前置筛选，替代盲目的 LIMIT 10。

    Args:
        student_skill_details: [{"name": "Java", "proficiency": 4.5}, ...]
        job_ids: 可选，限定岗位范围（None = 全量）
        top_n: 返回前 N 个岗位

    Returns:
        [(job_id, score), ...]  按 score 降序，长度 ≤ top_n

    评分公式：
        job_score = Σ (matched_skill.weight × proficiency_factor)
        proficiency_factor = min(1.0, student_level / required_level)
        未匹配的技能不扣分，但也不加分（自然降低排名）
    """
    if not student_skill_details:
        return []

    conn = get_db_connection()
    cursor = conn.cursor()

    if job_ids and isinstance(job_ids, list) and len(job_ids) > 0:
        placeholders = ','.join(['%s'] * len(job_ids))
        cursor.execute(
            f"SELECT job_id, skill_name, weight, required_level "
            f"FROM job_skill_requirements WHERE job_id IN ({placeholders})",
            job_ids
        )
    else:
        cursor.execute(
            "SELECT job_id, skill_name, weight, required_level FROM job_skill_requirements"
        )

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return []

    # 学生技能名 → proficiency 映射
    student_map = {s['name'].lower(): s.get('proficiency', 3.0) for s in student_skill_details}

    # 按 job_id 分组计算分数
    job_scores = {}  # job_id → score
    for row in rows:
        job_id = row['job_id']
        skill_name = row['skill_name']
        weight = float(row['weight'])
        required_level = float(row['required_level'])

        student_level = student_map.get(skill_name.lower())
        if student_level is not None:
            proficiency_factor = min(1.0, student_level / max(required_level, 0.1))
            score_contribution = weight * proficiency_factor
            job_scores[job_id] = job_scores.get(job_id, 0.0) + score_contribution

    # 按分数降序，取 top_n
    sorted_jobs = sorted(job_scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_jobs[:top_n]


def format_gap_for_prompt(gap_result: dict) -> str:
    """
    将差距分析结果格式化为注入 Prompt 的文本段。
    用于 Agent C / E 的 user_message。
    """
    if not gap_result or gap_result.get('job_skill_count', 0) == 0:
        return "（该岗位暂无结构化技能数据）"

    lines = [f"## 技能差距分析（匹配率: {gap_result['match_rate'] * 100:.0f}%）"]

    if gap_result['matched']:
        items = [f"{m['name']}(学生{m['student']}分 vs 要求{m['required']}分)" for m in gap_result['matched'][:5]]
        lines.append(f"- 已匹配: {', '.join(items)}")

    if gap_result['insufficient']:
        items = [f"{m['name']}(学生{m['student']}分 vs 要求{m['required']}分, 差距{m['gap']}分)" for m in gap_result['insufficient']]
        lines.append(f"- 熟练度不足: {', '.join(items)}")

    if gap_result['missing']:
        items = [f"{m['name']}(要求{m['required']}分)" for m in gap_result['missing'][:8]]
        lines.append(f"- 完全缺失: {', '.join(items)}")

    lines.append("\n请针对以上具体技能差距给出提升建议，不要泛泛而谈。")
    return '\n'.join(lines)
