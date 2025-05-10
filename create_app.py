import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Configurar o logging
logging.basicConfig(level=logging.DEBUG)

# Inicializar o SQLAlchemy
db = SQLAlchemy()


def create_app():
    # Criar a aplicação Flask
    app = Flask(__name__)

    # Configurar a aplicação
    app.secret_key = os.environ.get(
        "SESSION_SECRET", "burnout-prevention-secret-key")

    # Configurar o banco de dados - usando SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///burnout_prevention.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Inicializar o banco de dados com a aplicação
    db.init_app(app)

    # Criar as tabelas dentro do contexto da aplicação
    with app.app_context():
        from models import User, Response
        db.create_all()

    # Importar e registrar os blueprints/rotas
    from routes import init_app
    init_app(app)

    return app
