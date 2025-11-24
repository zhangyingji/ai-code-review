"""报告格式化器模块"""
from .base_formatter import BaseFormatter
from .html_formatter import HtmlFormatter

try:
    from .excel_formatter import ExcelFormatter
    EXCEL_AVAILABLE = True
except ImportError:
    ExcelFormatter = None
    EXCEL_AVAILABLE = False

__all__ = [
    'BaseFormatter',
    'HtmlFormatter',
    'ExcelFormatter',
    'EXCEL_AVAILABLE'
]
