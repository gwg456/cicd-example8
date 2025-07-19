#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库表和初始数据
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models import Base
from app import crud, schemas
from app.auth import get_password_hash

def create_tables():
    """创建数据库表"""
    print("正在创建数据库表...")
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")
    return engine

def create_initial_data(engine):
    """创建初始数据"""
    print("正在创建初始数据...")
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 创建默认角色
        default_roles = [
            {"name": "admin", "description": "系统管理员，拥有完全权限"},
            {"name": "manager", "description": "管理员，拥有用户管理权限"},
            {"name": "user", "description": "普通用户，只能访问基本功能"}
        ]
        
        for role_data in default_roles:
            existing_role = crud.get_role_by_name(db, role_data["name"])
            if not existing_role:
                role_create = schemas.RoleCreate(**role_data)
                crud.create_role(db, role_create)
                print(f"✅ 创建角色: {role_data['name']}")
            else:
                print(f"⚠️  角色已存在: {role_data['name']}")
        
        # 创建超级管理员用户
        superuser_username = "admin"
        superuser = crud.get_user_by_username(db, superuser_username)
        
        if not superuser:
            superuser_data = schemas.UserCreate(
                username=superuser_username,
                email="admin@example.com",
                password="admin123",
                full_name="系统管理员",
                is_active=True
            )
            superuser = crud.create_user(db, superuser_data)
            
            # 设置为超级用户
            superuser.is_superuser = True
            db.commit()
            
            # 分配admin角色
            admin_role = crud.get_role_by_name(db, "admin")
            if admin_role:
                crud.assign_role_to_user(db, superuser.id, admin_role.id)
            
            print(f"✅ 创建超级管理员: {superuser_username} (密码: admin123)")
        else:
            print(f"⚠️  超级管理员已存在: {superuser_username}")
        
        # 创建示例用户
        sample_users = [
            {
                "username": "manager1",
                "email": "manager@example.com",
                "password": "manager123",
                "full_name": "示例管理员",
                "role": "manager"
            },
            {
                "username": "user1",
                "email": "user@example.com", 
                "password": "user123",
                "full_name": "示例用户",
                "role": "user"
            }
        ]
        
        for user_data in sample_users:
            existing_user = crud.get_user_by_username(db, user_data["username"])
            if not existing_user:
                role_name = user_data.pop("role")
                user_create = schemas.UserCreate(**user_data)
                user = crud.create_user(db, user_create)
                
                # 分配角色
                role = crud.get_role_by_name(db, role_name)
                if role:
                    crud.assign_role_to_user(db, user.id, role.id)
                
                print(f"✅ 创建示例用户: {user_data['username']} (密码: {user_data['password']})")
            else:
                print(f"⚠️  用户已存在: {user_data['username']}")
        
        print("✅ 初始数据创建完成")
        
    except Exception as e:
        print(f"❌ 创建初始数据失败: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """主函数"""
    print("🚀 开始初始化数据库...")
    print(f"数据库URL: {settings.database_url}")
    
    try:
        # 创建表
        engine = create_tables()
        
        # 创建初始数据
        create_initial_data(engine)
        
        print("\n🎉 数据库初始化完成！")
        print("\n默认账户信息:")
        print("👤 超级管理员 - 用户名: admin, 密码: admin123")
        print("👤 管理员 - 用户名: manager1, 密码: manager123")
        print("👤 普通用户 - 用户名: user1, 密码: user123")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()