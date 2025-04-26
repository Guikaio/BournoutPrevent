import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask

# Initialize Firestore
db = None
try:
    firebase_project_id = os.environ.get("FIREBASE_PROJECT_ID")
    
    # Configure Firebase Admin SDK
    firebase_config = {
        'projectId': firebase_project_id,
    }
    
    # Use service account if available in environment
    cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # Use application default credentials if service account not provided
        cred = credentials.ApplicationDefault()
    
    # Initialize Firebase with explicit project ID
    firebase_admin.initialize_app(cred, firebase_config)
    db = firestore.client()
    logging.info("Firebase initialized successfully with project ID: %s", firebase_project_id)
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