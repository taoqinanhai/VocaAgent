"""
简历解析服务：从 Agent A 的 JSON 响应中提取学生画像并存入数据库

适配新的 3-Agent 架构 — Agent A 只输出画像数据
(resume_detail_info + ability_dimension_scores + ability_overall_scores)
"""
import re
import json
import datetime
from utils.db import get_db_connection


def parse_profile_json(ai_response_text):
    """
    从 Agent A 的流式响应中提取 JSON

    Agent A 输出格式（无 core_output 包裹）：
    {
      "resume_detail_info": {...},
      "ability_dimension_scores": {...},
      "ability_overall_scores": {...}
    }
    """
    try:
        # 尝试从 markdown 代码块提取
        json_match = re.search(r'```json\n([\s\S]*?)\n```', ai_response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 直接从文本中提取 JSON 对象
            json_match = re.search(r'\{[\s\S]*\}', ai_response_text.strip())
            if not json_match:
                return None, "无法从 AI 返回内容中提取 JSON 数据"
            json_str = json_match.group(0)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            return None, f"JSON 解析失败：{str(e)}"

        return data, None
    except Exception as e:
        return None, f"解析异常：{str(e)}"


def save_student_profile(profile_data, user_id=1):
    """
    将 Agent A 的学生画像存入 students 表

    输入格式：
    {
      "resume_detail_info": {
        "name", "email", "phone", "education", "school", "major",
        "graduation_year", "professional_skills", "certificates",
        "internship_experience_detail", "project_experience", "resume_text"
      },
      "ability_dimension_scores": {
        "professional_skills_certificates", "innovation_ability",
        "learning_ability", "stress_resistance",
        "communication_ability", "internship_experience"
      },
      "ability_overall_scores": {
        "profile_completeness", "competitiveness_score"
      }
    }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        resume_detail = profile_data.get("resume_detail_info", {})
        ability_dim = profile_data.get("ability_dimension_scores", {})
        ability_overall = profile_data.get("ability_overall_scores", {})

        # 安全类型转换
        def safe_float(value, default=0.0):
            try:
                return float(value)
            except (ValueError, TypeError):
                return default

        def safe_int(value, default=0):
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        # 实习详情 → JSON 字符串
        internship_detail = resume_detail.get("internship_experience_detail", [])
        if isinstance(internship_detail, (list, dict)):
            internship_detail = json.dumps(internship_detail, ensure_ascii=False)

        sql_student = """
        INSERT INTO students (
            user_id, student_id,
            name, email, phone, education, school, major, graduation_year,
            professional_skills, certificates,
            professional_skills_certificates,
            innovation_ability,
            learning_ability,
            stress_resistance,
            communication_ability,
            internship_experience,
            project_experience,
            profile_completeness,
            competitiveness_score,
            resume_text,
            resume_url,
            internship_experience_detail,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """

        val_student = (
            user_id,
            None,
            resume_detail.get("name", ""),
            resume_detail.get("email", ""),
            resume_detail.get("phone", ""),
            resume_detail.get("education", ""),
            resume_detail.get("school", ""),
            resume_detail.get("major", ""),
            safe_int(resume_detail.get("graduation_year")),

            json.dumps(resume_detail.get("professional_skills", []), ensure_ascii=False),
            json.dumps(resume_detail.get("certificates", []), ensure_ascii=False),

            safe_float(ability_dim.get("professional_skills_certificates", 0)),
            safe_float(ability_dim.get("innovation_ability", 0)),
            safe_float(ability_dim.get("learning_ability", 0)),
            safe_float(ability_dim.get("stress_resistance", 0)),
            safe_float(ability_dim.get("communication_ability", 0)),
            safe_float(ability_dim.get("internship_experience", 0)),

            json.dumps(resume_detail.get("project_experience", []), ensure_ascii=False),

            safe_float(ability_overall.get("profile_completeness", 0)),
            safe_float(ability_overall.get("competitiveness_score", 0)),

            resume_detail.get("resume_text", ""),
            "",
            internship_detail,

            datetime.datetime.now(),
            datetime.datetime.now()
        )

        cursor.execute(sql_student, val_student)
        student_id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()

        return student_id, None

    except Exception as e:
        import traceback
        print("===== 保存学生画像失败 =====")
        traceback.print_exc()
        return None, f"保存失败：{str(e)}"


def parse_and_save_resume_data(ai_response_text, user_id=1):
    """
    兼容旧接口：解析 Agent A 响应 → 存入数据库
    返回 (student_id, error_message)
    """
    # 1. 提取 JSON
    data, error = parse_profile_json(ai_response_text)
    if error:
        return None, error

    # 2. 存入数据库
    return save_student_profile(data, user_id)
