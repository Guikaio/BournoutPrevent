# Importações necessárias
import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from models import User, Response
from create_app import db

# Configura o nível de log para DEBUG
logging.basicConfig(level=logging.DEBUG)

# ------------------ Funções auxiliares ------------------


def calculate_burnout_score(responses):
    """
    Calcula a pontuação de burnout com base em respostas do questionário (modelo MBI).
    Ajusta a pontuação com base em estilo de vida (sono, atividade física, apoio social).
    """
    try:
        # Questões de Exaustão Emocional (5-9)
        ee_questions = [f"q{i}" for i in range(5, 10)]
        ee_score = sum(int(
            responses[q]) for q in ee_questions if q in responses and responses[q].isdigit())

        # Questões de Despersonalização (10-13)
        dp_questions = [f"q{i}" for i in range(10, 14)]
        dp_score = sum(int(
            responses[q]) for q in dp_questions if q in responses and responses[q].isdigit())

        # Questões de Realização Pessoal (14-15) - reversas
        pa_questions = [f"q{i}" for i in range(14, 16)]
        pa_score = sum(int(
            responses[q]) for q in pa_questions if q in responses and responses[q].isdigit())
        reversed_pa_score = 4 * len(pa_questions) - pa_score  # Inversão

        # Cálculo da pontuação base
        total_score = ee_score + dp_score + reversed_pa_score
        max_possible = 4 * (len(ee_questions) +
                            len(dp_questions) + len(pa_questions))
        burnout_percentage = (total_score / max_possible) * 100

        # Ajustes de estilo de vida
        lifestyle_adjustment = 0
        if responses.get("q18") == "Menos de 5 horas":
            lifestyle_adjustment += 5
        elif responses.get("q18") == "5-6 horas":
            lifestyle_adjustment += 2.5
        if responses.get("q19") == "Raramente ou nunca":
            lifestyle_adjustment += 5
        elif responses.get("q19") == "1-2 vezes por semana":
            lifestyle_adjustment += 2.5
        if responses.get("q20") == "Nenhum apoio":
            lifestyle_adjustment += 5
        elif responses.get("q20") == "Pouco apoio":
            lifestyle_adjustment += 2.5

        adjusted_score = min(100, burnout_percentage +
                             min(lifestyle_adjustment, 15))
        return round(adjusted_score, 1)
    except Exception as e:
        logging.error(f"Erro ao calcular burnout: {e}")
        return 50.0  # valor padrão em caso de falha


def is_authenticated():
    """Verifica se o usuário está logado na sessão"""
    return 'user_id' in session


def get_user_data(user_id):
    """Retorna os dados básicos do usuário a partir do ID"""
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
        logging.error(f"Erro ao buscar usuário: {e}")
        return None


def save_questionnaire_responses(user_id, responses, burnout_score):
    """Salva as respostas do questionário no banco de dados"""
    try:
        user = User.query.get(user_id)
        if not user:
            logging.error(f"Usuário não encontrado: {user_id}")
            return False

        new_response = Response(
            user_id=user.id, burnout_score=burnout_score, timestamp=datetime.now())

        # Preenchimento das respostas
        for q, answer in responses.items():
            if hasattr(new_response, q):
                if q in [f"q{i}" for i in range(5, 16)] and answer.isdigit():
                    setattr(new_response, q, int(answer))
                elif q in [f"q{i}" for i in range(1, 5)] + [f"q{i}" for i in range(16, 26)]:
                    setattr(new_response, q, 1)

        user.latest_burnout_score = burnout_score
        user.last_assessment = datetime.now()

        db.session.add(new_response)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao salvar respostas: {e}")
        return False


def get_burnout_history(user_id):
    """Retorna o histórico de avaliações do usuário"""
    try:
        responses = Response.query.filter_by(
            user_id=user_id).order_by(Response.timestamp).all()
        return [{'score': r.burnout_score, 'timestamp': r.timestamp.strftime('%d/%m/%Y')} for r in responses]
    except Exception as e:
        logging.error(f"Erro ao buscar histórico: {e}")
        return []

# ------------------ Inicialização da aplicação ------------------


def init_app(app):
    # Configura o Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ------------------ Rotas ------------------

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
                if User.query.filter_by(email=email).first():
                    flash('Este e-mail já está em uso.', 'error')
                    return redirect(url_for('register'))

                user = User(name=name, email=email, created_at=datetime.now())
                user.set_password(password)

                db.session.add(user)
                db.session.commit()
                flash('Conta criada com sucesso! Faça login.', 'success')
                return redirect(url_for('login'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Erro no registro: {e}")
                flash('Erro ao criar conta.', 'error')
        return render_template('register.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if is_authenticated():
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            if not email or not password:
                flash('Preencha todos os campos', 'error')
                return redirect(url_for('login'))

            try:
                user = User.query.filter_by(email=email).first()
                if not user or not user.check_password(password):
                    flash('Email ou senha inválidos', 'error')
                    return redirect(url_for('login'))

                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_email'] = user.email

                login_user(user)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
            except Exception as e:
                logging.error(f"Erro no login: {e}")
                flash('Erro durante o login.', 'error')
        return render_template('login.html')

    @app.route('/logout')
    def logout():
        logout_user()
        session.clear()
        flash('Você foi desconectado', 'info')
        return redirect(url_for('index'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user_id = current_user.id
        user_data = get_user_data(user_id)
        if not user_data:
            flash('Erro ao carregar dados.', 'error')
            return redirect(url_for('index'))

        burnout_history = get_burnout_history(user_id)
        latest_score = user_data.get('latest_burnout_score')
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
            user_id = current_user.id
            responses = {k: request.form.get(
                k) for k in request.form if k.startswith('q')}
            score = calculate_burnout_score(responses)
            if save_questionnaire_responses(user_id, responses, score):
                flash('Respostas salvas com sucesso!', 'success')
            else:
                flash('Erro ao salvar respostas.', 'error')
            return redirect(url_for('dashboard'))
        return render_template('questionnaire.html')

    @app.route('/tips')
    @login_required
    def tips():
        return render_template('tips.html')

    # ------------------ Tratamento de erros ------------------

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        logging.error(f"Erro interno: {e}")
        return render_template('index.html'), 500
