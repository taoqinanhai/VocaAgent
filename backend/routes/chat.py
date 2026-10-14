"""
对话路由：/api/chat, /api/chat/customer-service
"""
import json
import os
import time
import sys
from http import HTTPStatus
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from dashscope import Application
from config.settings import (
    API_KEY, APP_ID_A, API_KEY1, APP_ID1,
    KNOWLEDGE_BASE_IDS, UPLOAD_FOLDER,
)
from utils.file_processor import allowed_file, extract_file_content

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "服务运行正常"})


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        content_type = request.content_type or ''

        if content_type.startswith('multipart/form-data'):
            file = request.files.get('file')
            message = request.form.get('message', '')
            history_str = request.form.get('history', '[]')
        elif content_type.startswith('application/json'):
            data = request.get_json()
            if not data:
                return jsonify({"error": "请求数据不能为空"}), 400
            message = data.get('message', '')
            history_str = json.dumps(data.get('history', []))
            file = None
        else:
            return jsonify({"error": "不支持的请求格式"}), 415

        try:
            history = json.loads(history_str)
        except json.JSONDecodeError:
            history = []

        if not message and not file:
            return jsonify({"error": "消息不能为空"}), 400

        messages = []
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role and content:
                messages.append({'role': role, 'content': content})

        if file and file.filename != '':
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                if os.path.exists(filepath):
                    name, ext = os.path.splitext(filename)
                    filename = f"{name}_{int(time.time())}{ext}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                file.save(filepath)

                file_summary = extract_file_content(filepath)

                if file_summary:
                    messages.append({'role': 'user', 'content': f"简历内容：{file_summary}"})
            else:
                return jsonify({"error": "不支持的文件格式"}), 400

        messages.append({'role': 'user', 'content': message})

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

        try:
            response = Application.call(**call_params)

            full_response = ""
            for chunk in response:
                if chunk.status_code == HTTPStatus.OK:
                    full_response += chunk.output.text
                else:
                    return jsonify({
                        "error": f"API 调用失败：{chunk.message} (code={chunk.status_code}, request_id={chunk.request_id})"
                    }), 500
        except Exception as e:
            print(f"API 调用失败: {str(e)}")
            return jsonify({
                "error": f"API 调用失败：{str(e)}"
            }), 500

        return jsonify({"response": full_response})

    except Exception as e:
        print(f"聊天接口错误: {str(e)}")
        return jsonify({"error": f"服务器内部错误：{str(e)}"}), 500


@chat_bp.route('/api/chat/customer-service', methods=['POST'])
def customer_service_chat():
    try:
        content_type = request.content_type or ''

        if content_type.startswith('multipart/form-data'):
            file = request.files.get('file')
            message = request.form.get('message', '')
            history_str = request.form.get('history', '[]')
        elif content_type.startswith('application/json'):
            data = request.get_json()
            if not data:
                return jsonify({"error": "请求数据不能为空"}), 400
            message = data.get('message', '')
            history_str = json.dumps(data.get('history', []))
            file = None
        else:
            return jsonify({"error": "不支持的请求格式"}), 415

        try:
            history = json.loads(history_str)
        except json.JSONDecodeError:
            history = []

        if not message and not file:
            return jsonify({"error": "消息不能为空"}), 400

        messages = []
        for msg in history:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if role and content:
                messages.append({'role': role, 'content': content})

        if file and file.filename != '':
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                if os.path.exists(filepath):
                    name, ext = os.path.splitext(filename)
                    filename = f"{name}_{int(time.time())}{ext}"
                    filepath = os.path.join(UPLOAD_FOLDER, filename)

                file.save(filepath)

                file_summary = extract_file_content(filepath)

                if file_summary:
                    messages.append({'role': 'user', 'content': f"文件内容：{file_summary}"})
            else:
                return jsonify({"error": "不支持的文件格式"}), 400

        messages.append({'role': 'user', 'content': message})

        system_prompt = "你是一个专业的AI客服助手，负责回答用户关于大学生就业规划平台的各种问题。你的职责包括：\n1. 解答平台使用方法和功能相关的问题\n2. 提供职业规划相关的基本指导\n3. 帮助用户理解平台的各项服务\n4. 以友好、专业的态度与用户交流\n5. 对于复杂问题，引导用户使用平台的专业功能\n\n请保持回答简洁明了，直接针对用户问题给出有用的信息。"

        if not API_KEY1 or not APP_ID1:
            return jsonify({"response": "客服功能暂未开放，敬请期待。您可以先浏览岗位或使用其他功能。"}), 200

        call_params = {
            'api_key': API_KEY1,
            'app_id': APP_ID1,
            'messages': [{'role': 'system', 'content': system_prompt}] + messages,
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
                    "error": f"API 调用失败：{chunk.message} (code={chunk.status_code}, request_id={chunk.request_id})"
                }), 500

        return jsonify({"response": full_response})

    except Exception as e:
        return jsonify({"error": f"服务器内部错误：{str(e)}"}), 500
