/**
 * Master Host Logbook Component
 * Handles fetching and rendering development entries.
 */
class MasterLogbook {
    constructor() {
        this.container = null;
        this.entriesList = null;
        this.currentFilter = 'all';
    }

    init() {
        this.createPanel();
        this.setupEventListeners();
    }

    createPanel() {
        const panel = document.createElement('aside');
        panel.id = 'logbook-panel';
        panel.innerHTML = `
            <header class="logbook-header">
                <div class="header-main">
                    <h2>Master Logbook</h2>
                    <span id="sys-version-tag" style="font-size: 0.6rem; background: var(--glass); padding: 2px 6px; border-radius: 10px; color: var(--accent); margin-left: 10px;">v0.0.0</span>
                </div>
                <button class="close-logbook">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M18 6L6 18M6 6l12 12"/>
                    </svg>
                </button>
            </header>
            <div id="system-dashboard" style="padding: 10px; background: rgba(0,0,0,0.2); border-bottom: 1px solid var(--glass-border); display: none;">
               <div style="display: flex; gap: 10px; font-size: 0.7rem; color: var(--text-dim);">
                  <div>Branch: <span id="sys-branch" style="color: white;">-</span></div>
                  <div>Commit: <span id="sys-commit" style="color: white;">-</span></div>
               </div>
               <div id="sys-modules" style="display: flex; gap: 5px; flex-wrap: wrap; margin-top: 5px;"></div>
            </div>
            <div class="logbook-filters">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="bug">Bugs</button>
                <button class="filter-btn" data-filter="idea">Ideas</button>
                <button class="filter-btn" data-filter="task">Tasks</button>
                <button class="filter-btn" data-filter="decision">Decisions</button>
            </div>
            <div class="logbook-entries" id="log-entries-list">
                <!-- Entries will be loaded here -->
                <div class="loading-entries" style="padding: 20px; text-align: center; color: rgba(255,255,255,0.5);">
                    Synchronizing system memory...
                </div>
            </div>
        `;
        document.getElementById('shell-container').appendChild(panel);
        this.container = panel;
        this.entriesList = document.getElementById('log-entries-list');
    }

    setupEventListeners() {
        this.container.querySelector('.close-logbook').onclick = () => this.toggle(false);

        this.container.querySelectorAll('.filter-btn').forEach(btn => {
            btn.onclick = () => {
                this.container.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.currentFilter = btn.dataset.filter;
                this.loadEntries();
            };
        });
    }

    async loadEntries() {
        try {
            // Load Snapshot first if not loaded or every time
            const snapRes = await fetch('/api/v1/system/logbook/snapshot', {
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            const snap = await snapRes.json();
            this.updateSystemUI(snap);

            let url = '/api/v1/system/logbook/';
            if (this.currentFilter !== 'all') {
                url += `?type=${this.currentFilter}`;
            }

            const response = await fetch(url, {
                headers: {
                    'Authorization': 'Bearer omniweb-dev-secret-token'
                }
            });
            const data = await response.json();
            this.renderEntries(data);
        } catch (error) {
            console.error('Failed to load logbook entries:', error);
            this.entriesList.innerHTML = '<div style="padding: 20px; color: #ff5050;">Error access memory bank.</div>';
        }
    }

    updateSystemUI(snap) {
        const vTag = document.getElementById('sys-version-tag');
        const dash = document.getElementById('system-dashboard');
        const branchEl = document.getElementById('sys-branch');
        const commitEl = document.getElementById('sys-commit');
        const modulesEl = document.getElementById('sys-modules');

        if (vTag) vTag.innerText = snap.version;
        if (dash) dash.style.display = 'block';
        if (branchEl) branchEl.innerText = snap.git_branch;
        if (commitEl) commitEl.innerText = snap.last_commit;

        if (modulesEl && snap.module_inventory) {
            modulesEl.innerHTML = snap.module_inventory.map(m =>
                `<span style="font-size: 0.6rem; background: rgba(50,255,150,0.1); color: #32ff96; padding: 1px 5px; border-radius: 4px; border: 1px solid rgba(50,255,150,0.2);">${m}</span>`
            ).join('');
        }
    }

    renderEntries(entries) {
        if (entries.length === 0) {
            this.entriesList.innerHTML = '<div style="padding: 40px; text-align: center; color: rgba(255,255,255,0.3);">No entries found. Start by telling the AI Host.</div>';
            return;
        }

        this.entriesList.innerHTML = entries.map(entry => `
            <div class="log-entry">
                <div class="log-entry-header">
                    <span class="entry-type type-${entry.type}">${entry.type}</span>
                    <span class="entry-priority ${entry.priority}">${entry.priority}</span>
                </div>
                <div class="log-entry-content">${entry.content}</div>
                <div class="log-entry-footer">
                    <span>${new Date(entry.timestamp).toLocaleDateString()}</span>
                    ${entry.chip_reference ? `<span class="chip-tag">${entry.chip_reference}</span>` : ''}
                    <span class="entry-status status-${entry.status}">${entry.status}</span>
                </div>
            </div>
        `).join('');
    }

    toggle(force) {
        const isActive = force !== undefined ? force : !this.container.classList.contains('active');
        if (isActive) {
            this.container.classList.add('active');
            this.loadEntries();
        } else {
            this.container.classList.remove('active');
        }
    }
}

const masterLogbook = new MasterLogbook();
window.masterLogbook = masterLogbook;
document.addEventListener('DOMContentLoaded', () => masterLogbook.init());
