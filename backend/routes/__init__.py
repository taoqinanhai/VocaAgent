"""
路由注册中心
将各模块 Blueprint 注册到 Flask app
"""
from .chat import chat_bp
from .auth import auth_bp
from .students import students_bp
from .jobs import jobs_bp
from .resumes import resumes_bp
from .reports import reports_bp
from .admin import admin_bp
from .agent import agent_bp


def register_routes(app):
    """将所有 Blueprint 注册到 Flask 应用"""
    app.register_blueprint(chat_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(resumes_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(agent_bp)
