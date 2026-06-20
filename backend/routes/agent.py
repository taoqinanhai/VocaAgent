"""
Agent 路由：/api/agent/profile、/api/agent/match、/api/agent/report
实现 SSE 流式响应，支持前端渐进式渲染
并在完成时持久化数据到 MySQL
"""
import json
import os
import time
import datetime
from flask import Blueprint, request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename
from services.agent_orchestrator import orchestrator
from services.resume_parser import parse_and_save_resume_data, parse_profile_json, save_student_profile
from config.settings import UPLOAD_FOLDER
from utils.file_processor import allowed_file, extract_file_content
from utils.db import get_db_connection
from utils.auth import get_current_user

agent_bp = Blueprint('agent', __name__)


# ============================================================
# Agent A：简历解析 → 学生能力画像
# ============================================================

@agent_bp.route('/api/agent/profile', methods=['POST'])
def agent_profile():
    """
    输入：简历文件（multipart）或 纯文本（JSON）
    输出：SSE 流 → 学生能力画像 JSON

    请求格式 1（文件上传）:
      multipart/form-data: file=简历.pdf

    请求格式 2（纯文本）:
      application/json: {"resume_text": "简历内容...", "user_id": 1}
    """
    try:
        content_type = request.content_type or ''
        resume_text = ""

        # 获取当前登录用户（用于 DB 持久化）
        current_user = get_current_user()
        user_id = current_user['id'] if current_user else 1

        if content_type.startswith('multipart/form-data'):
            file = request.files.get('file')
            if not file or file.filename == '':
                return jsonify({"error": "请上传简历文件"}), 400
            if not allowed_file(file.filename):
                return jsonify({"error": "不支持的文件格式，支持 PDF/Word/TXT"}), 400

            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, f"profile_{int(time.time())}_{filename}")
            file.save(filepath)
            resume_text = extract_file_content(filepath)

            if not resume_text:
                return jsonify({"error": "无法从文件中提取文本内容"}), 400

        elif content_type.startswith('application/json'):
            data = request.get_json()
            if not data:
                return jsonify({"error": "请求数据不能为空"}), 400
            resume_text = data.get('resume_text', '')
            if not resume_text:
                return jsonify({"error": "简历文本不能为空"}), 400
        else:
            return jsonify({"error": "不支持的请求格式"}), 415

        def generate():
            full_response = ""
            for event in orchestrator.run_agent_a(resume_text):
                if event["type"] == "chunk":
                    full_response += event["content"]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': event['content']}, ensure_ascii=False)}\n\n"
                elif event["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event['message']}, ensure_ascii=False)}\n\n"
                    return

            # ---- 持久化：写入 students 表 ----
            student_id = None
            db_warning = None
            try:
                student_id, error = parse_and_save_resume_data(full_response, user_id)
                if error:
                    db_warning = f"画像已生成但保存失败：{error}"
                    print(f"[Agent A] DB保存失败: {error}")
                else:
                    print(f"[Agent A] 画像已保存, student_id={student_id}")
            except Exception as e:
                db_warning = f"画像已生成但保存失败：{str(e)}"
                print(f"[Agent A] DB保存异常: {e}")

            done_event = {'type': 'done', 'result': full_response}
            if student_id:
                done_event['student_id'] = student_id
            if db_warning:
                done_event['warning'] = db_warning

            yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        return jsonify({"error": f"服务器内部错误：{str(e)}"}), 500


# ============================================================
# Agent B：岗位匹配 → 10 岗位评分
# ============================================================

@agent_bp.route('/api/agent/match', methods=['POST'])
def agent_match():
    """
    输入：学生画像 JSON
    输出：SSE 流 → job_post_profiles JSON（渐进渲染岗位卡片）

    请求格式:
      application/json: {
        "student_profile": { ... Agent A 的输出 ... },
        "job_ids": [1, 2, 3],  // 可选，指定要匹配的岗位ID，不传则匹配全部
        "student_id": 42,       // 可选，关联的学生ID（用于DB持久化）
        "user_id": 1            // 可选
      }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        student_profile = data.get('student_profile')
        if not student_profile:
            return jsonify({"error": "学生画像数据不能为空"}), 400

        req_student_id = data.get('student_id')      # 前端传入的学生DB ID
        current_user = get_current_user()
        req_user_id = current_user['id'] if current_user else 1

        # 从 MySQL 获取岗位描述
        conn = get_db_connection()
        cursor = conn.cursor()

        job_ids = data.get('job_ids')
        if job_ids and isinstance(job_ids, list):
            placeholders = ','.join(['%s'] * len(job_ids))
            query = f"SELECT id, job_name, industry, job_description FROM jobs WHERE id IN ({placeholders})"
            cursor.execute(query, job_ids)
        else:
            query = "SELECT id, job_name, industry, job_description FROM jobs LIMIT 10"
            cursor.execute(query)

        jobs = cursor.fetchall()
        cursor.close()
        conn.close()

        if not jobs:
            return jsonify({"error": "数据库中没有岗位数据，请先导入岗位"}), 500

        job_descriptions = [
            {
                'id': job['id'],
                'job_name': job['job_name'],
                'industry': job.get('industry', '未知'),
                'job_description': job.get('job_description', '')
            }
            for job in jobs
        ]

        student_profile_str = json.dumps(student_profile, ensure_ascii=False, indent=2)

        def generate():
            full_response = ""
            for event in orchestrator.run_agent_b(student_profile_str, job_descriptions):
                if event["type"] == "chunk":
                    full_response += event["content"]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': event['content']}, ensure_ascii=False)}\n\n"
                elif event["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event['message']}, ensure_ascii=False)}\n\n"
                    return

            # ---- 持久化：写入 student_job_matches 表 ----
            match_count = 0
            db_warning = None
            try:
                # 优先使用请求中传入的 student_id；否则尝试从 student_profile 查 name
                student_id = req_student_id
                if not student_id:
                    # 如果没传 student_id，尝试从 profile 中提取 name 去数据库查找
                    profile_name = student_profile.get('resume_detail_info', {}).get('name', '')
                    if profile_name:
                        conn2 = get_db_connection()
                        cur2 = conn2.cursor()
                        cur2.execute(
                            "SELECT id FROM students WHERE name = %s AND user_id = %s ORDER BY created_at DESC LIMIT 1",
                            (profile_name, req_user_id)
                        )
                        row = cur2.fetchone()
                        cur2.close()
                        conn2.close()
                        if row:
                            student_id = row['id']

                if student_id:
                    # 解析 Agent B 的输出
                    parsed = _extract_json(full_response)
                    job_profiles = parsed.get('job_post_profiles', []) if parsed else []

                    if job_profiles:
                        conn3 = get_db_connection()
                        cur3 = conn3.cursor()

                        # 先删除旧匹配记录
                        cur3.execute(
                            "DELETE FROM student_job_matches WHERE student_id = %s",
                            (student_id,)
                        )

                        for rank, job in enumerate(job_profiles, start=1):
                            matching = job.get('user_matching_scores', {})
                            cur3.execute("""
                                INSERT INTO student_job_matches
                                (job_id, student_id, match_rank,
                                 basic_requirements_matching, professional_skills_matching,
                                 professional_literacy_matching, development_potential_matching,
                                 overall_matching, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (
                                job.get('id'),
                                student_id,
                                rank,
                                matching.get('basic_requirements_matching', 0),
                                matching.get('professional_skills_matching', 0),
                                matching.get('professional_literacy_matching', 0),
                                matching.get('development_potential_matching', 0),
                                matching.get('overall_matching', 0),
                                datetime.datetime.now(),
                                datetime.datetime.now()
                            ))
                            match_count += 1

                        conn3.commit()
                        cur3.close()
                        conn3.close()
                        print(f"[Agent B] 匹配结果已保存, student_id={student_id}, count={match_count}")
                    else:
                        db_warning = "Agent B 返回数据无 job_post_profiles，无法保存匹配结果"
                else:
                    db_warning = "未传入 student_id 且无法从画像推断，匹配结果未保存到数据库"
            except Exception as e:
                import traceback
                traceback.print_exc()
                db_warning = f"匹配结果保存失败：{str(e)}"

            done_event = {'type': 'done'}
            if match_count > 0:
                done_event['saved_matches'] = match_count
            if db_warning:
                done_event['warning'] = db_warning

            yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        return jsonify({"error": f"服务器内部错误：{str(e)}"}), 500


# ============================================================
# Agent C：单岗位画像分析（按需触发）
# ============================================================

@agent_bp.route('/api/agent/job-profile', methods=['POST'])
def agent_job_profile():
    """
    Agent C：单岗位画像分析 (SSE 流式)

    请求格式:
      application/json: {
        "job_id": 1,
        "job_name": "...",
        "job_description": "...",
        "industry": "...",
        "student_profile": { ... Agent A 的输出 ... },
        "student_id": 42
      }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        job_id = data.get('job_id')
        job_name = data.get('job_name', '')
        job_description = data.get('job_description', '')
        industry = data.get('industry', '')
        student_profile = data.get('student_profile')
        req_student_id = data.get('student_id')

        if not student_profile:
            return jsonify({"error": "学生画像数据不能为空"}), 400
        if not job_id:
            return jsonify({"error": "岗位ID不能为空"}), 400

        job_info = {
            'id': job_id,
            'job_name': job_name,
            'job_description': job_description,
            'industry': industry
        }
        student_profile_str = json.dumps(student_profile, ensure_ascii=False, indent=2)

        def generate():
            full_response = ""
            for event in orchestrator.run_agent_c(job_info, student_profile_str):
                if event["type"] == "chunk":
                    full_response += event["content"]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': event['content']}, ensure_ascii=False)}\n\n"
                elif event["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event['message']}, ensure_ascii=False)}\n\n"
                    return

            # ---- 持久化：写入 job_ai_profiles 表 ----
            profile_id = None
            db_warning = None
            try:
                if req_student_id and job_id:
                    parsed = _extract_json(full_response)
                    if parsed:
                        conn = get_db_connection()
                        cur = conn.cursor()

                        # UPSERT: 每个 student×job 只保留最新一条
                        cur.execute("""
                            INSERT INTO job_ai_profiles
                            (job_id, student_id, ability_requirement_scores,
                             vertical_promotion_info, job_transfer_paths, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON DUPLICATE KEY UPDATE
                                ability_requirement_scores = VALUES(ability_requirement_scores),
                                vertical_promotion_info = VALUES(vertical_promotion_info),
                                job_transfer_paths = VALUES(job_transfer_paths),
                                created_at = VALUES(created_at)
                        """, (
                            job_id,
                            req_student_id,
                            json.dumps(parsed.get('ability_requirement_scores'), ensure_ascii=False),
                            json.dumps(parsed.get('vertical_promotion_info'), ensure_ascii=False),
                            json.dumps(parsed.get('job_transfer_paths'), ensure_ascii=False),
                            datetime.datetime.now()
                        ))
                        conn.commit()
                        profile_id = cur.lastrowid
                        cur.close()
                        conn.close()
                        print(f"[Agent C] 岗位画像已保存, student_id={req_student_id}, job_id={job_id}")
                    else:
                        db_warning = "Agent C 返回数据无法解析为 JSON"
                else:
                    db_warning = "缺少 student_id 或 job_id，画像未保存到数据库"
            except Exception as e:
                import traceback
                traceback.print_exc()
                db_warning = f"岗位画像保存失败：{str(e)}"

            done_event = {'type': 'done'}
            if profile_id:
                done_event['profile_id'] = profile_id
            if db_warning:
                done_event['warning'] = db_warning

            yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        return jsonify({"error": f"服务器内部错误：{str(e)}"}), 500


@agent_bp.route('/api/agent/job-profile/<int:student_id>/<int:job_id>', methods=['GET'])
def check_job_profile_exists(student_id, job_id):
    """
    检查某个 student×job 的 AI 画像是否已生成
    有 → 返回 JSON 数据；没有 → 返回 exists=false
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, ability_requirement_scores, vertical_promotion_info,
                   job_transfer_paths, created_at
            FROM job_ai_profiles
            WHERE job_id = %s AND student_id = %s
            ORDER BY created_at DESC LIMIT 1
        """, (job_id, student_id))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            return jsonify({
                "exists": True,
                "profile_id": row['id'],
                "ability_requirement_scores": json.loads(row['ability_requirement_scores']) if isinstance(row['ability_requirement_scores'], str) else row['ability_requirement_scores'],
                "vertical_promotion_info": json.loads(row['vertical_promotion_info']) if isinstance(row['vertical_promotion_info'], str) else row['vertical_promotion_info'],
                "job_transfer_paths": json.loads(row['job_transfer_paths']) if isinstance(row['job_transfer_paths'], str) else row['job_transfer_paths'],
                "created_at": row['created_at'].strftime('%Y-%m-%d %H:%M') if row['created_at'] else '',
            })
        else:
            return jsonify({"exists": False})
    except Exception as e:
        return jsonify({"error": f"查询失败：{str(e)}"}), 500


# ============================================================
# Agent D：报告生成 → 职业规划报告 HTML
# ============================================================

@agent_bp.route('/api/agent/report', methods=['POST'])
def agent_report():
    """
    输入：学生画像 + Top 3 匹配结果
    输出：SSE 流 → HTML 报告

    请求格式:
      application/json: {
        "student_profile": { ... Agent A 的输出 ... },
        "top3_matches": [ ... Agent B 输出的前 3 个匹配 ... ],
        "student_id": 42,       // 可选，关联的学生ID（用于DB持久化）
        "target_job_id": 5,     // 可选，目标岗位ID（默认取 top3 第一个的 job_id）
        "report_title": "...",  // 可选，报告标题
        "user_id": 1            // 可选
      }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        student_profile = data.get('student_profile')
        top3_matches = data.get('top3_matches')

        if not student_profile:
            return jsonify({"error": "学生画像数据不能为空"}), 400
        if not top3_matches:
            return jsonify({"error": "匹配结果不能为空"}), 400

        req_student_id = data.get('student_id')
        current_user = get_current_user()
        req_user_id = current_user['id'] if current_user else 1
        req_target_job_id = data.get('target_job_id')
        req_report_title = data.get('report_title', '职业发展规划报告')

        # 如果没有传 target_job_id，尝试从 top3 第一个取
        if not req_target_job_id and isinstance(top3_matches, list) and len(top3_matches) > 0:
            req_target_job_id = top3_matches[0].get('job_id') or top3_matches[0].get('id')

        # ★ 自动生成报告标题：{岗位名} - {秒级时间戳}
        if not data.get('report_title') and req_target_job_id:
            try:
                conn_title = get_db_connection()
                cur_title = conn_title.cursor()
                cur_title.execute("SELECT job_name FROM jobs WHERE id = %s", (req_target_job_id,))
                job_row = cur_title.fetchone()
                cur_title.close()
                conn_title.close()
                if job_row and job_row['job_name']:
                    req_report_title = f"{job_row['job_name']} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            except Exception:
                pass  # 兜底：保持默认标题

        student_profile_str = json.dumps(student_profile, ensure_ascii=False, indent=2)
        top3_matches_str = json.dumps(top3_matches, ensure_ascii=False, indent=2)

        def generate():
            # ---- 0. 提前解析 student_id（Agent C 需要用到）----
            student_id = req_student_id
            if not student_id:
                profile_name = student_profile.get('resume_detail_info', {}).get('name', '')
                if profile_name:
                    try:
                        conn_pre = get_db_connection()
                        cur_pre = conn_pre.cursor()
                        cur_pre.execute(
                            "SELECT id FROM students WHERE name = %s AND user_id = %s ORDER BY created_at DESC LIMIT 1",
                            (profile_name, req_user_id)
                        )
                        row = cur_pre.fetchone()
                        cur_pre.close()
                        conn_pre.close()
                        if row:
                            student_id = row['id']
                    except Exception:
                        pass

            # ---- 1. Agent C 自动串联：查缓存 / 调 AI ----
            agent_c_data = None
            if req_target_job_id:
                try:
                    conn_job = get_db_connection()
                    cur_job = conn_job.cursor()
                    cur_job.execute(
                        "SELECT job_name, job_description, industry FROM jobs WHERE id = %s",
                        (req_target_job_id,)
                    )
                    job_row = cur_job.fetchone()
                    cur_job.close()
                    conn_job.close()

                    if job_row and job_row['job_name']:
                        target_job_name = job_row['job_name']

                        # ① 查 job_ai_profiles 缓存
                        if student_id:
                            try:
                                conn_c = get_db_connection()
                                cur_c = conn_c.cursor()
                                cur_c.execute(
                                    "SELECT ability_requirement_scores, vertical_promotion_info, job_transfer_paths "
                                    "FROM job_ai_profiles WHERE student_id = %s AND job_id = %s",
                                    (student_id, req_target_job_id)
                                )
                                cached = cur_c.fetchone()
                                cur_c.close()
                                conn_c.close()
                                if cached:
                                    agent_c_data = {
                                        'job_name': target_job_name,
                                        'ability_requirement_scores': (
                                            json.loads(cached['ability_requirement_scores'])
                                            if isinstance(cached['ability_requirement_scores'], str)
                                            else cached['ability_requirement_scores']
                                        ) or {},
                                        'vertical_promotion_info': (
                                            json.loads(cached['vertical_promotion_info'])
                                            if isinstance(cached['vertical_promotion_info'], str)
                                            else cached['vertical_promotion_info']
                                        ) or {},
                                        'job_transfer_paths': (
                                            json.loads(cached['job_transfer_paths'])
                                            if isinstance(cached['job_transfer_paths'], str)
                                            else cached['job_transfer_paths']
                                        ) or [],
                                    }
                                    print(f"[Agent D] 命中 Agent C 缓存, student={student_id}, job={req_target_job_id}")
                            except Exception:
                                pass

                        # ② 缓存未命中 → 自动调 Agent C
                        if not agent_c_data and student_id:
                            yield f"data: {json.dumps({'type': 'status', 'message': '正在分析目标岗位需求…'}, ensure_ascii=False)}\n\n"
                            job_info = {
                                'id': req_target_job_id,
                                'job_name': target_job_name,
                                'job_description': job_row['job_description'] or '',
                                'industry': job_row['industry'] or ''
                            }
                            parsed = orchestrator.run_agent_c_sync(job_info, student_profile_str)
                            if parsed:
                                agent_c_data = {
                                    'job_name': target_job_name,
                                    'ability_requirement_scores': parsed.get('ability_requirement_scores') or {},
                                    'vertical_promotion_info': parsed.get('vertical_promotion_info') or {},
                                    'job_transfer_paths': parsed.get('job_transfer_paths') or [],
                                }
                                # ③ 入库缓存
                                try:
                                    conn_save = get_db_connection()
                                    cur_save = conn_save.cursor()
                                    cur_save.execute("""
                                        INSERT INTO job_ai_profiles
                                        (job_id, student_id, ability_requirement_scores,
                                         vertical_promotion_info, job_transfer_paths, created_at)
                                        VALUES (%s, %s, %s, %s, %s, %s)
                                        ON DUPLICATE KEY UPDATE
                                            ability_requirement_scores = VALUES(ability_requirement_scores),
                                            vertical_promotion_info = VALUES(vertical_promotion_info),
                                            job_transfer_paths = VALUES(job_transfer_paths),
                                            created_at = VALUES(created_at)
                                    """, (
                                        req_target_job_id, student_id,
                                        json.dumps(agent_c_data['ability_requirement_scores'], ensure_ascii=False),
                                        json.dumps(agent_c_data['vertical_promotion_info'], ensure_ascii=False),
                                        json.dumps(agent_c_data['job_transfer_paths'], ensure_ascii=False),
                                        datetime.datetime.now()
                                    ))
                                    conn_save.commit()
                                    cur_save.close()
                                    conn_save.close()
                                    print(f"[Agent D] Agent C 自动完成并入库, student={student_id}, job={req_target_job_id}")
                                except Exception:
                                    pass
                            else:
                                yield f"data: {json.dumps({'type': 'status', 'message': '岗位画像分析未成功，将使用基础数据生成报告'}, ensure_ascii=False)}\n\n"
                except Exception:
                    pass

            # ---- 2. Agent D：生成报告 ----
            full_response = ""
            for event in orchestrator.run_agent_d(student_profile_str, top3_matches_str, agent_c_data):
                if event["type"] == "chunk":
                    full_response += event["content"]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': event['content']}, ensure_ascii=False)}\n\n"
                elif event["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event['message']}, ensure_ascii=False)}\n\n"
                    return

            # ---- 持久化：写入 career_reports + 更新 students 职业规划字段 ----
            report_id = None
            db_warning = None
            try:
                if student_id:
                    conn3 = get_db_connection()
                    cur3 = conn3.cursor()

                    # 从 HTML 中提取各板块文本（用于填充 students 表）
                    career_fields = _extract_career_fields(full_response)

                    # ---- 从 student_profile 提取补充字段 ----
                    resume_detail = student_profile.get('resume_detail_info', {})
                    ability_dim = student_profile.get('ability_dimension_scores', {})

                    # 专业技能 → 逗号拼接
                    raw_skills = resume_detail.get('professional_skills', [])
                    skills_str = ', '.join(raw_skills) if isinstance(raw_skills, list) else str(raw_skills)

                    # 六维评分 → PDF 友好数组
                    DIM_LABELS = {
                        'professional_skills_certificates': '专业技能与证书',
                        'innovation_ability': '创新能力',
                        'learning_ability': '学习能力',
                        'stress_resistance': '抗压能力',
                        'communication_ability': '沟通能力',
                        'internship_experience': '实习经历',
                    }
                    ability_scores = [
                        {"dimension": DIM_LABELS.get(k, k), "score": v}
                        for k, v in ability_dim.items()
                    ]

                    # Top10 匹配结果 → 从 DB 查
                    job_matches = []
                    if student_id:
                        cur3.execute("""
                            SELECT sjm.job_id, j.job_name, sjm.overall_matching as match_score
                            FROM student_job_matches sjm
                            LEFT JOIN jobs j ON sjm.job_id = j.id
                            WHERE sjm.student_id = %s
                            ORDER BY sjm.match_rank
                        """, (student_id,))
                        for row in cur3.fetchall():
                            job_matches.append({
                                'job_id': row['job_id'],
                                'job_name': row['job_name'] or f"岗位 #{row['job_id']}",
                                'match_score': row['match_score'],
                            })

                    # 构建结构化 report_content（兼容旧 /api/reports/:id 读取）
                    report_content = json.dumps({
                        "student_name": resume_detail.get('name', ''),
                        "job_direction": resume_detail.get('major', ''),
                        "report_date": datetime.datetime.now().strftime("%Y 年 %m 月 %d 日"),
                        "resume_score": student_profile.get('ability_overall_scores', {}).get('profile_completeness', 0),
                        "competitiveness_score": student_profile.get('ability_overall_scores', {}).get('competitiveness_score', 0),
                        "email": resume_detail.get('email', ''),
                        "phone": resume_detail.get('phone', ''),
                        "education": resume_detail.get('education', ''),
                        "skills": skills_str,
                        "ability_scores": ability_scores,
                        "job_matches": job_matches,
                        "match_conclusion": career_fields.get('person_post_matching_analysis', ''),
                        "career_goal": career_fields.get('core_career_goal', ''),
                        "industry_trend_analysis": career_fields.get('industry_demand_and_trend_analysis', ''),
                        "development_path": career_fields.get('clear_career_development_path', ''),
                        "action_plan": career_fields.get('staged_growth_plan', ''),
                        "evaluation_mechanism": career_fields.get('dynamic_evaluation_mechanism', ''),
                        "report_html": full_response,
                    }, ensure_ascii=False)

                    cur3.execute("""
                        INSERT INTO career_reports
                        (student_id, target_job_id, report_title, report_content, report_html, user_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        student_id,
                        req_target_job_id,
                        req_report_title,
                        report_content,
                        full_response,
                        req_user_id,
                        datetime.datetime.now(),
                        datetime.datetime.now()
                    ))

                    # ★ 同时更新 students 表的 6 个职业规划字段
                    cur3.execute("""
                        UPDATE students SET
                            person_post_matching_analysis = %s,
                            core_career_goal = %s,
                            industry_demand_and_trend_analysis = %s,
                            clear_career_development_path = %s,
                            staged_growth_plan = %s,
                            dynamic_evaluation_mechanism = %s,
                            updated_at = %s
                        WHERE id = %s AND user_id = %s
                    """, (
                        career_fields.get('person_post_matching_analysis', ''),
                        career_fields.get('core_career_goal', ''),
                        career_fields.get('industry_demand_and_trend_analysis', ''),
                        career_fields.get('clear_career_development_path', ''),
                        career_fields.get('staged_growth_plan', ''),
                        career_fields.get('dynamic_evaluation_mechanism', ''),
                        datetime.datetime.now(),
                        student_id,
                        req_user_id
                    ))

                    conn3.commit()
                    report_id = cur3.lastrowid
                    # 兜底：lastrowid 可能为 0（如 SELECT 干扰），主动查一次
                    if not report_id and student_id:
                        cur3.execute(
                            "SELECT id FROM career_reports WHERE student_id=%s ORDER BY created_at DESC LIMIT 1",
                            (student_id,)
                        )
                        row = cur3.fetchone()
                        if row:
                            report_id = row['id']
                    cur3.close()
                    conn3.close()
                    print(f"[Agent D] 报告已保存, report_id={report_id}, student_id={student_id}")
                    print(f"[Agent D] students 表职业规划字段已同步更新")
                else:
                    db_warning = "未传入 student_id 且无法从画像推断，报告未保存到数据库"
            except Exception as e:
                import traceback
                traceback.print_exc()
                db_warning = f"报告保存失败：{str(e)}"

            # ---- 校验 HTML 完整性 ----
            html_warnings = _validate_report_html(full_response)
            if html_warnings:
                db_warning = (db_warning + '; ' if db_warning else '') + html_warnings
                print(f"[Agent D] HTML 完整性警告: {html_warnings}")

            done_event = {'type': 'done'}
            if report_id:
                done_event['report_id'] = report_id
            if db_warning:
                done_event['warning'] = db_warning

            yield f"data: {json.dumps(done_event, ensure_ascii=False)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        return jsonify({"error": f"服务器内部错误：{str(e)}"}), 500


# ============================================================
# GET 查 DB 接口：判断是否需要调用 Agent B / C
# ============================================================

@agent_bp.route('/api/agent/match/<int:student_id>', methods=['GET'])
def check_match_exists(student_id):
    """
    检查学生是否已有岗位匹配结果（查 student_job_matches 表）
    有 → 返回匹配数据；没有 → 返回 exists=false
    """
    try:
        current_user = get_current_user()
        user_id = current_user['id'] if current_user else 1

        conn = get_db_connection()
        cursor = conn.cursor()

        # 先查学生姓名
        cursor.execute(
            "SELECT name FROM students WHERE id = %s AND user_id = %s",
            (student_id, user_id)
        )
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            return jsonify({"exists": False, "error": "学生不存在"}), 404

        student_name = student['name']

        # 查匹配结果
        cursor.execute("""
            SELECT sjm.*, j.job_name, j.company_name, j.salary_range, j.work_address, j.industry
            FROM student_job_matches sjm
            LEFT JOIN jobs j ON sjm.job_id = j.id
            WHERE sjm.student_id = %s
            ORDER BY sjm.match_rank
        """, (student_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        if rows:
            matches = []
            for row in rows:
                matches.append({
                    'job_id': row['job_id'],
                    'match_rank': row['match_rank'],
                    'job_name': row.get('job_name', f"岗位 #{row['job_id']}"),
                    'company_name': row.get('company_name', ''),
                    'salary': row.get('salary_range', ''),
                    'location': row.get('work_address', ''),
                    'industry': row.get('industry', ''),
                    'overall_match_score': row['overall_matching'],
                    'match_level': (
                        'excellent' if row['overall_matching'] >= 80 else
                        'good' if row['overall_matching'] >= 60 else
                        'moderate' if row['overall_matching'] >= 40 else
                        'poor'
                    ),
                    'basic_requirements_score': row['basic_requirements_matching'],
                    'professional_skills_score': row['professional_skills_matching'],
                    'professional_qualities_score': row['professional_literacy_matching'],
                    'development_potential_score': row['development_potential_matching'],
                })
            return jsonify({
                "exists": True,
                "student_name": student_name,
                "data": matches,
            })
        else:
            return jsonify({
                "exists": False,
                "student_name": student_name,
            })
    except Exception as e:
        return jsonify({"error": f"查询失败：{str(e)}"}), 500


@agent_bp.route('/api/agent/report/<int:student_id>', methods=['GET'])
def check_report_exists(student_id):
    """
    检查学生是否已有职业报告（查 career_reports 表）
    支持 ?job_id= 按岗位过滤
    有 → 返回报告 HTML；没有 → 返回 exists=false
    """
    try:
        current_user = get_current_user()
        user_id = current_user['id'] if current_user else 1

        # 可选：按岗位过滤
        target_job_id = request.args.get('job_id', type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

        # 先查学生姓名
        cursor.execute(
            "SELECT name FROM students WHERE id = %s AND user_id = %s",
            (student_id, user_id)
        )
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            return jsonify({"exists": False, "error": "学生不存在"}), 404

        student_name = student['name']

        # 查最新报告（按学生+岗位）
        if target_job_id:
            cursor.execute("""
                SELECT id, report_html, report_title, created_at, target_job_id
                FROM career_reports
                WHERE student_id = %s AND target_job_id = %s AND user_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, (student_id, target_job_id, user_id))
        else:
            cursor.execute("""
                SELECT id, report_html, report_title, created_at, target_job_id
                FROM career_reports
                WHERE student_id = %s AND user_id = %s
                ORDER BY created_at DESC LIMIT 1
            """, (student_id, user_id))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row and row['report_html']:
            return jsonify({
                "exists": True,
                "student_name": student_name,
                "report_id": row['id'],
                "report_title": row['report_title'],
                "report_html": row['report_html'],
                "target_job_id": row.get('target_job_id'),
                "created_at": row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
            })
        else:
            return jsonify({
                "exists": False,
                "student_name": student_name,
            })
    except Exception as e:
        return jsonify({"error": f"查询失败：{str(e)}"}), 500


# ============================================================
# 工具函数
# ============================================================

def _extract_json(text: str):
    """从 AI 返回的文本中提取 JSON 对象"""
    import re
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
    import re
    warnings = []

    if not html or not html.strip():
        return "报告 HTML 为空"

    stripped = html.strip()

    # 1. 检查 HTML 是否以 </div> 结尾（报告最外层容器）
    if not stripped.endswith('</div>'):
        # 检查末尾是否被截断（没闭合的标签）
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
    从 Agent C 输出的 HTML 报告中提取 6 个职业规划文本字段，
    用于填充 students 表（配合 Agent A 的画像数据，完成整条学生记录）

    HTML 报告结构（Agent C System Prompt 定义）:
      <section id="matching-analysis"> → person_post_matching_analysis
      <section id="career-goal">
        <h3>1. 核心职业目标</h3> → core_career_goal
        <h3>2. 行业需求与趋势分析</h3> → industry_demand_and_trend_analysis
        <h3>3. 明确的发展路径</h3> → clear_career_development_path
      <section id="action-plan">
        <h3>1. 分阶段成长计划</h3> → staged_growth_plan
        <h3>2. 动态评估机制</h3> → dynamic_evaluation_mechanism
    """
    import re

    def _strip_tags(s: str) -> str:
        """去掉 HTML 标签，保留文本"""
        s = re.sub(r'<[^>]+>', '', s)
        # 压缩多余空白
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

        # 找到目标 h3 标签后的内容（$ 兜底 section 内最后一个 h3）
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


# ============================================================
# Agent E：虚拟行业大佬 1v1 访谈
# ============================================================

@agent_bp.route('/api/agent/interview', methods=['POST'])
def agent_interview():
    """
    输入：student_id, job_id, message
    输出：SSE 流 → "行业大佬"角色的回复文本

    请求格式（application/json）:
      {
        "student_id": 1,
        "job_id": 5,
        "message": "老哥，这行35岁后大家都去哪了？"
      }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        student_id = data.get('student_id')
        job_id = data.get('job_id')
        message = data.get('message', '').strip()

        if not student_id or not job_id:
            return jsonify({"error": "student_id 和 job_id 不能为空"}), 400
        if not message:
            return jsonify({"error": "消息不能为空"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 辅助函数
        def _parse_json(val):
            return json.loads(val) if isinstance(val, str) else val

        # 1. 查学生是否存在
        cursor.execute("SELECT name FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            cursor.close()
            conn.close()
            return jsonify({"error": "学生不存在"}), 404

        # 2. 构建学生画像（优先用前端传入的 Agent A 输出，否则从 DB 构建）
        student_profile = data.get('student_profile')
        if not student_profile:
            cursor.execute("""
                SELECT name, email, phone, education,
                       professional_skills, project_experience, resume_text,
                       professional_skills_certificates, innovation_ability,
                       learning_ability, stress_resistance, communication_ability,
                       internship_experience, profile_completeness, competitiveness_score
                FROM students WHERE id = %s
            """, (student_id,))
            db_student = cursor.fetchone()

            student_profile = {
                "resume_detail_info": {
                    "name": (db_student.get('name') or '') if db_student else '',
                    "email": (db_student.get('email') or '') if db_student else '',
                    "phone": (db_student.get('phone') or '') if db_student else '',
                    "education": (db_student.get('education') or '') if db_student else '',
                    "professional_skills": _parse_json(db_student.get('professional_skills')) if db_student else [],
                },
                "ability_dimension_scores": {
                    "专业技能证书": (db_student.get('professional_skills_certificates') or 0) if db_student else 0,
                    "创新能力": (db_student.get('innovation_ability') or 0) if db_student else 0,
                    "学习能力": (db_student.get('learning_ability') or 0) if db_student else 0,
                    "抗压能力": (db_student.get('stress_resistance') or 0) if db_student else 0,
                    "沟通能力": (db_student.get('communication_ability') or 0) if db_student else 0,
                    "实习经验": (db_student.get('internship_experience') or 0) if db_student else 0,
                },
                "ability_overall_scores": {
                    "profile_completeness": (db_student.get('profile_completeness') or 0) if db_student else 0,
                    "competitiveness_score": (db_student.get('competitiveness_score') or 0) if db_student else 0,
                },
            }

        # 2. 查岗位详情
        cursor.execute("""
            SELECT id, job_name, company_name, salary_range, industry, job_description
            FROM jobs WHERE id = %s
        """, (job_id,))
        job = cursor.fetchone()
        if not job:
            cursor.close()
            conn.close()
            return jsonify({"error": "岗位不存在"}), 404

        job_info = {
            'id': job['id'],
            'job_name': job['job_name'],
            'company_name': job.get('company_name', '') or '',
            'salary_range': job.get('salary_range', '') or '',
            'industry': job.get('industry', '') or '',
            'job_description': job.get('job_description', '') or '',
        }

        # 3. 查 Agent C 岗位 AI 画像（自动串联：未命中则同步调 Agent C）
        cursor.execute("""
            SELECT ability_requirement_scores, vertical_promotion_info, job_transfer_paths
            FROM job_ai_profiles
            WHERE student_id = %s AND job_id = %s
            ORDER BY created_at DESC LIMIT 1
        """, (student_id, job_id))
        c_row = cursor.fetchone()

        agent_c_data = None
        if c_row:
            agent_c_data = {
                'ability_requirement_scores': _parse_json(c_row['ability_requirement_scores']),
                'vertical_promotion_info': _parse_json(c_row['vertical_promotion_info']),
                'job_transfer_paths': _parse_json(c_row['job_transfer_paths']),
                'job_name': job_info['job_name'],
            }
        else:
            # 自动触发 Agent C 同步版
            print(f"[Agent E] job_ai_profiles 缓存未命中 (sid={student_id}, jid={job_id})，自动调 Agent C...")
            student_profile_str = json.dumps(student_profile, ensure_ascii=False)
            c_result = orchestrator.run_agent_c_sync(job_info, student_profile_str)
            if c_result:
                agent_c_data = {
                    'ability_requirement_scores': c_result.get('ability_requirement_scores', {}),
                    'vertical_promotion_info': c_result.get('vertical_promotion_info', {}),
                    'job_transfer_paths': c_result.get('job_transfer_paths', []),
                    'job_name': job_info['job_name'],
                }
                # 入库
                try:
                    cursor.execute("""
                        INSERT INTO job_ai_profiles
                            (job_id, student_id, ability_requirement_scores,
                             vertical_promotion_info, job_transfer_paths)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            ability_requirement_scores = VALUES(ability_requirement_scores),
                            vertical_promotion_info = VALUES(vertical_promotion_info),
                            job_transfer_paths = VALUES(job_transfer_paths)
                    """, (
                        job_id, student_id,
                        json.dumps(agent_c_data['ability_requirement_scores'], ensure_ascii=False),
                        json.dumps(agent_c_data['vertical_promotion_info'], ensure_ascii=False),
                        json.dumps(agent_c_data['job_transfer_paths'], ensure_ascii=False),
                    ))
                    conn.commit()
                    print(f"[Agent E] Agent C 数据已入库 (sid={student_id}, jid={job_id})")
                except Exception as e:
                    print(f"[Agent E] Agent C 入库失败: {e}")

        # 4. 查历史对话
        cursor.execute("""
            SELECT messages FROM interview_sessions
            WHERE student_id = %s AND job_id = %s
        """, (student_id, job_id))
        session_row = cursor.fetchone()

        chat_history = []
        if session_row:
            messages_raw = session_row['messages']
            chat_history = json.loads(messages_raw) if isinstance(messages_raw, str) else messages_raw

        cursor.close()
        conn.close()

        # 硬上限：超过 50 轮（100 条实际消息）强制开启新对话
        MAX_MSG_COUNT = 100
        actual_count = sum(1 for m in chat_history if m.get('role') != 'summary')
        is_reset = actual_count >= MAX_MSG_COUNT
        if is_reset:
            print(f"[Agent E] 对话已达 {actual_count} 条（50 轮上限），强制开启新对话 (sid={student_id}, jid={job_id})")
            chat_history = []

        student_profile_str = json.dumps(student_profile, ensure_ascii=False)

        def generate():
            nonlocal chat_history

            # 告知前端是新对话
            if is_reset:
                yield f"data: {json.dumps({'type': 'reset', 'message': '对话已达50轮上限，已自动开启新对话'}, ensure_ascii=False)}\n\n"

            # 流式调用 Agent E
            full_response = ""
            for event in orchestrator.run_agent_e(
                student_profile_str, job_info, agent_c_data,
                chat_history, message
            ):
                if event["type"] == "chunk":
                    full_response += event["content"]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': event['content']}, ensure_ascii=False)}\n\n"
                elif event["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event['message']}, ensure_ascii=False)}\n\n"
                    return

            # 持久化：追加本轮对话
            now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            chat_history.append({"role": "user", "content": message, "time": now_str})
            chat_history.append({"role": "assistant", "content": full_response, "time": now_str})

            # 摘要压缩：超过 3 轮（6 条）时，压缩旧对话
            RECENT_MSG_COUNT = 6
            MESSAGES = chat_history

            # 分离摘要和实际消息
            old_summary = ""
            actual_msgs = []
            for m in MESSAGES:
                if m.get('role') == 'summary':
                    old_summary = m['content']
                else:
                    actual_msgs.append(m)

            if len(actual_msgs) > RECENT_MSG_COUNT:
                overflow = actual_msgs[:-RECENT_MSG_COUNT]
                recent = actual_msgs[-RECENT_MSG_COUNT:]
                print(f"[Agent E] 压缩 {len(overflow)} 条旧消息为摘要...")
                new_summary = orchestrator._summarize_history(overflow, old_summary)
                # 重建 messages：摘要 + 最近 3 轮
                chat_history = [{"role": "summary", "content": new_summary}]
                chat_history.extend(recent)
                print(f"[Agent E] 摘要压缩完成，摘要长度: {len(new_summary)} 字")

            try:
                conn2 = get_db_connection()
                cur2 = conn2.cursor()
                messages_json = json.dumps(chat_history, ensure_ascii=False)
                cur2.execute("""
                    INSERT INTO interview_sessions (student_id, job_id, messages)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE messages = VALUES(messages)
                """, (student_id, job_id, messages_json))
                conn2.commit()
                cur2.close()
                conn2.close()
            except Exception as e:
                print(f"[Agent E] 对话保存失败: {e}")

            yield f"data: {json.dumps({'type': 'done', 'result': full_response}, ensure_ascii=False)}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
    except Exception as e:
        return jsonify({"error": f"服务器内部错误：{str(e)}"}), 500


@agent_bp.route('/api/agent/interview/<int:student_id>/<int:job_id>', methods=['GET'])
def get_interview_history(student_id, job_id):
    """
    查询某学生对某岗位的历史对话记录
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, student_id, job_id, messages, created_at, updated_at
            FROM interview_sessions
            WHERE student_id = %s AND job_id = %s
        """, (student_id, job_id))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row:
            messages_raw = row['messages']
            all_messages = json.loads(messages_raw) if isinstance(messages_raw, str) else messages_raw
            # 过滤掉摘要消息，只返回实际对话
            messages = [m for m in all_messages if m.get('role') != 'summary']
            return jsonify({
                "exists": True,
                "session_id": row['id'],
                "student_id": row['student_id'],
                "job_id": row['job_id'],
                "messages": messages,
                "created_at": row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else '',
                "updated_at": row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if row['updated_at'] else '',
            })
        else:
            return jsonify({
                "exists": False,
                "messages": []
            })
    except Exception as e:
        return jsonify({"error": f"查询失败：{str(e)}"}), 500


@agent_bp.route('/api/agent/interview/<int:student_id>/<int:job_id>', methods=['DELETE'])
def delete_interview_history(student_id, job_id):
    """
    清空某学生对某岗位的对话历史（重新开始访谈）
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM interview_sessions
            WHERE student_id = %s AND job_id = %s
        """, (student_id, job_id))
        deleted = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "deleted": deleted > 0,
            "message": "对话历史已清空" if deleted else "没有可清空的记录"
        })
    except Exception as e:
        return jsonify({"error": f"清空失败：{str(e)}"}), 500
