"""
查询服务 - 提供数据查询和统计功能
"""
import logging
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from ..models.review_models import ReviewSession, ReviewFile, ReviewIssue, CommitInfo
from ..schemas.review_schemas import (
    ReviewSessionResponse, ReviewSessionListResponse,
    ReviewIssueResponse, ReviewIssueListResponse,
    ReviewIssueUpdate, BatchUpdateResponse,
    StatisticsOverview, SeverityStats
)

logger = logging.getLogger(__name__)


class QueryService:
    """查询服务 - 负责数据查询和统计"""
    
    def __init__(self, db_session: Session):
        """
        初始化查询服务
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def get_review_sessions(self,
                           page: int = 1,
                           page_size: int = 20,
                           project_name: Optional[str] = None,
                           review_branch: Optional[str] = None,
                           base_branch: Optional[str] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           min_issues: Optional[int] = None) -> ReviewSessionListResponse:
        """
        获取评审会话列表
        
        Args:
            page: 页码
            page_size: 每页数量
            project_name: 项目名称筛选
            review_branch: 评审分支筛选
            base_branch: 基准分支筛选
            start_date: 开始日期
            end_date: 结束日期
            min_issues: 最小问题数
            
        Returns:
            评审会话列表响应
        """
        # 构建查询
        query = self.db.query(ReviewSession)
        
        # 应用筛选条件
        if project_name:
            query = query.filter(ReviewSession.project_name.like(f'%{project_name}%'))
        if review_branch:
            query = query.filter(ReviewSession.review_branch.like(f'%{review_branch}%'))
        if base_branch:
            query = query.filter(ReviewSession.base_branch == base_branch)
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(ReviewSession.review_time >= start_dt)
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(ReviewSession.review_time <= end_dt)
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date}")
        if min_issues is not None:
            query = query.filter(ReviewSession.total_issues >= min_issues)
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        offset = (page - 1) * page_size
        sessions = query.order_by(desc(ReviewSession.review_time)).offset(offset).limit(page_size).all()
        
        # 转换为响应模型
        items = [ReviewSessionResponse.from_orm_with_stats(s) for s in sessions]
        
        return ReviewSessionListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )
    
    def get_review_session(self, session_id: int) -> Optional[ReviewSessionResponse]:
        """
        获取单个评审会话详情
        
        Args:
            session_id: 会话ID
            
        Returns:
            评审会话响应，不存在则返回None
        """
        session = self.db.query(ReviewSession).filter(ReviewSession.id == session_id).first()
        if not session:
            return None
        return ReviewSessionResponse.from_orm_with_stats(session)
    
    def get_review_issues(self,
                         session_id: int,
                         page: int = 1,
                         page_size: int = 50,
                         severity: Optional[str] = None,
                         author: Optional[str] = None,
                         confirm_status: Optional[str] = None,
                         is_fixed: Optional[bool] = None,
                         file_path: Optional[str] = None) -> ReviewIssueListResponse:
        """
        获取评审问题列表
        
        Args:
            session_id: 会话ID
            page: 页码
            page_size: 每页数量
            severity: 严重程度筛选（逗号分隔）
            author: 提交人筛选
            confirm_status: 确认意见筛选
            is_fixed: 是否已修改筛选
            file_path: 文件路径模糊搜索
            
        Returns:
            评审问题列表响应
        """
        # 构建查询
        query = self.db.query(ReviewIssue).filter(ReviewIssue.session_id == session_id)
        
        # 应用筛选条件
        if severity:
            # 支持多个严重程度，逗号分隔
            severities = [s.strip() for s in severity.split(',')]
            query = query.filter(ReviewIssue.severity.in_(severities))
        if author:
            query = query.filter(ReviewIssue.author == author)
        if confirm_status:
            query = query.filter(ReviewIssue.confirm_status == confirm_status)
        if is_fixed is not None:
            query = query.filter(ReviewIssue.is_fixed == is_fixed)
        if file_path:
            query = query.filter(ReviewIssue.file_path.like(f'%{file_path}%'))
        
        # 获取总数
        total = query.count()
        
        # 分页和排序（按严重程度和创建时间）
        offset = (page - 1) * page_size
        # 严重程度排序：critical > major > minor > suggestion
        severity_order = {
            'critical': 0,
            'major': 1,
            'minor': 2,
            'suggestion': 3
        }
        
        issues = query.order_by(ReviewIssue.created_at).offset(offset).limit(page_size).all()
        
        # 按严重程度排序
        issues.sort(key=lambda x: (severity_order.get(x.severity, 99), x.created_at))
        
        # 转换为响应模型
        items = [ReviewIssueResponse.from_orm(i) for i in issues]
        
        return ReviewIssueListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )
    
    def update_issue(self, issue_id: int, update_data: ReviewIssueUpdate) -> Optional[ReviewIssueResponse]:
        """
        更新问题状态
        
        Args:
            issue_id: 问题ID
            update_data: 更新数据
            
        Returns:
            更新后的问题响应，不存在则返回None
        """
        issue = self.db.query(ReviewIssue).filter(ReviewIssue.id == issue_id).first()
        if not issue:
            return None
        
        # 更新字段
        if update_data.confirm_status is not None:
            issue.confirm_status = update_data.confirm_status
        if update_data.is_fixed is not None:
            issue.is_fixed = update_data.is_fixed
        if update_data.review_comment is not None:
            issue.review_comment = update_data.review_comment
        
        # 更新时间
        issue.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(issue)
        
        return ReviewIssueResponse.from_orm(issue)
    
    def batch_update_issues(self, 
                           issue_ids: List[int],
                           confirm_status: Optional[str] = None,
                           is_fixed: Optional[bool] = None) -> BatchUpdateResponse:
        """
        批量更新问题
        
        Args:
            issue_ids: 问题ID列表
            confirm_status: 确认意见
            is_fixed: 是否已修改
            
        Returns:
            批量更新响应
        """
        # 查询所有问题
        issues = self.db.query(ReviewIssue).filter(ReviewIssue.id.in_(issue_ids)).all()
        
        # 更新字段
        updated_count = 0
        for issue in issues:
            if confirm_status is not None:
                issue.confirm_status = confirm_status
            if is_fixed is not None:
                issue.is_fixed = is_fixed
            issue.updated_at = datetime.now()
            updated_count += 1
        
        self.db.commit()
        
        return BatchUpdateResponse(updated_count=updated_count)
    
    def get_statistics_overview(self,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               project_name: Optional[str] = None) -> StatisticsOverview:
        """
        获取统计概览
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            project_name: 项目筛选
            
        Returns:
            统计概览
        """
        # 构建查询
        session_query = self.db.query(ReviewSession)
        issue_query = self.db.query(ReviewIssue)
        
        # 应用筛选条件
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                session_query = session_query.filter(ReviewSession.review_time >= start_dt)
                # 通过session关联筛选issue
                issue_query = issue_query.join(ReviewSession).filter(ReviewSession.review_time >= start_dt)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                session_query = session_query.filter(ReviewSession.review_time <= end_dt)
                issue_query = issue_query.join(ReviewSession).filter(ReviewSession.review_time <= end_dt)
            except ValueError:
                pass
        if project_name:
            session_query = session_query.filter(ReviewSession.project_name == project_name)
            issue_query = issue_query.join(ReviewSession).filter(ReviewSession.project_name == project_name)
        
        # 统计评审次数
        total_reviews = session_query.count()
        
        # 统计总问题数
        total_issues = issue_query.count()
        
        # 严重程度分布
        severity_stats = self.db.query(
            ReviewIssue.severity,
            func.count(ReviewIssue.id).label('count')
        ).group_by(ReviewIssue.severity).all()
        
        severity_distribution = SeverityStats()
        for severity, count in severity_stats:
            if severity == 'critical':
                severity_distribution.critical = count
            elif severity == 'major':
                severity_distribution.major = count
            elif severity == 'minor':
                severity_distribution.minor = count
            elif severity == 'suggestion':
                severity_distribution.suggestion = count
        
        # Top作者
        top_authors_query = self.db.query(
            ReviewIssue.author,
            func.count(ReviewIssue.id).label('issue_count')
        ).filter(
            ReviewIssue.author.isnot(None),
            ReviewIssue.author != ''
        ).group_by(ReviewIssue.author).order_by(desc('issue_count')).limit(10).all()
        
        top_authors = [
            {"author": author, "issue_count": count}
            for author, count in top_authors_query
        ]
        
        # 趋势数据（按日期统计）
        trend_data = []  # TODO: 实现趋势数据统计
        
        return StatisticsOverview(
            total_reviews=total_reviews,
            total_issues=total_issues,
            severity_distribution=severity_distribution,
            top_authors=top_authors,
            trend_data=trend_data
        )
"""
查询服务 - 提供数据查询和统计功能
"""
import logging
from datetime import datetime
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from ..models.review_models import ReviewSession, ReviewFile, ReviewIssue, CommitInfo
from ..schemas.review_schemas import (
    ReviewSessionResponse, ReviewSessionListResponse,
    ReviewIssueResponse, ReviewIssueListResponse,
    ReviewIssueUpdate, BatchUpdateResponse,
    StatisticsOverview, SeverityStats
)

logger = logging.getLogger(__name__)


class QueryService:
    """查询服务 - 负责数据查询和统计"""
    
    def __init__(self, db_session: Session):
        """
        初始化查询服务
        
        Args:
            db_session: 数据库会话
        """
        self.db = db_session
    
    def get_review_sessions(self,
                           page: int = 1,
                           page_size: int = 20,
                           project_name: Optional[str] = None,
                           review_branch: Optional[str] = None,
                           base_branch: Optional[str] = None,
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None,
                           min_issues: Optional[int] = None) -> ReviewSessionListResponse:
        """
        获取评审会话列表
        
        Args:
            page: 页码
            page_size: 每页数量
            project_name: 项目名称筛选
            review_branch: 评审分支筛选
            base_branch: 基准分支筛选
            start_date: 开始日期
            end_date: 结束日期
            min_issues: 最小问题数
            
        Returns:
            评审会话列表响应
        """
        # 构建查询
        query = self.db.query(ReviewSession)
        
        # 应用筛选条件
        if project_name:
            query = query.filter(ReviewSession.project_name.like(f'%{project_name}%'))
        if review_branch:
            query = query.filter(ReviewSession.review_branch.like(f'%{review_branch}%'))
        if base_branch:
            query = query.filter(ReviewSession.base_branch == base_branch)
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(ReviewSession.review_time >= start_dt)
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date}")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(ReviewSession.review_time <= end_dt)
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date}")
        if min_issues is not None:
            query = query.filter(ReviewSession.total_issues >= min_issues)
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        offset = (page - 1) * page_size
        sessions = query.order_by(desc(ReviewSession.review_time)).offset(offset).limit(page_size).all()
        
        # 转换为响应模型
        items = [ReviewSessionResponse.from_orm_with_stats(s) for s in sessions]
        
        return ReviewSessionListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )
    
    def get_review_session(self, session_id: int) -> Optional[ReviewSessionResponse]:
        """
        获取单个评审会话详情
        
        Args:
            session_id: 会话ID
            
        Returns:
            评审会话响应，不存在则返回None
        """
        session = self.db.query(ReviewSession).filter(ReviewSession.id == session_id).first()
        if not session:
            return None
        return ReviewSessionResponse.from_orm_with_stats(session)
    
    def get_review_issues(self,
                         session_id: int,
                         page: int = 1,
                         page_size: int = 50,
                         severity: Optional[str] = None,
                         author: Optional[str] = None,
                         confirm_status: Optional[str] = None,
                         is_fixed: Optional[bool] = None,
                         file_path: Optional[str] = None) -> ReviewIssueListResponse:
        """
        获取评审问题列表
        
        Args:
            session_id: 会话ID
            page: 页码
            page_size: 每页数量
            severity: 严重程度筛选（逗号分隔）
            author: 提交人筛选
            confirm_status: 确认意见筛选
            is_fixed: 是否已修改筛选
            file_path: 文件路径模糊搜索
            
        Returns:
            评审问题列表响应
        """
        # 构建查询
        query = self.db.query(ReviewIssue).filter(ReviewIssue.session_id == session_id)
        
        # 应用筛选条件
        if severity:
            # 支持多个严重程度，逗号分隔
            severities = [s.strip() for s in severity.split(',')]
            query = query.filter(ReviewIssue.severity.in_(severities))
        if author:
            query = query.filter(ReviewIssue.author == author)
        if confirm_status:
            query = query.filter(ReviewIssue.confirm_status == confirm_status)
        if is_fixed is not None:
            query = query.filter(ReviewIssue.is_fixed == is_fixed)
        if file_path:
            query = query.filter(ReviewIssue.file_path.like(f'%{file_path}%'))
        
        # 获取总数
        total = query.count()
        
        # 分页和排序（按严重程度和创建时间）
        offset = (page - 1) * page_size
        # 严重程度排序：critical > major > minor > suggestion
        severity_order = {
            'critical': 0,
            'major': 1,
            'minor': 2,
            'suggestion': 3
        }
        
        issues = query.order_by(ReviewIssue.created_at).offset(offset).limit(page_size).all()
        
        # 按严重程度排序
        issues.sort(key=lambda x: (severity_order.get(x.severity, 99), x.created_at))
        
        # 转换为响应模型
        items = [ReviewIssueResponse.from_orm(i) for i in issues]
        
        return ReviewIssueListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )
    
    def update_issue(self, issue_id: int, update_data: ReviewIssueUpdate) -> Optional[ReviewIssueResponse]:
        """
        更新问题状态
        
        Args:
            issue_id: 问题ID
            update_data: 更新数据
            
        Returns:
            更新后的问题响应，不存在则返回None
        """
        issue = self.db.query(ReviewIssue).filter(ReviewIssue.id == issue_id).first()
        if not issue:
            return None
        
        # 更新字段
        if update_data.confirm_status is not None:
            issue.confirm_status = update_data.confirm_status
        if update_data.is_fixed is not None:
            issue.is_fixed = update_data.is_fixed
        if update_data.review_comment is not None:
            issue.review_comment = update_data.review_comment
        
        # 更新时间
        issue.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(issue)
        
        return ReviewIssueResponse.from_orm(issue)
    
    def batch_update_issues(self, 
                           issue_ids: List[int],
                           confirm_status: Optional[str] = None,
                           is_fixed: Optional[bool] = None) -> BatchUpdateResponse:
        """
        批量更新问题
        
        Args:
            issue_ids: 问题ID列表
            confirm_status: 确认意见
            is_fixed: 是否已修改
            
        Returns:
            批量更新响应
        """
        # 查询所有问题
        issues = self.db.query(ReviewIssue).filter(ReviewIssue.id.in_(issue_ids)).all()
        
        # 更新字段
        updated_count = 0
        for issue in issues:
            if confirm_status is not None:
                issue.confirm_status = confirm_status
            if is_fixed is not None:
                issue.is_fixed = is_fixed
            issue.updated_at = datetime.now()
            updated_count += 1
        
        self.db.commit()
        
        return BatchUpdateResponse(updated_count=updated_count)
    
    def get_statistics_overview(self,
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               project_name: Optional[str] = None) -> StatisticsOverview:
        """
        获取统计概览
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            project_name: 项目筛选
            
        Returns:
            统计概览
        """
        # 构建查询
        session_query = self.db.query(ReviewSession)
        issue_query = self.db.query(ReviewIssue)
        
        # 应用筛选条件
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                session_query = session_query.filter(ReviewSession.review_time >= start_dt)
                # 通过session关联筛选issue
                issue_query = issue_query.join(ReviewSession).filter(ReviewSession.review_time >= start_dt)
            except ValueError:
                pass
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                session_query = session_query.filter(ReviewSession.review_time <= end_dt)
                issue_query = issue_query.join(ReviewSession).filter(ReviewSession.review_time <= end_dt)
            except ValueError:
                pass
        if project_name:
            session_query = session_query.filter(ReviewSession.project_name == project_name)
            issue_query = issue_query.join(ReviewSession).filter(ReviewSession.project_name == project_name)
        
        # 统计评审次数
        total_reviews = session_query.count()
        
        # 统计总问题数
        total_issues = issue_query.count()
        
        # 严重程度分布
        severity_stats = self.db.query(
            ReviewIssue.severity,
            func.count(ReviewIssue.id).label('count')
        ).group_by(ReviewIssue.severity).all()
        
        severity_distribution = SeverityStats()
        for severity, count in severity_stats:
            if severity == 'critical':
                severity_distribution.critical = count
            elif severity == 'major':
                severity_distribution.major = count
            elif severity == 'minor':
                severity_distribution.minor = count
            elif severity == 'suggestion':
                severity_distribution.suggestion = count
        
        # Top作者
        top_authors_query = self.db.query(
            ReviewIssue.author,
            func.count(ReviewIssue.id).label('issue_count')
        ).filter(
            ReviewIssue.author.isnot(None),
            ReviewIssue.author != ''
        ).group_by(ReviewIssue.author).order_by(desc('issue_count')).limit(10).all()
        
        top_authors = [
            {"author": author, "issue_count": count}
            for author, count in top_authors_query
        ]
        
        # 趋势数据（按日期统计）
        trend_data = []  # TODO: 实现趋势数据统计
        
        return StatisticsOverview(
            total_reviews=total_reviews,
            total_issues=total_issues,
            severity_distribution=severity_distribution,
            top_authors=top_authors,
            trend_data=trend_data
        )
