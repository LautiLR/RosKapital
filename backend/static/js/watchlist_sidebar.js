/**
 * RosKapital - Watchlist Sidebar
 * Componente reutilizable para todas las páginas.
 * 
 * INSTALACIÓN en cualquier template:
 *   1. Agregar el HTML del sidebar (ver abajo) antes de </body>
 *   2. Agregar <script src="/static/js/watchlist_sidebar.js"></script>
 *   3. Listo. Se inicializa automáticamente.
 * 
 * ── HTML A PEGAR (una sola vez por página) ──────────────────────────────────
 *
 * <!-- Botón flotante para abrir el sidebar -->
 * <button id="wlToggleBtn" onclick="wlToggle()" title="Mis Activos Seguidos">
 *   <i class="fas fa-star"></i>
 *   <span id="wlBtnBadge" style="display:none"></span>
 * </button>
 *
 * <!-- Overlay oscuro de fondo -->
 * <div id="wlOverlay" onclick="wlClose()"></div>
 *
 * <!-- Panel lateral -->
 * <div id="wlSidebar">
 *   <div id="wlHeader">
 *     <div style="display:flex;align-items:center;gap:0.6rem">
 *       <i class="fas fa-star" style="color:#ffa726"></i>
 *       <span style="font-weight:600;color:#e0e3eb">Mis Activos</span>
 *       <span id="wlBadge"></span>
 *     </div>
 *     <button onclick="wlClose()" id="wlCloseBtn"><i class="fas fa-times"></i></button>
 *   </div>
 *   <div id="wlList"></div>
 *   <div id="wlAddRow">
 *     <input id="wlInput" placeholder="Ej: AAPL, MELI" maxlength="10"
 *            onkeydown="if(event.key==='Enter') wlAdd()" autocomplete="off" />
 *     <button onclick="wlAdd()"><i class="fas fa-plus"></i> Agregar</button>
 *   </div>
 *   <div id="wlMsg"></div>
 * </div>
 * ────────────────────────────────────────────────────────────────────────────
 */

(function () {

  // ── Inyectar CSS ──────────────────────────────────────────────────────────
  const style = document.createElement('style');
  style.textContent = `
    /* Botón flotante */
    #wlToggleBtn {
      position: fixed;
      right: 0;
      top: 50%;
      transform: translateY(-50%);
      z-index: 1050;
      background: #1e222d;
      border: 1px solid rgba(255,255,255,0.12);
      border-right: none;
      border-radius: 10px 0 0 10px;
      color: #ffa726;
      padding: 14px 10px;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      font-size: 1rem;
      box-shadow: -3px 0 12px rgba(0,0,0,0.4);
      transition: background 0.2s, padding 0.2s;
    }
    #wlToggleBtn:hover {
      background: #252933;
      padding-right: 14px;
    }
    #wlBtnBadge {
      background: #2962ff;
      color: #fff;
      border-radius: 10px;
      font-size: 0.65rem;
      font-weight: 700;
      padding: 1px 6px;
      min-width: 18px;
      text-align: center;
    }

    /* Overlay */
    #wlOverlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.45);
      z-index: 1055;
      backdrop-filter: blur(2px);
    }
    #wlOverlay.active { display: block; }

    /* Sidebar */
    #wlSidebar {
      position: fixed;
      top: 0;
      right: -340px;
      width: 320px;
      height: 100vh;
      background: #1e222d;
      border-left: 1px solid rgba(255,255,255,0.1);
      z-index: 1060;
      display: flex;
      flex-direction: column;
      transition: right 0.32s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: -6px 0 24px rgba(0,0,0,0.5);
    }
    #wlSidebar.open { right: 0; }

    /* Header del sidebar */
    #wlHeader {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1rem 1.25rem;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      flex-shrink: 0;
    }
    #wlCloseBtn {
      background: none;
      border: none;
      color: #787b86;
      cursor: pointer;
      font-size: 1rem;
      padding: 4px 8px;
      border-radius: 6px;
      transition: all 0.2s;
    }
    #wlCloseBtn:hover { background: rgba(255,255,255,0.06); color: #e0e3eb; }

    #wlBadge {
      background: rgba(41,98,255,0.15);
      color: #2962ff;
      border: 1px solid rgba(41,98,255,0.3);
      border-radius: 20px;
      padding: 1px 9px;
      font-size: 0.72rem;
      font-weight: 600;
    }

    /* Lista de activos */
    #wlList {
      flex: 1;
      overflow-y: auto;
      padding: 0.5rem 0;
    }
    #wlList::-webkit-scrollbar { width: 4px; }
    #wlList::-webkit-scrollbar-track { background: transparent; }
    #wlList::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

    .wl-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.7rem 1.25rem;
      border-bottom: 1px solid rgba(255,255,255,0.04);
      cursor: pointer;
      transition: background 0.15s;
    }
    .wl-item:hover { background: rgba(255,255,255,0.03); }
    .wl-item-left { display: flex; flex-direction: column; }
    .wl-ticker { font-weight: 700; color: #e0e3eb; font-size: 0.9rem; }
    .wl-name { font-size: 0.72rem; color: #787b86; margin-top: 1px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .wl-item-right { display: flex; align-items: center; gap: 0.75rem; }
    .wl-price-block { text-align: right; }
    .wl-price { font-size: 0.88rem; font-weight: 600; color: #e0e3eb; }
    .wl-change { font-size: 0.75rem; font-weight: 600; }
    .wl-up { color: #089981; }
    .wl-down { color: #f23645; }

    .wl-remove {
      background: none;
      border: none;
      color: #787b86;
      cursor: pointer;
      padding: 3px 6px;
      border-radius: 5px;
      font-size: 0.75rem;
      transition: all 0.2s;
      line-height: 1;
    }
    .wl-remove:hover { background: rgba(242,54,69,0.15); color: #f23645; }

    .wl-empty {
      text-align: center;
      color: #787b86;
      padding: 2.5rem 1rem;
      font-size: 0.85rem;
    }
    .wl-empty i { display: block; font-size: 1.5rem; margin-bottom: 0.5rem; opacity: 0.4; }

    .wl-loading-dot {
      display: inline-block;
      width: 5px; height: 5px;
      border-radius: 50%;
      background: #787b86;
      animation: wlBlink 1.2s infinite;
    }
    @keyframes wlBlink {
      0%,100% { opacity: 0.2; }
      50% { opacity: 1; }
    }

    /* Fila agregar */
    #wlAddRow {
      padding: 0.9rem 1.25rem;
      border-top: 1px solid rgba(255,255,255,0.08);
      display: flex;
      gap: 0.5rem;
      flex-shrink: 0;
    }
    #wlInput {
      flex: 1;
      background: rgba(255,255,255,0.05);
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 8px;
      color: #e0e3eb;
      padding: 0.42rem 0.75rem;
      font-size: 0.83rem;
      text-transform: uppercase;
      outline: none;
      transition: border-color 0.2s;
    }
    #wlInput:focus { border-color: #2962ff; }
    #wlInput::placeholder { color: #787b86; text-transform: none; }
    #wlAddRow button {
      background: rgba(41,98,255,0.15);
      border: 1px solid rgba(41,98,255,0.3);
      color: #2962ff;
      border-radius: 8px;
      padding: 0.42rem 0.85rem;
      font-size: 0.8rem;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.2s;
    }
    #wlAddRow button:hover { background: rgba(41,98,255,0.28); }

    #wlMsg {
      padding: 0 1.25rem 0.7rem;
      font-size: 0.78rem;
      min-height: 1.2rem;
      flex-shrink: 0;
    }
  `;
  document.head.appendChild(style);

  // ── Estado ────────────────────────────────────────────────────────────────
  let isOpen = false;

  // ── API ───────────────────────────────────────────────────────────────────
  window.wlToggle = function () { isOpen ? wlClose() : wlOpen(); };

  window.wlOpen = function () {
    isOpen = true;
    document.getElementById('wlSidebar').classList.add('open');
    document.getElementById('wlOverlay').classList.add('active');
    wlLoad();
  };

  window.wlClose = function () {
    isOpen = false;
    document.getElementById('wlSidebar').classList.remove('open');
    document.getElementById('wlOverlay').classList.remove('active');
  };

  window.wlAdd = async function () {
    const input = document.getElementById('wlInput');
    const msg = document.getElementById('wlMsg');
    const ticker = input.value.trim().toUpperCase();

    if (!ticker) return;

    if (!/^[A-Z0-9.\-]{1,10}$/.test(ticker)) {
      wlMsg('Ticker inválido.', '#f23645'); return;
    }

    const list = wlGetList();
    if (list.length >= 15) { wlMsg('Máximo 15 activos.', '#f23645'); return; }

    // Guardar en DB si está logueado
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
      try {
        const res = await authFetch(`/api/portfolio/watchlist/${ticker}`, { method: 'POST' });
        if (!res.ok) {
          const data = await res.json();
          if (data.detail === 'Ya está en tu watchlist') {
            wlMsg('Ya está en tu lista.', '#ffa726');
            return;
          }
          wlMsg(data.detail || 'Error', '#f23645');
          return;
        }
      } catch (e) { console.warn('Error guardando en DB:', e); }
    }

    if (list.includes(ticker)) { wlMsg('Ya está en tu lista.', '#ffa726'); return; }

    list.push(ticker);
    wlSave(list);
    input.value = '';
    wlMsg(`${ticker} agregado ✓`, '#089981');
    wlLoad();
  };

  window.wlRemove = async function (ticker) {
    // Eliminar de DB si está logueado
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
      try {
        await authFetch(`/api/portfolio/watchlist/${ticker}`, { method: 'DELETE' });
      } catch (e) { console.warn('Error eliminando de DB:', e); }
    }

    const list = wlGetList().filter(t => t !== ticker);
    wlSave(list);
    wlLoad();
  };

  // ── Helpers ───────────────────────────────────────────────────────────────
  function wlGetList() {
    return JSON.parse(localStorage.getItem('fintech_watchlist') || '[]');
  }

  async function wlGetListSmart() {
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
      try {
        const res = await authFetch('/api/portfolio/watchlist');
        if (res.ok) {
          const data = await res.json();
          localStorage.setItem('fintech_watchlist', JSON.stringify(data));
          return data;
        }
      } catch (e) { console.warn('Error cargando watchlist:', e); }
    }
    return wlGetList();
  }

  function wlSave(list) {
    localStorage.setItem('fintech_watchlist', JSON.stringify(list));
    const badge = document.getElementById('wlBtnBadge');
    if (badge) {
      badge.textContent = list.length;
      badge.style.display = list.length > 0 ? 'block' : 'none';
    }
  }

  function wlMsg(text, color) {
    const el = document.getElementById('wlMsg');
    if (!el) return;
    el.textContent = text;
    el.style.color = color;
    setTimeout(() => { el.textContent = ''; }, 2500);
  }

  // ── Render + fetch de precios ─────────────────────────────────────────────
  async function wlLoad() {
    const list = await wlGetListSmart();
    const listEl = document.getElementById('wlList');
    const badge = document.getElementById('wlBadge');
    if (!listEl) return;

    // Badge
    if (badge) badge.textContent = list.length;
    wlSave(list); // actualiza badge del botón también

    if (list.length === 0) {
      listEl.innerHTML = `
        <div class="wl-empty">
          <i class="fas fa-star"></i>
          No tenés activos en seguimiento.<br>Agregá uno abajo.
        </div>`;
      await wlRenderAlertas();
      return;
    }

    // Skeleton de carga
    listEl.innerHTML = list.map(t => `
      <div class="wl-item" id="wli-${t.replace('.', '_').replace('-', '_')}">
        <div class="wl-item-left">
          <span class="wl-ticker">${t}</span>
          <span class="wl-name">Cargando...</span>
        </div>
        <div class="wl-item-right">
          <div class="wl-price-block">
            <span class="wl-loading-dot"></span>
          </div>
          <button class="wl-remove" onclick="event.stopPropagation();wlRemove('${t}')">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </div>
    `).join('');

    // Asignar click de navegación
    list.forEach(t => {
      const id = `wli-${t.replace('.', '_').replace('-', '_')}`;
      const el = document.getElementById(id);
      if (el) el.onclick = () => window.location.href = `/explorar/${t}`;
    });

    // Fetch precios — URL correcta: /api/cotizaciones (prefix /api, no /api/market)
    try {
      const res = await fetch(`/api/cotizaciones?tickers=${list.join(',')}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const datos = await res.json();

      list.forEach(t => {
        const id = `wli-${t.replace('.', '_').replace('-', '_')}`;
        const el = document.getElementById(id);
        if (!el) return;

        const d = datos[t];  // clave exacta como vino del backend

        if (!d) {
          // ticker no encontrado en yfinance
          el.querySelector('.wl-name').textContent = 'Sin datos';
          el.querySelector('.wl-price-block').innerHTML =
            `<span style="color:#787b86;font-size:0.75rem">N/D</span>`;
          return;
        }

        const esPos = d.variacion >= 0;
        const signo = esPos ? '+' : '';
        const cls = esPos ? 'wl-up' : 'wl-down';

        el.querySelector('.wl-name').textContent = 'Click para analizar';
        el.querySelector('.wl-price-block').innerHTML = `
          <div class="wl-price">$${d.precio.toFixed(2)}</div>
          <div class="wl-change ${cls}">${signo}${d.variacion.toFixed(2)}%</div>
        `;
      });

    } catch (err) {
      console.error('[Watchlist] Error fetching cotizaciones:', err);
    }
    await wlRenderAlertas();
  }

  // ── Init: actualizar badge del botón al cargar la página ─────────────────
  document.addEventListener('DOMContentLoaded', () => {
    const list = wlGetList();
    const badge = document.getElementById('wlBtnBadge');
    if (badge && list.length > 0) {
      badge.textContent = list.length;
      badge.style.display = 'block';
    }
  });

  const alertaStyle = document.createElement('style');
  alertaStyle.textContent = `
    #wlAlertSection {
      border-top: 1px solid rgba(255,255,255,0.08);
      padding: 0.5rem 0;
      flex-shrink: 0;
    }
    #wlAlertHeader {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.5rem 1.25rem;
      color: #ffa726;
      font-size: 0.78rem;
      font-weight: 600;
    }
    .wl-alert-item {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0.5rem 1.25rem;
      border-bottom: 1px solid rgba(255,255,255,0.03);
      font-size: 0.8rem;
    }
    .wl-alert-item:last-child { border-bottom: none; }
    .wl-alert-left {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }
    .wl-alert-ticker {
      font-weight: 700;
      color: #e0e3eb;
      font-size: 0.82rem;
    }
    .wl-alert-dir {
      font-size: 0.7rem;
      padding: 1px 6px;
      border-radius: 4px;
      font-weight: 600;
    }
    .wl-alert-up {
      background: rgba(8,153,129,0.15);
      color: #089981;
    }
    .wl-alert-down {
      background: rgba(242,54,69,0.15);
      color: #f23645;
    }
    .wl-alert-price {
      color: #e0e3eb;
      font-weight: 600;
      font-size: 0.85rem;
    }
    .wl-alert-remove {
      background: none;
      border: none;
      color: #787b86;
      cursor: pointer;
      padding: 2px 5px;
      border-radius: 4px;
      font-size: 0.7rem;
      transition: all 0.2s;
    }
    .wl-alert-remove:hover {
      background: rgba(242,54,69,0.15);
      color: #f23645;
    }
    .wl-alert-empty {
      padding: 0.5rem 1.25rem;
      font-size: 0.75rem;
      color: #787b86;
    }
  `;
  document.head.appendChild(alertaStyle);

  // ── Render alertas en sidebar ────────────────────────────────────────────
  window.wlRenderAlertas = async function () {
    // Buscar o crear el contenedor
    let section = document.getElementById('wlAlertSection');
    if (!section) {
      section = document.createElement('div');
      section.id = 'wlAlertSection';
      // Insertar antes del wlAddRow
      const addRow = document.getElementById('wlAddRow');
      if (addRow) {
        addRow.parentNode.insertBefore(section, addRow);
      }
    }

    // Smart: si está logueado, cargar alertas desde DB y sincronizar localStorage
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
      try {
        const res = await authFetch('/api/portfolio/alertas');
        if (res.ok) {
          const data = await res.json();
          localStorage.setItem('roskapital_alertas', JSON.stringify(data));
        }
      } catch (e) { console.warn('Error cargando alertas de DB:', e); }
    }

    const alertas = JSON.parse(localStorage.getItem('roskapital_alertas') || '[]');

    if (alertas.length === 0) {
      section.innerHTML = `
        <div id="wlAlertHeader">
          <i class="fas fa-bell"></i> Alertas
          <span style="color:#787b86; font-weight:400;">(0)</span>
        </div>
        <div class="wl-alert-empty">No tenés alertas activas.</div>
      `;
      return;
    }

    let html = `
      <div id="wlAlertHeader">
        <i class="fas fa-bell"></i> Alertas
        <span style="color:#787b86; font-weight:400;">(${alertas.length}/4)</span>
      </div>
    `;

    alertas.forEach((alerta, i) => {
      const esUp = alerta.direccion === 'above';
      const dirClass = esUp ? 'wl-alert-up' : 'wl-alert-down';
      const dirText = esUp ? '↑ Sube' : '↓ Baja';

      html += `
        <div class="wl-alert-item">
          <div class="wl-alert-left">
            <span class="wl-alert-ticker">${alerta.ticker}</span>
            <span class="wl-alert-dir ${dirClass}">${dirText}</span>
          </div>
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span class="wl-alert-price">$${alerta.precio.toFixed(2)}</span>
            <button class="wl-alert-remove" onclick="event.stopPropagation(); wlRemoveAlerta(${i})" title="Eliminar alerta">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      `;
    });

    section.innerHTML = html;
  };

  window.wlRemoveAlerta = async function (index) {
    const alertas = JSON.parse(localStorage.getItem('roskapital_alertas') || '[]');
    const alerta = alertas[index];

    // Eliminar de DB si está logueado y tiene id
    if (typeof isLoggedIn === 'function' && isLoggedIn() && alerta && alerta.id) {
      try {
        await authFetch(`/api/portfolio/alertas/${alerta.id}`, { method: 'DELETE' });
      } catch (e) { console.warn('Error eliminando alerta de DB:', e); }
    }

    alertas.splice(index, 1);
    localStorage.setItem('roskapital_alertas', JSON.stringify(alertas));
    await wlRenderAlertas();
  };

})();
