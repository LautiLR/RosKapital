/**
 * RosKapital - Notificaciones In-App
 * Se inyecta automáticamente en el navbar.
 * Requiere: auth_client.js cargado antes.
 */
(function () {

  // ── CSS ──
  const style = document.createElement('style');
  style.textContent = `
    #notifBtn {
      position: relative;
      background: none;
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 50%;
      width: 36px;
      height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #787b86;
      cursor: pointer;
      transition: all 0.2s;
      padding: 0;
    }
    #notifBtn:hover {
      background: rgba(255,255,255,0.06);
      color: #e0e3eb;
      border-color: rgba(255,255,255,0.2);
    }
    #notifBadge {
      position: absolute;
      top: -4px;
      right: -4px;
      background: #f23645;
      color: white;
      font-size: 0.6rem;
      font-weight: 700;
      border-radius: 50%;
      min-width: 18px;
      height: 18px;
      display: none;
      align-items: center;
      justify-content: center;
      line-height: 1;
    }

    #notifDropdown {
      display: none;
      position: absolute;
      top: calc(100% + 8px);
      right: 0;
      width: 360px;
      max-height: 450px;
      background: #1e222d;
      border: 1px solid rgba(255,255,255,0.1);
      border-radius: 12px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.5);
      z-index: 2000;
      overflow: hidden;
      flex-direction: column;
    }
    #notifDropdown.open {
      display: flex;
    }

    #notifHeader {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 0.85rem 1rem;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      flex-shrink: 0;
    }
    #notifHeader span {
      font-weight: 700;
      color: #e0e3eb;
      font-size: 0.9rem;
    }
    #notifMarkAll {
      background: none;
      border: none;
      color: #3b7dff;
      font-size: 0.75rem;
      cursor: pointer;
      font-weight: 600;
      padding: 4px 8px;
      border-radius: 6px;
      transition: background 0.2s;
    }
    #notifMarkAll:hover {
      background: rgba(59,125,255,0.1);
    }

    #notifList {
      flex: 1;
      overflow-y: auto;
      max-height: 350px;
    }
    #notifList::-webkit-scrollbar { width: 4px; }
    #notifList::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 4px; }

    .notif-item {
      display: flex;
      gap: 0.7rem;
      padding: 0.75rem 1rem;
      border-bottom: 1px solid rgba(255,255,255,0.04);
      cursor: pointer;
      transition: background 0.15s;
      text-decoration: none;
    }
    .notif-item:hover { background: rgba(255,255,255,0.03); }
    .notif-item.unread { background: rgba(59,125,255,0.05); }

    .notif-icon {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.95rem;
      flex-shrink: 0;
    }
    .notif-icon.alerta_precio { background: rgba(255,167,38,0.15); }
    .notif-icon.mision { background: rgba(8,153,129,0.15); }
    .notif-icon.comunidad { background: rgba(59,125,255,0.15); }
    .notif-icon.sistema { background: rgba(255,255,255,0.08); }

    .notif-content { flex: 1; min-width: 0; }
    .notif-title {
      font-size: 0.82rem;
      font-weight: 600;
      color: #e0e3eb;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .notif-msg {
      font-size: 0.75rem;
      color: #787b86;
      margin-top: 2px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .notif-time {
      font-size: 0.65rem;
      color: #555;
      margin-top: 3px;
    }
    .notif-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #3b7dff;
      flex-shrink: 0;
      align-self: center;
    }

    .notif-empty {
      text-align: center;
      padding: 2.5rem 1rem;
      color: #787b86;
      font-size: 0.85rem;
    }
    .notif-empty i {
      display: block;
      font-size: 1.5rem;
      margin-bottom: 0.5rem;
      opacity: 0.4;
    }

    @media (max-width: 576px) {
      #notifDropdown {
        width: 300px;
        right: -60px;
      }
    }

    .notif-delete {
      background: none;
      border: none;
      color: #787b86;
      cursor: pointer;
      padding: 2px 6px;
      border-radius: 5px;
      font-size: 0.85rem;
      transition: all 0.2s;
      flex-shrink: 0;
      align-self: center;
      line-height: 1;
    }
    .notif-delete:hover {
      background: rgba(242,54,69,0.15);
      color: #f23645;
    }
  `;
  document.head.appendChild(style);

  // ── Iconos por tipo ──
  const ICONS = {
    alerta_precio: '🔔',
    mision: '🏆',
    comunidad: '💬',
    sistema: '⚙️'
  };

  // ── Tiempo relativo ──
  function timeAgo(dateStr) {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'ahora';
    if (mins < 60) return `hace ${mins}m`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `hace ${hrs}h`;
    const days = Math.floor(hrs / 24);
    if (days < 7) return `hace ${days}d`;
    return new Date(dateStr).toLocaleDateString('es-AR', { day: 'numeric', month: 'short' });
  }

  // ── Inyectar botón en navbar ──
  function injectButton() {
    // Solo mostrar si está logueado
    if (typeof isLoggedIn !== 'function' || !isLoggedIn()) return;

    const container = document.querySelector('#userNavInfo') ||
                      document.querySelector('.d-flex.align-items-center.gap-2');
    if (!container) return;

    // Crear wrapper posicionado
    const wrapper = document.createElement('div');
    wrapper.style.position = 'relative';
    wrapper.innerHTML = `
      <button id="notifBtn" title="Notificaciones">
        <i class="bi bi-bell"></i>
        <span id="notifBadge"></span>
      </button>
      <div id="notifDropdown">
        <div id="notifHeader">
          <span>Notificaciones</span>
          <button id="notifMarkAll" onclick="notifMarkAllRead()">Marcar todas leídas</button>
        </div>
        <div id="notifList"></div>
      </div>
    `;

    // Insertar antes del botón de settings
    const settingsBtn = container.querySelector('[data-bs-target="#modalSettings"]');
    if (settingsBtn) {
      container.insertBefore(wrapper, settingsBtn);
    } else {
      container.appendChild(wrapper);
    }

    // Toggle dropdown
    document.getElementById('notifBtn').addEventListener('click', (e) => {
      e.stopPropagation();
      const dd = document.getElementById('notifDropdown');
      dd.classList.toggle('open');
      if (dd.classList.contains('open')) {
        loadNotifications();
      }
    });

    // Cerrar al clickear fuera
    document.addEventListener('click', (e) => {
      const dd = document.getElementById('notifDropdown');
      if (dd && !dd.contains(e.target) && e.target.id !== 'notifBtn') {
        dd.classList.remove('open');
      }
    });

    // Cargar conteo inicial
    loadCount();
  }

  // ── Cargar conteo ──
  async function loadCount() {
    try {
      const res = await authFetch('/api/portfolio/notificaciones/count');
      if (res.ok) {
        const data = await res.json();
        const badge = document.getElementById('notifBadge');
        if (badge) {
          if (data.count > 0) {
            badge.textContent = data.count > 99 ? '99+' : data.count;
            badge.style.display = 'flex';
          } else {
            badge.style.display = 'none';
          }
        }
      }
    } catch (e) { console.warn('Error cargando conteo notifs:', e); }
  }

  // ── Cargar lista ──
  async function loadNotifications() {
    const list = document.getElementById('notifList');
    if (!list) return;

    list.innerHTML = '<div class="notif-empty"><span class="notif-icon" style="animation: wlBlink 1.2s infinite; display:inline-block; width:8px; height:8px; border-radius:50%; background:#787b86;"></span></div>';

    try {
      const res = await authFetch('/api/portfolio/notificaciones');
      if (!res.ok) throw new Error('Error');
      const notifs = await res.json();

      if (notifs.length === 0) {
        list.innerHTML = `
          <div class="notif-empty">
            <i class="bi bi-bell-slash"></i>
            No tenés notificaciones
          </div>`;
        return;
      }

      list.innerHTML = notifs.map(n => `
        <div class="notif-item ${n.leida ? '' : 'unread'}" onclick="notifClick(${n.id}, '${n.link || ''}', ${!n.leida})">
          <div class="notif-icon ${n.tipo}">${ICONS[n.tipo] || '📌'}</div>
          <div class="notif-content">
            <div class="notif-title">${n.titulo}</div>
            <div class="notif-msg">${n.mensaje}</div>
            <div class="notif-time">${timeAgo(n.created_at)}</div>
          </div>
          ${n.leida ? '' : '<div class="notif-dot"></div>'}
          <button class="notif-delete" onclick="event.stopPropagation(); notifDelete(${n.id})" title="Eliminar">
            <i class="bi bi-x"></i>
          </button>
        </div>
      `).join('');

    } catch (e) {
      list.innerHTML = '<div class="notif-empty">Error cargando notificaciones</div>';
    }
  }

  // ── Acciones ──
  window.notifDelete = async function (id) {
    try {
      await authFetch(`/api/portfolio/notificaciones/${id}`, { method: 'DELETE' });
      loadCount();
      loadNotifications();
    } catch (e) { console.warn('Error eliminando notificación:', e); }
  };

  window.notifClick = async function (id, link, isUnread) {
    if (isUnread) {
      try {
        await authFetch(`/api/portfolio/notificaciones/${id}/read`, { method: 'PUT' });
        loadCount();
      } catch (e) {}
    }
    if (link) {
      window.location.href = link;
    } else {
      loadNotifications();
    }
  };

  window.notifMarkAllRead = async function () {
    try {
      await authFetch('/api/portfolio/notificaciones/read-all', { method: 'PUT' });
      loadCount();
      loadNotifications();
    } catch (e) { console.warn('Error marcando leídas:', e); }
  };

  // ── Polling cada 60s ──
  setInterval(() => {
    if (typeof isLoggedIn === 'function' && isLoggedIn()) {
      loadCount();
    }
  }, 60000);

  // ── Init ──
  document.addEventListener('DOMContentLoaded', injectButton);

})();