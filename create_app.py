import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Firestore
db = None
try:
    firebase_project_id = os.environ.get("FIREBASE_PROJECT_ID")
    
    # Configure Firebase Admin SDK
    firebase_config = {
        'projectId': firebase_project_id,
    }
    
    # Check if Firebase is already initialized
    if not firebase_admin._apps:
        # Not initialized yet, proceed with initialization
        try:
            # Use application default credentials
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, firebase_config)
            logging.info("Firebase initialized with application default credentials")
        except Exception as cred_error:
            logging.error(f"Error with application default credentials: {cred_error}")
            # Fall back to a simpler initialization without credentials (limited functionality)
            firebase_admin.initialize_app(options=firebase_config)
            logging.info("Firebase initialized without credentials")
    
    # Get Firestore client
    db = firestore.client()
    logging.info("Firestore client created successfully")
    
except Exception as e:
    logging.error(f"Error initializing Firebase: {e}")
    db = None

def create_app():
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.secret_key = os.environ.get("SESSION_SECRET", "burnout-prevention-secret-key")
    
    # Import and register blueprints/routes
    from routes import init_app
    init_app(app)
    
    return app