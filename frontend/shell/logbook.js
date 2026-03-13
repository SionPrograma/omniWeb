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
            <div class="panel-handle"></div>
            <header class="logbook-header">
                <div class="header-main">
                    <h2>Master Logbook</h2>
                </div>
                <button class="close-logbook">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M19 12H5M12 19l-7-7 7-7" />
                    </svg>
                </button>
            </header>
            
            <div id="system-dashboard">
                <div class="stats-grid">
                    <div class="stat-item">
                        System Version
                        <span class="stat-value" id="log-sys-version">-</span>
                    </div>
                    <div class="stat-item">
                        Git Branch
                        <span class="stat-value" id="log-sys-branch">-</span>
                    </div>
                    <div class="stat-item" style="grid-column: span 2;">
                        Active Context
                        <div id="sys-modules" style="display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px;"></div>
                    </div>
                </div>
            </div>

            <div class="logbook-filters">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="idea">Ideas</button>
                <button class="filter-btn" data-filter="bug">Bugs</button>
                <button class="filter-btn" data-filter="system_audit">Audits</button>
                <button class="filter-btn" data-filter="auto_fix">Fixes</button>
                <button class="filter-btn" data-filter="roadmap">Roadmap</button>
            </div>

            <div class="logbook-entries" id="log-entries-list">
                <div class="loading-entries" style="padding: 40px; text-align: center;">
                    <div class="spinner" style="margin-bottom: 10px;">⚡</div>
                    <span style="opacity: 0.5; font-size: 0.8rem;">Accessing Omni memory bank...</span>
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

        // Interactive Drag-to-Close
        let touchStartX = 0;
        let currentX = 0;
        let isDragging = false;

        this.container.addEventListener('touchstart', (e) => {
            touchStartX = e.touches[0].clientX;
            isDragging = true;
            this.container.style.transition = 'none';
        }, { passive: true });

        this.container.addEventListener('touchmove', (e) => {
            if (!isDragging) return;
            const touchX = e.touches[0].clientX;
            currentX = touchX - touchStartX;

            if (currentX > 0) {
                this.container.style.transform = `translateX(${currentX}px)`;
            }
        }, { passive: true });

        this.container.addEventListener('touchend', (e) => {
            if (!isDragging) return;
            isDragging = false;
            this.container.style.transition = '';

            if (currentX > 100) {
                this.toggle(false);
            } else {
                this.container.style.transform = '';
            }
            currentX = 0;
        }, { passive: true });
    }

    async loadEntries() {
        try {
            const snapRes = await fetch('/api/v1/system/logbook/snapshot', {
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            const snap = await snapRes.json();
            this.updateSystemUI(snap);

            let url = '/api/v1/system/logbook/';
            const params = new URLSearchParams();
            if (this.currentFilter !== 'all') params.append('type', this.currentFilter);

            if (params.toString()) url += `?${params.toString()}`;

            const response = await fetch(url, {
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            const data = await response.json();
            this.renderEntries(data);
        } catch (error) {
            console.error('Failed to load logbook entries:', error);
            this.entriesList.innerHTML = '<div style="padding: 20px; color: #ff5050; text-align: center;">Error: System link interrupted.</div>';
        }
    }

    updateSystemUI(snap) {
        document.getElementById('log-sys-version').innerText = snap.version || '0.0.0';
        document.getElementById('log-sys-branch').innerText = snap.git_branch || 'main';

        const modulesEl = document.getElementById('sys-modules');
        if (modulesEl && snap.module_inventory) {
            modulesEl.innerHTML = snap.module_inventory.map(m =>
                `<span style="font-size: 0.6rem; background: rgba(50,150,255,0.1); color: #3296ff; padding: 1px 5px; border-radius: 4px; border: 1px solid rgba(50,150,255,0.2);">${m}</span>`
            ).join('');
        }
    }

    renderEntries(entries) {
        if (entries.length === 0) {
            this.entriesList.innerHTML = `
                <div style="padding: 60px 20px; text-align: center; color: rgba(255,255,255,0.2);">
                    <p style="font-size: 0.9rem;">No entries found in this frequency.</p>
                    <p style="font-size: 0.7rem;">Try: "Log idea: improve the shell interface"</p>
                </div>
            `;
            return;
        }

        this.entriesList.innerHTML = entries.map(entry => `
            <div class="log-entry entry-${entry.type}" id="entry-${entry.id}" onclick="masterLogbook.toggleEntry('${entry.id}')">
                <div class="log-entry-header">
                    <span class="entry-type">${entry.type}</span>
                    <span class="entry-priority priority-${entry.priority}">${entry.priority}</span>
                </div>
                <div class="log-entry-content">${this.escapeHTML(entry.content)}</div>
                
                <div class="entry-metadata" style="display: none; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px; font-size: 0.65rem; color: #888; margin-bottom: 10px;">
                    <strong style="display: block; margin-bottom: 4px; color: #aaa;">System Context:</strong>
                    ${Object.entries(entry.metadata || {}).map(([k, v]) => `<div><span style="color: #555;">${k}:</span> ${v}</div>`).join('')}
                </div>

                <div class="log-entry-footer">
                    <span>${new Date(entry.timestamp).toLocaleDateString()}</span>
                    ${entry.chip_reference ? `<span class="chip-tag">${entry.chip_reference}</span>` : ''}
                    <div class="status-badge status-${entry.status}" onclick="event.stopPropagation(); masterLogbook.toggleStatus('${entry.id}', '${entry.status}')">
                        ${entry.status}
                    </div>
                </div>
            </div>
        `).join('');
    }

    toggleEntry(id) {
        const entry = document.getElementById(`entry-${id}`);
        const meta = entry.querySelector('.entry-metadata');
        const isCollapsed = meta.style.display === 'none';

        // Collapse others
        this.entriesList.querySelectorAll('.entry-metadata').forEach(m => m.style.display = 'none');
        this.entriesList.querySelectorAll('.log-entry').forEach(e => e.classList.remove('expanded'));

        if (isCollapsed) {
            meta.style.display = 'block';
            entry.classList.add('expanded');
        }
    }

    escapeHTML(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    async toggleStatus(entryId, currentStatus) {
        const newStatus = currentStatus === 'done' ? 'open' : 'done';
        try {
            const response = await fetch(`/api/v1/system/logbook/${entryId}/status?status=${newStatus}`, {
                method: 'PATCH',
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            if (response.ok) {
                this.loadEntries(); // Refresh
            }
        } catch (error) {
            console.error('Failed to update status:', error);
        }
    }

    toggle(force) {
        const isActive = force !== undefined ? force : !this.container.classList.contains('active');
        if (isActive) {
            // Coordinate with Shell
            if (window.omniShell) window.omniShell.closeLauncher();

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
