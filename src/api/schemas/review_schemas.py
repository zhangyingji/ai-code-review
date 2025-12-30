"""
评审相关的Pydantic数据模式
用于API请求和响应的数据验证
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== 评审会话相关模式 ==========

class SeverityStats(BaseModel):
    """严重程度统计"""
    critical: int = 0
    major: int = 0
    minor: int = 0
    suggestion: int = 0


class ReviewSessionBase(BaseModel):
    """评审会话基础模式"""
    project_name: Optional[str] = None
    review_branch: str
    base_branch: str
    review_time: datetime
    duration_seconds: Optional[float] = None
    total_commits: int = 0
    total_files_changed: int = 0
    total_files_reviewed: int = 0
    total_issues: int = 0
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    suggestion_count: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    concurrent_mode: bool = False


class ReviewSessionResponse(ReviewSessionBase):
    """评审会话响应模式"""
    id: int
    session_uuid: str
    created_at: datetime
    severity_stats: Optional[SeverityStats] = None
    major_critical_issues_count: int = 0
    major_critical_accepted_count: int = 0
    major_critical_adoption_rate: float = 0.0
    
    class Config:
        from_attributes = True
        
    @staticmethod
    def from_orm_with_stats(session, adoption_data=None):
        """从ORM模型创建响应，包含统计信息和采纳率"""
        data = {
            "id": session.id,
            "session_uuid": session.session_uuid,
            "project_name": session.project_name,
            "review_branch": session.review_branch,
            "base_branch": session.base_branch,
            "review_time": session.review_time,
            "duration_seconds": session.duration_seconds,
            "total_commits": session.total_commits,
            "total_files_changed": session.total_files_changed,
            "total_files_reviewed": session.total_files_reviewed,
            "total_issues": session.total_issues,
            "critical_count": session.critical_count,
            "major_count": session.major_count,
            "minor_count": session.minor_count,
            "suggestion_count": session.suggestion_count,
            "total_additions": session.total_additions,
            "total_deletions": session.total_deletions,
            "concurrent_mode": session.concurrent_mode,
            "created_at": session.created_at,
            "severity_stats": {
                "critical": session.critical_count,
                "major": session.major_count,
                "minor": session.minor_count,
                "suggestion": session.suggestion_count
            },
            "major_critical_issues_count": adoption_data["major_critical_count"] if adoption_data else 0,
            "major_critical_accepted_count": adoption_data["major_critical_accepted"] if adoption_data else 0,
            "major_critical_adoption_rate": adoption_data["major_critical_adoption_rate"] if adoption_data else 0.0
        }
        return ReviewSessionResponse(**data)


class ReviewSessionListResponse(BaseModel):
    """评审会话列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ReviewSessionResponse]


# ========== 问题相关模式 ==========

class ReviewIssueBase(BaseModel):
    """评审问题基础模式"""
    severity: str
    category: Optional[str] = None
    author: Optional[str] = None
    file_path: str
    line_info: Optional[str] = None
    method_name: Optional[str] = None
    description: Optional[str] = None
    suggestion: Optional[str] = None
    code_snippet_json: Optional[str] = None
    matched_rule: Optional[str] = None
    matched_rule_category: Optional[str] = None
    confirm_status: str = 'pending'
    is_fixed: bool = False
    review_comment: Optional[str] = None


class ReviewIssueResponse(ReviewIssueBase):
    """评审问题响应模式"""
    id: int
    file_id: int
    session_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReviewIssueUpdate(BaseModel):
    """评审问题更新模式"""
    confirm_status: Optional[str] = None
    is_fixed: Optional[bool] = None
    review_comment: Optional[str] = None


class ReviewIssueListResponse(BaseModel):
    """评审问题列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ReviewIssueResponse]


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    issue_ids: List[int]
    confirm_status: Optional[str] = None
    is_fixed: Optional[bool] = None


class BatchUpdateResponse(BaseModel):
    """批量更新响应"""
    updated_count: int


# ========== 提交信息相关模式 ==========

class CommitInfoResponse(BaseModel):
    """提交信息响应模式"""
    id: int
    commit_id: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    commit_message: Optional[str] = None
    commit_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ========== 统计分析相关模式 ==========

class StatisticsOverview(BaseModel):
    """统计概览"""
    total_reviews: int
    total_issues: int
    severity_distribution: SeverityStats
    top_authors: List[dict]  # [{"author": "name", "issue_count": 10}, ...]
    trend_data: List[dict]  # [{"date": "2024-01-01", "issue_count": 5}, ...]
"""
评审相关的Pydantic数据模式
用于API请求和响应的数据验证
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== 评审会话相关模式 ==========

class SeverityStats(BaseModel):
    """严重程度统计"""
    critical: int = 0
    major: int = 0
    minor: int = 0
    suggestion: int = 0


class ReviewSessionBase(BaseModel):
    """评审会话基础模式"""
    project_name: Optional[str] = None
    review_branch: str
    base_branch: str
    review_time: datetime
    duration_seconds: Optional[float] = None
    total_commits: int = 0
    total_files_changed: int = 0
    total_files_reviewed: int = 0
    total_issues: int = 0
    critical_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    suggestion_count: int = 0
    total_additions: int = 0
    total_deletions: int = 0
    concurrent_mode: bool = False


class ReviewSessionResponse(ReviewSessionBase):
    """评审会话响应模式"""
    id: int
    session_uuid: str
    created_at: datetime
    severity_stats: Optional[SeverityStats] = None
    major_critical_issues_count: int = 0
    major_critical_accepted_count: int = 0
    major_critical_adoption_rate: float = 0.0
    
    class Config:
        from_attributes = True
        
    @staticmethod
    def from_orm_with_stats(session, adoption_data=None):
        """从ORM模型创建响应，包含统计信息和采纳率"""
        data = {
            "id": session.id,
            "session_uuid": session.session_uuid,
            "project_name": session.project_name,
            "review_branch": session.review_branch,
            "base_branch": session.base_branch,
            "review_time": session.review_time,
            "duration_seconds": session.duration_seconds,
            "total_commits": session.total_commits,
            "total_files_changed": session.total_files_changed,
            "total_files_reviewed": session.total_files_reviewed,
            "total_issues": session.total_issues,
            "critical_count": session.critical_count,
            "major_count": session.major_count,
            "minor_count": session.minor_count,
            "suggestion_count": session.suggestion_count,
            "total_additions": session.total_additions,
            "total_deletions": session.total_deletions,
            "concurrent_mode": session.concurrent_mode,
            "created_at": session.created_at,
            "severity_stats": {
                "critical": session.critical_count,
                "major": session.major_count,
                "minor": session.minor_count,
                "suggestion": session.suggestion_count
            },
            "major_critical_issues_count": adoption_data["major_critical_count"] if adoption_data else 0,
            "major_critical_accepted_count": adoption_data["major_critical_accepted"] if adoption_data else 0,
            "major_critical_adoption_rate": adoption_data["major_critical_adoption_rate"] if adoption_data else 0.0
        }
        return ReviewSessionResponse(**data)


class ReviewSessionListResponse(BaseModel):
    """评审会话列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ReviewSessionResponse]


# ========== 问题相关模式 ==========

class ReviewIssueBase(BaseModel):
    """评审问题基础模式"""
    severity: str
    category: Optional[str] = None
    author: Optional[str] = None
    file_path: str
    line_info: Optional[str] = None
    method_name: Optional[str] = None
    description: Optional[str] = None
    suggestion: Optional[str] = None
    code_snippet_json: Optional[str] = None
    matched_rule: Optional[str] = None
    matched_rule_category: Optional[str] = None
    confirm_status: str = 'pending'
    is_fixed: bool = False
    review_comment: Optional[str] = None


class ReviewIssueResponse(ReviewIssueBase):
    """评审问题响应模式"""
    id: int
    file_id: int
    session_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ReviewIssueUpdate(BaseModel):
    """评审问题更新模式"""
    confirm_status: Optional[str] = None
    is_fixed: Optional[bool] = None
    review_comment: Optional[str] = None


class ReviewIssueListResponse(BaseModel):
    """评审问题列表响应"""
    total: int
    page: int
    page_size: int
    items: List[ReviewIssueResponse]


class BatchUpdateRequest(BaseModel):
    """批量更新请求"""
    issue_ids: List[int]
    confirm_status: Optional[str] = None
    is_fixed: Optional[bool] = None


class BatchUpdateResponse(BaseModel):
    """批量更新响应"""
    updated_count: int


# ========== 提交信息相关模式 ==========

class CommitInfoResponse(BaseModel):
    """提交信息响应模式"""
    id: int
    commit_id: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None
    commit_message: Optional[str] = None
    commit_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# ========== 统计分析相关模式 ==========

class StatisticsOverview(BaseModel):
    """统计概览"""
    total_reviews: int
    total_issues: int
    severity_distribution: SeverityStats
    top_authors: List[dict]  # [{"author": "name", "issue_count": 10}, ...]
    trend_data: List[dict]  # [{"date": "2024-01-01", "issue_count": 5}, ...]
