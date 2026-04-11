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
        this.lastCopilotResponse = null;

        // Phase 21: Visual Annotation Layer State
        this.currentAnnotatingMediaId = null;
        this.annotatorTool = 'point'; // 'point' | 'box'
        this.tempAnnotations = [];
        this.currentCorrectionStepId = null; // Phase 21: Track if we're correcting a rejected job
        this._pendingWorkspacePanel = null; // Fix for navigation loop
        this._navigationGuard = false;
        this.workspaceHasBeenOpenedBefore = false;
        this.modeController = null; // Block 01: Surface Mode Controller
    }

    init() {
        console.log("Initializing Creator Environment...");
        this.triggerLightBurst();
        this.startStatusPolling();
        this.setupPermissionModal();
        this.setupMissionControl();
        this.setupVisualAnnotator();
        this.bindAIVisual();
        this.setupQRScanner();
        this.setupAuditDrawer();

        // Block 01: Initialize Mode Surface Controller
        this.modeController = new SurfaceModeController(this);

        try {
            this.setupWorkspace();
        } catch (err) {
            console.error("Workspace Setup Failed:", err);
        }

        this.setupAdminShortcuts();

        // --- Emergency Readiness Pulse (Mission 36) ---
        // If telemetry is slow or fails, we don't leave the creator hanging in the dark.
        setTimeout(() => {
            const cockpitLoading = document.querySelector('#cockpit-main-panel .loading-indicator');
            if (cockpitLoading && !this.systemState) {
                console.warn("[CREATOR_BOOT] Slow telemetry detected. Rendering fallback UI...");
                cockpitLoading.innerHTML = "Telemetría lenta o bloqueada. Intentando re-vincular...";
                cockpitLoading.style.opacity = "0.5";

                // Only render fallback cockpit if NOT in user-mode
                if (!document.body.classList.contains('user-mode')) {
                    this.renderCockpit();
                }
            }
        }, 2500);

        setTimeout(() => {
            const hasAdminToken = localStorage.getItem('omni_token') || localStorage.getItem('omni_session');
            const urlParams = new URLSearchParams(window.location.search);
            const viewRequest = urlParams.get('view');
            const isUserMode = document.body.classList.contains('user-mode');

            // Block 01: Mode-Aware Auto Routing
            if (!viewRequest) {
                if (isUserMode) {
                    console.log("[USER_BOOT] Defaulting to Public Surface (Chat)");
                    this.switchView('chat');
                } else if (document.body.classList.contains('creator-authenticated') || hasAdminToken) {
                    console.log("[CREATOR_BOOT] Restoring default Creator session (Mission)...");
                    this.switchView('mission');
                    if (window.masterLogbook) window.masterLogbook.toggle(true);
                }
            } else if (viewRequest) {
                console.log("[CREATOR_BOOT] Respecting Deep Link view:", viewRequest);
                this.switchView(viewRequest);
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
        // Shared update function
        this.forceSync = async () => {
            try {
                const res = await fetch('/api/v1/system/state', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
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

        const pollLoop = async () => {
            await this.forceSync();

            // Adaptive Interval (Phase 16: Performance & Sync Hardening)
            let interval = 5000; // Normal
            const isMissionActive = this.systemState && this.systemState.active_mission &&
                ['OPEN', 'ACTIVE', 'RECOVERING'].includes(this.systemState.active_mission.status);
            const isWorkspaceVisible = document.getElementById('creator-workspace-view').classList.contains('active');

            if (isMissionActive) {
                interval = 1000; // FLUID SYNC (Matched with Adaptive Backend TTL)
            } else if (isWorkspaceVisible) {
                interval = 3000; // Normal Workspace
            } else {
                interval = 10000; // Low power background
            }

            this.statusInterval = setTimeout(pollLoop, interval);
        };

        pollLoop();
    }

    updateUI(state) {
        if (!state) return;

        // OMNI_MODE_SURFACE_POLISH_V1.3: Adaptive UI by Active Mode
        const mode = state.mode || 'PUBLIC';

        // Block 03: Workspace Persistence Restore
        if (state.space && state.space.space_id && window.workspaceManager && !this.workspaceRestored) {
            window.workspaceManager.restoreWorkspace();
            this.workspaceRestored = true;
        }

        // Body Class Hygiene
        document.body.classList.remove('mode-creator', 'mode-admin', 'mode-tester', 'mode-public', 'user-mode', 'creator-authenticated');
        document.body.classList.add(`mode-${mode.toLowerCase()}`);

        const isCreator = (mode === 'CREATOR');
        const isAdmin = (mode === 'ADMIN' || isCreator);
        const isTester = (mode === 'TESTER' || isAdmin);

        if (mode === 'PUBLIC') {
            document.body.classList.add('user-mode');
        } else if (isCreator) {
            document.body.classList.add('creator-authenticated');
        }

        const qrBtn = document.getElementById('global-qr-scan');
        if (qrBtn) qrBtn.style.display = isAdmin ? 'flex' : 'none';

        const creatorBadge = document.getElementById('creator-badge');
        if (creatorBadge) {
            creatorBadge.style.display = (mode === 'PUBLIC' ? 'none' : 'inline-block');
            creatorBadge.className = `mode-badge mode-${mode.toLowerCase()}`;
            creatorBadge.innerText = mode;
        }

        // Announcement & Maintenance (Phase 23)
        const announcementBar = document.getElementById('global-announcement');
        const announcementText = document.getElementById('announcement-text');

        let displayMsg = null;
        let msgType = 'info';

        if (state.system_mode === 'maintenance_pending') {
            displayMsg = "SISTEMA: Ventana de mantenimiento próximamente.";
            msgType = 'warning';
        } else if (state.announcement && state.announcement.message) {
            displayMsg = state.announcement.message;
            msgType = (state.announcement.type || 'info').toLowerCase();
        }

        if (displayMsg && announcementBar) {
            announcementBar.style.display = 'block';
            if (announcementText) announcementText.innerText = displayMsg;
            announcementBar.className = `global-announcement-bar active ${msgType}`;
        } else if (announcementBar) {
            announcementBar.style.display = 'none';
        }

        // Basic Info
        const verEl = document.getElementById('sys-status-version');
        if (verEl) verEl.innerText = `v${state.version || '0.0.0'}`;

        const branchEl = document.getElementById('sys-status-branch');
        if (branchEl) branchEl.innerText = state.git_branch || 'master';

        const chipEl = document.getElementById('sys-chips-count');
        if (chipEl) chipEl.innerText = (state.chips ? state.chips.length : 0);

        // Health Indicators
        this.updateIndicator('db-indicator', (state.database && state.database.connected));
        this.updateIndicator('ai-indicator', (state.ai_host && state.ai_host.status === 'online'));

        // Orb Effects
        const orb = document.getElementById('main-ai-orb');
        if (orb) {
            orb.classList.remove('system_warning', 'system_error', 'auto_fix_running');
            if (state.health === 'warning') orb.classList.add('system_warning');
            if (state.health === 'error') orb.classList.add('system_error');
            if (state.is_healing) orb.classList.add('auto_fix_running');
        }

        // Chip Status List (Restored for Hub Visibility & Sovereign Integration)
        const chipContainer = document.getElementById('chip-status-container');
        if (chipContainer && state.chips) {
            if (state.chips.length === 0) {
                chipContainer.innerHTML = '<div class="loading-indicator">No hay módulos cargados.</div>';
            } else {
                chipContainer.innerHTML = state.chips.map(chip => {
                    const healthClass = chip.health === 'healthy' ? 'online' : (chip.health === 'warning' ? 'warning' : 'offline');
                    const statusDotColor = healthClass === 'online' ? '#00ffcc' : (healthClass === 'warning' ? '#ffcc00' : '#ff4444');
                    return `
                     <div class="chip-status-card" onclick="if(window.creatorEnv && window.creatorEnv.inspectChip) window.creatorEnv.inspectChip('${chip.slug}')">
                         <div class="chip-status-info">
                             <h4>${chip.name}</h4>
                             <p title="${chip.description || ''}">${chip.status} | <span style="opacity: 0.6">Role: ${chip.type}</span></p>
                         </div>
                         <div class="chip-health-indicator">
                             <span class="status-dot ${healthClass}" style="background-color: ${statusDotColor}; box-shadow: 0 0 5px ${statusDotColor}"></span>
                             <span class="health-label" style="color: ${statusDotColor}">${chip.health}</span>
                         </div>
                     </div>
                 `}).join('');
            }
        }

        // Dashboard Dispatch (Additive)
        if (this.currentTab === 'health') {
            this.renderCockpit();
        }

        // Render Creator Dashboard components (MissionState, etc.)
        this.renderWorkspaceMissionDashboard(state);
        this.renderMissionPortfolio(state);
        this.renderRoadmap();

        // Update Editor with Swarm info
        if (window.creatorEditor) {
            window.creatorEditor.updateFromState(state);
        }

        // Block 01: Enforce Surface Boundaries
        if (this.modeController) {
            this.modeController.applySurfaceRestrictions(mode);
        }
    }

    renderWorkspaceMissionDashboard(state) {
        const mount = document.getElementById('ws-mission-mount');
        const panel = document.getElementById('ws-panel-mission');
        if (mount && panel && panel.classList.contains('active') && window.pizarronUI) {
            window.pizarronUI.renderInto(mount, {
                active_mission: state.active_mission,
                parallel_missions: state.parallel_missions,
                resource_locks: state.resource_locks
            });
        }
    }

    renderMissionPortfolio(state) {
        const mount = document.getElementById('ws-portfolio-mount');
        const panel = document.getElementById('ws-panel-portfolio');
        if (mount && panel && panel.classList.contains('active') && window.pizarronUI && window.pizarronUI.renderPortfolio) {
            window.pizarronUI.renderPortfolio(mount, state);
        }
    }

    renderRoadmap() {
        const mount = document.getElementById('ws-roadmap-mount');
        const panel = document.getElementById('ws-panel-roadmap');
        if (mount && panel && panel.classList.contains('active') && window.roadmapUI) {
            window.roadmapUI.refresh(); // Or pass data if we had it in systemState
            const grid = document.getElementById('creator-grid');
            if (grid) grid.classList.add('roadmap-focus');
        } else {
            const grid = document.getElementById('creator-grid');
            if (grid) grid.classList.remove('roadmap-focus');
        }
    }

    updateIndicator(id, status) {
        const el = document.getElementById(id);
        if (!el) return;

        // Remove all possible status classes
        el.classList.remove('online', 'offline', 'warning', 'neutral', 'unknown', 'deactivated');

        // Map Boolean or Enum status to CSS class
        let cssClass = 'offline';
        if (status === true || status === 'healthy' || status === 'online') cssClass = 'online';
        else if (status === 'warning') cssClass = 'warning';
        else if (status === 'unverified') cssClass = 'neutral';
        else if (status === 'deactivated') cssClass = 'deactivated';
        else if (status === 'unknown') cssClass = 'unknown';

        el.classList.add(cssClass);
    }

    // --- AUDIT SURFACE (Block 06) ---
    async fetchAuditSummary() {
        try {
            const res = await fetch('/api/v1/creator/control/audit/summary', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            if (!res.ok) throw new Error("Audit fetch failed");
            const data = await res.json();
            return data.payload?.audit_summary ? { history: data.payload.audit_summary } : { history: [] };
        } catch (err) {
            console.error("Audit summary fetch failed:", err);
            return { history: [] };
        }
    }

    async fetchStructuralDebt() {
        try {
            const res = await fetch('/api/v1/creator/control/audit/debt', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            if (!res.ok) throw new Error("Debt fetch failed");
            const data = await res.json();
            return data.payload?.debt_clusters || [];
        } catch (err) {
            console.error("Debt monitor fetch failed:", err);
            return [];
        }
    }

    async renderAuditSurface(panel) {
        panel.innerHTML = `<div class="loading-indicator">Auditando historial de verdad...</div>`;

        // Parallel fetch for summary and debt
        const [auditData, debtClusters] = await Promise.all([
            this.fetchAuditSummary(),
            this.fetchStructuralDebt()
        ]);

        if (!auditData.history || auditData.history.length === 0) {
            panel.innerHTML = `
                <div class="audit-empty" style="padding:40px; text-align:center;">
                    <h3 style="color:var(--accent);">HISTORIAL NOMINAL</h3>
                    <p style="opacity:0.5;">No hay misiones recientes registradas en el ledger de auditoría.</p>
                </div>`;
            return;
        }

        // 1. Render Debt Monitor Section
        let debtHtml = '';
        if (debtClusters && debtClusters.length > 0) {
            debtHtml = `
                <div class="debt-monitor-panel">
                    <div class="debt-header">
                        <h3 style="font-family:'Outfit'; font-size:0.8rem; letter-spacing:1px;">MONITOR DE DEUDA ESTRUCTURAL</h3>
                        <span class="audit-pill drift">${debtClusters.length} CLUSTERS DETECTADOS</span>
                    </div>
                    <div class="debt-grid">
                        ${debtClusters.map(cluster => `
                            <div class="debt-card">
                                <div class="severity-badge ${cluster.severity}">${cluster.severity}</div>
                                <div class="debt-sector">${cluster.sector}</div>
                                <div class="debt-metrics">
                                    <div class="debt-stat">⚠️ ${cluster.conflict_count} conflictos</div>
                                    <div class="debt-stat">📊 ${cluster.evidence_count} evidencias</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }

        let html = `
            ${debtHtml}
            <div class="audit-header" style="padding: 10px 20px; display:flex; justify-content:space-between; align-items:center;">
                <h2 style="font-family:'Outfit'; font-weight:300; letter-spacing:1px; color:var(--accent); margin:0;">EVIDENCE COCKPIT</h2>
                <span class="audit-pill aligned">${auditData.history.length} MISIONES</span>
            </div>
            <div class="audit-feed">`;

        data.history.forEach(entry => {
            const statusClass = `status-${(entry.outcome || 'aligned').toLowerCase()}`;
            const pillClass = (entry.outcome || 'aligned').toLowerCase();
            const verification = entry.verification || {};

            // Logic to determine verification UI
            const isAligned = verification.is_aligned;
            const verTag = isAligned ? 'ALINEADO' : 'CONFLICTO';
            const verTagClass = isAligned ? 'tag-success' : 'tag-error';
            const verIcon = isAligned ? '✅' : '⚠️';

            // Evidence parsing
            let evidenceHtml = `<div class="audit-empty-evidence" style="font-size:0.7rem; opacity:0.4;">Sin evidencia vinculada.</div>`;
            if (entry.artifacts && entry.artifacts.length > 0) {
                evidenceHtml = `
                    <div class="evidence-title">Evidencia Vinculada</div>
                    <div class="evidence-list">
                        ${entry.artifacts.map(art => `
                            <span class="evidence-tag" onclick="creatorEnv.openArtifactPreview('${art}')">
                                📄 ${art.split('/').pop()}
                            </span>
                        `).join('')}
                    </div>`;
            }

            html += `
                <div class="audit-card ${statusClass}">
                    <div class="audit-header">
                        <span class="audit-mission-name">${entry.mission_name}</span>
                        <span class="audit-pill ${pillClass}">${entry.outcome.toUpperCase()}</span>
                    </div>
                    <div class="audit-intent">${entry.goal || 'Sin objetivo definido'}</div>
                    
                    <div class="audit-evidence-box">
                        ${evidenceHtml}
                    </div>

                    <div class="audit-verification">
                        <div class="verification-icon">${verIcon}</div>
                        <div class="verification-text">
                            <span class="verification-tag-small ${verTagClass}">${verTag}</span>
                            ${verification.rationale || 'Sincronización de gobernanza nominal.'}
                        </div>
                    </div>
                </div>`;
        });

        html += `</div>`;
        panel.innerHTML = html;
    }

    // --- ARTIFACT PREVIEW HOOK ---
    async openArtifactPreview(path) {
        if (!path) return;

        // Use existing modal infrastructure
        const modal = document.getElementById('artifact-preview-modal');
        const content = document.getElementById('preview-content');
        const filename = document.getElementById('preview-filename');

        if (!modal || !content) return;

        filename.innerText = path.split('/').pop();
        content.innerHTML = `<div class="loading-indicator">Recuperando evidencia...</div>`;
        modal.style.display = 'flex';

        try {
            const res = await fetch(`/api/v1/creator/fs/read?path=${encodeURIComponent(path)}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            if (data.status === 'success') {
                content.innerHTML = `<pre style="font-family:monospace; font-size:0.8rem; padding:10px; color:#ccc; overflow:auto; max-height:60vh;">${this.escapeHtml(data.content)}</pre>`;
            } else {
                content.innerHTML = `<div class="error-msg">${data.error || 'No se pudo leer la evidencia.'}</div>`;
            }
        } catch (err) {
            content.innerHTML = `<div class="error-msg">Error de conexión con el FS.</div>`;
        }
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // 2. MISSION CONTROL (COCKPIT)
    setupMissionControl() {
        // Tab switching
        document.querySelectorAll('.cockpit-tab').forEach(tab => {
            tab.onclick = () => {
                document.querySelectorAll('.cockpit-tab').forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                this.currentTab = tab.dataset.tab;
                console.log("[CREATOR] Switching Cockpit Tab to:", this.currentTab);
                this.renderCockpit();
            };
        });

        // Nav link is now handled globally in main.js via .nav-item listener

    }

    switchView(viewName) {
        // --- GLOBAL VISUAL STATE MACHINE ---
        if (this._navigationGuard) {
            console.warn("[OMNI_NAV] Blocked recursive navigation to:", viewName);
            return;
        }

        // Block 01: Public Mode Safety Router
        const isPublic = document.body.classList.contains('user-mode');
        if (isPublic && (viewName === 'mission' || viewName === 'workspace')) {
            console.error(`[OMNI_GOVERNANCE] Access Denied: User attempted to enter ${viewName} while in PUBLIC mode.`);
            this.switchView('chat');
            return;
        }

        this._navigationGuard = true;

        try {
            console.log("[OMNI_NAV] Switching to view:", viewName);

            // 1. Overlay Toggles (Launcher & Context)
            if (viewName === 'context') {
                if (window.omniShell && window.omniShell.toggleContext) {
                    const panel = document.getElementById('context-panel');
                    const isCurrentlyActive = panel && panel.classList.contains('active');
                    window.omniShell.toggleContext(!isCurrentlyActive);
                }
                const navBtn = document.querySelector('[data-view="context"]');
                if (navBtn) {
                    const panel = document.getElementById('context-panel');
                    const isActive = panel && panel.classList.contains('active');
                    navBtn.classList.toggle('active', isActive);
                }
                return;
            }

            if (viewName === 'launcher') {
                if (window.omniShell && window.omniShell.setLauncherActive) window.omniShell.setLauncherActive();
                return;
            }

            // Close all overlays/chip views when switching to a primary view
            if (window.omniShell) {
                if (window.omniShell.closeLauncher) window.omniShell.closeLauncher();
                if (window.omniShell.toggleContext) window.omniShell.toggleContext(false);
            }
            const chipView = document.getElementById('active-chip-view');
            if (viewName === 'chip-view-active') {
                this._clearPrimaryViews();
                return;
            } else if (chipView) {
                chipView.classList.remove('active');
            }

            // --- PRIMARY VIEW ACTIVATION ---
            this._clearPrimaryViews();

            const inputBar = document.querySelector('.input-bar');
            if (inputBar) inputBar.style.display = (viewName === 'chat') ? 'flex' : 'none';

            // Creator Toolbar / Badge Logic (Persistence vs Contextual focus)
            const toolbar = document.getElementById('creator-toolbar');
            const badge = document.querySelector('.creator-badge');
            const showCreatorTools = (viewName !== 'chat');
            if (toolbar) toolbar.style.display = showCreatorTools ? 'flex' : 'none';
            if (badge) badge.style.display = showCreatorTools ? 'block' : 'none';

            const aiView = document.getElementById('ai-host-view');
            const missionView = document.getElementById('mission-control-view');
            const workspaceView = document.getElementById('creator-workspace-view');
            const userHomeView = document.getElementById('user-home-view');
            const navItems = document.querySelectorAll('.nav-item');

            if (aiView) aiView.classList.remove('active');
            if (missionView) missionView.classList.remove('active');
            if (workspaceView) workspaceView.classList.remove('active');
            if (userHomeView) userHomeView.classList.remove('active');

            navItems.forEach(n => n.classList.remove('active'));

            if (viewName === 'chat') {
                if (aiView) aiView.classList.add('active');
                document.querySelector('[data-view="chat"]').classList.add('active');
            } else if (viewName === 'mission') {
                if (missionView) missionView.classList.add('active');
                document.querySelector('[data-view="mission"]').classList.add('active');
                this.renderCockpit();
            } else if (viewName === 'workspace') {
                if (workspaceView) workspaceView.classList.add('active');
                document.querySelector('[data-view="workspace"]').classList.add('active');
                if (!this.workspaceHasBeenOpenedBefore) {
                    this.initWorkspaceLayout();
                    this.workspaceHasBeenOpenedBefore = true;
                }
            } else if (viewName === 'home') {
                if (userHomeView) userHomeView.classList.add('active');
                document.querySelector('[data-view="home"]').classList.add('active');
                this.fetchUserArtifacts();
            }
        } finally {
            this._navigationGuard = false;
        }
    }

    _clearPrimaryViews() {
        document.querySelectorAll('main').forEach(m => m.classList.remove('active'));
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.body.classList.remove('workspace-active');
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
                        this.addWorkspaceLog(`CRITICAL ERROR: ${err.message} `, 'error');
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
                            this.addWorkspaceLog(`Proposal generated: ${preview_id} `, 'system');
                        } else {
                            this.addWorkspaceLog("Draft proposed but no preview ID returned.", 'warning');
                        }
                    } else {
                        this.addWorkspaceLog(`Propose failed: ${data.detail || "Unknown API error"} `, 'error');
                    }
                } catch (err) {
                    this.addWorkspaceLog(`CRITICAL ERROR during proposal: ${err.message} `, 'error');
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

        // --- MEGAPROMPT LOGIC (MEGAPROMPTS & COMPILATION) ---
        const modeToggle = document.getElementById('ws-copilot-mode-toggle');
        const compileBtn = document.getElementById('ws-copilot-compile');
        const inputArea = document.getElementById('ws-copilot-input');

        if (modeToggle && compileBtn && inputArea) {
            modeToggle.onclick = () => {
                const isMegaprompt = modeToggle.classList.toggle('active');
                if (isMegaprompt) {
                    modeToggle.innerText = "CHAT MODE";
                    modeToggle.style.background = "rgba(0, 150, 255, 0.1)";
                    modeToggle.style.borderColor = "rgba(0, 150, 255, 0.3)";
                    modeToggle.style.color = "#0096ff";
                    inputArea.placeholder = "Pegué un Megaprompt aquí (Ej: 'MISIÓN: Refactorizar X...')";
                    inputArea.rows = 8;
                    compileBtn.style.display = 'block';
                    copilotSend.style.display = 'none';
                } else {
                    modeToggle.innerText = "MEGAPROMPT";
                    modeToggle.style.background = "rgba(212, 175, 55, 0.1)";
                    modeToggle.style.borderColor = "rgba(212, 175, 55, 0.3)";
                    modeToggle.style.color = "var(--creator-gold)";
                    inputArea.placeholder = "Ask Copilot (e.g. 'Analizá este archivo')";
                    inputArea.rows = 2;
                    compileBtn.style.display = 'none';
                    copilotSend.style.display = 'inline-block';
                }
            };

            compileBtn.onclick = async () => {
                const prompt = inputArea.value.trim();
                if (!prompt) return;

                compileBtn.innerText = "COMPILING...";
                compileBtn.disabled = true;

                // Add to chat as system command
                this.addCopilotMsg(`Compilando Megaprompt: "${prompt.substring(0, 50)}..."`, 'system');

                try {
                    // Send to backend with force mission flag
                    const res = await fetch('/api/v1/ai-host/process', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer omniweb-dev-secret-token',
                            'X-Shell-Identity': 'omniweb-shell'
                        },
                        body: JSON.stringify({
                            message: `MISSION: ${prompt}`,
                            source_surface: 'workspace',
                            options: { compile_only: false } // Trigger execution tree generation
                        })
                    });
                    const data = await res.json();
                    if (data.message) {
                        this.addCopilotMsg(data.message, 'ai');
                        // Switch to Mission panel to see the tree
                        this.openWorkspace('mission');
                    }
                } catch (err) {
                    this.addCopilotMsg("Error during mission compilation.", "error");
                } finally {
                    compileBtn.innerText = "COMPILE MISSION";
                    compileBtn.disabled = false;
                }
            };
        }
    }

    updateWorkspaceBackendState() {
        if (!this.systemState) return;
        const stateEl = document.getElementById('ws-backend-state');
        if (!stateEl) return;

        const uptime = Math.floor(this.systemState.uptime_seconds || 0);
        const hours = Math.floor(uptime / 3600);
        const minutes = Math.floor((uptime % 3600) / 60);
        const uptimeStr = hours > 0 ? `${hours}h ${minutes} m` : `${minutes}m ${uptime % 60} s`;

        const cluster = this.systemState.cluster || {};
        const flows = this.systemState.flow_data || {};

        stateEl.innerHTML = `
                < div style = "margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px;" >
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>OmniEngine:</span> <span style="color:var(--pass-color)">${this.systemState.health || 'nominal'}</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>Memory:</span> <span>${(this.systemState.memory_usage && this.systemState.memory_usage.rss_mb) || 0} MB</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>Uptime:</span> <span style="color:var(--creator-gold)">${uptimeStr}</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 4px;"><span>Cluster Load:</span> <span>${(cluster.cluster_load || 0).toFixed(1)}%</span></div>
            </div >
            
            <h5 style="color:var(--creator-gold); font-family:'Outfit'; margin-bottom:6px; font-size: 0.75rem;">Technical Flows</h5>
            <div style="margin-bottom: 12px; font-size: 0.7rem; opacity: 0.8;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;"><span>AI Core Latency:</span> <span>${(flows.ai_to_chips && flows.ai_to_chips.latency) || 0}ms</span></div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 2px;"><span>Knowledge Sync:</span> <span>${(flows.chips_to_state && flows.chips_to_state.latency) || 0}ms</span></div>
            </div>

            <h5 style="color:var(--creator-gold); font-family:'Outfit'; margin-bottom:6px; font-size: 0.75rem;">Active Chips</h5>
            <div style="display:flex; flex-wrap:wrap; gap:4px;">
                ${(this.systemState.chips || []).map(c => `<span style="background:rgba(255,255,255,0.1); padding:2px 6px; border-radius:3px; font-size:0.65rem; border: 1px solid rgba(255,255,255,0.05);">${c.slug}</span>`).join('')}
            </div>
            `;
    }

    openWorkspace(targetPanel = 'editor', skipSwitch = false) {
        this.setupWorkspace();
        const wsView = document.getElementById('creator-workspace-view');
        if (!wsView) return;

        const isAlreadyActive = wsView.classList.contains('active');

        // Ensure workspace is the active view
        if (!isAlreadyActive && !skipSwitch) {
            this._pendingWorkspacePanel = targetPanel;
            this.switchView('workspace');
            return;
        }

        // Initialize all panels as active ONLY if opening for the first time
        if (!this.workspaceHasBeenOpenedBefore) {
            this.workspaceHasBeenOpenedBefore = true;
            ['editor', 'copilot', 'changes', 'backend', 'mission', 'portfolio'].forEach(pId => {
                const panel = document.getElementById(`ws-panel-${pId}`);
                const btn = document.querySelector(`.ws-toggle[data-panel="${pId}"]`);
                if (panel) panel.classList.add('active');
                if (btn) btn.classList.add('active');
            });
        }

        // UX RULE: If targetPanel is explicitly requested (from outside or inside)
        if (targetPanel) {
            const panelsToOpen = targetPanel === 'editor' ? ['editor', 'copilot'] : [targetPanel];
            panelsToOpen.forEach(pId => {
                const panel = document.getElementById(`ws-panel-${pId}`);
                const btn = document.querySelector(`.ws-toggle[data-panel="${pId}"]`);
                if (panel) {
                    // Toggle OFF if already active inside an active workspace (only for single panel targets)
                    if (isAlreadyActive && panel.classList.contains('active') && panelsToOpen.length === 1) {
                        panel.classList.remove('active');
                        if (btn) btn.classList.remove('active');
                    } else {
                        // Otherwise ensure it's ON
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
        this.renderWorkspaceMissionDashboard(this.systemState);
        this.renderRoadmap();

        this.updateGridLayout();
    }

    openPizarron() {
        this.openWorkspace('mission');
    }

    updateGridLayout() {
        const grid = document.getElementById('creator-grid');
        const activePanels = document.querySelectorAll('.ws-panel.active').length;

        // Reset classes
        grid.className = 'workspace-grid';
        if (activePanels > 0) {
            grid.classList.add(`panels-${activePanels}`);
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
                body: JSON.stringify({
                    message: prompt,
                    multimodal_evidence: evidence,
                    source_surface: 'workspace'
                })
            });
            const data = await res.json();
            this.lastCopilotResponse = data;

            // --- MISSION INTAKE (COMMAND CONSOLE) ---
            if (data.payload && data.payload.tactical_overlay && data.payload.tactical_overlay.is_intake) {
                console.log("[CREATOR] Mission Intake Proposed. Opening Command Console.");
                const mount = document.getElementById('ws-intake-mount');
                const panel = document.getElementById('ws-panel-intake');
                const toggleBtn = document.querySelector('.ws-toggle[data-panel="intake"]');

                if (mount && window.pizarronUI) {
                    window.pizarronUI.renderIntakePanel(mount, data.payload.tactical_overlay.proposed_mission);

                    if (panel && !panel.classList.contains('active')) {
                        panel.classList.add('active');
                        if (toggleBtn) toggleBtn.classList.add('active');
                        this.updateGridLayout();
                    }
                }
            }

            // --- AUTO TRIGGER PATCH PREVIEW ---
            if (data.payload && data.payload.preview_id && window.builderUI) {
                console.log("[CREATOR] Proposal with preview detected. Launching preview UI:", data.payload.preview_id);
                window.builderUI.showPreview(data.payload.preview_id);
            }

            if (data.message) {
                this.addCopilotMsg(data.message, 'ai', data.payload);
                this.forceSync(); // IMMEDIATE FEEDBACK (Block 16)
            }
            if (data.audit && this.updateAuditResult) {
                this.updateAuditResult(data.audit);
            }
        } catch (err) {
            this.addCopilotMsg("Error talking to AI Host.", "error");
        }
    }

    addCopilotMsg(text, type, payload = null) {
        const log = document.getElementById('ws-copilot-log');
        if (!log) return;

        const mode = (this.systemState && this.systemState.mode) || 'PUBLIC';
        const isCreator = (mode === 'CREATOR');

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
                html += `< div class="diff-container" > `;
                const escape = (unsafe) => unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
                diffPart.split('\n').forEach(line => {
                    let cls = "";
                    if (line.startsWith('---') || line.startsWith('+++')) cls = "header";
                    else if (line.startsWith('@@')) cls = "info";
                    else if (line.startsWith('-')) cls = "removed";
                    else if (line.startsWith('+')) cls = "added";

                    if (cls) html += `< div class="diff-line ${cls}" > ${escape(line)}</div > `;
                    else if (line.trim()) html += `< div class="diff-line" > ${escape(line)}</div > `;
                });
                html += `</div > `;
            }
            return html;
        };

        msg.innerHTML = renderDiff(text);

        // --- PHASE 103: GOVERNANCE CHAT ENRICHMENT ---
        if (payload && payload.gov_enrichment && payload.gov_enrichment.count > 0) {
            payload.gov_enrichment.signals.forEach(s => {
                const sigEl = document.createElement('div');
                sigEl.className = `governance-chat-signal gov-signal-${s.severity_band}`;
                sigEl.innerHTML = `
                    <div class="gov-signal-header">
                        <span class="gov-signal-title">🛡️ GOBERNANZA: ${s.signal_type.replace(/_/g, ' ')}</span>
                        <span style="font-size: 0.5rem; opacity: 0.5;">${(s.confidence * 100).toFixed(0)}% Conf.</span>
                    </div>
                    <div class="gov-signal-rationale">${s.rationale}</div>
                    <div class="gov-signal-actions">
                        <button class="gov-action-btn" onclick="window.creator.handleGovChatAction('evidence', '${s.signal_id}', '${s.target_domain}')">VER EVIDENCIA</button>
                        ${(s.suggested_adjustment && isCreator) ? `
                            <button class="gov-action-btn primary" onclick="window.creator.handleGovChatAction('apply', '${s.signal_id}', ${JSON.stringify(s.adjustment_payload || "").replace(/"/g, '&quot;')})">APLICAR: ${s.suggested_adjustment}</button>
                        ` : ''}
                        <button class="gov-action-btn" onclick="this.parentElement.parentElement.remove()">IGNORAR</button>
                    </div>
                `;
                msg.appendChild(sigEl);
            });
        }

        // --- PHASE 21: VISUAL DIFF OVERLAY RENDERER ---
        if (payload && payload.visual_diff && payload.visual_context) {
            const vCtx = payload.visual_context;
            const diff = payload.visual_diff;

            const diffEl = document.createElement('div');
            diffEl.className = "visual-diff-chat-container";
            diffEl.style.cssText = "margin-top: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px solid rgba(255,170,0,0.2); padding: 10px; display: flex; gap: 12px; align-items: center;";

            diffEl.innerHTML = `
                <div style="position: relative; width: 80px; height: 80px; background: #000; border-radius: 6px; overflow: hidden; border: 1px solid rgba(255,170,0,0.3); flex-shrink: 0;">
                    <img src="${vCtx.source_image}" style="width:100%; height:100%; object-fit: cover; opacity: 0.5;">
                    ${(diff.removed_regions || []).map(r => `<div style="position:absolute; left:${r.x}%; top:${r.y}%; width:4px; height:4px; background:#ff4444; border-radius:50%; transform:translate(-50%, -50%); box-shadow: 0 0 5px #ff4444;"></div>`).join('')}
                    ${(diff.persistent_regions || []).map(r => `<div style="position:absolute; left:${r.x}%; top:${r.y}%; width:2px; height:2px; background:#ffaa00; border-radius:50%; transform:translate(-50%, -50%);"></div>`).join('')}
                    ${(diff.added_regions || []).map(r => `<div style="position:absolute; left:${r.x}%; top:${r.y}%; width:6px; height:6px; background:#00ff88; border-radius:50%; transform:translate(-50%, -50%); border: 1px solid #fff; box-shadow: 0 0 8px #00ff88;"></div>`).join('')}
                </div>
                <div style="flex: 1;">
                    <div style="font-size: 0.65rem; color: #ffaa00; font-weight: bold; margin-bottom: 2px;">Δ VISUAL DETECTADO</div>
                    <div style="font-size: 0.6rem; color: #aaa; line-height: 1.2;">
                        <span style="color: #00ff88;">+${diff.added_count} puntos de foco</span><br/>
                        <span style="color: #ff4444;">-${diff.removed_count} regiones descartadas</span>
                    </div>
                </div>
            `;
            msg.appendChild(diffEl);
        }

        log.appendChild(msg);
        log.scrollTop = log.scrollHeight;
    }

    handleGovChatAction(action, signalId, data) {
        console.log(`[GOVERNANZA] Chat Action: ${action} on ${signalId}`, data);

        if (action === 'evidence') {
            // Navigate to Heatmap or learning surface context
            this.openPizarron();
            if (window.pizarronUI) {
                // Focus on domain in heatmap if possible
                console.log("Requesting deep evidence for", data);
            }
        } else if (action === 'apply') {
            if (window.pizarronUI && data) {
                const payload = typeof data === 'string' ? JSON.parse(data) : data;
                window.pizarronUI.applyCopilotAdjustment(payload);
                this.addWorkspaceLog(`Ajuste de gobernanza aplicado desde chat: ${signalId}`, 'success');
            }
        }

        // Log the interaction for traceability
        fetch(`/api/v1/governance/trace/interaction`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ signal_id: signalId, action: action })
        }).catch(e => console.warn("Failed to log gov interaction", e));
    }

    addWorkspaceLog(text, type = 'info') {
        const log = document.getElementById('ws-monitor-logs');
        const entry = document.createElement('div');
        entry.className = `log-entry ${type}`;
        entry.innerText = `[${new Date().toLocaleTimeString()}] ${text} `;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }

    updateWorkspaceMonitor(state) {
        const cpu = document.getElementById('ws-stat-cpu');
        const ram = document.getElementById('ws-stat-ram');
        const disk = document.getElementById('ws-stat-disk');

        if (cpu) cpu.innerText = `${state.health === 'nominal' ? '5%' : (state.health === 'warning' ? '14%' : '32%')} `;
        if (ram) ram.innerText = `${(state.memory_usage && state.memory_usage.rss_mb) || 0} MB`;
        if (disk) disk.innerText = (state.database && state.database.connected) ? 'READY' : 'FAULT';

        // Throttled random logs for realism
        if (Math.random() > 0.98 && state.auditor_summary && state.auditor_summary.issues && state.auditor_summary.issues.length > 0) {
            const issue = state.auditor_summary.issues[0];
            this.addWorkspaceLog(`AUDIT: ${issue.message} `, 'system');
        }
    }

    renderCockpit() {
        const panel = document.getElementById('cockpit-main-panel');
        if (!panel) return;

        if (!this.systemState) {
            panel.innerHTML = `<div style="text-align:center; padding:40px; color:#666;">
                <p>TELEMETRÍA PENDIENTE</p>
                <small>Conectando con el núcleo cognitivo...</small>
            </div>`;
            return;
        }

        const mode = this.systemState.mode || 'PUBLIC';
        const isCreator = mode === 'CREATOR';
        const isAdmin = mode === 'ADMIN' || isCreator;
        const isTester = mode === 'TESTER' || isAdmin;

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
                            <span class="metric-value ${(this.systemState.database && this.systemState.database.connected) ? 'pass' : 'fail'}">${(this.systemState.database && this.systemState.database.status) || 'OFF'}</span>
                        </div>
                         <div class="health-metric">
                            <span class="metric-label">AI Host</span>
                            <span class="metric-value pass">${(this.systemState.ai_host && this.systemState.ai_host.status)} [${(this.systemState.ai_host && this.systemState.ai_host.mode)}]</span>
                        </div>
                        <div class="health-metric">
                            <span class="metric-label">Memory</span>
                            <span class="metric-value info">${(this.systemState.memory_usage && this.systemState.memory_usage.rss_mb) || 0} MB (${(this.systemState.memory_usage && this.systemState.memory_usage.percent) || 0}%)</span>
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>Core Processors</h3>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${(this.systemState.ai_host && this.systemState.ai_host.processors ? this.systemState.ai_host.processors : []).map(p => `<span class="chip-tag">${p}</span>`).join('')}
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>Filesystem Health</h3>
                        ${(audit.issues && audit.issues.length > 0) ?
                    audit.issues.map(i => `<div class="fix-item"><h4>${i.sector}: ${i.level}</h4><p>${i.message}</p></div>`).join('') :
                    '<p style="opacity: 0.5; font-size: 0.8rem;">No filesystem issues detected.</p>'
                }
                    </div>
                </div>
                `;
        } else if (this.currentTab === 'operations') {
            // --- PIZARRON VIVO INTEGRATION ---
            const missionData = {
                active_mission: this.systemState.active_mission
            };

            // Re-use Pizarrón Logic as an embedded Dashboard
            if (window.pizarronUI) {
                // Ensure panel has base structure for Pizarrón
                panel.innerHTML = `<div id="pizarron-dashboard-mount" class="pizarron-dashboard-panel"></div>`;
                const mount = document.getElementById('pizarron-dashboard-mount');
                window.pizarronUI.renderInto(mount, missionData);
            } else {
                panel.innerHTML = `<div class="error-msg">Pizarrón Module not initialized.</div>`;
            }
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
            // IntegraciÃ³n con lÃ­nea de tiempo (eventos)
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
                < div class="cockpit-card" style = "margin-bottom: 15px;" >
                    <h3>System Inspection</h3>
                    <div style="display: flex; gap: 10px; margin-bottom: 15px;">
                        <input type="text" id="cockpit-inspect-query" placeholder="Search architecture (e.g. 'router', 'auth')..." 
                            style="flex: 1; background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border); color: #fff; border-radius: 8px; padding: 8px;">
                        <button class="btn-apply" style="width: auto; margin: 0; padding: 0 15px;" onclick="creatorEnv.runInspection()">Inspect</button>
                    </div>
                    <div id="inspection-results" style="font-size: 0.8rem; height: 150px; overflow-y: auto; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px;">
                        <p style="opacity: 0.5;">Select a chip below or enter a search query.</p>
                    </div>
                </div >
                <div class="cockpit-grid">
                    ${this.systemState.chips.map(chip => `
                        <div class="cockpit-card" onclick="creatorEnv.runInspection('${chip.slug}')">
                            <h3>${chip.name} <span class="status-dot ${chip.health}"></span></h3>
                            <p style="font-size: 0.75rem; color: #888;">Slug: ${chip.slug}</p>
                            <p style="font-size: 0.75rem; color: #888;">State: ${chip.status}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (this.currentTab === 'security') {
            panel.innerHTML = `
                < div class="cockpit-grid" >
                    <div class="cockpit-card">
                        <h3>Chip Permissions Model</h3>
                        <div style="font-size: 0.8rem; height: 300px; overflow-y: auto;">
                            ${this.systemState.chips.map(chip => `
                                <div style="margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px;">
                                    <h4 style="margin:0; font-family: 'Outfit';">${chip.name}</h4>
                                    <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px;">
                                        ${((chip.metadata && chip.metadata.permissions) || []).map(p => `<span class="chip-tag" style="background: rgba(0, 212, 255, 0.1); border: 1px solid var(--primary-low);">${p}</span>`).join('')}
                                        ${((chip.metadata && chip.metadata.permissions) || []).length === 0 ? '<span style="opacity: 0.4; font-size: 0.7rem;">Sandbox (No permissions)</span>' : ''}
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
                </div >
                `;
            this.fetchSecurityLogs();
        } else if (this.currentTab === 'sync') {
            const sync = this.systemState.sync_status || { devices_count: 0, status: 'unconfigured' };
            panel.innerHTML = `
                < div class="cockpit-grid" >
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
                </div >
                `;
            this.fetchSyncLogs();
        } else if (this.currentTab === 'insights') {
            panel.innerHTML = `
                < div class="cockpit-card" >
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h3>Actionable Insights</h3>
                        <button class="btn-apply" style="width: auto; margin: 0; padding: 5px 15px;" onclick="creatorEnv.analyzeInsights()">Refresh Analysis</button>
                    </div>
                    <div id="insights-container">
                        <div class="loading-indicator">Analyzing patterns and system state...</div>
                    </div>
                </div >
                `;
            this.fetchInsights();
        } else if (this.currentTab === 'admin') {
            panel.innerHTML = `
                < div class="cockpit-grid" >
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
                            ${isCreator ? `<button class="btn-apply" style="width: auto; margin: 0;" onclick="creatorEnv.createCheckpoint()">Save State</button>` : ''}
                        </div>
                        <div id="checkpoints-list" style="font-size: 0.75rem;">
                            <p style="opacity: 0.5;">Enter a label to create a new system-wide checkpoint.</p>
                        </div>
                    </div>
                </div >
                `;
            this.fetchAdminData();
        } else if (this.currentTab === 'creator') {
            const maint = this.systemState.maintenance_info;
            panel.innerHTML = `
                < div class="cockpit-grid" >
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
                        ${isCreator ? `<button class="btn-apply" onclick="creatorEnv.setSystemMode()">Apply Mode</button>` : ''}
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
                            ${isCreator ? `
                            <button class="btn-apply" style="margin:0; font-size: 0.7rem; padding: 5px;" onclick="creatorEnv.nodeOp('drain')">Drain</button>
                            <button class="btn-apply" style="margin:0; font-size: 0.7rem; padding: 5px;" onclick="creatorEnv.nodeOp('restart')">Restart</button>
                            <button class="btn-cancel" style="margin:0; font-size: 0.7rem; padding: 5px;" onclick="creatorEnv.nodeOp('disable')">Disable</button>
                            <button class="btn-apply" style="margin:0; font-size: 0.7rem; padding: 5px; background: var(--pass-color);" onclick="creatorEnv.nodeOp('resume')">Resume</button>
                            ` : `<p style="grid-column: span 2; font-size: 0.7rem; opacity: 0.5; text-align: center;">Requires Creator Authority</p>`}
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('system-mode-selector').value = this.systemState.system_mode;
        } else if (this.currentTab === 'cluster') {
            const cluster = this.systemState.cluster;
            panel.innerHTML = `
                < div class="cockpit-grid" >
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
                                            ${isCreator ? `
                                            <button onclick="creatorEnv.nodeControl('${node.node_id}', 'drain')" class="node-btn">Drain</button>
                                            <button onclick="creatorEnv.nodeControl('${node.node_id}', 'restart')" class="node-btn">Restart</button>
                                            <button onclick="creatorEnv.nodeControl('${node.node_id}', 'disable')" class="node-btn">Disable</button>
                                            ` : `<span style="font-size: 0.6rem; opacity: 0.4;">Read Only</span>`}
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
                < div class="knowledge-container" >
                    <div class="cockpit-header">
                        <h2>Knowledge Explorer</h2>
                        <div class="k-type-tag">Semantic Index Active</div>
                    </div>
                    <div class="knowledge-grid" id="knowledge-grid-content">
                        <div style="padding: 20px; text-align: center; opacity: 0.3;">Scanning Digital Alexandria...</div>
                    </div>
                </div >
                `;
        } else if (this.currentTab === 'learning') {
            panel.innerHTML = `
                < div class="learning-container" >
                    <h3>Adaptive Learning Paths</h3>
                    <div class="cockpit-grid">
                        <div class="cockpit-card">
                            <h4>Active Path: Web Architecture</h4>
                            <div class="path-node"><div class="node-status completed"></div> Fundamentals</div>
                            <div class="path-node"><div class="node-status active"></div> Distributed Systems</div>
                            <div class="path-node"><div class="node-status locked"></div> Scale Optimization</div>
                        </div>
                    </div>
                </div >
                `;
        } else if (this.currentTab === 'certs') {
            panel.innerHTML = `
                < div class="certs-container" >
                    <h3>Decentralized Certifications</h3>
                    <div class="cockpit-grid">
                        <div class="cockpit-card">
                            <h4>Fullstack Web Mastery</h4>
                            <div class="label">ISSUER: OMNIWEB AI</div>
                            <div class="label">SIG: 0x82f...a12</div>
                            <div style="color: #00ff88; font-size: 0.8rem; margin-top:10px;">VERIFIED SYSTEM-WIDE</div>
                        </div>
                    </div>
                </div >
                `;
        } else if (this.currentTab === 'opportunities') {
            this.fetchOpportunities();
            panel.innerHTML = `
                < div class="opportunities-container" >
                    <h3>Skill-Based Opportunities</h3>
                    <div id="opp-list-content">
                        <div style="padding: 20px; text-align: center; opacity: 0.3;">Matching skills to market...</div>
                    </div>
                </div >
                `;
        } else if (this.currentTab === 'collab') {
            this.fetchProjects();
            panel.innerHTML = `
                < div class="collab-container" >
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>Collaborative Projects</h3>
                        <button class="cockpit-btn">Start New Project</button>
                    </div>
                    <div class="collab-grid" id="project-list-content">
                        <div style="padding: 20px; text-align: center; opacity: 0.3;">Fetching active collaborations...</div>
                    </div>
                </div >
                `;
        } else if (this.currentTab === 'labs') {
            panel.innerHTML = `
                < div class="labs-container" >
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
                </div >
                `;
        } else if (this.currentTab === 'market') {
            this.fetchMarketListings();
            panel.innerHTML = `
                < div class="market-container" >
                    <h3>Knowledge & Skill Market</h3>
                    <div class="market-grid" id="market-list-content">
                        <div style="padding: 20px; text-align: center; opacity: 0.3;">Connecting to the global marketplace...</div>
                    </div>
                </div >
                `;
        } else if (this.currentTab === 'mentor') {
            this.fetchMentorState();
            panel.innerHTML = `
                < div class="mentor-container" >
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
                </div >
                `;
        } else if (this.currentTab === 'omniverse') {
            this.fetchGateways();
            panel.innerHTML = `
                < div class="omniverse-container" >
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
                </div >
                `;
        } else if (this.currentTab === 'observability') {
            this.fetchMetrics();
            panel.innerHTML = `
                < div class="observability-container" >
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
                </div >
                `;
        } else if (this.currentTab === 'beta') {
            panel.innerHTML = `
                < div class="beta-container" >
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h3>Public Beta Controller</h3>
                        <button class="cockpit-btn" onclick="missionControl.generateBetaInvite()">Generate Viral Invite</button>
                    </div>
                    <div class="beta-feedback-form" style="margin-top: 20px;">
                        <h4>Direct Beta Feedback</h4>
                        <textarea id="beta-feedback-input" placeholder="Enter feature feedback or bug reports..."></textarea>
                        <button class="cockpit-btn" onclick="missionControl.submitBetaFeedback()">Submit Feedback</button>
                    </div>
                </div >
                `;
        } else if (this.currentTab === 'archival') {
            panel.innerHTML = `
                < div class="archival-container" >
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
                </div >
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
                                <button class="btn-apply" style="width: auto; margin: 0; padding: 5px 12px; font-size: 0.7rem;" onclick="creatorEnv.switchView('chat'); window.addMessage && window.addMessage('Show me the active groove analysis', 'ai');">Analyze Groove</button>
                            </div>
                        </div>
                        <div style="font-family: monospace; padding: 12px; background: #08080c; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; font-size: 0.8rem; color: #00ff88; letter-spacing: 2px; margin-top: 15px;" id="music-groove-timeline">
                            [----|----|----|----]
                        </div>
                        <div style="margin-top: 15px; display: flex; justify-content: space-between; font-size: 0.85rem;">
                            <span id="music-detected-bpm">120.0 BPM</span>
                            <span id="music-detected-swing" style="color: #00ff88;">Straight</span>
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
                        <!-- Phase 16: Cognitive Telemetry Pulse -->
                ${state.active_mission && state.active_mission.telemetry_snap ? `
                    <div style="margin-top: 20px; padding: 15px; background: rgba(212,175,55,0.05); border: 1px solid rgba(212,175,55,0.2); border-radius: 8px;">
                        <h5 style="color: var(--creator-gold); font-family: 'Outfit'; font-size: 0.8rem; margin: 0 0 10px 0;">COGNITIVE TELEMETRY PULSE</h5>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.75rem;">Status: <b style="color: ${state.active_mission.telemetry_snap.status_color}">${state.active_mission.telemetry_snap.last_event || 'Monitoring...'}</b></span>
                            <span style="font-size: 0.7rem; opacity: 0.6;">Heartbeat: ${state.active_mission.telemetry_snap.last_sync}</span>
                        </div>
                    </div>
                ` : `
                    <div style="margin-top: 20px; padding: 15px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; text-align: center; opacity: 0.5;">
                        <span style="font-size: 0.7rem;">Telemetry Offline (No Active Mission)</span>
                    </div>
                `}
                        <div style="font-family: monospace; padding: 12px; background: #08080c; border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; font-size: 0.8rem; color: #00ff88; letter-spacing: 2px; margin-top: 15px;" id="music-groove-timeline">
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
                </div >
                `;
        } else if (this.currentTab === 'integration') {
            this.fetchIntegrationData();
            panel.innerHTML = `
                < div class="cockpit-grid" >
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
                </div >
                `;
        } else if (this.currentTab === 'qr_gateway') {
            this.fetchQRData();
            panel.innerHTML = `
                < div class="cockpit-grid" >
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
                </div >
                `;
        } else if (this.currentTab === 'workload') {
            this.fetchWorkloadData();
            panel.innerHTML = `
                < div class="cockpit-grid" >
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
                                <option value="none">Core Analyzer</option>
                                <option value="finanzas">Finance Auditor</option>
                            </select>
                            <button class="btn-apply" onclick="creatorEnv.submitWorkloadTask()">Dispatch Cluster Task</button>
                        </div>
                    </div>
                </div >
                `;
        } else if (this.currentTab === 'mesh') {
            this.fetchMeshData();
            panel.innerHTML = `
                < div class="mesh-container" >
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
                </div >
                `;
        } else if (this.currentTab === 'autonomous') {
            this.fetchOfflineData();
            panel.innerHTML = `
                < div class="autonomous-container" >
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
                </div >
                `;
        } else if (this.currentTab === 'runtime') {
            this.fetchRuntimeData();
            panel.innerHTML = `
                < div class="runtime-container" >
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
                </div >
                `;
        } else if (this.currentTab === 'storage') {
            this.fetchStorageData();
            panel.innerHTML = `
                < div class="storage-container" >
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
                </div >
                `;
        } else if (this.currentTab === 'governance') {
            this.fetchGovernanceData();
            panel.innerHTML = `
                < div class="cockpit-grid" >
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h3>ðŸ›ï¸ AI Governance Advisor</h3>
                            <div style="display: flex; gap: 8px;">
                                <button class="btn-apply" style="width: auto; margin: 0; padding: 5px 15px; background: var(--accent); color: white;" onclick="window.omniRenderFrictionHeatmap()">MAPA DE FRICCIÓN</button>
                                <button class="btn-apply" style="width: auto; margin: 0; padding: 5px 15px; background: rgba(5,5,8,0.5); border: 1px solid var(--accent-transparent);" onclick="window.omniRenderForensicCockpit()">CABINA FORENSE</button>
                                <button class="btn-apply" style="width: auto; margin: 0; padding: 5px 15px;" onclick="creatorEnv.runLeadershipAnalysis()">Run Analysis</button>
                            </div>
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
        } else if (this.currentTab === 'connectors') {
            this.fetchConnectorsSummary();
            panel.innerHTML = `
                <div class="cockpit-grid">
                    <div class="cockpit-card" style="grid-column: span 2;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 1.5rem;">🛰️</span>
                                <div>
                                    <h3 style="margin: 0;">External App Connectors</h3>
                                    <p style="margin: 0; font-size: 0.7rem; opacity: 0.5;">Governed control for subordinate tools & services</p>
                                </div>
                            </div>
                            <div class="governance-stats" style="display: flex; gap: 20px;">
                                <div class="metric"><span class="label">TOTAL</span><span class="value" id="conn-total">0</span></div>
                                <div class="metric"><span class="label">ACTIVE</span><span class="value" id="conn-active" style="color: #00ff88;">0</span></div>
                                <div class="metric"><span class="label">VAULT</span><span class="value" style="color: var(--creator-gold);">PROTECTED</span></div>
                            </div>
                        </div>
                    </div>

                    <div class="cockpit-card" style="grid-column: span 2;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                            <h3>Registered Connectors</h3>
                            <div style="display: flex; gap: 8px;">
                                <button class="ws-btn-mini" onclick="creatorEnv.fetchConnectorsSummary()" style="padding: 4px 10px;">REFRESH</button>
                                <button class="ws-btn-mini" onclick="creatorEnv.toggleRegistrationForm()" id="btn-toggle-reg" style="padding: 4px 10px; background: var(--accent); color: #fff;">+ REGISTER NEW</button>
                            </div>
                        </div>

                        <!-- REGISTRATION FORM (HIDDEN BY DEFAULT) -->
                        <div id="connector-registration-form" style="display: none; margin-bottom: 25px; padding: 20px; background: rgba(0,212,255,0.05); border: 1px solid rgba(0,212,255,0.2); border-radius: 12px; animation: slideDown 0.3s ease;">
                            <h4 style="margin-top: 0; color: var(--accent);">Initialize Governed Connector</h4>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                                <div>
                                    <label style="display: block; font-size: 0.65rem; opacity: 0.6; margin-bottom: 5px;">CONNECTOR ID</label>
                                    <input type="text" id="reg-conn-id" placeholder="e.g., google_drive_v1" class="cockpit-input" style="width: 100%;">
                                </div>
                                <div>
                                    <label style="display: block; font-size: 0.65rem; opacity: 0.6; margin-bottom: 5px;">PROVIDER TYPE</label>
                                    <select id="reg-conn-provider" class="cockpit-select" style="width: 100%;">
                                        <option value="EXTERNAL_API">External API (REST/RPC)</option>
                                        <option value="LOCAL_EXEC">Local Execution (Python/Node)</option>
                                        <option value="BRIDGE_AGENT">Subordinate Bridge Agent</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display: block; font-size: 0.65rem; opacity: 0.6; margin-bottom: 5px;">CAPABILITY CLASS</label>
                                    <select id="reg-conn-capability" class="cockpit-select" style="width: 100%;">
                                        <option value="READ_ONLY">Read Only</option>
                                        <option value="READ_WRITE">Read & Write</option>
                                        <option value="EXECUTION_ONLY">Execution Only</option>
                                        <option value="ADMIN">Full Administrative</option>
                                    </select>
                                </div>
                                <div>
                                    <label style="display: block; font-size: 0.65rem; opacity: 0.6; margin-bottom: 5px;">TARGET PERSONAL SPACE</label>
                                    <select id="reg-conn-space" class="cockpit-select" style="width: 100%;">
                                        <option value="">Loading spaces...</option>
                                    </select>
                                </div>
                            </div>
                            <div style="margin-bottom: 15px;">
                                <label style="display: block; font-size: 0.65rem; opacity: 0.6; margin-bottom: 5px;">CONFIGURATION (Key=Value, line by line. Use '_key' or '_token' suffix to auto-vault)</label>
                                <textarea id="reg-conn-config" placeholder="api_endpoint=https://api.example.com&#10;api_key=PASTE_SECRET_HERE" class="cockpit-input" style="width: 100%; height: 80px; font-family: monospace; font-size: 0.75rem;"></textarea>
                            </div>
                            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                                <button class="ws-btn-mini" onclick="creatorEnv.toggleRegistrationForm()" style="background: rgba(255,255,255,0.05);">CANCEL</button>
                                <button class="btn-apply" onclick="creatorEnv.submitConnectorRegistration()" style="width: auto; margin: 0; padding: 8px 25px;">REGISTER & VAULT</button>
                            </div>
                        </div>

                        <div id="connectors-list" class="connector-grid-display" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px;">
                            <div class="loading-indicator">Retrieving governed connectors...</div>
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <h3>Sovereign Personal Space</h3>
                        <div id="space-info-card" class="space-info-card">
                            <div class="loading-indicator">Resolving space ownership...</div>
                        </div>
                    </div>

                    <div class="cockpit-card">
                        <h3>Recent External History</h3>
                        <div id="connector-history-list" class="connector-history-list" style="max-height: 300px; overflow-y: auto;">
                            <div class="loading-indicator">Fetching audit trail...</div>
                        </div>
                    </div>
                </div>
            `;
        } else if (this.currentTab === 'wisdom') {
            panel.innerHTML = `<div id="wisdom-atlas-mount" class="wisdom-atlas-mount" style="height: 100%; min-height: 500px;"></div>`;
            if (window.wisdomAtlas && typeof window.wisdomAtlas.init === 'function') {
                window.wisdomAtlas.init('wisdom-atlas-mount');
            }
        } else if (this.currentTab === 'copilot') {
            this.renderCopilotUI(panel);
        } else if (this.currentTab === 'audit') {
            this.renderAuditSurface(panel);
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
            alert(`Sync Complete: ${(result.results && result.results.applied) || 0} items applied.`);
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
                                ${isCreator ? `<button class="btn-cancel" style="width: auto; margin: 0; padding: 4px 10px; font-size: 0.65rem;" onclick="creatorEnv.rollback(${c.id})">Restore</button>` : ''}
                            </div>
                         `).join('')}
                         ${data.length === 0 ? '<p style="opacity: 0.3; font-size: 0.7rem;">No checkpoints found.</p>' : ''}
                    </div>
                </div >
                `;
        } catch (err) { }
    }

    async rollback(checkpointId) {
        if (!document.body.classList.contains('mode-creator')) {
            alert("Acceso denegado: Se requiere autoridad de Creator.");
            return;
        }
        if (await this.askPermission("ULTIMATE SECURITY OVERRIDE", "Are you sure? This will revert the entire system state. Current session will be lost.")) {
            this.triggerLightBurst();
            const res = await fetch(`/ api / v1 / system / admin / rollback / ${checkpointId} `, { method: 'POST' });
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
        if (!document.body.classList.contains('mode-creator') && !document.body.classList.contains('mode-admin')) {
            alert("Acceso denegado: Se requieren permisos de Admin.");
            return;
        }
        if (await this.askPermission("Admin Review", `Confirm ${status} for ${sid} ? `)) {
            await fetch(`/ api / v1 / system / admin / suggestions / ${sid} / review ? status = ${status} `, { method: 'POST' });
            this.fetchAdminData();
        }
    }

    async createCheckpoint() {
        if (!document.body.classList.contains('mode-creator')) {
            alert("Acceso denegado: Se requiere autoridad de Creator.");
            return;
        }
        const label = document.getElementById('checkpoint-label').value;
        if (!label) return alert("Please provide a label.");

        if (await this.askPermission("System Checkpoint", "Create a full system snapshot? This includes the database and core state.")) {
            this.triggerLightBurst();
            const res = await fetch(`/ api / v1 / system / admin / checkpoint / create ? label = ${encodeURIComponent(label)} `, { method: 'POST' });
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
        await fetch(`/ api / v1 / user / insights / action / ${insightId} `, { method: 'POST' });
        this.triggerLightBurst();
        alert("Insight actioned: Task queued in your logbook.");
    }

    async runInspection(query) {
        if (!query) {
            const inspectEl = document.getElementById('cockpit-inspect-query');
            query = inspectEl ? inspectEl.value : "";
        }
        const resEl = document.getElementById('inspection-results');
        if (!resEl) return;
        resEl.innerHTML = '<p>Analyzing system structure...</p>';

        try {
            const res = await fetch(`/ api / v1 / system / inspect ? query = ${query} `);
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
                const res = await fetch(`/ api / v1 / system / audit / fix / apply ? proposal_id = ${proposalId} `, { method: 'POST' });
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
        if (!document.body.classList.contains('mode-creator')) {
            alert("Acceso denegado: Se requiere autoridad de Creator.");
            return;
        }
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
        if (!document.body.classList.contains('mode-creator')) {
            alert("Acceso denegado: Se requiere autoridad de Creator.");
            return;
        }
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
        if (!document.body.classList.contains('mode-creator')) {
            alert("Acceso denegado: Se requiere autoridad de Creator.");
            return;
        }
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

        const response = await fetch('/api/v1/ai/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: content, context: { source_surface: 'workspace' } })
        });
        const data = await response.json();
        this.forceSync(); // IMMEDIATE FEEDBACK (Block 16)
        alert("Feedback received. AI Optimization loop updated.");
        input.value = '';
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
                                    <span style="opacity: 0.5;"> â†’ </span>
                                    <span>${m.recipient_contact_id.substring(0, 8)}</span>
                                    ${m.target_language ? `<span class="chip-tag" style="margin-left: 8px; font-size: 0.6rem;">${m.original_language} â†’ ${m.target_language}</span>` : ''}
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
                                <button class="btn-apply" style="font-size: 0.65rem; padding: 3px 10px; width: auto;" onclick="creatorEnv.approveInsight('${i.id}')">âœ“ Approve Promotion</button>
                                <button class="btn-cancel" style="font-size: 0.65rem; padding: 3px 10px; width: auto;" onclick="creatorEnv.rejectInsight('${i.id}')">âœ— Reject</button>
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
        const lookupEl = document.getElementById('gov-user-lookup');
        const userId = lookupEl ? lookupEl.value : "";
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
                if (bpmEl) bpmEl.innerText = `${(data.bpm && data.bpm.toFixed(1)) || "120.0"} BPM`;

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
                                <textarea id="copilot-prompt-input" placeholder="e.g. 'AuditÃ¡ el sistema actual y mostrame los problemas.'" class="cockpit-input" style="height: 80px;"></textarea>
                                <div style="display:flex; justify-content: space-between; margin-top: 10px;">
                                    <button class="upload-trigger-btn" onclick="document.getElementById('global-media-upload').click()">
                                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4m4-5l5-5 5 5m-5-5v12"/></svg> ADD EVIDENCE
                                </button>
                                ${mode !== 'PUBLIC' ? `<button class="btn-apply" onclick="creatorEnv.generateCopilotPlan()">Generate Plan</button>` : ''}
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
                                ${document.body.classList.contains('mode-creator') ? `<button class="btn-apply" onclick="creatorEnv.executeApprovedSteps()">Execute Approved</button>` : ''}
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
        document.getElementById('copilot-prompt-input').value = "ProponÃ© correcciÃ³n para los problemas detectados.";
        this.generateCopilotPlan();
    }

    async approveCorrection(issueId) {
        document.getElementById('copilot-prompt-input').value = "AplicÃ¡ la correcciÃ³n aprobada.";
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
        if (!document.body.classList.contains('mode-creator')) {
            alert("Acceso denegado: Solo el Creator puede modificar el núcleo cognitivo.");
            return;
        }
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
            <div class="evidence-item ${m.annotations && m.annotations.length > 0 ? 'annotated' : ''}" 
                 onclick="creatorEnv.openAnnotator('${m.id}')" title="Clic para anotar: ${m.name}">
                ${m.type === 'image'
                ? `<img src="${m.data}" alt="Evidence">`
                : `<video src="${m.data}"></video><div class="type-tag">VIDEO</div>`}
                ${m.annotations && m.annotations.length > 0 ? '<div class="annotation-badge">📍</div>' : ''}
            </div>
        `).join('');

        if (shellGrid) shellGrid.innerHTML = html;
        if (copilotGrid) copilotGrid.innerHTML = html;
    }

    // --- VISUAL ANNOTATOR CORE (Phase 21) ---
    setupVisualAnnotator() {
        const container = document.getElementById('annotator-container');
        if (container) {
            container.addEventListener('click', (e) => this.handleAnnotatorClick(e));
        }
    }

    // New: Handle iterative feedback (PHASE 21)
    openReAnnotation(mediaId, stepId) {
        this.currentCorrectionStepId = stepId;

        // If not in sessionMedia, try to recover from history (PHASE 21)
        if (!this.sessionMedia.find(m => m.id === mediaId)) {
            const mission = this.systemState?.active_mission;
            if (mission) {
                // Check current context
                let found = null;
                if (mission.visual_context && mission.visual_context.media_id === mediaId) {
                    found = mission.visual_context;
                } else if (mission.multimodal_history) {
                    // Check history snapshots
                    const snap = mission.multimodal_history.find(h => h.visual_context && h.visual_context.media_id === mediaId);
                    if (snap) found = snap.visual_context;
                }

                if (found) {
                    this.sessionMedia.push({
                        id: mediaId,
                        name: "Captura Histórica",
                        type: 'image',
                        data: found.source_image,
                        annotations: JSON.parse(JSON.stringify(found.annotations || [])),
                        timestamp: new Date().toISOString()
                    });
                    this.renderMediaPreviews();
                }
            }
        }

        this.openAnnotator(mediaId);

        const title = document.querySelector('#visual-annotator h3');
        if (title) title.innerText = "RE-ORIENTACIÓN DE EVIDENCIA";
        if (window.showToast) window.showToast("RE-ANOTACIÓN: Marcá el punto exacto de la falla.", 'info');
    }

    openAnnotator(mediaId) {
        const media = this.sessionMedia.find(m => m.id === mediaId);
        if (!media || media.type !== 'image') return;

        this.currentAnnotatingMediaId = mediaId;
        this.tempAnnotations = media.annotations ? JSON.parse(JSON.stringify(media.annotations)) : [];

        const overlay = document.getElementById('visual-annotator');
        const img = document.getElementById('annotator-img');
        const commentInput = document.getElementById('annotator-comment');

        if (overlay && img) {
            img.src = media.data;
            overlay.classList.add('active');
            commentInput.value = "";
            this.renderTempAnnotations();
        }
    }

    closeAnnotator() {
        const overlay = document.getElementById('visual-annotator');
        if (overlay) overlay.classList.remove('active');

        const title = document.querySelector('#visual-annotator h3');
        if (title) title.innerText = "ANOTACIÓN DE EVIDENCIA VISUAL";

        this.currentAnnotatingMediaId = null;
        this.tempAnnotations = [];
        this.currentCorrectionStepId = null;
    }

    setAnnotatorTool(tool) {
        this.annotatorTool = tool;
        document.querySelectorAll('.annotator-btn').forEach(btn => btn.classList.remove('active'));
        const btnId = tool === 'point' ? 'tool-point' : 'tool-box';
        const btn = document.getElementById(btnId);
        if (btn) btn.classList.add('active');
    }

    handleAnnotatorClick(e) {
        if (!this.currentAnnotatingMediaId) return;
        const container = document.getElementById('annotator-container');
        const rect = container.getBoundingClientRect();

        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        const comment = document.getElementById('annotator-comment').value.trim();

        if (this.annotatorTool === 'point') {
            this.tempAnnotations.push({
                type: 'point',
                x, y,
                comment: comment || "Punto de interés"
            });
            document.getElementById('annotator-comment').value = ""; // Clear for next point
            this.renderTempAnnotations();
        } else if (this.annotatorTool === 'box') {
            // Simple box: constant size for now, centered at click
            this.tempAnnotations.push({
                type: 'box',
                x: x - 5, y: y - 5,
                w: 10, h: 10,
                comment: comment || "Zona problemática"
            });
            document.getElementById('annotator-comment').value = "";
            this.renderTempAnnotations();
        }
    }

    renderTempAnnotations() {
        const container = document.getElementById('annotator-container');
        // Remove existing overlays
        container.querySelectorAll('.annotation-pin, .annotation-box').forEach(el => el.remove());

        this.tempAnnotations.forEach((ann, idx) => {
            if (ann.type === 'point') {
                const pin = document.createElement('div');
                pin.className = 'annotation-pin';
                pin.style.left = `${ann.x}%`;
                pin.style.top = `${ann.y}%`;
                pin.innerText = idx + 1;
                pin.title = ann.comment;
                container.appendChild(pin);
            } else {
                const box = document.createElement('div');
                box.className = 'annotation-box';
                box.style.left = `${ann.x}%`;
                box.style.top = `${ann.y}%`;
                box.style.width = `${ann.w}%`;
                box.style.height = `${ann.h}%`;
                box.title = ann.comment;
                container.appendChild(box);
            }
        });
    }

    saveAnnotations() {
        const media = this.sessionMedia.find(m => m.id === this.currentAnnotatingMediaId);
        if (media) {
            media.annotations = JSON.parse(JSON.stringify(this.tempAnnotations));

            // Integrate global comment into annotations if not already linked
            const finalComment = document.getElementById('annotator-comment').value.trim();
            if (finalComment && this.tempAnnotations.length === 0) {
                // If no points, create a general context/correction one
                media.annotations.push({ type: this.currentCorrectionStepId ? 'correction' : 'context', comment: finalComment });
            }
        }

        // Handle iterative re-orientation (PHASE 21)
        if (this.currentCorrectionStepId) {
            const comment = document.getElementById('annotator-comment').value.trim() || "Re-anotación correctiva aplicada";
            const cmd = `reorient job ${this.currentCorrectionStepId} with evidence: ${comment}`;
            if (window.omniShell) window.omniShell.addInput(cmd);
        }

        this.renderMediaPreviews();
        this.closeAnnotator();

        if (window.showToast) window.showToast(this.currentCorrectionStepId ? "Foco reorientado. Reiniciando diagnóstico." : "Anotaciones vinculadas.", 'success');
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

            ${(audit.failure_types && audit.failure_types.length > 0) ? `
            <div class="audit-section">
                <h4>Failure Types Detected</h4>
                <div class="audit-failure-list">
                    ${audit.failure_types.map(f => `<span class="audit-tag fail">${f}</span>`).join('')}
                </div>
            </div>
            ` : ''}

            ${((audit.suspicious_layers && audit.suspicious_layers.length > 0) || (audit.suspicious_modules && audit.suspicious_modules.length > 0)) ? `
            <div class="audit-section">
                <h4>Detection Origin</h4>
                <div class="audit-failure-list">
                    ${Array.isArray(audit.suspicious_layers) ? audit.suspicious_layers.map(l => `<span class="audit-tag">Layer: ${l}</span>`).join('') : ''}
                    ${Array.isArray(audit.suspicious_modules) ? audit.suspicious_modules.map(m => `<span class="audit-tag">Module: ${m}</span>`).join('') : ''}
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

    async fetchConnectorsSummary() {
        try {
            const res = await fetch('/api/v1/auth/connectors/summary');
            if (res.ok) {
                const data = await res.json();
                this.updateConnectorsUI(data);
            }
        } catch (e) {
            console.error("Failed to fetch connectors summary", e);
        }
    }

    // --- MISSION BLOCK 06: MANUAL CONNECTOR REGISTRATION ---

    toggleRegistrationForm() {
        const form = document.getElementById('connector-registration-form');
        const btn = document.getElementById('btn-toggle-reg');
        if (!form) return;

        if (form.style.display === 'none') {
            form.style.display = 'block';
            btn.innerText = '✕ CLOSE FORM';
            btn.style.background = 'rgba(255,255,255,0.1)';
            this.fetchSpacesForRegistration();
        } else {
            form.style.display = 'none';
            btn.innerText = '+ REGISTER NEW';
            btn.style.background = 'var(--accent)';
        }
    }

    async fetchSpacesForRegistration() {
        const select = document.getElementById('reg-conn-space');
        if (!select) return;

        try {
            const res = await fetch('/api/v1/auth/spaces');
            const data = await res.json();
            if (data.status === 'success') {
                select.innerHTML = data.spaces.map(s => `
                    <option value="${s.space_id}">${s.user_id} (${s.space_id.substring(0, 8)})</option>
                `).join('');
            }
        } catch (e) {
            select.innerHTML = '<option value="">Failed to load spaces</option>';
        }
    }

    async submitConnectorRegistration() {
        const id = document.getElementById('reg-conn-id').value;
        const provider = document.getElementById('reg-conn-provider').value;
        const capability = document.getElementById('reg-conn-capability').value;
        const spaceId = document.getElementById('reg-conn-space').value;
        const configRaw = document.getElementById('reg-conn-config').value;

        if (!id || !spaceId) return alert("Connector ID and Target Space are mandatory.");

        // Parse Config
        const config = {};
        configRaw.split('\n').forEach(line => {
            const [k, ...vParts] = line.split('=');
            if (k && vParts.length > 0) {
                config[k.strip ? k.strip() : k.trim()] = vParts.join('=').trim();
            }
        });

        if (await this.askPermission("Connector Registration", `Register governed connector '${id}' for space ${spaceId}?`)) {
            try {
                const res = await fetch('/api/v1/auth/connectors', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        connector_id: id,
                        owner_space_id: spaceId,
                        provider_type: provider,
                        capability: capability,
                        config: config
                    })
                });

                if (res.ok) {
                    if (window.showToast) window.showToast("Connector Registered & Vaulted", "success");
                    this.toggleRegistrationForm();
                    this.fetchConnectorsSummary();
                } else {
                    const err = await res.json();
                    alert("Registration failed: " + (err.detail || "Unknown error"));
                }
            } catch (e) {
                alert("Critical error during registration.");
            }
        }
    }

    updateConnectorsUI(data) {
        if (this.currentTab !== 'connectors') return;

        const el = (id) => document.getElementById(id);
        if (el('conn-total')) el('conn-total').innerText = data.metrics.total_connectors;
        if (el('conn-active')) el('conn-active').innerText = data.metrics.active_connectors;

        // Space Info
        const spaceCard = el('space-info-card');
        if (spaceCard) {
            spaceCard.innerHTML = `
                <div class="space-detail" style="margin-bottom: 12px; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div class="label" style="font-size: 0.6rem; opacity: 0.5; text-transform: uppercase;">Space ID</div>
                    <div class="value" style="font-family: monospace; color: var(--accent);">${data.space.space_id}</div>
                </div>
                <div class="space-detail" style="margin-bottom: 12px; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div class="label" style="font-size: 0.6rem; opacity: 0.5; text-transform: uppercase;">Owner Anchor</div>
                    <div class="value">${data.space.owner_id}</div>
                </div>
                <div class="space-detail" style="margin-bottom: 12px; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div class="label" style="font-size: 0.6rem; opacity: 0.5; text-transform: uppercase;">Root Filesystem</div>
                    <div class="value" style="font-size: 0.65rem; opacity: 0.7; word-break: break-all;">${data.space.root_path}</div>
                </div>
                <div style="margin-top: 15px; padding: 12px; background: rgba(0,212,255,0.05); border-radius: 6px; border: 1px solid rgba(0,212,255,0.1); font-size: 0.65rem; line-height: 1.4;">
                    <strong>Sovereignty Note:</strong> All artifacts generated by connectors are deterministically stored within this isolated directory.
                </div>
            `;
        }

        // Connectors List
        const list = el('connectors-list');
        if (list) {
            if (data.connectors.length === 0) {
                list.innerHTML = '<div style="grid-column: 1/-1; padding: 40px; text-align: center; opacity: 0.3; background: rgba(0,0,0,0.2); border-radius: 8px;">No external connectors registered for this space.</div>';
            } else {
                list.innerHTML = data.connectors.map(c => {
                    const statusClass = c.status.toLowerCase();
                    return `
                        <div class="connector-card-ui ${statusClass}" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 15px; transition: all 0.3s ease;">
                            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                                <div style="font-weight: 700; font-family: 'Outfit'; color: #fff;">${c.name}</div>
                                <span class="status-badge" style="font-size: 0.6rem; padding: 2px 8px; border-radius: 4px; background: ${statusClass === 'active' ? 'rgba(0,255,136,0.1)' : 'rgba(255,68,68,0.1)'}; color: ${statusClass === 'active' ? '#00ff88' : '#ff4444'}; border: 1px solid ${statusClass === 'active' ? 'rgba(0,255,136,0.2)' : 'rgba(255,68,68,0.2)'};">${c.status}</span>
                            </div>
                            <div style="font-size: 0.75rem; opacity: 0.6; margin-bottom: 15px; height: 2.4em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">${c.description || 'Governed connector for external tool access.'}</div>
                            
                            <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 20px;">
                                ${c.capabilities.map(cap => `<span style="font-size: 0.55rem; padding: 1px 5px; background: rgba(212,175,55,0.1); color: var(--creator-gold); border: 1px solid rgba(212,175,55,0.2); border-radius: 3px;">${cap}</span>`).join('')}
                            </div>

                            <div style="display: flex; gap: 8px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px;">
                                ${c.status === 'ACTIVE' ? `
                                    <button class="ws-btn-mini" onclick="creatorEnv.updateConnectorStatus('${c.connector_id}', 'SUSPENDED')" style="background: rgba(255,170,0,0.1); border-color: rgba(255,170,0,0.3); color: #ffaa00;">SUSPEND</button>
                                ` : ''}
                                ${c.status === 'SUSPENDED' ? `
                                    <button class="ws-btn-mini" onclick="creatorEnv.updateConnectorStatus('${c.connector_id}', 'ACTIVE')" style="background: rgba(0,212,255,0.1); border-color: rgba(0,212,255,0.3); color: #00d4ff;">ACTIVATE</button>
                                ` : ''}
                                ${c.status !== 'REVOKED' ? `
                                    <button class="ws-btn-mini" onclick="creatorEnv.updateConnectorStatus('${c.connector_id}', 'REVOKED')" style="background: rgba(255,68,68,0.1); border-color: rgba(255,68,68,0.3); color: #ff4444;">REVOKE</button>
                                ` : '<span style="font-size: 0.6rem; opacity: 0.4;">PERMANENTLY REVOKED</span>'}
                            </div>
                        </div>
                    `;
                }).join('');
            }
        }

        // History
        const historyList = el('connector-history-list');
        if (historyList) {
            if (data.history.length === 0) {
                historyList.innerHTML = '<div style="padding: 20px; text-align: center; opacity: 0.3;">No execution history recorded.</div>';
            } else {
                historyList.innerHTML = data.history.map(h => `
                    <div class="history-item-ui" style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <span style="font-weight: 700; font-size: 0.7rem; color: var(--accent);">${h.connector_id.toUpperCase()}</span>
                            <span style="font-size: 0.6rem; opacity: 0.4;">${new Date(h.timestamp).toLocaleString()}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.8rem; color: #fff;">${h.action}</span>
                            <span style="font-size: 0.6rem; font-weight: bold; padding: 2px 6px; border-radius: 3px; background: ${h.status === 'SUCCESS' ? 'rgba(0,255,136,0.1)' : 'rgba(255,68,68,0.1)'}; color: ${h.status === 'SUCCESS' ? '#00ff88' : '#ff4444'};">${h.status}</span>
                        </div>
                        ${h.error ? `<div style="font-size: 0.65rem; color: #ff4444; margin-top: 5px; opacity: 0.8;">[ERROR] ${h.error}</div>` : ''}
                    </div>
                `).join('');
            }
        }
    }

    async updateConnectorStatus(id, status) {
        if (!confirm(`Confirm change of connector ${id} to ${status}?`)) return;

        try {
            const res = await fetch(`/api/v1/auth/connectors/${id}/status?status=${status}`, {
                method: 'PATCH'
            });
            if (res.ok) {
                this.fetchConnectorsSummary();
                if (window.showToast) window.showToast(`Connector status set to ${status}`, 'success');
            } else {
                const err = await res.json();
                alert("Failed to update status: " + (err.message || 'Unknown error'));
            }
        } catch (e) {
            console.error("Status update failed", e);
        }
    }

    async fetchUserArtifacts() {
        try {
            const res = await fetch('/api/v1/auth/artifacts');
            const data = await res.json();
            if (data.status === 'success') {
                this.renderArtifactGrid(data.artifacts);

                // Update header stats
                const countBadge = document.getElementById('home-artifact-count');
                if (countBadge) countBadge.innerText = data.artifacts.length;

                // Find Space ID from state if available
                if (this.systemState && this.systemState.space) {
                    const spaceIdEl = document.getElementById('home-space-id');
                    if (spaceIdEl) spaceIdEl.innerText = `SPACE_ID: ${this.systemState.space.space_id}`;
                }
            }
        } catch (e) {
            console.error("[HOME] Failed to fetch artifacts", e);
        }
    }

    renderArtifactGrid(artifacts) {
        const grid = document.getElementById('artifact-grid');
        if (!grid) return;

        if (!artifacts || artifacts.length === 0) {
            grid.innerHTML = `
                <div class="gallery-empty">
                    <div class="empty-icon">📂</div>
                    <p>Aún no tienes resultados generados.</p>
                    <span>Tus creaciones aparecerán aquí automáticamente.</span>
                </div>
            `;
            return;
        }

        // Sort by date (recent first)
        const sorted = [...artifacts].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));

        grid.innerHTML = sorted.map(a => {
            const dateStr = new Date(a.created_at).toLocaleDateString();
            const timeStr = new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

            // Basic Icon Mapping
            let icon = '📄';
            if (a.artifact_type === 'IMAGE') icon = '🖼️';
            if (a.artifact_type === 'MEDIA') icon = '🎥';
            if (a.artifact_type === 'CODE') icon = '⌨️';
            if (a.artifact_type === 'NOTE') icon = '📝';

            return `
                <div class="artifact-card" title="${a.filename}" onclick="creatorEnv.openArtifact('${a.artifact_id}')">
                    <div class="artifact-preview">
                        <span class="artifact-icon-large">${icon}</span>
                        <div class="artifact-type-tag">${a.artifact_type}</div>
                    </div>
                    <div class="artifact-info">
                        <div class="artifact-title">${a.filename}</div>
                        <div class="artifact-meta">
                            <span>${dateStr}</span>
                            <span class="meta-dot">•</span>
                            <span>${timeStr}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // --- ARTIFACT PREVIEW MODULE ---

    async openArtifact(artifactId) {
        // Redirige al nuevo sistema espacial (Block 02 integration)
        if (window.workspaceManager) {
            window.workspaceManager.openArtifact(artifactId);
        } else {
            console.error("Workspace Manager no disponible.");
        }
    }

    closeArtifactPreview() {
        const modal = document.getElementById('artifact-preview-modal');
        if (modal) modal.style.display = 'none';
        const contentBody = document.getElementById('preview-content');
        if (contentBody) contentBody.innerHTML = '';
    }
}

const creatorEnv = new CreatorEnvironment();

window.missionControl = creatorEnv;
window.creatorEnv = creatorEnv;
document.addEventListener('DOMContentLoaded', () => creatorEnv.init());
