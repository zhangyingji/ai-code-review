"""
时间过滤工具模块
用于处理代码评审的时间范围过滤
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging
from dateutil import tz

logger = logging.getLogger(__name__)


class TimeFilter:
    """时间过滤器类
    
    用于根据配置或参数生成时间范围，并过滤提交记录
    """
    
    def __init__(self, timezone: str = "Asia/Shanghai"):
        """
        初始化时间过滤器
        
        Args:
            timezone: 时区设置，默认为上海时区
        """
        self.timezone = tz.gettz(timezone)
        if not self.timezone:
            logger.warning(f"无法识别时区 {timezone}，使用本地时区")
            self.timezone = tz.tzlocal()
    
    def get_today_range(self) -> Tuple[datetime, datetime]:
        """
        获取今天的时间范围（从0点到当前时间）
        
        Returns:
            (起始时间, 结束时间) 元组
        """
        now = datetime.now(self.timezone)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now
    
    def get_yesterday_range(self) -> Tuple[datetime, datetime]:
        """
        获取昨天的时间范围（昨天0点到23:59:59）
        
        Returns:
            (起始时间, 结束时间) 元组
        """
        now = datetime.now(self.timezone)
        yesterday = now - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        return start, end
    
    def get_last_n_days_range(self, n: int) -> Tuple[datetime, datetime]:
        """
        获取最近N天的时间范围
        
        Args:
            n: 天数
            
        Returns:
            (起始时间, 结束时间) 元组
        """
        now = datetime.now(self.timezone)
        start = (now - timedelta(days=n)).replace(hour=0, minute=0, second=0, microsecond=0)
        return start, now
    
    def get_custom_range(self, since: str, until: Optional[str] = None) -> Tuple[datetime, datetime]:
        """
        获取自定义时间范围
        
        Args:
            since: 起始日期字符串 (YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS)
            until: 结束日期字符串 (可选)，如果为None则使用当前时间
            
        Returns:
            (起始时间, 结束时间) 元组
        """
        # 解析起始时间
        start = self._parse_datetime(since)
        
        # 解析结束时间
        if until:
            end = self._parse_datetime(until)
        else:
            end = datetime.now(self.timezone)
        
        return start, end
    
    def _parse_datetime(self, dt_str: str) -> datetime:
        """
        解析日期时间字符串
        
        Args:
            dt_str: 日期时间字符串
            
        Returns:
            datetime对象
        """
        # 支持多种格式
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(dt_str, fmt)
                # 添加时区信息
                dt = dt.replace(tzinfo=self.timezone)
                return dt
            except ValueError:
                continue
        
        raise ValueError(f"无法解析日期时间字符串: {dt_str}")
    
    def get_time_range(self, mode: str, **kwargs) -> Tuple[datetime, datetime]:
        """
        根据模式获取时间范围
        
        Args:
            mode: 模式，可选值: today, yesterday, last_n_days, custom
            **kwargs: 其他参数
                - last_n_days: 最近N天（当mode为last_n_days时）
                - since: 起始时间（当mode为custom时）
                - until: 结束时间（当mode为custom时）
                
        Returns:
            (起始时间, 结束时间) 元组
        """
        if mode == "today":
            return self.get_today_range()
        elif mode == "yesterday":
            return self.get_yesterday_range()
        elif mode == "last_n_days":
            n = kwargs.get("last_n_days", 1)
            return self.get_last_n_days_range(n)
        elif mode == "custom":
            since = kwargs.get("since")
            until = kwargs.get("until")
            if not since:
                raise ValueError("custom模式下必须提供since参数")
            return self.get_custom_range(since, until)
        else:
            raise ValueError(f"不支持的时间模式: {mode}")
    
    def filter_commits_by_time(self, commits: list, since: datetime, until: datetime) -> list:
        """
        按时间范围过滤提交记录
        
        Args:
            commits: 提交记录列表
            since: 起始时间
            until: 结束时间
            
        Returns:
            过滤后的提交记录列表
        """
        filtered = []
        
        for commit in commits:
            # 获取提交时间（支持多种字段名）
            commit_time_str = commit.get('created_at') or commit.get('committed_date') or commit.get('authored_date')
            
            if not commit_time_str:
                logger.warning(f"提交记录缺少时间字段: {commit.get('id', 'unknown')}")
                continue
            
            try:
                # 解析提交时间
                commit_time = self._parse_iso_datetime(commit_time_str)
                
                # 检查是否在时间范围内
                if since <= commit_time <= until:
                    filtered.append(commit)
            except Exception as e:
                logger.warning(f"解析提交时间失败: {commit_time_str}, 错误: {e}")
                continue
        
        return filtered
    
    def _parse_iso_datetime(self, dt_str: str) -> datetime:
        """
        解析ISO格式的日期时间字符串（GitLab API返回格式）
        
        Args:
            dt_str: ISO格式日期时间字符串
            
        Returns:
            datetime对象
        """
        # GitLab返回的时间格式通常是ISO 8601
        # 例如: 2025-01-15T10:30:00.000+08:00
        from dateutil import parser
        dt = parser.isoparse(dt_str)
        
        # 如果没有时区信息，添加配置的时区
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self.timezone)
        
        return dt
    
    def format_time_range(self, since: datetime, until: datetime) -> dict:
        """
        格式化时间范围为字典（用于报告元数据）
        
        Args:
            since: 起始时间
            until: 结束时间
            
        Returns:
            包含格式化时间信息的字典
        """
        return {
            'time_filter_enabled': True,
            'time_filter_since': since.isoformat(),
            'time_filter_until': until.isoformat(),
            'time_filter_timezone': str(self.timezone)
        }
