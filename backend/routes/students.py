"""
学生画像 + 简历解析路由：/api/students/*, /api/parse-resume
"""
import json
import os
import time
import sys
import datetime
from http import HTTPStatus
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from dashscope import Application
from config.settings import API_KEY, APP_ID_A, KNOWLEDGE_BASE_IDS, UPLOAD_FOLDER
from utils.db import get_db_connection
from utils.auth import get_current_user
from utils.file_processor import allowed_file, extract_file_content
from services.resume_parser import parse_and_save_resume_data

students_bp = Blueprint('students', __name__)


# ==================== 简历解析 ====================

@students_bp.route('/api/parse-resume', methods=['POST'])
def parse_resume():
    """上传简历或手动输入文本并解析存入数据库"""
    try:
        content_type = request.content_type or ''

        if content_type.startswith('multipart/form-data'):
            file = request.files.get('file')
            user_id = request.form.get('user_id', 1)

            current_user = get_current_user()
            if current_user:
                user_id = current_user['id']
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    cursor.close()
                    conn.close()
                    return jsonify({"error": "用户不存在，请先登录或创建用户"}), 400
                cursor.close()
                conn.close()

            if not file or file.filename == '':
                return jsonify({"error": "请上传简历文件"}), 400

            if not allowed_file(file.filename):
                return jsonify({"error": "不支持的文件格式"}), 400

            original_filename = file.filename
            if '.' in original_filename:
                ext = original_filename.rsplit('.', 1)[1].lower()
            else:
                ext = ''

            safe_name = secure_filename(original_filename.rsplit('.', 1)[0]) if '.' in original_filename else secure_filename(original_filename)
            if not safe_name:
                safe_name = 'file'
            filename = f"{safe_name}_{int(time.time())}.{ext}" if ext else f"{safe_name}_{int(time.time())}"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            print(f"===== 简历文件信息 =====")
            print(f"原始文件名: {original_filename}")
            print(f"提取的扩展名: {ext}")
            print(f"保存的文件名: {filename}")
            print(f"完整路径: {filepath}")
            print(f"文件是否存在: {os.path.exists(filepath)}")
            print(f"========================")
            sys.stdout.flush()

            file_content = extract_file_content(filepath)

            prompt = f"""请分析以下简历内容，返回JSON格式结果。

简历内容：
{file_content}

请返回包含学生能力画像、职业规划和岗位匹配结果的JSON数据。"""

            messages = [{'role': 'user', 'content': prompt}]

            call_params = {
                'api_key': API_KEY,
                'app_id': APP_ID_A,
                'messages': messages,
                'stream': True,
                'incremental_output': True
            }

            if KNOWLEDGE_BASE_IDS:
                call_params['rag_options'] = {
                    'pipeline_ids': KNOWLEDGE_BASE_IDS
                }

            response = Application.call(**call_params)

            full_response = ""
            for chunk in response:
                if chunk.status_code == HTTPStatus.OK:
                    full_response += chunk.output.text
                else:
                    return jsonify({
                        "error": f"AI调用失败：{chunk.message}"
                    }), 500

            return jsonify({"response": full_response})

        elif content_type.startswith('application/json'):
            data = request.get_json()
            if not data:
                return jsonify({"error": "请求数据不能为空"}), 400

            ai_response = data.get('ai_response')
            user_id = data.get('user_id', 1)

            current_user = get_current_user()
            if current_user:
                user_id = current_user['id']
            else:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
                if not cursor.fetchone():
                    cursor.close()
                    conn.close()
                    return jsonify({"error": "用户不存在，请先登录或创建用户"}), 400
                cursor.close()
                conn.close()

            if not ai_response:
                return jsonify({"error": "AI响应数据不能为空"}), 400

            full_response = ai_response
        else:
            return jsonify({"error": "不支持的请求格式"}), 415

        student_id, error = parse_and_save_resume_data(full_response, user_id)

        if error:
            return jsonify({
                "error": error,
                "ai_response": full_response
            }), 500

        return jsonify({
            "success": True,
            "message": "画像生成成功",
            "student_id": student_id,
            "ai_response": full_response
        })

    except Exception as e:
        import traceback
        print(f"[ERROR] parse-resume failed: {str(e)}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({"error": f"服务器错误：{str(e)}"}), 500


# ==================== 学生画像 CRUD ====================

@students_bp.route('/api/students/<int:student_id>/profile', methods=['GET'])
def get_student_profile(student_id):
    """获取学生能力画像"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students WHERE id = %s AND user_id = %s", (student_id, user_id))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({"error": "学生不存在或无权限访问"}), 404

        professional_skills = []
        if student.get('professional_skills'):
            try:
                professional_skills = json.loads(student['professional_skills']) if isinstance(student['professional_skills'], str) else student['professional_skills']
            except:
                professional_skills = []

        certificates = []
        if student.get('certificates'):
            try:
                certificates = json.loads(student['certificates']) if isinstance(student['certificates'], str) else student['certificates']
            except:
                certificates = []

        project_experience = []
        if student.get('project_experience'):
            try:
                project_experience = json.loads(student['project_experience']) if isinstance(student['project_experience'], str) else student['project_experience']
            except:
                project_experience = []

        internship_experience = []
        if student.get('internship_experience_detail'):
            try:
                internship_experience = json.loads(student['internship_experience_detail']) if isinstance(student['internship_experience_detail'], str) else student['internship_experience_detail']
            except:
                if isinstance(student['internship_experience_detail'], str):
                    internship_experience = [{
                        "position": "实习经历",
                        "company": "",
                        "duration": "",
                        "description": student['internship_experience_detail']
                    }]
                else:
                    internship_experience = []

        profile = {
            "id": student['id'],
            "name": student.get('name', ''),
            "basic_info": {
                "school": student.get('school', ''),
                "major": student.get('major', ''),
                "education": student.get('education', ''),
                "graduation_year": student.get('graduation_year'),
                "email": student.get('email', ''),
                "phone": student.get('phone', '')
            },
            "ability_profile": {
                "professional_skills": professional_skills,
                "certificates": certificates,
                "professional_skills_certificates": student.get('professional_skills_certificates', 0),
                "innovation_ability": student.get('innovation_ability', 0),
                "learning_ability": student.get('learning_ability', 0),
                "stress_resistance": student.get('stress_resistance', 0),
                "communication_ability": student.get('communication_ability', 0),
                "internship_experience": student.get('internship_experience', 0)
            },
            "experience": {
                "internship_experience": internship_experience,
                "project_experience": project_experience
            },
            "career_planning": {
                "internship_experience_detail": student.get('internship_experience_detail', ''),
                "person_post_matching_analysis": student.get('person_post_matching_analysis', ''),
                "core_career_goal": student.get('core_career_goal', ''),
                "industry_demand_and_trend_analysis": student.get('industry_demand_and_trend_analysis', ''),
                "clear_career_development_path": student.get('clear_career_development_path', ''),
                "staged_growth_plan": student.get('staged_growth_plan', ''),
                "dynamic_evaluation_mechanism": student.get('dynamic_evaluation_mechanism', '')
            },
            "scores": {
                "profile_completeness": student.get('profile_completeness', 0),
                "competitiveness_score": student.get('competitiveness_score', 0)
            },
            "resume_text": student.get('resume_text', ''),
            "created_at": student.get('created_at'),
            "updated_at": student.get('updated_at')
        }

        cursor.close()
        conn.close()

        return jsonify(profile)
    except Exception as e:
        return jsonify({"error": f"获取画像失败：{str(e)}"}), 500


@students_bp.route('/api/students/list', methods=['GET'])
def get_students_list():
    """获取当前用户的学生列表"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, name, school, major, education, competitiveness_score, created_at FROM students WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        students = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": students})
    except Exception as e:
        return jsonify({"error": f"获取学生列表失败：{str(e)}"}), 500


@students_bp.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """删除学生画像"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM students WHERE id = %s AND user_id = %s", (student_id, user_id))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"error": "无权限删除此学生画像"}), 403

        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        cursor.execute("DELETE FROM student_job_matches WHERE student_id = %s", (student_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "删除成功"})
    except Exception as e:
        return jsonify({"error": f"删除学生失败：{str(e)}"}), 500


@students_bp.route('/api/students/current', methods=['GET'])
def get_current_student():
    """获取当前用户的最新学生画像"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM students WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        )
        student = cursor.fetchone()

        cursor.close()
        conn.close()

        if student:
            return jsonify({"success": True, "student_id": student['id']})
        else:
            return jsonify({"success": False, "message": "暂无学生画像"})
    except Exception as e:
        return jsonify({"error": f"获取学生信息失败：{str(e)}"}), 500


@students_bp.route('/api/students/<int:student_id>/improvement-suggestions', methods=['GET'])
def get_improvement_suggestions(student_id):
    """获取学生改进建议"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students WHERE id = %s AND user_id = %s", (student_id, user_id))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({"error": "学生不存在或无权限访问"}), 404

        suggestions = []

        if student.get('professional_skills_certificates', 0) < 7:
            suggestions.append({
                "dimension": "专业技能",
                "current_score": student.get('professional_skills_certificates', 0),
                "suggestion": "建议考取相关专业证书，如计算机二级、英语四六级等，提升专业技能认证"
            })

        if student.get('innovation_ability', 0) < 7:
            suggestions.append({
                "dimension": "创新能力",
                "current_score": student.get('innovation_ability', 0),
                "suggestion": "建议参加创新创业比赛、科研项目，培养创新思维和实践能力"
            })

        if student.get('learning_ability', 0) < 7:
            suggestions.append({
                "dimension": "学习能力",
                "current_score": student.get('learning_ability', 0),
                "suggestion": "建议制定学习计划，培养自主学习能力，多阅读专业书籍和论文"
            })

        if student.get('stress_resistance', 0) < 7:
            suggestions.append({
                "dimension": "抗压能力",
                "current_score": student.get('stress_resistance', 0),
                "suggestion": "建议参加社团活动或兼职工作，锻炼应对压力的能力"
            })

        if student.get('communication_ability', 0) < 7:
            suggestions.append({
                "dimension": "沟通能力",
                "current_score": student.get('communication_ability', 0),
                "suggestion": "建议参加演讲比赛、辩论赛等活动，提升口头表达能力"
            })

        if student.get('internship_experience', 0) < 7:
            suggestions.append({
                "dimension": "实习经验",
                "current_score": student.get('internship_experience', 0),
                "suggestion": "建议积极寻找实习机会，积累实际工作经验"
            })

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": suggestions
        })
    except Exception as e:
        return jsonify({"error": f"获取建议失败：{str(e)}"}), 500


@students_bp.route('/api/students/<int:student_id>/matches', methods=['GET'])
def get_student_job_matches(student_id):
    """获取学生岗位匹配数据"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students WHERE id = %s AND user_id = %s", (student_id, user_id))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({"error": "学生不存在或无权限访问"}), 404

        cursor.execute("""
            SELECT
                sjm.job_id,
                sjm.match_rank,
                sjm.basic_requirements_matching,
                sjm.professional_skills_matching,
                sjm.professional_literacy_matching,
                sjm.development_potential_matching,
                sjm.overall_matching,
                j.job_name,
                j.company_name,
                j.salary_range,
                j.work_address
            FROM student_job_matches sjm
            JOIN jobs j ON sjm.job_id = j.id
            WHERE sjm.student_id = %s
            ORDER BY sjm.match_rank ASC
            LIMIT 10
        """, (student_id,))
        matches = cursor.fetchall()

        cursor.close()
        conn.close()

        result = []
        for match in matches:
            result.append({
                "job_id": match['job_id'],
                "match_rank": match['match_rank'],
                "basic_requirements_matching": match['basic_requirements_matching'],
                "professional_skills_matching": match['professional_skills_matching'],
                "professional_literacy_matching": match['professional_literacy_matching'],
                "development_potential_matching": match['development_potential_matching'],
                "overall_matching": match['overall_matching'],
                "job_name": match['job_name'],
                "company_name": match['company_name'],
                "salary_range": match['salary_range'],
                "work_address": match['work_address']
            })

        return jsonify({
            "success": True,
            "data": result,
            "student_name": student.get('name', '')
        })
    except Exception as e:
        return jsonify({"error": f"获取岗位匹配数据失败：{str(e)}"}), 500
