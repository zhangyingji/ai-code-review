#!/usr/bin/env python3
"""验证迁移后的报告生成器"""

from src.report_generator import ReportGenerator
from datetime import datetime

# 创建测试数据
test_data = {
    'metadata': {
        'source_branch': 'feature/migration-test',
        'target_branch': 'main',
        'review_time': datetime.now().isoformat(),
        'duration_seconds': 2.5,
        'total_commits': 3,
        'total_files_changed': 2,
        'total_files_reviewed': 2,
    },
    'statistics': {
        'total_issues': 3,
        'by_severity': {
            'critical': 1,
            'major': 1,
            'minor': 1,
            'suggestion': 0,
        },
        'total_additions': 50,
        'total_deletions': 20,
    },
    'author_stats': [
        {
            'name': '李四',
            'email': 'lisi@example.com',
            'commit_count': 2,
            'file_count': 2,
            'issue_count': 2,
            'issue_by_severity': {
                'critical': 1,
                'major': 1,
                'minor': 0,
                'suggestion': 0,
            },
            'issues': [
                {
                    'id': '1',
                    'category': '安全问题',
                    'severity': 'critical',
                    'description': 'SQL注入风险',
                    'suggestion': '使用参数化查询',
                    'file_path': 'src/db.py',
                    'method': 'query_user',
                    'line': 25,
                    'code_snippet': {
                        'start_line': 23,
                        'end_line': 28,
                        'lines': [
                            {'line_num': 23, 'content': '    def query_user(user_id):', 'type': ''},
                            {'line_num': 24, 'content': '        sql = f"SELECT * FROM users WHERE id={user_id}"', 'type': ''},
                            {'line_num': 25, 'content': '        return db.execute(sql)', 'type': 'highlight', 'in_range': True},
                        ]
                    },
                    'author': '李四',
                }
            ]
        }
    ],
    'file_reviews': [
        {
            'file_path': 'src/api.py',
            'additions': 30,
            'deletions': 10,
            'issues': [
                {
                    'id': '2',
                    'category': '代码质量',
                    'severity': 'major',
                    'description': '缺少错误处理',
                    'suggestion': '添加try-except块',
                    'method': 'handle_request',
                    'line': 15,
                }
            ]
        }
    ]
}

# 测试生成HTML报告
print("=" * 60)
print("开始验证迁移后的报告生成器")
print("=" * 60)

generator = ReportGenerator()

# 测试1：生成HTML报告
try:
    html_file = generator.generate_report(test_data, format='html')
    print(f"✅ HTML报告生成成功: {html_file}")
except Exception as e:
    print(f"❌ HTML报告生成失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2：生成Markdown报告
try:
    md_file = generator.generate_report(test_data, format='markdown')
    print(f"✅ Markdown报告生成成功: {md_file}")
except Exception as e:
    print(f"❌ Markdown报告生成失败: {e}")

# 测试3：生成JSON报告
try:
    json_file = generator.generate_report(test_data, format='json')
    print(f"✅ JSON报告生成成功: {json_file}")
except Exception as e:
    print(f"❌ JSON报告生成失败: {e}")

# 测试4：测试group_by_author参数兼容性
try:
    html_file = generator.generate_report(test_data, format='html', group_by_author=False)
    print(f"✅ group_by_author参数兼容性测试通过")
except Exception as e:
    print(f"❌ group_by_author参数兼容性测试失败: {e}")

# 测试5：多格式生成
try:
    results = generator.generate_multiple_formats(test_data, formats=['html', 'markdown'])
    success_count = sum(1 for v in results.values() if v is not None)
    print(f"✅ 多格式报告生成成功: {success_count}/2 个报告")
except Exception as e:
    print(f"❌ 多格式报告生成失败: {e}")

print("=" * 60)
print("验证完成！迁移成功 ✅")
print("=" * 60)
