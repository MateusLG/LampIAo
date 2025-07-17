document.addEventListener('DOMContentLoaded', () => {

    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const body = document.body;

    // Função que aplica o tema visualmente
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            body.classList.add('dark-theme');
            themeToggleBtn.innerHTML = '☀️'; // Ícone de sol
        } else {
            body.classList.remove('dark-theme');
            themeToggleBtn.innerHTML = '🌙'; // Ícone de lua
        }
    };

    // Função que é chamada ao clicar no botão
    const toggleTheme = () => {
        // Verifica se o tema atual é escuro para decidir para qual trocar
        const isDarkMode = body.classList.contains('dark-theme');
        const newTheme = isDarkMode ? 'light' : 'dark';
        
        localStorage.setItem('theme', newTheme); // Salva a nova escolha
        applyTheme(newTheme); // Aplica a nova escolha
    };

    // No carregamento da página, aplica o tema que estiver salvo
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    }

    // Adiciona o evento de clique ao botão
    themeToggleBtn.addEventListener('click', toggleTheme);

});