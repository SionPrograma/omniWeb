document.addEventListener('DOMContentLoaded', () => {
    // --- OMNI SAFE-MODE CACHE CLEANUP (MISSION 36) ---
    // Rule: Eliminate all cache/SW interference to ensure single-source-of-truth.
    const CACHE_RESET_ID = "omni_v1_stable";
    try {
        if (localStorage.getItem("omni_cache_reset") !== CACHE_RESET_ID) {
            // Fixed by Jetski Subagent
            console.warn("[SAFE_MODE] Cache inconsistency detected. Purging SW and Caches...");

            // 1. Unregister all service workers
            if (navigator.serviceWorker) {
                navigator.serviceWorker.getRegistrations().then(registrations => {
                    for (let registration of registrations) {
                        registration.unregister().then(() => {
                            console.log("[SAFE_MODE] SW Unregistered.");
                        });
                    }
                });
            }

            // 2. Delete all caches
            if (window.caches) {
                caches.keys().then(names => {
                    for (let name of names) {
                        caches.delete(name).then(() => {
                            console.log("[SAFE_MODE] Cache Purged:", name);
                        });
                    }
                });
            }

            // 3. Mark as reset and reload once
            localStorage.setItem("omni_cache_reset", CACHE_RESET_ID);
            console.warn("[SAFE_MODE] Reset complete. Reloading for fresh state.");
            setTimeout(() => {
                window.location.reload(true);
            }, 500);
            return; // Halt this execution
        }
    } catch (e) {
        console.warn("[SAFE_MODE] Reset guard failed - likely storage restriction.");
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
    async function initGreeting() {
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const inviteToken = urlParams.get('invite') || urlParams.get('beta');

            const browser_lang = navigator.language.split('-')[0] || 'en';
            const res = await fetch('/api/v1/onboarding/greeting', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: "Hola Omni",
                    browser_lang: browser_lang,
                    invite_token: inviteToken
                })
            });

            if (!res.ok) throw new Error("API response not ok");

            const data = await res.json();
            if (data.payload?.message) {
                if (data.payload.title) {
                    const greetingEl = document.getElementById('greeting');
                    if (greetingEl) greetingEl.innerText = data.payload.title;
                }
                addMessage(data.payload.message, 'ai');
                if (window.creatorEnv && data.audit) {
                    window.creatorEnv.updateAuditResult(data.audit);
                }
            } else {
                // Local fallback if message is empty
                addMessage("Sistema Omni inicializado. Listo para recibir instrucciones.", 'ai');
            }
        } catch (err) {
            console.error("Greeting failed:", err);
            // Local fallback on error
            addMessage("Enlace Omni Establecido. ¿Cómo puedo ayudarte hoy?", 'ai');
        }
    }
    initGreeting();

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
                    // Update tab UI
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
    setTimeout(handleDeepLink, 1000); // Wait for other components to init
    function setLauncherActive(active) {
        const isActive = active !== undefined ? active : !launcherOverlay.classList.contains('active');
        launcherOverlay.classList.toggle('active', isActive);
        openLauncherBtn.classList.toggle('active', isActive);
        document.body.classList.toggle('launcher-active', isActive);
        return isActive;
    }

    window.omniShell = {
        closeLauncher: () => setLauncherActive(false)
    };

    openLauncherBtn.addEventListener('click', () => {
        setLauncherActive();
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
        chipView.classList.add('active');

        // Minimize AI Host
        aiHostView.classList.remove('active');
    }

    closeChipBtn.addEventListener('click', () => {
        chipView.classList.remove('active');
        aiHostView.classList.add('active');
        setTimeout(() => {
            chipFrame.src = ''; // Clear iframe after transition
        }, 400);
    });

    // --- Navigation Logic ---
    navItems.forEach(nav => {
        nav.addEventListener('click', () => {
            const view = nav.getAttribute('data-view');
            if (!view) return;

            navItems.forEach(n => n.classList.remove('active'));
            nav.classList.add('active');

            if (view === 'context') {
                toggleContext(true);
            } else {
                toggleContext(false);
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
            activeView = 'chat';
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
            aiHostView.scrollTo({
                top: aiHostView.scrollHeight,
                behavior: 'smooth'
            });
        }
    }

    function addMessage(text, sender = 'ai', forceScroll = false) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${sender}`;

        // --- VISUAL DIFF ENHANCEMENT ---
        const content = renderDiff(text);
        msgDiv.innerHTML = `<div class="msg-bubble">${content}</div>`;

        chatLog.appendChild(msgDiv);
        scrollToBottom(forceScroll || sender === 'user');
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

    window.addMessage = addMessage; // Expose to creator.js

    // --- Phase 2: Canonical Submit Path (Reliable Touch/Click) ---
    let lastSubmitTime = 0;
    const submitWithGuard = () => {
        const now = Date.now();
        if (now - lastSubmitTime < 300) return; // Prevent double-fire
        lastSubmitTime = now;
        processCommand();
    };

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
                shellInput.placeholder = "Escribe un comando...";
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
            addMessage(`⚠️ ${msg}`, 'ai');
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
            const response = await fetch('/api/v1/ai-host/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer omniweb-dev-secret-token' // Default dev token
                },
                body: JSON.stringify({
                    message: cmd,
                    multimodal_evidence: evidence
                })
            });

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

                // Voice Feedback
                voice.speak(data.message);
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

            // Visual Payload Handling (Step 6)
            if (data.payload?.visual) {
                handleVisualResponse(data.payload.visual);
            } else if (data.display_data) {
                // SuperCommand display data
                handleVisualResponse({
                    type: 'task-report',
                    title: data.display_data.task_title || 'Ejecución de Tarea',
                    data: {
                        status: data.payload.status,
                        actions: data.payload.actions,
                        issues: data.payload.issues
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

            if (data.intent === 'open_chip' && data.payload?.target) {
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

            if (data.intent === 'inspect_chip' && data.payload?.target) {
                if (window.creatorEnv && window.creatorEnv.inspectChip) {
                    window.creatorEnv.inspectChip(data.payload.target);
                }
            }

            if (data.intent === 'navigate_to' && data.payload?.ui_instruction?.view) {
                const view = data.payload.ui_instruction.view;
                if (window.creatorEnv && window.creatorEnv.switchView) {
                    window.creatorEnv.switchView(view);
                }
            }

            if (data.intent === 'focus_chip_runtime' && data.payload?.target) {
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
            if (data.intent === 'approve_roadmap' && data.payload?.task_id) {
                // Show console immediately or wait for start?
                // User requirement: "UI feedback on current module..."
                // I'll show it as soon as it's approved.
                if (window.builderUI) {
                    window.builderUI.show(data.payload.task_id);
                }
            }

            if (data.intent === 'start_execution' && data.payload?.task_id) {
                if (window.builderUI) {
                    window.builderUI.show(data.payload.task_id);
                }
            }

        } catch (error) {
            console.error('AI Host Error:', error);
            typingDiv.remove();
            addMessage("Tengo problemas para conectar con el sistema central. Por favor, verifica la conexión.", 'ai');
        }
    }

    function handleVisualResponse(visual) {
        if (!visual) return;

        // Skip empty task reports
        if (visual.type === 'task-report') {
            const hasActions = visual.data?.actions && visual.data.actions.length > 0;
            const hasIssues = visual.data?.issues && visual.data.issues.length > 0;
            if (!hasActions && !hasIssues) {
                console.info("[UI_STABILIZATION] Ghost Task Execution panel suppressed.");
                return;
            }
        }

        console.log("Rendering visual response:", visual);
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ai-visual type-${visual.type}`;

        let content = `<div class="visual-card">
            <h4>${visual.title || 'Actualización del Sistema'}</h4>`;

        if (visual.type === 'task-report') {
            const actions = visual.data.actions || [];
            content += `<ul style="font-size: 0.8rem; margin-top: 5px; list-style: none; padding: 0;">
                ${actions.map(a => `<li style="color: #32ff96;">✓ ${a}</li>`).join('')}
            </ul>`;
            if (visual.data.issues?.length > 0) {
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
                ${files.map(f => `<div style="color: var(--text-dim); margin-bottom: 2px; font-family: monospace; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 2px 0;">📄 ${f}</div>`).join('')}
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
                    editorSaveBtn.innerText = 'Saved ✓';
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
});
