"""
认证工具：密码哈希、Token 生成/验证、用户获取
"""
import hashlib
import secrets
import datetime
from flask import request
from utils.db import get_db_connection


def hash_password(password):
    """密码加密"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(hashed_password, password):
    """验证密码"""
    return hashlib.sha256(password.encode()).hexdigest() == hashed_password


def generate_token():
    """生成Token"""
    return secrets.token_hex(32)


def generate_expiration_time(hours=24):
    """生成过期时间"""
    return datetime.datetime.now() + datetime.timedelta(hours=hours)


def verify_token(token):
    """验证Token"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT user_id, expires_at FROM user_tokens WHERE token = %s",
            (token,)
        )
        token_data = cursor.fetchone()

        if not token_data:
            return None

        if token_data['expires_at'] < datetime.datetime.now():
            return None

        return token_data['user_id']
    except Exception as e:
        print(f"Token验证失败: {str(e)}")
        return None
    finally:
        # 异常路径也必须归还连接：连接池 blocking=True，泄漏会把池耗尽并让后续请求阻塞
        _close_quietly(cursor, conn)


def _close_quietly(cursor, conn):
    """尽力关闭游标与连接，忽略关闭过程中的异常（连接已断时 close 本身也会抛）"""
    if cursor:
        try:
            cursor.close()
        except Exception:
            pass
    if conn:
        try:
            conn.close()
        except Exception:
            pass


def get_current_user():
    """获取当前登录用户"""
    conn = None
    cursor = None
    try:
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None

        if not token:
            return None

        user_id = verify_token(token)
        if not user_id:
            return None

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()

        return user
    except Exception as e:
        print(f"获取当前用户失败: {str(e)}")
        return None
    finally:
        # 同上：异常路径不归还连接会导致连接池耗尽
        _close_quietly(cursor, conn)
