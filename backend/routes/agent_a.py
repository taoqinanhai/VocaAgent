"""
Agent A 路由：简历解析 → 学生能力画像 (SSE 流式)
"""
import json
import os
import time
from flask import Blueprint, request, jsonify, Response, stream_with_context
from werkzeug.utils import secure_filename
from services.agent_orchestrator import orchestrator
from services.resume_parser import parse_and_save_resume_data
from config.settings import UPLOAD_FOLDER
from utils.file_processor import allowed_file, extract_file_content
from utils.auth import get_current_user

agent_a_bp = Blueprint('agent_a', __name__)


@agent_a_bp.route('/api/agent/profile', methods=['POST'])
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

            if not resume_text or len(resume_text.strip()) < 30:
                return jsonify({
                    "error": "无法从文件中提取有效文本内容。"
                             "如果您的PDF是扫描图片，请确保图片清晰可读；"
                             "如果是文字型PDF，请确认文件未加密或损坏。"
                }), 400

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
                student_id, error = parse_and_save_resume_data(full_response, user_id, resume_text)
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
