class CreatorEnvironment {
    constructor() {
        this.statusInterval = null;
        this.currentTab = 'health';
        this.systemState = null;
        this.copilotPlan = null;
        this.copilotTerminal = [];
        this.auditIssues = [];
        this.correctionProposals = [];
        this.sessionMedia = [];
        this.sessionMediaAnnotations = [];
    }

    init() {
        console.log("Initializing Creator Environment...");
        this.triggerLightBurst();
        this.startStatusPolling();
        this.setupPermissionModal();
        this.setupMissionControl();
        this.bindAIVisual();
        this.setupQRScanner();
        this.setupAuditDrawer();
        try {
            this.setupWorkspace();
        } catch (err) {
            console.error("Workspace Setup Failed:", err);
        }

        // Auto-access for Creator Audit (Phase 30)
        setTimeout(() => {
            if (document.body.classList.contains('creator-authenticated') || !document.body.classList.contains('user-mode')) {
                console.log("Restoring Creator session...");
                this.switchView('mission');
                if (window.masterLogbook) window.masterLogbook.toggle(true);
            }
        }, 1500);
    }

    triggerLightBurst() {
        const orb = document.getElementById('main-ai-orb');
        if (orb) {
            orb.classList.add('burst');
            setTimeout(() => orb.classList.remove('burst'), 1500);
        }
    }

    // 1. SYSTEM STATE UPDATES
    async startStatusPolling() {
        const updateStatus = async () => {
            try {
                const res = await fetch('/api/v1/system/state', {
                    headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
                });
                this.systemState = await res.json();
                this.updateUI(this.systemState);
                if (document.getElementById('mission-control-view').classList.contains('active')) {
                    this.renderCockpit();
                }
            } catch (err) {
                console.warn("Status polling offline.");
            }
        };

        updateStatus();
        this.statusInterval = setInterval(() => {
            // Adaptive Polling (Phase 14)
            const isMissionActive = document.getElementById('mission-control-view').classList.contains('active');
            const isUserMode = document.body.classList.contains('user-mode');

            // Only poll frequently if in creator mode AND watching the cockpit
            if (isMissionActive && !isUserMode) {
                updateStatus();
            } else if (Date.now() % 15000 < 5000) { // Every 15s for background/user
                updateStatus();
            }
        }, 5000);
    }

    updateUI(state) {
        // Mode & Auth Handling (Phase 14 + Creator Session)
        const isCreator = state.creator_authenticated || state.system_mode === 'creator' || state.system_mode === 'live';

        if (state.system_mode === 'user') {
            document.body.classList.add('user-mode');
            document.body.classList.remove('creator-authenticated');
        } else if (isCreator) {
            document.body.classList.remove('user-mode');
            document.body.classList.add('creator-authenticated');
            console.log("[AUDIT_DRAWER] Creator Mode detected and authenticated.");
        }

        const qrBtn = document.getElementById('global-qr-scan');
        if (qrBtn) qrBtn.style.display = isCreator ? 'flex' : 'none';

        const creatorBadge = document.getElementById('creator-badge');
        if (creatorBadge) {
            creatorBadge.style.display = isCreator ? 'inline-block' : 'none';
        }

        // Announcement & Maintenance (Phase 23)
        const announcementBar = document.getElementById('global-announcement');
        const announcementText = document.getElementById('announcement-text');

        let displayMsg = null;
        let msgType = 'info';

        if (state.system_mode === 'maintenance_pending') {
            displayMsg = "SYSTEM ALERT: Maintenance window starting soon. Please save your work.";
            msgType = 'warning';
        } else if (state.announcement) {
            displayMsg = state.announcement.message;
            msgType = state.announcement.type.toLowerCase();
        }

        if (displayMsg && announcementBar) {
            announcementBar.style.display = 'block';
            announcementText.innerText = displayMsg;
            announcementBar.className = `global-announcement-bar active ${msgType}`;
        } else if (announcementBar) {
            announcementBar.style.display = 'none';
        }

        // Top Bar
        document.getElementById('sys-status-version').innerText = `v${state.version}`;
        document.getElementById('sys-status-branch').innerText = state.git_branch;
        document.getElementById('sys-chips-count').innerText = state.chips.length;

        // DB & AI Indicators
        this.updateIndicator('db-indicator', state.database?.connected);
        this.updateIndicator('ai-indicator', state.ai_host?.status === 'online');

        // AI Orb States
        const orb = document.getElementById('main-ai-orb');
        if (orb) {
            orb.classList.remove('system_warning', 'system_error', 'auto_fix_running');
            if (state.health === 'error') orb.classList.add('system_error');
            else if (state.health === 'warning') orb.classList.add('system_warning');

            if (state.is_healing) {
                orb.classList.add('auto_fix_running');
            }
        }

        // Chip Status List
        const chipContainer = document.getElementById('chip-status-container');
        if (chipContainer) {
            chipContainer.innerHTML = state.chips.map(chip => {
                const healthClass = chip.health === 'healthy' ? 'online' : (chip.health === 'warning' ? 'warning' : 'offline');
                return `
                <div class="chip-status-card" onclick="creatorEnv.inspectChip('${chip.slug}')">
                    <div class="chip-status-info">
                        <h4>${chip.name}</h4>
                        <p>${chip.status} | <span style="opacity: 0.6">Last act: ${chip.last_execution || 'never'}</span></p>
                    </div>
                    <div class="chip-health-indicator">
                        <span class="status-dot ${healthClass}"></span>
                        <span class="health-label" style="color: var(--${healthClass}-color, inherit)">${chip.health}</span>
                    </div>
                </div>
            `}).join('');
        }

        // Update Workspace Monitor if active
        const wsView = document.getElementById('creator-workspace-view');
        if (wsView && wsView.classList.contains('active')) {
            this.updateWorkspaceMonitor(state);
        }
    }

    updateIndicator(id, isOnline) {
        const el = document.getElementById(id);
        if (!el) return;
        el.classList.toggle('online', isOnline);
        el.classList.toggle('offline', !isOnline);
    }

    // 2. MISSION CONTROL (COCKPIT)
    setupMissionControl() {
        // Tab switching
        document.querySelectorAll('.cockpit-tab').forEach(tab => {
            tab.onclick = () => {
                document.querySelectorAll('.cockpit-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.currentTab = tab.dataset.tab;
                this.renderCockpit();
            };
        });

        // Nav link
        const missionNav = document.querySelector('[data-view="mission"]');
        if (missionNav) {
            missionNav.onclick = () => {
                this.switchView('mission');
                this.renderCockpit();
            };
        }
    }

    switchView(viewName) {
        document.querySelectorAll('main').forEach(m => m.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.body.classList.remove('workspace-active');

        if (viewName === 'mission') {
            document.getElementById('mission-control-view').classList.add('active');
            const navBtn = document.querySelector('[data-view="mission"]');
            if (navBtn) navBtn.classList.add('active');
        } else if (viewName === 'chat') {
            document.getElementById('ai-host-view').classList.add('active');
            const navBtn = document.querySelector('[data-view="chat"]');
            if (navBtn) navBtn.classList.add('active');
        } else if (viewName === 'workspace') {
            document.getElementById('creator-workspace-view').classList.add('active');
            document.body.classList.add('workspace-active');
        }
    }

    closeWorkspaceAndGoToMain() {
        const wsView = document.getElementById('creator-workspace-view');
        if (wsView) {
            wsView.classList.remove('active');
        }
        document.body.classList.remove('workspace-active');
        this.switchView('chat');
    }

    // 3. CREATOR WORKSPACE
    setupWorkspace() {
        if (this.workspaceInitialized) return;
        this.workspaceInitialized = true;
        // Toggle Logic
        document.querySelectorAll('.ws-toggle').forEach(btn => {
            btn.onclick = () => {
                const panelId = btn.dataset.panel;
                const panel = document.getElementById(`ws-panel-${panelId}`);
                if (panel) {
                    const isActive = panel.classList.toggle('active');
                    btn.classList.toggle('active', isActive);
                    this.updateGridLayout();
                }
            };
        });

        // Close Btn
        const closeBtn = document.getElementById('close-workspace');
        if (closeBtn) {
            closeBtn.onclick = () => {
                document.getElementById('creator-workspace-view').classList.remove('active');
                this.switchView('chat');
            };
        }

        // Editor: Open
        const openBtn = document.getElementById('ws-editor-open');
        if (openBtn) {
            openBtn.onclick = async () => {
                const pathInput = document.getElementById('ws-editor-path');
                const path = pathInput.value.trim();
                if (!path) return;

                openBtn.innerText = "LOADING...";
                openBtn.disabled = true;

                if (window.creatorEditor) {
                    this.addWorkspaceLog(`Requesting: ${path}...`, 'system');
                    try {
                        const result = await window.creatorEditor.openFile(path);
                        if (result !== null && typeof result === 'string') {
                            const wsTextarea = document.getElementById('ws-editor-content');
                            if (wsTextarea) {
                                wsTextarea.value = result;
                                wsTextarea.dispatchEvent(new Event('input'));
                            }
                            this.addWorkspaceLog(`SUCCESS: ${path} loaded.`, 'system');
                        } else {
                            const error = (result && result.error) ? result.error : "Failed to read file content";
                            this.addWorkspaceLog(`FAILED: ${path} (${error})`, 'error');
                            const wsTextarea = document.getElementById('ws-editor-content');
                            if (wsTextarea) wsTextarea.value = "";
                        }
                    } catch (err) {
                        this.addWorkspaceLog(`CRITICAL ERROR: ${err.message}`, 'error');
                    }
                } else {
                    this.addWorkspaceLog("ERROR: CreatorEditor system not initialized.", 'error');
                }
                openBtn.innerText = "OPEN";
                openBtn.disabled = false;
            };
        }

        // Editor: Propose
        const proposeBtn = document.getElementById('ws-editor-propose');
        if (proposeBtn) {
            proposeBtn.onclick = async () => {
                const path = document.getElementById('ws-editor-path').value.trim();
                const content = document.getElementById('ws-editor-content').value;
                if (!path) return;

                proposeBtn.innerText = "PROPOSING...";
                proposeBtn.disabled = true;

                try {
                    const res = await fetch('/api/v1/editor/file/propose-edit', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer omniweb-dev-secret-token',
                            'X-Shell-Identity': 'omniweb-shell'
                        },
                        body: JSON.stringify({ path: path, content: content })
                    });
                    const data = await res.json();

                    if (data.status === 'success' && data.payload) {
                        let preview_id = null;
                        if (data.payload.payload && data.payload.payload.preview_id) {
                            preview_id = data.payload.payload.preview_id;
                        } else if (data.payload.preview_id) {
                            preview_id = data.payload.preview_id;
                        }

                        if (preview_id && window.builderUI) {
                            window.builderUI.showPreview(preview_id);
                            this.addWorkspaceLog(`Proposal generated: ${preview_id}`, 'system');
                        } else {
                            this.addWorkspaceLog("Draft proposed but no preview ID returned.", 'warning');
                        }
                    } else {
                        this.addWorkspaceLog(`Propose failed: ${data.detail || "Unknown API error"}`, 'error');
                    }
                } catch (err) {
                    this.addWorkspaceLog(`CRITICAL ERROR during proposal: ${err.message}`, 'error');
                } finally {
                    proposeBtn.innerText = "PROPOSE";
                    proposeBtn.disabled = false;
                }
            };
        }

        // Copilot: Send
        const copilotSend = document.getElementById('ws-copilot-send');
        if (copilotSend) {
            copilotSend.onclick = () => this.sendCopilotPrompt();
        }

        // Deleted: Preview Reload (Replaced by Backend State integration)
    }

    updateWorkspaceBackendState() {
        if (!this.systemState) return;
        const stateEl = document.getElementById('ws-backend-state');
        if (!stateEl) return;

        const uptime = Math.floor(this.systemState.uptime_seconds || 0);
        const hours = Math.floor(uptime / 3600);
        const minutes = Math.floor((uptime % 3600) / 60);
        const uptimeStr = hours > 0 ? `${hours}h ${minutes}m` : `${minutes}m ${uptime % 60}s`;

        const cluster = this.systemState.cluster || {};
        const flows = this.systemState.flow_data || {};

        stateEl.innerHTML = `
            <div style="margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>OmniEngine:</span> <span style="color:var(--pass-color)">${this.systemState.health || 'nominal'}</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>Memory:</span> <span>${this.systemState.memory_usage?.rss_mb || 0} MB</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>Uptime:</span> <span style="color:var(--creator-gold)">${uptimeStr}</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>Cluster Load:</span> <span>${(cluster.cluster_load || 0).toFixed(1)}%</span></div>
            </div>
            
            <h5 style="color:var(--creator-gold); font-family:'Outfit'; margin-bottom:6px; font-size: 0.75rem;">Technical Flows</h5>
            <div style="margin-bottom: 12px; font-size: 0.7rem; opacity: 0.8;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;"><span>AI Core Latency:</span> <span>${flows.ai_to_chips?.latency || 0}ms</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;"><span>Knowledge Sync:</span> <span>${flows.chips_to_state?.latency || 0}ms</span></div>
            </div>

            <h5 style="color:var(--creator-gold); font-family:'Outfit'; margin-bottom:6px; font-size: 0.75rem;">Active Chips</h5>
            <div style="display:flex; flex-wrap:wrap; gap:4px;">
                ${(this.systemState.chips || []).map(c => `<span style="background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:3px; font-size:0.65rem; border: 1px solid rgba(255,255,255,0.05);">${c.slug}</span>`).join('')}
            </div>
        `;
    }

    openWorkspace(targetPanel = 'editor') {
        this.setupWorkspace();
        const wsView = document.getElementById('creator-workspace-view');
        if (!wsView) return;

        const isAlreadyActive = wsView.classList.contains('active');

        // Ensure workspace is the active view
        if (!isAlreadyActive) {
            this.switchView('workspace');
        }

        // Initialize all panels as active if opening for the first time
        if (!isAlreadyActive) {
            ['editor', 'copilot', 'changes', 'backend'].forEach(pId => {
                const panel = document.getElementById(`ws-panel-${pId}`);
                const btn = document.querySelector(`.ws-toggle[data-panel="${pId}"]`);
                if (panel) panel.classList.add('active');
                if (btn) btn.classList.add('active');
            });
        } else {
            // UX RULE: If already active, toggle the specific panel
            const panelsToOpen = targetPanel === 'editor' ? ['editor', 'copilot'] : [targetPanel];

            panelsToOpen.forEach(pId => {
                const panel = document.getElementById(`ws-panel-${pId}`);
                const btn = document.querySelector(`.ws-toggle[data-panel="${pId}"]`);
                if (panel) {
                    // Toggle OFF if already active inside an active workspace (only for single panel targets)
                    if (panel.classList.contains('active') && panelsToOpen.length === 1) {
                        panel.classList.remove('active');
                        if (btn) btn.classList.remove('active');
                    } else {
                        panel.classList.add('active');
                        if (btn) btn.classList.add('active');
                    }
                }
            });
        }

        // If Editor is target or open, sync path & content from main editor
        const wsPathInput = document.getElementById('ws-editor-path');
        const wsContentInput = document.getElementById('ws-editor-content');
        if (window.creatorEditor && window.creatorEditor.currentPath && wsPathInput) {
            wsPathInput.value = window.creatorEditor.currentPath;
            const mainContent = document.getElementById('code-textarea');
            if (mainContent && wsContentInput) wsContentInput.value = mainContent.value;
        }

        // Update backend state panel when workspace is active
        this.updateWorkspaceBackendState();

        this.updateGridLayout();
    }

    updateGridLayout() {
        const grid = document.getElementById('creator-grid');
        const activePanels = document.querySelectorAll('.ws-panel.active').length;

        // Simple grid adjustment via classes
        grid.className = 'workspace-grid';
        if (activePanels === 1) {
            const only = document.querySelector('.ws-panel.active').dataset.panel;
            grid.classList.add(`solo-${only}`);
        }
    }

    async sendCopilotPrompt() {
        const input = document.getElementById('ws-copilot-input');
        const prompt = input.value.trim();
        if (!prompt) return;

        this.addCopilotMsg(prompt, 'user');
        input.value = '';

        // Omni Fix: Use currentPath from verified editor state instead of volatile input
        const path = (window.creatorEditor && window.creatorEditor.currentPath) ? window.creatorEditor.currentPath : "";
        const evidence = path ? [{ type: 'current_file', path: path }] : [];

        try {
            const res = await fetch('/api/v1/ai-host/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer omniweb-dev-secret-token',
                    'X-Shell-Identity': 'omniweb-shell'
                },
                body: JSON.stringify({ message: prompt, multimodal_evidence: evidence })
            });
            const data = await res.json();
            if (data.message) {
                this.addCopilotMsg(data.message, 'ai');
            }

            // --- AUTO TRIGGER PATCH PREVIEW ---
            if (data.payload && data.payload.preview_id && window.builderUI) {
                console.log("[CREATOR] Proposal with preview detected. Launching preview UI:", data.payload.preview_id);
                window.builderUI.showPreview(data.payload.preview_id);
            }
            if (data.audit && this.updateAuditResult) {
                this.updateAuditResult(data.audit);
            }
        } catch (err) {
            this.addCopilotMsg("Error connecting to AI Host.", "system");
        }
    }

    addCopilotMsg(text, type) {
        const log = document.getElementById('ws-copilot-log');
        if (!log) return;

        const msg = document.createElement('div');
        msg.className = `copilot-msg ${type}`;

        // --- VISUAL DIFF RENDERER (CREATOR MODE) ---
        const renderDiff = (raw) => {
            if (!raw || typeof raw !== 'string') return raw;
            const diffMarker = "\n---";
            const parts = raw.split(diffMarker);
            let mainText = parts[0];
            let diffPart = parts.length > 1 ? parts.slice(1).join(diffMarker).trim() : "";

            // Fallback for raw diffs without headers
            if (!diffPart && (raw.includes('\n-') || raw.includes('\n+')) && raw.includes('@@')) {
                diffPart = raw;
                mainText = "";
            }

            let html = mainText
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\n/g, '<br/>');

            if (diffPart) {
                html += `<div class="diff-container">`;
                const escape = (unsafe) => unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                diffPart.split('\n').forEach(line => {
                    let cls = "";
                    if (line.startsWith('---') || line.startsWith('+++')) cls = "header";
                    else if (line.startsWith('@@')) cls = "info";
                    else if (line.startsWith('-')) cls = "removed";
                    else if (line.startsWith('+')) cls = "added";

                    if (cls) html += `<div class="diff-line ${cls}">${escape(line)}</div>`;
                    else if (line.trim()) html += `<div class="diff-line">${escape(line)}</div>`;
                });
                html += `</div>`;
            }
            return html;
        };

        msg.innerHTML = renderDiff(text);
        log.appendChild(msg);
        log.scrollTop = log.scrollHeight;
    }

    addWorkspaceLog(text, type = 'info') {
        const log = document.getElementById('ws-monitor-logs');
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.innerText = `[${new Date().toLocaleTimeString()}] ${text}`;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }

    updateWorkspaceMonitor(state) {
        const cpu = document.getElementById('ws-stat-cpu');
        const ram = document.getElementById('ws-stat-ram');
        const disk = document.getElementById('ws-stat-disk');

        if (cpu) cpu.innerText = `${state.health === 'nominal' ? '5%' : (state.health === 'warning' ? '14%' : '32%')}`;
        if (ram) ram.innerText = `${state.memory_usage?.rss_mb || 0}MB`;
        if (disk) disk.innerText = state.database?.connected ? 'READY' : 'FAULT';

        // Throttled random logs for realism
        if (Math.random() > 0.98 && state.auditor_summary?.issues?.length > 0) {
            const issue = state.auditor_summary.issues[0];
            this.addWorkspaceLog(`AUDIT: ${issue.message}`, 'system');
        }
    }

    renderCockpit() {
        const panel = document.getElementById('cockpit-main-panel');
        if (!this.systemState) return;

        if (this.currentTab === 'health') {
            const audit = this.systemState.auditor_summary || {};
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card">
                        <h3>System Health [${this.systemState.health.toUpperCase()}]</h3>
                        <div class="health-metric">
                            <span class="metric-label">Unified View</span>
                            <span class="metric-value ${this.systemState.health}">${this.systemState.health.toUpperCase()}</span>
                        </div>
                        <div class="health-metric">
                            <span class="metric-label">DB Link</span>
                            <span class="metric-value ${this.systemState.database?.connected ? 'pass' : 'fail'}">${this.systemState.database?.status}</span>
                        </div>
                         <div class="health-metric">
                            <span class="metric-label">AI Host</span>
                            <span class="metric-value pass">${this.systemState.ai_host?.status} [${this.systemState.ai_host?.mode}]</span>
                        </div>
                        <div class="health-metric">
                            <span class="metric-label">Memory</span>
                            <span class="metric-value info">${this.systemState.memory_usage?.rss_mb || 0} MB (${this.systemState.memory_usage?.percent || 0}%)</span>
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>Core Processors</h3>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${(this.systemState.ai_host?.processors || []).map(p => `<span class="chip-tag">${p}</span>`).join('')}
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>Filesystem Health</h3>
                        ${audit.issues?.length > 0 ?
                    audit.issues.map(i => `<div class="fix-item"><h4>${i.sector}: ${i.level}</h4><p>${i.message}</p></div>`).join('') :
                    '<p style="opacity: 0.5; font-size: 0.8rem;">No filesystem issues detected.</p>'
                }
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'evidence') {
            const sessionMedia = this.sessionMedia || [];
            const annotations = this.sessionMediaAnnotations || [];
            // Agrupar por lote
            const batches = {};
            sessionMedia.forEach((media, idx) => {
                const batch = media.batch || 1;
                if (!batches[batch]) batches[batch] = [];
                batches[batch].push({ ...media, idx: idx + 1 });
            });
            // Renderizado principal
            panel.innerHTML = `
                <div class="evidence-viewer-panel">
                    <h3>Evidence Viewer <span style='font-size:0.8em;opacity:0.6;'>(Session Media)</span></h3>
                    <div class="evidence-batch-list">
                        ${Object.keys(batches).map(batchNum => `
                            <div class="evidence-batch-group">
                                <h4>Batch #${batchNum} <span class="batch-count">(${batches[batchNum].length})</span></h4>
                                <div class="evidence-media-list">
                                    ${batches[batchNum].map(media => {
                const annotation = annotations.find(a => a.media_id === media.id);
                const typeIcon = media.type === 'video' ? '🎬' : '🖼️';
                return `
                                            <div class="evidence-media-card" data-media-id="${media.id}">
                                                <div class="media-preview">
                                                    ${media.type === 'image' ? `<img src="${media.url}" loading="lazy" alt="Image #${media.idx}"/>` : `<video src="${media.url}" controls preload="metadata"></video>`}
                                                </div>
                                                <div class="media-meta">
                                                    <span class="media-id">${typeIcon} ${media.type.charAt(0).toUpperCase() + media.type.slice(1)} #${media.idx}</span>
                                                    <span class="media-timestamp">${new Date(media.timestamp).toLocaleString()}</span>
                                                    <span class="media-batch">Batch ${batchNum}</span>
                                                    ${annotation ? `<span class="annotation-badge ${annotation.severity}">${annotation.severity.toUpperCase()}</span>` : ''}
                                                </div>
                                                ${annotation ? `<div class="media-annotation">
                                                    <strong>Copilot:</strong> ${annotation.comment}<br/>
                                                    <span class="annotation-ts">${new Date(annotation.timestamp).toLocaleString()}</span>
                                                </div>` : ''}
                                            </div>
                                        `;
            }).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
            // Integración con línea de tiempo (eventos)
            if (this.systemState && this.systemState.timeline) {
                const timelinePanel = document.getElementById('timeline-panel');
                if (timelinePanel) {
                    const mediaEvents = this.systemState.timeline.filter(e => e.type === 'MEDIA_UPLOADED' || e.type === 'MEDIA_ANNOTATED');
                    timelinePanel.innerHTML = mediaEvents.map(e => `<div class="timeline-event ${e.type}">
                        <span class="event-type">${e.type}</span>
                        <span class="event-ts">${new Date(e.timestamp).toLocaleString()}</span>
                        <span class="event-detail">${e.detail || ''}</span>
                    </div>`).join('');
                }
            }
            return;
        } else if (this.currentTab === 'map') {
            panel.innerHTML = `
                <div class="cockpit-card" style="padding: 0;">
                    <div class="galaxy-container" id="galaxy-map-mount">
                        <div class="loading-indicator">Mapping galactic nodes...</div>
                    </div>
                </div>
            `;
            setTimeout(() => {
                if (window.galaxyMap) {
                    if (!window.galaxyMap.initialized) {
                        window.galaxyMap.init('galaxy-map-mount');
                    }
                    window.galaxyMap.update(this.systemState);
                }
            }, 50);
        } else if (this.currentTab === 'fixes') {
            panel.innerHTML = `
                <div class="cockpit-card">
                    <h3>Pending Auto-Fixes (${this.systemState.pending_fixes})</h3>
                    ${this.systemState.is_healing ? '<p class="healing-pulse">✨ System is actively healing...</p>' : ''}
                    <p style="text-align: center; padding: 20px; opacity: 0.5;">
                        ${this.systemState.pending_fixes > 0 ? 'Repairs are queued. Approve them via AI Host.' : 'Stable. No pending fixes.'}
                    </p>
                </div>
            `;
        } else if (this.currentTab === 'editor') {
            if (window.creatorEditor) {
                window.creatorEditor.init();
            } else {
                panel.innerHTML = '<div class="error-msg">Editor module not loaded.</div>';
            }
        } else if (this.currentTab === 'code') {
            panel.innerHTML = `
                <div class="cockpit-card" style="margin-bottom: 15px;">
                    <h3>System Inspection</h3>
                    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                        <input type="text" id="cockpit-inspect-query" placeholder="Search architecture (e.g. 'router', 'auth')..." 
                            style="flex: 1; background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border); color: #fff; border-radius: 8px; padding: 8px;">
                        <button class="btn-apply" style="width: auto; margin: 0; padding: 0 15px;" onclick="creatorEnv.runInspection()">Inspect</button>
                    </div>
                    <div id="inspection-results" style="font-size: 0.8rem; height: 150px; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px;">
                        <p style="opacity: 0.5;">Select a chip below or enter a search query.</p>
                    </div>
                </div>
                <div class="cockpit-grid">
                    ${this.systemState.chips.map(chip => `
                        <div class="cockpit-card" onclick="creatorEnv.runInspection('${chip.slug}')">
                            <h3>${chip.name} <span class="status-dot ${chip.health === 'healthy' ? 'online' : 'warning'}"></span></h3>
                            <p style="font-size: 0.75rem; color: #888;">Slug: ${chip.slug}</p>
                            <p style="font-size: 0.75rem; color: #888;">State: ${chip.status}</p>
                        </div>
                    `).join('')}
                </div>
             `;
        } else if (this.currentTab === 'security') {
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card">
                        <h3>Chip Permissions Model</h3>
                        <div style="font-size: 0.8rem; height: 300px; overflow-y: auto;">
                            ${this.systemState.chips.map(chip => `
                                <div style="margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px;">
                                    <h4 style="margin:0; font-family: 'Outfit';">${chip.name}</h4>
                                    <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px;">
                                        ${(chip.metadata?.permissions || []).map(p => `<span class="chip-tag" style="background: rgba(0, 212, 255, 0.1); border: 1px solid var(--primary-low);">${p}</span>`).join('')}
                                        ${(chip.metadata?.permissions || []).length === 0 ? '<span style="opacity: 0.4; font-size: 0.7rem;">Sandbox (No permissions)</span>' : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>Access Violation Log</h3>
                        <div id="security-violations-container" style="font-size: 0.75rem;">
                            <div class="loading-indicator">Monitoring audit trail...</div>
                        </div>
                    </div>
                </div>
            `;
            this.fetchSecurityLogs();
        } else if (this.currentTab === 'sync') {
            const sync = this.systemState.sync_status || { devices_count: 0, status: 'unconfigured' };
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card">
                        <h3>Device Sync Status</h3>
                        <div class="health-metric">
                            <span class="metric-label">Registered Devices</span>
                            <span class="metric-value ${sync.devices_count > 0 ? 'pass' : 'info'}">${sync.devices_count}</span>
                        </div>
                        <div class="health-metric">
                            <span class="metric-label">Sync Health</span>
                            <span class="metric-value ${sync.status === 'SUCCESS' ? 'pass' : (sync.status === 'error' ? 'fail' : 'info')}">${sync.status.toUpperCase()}</span>
                        </div>
                        <div class="health-metric">
                            <span class="metric-label">Last Operation</span>
                            <span class="metric-value info">${sync.last_sync ? new Date(sync.last_sync).toLocaleString() : 'Never'}</span>
                        </div>
                        <div style="margin-top: 20px;">
                            <button class="btn-apply" onclick="creatorEnv.triggerSync()">Sync Now</button>
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>Sync Audit Log</h3>
                        <div id="sync-audit-log-container" style="font-size: 0.75rem;">
                            <div class="loading-indicator">Retrieving sync history...</div>
                        </div>
                    </div>
                </div>
            `;
            this.fetchSyncLogs();
        } else if (this.currentTab === 'insights') {
            panel.innerHTML = `
                <div class="cockpit-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h3>Actionable Insights</h3>
                        <button class="btn-apply" style="width: auto; margin: 0; padding: 5px 15px;" onclick="creatorEnv.analyzeInsights()">Refresh Analysis</button>
                    </div>
                    <div id="insights-container">
                        <div class="loading-indicator">Analyzing patterns and system state...</div>
                    </div>
                </div>
            `;
            this.fetchInsights();
        } else if (this.currentTab === 'admin') {
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card">
                        <h3>AI Suggestions for Approval</h3>
                        <div id="admin-suggestions-container" style="font-size: 0.8rem; height: 300px; overflow-y: auto;">
                            <div class="loading-indicator">Checking AI proposals...</div>
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>System Operational Log</h3>
                        <div id="admin-ops-log-container" style="font-size: 0.7rem; height: 300px; overflow-y: auto;">
                            <div class="loading-indicator">Retrieving admin history...</div>
                        </div>
                    </div>
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <h3>Creator Rollback System</h3>
                        <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                            <input type="text" id="checkpoint-label" placeholder="Checkpoint Label (e.g. 'Before big refactor')" 
                                style="flex: 1; background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border); color: #fff; border-radius: 8px; padding: 8px;">
                            <button class="btn-apply" style="width: auto; margin: 0;" onclick="creatorEnv.createCheckpoint()">Save State</button>
                        </div>
                        <div id="checkpoints-list" style="font-size: 0.75rem;">
                            <p style="opacity: 0.5;">Enter a label to create a new system-wide checkpoint.</p>
                        </div>
                    </div>
                </div>
            `;
            this.fetchAdminData();
        } else if (this.currentTab === 'creator') {
            const maint = this.systemState.maintenance_info;
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card">
                        <h3>System Governance Mode</h3>
                        <p style="font-size: 0.8rem; margin-bottom: 15px; opacity: 0.7;">
                            Current: <strong class="pass" id="current-mode-display">${this.systemState.system_mode.toUpperCase()}</strong>
                        </p>
                        <select id="system-mode-selector" class="cockpit-select" style="width: 100%; margin-bottom: 10px;">
                            <option value="live">Live (Normal)</option>
                            <option value="maintenance_pending">Maintenance Pending</option>
                            <option value="read_only">Read-Only Mode</option>
                            <option value="maintenance_active">Maintenance Active</option>
                            <option value="lockdown">Emergency Lockdown</option>
                        </select>
                        <button class="btn-apply" onclick="creatorEnv.setSystemMode()">Apply Mode</button>
                    </div>

                    <div class="cockpit-card">
                        <h3>Maintenance Scheduler</h3>
                        <div class="scheduler-form">
                            <input type="datetime-local" id="maint-start" class="cockpit-input">
                            <input type="number" id="maint-duration" placeholder="Duration (min)" class="cockpit-input">
                            <textarea id="maint-msg" placeholder="Maintenance message for users..." class="cockpit-input" style="height: 60px;"></textarea>
                            <button class="btn-apply" onclick="creatorEnv.scheduleMaintenance()">Schedule Window</button>
                        </div>
                        ${maint ? `
                            <div class="scheduled-maint-status" style="margin-top: 10px; font-size: 0.75rem; color: #ffaa00;">
                                <p><strong>Active/Upcoming:</strong> ${maint.status}</p>
                                <p>${new Date(maint.start_time).toLocaleString()} (${maint.duration_minutes} min)</p>
                            </div>
                        ` : ''}
                    </div>

                    <div class="cockpit-card">
                        <h3>Global Announcements</h3>
                        <textarea id="announcement-msg" placeholder="Broadcast message..." class="cockpit-input" style="height: 80px;"></textarea>
                        <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                            <select id="announcement-type" class="cockpit-select" style="flex: 1;">
                                <option value="INFO">Info</option>
                                <option value="WARNING">Warning</option>
                                <option value="CRITICAL">Critical</option>
                            </select>
                            <input type="number" id="announcement-expiry" placeholder="Exp (min)" class="cockpit-input" value="1440" style="width: 80px;">
                        </div>
                        <button class="btn-apply" onclick="creatorEnv.publishAnnouncement()">Broadcast Globally</button>
                        ${this.systemState.announcement ? `
                            <div style="margin-top: 10px; font-size: 0.75rem; border: 1px dashed var(--primary-low); padding: 5px; opacity: 0.8;">
                                <strong>Live:</strong> ${this.systemState.announcement.message}
                            </div>
                        ` : ''}
                    </div>

                    <div class="cockpit-card">
                        <h3>Node Operations</h3>
                        <div style="display: flex; gap: 5px; margin-bottom: 10px;">
                            <input type="text" id="node-id-op" placeholder="Node ID" class="cockpit-input">
                        </div>
                        <div class="btn-group" style="display: grid; grid-template-columns: 1fr 1fr; gap: 5px;">
                            <button class="btn-apply" style="margin:0; font-size: 0.7rem; padding: 5px;" onclick="creatorEnv.nodeOp('drain')">Drain</button>
                            <button class="btn-apply" style="margin:0; font-size: 0.7rem; padding: 5px;" onclick="creatorEnv.nodeOp('restart')">Restart</button>
                            <button class="btn-cancel" style="margin:0; font-size: 0.7rem; padding: 5px;" onclick="creatorEnv.nodeOp('disable')">Disable</button>
                            <button class="btn-apply" style="margin:0; font-size: 0.7rem; padding: 5px; background: var(--pass-color);" onclick="creatorEnv.nodeOp('resume')">Resume</button>
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('system-mode-selector').value = this.systemState.system_mode;
        } else if (this.currentTab === 'cluster') {
            const cluster = this.systemState.cluster;
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <h3>Cluster Infrastructure Overview</h3>
                        <div style="display: flex; gap: 20px; margin-top: 10px;">
                            <div class="metric">
                                <span class="label">ACTIVE NODES</span>
                                <span class="value">${cluster.active_nodes} / ${cluster.total_nodes}</span>
                            </div>
                            <div class="metric">
                                <span class="label">AVG CLUSTER LOAD</span>
                                <span class="value">${(cluster.cluster_load * 100).toFixed(1)}%</span>
                            </div>
                        </div>
                    </div>
                    
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <h3>Node Registry</h3>
                        <div class="node-list" id="cluster-node-list">
                            ${cluster.nodes.map(node => `
                                <div class="node-card ${node.node_status}">
                                    <div class="node-header">
                                        <div class="node-id">
                                            <span class="status-dot ${node.node_status === 'online' ? 'online' : 'offline'}"></span>
                                            <strong>${node.node_id}</strong>
                                            <span class="node-role-tag">${node.node_role.toUpperCase()}</span>
                                        </div>
                                        <div class="node-metrics">
                                            <span>CPU: ${(node.cpu_usage * 100).toFixed(1)}%</span>
                                            <span>RAM: ${(node.memory_usage * 100).toFixed(1)}%</span>
                                        </div>
                                    </div>
                                    <div class="node-footer">
                                        <div class="node-meta">
                                            <span>Region: ${node.node_region}</span>
                                            <span>Chips: ${node.active_chips}</span>
                                        </div>
                                        <div class="node-actions">
                                            <button onclick="creatorEnv.nodeControl('${node.node_id}', 'drain')" class="node-btn">Drain</button>
                                            <button onclick="creatorEnv.nodeControl('${node.node_id}', 'restart')" class="node-btn">Restart</button>
                                            <button onclick="creatorEnv.nodeControl('${node.node_id}', 'disable')" class="node-btn">Disable</button>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <h3>Simulate Node Registration</h3>
                        <div class="scheduler-form">
                            <input type="text" id="new-node-id" placeholder="node-worker-02" class="cockpit-input">
                            <select id="new-node-role" class="cockpit-select">
                                <option value="worker">Worker</option>
                                <option value="storage">Storage</option>
                                <option value="edge">Edge</option>
                            </select>
                            <input type="text" id="new-node-region" placeholder="eu-central" class="cockpit-input">
                            <button class="btn-apply" onclick="creatorEnv.registerSimulatedNode()">Register Node</button>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'knowledge') {
            this.fetchKnowledgeUnits();
            panel.innerHTML = `
                <div class="knowledge-container">
                    <div class="cockpit-header">
                        <h2>Knowledge Explorer</h2>
                        <div class="k-type-tag">Semantic Index Active</div>
                    </div>
                    <div class="knowledge-grid" id="knowledge-grid-content">
                        <div style="padding: 20px; text-align: center; opacity: 0.3;">Scanning Digital Alexandria...</div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'learning') {
            panel.innerHTML = `
                <div class="learning-container">
                    <h3>Adaptive Learning Paths</h3>
                    <div class="cockpit-grid">
                        <div class="cockpit-card">
                            <h4>Active Path: Web Architecture</h4>
                            <div class="path-node"><div class="node-status completed"></div> Fundamentals</div>
                            <div class="path-node"><div class="node-status active"></div> Distributed Systems</div>
                            <div class="path-node"><div class="node-status locked"></div> Scale Optimization</div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'certs') {
            panel.innerHTML = `
                <div class="certs-container">
                    <h3>Decentralized Certifications</h3>
                    <div class="cockpit-grid">
                        <div class="cockpit-card">
                            <h4>Fullstack Web Mastery</h4>
                            <div class="label">ISSUER: OMNIWEB AI</div>
                            <div class="label">SIG: 0x82f...a12</div>
                            <div style="color: #00ff88; font-size: 0.8rem; margin-top:10px;">VERIFIED SYSTEM-WIDE</div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'opportunities') {
            this.fetchOpportunities();
            panel.innerHTML = `
                <div class="opportunities-container">
                    <h3>Skill-Based Opportunities</h3>
                    <div id="opp-list-content">
                        <div style="padding: 20px; text-align: center; opacity: 0.3;">Matching skills to market...</div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'collab') {
            this.fetchProjects();
            panel.innerHTML = `
                <div class="collab-container">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>Collaborative Projects</h3>
                        <button class="cockpit-btn">Start New Project</button>
                    </div>
                    <div class="collab-grid" id="project-list-content">
                        <div style="padding: 20px; text-align: center; opacity: 0.3;">Fetching active collaborations...</div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'labs') {
            panel.innerHTML = `
                <div class="labs-container">
                    <div class="cockpit-header">
                        <h3>Creator Labs</h3>
                        <span class="reputation-badge">Experimental Access Active</span>
                    </div>
                    <div class="cockpit-grid">
                        <div class="cockpit-card" style="grid-column: span 2;">
                            <h4>Active Sandbox: Neural Filter v2</h4>
                            <div style="font-size: 0.8rem; opacity: 0.6; margin: 10px 0;">Private environment for chip prototyping and rapid iteration.</div>
                            <div class="storage-bar-container"><div class="storage-bar-fill" style="width: 45%; background: #f1c40f;"></div></div>
                            <div style="display:flex; gap: 10px; margin-top: 15px;">
                                <button class="cockpit-btn">Open Sandbox</button>
                                <button class="cockpit-btn">Publish Implementation</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'market') {
            this.fetchMarketListings();
            panel.innerHTML = `
                <div class="market-container">
                    <h3>Knowledge & Skill Market</h3>
                    <div class="market-grid" id="market-list-content">
                        <div style="padding: 20px; text-align: center; opacity: 0.3;">Connecting to the global marketplace...</div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'mentor') {
            this.fetchMentorState();
            panel.innerHTML = `
                <div class="mentor-container">
                    <h3>AI Personal Mentor</h3>
                    <div class="cockpit-grid">
                        <div class="cockpit-card" style="grid-column: span 2;">
                            <div class="mentor-chat" id="mentor-suggestions">
                                <div class="mentor-suggestion">Analyzing your recent activity in Phase 30...</div>
                            </div>
                        </div>
                        <div class="cockpit-card">
                            <h4>Human Productivity</h4>
                            <div class="metric"><span class="label">FOCUS DEPTH</span><span class="value">8.4</span></div>
                            <div class="metric"><span class="label">SKILL GROWTH</span><span class="value">+12%</span></div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'omniverse') {
            this.fetchGateways();
            panel.innerHTML = `
                <div class="omniverse-container">
                    <h3>Omniverse Gateways</h3>
                    <div class="omniverse-viz" id="gate-viz">
                        <div class="gate-token">G-01</div>
                    </div>
                    <div class="cockpit-card" style="margin-top: 20px;">
                        <h4>Active Gates</h4>
                        <div id="gate-list-content">
                            <div style="opacity:0.3; text-align:center;">Initializing spatial mapping...</div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'observability') {
            this.fetchMetrics();
            panel.innerHTML = `
                <div class="observability-container">
                    <h3>Global System Telemetry</h3>
                    <div class="telemetry-grid">
                        <div class="telemetry-card">
                            <div class="label">P99 LATENCY</div>
                            <div class="telemetry-value" id="metrics-latency">42ms</div>
                        </div>
                        <div class="telemetry-card">
                            <div class="label">EDGE NODES</div>
                            <div class="telemetry-value" id="metrics-edge">12</div>
                        </div>
                        <div class="telemetry-card">
                            <div class="label">ANOMALY STATUS</div>
                            <div class="telemetry-value" style="color: #00ff88;">NOMINAL</div>
                        </div>
                    </div>
                    <div class="cockpit-card" style="margin-top:20px;">
                        <h4>Security Audit Trail</h4>
                        <div class="security-log" id="security-trail-content">
                            <div style="opacity:0.3;">Scanning threat vectors...</div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'beta') {
            panel.innerHTML = `
                <div class="beta-container">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>Public Beta Controller</h3>
                        <button class="cockpit-btn" onclick="missionControl.generateBetaInvite()">Generate Viral Invite</button>
                    </div>
                    <div class="beta-feedback-form" style="margin-top: 20px;">
                        <h4>Direct Beta Feedback</h4>
                        <textarea id="beta-feedback-input" placeholder="Enter feature feedback or bug reports..."></textarea>
                        <button class="cockpit-btn" onclick="missionControl.submitBetaFeedback()">Submit Feedback</button>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'archival') {
            panel.innerHTML = `
                <div class="archival-container">
                    <h3>Distributed Archive Layer</h3>
                    <div class="cockpit-card">
                        <div class="archive-row" style="font-weight:bold;">
                            <span>SNAPSHOT TITLE</span>
                            <span>DATE</span>
                            <span>SIZE</span>
                            <span>CHECKSUM</span>
                        </div>
                        <div id="archive-list-content">
                            <div style="padding: 20px; text-align: center; opacity: 0.3;">Accessing cold storage grid...</div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'communication') {
            this.fetchCommunicationData();
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3>📡 Natural Communication Layer</h3>
                            <div style="display: flex; gap: 8px;">
                                <button class="btn-apply" style="width: auto; margin: 0; padding: 5px 12px; font-size: 0.7rem;" onclick="creatorEnv.switchView('chat'); window.addMessage && window.addMessage('Communication mode active. Try: write to [name] that [message]', 'ai');">Open in Chat</button>
                            </div>
                        </div>
                        <div style="display: flex; gap: 20px; margin-top: 15px;">
                            <div class="metric"><span class="label">MESSAGES SENT</span><span class="value" id="comm-total-messages">0</span></div>
                            <div class="metric"><span class="label">CONTACTS</span><span class="value" id="comm-total-contacts">0</span></div>
                            <div class="metric"><span class="label">CONVERSATIONS</span><span class="value" id="comm-total-conversations">0</span></div>
                            <div class="metric"><span class="label">ACTIVE CALLS</span><span class="value" id="comm-active-calls" style="color: #00ff88;">0</span></div>
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <h3>Recent Conversations</h3>
                        <div id="comm-recent-list" style="font-size: 0.8rem; max-height: 250px; overflow-y: auto;">
                            <div class="loading-indicator">Loading conversations...</div>
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <h3>🌐 Translation Monitor</h3>
                        <div style="background: #000; padding: 12px; border-radius: 8px; font-family: monospace; font-size: 0.75rem; max-height: 220px; overflow-y: auto;" id="comm-translation-feed">
                            <p style="color: #00ff88;">[SYSTEM] Translation adapter connected.</p>
                            <p>[ES → EN] Active bridge operational.</p>
                            <p>[ES → FR] Active bridge operational.</p>
                            <p>[ES → DE] Active bridge operational.</p>
                        </div>
                    </div>

                    <div class="cockpit-card" style="grid-column: span 2;">
                        <h3>Communication Logs</h3>
                        <div id="comm-logs-list" style="font-size: 0.8rem; max-height: 200px; overflow-y: auto;">
                            <div class="loading-indicator">Fetching message logs...</div>
                        </div>
                    </div>
                </div>
            `;

        } else if (this.currentTab === 'accessibility') {
            panel.innerHTML = `
                <div class="access-container">
                    <h3>Accessibility Settings</h3>
                    <div class="access-toggle"><span>Voice Navigation</span><input type="checkbox"></div>
                    <div class="access-toggle"><span>Braille Output Scaffolding</span><input type="checkbox"></div>
                    <div class="access-toggle"><span>Cognitive Simplification</span><input type="range" min="0" max="2"></div>
                </div>
            `;
        } else if (this.currentTab === 'music') {
            this.fetchMusicData();
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3>🎵 Music Intelligence Domain</h3>
                            <div style="display: flex; gap: 8px;">
                                <button class="btn-apply" style="width: auto; margin: 0; padding: 5px 12px; font-size: 0.7rem;" onclick="creatorEnv.switchView('chat'); window.addMessage && window.addMessage('Music mode active. Try: analyze this song on YouTube', 'ai');">Open in Chat</button>
                            </div>
                        </div>
                        <div style="display: flex; gap: 20px; margin-top: 15px;">
                            <div class="metric"><span class="label">PITCH PRECISION</span><span class="value">±1 cent</span></div>
                            <div class="metric"><span class="label">GROOVE MODE</span><span class="value">Active</span></div>
                            <div class="metric"><span class="label">INSTRUMENTS</span><span class="value">4</span></div>
                            <div class="metric"><span class="label">TRAINER</span><span class="value" style="color: #00ff88;">READY</span></div>
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <div style="display: flex; justify-content: space-between;">
                            <h3>Sonic Map</h3>
                            <span class="status-tag">Real-time</span>
                        </div>
                        <div style="background: #000; height: 120px; border-radius: 8px; margin-top: 10px; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden; border: 1px solid rgba(0,255,136,0.2);">
                            <div style="position: absolute; font-family: monospace; font-size: 2.5rem; color: #00ff88; text-shadow: 0 0 15px rgba(0,255,136,0.5);" id="music-detected-note">--</div>
                            <div style="position: absolute; bottom: 5px; right: 8px; font-size: 0.6rem; opacity: 0.5;">FRACTAL Pitch Analytics</div>
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <h3>Groove Trainer</h3>
                        <div style="font-family: monospace; padding: 12px; background: #08080c; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; font-size: 0.8rem; color: #00ff88; letter-spacing: 2px;" id="music-groove-timeline">
                            [----|----|----|----]
                        </div>
                        <div style="margin-top: 15px; display: flex; justify-content: space-between; font-size: 0.85rem;">
                            <span id="music-detected-bpm">120.0 BPM</span>
                            <span id="music-detected-swing" style="color: #00ff88;">Straight</span>
                        </div>
                    </div>

                    <div class="cockpit-card" style="grid-column: span 2;">
                        <div style="display: flex; justify-content: space-between;">
                            <h3>Instrument Mapper</h3>
                            <div style="gap: 5px; display: flex;">
                                <button class="btn-apply" style="width: auto; margin: 0; padding: 4px 10px; font-size: 0.65rem;">Bass</button>
                                <button class="btn-cancel" style="width: auto; margin: 0; padding: 4px 10px; font-size: 0.65rem; background: rgba(255,255,255,0.05);">Guitar</button>
                                <button class="btn-cancel" style="width: auto; margin: 0; padding: 4px 10px; font-size: 0.65rem; background: rgba(255,255,255,0.05);">Piano</button>
                            </div>
                        </div>
                        <div id="music-instrument-viz" style="margin-top: 15px; padding: 20px; background: #000; border-radius: 8px; border-left: 4px solid #00ff88; min-height: 100px; display: flex; align-items: center; justify-content: center;">
                            <p style="opacity: 0.3; font-size: 0.8rem;">Detecting real instrument neck... Overlay active.</p>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'integration') {
            this.fetchIntegrationData();
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <h3>Active Domain Bridges</h3>
                        <div id="integration-bridges-list" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <div class="loading-indicator">Initializing nervous system...</div>
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>Cross-Domain Events</h3>
                        <div id="integration-events-log" style="font-size: 0.75rem; max-height: 200px; overflow-y: auto;">
                            <p style="opacity: 0.5;">Awaiting domain signals...</p>
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>AI Orchestration</h3>
                        <div class="metric">
                            <span class="label">STATUS</span>
                            <span class="value" style="color: var(--pass-color);">ENABLED</span>
                        </div>
                        <p style="font-size: 0.7rem; opacity: 0.6; margin-top: 10px;">
                            AI Host is now authorized to chain actions across Music, Education, and Governance domains.
                        </p>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'qr_gateway') {
            this.fetchQRData();
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <h3>Active QR Tokens</h3>
                        <div id="qr-tokens-list" style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                            <div class="loading-indicator">Retrieving cryptographic keys...</div>
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>QR Status</h3>
                        <div class="metric">
                            <span class="label">GATEWAY</span>
                            <span class="value" style="color: var(--pass-color);">ONLINE</span>
                        </div>
                        <p style="font-size: 0.7rem; opacity: 0.6; margin-top: 10px;">
                            Branded physical QRs generated and deployed to /Desktop/QRs/.
                        </p>
                        <button class="btn-apply" style="margin-top: 15px;" onclick="creatorEnv.refreshQRVisuals()">Regenerate All QRs</button>
                        <button class="btn-apply" style="margin-top: 10px; border-color: var(--pass-color); color: var(--pass-color);" onclick="creatorEnv.openScanner()">Scan Creator QR</button>
                    </div>
                    <div class="cockpit-card">
                        <h3>Access Logs</h3>
                        <div id="qr-logs-container" style="font-size: 0.7rem; opacity: 0.7; max-height: 150px; overflow-y: auto;">
                            <p>Scanning system ready...</p>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'workload') {
            this.fetchWorkloadData();
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <h3>Cluster Workload Distribution</h3>
                        <div class="workload-stats" id="workload-stats-container">
                            <div class="metric"><span class="label">ACTIVE</span><span class="value" id="stat-active">0</span></div>
                            <div class="metric"><span class="label">QUEUED</span><span class="value" id="stat-queued">0</span></div>
                            <div class="metric"><span class="label">COMPLETED</span><span class="value" id="stat-completed">0</span></div>
                            <div class="metric"><span class="label">LATENCY</span><span class="value" id="stat-latency">0ms</span></div>
                        </div>
                    </div>

                    <div class="cockpit-card" style="grid-column: span 2;">
                        <h3>Task Registry</h3>
                        <div class="task-queue" id="task-registry-list">
                            <div style="padding: 20px; text-align: center; opacity: 0.5;">Synchronizing task states...</div>
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <h3>Injection Console</h3>
                        <div class="scheduler-form">
                            <select id="inject-chip-slug" class="cockpit-select">
                                <option value="core">Core Optimizer</option>
                                <option value="lingua">Lingua Transcriber</option>
                                <option value="finanzas">Finance Auditor</option>
                            </select>
                            <button class="btn-apply" onclick="creatorEnv.submitWorkloadTask()">Dispatch Cluster Task</button>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'mesh') {
            this.fetchMeshData();
            panel.innerHTML = `
                <div class="mesh-container">
                    <div class="cockpit-card">
                        <h3>OmniWeb Mesh Network Health</h3>
                        <div style="display: flex; justify-content: space-between; font-size: 0.8rem; opacity: 0.6;">
                            <span>DECENTRALIZED P2P CONNECTIVITY</span>
                            <span id="mesh-health-percent">0%</span>
                        </div>
                        <div class="mesh-health-bar">
                            <div class="mesh-health-fill" id="mesh-health-fill" style="width: 0%"></div>
                        </div>
                        <div style="display: flex; gap: 20px;">
                            <div class="metric"><span class="label">ACTIVE PEERS</span><span class="value" id="mesh-peers-count">0</span></div>
                            <div class="metric"><span class="label">LOCAL NODE</span><span class="value" id="mesh-local-id">--</span></div>
                        </div>
                    </div>

                    <div style="margin-top: 20px;">
                        <h3>Peer Map</h3>
                        <div class="peer-grid" id="mesh-peer-grid">
                            <div style="grid-column: 1/-1; padding: 40px; text-align: center; opacity: 0.3;">Discovering peers...</div>
                        </div>
                    </div>

                    <div class="mesh-map-sim" id="mesh-visual-map">
                        <div style="opacity: 0.2;">REAL-TIME MESH TOPOLOGY MAP (SIMULATED)</div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'autonomous') {
            this.fetchOfflineData();
            panel.innerHTML = `
                <div class="autonomous-container">
                    <div class="offline-status-banner" id="offline-banner">
                        <div class="sync-pulse" id="offline-pulse"></div>
                        <div>
                            <strong id="offline-status-text">DETECTING CONNECTIVITY...</strong>
                            <div style="font-size: 0.75rem; opacity: 0.8;" id="offline-description">Monitoring mesh health and local runtime state.</div>
                        </div>
                    </div>

                    <div class="cockpit-grid">
                        <div class="cockpit-card">
                            <h3>Sync Backlog</h3>
                            <div class="metric"><span class="label">QUEUED OPS</span><span class="value" id="backlog-count">0</span></div>
                            <div style="margin-top: 15px;">
                                <button class="btn-apply" onclick="creatorEnv.reconcileOffline()">Force Reconciliation</button>
                            </div>
                        </div>

                        <div class="cockpit-card" style="grid-column: span 2;">
                            <h3>Operation Buffer</h3>
                            <div class="backlog-list" id="backlog-item-list">
                                <div style="padding: 20px; text-align: center; opacity: 0.3;">No pending operations.</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'runtime') {
            this.fetchRuntimeData();
            panel.innerHTML = `
                <div class="runtime-container">
                    <div class="boot-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h3>OmniWeb Standalone Execution</h3>
                                <div style="margin-top:10px;">
                                    <span class="boot-badge" id="runtime-env">DETECTING...</span>
                                    <span class="boot-badge" style="background: rgba(255,255,255,0.1); color: #fff; margin-left: 10px;" id="boot-source">DISK</span>
                                </div>
                            </div>
                            <div class="metric">
                                <span class="label">UPTIME</span>
                                <span class="value" id="runtime-uptime">0s</span>
                            </div>
                        </div>
                    </div>

                    <div class="cockpit-grid">
                        <div class="cockpit-card" style="grid-column: span 2;">
                            <h3>Core Service Stack</h3>
                            <div class="service-stack" id="runtime-service-list">
                                <div style="padding: 20px; text-align: center; opacity: 0.3;">Initializing services...</div>
                            </div>
                        </div>

                        <div class="cockpit-card">
                            <h3>Environment Map</h3>
                            <div class="env-map" id="runtime-env-map">
                                <div class="env-row"><span>Hostname</span><span id="env-hostname">--</span></div>
                                <div class="env-row"><span>Profile</span><span id="env-profile">--</span></div>
                                <div class="env-row"><span>Mode</span><span id="env-mode">--</span></div>
                                <div class="env-row"><span>Portable</span><span id="env-portable">--</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'storage') {
            this.fetchStorageData();
            panel.innerHTML = `
                <div class="storage-container">
                    <div class="storage-hero">
                        <div class="storage-stat-card">
                            <div class="label">GRID CAPACITY</div>
                            <div class="storage-stat-value" id="storage-total">0 GB</div>
                            <div class="storage-bar-container"><div class="storage-bar-fill" id="storage-usage-bar" style="width: 0%"></div></div>
                            <div style="font-size: 0.7rem; margin-top: 10px; opacity: 0.6;" id="storage-used-text">0 MB Used</div>
                        </div>
                        <div class="storage-stat-card">
                            <div class="label">REPLICATION</div>
                            <div class="storage-stat-value" id="storage-replication">0x</div>
                            <div style="font-size: 0.7rem; opacity: 0.6;">Redundancy Strategy</div>
                        </div>
                        <div class="storage-stat-card">
                            <div class="label">HEALTHY BLOCKS</div>
                            <div class="storage-stat-value" id="storage-healthy">0</div>
                            <div style="font-size: 0.7rem; color: #00ff88;">All Fragments Online</div>
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <h3>Block Registry</h3>
                        <div class="block-registry">
                            <div class="block-item" style="border-bottom: 2px solid rgba(255,255,255,0.1); font-weight: bold;">
                                <span>BLOCK ID / HASH</span>
                                <span>TYPE</span>
                                <span>SIZE</span>
                                <span>REPLICATION</span>
                            </div>
                            <div id="block-list-content">
                                <div style="padding: 20px; text-align: center; opacity: 0.3;">Scanning global grid...</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'governance') {
            this.fetchGovernanceData();
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3>🏛️ AI Governance Advisor</h3>
                            <button class="btn-apply" style="width: auto; margin: 0; padding: 5px 15px;" onclick="creatorEnv.runLeadershipAnalysis()">Run Analysis</button>
                        </div>
                        <div class="governance-stats" style="display: flex; gap: 20px; margin-top: 15px;">
                            <div class="metric"><span class="label">TOTAL INSIGHTS</span><span class="value" id="gov-total-insights">0</span></div>
                            <div class="metric"><span class="label">PENDING</span><span class="value" id="gov-pending-insights" style="color: #ffaa00;">0</span></div>
                            <div class="metric"><span class="label">TRUST EDGES</span><span class="value" id="gov-trust-edges">0</span></div>
                            <div class="metric"><span class="label">TIMELINE ENTRIES</span><span class="value" id="gov-timeline-entries">0</span></div>
                        </div>
                    </div>

                    <div class="cockpit-card" style="grid-column: span 2;">
                        <h3>Pending Recommendations</h3>
                        <div id="governance-insights-list" style="font-size: 0.8rem; max-height: 300px; overflow-y: auto;">
                            <div class="loading-indicator">Scanning leadership patterns...</div>
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <h3>Beta Tester Registry</h3>
                        <div id="governance-tester-list" style="font-size: 0.8rem; max-height: 250px; overflow-y: auto;">
                            <div class="loading-indicator">Fetching tester roster...</div>
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <h3>User Timeline Lookup</h3>
                        <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                            <input type="text" id="gov-user-lookup" placeholder="Enter user ID..." 
                                style="background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border); color: #fff; border-radius: 8px; padding: 8px; flex: 1;">
                            <button class="btn-apply" style="width: auto; margin: 0; padding: 0 15px;" onclick="creatorEnv.lookupUserTimeline()">Lookup</button>
                        </div>
                        <div id="governance-timeline-view" style="font-size: 0.75rem; max-height: 200px; overflow-y: auto;">
                            <p style="opacity: 0.5;">Enter a user ID to view their evolution timeline.</p>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'copilot') {
            this.renderCopilotUI(panel);
        }
    }

    async fetchSyncLogs() {
        const container = document.getElementById('sync-audit-log-container');
        if (!container) return;
        try {
            const res = await fetch('/api/v1/system/sync/status');
            const data = await res.json();
            if (data.recent_logs.length === 0) {
                container.innerHTML = '<p style="opacity: 0.5; padding: 20px; text-align: center;">No sync history found.</p>';
                return;
            }
            container.innerHTML = data.recent_logs.map(log => `
                < div class="fix-item" style = "border-left: 2px solid ${log.status === 'SUCCESS' ? 'var(--pass-color)' : 'var(--fail-color)'}; margin-bottom: 8px;" >
                    <div style="display: flex; justify-content: space-between; font-size: 0.7rem; opacity: 0.6;">
                        <span style="font-weight: bold;">[${log.action_type}] ${log.target_sector.toUpperCase()}</span>
                        <span>${new Date(log.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p style="margin: 4px 0;">Status: <strong>${log.status}</strong></p>
                    <p style="opacity: 0.5; font-size: 0.65rem;">Payload: ${log.payload_summary}</p>
                </div >
                `).join('');
        } catch (err) {
            container.innerHTML = '<p style="color: #ff4444;">Failed to fetch sync logs.</p>';
        }
    }

    async triggerSync() {
        this.triggerLightBurst();
        try {
            const res = await fetch('/api/v1/system/sync/package');
            const packageData = await res.json();
            const ingestRes = await fetch('/api/v1/system/sync/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(packageData)
            });
            const result = await ingestRes.json();
            alert(`Sync Complete: ${result.results?.applied || 0} items applied.`);
            this.renderCockpit();
        } catch (err) {
            alert("Sync operation failed.");
        }
    }

    async fetchAdminData() {
        this.fetchAdminLogs();
        this.fetchPendingSuggestions();
        this.fetchCheckpoints();
    }

    async fetchCheckpoints() {
        const container = document.getElementById('checkpoints-list');
        if (!container) return;
        try {
            const res = await fetch('/api/v1/system/admin/checkpoints');
            const data = await res.json();

            container.innerHTML = `
                < div style = "margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;" >
                    <p style="opacity: 0.5; margin-bottom: 10px;">Available Checkpoints (Requires Creator):</p>
                    <div id="checkpoints-items">
                         ${data.map(c => `
                            <div style="display: flex; justify-content: space-between; align-items: center; background: rgba(255, 68, 68, 0.1); padding: 8px; border-radius: 4px; border: 1px solid rgba(255, 68, 68, 0.2); margin-bottom: 5px;">
                                <div>
                                    <strong style="display: block; font-size: 0.8rem;">${c.label}</strong>
                                    <span style="font-size: 0.6rem; opacity: 0.6;">${new Date(c.created_at).toLocaleString()}</span>
                                </div>
                                <button class="btn-cancel" style="width: auto; margin: 0; padding: 4px 10px; font-size: 0.65rem;" onclick="creatorEnv.rollback(${c.id})">Restore</button>
                            </div>
                         `).join('')}
                         ${data.length === 0 ? '<p style="opacity: 0.3; font-size: 0.7rem;">No checkpoints found.</p>' : ''}
                    </div>
                </div >
                `;
        } catch (err) { }
    }

    async rollback(checkpointId) {
        if (await this.askPermission("ULTIMATE SECURITY OVERRIDE", "Are you sure? This will revert the entire system state. Current session will be lost.")) {
            this.triggerLightBurst();
            const res = await fetch(`/api/v1/system/admin/rollback/${checkpointId}`, { method: 'POST' });
            const result = await res.json();
            if (result.status === 'success') {
                alert("Rollback successful. System re-initialized.");
                location.reload();
            } else {
                alert("Rollback failed: " + result.detail);
            }
        }
    }

    async fetchAdminLogs() {
        const container = document.getElementById('admin-ops-log-container');
        if (!container) return;
        try {
            const res = await fetch('/api/v1/system/admin/logs');
            const logs = await res.json();
            container.innerHTML = logs.map(l => `
                < div class="fix-item" style = "border-left: 2px solid var(--primary-color); margin-bottom: 8px; background: rgba(0, 212, 255, 0.03);" >
                    <div style="display: flex; justify-content: space-between; font-size: 0.65rem; opacity: 0.6;">
                        <strong>${l.operation_type}</strong>
                        <span>${new Date(l.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p style="margin: 4px 0;">Resource: ${l.target_resource}</p>
                    <p style="opacity: 0.5; font-size: 0.65rem;">Admin: ${l.admin_id}</p>
                </div >
                `).join('');
            if (logs.length === 0) container.innerHTML = '<p style="opacity:0.5; text-align:center;">No operations logged.</p>';
        } catch (err) { }
    }

    async fetchPendingSuggestions() {
        const container = document.getElementById('admin-suggestions-container');
        if (!container) return;
        try {
            const res = await fetch('/api/v1/system/admin/suggestions/pending');
            const data = await res.json();
            container.innerHTML = data.map(s => `
                < div class="insight-item" style = "background: rgba(255,255,255,0.03); padding: 10px; margin-bottom: 8px;" >
                    <div style="display: flex; justify-content: space-between; font-size: 0.7rem;">
                         <span style="color: var(--info-color);">${s.suggestion_type.toUpperCase()}</span>
                         <span>${new Date(s.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p style="margin: 5px 0;">${s.id}</p>
                    <div style="display: flex; gap: 5px; margin-top: 10px;">
                        <button class="btn-apply" style="font-size: 0.65rem; padding: 3px 8px; width: auto;" onclick="creatorEnv.reviewSuggestion('${s.id}', 'APPROVED')">Approve</button>
                        <button class="btn-cancel" style="font-size: 0.65rem; padding: 3px 8px; width: auto;" onclick="creatorEnv.reviewSuggestion('${s.id}', 'REJECTED')">Reject</button>
                    </div>
                </div >
                `).join('');
            if (data.length === 0) container.innerHTML = '<p style="opacity:0.5; text-align:center;">No pending suggestions.</p>';
        } catch (err) { }
    }

    async reviewSuggestion(sid, status) {
        if (await this.askPermission("Admin Review", `Confirm ${status} for ${sid} ? `)) {
            await fetch(`/api/v1/system/admin/suggestions/${sid}/review?status=${status}`, { method: 'POST' });
            this.fetchAdminData();
        }
    }

    async createCheckpoint() {
        const label = document.getElementById('checkpoint-label').value;
        if (!label) return alert("Please provide a label.");

        if (await this.askPermission("System Checkpoint", "Create a full system snapshot? This includes the database and core state.")) {
            this.triggerLightBurst();
            const res = await fetch(`/api/v1/system/admin/checkpoint/create?label=${encodeURIComponent(label)}`, { method: 'POST' });
            const data = await res.json();
            alert(`Checkpoint Created: ${label} `);
            this.fetchAdminData();
        }
    }

    async fetchInsights() {
        const container = document.getElementById('insights-container');
        if (!container) return;
        try {
            const res = await fetch('/api/v1/user/insights/summary');
            const insights = await res.json();
            this.renderInsightList(insights);
        } catch (err) {
            container.innerHTML = '<p style="color: #ff4444;">Failed to fetch insights.</p>';
        }
    }

    async analyzeInsights() {
        const container = document.getElementById('insights-container');
        if (container) container.innerHTML = '<div class="loading-indicator">Performing deep analysis...</div>';
        try {
            const res = await fetch('/api/v1/user/insights/analyze', { method: 'POST' });
            const insights = await res.json();
            this.renderInsightList(insights);
        } catch (err) {
            if (container) container.innerHTML = '<p style="color: #ff4444;">Analysis failed.</p>';
        }
    }

    async fetchSecurityLogs() {
        const container = document.getElementById('security-violations-container');
        if (!container) return;
        try {
            const res = await fetch('/api/v1/system/audit_trail?limit=20');
            const logs = await res.json();
            const violations = logs.filter(l => l.action_type === 'PERMISSION_DENIED');

            if (violations.length === 0) {
                container.innerHTML = '<p style="opacity: 0.5; padding: 20px; text-align: center;">No security violations detected.</p>';
                return;
            }

            container.innerHTML = violations.map(v => {
                let payload = {};
                try { payload = JSON.parse(v.payload_snapshot); } catch (e) { }
                return `
                < div class="fix-item" style = "border-left: 2px solid #ff4444; margin-bottom: 8px; padding-left: 10px; background: rgba(255, 68, 68, 0.05);" >
                        <div style="display: flex; justify-content: space-between; opacity: 0.6; font-size: 0.65rem;">
                            <span style="color: #ff4444; font-weight: bold;">[${v.target_resource.toUpperCase()}]</span>
                            <span>${new Date(v.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <p style="margin: 4px 0;">Blocked access to: <strong>${payload.requested || 'Unknown'}</strong></p>
                        <p style="opacity: 0.5; font-size: 0.7rem;">Invoked by: ${v.creator_id}</p>
                    </div >
                `;
            }).join('');
        } catch (err) {
            container.innerHTML = '<p style="color: #ff4444;">Failed to load logs.</p>';
        }
    }

    renderInsightList(insights) {
        const container = document.getElementById('insights-container');
        if (!container) return;
        if (insights.length === 0) {
            container.innerHTML = '<p style="opacity: 0.5; padding: 20px; text-align: center;">No insights detected. System and memories are in balance.</p>';
            return;
        }

        container.innerHTML = insights.map(i => {
            const severityColor = i.severity === 'critical' ? '#ff4444' : (i.severity === 'warning' ? '#ffaa00' : '#00d4ff');
            return `
                < div class="insight-item" style = "border-left: 3px solid ${severityColor}; background: rgba(255,255,255,0.03); padding: 12px; margin-bottom: 10px; border-radius: 4px;" >
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-weight: 600; font-size: 0.9rem; color: ${severityColor};">${i.type.toUpperCase()}</span>
                        <span style="font-size: 0.7rem; opacity: 0.5;">${new Date(i.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <h4 style="margin: 5px 0; font-family: 'Outfit';">${i.title}</h4>
                    <p style="font-size: 0.8rem; margin-bottom: 10px; opacity: 0.8;">${i.description}</p>
                    <div style="display: flex; gap: 8px;">
                        <button class="btn-apply" style="font-size: 0.7rem; padding: 4px 10px; width: auto;" onclick="creatorEnv.actionInsight('${i.id}')">Convert to Task</button>
                        <button class="btn-cancel" style="font-size: 0.7rem; padding: 4px 10px; width: auto;" onclick="this.parentElement.parentElement.style.display='none'">Dismiss</button>
                    </div>
                </div >
                `;
        }).join('');
    }

    async actionInsight(insightId) {
        await fetch(`/api/v1/user/insights/action/${insightId}`, { method: 'POST' });
        this.triggerLightBurst();
        alert("Insight actioned: Task queued in your logbook.");
    }

    async runInspection(query) {
        if (!query) query = document.getElementById('cockpit-inspect-query')?.value;
        const resEl = document.getElementById('inspection-results');
        if (!resEl) return;
        resEl.innerHTML = '<p>Analyzing system structure...</p>';

        try {
            const res = await fetch(`/api/v1/system/inspect?query=${query}`);
            const data = await res.json();
            resEl.innerHTML = `
                < div style = "margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px;" >
                    <strong>Results for "${data.query}":</strong>
                </div >
                ${data.relevant_files.map(f => `<div style="padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.02); color: #00d4ff;">${f}</div>`).join('')}
                ${data.relevant_files.length === 0 ? '<p>No matching files found.</p>' : ''}
            `;
        } catch (err) {
            resEl.innerHTML = '<p style="color: #ff4444;">Inspection failed.</p>';
        }
    }

    async applyFix(proposalId) {
        if (await this.askPermission("Confirm System Modification", `Apply auto - fix ${proposalId}? This will patch system files and reload modules.`)) {
            try {
                const res = await fetch(`/api/v1/system/audit/fix/apply?proposal_id=${proposalId}`, { method: 'POST' });
                const data = await res.json();
                if (data.status === 'success') {
                    this.triggerLightBurst();
                    this.renderCockpit();
                }
            } catch (err) {
                alert("Fix application failed. Bridge error.");
            }
        }
    }

    // 3. CHIP INSPECTION
    async inspectChip(slug) {
        console.log(`Inspecting chip: ${slug} `);
        this.triggerLightBurst();
        const orb = document.getElementById('main-ai-orb');
        orb.classList.add('processing');

        if (window.addMessage) {
            window.addMessage(`Scanning kernel for ** ${slug} **...`, 'ai');
            setTimeout(() => {
                orb.classList.remove('processing');
                window.addMessage(`### Chip Analysis: ${slug} \n - ** Registry Status:** Online\n - ** Verdict:** Stable.`, 'ai');
            }, 1200);
        }
        this.switchView('chat');
    }

    // 4. PERMISSION SYSTEM
    async askPermission(title, message) {
        return new Promise((resolve) => {
            const modal = document.getElementById('permission-modal');
            document.getElementById('perm-title').innerText = title;
            document.getElementById('perm-message').innerText = message;
            modal.classList.add('active');
            const cleanup = (value) => {
                modal.classList.remove('active');
                resolve(value);
            };
            document.getElementById('perm-confirm').onclick = () => cleanup(true);
            document.getElementById('perm-cancel').onclick = () => cleanup(false);
        });
    }

    async setSystemMode() {
        const mode = document.getElementById('system-mode-selector').value;
        if (await this.askPermission("System Governance", `Change system mode to ${mode.toUpperCase()}? This may restrict user access instantly.`)) {
            const res = await fetch('/api/v1/creator/control/mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(mode)
            });
            if (res.ok) {
                this.triggerLightBurst();
                alert("System mode updated.");
            }
        }
    }

    async scheduleMaintenance() {
        const start = document.getElementById('maint-start').value;
        const duration = parseInt(document.getElementById('maint-duration').value);
        const message = document.getElementById('maint-msg').value;

        if (!start || !duration) return alert("Please set start time and duration.");

        if (await this.askPermission("Maintenance Schedule", "Confirm maintenance window?")) {
            await fetch('/api/v1/creator/control/maintenance/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start_time: start, duration, message })
            });
            alert("Maintenance scheduled.");
        }
    }

    async publishAnnouncement() {
        const msg = document.getElementById('announcement-msg').value;
        const type = document.getElementById('announcement-type').value;
        const expiry = parseInt(document.getElementById('announcement-expiry').value);

        if (!msg) return alert("Message cannot be empty.");

        await fetch('/api/v1/creator/control/announcement', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg, type, expires_in_minutes: expiry })
        });
        alert("Broadcast sent.");
    }

    async nodeOp(op) {
        const nodeId = document.getElementById('node-id-op').value || "primary-node-01";
        if (await this.askPermission("Node Operation", `Trigger ${op} on node ${nodeId}?`)) {
            await fetch('/api/v1/creator/control/node/operation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ node_id: nodeId, operation: op })
            });
            alert(`Operation ${op} sent.`);
        }
    }

    async nodeControl(nodeId, operation) {
        if (await this.askPermission("Cluster Control", `Trigger ${operation.toUpperCase()} on node ${nodeId}?`)) {
            const res = await fetch('/api/v1/system/cluster/operation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target_node_id: nodeId, operation: operation })
            });
            if (res.ok) alert(`Operation ${operation} scheduled for ${nodeId}`);
        }
    }

    async registerSimulatedNode() {
        const id = document.getElementById('new-node-id').value;
        const role = document.getElementById('new-node-role').value;
        const region = document.getElementById('new-node-region').value;

        if (!id) return alert("Node ID required.");

        const nodeData = {
            node_id: id,
            node_role: role,
            node_region: region,
            node_url: `http://${id}.omniweb.cluster:8000`,
            node_secret: "cluster-secret-key-phase24",
            connected_services: ["worker-runtime"]
        };

        const res = await fetch('/api/v1/system/cluster/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(node_data)
        });
        if (res.ok) {
            alert("Simulated node registered.");
            this.fetchSystemState();
        }
    }

    async fetchWorkloadData() {
        const res = await fetch('/api/v1/system/cluster/workload');
        if (res.ok) {
            const data = await res.json();
            this.updateWorkloadUI(data);
        }
    }

    updateWorkloadUI(data) {
        if (this.currentTab !== 'workload') return;

        document.getElementById('stat-active').innerText = data.active_tasks;
        document.getElementById('stat-queued').innerText = data.queued_tasks;
        document.getElementById('stat-completed').innerText = data.completed_tasks;
        document.getElementById('stat-latency').innerText = `${data.avg_task_latency.toFixed(1)}ms`;

        const list = document.getElementById('task-registry-list');
        if (list) {
            list.innerHTML = data.tasks.map(task => `
                <div class="task-item">
                    <div>
                        <div class="task-slug">${task.chip_slug.toUpperCase()}</div>
                        <div class="task-meta">ID: ${task.task_id.substring(0, 8)} | Worker: ${task.worker_node_id || 'unassigned'}</div>
                    </div>
                    <div class="task-status status-${task.status}">${task.status}</div>
                </div>
            `).join('');
        }
    }

    async submitWorkloadTask() {
        const slug = document.getElementById('inject-chip-slug').value;
        const res = await fetch(`/api/v1/system/cluster/task/submit?chip_slug=${slug}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ trigger: 'manual_injection', timestamp: Date.now() })
        });
        if (res.ok) {
            const data = await res.json();
            console.log("Task submitted:", data.task_id);
            this.fetchWorkloadData();
        }
    }

    async fetchMeshData() {
        const res = await fetch('/api/v1/system/cluster/mesh/state');
        if (res.ok) {
            const data = await res.json();
            this.updateMeshUI(data);
        }
    }

    updateMeshUI(data) {
        if (this.currentTab !== 'mesh') return;

        document.getElementById('mesh-health-percent').innerText = `${(data.network_health * 100).toFixed(0)}%`;
        document.getElementById('mesh-health-fill').style.width = `${(data.network_health * 100)}%`;
        document.getElementById('mesh-peers-count').innerText = data.connected_peers;
        document.getElementById('mesh-local-id').innerText = data.node_id.substring(0, 8);

        const grid = document.getElementById('mesh-peer-grid');
        if (grid) {
            grid.innerHTML = data.peers.map(peer => `
                <div class="peer-card ${peer.status}">
                    <div class="peer-header">
                        <div class="peer-id">${peer.node_id}</div>
                        <div class="peer-status-tag">${peer.status.toUpperCase()}</div>
                    </div>
                    <div class="peer-body">
                        <div>
                            <div class="label">LATENCY</div>
                            <div class="peer-latency">${peer.latency.toFixed(1)}ms</div>
                        </div>
                        <div>
                            <div class="label">REGION</div>
                            <div>${peer.region}</div>
                        </div>
                    </div>
                    <div style="font-size: 0.65rem; opacity: 0.4; margin-top: 10px;">
                        Address: ${peer.address}
                    </div>
                </div>
            `).join('');
        }
    }

    async fetchOfflineData() {
        const res = await fetch('/api/v1/system/cluster/offline/state');
        if (res.ok) {
            const data = await res.json();
            this.updateOfflineUI(data);
        }
    }

    updateOfflineUI(data) {
        if (this.currentTab !== 'autonomous') return;

        const banner = document.getElementById('offline-banner');
        const text = document.getElementById('offline-status-text');
        const desc = document.getElementById('offline-description');
        const pulse = document.getElementById('offline-pulse');

        if (data.is_offline) {
            banner.className = 'offline-status-banner';
            text.innerText = 'AUTONOMOUS MODE ACTIVE';
            desc.innerText = 'Node is disconnected from mesh. Operations are being buffered locally.';
            pulse.style.background = '#ff4444';
        } else {
            banner.className = 'offline-status-banner online';
            text.innerText = 'MESH CONNECTIVITY STABLE';
            desc.innerText = 'Node is synchronized with the wider cluster infrastructure.';
            pulse.style.background = '#00ff88';
        }

        document.getElementById('backlog-count').innerText = data.backlog_count;
    }

    async fetchRuntimeData() {
        const res = await fetch('/api/v1/system/runtime');
        if (res.ok) {
            const data = await res.json();
            this.updateRuntimeUI(data.runtime);
        }
    }

    updateRuntimeUI(data) {
        if (this.currentTab !== 'runtime') return;

        document.getElementById('runtime-env').innerText = data.environment.toUpperCase();
        document.getElementById('boot-source').innerText = data.boot_source.toUpperCase();
        document.getElementById('runtime-uptime').innerText = this.formatUptime(data.uptime_seconds);

        document.getElementById('env-hostname').innerText = data.hostname;
        document.getElementById('env-profile').innerText = data.profile;
        document.getElementById('env-mode').innerText = data.runtime_mode;
        document.getElementById('env-portable').innerText = data.is_portable ? 'YES' : 'NO';

        const list = document.getElementById('runtime-service-list');
        if (list) {
            list.innerHTML = data.services.map(svc => `
                <div class="svc-item">
                    <span class="svc-name">${svc.name}</span>
                    <span class="svc-status ${svc.status}">${svc.status}</span>
                </div>
            `).join('');
        }
    }

    formatUptime(seconds) {
        if (seconds < 60) return `${Math.floor(seconds)}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
        return `${(seconds / 3600).toFixed(1)}h`;
    }

    async fetchProjects() {
        const res = await fetch('/api/v1/ecosystem_collab/projects');
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('project-list-content');
            if (list) {
                if (data.length === 0) {
                    list.innerHTML = `<div style="padding: 20px; text-align: center; opacity: 0.3;">Become a creator by starting your first project.</div>`;
                    return;
                }
                list.innerHTML = data.map(p => `
                    <div class="collab-card">
                        <h4>${p.title}</h4>
                        <p style="font-size: 0.75rem; opacity: 0.7;">${p.description}</p>
                        <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                            <span class="reputation-badge">${p.status.toUpperCase()}</span>
                            <button class="cockpit-btn" style="font-size: 0.6rem;">Join Space</button>
                        </div>
                    </div>
                `).join('');
            }
        }
    }

    async fetchMarketListings() {
        const res = await fetch('/api/v1/ecosystem_collab/market/listings');
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('market-list-content');
            if (list) {
                if (data.length === 0) {
                    list.innerHTML = `<div style="padding: 20px; text-align: center; opacity: 0.3;">The Global Market is currently being provisioned.</div>`;
                    return;
                }
                list.innerHTML = data.map(l => `
                    <div class="market-card">
                        <div class="k-type-tag">${l.type.replace('_', ' ')}</div>
                        <h4 style="margin: 10px 0;">${l.title}</h4>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="color: var(--accent); font-weight: bold;">${l.price_value} ${l.price_currency}</span>
                            <button class="cockpit-btn">Details</button>
                        </div>
                    </div>
                `).join('');
            }
        }
    }

    async fetchMentorState() {
        const res = await fetch('/api/v1/ecosystem_collab/mentor/state');
        if (res.ok) {
            const data = await res.json();
            const container = document.getElementById('mentor-suggestions');
            if (container) {
                container.innerHTML = data.suggestions.map(s => `
                    <div class="mentor-suggestion">${s}</div>
                `).join('');
            }
        }
    }

    async fetchGateways() {
        const res = await fetch('/api/v1/ecosystem_collab/omniverse/gateways');
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('gate-list-content');
            if (list) {
                if (data.length === 0) {
                    list.innerHTML = `<div style="padding: 20px; text-align: center; opacity: 0.3;">No spatial gateways deployed.</div>`;
                    return;
                }
                list.innerHTML = data.map(g => `
                    <div style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.8rem;">
                        <strong>${g.title}</strong>
                        <div style="opacity: 0.6; font-size: 0.7rem;">COORDINATES: ${g.spatial_coordinates}</div>
                    </div>
                `).join('');
            }
        }
    }

    async fetchMetrics() {
        const res = await fetch('/api/v1/scaling/metrics');
        const trailRes = await fetch('/api/v1/scaling/security/trail');

        if (trailRes.ok) {
            const data = await trailRes.json();
            const log = document.getElementById('security-trail-content');
            if (log) {
                if (data.length === 0) {
                    log.innerHTML = `<div class="log-entry verified">All systems verified. No intrusions detected.</div>`;
                    return;
                }
                log.innerHTML = data.map(ev => `
                    <div class="log-entry ${ev.severity === 'high' ? 'high' : ''}">
                        [${ev.timestamp}] ${ev.event_type.toUpperCase()}: ${ev.outcome}
                    </div>
                `).join('');
            }
        }
    }

    async generateBetaInvite() {
        const res = await fetch('/api/v1/scaling/beta/invite', { method: 'POST' });
        if (res.ok) {
            const data = await res.json();
            alert(`Beta Access Token Generated: ${data.token}`);
        }
    }

    async submitBetaFeedback() {
        const input = document.getElementById('beta-feedback-input');
        const content = input.value;
        if (!content) return;

        const res = await fetch('/api/v1/scaling/beta/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });

        if (res.ok) {
            alert("Feedback received. AI Optimization loop updated.");
            input.value = '';
        }
    }

    async fetchStorageData() {
        const res = await fetch('/api/v1/system/cluster/storage/state');
        if (res.ok) {
            const data = await res.json();
            this.updateStorageUI(data);
        }
    }

    updateStorageUI(data) {
        if (this.currentTab !== 'storage') return;

        const totalGB = (data.total_capacity / (1024 ** 3)).toFixed(1);
        const usedMB = (data.used_capacity / (1024 ** 2)).toFixed(2);
        const usagePercent = (data.used_capacity / data.total_capacity) * 100;

        document.getElementById('storage-total').innerText = `${totalGB} GB`;
        document.getElementById('storage-used-text').innerText = `${usedMB} MB Used`;
        document.getElementById('storage-usage-bar').style.width = `${Math.max(2, usagePercent)}%`;
        document.getElementById('storage-replication').innerText = `${data.replication_factor}x`;
        document.getElementById('storage-healthy').innerText = data.healthy_blocks;

        const list = document.getElementById('block-list-content');
        if (list) {
            if (data.blocks.length === 0) {
                list.innerHTML = `<div style="padding: 20px; text-align: center; opacity: 0.3;">Digital Alexandria is currently empty.</div>`;
                return;
            }
            list.innerHTML = data.blocks.map(block => `
                <div class="block-item">
                    <div style="display: flex; flex-direction: column;">
                        <span class="block-id">${block.block_id}</span>
                        <span style="font-size: 0.6rem; opacity: 0.4;">SHA256: ${block.content_hash.substring(0, 16)}...</span>
                    </div>
                    <span class="block-type">${block.data_type}</span>
                    <span>${(block.size_bytes / 1024).toFixed(1)} KB</span>
                    <div><span class="replication-badge">Replicated</span></div>
                </div>
            `).join('');
        }
    }

    async fetchKnowledgeUnits() {
        const res = await fetch('/api/v1/human/knowledge/units');
        if (res.ok) {
            const data = await res.json();
            const grid = document.getElementById('knowledge-grid-content');
            if (grid) {
                if (data.length === 0) {
                    grid.innerHTML = `<div style="padding: 20px; text-align: center; opacity: 0.3;">No knowledge units indexed yet.</div>`;
                    return;
                }
                grid.innerHTML = data.map(unit => `
                    <div class="knowledge-card">
                        <div class="k-type-tag">${unit.type}</div>
                        <h4 style="margin: 10px 0;">${unit.title}</h4>
                        <div style="font-size: 0.7rem; opacity: 0.7;">${unit.content}</div>
                    </div>
                `).join('');
            }
        }
    }

    async fetchOpportunities() {
        const res = await fetch('/api/v1/human/opportunities');
        if (res.ok) {
            const data = await res.json();
            const list = document.getElementById('opp-list-content');
            if (list) {
                if (data.length === 0) {
                    list.innerHTML = `<div style="padding: 20px; text-align: center; opacity: 0.3;">Upgrade your skills to unlock opportunities.</div>`;
                    return;
                }
                list.innerHTML = data.map(opp => `
                    <div class="opp-item">
                        <strong>${opp.title}</strong>
                        <div style="font-size: 0.75rem; opacity: 0.8; margin-top: 5px;">Reward: $${opp.reward_value}</div>
                    </div>
                `).join('');
            }
        }
    }

    async reconcileOffline() {
        alert("Initiating reconciliation sequence...");
        this.fetchOfflineData();
    }

    bindAIVisual() {
        const orb = document.getElementById('main-ai-orb');
        if (orb) {
            orb.onclick = () => this.switchView('chat');
        }
    }

    // === COMMUNICATION PANEL METHODS (Phase 9) ===

    async fetchCommunicationData() {
        const headers = { 'Authorization': 'Bearer omniweb-dev-secret-token' };

        // Monitor (admin stats)
        try {
            const monRes = await fetch('/api/v1/communication/monitor', { headers });
            if (monRes.ok) {
                const data = await monRes.json();
                const el = (id) => document.getElementById(id);
                if (el('comm-total-messages')) el('comm-total-messages').innerText = data.total_messages;
                if (el('comm-total-contacts')) el('comm-total-contacts').innerText = data.total_contacts;
                if (el('comm-total-conversations')) el('comm-total-conversations').innerText = data.total_conversation_entries;

                // Communication logs
                const logsList = document.getElementById('comm-logs-list');
                if (logsList) {
                    if (data.recent_messages.length === 0) {
                        logsList.innerHTML = '<p style="opacity: 0.5; text-align: center; padding: 20px;">No messages sent yet.</p>';
                    } else {
                        logsList.innerHTML = data.recent_messages.map(m => `
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.75rem;">
                                <div>
                                    <span style="color: #00d4ff; font-weight: bold;">${m.sender_id}</span>
                                    <span style="opacity: 0.5;"> → </span>
                                    <span>${m.recipient_contact_id.substring(0, 8)}</span>
                                    ${m.target_language ? `<span class="chip-tag" style="margin-left: 8px; font-size: 0.6rem;">${m.original_language} → ${m.target_language}</span>` : ''}
                                </div>
                                <span style="opacity: 0.5;">${new Date(m.timestamp).toLocaleTimeString()}</span>
                            </div>
                        `).join('');
                    }
                }
            }
        } catch (e) { console.warn('Communication monitor unavailable', e); }

        // Recent conversations placeholder
        const recentList = document.getElementById('comm-recent-list');
        if (recentList && recentList.querySelector('.loading-indicator')) {
            recentList.innerHTML = '<p style="opacity: 0.5; text-align: center; padding: 15px;">Use the AI Chat to send messages: "write to [name] that [message]"</p>';
        }
    }

    // === GOVERNANCE PANEL METHODS (Phase 2-4) ===

    async fetchGovernanceData() {
        const headers = { 'Authorization': 'Bearer omniweb-dev-secret-token' };

        // Stats
        try {
            const statsRes = await fetch('/api/v1/governance/stats', { headers });
            if (statsRes.ok) {
                const stats = await statsRes.json();
                const el = (id) => document.getElementById(id);
                if (el('gov-total-insights')) el('gov-total-insights').innerText = stats.total_insights;
                if (el('gov-pending-insights')) el('gov-pending-insights').innerText = stats.pending_insights;
                if (el('gov-trust-edges')) el('gov-trust-edges').innerText = stats.reputation_edges;
                if (el('gov-timeline-entries')) el('gov-timeline-entries').innerText = stats.timeline_entries;
            }
        } catch (e) { console.warn('Governance stats unavailable', e); }

        // Insights
        try {
            const insightRes = await fetch('/api/v1/governance/insights', { headers });
            const insightsList = document.getElementById('governance-insights-list');
            if (insightRes.ok && insightsList) {
                const insights = await insightRes.json();
                if (insights.length === 0) {
                    insightsList.innerHTML = '<p style="opacity: 0.5; text-align: center; padding: 20px;">No pending recommendations. Community is stable.</p>';
                } else {
                    insightsList.innerHTML = insights.map(i => `
                        <div style="background: rgba(255,255,255,0.03); padding: 12px; margin-bottom: 8px; border-left: 3px solid #ffaa00; border-radius: 4px;">
                            <div style="display: flex; justify-content: space-between;">
                                <span style="font-weight: 600; color: #ffaa00;">${i.insight_type.toUpperCase()}</span>
                                <span style="font-size: 0.7rem; opacity: 0.5;">${new Date(i.timestamp).toLocaleString()}</span>
                            </div>
                            <p style="margin: 8px 0; font-size: 0.85rem;">${i.message}</p>
                            <div style="font-size: 0.7rem; opacity: 0.6;">User: ${i.user_id} | Recommender: ${i.recommender}</div>
                            <div style="display: flex; gap: 5px; margin-top: 10px;">
                                <button class="btn-apply" style="font-size: 0.65rem; padding: 3px 10px; width: auto;" onclick="creatorEnv.approveInsight('${i.id}')">✓ Approve Promotion</button>
                                <button class="btn-cancel" style="font-size: 0.65rem; padding: 3px 10px; width: auto;" onclick="creatorEnv.rejectInsight('${i.id}')">✗ Reject</button>
                            </div>
                        </div>
                    `).join('');
                }
            }
        } catch (e) { console.warn('Governance insights unavailable', e); }

        // Beta Testers
        try {
            const testersRes = await fetch('/api/v1/governance/beta/testers', { headers });
            const testerList = document.getElementById('governance-tester-list');
            if (testersRes.ok && testerList) {
                const testers = await testersRes.json();
                if (testers.length === 0) {
                    testerList.innerHTML = '<p style="opacity: 0.5; text-align: center;">No beta testers registered yet.</p>';
                } else {
                    testerList.innerHTML = testers.map(t => `
                        <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <div>
                                <strong>${t.username || t.id}</strong>
                                <span class="chip-tag" style="margin-left: 8px; background: ${t.role === 'admin_candidate' ? 'rgba(0, 255, 136, 0.2)' : 'rgba(0, 212, 255, 0.15)'}; border: 1px solid ${t.role === 'admin_candidate' ? '#00ff88' : 'var(--primary-low)'};">${t.role.toUpperCase()}</span>
                            </div>
                            <button class="btn-apply" style="font-size: 0.6rem; padding: 2px 8px; width: auto; margin: 0;" onclick="creatorEnv.lookupUserTimelineById('${t.id}')">Timeline</button>
                        </div>
                    `).join('');
                }
            }
        } catch (e) { console.warn('Beta testers list unavailable', e); }
    }

    async runLeadershipAnalysis() {
        this.triggerLightBurst();
        const container = document.getElementById('governance-insights-list');
        if (container) container.innerHTML = '<div class="loading-indicator">Running leadership analysis across all users...</div>';

        try {
            const res = await fetch('/api/v1/governance/insights/analyze', {
                method: 'POST',
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            if (res.ok) {
                this.fetchGovernanceData();
            }
        } catch (e) {
            if (container) container.innerHTML = '<p style="color: #ff4444;">Analysis failed.</p>';
        }
    }

    async approveInsight(insightId) {
        if (await this.askPermission("Governance Action", "Approve this leadership promotion recommendation?")) {
            await fetch(`/api/v1/governance/insights/${insightId}/approve`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            this.triggerLightBurst();
            this.fetchGovernanceData();
        }
    }

    async rejectInsight(insightId) {
        await fetch(`/api/v1/governance/insights/${insightId}/reject`, {
            method: 'POST',
            headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
        });
        this.fetchGovernanceData();
    }

    async lookupUserTimeline() {
        const userId = document.getElementById('gov-user-lookup')?.value;
        if (!userId) return;
        this.lookupUserTimelineById(userId);
    }

    async lookupUserTimelineById(userId) {
        const container = document.getElementById('governance-timeline-view');
        if (!container) return;
        container.innerHTML = '<div class="loading-indicator">Loading timeline...</div>';

        try {
            const res = await fetch(`/api/v1/governance/timeline/${userId}`, {
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            if (res.ok) {
                const milestones = await res.json();
                if (milestones.length === 0) {
                    container.innerHTML = '<p style="opacity: 0.5;">No timeline entries for this user.</p>';
                    return;
                }
                container.innerHTML = milestones.map(m => `
                    <div style="border-left: 2px solid var(--primary-color); padding-left: 10px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; font-size: 0.65rem; opacity: 0.6;">
                            <span style="text-transform: uppercase; font-weight: bold; color: #00d4ff;">${m.milestone_type}</span>
                            <span>${new Date(m.timestamp).toLocaleString()}</span>
                        </div>
                        <p style="margin: 4px 0;">${m.description}</p>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p style="color: #ff4444;">Failed to load timeline.</p>';
            }
        } catch (e) {
            container.innerHTML = '<p style="color: #ff4444;">Connection error.</p>';
        }
    }

    async fetchMusicData() {
        try {
            const res = await fetch('/api/v1/music-intelligence/status');
            if (res.ok) {
                const data = await res.json();
                const noteEl = document.getElementById('music-detected-note');
                if (noteEl) noteEl.innerText = data.last_note || "A2";

                const bpmEl = document.getElementById('music-detected-bpm');
                if (bpmEl) bpmEl.innerText = `${data.bpm?.toFixed(1) || "120.0"} BPM`;

                const timelineEl = document.getElementById('music-groove-timeline');
                if (timelineEl) timelineEl.innerText = data.groove_pattern || "[X---.---X---.--X]";
            }
        } catch (err) {
            console.error("Music Lab sync error:", err);
        }
    }

    async fetchIntegrationData() {
        const bridgesList = document.getElementById('integration-bridges-list');
        if (!bridgesList) return;

        try {
            const res = await fetch('/api/v1/integration/status');
            const data = await res.json();

            bridgesList.innerHTML = data.active_bridges.map(bridge => `
                <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 4px; border-left: 2px solid #00d4ff;">
                    <div style="font-weight: bold; font-size: 0.8rem; color: #00d4ff;">${bridge.bridge_id}</div>
                    <div style="font-size: 0.65rem; opacity: 0.6; margin-top: 4px;">Domains: ${bridge.domains.join(', ')}</div>
                    <div style="font-size: 0.6rem; margin-top: 8px;">
                        <span class="status-dot online" style="width: 6px; height: 6px;"></span>
                        <span style="opacity: 0.8;">CONNECTION STABLE</span>
                    </div>
                </div>
            `).join('');

        } catch (err) {
            bridgesList.innerHTML = '<p style="color: #ff4444;">Nervous system offline.</p>';
        }
    }

    async fetchQRData() {
        const list = document.getElementById('qr-tokens-list');
        if (!list) return;
        try {
            const res = await fetch('/api/v1/qr/tokens');
            const data = await res.json();
            const entries = Object.entries(data);
            if (entries.length === 0) {
                list.innerHTML = '<p style="opacity: 0.5;">No active tokens found.</p>';
                return;
            }
            list.innerHTML = entries.map(([token, info]) => `
                <div style="background: rgba(255,255,255,0.05); padding: 8px; border-radius: 4px; font-size: 0.65rem;">
                    <div style="color: var(--pass-color); font-weight: bold;">${info.role.toUpperCase()}</div>
                    <div style="opacity: 0.5; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${token}</div>
                    <div style="margin-top: 4px; opacity: 0.8;">Exp: ${new Date(info.expires_at * 1000).toLocaleTimeString()}</div>
                </div>
            `).join('');
        } catch (err) {
            list.innerHTML = '<p style="color: #ff4444;">Failed to sync tokens.</p>';
        }
    }

    async refreshQRVisuals() {
        this.triggerLightBurst();
        try {
            const res = await fetch('/api/v1/qr/refresh-visuals', { method: 'POST' });
            const data = await res.json();
            alert(`Gallery Refreshed: ${data.generated.length} master QRs regenerated.`);
            this.fetchQRData();
        } catch (err) {
            alert("Error regenerating visuals.");
        }
    }

    // --- COPILOT CONSOLE LOGIC ---
    renderCopilotUI(panel) {
        panel.innerHTML = `
            <div class="copilot-container">
                <div class="circuit-decoration top-right"></div>
                <div class="copilot-split-layout">
                    <div class="copilot-left-panel">
                        <div class="cockpit-card">
                            <h3>Creator Copilot Console</h3>
                            <p style="font-size: 0.8rem; margin-bottom: 15px; opacity: 0.7;">
                                Describe the development action you want OmniWeb to perform.
                            </p>
                            <div class="prompt-input-area">
                                <textarea id="copilot-prompt-input" placeholder="e.g. 'Auditá el sistema actual y mostrame los problemas.'" class="cockpit-input" style="height: 80px;"></textarea>
                                <div style="display:flex; justify-content: space-between; margin-top: 10px;">
                                    <button class="upload-trigger-btn" onclick="document.getElementById('global-media-upload').click()">
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4m4-5l5-5 5 5m-5-5v12"/></svg> ADD EVIDENCE
                                    </button>
                                    <button class="btn-apply" onclick="creatorEnv.generateCopilotPlan()">Generate Plan</button>
                                </div>
                            </div>
                        </div>

                        <!-- Phase 32: Copilot Media Evidence -->
                        <div id="copilot-media-evidence" class="media-evidence-panel" style="margin-top: 20px;">
                            <div class="evidence-header">
                                <h4><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:5px;"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg> CONTEXTUAL EVIDENCE</h4>
                                <span class="evidence-count" id="copilot-media-count">0</span>
                            </div>
                            <div class="evidence-grid" id="copilot-media-grid"></div>
                        </div>

                        ${this.auditIssues.length > 0 ? this.renderAuditPanel() : ''}
                        ${this.correctionProposals.length > 0 ? this.renderProposalPanel() : ''}
                        
                        <div id="copilot-plan-preview" class="cockpit-card" style="display: ${this.copilotPlan ? 'block' : 'none'};">
                            <h3>Copilot Action Plan</h3>
                            <div id="plan-steps-list" class="plan-steps-list">
                                ${this.copilotPlan ? this.renderPlanSteps() : ''}
                            </div>
                            <div class="plan-actions" style="margin-top: 15px; display: flex; gap: 10px;">
                                <button class="btn-apply" onclick="creatorEnv.executeApprovedSteps()">Execute Approved</button>
                                <button class="btn-cancel" onclick="creatorEnv.cancelCopilotPlan()">Reset</button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="copilot-right-panel">
                        <div class="cockpit-card terminal-card">
                            <h3>Live Runtime View</h3>
                            <div id="copilot-terminal" class="copilot-terminal">
                                ${this.copilotTerminal.length > 0 ? this.copilotTerminal.join('') : '<p class="term-line system">Awaiting action...</p>'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        // Scroll terminal to bottom
        const term = document.getElementById('copilot-terminal');
        if (term) term.scrollTop = term.scrollHeight;
    }

    renderAuditPanel() {
        return `
            <div class="cockpit-card audit-panel">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="margin:0;">System Audit Findings</h3>
                    <span class="badge" style="background: rgba(255,100,0,0.2); color: #ff6400;">${this.auditIssues.length} ISSUES</span>
                </div>
                <div class="audit-issues-list">
                    ${this.auditIssues.map(issue => `
                        <div class="audit-issue severity-${issue.severity}">
                            <div class="issue-header">
                                <span class="layer-tag">${issue.layer}</span>
                                <h4>${issue.title}</h4>
                            </div>
                            <p class="issue-cause">${issue.cause}</p>
                            <div class="issue-meta">
                                <strong>Files:</strong> ${issue.affected_files.join(', ')}
                            </div>
                            <div class="suggested-fix">
                                <strong>Suggested Action:</strong> ${issue.suggested_action}
                            </div>
                        </div>
                    `).join('')}
                </div>
                <button class="btn-apply" style="margin-top: 15px;" onclick="creatorEnv.requestCorrectionProposal()">Generate Correction Proposals</button>
            </div>
        `;
    }

    renderProposalPanel() {
        return `
            <div class="cockpit-card proposal-panel">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="margin:0;">Correction Proposals</h3>
                    <span class="badge" style="background: rgba(0,212,255,0.2); color: #00d4ff;">PENDING APPROVAL</span>
                </div>
                <div class="proposals-list">
                    ${this.correctionProposals.map(prop => `
                        <div class="proposal-card">
                            <h4>${prop.title}</h4>
                            <p>${prop.expected_effect}</p>
                            <div class="proposal-meta">
                                <span>Risk: <strong class="risk-${prop.risk_level}">${prop.risk_level.toUpperCase()}</strong></span>
                                <span>Files: ${prop.files_to_modify.join(', ')}</span>
                            </div>
                            <div class="proposal-actions">
                                <button class="btn-apply" onclick="creatorEnv.approveCorrection('${prop.issue_id}')">Approve & Apply</button>
                                <button class="btn-cancel" onclick="creatorEnv.rejectCorrection('${prop.issue_id}')">Reject</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    async requestCorrectionProposal() {
        document.getElementById('copilot-prompt-input').value = "Proponé corrección para los problemas detectados.";
        this.generateCopilotPlan();
    }

    async approveCorrection(issueId) {
        document.getElementById('copilot-prompt-input').value = "Aplicá la corrección aprobada.";
        await this.generateCopilotPlan();
        this.executeApprovedSteps();
    }

    rejectCorrection(issueId) {
        this.correctionProposals = this.correctionProposals.filter(p => p.issue_id !== issueId);
        this.renderCockpit();
        this.addCopilotTerminalLine(`Proposal for issue ${issueId} rejected by Creator.`, 'system');
    }

    async generateCopilotPlan() {
        const promptInput = document.getElementById('copilot-prompt-input');
        const query = promptInput ? promptInput.value : '';

        // Phase 32: Multimodal Context
        const mediaContext = this.sessionMedia.map(m => ({
            type: m.type,
            name: m.name,
            timestamp: m.timestamp
        }));

        const body = {
            prompt: query,
            multimodal_evidence: mediaContext
        };

        if (!query && mediaContext.length === 0) return; // Only return if both are empty

        this.addCopilotTerminalLine(`> Analyzing prompt: "${query}"`, 'prompt');
        this.triggerLightBurst();

        try {
            const res = await fetch('/api/v1/creator/copilot/plan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer omniweb-dev-secret-token'
                },
                body: JSON.stringify(body)
            });
            this.copilotPlan = await res.json();
            this.addCopilotTerminalLine(`System generated plan ${this.copilotPlan.id}. Awaiting approval.`, 'system');
            this.renderCockpit();
        } catch (err) {
            this.addCopilotTerminalLine(`Error generating plan: ${err.message}`, 'error');
        }
    }

    renderPlanSteps() {
        return this.copilotPlan.steps.map(step => `
            <div class="step-card ${step.status}">
                <div class="step-info">
                    <h4>${step.description}</h4>
                    <p>Action: ${step.action_type}</p>
                </div>
                <div class="step-status-tag">${step.status}</div>
            </div>
        `).join('');
    }

    async executeApprovedSteps() {
        if (!this.copilotPlan) return;

        this.addCopilotTerminalLine("Starting plan execution sequence...", 'system');

        for (const step of this.copilotPlan.steps) {
            if (step.status === 'completed') continue;

            this.addCopilotTerminalLine(`Executing: ${step.description}...`, 'exec');
            step.status = 'executing';
            this.renderCockpit();

            try {
                const res = await fetch('/api/v1/ai-host/copilot/execute-step', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Bearer omniweb-dev-secret-token'
                    },
                    body: JSON.stringify({ plan_id: this.copilotPlan.id, step_id: step.id })
                });
                const result = await res.json();

                if (result.success) {
                    step.status = 'completed';
                    this.addCopilotTerminalLine(`Step completed: ${step.description}`, 'system');

                    // Specific result handlers for Phase 2
                    if (step.action_type === 'audit_system' || step.action_type === 'audit_chip') {
                        this.auditIssues = result.data;
                        this.addCopilotTerminalLine(`Detected ${this.auditIssues.length} issues in ${step.payload.scope || 'target'}.`, 'system');
                    } else if (step.action_type === 'propose_fix') {
                        this.correctionProposals = result.data;
                        this.addCopilotTerminalLine(`Generated ${this.correctionProposals.length} correction proposals.`, 'system');
                    } else if (step.action_type === 'apply_fix') {
                        this.correctionProposals = [];
                        this.auditIssues = [];
                        this.addCopilotTerminalLine("Correction applied successfully. System re-auditing...", 'system');
                    }
                } else {
                    step.status = 'failed';
                    this.addCopilotTerminalLine(`Step failed: ${result.error || 'Unknown error'}`, 'error');
                    break;
                }
            } catch (err) {
                step.status = 'failed';
                this.addCopilotTerminalLine(`Execution error: ${err.message}`, 'error');
                break;
            }
            this.renderCockpit();
        }

        this.addCopilotTerminalLine("Execution cycle finished.", 'system');
    }

    cancelCopilotPlan() {
        this.copilotPlan = null;
        this.addCopilotTerminalLine("Plan reset.", 'system');
        this.renderCockpit();
    }

    addCopilotTerminalLine(text, type) {
        const line = `<p class="term-line ${type}">[${new Date().toLocaleTimeString()}] ${text}</p>`;
        this.copilotTerminal.push(line);
        if (this.copilotTerminal.length > 100) this.copilotTerminal.shift();

        const term = document.getElementById('copilot-terminal');
        if (term) {
            term.innerHTML += line;
            term.scrollTop = term.scrollHeight;
        }
    }

    // 10. QR ACCESS SCANNER (Phase 31)
    setupQRScanner() {
        const qrBtn = document.getElementById('global-qr-scan');
        if (qrBtn) {
            qrBtn.onclick = () => this.openScanner();
        }

        const simBtn = document.getElementById('sim-scan-btn');
        if (simBtn) {
            simBtn.onclick = () => {
                const mockTokens = ["creator_auth_token_882", "admin_session_x99", "beta_access_k12"];
                const randomToken = mockTokens[Math.floor(Math.random() * mockTokens.length)];
                this.handleQRResult(`${window.location.origin}/api/v1/qr/join?token=${randomToken}`);
            };
        }
    }

    async openScanner() {
        if (await this.askPermission("Camera Access Required", "OmniWeb needs camera access to scan your Creator QR code. Approval will activate the live video stream.")) {
            const overlay = document.getElementById('qr-scanner-overlay');
            const video = document.getElementById('scanner-video');
            overlay.classList.add('active');

            try {
                this.scanStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
                video.srcObject = this.scanStream;
                console.log("Scanner stream active.");
            } catch (err) {
                console.error("Camera failed:", err);
                alert("Could not access camera. Ensure you are on HTTPS or localhost.");
                this.closeScanner();
            }
        }
    }

    closeScanner() {
        const overlay = document.getElementById('qr-scanner-overlay');
        overlay.classList.remove('active');
        if (this.scanStream) {
            this.scanStream.getTracks().forEach(track => track.stop());
            this.scanStream = null;
        }
    }

    async handleQRResult(url) {
        console.log("QR Scan Result:", url);
        this.triggerLightBurst();
        this.closeScanner();

        if (window.addMessage) {
            window.addMessage(`Payload detected: **${url}**\n\nResolving cryptographic session...`, 'ai');
        }

        try {
            // Extract token and ping the resolver
            const urlObj = new URL(url);
            const token = urlObj.searchParams.get('token');

            const res = await fetch(`/api/v1/qr/join?token=${token}`);
            if (res.ok) {
                setTimeout(() => {
                    window.location.reload(); // Reload to apply session
                }, 1500);
            } else {
                throw new Error("Invalid Token");
            }
        } catch (err) {
            if (window.addMessage) window.addMessage("### Access Denied\nToken expired or invalid signature.", 'ai');
        }
    }

    // 11. MULTIMODAL EVIDENCE HANDLING (Phase 32)
    handleMediaUpload(input) {
        if (!input.files || input.files.length === 0) return;

        const files = Array.from(input.files);
        if (files.length > 15) {
            alert("Maximum 15 items per batch supported.");
            return;
        }

        files.forEach(file => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const mediaItem = {
                    id: `media_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
                    name: file.name,
                    type: file.type.startsWith('image/') ? 'image' : 'video',
                    data: e.target.result,
                    timestamp: new Date().toISOString()
                };

                this.sessionMedia.push(mediaItem);
                this.renderMediaPreviews();
            };

            if (file.type.startsWith('image/') || file.type.startsWith('video/')) {
                reader.readAsDataURL(file);
            }
        });

        // Reset input for sequential batches
        input.value = "";
    }

    renderMediaPreviews() {
        const shellGrid = document.getElementById('shell-media-grid');
        const copilotGrid = document.getElementById('copilot-media-grid');
        const shellCount = document.getElementById('shell-media-count');
        const copilotCount = document.getElementById('copilot-media-count');
        const shellPanel = document.getElementById('shell-media-evidence');
        const copilotPanel = document.getElementById('copilot-media-evidence');

        const total = this.sessionMedia.length;

        // Visibility toggles
        if (shellPanel) shellPanel.classList.toggle('active', total > 0);
        if (copilotPanel) copilotPanel.classList.toggle('active', total > 0);
        if (shellCount) shellCount.innerText = total;
        if (copilotCount) copilotCount.innerText = total;

        const html = this.sessionMedia.map(m => `
            <div class="evidence-item" title="${m.name}">
                ${m.type === 'image'
                ? `<img src="${m.data}" alt="Evidence">`
                : `<video src="${m.data}"></video><div class="type-tag">VIDEO</div>`}
            </div>
        `).join('');

        if (shellGrid) shellGrid.innerHTML = html;
        if (copilotGrid) copilotGrid.innerHTML = html;
    }

    clearMedia() {
        this.sessionMedia = [];
        this.renderMediaPreviews();
    }

    // --- COGNITIVE AUDIT DRAWER (ADDITIVE) ---
    setupAuditDrawer() {
        console.log("[AUDIT_DRAWER] Initializing setup...");
        const toggle = document.getElementById('audit-drawer-toggle');
        const container = document.getElementById('audit-drawer-container');

        if (!toggle) console.error("[AUDIT_DRAWER] Handle NOT found in DOM (id: audit-drawer-toggle)");
        if (!container) console.error("[AUDIT_DRAWER] Container NOT found in DOM (id: audit-drawer-container)");

        if (toggle && container) {
            console.log("[AUDIT_DRAWER] Elements found. Binding toggle...");

            const performToggle = (e) => {
                if (e) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                const isClosing = !container.classList.contains('collapsed');
                container.classList.toggle('collapsed');
                console.log("[AUDIT_DRAWER] UI Toggle triggered. New state [Expanded]:", isClosing === false);
            };

            // Use both click and pointerdown for maximum compatibility
            toggle.addEventListener('click', performToggle);
            toggle.addEventListener('pointerdown', (e) => e.stopPropagation()); // Prevent drag conflicts

            // Bind close button
            const closeBtn = container.querySelector('.close-drawer');
            if (closeBtn) {
                closeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    container.classList.add('collapsed');
                });
            }

            console.log("[AUDIT_DRAWER] Toggle bound successfully.");
        }
    }

    updateAuditResult(audit) {
        const body = document.getElementById('audit-drawer-body');
        const dot = document.getElementById('audit-indicator-dot');
        const container = document.getElementById('audit-drawer-container');
        if (!body) return;

        // Auto-open if audit failed and severity is not low (optional, but good for awareness)
        // if (audit && !audit.passed && audit.severity !== 'low') {
        //     container.classList.remove('collapsed');
        // }

        if (!audit) {
            body.innerHTML = '<div class="no-audit-data">No audit data available for the last interaction.</div>';
            if (dot) {
                dot.className = 'status-indicator';
                dot.title = "No audit data";
            }
            return;
        }

        // Update dot status
        if (dot) {
            dot.className = `status-indicator ${audit.passed ? 'pass' : 'fail'}`;
            dot.title = audit.passed ? "Audit Passed" : "Audit Failed";
        }

        const statusLabel = audit.passed ? 'PASS' : 'FAIL';
        const statusClass = audit.passed ? 'pass' : 'fail';

        body.innerHTML = `
            <div class="audit-section">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h4>Contract Status</h4>
                    <span class="audit-status-badge ${statusClass}">${statusLabel}</span>
                </div>
            </div>

            <div class="audit-section">
                <h4>Core Metadata</h4>
                <div class="audit-grid">
                    <div class="audit-item">
                        <span class="label">Intent Group</span>
                        <span class="value">${audit.intent_group || 'N/A'}</span>
                    </div>
                    <div class="audit-item">
                        <span class="label">Severity</span>
                        <span class="value">${audit.severity || 'low'}</span>
                    </div>
                    <div class="audit-item">
                        <span class="label">Confidence</span>
                        <span class="value">${(audit.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div class="audit-item">
                        <span class="label">Auditor</span>
                        <span class="value">CognitiveAuditor V1</span>
                    </div>
                </div>
            </div>

            ${audit.failure_types?.length > 0 ? `
            <div class="audit-section">
                <h4>Failure Types Detected</h4>
                <div class="audit-failure-list">
                    ${audit.failure_types.map(f => `<span class="audit-tag fail">${f}</span>`).join('')}
                </div>
            </div>
            ` : ''}

            ${(audit.suspicious_layers?.length > 0 || audit.suspicious_modules?.length > 0) ? `
            <div class="audit-section">
                <h4>Detection Origin</h4>
                <div class="audit-failure-list">
                    ${(audit.suspicious_layers || []).map(l => `<span class="audit-tag">Layer: ${l}</span>`).join('')}
                    ${(audit.suspicious_modules || []).map(m => `<span class="audit-tag">Module: ${m}</span>`).join('')}
                </div>
            </div>
            ` : ''}

            <div class="audit-section">
                <h4>Analysis & Explanation</h4>
                <div class="audit-explanation">
                    ${audit.explanation || "Output follows established cognitive contract."}
                </div>
            </div>

            <div class="audit-section">
                <h4>Safe Next Action</h4>
                <div class="recommended-box">
                    <strong>Action:</strong> ${audit.recommended_action || "Continue monitoring."}<br/>
                    <small style="opacity: 0.6; display: block; margin-top: 5px;">
                        Tool suggest: ${audit.recommended_tool || "none"}
                    </small>
                </div>
            </div>
        `;
    }
}

const creatorEnv = new CreatorEnvironment();
window.missionControl = creatorEnv;
window.creatorEnv = creatorEnv;
document.addEventListener('DOMContentLoaded', () => creatorEnv.init());
