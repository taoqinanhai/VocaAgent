"""
VocaAgent-2.0 数据库一键初始化脚本
在一台新电脑上只需执行：python init_database.py
即可创建与现有数据库完全相同的表和字段结构
"""
import pandas as pd
import pymysql
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from config.settings import DB_CONFIG


def create_tables():
    """创建所有表（与生产数据库完全一致）"""
    conn = pymysql.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        charset=DB_CONFIG['charset']
    )
    cursor = conn.cursor()

    # 创建数据库
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} "
                   "DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci")
    print(f"[OK] 数据库 {DB_CONFIG['database']} 已就绪")

    cursor.execute(f"USE {DB_CONFIG['database']}")

    # ===================== users =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            email VARCHAR(200) NOT NULL UNIQUE,
            name VARCHAR(100),
            role VARCHAR(20) NOT NULL DEFAULT 'user',
            is_active TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] users")

    # ===================== user_tokens =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_tokens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            token VARCHAR(255) NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] user_tokens")

    # ===================== students =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            student_id VARCHAR(50),
            name VARCHAR(100),
            email VARCHAR(200),
            phone VARCHAR(20),
            education VARCHAR(50),
            school VARCHAR(200),
            major VARCHAR(200),
            graduation_year INT,
            professional_skills JSON,
            certificates JSON,
            professional_skills_certificates FLOAT,
            innovation_ability FLOAT,
            learning_ability FLOAT,
            stress_resistance FLOAT,
            communication_ability FLOAT,
            internship_experience FLOAT,
            project_experience JSON,
            profile_completeness FLOAT,
            competitiveness_score FLOAT,
            resume_text TEXT,
            resume_url VARCHAR(500),
            internship_experience_detail TEXT,
            person_post_matching_analysis TEXT,
            core_career_goal TEXT,
            industry_demand_and_trend_analysis TEXT,
            clear_career_development_path TEXT,
            staged_growth_plan TEXT,
            dynamic_evaluation_mechanism TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] students")

    # ===================== jobs =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_name VARCHAR(255) NOT NULL,
            work_address VARCHAR(255) NOT NULL,
            salary_range VARCHAR(100) NOT NULL,
            company_name VARCHAR(255) NOT NULL,
            industry VARCHAR(100) NOT NULL,
            company_size VARCHAR(100),
            company_type VARCHAR(100),
            job_code VARCHAR(100),
            job_description TEXT,
            promotion_path TEXT,
            transfer_path TEXT,
            core_highlight TEXT,
            professional_skills_certificates INT DEFAULT 0,
            innovation_ability INT DEFAULT 0,
            learning_ability INT DEFAULT 0,
            stress_resistance INT DEFAULT 0,
            communication_ability INT DEFAULT 0,
            internship_experience INT DEFAULT 0,
            update_date VARCHAR(100),
            company_description TEXT,
            job_source_url VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] jobs")

    # ===================== career_reports =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS career_reports (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            target_job_id INT,
            report_title VARCHAR(255),
            report_content TEXT,
            report_html TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            user_id INT NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] career_reports")

    # ===================== job_ai_profiles =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_ai_profiles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_id INT NOT NULL,
            student_id INT NOT NULL,
            ability_requirement_scores JSON,
            vertical_promotion_info JSON,
            job_transfer_paths JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            UNIQUE KEY unique_student_job (student_id, job_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] job_ai_profiles")

    # ===================== interview_sessions =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            job_id INT NOT NULL,
            messages JSON NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_student_job (student_id, job_id),
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] interview_sessions")

    # ===================== student_job_matches =====================""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_job_matches (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_id INT NOT NULL,
            student_id INT NOT NULL,
            match_rank INT NOT NULL,
            basic_requirements_matching FLOAT DEFAULT 0,
            professional_skills_matching FLOAT DEFAULT 0,
            professional_literacy_matching FLOAT DEFAULT 0,
            development_potential_matching FLOAT DEFAULT 0,
            overall_matching FLOAT DEFAULT 0,
            is_favorite TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] student_job_matches")

    # ===================== industries =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS industries (
            id INT AUTO_INCREMENT PRIMARY KEY,
            industry_name VARCHAR(100) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] industries")

    # ===================== resumes =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            resume_name VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_type VARCHAR(50),
            file_size INT,
            resume_text TEXT,
            is_default TINYINT(1) DEFAULT 0,
            status VARCHAR(20) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user_id (user_id),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] resumes")

    # ===================== resume_analyses =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_analyses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            resume_id INT,
            analysis_type VARCHAR(50) NOT NULL,
            analysis_content JSON NOT NULL,
            raw_response TEXT,
            suggested_jobs JSON,
            competitiveness_score FLOAT,
            ability_scores JSON,
            extracted_skills JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE SET NULL,
            INDEX idx_user_id (user_id),
            INDEX idx_resume_id (resume_id),
            INDEX idx_analysis_type (analysis_type),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] resume_analyses")

    # ===================== resume_job_matches =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resume_job_matches (
            id INT AUTO_INCREMENT PRIMARY KEY,
            resume_id INT NOT NULL,
            job_id INT NOT NULL,
            user_id INT NOT NULL,
            match_score FLOAT,
            match_reason TEXT,
            is_favorite TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE CASCADE,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE KEY unique_resume_job (resume_id, job_id),
            INDEX idx_user_id (user_id),
            INDEX idx_match_score (match_score)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] resume_job_matches")

    # ===================== job_skill_requirements =====================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_skill_requirements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_id INT NOT NULL,
            skill_name VARCHAR(100) NOT NULL,
            weight FLOAT DEFAULT 0.1,
            required_level FLOAT DEFAULT 3.0,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            INDEX idx_job_id (job_id),
            INDEX idx_skill_name (skill_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)
    print("[OK] job_skill_requirements")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n[OK] 13 张表已就绪！")


def import_excel_data():
    """从Excel导入岗位和行业数据"""
    excel_path = os.path.join(os.path.dirname(__file__), '20260226105856_457.xls')

    if not os.path.exists(excel_path):
        print(f"[SKIP] Excel文件不存在: {excel_path}")
        return

    df = pd.read_excel(excel_path)
    print(f"[OK] 读取Excel成功，共 {len(df)} 条岗位")

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    industries_set = set()
    count = 0
    for _, row in df.iterrows():
        industry = str(row.get('所属行业', ''))
        if industry:
            industries_set.add(industry)

        cursor.execute("""
            INSERT INTO jobs (
                job_name, work_address, salary_range, company_name, industry,
                company_size, company_type, job_code, job_description,
                promotion_path, transfer_path, core_highlight,
                professional_skills_certificates, innovation_ability,
                learning_ability, stress_resistance, communication_ability,
                internship_experience, update_date, company_description, job_source_url
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            str(row.get('岗位名称', '')),
            str(row.get('地址', '')),
            str(row.get('薪资范围', '')),
            str(row.get('公司名称', '')),
            industry,
            str(row.get('公司规模', '')),
            str(row.get('公司类型', '')),
            str(row.get('岗位编码', '')),
            str(row.get('岗位详情', '')),
            '', '', '', 0, 0, 0, 0, 0, 0,
            row.get('更新日期'),
            str(row.get('公司详情', '')),
            str(row.get('岗位来源地址', ''))
        ))
        count += 1
        if count % 100 == 0:
            conn.commit()
            print(f"  已导入 {count}/{len(df)}")

    conn.commit()

    for ind in industries_set:
        cursor.execute("INSERT IGNORE INTO industries (industry_name) VALUES (%s)", (ind,))

    conn.commit()
    print(f"[OK] 岗位 {count} 条, 行业 {len(industries_set)} 个导入完成")

    cursor.close()
    conn.close()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='VocaAgent-2.0 数据库初始化')
    parser.add_argument('--import-excel', action='store_true',
                        help='从Excel导入岗位和行业数据（仅在首次部署时使用）')
    parser.add_argument('--populate-skills', action='store_true',
                        help='从岗位描述中提取技能关键词并填充 job_skill_requirements 表（增量模式，只处理新岗位）')
    parser.add_argument('--force', action='store_true',
                        help='配合 --populate-skills 使用：清空旧数据，全量重建')
    args = parser.parse_args()

    print("=" * 50)
    print("  VocaAgent-2.0 数据库初始化")
    print("=" * 50)
    create_tables()
    if args.import_excel:
        print()
        import_excel_data()
    if args.populate_skills:
        print()
        from utils.skill_analyzer import populate_job_skills
        populate_job_skills(force=args.force)
    # 检查 job_skill_requirements 是否为空
    if not args.populate_skills:
        from utils.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM job_skill_requirements")
        if cursor.fetchone()['cnt'] == 0:
            print("\n" + "=" * 50)
            print("⚠  job_skill_requirements 表为空！")
            print("   岗位匹配和技能差距分析将不可用。")
            print("   请运行: python init_database.py --populate-skills")
            print("=" * 50)
        cursor.close()
        conn.close()
    print("\n[OK] 全部完成！")


if __name__ == '__main__':
    main()
