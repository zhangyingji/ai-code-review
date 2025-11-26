"""
测试环境检查脚本
检查测试所需的依赖和配置是否就绪
"""
import sys
import os

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    if version >= (3, 8):
        print("✓ Python 版本符合要求 (>= 3.8)")
        return True
    else:
        print("✗ Python 版本过低，需要 3.8 或更高版本")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n检查依赖包...")
    dependencies = [
        ('yaml', 'PyYAML'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('pymysql', 'PyMySQL'),
        ('apscheduler', 'APScheduler'),
        ('openpyxl', 'openpyxl'),
    ]
    
    all_installed = True
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {package_name} 已安装")
        except ImportError:
            print(f"✗ {package_name} 未安装")
            all_installed = False
    
    return all_installed

def check_config():
    """检查配置文件"""
    print("\n检查配置文件...")
    
    if not os.path.exists('config.yaml'):
        print("✗ config.yaml 不存在")
        return False
    
    print("✓ config.yaml 存在")
    
    try:
        import yaml
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 检查基本配置
        has_gitlab = 'gitlab' in config
        has_llm = 'llm' in config
        has_storage = config.get('storage', {}).get('enabled', False)
        
        print(f"  GitLab 配置: {'✓' if has_gitlab else '✗'}")
        print(f"  LLM 配置: {'✓' if has_llm else '✗'}")
        print(f"  存储配置: {'✓ 已启用' if has_storage else '- 未启用（可选）'}")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置文件解析失败: {e}")
        return False

def check_database():
    """检查数据库连接"""
    print("\n检查数据库连接...")
    
    try:
        import yaml
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 尝试加载本地配置
        if os.path.exists('config.local.yaml'):
            with open('config.local.yaml', 'r', encoding='utf-8') as f:
                local_config = yaml.safe_load(f)
                if local_config:
                    config.update(local_config)
        
        storage_config = config.get('storage', {})
        if not storage_config.get('enabled'):
            print("- 存储功能未启用，跳过数据库检查")
            return True
        
        # 尝试连接数据库
        import pymysql
        conn_config = storage_config.get('connection', {})
        
        connection = pymysql.connect(
            host=conn_config.get('host', 'localhost'),
            port=conn_config.get('port', 3306),
            user=conn_config.get('username'),
            password=conn_config.get('password'),
            database=conn_config.get('database'),
            charset=conn_config.get('charset', 'utf8mb4')
        )
        connection.close()
        
        print("✓ 数据库连接成功")
        print(f"  主机: {conn_config.get('host')}")
        print(f"  数据库: {conn_config.get('database')}")
        return True
        
    except ImportError:
        print("✗ PyMySQL 未安装")
        return False
    except Exception as e:
        print(f"✗ 数据库连接失败: {e}")
        return False

def main():
    """主函数"""
    print("="*70)
    print("测试环境检查")
    print("="*70)
    
    results = {}
    
    results['python'] = check_python_version()
    results['dependencies'] = check_dependencies()
    results['config'] = check_config()
    results['database'] = check_database()
    
    # 总结
    print("\n" + "="*70)
    print("检查结果总结")
    print("="*70)
    
    for name, success in results.items():
        status = "✓ 就绪" if success else "✗ 未就绪"
        print(f"{name.ljust(15)}: {status}")
    
    print("="*70)
    
    if all(results.values()):
        print("✓ 测试环境完全就绪，可以运行所有测试")
        return 0
    elif results['python'] and results['dependencies']:
        print("⚠ 部分功能未配置，某些测试可能被跳过")
        return 0
    else:
        print("✗ 测试环境不完整，请先安装依赖或配置")
        print("\n安装依赖: pip install -r requirements.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
