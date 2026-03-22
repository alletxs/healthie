import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from models import db
from routes.auth import auth_bp
from routes.analyze import analyze_bp
from routes.meals import meals_bp
from routes.insights import insights_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'healthie-dev-secret-2025')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthie.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    db.init_app(app)

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(analyze_bp, url_prefix='/api')
    app.register_blueprint(meals_bp, url_prefix='/api/meals')
    app.register_blueprint(insights_bp, url_prefix='/api')

    with app.app_context():
        db.create_all()

    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'app': 'Healthie API', 'version': '1.0.0'}

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=False, port=5000)
