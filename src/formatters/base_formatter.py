"""基础格式化器抽象类"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseFormatter(ABC):
    """报告格式化器基类
    
    所有格式化器都应该继承此类并实现format方法
    """
    
    def __init__(self, output_dir: str = "./reports"):
        """初始化格式化器
        
        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = output_dir
        self.logger = logger
    
    @abstractmethod
    def format(self, review_data: Dict[str, Any], **kwargs) -> str:
        """格式化评审数据
        
        Args:
            review_data: 评审数据字典
            **kwargs: 额外的格式化参数
            
        Returns:
            格式化后的报告内容
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """获取文件扩展名
        
        Returns:
            文件扩展名（如 .html, .md, .json等）
        """
        pass
    
    def validate_data(self, review_data: Dict[str, Any]) -> bool:
        """验证评审数据的完整性
        
        Args:
            review_data: 评审数据字典
            
        Returns:
            数据是否有效
        """
        required_keys = ['metadata', 'statistics', 'file_reviews']
        for key in required_keys:
            if key not in review_data:
                self.logger.error(f"缺少必需的数据字段: {key}")
                return False
        return True
    
    def pre_process(self, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """预处理评审数据（子类可选重写）
        
        Args:
            review_data: 原始评审数据
            
        Returns:
            处理后的评审数据
        """
        return review_data
    
    def post_process(self, content: str) -> str:
        """后处理格式化内容（子类可选重写）
        
        Args:
            content: 格式化后的内容
            
        Returns:
            后处理后的内容
        """
        return content
