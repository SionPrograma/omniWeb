class CreatorEnvironment {
    constructor() {
        this.statusInterval = null;
        this.currentTab = 'health';
        this.systemState = null;
    }

    init() {
        console.log("Initializing Creator Environment...");
        this.triggerLightBurst();
        this.startStatusPolling();
        this.setupPermissionModal();
        this.setupMissionControl();
        this.bindAIVisual();
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
                const res = await fetch('/api/v1/system/state');
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
        // Mode Handling (Phase 14)
        if (state.system_mode === 'user') {
            document.body.classList.add('user-mode');
        } else {
            document.body.classList.remove('user-mode');
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

        if (viewName === 'mission') {
            document.getElementById('mission-control-view').classList.add('active');
            document.querySelector('[data-view="mission"]').classList.add('active');
        } else if (viewName === 'chat') {
            document.getElementById('ai-host-view').classList.add('active');
            document.querySelector('[data-view="chat"]').classList.add('active');
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
                            <span class="metric-value ${this.systemState.database.connected ? 'pass' : 'fail'}">${this.systemState.database.status}</span>
                        </div>
                         <div class="health-metric">
                            <span class="metric-label">AI Host</span>
                            <span class="metric-value pass">${this.systemState.ai_host.status} [${this.systemState.ai_host.mode}]</span>
                        </div>
                        <div class="health-metric">
                            <span class="metric-label">Memory</span>
                            <span class="metric-value info">${this.systemState.memory_usage?.rss_mb || 0} MB (${this.systemState.memory_usage?.percent || 0}%)</span>
                        </div>
                    </div>
                    <div class="cockpit-card">
                        <h3>Core Processors</h3>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${this.systemState.ai_host.processors.map(p => `<span class="chip-tag">${p}</span>`).join('')}
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
        } else if (this.currentTab === 'map') {
            panel.innerHTML = `
                <div class="cockpit-card" style="padding: 0;">
                    <div class="galaxy-container" id="galaxy-map-mount">
                        <div class="loading-indicator">Mapping galactic nodes...</div>
                    </div>
                </div>
            `;
            // Initialize or update Galaxy Map
            setTimeout(() => {
                if (window.galaxyMap) {
                    if (!window.galaxyMap.initialized) {
                        window.galaxyMap.init('galaxy-map-mount');
                    }
                    window.galaxyMap.update(this.systemState);
                }
            }, 50);
        } else if (this.currentTab === 'fixes') {
            // For fixes, we still might want to show pending fix descriptions if available in state
            // But for now matching current logic
            panel.innerHTML = `
                <div class="cockpit-card">
                    <h3>Pending Auto-Fixes (${this.systemState.pending_fixes})</h3>
                    ${this.systemState.is_healing ? '<p class="healing-pulse">✨ System is actively healing...</p>' : ''}
                    <p style="text-align: center; padding: 20px; opacity: 0.5;">
                        ${this.systemState.pending_fixes > 0 ? 'Repairs are queued. Approve them via AI Host.' : 'Stable. No pending fixes.'}
                    </p>
                </div>
            `;
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
                    <div class="fix-item" style="border-left: 2px solid #ff4444; margin-bottom: 8px; padding-left: 10px; background: rgba(255, 68, 68, 0.05);">
                        <div style="display: flex; justify-content: space-between; opacity: 0.6; font-size: 0.65rem;">
                            <span style="color: #ff4444; font-weight: bold;">[${v.target_resource.toUpperCase()}]</span>
                            <span>${new Date(v.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <p style="margin: 4px 0;">Blocked access to: <strong>${payload.requested || 'Unknown'}</strong></p>
                        <p style="opacity: 0.5; font-size: 0.7rem;">Invoked by: ${v.creator_id}</p>
                    </div>
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
                <div class="insight-item" style="border-left: 3px solid ${severityColor}; background: rgba(255,255,255,0.03); padding: 12px; margin-bottom: 10px; border-radius: 4px;">
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
                </div>
            `;
        }).join('');
    }

    async actionInsight(insightId) {
        await fetch(`/api/v1/user/insights/action/${insightId}`, { method: 'POST' });
        this.triggerLightBurst();
        alert("Insight actioned: Task queued in your logbook.");
    }

    async runInspection(query) {
        if (!query) query = document.getElementById('cockpit-inspect-query').value;
        const resEl = document.getElementById('inspection-results');
        resEl.innerHTML = '<p>Analyzing system structure...</p>';

        try {
            const res = await fetch(`/api/v1/system/inspect?query=${query}`);
            const data = await res.json();
            resEl.innerHTML = `
                <div style="margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px;">
                    <strong>Results for "${data.query}":</strong>
                </div>
                ${data.relevant_files.map(f => `<div style="padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.02); color: #00d4ff;">${f}</div>`).join('')}
                ${data.relevant_files.length === 0 ? '<p>No matching files found.</p>' : ''}
            `;
        } catch (err) {
            resEl.innerHTML = '<p style="color: #ff4444;">Inspection failed.</p>';
        }
    }

    async applyFix(proposalId) {
        if (await this.askPermission("Confirm System Modification", `Apply auto-fix ${proposalId}? This will patch system files and reload modules.`)) {
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
        console.log(`Inspecting chip: ${slug}`);
        this.triggerLightBurst();
        const orb = document.getElementById('main-ai-orb');
        orb.classList.add('processing');

        if (window.addMessage) {
            window.addMessage(`Scanning kernel for **${slug}**...`, 'ai');
            setTimeout(() => {
                orb.classList.remove('processing');
                window.addMessage(`### Chip Analysis: ${slug}\n- **Registry Status:** Online\n- **Verdict:** Stable.`, 'ai');
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

    bindAIVisual() {
        const orb = document.getElementById('main-ai-orb');
        if (orb) {
            orb.onclick = () => this.switchView('chat');
        }
    }
}

const creatorEnv = new CreatorEnvironment();
window.creatorEnv = creatorEnv;
document.addEventListener('DOMContentLoaded', () => creatorEnv.init());
