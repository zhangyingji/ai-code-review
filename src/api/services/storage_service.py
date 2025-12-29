"""
存储服务 - 将评审结果保存到数据库
"""
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

from ..models.review_models import ReviewSession, ReviewFile, ReviewIssue, CommitInfo

logger = logging.getLogger(__name__)


class StorageService:
    """存储服务 - 负责将评审数据保存到数据库"""
    
    def __init__(self, db_session: Session):
        """
        初始化存储服务
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def save_review_data(self, review_data: Dict[str, Any]) -> str:
        """
        保存评审数据到数据库
        
        Args:
            review_data: 评审引擎生成的评审数据字典
            
        Returns:
            会话UUID
            
        Raises:
            Exception: 保存失败时抛出异常
        """
        try:
            # 生成会话UUID
            session_uuid = str(uuid.uuid4())
            
            logger.info(f"开始保存评审数据，会话UUID: {session_uuid}")
            
            # 开始事务
            # 1. 创建评审会话
            session = self._create_review_session(review_data, session_uuid)
            self.db.add(session)
            self.db.flush()  # 刷新以获取session.id
            
            session_id = session.id
            logger.debug(f"评审会话已创建，ID: {session_id}")
            
            # 2. 保存提交信息
            if review_data.get('commits'):
                self._save_commits(session_id, review_data['commits'])
                logger.debug(f"已保存 {len(review_data['commits'])} 条提交信息")
            
            # 3. 保存文件和问题信息
            if review_data.get('file_reviews'):
                self._save_files_and_issues(session_id, review_data['file_reviews'])
                logger.debug(f"已保存 {len(review_data['file_reviews'])} 个文件的评审信息")
            
            # 提交事务
            self.db.commit()
            
            logger.info(f"评审数据保存成功，会话UUID: {session_uuid}, ID: {session_id}")
            return session_uuid
            
        except Exception as e:
            # 回滚事务
            self.db.rollback()
            logger.error(f"保存评审数据失败: {e}", exc_info=True)
            raise Exception(f"保存评审数据失败: {e}")
    
    def _create_review_session(self, review_data: Dict[str, Any], session_uuid: str) -> ReviewSession:
        """
        创建评审会话记录
        
        Args:
            review_data: 评审数据
            session_uuid: 会话UUID
            
        Returns:
            ReviewSession对象
        """
        metadata = review_data['metadata']
        statistics = review_data['statistics']
        
        # 解析评审时间
        review_time_str = metadata.get('review_time')
        if isinstance(review_time_str, str):
            review_time = datetime.fromisoformat(review_time_str)
        else:
            review_time = review_time_str or datetime.now()
        
        session = ReviewSession(
            session_uuid=session_uuid,
            project_name=metadata.get('project_name', ''),
            review_branch=metadata.get('review_branch') or metadata.get('source_branch', ''),
            base_branch=metadata.get('base_branch') or metadata.get('target_branch', ''),
            review_time=review_time,
            duration_seconds=metadata.get('duration_seconds', 0),
            total_commits=metadata.get('total_commits', 0),
            total_files_changed=metadata.get('total_files_changed', 0),
            total_files_reviewed=metadata.get('total_files_reviewed', 0),
            total_issues=statistics.get('total_issues', 0),
            critical_count=statistics.get('by_severity', {}).get('critical', 0),
            major_count=statistics.get('by_severity', {}).get('major', 0),
            minor_count=statistics.get('by_severity', {}).get('minor', 0),
            suggestion_count=statistics.get('by_severity', {}).get('suggestion', 0),
            total_additions=statistics.get('total_additions', 0),
            total_deletions=statistics.get('total_deletions', 0),
            concurrent_mode=metadata.get('concurrent_mode', False)
        )
        
        return session
    
    def _save_commits(self, session_id: int, commits: list):
        """
        保存提交信息
        
        Args:
            session_id: 会话ID
            commits: 提交信息列表
        """
        for commit in commits:
            # 解析提交时间
            commit_time_str = commit.get('commit_time')
            if isinstance(commit_time_str, str):
                try:
                    commit_time = datetime.fromisoformat(commit_time_str)
                except:
                    commit_time = None
            else:
                commit_time = commit_time_str
            
            commit_info = CommitInfo(
                session_id=session_id,
                commit_id=commit.get('commit_id', ''),
                author_name=commit.get('author_name', ''),
                author_email=commit.get('author_email', ''),
                commit_message=commit.get('commit_message', ''),
                commit_time=commit_time
            )
            self.db.add(commit_info)
    
    def _save_files_and_issues(self, session_id: int, file_reviews: list):
        """
        保存文件和问题信息
        
        Args:
            session_id: 会话ID
            file_reviews: 文件评审列表
        """
        for file_review in file_reviews:
            # 创建文件记录
            file_path = file_review.get('file_path', '')
            issues = file_review.get('issues', [])
            
            review_file = ReviewFile(
                session_id=session_id,
                file_path=file_path,
                additions=file_review.get('additions', 0),
                deletions=file_review.get('deletions', 0),
                new_file=file_review.get('new_file', False),
                renamed_file=file_review.get('renamed_file', False),
                issue_count=len(issues)
            )
            self.db.add(review_file)
            self.db.flush()  # 刷新以获取file_id
            
            # 保存问题
            if issues:
                self._save_issues(session_id, review_file.id, file_path, issues)
    
    def _save_issues(self, session_id: int, file_id: int, file_path: str, issues: list):
        """
        保存问题信息
        
        Args:
            session_id: 会话ID
            file_id: 文件ID
            file_path: 文件路径
            issues: 问题列表
        """
        for issue in issues:
            # 将code_snippet转换为JSON字符串
            code_snippet = issue.get('code_snippet')
            if code_snippet and isinstance(code_snippet, dict):
                code_snippet_json = json.dumps(code_snippet, ensure_ascii=False)
            else:
                code_snippet_json = None
            
            review_issue = ReviewIssue(
                session_id=session_id,
                file_id=file_id,
                file_path=file_path,
                severity=issue.get('severity', 'minor'),
                category=issue.get('category', ''),
                author=issue.get('author', ''),
                line_info=issue.get('line', ''),
                method_name=issue.get('method', ''),
                description=issue.get('description', ''),
                suggestion=issue.get('suggestion', ''),
                code_snippet_json=code_snippet_json,
                matched_rule=issue.get('matched_rule', ''),
                matched_rule_category=issue.get('matched_rule_category', ''),
                confirm_status='pending',
                is_fixed=False,
                review_comment=''
            )
            self.db.add(review_issue)
