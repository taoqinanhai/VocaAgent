"""
简历路由：/api/resumes/*
"""
import json
import os
import time
from http import HTTPStatus
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from dashscope import Application
from config.settings import API_KEY, APP_ID_A, KNOWLEDGE_BASE_IDS, UPLOAD_FOLDER
from utils.db import get_db_connection
from utils.auth import get_current_user
from utils.file_processor import allowed_file, extract_file_content

resumes_bp = Blueprint('resumes', __name__)


@resumes_bp.route('/api/resumes/upload', methods=['POST'])
def upload_resume():
    """上传简历文件并关联当前用户"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        if 'file' not in request.files:
            return jsonify({"error": "请选择要上传的简历文件"}), 400

        file = request.files['file']
        resume_name = request.form.get('resume_name', '').strip()

        if file.filename == '':
            return jsonify({"error": "请选择要上传的简历文件"}), 400

        if file and allowed_file(file.filename):
            original_filename = secure_filename(file.filename)
            file_ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)

            timestamp = int(time.time())
            storage_filename = f"user_{user_id}_{timestamp}_{original_filename}"
            file_path = os.path.join(UPLOAD_FOLDER, storage_filename)

            file.save(file_path)

            resume_text = extract_file_content(file_path)

            if not resume_name:
                resume_name = original_filename.rsplit('.', 1)[0]

            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM resumes WHERE user_id = %s AND is_default = TRUE", (user_id,))
            result = cursor.fetchone()
            is_default = result['count'] == 0

            insert_sql = """
            INSERT INTO resumes (user_id, resume_name, original_filename, file_path, file_type, file_size, resume_text, is_default)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (user_id, resume_name, original_filename, file_path, file_ext, file_size, resume_text, is_default))
            conn.commit()

            resume_id = cursor.lastrowid

            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "message": "简历上传成功",
                "data": {
                    "id": resume_id,
                    "resume_name": resume_name,
                    "original_filename": original_filename,
                    "file_type": file_ext,
                    "file_size": file_size,
                    "is_default": is_default,
                    "resume_text_preview": resume_text[:200] + "..." if len(resume_text) > 200 else resume_text
                }
            }), 201
        else:
            return jsonify({"error": "不支持的文件格式，请上传 PDF、Word 或图片文件"}), 400

    except Exception as e:
        return jsonify({"error": f"上传简历失败：{str(e)}"}), 500


@resumes_bp.route('/api/resumes', methods=['GET'])
def get_user_resumes():
    """获取当前用户的简历列表"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT id, resume_name, original_filename, file_type, file_size, is_default, status, created_at, updated_at
        FROM resumes
        WHERE user_id = %s AND status = 'active'
        ORDER BY is_default DESC, created_at DESC
        """
        cursor.execute(query, (user_id,))
        resumes = cursor.fetchall()

        for resume in resumes:
            cursor.execute("SELECT COUNT(*) as analysis_count FROM resume_analyses WHERE resume_id = %s", (resume['id'],))
            count_result = cursor.fetchone()
            resume['analysis_count'] = count_result['analysis_count']

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": resumes
        })

    except Exception as e:
        return jsonify({"error": f"获取简历列表失败：{str(e)}"}), 500


@resumes_bp.route('/api/resumes/<int:resume_id>', methods=['GET'])
def get_resume_detail(resume_id):
    """获取简历详情"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT id, user_id, resume_name, original_filename, file_path, file_type, file_size,
               resume_text, is_default, status, created_at, updated_at
        FROM resumes
        WHERE id = %s AND user_id = %s AND status = 'active'
        """
        cursor.execute(query, (resume_id, user_id))
        resume = cursor.fetchone()

        if not resume:
            return jsonify({"error": "简历不存在或无权限访问"}), 404

        cursor.execute("""
            SELECT id, analysis_type, analysis_content, competitiveness_score, created_at
            FROM resume_analyses
            WHERE resume_id = %s
            ORDER BY created_at DESC
        """, (resume_id,))
        analyses = cursor.fetchall()

        resume['analyses'] = analyses

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": resume
        })

    except Exception as e:
        return jsonify({"error": f"获取简历详情失败：{str(e)}"}), 500


@resumes_bp.route('/api/resumes/<int:resume_id>/analyze', methods=['POST'])
def analyze_resume(resume_id):
    """分析简历并保存结果"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']
        data = request.get_json() or {}
        analysis_type = data.get('analysis_type', 'full')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, resume_name, resume_text FROM resumes
            WHERE id = %s AND user_id = %s AND status = 'active'
        """, (resume_id, user_id))
        resume = cursor.fetchone()

        if not resume:
            return jsonify({"error": "简历不存在或无权限访问"}), 404

        resume_text = resume['resume_text'] or ""

        if analysis_type == 'full':
            prompt = f"""请对以下简历进行全面分析，并以JSON格式返回分析结果：

简历内容：
{resume_text}

请分析并返回以下信息（JSON格式）：
{{
    "personal_info": {{"name": "姓名", "education": "学历", "major": "专业", "school": "学校"}},
    "skills": ["技能1", "技能2", ...],
    "ability_scores": {{"innovation": 分数(0-100), "learning": 分数, "stress_resistance": 分数, "communication": 分数, "professional": 分数}},
    "competitiveness_score": 综合竞争力分数(0-100),
    "strengths": ["优势1", "优势2", ...],
    "weaknesses": ["待提升点1", "待提升点2", ...],
    "career_suggestions": ["建议1", "建议2", ...],
    "suitable_positions": ["适合岗位1", "适合岗位2", ...]
}}"""
        elif analysis_type == 'skills':
            prompt = f"""请分析以下简历中的技能，并以JSON格式返回：

简历内容：
{resume_text}

返回格式：
{{
    "skills": [{{"name": "技能名", "level": "掌握程度", "category": "类别"}}],
    "skill_gaps": ["需要补充的技能1", "需要补充的技能2"],
    "certifications": ["证书1", "证书2"]
}}"""
        else:
            prompt = f"""请分析以下简历：\n\n{resume_text}"""

        messages = [{'role': 'user', 'content': prompt}]

        call_params = {
            'api_key': API_KEY,
            'app_id': APP_ID_A,
            'messages': messages,
            'stream': False
        }

        if KNOWLEDGE_BASE_IDS:
            call_params['rag_options'] = {'pipeline_ids': KNOWLEDGE_BASE_IDS}

        response = Application.call(**call_params)

        if response.status_code == HTTPStatus.OK:
            ai_response = response.output.text

            try:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}')
                if json_start != -1 and json_end != -1:
                    analysis_content = json.loads(ai_response[json_start:json_end+1])
                else:
                    analysis_content = {"raw_analysis": ai_response}

                ability_scores = analysis_content.get('ability_scores', {})
                competitiveness_score = analysis_content.get('competitiveness_score', 0)
                extracted_skills = analysis_content.get('skills', [])

            except:
                analysis_content = {"raw_analysis": ai_response}
                ability_scores = {}
                competitiveness_score = 0
                extracted_skills = []

            insert_sql = """
            INSERT INTO resume_analyses
            (user_id, resume_id, analysis_type, analysis_content, raw_response, ability_scores, extracted_skills, competitiveness_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (
                user_id, resume_id, analysis_type,
                json.dumps(analysis_content, ensure_ascii=False),
                ai_response,
                json.dumps(ability_scores, ensure_ascii=False),
                json.dumps(extracted_skills, ensure_ascii=False),
                competitiveness_score
            ))
            conn.commit()

            analysis_id = cursor.lastrowid

            cursor.close()
            conn.close()

            return jsonify({
                "success": True,
                "message": "简历分析完成",
                "data": {
                    "analysis_id": analysis_id,
                    "analysis_type": analysis_type,
                    "analysis_content": analysis_content,
                    "competitiveness_score": competitiveness_score,
                    "ability_scores": ability_scores
                }
            })
        else:
            return jsonify({"error": f"AI分析失败：{response.message}"}), 500

    except Exception as e:
        return jsonify({"error": f"分析简历失败：{str(e)}"}), 500


@resumes_bp.route('/api/resumes/analyses', methods=['GET'])
def get_resume_analyses():
    """获取当前用户的简历分析历史"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']
        analysis_type = request.args.get('type')

        conn = get_db_connection()
        cursor = conn.cursor()

        if analysis_type:
            query = """
            SELECT ra.id, ra.resume_id, r.resume_name, ra.analysis_type, ra.competitiveness_score, ra.created_at
            FROM resume_analyses ra
            LEFT JOIN resumes r ON ra.resume_id = r.id
            WHERE ra.user_id = %s AND ra.analysis_type = %s
            ORDER BY ra.created_at DESC
            """
            cursor.execute(query, (user_id, analysis_type))
        else:
            query = """
            SELECT ra.id, ra.resume_id, r.resume_name, ra.analysis_type, ra.competitiveness_score, ra.created_at
            FROM resume_analyses ra
            LEFT JOIN resumes r ON ra.resume_id = r.id
            WHERE ra.user_id = %s
            ORDER BY ra.created_at DESC
            """
            cursor.execute(query, (user_id,))

        analyses = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": analyses
        })

    except Exception as e:
        return jsonify({"error": f"获取分析历史失败：{str(e)}"}), 500


@resumes_bp.route('/api/resumes/analyses/<int:analysis_id>', methods=['GET'])
def get_analysis_detail(analysis_id):
    """获取分析详情"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
        SELECT ra.*, r.resume_name, r.original_filename
        FROM resume_analyses ra
        LEFT JOIN resumes r ON ra.resume_id = r.id
        WHERE ra.id = %s AND ra.user_id = %s
        """
        cursor.execute(query, (analysis_id, user_id))
        analysis = cursor.fetchone()

        if not analysis:
            return jsonify({"error": "分析记录不存在或无权限访问"}), 404

        analysis['analysis_content'] = json.loads(analysis['analysis_content']) if analysis['analysis_content'] else {}
        analysis['ability_scores'] = json.loads(analysis['ability_scores']) if analysis['ability_scores'] else {}
        analysis['extracted_skills'] = json.loads(analysis['extracted_skills']) if analysis['extracted_skills'] else []

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": analysis
        })

    except Exception as e:
        return jsonify({"error": f"获取分析详情失败：{str(e)}"}), 500


@resumes_bp.route('/api/resumes/<int:resume_id>', methods=['DELETE'])
def delete_resume(resume_id):
    """删除简历（软删除）"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, is_default FROM resumes WHERE id = %s AND user_id = %s AND status = 'active'", (resume_id, user_id))
        resume = cursor.fetchone()

        if not resume:
            return jsonify({"error": "简历不存在或无权限访问"}), 404

        cursor.execute("UPDATE resumes SET status = 'deleted' WHERE id = %s", (resume_id,))

        if resume['is_default']:
            cursor.execute("""
                UPDATE resumes SET is_default = TRUE
                WHERE user_id = %s AND status = 'active'
                ORDER BY created_at DESC LIMIT 1
            """, (user_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "简历已删除"
        })

    except Exception as e:
        return jsonify({"error": f"删除简历失败：{str(e)}"}), 500


@resumes_bp.route('/api/resumes/<int:resume_id>/default', methods=['PUT'])
def set_default_resume(resume_id):
    """设置默认简历"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM resumes WHERE id = %s AND user_id = %s AND status = 'active'", (resume_id, user_id))
        if not cursor.fetchone():
            return jsonify({"error": "简历不存在或无权限访问"}), 404

        cursor.execute("UPDATE resumes SET is_default = FALSE WHERE user_id = %s", (user_id,))
        cursor.execute("UPDATE resumes SET is_default = TRUE WHERE id = %s", (resume_id,))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "默认简历设置成功"
        })

    except Exception as e:
        return jsonify({"error": f"设置默认简历失败：{str(e)}"}), 500
