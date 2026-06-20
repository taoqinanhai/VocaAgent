"""
数据库连接工具
"""
import pymysql
from config.settings import DB_CONFIG


def get_db_connection():
    """获取数据库连接（使用 DictCursor）"""
    config = DB_CONFIG.copy()
    config['cursorclass'] = pymysql.cursors.DictCursor
    return pymysql.connect(**config)
