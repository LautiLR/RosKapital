// ============================================
// SETTINGS: THEME + EXPERT MODE
// ============================================

// ── THEME ──
(function initTheme() {
    const saved = localStorage.getItem('roskapital_theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
})();

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('roskapital_theme', theme);
    updateThemeButtons(theme);
    
    // Actualizar TradingView widgets si existen (necesitan reload para cambiar tema)
    // Los widgets de TV no se pueden cambiar dinámicamente, solo al crear
}

function updateThemeButtons(theme) {
    document.querySelectorAll('.theme-opt').forEach(btn => {
        const val = btn.getAttribute('data-theme-val');
        if (val === theme) {
            btn.style.background = 'var(--accent-blue)';
            btn.style.color = 'white';
            btn.style.border = 'none';
        } else {
            btn.style.background = 'var(--input-bg)';
            btn.style.color = 'var(--text-secondary)';
            btn.style.border = '1px solid var(--border)';
        }
    });
}

// ── EXPERT MODE ──
function isExpertMode() {
    return localStorage.getItem('roskapital_expert') === 'true';
}

function toggleExpertMode(enabled) {
    localStorage.setItem('roskapital_expert', enabled ? 'true' : 'false');
    document.querySelectorAll('.expert-only').forEach(el => {
        el.style.display = enabled ? '' : 'none';
    });
    document.querySelectorAll('.basic-only').forEach(el => {
        el.style.display = enabled ? 'none' : '';
    });
}

// Inicializar al cargar DOM
document.addEventListener('DOMContentLoaded', () => {
    // Theme buttons
    const currentTheme = localStorage.getItem('roskapital_theme') || 'dark';
    updateThemeButtons(currentTheme);
    
    // Expert mode
    const expert = isExpertMode();
    const toggle = document.getElementById('expertModeToggle');
    if (toggle) toggle.checked = expert;
    
    // Aplicar visibilidad
    document.querySelectorAll('.expert-only').forEach(el => {
        el.style.display = expert ? '' : 'none';
    });
});