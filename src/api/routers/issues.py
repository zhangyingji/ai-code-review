"""
问题管理相关的API路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.database import get_db
from ..services.query_service import QueryService
from ..schemas.review_schemas import (
    ReviewIssueResponse,
    ReviewIssueUpdate,
    BatchUpdateRequest,
    BatchUpdateResponse
)

router = APIRouter(prefix="/issues", tags=["issues"])


@router.put("/{issue_id}", response_model=ReviewIssueResponse)
def update_issue(
    issue_id: int,
    update_data: ReviewIssueUpdate,
    db: Session = Depends(get_db)
):
    """更新问题状态"""
    query_service = QueryService(db)
    issue = query_service.update_issue(issue_id, update_data)
    if not issue:
        raise HTTPException(status_code=404, detail="问题不存在")
    return issue


@router.put("/batch", response_model=BatchUpdateResponse)
def batch_update_issues(
    request: BatchUpdateRequest,
    db: Session = Depends(get_db)
):
    """批量更新问题"""
    query_service = QueryService(db)
    return query_service.batch_update_issues(
        issue_ids=request.issue_ids,
        confirm_status=request.confirm_status,
        is_fixed=request.is_fixed
    )
