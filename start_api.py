"""
API服务器启动脚本
"""
import uvicorn
import yaml
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml"):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 检查本地配置
    local_config_path = config_path.replace('.yaml', '.local.yaml')
    import os
    if os.path.exists(local_config_path):
        logger.info(f"加载本地配置: {local_config_path}")
        with open(local_config_path, 'r', encoding='utf-8') as f:
            local_config = yaml.safe_load(f)
            config.update(local_config)
    
    return config


if __name__ == "__main__":
    # 加载配置
    config = load_config()
    
    # 从配置中读取API设置
    api_config = config.get('api', {})
    host = api_config.get('host', '0.0.0.0')
    port = api_config.get('port', 8000)
    
    # 从配置中读取数据库设置并初始化
    from src.api.models.database import init_database
    db_config = config.get('database', {})
    db_path = db_config.get('path', './data/review.db')
    
    logger.info(f"初始化数据库: {db_path}")
    init_database(db_path)
    
    # 启动服务器
    logger.info(f"启动API服务器: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/api/docs")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    )
"""
API服务器启动脚本
"""
import uvicorn
import yaml
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config.yaml"):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 检查本地配置
    local_config_path = config_path.replace('.yaml', '.local.yaml')
    import os
    if os.path.exists(local_config_path):
        logger.info(f"加载本地配置: {local_config_path}")
        with open(local_config_path, 'r', encoding='utf-8') as f:
            local_config = yaml.safe_load(f)
            config.update(local_config)
    
    return config


if __name__ == "__main__":
    # 加载配置
    config = load_config()
    
    # 从配置中读取API设置
    api_config = config.get('api', {})
    host = api_config.get('host', '0.0.0.0')
    port = api_config.get('port', 8000)
    
    # 从配置中读取数据库设置并初始化
    from src.api.models.database import init_database
    db_config = config.get('database', {})
    db_path = db_config.get('path', './data/review.db')
    
    logger.info(f"初始化数据库: {db_path}")
    init_database(db_path)
    
    # 启动服务器
    logger.info(f"启动API服务器: http://{host}:{port}")
    logger.info(f"API文档: http://{host}:{port}/api/docs")
    
    uvicorn.run(
        "src.api.main:app",
        host=host,
        port=port,
        reload=True,  # 开发模式下自动重载
        log_level="info"
    )
