import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

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

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login' 

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route('/')
    def index():
        # Agora a página inicial leva para o login
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Se o usuário já está logado, vai direto para o dashboard
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()

            # Verifica se o usuário existe e se a senha (comparando o hash) está correta
            if user and check_password_hash(user.password_hash, password):
                login_user(user) # Função do Flask-Login que gerencia a sessão
                return redirect(url_for('dashboard'))
            else:
                flash('Usuário ou senha inválidos. Tente novamente.', 'danger')
        
        return render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')

            email_exists = User.query.filter_by(email=email).first()
            if email_exists:
                flash('Este e-mail já está em uso.', 'warning')
                return redirect(url_for('register'))
            
            username_exists = User.query.filter_by(username=username).first()
            if username_exists:
                flash('Este nome de usuário já está em uso.', 'warning')
                return redirect(url_for('register'))

            password_hash = generate_password_hash(password, method='pbkdf2:sha256')

            new_user = User(username=username, email=email, password_hash=password_hash)

            db.session.add(new_user)
            db.session.commit()

            flash('Conta criada com sucesso! Por favor, faça o login.', 'success')
            return redirect(url_for('login')) 

        return render_template('register.html')
    
    @app.route('/dashboard')

    @login_required  # Este decorador protege a rota. Só usuários logados podem acessar.
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user() # Função do Flask-Login que encerra a sessão
        flash('Você foi desconectado com sucesso.', 'info')
        return redirect(url_for('login'))

    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    @app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            email = request.form.get('email')
            user = User.query.filter_by(email=email).first()

            if user:
                # Gera um token com o email do usuário
                token = s.dumps(email, salt='password-reset-salt')
                # Cria o link de redefinição
                reset_url = url_for('reset_with_token', token=token, _external=True)
                
                # Cria e envia o e-mail
                msg = Message('Redefinição de Senha - LampIAo', recipients=[email])
                msg.body = f'Para redefinir sua senha, clique no link a seguir: {reset_url}'
                mail.send(msg)

                flash('Um e-mail com instruções para redefinir sua senha foi enviado.', 'info')
                return redirect(url_for('login'))
            else:
                flash('Este e-mail não foi encontrado em nosso sistema.', 'warning')
        
        return render_template('forgot_password.html')

    @app.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_with_token(token):
        try:
            # Valida o token e seu tempo de expiração (1 hora = 3600 seg)
            email = s.loads(token, salt='password-reset-salt', max_age=3600)
        except SignatureExpired:
            flash('O link de redefinição de senha expirou.', 'danger')
            return redirect(url_for('forgot_password'))
        except Exception:
            flash('O link de redefinição de senha é inválido.', 'danger')
            return redirect(url_for('forgot_password'))

        if request.method == 'POST':
            password = request.form.get('password')
            user = User.query.filter_by(email=email).first()
            
            if user:
                # Atualiza a senha do usuário com o novo hash
                user.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
                db.session.commit()
                flash('Sua senha foi atualizada com sucesso!', 'success')
                return redirect(url_for('login'))

        return render_template('reset_password.html', token=token)

    with app.app_context():
        db.create_all()

    return app