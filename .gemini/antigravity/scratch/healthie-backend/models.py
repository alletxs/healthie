from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    meals = db.relationship('MealLog', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'email': self.email, 'created_at': self.created_at.isoformat()}

class MealLog(db.Model):
    __tablename__ = 'meal_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    food_name = db.Column(db.String(200), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    protein_g = db.Column(db.Float, default=0)
    carbs_g = db.Column(db.Float, default=0)
    fats_g = db.Column(db.Float, default=0)
    fiber_g = db.Column(db.Float, default=0)
    sugar_g = db.Column(db.Float, default=0)
    sodium_mg = db.Column(db.Float, default=0)
    commentary_json = db.Column(db.Text, default='{}')
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    image_data_url = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'food_name': self.food_name,
            'calories': self.calories,
            'protein_g': self.protein_g,
            'carbs_g': self.carbs_g,
            'fats_g': self.fats_g,
            'fiber_g': self.fiber_g,
            'sugar_g': self.sugar_g,
            'sodium_mg': self.sodium_mg,
            'commentary': json.loads(self.commentary_json or '{}'),
            'logged_at': self.logged_at.isoformat(),
            'image_data_url': self.image_data_url
        }
