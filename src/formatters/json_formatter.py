"""JSON格式化器"""
import json
from typing import Dict, Any
from .base_formatter import BaseFormatter


class JsonFormatter(BaseFormatter):
    """JSON报告格式化器"""
    
    def format(self, review_data: Dict[str, Any], **kwargs) -> str:
        """格式化为JSON报告
        
        Args:
            review_data: 评审数据
            **kwargs: 可选参数
                - indent: 缩进空格数，默认2
                - ensure_ascii: 是否转义非ASCII字符，默认False
            
        Returns:
            JSON格式的报告内容
        """
        # 验证数据
        if not self.validate_data(review_data):
            raise ValueError("Invalid review data")
        
        # 预处理数据
        review_data = self.pre_process(review_data)
        
        # 格式化参数
        indent = kwargs.get('indent', 2)
        ensure_ascii = kwargs.get('ensure_ascii', False)
        
        # 序列化为JSON
        content = json.dumps(
            review_data,
            indent=indent,
            ensure_ascii=ensure_ascii,
            default=str  # 处理datetime等特殊类型
        )
        
        return self.post_process(content)
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return ".json"
