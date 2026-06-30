"""
VocaAgent-2.0 主入口
AI 职业规划智能体 - Flask 后端应用
"""
from flask import Flask
from flask_cors import CORS
from config.settings import UPLOAD_FOLDER, MAX_CONTENT_LENGTH
from routes import register_routes

app = Flask(__name__)
CORS(app)

# 配置文件上传
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 注册所有路由 Blueprint
register_routes(app)

if __name__ == '__main__':
    from utils.file_processor import is_ocr_available
    ocr_status = "可用" if is_ocr_available() else "不可用（仅支持文字型 PDF）"
    print(f"[app] OCR 状态: {ocr_status}")
    app.run(debug=True, host='0.0.0.0', port=5000)
