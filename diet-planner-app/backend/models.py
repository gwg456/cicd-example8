from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    azure_id = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 用户基本信息
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    height = db.Column(db.Float)  # cm
    current_weight = db.Column(db.Float)  # kg
    target_weight = db.Column(db.Float)  # kg
    activity_level = db.Column(db.String(20))  # sedentary, light, moderate, active, very_active
    
    # 关联关系
    diet_plans = db.relationship('DietPlan', backref='user', lazy=True, cascade='all, delete-orphan')
    weight_records = db.relationship('WeightRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    meal_records = db.relationship('MealRecord', backref='user', lazy=True, cascade='all, delete-orphan')

class DietPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    target_calories = db.Column(db.Integer)  # 每日目标卡路里
    target_protein = db.Column(db.Float)     # 每日目标蛋白质(g)
    target_carbs = db.Column(db.Float)       # 每日目标碳水化合物(g)
    target_fat = db.Column(db.Float)         # 每日目标脂肪(g)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WeightRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)  # kg
    recorded_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MealRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_type = db.Column(db.String(20), nullable=False)  # breakfast, lunch, dinner, snack
    food_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False)  # g, ml, piece, etc.
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fat = db.Column(db.Float)
    meal_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    exercise_name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    calories_burned = db.Column(db.Float)
    exercise_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)