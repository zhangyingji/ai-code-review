"""HTML格式化器"""
from typing import Dict, Any
from jinja2 import Template
from .base_formatter import BaseFormatter
from ..templates.html_template import get_html_template, get_scripts
from ..templates.styles import get_css_styles
from ..utils.data_processor import DataProcessor

# 严重程度标签
SEVERITY_LABELS = {
    'critical': '严重',
    'major': '主要',
    'minor': '次要',
    'suggestion': '建议'
}


class HtmlFormatter(BaseFormatter):
    """HTML报告格式化器"""
    
    def format(self, review_data: Dict[str, Any], **kwargs) -> str:
        """格式化为HTML报告
        
        Args:
            review_data: 评审数据
            **kwargs: 额外参数
            
        Returns:
            HTML报告内容
        """
        # 验证数据
        if not self.validate_data(review_data):
            raise ValueError("Invalid review data")
        
        # 预处理数据
        review_data = self.pre_process(review_data)
        
        # 数据处理 - 排序问题
        DataProcessor.enrich_file_reviews(review_data)
        
        # 获取模板组件
        html_template = get_html_template()
        css_styles = get_css_styles()
        scripts = get_scripts()
        
        # 渲染模板
        template = Template(html_template)
        html = template.render(
            review_data=review_data,
            severity_labels=SEVERITY_LABELS,
            styles=css_styles,
            scripts=scripts
        )
        
        # 后处理
        return self.post_process(html)
    
    def get_file_extension(self) -> str:
        """获取文件扩展名"""
        return ".html"
