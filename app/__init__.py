import logging
import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import inspect, text
from .config import Config
from .extensions import db, limiter

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise RuntimeError('DATABASE_URL must be configured with a MySQL connection string.')
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
    db.init_app(app)
    limiter.init_app(app)
    # Vite can be opened as either localhost or 127.0.0.1 in development.
    # Permit both so the browser can complete its preflight and send the API POST.
    allowed_origins = list({
        app.config['FRONTEND_URL'].rstrip('/'),
        r'^http://localhost(:\d+)?$',
        r'^http://127\.0\.0\.1(:\d+)?$',
    })
    CORS(app, resources={r'/api/*': {'origins': allowed_origins}}, methods=['GET', 'POST'], allow_headers=['Content-Type', 'X-Export-Secret'], supports_credentials=True)
    from .routes import api
    app.register_blueprint(api)

    @app.get('/')
    def root_health_check():
        return jsonify({'success': True, 'message': 'MobileHub Backend is running'})

    @app.errorhandler(429)
    def rate_limited(_error):
        return jsonify({'success': False, 'message': 'Too many requests. Please wait a moment and try again.'}), 429

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({'success': False, 'message': 'Route not found.'}), 404

    @app.cli.command('init-db')
    def init_db():
        from .seed import seed_prizes
        with app.app_context():
            db.create_all()
            # Existing installations predate the social-confirmation columns.
            # Add them once without touching customer or prize data.
            inspector = inspect(db.engine)
            existing_columns = {column['name'] for column in inspector.get_columns('customers')}
            for column in ('facebook_completed', 'instagram_completed', 'whatsapp_completed'):
                if column not in existing_columns:
                    db.session.execute(text(f'ALTER TABLE customers ADD COLUMN {column} BOOLEAN NOT NULL DEFAULT FALSE'))
            db.session.commit()
            seed_prizes()
        print('Database tables created and prizes seeded.')

    return app
