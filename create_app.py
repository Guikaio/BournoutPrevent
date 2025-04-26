import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.secret_key = os.environ.get("SESSION_SECRET", "burnout-prevention-secret-key")
    
    # Configure database - using SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///burnout_prevention.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize database with app
    db.init_app(app)
    
    # Create tables within application context
    with app.app_context():
        from models import User, Response
        db.create_all()
    
    # Import and register blueprints/routes
    from routes import init_app
    init_app(app)
    
    return app