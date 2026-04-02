document.addEventListener('DOMContentLoaded', () => {
    // --- Phase 0: Emergency UI Bootstrap (Mission 36) ---
    const loadPlaceholder = document.getElementById('js-load-placeholder');
    if (loadPlaceholder) loadPlaceholder.remove();

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
            const title = item.getAttribute('data-chip');
            launchChip(url, title);
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

    function addMessage(text, sender = 'ai', forceScroll = false, shouldSave = true) {
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

    async function processCommand() {
        const cmd = shellInput.value.trim();
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

            if (data.message) {
                console.log("[EXECUTION_SUCCESS] Response received.");
                addMessage(data.message, 'ai');
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

});

function logout() {
    console.log("Sesion cerrada");
    console.log("FINAL LOGOUT");
}
