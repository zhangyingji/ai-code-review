"""重构后的报告生成器 - 主入口"""
import os
import logging
from typing import Dict, Any
from datetime import datetime
from src.formatters import (
    HtmlFormatter,
    MarkdownFormatter,
    JsonFormatter,
    ExcelFormatter,
    EXCEL_AVAILABLE
)
from src.utils.helpers import sanitize_filename, format_timestamp

logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器 - 重构后的简洁版本
    
    职责：
    1. 接收评审数据
    2. 根据格式选择合适的格式化器
    3. 生成报告文件并保存
    """
    
    def __init__(self, output_dir: str = "./reports"):
        """初始化报告生成器
        
        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化所有格式化器
        self.formatters = {
            'html': HtmlFormatter(output_dir),
            'markdown': MarkdownFormatter(output_dir),
            'json': JsonFormatter(output_dir),
        }
        
        # Excel格式化器可选
        if EXCEL_AVAILABLE:
            try:
                self.formatters['excel'] = ExcelFormatter(output_dir)
            except ImportError:
                logger.warning("Excel格式化器不可用，已跳过")
    
    def generate_report(self, review_data: Dict[str, Any], format: str = "html",
                       **kwargs) -> str:
        """生成评审报告
        
        Args:
            review_data: 评审数据
            format: 报告格式 (html, markdown, json, excel)
            **kwargs: 额外参数，传递给格式化器
            
        Returns:
            报告文件路径
        """
        # 检查格式是否支持
        if format not in self.formatters:
            supported_formats = ', '.join(self.formatters.keys())
            raise ValueError(f"不支持的格式: {format}。支持的格式: {supported_formats}")
        
        # 获取格式化器
        formatter = self.formatters[format]
        
        # 生成文件名
        timestamp = format_timestamp()
        source_branch = review_data['metadata']['source_branch']
        safe_branch_name = sanitize_filename(source_branch)
        extension = formatter.get_file_extension()
        filename = f"review_{safe_branch_name}_{timestamp}{extension}"
        filepath = os.path.join(self.output_dir, filename)
        
        # Excel格式特殊处理（直接保存文件）
        if format == 'excel':
            kwargs['filepath'] = filepath
            filepath = formatter.format(review_data, **kwargs)
            logger.info(f"报告已生成: {filepath}")
            return filepath
        
        # 其他格式：格式化后写入文件
        content = formatter.format(review_data, **kwargs)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"报告已生成: {filepath}")
        return filepath
    
    def generate_multiple_formats(self, review_data: Dict[str, Any],
                                  formats: list | None = None) -> Dict[str, str]:
        """生成多种格式的报告
        
        Args:
            review_data: 评审数据
            formats: 格式列表，默认生成所有支持的格式
            
        Returns:
            格式到文件路径的映射
        """
        if formats is None:
            formats = list(self.formatters.keys())
        
        results = {}
        for fmt in formats:
            try:
                filepath = self.generate_report(review_data, fmt)
                results[fmt] = filepath
            except Exception as e:
                logger.error(f"生成{fmt}格式报告失败: {e}")
                results[fmt] = None
        
        return results
    
    def get_supported_formats(self) -> list:
        """获取支持的报告格式列表
        
        Returns:
            支持的格式列表
        """
        return list(self.formatters.keys())
