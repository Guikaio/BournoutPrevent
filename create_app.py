import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configura o sistema de logging para exibir mensagens de debug no console
logging.basicConfig(level=logging.DEBUG)

# Inicializa o objeto do SQLAlchemy (ORM que será usado para manipular o banco de dados)
db = SQLAlchemy()


def create_app():
    # Cria a instância do aplicativo Flask
    app = Flask(__name__)

    # Define a chave secreta da aplicação (usada para sessões e cookies)
    # Se não estiver definida em variável de ambiente, usa uma chave padrão
    app.secret_key = os.environ.get(
        "SESSION_SECRET", "burnout-prevention-secret-key")

    # Configuração do banco de dados SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///burnout_prevention.db"
    # Desativa o rastreamento de modificações (economiza recursos)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Vincula o SQLAlchemy ao aplicativo Flask
    db.init_app(app)

    # Cria as tabelas do banco de dados dentro do contexto da aplicação
    with app.app_context():
        from models import User, Response  # Importa os modelos definidos
        db.create_all()  # Cria as tabelas no banco (se ainda não existirem)

    # Importa e registra as rotas (blueprints) da aplicação
    from routes import init_app
    init_app(app)  # Registra todas as rotas configuradas no módulo routes

    # Retorna a aplicação configurada
    return app
