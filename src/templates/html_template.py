"""HTML报告模板"""


def get_html_template() -> str:
    """获取HTML报告模板
    
    Returns:
        HTML模板字符串
    """
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>代码评审报告 - {{ review_data.metadata.source_branch }}</title>
    {{ styles }}
</head>
<body>
    <div class="container">
        <h1>🔍 代码评审报告</h1>
        
        <!-- 基本元数据 -->
        <div class="metadata">
            <div class="metadata-item"><span class="metadata-label">源分支:</span> {{ review_data.metadata.source_branch }}</div>
            <div class="metadata-item"><span class="metadata-label">目标分支:</span> {{ review_data.metadata.target_branch }}</div>
            <div class="metadata-item"><span class="metadata-label">评审时间:</span> {{ review_data.metadata.review_time }}</div>
            <div class="metadata-item"><span class="metadata-label">评审耗时:</span> {{ "%.2f"|format(review_data.metadata.duration_seconds) }} 秒</div>
        </div>
        
        <!-- 仪表盘 - 按严重程度筛选 -->
        <div class="dashboard">
            <h2>📈 按严重程度筛选</h2>
            <div class="dashboard-grid">
                <div class="dashboard-item" data-severity="critical" onclick="filterIssues('critical')">
                    <div class="dashboard-item-label">严重问题</div>
                    <div class="dashboard-item-value" style="color: #ff6b6b;">{{ review_data.statistics.by_severity.critical }}</div>
                </div>
                <div class="dashboard-item" data-severity="major" onclick="filterIssues('major')">
                    <div class="dashboard-item-label">主要问题</div>
                    <div class="dashboard-item-value" style="color: #ffa500;">{{ review_data.statistics.by_severity.major }}</div>
                </div>
                <div class="dashboard-item" data-severity="minor" onclick="filterIssues('minor')">
                    <div class="dashboard-item-label">次要问题</div>
                    <div class="dashboard-item-value" style="color: #ffd700;">{{ review_data.statistics.by_severity.minor }}</div>
                </div>
                <div class="dashboard-item" data-severity="suggestion" onclick="filterIssues('suggestion')">
                    <div class="dashboard-item-label">建议</div>
                    <div class="dashboard-item-value" style="color: #87ceeb;">{{ review_data.statistics.by_severity.suggestion }}</div>
                </div>
            </div>
        </div>
        
        <!-- 问题列表 -->
        <h2 id="issues-section">🔍 问题详情</h2>
        <div id="issues-container" class="issues-list">
            {% set all_issues = [] %}
            {# 从author_stats收集问题 #}
            {% if review_data.author_stats %}
                {% for author in review_data.author_stats %}
                    {% for issue in author.issues %}
                        {% set _ = all_issues.append(issue) %}
                    {% endfor %}
                {% endfor %}
            {% endif %}
            {# 如果author_stats为空，从file_reviews收集问题 #}
            {% if all_issues|length == 0 %}
                {% for file_review in review_data.file_reviews %}
                    {% for issue in file_review.issues %}
                        {% set issue_with_file = issue.copy() if issue.copy else issue %}
                        {% if issue.copy %}
                            {% set _ = issue_with_file.update({'file_path': file_review.file_path}) %}
                        {% else %}
                            {% set issue_with_file = dict(issue, file_path=file_review.file_path) %}
                        {% endif %}
                        {% set _ = all_issues.append(issue_with_file) %}
                    {% endfor %}
                {% endfor %}
            {% endif %}
            
            {% if all_issues|length > 0 %}
                {% for issue in all_issues %}
                    {% set author_name = issue.get('author', 'Unknown') if issue.get('author') else 'Unknown' %}
                    <div class="problem-card" data-severity="{{ issue.severity }}">
                        <!-- 问题头部 -->
                        <div class="problem-header">
                            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                                <span class="severity-badge badge-{{ issue.severity }}">{{ severity_labels[issue.severity] }}</span>
                                <strong>{{ issue.category }}</strong>
                            </div>
                            <div class="problem-author">👤 {{ author_name }}</div>
                        </div>
                        
                        <!-- 文件、方法、位置信息 -->
                        <div class="problem-location">
                            {% if issue.file_path %}<div><strong>📄 文件:</strong> {{ issue.file_path }}</div>{% endif %}
                            {% if issue.method %}<div><strong>🔍 方法:</strong> <code>{{ issue.method }}</code></div>{% endif %}
                            {% if issue.line %}<div><strong>📍 位置:</strong> 第 {{ issue.line }} 行</div>{% endif %}
                        </div>
                        
                        <!-- 问题描述 -->
                        <div class="problem-description">
                            <strong>❌ 问题:</strong> {{ issue.description }}
                        </div>
                        
                        <!-- 修复建议 -->
                        {% if issue.suggestion %}
                        <div class="problem-suggestion">
                            💡 <strong>建议:</strong> {{ issue.suggestion }}
                        </div>
                        {% endif %}
                        
                        <!-- 代码段落 - 默认折叠 -->
                        {% if issue.code_snippet %}
                        <div class="code-snippet">
                            <div class="code-snippet-header" onclick="toggleCodeSnippet(this)">
                                <span>📄 {{ issue.code_snippet.start_line }}-{{ issue.code_snippet.end_line }} 行的代码段落</span>
                                <span class="code-snippet-toggle collapsed">▼</span>
                            </div>
                            <div class="code-snippet-content collapsed">
                                {% for line in issue.code_snippet.lines %}
                                <div class="code-line {% if line.type %}{{ line.type }}{% endif %}{% if line.in_range %} in-range{% endif %}">
                                    <div class="code-line-num">{{ line.line_num }}</div>
                                    <div class="code-line-content">{{ line.content }}</div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                        {% endif %}
                    </div>
                {% endfor %}
            {% else %}
                <div style="text-align: center; padding: 40px; color: #586069;">
                    <p>🌟 没有找到任何问题!</p>
                </div>
            {% endif %}
        </div>
        
        <footer>
            Generated by Code Review System | {{ review_data.metadata.review_time }}
        </footer>
    </div>
    
    {{ scripts }}
</body>
</html>
"""


def get_scripts() -> str:
    """获取JavaScript脚本
    
    Returns:
        JavaScript代码
    """
    return """<script>
    // 代码段落展开/折叠
    function toggleCodeSnippet(header) {
        const content = header.nextElementSibling;
        const toggle = header.querySelector('.code-snippet-toggle');
        
        if (content && toggle) {
            content.classList.toggle('collapsed');
            toggle.classList.toggle('collapsed');
        }
    }
    
    // 按严重程度筛选问题
    function filterIssues(severity) {
        const cards = document.querySelectorAll('.problem-card');
        const dashboardItems = document.querySelectorAll('.dashboard-item');
        
        // 更新仪表板激活状态
        dashboardItems.forEach(item => {
            if (item.getAttribute('data-severity') === severity) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });
        
        // 筛选问题卡片
        cards.forEach(card => {
            if (card.getAttribute('data-severity') === severity) {
                card.classList.add('show');
            } else {
                card.classList.remove('show');
            }
        });
    }
    
    // 页面加载完成后，默认显示严重问题
    document.addEventListener('DOMContentLoaded', function() {
        filterIssues('critical');
    });
</script>"""
