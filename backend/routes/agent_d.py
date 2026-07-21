"""
Agent D 路由：报告生成 → 职业规划报告 HTML (SSE 流式)
内部自动串联 Agent C（查缓存 / 调 AI / 入库）
+ 报告缓存查询
"""
import json
import datetime
from flask import Blueprint, request, jsonify, Response, stream_with_context
from services.agent_orchestrator import orchestrator
from utils.db import get_db_connection
from utils.auth import get_current_user
from utils.skill_analyzer import analyze_skill_gap, format_gap_for_prompt
from .agent_utils import _extract_json, _validate_report_html, _extract_career_fields, build_job_context, JOB_CONTEXT_COLUMNS

agent_d_bp = Blueprint('agent_d', __name__)


@agent_d_bp.route('/api/agent/report', methods=['POST'])
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

        # ---- 规则引擎预计算：技能差距分析 ----
        skill_details = student_profile.get('skill_details', [])
        skill_gap_text = None
        if skill_details and req_target_job_id:
            try:
                gap = analyze_skill_gap(skill_details, req_target_job_id)
                skill_gap_text = format_gap_for_prompt(gap)
            except Exception:
                pass  # 差距分析失败不阻塞主流程

        # ---- 补全 top3_matches：DB 批量查询，把岗位名/公司名拼进去 ----
        enriched_matches = list(top3_matches) if isinstance(top3_matches, list) else []
        if enriched_matches:
            try:
                match_ids = [
                    m.get('job_id') or m.get('id')
                    for m in enriched_matches
                    if (m.get('job_id') or m.get('id'))
                ]
                if match_ids:
                    conn_enrich = get_db_connection()
                    cur_enrich = conn_enrich.cursor()
                    placeholders = ','.join(['%s'] * len(match_ids))
                    cur_enrich.execute(
                        f"SELECT id, job_name, company_name FROM jobs WHERE id IN ({placeholders})",
                        match_ids
                    )
                    id_to_info = {}
                    for row in cur_enrich.fetchall():
                        id_to_info[row['id']] = {
                            'job_name': row['job_name'],
                            'company_name': row.get('company_name', ''),
                        }
                    cur_enrich.close()
                    conn_enrich.close()
                    for m in enriched_matches:
                        mid = m.get('job_id') or m.get('id')
                        if mid and mid in id_to_info:
                            m['job_name'] = id_to_info[mid]['job_name']
                            m['company_name'] = id_to_info[mid]['company_name']
            except Exception:
                pass  # 补全失败不阻塞主流程
        top3_matches_str = json.dumps(enriched_matches, ensure_ascii=False, indent=2)

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
                        f"SELECT {JOB_CONTEXT_COLUMNS} FROM jobs WHERE id = %s",
                        (req_target_job_id,)
                    )
                    job_row = cur_job.fetchone()
                    cur_job.close()
                    conn_job.close()

                    if job_row and job_row['job_name']:
                        target_job_name = job_row['job_name']
                        target_job_context = build_job_context(job_row)

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
                            parsed = orchestrator.run_agent_c_sync(target_job_context, student_profile_str)
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
            for event in orchestrator.run_agent_d(student_profile_str, top3_matches_str, agent_c_data, skill_gap_text):
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


@agent_d_bp.route('/api/agent/report/<int:student_id>', methods=['GET'])
def check_report_exists(student_id):
    """
    检查学生是否已有职业报告（查 career_reports 表）
    支持 ?job_id= 按岗位过滤
    有 → 返回报告 HTML；没有 → 返回 exists=false
    """
    try:
        current_user = get_current_user()
        user_id = current_user['id'] if current_user else 1

        target_job_id = request.args.get('job_id', type=int)

        conn = get_db_connection()
        cursor = conn.cursor()

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
