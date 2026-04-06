const preguntasTest = [
    {
        pregunta: "¿Cuál es tu objetivo principal al invertir?",
        opciones: [
            { texto: "Que mis ahorros no pierdan contra la inflación.", valor: 0 },
            { texto: "Comprar una casa o auto en unos años.", valor: 1 },
            { texto: "Multiplicar mi capital, aunque tome riesgo.", valor: 2 }
        ]
    },
    {
        pregunta: "¿Por cuánto tiempo dejarías tu dinero invertido?",
        opciones: [
            { texto: "Menos de un año (necesito liquidez).", valor: 0 },
            { texto: "De 2 a 5 años.", valor: 1 },
            { texto: "Más de 5 años, no tengo apuro.", valor: 2 }
        ]
    },
    {
        pregunta: "Si tu inversión cae un 15% en una semana...",
        opciones: [
            { texto: "Vendo todo para no perder más.", valor: 0 },
            { texto: "Me preocupo, pero espero.", valor: 1 },
            { texto: "Compro más, ¡está barato!", valor: 2 }
        ]
    },
    {
        pregunta: "¿Qué frase te representa mejor?",
        opciones: [
            { texto: 'Más vale pájaro en mano que cien volando.', valor: 0 },
            { texto: 'El equilibrio es la base del éxito.', valor: 1 },
            { texto: 'El que no arriesga, no gana.', valor: 2 }
        ]
    },
    {
        pregunta: "¿En qué preferirías invertir?",
        opciones: [
            { texto: "Coca-Cola o Walmart (Estables).", valor: 0 },
            { texto: "Apple o Microsoft (Crecimiento).", valor: 1 },
            { texto: "Bitcoin o una Startup de IA.", valor: 2 }
        ]
    },
    {
        pregunta: "¿Qué porcentaje de tus ahorros usarás aquí?",
        opciones: [
            { texto: "Casi todo mi capital.", valor: 0 }, // Paradójicamente, si usa todo, debe ser conservador
            { texto: "Una parte importante.", valor: 1 },
            { texto: "Solo un dinero extra que puedo perder.", valor: 2 }
        ]
    },
    {
        pregunta: "Nivel de conocimiento financiero:",
        opciones: [
            { texto: "Principiante.", valor: 0 },
            { texto: "Intermedio.", valor: 1 },
            { texto: "Avanzado / Experto.", valor: 2 }
        ]
    }
];

// Variables de Estado
let preguntaActual = 0;
let puntajeTotal = 0;

// Función para abrir el modal
function abrirTestInversor() {
    const modal = new bootstrap.Modal(document.getElementById('modalPerfilInversor'));
    preguntaActual = 0;
    puntajeTotal = 0;
    mostrarPregunta();
    document.getElementById('footerResultados').classList.add('d-none');
    modal.show();
}

// Renderiza la pregunta actual
function mostrarPregunta() {
    const contenedor = document.getElementById('contenidoTest');
    const barra = document.getElementById('barraProgreso');
    const data = preguntasTest[preguntaActual];

    // Actualizar barra
    const porcentaje = ((preguntaActual) / preguntasTest.length) * 100;
    barra.style.width = porcentaje + '%';

    // HTML de la pregunta
    let html = `
        <h4 class="mb-4">${data.pregunta}</h4>
        <div class="d-grid gap-2">
    `;

    data.opciones.forEach((opcion, index) => {
        html += `
            <div class="opcion-card" onclick="seleccionarOpcion(${opcion.valor})" style="user-select:none; cursor:pointer;">
                <div class="d-flex align-items-center">
                    <div class="badge bg-warning text-dark me-3 rounded-circle p-2">${String.fromCharCode(65 + index)}</div>
                    <span class="fs-5">${opcion.texto}</span>
                </div>
            </div>
        `;
    });

    html += `</div>`;
    contenedor.innerHTML = html;
}

// Maneja la selección
function seleccionarOpcion(valor) {
    puntajeTotal += valor;
    preguntaActual++;

    if (preguntaActual < preguntasTest.length) {
        mostrarPregunta();
    } else {
        mostrarResultado();
    }
}

// Calcula y muestra el personaje final
function mostrarResultado() {
    const contenedor = document.getElementById('contenidoTest');
    const footer = document.getElementById('footerResultados');
    const barra = document.getElementById('barraProgreso');
    barra.style.width = '100%';

    let perfil = {};

    // Lógica de asignación de Perfil
    if (puntajeTotal <= 5) {
        perfil = {
            tipo: "Conservador",
            personaje: "Don Horacio",
            icono: "🛡️",
            clase: "text-success",
            mensaje: "¡Un gusto! Soy Don Horacio. Veo que valorás la seguridad. Mi lema es: 'Cuidar el capital ante todo'. Vamos a buscar acciones sólidas y dividendos."
        };
    } else if (puntajeTotal <= 10) {
        perfil = {
            tipo: "Moderado",
            personaje: "Valeria",
            icono: "⚖️",
            clase: "text-primary",
            mensaje: "¡Hola! Soy Valeria. Tu perfil es equilibrado. Vamos a buscar crecimiento, pero siempre con un plan de respaldo. Diversificar es nuestra clave."
        };
    } else {
        perfil = {
            tipo: "Arriesgado",
            personaje: "Enzo",
            icono: "🚀",
            clase: "text-danger",
            mensaje: "¡Qué onda! Soy Enzo. Si estás acá es porque querés rendimientos altos y no le temés al riesgo. ¡Abróchate el cinturón que vamos por las tecnológicas!"
        };
    }

    // Guardar en LocalStorage
    localStorage.setItem('perfil_inversor', JSON.stringify(perfil));

    // Guardar en DB si está logueado
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
        try {
            authFetch('/api/portfolio/perfil', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tipo: perfil.tipo, personaje: perfil.personaje })
            });
        } catch (e) { console.warn('Error guardando perfil en DB:', e); }
    }

    completarMision('identidad');

    // Mostrar HTML del Resultado
    contenedor.innerHTML = `
        <div class="fade-in-up">
            <div class="personaje-avatar ${perfil.clase}">
                ${perfil.icono}
            </div>
            <h2 class="fw-bold mb-1 ${perfil.clase}">¡Eres ${perfil.tipo}!</h2>
            <h5 class="text-muted mb-4">Tu mentor es ${perfil.personaje}</h5>
            <div class="p-3 rounded" style="background: rgba(255,255,255,0.05);">
                <p class="fs-5 fst-italic">"${perfil.mensaje}"</p>
            </div>
        </div>
    `;

    footer.classList.remove('d-none'); // Mostrar botón de finalizar
    actualizarBotonNavbar(perfil);
}

async function cargarPerfilDesdeDB() {
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
        try {
            const res = await authFetch('/api/portfolio/perfil');
            if (res.ok) {
                const data = await res.json();
                if (data.investor_profile) {
                    // Reconstruir el objeto perfil desde el tipo guardado
                    const tipo = data.investor_profile;
                    let perfil = null;
                    if (tipo === 'Conservador') {
                        perfil = { tipo: "Conservador", personaje: "Don Horacio", icono: "🛡️", clase: "text-success" };
                    } else if (tipo === 'Moderado') {
                        perfil = { tipo: "Moderado", personaje: "Valeria", icono: "⚖️", clase: "text-primary" };
                    } else if (tipo === 'Arriesgado') {
                        perfil = { tipo: "Arriesgado", personaje: "Enzo", icono: "🚀", clase: "text-danger" };
                    }
                    if (perfil) {
                        localStorage.setItem('perfil_inversor', JSON.stringify(perfil));
                    }
                }
            }
        } catch (e) { console.warn('Error cargando perfil de DB:', e); }
    }
}

/* --- REEMPLAZA TU FUNCIÓN verificarPerfilExistente POR ESTA --- */
function verificarPerfilExistente() {
    const perfilGuardado = JSON.parse(localStorage.getItem('perfil_inversor'));
    
    if (perfilGuardado) {
        actualizarBotonNavbar(perfilGuardado);
    }
}

function reiniciarTest() {
    if(confirm("¿Seguro que quieres borrar tu perfil y hacer el test de nuevo?")) {
        localStorage.removeItem('perfil_inversor');
        location.reload(); // Recarga la página para empezar de cero
    }
}

// Cambia el botón del menú
function actualizarBotonNavbar(perfil) {
    const btnTexto = document.getElementById('textoBotonPerfil');
    const btn = document.getElementById('btnTestInversor');
    
    if(btnTexto && btn) {
        btnTexto.innerHTML = `Mentor: ${perfil.personaje}`;
        btn.classList.remove('btn-outline-warning');
        btn.classList.add('btn-dark'); // O un color que resalte que ya está activo
        // Opcional: Agregar el icono del personaje al botón
    }
}
/* --- FUNCIÓN EXTRA: ETIQUETADO AUTOMÁTICO DE RIESGO --- */

// 1. "Base de datos" manual de riesgos (puedes agregar más aquí)
const diccionarioRiesgo = {
    // Escudos (Conservador)
    'KO': 'escudo', 'MCD': 'escudo', 'JNJ': 'escudo', 'PG': 'escudo', 'WMT': 'escudo', 'IBM': 'escudo',
    // Motores (Moderado)
    'AAPL': 'motor', 'MSFT': 'motor', 'GOOGL': 'motor', 'AMZN': 'motor', 'DIS': 'motor', 'V': 'motor',
    // Cohetes (Arriesgado)
    'TSLA': 'cohete', 'NVDA': 'cohete', 'BTC': 'cohete', 'AMD': 'cohete', 'NFLX': 'cohete', 'META': 'cohete','INTC': 'cohete' 
};

// 2. Función que recorre la página y pone las etiquetas
function aplicarEtiquetasRiesgo() {
    // Busca todos los elementos que marcamos en el HTML
    const celdas = document.querySelectorAll('.dato-ticker');

    celdas.forEach(celda => {
        const ticker = celda.innerText.trim().toUpperCase(); // Obtiene "AAPL" o "KO"
        
        // Si el ticker está en nuestra lista, agregamos el badge
        if (diccionarioRiesgo[ticker]) {
            const tipo = diccionarioRiesgo[ticker]; // 'escudo', 'motor' o 'cohete'
            
            // Creamos el HTML del badge
            let badgeHTML = '';
            if(tipo === 'escudo') badgeHTML = ' <span class="badge-escudo" style="font-size:0.7em;">🛡️</span>';
            if(tipo === 'motor')  badgeHTML = ' <span class="badge-motor" style="font-size:0.7em;">⚖️</span>';
            if(tipo === 'cohete') badgeHTML = ' <span class="badge-cohete" style="font-size:0.7em;">🚀</span>';

            // Agregamos el badge al lado del texto existente
            // Verificamos para no agregarlo doble si la función corre dos veces
            if (!celda.innerHTML.includes('badge-')) {
                celda.innerHTML += badgeHTML;
            }
        }
    });
}

/* --- PAQUETE 2: INICIALIZACIÓN DE TOOLTIPS Y MISIONES --- */

document.addEventListener('DOMContentLoaded', function() {
    verificarPerfilExistente();
    aplicarEtiquetasRiesgo();

    let tooltipsLeidos = 0;
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        let tooltip = new bootstrap.Tooltip(tooltipTriggerEl);
        tooltipTriggerEl.addEventListener('shown.bs.tooltip', function () {
            tooltipsLeidos++;
            if (tooltipsLeidos === 3) {
                completarMision('curioso');
            }
        });
        return tooltip;
    });
});

/* --- SISTEMA DE MISIONES--- */
const misiones = {
    'identidad': { titulo: "¡Identidad Definida!", desc: "Completaste el Test de Inversor.", icono: "🎭" },
    'explorador': { titulo: "Primeros Pasos", desc: "Visitaste el Simulador por primera vez.", icono: "🚀" },
    'curioso': { titulo: "¡Curiosidad Financiera!", desc: "Leíste 3 conceptos nuevos en los tooltips.", icono: "🔍" },
    'inversor': { titulo: "¡Accionista!", desc: "Hiciste tu primera operación de compra.", icono: "📈" },
    'vigilante': { titulo: "¡Ojo de Halcón!", desc: "Agregaste tu primer activo a la watchlist.", icono: "⭐" },
    'alerta': { titulo: "¡Alerta Activada!", desc: "Configuraste tu primera alerta de precio.", icono: "🔔" },
    'analista': { titulo: "¡Analista Junior!", desc: "Exploraste 5 activos diferentes.", icono: "🔬" },
    'comparador': { titulo: "¡Versus Mode!", desc: "Usaste el comparador de activos.", icono: "⚖️" },
    'diversificado': { titulo: "¡Cartera Diversificada!", desc: "Tenés activos en 3 sectores diferentes.", icono: "🎯" },
    'trader': { titulo: "¡Trader Activo!", desc: "Realizaste 5 operaciones en el simulador.", icono: "💹" },
    'ganador': { titulo: "¡Primera Ganancia!", desc: "Vendiste un activo con ganancia.", icono: "🏆" }
};

async function completarMision(idMision) {
    let historial = JSON.parse(localStorage.getItem('misiones_completadas')) || [];
    
    if (historial.includes(idMision)) return;

    // Guardar misión en DB y crear notificación
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
        try {
            await authFetch(`/api/portfolio/misiones/${idMision}`, { method: 'POST' });
        } catch (e) { console.warn('Error guardando misión en DB:', e); }
    }

    historial.push(idMision);
    localStorage.setItem('misiones_completadas', JSON.stringify(historial));
    
    // Actualizar badge de campana en vez de toast
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
        function updateBadge() {
            const badge = document.getElementById('notifBadge');
            if (badge) {
                const current = parseInt(badge.textContent || '0');
                badge.textContent = current + 1;
                badge.style.display = 'flex';
            } else {
                setTimeout(updateBadge, 500);
            }
        }
        updateBadge();
    } else {
        mostrarNotificacionMision(idMision);
    }
}

async function cargarMisionesDesdeDB() {
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
        try {
            const res = await authFetch('/api/portfolio/misiones');
            if (res.ok) {
                const data = await res.json();
                localStorage.setItem('misiones_completadas', JSON.stringify(data));
            }
        } catch (e) { console.warn('Error cargando misiones de DB:', e); }
    }
}

function mostrarNotificacionMision(idMision) {
    if (typeof isLoggedIn === 'function' && isLoggedIn()) return;
    
    const mision = misiones[idMision];
    if (!mision) return;
    
    const toastEl = document.getElementById('liveToast');
    const toastBody = document.getElementById('textoMision');
    
    if (toastEl && toastBody) {
        toastBody.innerHTML = `${mision.icono} <strong class="me-1">¡Misión Cumplida!</strong> ${mision.titulo}`;
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
    }
}

// ── TRIGGERS AUTOMÁTICOS DE MISIONES ──────────────────────────────

// Misión: vigilante (agregar a watchlist)
function checkMisionVigilante() {
    const watchlist = JSON.parse(localStorage.getItem('fintech_watchlist') || '[]');
    if (watchlist.length >= 1) {
        completarMision('vigilante');
    }
}

// Misión: alerta (crear primera alerta)
function checkMisionAlerta() {
    const alertas = JSON.parse(localStorage.getItem('roskapital_alertas') || '[]');
    if (alertas.length >= 1) {
        completarMision('alerta');
    }
}

// Misión: analista (explorar 5 activos diferentes)
function checkMisionAnalista() {
    let visitados = JSON.parse(localStorage.getItem('roskapital_tickers_visitados') || '[]');
    const path = window.location.pathname;
    
    if (path.startsWith('/explorar/')) {
        const ticker = path.split('/explorar/')[1];
        if (ticker && !visitados.includes(ticker)) {
            visitados.push(ticker);
            localStorage.setItem('roskapital_tickers_visitados', JSON.stringify(visitados));
        }
    }
    
    if (visitados.length >= 5) {
        completarMision('analista');
    }
}

// Misión: comparador (usar comparador)
function checkMisionComparador() {
    if (window.location.pathname === '/comparar') {
        completarMision('comparador');
    }
}

// Misión: diversificado (3+ sectores diferentes en portfolio)
async function checkMisionDiversificado() {
    const portfolio = JSON.parse(localStorage.getItem('fintech_sim_portfolio') || '[]');
    if (portfolio.length < 3) return;

    try {
        const sectores = new Set();
        for (const pos of portfolio) {
            try {
                const r = await fetch(`/api/fundamentals/${pos.ticker}`);
                if (r.ok) {
                    const d = await r.json();
                    if (d.sector && d.sector !== 'N/A') {
                        sectores.add(d.sector);
                    }
                }
            } catch (e) {}
        }

        if (sectores.size >= 3) {
            completarMision('diversificado');
        }

        // Calcular perfil de volatilidad del portfolio
        calcularPerfilPortfolio(portfolio);

    } catch (e) {
        console.warn('Error chequeando diversificación:', e);
    }
}

// Calcular perfil de volatilidad del portfolio
async function calcularPerfilPortfolio(portfolio) {
    if (portfolio.length === 0) return;

    let totalBeta = 0;
    let count = 0;

    for (const pos of portfolio) {
        try {
            const r = await fetch(`/api/fundamentals/${pos.ticker}`);
            if (r.ok) {
                const d = await r.json();
                if (d.beta && d.beta > 0) {
                    totalBeta += d.beta;
                    count++;
                }
            }
        } catch (e) {}
    }

    if (count === 0) return;

    const betaPromedio = totalBeta / count;
    let perfil = {};

    if (betaPromedio > 1.3) {
        perfil = {
            tipo: 'Agresivo',
            desc: 'Gran potencial de crecimiento',
            color: '#f23645',
            icono: '🚀',
            beta: betaPromedio.toFixed(2)
        };
    } else if (betaPromedio >= 0.8) {
        perfil = {
            tipo: 'Equilibrado',
            desc: 'Balance entre riesgo y retorno',
            color: '#ffa726',
            icono: '⚖️',
            beta: betaPromedio.toFixed(2)
        };
    } else {
        perfil = {
            tipo: 'Defensivo',
            desc: 'Menor volatilidad, más estable',
            color: '#089981',
            icono: '🛡️',
            beta: betaPromedio.toFixed(2)
        };
    }

    // Guardar en DB
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
        try {
            authFetch('/api/portfolio/portfolio-profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tipo: perfil.tipo })
            });
        } catch (e) {}
    }

    localStorage.setItem('roskapital_perfil_portfolio', JSON.stringify(perfil));
}

// Misión: trader (5 operaciones)
function checkMisionTrader() {
    const trades = JSON.parse(localStorage.getItem('fintech_trade_history') || '[]');
    if (trades.length >= 5) {
        completarMision('trader');
    }
}

// Misión: ganador (vender con ganancia)
function checkMisionGanador() {
    const trades = JSON.parse(localStorage.getItem('fintech_trade_history') || '[]');
    const ventas = trades.filter(t => t.tipo === 'VENTA');
    if (ventas.length >= 1) {
        completarMision('ganador');
    }
}

// Ejecutar todos los checks al cargar cualquier página
document.addEventListener('DOMContentLoaded', function() {
    checkMisionVigilante();
    checkMisionAlerta();
    checkMisionAnalista();
    checkMisionComparador();
    checkMisionTrader();
    checkMisionGanador();
    
    // Solo chequear diversificación en Home y Simulador (requiere fetch)
    if (window.location.pathname === '/' || window.location.pathname === '/simulador') {
        checkMisionDiversificado();
    }
});

// ── MODAL DE MISIONES ─────────────────────────────────────────────

function abrirModalMisiones() {
    const historial = JSON.parse(localStorage.getItem('misiones_completadas')) || [];
    const total = Object.keys(misiones).length;
    const completadas = historial.length;
    
    // Progress bar
    const pct = Math.round((completadas / total) * 100);
    document.getElementById('misionesProgressBar').style.width = pct + '%';
    document.getElementById('misionesProgressText').textContent = `${completadas} de ${total} completadas`;
    
    // Lista de misiones
    let html = '';
    Object.keys(misiones).forEach(id => {
        const m = misiones[id];
        const done = historial.includes(id);
        
        html += `
            <div style="display:flex; align-items:center; gap:0.75rem; padding:0.7rem 0.5rem; border-bottom:1px solid rgba(255,255,255,0.05); ${done ? '' : 'opacity:0.5;'}">
                <span style="font-size:1.3rem; width:32px; text-align:center;">${done ? m.icono : '🔒'}</span>
                <div style="flex:1;">
                    <div style="font-weight:600; color:${done ? 'white' : '#787b86'}; font-size:0.9rem;">${m.titulo}</div>
                    <div style="font-size:0.78rem; color:#787b86;">${m.desc}</div>
                </div>
                ${done ? '<i class="bi bi-check-circle-fill text-success"></i>' : '<i class="bi bi-circle text-secondary" style="opacity:0.3;"></i>'}
            </div>
        `;
    });
    
    document.getElementById('misionesLista').innerHTML = html;
    
    const modal = new bootstrap.Modal(document.getElementById('modalMisiones'));
    modal.show();
}

// Actualizar contador de misiones en el navbar
function actualizarContadorMisiones() {
    const historial = JSON.parse(localStorage.getItem('misiones_completadas')) || [];
    const el = document.getElementById('misionesCount');
    if (el) {
        el.textContent = historial.length;
    }
}

// Ejecutar al cargar
document.addEventListener('DOMContentLoaded', async function() {
    // Cargar misiones y perfil desde DB si está logueado
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
        await cargarMisionesDesdeDB();
        await cargarPerfilDesdeDB();
    }
    actualizarContadorMisiones();
    verificarPerfilExistente();
});


