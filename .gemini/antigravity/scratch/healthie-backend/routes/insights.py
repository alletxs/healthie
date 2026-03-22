import os, json
from flask import Blueprint, request, jsonify
import google.generativeai as genai
from models import MealLog
from routes.auth import get_current_user
from datetime import datetime, timedelta

insights_bp = Blueprint('insights', __name__)

@insights_bp.route('/insights', methods=['GET'])
def get_insights():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return jsonify({'error': 'Gemini API key not configured'}), 500

    since = datetime.utcnow() - timedelta(days=30)
    meals = MealLog.query.filter(MealLog.user_id == user.id, MealLog.logged_at >= since).order_by(MealLog.logged_at.desc()).limit(50).all()

    if len(meals) < 3:
        return jsonify({'error': 'Log at least 3 meals to generate insights'}), 400

    meal_summary = "\n".join([
        f"- {m.logged_at.strftime('%Y-%m-%d %H:%M')}: {m.food_name} | {m.calories}kcal | P:{m.protein_g}g C:{m.carbs_g}g F:{m.fats_g}g Fiber:{m.fiber_g}g Sugar:{m.sugar_g}g Na:{m.sodium_mg}mg"
        for m in meals
    ])

    total_calories = sum(m.calories for m in meals)
    avg_cal = total_calories / len(meals)

    INSIGHTS_PROMPT = f"""You are a professional nutritionist and health coach. Analyze this person's meal history from the last 30 days and generate a personalized health intelligence report.

User: {user.name}
Total meals analyzed: {len(meals)}
Average calories per meal: {round(avg_cal)}

MEAL HISTORY:
{meal_summary}

Write a genuine, personalized report in plain language. Be specific — reference actual foods they ate. Do NOT be generic.

Return ONLY a valid JSON object:
{{
  "dietary_patterns": "3-4 sentences observing patterns in what they actually eat",
  "strengths": "3-4 sentences about genuine nutritional positives from their actual data",
  "improvements": "3-4 sentences about specific things to improve based on their actual data",
  "outlook": "2-3 sentences about long-term health trajectory if current habits continue",
  "recommendations": ["specific action 1 referencing actual foods", "specific action 2", "specific action 3", "specific action 4"],
  "metrics": {{
    "avg_daily_calories": {round(avg_cal)},
    "protein_consistency": number between 0-100 representing how consistently they hit protein goals,
    "diet_diversity": number between 1-10 rating variety of foods
  }}
}}"""

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        response = model.generate_content(INSIGHTS_PROMPT)
        raw = response.text.strip()
        import re
        raw = re.sub(r'^```(?:json)?\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        result = json.loads(raw.strip())
        return jsonify({'success': True, 'report': result, 'meals_analyzed': len(meals)}), 200
    except Exception as e:
        return jsonify({'error': f'Insight generation failed: {str(e)}'}), 500
