"""
评审相关的API路由
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..models.database import get_db
from ..services.query_service import QueryService
from ..schemas.review_schemas import (
    ReviewSessionListResponse,
    ReviewSessionResponse,
    ReviewIssueListResponse,
    ReviewIssueResponse,
    ReviewIssueUpdate,
    BatchUpdateRequest,
    BatchUpdateResponse
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=ReviewSessionListResponse)
def get_review_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    project_name: Optional[str] = Query(None, description="项目名称筛选"),
    review_branch: Optional[str] = Query(None, description="评审分支筛选"),
    base_branch: Optional[str] = Query(None, description="基准分支筛选"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    min_issues: Optional[int] = Query(None, ge=0, description="最小问题数"),
    db: Session = Depends(get_db)
):
    """获取评审会话列表"""
    query_service = QueryService(db)
    return query_service.get_review_sessions(
        page=page,
        page_size=page_size,
        project_name=project_name,
        review_branch=review_branch,
        base_branch=base_branch,
        start_date=start_date,
        end_date=end_date,
        min_issues=min_issues
    )


@router.get("/{session_id}", response_model=ReviewSessionResponse)
def get_review_detail(
    session_id: int,
    db: Session = Depends(get_db)
):
    """获取评审会话详情"""
    query_service = QueryService(db)
    session = query_service.get_review_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="评审会话不存在")
    return session


@router.get("/{session_id}/issues", response_model=ReviewIssueListResponse)
def get_review_issues(
    session_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    severity: Optional[str] = Query("critical,major", description="严重程度筛选（逗号分隔）"),
    author: Optional[str] = Query(None, description="提交人筛选"),
    confirm_status: Optional[str] = Query(None, description="确认意见筛选"),
    is_fixed: Optional[bool] = Query(None, description="是否已修改筛选"),
    file_path: Optional[str] = Query(None, description="文件路径模糊搜索"),
    db: Session = Depends(get_db)
):
    """获取评审问题列表"""
    query_service = QueryService(db)
    return query_service.get_review_issues(
        session_id=session_id,
        page=page,
        page_size=page_size,
        severity=severity,
        author=author,
        confirm_status=confirm_status,
        is_fixed=is_fixed,
        file_path=file_path
    )
