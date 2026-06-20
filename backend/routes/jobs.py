"""
岗位路由：/api/jobs/*
"""
import json
from flask import Blueprint, request, jsonify
from utils.db import get_db_connection

jobs_bp = Blueprint('jobs', __name__)


@jobs_bp.route('/api/jobs/list', methods=['GET'])
def get_jobs():
    """获取岗位列表"""
    try:
        skip = int(request.args.get('skip', 0))
        limit = int(request.args.get('limit', 1000))

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM jobs LIMIT %s OFFSET %s"
        cursor.execute(query, (limit, skip))
        jobs = cursor.fetchall()

        result = []
        for job in jobs:
            skills = []
            if job.get('job_description'):
                desc = job['job_description']
                skill_keywords = ['Python', 'Java', 'JavaScript', 'HTML', 'CSS', 'React', 'Vue', 'Flask', 'Django', 'MySQL', 'PostgreSQL', 'MongoDB', 'AWS', 'Docker', 'Git']
                for skill in skill_keywords:
                    if skill.lower() in desc.lower() and skill not in skills:
                        skills.append(skill)

            vertical_promotion_info = None
            if job.get('complete_promotion_path'):
                try:
                    vertical_promotion_info = json.loads(job['complete_promotion_path']) if isinstance(job['complete_promotion_path'], str) else job['complete_promotion_path']
                except:
                    vertical_promotion_info = []

            transfer_paths_info = None
            if job.get('transfer_paths'):
                try:
                    transfer_paths_info = json.loads(job['transfer_paths']) if isinstance(job['transfer_paths'], str) else job['transfer_paths']
                except:
                    transfer_paths_info = []

            result.append({
                'id': job['id'],
                'job_name': job['job_name'],
                'salary_range': job['salary_range'],
                'company_name': job['company_name'],
                'work_address': job['work_address'],
                'professional_skills': skills,
                'industry': job['industry'],
                'ability_requirement_scores': {
                    'professional_skills_certificates': job.get('professional_skills_certificates', 0),
                    'innovation_ability': job.get('innovation_ability', 0),
                    'learning_ability': job.get('learning_ability', 0),
                    'stress_resistance': job.get('stress_resistance', 0),
                    'communication_ability': job.get('communication_ability', 0),
                    'internship_experience': job.get('internship_experience', 0)
                },
                'vertical_promotion_info': vertical_promotion_info,
                'transfer_paths': transfer_paths_info
            })

        cursor.close()
        conn.close()

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取岗位列表失败：{str(e)}"}), 500


@jobs_bp.route('/api/jobs/industries', methods=['GET'])
def get_industries():
    """获取行业列表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT industry_name FROM industries ORDER BY industry_name"
        cursor.execute(query)
        industries = [row['industry_name'] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": industries})
    except Exception as e:
        return jsonify({"success": False, "error": f"获取行业列表失败：{str(e)}"}), 500


@jobs_bp.route('/api/jobs/search', methods=['GET'])
def search_jobs():
    """搜索岗位"""
    try:
        query = request.args.get('query', '')

        conn = get_db_connection()
        cursor = conn.cursor()

        search_query = f"%{query}%"
        sql = """
        SELECT * FROM jobs
        WHERE job_name LIKE %s OR company_name LIKE %s OR job_description LIKE %s
        LIMIT 1000
        """
        cursor.execute(sql, (search_query, search_query, search_query))
        jobs = cursor.fetchall()

        result = []
        for job in jobs:
            skills = []
            if job.get('job_description'):
                desc = job['job_description']
                skill_keywords = ['Python', 'Java', 'JavaScript', 'HTML', 'CSS', 'React', 'Vue', 'Flask', 'Django', 'MySQL', 'PostgreSQL', 'MongoDB', 'AWS', 'Docker', 'Git']
                for skill in skill_keywords:
                    if skill.lower() in desc.lower() and skill not in skills:
                        skills.append(skill)

            vertical_promotion_info = None
            if job.get('promotion_path'):
                try:
                    vertical_promotion_info = json.loads(job['promotion_path']) if isinstance(job['promotion_path'], str) else job['promotion_path']
                except:
                    vertical_promotion_info = []

            transfer_paths_info = None
            if job.get('transfer_path'):
                try:
                    transfer_paths_info = json.loads(job['transfer_path']) if isinstance(job['transfer_path'], str) else job['transfer_path']
                except:
                    transfer_paths_info = []

            result.append({
                'id': job['id'],
                'job_name': job['job_name'],
                'salary_range': job['salary_range'],
                'company_name': job['company_name'],
                'work_address': job['work_address'],
                'professional_skills': skills,
                'industry': job['industry'],
                'ability_requirement_scores': {
                    'professional_skills_certificates': job.get('professional_skills_certificates', 0),
                    'innovation_ability': job.get('innovation_ability', 0),
                    'learning_ability': job.get('learning_ability', 0),
                    'stress_resistance': job.get('stress_resistance', 0),
                    'communication_ability': job.get('communication_ability', 0),
                    'internship_experience': job.get('internship_experience', 0)
                },
                'vertical_promotion_info': vertical_promotion_info,
                'transfer_paths': transfer_paths_info
            })

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": result})
    except Exception as e:
        return jsonify({"success": False, "error": f"搜索岗位失败：{str(e)}"}), 500


@jobs_bp.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job_detail(job_id):
    """获取岗位详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM jobs WHERE id = %s"
        cursor.execute(query, (job_id,))
        job = cursor.fetchone()

        if not job:
            return jsonify({"error": "岗位不存在"}), 404

        skills = []
        if job.get('job_description'):
            desc = job['job_description']
            skill_keywords = ['Python', 'Java', 'JavaScript', 'HTML', 'CSS', 'React', 'Vue', 'Flask', 'Django', 'MySQL', 'PostgreSQL', 'MongoDB', 'AWS', 'Docker', 'Git']
            for skill in skill_keywords:
                if skill.lower() in desc.lower() and skill not in skills:
                    skills.append(skill)

        vertical_promotion_info = None
        if job.get('promotion_path'):
            try:
                vertical_promotion_info = json.loads(job['promotion_path']) if isinstance(job['promotion_path'], str) else job['promotion_path']
            except:
                vertical_promotion_info = []

        transfer_paths_info = None
        if job.get('transfer_path'):
            try:
                transfer_paths_info = json.loads(job['transfer_path']) if isinstance(job['transfer_path'], str) else job['transfer_path']
            except:
                transfer_paths_info = []

        result = {
            'id': job['id'],
            'job_name': job['job_name'],
            'salary_range': job['salary_range'],
            'company_name': job['company_name'],
            'work_address': job['work_address'],
            'industry': job['industry'],
            'company_size': job['company_size'],
            'company_type': job['company_type'],
            'job_description': job['job_description'],
            'update_date': job['update_date'],
            'company_description': job['company_description'],
            'job_source_url': job['job_source_url'],
            'job_code': job.get('job_code', ''),
            'company_industry': job['industry'],
            'company_nature': job['company_type'],
            'profile': {
                'professional_skills': skills,
                'certificate_requirements': [],
                'innovation_ability': job.get('innovation_ability', 0),
                'learning_ability': job.get('learning_ability', 0),
                'stress_resistance': job.get('stress_resistance', 0),
                'communication_ability': job.get('communication_ability', 0),
                'internship_ability': job.get('internship_experience', 0)
            },
            'ability_requirement_scores': {
                'professional_skills_certificates': job.get('professional_skills_certificates', 0),
                'innovation_ability': job.get('innovation_ability', 0),
                'learning_ability': job.get('learning_ability', 0),
                'stress_resistance': job.get('stress_resistance', 0),
                'communication_ability': job.get('communication_ability', 0),
                'internship_experience': job.get('internship_experience', 0)
            },
            'vertical_promotion_info': vertical_promotion_info,
            'transfer_paths': transfer_paths_info
        }

        cursor.close()
        conn.close()

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取岗位详情失败：{str(e)}"}), 500


@jobs_bp.route('/api/students/<int:student_id>/matches/<int:match_rank>/job', methods=['GET'])
def get_match_job_detail(student_id, match_rank):
    """根据学生ID和匹配排名获取岗位详情"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        match_query = """
        SELECT job_id FROM student_job_matches
        WHERE student_id = %s AND match_rank = %s
        """
        cursor.execute(match_query, (student_id, match_rank))
        match_result = cursor.fetchone()

        if not match_result:
            return jsonify({"error": "匹配记录不存在"}), 404

        job_id = match_result['job_id']

        job_query = "SELECT * FROM jobs WHERE id = %s"
        cursor.execute(job_query, (job_id,))
        job = cursor.fetchone()

        if not job:
            return jsonify({"error": "岗位不存在"}), 404

        skills = []
        if job.get('job_description'):
            desc = job['job_description']
            skill_keywords = ['Python', 'Java', 'JavaScript', 'HTML', 'CSS', 'React', 'Vue', 'Flask', 'Django', 'MySQL', 'PostgreSQL', 'MongoDB', 'AWS', 'Docker', 'Git']
            for skill in skill_keywords:
                if skill.lower() in desc.lower() and skill not in skills:
                    skills.append(skill)

        # 尝试从 job_ai_profiles 获取 AI 生成的岗位画像数据
        ai_profile = None
        try:
            cursor.execute("""
                SELECT ability_requirement_scores, vertical_promotion_info, job_transfer_paths
                FROM job_ai_profiles
                WHERE job_id = %s AND student_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, (job_id, student_id))
            ai_row = cursor.fetchone()
            if ai_row:
                ai_profile = {
                    'ability_requirement_scores': json.loads(ai_row['ability_requirement_scores']) if isinstance(ai_row['ability_requirement_scores'], str) else ai_row['ability_requirement_scores'],
                    'vertical_promotion_info': json.loads(ai_row['vertical_promotion_info']) if isinstance(ai_row['vertical_promotion_info'], str) else ai_row['vertical_promotion_info'],
                    'job_transfer_paths': json.loads(ai_row['job_transfer_paths']) if isinstance(ai_row['job_transfer_paths'], str) else ai_row['job_transfer_paths'],
                }
        except:
            pass  # AI profile fetch is best-effort

        vertical_promotion_info = None
        if ai_profile and ai_profile.get('vertical_promotion_info'):
            vertical_promotion_info = ai_profile['vertical_promotion_info']
        elif job.get('promotion_path'):
            try:
                vertical_promotion_info = json.loads(job['promotion_path']) if isinstance(job['promotion_path'], str) else job['promotion_path']
            except:
                vertical_promotion_info = []

        transfer_paths_info = None
        if ai_profile and ai_profile.get('job_transfer_paths'):
            transfer_paths_info = ai_profile['job_transfer_paths']
        elif job.get('transfer_path'):
            try:
                transfer_paths_info = json.loads(job['transfer_path']) if isinstance(job['transfer_path'], str) else job['transfer_path']
            except:
                transfer_paths_info = []

        aas = ai_profile.get('ability_requirement_scores', {}) if ai_profile else {}
        result = {
            'id': job['id'],
            'job_name': job['job_name'],
            'salary_range': job['salary_range'],
            'company_name': job['company_name'],
            'work_address': job['work_address'],
            'industry': job['industry'],
            'company_size': job['company_size'],
            'company_type': job['company_type'],
            'job_description': job['job_description'],
            'update_date': job['update_date'],
            'company_description': job['company_description'],
            'job_source_url': job['job_source_url'],
            'job_code': job.get('job_code', ''),
            'company_industry': job['industry'],
            'company_nature': job['company_type'],
            'profile': {
                'professional_skills': skills,
                'certificate_requirements': [],
                'innovation_ability': aas.get('innovation_ability') or job.get('innovation_ability', 0),
                'learning_ability': aas.get('learning_ability') or job.get('learning_ability', 0),
                'stress_resistance': aas.get('stress_resistance') or job.get('stress_resistance', 0),
                'communication_ability': aas.get('communication_ability') or job.get('communication_ability', 0),
                'internship_ability': aas.get('internship_experience') or job.get('internship_experience', 0)
            },
            'ability_requirement_scores': {
                'professional_skills_certificates': aas.get('professional_skills_certificates') or job.get('professional_skills_certificates', 0),
                'innovation_ability': aas.get('innovation_ability') or job.get('innovation_ability', 0),
                'learning_ability': aas.get('learning_ability') or job.get('learning_ability', 0),
                'stress_resistance': aas.get('stress_resistance') or job.get('stress_resistance', 0),
                'communication_ability': aas.get('communication_ability') or job.get('communication_ability', 0),
                'internship_experience': aas.get('internship_experience') or job.get('internship_experience', 0)
            },
            'vertical_promotion_info': vertical_promotion_info,
            'transfer_paths': transfer_paths_info,
            'has_ai_profile': ai_profile is not None
        }

        cursor.close()
        conn.close()

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"获取岗位详情失败：{str(e)}"}), 500
