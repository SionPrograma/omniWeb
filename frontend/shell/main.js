document.addEventListener('DOMContentLoaded', () => {
    // --- Phase 0: Emergency UI Bootstrap (Mission 36) ---
    const loadPlaceholder = document.getElementById('js-load-placeholder');
    if (loadPlaceholder) loadPlaceholder.remove();

    // --- OMNI ONBOARDING INFRASTRUCTURE ---
    const onboardingScript = document.createElement('script');
    onboardingScript.src = '/shell/onboarding_manager.js?v=v1_infra';
    document.head.appendChild(onboardingScript);

    onboardingScript.onload = () => {
        if (window.onboardingManager) window.onboardingManager.init();
    };

    // --- OMNI SAFE-MODE CACHE CLEANUP ---
    const CACHE_RESET_ID = "omni_v6_mobile_safe";
    try {
        if (localStorage.getItem("omni_cache_reset") !== CACHE_RESET_ID) {
            if (sessionStorage.getItem("omni_reset_attempted")) {
                console.warn("[SAFE_MODE] Persistent storage failed. Aborting reset loop.");
            } else {
                sessionStorage.setItem("omni_reset_attempted", "true");
                console.warn("[SAFE_MODE] Cache/Storage inconsistency detected. Purging...");

                if (navigator.serviceWorker) {
                    navigator.serviceWorker.getRegistrations().then(regs => {
                        for (let r of regs) r.unregister();
                    });
                }
                if (window.caches) {
                    caches.keys().then(names => {
                        for (let n of names) caches.delete(n);
                    });
                }
                localStorage.removeItem("omni_chat_history_v1");
                localStorage.setItem("omni_cache_reset", CACHE_RESET_ID);
                console.warn("[SAFE_MODE] Reset complete. Forcing clean reload...");
                setTimeout(() => {
                    window.location.search = `?reset_v=${Date.now()}`;
                }, 500);
                return;
            }
        }
    } catch (e) {
        console.warn("[SAFE_MODE] Reset guard failed.", e);
    }

    // DOM Elements
    const aiHostView = document.getElementById('ai-host-view');
    const chipView = document.getElementById('active-chip-view');
    const chipFrame = document.getElementById('chip-frame');
    const chipTitle = document.getElementById('active-chip-title');
    const closeChipBtn = document.getElementById('close-chip');

    const launcherOverlay = document.getElementById('launcher-overlay');
    const openLauncherBtn = document.getElementById('open-launcher');
    const closeLauncherBtn = document.getElementById('close-launcher');
    const launcherItems = document.querySelectorAll('.chip-launcher-item');

    const navItems = document.querySelectorAll('.nav-item');
    const contextPanel = document.getElementById('context-panel');

    // --- Phase 86: I18N Frontend Bridge (Block 02 Shell I18n) ---
    window.omniI18n = {
        ctx: { ui_language: 'es' },
        translations: {},
        fallback: {},
        loaded: false
    };

    function t(key, params = {}) {
        const keys = key.split('.');
        const resolve = (obj, path) => path.reduce((prev, curr) => prev && prev[curr], obj);

        // 1. Try Target
        let val = resolve(window.omniI18n.translations, keys);
        // 2. Try Fallback
        if (val === undefined) val = resolve(window.omniI18n.fallback, keys);

        if (val === undefined) return `[MISSING: ${key}]`;

        // Handle params
        let result = String(val);
        Object.entries(params).forEach(([k, v]) => {
            result = result.replace(`{${k}}`, v);
        });
        return result;
    }
    window.t = t;

    function applyI18n() {
        // Text Content
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = t(key);
        });
        // Attributes (e.g. data-i18n-attr="placeholder:shell.input.placeholder")
        document.querySelectorAll('[data-i18n-attr]').forEach(el => {
            const mapping = el.getAttribute('data-i18n-attr');
            if (!mapping) return;
            const [attr, key] = mapping.split(':');
            if (attr && key) el.setAttribute(attr, t(key));
        });
        console.log("[I18N] Shell applied.");
    }

    // --- Phase 86.1: Timezone / Region Normalization (Block 03) ---
    window.omniTime = {
        format: (val, options = {}) => {
            if (!val) return '-';
            const date = new Date(val);
            if (isNaN(date.getTime())) return val; // Honest fallback

            const defaultOptions = {
                timeZone: window.omniI18n.ctx.timezone || 'UTC',
                year: 'numeric', month: 'short', day: 'numeric',
                hour: '2-digit', minute: '2-digit'
            };

            try {
                return new Intl.DateTimeFormat(window.omniI18n.ctx.locale_code || 'es-ES', {
                    ...defaultOptions,
                    ...options
                }).format(date);
            } catch (e) {
                console.warn("[OMNI_TIME] Formatting error:", e);
                return date.toISOString(); // Safest truth
            }
        }
    };

    async function initI18n() {
        try {
            console.log("[I18N] Contacting Core for locale...");
            const res = await fetch('/api/v1/ai-host/locale');
            const data = await res.json();
            if (data.status === 'success') {
                window.omniI18n.ctx = data.context;
                window.omniI18n.translations = data.translations;
                window.omniI18n.fallback = data.fallback;

                // Auto-detect & Sync Timezone/Region if not explicitly set
                const clientTZ = Intl.DateTimeFormat().resolvedOptions().timeZone;
                const clientLocale = navigator.language || 'es-ES';

                if (window.omniI18n.ctx.timezone !== clientTZ || window.omniI18n.ctx.locale_code !== clientLocale) {
                    console.log("[I18N] Timezone drift detected, syncing...", clientTZ);
                    const syncRes = await fetch('/api/v1/ai-host/locale', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            ...window.omniI18n.ctx,
                            timezone: clientTZ,
                            locale_code: clientLocale
                        })
                    });
                    const syncData = await syncRes.json();
                    if (syncData.status === 'success') {
                        window.omniI18n.ctx = syncData.context;
                    }
                }

                window.omniI18n.loaded = true;
                applyI18n();
            }
        } catch (e) {
            console.warn("[I18N] Initialization failed. Staying in safety fallback ES.", e);
        }
    }
    initI18n();

    const shellInput = document.getElementById('shell-input');
    const shellForm = document.getElementById('shell-input-form');
    const sendBtn = document.getElementById('send-command');
    const voiceBtn = document.getElementById('voice-command');
    const chatLog = document.getElementById('chat-log');
    const closeContextBtn = document.getElementById('close-context');

    if (shellInput) {
        shellInput.addEventListener('input', () => {
            shellInput.classList.remove('input-error');
        });
    }

    if (closeContextBtn) {
        closeContextBtn.addEventListener('click', () => {
            toggleContext(false);
            navItems.forEach(n => n.classList.remove('active'));
            document.querySelector('[data-view="chat"]').classList.add('active');
        });
    }

    // --- State ---
    let activeView = 'chat';

    // --- Onboarding Greeting ---
    function initGreeting() {
        // Show suggestion chips on first load
        showSuggestionChips();
        const fallback = "¿En qué puedo ayudarte hoy?";
        const urlParams = new URLSearchParams(window.location.search);
        const inviteToken = urlParams.get('invite') || urlParams.get('beta');
        const browser_lang = (navigator.language || 'es').split('-')[0];

        // Una sola voz: Greeting oficial
        addMessage(fallback, 'ai');

        // Background check (Solo si el usuario interactúa, para no "contaminar" el arranque)
        fetch('/api/v1/onboarding/greeting', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: "Hola", browser_lang, invite_token: inviteToken })
        }).catch(err => console.debug("Greeting background check deferred."));
    }

    // --- Persistent History Rehydration ---
    const historyFound = loadHistory();
    if (!historyFound) {
        initGreeting();
    } else {
        if (window.updateCapabilities) window.updateCapabilities();
    }

    // --- Deep Link Handling (Phase 14) ---
    function handleDeepLink() {
        const urlParams = new URLSearchParams(window.location.search);
        const view = urlParams.get('view');
        const tab = urlParams.get('tab');

        if (view) {
            if (view === 'mission' && window.creatorEnv) {
                window.creatorEnv.switchView('mission');
                if (tab) {
                    window.creatorEnv.currentTab = tab;
                    document.querySelectorAll('.cockpit-tab').forEach(t => {
                        t.classList.toggle('active', t.dataset.tab === tab);
                    });
                    window.creatorEnv.renderCockpit();
                }
            } else if (view === 'chat') {
                if (window.creatorEnv) window.creatorEnv.switchView('chat');
            }
        }
    }
    setTimeout(handleDeepLink, 1000);

    function setLauncherActive(active) {
        const isActive = active !== undefined ? active : !launcherOverlay.classList.contains('active');
        launcherOverlay.classList.toggle('active', isActive);
        openLauncherBtn.classList.toggle('active', isActive);
        document.body.classList.toggle('launcher-active', isActive);
        return isActive;
    }

    window.omniShell = {
        closeLauncher: () => setLauncherActive(false),
        toggleContext: toggleContext,
        setLauncherActive: setLauncherActive,
        addInput: (text) => {
            if (shellInput) {
                shellInput.value = text;
                processCommand();
            }
        }
    };

    openLauncherBtn.addEventListener('click', () => {
        if (window.creatorEnv) {
            window.creatorEnv.switchView('launcher');
        } else {
            setLauncherActive();
        }
    });

    if (closeLauncherBtn) {
        closeLauncherBtn.addEventListener('click', () => {
            setLauncherActive(false);
        });
    }

    launcherItems.forEach(item => {
        item.addEventListener('click', () => {
            if (item.classList.contains('disabled')) return;

            const url = item.getAttribute('data-url');
            const view = item.getAttribute('data-view');
            const title = item.getAttribute('data-chip');

            if (view && window.creatorEnv) {
                window.creatorEnv.switchView(view);
                if (view === 'mission') {
                    window.creatorEnv.currentTab = 'copilot'; // Preference for Copilot chip
                    window.creatorEnv.renderCockpit();
                }
            } else if (url) {
                launchChip(url, title);
            }
            setLauncherActive(false);

        });
    });

    // --- Chip Management ---
    function launchChip(url, title) {
        console.log(`Launching chip: ${title} at ${url}`);
        chipTitle.innerText = `Chip: ${title.charAt(0).toUpperCase() + title.slice(1)}`;
        chipFrame.src = url;

        // Use Global State Machine to close competing views
        if (window.creatorEnv) {
            window.creatorEnv.switchView('chip-view-active');
        } else {
            chipView.classList.add('active');
            aiHostView.classList.remove('active');
        }
        chipView.classList.add('active'); // Ensure it stays active
    }

    closeChipBtn.addEventListener('click', () => {
        chipView.classList.remove('active');
        if (window.creatorEnv) {
            window.creatorEnv.switchView('chat');
        } else {
            aiHostView.classList.add('active');
        }
        setTimeout(() => {
            chipFrame.src = ''; // Clear iframe after transition
        }, 400);
    });

    // --- Navigation Logic (Unified) ---
    navItems.forEach(nav => {
        nav.addEventListener('click', () => {
            const view = nav.getAttribute('data-view');
            if (!view) return;

            // Route everything through the Global State Machine if available
            if (window.creatorEnv && typeof window.creatorEnv.switchView === 'function') {
                window.creatorEnv.switchView(view);
            } else {
                // Fallback basic logic
                navItems.forEach(n => n.classList.remove('active'));
                nav.classList.add('active');
                if (view === 'context') toggleContext(true);
                else toggleContext(false);
            }
        });
    });

    function toggleContext(show) {
        if (show) {
            setLauncherActive(false);
            contextPanel.classList.add('active');
            activeView = 'context';
        } else {
            contextPanel.classList.remove('active');
        }
    }

    // --- Interactive Drag for Context Panel ---
    let ctxTouchStartX = 0;
    let ctxCurrentX = 0;
    let isCtxDragging = false;

    contextPanel.addEventListener('touchstart', (e) => {
        ctxTouchStartX = e.touches[0].clientX;
        isCtxDragging = true;
        contextPanel.style.transition = 'none';
    }, { passive: true });

    contextPanel.addEventListener('touchmove', (e) => {
        if (!isCtxDragging) return;
        const touchX = e.touches[0].clientX;
        ctxCurrentX = touchX - ctxTouchStartX;

        // Only allow dragging to the right (close)
        if (ctxCurrentX > 0) {
            contextPanel.style.transform = `translateX(${ctxCurrentX}px)`;
        }
    }, { passive: true });

    contextPanel.addEventListener('touchend', (e) => {
        if (!isCtxDragging) return;
        isCtxDragging = false;
        contextPanel.style.transition = '';

        if (ctxCurrentX > 100) {
            toggleContext(false);
            navItems.forEach(n => n.classList.remove('active'));
            document.querySelector('[data-view="chat"]').classList.add('active');
        } else {
            contextPanel.style.transform = '';
        }
        ctxCurrentX = 0;
    }, { passive: true });

    let touchStartY = 0; // Guard for strict mode
    launcherOverlay.addEventListener('touchstart', (e) => {
        touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    launcherOverlay.addEventListener('touchend', (e) => {
        const touchEndY = e.changedTouches[0].screenY;
        if (touchEndY - touchStartY > 100) { // Swipe Down to close launcher
            setLauncherActive(false);
        }
    }, { passive: true });


    // Handle virtual keyboard orientation/resize
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', () => {
            const inputBar = document.querySelector('.input-bar');
            if (inputBar) {
                const layoutHeight = window.visualViewport.height;
                const windowHeight = window.innerHeight;

                // If the visible height is significantly less than window height, keyboard is likely open
                if (windowHeight - layoutHeight > 150) {
                    document.body.classList.add('keyboard-open');
                    // Move the input bar above the keyboard
                    inputBar.style.bottom = `${(windowHeight - layoutHeight) + 10}px`;
                    // Scroll to bottom to keep messages visible
                    setTimeout(scrollToBottom, 100);
                } else {
                    document.body.classList.remove('keyboard-open');
                    inputBar.style.bottom = ''; // Revert to CSS
                    setTimeout(scrollToBottom, 100);
                }
            }
        });
    }

    // --- Chat / Command Logic ---
    function scrollToBottom(force = false) {
        const threshold = 150; // tolerance in px
        const isNearBottom = (aiHostView.scrollHeight - aiHostView.scrollTop - aiHostView.clientHeight) < threshold;

        if (force || isNearBottom) {
            setTimeout(() => {
                aiHostView.scrollTo({
                    top: aiHostView.scrollHeight,
                    behavior: 'smooth'
                });
            }, 100);
        }
    }

    function addMessage(text, sender = 'ai', forceScroll = false, shouldSave = true, payload = null) {
        if (!text) return;
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

        // --- ADVANCED ACTION BAR & BUBBLE ---
        const content = renderDiff(text);
        let innerHTML = "";

        if (sender === 'ai') {
            const speechText = text.replace(/[*#`]/g, '').trim();
            // Sanitize for attribute usage (sanitize both single and double quotes)
            const shareText = (speechText.length > 100 ? speechText.substring(0, 100) + '...' : speechText)
                .replace(/'/g, "\\'")
                .replace(/"/g, '&quot;');

            innerHTML += `
            <div class="msg-actions top">
                <button class="replay-btn" title="Repetir audio" onclick="window.voice.speak(\`${speechText.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`)">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 5L6 9H2v6h4l5 4V5z"></path>
                        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
                    </svg>
                </button>
                <div class="msg-feedback">
                    <button class="action-btn" title="Útil" onclick="this.classList.toggle('active')">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                        </svg>
                    </button>
                    <button class="action-btn" title="No útil" onclick="this.classList.toggle('active')">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                            <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h3a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-3"></path>
                        </svg>
                    </button>
                </div>
                <button class="action-btn" title="Compartir" onclick="navigator.share && navigator.share({title: 'Omni Output', text: '${shareText}'})">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8M16 6l-4-4-4 4M12 2v13"/>
                    </svg>
                </button>
            </div>`;

            if (payload && payload.tactical_overlay) {
                // Block 01: Suppress tactical complexity for PUBLIC mode
                const isPublic = document.body.classList.contains('user-mode');
                if (!isPublic) {
                    innerHTML += renderTacticalOverlay(payload.tactical_overlay);
                } else {
                    console.info("[PUBLIC_MODE] Tactical overlay suppressed from chat bubble.");
                }
            }
        }

        innerHTML += `<div class="msg-bubble">${content}</div>`;
        msgDiv.innerHTML = innerHTML;

        chatLog.appendChild(msgDiv);
        scrollToBottom(forceScroll || sender === 'user');

        if (shouldSave && sender !== 'typing') {
            saveHistory(text, sender);
        }
    }

    function saveHistory(text, sender) {
        try {
            const history = JSON.parse(localStorage.getItem("omni_chat_history_v1") || "[]");
            history.push({ text, sender, timestamp: Date.now() });
            // Keep last 100 for UI performance
            if (history.length > 100) history.shift();
            localStorage.setItem("omni_chat_history_v1", JSON.stringify(history));
        } catch (e) { console.warn("Save history failed:", e); }
    }

    function loadHistory() {
        try {
            const historyStr = localStorage.getItem("omni_chat_history_v1");
            if (historyStr) {
                const history = JSON.parse(historyStr);
                if (history && history.length > 0) {
                    chatLog.innerHTML = "";
                    history.forEach(m => {
                        addMessage(m.text, m.sender, false, false);
                    });
                    return true;
                }
            }
        } catch (e) {
            console.warn("Load history failed:", e);
        }
        return false;
    }

    // --- DIFF RENDERER HELPERS ---
    function renderDiff(text) {
        if (!text || typeof text !== 'string') return text;

        const diffMarker = "\n---";
        const parts = text.split(diffMarker);

        let mainText = parts[0];
        let diffPart = parts.length > 1 ? parts.slice(1).join(diffMarker).trim() : "";

        // Manual fallback if no marker but contains diff patterns
        if (!diffPart && (text.includes('\n-') || text.includes('\n+')) && text.includes('@@')) {
            diffPart = text;
            mainText = "";
        }

        let html = mainText
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\n/g, '<br/>');

        if (diffPart) {
            html += `<div class="diff-container">`;
            const lines = diffPart.split('\n');
            lines.forEach(line => {
                let cls = "";
                if (line.startsWith('---') || line.startsWith('+++')) cls = "header";
                else if (line.startsWith('@@')) cls = "info";
                else if (line.startsWith('-')) cls = "removed";
                else if (line.startsWith('+')) cls = "added";

                if (cls) {
                    html += `<div class="diff-line ${cls}">${escapeHtml(line)}</div>`;
                } else if (line.trim()) {
                    html += `<div class="diff-line">${escapeHtml(line)}</div>`;
                }
            });
            html += `</div>`;
        }

        return html;
    }

    function renderTacticalOverlay(overlay) {
        if (!overlay) return "";
        const riskClass = (overlay.risk_state || "low").toLowerCase();

        let surfaceHtml = "";
        if (overlay.affected_surface) {
            surfaceHtml = `<div class="tactical-surface">` +
                overlay.affected_surface.map(s => `<span class="surface-badge">${s}</span>`).join("") +
                `</div>`;
        }

        let pathHtml = "";
        if (overlay.execution_path) {
            pathHtml = `<div class="tactical-stepper">` +
                overlay.execution_path.map(step => {
                    const statusClass = step.status === "COMPLETADO" ? "completed" :
                        step.status === "PROCESANDO" ? "processing" :
                            step.status === "BLOQUEADO" ? "blocked" : "";
                    return `<div class="tactical-step ${statusClass}">
                        <strong>${step.name}</strong><br/>
                        <span style="font-size: 0.7rem; opacity: 0.7">${step.detail}</span>
                    </div>`;
                }).join("") +
                `</div>`;
        }

        let overrideHtml = "";
        if (overlay.lock_info) {
            overrideHtml = `
            <div class="tactical-override">
                <div class="tactical-lock-reason">
                    <strong>SEGURIDAD:</strong> ${overlay.lock_info.reason}
                </div>
                <div class="tactical-actions">
                    ${(overlay.actions || []).map(a => `
                        <button class="tactical-btn ${a.style || ''}" 
                                onclick="window.omniManualAction('${overlay.mission_id}', '${a.action}', '${a.label}')">
                            ${a.label}
                        </button>
                    `).join('')}
                </div>
                <div class="tactical-authority-gate">
                    GATE: ${overlay.lock_info.authority_gate || 'MANUAL_REQUIRED'}
                </div>
            </div>`;
        }

        // CAPA 4: Session Status (Phase 82)
        let authorityHtml = "";
        if (overlay.authority_info && overlay.authority_info.active) {
            authorityHtml = `<div class="authority-status active">AUTORIDAD ACTIVA (EXPIRA: ${overlay.authority_info.expires_at.split('T')[1].substring(0, 5)})</div>`;
        } else if (overlay.authority_info && overlay.authority_info.reason === 'EXPIRED') {
            authorityHtml = `<div class="authority-status" style="color:#ff3232;">SESIÓN EXPIRADA</div>`;
        }

        // CAPA 3: Audit Trail (Phase 82)
        let auditHtml = "";
        if (overlay.audit_trail && overlay.audit_trail.length > 0) {
            auditHtml = `
                <div class="tactical-audit">
                    <div class="audit-title">AUDIT TRAIL / GOBERNANZA</div>
                    ${overlay.audit_trail.map(e => `
                        <div class="audit-entry">
                            <span class="audit-ts">${e.ts}</span>
                            <span class="audit-type">${e.type}</span>
                            <span class="audit-msg">${e.msg}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        return `
        <div class="tactical-card">
            <div class="tactical-header">
                <div class="tactical-intent">
                    <span class="tactical-branding">${overlay.branding || 'OmniWeb Core'}</span>
                    <span class="tactical-goal">${overlay.understood_intent || 'Misión Técnica'}</span>
                </div>
                <span class="risk-badge ${riskClass}">${overlay.risk_state || 'BAJO'}</span>
            </div>
            ${authorityHtml}
            ${surfaceHtml}
            ${pathHtml}
            ${overrideHtml}
            <div class="tactical-next-action">
                ${overlay.next_action || 'Esperando interacción...'}
            </div>
            ${auditHtml}
            ${overlay.global_governance ? renderGovernanceDashboard(overlay.global_governance) : ''}
        </div>`;
    }

    function renderGovernanceDashboard(snapshot) {
        if (!snapshot || snapshot.length === 0) return "";

        const rows = snapshot.map(m => {
            const urgencyClass = `urgency-${m.urgency}`;
            const stateLabel = m.governance_state.replace(/_/g, ' ');
            const authStatus = m.authority.active ?
                `<span class="auth-tag active">SESIÓN ACTIVA</span>` :
                (m.governance_state === "SESSION_EXPIRED" ? `<span class="auth-tag expired">EXPIRADA</span>` : "");

            const missionName = m.name.length > 30 ? m.name.substring(0, 27) + '...' : m.name;

            const quickActionsHtml = (m.quick_actions || []).map(a => `
                <button class="quick-action-btn level-${a.level || 'safe'}" 
                        onclick="event.stopPropagation(); window.omniRunQuickAction('${m.mission_id}', '${a.id}', '${a.label}', ${!!a.requires_pin}, ${!!a.requires_confirmation})">
                    <span class="action-icon">${a.icon || '⚡'}</span> ${a.label}
                </button>
            `).join('');

            return `
                <div class="gov-row ${urgencyClass}" onclick="window.omniSwitchMission ? window.omniSwitchMission('${m.mission_id}') : console.log('Mission switch:', '${m.mission_id}')">
                    <div class="gov-mission-info">
                        <div class="gov-mission-name">${missionName}</div>
                        <div class="gov-mission-id">${m.mission_id.substring(0, 8)}...</div>
                    </div>
                    <div class="gov-state-block">
                        <div class="gov-state-badge">${stateLabel}</div>
                        ${authStatus}
                    </div>
                    <div class="gov-event-info">
                        ${m.latest_event ? `
                            <span class="event-ts">${m.latest_event.ts}</span>
                            <span class="event-msg">${m.latest_event.msg}</span>
                        ` : '<span class="event-none">Sin eventos tácticos</span>'}
                    </div>
                    <div class="gov-actions-container">
                        ${quickActionsHtml}
                    </div>
                </div>
            `;
        }).join('');

        return `
            <div class="gov-dashboard">
                <div class="gov-dashboard-header">
                    OPERACIÓN GLOBAL / GOBERNANZA
                </div>
                <div class="gov-table">
                    ${rows}
                </div>
            </div>
        `;
    }

    // --- MISSION MANUAL OVERRIDE HANDLERS ---
    // --- MISSION CONTROL QUICK ACTIONS (Unidad 83) ---
    window.omniRunQuickAction = function (missionId, actionId, label, requiresPin, requiresConfirmation) {
        console.log(`[MISSION_CONTROL] Action triggered: ${actionId} for mission ${missionId}`);

        if (requiresConfirmation && !confirm(`¿Está seguro de ejecutar "${label}"?`)) {
            return;
        }

        if (requiresPin) {
            const pin = prompt(`"${label}" requiere autorización del Creador.\nIngrese su PIN:`);
            if (!pin) return;

            // Dispatch governed action command
            const cmd = `mission: governed_action ${actionId} mission_id ${missionId} PIN ${pin}`;
            shellInput.value = cmd;
            processCommand();
            return;
        }

        // Direct commands based on actionId
        let command = "";
        switch (actionId) {
            case 'switch_focus':
                if (window.omniSwitchMission) window.omniSwitchMission(missionId);
                return;
            case 'pause_mission':
                command = `mission: pause ${missionId}`;
                break;
            case 'resume_mission':
                command = `mission: resume ${missionId}`;
                break;
            case 'abort_mission':
                command = `mission: abort ${missionId}`;
                break;
            case 'request_forecast':
                command = `mission: forecast ${missionId}`;
                break;
            case 'view_risk':
                command = `mission: audit risk ${missionId}`;
                break;
            default:
                command = `mission: action ${actionId} target ${missionId}`;
        }

        if (command) {
            shellInput.value = command;
            processCommand();
        }
    };

    window.omniManualAction = function (missionId, action, label) {
        // Fallback for legacy tactical cards
        const needsPin = (action === 'request_override');
        window.omniRunQuickAction(missionId, action, label, needsPin, (action === 'abort_mission'));
    };

    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // --- SUGGESTION CHIPS (Modo Conversación) ---
    function showSuggestionChips() {
        const existing = document.getElementById('suggestion-chips');
        if (existing) return; // Don't duplicate

        const container = document.createElement('div');
        container.id = 'suggestion-chips';
        container.className = 'suggestion-chips';

        const suggestions = [
            { emoji: '💬', text: '¿Qué puedes hacer?' },
            { emoji: '📋', text: '¿En qué proyecto estamos?' },
            { emoji: '🧠', text: '¿Cómo funciona tu memoria?' },
            { emoji: '🚀', text: 'Cuéntame sobre OmniWeb' }
        ];

        suggestions.forEach(s => {
            const chip = document.createElement('button');
            chip.className = 'suggestion-chip';
            chip.innerHTML = `<span class="chip-emoji">${s.emoji}</span>${s.text}`;
            chip.addEventListener('click', () => {
                shellInput.value = s.text;
                processCommand();
                container.remove();
            });
            container.appendChild(chip);
        });

        chatLog.appendChild(container);
        scrollToBottom(true);
    }

    // Remove suggestion chips when user types manually
    if (shellInput) {
        shellInput.addEventListener('focus', () => {
            const chips = document.getElementById('suggestion-chips');
            if (chips && shellInput.value.length > 0) chips.remove();
        });
    }

    window.addMessage = addMessage; // Expose to creator.js

    // --- Phase 2: Canonical Submit Path (Reliable Touch/Click) ---
    let lastSubmitTime = 0;
    const submitWithGuard = () => {
        const now = Date.now();
        if (now - lastSubmitTime < 300) return; // Prevent double-fire
        lastSubmitTime = now;
        processCommand();
    };

    // --- TOAST NOTIFICATIONS (Phase 30 Saneamiento) ---
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `omni-toast ${type}`;
        toast.innerText = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.classList.add('visible'), 10);
        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => toast.remove(), 500);
        }, 3500);
    }
    window.showToast = showToast;

    // --- Phase 4: Cognitive Overlay HUD (Always-On Status) ---
    function updateHUD(hud) {
        const hudContainer = document.getElementById('omni-hud');
        if (!hudContainer) return;

        if (!hud || !hud.mission_id) {
            hudContainer.style.display = 'none';
            return;
        }

        hudContainer.style.display = 'flex';
        const driftState = (hud.drift && hud.drift.state) ? hud.drift.state.toLowerCase() : 'nominal';
        const govState = (hud.governance && hud.governance.state) ? hud.governance.state.replace(/_/g, ' ') : 'NOMINAL';
        const urgency = hud.governance ? hud.governance.urgency : 1;

        hudContainer.classList.toggle('alert-mode', urgency >= 4 || driftState === 'critical');

        let alertsHtml = "";
        if (hud.critical_alerts_count > 0) {
            alertsHtml = `
                <div class="hud-alert-summary" onclick="window.omniShell && window.omniShell.switchView ? window.omniShell.switchView('mission') : ''" style="cursor:pointer;">
                    <div class="hud-alert-dot"></div>
                    <span>${hud.critical_alerts_count} ALERTAS</span>
                </div>
            `;
        }

        let authHtml = "";
        if (hud.governance && hud.governance.authority_active) {
            authHtml = `<span class="hud-badge nominal" style="font-size: 0.55rem; padding: 1px 4px; border: none; border-radius: 2px;">AUTH ACTIVA</span>`;
        }

        // 5. Accepted Debt Summary (Phase 107 Integration)
        let debtHtml = "";
        if (hud.debt && hud.debt.total > 0) {
            const d = hud.debt;
            const severityClass = d.severity.toLowerCase();
            let label = "DEUDA";
            let val = d.total;

            if (d.severity === 'CRITICAL') {
                label = "VENCIDA";
                val = d.urgent_count;
            } else if (d.severity === 'WARNING') {
                label = "REVISIÓN";
                val = d.review_due;
            }

            debtHtml = `
                <div class="hud-section ${d.is_running_under_debt ? 'running-debt' : ''}" 
                     onclick="if(window.roadmapUI) window.roadmapUI.checkDebtCockpit();" 
                     style="cursor:pointer; padding: 0 8px; border-radius: 4px; transition: background 0.2s;"
                     onmouseover="this.style.background='rgba(255,255,255,0.05)'"
                     onmouseout="this.style.background='transparent'">
                    <span class="hud-badge ${severityClass}" style="min-width: 60px; text-align: center;">
                        ${label}: ${val}
                    </span>
                    ${d.is_running_under_debt ? '<span class="hud-debt-marker animated">⚠️ BAJO DEUDA</span>' : ''}
                </div>
            `;
        }

        hudContainer.innerHTML = `
            <div class="hud-section" onclick="window.omniSwitchMission('${hud.mission_id}')" style="cursor:pointer;">
                <span class="hud-label">MISIÓN:</span>
                <span class="hud-value">${hud.mission_name}</span>
            </div>
            <div class="hud-section">
                <span class="hud-badge ${driftState === 'nominal' ? 'nominal' : (driftState === 'warning' ? 'warning' : 'critical')}" style="min-width: 65px; text-align: center;">
                    ${driftState === 'nominal' ? 'ALINEADO' : (driftState === 'warning' ? 'DERIVA' : 'CRÍTICO')}
                </span>
                ${hud.drift && hud.drift.is_healing ? '<span class="hud-badge nominal" style="animation: orbPulse 1.5s infinite; border-style: dotted;">HEALING</span>' : ''}
            </div>
            <div class="hud-section">
                <span class="hud-label">GOBERNANZA:</span>
                <span class="hud-value" style="font-size: 0.62rem; letter-spacing: 0;">${govState}</span>
                ${authHtml}
            </div>
            ${debtHtml}
            <div class="hud-interaction">
                ${alertsHtml}
                <button class="hud-button" onclick="window.omniSwitchMission('${hud.mission_id}')">EXPANDIR</button>
            </div>
        `;
    }
    window.omniUpdateHUD = updateHUD;

    if (shellForm) {
        shellForm.addEventListener('submit', (e) => {
            e.preventDefault();
            submitWithGuard();
        });
    }

    // Reliability: Listen to pointerdown for instant touch response
    // But let the form submit naturally as well (or intercept specifically)
    if (sendBtn) {
        sendBtn.addEventListener('pointerdown', (e) => {
            // Instant feedback
            console.log("[INPUT_FIX] PointerDown on Send button.");
        });
    }

    // --- Voice Logic Integration (Reconstructed) ---
    const voice = new VoiceInterface({
        onResult: (text) => {
            console.log("[VOICE_RESULT] Final:", text);
            shellInput.value = text;
            processCommand();
        },
        onStateChange: (state, interimText) => {
            console.log("[VOICE_STATE]", state);
            if (state === 'listening') {
                voiceBtn.classList.add('listening');
                shellInput.placeholder = interimText || "Escuchando...";
                if (interimText) shellInput.value = interimText;
            } else if (state === 'transcribing') {
                voiceBtn.classList.add('processing');
                shellInput.placeholder = "Procesando...";
            } else {
                voiceBtn.classList.remove('listening', 'processing');
                shellInput.placeholder = "Preguntame algo...";
                if (state === 'error') {
                    shellInput.classList.add('input-error');
                    setTimeout(() => shellInput.classList.remove('input-error'), 2000);
                }
            }
        },
        onError: (error) => {
            console.error("[VOICE_ERROR_DIAGNOSTIC]", error);
            let msg = "Error de voz.";
            if (error === 'not-allowed' || error === 'denied') {
                msg = "Acceso a micrófono denegado.";
            } else if (error === 'browser-unsupported' || error === 'unsupported') {
                msg = "Navegador no soporta voz.";
            } else if (!window.isSecureContext && window.location.hostname !== 'localhost') {
                msg = "Requiere HTTPS para voz.";
            }
            showToast(msg, 'warning');
        },
        onSpeechStart: () => {
            const orb = document.querySelector('.ai-orb');
            if (orb) orb.classList.add('speaking');
        },
        onSpeechEnd: () => {
            const orb = document.querySelector('.ai-orb');
            if (orb) orb.classList.remove('speaking');
        }
    });

    window.voice = voice; // Global for replay actions

    if (voiceBtn) {
        voiceBtn.addEventListener('click', () => {
            console.log("[DIAGNOSTIC] Mic button clicked. SecureContext:", window.isSecureContext);
            voice.toggle();
        });
    }

    async function processCommand(explicitCmd = null) {
        const cmd = (explicitCmd !== null) ? explicitCmd : shellInput.value.trim();
        if (!cmd) return;

        addMessage(cmd, 'user', true); // Force scroll for user message
        shellInput.value = '';
        shellInput.classList.remove('input-error'); // Clear error state on submission

        // Remove suggestion chips on first interaction
        const sugChips = document.getElementById('suggestion-chips');
        if (sugChips) sugChips.remove();

        // Typing indicator + Orb pulse
        const orb = document.querySelector('.ai-orb');
        if (orb) orb.classList.add('processing');

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message ai typing';
        typingDiv.innerHTML = '<div class="msg-bubble">...</div>';
        chatLog.appendChild(typingDiv);
        scrollToBottom();

        const evidence = [];
        if (window.creatorEditor && window.creatorEditor.currentPath) {
            evidence.push({ type: 'current_file', path: window.creatorEditor.currentPath });
        }

        // Phase 21: Multimodal Evidence Integration
        if (window.creatorEnv && window.creatorEnv.sessionMedia && window.creatorEnv.sessionMedia.length > 0) {
            window.creatorEnv.sessionMedia.forEach(m => {
                evidence.push({
                    type: 'image_capture',
                    url: m.data,
                    name: m.name,
                    annotations: m.annotations || []
                });
            });
            // Auto-clear after sending to avoid duplication
            window.creatorEnv.clearMedia();
        }

        try {
            // === HOTFIX: Timeout protection to prevent eternal hang ===
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s max

            const response = await fetch('/api/v1/ai-host/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer omniweb-dev-secret-token' // Default dev token
                },
                body: JSON.stringify({
                    message: cmd,
                    multimodal_evidence: evidence,
                    source_surface: document.getElementById('creator-workspace-view').classList.contains('active') ? 'workspace' : 'chat'
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            // === END HOTFIX ===

            const data = await response.json();
            if (orb) orb.classList.remove('processing');
            typingDiv.remove();

            // CAPA 1-4: Cognitive Overlay HUD update (Unidad 84)
            if (window.omniUpdateHUD) window.omniUpdateHUD(data.hud);

            if (data.message) {
                console.log("[EXECUTION_SUCCESS] Response received.");
                addMessage(data.message, 'ai', false, true, data.payload);
                console.log("[RESPONSE_RENDERED] Message displayed in UI.");

                // Update Audit Drawer if in Creator Mode
                if (window.creatorEnv && data.audit) {
                    window.creatorEnv.updateAuditResult(data.audit);
                }

                // Voice Feedback (Use normalized speech if available)
                voice.speak(data.speech || data.message);
            }

            if (data.intent === 'idea_captured') {
                console.log("[MEMORY_STORED] Thought captured in Idea Cloud.");
                // Visual feedback: Highlight Knowledge Explorer tab
                const knowledgeTab = document.querySelector('[data-tab="knowledge"]');
                if (knowledgeTab) {
                    knowledgeTab.style.background = 'rgba(50, 255, 150, 0.2)';
                    knowledgeTab.style.borderColor = '#32ff96';
                    setTimeout(() => {
                        knowledgeTab.style.background = '';
                        knowledgeTab.style.borderColor = '';
                    }, 3000);
                }
            }

            // Workspace / Creator Bridge (Phase 10 Hardening)
            if (window.creatorEnv) {
                window.creatorEnv.lastCopilotResponse = data;
            }

            // Visual Payload Handling (Step 6)
            if (data.payload && data.payload.visual) {
                handleVisualResponse(data.payload.visual);
            } else if (data.display_data) {
                // SuperCommand display data
                const p = data.payload || {};
                handleVisualResponse({
                    type: 'task-report',
                    title: data.display_data.task_title || 'Ejecución de Tarea',
                    data: {
                        status: p.status,
                        actions: p.actions,
                        issues: p.issues
                    }
                });
            }

            // Intent Handling
            if (data.intent === 'confirmation_required') {
                const confirmed = await window.creatorEnv.askPermission(
                    "Confirmación del Sistema",
                    data.message || "¿Deseas proceder con esta operación?"
                );
                if (confirmed) {
                    shellInput.value = `confirm ${cmd}`;
                    processCommand();
                }
                return;
            }

            // Close launcher if user manually types a command
            setLauncherActive(false);

            if (data.intent === 'open_chip' && data.payload && data.payload.target) {
                const target = data.payload.target;
                // Visually highlight in launcher if open
                const launcherItem = document.querySelector(`.chip-launcher-item[data-chip="${target}"]`);
                if (launcherItem) {
                    launcherItem.classList.add('active');
                    setTimeout(() => launcherItem.classList.remove('active'), 2000);
                }

                const url = `/${target}/`;
                setTimeout(() => launchChip(url, target), 600);
            }

            if (data.intent === 'inspect_chip' && data.payload && data.payload.target) {
                if (window.creatorEnv && window.creatorEnv.inspectChip) {
                    window.creatorEnv.inspectChip(data.payload.target);
                }
            }

            if (data.intent === 'navigate_to' && data.payload && data.payload.ui_instruction && data.payload.ui_instruction.view) {
                const view = data.payload.ui_instruction.view;
                if (window.creatorEnv && window.creatorEnv.switchView) {
                    window.creatorEnv.switchView(view);
                }
            }

            if (data.intent === 'focus_chip_runtime' && data.payload && data.payload.target) {
                const url = `/${data.payload.target}/`;
                launchChip(url, data.payload.target);
            }

            if (data.intent === 'logbook_entry_created') {
                // visual hint that it was saved
                const logBtn = document.querySelector('[onclick="masterLogbook.toggle()"]');
                if (logBtn) {
                    logBtn.style.color = '#32ff96';
                    setTimeout(() => logBtn.style.color = '', 2000);
                }
            }

            // --- Builder Execution Handling ---
            if (data.intent === 'approve_roadmap' && data.payload && data.payload.task_id) {
                // Show console immediately or wait for start?
                // User requirement: "UI feedback on current module..."
                // I'll show it as soon as it's approved.
                if (window.builderUI) {
                    window.builderUI.show(data.payload.task_id);
                }
            }

            if (data.intent === 'start_execution' && data.payload && data.payload.task_id) {
                if (window.builderUI) {
                    window.builderUI.show(data.payload.task_id);
                }
            }

        } catch (error) {
            if (orb) orb.classList.remove('processing');
            typingDiv.remove();

            if (error.name === 'AbortError') {
                // === HOTFIX: Timeout fallback — respond locally ===
                console.warn('[CHAT_TIMEOUT] Backend exceeded 15s. Showing local fallback.');
                addMessage("Estoy tardando más de lo esperado en procesar tu mensaje. Probá de nuevo en un momento.", 'ai');
            } else {
                console.error('AI Host Error:', error);
                addMessage("Tengo problemas para conectar con el sistema central. Por favor, verificá la conexión.", 'ai');
            }
        }
    }

    function handleVisualResponse(visual) {
        if (!visual) return;

        // Block 01: Suppress technical visual responses for PUBLIC mode
        const isPublic = document.body.classList.contains('user-mode');
        if (isPublic) {
            const technicalTypes = ['task-report', 'chip-modification-success', 'file-list', 'logbook-list', 'visual-diff'];
            if (technicalTypes.includes(visual.type)) {
                console.info(`[PUBLIC_MODE] Technical visual response (${visual.type}) suppressed.`);
                return;
            }
        }

        // Skip empty task reports
        if (visual.type === 'task-report') {
            const hasActions = visual.data && visual.data.actions && visual.data.actions.length > 0;
            const hasIssues = visual.data && visual.data.issues && visual.data.issues.length > 0;
            if (!hasActions && !hasIssues) {
                console.info("[UI_STABILIZATION] Ghost Task Execution panel suppressed.");
                return;
            }
        }

        console.log("Rendering visual response:", visual);
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ai-visual type-${visual.type}`;

        let content = `<div class="visual-card">
            <h4>${visual.title || 'ActualizaciÃ³n del Sistema'}</h4>`;

        if (visual.type === 'task-report') {
            const actions = (visual.data && visual.data.actions) || [];
            content += `<ul style="font-size: 0.8rem; margin-top: 5px; list-style: none; padding: 0;">
                ${actions.map(a => `<li style="color: #32ff96;">âœ“ ${a}</li>`).join('')}
            </ul>`;
            if (visual.data && visual.data.issues && visual.data.issues.length > 0) {
                content += `<p style="color: #ff5050; font-size: 0.7rem; margin-top: 5px;">! ${visual.data.issues[0]}</p>`;
            }
        } else if (visual.type === 'chip-modification-success') {
            content += `<p style="font-size: 0.8rem; color: #32ff96;">${visual.data}</p>`;
        } else if (visual.type === 'logbook-list') {
            const list = visual.data.entries || [];
            content += `<div style="font-size: 0.8rem; margin-top: 8px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px;">
                ${list.map(e => `
                    <div style="margin-bottom: 8px; border-left: 2px solid var(--accent-color); padding-left: 8px;">
                        <span style="opacity: 0.5; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.05em;">${e.type}</span>
                        <div style="color: #fff; margin-top: 2px;">${e.content}</div>
                    </div>
                `).join('')}
            </div>`;
        } else if (visual.type === 'file-list') {
            const files = visual.data.files || [];
            content += `<div style="font-size: 0.8rem; margin-top: 8px;">
                ${files.map(f => `<div style="color: var(--text-dim); margin-bottom: 2px; font-family: monospace; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 2px 0;">ðŸ“„ ${f}</div>`).join('')}
            </div>`;
        } else {
            content += `<pre style="font-size: 0.7rem; color: var(--text-dim); overflow: auto;">${JSON.stringify(visual.data, null, 2)}</pre>`;
        }

        content += `</div>`;
        msgDiv.innerHTML = content;

        // Visual Diff Mini-Preview in Chat (Phase 21)
        if (payload && payload.visual_diff && payload.visual_context) {
            // Block 01: Visual Diff is high-complexity technical telemetry
            if (document.body.classList.contains('user-mode')) {
                return;
            }
            const vCtx = payload.visual_context;
            const diff = payload.visual_diff;
            const diffEl = document.createElement('div');
            diffEl.className = "visual-diff-preview";
            diffEl.style.cssText = "margin-top: 10px; background: rgba(0,0,0,0.15); border: 1px solid rgba(255,170,0,0.2); border-left: 3px solid #ffaa00; border-radius: 8px; padding: 12px; display: flex; gap: 12px; align-items: center; overflow: hidden;";

            diffEl.innerHTML = `
                <div style="position: relative; width: 60px; height: 60px; border-radius: 4px; overflow: hidden; border: 1px solid rgba(255,255,255,0.1); flex-shrink: 0;">
                    <img src="${vCtx.source_image}" style="width:100%; height:100%; object-fit: cover; opacity: 0.6;">
                    ${(diff.removed_regions || []).map(r => `<div style="position:absolute; left:${r.x}%; top:${r.y}%; width:4px; height:4px; background:#ff4444; border-radius:50%; transform:translate(-50%, -50%);"></div>`).join('')}
                    ${(diff.added_regions || []).map(r => `<div style="position:absolute; left:${r.x}%; top:${r.y}%; width:6px; height:6px; background:#00ff88; border-radius:50%; transform:translate(-50%, -50%); border: 1px solid #fff;"></div>`).join('')}
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 0.65rem; color: #ffaa00; font-weight: bold; letter-spacing: 0.5px;">DIAGNÓSTICO RE-ORIENTADO</div>
                    <div style="font-size: 0.6rem; opacity: 0.7; margin-top: 2px;">Detectado cambio en el foco visual. Ver Pizarrón para detalles.</div>
                </div>
            `;
            msgDiv.appendChild(diffEl);
        }

        chatLog.appendChild(msgDiv);
        scrollToBottom();
    }

    // --- Phase 4 & 5: Creator Tools Restore ---
    const toolbar = {
        editor: document.getElementById('toolbar-editor'),
        copilot: document.getElementById('toolbar-copilot'),
        reload: document.getElementById('toolbar-reload')
    };

    const overlays = {
        editor: document.getElementById('creator-editor-overlay'),
        copilot: document.getElementById('creator-copilot-overlay')
    };

    if (toolbar.reload) {
        toolbar.reload.addEventListener('click', () => {
            window.location.reload(true);
        });
    }

    if (toolbar.editor) {
        toolbar.editor.addEventListener('click', (e) => {
            // MISSION UNIFY: If workspace is active or Creator mode is preferred, bypass legacy overlay
            if (window.creatorEnv && document.getElementById('creator-workspace-view')) {
                // The onclick in index.html handles the workspace opening
                // We just prevent the legacy overlay from firing if workspace is the target
                return;
            }
            if (overlays.editor) overlays.editor.style.display = overlays.editor.style.display === 'none' ? 'flex' : 'none';
        });
    }

    if (toolbar.copilot) {
        toolbar.copilot.addEventListener('click', (e) => {
            if (window.creatorEnv && document.getElementById('creator-workspace-view')) {
                return;
            }
            if (overlays.copilot) overlays.copilot.style.display = overlays.copilot.style.display === 'none' ? 'flex' : 'none';
        });
    }

    // Editor Logic (Phase 5)
    const editorOpenBtn = document.getElementById('editor-open-btn');
    const editorSaveBtn = document.getElementById('editor-save-btn');
    const editorPathInput = document.getElementById('editor-file-path');
    const editorContent = document.getElementById('editor-content');

    if (editorOpenBtn) {
        editorOpenBtn.addEventListener('click', async () => {
            const path = editorPathInput.value.trim();
            if (!path) return;

            editorOpenBtn.innerText = 'Cargando...';
            try {
                const res = await fetch(`/api/v1/creator/fs/read?path=${encodeURIComponent(path)}`, {
                    headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
                });
                const data = await res.json();
                if (data.status === 'success' && data.content !== undefined) {
                    editorContent.value = data.content;
                    editorOpenBtn.innerText = 'Archivo Abierto';
                } else {
                    const detail = data.detail || data.error || data.message || "Unknown error";
                    console.error("FS_READ ERROR RESPONSE:", data);
                    alert("Error reading file: " + detail);
                    editorOpenBtn.innerText = 'Abrir Archivo';
                }
            } catch (err) {
                console.error("Editor Read Error:", err);
                alert("Could not connect to editor API.");
                editorOpenBtn.innerText = 'Open File';
            }
            setTimeout(() => editorOpenBtn.innerText = 'Abrir Archivo', 2000);
        });
    }

    if (editorSaveBtn) {
        editorSaveBtn.addEventListener('click', async () => {
            const path = editorPathInput.value.trim();
            const content = editorContent.value;
            if (!path) return;

            editorSaveBtn.innerText = 'Guardando...';
            try {
                const res = await fetch('/api/v1/creator/fs/write', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer omniweb-dev-secret-token'
                    },
                    body: JSON.stringify({ path, content })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    editorSaveBtn.innerText = 'Saved âœ“';
                    addMessage(`File updated: **${path}**`, 'ai');
                } else {
                    alert("Error saving file: " + (data.detail || data.error || "Unknown error"));
                    editorSaveBtn.innerText = 'Guardar Cambios';
                }
            } catch (err) {
                console.error("Editor Save Error:", err);
                alert("Could not connect to editor API.");
                editorSaveBtn.innerText = 'Save Changes';
            }
            setTimeout(() => editorSaveBtn.innerText = 'Guardar Cambios', 2000);
        });
    }

    // --- Particles Background (Animated) ---
    function createParticles() {
        const container = document.getElementById('particles');
        if (!container) return;
        container.innerHTML = '';

        // Optimize for mobile: fewer particles
        const isMobile = window.innerWidth < 768;
        const count = isMobile ? 15 : 40;

        for (let i = 0; i < count; i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            const size = Math.random() * (isMobile ? 2 : 3);
            const duration = 10 + Math.random() * 20;
            p.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                background: white;
                opacity: ${Math.random() * 0.5 + 0.2};
                top: ${Math.random() * 100}%;
                left: ${Math.random() * 100}%;
                border-radius: 50%;
                pointer-events: none;
                filter: blur(1px);
                animation: floatParticle ${duration}s linear infinite;
            `;
            container.appendChild(p);
        }
    }
    createParticles();

    // Add particle animation to stylesheet
    const style = document.createElement('style');
    const animId = "anim_" + Math.random().toString(36).substr(2, 9);
    style.innerHTML = `
        @keyframes ${animId} {
            0% { transform: translate(0, 0); }
            33% { transform: translate(${Math.random() * 50}px, ${Math.random() * 50}px); }
            66% { transform: translate(${Math.random() * -50}px, ${Math.random() * 20}px); }
            100% { transform: translate(0, 0); }
        }
        .particle { animation-name: ${animId} !important; }
    `;
    document.head.appendChild(style);

    // --- Capabilities Management (Monitoring Only, Progressive Request) ---
    async function updateCapabilities() {
        const caps = [
            { id: 'cap-sound', check: () => ('speechSynthesis' in window) },
            {
                id: 'cap-mic', check: async () => {
                    if (!navigator.mediaDevices) return 'no-https';
                    try {
                        const status = await navigator.permissions.query({ name: 'microphone' });
                        return status.state;
                    } catch (e) { return 'unsupported'; }
                }
            },
            {
                id: 'cap-camera', check: async () => {
                    if (!navigator.mediaDevices) return 'no-https';
                    try {
                        const status = await navigator.permissions.query({ name: 'camera' });
                        return status.state;
                    } catch (e) { return 'unsupported'; }
                }
            },
            {
                id: 'cap-geo', check: async () => {
                    try {
                        const status = await navigator.permissions.query({ name: 'geolocation' });
                        return status.state;
                    } catch (e) { return 'unsupported'; }
                }
            }
        ];

        for (const cap of caps) {
            const el = document.getElementById(cap.id);
            if (!el) continue;
            const statusEl = el.querySelector('.status');
            const result = await cap.check();

            if (result === true || result === 'granted') {
                statusEl.innerText = 'Permitido';
                statusEl.className = 'status pass';
            } else if (result === 'prompt' || result === 'prompted') {
                statusEl.innerText = 'Disponible';
                statusEl.className = 'status info';
            } else if (result === 'denied') {
                statusEl.innerText = 'Bloqueado';
                statusEl.className = 'status fail';
            } else if (result === 'no-https') {
                statusEl.innerText = 'Requiere HTTPS';
                statusEl.className = 'status warning';
            } else {
                statusEl.innerText = 'Inactivo';
                statusEl.className = 'status neutral';
            }
        }
    }
    window.updateCapabilities = updateCapabilities;
    updateCapabilities(); // Initial check
    setInterval(updateCapabilities, 8000); // Polling status

    window.omniSwitchMission = function (missionId) {
        console.log("Navigating to Mission Context:", missionId);
        if (window.omniShell && typeof window.omniShell.switchView === 'function') {
            // Update backend focus context
            shellInput.value = `mission: switch_focus ${missionId}`;
            processCommand();

            // First switch to workspace view where the cockpit resides
            window.omniShell.switchView('workspace');

            // Highlight the target mission visually if possible
            const missionCards = document.querySelectorAll('.mission-card, .tactical-card');
            missionCards.forEach(card => {
                if (card.dataset && card.dataset.missionId === missionId) {
                    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    card.style.ring = '2px solid var(--accent)';
                }
            });
        }
    };

    /* GOVERNANCE FUSION BRIDGE (Unidad 108) */
    async function renderGovernanceFusion(containerId, targetId, targetType = 'MISSION') {
        const container = document.getElementById(containerId);
        if (!container) return;

        try {
            const res = await fetch(`/api/v1/governance/fusion/${targetId}?target_type=${targetType}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            if (!res.ok) return;

            const snapshot = await res.json();
            if (snapshot.fused_status === 'NOMINAL') {
                container.style.display = 'none';
                return;
            }

            container.style.display = 'flex';
            let traceHtml = '';
            if (snapshot.last_action_trace) {
                const trace = snapshot.last_action_trace;
                traceHtml = `
                    <div class="fusion-trace-box outcome-${trace.outcome_status.toLowerCase().replace(/_/g, '-')}">
                        <div class="trace-header">
                            <span class="trace-action-pill">${trace.creator_action.replace(/_/g, ' ')}</span>
                            <span class="trace-outcome-status">${trace.outcome_status.replace(/_/g, ' ')}</span>
                        </div>
                        <div class="trace-rationale">${trace.rationale_summary || ''}</div>
                        <div class="trace-footer">
                            <span>Efecto: ${trace.severity_delta < 0 ? 'ALIVIO' : (trace.severity_delta > 0 ? 'ESCALADA' : 'ESTABLE')}</span>
                            <span class="trace-eval-at">Auditado: ${new Date(trace.last_evaluated_at).toLocaleTimeString()}</span>
                        </div>
                    </div>
                `;
            }

            container.innerHTML = `
                <div class="gov-fusion-card band-${snapshot.severity_band.toLowerCase()}">
                    <div class="fusion-header">
                        <span class="fusion-title">CONTEXTO DE RIESGO UNIFICADO</span>
                        <span class="fusion-badge badge-${snapshot.fused_status.toLowerCase().replace(/_/g, '-')}">${snapshot.fused_status.replace(/_/g, ' ')}</span>
                    </div>
                    <div class="fusion-body">
                        <div class="fusion-rationale">${snapshot.rationale}</div>
                        <div class="fusion-composition">
                            <div class="fusion-comp-item"><span>DEUDA:</span> ${snapshot.debt_state}</div>
                            <div class="fusion-comp-item"><span>PRESIÓN:</span> ${snapshot.pressure_state.replace(/_/g, ' ')}</div>
                            <div class="fusion-comp-item"><span>BASE:</span> ${snapshot.advisory_state}</div>
                        </div>
                        ${traceHtml}
                    </div>
                    <div class="fusion-action-row">
                        <button class="fusion-btn primary" onclick="window.omniHandleFusionAction('${snapshot.next_action}', '${targetId}', '${targetType}')">
                            ${snapshot.next_action.replace(/_/g, ' ')}
                        </button>
                    </div>
                </div>
            `;
        } catch (err) {
            console.error("Fusion render failed", err);
        }
    }
    window.omniRenderFusion = renderGovernanceFusion;

    window.omniHandleFusionAction = function (action, targetId, targetType) {
        console.log("Fusion Action:", action, targetId);
        if (action === 'OPEN_REBASE_PREVIEW' || action === 'OPEN_REBASE_ADVISOR') {
            if (window.roadmapUI) window.roadmapUI.adjustPlan(targetId);
        } else if (action === 'OPEN_DEBT_COCKPIT' || action === 'REVIEW_DEBT') {
            if (window.roadmapUI) {
                window.roadmapUI.checkDebtCockpit();
            } else {
                window.omniShell.addInput('governance: check_debt');
            }
        } else if (action === 'INSPECT_TIMELINE') {
            window.omniShell.addInput(`governance: inspect_timeline ${targetId}`);
        } else if (action === 'FREEZE_UNTIL_RECOVERY') {
            window.omniShell.addInput(`mission: freeze ${targetId} --reason "Compromiso estructural detectado via Fusión"`);
        } else {
            window.omniShell.addInput(`inspect ${targetType.toLowerCase()} ${targetId}`);
        }

        // Switch to appropriate view
        if (action.includes('DEBT') || action.includes('PREVIEW') || action.includes('TIMELINE') || action.includes('COCKPIT')) {
            window.omniShell.switchView('workspace');
        }
    };

    /* FORENSIC DECISION COCKPIT (Unidad 109) */
    async function renderForensicCockpit() {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) return;

        mainContent.innerHTML = `<div class="forensic-cockpit-container"><h1 style="color:var(--accent); font-family: Outfit; letter-spacing: 2px;">AUDITANDO HISTORIAL FORENSE...</h1></div>`;

        try {
            const res = await fetch(`/api/v1/governance/forensic/cockpit`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            const payload = data.payload;
            const summary = payload.summary;

            let traceRows = payload.traces.map(t => {
                const outcomeClass = t.outcome_status.toLowerCase().replace(/_/g, '-');
                const appliedStr = new Date(t.applied_at).toLocaleString();
                return `
                    <tr class="forensic-trace-row" onclick="window.omniShell.addInput('inspect mission ${t.target_id}'); window.omniShell.switchView('workspace');">
                        <td class="trace-cell-id">#${t.trace_id}</td>
                        <td class="trace-cell-domain">${t.target_domain}</td>
                        <td class="trace-cell-action">${t.creator_action.replace(/_/g, ' ')}</td>
                        <td><span class="outcome-badge outcome-${outcomeClass}">${t.outcome_status.replace(/_/g, ' ')}</span></td>
                        <td class="trace-cell-rationale">${t.rationale_summary || ''}</td>
                        <td class="trace-cell-date">${appliedStr}</td>
                    </tr>
                `;
            }).join('');

            let hotspotsHtml = Object.entries(summary.hotspots).map(([dom, count]) => `
                <div class="hotspot-pill">
                    <span>${dom}</span>
                    <span class="hotspot-count">${count}</span>
                </div>
            `).join('') || '<div class="hotspot-pill">Sin fricción detectada</div>';

            let insightsHtml = payload.insights.map(ins => `<div class="insight-item">${ins}</div>`).join('');

            mainContent.innerHTML = `
                <div class="forensic-cockpit-container">
                    <div class="forensic-header">
                        <div>
                            <h1>CABINA FORENSE DE DECISIONES</h1>
                            <div class="forensic-description">Auditoría global de efectividad estructural: Convirtiendo decisiones del Creador en aprendizaje sistémico.</div>
                        </div>
                    </div>

                    <div class="forensic-summary-row">
                        <div class="forensic-card">
                            <div class="card-label">Decisiones Totales</div>
                            <div class="card-value">${summary.total_decisions}</div>
                            <div class="card-sub">Capturadas en este roadmap</div>
                        </div>
                        <div class="forensic-card">
                            <div class="card-label">Efectividad</div>
                            <div class="card-value text-effective">${summary.outcomes.EFFECTIVE}</div>
                            <div class="card-sub">Alivio estructural confirmado</div>
                        </div>
                        <div class="forensic-card">
                            <div class="card-label">Degradación Post-Acción</div>
                            <div class="card-value text-degraded">${summary.outcomes.DEGRADED}</div>
                            <div class="card-sub">Intervenciones ineficaces</div>
                        </div>
                        <div class="forensic-card">
                            <div class="card-label">Evaluaciones Pendientes</div>
                            <div class="card-value text-pending">${summary.outcomes.PENDING}</div>
                            <div class="card-sub">Esperando señal operativa</div>
                        </div>
                    </div>

                    ${insightsHtml ? `
                    <div class="forensic-insights-box">
                        <div class="card-label" style="color:var(--accent)">Análisis de Patrones</div>
                        <div class="insights-list">${insightsHtml}</div>
                    </div>` : ''}

                    <div>
                        <div class="card-label">Hotspots de Fricción Forense (Degradación por Dominio)</div>
                        <div class="forensic-hotspots">${hotspotsHtml}</div>
                    </div>

                    <div style="margin-top: 1rem;">
                        <div class="forensic-list-header">HISTORIAL FORENSE DETALLADO</div>
                        <div style="overflow-x: auto;">
                            <table class="forensic-trace-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Dominio</th>
                                        <th>Acción</th>
                                        <th>Resultado</th>
                                        <th>Resumen Forense</th>
                                        <th>Fecha</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${traceRows || '<tr><td colspan="6" style="text-align:center; padding: 2rem;">No hay trazas forenses registradas aún.</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (err) {
            console.error(err);
            mainContent.innerHTML = `<div class="forensic-cockpit-container"><h1>ERROR AL CARGAR DASHBOARD FORENSE</h1></div>`;
        }
    }
    window.omniRenderForensicCockpit = renderForensicCockpit;

    /* FRICTION HEATMAP (Unidad 111) */
    async function renderFrictionHeatmap() {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) return;

        mainContent.innerHTML = `<div class="heatmap-container"><h1 style="color:var(--accent); font-family: Outfit; letter-spacing: 2px;">CALCULANDO FRICCIÓN ESTRUCTURAL...</h1></div>`;

        try {
            const res = await fetch(`/api/v1/governance/forensic/heatmap`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            const nodes = data.payload;

            let nodesHtml = await Promise.all(nodes.map(async (n) => {
                const bandClass = `band-${n.severity_band.toLowerCase()}`;
                const signals = n.signals;

                // Fetch associated relief proposals
                let reliefHtml = '';
                let statusBadgeHtml = '';
                try {
                    const rRes = await fetch(`/api/v1/governance/forensic/relief/proposals?domain=${n.domain}`, {
                        headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
                    });
                    const rData = await rRes.json();
                    if (rData.payload && rData.payload.length > 0) {
                        const p = rData.payload[0];
                        if (p.status === 'PENDING') {
                            reliefHtml = `
                            <div class="relief-available-badge" onclick="event.stopPropagation(); window.omniRenderReliefPreview('${p.proposal_id}')">
                                🛡️ ALIVIO DISPONIBLE
                            </div>
                            `;
                        } else if (p.status === 'ACCEPTED') {
                            const outcomeEmoji = {
                                'EFFECTIVE_RELIEF': '✅',
                                'PARTIAL_RELIEF': '📈',
                                'STRUCTURAL_RESISTANCE': '🔥',
                                'ESCALATING_DESPITE_RELIEF': '⚠️',
                                'UNDER_OBSERVATION': '🕒'
                            }[p.relief_outcome] || '🛡️';

                            statusBadgeHtml = `
                            <div class="stabilization-status-badge ${p.relief_outcome ? p.relief_outcome.toLowerCase() : ''}" onclick="event.stopPropagation(); window.omniRenderReliefPreview('${p.proposal_id}')">
                                ${outcomeEmoji} ${p.relief_outcome ? p.relief_outcome.replace(/_/g, ' ') : 'STABILIZING'}
                            </div>
                           `;
                        }
                    }
                } catch (e) { }

                return `
                <div class="heatmap-node ${bandClass} ${statusBadgeHtml ? 'under-relief' : ''}" onclick="window.omniShell.addInput('governance: check_debt ${n.domain}'); window.omniShell.switchView('workspace');">
                    <div class="node-severity-indicator"></div>
                    ${reliefHtml}
                    ${statusBadgeHtml}
                    <div class="node-header">
                        <span class="node-domain">${n.domain}</span>
                        <span class="node-score">${n.friction_score.toFixed(0)}</span>
                    </div>
                    <div class="node-rationale">${n.rationale}</div>
                    <div class="node-signals">
                        ${signals.debt_count > 0 ? `<span class="signal-pill">Deuda: ${signals.debt_count}</span>` : ''}
                        ${signals.advisory_count > 0 ? `<span class="signal-pill">Avisos: ${signals.advisory_count}</span>` : ''}
                        ${signals.degraded_traces > 0 ? ` <span class="signal-pill">Fallos: ${signals.degraded_traces}</span>` : ''}
                        ${signals.avg_delta !== 0 ? `<span class="signal-pill">Impacto: ${signals.avg_delta > 0 ? '+' : ''}${signals.avg_delta}</span>` : ''}
                    </div>
                    <div class="node-actions">
                        <span class="action-label">${n.recommended_action.replace(/_/g, ' ')}</span>
                        <span class="node-footer-meta">${new Date(n.last_updated).toLocaleTimeString()}</span>
                    </div>
                </div>
                `;
            }));

            mainContent.innerHTML = `
                <div class="heatmap-container">
                    <div class="heatmap-header" style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2>MAPA DE FRICCIÓN ESTRUCTURAL</h2>
                            <div class="forensic-description">Priorización espacial de riesgo: Consolidando deuda, presión y efectividad forense.</div>
                        </div>
                        <button class="btn-apply" style="width: auto; margin: 0; padding: 10px 20px; background: var(--accent); color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.4);" 
                            onclick="creatorEnv.generateFrictionRelief()">SCAN & GENERATE RELIEF</button>
                    </div>
                    <div class="heatmap-grid">
                        ${nodesHtml.join('') || '<div style="grid-column: 1/-1; text-align: center; padding: 3rem; opacity: 0.5;">No hay señales de fricción registradas. El sistema está nominal.</div>'}
                    </div>
                </div>
            `;
        } catch (err) {
            console.error(err);
            mainContent.innerHTML = `<div class="heatmap-container"><h1>ERROR AL CARGAR MAPA DE CALOR</h1></div>`;
        }
    }
    window.omniRenderFrictionHeatmap = renderFrictionHeatmap;

    /* RELIEF MISSION PREVIEW (Unidad 112) */
    async function renderReliefPreview(proposalId) {
        const overlay = document.createElement('div');
        overlay.id = "relief-preview-overlay";
        overlay.style = "position: fixed; inset: 0; background: rgba(5,5,8,0.9); z-index: 10000; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(8px); animation: fadeIn 0.2s ease-out;";

        overlay.innerHTML = `<div class="cockpit-card" style="width: 600px; max-width: 90%; border: 1px solid var(--accent); padding: 2rem; position: relative;">
            <h2 style="color:var(--accent); font-family: Outfit; margin-bottom: 1rem;">PREVIEW: MISIÃ“N DE ALIVIO ESTRUCTURAL</h2>
            <div id="relief-proposal-content" class="loading-indicator">Cargando diseÃ±o de intervenciÃ³n...</div>
        </div>`;

        document.body.appendChild(overlay);

        try {
            const res = await fetch(`/api/v1/governance/forensic/relief/proposals`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            const p = data.payload.find(x => x.proposal_id === proposalId);

            if (!p) throw new Error("Proposal not found");

            document.getElementById('relief-proposal-content').innerHTML = `
                <div style="background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem;">
                    <div style="font-size: 0.8rem; opacity: 0.7; margin-bottom: 0.5rem;">TIPO DE INTERVENCIÃ“N</div>
                    <div style="font-family: Outfit; font-weight: bold; color: var(--accent); letter-spacing: 1px;">${p.relief_type.replace(/_/g, ' ')}</div>
                    <div style="margin-top: 1rem; font-size: 0.9rem; line-height: 1.5;">${p.rationale}</div>
                </div>

                <div style="margin-bottom: 1.5rem;">
                    <div style="font-size: 0.8rem; opacity: 0.7; margin-bottom: 0.5rem;">OBJETIVO PROPUESTO</div>
                    <div style="font-family: Inter; font-size: 1.1rem; font-weight: 500;">${p.proposed_objective}</div>
                </div>

                <div style="display: flex; gap: 20px; border-top: 1px solid var(--border-subtle); padding-top: 1.5rem;">
                    <div style="flex: 1;">
                        <span style="display: block; font-size: 0.75rem; opacity: 0.6;">CONFIANZA RED</span>
                        <span style="font-size: 1.2rem; font-weight: bold; color: #10B981;">${(p.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div style="flex: 1;">
                        <span style="display: block; font-size: 0.75rem; opacity: 0.6;">ALIVIO PROYECTADO</span>
                        <span style="font-size: 1.2rem; font-weight: bold; color: #06B6D4;">-${p.expected_heat_reduction.toFixed(0)} pts</span>
                    </div>
                </div>

                <div style="margin-top: 2rem; display: flex; gap: 10px;">
                    <button class="btn-apply" onclick="window.omniHandleReliefDecision('${p.proposal_id}', 'ACCEPT')" style="background: var(--accent); color: white;">ACEPTAR & LANZAR MISIÃ“N</button>
                    <button class="btn-apply" onclick="window.omniHandleReliefDecision('${p.proposal_id}', 'POSTPONE')" style="background: rgba(255,255,255,0.05);">POSTERGAR</button>
                    <button class="btn-apply" onclick="document.getElementById('relief-preview-overlay').remove()" style="background: transparent; border: 1px solid rgba(255,255,255,0.1);">CERRAR</button>
                </div>
            `;
        } catch (err) {
            overlay.innerHTML = `<div class="cockpit-card">Error cargando propuesta.</div>`;
        }
    }
    window.omniRenderReliefPreview = renderReliefPreview;

    async function handleReliefDecision(id, decision) {
        try {
            await fetch(`/api/v1/governance/forensic/relief/proposals/${id}/decision?decision=${decision}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            document.getElementById('relief-preview-overlay').remove();
            window.omniRenderFrictionHeatmap();
            if (decision === 'ACCEPT') {
                window.omniShell.addInput(`governance: relief_mission_launched ${id}`);
            }
        } catch (e) { }
    }
    window.omniHandleReliefDecision = handleReliefDecision;

    // Helper for Creator Workspace
    if (!window.creatorEnv) window.creatorEnv = {};
    window.creatorEnv.generateFrictionRelief = async function () {
        try {
            await fetch(`/api/v1/governance/forensic/relief/generate`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            window.omniRenderFrictionHeatmap();
        } catch (e) { }
    }

    async function evaluateEffects() {
        try {
            await fetch(`/api/v1/governance/forensic/relief/evaluate`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            window.omniRenderFrictionHeatmap();
        } catch (e) { }
    }
    window.omniEvaluateEffects = evaluateEffects;

});

function logout() {
    console.log("Sesion cerrada");
    console.log("FINAL LOGOUT");
}
