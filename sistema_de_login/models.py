from app import db
from flask_login import UserMixin

# UserMixin é uma classe do Flask-Login que já inclui
# as propriedades e métodos padrão para um modelo de usuário
# (is_authenticated, is_active, is_anonymous, get_id()).
class User(UserMixin, db.Model):
    """Modelo para a tabela de usuários no banco de dados."""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'
