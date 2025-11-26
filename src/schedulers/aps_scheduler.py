"""
APScheduler调度器实现
基于APScheduler实现定时评审任务调度
"""
import logging
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from pytz import timezone as pytz_timezone

from .base_scheduler import BaseScheduler

logger = logging.getLogger(__name__)


class APSScheduler(BaseScheduler):
    """基于APScheduler的调度器实现"""
    
    def __init__(self, timezone: str = 'Asia/Shanghai', max_instances: int = 3):
        """
        初始化调度器
        
        Args:
            timezone: 时区
            max_instances: 最大并发任务实例数
        """
        super().__init__()
        self.timezone = pytz_timezone(timezone)
        self.max_instances = max_instances
        
        # 配置调度器
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': ThreadPoolExecutor(max_instances)
        }
        job_defaults = {
            'coalesce': True,  # 合并错过的执行
            'max_instances': 1,  # 每个任务最多一个实例
            'misfire_grace_time': 300  # 错过执行的宽限时间（秒）
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=self.timezone
        )
        self.running = False
        
        logger.info(f"APScheduler初始化完成，时区: {timezone}")
    
    def schedule_job(self, job_id: str, schedule_expr: str,
                    task_func: Callable, **task_kwargs) -> bool:
        """
        调度一个任务
        
        Args:
            job_id: 任务唯一标识
            schedule_expr: 调度表达式（cron格式或间隔时间）
            task_func: 要执行的任务函数
            **task_kwargs: 任务参数
            
        Returns:
            是否调度成功
        """
        try:
            # 解析调度表达式
            trigger = self._parse_schedule_expr(schedule_expr)
            
            # 添加任务
            job = self.scheduler.add_job(
                task_func,
                trigger=trigger,
                id=job_id,
                kwargs=task_kwargs,
                replace_existing=True
            )
            
            self.jobs[job_id] = {
                'id': job_id,
                'schedule_expr': schedule_expr,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'status': 'scheduled'
            }
            
            logger.info(f"任务调度成功: {job_id}, 下次执行: {job.next_run_time}")
            return True
            
        except Exception as e:
            logger.error(f"任务调度失败: {job_id}, 错误: {e}")
            return False
    
    def _parse_schedule_expr(self, schedule_expr: str):
        """
        解析调度表达式
        
        支持格式:
        - Cron表达式: "0 2 * * *" (每天凌晨2点)
        - 间隔时间: "interval:hours=6" (每6小时)
        - 每日时间: "daily:10:00" (每天10点)
        - 每周时间: "weekly:MON:09:00" (每周一9点)
        """
        if schedule_expr.startswith('interval:'):
            # 间隔调度
            parts = schedule_expr.replace('interval:', '').split('=')
            if len(parts) == 2:
                unit = parts[0]
                value = int(parts[1])
                kwargs = {unit: value}
                return IntervalTrigger(**kwargs)
        
        elif schedule_expr.startswith('daily:'):
            # 每日调度
            time_str = schedule_expr.replace('daily:', '')
            hour, minute = map(int, time_str.split(':'))
            return CronTrigger(hour=hour, minute=minute)
        
        elif schedule_expr.startswith('weekly:'):
            # 每周调度
            parts = schedule_expr.replace('weekly:', '').split(':')
            day_of_week = parts[0]
            hour, minute = map(int, parts[1].split(':'))
            return CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
        
        else:
            # Cron表达式
            parts = schedule_expr.split()
            if len(parts) == 5:
                minute, hour, day, month, day_of_week = parts
                return CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                )
        
        raise ValueError(f"无法解析调度表达式: {schedule_expr}")
    
    def cancel_job(self, job_id: str) -> bool:
        """取消任务"""
        try:
            self.scheduler.remove_job(job_id)
            if job_id in self.jobs:
                del self.jobs[job_id]
            logger.info(f"任务已取消: {job_id}")
            return True
        except Exception as e:
            logger.error(f"取消任务失败: {job_id}, 错误: {e}")
            return False
    
    def start(self) -> None:
        """启动调度器"""
        if not self.running:
            self.scheduler.start()
            self.running = True
            logger.info("调度器已启动")
    
    def stop(self) -> None:
        """停止调度器"""
        if self.running:
            self.scheduler.shutdown(wait=False)
            self.running = False
            logger.info("调度器已停止")
    
    def list_jobs(self) -> Dict[str, Any]:
        """列出所有任务"""
        jobs_info = {}
        for job in self.scheduler.get_jobs():
            jobs_info[job.id] = {
                'id': job.id,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
        return jobs_info
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        job = self.scheduler.get_job(job_id)
        if job:
            return {
                'id': job.id,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
        return None
