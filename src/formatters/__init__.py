"""报告格式化器模块"""
from .base_formatter import BaseFormatter
from .html_formatter import HtmlFormatter
from .markdown_formatter import MarkdownFormatter
from .json_formatter import JsonFormatter

try:
    from .excel_formatter import ExcelFormatter
    EXCEL_AVAILABLE = True
except ImportError:
    ExcelFormatter = None
    EXCEL_AVAILABLE = False

__all__ = [
    'BaseFormatter',
    'HtmlFormatter',
    'MarkdownFormatter',
    'JsonFormatter',
    'ExcelFormatter',
    'EXCEL_AVAILABLE'
]
