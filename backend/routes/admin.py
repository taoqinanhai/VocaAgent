"""
管理员路由：/api/admin/*
"""
from flask import Blueprint, request, jsonify
from utils.db import get_db_connection
from utils.auth import get_current_user, hash_password

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/admin/users', methods=['GET'])
def get_users():
    """获取用户列表"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "未授权访问"}), 401

        if current_user['role'] != 'admin':
            return jsonify({"error": "权限不足"}), 403

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, username, email, name, role, is_active, created_at FROM users")
        users = cursor.fetchall()

        result = []
        for user in users:
            result.append({
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'is_active': bool(user['is_active']),
                'created_at': user['created_at'].isoformat() if user['created_at'] else None
            })

        cursor.close()
        conn.close()

        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        return jsonify({"error": f"获取用户列表失败：{str(e)}"}), 500


@admin_bp.route('/api/admin/users', methods=['POST'])
def create_user():
    """创建用户"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "未授权访问"}), 401

        if current_user['role'] != 'admin':
            return jsonify({"error": "权限不足"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        name = data.get('name')
        role = data.get('role', 'user')

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
            "INSERT INTO users (username, password, email, name, role, is_active) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, hashed_password, email, name, role, True)
        )
        conn.commit()

        user_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "用户创建成功", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"error": f"创建用户失败：{str(e)}"}), 500


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """更新用户"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "未授权访问"}), 401

        if current_user['role'] != 'admin':
            return jsonify({"error": "权限不足"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        email = data.get('email')
        name = data.get('name')
        role = data.get('role')
        is_active = data.get('is_active')

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "用户不存在"}), 404

        cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (email, user_id))
        if cursor.fetchone():
            return jsonify({"error": "邮箱已被其他用户使用"}), 400

        update_data = []
        update_fields = []

        if email:
            update_fields.append("email = %s")
            update_data.append(email)
        if name is not None:
            update_fields.append("name = %s")
            update_data.append(name)
        if role:
            update_fields.append("role = %s")
            update_data.append(role)
        if is_active is not None:
            update_fields.append("is_active = %s")
            update_data.append(int(is_active))

        if update_fields:
            update_data.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, update_data)
            conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "用户更新成功"}), 200
    except Exception as e:
        return jsonify({"error": f"更新用户失败：{str(e)}"}), 500


@admin_bp.route('/api/admin/users/<int:user_id>/password', methods=['PUT'])
def reset_password(user_id):
    """重置用户密码"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "未授权访问"}), 401

        if current_user['role'] != 'admin':
            return jsonify({"error": "权限不足"}), 403

        data = request.get_json(silent=True) or {}
        new_password = data.get('new_password')
        if not new_password:
            return jsonify({"error": "新密码不能为空"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "用户不存在"}), 404

        hashed_password = hash_password(new_password)

        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, user_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "密码重置成功"}), 200
    except Exception as e:
        return jsonify({"error": f"重置密码失败：{str(e)}"}), 500


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """删除用户"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "未授权访问"}), 401

        if current_user['role'] != 'admin':
            return jsonify({"error": "权限不足"}), 403

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"error": "用户不存在"}), 404

        cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user and user['role'] == 'admin':
            return jsonify({"error": "不能删除管理员用户"}), 403

        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "用户删除成功"}), 200
    except Exception as e:
        return jsonify({"error": f"删除用户失败：{str(e)}"}), 500
