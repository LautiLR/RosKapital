// ============================================
// AUTH CLIENT — Login/Register/Session
// ============================================

const AUTH_TOKEN_KEY = 'roskapital_token';
const AUTH_REFRESH_KEY = 'roskapital_refresh';
const AUTH_USER_KEY = 'roskapital_user';

// ── Estado de sesión ──
function getToken() {
    return localStorage.getItem(AUTH_TOKEN_KEY);
}

function getUser() {
    const u = localStorage.getItem(AUTH_USER_KEY);
    return u ? JSON.parse(u) : null;
}

function isLoggedIn() {
    return !!getToken();
}

function saveSession(data, user) {
    localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
    localStorage.setItem(AUTH_REFRESH_KEY, data.refresh_token);
    if (user) localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

function clearSession() {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_REFRESH_KEY);
    localStorage.removeItem(AUTH_USER_KEY);
}

// ── API calls ──
async function authFetch(url, options = {}) {
    const token = getToken();
    if (token) {
        options.headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
    }
    
    let res = await fetch(url, options);
    
    // Si da 401, intentar refresh
    if (res.status === 401 && token) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            options.headers['Authorization'] = `Bearer ${getToken()}`;
            res = await fetch(url, options);
        } else {
            updateNavbarAuth();
        }
    }
    
    return res;
}

async function loginUser(email, password) {
    const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Error al iniciar sesión');
    }

    const tokens = await res.json();

    // Obtener info del usuario
    const userRes = await fetch('/api/auth/me', {
        headers: { 'Authorization': `Bearer ${tokens.access_token}` }
    });

    const user = userRes.ok ? await userRes.json() : null;
    saveSession(tokens, user);

    // Migrar datos de localStorage
    await migrateLocalData(tokens.access_token);

    // Recargar para sincronizar datos de DB
    location.reload();

    return user;
}

async function registerUser(email, username, password, fullName) {
    const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, username, password, full_name: fullName || null })
    });

    const data = await res.json();

    if (!res.ok) {
        throw new Error(data.detail || 'Error al registrar');
    }

    return data;
}

function logoutUser() {
    clearSession();
    localStorage.removeItem('fintech_sim_portfolio');
    localStorage.removeItem('fintech_trade_history');
    localStorage.removeItem('fintech_watchlist');
    localStorage.removeItem('roskapital_alertas');
    localStorage.removeItem('fintech_capital');
    localStorage.removeItem('fintech_equity_history');
    localStorage.removeItem('misiones_completadas');
    localStorage.removeItem('perfil_inversor');
    localStorage.removeItem('roskapital_perfil_portfolio');
    updateNavbarAuth();
    location.reload();
}

// ── Migración de localStorage a DB ──
async function migrateLocalData(token) {
    try {
        const portfolio = JSON.parse(localStorage.getItem('fintech_sim_portfolio') || '[]');
        const watchlist = JSON.parse(localStorage.getItem('fintech_watchlist') || '[]');
        const alertas = JSON.parse(localStorage.getItem('roskapital_alertas') || '[]');
        const misiones = JSON.parse(localStorage.getItem('misiones_completadas') || '[]');
        const perfil = JSON.parse(localStorage.getItem('perfil_inversor') || 'null');
        const capital = parseFloat(localStorage.getItem('fintech_capital') || '100000');
        const trade_history = JSON.parse(localStorage.getItem('fintech_trade_history') || '[]');

        // Solo migrar si hay datos
        if (portfolio.length === 0 && watchlist.length === 0 && alertas.length === 0 &&
            misiones.length === 0 && !perfil && trade_history.length === 0) {
            return;
        }

        await fetch('/api/auth/migrate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                portfolio,
                watchlist,
                alertas,
                misiones,
                perfil_inversor: perfil,
                capital,
                trade_history
            })
        });

        console.log('Datos migrados a la cuenta');
    } catch (e) {
        console.warn('Error migrando datos:', e);
    }
}

// ── UI del modal ──
function abrirAuthModal(tab = 'login') {
    const modal = new bootstrap.Modal(document.getElementById('modalAuth'));
    switchAuthTab(tab);
    document.getElementById('authError').style.display = 'none';
    modal.show();
}

function switchAuthTab(tab) {
    const loginTab = document.getElementById('authTabLogin');
    const registerTab = document.getElementById('authTabRegister');
    const loginForm = document.getElementById('authLoginForm');
    const registerForm = document.getElementById('authRegisterForm');
    const errorEl = document.getElementById('authError');
    
    if (errorEl) errorEl.style.display = 'none';
    
    if (tab === 'login') {
        if (loginTab) { loginTab.style.color = 'var(--text-primary)'; loginTab.style.borderBottom = '2px solid var(--accent-blue)'; loginTab.style.fontWeight = '700'; }
        if (registerTab) { registerTab.style.color = 'var(--text-secondary)'; registerTab.style.borderBottom = '2px solid transparent'; registerTab.style.fontWeight = '600'; }
        if (loginForm) loginForm.style.display = 'block';
        if (registerForm) registerForm.style.display = 'none';
    } else {
        if (registerTab) { registerTab.style.color = 'var(--text-primary)'; registerTab.style.borderBottom = '2px solid var(--accent-blue)'; registerTab.style.fontWeight = '700'; }
        if (loginTab) { loginTab.style.color = 'var(--text-secondary)'; loginTab.style.borderBottom = '2px solid transparent'; loginTab.style.fontWeight = '600'; }
        if (registerForm) registerForm.style.display = 'block';
        if (loginForm) loginForm.style.display = 'none';
    }
}

async function handleLogin() {
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('authError');
    const btn = document.getElementById('loginBtn');

    if (!email || !password) {
        errorEl.textContent = 'Completá todos los campos';
        errorEl.style.display = 'block';
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Ingresando...';

    try {
        const user = await loginUser(email, password);
        try { bootstrap.Modal.getInstance(document.getElementById('modalAuth')).hide(); } catch(e) {}
        location.reload();
    } catch (e) {
        errorEl.textContent = e.message;
        errorEl.style.display = 'block';
        btn.disabled = false;
        btn.innerHTML = 'Iniciar Sesión';
    }
}

async function handleRegister() {
    const email = document.getElementById('registerEmail').value.trim();
    const username = document.getElementById('registerUsername').value.trim();
    const password = document.getElementById('registerPassword').value;
    const password2 = document.getElementById('registerPassword2').value;
    const fullName = document.getElementById('registerName').value.trim();
    const errorEl = document.getElementById('authError');
    const btn = document.getElementById('registerBtn');

    errorEl.style.display = 'none';

    if (!email || !username || !password) {
        errorEl.textContent = 'Completá todos los campos obligatorios';
        errorEl.style.display = 'block';
        return;
    }

    if (password !== password2) {
        errorEl.textContent = 'Las contraseñas no coinciden';
        errorEl.style.display = 'block';
        return;
    }

    if (password.length < 8) {
        errorEl.textContent = 'La contraseña debe tener al menos 8 caracteres';
        errorEl.style.display = 'block';
        return;
    }

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creando cuenta...';

    try {
        await registerUser(email, username, password, fullName);
        showVerificationStep(email);
    } catch (e) {
        errorEl.textContent = e.message;
        errorEl.style.display = 'block';
    } finally {
        btn.disabled = false;
        btn.innerHTML = 'Crear Cuenta';
    }
}

// ── Navbar update ──
function updateNavbarAuth() {
    const authBtns = document.getElementById('authNavButtons');
    const userInfo = document.getElementById('userNavInfo');

    if (!authBtns || !userInfo) return;

    if (isLoggedIn()) {
        const user = getUser();
        authBtns.style.display = 'none';
        userInfo.style.display = 'flex';
        userInfo.innerHTML = `
            <span style="font-size:0.82rem; color:var(--text-secondary);">
                👤 ${user?.username || user?.email || 'Usuario'}
            </span>
            <button class="btn btn-outline-secondary rounded-pill px-3 btn-sm" onclick="logoutUser()" title="Cerrar sesión">
                <i class="bi bi-box-arrow-right"></i>
            </button>
        `;
    } else {
        authBtns.style.display = 'flex';
        userInfo.style.display = 'none';
    }
}

// Inicializar al cargar
document.addEventListener('DOMContentLoaded', updateNavbarAuth);

function showVerificationStep(email) {
    const modalBody = document.querySelector('#modalAuth .modal-body');
    modalBody.innerHTML = `
        <div class="text-center mb-3">
            <div style="font-size:3rem;">📧</div>
            <h6 class="fw-bold mt-2">Verificá tu email</h6>
            <p class="small" style="color:var(--text-secondary);">Enviamos un código de 6 dígitos a <strong style="color:var(--text-primary);">${email}</strong></p>
        </div>
        <div id="verifyError" style="display:none; background:rgba(255,71,87,0.1); border:1px solid rgba(255,71,87,0.2); color:var(--negative); padding:0.6rem 1rem; border-radius:10px; font-size:0.85rem; margin-bottom:1rem;"></div>
        <div class="mb-3">
            <input type="text" class="form-control text-center fw-bold" id="verifyCode" maxlength="6" placeholder="000000"
                style="background:var(--input-bg); border:1px solid var(--border); color:var(--text-primary); font-size:1.5rem; letter-spacing:0.5rem; border-radius:10px; padding:0.7rem;"
                onkeydown="if(event.key==='Enter') doVerify('${email}')">
        </div>
        <button class="btn w-100 fw-bold" onclick="doVerify('${email}')"
            style="background:linear-gradient(135deg, var(--accent-blue), #2855cc); color:white; border:none; border-radius:10px; padding:0.75rem;">
            Verificar
        </button>
        <div class="text-center mt-3">
            <a href="#" class="small" style="color:var(--text-secondary); text-decoration:none;" 
                onclick="doResendCode('${email}'); return false;">¿No recibiste el código? Reenviar</a>
        </div>
    `;
}

async function doVerify(email) {
    const code = document.getElementById('verifyCode').value.trim();
    const errorEl = document.getElementById('verifyError');

    errorEl.style.display = 'none';

    if (code.length !== 6) {
        errorEl.textContent = 'Ingresá el código de 6 dígitos';
        errorEl.style.display = 'block';
        return;
    }

    try {
        const res = await fetch('/api/auth/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, code })
        });

        const data = await res.json();

        if (!res.ok) {
            errorEl.textContent = data.detail || 'Código inválido';
            errorEl.style.display = 'block';
            return;
        }

        // Obtener info del usuario
        const userRes = await fetch('/api/auth/me', {
            headers: { 'Authorization': `Bearer ${data.access_token}` }
        });
        const user = await userRes.json();

        saveSession(data, user);
        try { await migrateLocalData(data.access_token); } catch (e) { console.warn('Migración:', e); }

        // Cerrar modal y recargar
        try { bootstrap.Modal.getInstance(document.getElementById('modalAuth')).hide(); } catch (e) { }
        location.reload();

    } catch (err) {
        errorEl.textContent = 'Error de conexión';
        errorEl.style.display = 'block';
    }
}

async function doResendCode(email) {
    try {
        const res = await fetch(`/api/auth/resend-code?email=${encodeURIComponent(email)}`, { method: 'POST' });
        if (res.ok) {
            alert('Código reenviado. Revisá tu email.');
        } else {
            const data = await res.json();
            alert(data.detail || 'Error al reenviar');
        }
    } catch (err) {
        alert('Error de conexión');
    }
}

async function refreshAccessToken() {
    const refreshToken = localStorage.getItem(AUTH_REFRESH_KEY);
    if (!refreshToken) {
        clearSession();
        return false;
    }
    
    try {
        const res = await fetch(`/api/auth/refresh?refresh_token=${encodeURIComponent(refreshToken)}`, {
            method: 'POST'
        });
        
        if (!res.ok) {
            clearSession();
            return false;
        }
        
        const data = await res.json();
        localStorage.setItem(AUTH_TOKEN_KEY, data.access_token);
        localStorage.setItem(AUTH_REFRESH_KEY, data.refresh_token);
        return true;
    } catch (err) {
        clearSession();
        return false;
    }
}