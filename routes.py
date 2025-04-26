import os
import logging
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

def get_user_data(user_id):
    """Retrieve user data from database"""
    try:
        user = User.query.get(user_id)
        if not user:
            return None
        
        return {
            'name': user.name,
            'email': user.email,
            'latest_burnout_score': user.latest_burnout_score,
            'last_assessment': user.last_assessment
        }
    except Exception as e:
        logging.error(f"Error retrieving user data: {e}")
        return None

def save_questionnaire_responses(user_id, responses, burnout_score):
    """Save questionnaire responses to database"""
    try:
        # Get current timestamp
        timestamp = datetime.now()
        
        # Get user from database
        user = User.query.get(user_id)
        
        if not user:
            logging.error(f"User not found in database: {user_id}")
            return False
        
        # Create new response
        new_response = Response(
            user_id=user.id,
            burnout_score=burnout_score,
            timestamp=timestamp
        )
        
        # Add individual question responses
        for q, answer in responses.items():
            if hasattr(new_response, q):  # Check if question field exists
                setattr(new_response, q, int(answer))
        
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

def get_burnout_history(user_id):
    """Get user's burnout history"""
    try:
        # Get responses from database
        responses = Response.query.filter_by(user_id=user_id).order_by(Response.timestamp).all()
        
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

def init_app(app):
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
        
        return render_template('index.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if is_authenticated():
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            name = request.form.get('name')
            
            if not email or not password or not name:
                flash('Por favor, preencha todos os campos', 'error')
                return redirect(url_for('register'))
            
            try:
                # Check if user already exists
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('Este e-mail já está em uso.', 'error')
                    return redirect(url_for('register'))
                
                # Create user in database
                user = User(
                    name=name,
                    email=email,
                    created_at=datetime.now()
                )
                user.set_password(password)
                
                db.session.add(user)
                db.session.commit()
                
                flash('Conta criada com sucesso! Por favor, faça login.', 'success')
                return redirect(url_for('login'))
            
            except Exception as e:
                db.session.rollback()
                logging.error(f"Registration error: {e}")
                flash('Erro ao criar conta. Este e-mail pode já estar em uso.', 'error')
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if is_authenticated():
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                flash('Por favor, preencha todos os campos', 'error')
                return redirect(url_for('login'))
            
            try:
                # Find user by email
                user = User.query.filter_by(email=email).first()
                
                if not user or not user.check_password(password):
                    flash('Email ou senha inválidos', 'error')
                    return redirect(url_for('login'))
                
                # Set up session
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_email'] = user.email
                
                # Log in using Flask-Login
                login_user(user)
                
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                logging.error(f"Login error: {e}")
                flash('Ocorreu um erro durante o login. Tente novamente.', 'error')
        
        return render_template('login.html')
    
    @app.route('/logout')
    def logout():
        logout_user()  # Flask-Login logout
        session.clear()  # Clear session
        flash('Você foi desconectado', 'info')
        return redirect(url_for('index'))
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        user_id = current_user.id  # Use Flask-Login's current_user
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
            user_name=user_data.get('name'),
            latest_score=latest_score,
            burnout_history=burnout_history,
            has_completed_questionnaire=has_completed_questionnaire
        )
    
    @app.route('/questionnaire', methods=['GET', 'POST'])
    @login_required
    def questionnaire():
        if request.method == 'POST':
            user_id = current_user.id  # Use Flask-Login's current_user
            
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