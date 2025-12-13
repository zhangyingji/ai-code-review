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
                 enable_thinking: bool = False, ignore_extensions: Optional[List[str]] = None,
                 ignore_dirs: Optional[List[str]] = None, filter_authors: Optional[List[str]] = None,
                 branch_strategy: str = 'direct'):
        """
        初始化评审引擎
        
        Args:
            gitlab_client: GitLab客户端
            llm_client: 大模型客户端
            review_rules: 评审规则配置
            enable_concurrent: 是否启用并发评审
            max_workers: 最大并发worker数
            enable_thinking: 是否启用深度思考模式
            ignore_extensions: 忽略的文件扩展名列表
            ignore_dirs: 忽略的目录列表
            filter_authors: 提交人邮箱列表，为Empty时表示无限制
            branch_strategy: 分支比较策略，可选值：
                - 'direct': 仅比较两个分支之间的直接差异（默认，最快）
                - 'all_commits': 获取所有提交记录及其差异（适合合并驱动的工作流，较慢）
        """
        # ... existing code ...
        self.gitlab_client = gitlab_client
        self.llm_client = llm_client
        self.review_rules = review_rules
        self.enable_concurrent = enable_concurrent
        self.max_workers = max_workers
        self.enable_thinking = enable_thinking
        self.branch_strategy = branch_strategy
        
        # 设置忽略列表，支持用户自定义
        self.ignore_extensions = ignore_extensions or [
            '.md', '.txt', '.json', '.yaml', '.yml', 
            '.lock', '.gitignore', '.dockerignore',
            '.png', '.jpg', '.jpeg', '.gif', '.svg',
            '.ico', '.pdf', '.zip', '.tar', '.gz',
            '.woff', '.woff2', '.ttf', '.eot'
        ]
        self.ignore_dirs = ignore_dirs or [
            'node_modules', 'vendor', 'dist', 'build',
            '__pycache__', '.git', '.idea', '.vscode'
        ]
        
        # 设置提交人过滤配置
        self.filter_authors = filter_authors or []
        
    def _should_review_author(self, author_name: str) -> bool:
        """
        判断是否需要评审该提交人的提交
        
        Args:
            author_name: 提交人姓名
            
        Returns:
            是否需要评审
        """
        # 当 filter_authors 为空时，评审所有提交人
        if not self.filter_authors:
            return True
        
        # 当列表非空时，仅评审指定的提交人（按姓名匹配，不区分大小写）
        return author_name.lower() in [name.lower() for name in self.filter_authors]
    
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
        
        支持的文件类型: Python, JavaScript, TypeScript, Vue, Java, C++, C#, Go, 等技术文件
        忽略的文件类型和目录可事先配置
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否需要评审
        """
        # 检查文件扩展名
        for ext in self.ignore_extensions:
            if file_path.endswith(ext):
                return False
        
        # 检查目录
        for dir_name in self.ignore_dirs:
            if f'/{dir_name}/' in file_path or file_path.startswith(f'{dir_name}/'):
                return False
        
        return True
    
    def review_diff(self, diff_info: Dict, rules: List[str], commits: Optional[List[Dict]] = None) -> Optional[Dict]:
        """
        评审单个文件的差异
        
        Args:
            diff_info: 差异信息
            rules: 评审规则
            commits: 提交记录列表，用于关联提交人信息
            
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
        
        # 对于新增文件，即使没有diff也需要评审（使用整个文件内容）
        code_content = diff_info.get('diff', '')
        if diff_info.get('new_file'):
            logger.info(f"评审新增文件: {file_path}")
            # 为新增文件尝试获取完整文件内容
            if not code_content or code_content.strip() == '':
                logger.debug(f"新增文件 {file_path} 的diff为空，尝试获取完整文件内容")
                full_content = self.gitlab_client.get_file_content(file_path, diff_info.get('review_branch', 'HEAD'))
                if full_content:
                    # 构造类似diff格式的内容（全部为新增）
                    code_content = '\n'.join([f'+ {line}' for line in full_content.split('\n')])
                    logger.debug(f"成功获取新增文件 {file_path} 的完整内容")
        elif not code_content:
            logger.info(f"跳过无差异文件: {file_path}")
            return None
        
        logger.info(f"评审文件: {file_path}")
        
        # 使用大模型评审
        review_result = self.llm_client.review_code(
            code_diff=code_content,
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
        
        # 为每个问题添加代码段落和提交人信息
        if review_result.get('issues'):
            # 根据文件路径和提交列表，找到修改该文件的提交人
            commit_author = self._get_file_commit_author(diff_info['file_path'], commits)
            
            for issue in review_result['issues']:
                # 添加提交人信息
                if commit_author:
                    issue['author'] = commit_author.get('author_name', 'Unknown')
                else:
                    # 如果未能从commits中找到提交人，记录警告
                    logger.warning(f"未能为文件 {file_path} 找到任何提交人，commits列表为空或无法获取: {len(commits) if commits else 0}")
                    issue['author'] = 'Unknown'
                
                line_info = issue.get('line', '')
                
                # 验证行号信息 - 一些大模型可能返回缺陷行号
                if line_info and isinstance(line_info, str):
                    # 提取有效的数字（删除非数字字符）
                    import re
                    valid_line_match = re.search(r'\d+(?:-\d+)?', str(line_info))
                    if not valid_line_match:
                        logger.debug(f"问题缺少有效的行号 [{file_path}] - 原始行号: {line_info}")
                        continue  # 跳过此问题，不提取code_snippet
                    # 使用提取出的有效行号
                    line_info = valid_line_match.group()
                
                code_snippet = self._extract_code_snippet(
                    diff_info.get('diff', ''),
                    line_info
                )
                if code_snippet:
                    issue['code_snippet'] = code_snippet
                else:
                    # 代码段落提取失败时记录详细信息用于诊断
                    if line_info and line_info != 'N/A':
                        diff_preview = diff_info.get('diff', '')[:200]  # 获取diff前200个字符用于诊断
                        logger.info(f"提取代码段落失败 [{file_path}] - 行号: '{line_info}' (类型: {type(line_info).__name__}), Diff长度: {len(diff_info.get('diff', ''))}, Diff预览: {diff_preview}")
                    else:
                        logger.debug(f"问题缺少行号信息 [{file_path}]")
        
        return review_result
    
    def _get_file_commit_author(self, file_path: str, commits: Optional[List[Dict]]) -> Optional[Dict]:
        """
        根据文件路径找到修改该文件的提交人
        
        在direct模式下，使用第一个提交（源分支最早的提交）作为变更的原始发起者
        在all_commits模式下，使用真正修改该文件的提交人（跳过合并账号）
        
        Args:
            file_path: 文件路径
            commits: 提交记录列表
            
        Returns:
            提交信息（包含author_name等），如果找不到则返回None
        """
        if not commits:
            return None
        
        # 判断是direct还是all_commits模式
        # all_commits模式的提交有modified_files字段
        has_modified_files = any('modified_files' in c for c in commits)
        
        if has_modified_files:
            # all_commits模式：找到真正修改该文件的提交（非合并账号）
            for commit in commits:
                modified_files = commit.get('modified_files', [])
                
                # 检查该文件是否在此提交中被修改
                if file_path in modified_files:
                    author_name = commit.get('author_name', 'Unknown')
                    author_email = commit.get('author_email', '')
                    # 优先使用真正账号的提交（非合并账号）
                    if author_name.lower() != 'tooladmin':
                        logger.debug(f"找到文件 {file_path} 的真正修改者: {author_name} <{author_email}>")
                        return commit
            
            # 如果所有修改该文件的提交都是tooladmin，使用第一个非tooladmin的提交
            for commit in commits:
                author_name = commit.get('author_name', 'Unknown')
                if author_name.lower() != 'tooladmin':
                    logger.debug(f"未找到文件 {file_path} 的修改记录，使用提交 {author_name}")
                    return commit
            
            # 最后才用tooladmin的提交
            if commits:
                logger.warning(f"所有提交均来自合并账号，使用第一个: {commits[0]['author_name']}")
                return commits[0]
        else:
            # direct模式：使用第一个提交（源分支最早的提交）作为原始发起者
            # 按照规范，第一个提交代表变更的原始发起者
            author_name = commits[0].get('author_name', 'Unknown')
            author_email = commits[0].get('author_email', '')
            logger.debug(f"direct模式: 使用第一个提交作为原始发起者: {author_name} <{author_email}>")
            return commits[0]
        
        return None
    
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
        
        # 根据配置的分支比较策略选择不同的提交获取方法
        if self.branch_strategy == 'all_commits':
            logger.info(f"使用all_commits模式：获取两个分支之间的所有提交")
            commits = self.gitlab_client.get_commits_between_branches_all(review_branch, base_branch)
        else:
            # direct 模式（默认）
            logger.info(f"使用direct模式：仅比较两个分支之间的直接差异")
            commits = self.gitlab_client.get_commits_between_branches(review_branch, base_branch)
        
        logger.info(f"共有 {len(commits)} 个提交")
        
        # 根据配置对提交记录进行过滤
        if self.filter_authors:
            original_count = len(commits)
            commits = [c for c in commits if self._should_review_author(c.get('author_name', ''))]
            logger.info(f"提交人过滤: {original_count} -> {len(commits)} 个提交")
            
            # 如果过滤后没有任何提交，直接返回空报告
            if len(commits) == 0:
                logger.warning("过滤后没有任何提交需要评审，跳过文件扫描")
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                return {
                    'metadata': {
                        'review_branch': review_branch,
                        'base_branch': base_branch,
                        'source_branch': review_branch,
                        'target_branch': base_branch,
                        'review_time': start_time.isoformat(),
                        'duration_seconds': duration,
                        'total_commits': 0,
                        'total_files_changed': len(diffs),
                        'total_files_reviewed': 0,
                        'concurrent_mode': self.enable_concurrent
                    },
                    'commits': [],
                    'file_reviews': [],
                    'statistics': {
                        'total_issues': 0,
                        'by_severity': {'critical': 0, 'major': 0, 'minor': 0, 'suggestion': 0},
                        'total_additions': 0,
                        'total_deletions': 0
                    }
                }
        
        # 收集评审规则
        rules = self.collect_review_rules()
        logger.info(f"启用 {len(rules)} 条评审规则")
        
        if self.enable_concurrent and len(diffs) > 1:
            logger.info(f"启用并发评审模式,max_workers={self.max_workers}")
            file_reviews = self._review_concurrent(diffs, rules, commits)
        else:
            logger.info("使用串行评审模式")
            file_reviews = self._review_sequential(diffs, rules, commits)
        
        # 汇总统计
        total_issues = sum(len(r.get('issues', [])) for r in file_reviews)
        issue_by_severity = self._count_by_severity(file_reviews)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        review_report = {
            'metadata': {
                'review_branch': review_branch,  # 要评审的分支
                'base_branch': base_branch,      # 基准分支（比较徒）
                # 允许旧类型为backward compatibility
                'source_branch': review_branch,  # 废弃：使用 review_branch
                'target_branch': base_branch,    # 废弃：使用 base_branch
                'review_time': start_time.isoformat(),
                'duration_seconds': duration,
                'total_commits': len(commits),
                'total_files_changed': len(diffs),
                'total_files_reviewed': len(file_reviews),
                'concurrent_mode': self.enable_concurrent
            },
            'commits': commits,
            'file_reviews': file_reviews,
            'statistics': {
                'total_issues': total_issues,
                'by_severity': issue_by_severity,
                'total_additions': sum(d.get('additions', 0) for d in diffs),
                'total_deletions': sum(d.get('deletions', 0) for d in diffs)
            }
        }
        
        logger.info(f"评审完成,耗时 {duration:.2f} 秒,发现 {total_issues} 个问题")
        return review_report
    
    def _review_sequential(self, diffs: List[Dict], rules: List[str], commits: Optional[List[Dict]] = None) -> List[Dict]:
        """串行评审"""
        file_reviews = []
        for diff in diffs:
            result = self.review_diff(diff, rules, commits)
            if result:
                file_reviews.append(result)
        return file_reviews
    
    def _review_concurrent(self, diffs: List[Dict], rules: List[str], commits: Optional[List[Dict]] = None) -> List[Dict]:
        """并发评审"""
        file_reviews = []
        logger.info(f"启动 {self.max_workers} 个并发任务来评审 {len(diffs)} 个文件")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_diff = {
                executor.submit(self.review_diff, diff, rules, commits): diff 
                for diff in diffs
            }
            
            # 获取结果
            completed_count = 0
            for future in as_completed(future_to_diff):
                try:
                    result = future.result()
                    completed_count += 1
                    if result:
                        file_reviews.append(result)
                        issue_count = len(result.get('issues', []))
                        logger.debug(f"[并发-{completed_count}/{len(diffs)}] 成功评审 {result.get('file_path')} (问题数: {issue_count})")
                    else:
                        logger.debug(f"[并发-{completed_count}/{len(diffs)}] 跳过 {future_to_diff[future].get('file_path')}")
                except Exception as e:
                    completed_count += 1
                    diff = future_to_diff[future]
                    logger.error(f"[并发-{completed_count}/{len(diffs)}] 评审 {diff.get('file_path')} 失败: {e}")
        
        logger.info(f"并发评审完成: {completed_count}/{len(diffs)} 个文件, 发现 {sum(len(r.get('issues', [])) for r in file_reviews)} 个问题")
        return file_reviews
    
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
    
    def _extract_code_snippet(self, diff: str, line_info: str) -> Optional[Dict]:
        """
        从 diff 中提取指定行号的代码段落
        
        Args:
            diff: 代码差异文本
            line_info: 行号信息，格式为 "42" 或 "42-58"
            
        Returns:
            包含代码段落的字典，包括起始行、结束行和代码列表
        """
        if not diff or not line_info:
            return None
        
        try:
            # 解析行号信息
            if '-' in str(line_info):
                parts = str(line_info).split('-')
                start_line = int(parts[0])
                end_line = int(parts[1])
            else:
                start_line = int(line_info)
                end_line = start_line + 5  # 默认显示6行（当前行前2行，后3行）
            
            # 从 diff 中提取代码
            # diff 格式示例：
            # @@ -42,7 +42,10 @@ def method_name():
            #  context_line
            # -old_line
            # +new_line
            # 或者（对于新增文件或简化格式）：
            # + code_line
            # - code_line
            #   context_line
            
            lines = diff.split('\n')
            code_lines = []
            current_line_num = 0
            in_range = False
            has_valid_diff_header = False  # 标记是否找到有效的diff头部
            
            # 首先检查是否有标准的 @@ 头部
            for line in lines:
                if line.startswith('@@'):
                    has_valid_diff_header = True
                    break
            
            # 如果没有标准的diff头部，用简化模式处理（用于新增文件）
            if not has_valid_diff_header:
                current_line_num = 1  # 从第1行开始
            
            for line in lines:
                # 跳过 diff 头部和其他元数据
                if line.startswith('@@'):
                    # 从 @@ 行中提取起始行号
                    import re
                    match = re.search(r'\+([0-9]+)', line)
                    if match:
                        current_line_num = int(match.group(1))
                        in_range = False
                    continue
                
                if line.startswith('---') or line.startswith('+++'):
                    continue
                
                # 处理代码行
                # 注意：对于处于范围内的行，无论其是否以+、-、空格开头，都应该处理
                if line.startswith('-'):
                    # 删除的行，不计数行号
                    if in_range or (start_line <= current_line_num <= end_line + 5):
                        in_range = True
                        code_lines.append({
                            'line_num': current_line_num,
                            'type': 'deleted',
                            'content': line[1:],
                            'in_range': start_line <= current_line_num <= end_line
                        })
                elif line.startswith('+'):
                    # 新增的行，计数行号
                    if in_range or (start_line <= current_line_num <= end_line + 5):
                        in_range = True
                        code_lines.append({
                            'line_num': current_line_num,
                            'type': 'added',
                            'content': line[1:],
                            'in_range': start_line <= current_line_num <= end_line
                        })
                    current_line_num += 1
                else:
                    # 上下文行（以空格开头或其他）
                    # 计数行号，但要先检查是否在范围内
                    if in_range or (start_line <= current_line_num <= end_line + 5):
                        in_range = True
                        code_lines.append({
                            'line_num': current_line_num,
                            'type': 'context',
                            'content': line[1:] if line.startswith(' ') else line,
                            'in_range': start_line <= current_line_num <= end_line
                        })
                    current_line_num += 1
                
                if current_line_num > end_line + 5:
                    break
            
            if code_lines:
                return {
                    'start_line': start_line,
                    'end_line': end_line,
                    'lines': code_lines
                }
        
        except Exception as e:
            logger.debug(f"提取代码段落失败: {e}")
        
        return None
