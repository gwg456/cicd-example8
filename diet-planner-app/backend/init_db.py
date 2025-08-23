#!/usr/bin/env python3
"""
数据库初始化脚本
用于创建数据库表和初始数据
"""

from app import create_app
from models import db, User, DietPlan, WeightRecord, MealRecord, Exercise
from datetime import datetime, date

def init_database():
    """初始化数据库"""
    app = create_app()
    
    with app.app_context():
        print("正在创建数据库表...")
        
        # 删除所有表（如果存在）
        db.drop_all()
        
        # 创建所有表
        db.create_all()
        
        print("数据库表创建完成！")
        print("\n创建的表:")
        print("- users: 用户信息表")
        print("- diet_plan: 减肥计划表") 
        print("- weight_record: 体重记录表")
        print("- meal_record: 饮食记录表")
        print("- exercise: 运动记录表")
        
        # 可选：创建示例数据
        create_sample_data = input("\n是否创建示例数据? (y/N): ").lower().strip()
        
        if create_sample_data == 'y':
            create_sample_data_records()
            print("示例数据创建完成！")
        
        print("\n数据库初始化完成！")

def create_sample_data_records():
    """创建示例数据"""
    try:
        # 创建示例用户（注意：这只是用于开发测试）
        sample_user = User(
            azure_id='sample-user-123',
            email='sample@example.com',
            name='示例用户',
            age=25,
            gender='female',
            height=165.0,
            current_weight=65.0,
            target_weight=60.0,
            activity_level='moderate'
        )
        db.session.add(sample_user)
        db.session.flush()  # 获取用户ID
        
        # 创建示例减肥计划
        sample_plan = DietPlan(
            user_id=sample_user.id,
            name='春季减脂计划',
            description='为期3个月的健康减脂计划，目标减重5公斤',
            start_date=date.today(),
            target_calories=1800,
            target_protein=120.0,
            target_carbs=180.0,
            target_fat=60.0,
            is_active=True
        )
        db.session.add(sample_plan)
        
        # 创建示例体重记录
        weight_records = [
            WeightRecord(user_id=sample_user.id, weight=65.0, recorded_date=date.today(), notes='开始记录'),
            WeightRecord(user_id=sample_user.id, weight=64.5, recorded_date=date(2024, 1, 1), notes='新年第一称'),
        ]
        for record in weight_records:
            db.session.add(record)
        
        # 创建示例饮食记录
        meal_records = [
            MealRecord(
                user_id=sample_user.id,
                meal_type='breakfast',
                food_name='燕麦粥',
                quantity=100,
                unit='g',
                calories=350,
                protein=12.0,
                carbs=60.0,
                fat=8.0,
                meal_date=date.today()
            ),
            MealRecord(
                user_id=sample_user.id,
                meal_type='lunch',
                food_name='鸡胸肉沙拉',
                quantity=200,
                unit='g',
                calories=280,
                protein=35.0,
                carbs=15.0,
                fat=8.0,
                meal_date=date.today()
            )
        ]
        for record in meal_records:
            db.session.add(record)
        
        # 创建示例运动记录
        exercise_records = [
            Exercise(
                user_id=sample_user.id,
                exercise_name='慢跑',
                duration=30,
                calories_burned=250,
                exercise_date=date.today(),
                notes='晨跑，感觉很好'
            ),
            Exercise(
                user_id=sample_user.id,
                exercise_name='瑜伽',
                duration=45,
                calories_burned=150,
                exercise_date=date.today(),
                notes='拉伸运动'
            )
        ]
        for record in exercise_records:
            db.session.add(record)
        
        db.session.commit()
        print("✓ 示例数据已创建")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ 创建示例数据失败: {e}")
        raise

if __name__ == '__main__':
    init_database()