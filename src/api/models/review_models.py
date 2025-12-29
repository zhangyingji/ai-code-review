"""
评审相关的数据库模型
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class ReviewSession(Base):
    """评审会话表 - 存储每次评审的总体信息"""
    __tablename__ = "review_sessions"
    
    # 主键和唯一标识
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    session_uuid = Column(String(64), unique=True, nullable=False, index=True, comment="会话唯一标识")
    
    # 基本信息
    project_name = Column(String(255), index=True, comment="项目名称")
    review_branch = Column(String(255), nullable=False, index=True, comment="评审分支")
    base_branch = Column(String(255), nullable=False, comment="基准分支")
    review_time = Column(DateTime, nullable=False, index=True, comment="评审时间")
    duration_seconds = Column(Float, comment="评审耗时（秒）")
    
    # 统计信息
    total_commits = Column(Integer, default=0, comment="提交总数")
    total_files_changed = Column(Integer, default=0, comment="变更文件总数")
    total_files_reviewed = Column(Integer, default=0, comment="已评审文件数")
    total_issues = Column(Integer, default=0, comment="问题总数")
    critical_count = Column(Integer, default=0, comment="严重问题数")
    major_count = Column(Integer, default=0, comment="主要问题数")
    minor_count = Column(Integer, default=0, comment="次要问题数")
    suggestion_count = Column(Integer, default=0, comment="建议数")
    total_additions = Column(Integer, default=0, comment="新增代码行数")
    total_deletions = Column(Integer, default=0, comment="删除代码行数")
    concurrent_mode = Column(Boolean, default=False, comment="是否并发模式")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关联关系
    files = relationship("ReviewFile", back_populates="session", cascade="all, delete-orphan")
    issues = relationship("ReviewIssue", back_populates="session", cascade="all, delete-orphan")
    commits = relationship("CommitInfo", back_populates="session", cascade="all, delete-orphan")


class ReviewFile(Base):
    """评审文件表 - 存储每次评审中涉及的文件信息"""
    __tablename__ = "review_files"
    
    # 主键和外键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    session_id = Column(Integer, ForeignKey("review_sessions.id", ondelete="CASCADE"), 
                       nullable=False, index=True, comment="关联评审会话")
    
    # 文件信息
    file_path = Column(String(512), nullable=False, index=True, comment="文件路径")
    additions = Column(Integer, default=0, comment="新增行数")
    deletions = Column(Integer, default=0, comment="删除行数")
    new_file = Column(Boolean, default=False, comment="是否新文件")
    renamed_file = Column(Boolean, default=False, comment="是否重命名")
    issue_count = Column(Integer, default=0, comment="问题数量")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关联关系
    session = relationship("ReviewSession", back_populates="files")
    issues = relationship("ReviewIssue", back_populates="file", cascade="all, delete-orphan")


class ReviewIssue(Base):
    """评审问题表 - 存储具体的评审问题及其处理状态"""
    __tablename__ = "review_issues"
    
    # 主键和外键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    file_id = Column(Integer, ForeignKey("review_files.id", ondelete="CASCADE"), 
                    nullable=False, index=True, comment="关联文件")
    session_id = Column(Integer, ForeignKey("review_sessions.id", ondelete="CASCADE"), 
                       nullable=False, index=True, comment="关联会话（冗余，便于查询）")
    
    # 问题信息
    severity = Column(String(20), nullable=False, index=True, comment="严重程度")
    category = Column(String(100), comment="问题分类")
    author = Column(String(100), index=True, comment="提交人")
    file_path = Column(String(512), nullable=False, comment="文件路径（冗余）")
    line_info = Column(String(50), comment="行号信息")
    method_name = Column(String(255), comment="方法名")
    description = Column(Text, comment="问题描述")
    suggestion = Column(Text, comment="改进建议")
    code_snippet_json = Column(Text, comment="代码片段（JSON格式）")
    matched_rule = Column(Text, comment="匹配的规则")
    matched_rule_category = Column(String(100), comment="规则分类")
    
    # 处理状态
    confirm_status = Column(String(20), default='pending', index=True, 
                          comment="确认意见：pending/accepted/rejected/ignored")
    is_fixed = Column(Boolean, default=False, index=True, comment="是否已修改")
    review_comment = Column(Text, comment="评审意见")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关联关系
    session = relationship("ReviewSession", back_populates="issues")
    file = relationship("ReviewFile", back_populates="issues")
    comments = relationship("IssueComment", back_populates="issue", cascade="all, delete-orphan")
    
    # 复合索引
    __table_args__ = (
        Index('idx_session_severity', 'session_id', 'severity'),
        Index('idx_session_author', 'session_id', 'author'),
    )


class CommitInfo(Base):
    """提交信息表 - 存储评审涉及的提交记录"""
    __tablename__ = "commit_infos"
    
    # 主键和外键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    session_id = Column(Integer, ForeignKey("review_sessions.id", ondelete="CASCADE"), 
                       nullable=False, index=True, comment="关联评审会话")
    
    # 提交信息
    commit_id = Column(String(64), nullable=False, index=True, comment="提交ID")
    author_name = Column(String(100), index=True, comment="提交人姓名")
    author_email = Column(String(255), comment="提交人邮箱")
    commit_message = Column(Text, comment="提交信息")
    commit_time = Column(DateTime, comment="提交时间")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关联关系
    session = relationship("ReviewSession", back_populates="commits")


class IssueComment(Base):
    """问题评论表 - 存储对问题的评论记录（预留，支持协作讨论）"""
    __tablename__ = "issue_comments"
    
    # 主键和外键
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    issue_id = Column(Integer, ForeignKey("review_issues.id", ondelete="CASCADE"), 
                     nullable=False, index=True, comment="关联问题")
    
    # 评论信息
    commenter = Column(String(100), nullable=False, comment="评论人")
    content = Column(Text, nullable=False, comment="评论内容")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    # 关联关系
    issue = relationship("ReviewIssue", back_populates="comments")
