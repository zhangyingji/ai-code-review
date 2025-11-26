"""
数据库初始化脚本
用于创建评审系统所需的数据库表
"""
import yaml
import sys
import argparse
from sqlalchemy import create_engine
from src.storage.models import create_tables, drop_tables


def load_config(config_file='config.yaml'):
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 尝试加载本地配置
    local_config_file = config_file.replace('.yaml', '.local.yaml')
    try:
        with open(local_config_file, 'r', encoding='utf-8') as f:
            local_config = yaml.safe_load(f)
            config.update(local_config)
    except FileNotFoundError:
        pass
    
    return config


def create_connection_string(config):
    """创建数据库连接字符串"""
    conn = config['storage']['connection']
    return (
        f"mysql+pymysql://{conn['username']}:{conn['password']}"
        f"@{conn['host']}:{conn.get('port', 3306)}"
        f"/{conn['database']}"
        f"?charset={conn.get('charset', 'utf8mb4')}"
    )


def main():
    parser = argparse.ArgumentParser(description='初始化代码评审数据库')
    parser.add_argument('-c', '--config', default='config.yaml', help='配置文件路径')
    parser.add_argument('--drop', action='store_true', help='删除现有表')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 检查存储是否配置
    if 'storage' not in config or not config['storage'].get('connection'):
        print("错误: 配置文件中未找到存储配置")
        print("请在config.yaml中配置storage部分")
        return 1
    
    # 创建数据库引擎
    try:
        connection_string = create_connection_string(config)
        engine = create_engine(connection_string, echo=True)
        
        if args.drop:
            print("警告: 即将删除所有表，所有数据将丢失！")
            confirm = input("确认删除? (yes/no): ")
            if confirm.lower() == 'yes':
                print("删除现有表...")
                drop_tables(engine)
                print("表删除成功")
            else:
                print("操作已取消")
                return 0
        
        print("创建数据库表...")
        create_tables(engine)
        print("数据库表创建成功！")
        
        print("\n数据库初始化完成！")
        print(f"数据库: {config['storage']['connection']['database']}")
        print(f"主机: {config['storage']['connection']['host']}")
        
        return 0
        
    except Exception as e:
        print(f"错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
