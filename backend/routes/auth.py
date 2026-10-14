"""
认证路由：/api/auth/*
"""
from flask import Blueprint, request, jsonify
from utils.db import get_db_connection
from utils.auth import (
    hash_password, verify_password, generate_token,
    generate_expiration_time, get_current_user,
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        name = data.get('name')

        if not username or not password or not email:
            return jsonify({"error": "用户名、密码和邮箱不能为空"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"error": "用户名已存在"}), 400

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "邮箱已存在"}), 400

        hashed_password = hash_password(password)

        cursor.execute(
            "INSERT INTO users (username, password, email, name) VALUES (%s, %s, %s, %s)",
            (username, hashed_password, email, name)
        )
        conn.commit()

        user_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "注册成功", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"error": f"注册失败：{str(e)}"}), 500


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "邮箱和密码不能为空"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "用户名或密码错误"}), 401

        if not verify_password(user['password'], password):
            return jsonify({"error": "用户名或密码错误"}), 401

        if not user['is_active']:
            return jsonify({"error": "账户已被禁用"}), 403

        token = generate_token()
        expires_at = generate_expiration_time()

        # 清理该用户旧 Token，避免 user_tokens 表无限膨胀（每个用户只保留一个有效 Token）
        cursor.execute("DELETE FROM user_tokens WHERE user_id = %s", (user['id'],))
        cursor.execute(
            "INSERT INTO user_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
            (user['id'], token, expires_at)
        )
        conn.commit()

        cursor.close()
        conn.close()

        user_info = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'name': user['name'],
            'role': user['role'],
            'is_active': bool(user['is_active']),
            'created_at': user['created_at'].isoformat() if user['created_at'] else None
        }

        return jsonify({"success": True, "message": "登录成功", "user": user_info, "token": token}), 200
    except Exception as e:
        return jsonify({"error": f"登录失败：{str(e)}"}), 500


@auth_bp.route('/api/auth/user', methods=['GET'])
def get_user_info():
    """获取用户信息"""
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None

        if not token:
            return jsonify({"error": "未提供认证令牌"}), 401

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_tokens WHERE token = %s AND expires_at > NOW()", (token,))
        token_record = cursor.fetchone()

        if not token_record:
            cursor.close()
            conn.close()
            return jsonify({"error": "无效的认证令牌"}), 401

        user_id = token_record['user_id']
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({"error": "用户不存在"}), 404

        if not user['is_active']:
            cursor.close()
            conn.close()
            return jsonify({"error": "账户已被禁用"}), 403

        cursor.close()
        conn.close()

        user_info = {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'name': user['name'],
            'role': user['role'],
            'is_active': bool(user['is_active']),
            'created_at': user['created_at'].isoformat() if user['created_at'] else None
        }

        return jsonify({"success": True, "user": user_info}), 200
    except Exception as e:
        return jsonify({"error": f"获取用户信息失败：{str(e)}"}), 500


@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """用户登出"""
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None

        if token:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_tokens WHERE token = %s", (token,))
            conn.commit()
            cursor.close()
            conn.close()

        return jsonify({"success": True, "message": "登出成功"}), 200
    except Exception as e:
        return jsonify({"error": f"登出失败：{str(e)}"}), 500


@auth_bp.route('/api/auth/profile', methods=['PUT'])
def update_profile():
    """修改个人信息"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        name = data.get('name')
        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')

        if not name:
            return jsonify({"error": "姓名不能为空"}), 400

        # 只有要改密码时才要求原密码（允许只改姓名不填密码）
        if new_password and not old_password:
            return jsonify({"error": "修改密码需要提供原密码"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        if new_password:
            # 改密码：先验证原密码
            cursor.execute("SELECT password FROM users WHERE id = %s", (current_user['id'],))
            user = cursor.fetchone()
            if not user:
                cursor.close()
                conn.close()
                return jsonify({"error": "用户不存在"}), 404
            if not verify_password(user['password'], old_password):
                cursor.close()
                conn.close()
                return jsonify({"error": "原密码错误"}), 400

            hashed_password = hash_password(new_password)
            cursor.execute(
                "UPDATE users SET name = %s, password = %s, updated_at = NOW() WHERE id = %s",
                (name, hashed_password, current_user['id'])
            )
            # 改密码后使该用户所有旧 Token 失效，防止账号被盗后攻击者 Token 仍可用
            cursor.execute("DELETE FROM user_tokens WHERE user_id = %s", (current_user['id'],))
        else:
            # 只改姓名
            cursor.execute(
                "UPDATE users SET name = %s, updated_at = NOW() WHERE id = %s",
                (name, current_user['id'])
            )
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "修改成功"}), 200
    except Exception as e:
        return jsonify({"error": f"修改失败：{str(e)}"}), 500
