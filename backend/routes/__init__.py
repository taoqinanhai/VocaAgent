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

# Agent Pipeline：按 Agent 拆分为 5 个独立 Blueprint
from .agent_a import agent_a_bp
from .agent_b import agent_b_bp
from .agent_c import agent_c_bp
from .agent_d import agent_d_bp
from .agent_e import agent_e_bp


def register_routes(app):
    """将所有 Blueprint 注册到 Flask 应用"""
    app.register_blueprint(chat_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(resumes_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)

    # Agent Pipeline（5 个独立 Blueprint，URL 路径不变）
    app.register_blueprint(agent_a_bp)
    app.register_blueprint(agent_b_bp)
    app.register_blueprint(agent_c_bp)
    app.register_blueprint(agent_d_bp)
    app.register_blueprint(agent_e_bp)
