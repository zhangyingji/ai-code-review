"""
数据库模型定义
使用SQLAlchemy ORM定义评审记录和问题详情表
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class ReviewRecord(Base):
    """评审记录表"""
    __tablename__ = 'review_records'
    
    # 主键
    review_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 项目信息
    project_id = Column(Integer, nullable=False, index=True)
    project_name = Column(String(255))
    
    # 分支信息
    review_branch = Column(String(255), nullable=False, index=True)
    base_branch = Column(String(255), nullable=False)
    
    # 评审时间信息
    review_time = Column(DateTime, nullable=False, index=True)
    duration_seconds = Column(Float)
    
    # 统计信息
    total_commits = Column(Integer, default=0)
    total_files_reviewed = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    major_count = Column(Integer, default=0)
    minor_count = Column(Integer, default=0)
    suggestion_count = Column(Integer, default=0)
    
    # 时间过滤信息（可选）
    time_filter_enabled = Column(Integer, default=0)  # 0:未启用, 1:已启用
    time_filter_since = Column(String(64))
    time_filter_until = Column(String(64))
    time_filter_timezone = Column(String(64))
    
    # 创建信息
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(String(255))
    
    # 索引
    __table_args__ = (
        Index('idx_project_time', 'project_id', 'review_time'),
        Index('idx_branch', 'review_branch'),
    )


class ReviewIssue(Base):
    """问题详情表"""
    __tablename__ = 'review_issues'
    
    # 主键
    issue_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 外键关联评审记录
    review_id = Column(String(64), ForeignKey('review_records.review_id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 文件和位置信息
    file_path = Column(String(512), nullable=False)
    line_number = Column(String(64))  # 行号或行号范围，如 "42" 或 "42-58"
    
    # 问题信息
    issue_type = Column(String(128))  # 问题类型
    severity = Column(String(32), nullable=False, index=True)  # 严重程度: critical, major, minor, suggestion
    description = Column(Text, nullable=False)  # 问题描述
    suggestion = Column(Text)  # 修复建议
    code_snippet = Column(JSON)  # 代码片段（JSON格式存储）
    
    # 作者信息
    author_name = Column(String(255))
    author_email = Column(String(255), index=True)
    
    # 问题状态管理
    status = Column(String(32), default='pending', index=True)  # pending, confirmed, false_positive, ignored, resolved
    verified_by = Column(String(255))  # 复核人
    verified_at = Column(DateTime)  # 复核时间
    verification_note = Column(Text)  # 复核备注
    
    # 创建时间
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_review_status', 'review_id', 'status'),
        Index('idx_severity', 'severity'),
        Index('idx_author', 'author_email'),
    )


def create_tables(engine):
    """
    创建所有表
    
    Args:
        engine: SQLAlchemy引擎对象
    """
    Base.metadata.create_all(engine)


def drop_tables(engine):
    """
    删除所有表
    
    Args:
        engine: SQLAlchemy引擎对象
    """
    Base.metadata.drop_all(engine)
