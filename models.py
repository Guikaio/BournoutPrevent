from datetime import datetime
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, uid, name, email, created_at=None, latest_burnout_score=None, last_assessment=None):
        self.id = uid  # Nota: Flask-Login espera uma propriedade 'id'
        self.uid = uid
        self.name = name
        self.email = email
        self.created_at = created_at or datetime.now()
        self.latest_burnout_score = latest_burnout_score
        self.last_assessment = last_assessment
    
    @staticmethod
    def from_dict(uid, data):
        """Cria um objeto User a partir de um dicionário do Firestore"""
        return User(
            uid=uid,
            name=data.get('name'),
            email=data.get('email'),
            created_at=data.get('created_at'),
            latest_burnout_score=data.get('latest_burnout_score'),
            last_assessment=data.get('last_assessment')
        )
    
    def to_dict(self):
        """Converte o objeto User para um dicionário para salvar no Firestore"""
        return {
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at,
            'latest_burnout_score': self.latest_burnout_score,
            'last_assessment': self.last_assessment
        }
    
    def __repr__(self):
        return f'<User {self.email}>'


class Response:
    def __init__(self, user_id, burnout_score, timestamp=None, **questions):
        """
        Inicializa um objeto Response
        
        Args:
            user_id: ID do usuário que respondeu o questionário
            burnout_score: Pontuação calculada de burnout
            timestamp: Horário da resposta (se None, usa o horário atual)
            **questions: Respostas do questionário (q1, q2, etc.)
        """
        self.id = None  # Será preenchido quando salvo no Firestore
        self.user_id = user_id
        self.burnout_score = burnout_score
        self.timestamp = timestamp or datetime.now()
        self.questions = questions
    
    @staticmethod
    def from_dict(response_id, data):
        """Cria um objeto Response a partir de um dicionário do Firestore"""
        # Extrair as respostas do questionário
        questions = {}
        for key, value in data.items():
            if key.startswith('q') and key[1:].isdigit():
                questions[key] = value
        
        # Criar o objeto Response
        response = Response(
            user_id=data.get('user_id'),
            burnout_score=data.get('burnout_score'),
            timestamp=data.get('timestamp'),
            **questions
        )
        response.id = response_id
        return response
    
    def to_dict(self):
        """Converte o objeto Response para um dicionário para salvar no Firestore"""
        data = {
            'user_id': self.user_id,
            'burnout_score': self.burnout_score,
            'timestamp': self.timestamp,
        }
        # Adicionar as respostas do questionário
        data.update(self.questions)
        return data
    
    def __repr__(self):
        return f'<Response {self.id} - User {self.user_id}>'