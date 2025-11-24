"""
代码评审工具主程序
"""
import os
import sys
import yaml
import argparse
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Dict

from src.gitlab_client import GitLabClient
from src.llm_client import LLMClient
from src.review_engine import ReviewEngine
from src.report_generator import ReportGenerator

def setup_logging(config: Dict) -> str:
    """
    设置日志系统
    
    Args:
        config: 配置字典
        
    Returns:
        日志文件路径，如果未启用文件日志则返回None
    """
    log_config = config.get('logging', {})
    enabled = log_config.get('enabled', True)
    log_level = getattr(logging, log_config.get('level', 'INFO').upper())
    console_output = log_config.get('console_output', True)
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()  # 清除默认handler
    
    log_file_path = ""
    
    # 添加文件日志处理器
    if enabled:
        log_dir = log_config.get('log_dir', './logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # 生成日志文件名(包含时间戳)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file_path = os.path.join(log_dir, f'code_review_{timestamp}.log')
        
        # 使用轮转文件处理器
        max_bytes = log_config.get('max_file_size', 10) * 1024 * 1024  # MB to bytes
        backup_count = log_config.get('backup_count', 5)
        
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # 添加控制台日志处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    return log_file_path


def load_config(config_path: str) -> Dict:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        配置字典
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 检查是否有本地配置覆盖
    local_config_path = config_path.replace('.yaml', '.local.yaml')
    if os.path.exists(local_config_path):
        # 暂时使用基础logger，因为此时日志系统还未配置
        temp_logger = logging.getLogger(__name__)
        temp_logger.info(f"加载本地配置: {local_config_path}")
        with open(local_config_path, 'r', encoding='utf-8') as f:
            local_config = yaml.safe_load(f)
            # 合并配置
            config.update(local_config)
    
    return config


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='代码评审工具 - 自动评审GitLab代码变更')
    parser.add_argument('-c', '--config', default='config.yaml', 
                       help='配置文件路径 (默认: config.yaml)')
    parser.add_argument('-p', '--project', help='项目名称 (当配置中有多个项目时，用此参数选择特定项目)')
    parser.add_argument('-s', '--source', help='源分支名称 (覆盖配置文件)')
    parser.add_argument('-t', '--target', help='目标分支名称 (覆盖配置文件)')
    parser.add_argument('-f', '--format', choices=['html', 'json'],
                       help='报告格式 (覆盖配置文件)')
    parser.add_argument('-o', '--output', help='报告输出目录 (覆盖配置文件)')
    parser.add_argument('--no-group-by-author', action='store_true',
                       help='不按作者分组')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别 (覆盖配置文件)')
    
    args = parser.parse_args()
    
    log_file_path = ""
    
    try:
        # 加载配置
        config = load_config(args.config)
        
        # 命令行参数覆盖日志级别
        if args.log_level:
            if 'logging' not in config:
                config['logging'] = {}
            config['logging']['level'] = args.log_level
        
        # 设置日志系统
        log_file_path = setup_logging(config)
        
        # 现在可以使用logger了
        logger = logging.getLogger(__name__)
        
        logger.info("="*70)
        logger.info("代码评审系统启动")
        logger.info("="*70)
        # 获取项目配置
        project_id = config['gitlab'].get('project_id')
        project_name = config['gitlab'].get('project_name', '')  # 非必填
        if not project_id:
            # 如果没有 project_id，检查是否有 projects 列表
            projects = config['gitlab'].get('projects', [])
            if not projects:
                logger.error("错误: 未配置项目ID或项目列表")
                return 1
            
            # 如果指定了 --project 参数，使用该项目
            if args.project:
                found_project = None
                for proj in projects:
                    if proj.get('name') == args.project:
                        found_project = proj
                        break
                
                if not found_project:
                    logger.error(f"错误: 未找到项目 '{args.project}'")
                    logger.error(f"可用项目: {', '.join(p.get('name', '') for p in projects)}")
                    return 1
                
                project_id = found_project['id']
                project_name = args.project
                logger.info(f"使用项目: {args.project} (ID: {project_id})")
            else:
                logger.error(f"错误: 配置中有多个项目，请使用 -p/--project 指定项目")
                logger.error(f"可用项目: {', '.join(p.get('name', '') for p in projects)}")
                return 1
        
        # 打印项目信息
        if project_name:
            logger.info(f"使用项目: {project_name} (ID: {project_id})")
        else:
            logger.info(f"使用项目 ID: {project_id}")
        source_branch = args.source or config['branch'].get('review_branch', '')
        target_branch = args.target or config['branch'].get('base_branch', '')
        report_format = args.format or config['report']['format']
        output_dir = args.output or config['report']['output_dir']
        group_by_author = not args.no_group_by_author and config['report']['group_by_author']
        
        # 检查是否提供了源分支
        if not source_branch:
            logger.error("错误: 必须指定源分支 (-s/--source 或在配置文件中设置)")
            return 1
        
        # 检查是否提供了基准分支
        if not target_branch:
            logger.error("错误: 必须指定基准分支 (-t/--target 或在配罫件中设置)")
            return 1
        
        logger.info(f"评审配置: {target_branch} -> {source_branch}")
        
        # 初始化 GitLab 客户端
        logger.info("初始化 GitLab 客户端...")
        gitlab_client = GitLabClient(
            url=config['gitlab']['url'],
            private_token=config['gitlab']['private_token'],
            project_id=project_id
        )
        
        # 初始化大模型客户端
        logger.info(f"初始化大模型客户端...")
        llm_config = config['llm'].copy()
        api_url = llm_config.pop('api_url')
        api_key = llm_config.pop('api_key')
        model = llm_config.pop('model')
        enable_thinking = llm_config.pop('enable_thinking', False)
        llm_client = LLMClient(
            api_url=api_url,
            api_key=api_key,
            model=model,
            temperature=llm_config.get('temperature', 0.3),
            max_tokens=llm_config.get('max_tokens', 2000),
            enable_thinking=enable_thinking
        )
        
        # 获取性能配置
        performance_config = config.get('performance', {})
        enable_concurrent = performance_config.get('enable_concurrent', True)
        max_workers = performance_config.get('max_workers', 3)
        
        # 获取文件忽略配置
        file_ignore_config = config.get('file_filter', {})
        ignore_extensions = file_ignore_config.get('ignore_extensions')
        ignore_dirs = file_ignore_config.get('ignore_dirs')
        
        # 获取提交人过滤配置
        committer_filter_config = config.get('committer_filter', {})
        filter_authors = committer_filter_config.get('authors', [])
        
        review_engine = ReviewEngine(
            gitlab_client=gitlab_client,
            llm_client=llm_client,
            review_rules=config['review_rules'],
            enable_concurrent=enable_concurrent,
            max_workers=max_workers,
            enable_thinking=enable_thinking,
            ignore_extensions=ignore_extensions,
            ignore_dirs=ignore_dirs,
            filter_authors=filter_authors
        )
        
        # 执行评审
        logger.info("=" * 60)
        logger.info("开始代码评审...")
        logger.info("=" * 60)
        review_data = review_engine.review_branches(source_branch, target_branch)
        
        # 生成报告
        logger.info("=" * 60)
        logger.info("生成评审报告...")
        logger.info("=" * 60)
        report_generator = ReportGenerator(output_dir=output_dir)
        report_path = report_generator.generate_report(
            review_data=review_data,
            format=report_format,
            group_by_author=group_by_author
        )
        
        # 输出总结
        logger.info("="*70)
        logger.info("评审完成!")
        logger.info("="*70)
        logger.info(f"报告路径: {report_path}")
        logger.info(f"总问题数: {review_data['statistics']['total_issues']}")
        logger.info(f"  - 严重: {review_data['statistics']['by_severity']['critical']}")
        logger.info(f"  - 主要: {review_data['statistics']['by_severity']['major']}")
        logger.info(f"  - 次要: {review_data['statistics']['by_severity']['minor']}")
        logger.info(f"  - 建议: {review_data['statistics']['by_severity']['suggestion']}")
        if log_file_path:
            logger.info(f"日志文件: {log_file_path}")
        
        # 清理临时文件
        gitlab_client.cleanup()
        
        return 0
        
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error("="*70)
        logger.error("评审过程出错")
        logger.error("="*70)
        logger.error(f"错误信息: {e}", exc_info=True)
        if log_file_path:
            logger.error(f"详细错误信息已保存到日志文件: {log_file_path}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
