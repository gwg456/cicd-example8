from flask import Blueprint, request, jsonify
from datetime import datetime, date
from auth import token_required
from models import db, DietPlan, WeightRecord, MealRecord, Exercise

diet_bp = Blueprint('diet', __name__, url_prefix='/api')

# 减肥计划管理
@diet_bp.route('/diet-plans', methods=['GET'])
@token_required
def get_diet_plans():
    """获取用户的减肥计划列表"""
    user = request.current_user
    plans = DietPlan.query.filter_by(user_id=user.id).order_by(DietPlan.created_at.desc()).all()
    
    return jsonify([{
        'id': plan.id,
        'name': plan.name,
        'description': plan.description,
        'start_date': plan.start_date.isoformat(),
        'end_date': plan.end_date.isoformat() if plan.end_date else None,
        'target_calories': plan.target_calories,
        'target_protein': plan.target_protein,
        'target_carbs': plan.target_carbs,
        'target_fat': plan.target_fat,
        'is_active': plan.is_active,
        'created_at': plan.created_at.isoformat()
    } for plan in plans])

@diet_bp.route('/diet-plans', methods=['POST'])
@token_required
def create_diet_plan():
    """创建新的减肥计划"""
    try:
        user = request.current_user
        data = request.get_json()
        
        # 如果创建新的活跃计划，将其他计划设为非活跃
        if data.get('is_active', True):
            DietPlan.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
        
        plan = DietPlan(
            user_id=user.id,
            name=data['name'],
            description=data.get('description', ''),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
            target_calories=data.get('target_calories'),
            target_protein=data.get('target_protein'),
            target_carbs=data.get('target_carbs'),
            target_fat=data.get('target_fat'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(plan)
        db.session.commit()
        
        return jsonify({
            'id': plan.id,
            'message': 'Diet plan created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create diet plan', 'details': str(e)}), 500

@diet_bp.route('/diet-plans/<int:plan_id>', methods=['PUT'])
@token_required
def update_diet_plan(plan_id):
    """更新减肥计划"""
    try:
        user = request.current_user
        plan = DietPlan.query.filter_by(id=plan_id, user_id=user.id).first()
        
        if not plan:
            return jsonify({'error': 'Diet plan not found'}), 404
        
        data = request.get_json()
        
        # 如果设置为活跃计划，将其他计划设为非活跃
        if data.get('is_active') and not plan.is_active:
            DietPlan.query.filter_by(user_id=user.id, is_active=True).update({'is_active': False})
        
        # 更新字段
        if 'name' in data:
            plan.name = data['name']
        if 'description' in data:
            plan.description = data['description']
        if 'start_date' in data:
            plan.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if 'end_date' in data:
            plan.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data['end_date'] else None
        if 'target_calories' in data:
            plan.target_calories = data['target_calories']
        if 'target_protein' in data:
            plan.target_protein = data['target_protein']
        if 'target_carbs' in data:
            plan.target_carbs = data['target_carbs']
        if 'target_fat' in data:
            plan.target_fat = data['target_fat']
        if 'is_active' in data:
            plan.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({'message': 'Diet plan updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update diet plan', 'details': str(e)}), 500

# 体重记录管理
@diet_bp.route('/weight-records', methods=['GET'])
@token_required
def get_weight_records():
    """获取体重记录"""
    user = request.current_user
    
    # 获取查询参数
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    limit = request.args.get('limit', 30, type=int)
    
    query = WeightRecord.query.filter_by(user_id=user.id)
    
    if start_date:
        query = query.filter(WeightRecord.recorded_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(WeightRecord.recorded_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    records = query.order_by(WeightRecord.recorded_date.desc()).limit(limit).all()
    
    return jsonify([{
        'id': record.id,
        'weight': record.weight,
        'recorded_date': record.recorded_date.isoformat(),
        'notes': record.notes,
        'created_at': record.created_at.isoformat()
    } for record in records])

@diet_bp.route('/weight-records', methods=['POST'])
@token_required
def add_weight_record():
    """添加体重记录"""
    try:
        user = request.current_user
        data = request.get_json()
        
        record = WeightRecord(
            user_id=user.id,
            weight=data['weight'],
            recorded_date=datetime.strptime(data['recorded_date'], '%Y-%m-%d').date(),
            notes=data.get('notes', '')
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'id': record.id,
            'message': 'Weight record added successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add weight record', 'details': str(e)}), 500

# 饮食记录管理
@diet_bp.route('/meal-records', methods=['GET'])
@token_required
def get_meal_records():
    """获取饮食记录"""
    user = request.current_user
    
    # 获取查询参数
    meal_date = request.args.get('date', date.today().isoformat())
    
    records = MealRecord.query.filter_by(
        user_id=user.id,
        meal_date=datetime.strptime(meal_date, '%Y-%m-%d').date()
    ).order_by(MealRecord.created_at.asc()).all()
    
    return jsonify([{
        'id': record.id,
        'meal_type': record.meal_type,
        'food_name': record.food_name,
        'quantity': record.quantity,
        'unit': record.unit,
        'calories': record.calories,
        'protein': record.protein,
        'carbs': record.carbs,
        'fat': record.fat,
        'meal_date': record.meal_date.isoformat(),
        'created_at': record.created_at.isoformat()
    } for record in records])

@diet_bp.route('/meal-records', methods=['POST'])
@token_required
def add_meal_record():
    """添加饮食记录"""
    try:
        user = request.current_user
        data = request.get_json()
        
        record = MealRecord(
            user_id=user.id,
            meal_type=data['meal_type'],
            food_name=data['food_name'],
            quantity=data['quantity'],
            unit=data['unit'],
            calories=data.get('calories'),
            protein=data.get('protein'),
            carbs=data.get('carbs'),
            fat=data.get('fat'),
            meal_date=datetime.strptime(data['meal_date'], '%Y-%m-%d').date()
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'id': record.id,
            'message': 'Meal record added successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add meal record', 'details': str(e)}), 500

# 运动记录管理
@diet_bp.route('/exercises', methods=['GET'])
@token_required
def get_exercises():
    """获取运动记录"""
    user = request.current_user
    
    # 获取查询参数
    exercise_date = request.args.get('date', date.today().isoformat())
    
    exercises = Exercise.query.filter_by(
        user_id=user.id,
        exercise_date=datetime.strptime(exercise_date, '%Y-%m-%d').date()
    ).order_by(Exercise.created_at.asc()).all()
    
    return jsonify([{
        'id': exercise.id,
        'exercise_name': exercise.exercise_name,
        'duration': exercise.duration,
        'calories_burned': exercise.calories_burned,
        'exercise_date': exercise.exercise_date.isoformat(),
        'notes': exercise.notes,
        'created_at': exercise.created_at.isoformat()
    } for exercise in exercises])

@diet_bp.route('/exercises', methods=['POST'])
@token_required
def add_exercise():
    """添加运动记录"""
    try:
        user = request.current_user
        data = request.get_json()
        
        exercise = Exercise(
            user_id=user.id,
            exercise_name=data['exercise_name'],
            duration=data['duration'],
            calories_burned=data.get('calories_burned'),
            exercise_date=datetime.strptime(data['exercise_date'], '%Y-%m-%d').date(),
            notes=data.get('notes', '')
        )
        
        db.session.add(exercise)
        db.session.commit()
        
        return jsonify({
            'id': exercise.id,
            'message': 'Exercise record added successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to add exercise record', 'details': str(e)}), 500

# 统计数据
@diet_bp.route('/dashboard', methods=['GET'])
@token_required
def get_dashboard():
    """获取仪表板数据"""
    user = request.current_user
    today = date.today()
    
    # 获取今日饮食记录
    today_meals = MealRecord.query.filter_by(user_id=user.id, meal_date=today).all()
    today_calories = sum(meal.calories or 0 for meal in today_meals)
    today_protein = sum(meal.protein or 0 for meal in today_meals)
    today_carbs = sum(meal.carbs or 0 for meal in today_meals)
    today_fat = sum(meal.fat or 0 for meal in today_meals)
    
    # 获取今日运动记录
    today_exercises = Exercise.query.filter_by(user_id=user.id, exercise_date=today).all()
    today_exercise_calories = sum(ex.calories_burned or 0 for ex in today_exercises)
    
    # 获取最新体重记录
    latest_weight = WeightRecord.query.filter_by(user_id=user.id).order_by(WeightRecord.recorded_date.desc()).first()
    
    # 获取活跃的减肥计划
    active_plan = DietPlan.query.filter_by(user_id=user.id, is_active=True).first()
    
    return jsonify({
        'today_nutrition': {
            'calories': today_calories,
            'protein': today_protein,
            'carbs': today_carbs,
            'fat': today_fat
        },
        'today_exercise_calories': today_exercise_calories,
        'latest_weight': latest_weight.weight if latest_weight else None,
        'weight_date': latest_weight.recorded_date.isoformat() if latest_weight else None,
        'active_plan': {
            'id': active_plan.id,
            'name': active_plan.name,
            'target_calories': active_plan.target_calories,
            'target_protein': active_plan.target_protein,
            'target_carbs': active_plan.target_carbs,
            'target_fat': active_plan.target_fat
        } if active_plan else None
    })