"""
Library Management System
Main application entry point
"""
from flask import Flask
from models import db
from routes_auth import auth_bp
from routes_admin import admin_bp
from routes_library import library_bp
from config import *
from datetime import datetime


def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_BINDS'] = SQLALCHEMY_BINDS
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['PROFILE_UPLOAD_FOLDER'] = PROFILE_UPLOAD_FOLDER
    app.config['BOOK_UPLOAD_FOLDER'] = BOOK_UPLOAD_FOLDER
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(library_bp)
    
    # Context processor for templates
    @app.context_processor
    def inject_globals():
        return {'datetime': datetime}
    
    # Initialize database
    with app.app_context():
        db.create_all()
        
        # Schema migrations for existing databases
        try:
            conn = db.engines['users'].raw_connection()
            cur = conn.cursor()
            
            # Add missing columns if they don't exist
            cur.execute("PRAGMA table_info('user');")
            cols = [r[1] for r in cur.fetchall()]
            
            if 'profile_pic' not in cols:
                cur.execute("ALTER TABLE user ADD COLUMN profile_pic TEXT;")
                conn.commit()
            
            if 'email' not in cols:
                cur.execute("ALTER TABLE user ADD COLUMN email TEXT;")
                conn.commit()
            
            if 'role' not in cols:
                cur.execute("ALTER TABLE user ADD COLUMN role TEXT DEFAULT 'user';")
                conn.commit()
        except Exception:
            pass
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
