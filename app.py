import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore, auth
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from models import User, Response
from main import db, app

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Firebase
firebase_db = None
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
    firebase_db = firestore.client()
    logging.info("Firebase initialized successfully with project ID: %s", firebase_project_id)
except Exception as e:
    logging.error(f"Error initializing Firebase: {e}")
    firebase_db = None

# Helper functions
def calculate_burnout_score(responses):
    """
    Calculate burnout score from questionnaire responses.
    Questions 5-15 are used for burnout calculation.
    """
    burnout_questions = [f"q{i}" for i in range(5, 16)]
    total_score = sum(int(responses.get(q, 0)) for q in burnout_questions)
    max_possible = 4 * len(burnout_questions)  # max score is 4 per question
    burnout_percentage = (total_score / max_possible) * 100
    
    return round(burnout_percentage, 1)

def is_authenticated():
    """Check if user is logged in via session"""
    return 'user_id' in session

def get_user_data(firebase_uid):
    """Retrieve user data from database"""
    try:
        # First try to get user from our PostgreSQL DB
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        if user:
            return {
                'name': user.name,
                'email': user.email,
                'latest_burnout_score': user.latest_burnout_score,
                'last_assessment': user.last_assessment
            }
        
        # If not in our DB and Firebase is available, try to get from Firebase
        if firebase_db:
            user_ref = firebase_db.collection('users').document(firebase_uid)
            firebase_data = user_ref.get()
            if firebase_data.exists:
                return firebase_data.to_dict()
        
        return None
    except Exception as e:
        logging.error(f"Error retrieving user data: {e}")
        return None

def save_questionnaire_responses(firebase_uid, responses, burnout_score):
    """Save questionnaire responses to database"""
    try:
        # Get current timestamp
        timestamp = datetime.now()
        
        # Get user from database
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        
        if not user:
            logging.error(f"User not found in database: {firebase_uid}")
            return False
        
        # Create new response
        new_response = Response(
            user_id=user.id,
            burnout_score=burnout_score,
            timestamp=timestamp,
            q1=responses.get('q1'),
            q2=responses.get('q2'),
            q3=responses.get('q3'),
            q4=responses.get('q4'),
            q5=responses.get('q5'),
            q6=responses.get('q6'),
            q7=responses.get('q7'),
            q8=responses.get('q8'),
            q9=responses.get('q9'),
            q10=responses.get('q10'),
            q11=responses.get('q11'),
            q12=responses.get('q12'),
            q13=responses.get('q13'),
            q14=responses.get('q14'),
            q15=responses.get('q15')
        )
        
        # Update user's latest score
        user.latest_burnout_score = burnout_score
        user.last_assessment = timestamp
        
        # Add to database
        db.session.add(new_response)
        db.session.commit()
        
        return True
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving questionnaire responses: {e}")
        return False

def get_burnout_history(firebase_uid):
    """Get user's burnout history"""
    try:
        # Get user from database
        user = User.query.filter_by(firebase_uid=firebase_uid).first()
        
        if not user:
            logging.error(f"User not found in database: {firebase_uid}")
            return []
        
        # Get responses from database
        responses = Response.query.filter_by(user_id=user.id).order_by(Response.timestamp).all()
        
        history = []
        for response in responses:
            history.append({
                'score': response.burnout_score,
                'timestamp': response.timestamp.strftime('%d/%m/%Y') if response.timestamp else 'Unknown'
            })
        
        return history
    except Exception as e:
        logging.error(f"Error retrieving burnout history: {e}")
        return []

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if is_authenticated():
        return redirect(url_for('dashboard'))
    
    firebase_api_key = os.environ.get("FIREBASE_API_KEY", "")
    firebase_project_id = os.environ.get("FIREBASE_PROJECT_ID", "")
    firebase_app_id = os.environ.get("FIREBASE_APP_ID", "")
    
    return render_template(
        'index.html',
        firebase_api_key=firebase_api_key,
        firebase_project_id=firebase_project_id,
        firebase_app_id=firebase_app_id
    )

@app.route('/auth/firebase-api', methods=['POST'])
def auth_firebase():
    """Handle Firebase authentication sync with our server session"""
    try:
        firebase_uid = request.form.get('firebase_uid')
        email = request.form.get('email')
        name = request.form.get('name')
        
        if not firebase_uid or not email:
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Verify the Firebase user
        try:
            # Verify with Firebase Admin SDK
            firebase_user = auth.get_user(firebase_uid)
            
            # Check if user exists in our DB
            user = User.query.filter_by(firebase_uid=firebase_uid).first()
            
            if not user:
                # Create user in our DB
                user = User(
                    firebase_uid=firebase_uid,
                    name=name or firebase_user.display_name,
                    email=email,
                    created_at=datetime.now()
                )
                db.session.add(user)
                db.session.commit()
            
            # Log in the user
            login_user(user)
            
            # Set user session for backward compatibility 
            session['user_id'] = firebase_uid
            session['user_name'] = name or firebase_user.display_name
            session['user_email'] = email
            
            return jsonify({"success": True, "redirect": url_for('dashboard')})
            
        except Exception as auth_error:
            logging.error(f"Firebase auth verification error: {auth_error}")
            return jsonify({"error": "Failed to verify user with Firebase"}), 401
            
    except Exception as e:
        logging.error(f"Firebase auth error: {e}")
        return jsonify({"error": "Authentication failed"}), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if is_authenticated():
        return redirect(url_for('dashboard'))
    
    firebase_api_key = os.environ.get("FIREBASE_API_KEY", "")
    firebase_project_id = os.environ.get("FIREBASE_PROJECT_ID", "")
    firebase_app_id = os.environ.get("FIREBASE_APP_ID", "")
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if not email or not password or not name:
            flash('Por favor, preencha todos os campos', 'error')
            return redirect(url_for('register'))
        
        try:
            # Create user in Firebase Auth
            firebase_user = auth.create_user(
                email=email,
                password=password,
                display_name=name
            )
            
            # Create user in our DB
            user = User(
                firebase_uid=firebase_user.uid,
                name=name,
                email=email,
                created_at=datetime.now()
            )
            db.session.add(user)
            db.session.commit()
            
            flash('Conta criada com sucesso! Por favor, faça login.', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {e}")
            flash('Erro ao criar conta. Este e-mail pode já estar em uso.', 'error')
    
    return render_template(
        'register.html',
        firebase_api_key=firebase_api_key,
        firebase_project_id=firebase_project_id,
        firebase_app_id=firebase_app_id
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if is_authenticated():
        return redirect(url_for('dashboard'))
    
    firebase_api_key = os.environ.get("FIREBASE_API_KEY", "")
    firebase_project_id = os.environ.get("FIREBASE_PROJECT_ID", "")
    firebase_app_id = os.environ.get("FIREBASE_APP_ID", "")
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Por favor, preencha todos os campos', 'error')
            return redirect(url_for('login'))
        
        try:
            # Check if user exists in Firebase Auth
            try:
                firebase_user = auth.get_user_by_email(email)
                
                # For demo purposes since we can't verify password on server side
                # In a real app, authentication should be done client-side with Firebase Authentication
                
                # Check if user exists in our DB
                user = User.query.filter_by(firebase_uid=firebase_user.uid).first()
                
                if not user:
                    # Create user in our DB
                    user = User(
                        firebase_uid=firebase_user.uid,
                        name=firebase_user.display_name,
                        email=firebase_user.email,
                        created_at=datetime.now()
                    )
                    db.session.add(user)
                    db.session.commit()
                
                # Log in the user with Flask-Login
                login_user(user)
                
                # Set user session for backward compatibility
                session['user_id'] = firebase_user.uid
                session['user_name'] = firebase_user.display_name
                session['user_email'] = firebase_user.email
                
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as auth_error:
                logging.error(f"Authentication error: {auth_error}")
                flash('Email ou senha inválidos', 'error')
        
        except Exception as e:
            logging.error(f"Login error: {e}")
            flash('Ocorreu um erro durante o login. Tente novamente.', 'error')
    
    return render_template(
        'login.html',
        firebase_api_key=firebase_api_key,
        firebase_project_id=firebase_project_id,
        firebase_app_id=firebase_app_id
    )

@app.route('/logout')
def logout():
    logout_user()  # Flask-Login logout
    session.clear()  # Clear session for complete logout
    flash('Você foi desconectado', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session.get('user_id')
    user_data = get_user_data(user_id)
    
    if not user_data:
        flash('Erro ao carregar dados do usuário', 'error')
        return redirect(url_for('index'))
    
    # Get burnout history
    burnout_history = get_burnout_history(user_id)
    
    # Get latest burnout score
    latest_score = user_data.get('latest_burnout_score')
    
    # Check if the user has completed the questionnaire
    has_completed_questionnaire = latest_score is not None
    
    return render_template(
        'dashboard.html',
        user_name=session.get('user_name'),
        latest_score=latest_score,
        burnout_history=burnout_history,
        has_completed_questionnaire=has_completed_questionnaire
    )

@app.route('/questionnaire', methods=['GET', 'POST'])
@login_required
def questionnaire():
    if request.method == 'POST':
        user_id = session.get('user_id')
        
        # Extract responses from form
        responses = {key: request.form.get(key) for key in request.form if key.startswith('q')}
        
        # Calculate burnout score
        burnout_score = calculate_burnout_score(responses)
        
        # Save responses to database
        if save_questionnaire_responses(user_id, responses, burnout_score):
            flash('Questionário enviado com sucesso!', 'success')
        else:
            flash('Erro ao salvar respostas. Tente novamente.', 'error')
        
        return redirect(url_for('dashboard'))
    
    return render_template('questionnaire.html')

@app.route('/tips')
@login_required
def tips():
    return render_template('tips.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    logging.error(f"Server error: {e}")
    return render_template('index.html'), 500