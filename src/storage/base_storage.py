"""存储接口 - 用于评审结果持久化"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class BaseStorage(ABC):
    """存储基类
    
    用于将评审结果持久化到数据库或其他存储系统
    子类需要实现具体的存储逻辑
    """
    
    @abstractmethod
    def save_review(self, review_data: Dict[str, Any]) -> str:
        """保存评审数据
        
        Args:
            review_data: 完整的评审数据
            
        Returns:
            评审记录的唯一标识符
        """
        pass
    
    @abstractmethod
    def get_review(self, review_id: str) -> Optional[Dict[str, Any]]:
        """获取评审数据
        
        Args:
            review_id: 评审记录ID
            
        Returns:
            评审数据，不存在则返回None
        """
        pass
    
    @abstractmethod
    def list_reviews(self, project: str = None, branch: str = None,
                    start_date: datetime = None, end_date: datetime = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """列出评审记录
        
        Args:
            project: 项目名称（可选）
            branch: 分支名称（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 返回记录数量限制
            
        Returns:
            评审记录列表
        """
        pass
    
    @abstractmethod
    def delete_review(self, review_id: str) -> bool:
        """删除评审记录
        
        Args:
            review_id: 评审记录ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    def get_statistics(self, project: str = None, time_range: int = 30) -> Dict[str, Any]:
        """获取统计信息
        
        Args:
            project: 项目名称（可选）
            time_range: 时间范围（天数）
            
        Returns:
            统计数据
        """
        pass
    
    # 新增问题管理方法
    @abstractmethod
    def save_review_with_issues(self, review_data: Dict[str, Any]) -> str:
        """保存评审记录及问题详情
        
        Args:
            review_data: 完整的评审数据
            
        Returns:
            评审记录的唯一标识符
        """
        pass
    
    @abstractmethod
    def get_issue_by_id(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """根据问题ID获取问题详情
        
        Args:
            issue_id: 问题ID
            
        Returns:
            问题详情，不存在则返回None
        """
        pass
    
    @abstractmethod
    def update_issue_status(self, issue_id: str, status: str, 
                           verified_by: str = None, note: str = None) -> bool:
        """更新问题状态
        
        Args:
            issue_id: 问题ID
            status: 新状态 (confirmed, false_positive, ignored, resolved)
            verified_by: 复核人
            note: 复核备注
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    def list_issues_by_review(self, review_id: str) -> List[Dict[str, Any]]:
        """获取某次评审的所有问题
        
        Args:
            review_id: 评审记录ID
            
        Returns:
            问题列表
        """
        pass
    
    @abstractmethod
    def list_issues_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """按状态查询问题
        
        Args:
            status: 问题状态
            limit: 返回记录数量限制
            
        Returns:
            问题列表
        """
        pass
    
    @abstractmethod
    def get_issue_statistics(self, project_id: int = None, time_range: int = 30) -> Dict[str, Any]:
        """获取问题统计信息
        
        Args:
            project_id: 项目ID（可选）
            time_range: 时间范围（天数）
            
        Returns:
            统计数据
        """
        pass
