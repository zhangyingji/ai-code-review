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
        
        <!-- 维度选择 -->
        <div class="dashboard">
            <h2>📈 查看维度</h2>
            <div class="dashboard-grid">
                <div class="dashboard-item dimension-tab active" data-dimension="severity" onclick="switchDimension('severity')">
                    <div class="dashboard-item-label">按严重程度</div>
                    <div class="dashboard-item-value" style="font-size: 1.5em;">🎯</div>
                </div>
                <div class="dashboard-item dimension-tab" data-dimension="file" onclick="switchDimension('file')">
                    <div class="dashboard-item-label">按文件</div>
                    <div class="dashboard-item-value" style="font-size: 1.5em;">📄</div>
                </div>
                <div class="dashboard-item dimension-tab" data-dimension="author" onclick="switchDimension('author')">
                    <div class="dashboard-item-label">按提交人</div>
                    <div class="dashboard-item-value" style="font-size: 1.5em;">👤</div>
                </div>
            </div>
        </div>
        
        <!-- 严重程度维度 -->
        <div id="severity-dimension" class="dimension-view active">
            <h2>📊 按严重程度筛选</h2>
            <div class="severity-filter-dashboard">
                <div class="filter-item" data-severity="critical" onclick="filterBySeverity('critical')">
                    <div class="filter-label">严重问题</div>
                    <div class="filter-value" style="color: #ff6b6b;">{{ review_data.statistics.by_severity.critical }}</div>
                </div>
                <div class="filter-item" data-severity="major" onclick="filterBySeverity('major')">
                    <div class="filter-label">主要问题</div>
                    <div class="filter-value" style="color: #ffa500;">{{ review_data.statistics.by_severity.major }}</div>
                </div>
                <div class="filter-item" data-severity="minor" onclick="filterBySeverity('minor')">
                    <div class="filter-label">次要问题</div>
                    <div class="filter-value" style="color: #ffd700;">{{ review_data.statistics.by_severity.minor }}</div>
                </div>
                <div class="filter-item" data-severity="suggestion" onclick="filterBySeverity('suggestion')">
                    <div class="filter-label">建议</div>
                    <div class="filter-value" style="color: #87ceeb;">{{ review_data.statistics.by_severity.suggestion }}</div>
                </div>
            </div>
            <div id="severity-issues" class="issues-container"></div>
        </div>
        
        <!-- 文件维度 -->
        <div id="file-dimension" class="dimension-view" style="display: none;">
            <h2>📁 按文件维度展示</h2>
            <div id="file-issues" class="issues-container"></div>
        </div>
        
        <!-- 提交人维度 -->
        <div id="author-dimension" class="dimension-view" style="display: none;">
            <h2>👥 按提交人维度展示</h2>
            <div id="author-issues" class="issues-container"></div>
        </div>
        
        <!-- 隐藏的原始数据 - 用于JavaScript渲染 -->
        <script type="application/json" id="all-issues-data">
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
        {{ all_issues|tojson }}
        </script>
        
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
    // 问题严重程度排序
    const SEVERITY_RANK = {
        'critical': 0,
        'major': 1,
        'minor': 2,
        'suggestion': 3
    };
    
    // 问题严重程度标签
    const SEVERITY_LABELS = {
        'critical': '严重',
        'major': '主要',
        'minor': '次要',
        'suggestion': '建议'
    };
    
    // 页面初始化
    document.addEventListener('DOMContentLoaded', function() {
        const issues = JSON.parse(document.getElementById('all-issues-data').textContent);
        renderSeverityDimension(issues);
        renderFileDimension(issues);
        renderAuthorDimension(issues);
    });
    
    // 代码段落展开/折叠
    function toggleCodeSnippet(header) {
        const content = header.nextElementSibling;
        const toggle = header.querySelector('.code-snippet-toggle');
        
        if (content && toggle) {
            content.classList.toggle('collapsed');
            toggle.classList.toggle('collapsed');
        }
    }
    
    // 切换维度视图
    function switchDimension(dimension) {
        // 隐藏所有维度视图
        document.querySelectorAll('.dimension-view').forEach(view => {
            view.style.display = 'none';
        });
        document.querySelectorAll('.dimension-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // 显示选中的维度视图
        document.getElementById(dimension + '-dimension').style.display = 'block';
        document.querySelector('[data-dimension="' + dimension + '"]').classList.add('active');
    }
    
    // 渲染严重程度维度
    function renderSeverityDimension(issues) {
        const container = document.getElementById('severity-issues');
        
        // 按严重程度分组
        const bySevertity = {};
        ['critical', 'major', 'minor', 'suggestion'].forEach(s => {
            bySevertity[s] = [];
        });
        
        issues.forEach(issue => {
            const severity = issue.severity || 'suggestion';
            bySevertity[severity].push(issue);
        });
        
        // 构建HTML
        let html = '';
        ['critical', 'major', 'minor', 'suggestion'].forEach(severity => {
            const severityIssues = bySevertity[severity];
            if (severityIssues.length > 0) {
                html += `<div class="severity-group" data-severity="${severity}">
                    <h3 class="severity-group-title">
                        <span class="severity-badge badge-${severity}">${SEVERITY_LABELS[severity]}</span>
                        <span>${severityIssues.length}个问题</span>
                    </h3>`;
                
                severityIssues.forEach(issue => {
                    html += renderIssueCard(issue);
                });
                
                html += '</div>';
            }
        });
        
        container.innerHTML = html || '<div style="text-align: center; padding: 40px; color: #586069;">🌟 没有找到任何问题!</div>';
    }
    
    // 渲染文件维度
    function renderFileDimension(issues) {
        const container = document.getElementById('file-issues');
        
        // 按文件分组
        const byFile = {};
        issues.forEach(issue => {
            const filePath = issue.file_path || 'Unknown';
            if (!byFile[filePath]) {
                byFile[filePath] = [];
            }
            byFile[filePath].push(issue);
        });
        
        // 按问题数降序排序
        const files = Object.keys(byFile).sort((a, b) => {
            return byFile[b].length - byFile[a].length;
        });
        
        // 构建HTML
        let html = '';
        files.forEach(filePath => {
            const fileIssues = byFile[filePath];
            
            // 计算统计信息
            const stats = {};
            ['critical', 'major', 'minor', 'suggestion'].forEach(s => { stats[s] = 0; });
            fileIssues.forEach(issue => {
                const severity = issue.severity || 'suggestion';
                stats[severity]++;
            });
            
            // 按严重程度排序问题
            fileIssues.sort((a, b) => {
                return SEVERITY_RANK[a.severity || 'suggestion'] - SEVERITY_RANK[b.severity || 'suggestion'];
            });
            
            html += `<div class="file-group">
                <h3 class="file-group-title">
                    <span>📄 ${filePath}</span>
                    <span class="file-stats">${fileIssues.length}个问题（严重${stats.critical} 主要${stats.major} 次要${stats.minor} 建议${stats.suggestion}）</span>
                </h3>`;
            
            fileIssues.forEach(issue => {
                html += renderIssueCard(issue);
            });
            
            html += '</div>';
        });
        
        container.innerHTML = html || '<div style="text-align: center; padding: 40px; color: #586069;">🌟 没有找到任何问题!</div>';
    }
    
    // 渲染提交人维度
    function renderAuthorDimension(issues) {
        const container = document.getElementById('author-issues');
        
        // 按提交人分组
        const byAuthor = {};
        issues.forEach(issue => {
            const author = issue.author || 'Unknown';
            if (!byAuthor[author]) {
                byAuthor[author] = [];
            }
            byAuthor[author].push(issue);
        });
        
        // 按问题数降序排序
        const authors = Object.keys(byAuthor).sort((a, b) => {
            return byAuthor[b].length - byAuthor[a].length;
        });
        
        // 构建HTML
        let html = '';
        authors.forEach(author => {
            const authorIssues = byAuthor[author];
            
            // 计算统计信息
            const stats = {};
            ['critical', 'major', 'minor', 'suggestion'].forEach(s => { stats[s] = 0; });
            authorIssues.forEach(issue => {
                const severity = issue.severity || 'suggestion';
                stats[severity]++;
            });
            
            // 按严重程度排序问题
            authorIssues.sort((a, b) => {
                return SEVERITY_RANK[a.severity || 'suggestion'] - SEVERITY_RANK[b.severity || 'suggestion'];
            });
            
            html += `<div class="author-group">
                <h3 class="author-group-title">
                    <span>👤 ${author}</span>
                    <span class="author-stats">${authorIssues.length}个问题（严重${stats.critical} 主要${stats.major} 次要${stats.minor} 建议${stats.suggestion}）</span>
                </h3>`;
            
            authorIssues.forEach(issue => {
                html += renderIssueCard(issue);
            });
            
            html += '</div>';
        });
        
        container.innerHTML = html || '<div style="text-align: center; padding: 40px; color: #586069;">🌟 没有找到任何问题!</div>';
    }
    
    // 渲染问题卡片
    function renderIssueCard(issue) {
        const author = issue.author || 'Unknown';
        const filePath = issue.file_path || 'Unknown';
        const method = issue.method || '';
        const line = issue.line || '';
        const description = issue.description || '';
        const suggestion = issue.suggestion || '';
        const severity = issue.severity || 'suggestion';
        
        let html = `<div class="problem-card">
            <div class="problem-header">
                <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                    <span class="severity-badge badge-${severity}">${SEVERITY_LABELS[severity]}</span>
                    <strong>${issue.category || ''}</strong>
                </div>
                <div class="problem-author">👤 ${author}</div>
            </div>
            
            <div class="problem-location">
                ${filePath ? `<div><strong>📄 文件:</strong> ${filePath}</div>` : ''}
                ${method ? `<div><strong>🔍 方法:</strong> <code>${method}</code></div>` : ''}
                ${line ? `<div><strong>📍 位置:</strong> 第 ${line} 行</div>` : ''}
            </div>
            
            <div class="problem-description">
                <strong>❌ 问题:</strong> ${description}
            </div>`;
        
        if (suggestion) {
            html += `<div class="problem-suggestion">
                💡 <strong>建议:</strong> ${suggestion}
            </div>`;
        }
        
        if (issue.code_snippet) {
            const snippet = issue.code_snippet;
            const startLine = snippet.start_line || '';
            const endLine = snippet.end_line || '';
            html += `<div class="code-snippet">
                <div class="code-snippet-header" onclick="toggleCodeSnippet(this)">
                    <span>📄 ${startLine}-${endLine} 行的代码段落</span>
                    <span class="code-snippet-toggle collapsed">▼</span>
                </div>
                <div class="code-snippet-content collapsed">`;
            
            if (snippet.lines && Array.isArray(snippet.lines)) {
                snippet.lines.forEach(line => {
                    const type = line.type || '';
                    const inRange = line.in_range ? 'in-range' : '';
                    const lineNum = line.line_num || '';
                    const content = line.content || '';
                    html += `<div class="code-line ${type} ${inRange}">
                        <div class="code-line-num">${lineNum}</div>
                        <div class="code-line-content">${content}</div>
                    </div>`;
                });
            }
            
            html += `</div></div>`;
        }
        
        html += '</div>';
        return html;
    }
    
    // 按严重程度筛选（用于兼容性）
    function filterBySeverity(severity) {
        // 这个函数现在已经不需要了，因为数据是由JavaScript动态渲染的
        // 保留这个函数以便兼容任何可能的调用
    }
</script>"""

