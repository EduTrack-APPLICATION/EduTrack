/**
 * EduTrack - Frontend JavaScript
 * Theme toggling, sidebar, AJAX helpers, keyboard navigation
 */

(function () {
    'use strict';

    // ===== CSRF Token =====
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    window.CSRF_TOKEN = csrfMeta ? csrfMeta.getAttribute('content') : '';

    // ===== Theme Toggle =====
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    // El tema ya fue aplicado por el script inline en <head>.
    // Solo necesitamos sincronizar el icono y manejar el toggle.
    const currentTheme = html.getAttribute('data-theme') || 'light';
    updateThemeIcon(currentTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const current = html.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-theme', next);
            localStorage.setItem('edutrack-theme', next);
            updateThemeIcon(next);
        });
    }

    // Si el usuario no ha elegido manualmente y cambia su preferencia del SO,
    // seguir esa preferencia automáticamente.
    if (window.matchMedia) {
        const mq = window.matchMedia('(prefers-color-scheme: dark)');
        mq.addEventListener && mq.addEventListener('change', function (e) {
            if (!localStorage.getItem('edutrack-theme')) {
                const next = e.matches ? 'dark' : 'light';
                html.setAttribute('data-theme', next);
                updateThemeIcon(next);
            }
        });
    }

    function updateThemeIcon(theme) {
        if (!themeToggle) return;
        const icon = themeToggle.querySelector('i');
        if (!icon) return;
        icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars';
        themeToggle.setAttribute('title',
            theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro');
    }

    // ===== Sidebar Toggle (Mobile) =====
    const toggleBtn = document.getElementById('toggleSidebar');
    const sidebar = document.getElementById('sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });

        // Close on outside click on mobile
        document.addEventListener('click', function (e) {
            if (window.innerWidth >= 992) return;
            if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }

    // ===== Auto-dismiss alerts =====
    setTimeout(function () {
        document.querySelectorAll('.alert.alert-dismissible').forEach(function (a) {
            try { bootstrap.Alert.getOrCreateInstance(a).close(); } catch (_) {}
        });
    }, 6000);

    // ===== AJAX helper =====
    window.apiPost = async function (url, body) {
        const res = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': window.CSRF_TOKEN,
            },
            body: JSON.stringify(body || {}),
        });
        if (!res.ok) throw new Error('Error en la solicitud: ' + res.status);
        return res.json();
    };

    window.apiGet = async function (url) {
        const res = await fetch(url, { headers: { 'X-CSRFToken': window.CSRF_TOKEN } });
        if (!res.ok) throw new Error('Error en la solicitud: ' + res.status);
        return res.json();
    };

    // ===== Keyboard navigation in grade tables =====
    document.addEventListener('keydown', function (e) {
        const target = e.target;
        if (!target.classList || !target.classList.contains('grade-input')) return;

        const inputs = Array.from(document.querySelectorAll('.grade-input'));
        const idx = inputs.indexOf(target);

        if (e.key === 'ArrowDown' || (e.key === 'Enter' && !e.shiftKey)) {
            e.preventDefault();
            if (idx >= 0 && idx < inputs.length - 1) inputs[idx + 1].focus();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (idx > 0) inputs[idx - 1].focus();
        }
    });

    // ===== Confirm dialogs are handled by the Confirm API below =====
    // (registers automatically via event delegation)

    // ===== Live search filter for tables =====
    document.querySelectorAll('[data-table-filter]').forEach(function (input) {
        const targetSel = input.getAttribute('data-table-filter');
        const tbody = document.querySelector(targetSel + ' tbody');
        if (!tbody) return;

        input.addEventListener('input', function () {
            const q = input.value.toLowerCase().trim();
            tbody.querySelectorAll('tr').forEach(function (tr) {
                const txt = tr.textContent.toLowerCase();
                tr.style.display = (!q || txt.includes(q)) ? '' : 'none';
            });
        });
    });
})();

/* ============================================================
   Búsqueda global (Ctrl+K)
   ============================================================ */
(function () {
    'use strict';

    const trigger = document.getElementById('searchTrigger');
    const modal = document.getElementById('searchModal');
    const input = document.getElementById('searchInput');
    const results = document.getElementById('searchResults');

    if (!trigger || !modal || !input || !results) return; // página sin auth

    let activeIndex = -1;
    let resultLinks = [];
    let searchTimer = null;
    let lastQuery = '';

    function openSearch() {
        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        setTimeout(() => input.focus(), 50);
    }

    function closeSearch() {
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        input.value = '';
        lastQuery = '';
        renderEmpty();
    }

    function renderEmpty() {
        results.innerHTML = `
            <div class="search-empty">
                <i class="bi bi-search fs-2"></i>
                <p>Escribe al menos 2 caracteres para buscar</p>
                <div class="search-hints">
                    <span><kbd>↑</kbd><kbd>↓</kbd> navegar</span>
                    <span><kbd>↵</kbd> abrir</span>
                    <span><kbd>ESC</kbd> cerrar</span>
                </div>
            </div>`;
        resultLinks = [];
        activeIndex = -1;
    }

    function renderLoading() {
        results.innerHTML = '<div class="search-loading"><div class="spinner-border spinner-border-sm"></div> Buscando...</div>';
    }

    function renderNoResults(query) {
        const safe = escapeHtml(query);
        results.innerHTML = `
            <div class="search-empty">
                <i class="bi bi-emoji-frown fs-2"></i>
                <p>No se encontraron resultados para "<strong>${safe}</strong>"</p>
            </div>`;
        resultLinks = [];
    }

    function highlight(text, query) {
        if (!text || !query) return escapeHtml(text || '');
        const re = new RegExp('(' + escapeRegex(query) + ')', 'gi');
        return escapeHtml(text).replace(re, '<mark>$1</mark>');
    }

    function escapeHtml(s) {
        if (!s) return '';
        return String(s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function escapeRegex(s) {
        return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    function renderResults(items, query) {
        if (items.length === 0) { renderNoResults(query); return; }

        // Agrupar por tipo
        const grupos = {};
        items.forEach(r => {
            if (!grupos[r.tipo]) grupos[r.tipo] = [];
            grupos[r.tipo].push(r);
        });

        const orden = ['estudiante', 'profesor', 'grupo', 'materia'];
        const etiquetas = {
            estudiante: 'Estudiantes',
            profesor:   'Profesores',
            grupo:      'Grupos',
            materia:    'Materias',
        };

        let html = '';
        orden.forEach(tipo => {
            if (!grupos[tipo]) return;
            html += `<div class="search-group-label">${etiquetas[tipo]}</div>`;
            grupos[tipo].forEach(r => {
                html += `
                    <a href="${r.url}" class="search-result" data-url="${r.url}">
                        <div class="search-result-icon ${r.color}">
                            <i class="bi ${r.icono}"></i>
                        </div>
                        <div class="search-result-body">
                            <div class="search-result-title">${highlight(r.titulo, query)}</div>
                            <div class="search-result-sub">${highlight(r.subtitulo, query)}</div>
                        </div>
                        <span class="search-result-type">${r.tipo_label}</span>
                    </a>`;
            });
        });

        results.innerHTML = html;
        resultLinks = Array.from(results.querySelectorAll('.search-result'));
        activeIndex = resultLinks.length > 0 ? 0 : -1;
        updateActive();
    }

    function updateActive() {
        resultLinks.forEach((el, i) => {
            el.classList.toggle('active', i === activeIndex);
            if (i === activeIndex) {
                el.scrollIntoView({ block: 'nearest' });
            }
        });
    }

    async function doSearch(query) {
        if (query.length < 2) { renderEmpty(); return; }
        if (query === lastQuery) return;
        lastQuery = query;
        renderLoading();
        try {
            const res = await fetch('/api/buscar-global?q=' + encodeURIComponent(query),
                                    { headers: { 'X-CSRFToken': window.CSRF_TOKEN || '' } });
            if (!res.ok) throw new Error('http ' + res.status);
            const data = await res.json();
            if (lastQuery !== query) return; // ya hay una búsqueda más reciente
            renderResults(data.resultados || [], query);
        } catch (err) {
            results.innerHTML = '<div class="search-loading text-danger">Error al buscar. Intenta de nuevo.</div>';
        }
    }

    // Eventos
    trigger.addEventListener('click', openSearch);

    modal.querySelectorAll('[data-search-close]').forEach(el => {
        el.addEventListener('click', closeSearch);
    });

    input.addEventListener('input', () => {
        const q = input.value.trim();
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => doSearch(q), 200);
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') { closeSearch(); return; }
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (resultLinks.length > 0) {
                activeIndex = (activeIndex + 1) % resultLinks.length;
                updateActive();
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (resultLinks.length > 0) {
                activeIndex = activeIndex <= 0 ? resultLinks.length - 1 : activeIndex - 1;
                updateActive();
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            if (activeIndex >= 0 && resultLinks[activeIndex]) {
                window.location.href = resultLinks[activeIndex].dataset.url;
            }
        }
    });

    // Click en resultado (delegado)
    results.addEventListener('click', (e) => {
        const link = e.target.closest('.search-result');
        if (link) {
            e.preventDefault();
            window.location.href = link.dataset.url;
        }
    });

    // Atajo global Ctrl+K (o ⌘+K en Mac)
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
            e.preventDefault();
            if (modal.classList.contains('open')) closeSearch();
            else openSearch();
        } else if (e.key === '/' && document.activeElement &&
                   ['INPUT', 'TEXTAREA'].indexOf(document.activeElement.tagName) === -1) {
            // Atajo alternativo: tecla "/" cuando no estás escribiendo en un input
            e.preventDefault();
            openSearch();
        }
    });
})();

/* ============================================================
   Toast notifications API
   ============================================================ */
(function () {
    'use strict';

    const container = document.getElementById('toastContainer');
    if (!container) return;

    const ICONS = {
        success: 'bi-check-circle-fill',
        danger:  'bi-x-circle-fill',
        error:   'bi-x-circle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info:    'bi-info-circle-fill',
        primary: 'bi-info-circle-fill',
    };

    function escapeHtml(s) {
        if (!s) return '';
        return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function show(message, opts) {
        opts = opts || {};
        const category = (opts.category || 'info').toLowerCase();
        const duration = opts.duration !== undefined ? opts.duration : 5000;
        const icon = ICONS[category] || ICONS.info;

        const toast = document.createElement('div');
        toast.className = 'app-toast app-toast-' + category;
        toast.innerHTML = `
            <div class="app-toast-icon"><i class="bi ${icon}"></i></div>
            <div class="app-toast-body">${escapeHtml(message)}</div>
            <button class="app-toast-close" aria-label="Cerrar">
                <i class="bi bi-x"></i>
            </button>
            ${duration > 0 ? `<div class="app-toast-progress" style="animation-duration:${duration}ms"></div>` : ''}
        `;

        function dismiss() {
            if (toast.classList.contains('dismissing')) return;
            toast.classList.add('dismissing');
            setTimeout(() => toast.remove(), 250);
        }

        toast.querySelector('.app-toast-close').addEventListener('click', dismiss);

        if (duration > 0) {
            setTimeout(dismiss, duration);
        }

        container.appendChild(toast);
        return { dismiss };
    }

    // API global
    window.Toast = {
        show: show,
        success: (msg, opts) => show(msg, Object.assign({}, opts, { category: 'success' })),
        error:   (msg, opts) => show(msg, Object.assign({}, opts, { category: 'danger' })),
        warning: (msg, opts) => show(msg, Object.assign({}, opts, { category: 'warning' })),
        info:    (msg, opts) => show(msg, Object.assign({}, opts, { category: 'info' })),
    };

    // Procesar flash messages pendientes del backend
    if (window.__pendingToasts && Array.isArray(window.__pendingToasts)) {
        window.__pendingToasts.forEach((t, i) => {
            // Detectar mensajes con credenciales — duración muy larga (60s)
            const msg = (t.message || '').toLowerCase();
            const hasCredentials = msg.includes('contraseña') &&
                                    (msg.includes('usuario') || msg.includes('temporal'));
            const opts = { category: t.category };
            if (hasCredentials) {
                opts.duration = 60000;  // 1 minuto, debe darle tiempo de copiarlas
            }
            setTimeout(() => show(t.message, opts), i * 150);
        });
        window.__pendingToasts = [];
    }
})();

/* ============================================================
   Confirm modal API (reemplaza al confirm() nativo)
   ============================================================ */
(function () {
    'use strict';

    const modal = document.getElementById('confirmModal');
    if (!modal) return;

    const titleEl = modal.querySelector('#confirmModalTitle');
    const textEl = modal.querySelector('#confirmModalText');
    const iconEl = modal.querySelector('#confirmModalIcon');
    const acceptBtn = modal.querySelector('#confirmModalAccept');

    let resolvePromise = null;

    function open(opts) {
        opts = opts || {};
        const variant = opts.variant || 'danger'; // danger|warning|info
        const acceptLabel = opts.acceptLabel || 'Eliminar';
        const cancelLabel = opts.cancelLabel || 'Cancelar';

        titleEl.textContent = opts.title || '¿Confirmar acción?';
        textEl.textContent = opts.message || '';

        iconEl.className = 'confirm-modal-icon ' +
            (variant === 'warning' ? 'warning' : variant === 'info' ? 'info' : '');

        // Iconos según variant
        const iconCls = variant === 'warning' ? 'bi-exclamation-triangle-fill'
            : variant === 'info' ? 'bi-info-circle-fill'
            : 'bi-trash-fill';
        iconEl.innerHTML = `<i class="bi ${iconCls}"></i>`;

        acceptBtn.textContent = acceptLabel;
        acceptBtn.className = 'btn ' +
            (variant === 'warning' ? 'btn-warning' :
             variant === 'info' ? 'btn-primary' : 'btn-danger');

        modal.querySelectorAll('[data-confirm-close]').forEach(b => {
            if (b.tagName === 'BUTTON') b.textContent = cancelLabel;
        });

        modal.classList.add('open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
        setTimeout(() => acceptBtn.focus(), 50);

        return new Promise(resolve => { resolvePromise = resolve; });
    }

    function close(result) {
        modal.classList.remove('open');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        if (resolvePromise) {
            resolvePromise(result);
            resolvePromise = null;
        }
    }

    // Listeners del modal
    modal.querySelectorAll('[data-confirm-close]').forEach(el => {
        el.addEventListener('click', () => close(false));
    });

    acceptBtn.addEventListener('click', () => close(true));

    document.addEventListener('keydown', e => {
        if (modal.classList.contains('open') && e.key === 'Escape') close(false);
    });

    // API global
    window.Confirm = {
        open: open,
        ask: function (message, opts) {
            return open(Object.assign({ message: message }, opts || {}));
        },
    };

    // Interceptar todos los [data-confirm] de la app via event delegation
    // (esto reemplaza al confirm() nativo)
    document.addEventListener('click', async function (e) {
        const trigger = e.target.closest('[data-confirm]');
        if (!trigger) return;

        // Si ya hay un flag de "ya confirmado", deja pasar
        if (trigger.dataset.confirmed === 'yes') {
            trigger.dataset.confirmed = '';
            return;
        }

        e.preventDefault();
        e.stopPropagation();

        const message = trigger.getAttribute('data-confirm');
        const title = trigger.getAttribute('data-confirm-title') || '¿Confirmar acción?';
        const variant = trigger.getAttribute('data-confirm-variant') || 'danger';
        const acceptLabel = trigger.getAttribute('data-confirm-accept') ||
            (variant === 'danger' ? 'Eliminar' : 'Confirmar');

        const ok = await open({
            title: title,
            message: message,
            variant: variant,
            acceptLabel: acceptLabel,
        });

        if (ok) {
            // Marcar como ya confirmado y re-disparar el comportamiento original
            trigger.dataset.confirmed = 'yes';

            // Si es un button dentro de un form, submit el form
            if (trigger.tagName === 'BUTTON' && trigger.form) {
                trigger.form.submit();
            } else if (trigger.tagName === 'A' && trigger.href) {
                window.location.href = trigger.href;
            } else {
                trigger.click();
            }
        }
    }, true); // Captura el evento antes que otros listeners
})();

/* ============================================================
   Detectar cambios sin guardar en formularios
   ============================================================ */
(function () {
    'use strict';

    // Solo formularios con la clase 'track-changes' o data-track-changes
    // Por defecto: todos los <form method="post"> que no sean de búsqueda
    const forms = document.querySelectorAll('form[method="POST"], form[method="post"]');
    const trackedForms = [];

    forms.forEach(form => {
        // Excluir formularios pequeños / de filtro
        if (form.classList.contains('no-track') ||
            form.dataset.trackChanges === 'false') return;

        // Excluir formularios sin inputs significativos (filtros suelen tener pocos)
        const inputs = form.querySelectorAll('input, textarea, select');
        if (inputs.length < 3) return;

        const initial = serializeForm(form);
        let modified = false;
        let submitting = false;

        form.addEventListener('input', () => {
            modified = (serializeForm(form) !== initial);
        });

        form.addEventListener('submit', () => { submitting = true; });

        trackedForms.push({
            form: form,
            isModified: () => modified && !submitting,
        });
    });

    function serializeForm(form) {
        const data = new FormData(form);
        const out = [];
        for (const [k, v] of data.entries()) {
            if (k === 'csrf_token') continue;
            out.push(k + '=' + (typeof v === 'string' ? v : ''));
        }
        return out.sort().join('|');
    }

    if (trackedForms.length === 0) return;

    function hasUnsavedChanges() {
        return trackedForms.some(t => t.isModified());
    }

    // Aviso nativo al cerrar pestaña / navegar fuera
    window.addEventListener('beforeunload', function (e) {
        if (hasUnsavedChanges()) {
            e.preventDefault();
            e.returnValue = '';
            return '';
        }
    });

    // Interceptar clicks en links/botones internos para preguntar
    document.addEventListener('click', async function (e) {
        const link = e.target.closest('a[href]');
        if (!link) return;
        if (link.target === '_blank') return;
        if (link.getAttribute('href').startsWith('#')) return;
        if (link.getAttribute('href').startsWith('javascript:')) return;
        if (link.hasAttribute('data-skip-unsaved')) return;
        if (!hasUnsavedChanges()) return;

        // El usuario tiene cambios — pedir confirmación
        e.preventDefault();
        e.stopPropagation();

        if (window.Confirm) {
            const ok = await window.Confirm.open({
                title: 'Cambios sin guardar',
                message: 'Tienes cambios sin guardar en este formulario. ¿Quieres salir de todas formas? Perderás los cambios.',
                variant: 'warning',
                acceptLabel: 'Salir sin guardar',
                cancelLabel: 'Quedarme',
            });
            if (ok) {
                // Marcar como "submitting" para que beforeunload no dispare otra vez
                trackedForms.forEach(t => { t.form._navigatingAway = true; });
                window.location.href = link.href;
            }
        }
    }, true);
})();

/* ============================================================
   Atajos de teclado globales (estilo Linear/GitHub)
   ============================================================ */
(function () {
    'use strict';

    const shortcutsModal = document.getElementById('shortcutsModal');
    if (!shortcutsModal) return;

    // Tabla de atajos g+letra → url
    const NAV_MAP = {
        'd': '/dashboard/',
        'e': '/estudiantes/',
        'g': '/grupos/',
        'm': '/materias/',
        'v': '/evaluaciones/',
        'a': '/asistencia/',
        'r': '/reportes/',
        'h': '/cuadro-honor/',
        'p': '/profesores/',
    };

    // Mapa de "nuevo" según pathname actual
    const NEW_MAP = [
        { match: /^\/estudiantes/,    url: '/estudiantes/crear' },
        { match: /^\/profesores/,     url: '/profesores/crear' },
        { match: /^\/materias/,       url: '/materias/crear' },
        { match: /^\/grupos/,         url: '/grupos/crear' },
        { match: /^\/evaluaciones/,   url: '/evaluaciones/crear' },
    ];

    let gPressed = false;
    let gTimeout = null;

    function isTyping() {
        const el = document.activeElement;
        if (!el) return false;
        const tag = el.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return true;
        if (el.isContentEditable) return true;
        return false;
    }

    function isModalOpen() {
        return shortcutsModal.classList.contains('open') ||
            (document.getElementById('searchModal')?.classList.contains('open')) ||
            (document.getElementById('confirmModal')?.classList.contains('open'));
    }

    function openShortcuts() {
        shortcutsModal.classList.add('open');
        shortcutsModal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    function closeShortcuts() {
        shortcutsModal.classList.remove('open');
        shortcutsModal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    shortcutsModal.querySelectorAll('[data-shortcuts-close]').forEach(el => {
        el.addEventListener('click', closeShortcuts);
    });

    document.addEventListener('keydown', function (e) {
        // No interceptar si está escribiendo
        if (isTyping()) {
            // Pero Esc siempre cierra el modal
            if (e.key === 'Escape' && shortcutsModal.classList.contains('open')) {
                closeShortcuts();
            }
            return;
        }

        // No interceptar combinaciones con Ctrl/Meta/Alt (excepto las ya manejadas)
        if (e.ctrlKey || e.metaKey || e.altKey) return;

        const key = e.key.toLowerCase();

        // Cerrar atajos modal con Esc
        if (e.key === 'Escape') {
            if (shortcutsModal.classList.contains('open')) {
                closeShortcuts();
                return;
            }
        }

        // Si el modal de atajos está abierto, no procesar más
        if (isModalOpen()) return;

        // Si se presionó "g" recientemente, este es la segunda tecla
        if (gPressed) {
            clearTimeout(gTimeout);
            gPressed = false;
            if (NAV_MAP[key]) {
                e.preventDefault();
                window.location.href = NAV_MAP[key];
                return;
            }
            return; // tecla desconocida después de g, ignorar
        }

        // Atajos de una tecla
        switch (e.key) {
            case '?':
                e.preventDefault();
                openShortcuts();
                break;
            case 't':
                e.preventDefault();
                document.getElementById('themeToggle')?.click();
                break;
            case 'n': {
                // "nuevo" contextual según la página actual
                const path = window.location.pathname;
                const match = NEW_MAP.find(m => m.match.test(path));
                if (match) {
                    e.preventDefault();
                    window.location.href = match.url;
                }
                break;
            }
            case 'g':
                // Iniciar secuencia g+...
                e.preventDefault();
                gPressed = true;
                gTimeout = setTimeout(() => { gPressed = false; }, 1500);
                if (window.Toast) {
                    window.Toast.info('Presiona la siguiente tecla...', { duration: 1500 });
                }
                break;
        }
    });
})();

/* ============================================================
   View Transitions API — transiciones suaves entre páginas
   (Chrome/Edge modernos; degrada silenciosamente en Firefox/Safari)
   ============================================================ */
(function () {
    if (!document.startViewTransition) return;

    // Interceptar links internos para usar view-transitions
    document.addEventListener('click', function (e) {
        const link = e.target.closest('a[href]');
        if (!link) return;
        if (link.target === '_blank') return;
        if (link.hasAttribute('download')) return;
        if (link.getAttribute('href').startsWith('#')) return;
        if (link.getAttribute('href').startsWith('javascript:')) return;
        if (link.getAttribute('href').startsWith('mailto:')) return;

        // Solo URLs del mismo origen
        const url = new URL(link.href, window.location.origin);
        if (url.origin !== window.location.origin) return;

        // Saltarse links que ya tienen otro comportamiento
        if (link.hasAttribute('data-confirm')) return;
        if (link.hasAttribute('data-skip-transition')) return;

        e.preventDefault();
        document.startViewTransition(() => {
            window.location.href = link.href;
        });
    });
})();

/* ============================================================
   Detector de cambios — notificación de actualizaciones
   ============================================================ */
(function () {
    'use strict';

    // Solo activar si hay un usuario logueado (toast container existe)
    if (!document.getElementById('toastContainer')) return;

    let versionInicial = null;
    let yaNotificado = false;
    const INTERVALO = 60000;   // 60 segundos
    const ENDPOINT = '/api/version';

    async function consultarVersion() {
        try {
            const res = await fetch(ENDPOINT, {
                headers: { 'Accept': 'application/json' },
                credentials: 'same-origin'
            });
            if (!res.ok) return null;
            const data = await res.json();
            return data.version;
        } catch (e) {
            // Falla silenciosa si no hay conexión
            return null;
        }
    }

    function mostrarToastActualizacion() {
        if (yaNotificado) return;
        yaNotificado = true;

        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'app-toast app-toast-info app-toast-sticky';
        toast.innerHTML = `
            <div class="app-toast-icon"><i class="bi bi-arrow-clockwise"></i></div>
            <div class="app-toast-body">
                <div class="app-toast-title">Nuevos datos disponibles</div>
                <div class="app-toast-text">Otro usuario hizo cambios. Recarga para ver la información actualizada.</div>
                <div class="app-toast-actions">
                    <button class="btn btn-sm btn-primary" id="toastReload">
                        <i class="bi bi-arrow-clockwise"></i> Recargar
                    </button>
                    <button class="btn btn-sm btn-link app-toast-dismiss" type="button">
                        Más tarde
                    </button>
                </div>
            </div>
            <button class="app-toast-close" aria-label="Cerrar">
                <i class="bi bi-x"></i>
            </button>
        `;

        toast.querySelector('#toastReload').addEventListener('click', () => {
            window.location.reload();
        });

        const dismiss = () => {
            toast.classList.add('dismissing');
            setTimeout(() => toast.remove(), 250);
            // Permitir volver a notificar si hay otro cambio en el futuro
            setTimeout(() => { yaNotificado = false; }, 30000);
        };

        toast.querySelector('.app-toast-close').addEventListener('click', dismiss);
        toast.querySelector('.app-toast-dismiss').addEventListener('click', dismiss);

        container.appendChild(toast);
    }

    async function iniciar() {
        // Capturar la versión inicial al cargar la página
        versionInicial = await consultarVersion();
        if (!versionInicial) return;

        // Polling periódico
        setInterval(async () => {
            // No molestar al usuario si está editando (forms con cambios)
            const editandoForm = Array.from(
                document.querySelectorAll('form')
            ).some(f => f.querySelectorAll('input, textarea, select').length > 3
                && (f._tieneEdiciones || false));
            if (editandoForm) return;

            // Si la pestaña no está visible, no molestar
            if (document.hidden) return;

            const versionActual = await consultarVersion();
            if (versionActual && versionActual !== versionInicial && !yaNotificado) {
                mostrarToastActualizacion();
            }
        }, INTERVALO);
    }

    // Esperar a que la página esté lista
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
})();

/* ============================================================
   Counters animados — cualquier elemento con data-counter
   ============================================================ */
(function () {
    'use strict';

    function animateCounter(el, target, decimals) {
        decimals = decimals || 0;
        const duration = 900;
        const steps = 40;
        const stepTime = duration / steps;
        const stepVal = target / steps;
        let current = 0;
        let i = 0;

        const interval = setInterval(() => {
            i++;
            current += stepVal;
            if (i >= steps) {
                el.textContent = decimals > 0
                    ? target.toFixed(decimals)
                    : Math.round(target);
                clearInterval(interval);
            } else {
                el.textContent = decimals > 0
                    ? current.toFixed(decimals)
                    : Math.round(current);
            }
        }, stepTime);
    }

    function iniciar() {
        document.querySelectorAll('[data-counter]').forEach(el => {
            // Evitar re-animar
            if (el.dataset.counterDone) return;
            el.dataset.counterDone = '1';

            const target = parseFloat(el.dataset.counter);
            const decimals = parseInt(el.dataset.counterDecimals || '0', 10);

            if (!isNaN(target)) {
                setTimeout(() => animateCounter(el, target, decimals), 200);
            }
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', iniciar);
    } else {
        iniciar();
    }
})();

/* ============================================================
   TOUR DE BIENVENIDA — versión simple y robusta
   ============================================================ */
(function () {
    'use strict';

    const TOUR_KEY = 'edutrack-tour-completed-v1';
    const overlay = document.getElementById('tourOverlay');
    if (!overlay) return;

    const popover = document.getElementById('tourPopover');
    const highlight = document.getElementById('tourHighlight');
    const tourNum = document.getElementById('tourStepNum');
    const tourTitle = document.getElementById('tourTitle');
    const tourText = document.getElementById('tourText');
    const tourPrev = document.getElementById('tourPrev');
    const tourNext = document.getElementById('tourNext');
    const tourSkip = document.getElementById('tourSkip');

    const STEPS = [
        {
            title: 'Bienvenido a EduTrack',
            text: 'Te voy a mostrar lo más importante en unos pasos rápidos. Puedes saltar el tour cuando quieras.',
        },
        {
            target: '[data-tour="search"]',
            title: 'Búsqueda rápida (Ctrl + K)',
            text: 'Abre el buscador para encontrar estudiantes, ejecutar acciones rápidas como crear evaluaciones, o ir a cualquier módulo. Es el atajo más útil.',
        },
        {
            target: '[data-tour="theme"]',
            title: 'Cambia el tema',
            text: 'Click aquí para alternar entre modo claro y oscuro. Tu preferencia se guarda automáticamente.',
        },
        {
            target: '#fabHelp',
            title: 'Botón de ayuda',
            text: 'Abajo a la derecha siempre tienes el botón "?". Click ahí para ver todos los atajos de teclado disponibles.',
        },
        {
            title: '¡Listo!',
            text: 'Eso es todo. Recuerda: Ctrl+K para buscar y "?" para ver atajos. ¡A trabajar!',
        },
    ];

    let currentStep = 0;

    function positionFor(targetSelector) {
        // Reset
        popover.style.transform = '';
        popover.style.top = '';
        popover.style.left = '';
        popover.style.right = '';
        popover.style.bottom = '';
        highlight.style.display = 'none';

        if (!targetSelector) {
            // Centrar popover sin highlight
            popover.style.top = '50%';
            popover.style.left = '50%';
            popover.style.transform = 'translate(-50%, -50%)';
            return;
        }

        const el = document.querySelector(targetSelector);
        if (!el) {
            // Si el target no existe, centrar
            popover.style.top = '50%';
            popover.style.left = '50%';
            popover.style.transform = 'translate(-50%, -50%)';
            return;
        }

        const rect = el.getBoundingClientRect();

        // Posicionar el highlight
        highlight.style.display = 'block';
        highlight.style.top = (rect.top - 6) + 'px';
        highlight.style.left = (rect.left - 6) + 'px';
        highlight.style.width = (rect.width + 12) + 'px';
        highlight.style.height = (rect.height + 12) + 'px';

        // Posicionar popover: por defecto debajo, si no cabe arriba
        const popoverW = 380;
        const popoverH = 220;
        const margin = 16;
        const winW = window.innerWidth;
        const winH = window.innerHeight;

        let top, left;

        // Decidir vertical
        if (rect.bottom + popoverH + margin < winH) {
            top = rect.bottom + margin;
        } else if (rect.top - popoverH - margin > 0) {
            top = rect.top - popoverH - margin;
        } else {
            top = margin;  // arriba como fallback
        }

        // Decidir horizontal
        left = rect.left;
        if (left + popoverW > winW - margin) {
            left = winW - popoverW - margin;
        }
        if (left < margin) {
            left = margin;
        }

        popover.style.top = top + 'px';
        popover.style.left = left + 'px';
    }

    function render() {
        const step = STEPS[currentStep];
        if (!step) return finish();

        tourNum.textContent = `${currentStep + 1} / ${STEPS.length}`;
        tourTitle.textContent = step.title;
        tourText.textContent = step.text;

        tourPrev.style.visibility = currentStep === 0 ? 'hidden' : 'visible';
        tourNext.textContent = currentStep === STEPS.length - 1 ? 'Finalizar' : 'Siguiente';

        positionFor(step.target);
    }

    function next() {
        if (currentStep < STEPS.length - 1) {
            currentStep++;
            render();
        } else {
            finish();
        }
    }

    function prev() {
        if (currentStep > 0) {
            currentStep--;
            render();
        }
    }

    function finish() {
        overlay.classList.remove('active');
        localStorage.setItem(TOUR_KEY, '1');
    }

    function start() {
        // Resetear todo antes de empezar
        localStorage.removeItem(TOUR_KEY);
        currentStep = 0;
        overlay.classList.add('active');
        render();
    }

    tourNext.addEventListener('click', next);
    tourPrev.addEventListener('click', prev);
    tourSkip.addEventListener('click', finish);

    // Cerrar con Escape
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && overlay.classList.contains('active')) {
            finish();
        }
    });

    // Cerrar al hacer click fuera del popover
    overlay.addEventListener('click', e => {
        if (e.target === overlay) finish();
    });

    // Reposicionar al cambiar de tamaño
    window.addEventListener('resize', () => {
        if (overlay.classList.contains('active')) {
            positionFor(STEPS[currentStep]?.target);
        }
    });

    // Iniciar automáticamente la primera vez en el dashboard
    const inDashboard = /\/dashboard\/?$/.test(window.location.pathname) ||
                         window.location.pathname === '/';
    if (inDashboard && !localStorage.getItem(TOUR_KEY)) {
        // Esperar a que TODO esté renderizado
        window.addEventListener('load', () => {
            setTimeout(() => {
                if (!localStorage.getItem(TOUR_KEY)) {
                    currentStep = 0;
                    overlay.classList.add('active');
                    render();
                }
            }, 1000);
        });
    }

    // Exponer API global para reiniciar el tour
    window.EduTour = { start, finish };
})();


/* ============================================================
   FAB HELP — botón "?" siempre visible que abre los atajos
   ============================================================ */
(function () {
    'use strict';
    const fab = document.getElementById('fabHelp');
    if (!fab) return;

    fab.addEventListener('click', () => {
        const modal = document.getElementById('shortcutsModal');
        if (modal) modal.classList.add('open');
    });
})();


/* ============================================================
   COMMAND PALETTE — extender el search modal con acciones
   ============================================================ */
(function () {
    'use strict';
    const modal = document.getElementById('searchModal');
    const input = document.getElementById('searchInput');
    if (!modal || !input) return;

    // Definir acciones disponibles
    const ACTIONS = [
        { label: 'Crear nueva evaluación',  url: '/evaluaciones/crear',      icon: 'bi-plus-circle', keywords: 'evaluacion examen tarea proyecto' },
        { label: 'Tomar asistencia hoy',    url: '/asistencia/',             icon: 'bi-calendar-check', keywords: 'asistencia presente ausente' },
        { label: 'Ver estudiantes',         url: '/estudiantes/',            icon: 'bi-mortarboard', keywords: 'estudiantes alumnos lista' },
        { label: 'Ver grupos',              url: '/grupos/',                 icon: 'bi-people', keywords: 'grupos secciones' },
        { label: 'Ver materias',            url: '/materias/',               icon: 'bi-book', keywords: 'materias cursos' },
        { label: 'Cuadro de honor',         url: '/cuadro-honor/',           icon: 'bi-trophy', keywords: 'honor top mejores' },
        { label: 'Generar reportes',        url: '/reportes/',               icon: 'bi-file-earmark-bar-graph', keywords: 'reportes pdf excel boletin' },
        { label: 'Importar estudiantes',    url: '/estudiantes/importar',    icon: 'bi-cloud-arrow-up', keywords: 'importar excel csv' },
        { label: 'Cambiar contraseña',      url: '/auth/cambiar-password',   icon: 'bi-key', keywords: 'contraseña password seguridad' },
        { label: 'Configurar 2FA',          url: '/auth/2fa/config',         icon: 'bi-shield-lock', keywords: '2fa autenticacion doble factor' },
        { label: 'Ver auditoría de accesos', url: '/auth/auditoria/intentos-login', icon: 'bi-shield-check', keywords: 'auditoria intentos login seguridad' },
        { label: 'Reiniciar tour de bienvenida', action: () => window.EduTour && window.EduTour.start(), icon: 'bi-compass', keywords: 'tour ayuda guia inicio' },
        { label: 'Cambiar tema',            action: () => document.getElementById('themeToggle')?.click(), icon: 'bi-moon-stars', keywords: 'tema oscuro claro' },
        { label: 'Cerrar sesión',           url: '/auth/logout',             icon: 'bi-box-arrow-right', keywords: 'logout salir sesion' },
    ];

    // Si existe contenedor de resultados, agregar sección de acciones
    const resultsContainer = document.getElementById('searchResults') ||
                              modal.querySelector('.search-results');
    if (!resultsContainer) return;

    function renderActions(query) {
        const q = (query || '').toLowerCase().trim();
        let acciones = ACTIONS;

        if (q) {
            acciones = ACTIONS.filter(a => {
                const hay = (a.label + ' ' + (a.keywords || '')).toLowerCase();
                return hay.includes(q);
            });
        }

        if (acciones.length === 0) return null;

        const section = document.createElement('div');
        section.className = 'search-section search-actions';
        section.innerHTML = `
            <div class="search-section-title">
                <i class="bi bi-lightning-charge-fill"></i> Acciones
            </div>
        `;

        acciones.slice(0, 6).forEach(a => {
            const item = document.createElement('a');
            item.className = 'search-result search-action-item';
            item.href = a.url || '#';
            item.innerHTML = `
                <div class="search-result-icon"><i class="bi ${a.icon}"></i></div>
                <div class="search-result-body">
                    <div class="search-result-title">${a.label}</div>
                </div>
                <div class="search-result-meta"><i class="bi bi-arrow-return-left"></i></div>
            `;
            if (a.action) {
                item.addEventListener('click', e => {
                    e.preventDefault();
                    modal.classList.remove('open');
                    a.action();
                });
            }
            section.appendChild(item);
        });

        return section;
    }

    // Hook: cuando se abre el modal vacío, mostrar acciones
    const observer = new MutationObserver(() => {
        if (!modal.classList.contains('open')) return;
        // Si no hay query y no hay resultados, mostrar acciones por defecto
        if (!input.value.trim() && !resultsContainer.querySelector('.search-actions')) {
            const actionsSection = renderActions('');
            if (actionsSection) {
                resultsContainer.innerHTML = '';
                resultsContainer.appendChild(actionsSection);
            }
        }
    });
    observer.observe(modal, { attributes: true, attributeFilter: ['class'] });

    // También al escribir: incluir acciones que coincidan
    let lastValue = '';
    input.addEventListener('input', () => {
        const v = input.value.trim();
        if (v === lastValue) return;
        lastValue = v;
        // Esperar a que termine el debounce del search original, luego inyectar acciones
        setTimeout(() => {
            const existing = resultsContainer.querySelector('.search-actions');
            if (existing) existing.remove();
            const actionsSection = renderActions(v);
            if (actionsSection) {
                resultsContainer.insertBefore(actionsSection, resultsContainer.firstChild);
            }
        }, 250);
    });
})();


/* ============================================================
   SKELETON LOADING — placeholders mientras carga
   ============================================================ */
(function () {
    'use strict';

    // Mostrar skeleton durante navegación (page transitions)
    document.addEventListener('click', e => {
        const link = e.target.closest('a[href]');
        if (!link) return;
        if (link.hasAttribute('data-skip-transition')) return;
        if (link.hasAttribute('target')) return;
        if (link.getAttribute('href').startsWith('#')) return;
        if (link.getAttribute('href').startsWith('javascript:')) return;

        const url = new URL(link.href, window.location.origin);
        if (url.origin !== window.location.origin) return;

        // Marcar el contenido principal con skeleton class
        const main = document.querySelector('.app-content, main, .container-fluid');
        if (main && !main.classList.contains('skeleton-loading')) {
            // Dar un pequeño delay para que View Transitions API tome control primero
            setTimeout(() => {
                if (document.visibilityState === 'visible') {
                    main.classList.add('skeleton-loading');
                }
            }, 100);
        }
    });
})();


/* ============================================================
   Credentials Modal — detecta flashes con credenciales y los muestra
   en un modal persistente con botones de copiar
   ============================================================ */
(function () {
    'use strict';

    const modal = document.getElementById('credsModal');
    if (!modal) return;

    const usuarioEl = document.getElementById('credsUsuario');
    const passEl    = document.getElementById('credsPassword');
    const introEl   = document.getElementById('credsModalIntro');

    function open(username, password, intro) {
        usuarioEl.textContent = username || '—';
        passEl.textContent    = password || '—';
        if (intro) introEl.textContent = intro;
        modal.classList.add('open');
    }

    function close() {
        modal.classList.remove('open');
    }

    // Cerrar
    modal.querySelectorAll('[data-creds-close]').forEach(el => {
        el.addEventListener('click', close);
    });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && modal.classList.contains('open')) close();
    });

    // Copiar individual
    modal.querySelectorAll('[data-copy-target]').forEach(btn => {
        btn.addEventListener('click', async () => {
            const target = document.getElementById(btn.dataset.copyTarget);
            if (!target) return;
            try {
                await navigator.clipboard.writeText(target.textContent.trim());
                const i = btn.querySelector('i');
                const original = i.className;
                i.className = 'bi bi-check2';
                btn.classList.add('btn-success');
                btn.classList.remove('btn-outline-secondary');
                setTimeout(() => {
                    i.className = original;
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-outline-secondary');
                }, 1500);
            } catch {}
        });
    });

    // Copiar ambas
    const copyBothBtn = modal.querySelector('[data-copy-both]');
    if (copyBothBtn) {
        copyBothBtn.addEventListener('click', async () => {
            const text = `Usuario: ${usuarioEl.textContent.trim()}\nContraseña: ${passEl.textContent.trim()}`;
            try {
                await navigator.clipboard.writeText(text);
                const original = copyBothBtn.innerHTML;
                copyBothBtn.innerHTML = '<i class="bi bi-check2"></i> Copiado';
                setTimeout(() => { copyBothBtn.innerHTML = original; }, 1500);
            } catch {}
        });
    }

    // === Detectar flashes con credenciales y abrir modal ===
    // Patrones tolerantes a varios formatos:
    //   - 'usuario "X" ... contraseña ... "Y"'
    //   - 'usuario: X ... contraseña: Y'
    //   - 'Usuario X · Contraseña Y'
    function parsearCredenciales(mensaje) {
        if (!mensaje) return null;
        const lower = mensaje.toLowerCase();
        if (!lower.includes('contraseña') ||
            !(lower.includes('usuario') || lower.includes('temporal'))) {
            return null;
        }

        // Match: usuario "X" ... contraseña ... "Y"
        const matchQuoted = mensaje.match(
            /usuario[^"]*"([^"]+)"[^"]*contraseña[^"]*"([^"]+)"/i
        );
        if (matchQuoted) {
            return { username: matchQuoted[1], password: matchQuoted[2] };
        }

        // Match sin comillas pero con dos puntos
        const matchColon = mensaje.match(
            /usuario:\s*([^\s,·]+)[\s\S]*contraseña[^:]*:\s*([^\s,·]+)/i
        );
        if (matchColon) {
            return { username: matchColon[1], password: matchColon[2] };
        }

        return null;
    }

    // Reemplazar el procesamiento original: si detecta creds, abre modal
    // en vez de mostrar toast. El toast original ya muestra el mensaje breve.
    const originalToasts = window.__pendingToasts;
    if (originalToasts && Array.isArray(originalToasts)) {
        // Limpiar (ya fueron procesados por toast)
        // Pero buscar credenciales para abrir modal además
        let credsToShow = null;
        for (const t of originalToasts) {
            const creds = parsearCredenciales(t.message);
            if (creds) {
                credsToShow = creds;
                break;  // mostrar solo el primero
            }
        }
        if (credsToShow) {
            // Pequeño delay para que el toast aparezca antes
            setTimeout(() => {
                open(credsToShow.username, credsToShow.password);
            }, 400);
        }
    }
    // Si hay flash message con error, agrega la clase
if (document.querySelector('.alert-danger, [data-category="danger"]')) {
    document.querySelector('.login-card')?.classList.add('has-error');
}

    // API global para abrirlo manualmente
    window.CredsModal = { open, close };
    
})();
(function() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            const btn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (!btn || btn.disabled) return;
            const originalText = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span> Procesando...';
            // Restaurar tras 8s por si algo falla
            setTimeout(() => {
                btn.disabled = false;
                btn.innerHTML = originalText;
            }, 8000);
        });
    });
})();



/* ============================================================
   Navbar scroll effect — intensifica el blur al hacer scroll
   ============================================================ */
(function() {
    const navbar = document.querySelector('.navbar, header.navbar, .app-navbar');
    if (!navbar) return;
    
    function onScroll() {
        if (window.scrollY > 8) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
    
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();  // estado inicial
})();

/* ============================================================
   Sidebar Collapsible — con persistencia en localStorage
   ============================================================ */
(function() {
    const sidebar = document.querySelector('.sidebar, aside.sidebar, .app-sidebar');
    if (!sidebar) return;

    // === Crear el botón de toggle si no existe ===
    let toggleBtn = sidebar.querySelector('.sidebar-toggle');
    if (!toggleBtn) {
        toggleBtn = document.createElement('button');
        toggleBtn.className = 'sidebar-toggle';
        toggleBtn.type = 'button';
        toggleBtn.setAttribute('aria-label', 'Colapsar menú');
        toggleBtn.innerHTML = `
            <svg viewBox="0 0 12 12" fill="none">
                <path d="M7.5 3 L4.5 6 L7.5 9" stroke="currentColor"
                      stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        `;
        sidebar.appendChild(toggleBtn);
    }

    // === Agregar tooltips automáticos a los links ===
    sidebar.querySelectorAll('a, .nav-link').forEach(link => {
        if (!link.dataset.tooltip) {
            const text = link.textContent.trim();
            if (text) link.dataset.tooltip = text;
        }
    });

    // === Estado: leer de localStorage ===
    const STORAGE_KEY = 'edutrack:sidebar:collapsed';
    const isMobile = () => window.innerWidth <= 768;

    function isCollapsed() {
        if (isMobile()) return false; // en móvil siempre es por overlay
        return localStorage.getItem(STORAGE_KEY) === '1';
    }

    function setCollapsed(collapsed) {
        if (isMobile()) return;
        if (collapsed) {
            sidebar.classList.add('is-collapsed');
            localStorage.setItem(STORAGE_KEY, '1');
            toggleBtn.setAttribute('aria-label', 'Expandir menú');
        } else {
            sidebar.classList.remove('is-collapsed');
            localStorage.setItem(STORAGE_KEY, '0');
            toggleBtn.setAttribute('aria-label', 'Colapsar menú');
        }
    }

    // === Aplicar estado inicial ===
    if (isCollapsed()) {
        sidebar.classList.add('is-collapsed');
    }

    // === Toggle al click ===
    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        setCollapsed(!sidebar.classList.contains('is-collapsed'));
    });

    // === Atajo de teclado: Cmd/Ctrl + B ===
    document.addEventListener('keydown', (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
            e.preventDefault();
            setCollapsed(!sidebar.classList.contains('is-collapsed'));
        }
    });

    // === Mobile: overlay para cerrar al hacer click fuera ===
    if (isMobile()) {
        // Crear overlay si no existe
        let overlay = document.querySelector('.sidebar-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'sidebar-overlay';
            sidebar.parentNode.insertBefore(overlay, sidebar.nextSibling);
        }

        // Botón hamburguesa en navbar (si tienes)
        const mobileMenuBtn = document.querySelector(
            '.navbar-toggler, .mobile-menu-btn, [data-toggle="sidebar"]'
        );
        if (mobileMenuBtn) {
            mobileMenuBtn.addEventListener('click', () => {
                sidebar.classList.toggle('is-mobile-open');
                overlay.classList.toggle('is-active');
            });
        }

        // Click en overlay cierra
        overlay.addEventListener('click', () => {
            sidebar.classList.remove('is-mobile-open');
            overlay.classList.remove('is-active');
        });

        // Click en un link del sidebar cierra
        sidebar.querySelectorAll('a').forEach(a => {
            a.addEventListener('click', () => {
                sidebar.classList.remove('is-mobile-open');
                overlay.classList.remove('is-active');
            });
        });
    }

    // === Re-evaluar al cambiar tamaño de ventana ===
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (isMobile()) {
                // En móvil, quitar el estado de colapso desktop
                sidebar.classList.remove('is-collapsed');
            } else if (isCollapsed()) {
                sidebar.classList.add('is-collapsed');
            }
        }, 150);
    });
})();

