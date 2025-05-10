from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from create_app import db

class User(db.Model, UserMixin):
    """Modelo de usuário para o sistema"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    latest_burnout_score = db.Column(db.Float, nullable=True)
    last_assessment = db.Column(db.DateTime, nullable=True)
    
    # Relação com as respostas do questionário
    responses = db.relationship('Response', backref='user', lazy=True)
    
    def set_password(self, password):
        """Define a senha criptografada do usuário"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

class Response(db.Model):
    """Modelo para as respostas do questionário de burnout"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    burnout_score = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    # Respostas do questionário (25 questões)
    q1 = db.Column(db.Integer, nullable=True)
    q2 = db.Column(db.Integer, nullable=True)
    q3 = db.Column(db.Integer, nullable=True)
    q4 = db.Column(db.Integer, nullable=True)
    q5 = db.Column(db.Integer, nullable=True)
    q6 = db.Column(db.Integer, nullable=True)
    q7 = db.Column(db.Integer, nullable=True)
    q8 = db.Column(db.Integer, nullable=True)
    q9 = db.Column(db.Integer, nullable=True)
    q10 = db.Column(db.Integer, nullable=True)
    q11 = db.Column(db.Integer, nullable=True)
    q12 = db.Column(db.Integer, nullable=True)
    q13 = db.Column(db.Integer, nullable=True)
    q14 = db.Column(db.Integer, nullable=True)
    q15 = db.Column(db.Integer, nullable=True)
    q16 = db.Column(db.Integer, nullable=True)
    q17 = db.Column(db.Integer, nullable=True)
    q18 = db.Column(db.Integer, nullable=True)
    q19 = db.Column(db.Integer, nullable=True)
    q20 = db.Column(db.Integer, nullable=True)
    q21 = db.Column(db.Integer, nullable=True)
    q22 = db.Column(db.Integer, nullable=True)
    q23 = db.Column(db.Integer, nullable=True)
    q24 = db.Column(db.Integer, nullable=True)
    q25 = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f'<Response {self.id} - User {self.user_id}>'