{% extends "base.html" %}

{% block content %}
<div class="form-container">
    <h2>Criar Nova Conta</h2>
    <form method="POST" action="{{ url_for('register') }}">
        <div class="form-group">
            <label for="username">Nome de Usuário</label>
            <input type="text" id="username" name="username" required>
        </div>
        <div class="form-group">
            <label for="password">Senha</label>
            <input type="password" id="password" name="password" required>
        </div>
        <button type="submit" class="btn">Registrar</button>
    </form>
    <div class="extra-links">
        <p>Já tem uma conta? <a href="{{ url_for('login') }}">Faça o login</a></p>
    </div>
</div>
{% endblock %}
