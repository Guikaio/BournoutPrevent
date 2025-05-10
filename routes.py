import os
import logging
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime
from models import User, Response
from create_app import db

# Configura o registro de logs
logging.basicConfig(level=logging.DEBUG)

# Funções auxiliares


def calculate_burnout_score(responses):
    """
    Calcula a pontuação de burnout com base no Inventário de Burnout de Maslach (MBI) adaptado para estudantes.
    As questões são divididas nas seguintes dimensões:
    - Exaustão Emocional (EE) - Questões 5 a 9
    - Despersonalização/Ceticismo (DP) - Questões 10 a 13
    - Realização Pessoal (PA) - Questões 14 a 15 (pontuação invertida)

    Após o cálculo da pontuação nas três dimensões principais, a pontuação é ajustada com base nas questões
    de estilo de vida (Q16 a Q25). Fatores como padrões de sono, atividade física, apoio social, entre outros,
    afetam o cálculo final do burnout.

    A fórmula para calcular a pontuação final é:
    (EE + DP + (20 - PA)) / pontuação_max_total * 100
    Após a aplicação de ajustes baseados nos fatores de estilo de vida.
    """
    try:
        # Exaustão Emocional (EE) - Questões 5-9
        ee_questions = [f"q{i}" for i in range(5, 10)]
        ee_score = 0
        for q in ee_questions:
            if q in responses and responses[q].isdigit():
                ee_score += int(responses[q])

        # Despersonalização/Ceticismo (DP) - Questões 10-13
        dp_questions = [f"q{i}" for i in range(10, 14)]
        dp_score = 0
        for q in dp_questions:
            if q in responses and responses[q].isdigit():
                dp_score += int(responses[q])

        # Realização Pessoal (PA) - Questões 14-15 (pontuação invertida)
        pa_questions = [f"q{i}" for i in range(14, 16)]
        pa_score = 0
        for q in pa_questions:
            if q in responses and responses[q].isdigit():
                pa_score += int(responses[q])

        # Inverter a pontuação de PA (quanto maior PA, menor o burnout)
        max_pa_score = 4 * len(pa_questions)
        reversed_pa_score = max_pa_score - pa_score

        # Ajustes com base no estilo de vida (Q16-Q25)
        lifestyle_adjustment = 0

        # Padrões de sono (Q18) - Menos sono aumenta o risco de burnout
        if "q18" in responses:
            sleep_response = responses.get("q18")
            if sleep_response == "Menos de 5 horas":
                lifestyle_adjustment += 5
            elif sleep_response == "5-6 horas":
                lifestyle_adjustment += 2.5

        # Atividade física (Q19) - Menos atividade aumenta o risco de burnout
        if "q19" in responses:
            activity_response = responses.get("q19")
            if activity_response == "Raramente ou nunca":
                lifestyle_adjustment += 5
            elif activity_response == "1-2 vezes por semana":
                lifestyle_adjustment += 2.5

        # Apoio social (Q20) - Menos apoio aumenta o risco de burnout
        if "q20" in responses:
            support_response = responses.get("q20")
            if support_response == "Nenhum apoio":
                lifestyle_adjustment += 5
            elif support_response == "Pouco apoio":
                lifestyle_adjustment += 2.5

        # Limite de ajuste de estilo de vida
        lifestyle_adjustment = min(lifestyle_adjustment, 15)

        # Calcular pontuação total
        total_score = ee_score + dp_score + reversed_pa_score
        total_possible = 4 * (len(ee_questions) +
                              len(dp_questions) + len(pa_questions))

        # Calcular porcentagem de Burnout
        burnout_percentage = (total_score / total_possible) * 100

        # Aplicar ajuste de estilo de vida
        adjusted_score = min(100, burnout_percentage + lifestyle_adjustment)

        return round(adjusted_score, 1)
    except Exception as e:
        logging.error(f"Erro ao calcular a pontuação de burnout: {e}")
        return 50.0


def is_authenticated():
    """Verifica se o usuário está logado via sessão"""
    return 'user_id' in session


def get_user_data(user_id):
    """Recupera os dados do usuário no banco de dados"""
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
        logging.error(f"Erro ao recuperar dados do usuário: {e}")
        return None


def save_questionnaire_responses(user_id, responses, burnout_score):
    """Salva as respostas do questionário no banco de dados"""
    try:
        # Obtém o timestamp atual
        timestamp = datetime.now()

        # Obtém o usuário no banco de dados
        user = User.query.get(user_id)

        if not user:
            logging.error(
                f"Usuário não encontrado no banco de dados: {user_id}")
            return False

        # Cria uma nova resposta
        new_response = Response(
            user_id=user.id,
            burnout_score=burnout_score,
            timestamp=timestamp
        )

        # Adiciona as respostas individuais das questões
        for q, answer in responses.items():
            if hasattr(new_response, q):  # Verifica se o campo da questão existe
                # Trata as respostas numéricas (para questões de cálculo de Burnout)
                if q in [f"q{i}" for i in range(5, 16)] and answer.isdigit():
                    setattr(new_response, q, int(answer))
                # Trata as questões demográficas e de estilo de vida com valores textuais
                elif q in [f"q{i}" for i in range(1, 5)] or q in [f"q{i}" for i in range(16, 26)]:
                    # Armazena o valor 1 para indicar que a resposta foi fornecida
                    # As respostas textuais são usadas no cálculo de Burnout,
                    # mas não precisam ser armazenadas nos campos inteiros
                    setattr(new_response, q, 1)

        # Atualiza a pontuação mais recente do usuário
        user.latest_burnout_score = burnout_score
        user.last_assessment = timestamp

        # Adiciona ao banco de dados
        db.session.add(new_response)
        db.session.commit()

        return True
    except Exception as e:
        db.session.rollback()
        logging.error(f"Erro ao salvar as respostas do questionário: {e}")
        return False


def get_burnout_history(user_id):
    """Obtém o histórico de Burnout do usuário"""
    try:
        # Obtém as respostas do banco de dados
        responses = Response.query.filter_by(
            user_id=user_id).order_by(Response.timestamp).all()

        history = []
        for response in responses:
            history.append({
                'score': response.burnout_score,
                'timestamp': response.timestamp.strftime('%d/%m/%Y') if response.timestamp else 'Desconhecido'
            })

        return history
    except Exception as e:
        logging.error(f"Erro ao recuperar o histórico de burnout: {e}")
        return []


def init_app(app):
    # Configura o Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Rotas
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
                # Verifica se o usuário já existe
                existing_user = User.query.filter_by(email=email).first()
                if existing_user:
                    flash('Este e-mail já está em uso.', 'error')
                    return redirect(url_for('register'))

                # Cria o usuário no banco de dados
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
                logging.error(f"Erro no registro: {e}")
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
                # Encontra o usuário pelo e-mail
                user = User.query.filter_by(email=email).first()

                if not user or not user.check_password(password):
                    flash('Email ou senha inválidos', 'error')
                    return redirect(url_for('login'))

                # Configura a sessão
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_email'] = user.email

                # Faz login usando o Flask-Login
                login_user(user)

                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))

            except Exception as e:
                logging.error(f"Erro no login: {e}")
                flash('Ocorreu um erro durante o login. Tente novamente.', 'error')

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        logout_user()  # Logout com Flask-Login
        session.clear()  # Limpar sessão
        flash('Você foi desconectado', 'info')
        return redirect(url_for('index'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user_id = current_user.id  # Usando o current_user do Flask-Login
        user_data = get_user_data(user_id)

        if not user_data:
            flash('Erro ao carregar dados do usuário', 'error')
            return redirect(url_for('index'))

        # Obtém o histórico de Burnout
        burnout_history = get_burnout_history(user_id)

        # Obtém a última pontuação de Burnout
        latest_score = user_data.get('latest_burnout_score')

        # Verifica se o usuário completou o questionário
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
            user_id = current_user.id  # Usando o current_user do Flask-Login

            # Extrai as respostas do formulário
            responses = {key: request.form.get(
                key) for key in request.form if key.startswith('q')}

            # Calcula a pontuação de Burnout
            burnout_score = calculate_burnout_score(responses)

            # Salva as respostas no banco de dados
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

    # Tratadores de erro
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        logging.error(f"Erro no servidor: {e}")
        return render_template('index.html'), 500
