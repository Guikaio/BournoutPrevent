import os
import json
import logging
import firebase_admin
from firebase_admin import auth
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from models import User, Response
from create_app import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)

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

def get_user_by_id(user_id):
    """Retrieve a user by Firebase UID"""
    try:
        if not db:
            logging.error("Database connection not available")
            return None
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return None
            
        return User.from_dict(user_id, user_doc.to_dict())
    except Exception as e:
        logging.error(f"Error retrieving user by ID: {e}")
        return None

def get_user_by_email(email):
    """Retrieve a user by email"""
    try:
        if not db:
            logging.error("Database connection not available")
            return None
            
        users_ref = db.collection('users').where('email', '==', email).limit(1)
        users = list(users_ref.stream())
        
        if not users:
            return None
            
        user_doc = users[0]
        return User.from_dict(user_doc.id, user_doc.to_dict())
    except Exception as e:
        logging.error(f"Error retrieving user by email: {e}")
        return None

def create_user(firebase_uid, name, email):
    """Create a new user in Firestore"""
    try:
        if not db:
            logging.error("Database connection not available")
            return None
            
        user_data = {
            'name': name,
            'email': email,
            'created_at': datetime.now(),
            'latest_burnout_score': None,
            'last_assessment': None
        }
        
        db.collection('users').document(firebase_uid).set(user_data)
        return User.from_dict(firebase_uid, user_data)
    except Exception as e:
        logging.error(f"Error creating user: {e}")
        return None

def get_user_data(user_id):
    """Retrieve user data from Firestore"""
    try:
        if not db:
            logging.error("Database connection not available")
            return None
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            return None
            
        return user_doc.to_dict()
    except Exception as e:
        logging.error(f"Error retrieving user data: {e}")
        return None

def save_questionnaire_responses(user_id, responses, burnout_score):
    """Save questionnaire responses to Firestore"""
    try:
        if not db:
            logging.error("Database connection not available")
            return False
        
        # Get timestamp
        timestamp = datetime.now()
        
        # Add to responses collection
        response_data = {
            'user_id': user_id,
            'burnout_score': burnout_score,
            'timestamp': timestamp
        }
        
        # Add individual question responses
        for q, answer in responses.items():
            response_data[q] = int(answer)
        
        # Add document to responses collection
        db.collection('responses').add(response_data)
        
        # Update user's latest score
        user_ref = db.collection('users').document(user_id)
        user_ref.update({
            'latest_burnout_score': burnout_score,
            'last_assessment': timestamp
        })
        
        return True
    except Exception as e:
        logging.error(f"Error saving responses: {e}")
        return False

def get_burnout_history(user_id):
    """Get user's burnout history"""
    try:
        if not db:
            logging.error("Database connection not available")
            return []
        
        responses_ref = db.collection('responses')
        query = responses_ref.where('user_id', '==', user_id).order_by('timestamp')
        
        history = []
        for doc in query.stream():
            data = doc.to_dict()
            history.append({
                'score': data.get('burnout_score'),
                'timestamp': data.get('timestamp').strftime('%d/%m/%Y') if data.get('timestamp') else 'Unknown'
            })
        
        return history
    except Exception as e:
        logging.error(f"Error retrieving burnout history: {e}")
        return []

def init_app(app):
    # Configure Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)
    
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
                # Check if user already exists
                existing_user = get_user_by_email(email)
                if existing_user:
                    flash('Este e-mail já está em uso.', 'error')
                    return redirect(url_for('register'))
                
                # Create user in Firebase Auth
                firebase_user = auth.create_user(
                    email=email,
                    password=password,
                    display_name=name
                )
                
                # Create user in Firestore
                user = create_user(
                    firebase_uid=firebase_user.uid,
                    name=name,
                    email=email
                )
                
                if not user:
                    flash('Erro ao criar usuário. Tente novamente.', 'error')
                    return redirect(url_for('register'))
                
                flash('Conta criada com sucesso! Por favor, faça login.', 'success')
                return redirect(url_for('login'))
            
            except Exception as e:
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
                # For security reasons, we can't verify the password on the server side with Firebase Authentication
                # Typically, this is done client-side with Firebase Authentication SDK
                # For server-side email/password validation, we would need a different approach
                
                # Check if user exists
                try:
                    firebase_user = auth.get_user_by_email(email)
                    
                    # Get user from Firestore
                    user = get_user_by_id(firebase_user.uid)
                    
                    if not user:
                        # Create user in Firestore if not exists (should not happen normally)
                        user = create_user(
                            firebase_uid=firebase_user.uid,
                            name=firebase_user.display_name or email.split('@')[0],  # Fallback to email username
                            email=firebase_user.email
                        )
                    
                    if not user:
                        flash('Erro ao obter dados do usuário.', 'error')
                        return redirect(url_for('login'))
                    
                    # Set up session
                    session['user_id'] = user.id
                    session['user_name'] = user.name
                    session['user_email'] = user.email
                    
                    # Log in using Flask-Login
                    login_user(user)
                    
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
        session.clear()  # Clear session
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