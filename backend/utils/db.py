"""
数据库连接工具（带连接池，避免每次请求新建连接导致泄露/耗尽）
"""
import pymysql
from config.settings import DB_CONFIG

# 优先使用 DBUtils 连接池；未安装时回退到每次新建连接
try:
    from dbutils.pooled_db import PooledDB
except ImportError:
    PooledDB = None

# 注意：PooledDB 在构造时就会建立 mincached 条连接，因此这里必须兜住所有异常，
# 不能只兜 ImportError —— MySQL 未启动 / 密码错时若让异常冒出去，
# utils.db 导入失败会导致整个 Flask 应用起不来（旧行为是能启动、请求时才报错）。
_POOL = None
if PooledDB is None:
    print("[db] 未安装 DBUtils，使用每次新建连接（pip install DBUtils 可启用连接池）")
else:
    try:
        _POOL = PooledDB(
            creator=pymysql,
            maxconnections=20,
            mincached=2,
            maxcached=10,
            blocking=True,
            ping=1,
            **DB_CONFIG,
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as e:
        # 回退到每次新建连接：应用照常启动，请求时再报具体的连接错误
        print(f"[db] 连接池初始化失败，已回退为每次新建连接：{e}")
        print("[db] （MySQL 恢复后需重启后端才会重新启用连接池）")


def get_db_connection():
    """获取数据库连接（优先从连接池取，DictCursor）"""
    if _POOL is not None:
        return _POOL.connection()
    config = DB_CONFIG.copy()
    config['cursorclass'] = pymysql.cursors.DictCursor
    return pymysql.connect(**config)
