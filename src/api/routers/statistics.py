"""
统计分析相关的API路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..models.database import get_db
from ..services.query_service import QueryService
from ..schemas.review_schemas import StatisticsOverview

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/overview", response_model=StatisticsOverview)
def get_statistics_overview(
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    project_name: Optional[str] = Query(None, description="项目筛选"),
    db: Session = Depends(get_db)
):
    """获取统计概览"""
    query_service = QueryService(db)
    return query_service.get_statistics_overview(
        start_date=start_date,
        end_date=end_date,
        project_name=project_name
    )
"""
统计分析相关的API路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..models.database import get_db
from ..services.query_service import QueryService
from ..schemas.review_schemas import StatisticsOverview

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/overview", response_model=StatisticsOverview)
def get_statistics_overview(
    start_date: Optional[str] = Query(None, description="开始日期"),
    end_date: Optional[str] = Query(None, description="结束日期"),
    project_name: Optional[str] = Query(None, description="项目筛选"),
    db: Session = Depends(get_db)
):
    """获取统计概览"""
    query_service = QueryService(db)
    return query_service.get_statistics_overview(
        start_date=start_date,
        end_date=end_date,
        project_name=project_name
    )
