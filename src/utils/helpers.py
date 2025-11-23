"""辅助工具函数"""
import re
from datetime import datetime
from typing import Optional


def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """清理文件名，移除或替换非法字符
    
    Args:
        filename: 原始文件名
        replacement: 替换非法字符的字符串
        
    Returns:
        清理后的文件名
    """
    # Windows和Unix系统的非法文件名字符
    illegal_chars = r'[<>:"/\\|?*]'
    
    # 替换非法字符
    sanitized = re.sub(illegal_chars, replacement, filename)
    
    # 移除前后空格
    sanitized = sanitized.strip()
    
    # 如果文件名为空或只包含点，返回默认名称
    if not sanitized or sanitized.replace('.', '') == '':
        sanitized = 'unnamed'
    
    return sanitized


def format_duration(seconds: float) -> str:
    """格式化时长
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化的时长字符串
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}min"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_timestamp(timestamp: Optional[str] = None, format_str: str = "%Y%m%d_%H%M%S") -> str:
    """格式化时间戳
    
    Args:
        timestamp: ISO格式时间戳字符串，None则使用当前时间
        format_str: 输出格式
        
    Returns:
        格式化的时间字符串
    """
    if timestamp is None:
        dt = datetime.now()
    else:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    return dt.strftime(format_str)


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
        
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_line_range(line_str: str) -> tuple[int, int]:
    """解析行号范围
    
    Args:
        line_str: 行号字符串，如 "42" 或 "42-45"
        
    Returns:
        (起始行, 结束行) 元组
    """
    if '-' in line_str:
        parts = line_str.split('-')
        start = int(parts[0].strip())
        end = int(parts[1].strip())
        return start, end
    else:
        line = int(line_str.strip())
        return line, line
