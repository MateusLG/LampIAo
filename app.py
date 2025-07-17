import os
import re
import json
import markdown
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from ia import generate_insights_and_title

load_dotenv()

db = SQLAlchemy()
mail = Mail()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

    db.init_app(app)
    mail.init_app(app)

    @app.template_filter('markdown')
    def markdown_to_html(text):
        if text:
            return markdown.markdown(text)
        return ''

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    from models import User, Note

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Usuário ou senha inválidos.', 'danger')
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
            if not password_pattern.match(password):
                flash(
                    'A senha deve ter no mínimo 8 caracteres, uma letra maiúscula, '
                    'uma minúscula, um número e um caractere especial (@$!%*?&).', 
                    'danger'
                )
                return redirect(url_for('register'))

            user_exists = User.query.filter((User.username == username) | (User.email == email)).first()
            if user_exists:
                flash('Nome de usuário ou e-mail já cadastrado.', 'warning')
                return redirect(url_for('register'))
                
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, email=email, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()
            flash('Conta criada com sucesso! Por favor, faça o login.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Você foi desconectado com sucesso.', 'info')
        return redirect(url_for('login'))

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()
            if user:
                token = s.dumps(email, salt='password-reset-salt')
                reset_url = url_for('reset_with_token', token=token, _external=True)
                msg = Message('Redefinição de Senha - LampIAo', recipients=[email])
                msg.body = f'Para redefinir sua senha, clique no link a seguir: {reset_url}'
                mail.send(msg)
                flash('Um e-mail com instruções foi enviado.', 'info')
                return redirect(url_for('login'))
            else:
                flash('Este e-mail não foi encontrado.', 'warning')
        return render_template('forgot_password.html')

    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_with_token(token):
        try:
            email = s.loads(token, salt='password-reset-salt', max_age=3600)
        except (SignatureExpired, Exception):
            flash('O link de redefinição de senha é inválido ou expirou.', 'danger')
            return redirect(url_for('forgot_password'))

        if request.method == 'POST':
            password = request.form.get('password')
            password2 = request.form.get('password2')
            if password != password2:
                flash('As senhas não coincidem. Tente novamente.', 'danger')
                return render_template('reset_password.html', token=token)
            
            password_pattern = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
            if not password_pattern.match(password):
                flash(
                    'A nova senha não atende aos requisitos de segurança. '
                    'Ela deve ter no mínimo 8 caracteres, uma letra maiúscula, '
                    'uma minúscula, um número e um caractere especial (@$!%*?&).', 
                    'danger'
                )
                return render_template('reset_password.html', token=token)

            user = User.query.filter_by(email=email).first()
            if user:
                user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
                db.session.commit()
                flash('Sua senha foi atualizada com sucesso!', 'success')
                return redirect(url_for('login'))
        return render_template('reset_password.html', token=token)

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user_notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.created_at.desc()).all()
        return render_template('dashboard.html', notes=user_notes)

    @app.route('/add_note', methods=['POST'])
    @login_required
    def add_note():
        content = request.form.get('content')
        if not content:
            flash('O campo de ideias não pode estar vazio.', 'warning')
            return redirect(url_for('dashboard'))

        ai_result = generate_insights_and_title(content)

        if 'error' in ai_result:
            flash(f"Não foi possível processar a ideia com a IA: {ai_result['error']}", 'danger')
            return redirect(url_for('dashboard'))

        new_note = Note(
            title=ai_result.get('title', 'Ideia Sem Título'),
            original_content=content,
            ai_suggestions=ai_result.get('insights_markdown', ''),
            user_id=current_user.id
        )
        db.session.add(new_note)
        db.session.commit()
        
        flash('Nova ideia e insights gerados com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    @app.route('/delete_note/<int:note_id>', methods=['POST'])
    @login_required
    def delete_note(note_id):
        note_to_delete = Note.query.get_or_404(note_id)
        if note_to_delete.user_id != current_user.id:
            flash('Você não tem permissão para apagar esta ideia.', 'danger')
            return redirect(url_for('dashboard'))
        db.session.delete(note_to_delete)
        db.session.commit()
        flash('Ideia apagada.', 'info')
        return redirect(url_for('dashboard'))

    @app.route('/note/<int:note_id>')
    @login_required
    def note_page(note_id):
        note = Note.query.get_or_404(note_id)
        if note.user_id != current_user.id:
            flash('Acesso não permitido.', 'danger')
            return redirect(url_for('dashboard'))
        return render_template('nota.html', note=note)

    with app.app_context():
        db.create_all()

    return app