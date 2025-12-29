"""
初始化演示数据
用于展示前端界面效果
"""
import sys
import os
from datetime import datetime, timedelta
import json
import uuid

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from src.api.models.database import init_database, get_db
from src.api.models.review_models import (
    ReviewSession, ReviewFile, ReviewIssue, CommitInfo
)


def create_demo_data():
    """创建演示数据"""
    print("初始化数据库...")
    db_path = "./data/review.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    init_database(db_path)
    
    print("创建演示数据...")
    db = next(get_db())
    
    try:
        # 创建3个评审会话
        sessions_data = [
            {
                "project_name": "电商系统",
                "review_branch": "feature/payment-optimization",
                "base_branch": "main",
                "days_ago": 1,
                "files": 5,
                "issues": 15
            },
            {
                "project_name": "用户中心",
                "review_branch": "develop",
                "base_branch": "main",
                "days_ago": 3,
                "files": 8,
                "issues": 23
            },
            {
                "project_name": "订单系统",
                "review_branch": "feature/order-refactor",
                "base_branch": "develop",
                "days_ago": 7,
                "files": 12,
                "issues": 8
            }
        ]
        
        for idx, session_data in enumerate(sessions_data, 1):
            # 创建评审会话
            review_time = datetime.now() - timedelta(days=session_data["days_ago"])
            session = ReviewSession(
                session_uuid=str(uuid.uuid4()),
                project_name=session_data["project_name"],
                review_branch=session_data["review_branch"],
                base_branch=session_data["base_branch"],
                review_time=review_time,
                duration_seconds=45.5 + idx * 10,
                total_commits=3 + idx,
                total_files_changed=session_data["files"],
                total_files_reviewed=session_data["files"],
                total_issues=session_data["issues"],
                critical_count=session_data["issues"] // 5,
                major_count=session_data["issues"] // 3,
                minor_count=session_data["issues"] // 4,
                suggestion_count=session_data["issues"] - (session_data["issues"] // 5) - (session_data["issues"] // 3) - (session_data["issues"] // 4),
                total_additions=100 + idx * 50,
                total_deletions=30 + idx * 10,
                concurrent_mode=True
            )
            db.add(session)
            db.flush()
            
            # 创建提交信息
            authors = ["张三", "李四", "王五"]
            for i in range(session.total_commits):
                commit = CommitInfo(
                    session_id=session.id,
                    commit_id=f"abc{idx}{i}" * 8,
                    author_name=authors[i % len(authors)],
                    author_email=f"{authors[i % len(authors)]}@example.com",
                    commit_message=f"feat: 实现新功能 #{i+1}",
                    commit_time=review_time - timedelta(hours=i)
                )
                db.add(commit)
            
            # 创建文件和问题
            file_paths = [
                f"src/services/payment_service.py",
                f"src/controllers/user_controller.py",
                f"src/models/order_model.py",
                f"src/utils/validators.py",
                f"src/api/payment_api.py",
                f"src/middleware/auth.py",
                f"src/config/settings.py",
                f"tests/test_payment.py",
                f"src/services/order_service.py",
                f"src/utils/helpers.py",
                f"src/database/repositories.py",
                f"src/tasks/background_jobs.py"
            ]
            
            severities = ['critical', 'major', 'minor', 'suggestion']
            categories = ['代码风格', '安全性', '性能', '最佳实践', '可维护性']
            
            for i in range(min(session_data["files"], len(file_paths))):
                # 创建文件
                file = ReviewFile(
                    session_id=session.id,
                    file_path=file_paths[i],
                    additions=20 + i * 5,
                    deletions=5 + i * 2,
                    new_file=i % 4 == 0,
                    renamed_file=i % 5 == 0,
                    issue_count=session_data["issues"] // session_data["files"]
                )
                db.add(file)
                db.flush()
                
                # 为每个文件创建问题
                issues_per_file = session_data["issues"] // session_data["files"]
                for j in range(issues_per_file):
                    severity = severities[(i + j) % len(severities)]
                    category = categories[(i + j) % len(categories)]
                    
                    code_snippet = {
                        "start_line": 10 + j * 5,
                        "end_line": 15 + j * 5,
                        "lines": [
                            {
                                "line_num": 10 + j * 5,
                                "type": "context",
                                "content": "def process_payment(amount, user_id):",
                                "in_range": True
                            },
                            {
                                "line_num": 11 + j * 5,
                                "type": "added",
                                "content": "    if amount <= 0:",
                                "in_range": True
                            },
                            {
                                "line_num": 12 + j * 5,
                                "type": "added",
                                "content": "        raise ValueError('金额必须大于0')",
                                "in_range": True
                            }
                        ]
                    }
                    
                    issue = ReviewIssue(
                        file_id=file.id,
                        session_id=session.id,
                        severity=severity,
                        category=category,
                        author=authors[(i + j) % len(authors)],
                        file_path=file_paths[i],
                        line_info=f"{10 + j * 5}-{15 + j * 5}",
                        method_name=f"process_payment" if j % 2 == 0 else "validate_user",
                        description=f"发现{category}问题：建议检查参数验证逻辑",
                        suggestion=f"建议添加更完善的错误处理和日志记录",
                        code_snippet_json=json.dumps(code_snippet, ensure_ascii=False),
                        matched_rule=f"检查{category}是否符合规范",
                        matched_rule_category=category,
                        confirm_status='pending' if j % 3 != 0 else 'accepted',
                        is_fixed=j % 4 == 0,
                        review_comment="需要进一步确认" if j % 2 == 0 else ""
                    )
                    db.add(issue)
        
        db.commit()
        print("✅ 演示数据创建成功！")
        print(f"   - 创建了 {len(sessions_data)} 个评审会话")
        print(f"   - 数据库位置: {db_path}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建演示数据失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_demo_data()
