"""Markdown格式化器"""
from typing import Dict, Any, List
from .base_formatter import BaseFormatter
from ..utils.data_processor import DataProcessor

# 严重程度标签
SEVERITY_LABELS = {
    'critical': '🔴 严重',
    'major': '🟠 主要',
    'minor': '🟡 次要',
    'suggestion': '💡 建议'
}


class MarkdownFormatter(BaseFormatter):
    """Markdown报告格式化器"""
    
    def format(self, review_data: Dict[str, Any], **kwargs) -> str:
        """格式化为Markdown报告
        
        Args:
            review_data: 评审数据
            **kwargs: 可选参数
                - include_code_snippets: 是否包含代码片段，默认False
            
        Returns:
            Markdown格式的报告内容
        """
        # 验证数据
        if not self.validate_data(review_data):
            raise ValueError("Invalid review data")
        
        # 预处理数据
        review_data = self.pre_process(review_data)
        
        # 格式化参数
        include_code = kwargs.get('include_code_snippets', False)
        
        lines = []
        metadata = review_data['metadata']
        stats = review_data['statistics']
        
        # 标题和基本信息
        lines.append("# 代码评审报告\n")
        lines.append("## 基本信息\n")
        lines.append(f"- **源分支**: {metadata['source_branch']}")
        lines.append(f"- **目标分支**: {metadata['target_branch']}")
        lines.append(f"- **评审时间**: {metadata['review_time']}")
        lines.append(f"- **评审耗时**: {metadata['duration_seconds']:.2f} 秒")
        lines.append(f"- **提交数量**: {metadata['total_commits']}")
        lines.append(f"- **文件变更**: {metadata['total_files_changed']}")
        lines.append(f"- **评审文件**: {metadata['total_files_reviewed']}")
        
        # 统计信息
        lines.append("\n## 问题统计\n")
        lines.append(f"- **总问题数**: {stats['total_issues']}")
        lines.append(f"- **严重问题**: {stats['by_severity']['critical']}")
        lines.append(f"- **主要问题**: {stats['by_severity']['major']}")
        lines.append(f"- **次要问题**: {stats['by_severity']['minor']}")
        lines.append(f"- **建议**: {stats['by_severity']['suggestion']}")
        lines.append(f"- **代码增加**: +{stats['total_additions']} 行")
        lines.append(f"- **代码删除**: -{stats['total_deletions']} 行")
        
        # 按作者分组
        if review_data.get('author_stats'):
            lines.append("\n## 按提交人统计\n")
            for author in review_data['author_stats']:
                lines.append(f"\n### {author['name']} ({author['email']})\n")
                lines.append(f"- **提交数**: {author['commit_count']}")
                lines.append(f"- **修改文件**: {author['file_count']}")
                lines.append(f"- **问题数**: {author['issue_count']}")
                
                severity = author['issue_by_severity']
                lines.append(f"  - 严重: {severity['critical']}")
                lines.append(f"  - 主要: {severity['major']}")
                lines.append(f"  - 次要: {severity['minor']}")
                lines.append(f"  - 建议: {severity['suggestion']}")
                
                # 列出问题
                if author['issues']:
                    sorted_issues = DataProcessor.sort_issues_by_severity(author['issues'])
                    critical_issues = [i for i in sorted_issues if i['severity'] == 'critical']
                    other_issues = [i for i in sorted_issues if i['severity'] != 'critical']
                    
                    if critical_issues:
                        lines.append(f"\n**🔴 严重问题** (共 {len(critical_issues)} 个):")
                        for issue in critical_issues:
                            self._add_issue_to_lines(lines, issue, include_code)
                    
                    if other_issues:
                        display_count = min(10, len(other_issues))
                        lines.append(f"\n**其他问题** (显示 {display_count} 个，共 {len(other_issues)} 个):")
                        for issue in other_issues[:10]:
                            self._add_issue_to_lines(lines, issue, include_code)
        
        # 详细文件评审结果
        lines.append("\n## 文件评审详情\n")
        for file_review in review_data['file_reviews']:
            lines.append(f"\n### {file_review['file_path']}\n")
            lines.append(f"- **变更**: +{file_review['additions']} -{file_review['deletions']}")
            
            if file_review['new_file']:
                lines.append("- **状态**: 新文件")
            if file_review['renamed_file']:
                lines.append("- **状态**: 重命名")
            
            lines.append(f"\n**评审总结**: {file_review.get('summary', '无')}\n")
            
            if file_review.get('issues'):
                lines.append("\n**发现的问题**:\n")
                sorted_issues = DataProcessor.sort_issues_by_severity(file_review['issues'])
                for i, issue in enumerate(sorted_issues, 1):
                    self._add_issue_to_lines(lines, issue, include_code, index=i)
        
        content = "\n".join(lines)
        return self.post_process(content)
    
    def _add_issue_to_lines(self, lines: List[str], issue: Dict[str, Any], 
                            include_code: bool = False, index: int | None = None) -> None:
        """添加问题到Markdown行列表
        
        Args:
            lines: 行列表
            issue: 问题字典
            include_code: 是否包含代码片段
            index: 问题序号（可选）
        """
        severity_label = SEVERITY_LABELS.get(issue['severity'], issue['severity'])
        prefix = f"{index}. " if index else "- "
        
        lines.append(f"{prefix}[{severity_label}] **{issue['category']}**")
        lines.append(f"   - 文件: {issue.get('file_path', 'N/A')}")
        lines.append(f"   - 位置: 第 {issue.get('line', 'N/A')} 行")
        if issue.get('method'):
            lines.append(f"   - 方法: `{issue['method']}`")
        lines.append(f"   - 描述: {issue['description']}")
        if issue.get('suggestion'):
            lines.append(f"   - 建议: {issue['suggestion']}")
        
        # 添加代码片段
        if include_code and issue.get('code_snippet'):
            snippet = issue['code_snippet']
            lines.append(f"\n   代码片段 ({snippet['start_line']}-{snippet['end_line']} 行):")
            lines.append("   ```")
            for line in snippet['lines']:
                lines.append(f"   {line['line_num']}: {line['content']}")
            lines.append("   ```")
        
        lines.append("")
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return ".md"
