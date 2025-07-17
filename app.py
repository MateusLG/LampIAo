import os
import json
import markdown
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ia import generate_insights_and_title

load_dotenv()

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    @app.template_filter('markdown')
    def markdown_to_html(text):
        return markdown.markdown(text)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    from models import User, Note

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route('/')
    def index():
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
                flash('Usuário ou senha inválidos. Tente novamente.', 'danger')

        return render_template('login.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Você foi desconectado com sucesso.', 'info')
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user_exists = User.query.filter_by(username=username).first()
            if user_exists:
                flash('Este nome de usuário já está em uso. Por favor, escolha outro.', 'warning')
                return redirect(url_for('register'))

            new_user = User(
                username=username,
                password_hash=generate_password_hash(password, method='pbkdf2:sha256')
            )
            db.session.add(new_user)
            db.session.commit()

            flash('Conta criada com sucesso! Faça o login.', 'success')
            return redirect(url_for('login'))

        return render_template('register.html')
    
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

    return app