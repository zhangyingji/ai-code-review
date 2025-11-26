"""
MySQL存储实现
使用SQLAlchemy ORM实现评审结果的MySQL存储
"""
import logging
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import create_engine, and_, or_, func
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

from .base_storage import BaseStorage
from .models import Base, ReviewRecord, ReviewIssue

logger = logging.getLogger(__name__)


class MySQLStorage(BaseStorage):
    """MySQL存储实现类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化MySQL存储
        
        Args:
            config: 数据库配置字典，包含host, port, database, username, password等
        """
        self.config = config
        self.engine = None
        self.Session = None
        self._init_connection()
    
    def _init_connection(self):
        """初始化数据库连接"""
        try:
            conn_config = self.config.get('connection', {})
            connection_string = (
                f"mysql+pymysql://{conn_config['username']}:{conn_config['password']}"
                f"@{conn_config['host']}:{conn_config.get('port', 3306)}"
                f"/{conn_config['database']}"
                f"?charset={conn_config.get('charset', 'utf8mb4')}"
            )
            
            pool_size = self.config.get('pool_size', 10)
            self.engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=pool_size,
                pool_recycle=3600,
                echo=False
            )
            
            self.Session = scoped_session(sessionmaker(bind=self.engine))
            logger.info("MySQL存储初始化成功")
        except Exception as e:
            logger.error(f"MySQL连接失败: {e}")
            raise
    
    def save_review(self, review_data: Dict[str, Any]) -> str:
        """保存评审数据（仅保存基本记录）"""
        return self.save_review_with_issues(review_data)
    
    def save_review_with_issues(self, review_data: Dict[str, Any]) -> str:
        """保存评审记录及问题详情"""
        session = self.Session()
        try:
            metadata = review_data.get('metadata', {})
            statistics = review_data.get('statistics', {})
            
            # 创建评审记录
            review_record = ReviewRecord(
                review_id=str(uuid.uuid4()),
                project_id=metadata.get('project_id', 0),
                project_name=metadata.get('project_name', ''),
                review_branch=metadata.get('review_branch', ''),
                base_branch=metadata.get('base_branch', ''),
                review_time=datetime.fromisoformat(metadata.get('review_time', datetime.now().isoformat())),
                duration_seconds=metadata.get('duration_seconds', 0),
                total_commits=metadata.get('total_commits', 0),
                total_files_reviewed=metadata.get('total_files_reviewed', 0),
                total_issues=statistics.get('total_issues', 0),
                critical_count=statistics.get('by_severity', {}).get('critical', 0),
                major_count=statistics.get('by_severity', {}).get('major', 0),
                minor_count=statistics.get('by_severity', {}).get('minor', 0),
                suggestion_count=statistics.get('by_severity', {}).get('suggestion', 0),
                time_filter_enabled=1 if metadata.get('time_filter_enabled') else 0,
                time_filter_since=metadata.get('time_filter_since'),
                time_filter_until=metadata.get('time_filter_until'),
                time_filter_timezone=metadata.get('time_filter_timezone')
            )
            
            session.add(review_record)
            session.flush()  # 获取review_id
            
            # 保存问题详情
            file_reviews = review_data.get('file_reviews', [])
            for file_review in file_reviews:
                issues = file_review.get('issues', [])
                file_path = file_review.get('file_path', '')
                
                for issue in issues:
                    review_issue = ReviewIssue(
                        issue_id=str(uuid.uuid4()),
                        review_id=review_record.review_id,
                        file_path=file_path,
                        line_number=str(issue.get('line', '')),
                        issue_type=issue.get('type', ''),
                        severity=issue.get('severity', 'minor'),
                        description=issue.get('description', ''),
                        suggestion=issue.get('suggestion', ''),
                        code_snippet=json.dumps(issue.get('code_snippet')) if issue.get('code_snippet') else None,
                        author_name=issue.get('author', ''),
                        author_email=issue.get('author_email', ''),
                        status='pending'
                    )
                    session.add(review_issue)
            
            session.commit()
            logger.info(f"评审记录保存成功: {review_record.review_id}")
            return review_record.review_id
            
        except Exception as e:
            session.rollback()
            logger.error(f"保存评审数据失败: {e}")
            raise
        finally:
            session.close()
    
    def get_review(self, review_id: str) -> Optional[Dict[str, Any]]:
        """获取评审数据"""
        session = self.Session()
        try:
            record = session.query(ReviewRecord).filter_by(review_id=review_id).first()
            if not record:
                return None
            
            return self._record_to_dict(record)
        finally:
            session.close()
    
    def list_reviews(self, project: str = None, branch: str = None,
                    start_date: datetime = None, end_date: datetime = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """列出评审记录"""
        session = self.Session()
        try:
            query = session.query(ReviewRecord)
            
            if project:
                query = query.filter(ReviewRecord.project_name == project)
            if branch:
                query = query.filter(ReviewRecord.review_branch == branch)
            if start_date:
                query = query.filter(ReviewRecord.review_time >= start_date)
            if end_date:
                query = query.filter(ReviewRecord.review_time <= end_date)
            
            records = query.order_by(ReviewRecord.review_time.desc()).limit(limit).all()
            return [self._record_to_dict(r) for r in records]
        finally:
            session.close()
    
    def delete_review(self, review_id: str) -> bool:
        """删除评审记录"""
        session = self.Session()
        try:
            record = session.query(ReviewRecord).filter_by(review_id=review_id).first()
            if record:
                session.delete(record)
                session.commit()
                logger.info(f"删除评审记录: {review_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"删除评审记录失败: {e}")
            return False
        finally:
            session.close()
    
    def get_statistics(self, project: str = None, time_range: int = 30) -> Dict[str, Any]:
        """获取统计信息"""
        session = self.Session()
        try:
            query = session.query(ReviewRecord)
            
            # 时间范围过滤
            since_date = datetime.now() - timedelta(days=time_range)
            query = query.filter(ReviewRecord.review_time >= since_date)
            
            if project:
                query = query.filter(ReviewRecord.project_name == project)
            
            records = query.all()
            
            total_reviews = len(records)
            total_issues = sum(r.total_issues for r in records)
            
            return {
                'total_reviews': total_reviews,
                'total_issues': total_issues,
                'time_range_days': time_range,
                'project': project
            }
        finally:
            session.close()
    
    def get_issue_by_id(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """根据问题ID获取问题详情"""
        session = self.Session()
        try:
            issue = session.query(ReviewIssue).filter_by(issue_id=issue_id).first()
            if not issue:
                return None
            return self._issue_to_dict(issue)
        finally:
            session.close()
    
    def update_issue_status(self, issue_id: str, status: str,
                           verified_by: str = None, note: str = None) -> bool:
        """更新问题状态"""
        session = self.Session()
        try:
            issue = session.query(ReviewIssue).filter_by(issue_id=issue_id).first()
            if not issue:
                return False
            
            issue.status = status
            if verified_by:
                issue.verified_by = verified_by
            if note:
                issue.verification_note = note
            issue.verified_at = datetime.now()
            
            session.commit()
            logger.info(f"更新问题状态: {issue_id} -> {status}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"更新问题状态失败: {e}")
            return False
        finally:
            session.close()
    
    def list_issues_by_review(self, review_id: str) -> List[Dict[str, Any]]:
        """获取某次评审的所有问题"""
        session = self.Session()
        try:
            issues = session.query(ReviewIssue).filter_by(review_id=review_id).all()
            return [self._issue_to_dict(i) for i in issues]
        finally:
            session.close()
    
    def list_issues_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """按状态查询问题"""
        session = self.Session()
        try:
            issues = session.query(ReviewIssue).filter_by(status=status).limit(limit).all()
            return [self._issue_to_dict(i) for i in issues]
        finally:
            session.close()
    
    def get_issue_statistics(self, project_id: int = None, time_range: int = 30) -> Dict[str, Any]:
        """获取问题统计信息"""
        session = self.Session()
        try:
            # 获取时间范围内的评审记录
            since_date = datetime.now() - timedelta(days=time_range)
            review_query = session.query(ReviewRecord.review_id).filter(
                ReviewRecord.review_time >= since_date
            )
            
            if project_id:
                review_query = review_query.filter(ReviewRecord.project_id == project_id)
            
            review_ids = [r[0] for r in review_query.all()]
            
            # 统计问题
            issue_query = session.query(ReviewIssue).filter(
                ReviewIssue.review_id.in_(review_ids)
            )
            
            total_issues = issue_query.count()
            pending_issues = issue_query.filter(ReviewIssue.status == 'pending').count()
            confirmed_issues = issue_query.filter(ReviewIssue.status == 'confirmed').count()
            false_positive_issues = issue_query.filter(ReviewIssue.status == 'false_positive').count()
            
            return {
                'total_issues': total_issues,
                'pending': pending_issues,
                'confirmed': confirmed_issues,
                'false_positive': false_positive_issues,
                'time_range_days': time_range,
                'project_id': project_id
            }
        finally:
            session.close()
    
    def _record_to_dict(self, record: ReviewRecord) -> Dict[str, Any]:
        """将ORM对象转换为字典"""
        return {
            'review_id': record.review_id,
            'project_id': record.project_id,
            'project_name': record.project_name,
            'review_branch': record.review_branch,
            'base_branch': record.base_branch,
            'review_time': record.review_time.isoformat() if record.review_time else None,
            'duration_seconds': record.duration_seconds,
            'total_commits': record.total_commits,
            'total_files_reviewed': record.total_files_reviewed,
            'total_issues': record.total_issues,
            'critical_count': record.critical_count,
            'major_count': record.major_count,
            'minor_count': record.minor_count,
            'suggestion_count': record.suggestion_count,
            'created_at': record.created_at.isoformat() if record.created_at else None
        }
    
    def _issue_to_dict(self, issue: ReviewIssue) -> Dict[str, Any]:
        """将问题ORM对象转换为字典"""
        code_snippet = None
        if issue.code_snippet:
            try:
                code_snippet = json.loads(issue.code_snippet)
            except:
                pass
        
        return {
            'issue_id': issue.issue_id,
            'review_id': issue.review_id,
            'file_path': issue.file_path,
            'line_number': issue.line_number,
            'issue_type': issue.issue_type,
            'severity': issue.severity,
            'description': issue.description,
            'suggestion': issue.suggestion,
            'code_snippet': code_snippet,
            'author_name': issue.author_name,
            'author_email': issue.author_email,
            'status': issue.status,
            'verified_by': issue.verified_by,
            'verified_at': issue.verified_at.isoformat() if issue.verified_at else None,
            'verification_note': issue.verification_note,
            'created_at': issue.created_at.isoformat() if issue.created_at else None
        }
