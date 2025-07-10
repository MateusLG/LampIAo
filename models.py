from app import db # Importamos o objeto 'db' que criamos no app.py
from flask_login import UserMixin # Ferramenta do Flask-Login para gerenciar usuários
from datetime import datetime

# O UserMixin adiciona funcionalidades padrão de login ao nosso modelo de Usuário
class User(UserMixin, db.Model):
    __tablename__ = 'user' # Nome da tabela no banco de dados

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False) # NUNCA guarde senhas em texto plano!

    # Relacionamento: Um usuário pode ter muitas notas.
    # O 'backref' cria um atributo 'user' em cada Nota, para sabermos quem é o dono.
    # O 'lazy=True' significa que o SQLAlchemy carregará os dados conforme necessário.
    notes = db.relationship('Note', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'


class Note(db.Model):
    __tablename__ = 'note' # Nome da tabela no banco de dados

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    original_content = db.Column(db.Text, nullable=False)
    ai_suggestions = db.Column(db.Text, nullable=True) # Pode ser nulo, pois começa vazio
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Chave Estrangeira: vincula esta nota a um usuário.
    # 'user.id' refere-se à tabela 'user' e sua coluna 'id'.
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'<Note {self.title}>'