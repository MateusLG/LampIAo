import os
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ia import generate_insights_and_title
import markdown

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
        # Esta função é usada pelo Flask-Login para recarregar o objeto do usuário a partir do ID do usuário armazenado na sessão.
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
        # A página principal agora é o dashboard com a caixa de texto
        return render_template('dashboard.html', notes=user_notes)

    # SUBSTITUA a sua rota /add_note por esta nova versão:
    @app.route('/add_note', methods=['POST'])
    @login_required
    def add_note():
        content = request.form.get('content')

        if not content:
            flash('O campo de ideias não pode estar vazio.', 'warning')
            return redirect(url_for('dashboard'))

        # Chama a nossa nova função de IA
        ai_result = generate_insights_and_title(content)

        # Verifica se a IA retornou um erro
        if 'error' in ai_result:
            flash(f"Não foi possível processar a ideia com a IA: {ai_result['error']}", 'danger')
            return redirect(url_for('dashboard'))

        # Cria a nova nota com os dados gerados pela IA
        new_note = Note(
            title=ai_result.get('title', 'Faísca Sem Título'), # Pega o título ou usa um padrão
            original_content=content,
            ai_suggestions=ai_result.get('insights_markdown', ''), # Pega os insights
            user_id=current_user.id
        )
        db.session.add(new_note)
        db.session.commit()
        
        flash('Nova faísca e insights gerados com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    
    @app.route('/delete_note/<int:note_id>', methods=['POST'])
    @login_required
    def delete_note(note_id):
        note_to_delete = Note.query.get_or_404(note_id)

        if note_to_delete.user_id != current_user.id:
            flash('Você não tem permissão para apagar esta nota.', 'danger')
            return redirect(url_for('dashboard'))

        db.session.delete(note_to_delete)
        db.session.commit()
        flash('Faísca apagada.', 'info')
        
        return redirect(url_for('dashboard'))

    @app.route('/note/<int:note_id>')
    @login_required
    def note_page(note_id):
        # Busca a nota pelo ID ou retorna um erro 404 se não encontrar
        note = Note.query.get_or_404(note_id)

        # Garante que o usuário só pode ver as próprias notas
        if note.user_id != current_user.id:
            flash('Acesso não permitido.', 'danger')
            return redirect(url_for('dashboard'))
            
        # Renderiza a página de detalhes, passando o objeto da nota
        return render_template('nota.html', note=note)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('login'))

    return app
