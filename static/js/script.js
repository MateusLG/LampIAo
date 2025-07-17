document.addEventListener('DOMContentLoaded', () => {

    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const body = document.body;

    const applyTheme = (theme) => {
        if (theme === 'dark') {
            body.classList.add('dark-theme');
            themeToggleBtn.innerHTML = '☀️';
        } else {
            body.classList.remove('dark-theme');
            themeToggleBtn.innerHTML = '🌙';
        }
    };

    const toggleTheme = () => {
        const isDarkMode = body.classList.contains('dark-theme');
        const newTheme = isDarkMode ? 'light' : 'dark';
        
        localStorage.setItem('theme', newTheme);
        applyTheme(newTheme);
    };

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    }

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }

});