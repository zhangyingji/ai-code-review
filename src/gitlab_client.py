"""
GitLab 客户端模块
用于连接 GitLab API, 拉取代码和获取差异
"""
import os
import tempfile
import gitlab
from git import Repo
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GitLabClient:
    """GitLab 客户端,用于获取代码差异"""
    
    def __init__(self, url: str, private_token: str, project_id: int):
        """
        初始化 GitLab 客户端
        
        Args:
            url: GitLab 服务器地址
            private_token: 访问令牌
            project_id: 项目ID
        """
        self.gl = gitlab.Gitlab(url, private_token=private_token, ssl_verify=False)
        self.project = self.gl.projects.get(project_id)
        self.repo_path = None
        
    def clone_repository(self, branch: str, target_dir: Optional[str] = None) -> str:
        """
        克隆仓库到本地
        
        Args:
            branch: 分支名称
            target_dir: 目标目录,如果为None则使用临时目录
            
        Returns:
            仓库本地路径
        """
        if target_dir is None:
            target_dir = os.path.join(tempfile.gettempdir(), f"code_review_{self.project.id}")
        
        # 如果目录已存在,先删除
        if os.path.exists(target_dir):
            import shutil
            shutil.rmtree(target_dir)
        
        # 构建克隆URL(包含token)
        clone_url = self.project.http_url_to_repo
        if clone_url.startswith("https://"):
            clone_url = clone_url.replace("https://", f"https://oauth2:{self.gl.private_token}@")
        
        logger.info(f"正在克隆仓库到 {target_dir}, 分支: {branch}")
        repo = Repo.clone_from(clone_url, target_dir, branch=branch)
        self.repo_path = target_dir
        
        return target_dir
    
    def get_branch_merge_base(self, review_branch: str, base_branch: str = '') -> str:
        """
        获取用于比较的基准点
        如果指定了base_branch，则直接使用
        如果未指定，则尝试自动检测review_branch的创建起点
        
        Args:
            review_branch: 要评审的分支
            base_branch: 基准分支，如果为空则自动检测
            
        Returns:
            用于比较的基准分支或提交点
        """
        if base_branch:
            logger.info(f"使用指定的基准分支: {base_branch}")
            return base_branch
        
        logger.info(f"自动检测分支 {review_branch} 的创建起点...")
        return self.get_branch_base(review_branch)
    
    def get_branch_base(self, branch: str, default_base: str = 'main') -> str:
        """
        获取分支的创建起点（分离点）
        通过分析分支的提交历史找到真正的父分支
        
        Args:
            branch: 要检查的分支名称
            default_base: 默认的基础分支（如main/master）
            
        Returns:
            分支的创建起点分支名
        """
        try:
            # 首先尝试获取分支信息
            branch_info = self.project.branches.get(branch)
            logger.info(f"分支 {branch} 最新提交: {branch_info.commit['id'][:8]}")
            
            # 获取所有分支列表
            all_branches = self.project.branches.list(all=True)
            branch_names = [b.name for b in all_branches]
            
            logger.info(f"找到 {len(branch_names)} 个分支: {', '.join(branch_names[:10])}{'...' if len(branch_names) > 10 else ''}")
            
            # 分析分支命名模式，寻找可能的父分支
            parent_branch = self._find_parent_branch_by_naming(branch, branch_names)
            if parent_branch:
                logger.info(f"通过命名模式找到父分支: {parent_branch}")
                return parent_branch
            
            # 如果通过命名无法找到，尝试通过提交历史分析
            parent_branch = self._find_parent_branch_by_history(branch, branch_names)
            if parent_branch:
                logger.info(f"通过提交历史找到父分支: {parent_branch}")
                return parent_branch
            
            # 回退到常见的主分支名称
            main_branches = [default_base, 'main', 'master', 'develop']
            for main_branch in main_branches:
                if main_branch in branch_names:
                    logger.info(f"回退到常见主分支: {main_branch}")
                    return main_branch
            
            # 如果都没找到，返回默认值
            logger.warning(f"无法确定分支 {branch} 的创建起点，使用默认: {default_base}")
            return default_base
            
        except Exception as e:
            logger.error(f"获取分支创建起点失败: {e}")
            return default_base
    
    def _find_parent_branch_by_naming(self, branch: str, all_branches: List[str]) -> Optional[str]:
        """
        通过分支命名模式查找父分支
        例如: 202512_YD_1205 -> 202511_YD_1114
        """
        try:
            # 简单的命名模式匹配
            # 如果分支名包含版本号模式，尝试找到前一个版本
            import re
            
            # 匹配类似 202512_YD_1205 的模式
            pattern = r'(\d{4})(\d{2})_([A-Z]+)_(\d+)'
            match = re.match(pattern, branch)
            
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                prefix = match.group(3)
                version = int(match.group(4))
                
                # 寻找前一个版本
                if version > 1:
                    expected_parent = f"{year}{month:02d}_{prefix}_{version-1:04d}"
                    if expected_parent in all_branches:
                        return expected_parent
                
                # 寻找前一个月的版本
                if month > 1:
                    expected_parent = f"{year}{month-1:02d}_{prefix}_{version}"
                    if expected_parent in all_branches:
                        return expected_parent
                elif year > 2020:  # 回到上一年
                    expected_parent = f"{year-1}12_{prefix}_{version}"
                    if expected_parent in all_branches:
                        return expected_parent
            
            return None
        except Exception as e:
            logger.debug(f"通过命名模式查找父分支失败: {e}")
            return None
    
    def _find_parent_branch_by_history(self, branch: str, all_branches: List[str]) -> Optional[str]:
        """
        通过提交历史查找父分支
        """
        try:
            # 获取当前分支的提交历史
            commits = self.project.commits.list(ref_name=branch, per_page=50)
            
            # 检查每个提交是否存在于其他分支中
            for commit in commits[-10:]:  # 检查最早的10个提交
                commit_detail = self.project.commits.get(commit.id)
                
                # 检查这个提交在哪些分支中存在
                for branch_name in all_branches:
                    if branch_name == branch:  # 跳过当前分支
                        continue
                    
                    try:
                        # 检查提交是否在该分支中
                        branch_commits = self.project.commits.list(ref_name=branch_name, per_page=100)
                        commit_ids = [c.id for c in branch_commits]
                        
                        if commit.id in commit_ids:
                            # 找到包含该提交的分支，这很可能是父分支
                            return branch_name
                    except:
                        continue
            
            return None
        except Exception as e:
            logger.debug(f"通过提交历史查找父分支失败: {e}")
            return None
    
    def get_diff_between_branches(self, source_branch: str, target_branch: str) -> List[Dict]:
        """
        获取两个分支之间的差异
        
        Args:
            source_branch: 源分支
            target_branch: 目标分支
            
        Returns:
            差异文件列表,每个元素包含文件信息和差异内容
        """
        logger.info(f"获取分支差异: {target_branch} -> {source_branch}")
        
        # 使用 GitLab API 获取比较结果
        comparison = self.project.repository_compare(target_branch, source_branch)
        
        diffs = []
        for diff in comparison['diffs']:
            diff_info = {
                'file_path': diff['new_path'],
                'old_path': diff['old_path'],
                'new_file': diff['new_file'],
                'deleted_file': diff['deleted_file'],
                'renamed_file': diff['renamed_file'],
                'diff': diff['diff'],
                'additions': 0,
                'deletions': 0
            }
            
            # 统计增删行数
            if diff['diff']:
                for line in diff['diff'].split('\n'):
                    if line.startswith('+') and not line.startswith('+++'):
                        diff_info['additions'] += 1
                    elif line.startswith('-') and not line.startswith('---'):
                        diff_info['deletions'] += 1
            
            diffs.append(diff_info)
        
        logger.info(f"共找到 {len(diffs)} 个差异文件")
        return diffs
    
    def get_commits_between_branches(self, source_branch: str, target_branch: str) -> List[Dict]:
        """
        获取两个分支之间的提交记录
        
        Args:
            source_branch: 源分支
            target_branch: 目标分支
            
        Returns:
            提交记录列表
        """
        comparison = self.project.repository_compare(target_branch, source_branch)
        
        commits = []
        for commit in comparison['commits']:
            commits.append({
                'id': commit['id'],
                'short_id': commit['short_id'],
                'title': commit['title'],
                'message': commit['message'],
                'author_name': commit['author_name'],
                'author_email': commit['author_email'],
                'created_at': commit['created_at']
            })
        
        return commits
    
    def get_file_content(self, file_path: str, ref: str) -> Optional[str]:
        """
        获取指定版本的文件内容
        
        Args:
            file_path: 文件路径
            ref: 分支名或commit ID
            
        Returns:
            文件内容
        """
        try:
            file_info = self.project.files.get(file_path=file_path, ref=ref)
            import base64
            return base64.b64decode(file_info.content).decode('utf-8')
        except Exception as e:
            logger.warning(f"无法获取文件内容 {file_path}@{ref}: {e}")
            return None
    
    def cleanup(self):
        """清理临时文件"""
        if self.repo_path and os.path.exists(self.repo_path):
            import shutil
            shutil.rmtree(self.repo_path)
            logger.info(f"已清理临时目录: {self.repo_path}")
