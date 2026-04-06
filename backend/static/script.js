/**
 * FINTECH ADVISOR - CORE SCRIPT
 * Maneja: Modos de visualización, Búsqueda global, Gráficos TradingView y Persistencia.
 */

document.addEventListener('DOMContentLoaded', () => {
    initModoExperto();
    initRelojMercado();
    
    // Detectamos si estamos en la página de Explorar para cargar el gráfico
    const chartContainer = document.getElementById('tv_chart_container');
    if (chartContainer) {
        // Obtenemos el ticker desde la URL o el HTML renderizado
        const tickerRaw = document.querySelector('.symbol-badge')?.innerText || 'AAPL';
        initAdvancedChart(tickerRaw);
    }

    // Listener para la tecla ENTER en el buscador
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') ejecutarBusqueda(e);
        });
    }
});

/* =========================================
   1. SISTEMA DE MODOS (PERSISTENCIA)
   ========================================= */
function initModoExperto() {
    const switchBtn = document.getElementById('modoSwitch');
    const body = document.body;
    
    // 1. Leer preferencia guardada
    const esExperto = localStorage.getItem('expertMode') === 'true';
    
    // 2. Aplicar estado inicial
    if (esExperto) {
        body.classList.add('expert-mode');
        if (switchBtn) switchBtn.checked = true;
    } else {
        body.classList.remove('expert-mode');
        if (switchBtn) switchBtn.checked = false;
    }

    // 3. Escuchar cambios
    if (switchBtn) {
        switchBtn.addEventListener('change', () => {
            const activo = switchBtn.checked;
            body.classList.toggle('expert-mode', activo);
            localStorage.setItem('expertMode', activo);
            
            // Forzar un redibujado de widgets si es necesario
            window.dispatchEvent(new Event('resize'));
        });
    }
}

/* =========================================
   2. MOTOR DE BÚSQUEDA
   ========================================= */
function ejecutarBusqueda(e) {
    if (e) e.preventDefault();
    
    const input = document.getElementById('globalSearch');
    if (!input) return;

    let ticker = input.value.trim().toUpperCase();
    
    // Validación básica
    if (ticker === "") {
        alert("Por favor, ingresá un ticker (Ej: GGAL.BA, SPY, BTC-USD)");
        return;
    }

    // Redirección a la terminal de análisis
    window.location.href = `/explorar/${ticker}`;
}

/* =========================================
   3. INTEGRACIÓN TRADINGVIEW (WIDGET AVANZADO)
   ========================================= */
function initAdvancedChart(symbol) {
    // Si el ticker es de Buenos Aires, aseguramos el formato correcto para TV
    // TradingView usa "BCBA:GGAL" para Galicia, o simplemente "GGAL" si detecta el exchange.
    // Para simplificar, pasamos el símbolo limpio.
    
    new TradingView.widget({
        "autosize": true,
        "symbol": symbol,
        "interval": "D",
        "timezone": "America/Argentina/Buenos_Aires",
        "theme": "dark",
        "style": "1", // 1 = Velas Japonesas
        "locale": "es",
        "toolbar_bg": "#f1f3f6",
        "enable_publishing": false,
        "withdateranges": true,
        "hide_side_toolbar": false, // IMPORTANTE: Habilita herramientas de dibujo
        "allow_symbol_change": true,
        "container_id": "tv_chart_container",
        "save_image": true, // Permite sacar capturas
        "show_popup_button": true, // Botón de pantalla completa nativo
        "popup_width": "1000",
        "popup_height": "650",
        "studies": [
            "MASimple@tv-basicstudies", // Media Móvil Simple
            "RSI@tv-basicstudies",      // RSI
            "MACD@tv-basicstudies"      // MACD
        ],
        // TradingView guarda automáticamente los dibujos en el LocalStorage
        // del navegador bajo la clave de su librería.
    });
}

/* =========================================
   4. UTILIDADES
   ========================================= */
function initRelojMercado() {
    // Actualiza el reloj si existe el elemento en la navbar
    const reloj = document.getElementById('liveTime');
    if (!reloj) return;

    const actualizar = () => {
        const ahora = new Date();
        reloj.innerText = ahora.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
    };
    
    actualizar();
    setInterval(actualizar, 1000);
}

