#!/usr/bin/env python3
"""生成演示HTML报告"""

from src.report_generator import ReportGenerator
import json
from datetime import datetime

# 创建演示数据
demo_data = {
    'metadata': {
        'source_branch': 'feature/add-multi-dimension',
        'target_branch': 'main',
        'review_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'duration_seconds': 45.23
    },
    'commits': [
        {
            'id': 'abc123',
            'author_email': 'alice@example.com',
            'author_name': 'Alice',
            'title': 'feat: 添加多维度报告查看功能'
        },
        {
            'id': 'def456',
            'author_email': 'bob@example.com',
            'author_name': 'Bob',
            'title': 'fix: 修复HTML报告作者显示问题'
        }
    ],
    'file_reviews': [
        {
            'file_path': 'src/templates/html_template.py',
            'issues': [
                {
                    'category': '代码复杂度',
                    'severity': 'critical',
                    'description': 'JavaScript代码过长，建议拆分为多个函数',
                    'suggestion': '将renderIssueCard和相关函数拆分到单独的文件中',
                    'author': 'Alice',
                    'file_path': 'src/templates/html_template.py',
                    'method': 'renderIssueCard()',
                    'line': '247',
                    'code_snippet': {
                        'start_line': 240,
                        'end_line': 260,
                        'lines': [
                            {'line_num': 240, 'type': 'context', 'content': '    // 渲染问题卡片', 'in_range': False},
                            {'line_num': 241, 'type': 'context', 'content': '    function renderIssueCard(issue) {', 'in_range': False},
                            {'line_num': 242, 'type': 'added', 'content': '        const author = issue.author || \"Unknown\";', 'in_range': True},
                            {'line_num': 243, 'type': 'added', 'content': '        const filePath = issue.file_path || \"Unknown\";', 'in_range': True},
                            {'line_num': 244, 'type': 'context', 'content': '        let html = `<div class=\"problem-card\">`;', 'in_range': False},
                        ]
                    }
                },
                {
                    'category': '变量命名',
                    'severity': 'major',
                    'description': '变量名bySevertity拼写错误，应为bySeverity',
                    'suggestion': '修正变量名：bySevertity -> bySeverity',
                    'author': 'Alice',
                    'file_path': 'src/templates/html_template.py',
                    'method': 'renderSeverityDimension()',
                    'line': '143',
                    'code_snippet': {
                        'start_line': 140,
                        'end_line': 150,
                        'lines': [
                            {'line_num': 140, 'type': 'context', 'content': '    // 按严重程度分组', 'in_range': False},
                            {'line_num': 141, 'type': 'context', 'content': '        const bySevertity = {};', 'in_range': False},
                            {'line_num': 142, 'type': 'deleted', 'content': '        const bySeverity = {};', 'in_range': True},
                        ]
                    }
                }
            ]
        },
        {
            'file_path': 'src/templates/styles.py',
            'issues': [
                {
                    'category': '代码重复',
                    'severity': 'minor',
                    'description': 'CSS中有重复的样式定义',
                    'suggestion': '可以合并.filter-item和.dashboard-item的公共样式',
                    'author': 'Alice',
                    'file_path': 'src/templates/styles.py',
                    'method': None,
                    'line': '88',
                    'code_snippet': {
                        'start_line': 85,
                        'end_line': 95,
                        'lines': [
                            {'line_num': 85, 'type': 'context', 'content': '    .filter-item { text-align: center; padding: 12px; background: #f6f8fa; border-radius: 6px; cursor: pointer; border: 2px solid transparent; transition: all 0.3s; }', 'in_range': False},
                            {'line_num': 86, 'type': 'context', 'content': '    .filter-item:hover { background: #e1e4e8; }', 'in_range': False},
                            {'line_num': 87, 'type': 'deleted', 'content': '    .dashboard-item { text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 6px; cursor: pointer; border: 2px solid transparent; transition: all 0.3s; }', 'in_range': True},
                        ]
                    }
                }
            ]
        },
        {
            'file_path': 'src/gitlab_client.py',
            'issues': [
                {
                    'category': '错误处理',
                    'severity': 'suggestion',
                    'description': '建议为commit.diff(get_all=True)添加更详细的错误日志',
                    'suggestion': '在异常处理中记录commit ID和错误详情',
                    'author': 'Bob',
                    'file_path': 'src/gitlab_client.py',
                    'method': 'get_commits_between_branches()',
                    'line': '269',
                    'code_snippet': None
                }
            ]
        }
    ],
    'author_stats': [
        {
            'name': 'Alice',
            'email': 'alice@example.com',
            'commits': [
                {'id': 'abc123', 'author_name': 'Alice', 'author_email': 'alice@example.com', 'title': 'feat: 添加多维度报告查看功能', 'created_at': '2025-11-25T10:00:00Z'}
            ],
            'files_changed': ['src/templates/html_template.py', 'src/templates/styles.py'],
            'issues': [
                {
                    'category': '代码复杂度',
                    'severity': 'critical',
                    'description': 'JavaScript代码过长，建议拆分为多个函数',
                    'suggestion': '将renderIssueCard和相关函数拆分到单独的文件中',
                    'author': 'Alice',
                    'file_path': 'src/templates/html_template.py',
                    'method': 'renderIssueCard()',
                    'line': '247',
                    'code_snippet': {
                        'start_line': 240,
                        'end_line': 260,
                        'lines': [
                            {'line_num': 240, 'type': 'context', 'content': '    // 渲染问题卡片', 'in_range': False},
                            {'line_num': 241, 'type': 'context', 'content': '    function renderIssueCard(issue) {', 'in_range': False},
                            {'line_num': 242, 'type': 'added', 'content': '        const author = issue.author || "Unknown";', 'in_range': True},
                            {'line_num': 243, 'type': 'added', 'content': '        const filePath = issue.file_path || "Unknown";', 'in_range': True},
                            {'line_num': 244, 'type': 'context', 'content': '        let html = `<div class="problem-card">`;', 'in_range': False},
                        ]
                    }
                },
                {
                    'category': '变量命名',
                    'severity': 'major',
                    'description': '变量名bySevertity拼写错误，应为bySeverity',
                    'suggestion': '修正变量名：bySevertity -> bySeverity',
                    'author': 'Alice',
                    'file_path': 'src/templates/html_template.py',
                    'method': 'renderSeverityDimension()',
                    'line': '143',
                    'code_snippet': {
                        'start_line': 140,
                        'end_line': 150,
                        'lines': [
                            {'line_num': 140, 'type': 'context', 'content': '    // 按严重程度分组', 'in_range': False},
                            {'line_num': 141, 'type': 'context', 'content': '        const bySevertity = {};', 'in_range': False},
                            {'line_num': 142, 'type': 'deleted', 'content': '        const bySeverity = {};', 'in_range': True},
                        ]
                    }
                },
                {
                    'category': '代码重复',
                    'severity': 'minor',
                    'description': 'CSS中有重复的样式定义',
                    'suggestion': '可以合并.filter-item和.dashboard-item的公共样式',
                    'author': 'Alice',
                    'file_path': 'src/templates/styles.py',
                    'method': None,
                    'line': '88',
                    'code_snippet': {
                        'start_line': 85,
                        'end_line': 95,
                        'lines': [
                            {'line_num': 85, 'type': 'context', 'content': '    .filter-item { text-align: center; padding: 12px; background: #f6f8fa; border-radius: 6px; cursor: pointer; border: 2px solid transparent; transition: all 0.3s; }', 'in_range': False},
                            {'line_num': 86, 'type': 'context', 'content': '    .filter-item:hover { background: #e1e4e8; }', 'in_range': False},
                        ]
                    }
                }
            ],
            'commit_count': 1,
            'file_count': 2,
            'issue_count': 3,
            'issue_by_severity': {'critical': 1, 'major': 1, 'minor': 1, 'suggestion': 0}
        },
        {
            'name': 'Bob',
            'email': 'bob@example.com',
            'commits': [
                {'id': 'def456', 'author_name': 'Bob', 'author_email': 'bob@example.com', 'title': 'fix: 修复HTML报告作者显示问题', 'created_at': '2025-11-25T11:00:00Z'}
            ],
            'files_changed': ['src/gitlab_client.py'],
            'issues': [
                {
                    'category': '错误处理',
                    'severity': 'suggestion',
                    'description': '建议为commit.diff(get_all=True)添加更详细的错误日志',
                    'suggestion': '在异常处理中记录commit ID和错误详情',
                    'author': 'Bob',
                    'file_path': 'src/gitlab_client.py',
                    'method': 'get_commits_between_branches()',
                    'line': '269',
                    'code_snippet': None
                }
            ],
            'commit_count': 1,
            'file_count': 1,
            'issue_count': 1,
            'issue_by_severity': {'critical': 0, 'major': 0, 'minor': 0, 'suggestion': 1}
        }
    ],
    'statistics': {
        'total_issues': 5,
        'by_severity': {
            'critical': 1,
            'major': 1,
            'minor': 1,
            'suggestion': 1
        },
        'total_commits': 2,
        'total_files': 3,
        'avg_issues_per_file': 1.67
    }
}

# 生成报告
try:
    report_gen = ReportGenerator('./reports')
    report_gen.generate_report(demo_data, format='html')
    print('✅ 演示报告已生成到 ./reports 目录')
except Exception as e:
    print(f'❌ 错误: {e}')
    import traceback
    traceback.print_exc()
