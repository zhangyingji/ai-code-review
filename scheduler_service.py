"""
调度服务主程序
用于运行定时评审任务
"""
import os
import sys
import yaml
import logging
import signal
import time
from datetime import datetime

from src.schedulers.aps_scheduler import APSScheduler
from src.gitlab_client import GitLabClient
from src.llm_client import LLMClient
from src.review_engine import ReviewEngine
from src.report_generator import ReportGenerator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'./logs/scheduler_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config(config_file='config.yaml'):
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 尝试加载本地配置
    local_config_file = config_file.replace('.yaml', '.local.yaml')
    if os.path.exists(local_config_file):
        with open(local_config_file, 'r', encoding='utf-8') as f:
            local_config = yaml.safe_load(f)
            config.update(local_config)
    
    return config


def execute_review_task(config, job_config):
    """
    执行评审任务
    
    Args:
        config: 全局配置
        job_config: 任务配置
    """
    job_name = job_config.get('job_name', job_config['job_id'])
    logger.info(f"开始执行任务: {job_name}")
    
    try:
        # 初始化GitLab客户端
        gitlab_client = GitLabClient(
            url=config['gitlab']['url'],
            private_token=config['gitlab']['private_token'],
            project_id=job_config['project_id']
        )
        
        # 初始化LLM客户端
        llm_client = LLMClient(
            api_url=config['llm']['api_url'],
            api_key=config['llm']['api_key'],
            model=config['llm']['model'],
            temperature=config['llm'].get('temperature', 0.3),
            max_tokens=config['llm'].get('max_tokens', 2000)
        )
        
        # 初始化评审引擎
        review_engine = ReviewEngine(
            gitlab_client=gitlab_client,
            llm_client=llm_client,
            review_rules=config['review_rules'],
            enable_concurrent=config.get('performance', {}).get('enable_concurrent', True),
            max_workers=config.get('performance', {}).get('max_workers', 3)
        )
        
        # 执行评审
        review_data = review_engine.review_branches(
            job_config['review_branch'],
            job_config['base_branch']
        )
        
        # 生成报告
        report_generator = ReportGenerator(output_dir=config['report']['output_dir'])
        report_path = report_generator.generate_report(
            review_data=review_data,
            format=job_config.get('report_format', 'html'),
            group_by_author=True
        )
        
        logger.info(f"任务完成: {job_name}, 报告: {report_path}")
        
        # 保存到数据库（如果启用）
        if config.get('storage', {}).get('enabled'):
            from src.storage.mysql_storage import MySQLStorage
            storage = MySQLStorage(config['storage'])
            review_data['metadata']['project_id'] = job_config['project_id']
            review_id = storage.save_review_with_issues(review_data)
            logger.info(f"评审结果已保存到数据库: {review_id}")
        
        # 清理
        gitlab_client.cleanup()
        
    except Exception as e:
        logger.error(f"任务执行失败: {job_name}, 错误: {e}", exc_info=True)


def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='代码评审调度服务')
    parser.add_argument('command', choices=['start', 'stop', 'status'], help='命令')
    parser.add_argument('-c', '--config', default='config.yaml', help='配置文件路径')
    args = parser.parse_args()
    
    if args.command == 'start':
        # 加载配置
        config = load_config(args.config)
        scheduler_config = config.get('scheduler', {})
        
        if not scheduler_config.get('enabled', False):
            logger.error("调度器未启用，请在配置文件中启用")
            return 1
        
        # 创建调度器
        scheduler = APSScheduler(
            timezone=scheduler_config.get('timezone', 'Asia/Shanghai'),
            max_instances=scheduler_config.get('max_instances', 3)
        )
        
        # 注册所有任务
        jobs = scheduler_config.get('jobs', [])
        for job in jobs:
            if not job.get('enabled', True):
                continue
            
            scheduler.schedule_job(
                job_id=job['job_id'],
                schedule_expr=job['schedule_expr'],
                task_func=execute_review_task,
                config=config,
                job_config=job
            )
        
        # 启动调度器
        scheduler.start()
        logger.info("调度服务已启动")
        
        # 信号处理
        def signal_handler(sig, frame):
            logger.info("收到停止信号，正在关闭...")
            scheduler.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # 保持运行
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("正在关闭调度服务...")
            scheduler.stop()
    
    elif args.command == 'status':
        logger.info("查询调度服务状态...")
        # TODO: 实现状态查询
        print("调度服务状态功能待实现")
    
    elif args.command == 'stop':
        logger.info("停止调度服务...")
        # TODO: 实现停止命令
        print("停止服务功能待实现（使用Ctrl+C停止运行中的服务）")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
