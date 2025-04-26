from datetime import datetime
from flask_login import UserMixin
from create_app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    latest_burnout_score = db.Column(db.Float, nullable=True)
    last_assessment = db.Column(db.DateTime, nullable=True)
    
    # Relação com as respostas
    responses = db.relationship('Response', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'


class Response(db.Model):
    __tablename__ = 'responses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    burnout_score = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Perguntas específicas (q1-q15)
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
    
    def __repr__(self):
        return f'<Response {self.id} - User {self.user_id}>'