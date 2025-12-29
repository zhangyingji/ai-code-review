"""
数据库配置和连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库基类
Base = declarative_base()

# 全局变量
_engine = None
_SessionLocal = None


def init_database(db_path: str = "./data/review.db"):
    """
    初始化数据库连接
    
    Args:
        db_path: SQLite数据库文件路径
    """
    global _engine, _SessionLocal
    
    # 确保数据目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # 创建数据库引擎
    database_url = f"sqlite:///{db_path}"
    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},  # SQLite需要
        echo=False  # 设置为True可以看到SQL语句
    )
    
    # 创建Session工厂
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    # 创建所有表
    Base.metadata.create_all(bind=_engine)


def get_db():
    """
    获取数据库会话
    
    用于FastAPI依赖注入
    
    Yields:
        数据库会话
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    """获取数据库引擎"""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine
"""
数据库配置和连接管理
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库基类
Base = declarative_base()

# 全局变量
_engine = None
_SessionLocal = None


def init_database(db_path: str = "./data/review.db"):
    """
    初始化数据库连接
    
    Args:
        db_path: SQLite数据库文件路径
    """
    global _engine, _SessionLocal
    
    # 确保数据目录存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # 创建数据库引擎
    database_url = f"sqlite:///{db_path}"
    _engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},  # SQLite需要
        echo=False  # 设置为True可以看到SQL语句
    )
    
    # 创建Session工厂
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
    # 创建所有表
    Base.metadata.create_all(bind=_engine)


def get_db():
    """
    获取数据库会话
    
    用于FastAPI依赖注入
    
    Yields:
        数据库会话
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    """获取数据库引擎"""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine
