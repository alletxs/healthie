from flask import Blueprint, request, jsonify
from models import db, MealLog
from routes.auth import get_current_user
import json
from datetime import datetime, timedelta

meals_bp = Blueprint('meals', __name__)

@meals_bp.route('/save', methods=['POST'])
def save_meal():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    n = data.get('nutrition', {})
    commentary = data.get('commentary', {})

    meal = MealLog(
        user_id=user.id,
        food_name=data.get('food_name', 'Unknown Food'),
        calories=n.get('calories', 0),
        protein_g=n.get('protein_g', 0),
        carbs_g=n.get('carbs_g', 0),
        fats_g=n.get('fats_g', 0),
        fiber_g=n.get('fiber_g', 0),
        sugar_g=n.get('sugar_g', 0),
        sodium_mg=n.get('sodium_mg', 0),
        commentary_json=json.dumps(commentary),
        image_data_url=data.get('image_data_url', None)
    )
    db.session.add(meal)
    db.session.commit()
    return jsonify({'success': True, 'meal': meal.to_dict()}), 201

@meals_bp.route('/history', methods=['GET'])
def get_history():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    limit = request.args.get('limit', 100, type=int)
    meals = MealLog.query.filter_by(user_id=user.id).order_by(MealLog.logged_at.desc()).limit(limit).all()
    return jsonify({'meals': [m.to_dict() for m in meals]}), 200

@meals_bp.route('/delete/<int:meal_id>', methods=['DELETE'])
def delete_meal(meal_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    meal = MealLog.query.filter_by(id=meal_id, user_id=user.id).first()
    if not meal:
        return jsonify({'error': 'Meal not found'}), 404

    db.session.delete(meal)
    db.session.commit()
    return jsonify({'success': True}), 200

@meals_bp.route('/analytics', methods=['GET'])
def get_analytics():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)
    meals = MealLog.query.filter(MealLog.user_id == user.id, MealLog.logged_at >= since).order_by(MealLog.logged_at.asc()).all()

    # Group by date
    daily = {}
    for meal in meals:
        d = meal.logged_at.strftime('%Y-%m-%d')
        if d not in daily:
            daily[d] = {'date': d, 'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0, 'meal_count': 0}
        daily[d]['calories'] += meal.calories
        daily[d]['protein'] += meal.protein_g
        daily[d]['carbs'] += meal.carbs_g
        daily[d]['fats'] += meal.fats_g
        daily[d]['meal_count'] += 1

    daily_list = sorted(daily.values(), key=lambda x: x['date'])
    avg_calories = sum(d['calories'] for d in daily_list) / len(daily_list) if daily_list else 0

    return jsonify({
        'daily': daily_list,
        'total_meals': len(meals),
        'avg_daily_calories': round(avg_calories, 1),
        'days_tracked': len(daily_list)
    }), 200
