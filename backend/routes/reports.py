"""
报告路由：/api/reports/*
"""
import json
import os as _os_module
import datetime
import re
from http import HTTPStatus
from urllib.parse import quote
from io import BytesIO
from flask import Blueprint, request, jsonify, make_response, send_file
from dashscope import Application
from config.settings import API_KEY, APP_ID_C, APP_ID_D, KNOWLEDGE_BASE_IDS
from utils.db import get_db_connection
from utils.auth import get_current_user

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/api/reports/generate', methods=['POST'])
def generate_report():
    """生成学生职业发展报告"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        data = request.get_json()
        if not data:
            return jsonify({"error": "请求数据不能为空"}), 400

        student_id = data.get('student_id')
        if not student_id:
            return jsonify({"error": "学生ID不能为空"}), 400

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM students WHERE id = %s AND user_id = %s", (student_id, user_id))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({"error": "学生不存在或无权限访问"}), 404

        cursor.execute("""
            SELECT
                sjm.job_id,
                sjm.match_rank,
                sjm.overall_matching,
                j.job_name,
                j.promotion_path,
                j.transfer_path
            FROM student_job_matches sjm
            JOIN jobs j ON sjm.job_id = j.id
            WHERE sjm.student_id = %s
            ORDER BY sjm.match_rank ASC
            LIMIT 10
        """, (student_id,))
        job_matches = cursor.fetchall()

        project_experience = []
        if student.get('project_experience'):
            try:
                project_experience = json.loads(student['project_experience']) if isinstance(student['project_experience'], str) else student['project_experience']
            except:
                project_experience = []

        professional_skills = []
        if student.get('professional_skills'):
            try:
                professional_skills = json.loads(student['professional_skills']) if isinstance(student['professional_skills'], str) else student['professional_skills']
            except:
                professional_skills = []

        ability_scores = [
            {"dimension": "专业技能与证书", "score": float(student.get('professional_skills_certificates', 0))},
            {"dimension": "学习能力", "score": float(student.get('learning_ability', 0))},
            {"dimension": "创新能力", "score": float(student.get('innovation_ability', 0))},
            {"dimension": "抗压能力", "score": float(student.get('stress_resistance', 0))},
            {"dimension": "沟通能力", "score": float(student.get('communication_ability', 0))},
            {"dimension": "实习经历", "score": float(student.get('internship_experience', 0))}
        ]

        job_matches_data = []
        career_paths_data = []

        for match in job_matches:
            job_matches_data.append({
                "job_id": match['job_id'],
                "job_name": match['job_name'],
                "match_score": f"{match['overall_matching']:.0f} 分"
            })

            promotion_path = ""
            transfer_path = ""

            if match.get('promotion_path'):
                try:
                    promo_list = json.loads(match['promotion_path']) if isinstance(match['promotion_path'], str) else match['promotion_path']
                    if isinstance(promo_list, list):
                        promotion_path = "→".join(promo_list)
                    else:
                        promotion_path = str(promo_list)
                except:
                    promotion_path = str(match['promotion_path'])

            if match.get('transfer_path'):
                try:
                    transfer_list = json.loads(match['transfer_path']) if isinstance(match['transfer_path'], str) else match['transfer_path']
                    if isinstance(transfer_list, list):
                        transfer_path = "、".join(transfer_list)
                    else:
                        transfer_path = str(transfer_list)
                except:
                    transfer_path = str(match['transfer_path'])

            career_paths_data.append({
                "job_id": match['job_id'],
                "job_name": match['job_name'],
                "promotion_path": promotion_path,
                "transfer_path": transfer_path
            })

        report_date = datetime.datetime.now().strftime("%Y 年 %m 月 %d 日")

        report_content = {
            "student_name": student.get('name', ''),
            "job_direction": student.get('major', '未知方向'),
            "report_date": report_date,
            "resume_score": student.get('profile_completeness', 0),
            "competitiveness_score": student.get('competitiveness_score', 0),
            "email": student.get('email', ''),
            "phone": student.get('phone', ''),
            "education": f"{student.get('education', '')}（{student.get('school', '')} {student.get('major', '')}专业，{student.get('graduation_year', '')} 届）" if student.get('school') else student.get('education', ''),
            "skills": "、".join(professional_skills) if professional_skills else "暂无",
            "projects": project_experience if project_experience else [],
            "ability_scores": ability_scores,
            "job_matches": job_matches_data,
            "career_paths": career_paths_data,
            "match_conclusion": student.get('person_post_matching_analysis', ''),
            "career_goal": student.get('core_career_goal', ''),
            "industry_trend_analysis": student.get('industry_demand_and_trend_analysis', ''),
            "development_path": student.get('clear_career_development_path', ''),
            "action_plan": student.get('staged_growth_plan', ''),
            "evaluation_mechanism": student.get('dynamic_evaluation_mechanism', '')
        }

        cursor.execute("""
            INSERT INTO career_reports
            (student_id, user_id, report_content, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            student_id,
            user_id,
            json.dumps(report_content, ensure_ascii=False),
            datetime.datetime.now(),
            datetime.datetime.now()
        ))
        conn.commit()

        report_id = cursor.lastrowid
        report_content['id'] = report_id

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "报告生成成功",
            "data": {"id": report_id}
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"生成报告失败：{str(e)}"}), 500


@reports_bp.route('/api/reports/<int:report_id>', methods=['GET'])
def get_report(report_id):
    """获取报告详情"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cr.*, s.email as stu_email, s.phone as stu_phone,
                   s.professional_skills as stu_professional_skills, s.name as stu_name
            FROM career_reports cr
            LEFT JOIN students s ON cr.student_id = s.id
            WHERE cr.id = %s AND cr.user_id = %s
        """, (report_id, user_id))
        report = cursor.fetchone()

        if not report:
            cursor.close()
            conn.close()
            return jsonify({"error": "报告不存在或无权限访问"}), 404

        report_content = json.loads(report['report_content']) if report['report_content'] else {}
        report_content['id'] = report['id']
        report_content['created_at'] = report['created_at'].strftime("%Y-%m-%d %H:%M:%S") if report['created_at'] else ''

        # DB 兜底：旧报告 report_content 缺 email/phone/skills，从 students 表补全
        if not report_content.get('email'):
            report_content['email'] = report.get('stu_email') or ''
        if not report_content.get('phone'):
            report_content['phone'] = report.get('stu_phone') or ''
        if not report_content.get('skills'):
            skills_raw = report.get('stu_professional_skills')
            if skills_raw:
                try:
                    skills_list = json.loads(skills_raw) if isinstance(skills_raw, str) else skills_raw
                    report_content['skills'] = '、'.join(skills_list) if isinstance(skills_list, list) else str(skills_list)
                except:
                    pass
        if not report_content.get('student_name'):
            report_content['student_name'] = report.get('stu_name') or ''

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": report_content
        })

    except Exception as e:
        return jsonify({"error": f"获取报告失败：{str(e)}"}), 500


@reports_bp.route('/api/reports/student/<int:student_id>', methods=['GET'])
def get_student_reports(student_id):
    """获取学生的历史报告列表"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, major FROM students WHERE id = %s AND user_id = %s", (student_id, user_id))
        student = cursor.fetchone()

        if not student:
            cursor.close()
            conn.close()
            return jsonify({"error": "学生不存在或无权限访问"}), 404

        cursor.execute("""
            SELECT id, report_title, report_content, created_at
            FROM career_reports
            WHERE student_id = %s AND user_id = %s
            ORDER BY created_at DESC
        """, (student_id, user_id))
        reports = cursor.fetchall()

        result = []
        for report in reports:
            try:
                content = json.loads(report['report_content']) if report['report_content'] else {}
                result.append({
                    "id": report['id'],
                    "student_name": content.get('student_name') or student['name'],
                    "report_title": report['report_title'] or content.get('job_direction') or student['major'],
                    "job_direction": content.get('job_direction') or student['major'],
                    "created_at": report['created_at'].strftime("%Y-%m-%d %H:%M:%S") if report['created_at'] else ''
                })
            except:
                result.append({
                    "id": report['id'],
                    "student_name": student['name'],
                    "report_title": report['report_title'] or student['major'],
                    "job_direction": student['major'],
                    "created_at": report['created_at'].strftime("%Y-%m-%d %H:%M:%S") if report['created_at'] else ''
                })

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "data": result
        })

    except Exception as e:
        return jsonify({"error": f"获取报告历史失败：{str(e)}"}), 500


@reports_bp.route('/api/reports/<int:report_id>', methods=['DELETE'])
def delete_report(report_id):
    """删除报告"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id FROM career_reports
            WHERE id = %s AND user_id = %s
        """, (report_id, user_id))
        report = cursor.fetchone()

        if not report:
            cursor.close()
            conn.close()
            return jsonify({"error": "报告不存在或无权限访问"}), 404

        cursor.execute("""
            DELETE FROM career_reports
            WHERE id = %s AND user_id = %s
        """, (report_id, user_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "报告删除成功"})
    except Exception as e:
        return jsonify({"error": f"删除报告失败：{str(e)}"}), 500


@reports_bp.route('/api/reports/<int:report_id>/export', methods=['POST'])
def export_report(report_id):
    """导出报告"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT report_content FROM career_reports
            WHERE id = %s AND user_id = %s
        """, (report_id, user_id))
        report = cursor.fetchone()

        if not report:
            cursor.close()
            conn.close()
            return jsonify({"error": "报告不存在或无权限访问"}), 404

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": "报告导出成功",
            "download_url": f"/api/reports/{report_id}/download"
        })

    except Exception as e:
        return jsonify({"error": f"导出报告失败：{str(e)}"}), 500


@reports_bp.route('/api/reports/<int:report_id>/download', methods=['GET'])
def download_report(report_id):
    """下载报告为HTML"""
    print(f"\n=== 处理下载请求 ===")
    print(f"报告ID: {report_id}")

    try:
        print("1. 验证用户登录")
        current_user = get_current_user()
        print(f"当前用户: {current_user}")

        if not current_user:
            print("用户未登录")
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']
        print(f"用户ID: {user_id}")

        print("2. 连接数据库")
        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            print("数据库连接成功")
            cursor = conn.cursor()

            print("3. 查询报告数据")
            cursor.execute("""
                SELECT cr.report_html, cr.report_title, cr.report_content,
                       s.name as student_name
                FROM career_reports cr
                LEFT JOIN students s ON cr.student_id = s.id
                WHERE cr.id = %s AND cr.user_id = %s
            """, (report_id, user_id))

            report = cursor.fetchone()
            print(f"查询结果: report_id={report_id}")

            if not report:
                print("报告不存在或无权限访问")
                return jsonify({"error": "报告不存在或无权限访问"}), 404

            report_html = report.get('report_html') or ''
            report_title = report.get('report_title') or '职业发展报告'
            student_name = report.get('student_name') or '未知'

            # 从 report_content 取补充信息
            try:
                report_content = json.loads(report['report_content']) if report['report_content'] else {}
            except Exception:
                report_content = {}
            report_date = report_content.get('report_date', '') if isinstance(report_content, dict) else ''

            # 如果 report_html 为空（旧报告），用 report_content 兜底
            if not report_html.strip():
                report_html = _build_legacy_report_html(report_content, student_name)

            print("4. 构建报告HTML")
            html_content = _wrap_report_html(report_html, report_title, student_name, report_date)

            print("5. 生成响应")
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html; charset=utf-8'
            safe_name = student_name.replace(' ', '_')
            filename = f"{safe_name}_{report_title}.html"
            response.headers['Content-Disposition'] = f"attachment; filename*=UTF-8''{quote(filename)}"
            print("响应生成成功")
            return response

        finally:
            if cursor:
                cursor.close()
                print("数据库游标已关闭")
            if conn:
                conn.close()
                print("数据库连接已关闭")

    except Exception as e:
        print(f"\n=== 下载报告失败 ===")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"下载报告失败：{str(e)}"}), 500


@reports_bp.route('/api/reports/<int:report_id>/download/pdf', methods=['GET'])
def download_report_pdf(report_id):
    """下载报告为PDF（服务端生成真实PDF文件）"""
    try:
        token = request.args.get('token', '')
        current_user = get_current_user() if not token else _get_user_by_token(token)
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT cr.report_title, cr.report_content, s.name as student_name,
                   s.email as stu_email, s.phone as stu_phone,
                   s.professional_skills as stu_professional_skills,
                   s.education as stu_education
            FROM career_reports cr
            LEFT JOIN students s ON cr.student_id = s.id
            WHERE cr.id = %s AND cr.user_id = %s
        """, (report_id, user_id))

        report = cursor.fetchone()
        cursor.close()
        conn.close()

        if not report:
            return jsonify({"error": "报告不存在或无权限访问"}), 404

        report_title = report.get('report_title') or '职业发展报告'
        student_name = report.get('student_name') or '未知'
        try:
            content = json.loads(report['report_content']) if report['report_content'] else {}
        except Exception:
            content = {}
        if not isinstance(content, dict):
            content = {}

        # DB 兜底：旧报告 report_content 可能缺基础信息字段，从 students 表补全
        if not content.get('email'):
            content['email'] = report.get('stu_email') or ''
        if not content.get('phone'):
            content['phone'] = report.get('stu_phone') or ''
        if not content.get('education'):
            content['education'] = report.get('stu_education') or ''
        if not content.get('skills'):
            skills_raw = report.get('stu_professional_skills')
            if skills_raw:
                try:
                    skills_list = json.loads(skills_raw) if isinstance(skills_raw, str) else skills_raw
                    content['skills'] = '、'.join(skills_list) if isinstance(skills_list, list) else str(skills_list)
                except:
                    pass
        if not content.get('student_name'):
            content['student_name'] = student_name

        # 生成 PDF
        pdf_bytes = _generate_pdf(report_title, student_name, content)
        safe_name = student_name.replace(' ', '_')

        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{safe_name}_{report_title}.pdf"
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"下载PDF报告失败：{str(e)}"}), 500


def _generate_pdf(title, student_name, content):
    """使用 fpdf 生成专业排版的 PDF"""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ---- 加载中文字体 ----
    font_name = 'Helvetica'
    font_paths = [
        'C:/Windows/Fonts/simhei.ttf',
        'C:/Windows/Fonts/simkai.ttf',
        'C:/Windows/Fonts/simfang.ttf',
        'C:/Windows/Fonts/msyh.ttf',
        'C:/Windows/Fonts/STXIHEI.TTF',
    ]
    for fp in font_paths:
        if _os_module.path.exists(fp):
            try:
                pdf.add_font('CJK', '', fp, uni=True)
                pdf.add_font('CJK', 'B', fp, uni=True)
                font_name = 'CJK'
                break
            except Exception:
                continue

    # ---- 封面 ----
    pdf.set_fill_color(30, 58, 95)   # 深蓝 #1e3a5f
    pdf.rect(0, 0, 210, 297, 'F')
    pdf.set_y(60)

    pdf.set_font(font_name, 'B', 28)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 14, title, ln=True, align='C')

    pdf.set_font(font_name, '', 14)
    pdf.set_text_color(200, 210, 230)
    pdf.ln(8)
    pdf.cell(0, 10, f'{student_name} · 职业发展规划报告', ln=True, align='C')

    # 金色分割线
    pdf.set_draw_color(183, 147, 90)
    pdf.set_line_width(0.6)
    pdf.ln(10)
    x_center = 80
    pdf.line(x_center, pdf.get_y(), x_center + 50, pdf.get_y())
    pdf.ln(14)

    pdf.set_font(font_name, '', 12)
    pdf.set_text_color(180, 190, 210)
    pdf.cell(0, 8, f'报告对象：{student_name}', ln=True, align='C')
    report_date = content.get('report_date', '—')
    pdf.cell(0, 8, f'报告日期：{report_date}', ln=True, align='C')
    pdf.cell(0, 8, '生成引擎：VocaAgent AI', ln=True, align='C')

    # ---- 正文 ----
    pdf.add_page()
    pdf.set_text_color(40, 44, 52)

    def _section_header(text):
        pdf.ln(4)
        pdf.set_fill_color(30, 58, 95)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(font_name, 'B', 13)
        pdf.cell(0, 9, f'  {text}', ln=True, fill=True)
        pdf.ln(3)
        pdf.set_text_color(40, 44, 52)

    def _body_text(text, size=10):
        if not text or text == '无数据':
            return
        pdf.set_font(font_name, '', size)
        pdf.set_text_color(55, 65, 81)
        # 清理 HTML 标签
        import re
        clean = re.sub(r'<[^>]+>', '', str(text))
        clean = clean.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # 去掉每行首尾空格，合并多余空行
        lines = [line.strip() for line in clean.splitlines()]
        clean = '\n'.join(line for line in lines if line)
        pdf.multi_cell(0, 6, clean)
        pdf.ln(2)

    def _sub_header(text):
        pdf.set_font(font_name, 'B', 11)
        pdf.set_text_color(44, 82, 130)
        pdf.cell(0, 7, text, ln=True)
        pdf.ln(1)

    def _draw_line():
        pdf.set_draw_color(210, 218, 232)
        pdf.set_line_width(0.3)
        y = pdf.get_y()
        pdf.line(12, y, 198, y)
        pdf.ln(4)

    # ---- Section 1: 基本信息 ----
    _section_header('一、个人基础信息与能力画像')

    # 基础信息项
    basic_items = [
        ('姓名', student_name),
        ('邮箱', content.get('email', '')),
        ('电话', content.get('phone', '')),
        ('学历', content.get('education', '')),
    ]
    has_basic = any(v for _, v in basic_items)
    if has_basic:
        _sub_header('基本信息')
        pdf.set_font(font_name, '', 10)
        for label, val in basic_items:
            if val:
                pdf.cell(0, 6, f'  {label}：{val}', ln=True)
        pdf.ln(3)

    skills = content.get('skills', '')
    if skills:
        _sub_header('专业技能')
        _body_text(skills)

    education = content.get('education', '')
    ability_scores = content.get('ability_scores', [])
    if ability_scores:
        _sub_header('能力维度评分')
        pdf.set_font(font_name, '', 10)
        col_w = 88
        pdf.set_fill_color(237, 242, 247)
        pdf.set_text_color(40, 44, 52)
        pdf.cell(col_w, 7, '  维度', border=1, fill=True)
        pdf.cell(col_w, 7, '  得分 (满分 10)', border=1, fill=True, ln=True)
        for item in ability_scores:
            if isinstance(item, dict):
                dim = item.get('dimension', '')
                score = item.get('score', '')
                pdf.cell(col_w, 7, f'  {dim}', border=1)
                pdf.cell(col_w, 7, f'  {score}', border=1, ln=True)
        pdf.ln(4)

    # ---- Section 2: 岗位匹配 ----
    _section_header('二、岗位匹配结果')
    job_matches = content.get('job_matches', [])
    if job_matches:
        pdf.set_font(font_name, '', 9)
        col_w = 30
        pdf.set_fill_color(237, 242, 247)
        pdf.cell(col_w, 7, '  排名', border=1, fill=True)
        pdf.cell(80, 7, '  岗位名称', border=1, fill=True)
        pdf.cell(col_w + 5, 7, '  匹配分数', border=1, fill=True, ln=True)
        for i, jm in enumerate(job_matches[:10], 1):
            if isinstance(jm, dict):
                pdf.cell(col_w, 6, f'  #{i}', border=1)
                pdf.cell(80, 6, f'  {jm.get("job_name", "")}', border=1)
                pdf.cell(col_w + 5, 6, f'  {jm.get("match_score", "")}', border=1, ln=True)
        pdf.ln(4)

    # ---- Section 3-8: 分析板块 ----
    sections = [
        ('三、人岗匹配分析', content.get('match_conclusion', '')),
        ('四、核心职业目标', content.get('career_goal', '')),
        ('五、行业需求与趋势分析', content.get('industry_trend_analysis', '')),
        ('六、发展路径', content.get('development_path', '')),
        ('七、分阶段成长计划', content.get('action_plan', '')),
        ('八、动态评估机制', content.get('evaluation_mechanism', '')),
    ]
    for title, text in sections:
        _section_header(title)
        _body_text(text)
        _draw_line()

    # ---- 页脚 ----
    pdf.ln(6)
    pdf.set_font(font_name, '', 8)
    pdf.set_text_color(150, 155, 165)
    pdf.cell(0, 6, 'VocaAgent · AI 职业规划智能体', ln=True, align='C')
    pdf.cell(0, 5, '本报告由人工智能生成，仅供参考', ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1')


@reports_bp.route('/api/reports/<int:report_id>/polish', methods=['POST'])
def polish_report(report_id):
    """智能润色报告（使用 Agent D 报告专家）—— 润色后生成新报告行，原标题加 [润色] 后缀"""
    try:
        current_user = get_current_user()
        if not current_user:
            return jsonify({"error": "请先登录"}), 401

        user_id = current_user['id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM career_reports
            WHERE id = %s AND user_id = %s
        """, (report_id, user_id))
        old_report = cursor.fetchone()

        if not old_report:
            cursor.close()
            conn.close()
            return jsonify({"error": "报告不存在或无权限访问"}), 404

        content = json.loads(old_report['report_content']) if old_report['report_content'] else {}

        prompt = f"""请对以下职业发展报告进行润色优化，使内容更加专业、流畅、有吸引力：

职业目标：{content.get('career_goal', '')}

发展路径：{content.get('development_path', '')}

行动计划：{content.get('action_plan', '')}

人岗匹配分析：{content.get('match_conclusion', '')}

请保持原有结构和关键信息，优化语言表达，使其更加专业和有说服力。直接返回润色后的内容，使用以下JSON格式：

{{
    "career_goal": "润色后的职业目标",
    "development_path": "润色后的发展路径",
    "action_plan": "润色后的行动计划",
    "match_conclusion": "润色后的人岗匹配分析"
}}"""

        messages = [{'role': 'user', 'content': prompt}]

        call_params = {
            'api_key': API_KEY,
            'app_id': APP_ID_D,  # ★ 使用 Agent D（报告生成专家），而非 Agent C
            'messages': messages,
            'stream': False,
            'max_tokens': 6000   # 润色 4 个字段，需要充足 token
        }

        if KNOWLEDGE_BASE_IDS:
            call_params['rag_options'] = {'pipeline_ids': KNOWLEDGE_BASE_IDS}

        response = Application.call(**call_params)

        if response.status_code == HTTPStatus.OK:
            ai_response = response.output.text

            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}')
            if json_start != -1 and json_end != -1 and json_start < json_end:
                try:
                    polished_content = json.loads(ai_response[json_start:json_end+1])

                    content['career_goal'] = polished_content.get('career_goal', content.get('career_goal', ''))
                    content['development_path'] = polished_content.get('development_path', content.get('development_path', ''))
                    content['action_plan'] = polished_content.get('action_plan', content.get('action_plan', ''))
                    content['match_conclusion'] = polished_content.get('match_conclusion', content.get('match_conclusion', ''))

                    # ★ 生成润色版标题：原标题去掉已有的 [润色] 后缀，再加一次
                    old_title = old_report['report_title'] or ''
                    base_title = old_title.replace(' [润色]', '').replace('[润色]', '').strip()
                    new_title = f"{base_title} [润色]"

                    # ★ INSERT 新行而非 UPDATE：保留原始报告，润色版作为新记录
                    now = datetime.datetime.now()
                    cursor.execute("""
                        INSERT INTO career_reports
                        (student_id, target_job_id, report_title, report_content, report_html, user_id, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        old_report['student_id'],
                        old_report['target_job_id'],
                        new_title,
                        json.dumps(content, ensure_ascii=False),
                        old_report['report_html'] or '',  # 复用原 HTML（润色文字在 report_content 中）
                        user_id,
                        now,
                        now
                    ))
                    conn.commit()
                    new_report_id = cursor.lastrowid

                    cursor.close()
                    conn.close()

                    return jsonify({
                        "success": True,
                        "message": "报告润色完成，已保存为新版本",
                        "new_report_id": new_report_id,
                        "new_title": new_title
                    })
                except json.JSONDecodeError as e:
                    cursor.close()
                    conn.close()
                    return jsonify({"error": f"AI 返回内容解析失败：{str(e)}"}), 500
            else:
                cursor.close()
                conn.close()
                return jsonify({"error": "AI 未返回有效的 JSON 格式内容"}), 500
        else:
            cursor.close()
            conn.close()
            return jsonify({"error": f"AI 调用失败：{response.message} (code={response.status_code})"}), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"润色报告失败：{str(e)}"}), 500


# ============================================================
# 认证 & HTML 渲染辅助函数
# ============================================================

def _get_user_by_token(token):
    """通过 token 字符串获取用户（用于 ?token= 参数认证）"""
    from utils.auth import verify_token
    user_id = verify_token(token)
    if not user_id:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def _wrap_report_html(body_html, title, student_name, report_date, for_print=False):
    """将报告 body HTML 包装为完整的 HTML 文档，统一视觉风格"""
    print_script = '<script>window.onload=function(){window.print();}</script>' if for_print else ''
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{student_name} - {title}</title>
<style>
  :root {{
    --primary: #1e3a5f;
    --primary-light: #2c5282;
    --accent: #3182ce;
    --gold: #b7935a;
    --gold-light: #d4a96a;
    --bg: #f8f7f4;
    --card-bg: #ffffff;
    --text: #2d3748;
    --text-secondary: #4a5568;
    --text-muted: #718096;
    --border: #e2e8f0;
    --shadow: 0 2px 16px rgba(0,0,0,0.06);
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Noto Sans SC", -apple-system, BlinkMacSystemFont, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.85;
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
  }}

  /* ====== 封面 ====== */
  .report-cover {{
    background: linear-gradient(160deg, #0f1a2e 0%, #1a3650 30%, #1e3a5f 60%, #1a2a3a 100%);
    color: #fff;
    padding: 64px 48px 56px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }}

  .report-cover::before {{
    content: '';
    position: absolute;
    top: -40%;
    right: -20%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(183,147,90,0.15) 0%, transparent 70%);
    border-radius: 50%;
  }}

  .report-cover::after {{
    content: '';
    position: absolute;
    bottom: -30%;
    left: -15%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(49,130,206,0.12) 0%, transparent 70%);
    border-radius: 50%;
  }}

  .cover-badge {{
    display: inline-block;
    border: 1px solid rgba(183,147,90,0.5);
    color: var(--gold-light);
    padding: 6px 24px;
    border-radius: 20px;
    font-size: 14px;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 28px;
    position: relative;
    z-index: 1;
  }}

  .cover-title {{
    font-size: 36px;
    font-weight: 700;
    letter-spacing: 2px;
    margin-bottom: 16px;
    position: relative;
    z-index: 1;
    background: linear-gradient(180deg, #fff 0%, #c5d3e8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }}

  .cover-subtitle {{
    font-size: 18px;
    color: rgba(255,255,255,0.65);
    font-weight: 400;
    position: relative;
    z-index: 1;
    margin-bottom: 36px;
  }}

  .cover-divider {{
    width: 80px;
    height: 2px;
    background: var(--gold);
    margin: 0 auto 32px;
    position: relative;
    z-index: 1;
  }}

  .cover-meta {{
    display: flex;
    justify-content: center;
    gap: 48px;
    font-size: 15px;
    color: rgba(255,255,255,0.7);
    position: relative;
    z-index: 1;
  }}

  .cover-meta-item span {{
    display: block;
    font-size: 12px;
    color: rgba(255,255,255,0.4);
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-bottom: 4px;
  }}

  /* ====== 正文容器 ====== */
  .report-body {{
    max-width: 860px;
    margin: 0 auto;
    padding: 48px 40px 64px;
  }}

  /* ====== Agent D 输出样式增强 ====== */
  .career-report {{ }}
  .career-report .report-section {{
    margin-bottom: 40px;
    padding: 32px;
    background: var(--card-bg);
    border-radius: 12px;
    box-shadow: var(--shadow);
    border: 1px solid var(--border);
  }}

  .career-report .report-section h2 {{
    font-size: 22px;
    color: var(--primary);
    border-left: 4px solid var(--accent);
    padding-left: 14px;
    margin-bottom: 20px;
    font-weight: 700;
  }}

  .career-report .sub-section {{
    margin-bottom: 28px;
  }}

  .career-report .sub-section h3 {{
    font-size: 18px;
    color: var(--primary-light);
    margin-bottom: 12px;
    font-weight: 600;
  }}

  .career-report .sub-section h4 {{
    font-size: 16px;
    color: #2d3748;
    margin: 16px 0 8px;
    font-weight: 600;
  }}

  .career-report p {{
    margin-bottom: 14px;
    color: var(--text-secondary);
    text-align: justify;
  }}

  .career-report ul, .career-report ol {{
    margin: 10px 0 16px 20px;
    color: var(--text-secondary);
  }}

  .career-report li {{
    margin-bottom: 6px;
    line-height: 1.8;
  }}

  /* 路径时间线 */
  .career-report .path-timeline {{
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-top: 16px;
  }}

  .career-report .path-item {{
    padding: 18px 20px;
    background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
    border-radius: 10px;
    border-left: 3px solid var(--accent);
  }}

  .career-report .path-item h4 {{
    color: var(--primary);
    margin-top: 0;
    font-size: 15px;
  }}

  /* 行动计划阶段 */
  .career-report .plan-phase {{
    padding: 16px 20px;
    margin-bottom: 14px;
    background: #fafbfc;
    border-radius: 8px;
    border: 1px solid var(--border);
  }}

  .career-report .plan-phase h4 {{
    color: var(--accent);
    margin-top: 0;
    font-size: 15px;
  }}

  /* 表格 */
  .career-report table {{
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 14px;
  }}

  .career-report th {{
    background: #edf2f7;
    color: var(--primary);
    font-weight: 600;
    padding: 12px 14px;
    text-align: left;
    border-bottom: 2px solid var(--border);
  }}

  .career-report td {{
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    color: var(--text-secondary);
  }}

  .career-report tr:nth-child(even) td {{
    background: #f7fafc;
  }}

  /* ====== 页脚 ====== */
  .report-footer {{
    text-align: center;
    padding: 32px 40px;
    border-top: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 13px;
  }}

  .report-footer .footer-brand {{
    font-weight: 600;
    color: var(--primary);
    letter-spacing: 1px;
  }}

  /* ====== 打印样式 ====== */
  @media print {{
    @page {{
      size: A4;
      margin: 0;
    }}

    body {{
      background: #fff;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}

    .report-cover {{
      background: #1e3a5f !important;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
      page-break-after: always;
    }}

    .career-report .report-section {{
      box-shadow: none;
      border: 1px solid #e2e8f0;
      page-break-inside: avoid;
    }}

    .career-report .path-item,
    .career-report .plan-phase {{
      page-break-inside: avoid;
    }}

    .report-footer {{
      margin-top: 32px;
    }}
  }}

  @media (max-width: 768px) {{
    .report-body {{
      padding: 24px 16px;
    }}
    .cover-title {{
      font-size: 26px;
    }}
    .cover-meta {{
      flex-direction: column;
      gap: 12px;
    }}
    .career-report .report-section {{
      padding: 20px;
    }}
  }}
</style>
</head>
<body>
  <div class="report-cover">
    <div class="cover-badge">CAREER REPORT</div>
    <h1 class="cover-title">{title}</h1>
    <p class="cover-subtitle">{student_name} · 职业发展规划报告</p>
    <div class="cover-divider"></div>
    <div class="cover-meta">
      <div class="cover-meta-item"><span>报告对象</span>{student_name}</div>
      <div class="cover-meta-item"><span>报告日期</span>{report_date or '—'}</div>
      <div class="cover-meta-item"><span>生成引擎</span>VocaAgent AI</div>
    </div>
  </div>

  <div class="report-body">
    {body_html}
  </div>

  <div class="report-footer">
    <div class="footer-brand">VocaAgent</div>
    <div>AI 职业规划智能体 · 本报告由人工智能生成，仅供参考</div>
  </div>
  {print_script}
</body>
</html>"""


def _build_legacy_report_html(content, student_name):
    """旧报告（无 report_html）兜底：用 report_content 字段拼出基础 HTML"""
    if not isinstance(content, dict):
        return f'<p>{student_name} 的职业发展报告</p>'

    parts = []

    # 基础信息
    education = content.get('education', '')
    skills = content.get('skills', '')
    if education or skills:
        parts.append('<section class="report-section"><h2>个人基础信息</h2>')
        if education:
            parts.append(f'<p><strong>学历：</strong>{education}</p>')
        if skills:
            parts.append(f'<p><strong>专业技能：</strong>{skills}</p>')
        parts.append('</section>')

    # 能力评分
    ability_scores = content.get('ability_scores', [])
    if ability_scores:
        parts.append('<section class="report-section"><h2>能力维度评分</h2><table>')
        parts.append('<tr><th>维度</th><th>得分</th></tr>')
        for item in ability_scores:
            if isinstance(item, dict):
                parts.append(f'<tr><td>{item.get("dimension","")}</td><td>{item.get("score","")}</td></tr>')
        parts.append('</table></section>')

    # 岗位匹配
    job_matches = content.get('job_matches', [])
    if job_matches:
        parts.append('<section class="report-section"><h2>岗位匹配结果</h2><table>')
        parts.append('<tr><th>岗位名称</th><th>匹配分数</th></tr>')
        for j in job_matches:
            if isinstance(j, dict):
                parts.append(f'<tr><td>{j.get("job_name","")}</td><td>{j.get("match_score","")}</td></tr>')
        parts.append('</table></section>')

    # 四个分析板块
    sections = [
        ('match_conclusion', '人岗匹配分析'),
        ('career_goal', '核心职业目标'),
        ('industry_trend_analysis', '行业需求与趋势分析'),
        ('development_path', '发展路径'),
        ('action_plan', '分阶段成长计划'),
        ('evaluation_mechanism', '动态评估机制'),
    ]
    for key, title in sections:
        text = content.get(key, '')
        if text:
            parts.append(f'<section class="report-section"><h2>{title}</h2><p>{text}</p></section>')

    return '\n'.join(parts) if parts else f'<p>{student_name} 的职业发展报告（暂无详细内容）</p>'
