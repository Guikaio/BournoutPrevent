import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore, auth
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "burnout-prevention-secret-key")

# Initialize Firebase
try:
    # Use service account if available in environment
    cred_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # Use application default credentials if service account not provided
        cred = credentials.ApplicationDefault()
    
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logging.info("Firebase initialized successfully")
except Exception as e:
    logging.error(f"Error initializing Firebase: {e}")
    db = None

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
    """Check if user is logged in"""
    return 'user_id' in session

def get_user_data(user_id):
    """Retrieve user data from Firestore"""
    if not db:
        return None
    
    user_ref = db.collection('users').document(user_id)
    return user_ref.get().to_dict()

def save_questionnaire_responses(user_id, responses, burnout_score):
    """Save questionnaire responses to Firestore"""
    if not db:
        return False
    
    try:
        # Get timestamp
        timestamp = datetime.now()
        
        # Add to responses collection
        response_data = {
            'user_id': user_id,
            'responses': responses,
            'burnout_score': burnout_score,
            'timestamp': timestamp
        }
        
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
    if not db:
        return []
    
    try:
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
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        
        if not email or not password or not name:
            flash('Por favor, preencha todos os campos', 'error')
            return redirect(url_for('register'))
        
        try:
            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                display_name=name
            )
            
            # Store additional user info in Firestore
            db.collection('users').document(user.uid).set({
                'name': name,
                'email': email,
                'created_at': firestore.SERVER_TIMESTAMP,
                'latest_burnout_score': None,
                'last_assessment': None
            })
            
            flash('Conta criada com sucesso! Por favor, faça login.', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
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
            # Sign in user with Firebase Auth
            user = auth.get_user_by_email(email)
            
            # Note: We can't verify password here as Firebase Auth handles this
            # This is a simplified login flow for demonstration
            # In a real app, you would use Firebase client SDK for authentication
            
            # Set user session
            session['user_id'] = user.uid
            session['user_name'] = user.display_name
            session['user_email'] = user.email
            
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            logging.error(f"Login error: {e}")
            flash('Email ou senha inválidos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not is_authenticated():
        flash('Por favor, faça login para acessar o dashboard', 'warning')
        return redirect(url_for('login'))
    
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
def questionnaire():
    if not is_authenticated():
        flash('Por favor, faça login para acessar o questionário', 'warning')
        return redirect(url_for('login'))
    
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
def tips():
    if not is_authenticated():
        flash('Por favor, faça login para acessar as dicas', 'warning')
        return redirect(url_for('login'))
    
    return render_template('tips.html')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    logging.error(f"Server error: {e}")
    return render_template('index.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
