"""
Agent B 路由：岗位匹配 → 10 岗位评分 (SSE 流式) + 匹配结果缓存查询
"""
import json
import datetime
from flask import Blueprint, request, jsonify, Response, stream_with_context
from services.agent_orchestrator import orchestrator
from utils.db import get_db_connection
from utils.auth import get_current_user
from utils.skill_analyzer import select_top_jobs
from .agent_utils import _extract_json, build_job_context, JOB_CONTEXT_COLUMNS

agent_b_bp = Blueprint('agent_b', __name__)


def _to_float(value, default=0.0):
    """把 AI 返回的分数字段安全转成 float。

    AI 可能返回字符串（"85" / "85%"）甚至 null。直接用会在排序时抛
    TypeError: '<' not supported between 'str' and 'int'，导致整批匹配结果
    一条都不落库；写库时也会因类型不符失败。这里统一兜底。
    """
    if isinstance(value, bool):  # bool 是 int 子类，单独挡掉
        return default
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip().rstrip('%'))
    except (TypeError, ValueError):
        return default


@agent_b_bp.route('/api/agent/match', methods=['POST'])
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

        req_student_id = data.get('student_id')
        current_user = get_current_user()
        req_user_id = current_user['id'] if current_user else 1

        # ---- 规则引擎粗筛：从全量岗位中选出 Top N ----
        skill_details = student_profile.get('skill_details', [])
        conn = get_db_connection()
        cursor = conn.cursor()

        job_ids = data.get('job_ids')
        if job_ids and isinstance(job_ids, list):
            # 用户指定了岗位范围，直接取全部
            placeholders = ','.join(['%s'] * len(job_ids))
            cursor.execute(
                f"SELECT {JOB_CONTEXT_COLUMNS} FROM jobs WHERE id IN ({placeholders})",
                job_ids
            )
            jobs_raw = cursor.fetchall()
        elif skill_details:
            # 有技能数据 → 规则引擎粗筛 Top 10
            cursor.execute("SELECT id FROM jobs")
            all_ids = [row['id'] for row in cursor.fetchall()]
            top_jobs = select_top_jobs(skill_details, all_ids, top_n=10)
            top_ids = [job_id for job_id, score in top_jobs]
            if top_ids:
                placeholders = ','.join(['%s'] * len(top_ids))
                cursor.execute(
                    f"SELECT {JOB_CONTEXT_COLUMNS} FROM jobs WHERE id IN ({placeholders})",
                    top_ids
                )
                jobs_raw = cursor.fetchall()
                # 按 select_top_jobs 的排序重排（SQL IN 不保序）
                id_order = {jid: i for i, (jid, _) in enumerate(top_jobs)}
                jobs_raw = sorted(jobs_raw, key=lambda j: id_order.get(j['id'], 999))
            else:
                jobs_raw = []
        else:
            # 无 skill_details → 兜底：取前 10 条（按 ID 排序，保证确定性）
            cursor.execute(
                f"SELECT {JOB_CONTEXT_COLUMNS} FROM jobs ORDER BY id LIMIT 10"
            )
            jobs_raw = cursor.fetchall()
        cursor.close()
        conn.close()

        if not jobs_raw:
            return jsonify({"error": "数据库中没有岗位数据，请先导入岗位"}), 500

        job_descriptions = [build_job_context(j) for j in jobs_raw]

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
                student_id = req_student_id
                if not student_id:
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
                    parsed = _extract_json(full_response)
                    job_profiles = parsed.get('job_post_profiles', []) if parsed else []

                    if job_profiles:
                        # 写库前按综合匹配分降序排序，保证 match_rank 与分数顺序一致
                        # （分数可能被 AI 返回成字符串，用 _to_float 兜底，否则 TypeError
                        #   会让整批结果不落库）
                        job_profiles = sorted(
                            job_profiles,
                            key=lambda j: _to_float(j.get('user_matching_scores', {}).get('overall_matching', 0)),
                            reverse=True
                        )

                        conn3 = get_db_connection()
                        cur3 = conn3.cursor()
                        saved = False

                        try:
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
                                    _to_float(matching.get('basic_requirements_matching', 0)),
                                    _to_float(matching.get('professional_skills_matching', 0)),
                                    _to_float(matching.get('professional_literacy_matching', 0)),
                                    _to_float(matching.get('development_potential_matching', 0)),
                                    _to_float(matching.get('overall_matching', 0)),
                                    datetime.datetime.now(),
                                    datetime.datetime.now()
                                ))
                                match_count += 1

                            conn3.commit()
                            saved = True
                        except Exception as e:
                            conn3.rollback()
                            match_count = 0  # 已回滚，不能再对外报"已保存 N 条"
                            db_warning = f"匹配结果保存失败：{str(e)}"
                            print(f"[Agent B] 匹配结果保存失败: {e}")
                        finally:
                            cur3.close()
                            conn3.close()

                        # 只在真正 commit 成功后打印，避免回滚了还打"已保存"
                        if saved:
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


@agent_b_bp.route('/api/agent/match/<int:student_id>', methods=['GET'])
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
