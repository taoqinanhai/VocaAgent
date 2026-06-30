"""
Agent C 路由：单岗位画像分析 (SSE 流式, 按需触发) + 缓存查询
"""
import json
import datetime
from flask import Blueprint, request, jsonify, Response, stream_with_context
from services.agent_orchestrator import orchestrator
from utils.db import get_db_connection
from .agent_utils import _extract_json

agent_c_bp = Blueprint('agent_c', __name__)


@agent_c_bp.route('/api/agent/job-profile', methods=['POST'])
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


@agent_c_bp.route('/api/agent/job-profile/<int:student_id>/<int:job_id>', methods=['GET'])
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
