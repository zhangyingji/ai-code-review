"""
代码评审引擎
整合 GitLab 客户端和大模型客户端,执行完整的评审流程
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from .gitlab_client import GitLabClient
from .llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReviewEngine:
    """代码评审引擎"""
    
    def __init__(self, gitlab_client: GitLabClient, llm_client: LLMClient, 
                 review_rules: Dict, enable_concurrent: bool = True, max_workers: int = 3,
                 enable_thinking: bool = False):
        """
        初始化评审引擎
        
        Args:
            gitlab_client: GitLab客户端
            llm_client: 大模型客户端
            review_rules: 评审规则配置
            enable_concurrent: 是否启用并发评审
            max_workers: 最大并发worker数
            enable_thinking: 是否启用深度思考模式
        """
        self.gitlab_client = gitlab_client
        self.llm_client = llm_client
        self.review_rules = review_rules
        self.enable_concurrent = enable_concurrent
        self.max_workers = max_workers
        self.enable_thinking = enable_thinking
        
    def collect_review_rules(self) -> List[str]:
        """
        收集启用的评审规则
        
        Returns:
            规则列表
        """
        rules = []
        for category, config in self.review_rules.items():
            if config.get('enabled', False):
                rules.extend(config.get('rules', []))
        return rules
    
    def should_review_file(self, file_path: str) -> bool:
        """
        判断文件是否需要评审
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否需要评审
        """
        # 忽略的文件类型
        ignore_extensions = [
            '.md', '.txt', '.json', '.yaml', '.yml', 
            '.lock', '.gitignore', '.dockerignore',
            '.png', '.jpg', '.jpeg', '.gif', '.svg',
            '.ico', '.pdf', '.zip', '.tar', '.gz'
        ]
        
        # 忽略的目录
        ignore_dirs = [
            'node_modules', 'vendor', 'dist', 'build',
            '__pycache__', '.git', '.idea', '.vscode'
        ]
        
        # 检查文件扩展名
        for ext in ignore_extensions:
            if file_path.endswith(ext):
                return False
        
        # 检查目录
        for dir_name in ignore_dirs:
            if f'/{dir_name}/' in file_path or file_path.startswith(f'{dir_name}/'):
                return False
        
        return True
    
    def review_diff(self, diff_info: Dict, rules: List[str]) -> Optional[Dict]:
        """
        评审单个文件的差异
        
        Args:
            diff_info: 差异信息
            rules: 评审规则
            
        Returns:
            评审结果
        """
        file_path = diff_info['file_path']
        
        # 检查是否需要评审
        if not self.should_review_file(file_path):
            logger.info(f"跳过文件: {file_path}")
            return None
        
        # 跳过删除的文件
        if diff_info.get('deleted_file'):
            logger.info(f"跳过已删除文件: {file_path}")
            return None
        
        # 跳过没有差异的文件
        if not diff_info.get('diff'):
            logger.info(f"跳过无差异文件: {file_path}")
            return None
        
        logger.info(f"评审文件: {file_path}")
        
        # 使用大模型评审
        review_result = self.llm_client.review_code(
            code_diff=diff_info['diff'],
            file_path=file_path,
            rules=rules,
            enable_thinking=self.enable_thinking
        )
        
        # 添加文件信息
        review_result['file_path'] = file_path
        review_result['additions'] = diff_info.get('additions', 0)
        review_result['deletions'] = diff_info.get('deletions', 0)
        review_result['new_file'] = diff_info.get('new_file', False)
        review_result['renamed_file'] = diff_info.get('renamed_file', False)
        
        return review_result
    
    def review_branches(self, review_branch: str, base_branch: str = '') -> Dict:
        """
        评审两个分支之间的差异
        
        Args:
            review_branch: 要评审的分支
            base_branch: 基准分支，必须指定
            
        Returns:
            完整的评审结果
        """
        # 检查 base_branch 是否为bb指定
        if not base_branch:
            raise ValueError("错误: 必须指定 base_branch (基准分支)")
        
        logger.info(f"开始评审: {base_branch} -> {review_branch}")
        start_time = datetime.now()
        
        # 获取差异
        diffs = self.gitlab_client.get_diff_between_branches(review_branch, base_branch)
        logger.info(f"共有 {len(diffs)} 个文件发生变化")
        
        # 获取提交记录
        commits = self.gitlab_client.get_commits_between_branches(review_branch, base_branch)
        logger.info(f"共有 {len(commits)} 个提交")
        
        # 收集评审规则
        rules = self.collect_review_rules()
        logger.info(f"启用 {len(rules)} 条评审规则")
        
        # 评审每个文件 - 支持并发
        if self.enable_concurrent and len(diffs) > 1:
            logger.info(f"启用并发评审模式,max_workers={self.max_workers}")
            file_reviews = self._review_concurrent(diffs, rules)
        else:
            logger.info("使用串行评审模式")
            file_reviews = self._review_sequential(diffs, rules)
        
        # 按作者分组统计
        author_stats = self._group_by_author(commits, file_reviews)
        
        # 汇总统计
        total_issues = sum(len(r.get('issues', [])) for r in file_reviews)
        issue_by_severity = self._count_by_severity(file_reviews)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        review_report = {
            'metadata': {
                'source_branch': review_branch,
                'target_branch': base_branch,
                'review_time': start_time.isoformat(),
                'duration_seconds': duration,
                'total_commits': len(commits),
                'total_files_changed': len(diffs),
                'total_files_reviewed': len(file_reviews),
                'concurrent_mode': self.enable_concurrent
            },
            'commits': commits,
            'file_reviews': file_reviews,
            'author_stats': author_stats,
            'statistics': {
                'total_issues': total_issues,
                'by_severity': issue_by_severity,
                'total_additions': sum(d.get('additions', 0) for d in diffs),
                'total_deletions': sum(d.get('deletions', 0) for d in diffs)
            }
        }
        
        logger.info(f"评审完成,耗时 {duration:.2f} 秒,发现 {total_issues} 个问题")
        return review_report
    
    def _review_sequential(self, diffs: List[Dict], rules: List[str]) -> List[Dict]:
        """串行评审"""
        file_reviews = []
        for diff in diffs:
            result = self.review_diff(diff, rules)
            if result:
                file_reviews.append(result)
        return file_reviews
    
    def _review_concurrent(self, diffs: List[Dict], rules: List[str]) -> List[Dict]:
        """并发评审"""
        file_reviews = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_diff = {
                executor.submit(self.review_diff, diff, rules): diff 
                for diff in diffs
            }
            
            # 获取结果
            for future in as_completed(future_to_diff):
                try:
                    result = future.result()
                    if result:
                        file_reviews.append(result)
                except Exception as e:
                    diff = future_to_diff[future]
                    logger.error(f"评审文件 {diff.get('file_path')} 失败: {e}")
        
        return file_reviews
    
    def _group_by_author(self, commits: List[Dict], file_reviews: List[Dict]) -> List[Dict]:
        """
        按作者分组统计
        
        Args:
            commits: 提交列表
            file_reviews: 文件评审结果列表
            
        Returns:
            按作者分组的统计信息
        """
        # 提取所有作者
        authors = {}
        for commit in commits:
            author_email = commit['author_email']
            author_name = commit['author_name']
            
            if author_email not in authors:
                authors[author_email] = {
                    'name': author_name,
                    'email': author_email,
                    'commits': [],
                    'files_changed': set(),
                    'issues': []
                }
            
            authors[author_email]['commits'].append(commit)
        
        # 关联文件评审结果到作者
        # 注意: 这里简化处理,实际应该通过git blame获取每行代码的作者
        # 这里假设最近的提交者是主要负责人
        for review in file_reviews:
            # 找到最后修改此文件的作者
            file_path = review['file_path']
            
            # 简化处理:将问题分配给所有参与的作者
            for author_email in authors:
                authors[author_email]['files_changed'].add(file_path)
                if review.get('issues'):
                    authors[author_email]['issues'].extend(review['issues'])
        
        # 转换为列表并计算统计
        author_list = []
        for email, info in authors.items():
            info['files_changed'] = list(info['files_changed'])
            info['commit_count'] = len(info['commits'])
            info['file_count'] = len(info['files_changed'])
            info['issue_count'] = len(info['issues'])
            info['issue_by_severity'] = self._count_issues_by_severity(info['issues'])
            author_list.append(info)
        
        # 按提交数排序
        author_list.sort(key=lambda x: x['commit_count'], reverse=True)
        
        return author_list
    
    def _count_by_severity(self, file_reviews: List[Dict]) -> Dict[str, int]:
        """统计问题严重程度分布"""
        severity_count = {
            'critical': 0,
            'major': 0,
            'minor': 0,
            'suggestion': 0
        }
        
        for review in file_reviews:
            for issue in review.get('issues', []):
                severity = issue.get('severity', 'minor')
                if severity in severity_count:
                    severity_count[severity] += 1
        
        return severity_count
    
    def _count_issues_by_severity(self, issues: List[Dict]) -> Dict[str, int]:
        """统计单个问题列表的严重程度分布"""
        severity_count = {
            'critical': 0,
            'major': 0,
            'minor': 0,
            'suggestion': 0
        }
        
        for issue in issues:
            severity = issue.get('severity', 'minor')
            if severity in severity_count:
                severity_count[severity] += 1
        
        return severity_count
