"""
Agent E 路由：虚拟行业大佬 1v1 访谈 (SSE 流式, 多轮对话)
内部自动串联 Agent C（查缓存 / 调 AI / 入库）
+ 访谈历史查询 / 清空
"""
import json
import datetime
from flask import Blueprint, request, jsonify, Response, stream_with_context
from services.agent_orchestrator import orchestrator
from utils.db import get_db_connection

agent_e_bp = Blueprint('agent_e', __name__)


@agent_e_bp.route('/api/agent/interview', methods=['POST'])
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


@agent_e_bp.route('/api/agent/interview/<int:student_id>/<int:job_id>', methods=['GET'])
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


@agent_e_bp.route('/api/agent/interview/<int:student_id>/<int:job_id>', methods=['DELETE'])
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
