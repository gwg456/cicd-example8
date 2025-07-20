#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据库连接和会话管理
使用SQLAlchemy进行数据库操作
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# 数据库引擎配置
engine_kwargs = {
    "echo": settings.DATABASE_ECHO,
}

# SQLite特殊配置
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({
        "poolclass": StaticPool,
        "connect_args": {
            "check_same_thread": False,
            "timeout": 20
        }
    })

# 创建数据库引擎
engine = create_engine(
    settings.database_url_sync,
    **engine_kwargs
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建基础模型类
Base = declarative_base()

# 元数据
metadata = MetaData()

def get_db() -> Session:
    """
    获取数据库会话
    用于依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """创建所有数据库表"""
    try:
        # 导入所有模型以确保它们被注册
        from app.models import user
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 数据库表创建成功")
        
    except Exception as e:
        logger.error(f"❌ 创建数据库表失败: {e}")
        raise

def drop_tables():
    """删除所有数据库表（谨慎使用）"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("⚠️ 所有数据库表已删除")
    except Exception as e:
        logger.error(f"❌ 删除数据库表失败: {e}")
        raise

def check_database_connection():
    """检查数据库连接"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("✅ 数据库连接正常")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False

def get_database_info():
    """获取数据库信息"""
    try:
        db = SessionLocal()
        
        # 获取数据库类型
        db_type = engine.dialect.name
        
        # 获取表信息
        tables = Base.metadata.tables.keys()
        
        # 获取连接信息
        connection_info = {
            "database_type": db_type,
            "database_url": settings.DATABASE_URL,
            "tables": list(tables),
            "echo_enabled": settings.DATABASE_ECHO
        }
        
        db.close()
        return connection_info
        
    except Exception as e:
        logger.error(f"获取数据库信息失败: {e}")
        return None

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
        
    def create_session(self) -> Session:
        """创建新的数据库会话"""
        return self.SessionLocal()
    
    def execute_raw_sql(self, sql: str, params: dict = None):
        """执行原生SQL"""
        try:
            db = self.SessionLocal()
            result = db.execute(sql, params or {})
            db.commit()
            db.close()
            return result
        except Exception as e:
            logger.error(f"执行SQL失败: {e}")
            raise
    
    def backup_database(self, backup_path: str):
        """备份数据库（仅支持SQLite）"""
        if not settings.DATABASE_URL.startswith("sqlite"):
            raise ValueError("当前仅支持SQLite数据库备份")
        
        try:
            import shutil
            import os
            
            # 获取数据库文件路径
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            if not os.path.exists(db_path):
                raise FileNotFoundError(f"数据库文件不存在: {db_path}")
            
            # 执行备份
            shutil.copy2(db_path, backup_path)
            logger.info(f"✅ 数据库备份成功: {backup_path}")
            
        except Exception as e:
            logger.error(f"❌ 数据库备份失败: {e}")
            raise
    
    def restore_database(self, backup_path: str):
        """恢复数据库（仅支持SQLite）"""
        if not settings.DATABASE_URL.startswith("sqlite"):
            raise ValueError("当前仅支持SQLite数据库恢复")
        
        try:
            import shutil
            import os
            
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"备份文件不存在: {backup_path}")
            
            # 获取数据库文件路径
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            
            # 执行恢复
            shutil.copy2(backup_path, db_path)
            logger.info(f"✅ 数据库恢复成功: {db_path}")
            
        except Exception as e:
            logger.error(f"❌ 数据库恢复失败: {e}")
            raise
    
    def get_table_info(self, table_name: str):
        """获取表信息"""
        try:
            from sqlalchemy import inspect
            
            inspector = inspect(self.engine)
            
            # 获取表结构
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            foreign_keys = inspector.get_foreign_keys(table_name)
            
            return {
                "table_name": table_name,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys
            }
            
        except Exception as e:
            logger.error(f"获取表信息失败: {e}")
            return None
    
    def vacuum_database(self):
        """清理数据库（优化存储空间）"""
        try:
            if settings.DATABASE_URL.startswith("sqlite"):
                self.execute_raw_sql("VACUUM")
                logger.info("✅ 数据库清理完成")
            else:
                logger.warning("⚠️ 当前数据库类型不支持VACUUM操作")
        except Exception as e:
            logger.error(f"❌ 数据库清理失败: {e}")
            raise

# 创建全局数据库管理器实例
db_manager = DatabaseManager()

# 数据库初始化函数
def init_database():
    """初始化数据库"""
    logger.info("🔧 初始化数据库...")
    
    try:
        # 检查数据库连接
        if not check_database_connection():
            raise Exception("数据库连接失败")
        
        # 创建表
        create_tables()
        
        # 打印数据库信息
        db_info = get_database_info()
        if db_info:
            logger.info(f"📊 数据库类型: {db_info['database_type']}")
            logger.info(f"📋 数据表数量: {len(db_info['tables'])}")
            logger.info(f"📝 数据表: {', '.join(db_info['tables'])}")
        
        logger.info("✅ 数据库初始化完成")
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise

if __name__ == "__main__":
    # 测试数据库连接
    try:
        init_database()
        
        # 测试数据库操作
        db = SessionLocal()
        result = db.execute("SELECT 1 as test")
        print(f"测试查询结果: {result.fetchone()}")
        db.close()
        
        print("✅ 数据库测试通过")
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        exit(1)