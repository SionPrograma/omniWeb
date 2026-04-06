/**
 * OMNIWEB — BLOQUE: WISDOM ATLAS UX COMPONENT.
 * Unified visual surface for tactical memory and reusable knowledge.
 */

class WisdomAtlas {
    constructor() {
        this.container = null;
        this.nodes = [];
        this.filteredNodes = [];
        this.activeFilter = 'ALL';
        this.selectedNode = null;
    }

    viewNodeDetail(nodeId) {
        this.showDetail(nodeId);
    }

    async init(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.renderShell();
        if (window.wisdomGraph) {
            window.wisdomGraph.init();
        }
        if (window.wisdomReasoner) {
            window.wisdomReasoner.analyzeCurrentContext();
        }
        await this.loadNodes();
    }

    renderShell() {
        this.container.innerHTML = `
            <div class="wisdom-atlas-container">
                <header class="atlas-header">
                    <div class="atlas-title-group">
                        <span class="node-type-badge">CORE GOVERNANCE — TACTICAL MEMORY</span>
                        <h1>Wisdom Atlas</h1>
                        <p class="atlas-subtitle">Memoria táctica unificada, precedente multi-proyecto y patrones de decisión validados.</p>
                    </div>
                    <div class="atlas-controls">
                        <select id="atlas-type-filter" class="atlas-btn">
                            <option value="ALL">Todos los tipos</option>
                            <option value="LEARNING">Learnings</option>
                            <option value="AUTOPSY">Autopsias</option>
                            <option value="DECISION">Decisiones</option>
                            <option value="REPLAY_SYNC">REPLAY Sync</option>
                        </select>
                        <button id="refresh-atlas-btn" class="atlas-btn primary">Actualizar Sabiduría</button>
                        <button id="open-graph-btn" class="atlas-btn secondary graph-trigger">Wisdom Graph Explorer</button>
                    </div>
                </header>

                <!-- OMNIWEB — BLOQUE: TACTICAL WISDOM REASONER PANEL -->
                <div id="wisdom-reasoner-panel" class="wisdom-reasoner-panel">
                    <div class="loading-state">Analizando precedentes tácticos...</div>
                </div>

                <!-- OMNIWEB — BLOQUE: TACTICAL WISDOM FEEDBACK PANEL -->
                <div id="wisdom-feedback-surface" style="margin-top: 20px;"></div>

                <main id="atlas-surface" class="atlas-surface">
                    <div class="loading-state">Iniciando mapeo de sabiduría contextual...</div>
                </main>
                
                <div id="atlas-overlay" class="atlas-overlay" style="display:none;"></div>

                <!-- OMNIWEB — BLOQUE: WISDOM GRAPH EXPLORER LAYER -->
                <div id="wisdom-graph-layer" class="wisdom-graph-layer">
                    <header class="graph-header">
                        <div class="graph-title-section">
                            <span class="node-type-badge">CORE GOVERNANCE — TACTICAL CONNECTOR</span>
                            <h2>Wisdom Graph Explorer</h2>
                        </div>
                        <div class="graph-controls">
                            <button id="refresh-graph-btn" class="atlas-btn secondary">Refrescar Relaciones</button>
                            <button id="close-graph-btn" class="atlas-btn primary">Cerrar Grafo</button>
                        </div>
                    </header>
                    <div id="wisdom-graph-viewport" class="wisdom-graph-viewport">
                        <div class="graph-legend">
                            <div class="legend-item"><span class="legend-color" style="background:#4ade80"></span> Learning</div>
                            <div class="legend-item"><span class="legend-color" style="background:#60a5fa"></span> Autopsia</div>
                            <div class="legend-item"><span class="legend-color" style="background:#fbbf24"></span> Decisión</div>
                            <div class="legend-item"><span class="legend-color" style="background:#f87171"></span> Replay Sync</div>
                            <div class="legend-item"><span class="legend-color" style="background:#a78bfa"></span> Context Match</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.getElementById('refresh-atlas-btn').addEventListener('click', () => this.refreshAtlas());
        document.getElementById('open-graph-btn').addEventListener('click', () => {
            if (window.wisdomGraph) {
                window.wisdomGraph.toggle();
            }
        });
        document.getElementById('close-graph-btn').addEventListener('click', () => {
            if (window.wisdomGraph) {
                window.wisdomGraph.toggle();
            }
        });
        document.getElementById('refresh-graph-btn').addEventListener('click', async () => {
            if (window.wisdomGraph) {
                const btn = document.getElementById('refresh-graph-btn');
                btn.innerText = "Reconstruyendo...";
                btn.disabled = true;
                await fetch('/api/v1/governance/wisdom/graph/refresh', {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}` }
                });
                await window.wisdomGraph.refresh();
                btn.innerText = "Refrescar Relaciones";
                btn.disabled = false;
            }
        });
        document.getElementById('atlas-type-filter').addEventListener('change', (e) => {
            this.activeFilter = e.target.value;
            this.applyFilters();
        });
    }

    async loadNodes() {
        try {
            const response = await fetch('/api/governance/wisdom/atlas/nodes');
            const data = await response.json();

            if (data.status === 'success') {
                this.nodes = data.payload;
                this.applyFilters();
                await this.loadFeedback();
            } else {
                console.error("Failed to load atlas nodes:", data.message);
                this.renderEmptyState();
            }
        } catch (err) {
            console.error("Atlas loading error:", err);
            this.renderEmptyState();
        }
    }

    async loadFeedback() {
        const surface = document.getElementById('wisdom-feedback-surface');
        if (!surface) return;

        try {
            const response = await fetch('/api/v1/governance/wisdom/feedback/pending', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}` }
            });
            const data = await response.json();
            if (data.status === 'success' && data.payload.length > 0) {
                this.renderFeedback(surface, data.payload);
            } else {
                surface.innerHTML = '';
            }
        } catch (err) {
            console.warn("Atlas feedback load failed", err);
        }
    }

    renderFeedback(container, items) {
        container.innerHTML = `
            <div class="atlas-feedback-panel animate-slide-in">
                <div style="font-size: 0.65rem; color: #ffaa00; font-weight: bold; letter-spacing: 1px; margin-bottom: 12px; display:flex; justify-content:space-between;">
                    <span>Sugerencias de Recalibración Táctica</span>
                    <span style="opacity:0.5;">${items.length} EVENTOS</span>
                </div>
                ${items.map(item => `
                    <div class="feedback-item ${item.feedback_state}" style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 12px; margin-bottom: 10px; display:flex; gap:15px; align-items:center;">
                        <div style="font-size: 1.5rem;">${item.feedback_state === 'WISDOM_CONFIRMED' ? '✅' : (item.feedback_state === 'WISDOM_CONTRADICTED' ? '❌' : '⚠️')}</div>
                        <div style="flex:1;">
                            <div style="font-size: 0.85rem; font-weight:bold; color:#fff;">${item.feedback_state.replace(/_/g, ' ')}</div>
                            <div style="font-size: 0.75rem; color:#ccc;">${item.rationale}</div>
                            <div style="font-size: 0.65rem; color:#ffaa00; margin-top:5px; font-family:monospace;">Delta: ${item.proposed_confidence_delta > 0 ? '+' : ''}${(item.proposed_confidence_delta * 100).toFixed(0)}% confianza</div>
                        </div>
                        <div style="display:flex; gap:8px;">
                            <button class="atlas-btn tertiary" style="font-size:0.6rem; padding:6px 12px;" onclick="window.wisdomAtlas.processFeedback('${item.feedback_id}', 'IGNORE')">Ignorar</button>
                            <button class="atlas-btn primary" style="font-size:0.6rem; padding:6px 12px;" onclick="window.wisdomAtlas.processFeedback('${item.feedback_id}', 'APPLY')">Recalibrar Atlas</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async processFeedback(fbId, action) {
        if (action === 'IGNORE') {
            document.getElementById('wisdom-feedback-surface').innerHTML = '';
            return;
        }
        try {
            const res = await fetch(`/api/v1/governance/wisdom/feedback/${fbId}/confirm`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}` }
            });
            const data = await res.json();
            if (data.status === 'success') {
                await this.refreshAtlas();
                await this.loadFeedback();
            }
        } catch (err) {
            console.error("Feedback confirmation failed", err);
        }
    }

    async refreshAtlas() {
        const btn = document.getElementById('refresh-atlas-btn');
        if (!btn) return;
        const originalText = btn.innerText;
        btn.innerText = "Agregando...";
        btn.disabled = true;

        try {
            const response = await fetch('/api/governance/wisdom/atlas/refresh', { method: 'POST' });
            const data = await response.json();
            if (data.status === 'success') {
                await this.loadNodes();
            }
        } catch (err) {
            console.error("Refresh failed:", err);
        } finally {
            btn.innerText = originalText;
            btn.disabled = false;
        }
    }

    applyFilters() {
        if (this.activeFilter === 'ALL') {
            this.filteredNodes = this.nodes;
        } else {
            this.filteredNodes = this.nodes.filter(n => n.node_type === this.activeFilter);
        }

        this.renderNodes();
    }

    renderNodes() {
        const surface = document.getElementById('atlas-surface');
        if (!surface) return;
        if (this.filteredNodes.length === 0) {
            surface.innerHTML = '<div class="empty-state">No se han encontrado registros de sabiduría para los filtros actuales.</div>';
            return;
        }

        surface.innerHTML = this.filteredNodes.map(node => `
            <div class="wisdom-node-card node-${node.node_type.toLowerCase()}" data-id="${node.node_id}">
                <span class="node-type-badge">${node.node_type}</span>
                <h3 class="node-title">${node.title}</h3>
                <p class="node-summary">${node.summary.substring(0, 120)}${node.summary.length > 120 ? '...' : ''}</p>
                <div class="node-meta">
                    <div class="confidence-indicator">
                        <span class="confidence-dot ${this.getConfidenceClass(node.confidence)}"></span>
                        <span>Confidence: <strong>${Math.round(node.confidence * 100)}%</strong></span>
                    </div>
                    <div class="reusability-meter" title="Reusability: ${Math.round(node.reusability_score * 100)}%">
                        <div class="reusability-fill" style="width: ${node.reusability_score * 100}%"></div>
                    </div>
                </div>
            </div>
        `).join('');

        surface.querySelectorAll('.wisdom-node-card').forEach(card => {
            card.addEventListener('click', () => this.showDetail(card.dataset.id));
        });
    }

    getConfidenceClass(score) {
        if (score >= 0.8) return 'conf-high';
        if (score >= 0.5) return 'conf-mid';
        return 'conf-low';
    }

    async showDetail(nodeId) {
        const node = this.nodes.find(n => n.node_id === nodeId);
        if (!node) return;

        const overlay = document.getElementById('atlas-overlay');
        overlay.style.display = 'flex';

        overlay.innerHTML = `
            <div class="atlas-node-detail">
                <button class="close-detail">&times;</button>
                <div class="detail-content">
                    <div class="detail-header">
                        <span class="node-type-badge">${node.node_type}</span>
                        <h2>${node.title}</h2>
                        <div class="detail-pills">
                            <span class="pill">Confidence: ${Math.round(node.confidence * 100)}%</span>
                            <span class="pill">Reusability: ${Math.round(node.reusability_score * 100)}%</span>
                            <span class="pill status-${node.status_band.toLowerCase()}">${node.status_band}</span>
                        </div>
                    </div>
                    
                    <div class="detail-body">
                        <h3>Resumen Estructural</h3>
                        <p>${node.summary}</p>
                        
                        <div class="evidence-section">
                            <h3>Evidencia y Contexto</h3>
                            <div class="evidence-grid">
                                ${Object.entries(node.evidence_refs).map(([k, v]) => `
                                    <div class="evidence-item">
                                        <label>${k.replace(/_/g, ' ')}</label>
                                        <span>${typeof v === 'object' ? JSON.stringify(v) : v}</span>
                                    </div>
                                `).join('')}
                                <div class="evidence-item">
                                    <label>Dominios Afectados</label>
                                    <span>${node.affected_domains.join(', ') || 'Global'}</span>
                                </div>
                                <div class="evidence-item">
                                    <label>Origen</label>
                                    <span>${node.source_ref_type} ID: ${node.source_ref_id}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="actions-footer">
                        <button class="atlas-btn secondary close-btn">Cerrar</button>
                        ${node.node_type === 'LEARNING' || node.node_type === 'REUSABLE_TACTIC' ?
                `<button class="atlas-btn primary simulate-btn" data-id="${node.source_ref_id}">Simular en Proyecto Actual</button>` : ''}
                    </div>
                </div>
            </div>
        `;

        overlay.querySelector('.close-detail').onclick = () => overlay.style.display = 'none';
        overlay.querySelector('.close-btn').onclick = () => overlay.style.display = 'none';

        const simBtn = overlay.querySelector('.simulate-btn');
        if (simBtn) {
            simBtn.onclick = () => {
                alert(`Lanzando simulación táctica contextual para el recurso ${node.source_ref_id}...`);
                overlay.style.display = 'none';
            };
        }
    }

    renderEmptyState() {
        const surface = document.getElementById('atlas-surface');
        if (!surface) return;
        surface.innerHTML = `
            <div class="empty-state">
                <p>El Atlas de Sabiduría está vacío.</p>
                <button class="atlas-btn primary" onclick="window.wisdomAtlas.refreshAtlas()">Forzar Agregación</button>
            </div>
        `;
    }
}

window.wisdomAtlas = new WisdomAtlas();
