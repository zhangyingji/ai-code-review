"""数据处理工具类"""
from typing import Dict, List, Any


class DataProcessor:
    """数据处理工具类 - 处理评审数据的排序、分组等操作"""
    
    # 严重程度排序权重
    SEVERITY_ORDER = {
        'critical': 1,
        'major': 2,
        'minor': 3,
        'suggestion': 4
    }
    
    @staticmethod
    def sort_issues_by_severity(issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按严重程度排序问题（从严重到建议）
        
        Args:
            issues: 问题列表
            
        Returns:
            排序后的问题列表
        """
        return sorted(
            issues, 
            key=lambda x: DataProcessor.SEVERITY_ORDER.get(x.get('severity', ''), 999)
        )
    
    @staticmethod
    def group_issues_by_author(review_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """按作者分组问题
        
        Args:
            review_data: 评审数据
            
        Returns:
            以作者名为键，问题列表为值的字典
        """
        grouped = {}
        
        for file_review in review_data.get('file_reviews', []):
            for issue in file_review.get('issues', []):
                # 从commits中查找对应文件的作者
                author = issue.get('author', 'Unknown')
                if author not in grouped:
                    grouped[author] = []
                
                issue_copy = issue.copy()
                issue_copy['file_path'] = file_review['file_path']
                grouped[author].append(issue_copy)
        
        return grouped
    
    @staticmethod
    def group_issues_by_file(review_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """按文件分组问题
        
        Args:
            review_data: 评审数据
            
        Returns:
            以文件路径为键，问题列表为值的字典
        """
        grouped = {}
        
        for file_review in review_data.get('file_reviews', []):
            file_path = file_review['file_path']
            issues = file_review.get('issues', [])
            if issues:
                grouped[file_path] = issues
        
        return grouped
    
    @staticmethod
    def group_issues_by_severity(review_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """按严重程度分组问题
        
        Args:
            review_data: 评审数据
            
        Returns:
            以严重程度为键，问题列表为值的字典
        """
        grouped = {
            'critical': [],
            'major': [],
            'minor': [],
            'suggestion': []
        }
        
        for file_review in review_data.get('file_reviews', []):
            for issue in file_review.get('issues', []):
                severity = issue.get('severity', 'suggestion')
                if severity in grouped:
                    issue_copy = issue.copy()
                    issue_copy['file_path'] = file_review['file_path']
                    grouped[severity].append(issue_copy)
        
        return grouped
    
    @staticmethod
    def filter_issues_by_severity(review_data: Dict[str, Any], severity: str) -> List[Dict[str, Any]]:
        """筛选指定严重程度的问题
        
        Args:
            review_data: 评审数据
            severity: 严重程度 (critical, major, minor, suggestion)
            
        Returns:
            筛选后的问题列表
        """
        issues = []
        
        for file_review in review_data.get('file_reviews', []):
            for issue in file_review.get('issues', []):
                if issue.get('severity') == severity:
                    issue_copy = issue.copy()
                    issue_copy['file_path'] = file_review['file_path']
                    issues.append(issue_copy)
        
        return issues
    
    @staticmethod
    def enrich_author_stats(review_data: Dict[str, Any]) -> None:
        """丰富作者统计信息（就地修改）
        
        为每个作者的问题列表按严重程度排序
        
        Args:
            review_data: 评审数据
        """
        if 'author_stats' in review_data:
            for author in review_data['author_stats']:
                if author.get('issues'):
                    author['issues'] = DataProcessor.sort_issues_by_severity(author['issues'])
    
    @staticmethod
    def enrich_file_reviews(review_data: Dict[str, Any]) -> None:
        """丰富文件评审信息（就地修改）
        
        为每个文件的问题列表按严重程度排序
        
        Args:
            review_data: 评审数据
        """
        for file_review in review_data.get('file_reviews', []):
            if file_review.get('issues'):
                file_review['issues'] = DataProcessor.sort_issues_by_severity(file_review['issues'])
