"""
应用配置中心
统一管理数据库连接、API 密钥、文件上传等所有配置项
"""
import os
from dotenv import load_dotenv

# 加载环境变量
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

# ==================== 数据库配置（从 .env 读取）====================
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'vocaagent'),
    'charset': 'utf8mb4',
}


# ==================== 文件上传配置 ====================
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'jpg', 'jpeg', 'png'}
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20MB

# 确保上传文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==================== 统一 API Key（5 个应用共用）====================
API_KEY = os.getenv('API_KEY')

# ==================== Agent A：简历解析 ====================
APP_ID_A = os.getenv('APP_ID_A')

# ==================== Agent B：岗位匹配 ====================
APP_ID_B = os.getenv('APP_ID_B')

# ==================== Agent C：岗位画像（按需触发）====================
APP_ID_C = os.getenv('APP_ID_C')

# ==================== Agent D：报告生成 ====================
APP_ID_D = os.getenv('APP_ID_D')

# ==================== Agent E：虚拟行业大佬 1v1 访谈 ====================
APP_ID_E = os.getenv('APP_ID_E')

# ==================== 客服智能体（暂时保留）====================
API_KEY1 = os.getenv('API_KEY1')
APP_ID1 = os.getenv('APP_ID1')

# ==================== RAG 知识库配置 ====================
KNOWLEDGE_BASE_IDS_STR = os.getenv('KNOWLEDGE_BASE_IDS', '')
KNOWLEDGE_BASE_IDS = [id.strip() for id in KNOWLEDGE_BASE_IDS_STR.split(',') if id.strip()]

# ==================== DashScope 私网端点（可选）====================
DASHSCOPE_BASE_URL = os.getenv('DASHSCOPE_BASE_URL', '')

if DASHSCOPE_BASE_URL:
    os.environ['DASHSCOPE_HTTP_BASE_URL'] = DASHSCOPE_BASE_URL
    print(f"使用私网终端节点：{DASHSCOPE_BASE_URL}")

# ==================== 启动校验：必要配置缺一不可 ====================
MISSING = []
if not DB_CONFIG['password']:
    MISSING.append("DB_PASSWORD  (数据库密码)")
if not API_KEY:
    MISSING.append("API_KEY      (百炼 API 密钥)")
if not APP_ID_A:
    MISSING.append("APP_ID_A     (Agent A：简历解析)")
if not APP_ID_B:
    MISSING.append("APP_ID_B     (Agent B：岗位匹配)")
if not APP_ID_C:
    MISSING.append("APP_ID_C     (Agent C：岗位画像)")
if not APP_ID_D:
    MISSING.append("APP_ID_D     (Agent D：报告生成)")
if not APP_ID_E:
    MISSING.append("APP_ID_E     (Agent E：虚拟行业大佬访谈)")

if MISSING:
    print("\n" + "=" * 60)
    print("  [ERROR] 缺少必要配置，应用无法启动")
    print("=" * 60)
    print("  请在 backend/.env 中设置以下环境变量：\n")
    for item in MISSING:
        print(f"    {item}")
    print("\n  示例：")
    print("    DB_PASSWORD=你的数据库密码")
    print("    API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print("    APP_ID_A=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    print("=" * 60 + "\n")
    raise RuntimeError(f"缺少 {len(MISSING)} 项必要配置，详见上方输出")
