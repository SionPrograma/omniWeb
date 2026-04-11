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
            // OMNIWEB — BLOQUE: GOVERNANCE POST-MISSION WISDOM SYNC & POLICY REVIEW
            const [syncRes, propRes] = await Promise.all([
                fetch('/api/v1/governance/wisdom/sync/pending', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}` }
                }),
                fetch('/api/v1/governance/catalyst/policy/proposals', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}` }
                })
            ]);

            const syncData = await syncRes.json();
            const propData = await propRes.json();

            const syncItems = syncData.status === 'success' ? syncData.payload : [];
            const proposals = propData.status === 'success' ? propData.payload : [];

            if (syncItems.length > 0 || proposals.length > 0) {
                this.renderFeedback(surface, syncItems, proposals);
            } else {
                surface.innerHTML = '';
            }
        } catch (err) {
            console.warn("Atlas feedback/proposals load failed", err);
        }
    }

    renderFeedback(container, items, proposals = []) {
        let proposalHtml = '';
        if (proposals.length > 0) {
            proposalHtml = `
                <div style="margin-bottom: 25px; border-bottom: 1px solid rgba(139, 92, 246, 0.3); padding-bottom: 15px;">
                    <div style="font-size: 0.65rem; color: #8b5cf6; font-weight: bold; letter-spacing: 1px; margin-bottom: 12px;">
                        REFINAMIENTO DE POLÍTICA CATALYST (MODO GUIADO)
                    </div>
                    ${proposals.map(p => `
                        <div class="feedback-item" style="background: rgba(139, 92, 246, 0.05); border-left: 4px solid #8b5cf6; padding: 15px; border-radius: 12px; margin-bottom: 10px; display:flex; gap:15px; align-items:center;">
                            <div style="font-size: 1.5rem;">⚖️</div>
                            <div style="flex:1;">
                                <div style="font-size: 0.85rem; font-weight:bold; color:#fff;">${p.type.replace(/_/g, ' ')}</div>
                                <div style="font-size: 0.75rem; color:#ccc;">${p.rationale}</div>
                                <div style="font-size: 0.65rem; color:#8b5cf6; margin-top:5px; font-family:monospace;">
                                    Patrón: ${p.pattern_origin} | Frecuencia: ${p.occurrence_count} | Confianza: ${p.confidence}
                                </div>
                            </div>
                            <div style="display:flex; gap:8px;">
                                <button class="atlas-btn primary" style="font-size:0.6rem; padding:6px 12px; background:#4c1d95;" onclick="alert('Funcionalidad de aplicación en desarrollo (V0.5). Revise Ledger para auditoría.')">Registrar</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        container.innerHTML = `
            <div class="atlas-feedback-panel animate-slide-in">
                ${proposalHtml}
                <div style="font-size: 0.65rem; color: #4ade80; font-weight: bold; letter-spacing: 1px; margin-bottom: 12px; display:flex; justify-content:space-between;">
                    <span>Sugerencias de Recalibración Táctica (Post-Mission Sync)</span>
                    <span style="opacity:0.5;">${items.length} PENDIENTES</span>
                </div>
                ${items.map(item => `
                    <div class="feedback-item ${item.actual_outcome_type}" style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 12px; margin-bottom: 10px; display:flex; gap:15px; align-items:center;">
                        <div style="font-size: 1.5rem;">${item.actual_outcome_type === 'WISDOM_CONFIRMED' ? '✅' : (item.actual_outcome_type === 'WISDOM_CONTRADICTED' ? '❌' : '⚠️')}</div>
                        <div style="flex:1;">
                            <div style="font-size: 0.85rem; font-weight:bold; color:#fff;">${item.actual_outcome_type.replace(/_/g, ' ')}</div>
                            <div style="font-size: 0.75rem; color:#ccc;">${item.rationale}</div>
                            <div style="font-size: 0.65rem; color:#4ade80; margin-top:5px; font-family:monospace;">
                                Delta: ${item.proposed_confidence_delta > 0 ? '+' : ''}${(item.proposed_confidence_delta * 100).toFixed(0)}% confianza | 
                                Mission: <span style="opacity:0.6;">${item.source_mission_id.substring(0, 8)}</span>
                                ${item.catalyst_trace_id ? `<span class="catalyst-tag clickable" style="margin-left:10px;" onclick="window.wisdomAtlas.showTrace('${item.catalyst_trace_id}')">VÍA CATALYST [TRACE]</span>` : ''}
                            </div>
                        </div>
                        <div style="display:flex; gap:8px;">
                            <button class="atlas-btn tertiary" style="font-size:0.6rem; padding:6px 12px;" onclick="window.wisdomAtlas.processFeedback('${item.sync_id}', 'REJECTED')">Ignorar</button>
                            <button class="atlas-btn primary" style="font-size:0.6rem; padding:6px 12px;" onclick="window.wisdomAtlas.processFeedback('${item.sync_id}', 'ACCEPTED')">Recalibrar Atlas</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async processFeedback(syncId, decision) {
        try {
            // OMNIWEB — BLOQUE: GOVERNANCE POST-MISSION WISDOM SYNC
            const res = await fetch(`/api/v1/governance/wisdom/sync/${syncId}/decision`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ decision })
            });
            const data = await res.json();
            if (data.status === 'success') {
                await this.refreshAtlas();
                await this.loadFeedback();
            }
        } catch (err) {
            console.error("Sync decision failed", err);
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
        const overlay = document.getElementById('atlas-overlay');
        overlay.style.display = 'flex';
        overlay.innerHTML = `<div class="atlas-node-detail"><div class="loading-state">Consultando verdad operativa...</div></div>`;

        try {
            // OMNIWEB — BLOQUE: ATLAS EVIDENCE UI
            // Fetch enriched detail with sync history
            const response = await fetch(`/api/v1/governance/wisdom/atlas/node/${nodeId}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}` }
            });
            const data = await response.json();

            if (data.status !== 'success') throw new Error(data.message);
            const node = data.payload;
            const syncHistory = node.sync_history || [];

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
                            <div class="detail-tabs">
                                <button class="tab-btn active" id="tab-info-btn">Información</button>
                                <button class="tab-btn" id="tab-history-btn">Evidencia (${syncHistory.length})</button>
                            </div>

                            <div id="tab-info-content" class="tab-content">
                                <h3>Resumen Estructural</h3>
                                <p style="line-height: 1.5; color: #ddd; margin-bottom: 20px;">${node.summary}</p>
                                
                                <!-- OMNIWEB — BLOQUE: ATLAS EVIDENCE UI — SUMMARY BADGE STRIP -->
                                <div class="evidence-summary-strip">
                                    <div class="summary-badge conf" title="Misiones que validaron este nodo">
                                        <label>CONFIRMED</label>
                                        <span class="count">${node.evidence_summary.WISDOM_CONFIRMED}</span>
                                    </div>
                                    <div class="summary-badge partial" title="Misiones con éxito parcial">
                                        <label>PARTIAL</label>
                                        <span class="count">${node.evidence_summary.WISDOM_PARTIAL}</span>
                                    </div>
                                    <div class="summary-badge contradicted" title="Misiones que fallaron siguiendo esta táctica">
                                        <label>CONTRADICTED</label>
                                        <span class="count">${node.evidence_summary.WISDOM_CONTRADICTED}</span>
                                    </div>
                                    <div class="summary-badge biased" title="Misiones donde no se respetaron precondiciones">
                                        <label>EXECUTION BIASED</label>
                                        <span class="count">${node.evidence_summary.EXECUTION_BIASED}</span>
                                    </div>
                                </div>

                                <div class="evidence-section">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                                        <h3>Metadatos de Sabiduría</h3>
                                        ${node.evidence_summary.last_reviewed_at ? `
                                            <span style="font-size:0.65rem; color:rgba(255,255,255,0.4);">ÚLTIMA REVISIÓN: ${new Date(node.evidence_summary.last_reviewed_at).toLocaleDateString()}</span>
                                        ` : ''}
                                    </div>
                                    <div class="evidence-grid">
                                        ${Object.entries(node.evidence_refs).map(([k, v]) => `
                                            <div class="evidence-item">
                                                <label>${k.replace(/_/g, ' ')}</label>
                                                <span>${typeof v === 'object' ? JSON.stringify(v) : v}</span>
                                            </div>
                                        `).join('')}
                                        <div class="evidence-item">
                                            <label>Origen</label>
                                            <span style="font-size:0.7rem; font-family:monospace; opacity:0.8;">${node.source_ref_type}</span>
                                        </div>
                                        <div class="evidence-item">
                                            <label>Dominios</label>
                                            <span>${node.affected_domains.join(', ') || 'Global'}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div id="tab-history-content" class="tab-content" style="display:none;">
                                <h3 style="margin-bottom:15px;">Historial de Verdad (Runtime Evidence)</h3>
                                ${syncHistory.length === 0 ?
                    '<div class="empty-evidence">No hay misiones vinculadas a esta unidad de sabiduría aún.</div>' :
                    `<div class="sync-history-list">
                                        ${syncHistory.map(s => {
                        const outcome = s.actual_outcome_type;
                        const stateClass = outcome === 'WISDOM_CONFIRMED' ? 'sync-success' :
                            outcome === 'WISDOM_CONTRADICTED' ? 'sync-fail' :
                                outcome === 'EXECUTION_BIASED' ? 'sync-biased' : 'sync-partial';
                        return `
                                                <div class="history-item ${stateClass}">
                                                    <div class="history-meta">
                                                        <span class="sync-date">${new Date(s.created_at).toLocaleDateString()}</span>
                                                        <span class="sync-outcome">${outcome.replace(/_/g, ' ')}</span>
                                                        ${s.creator_decision === 'PENDING' ? '<span class="pending-badge">DECISION PENDING</span>' : ''}
                                                    </div>
                                                    <div class="history-rationale">${s.rationale}</div>
                                                    <div class="history-footer">
                                                        <div class="history-trace">
                                                             Trace: <small style="opacity:0.6">${s.sync_id.substring(0, 8)}</small>
                                                             ${s.catalyst_trace_id ? `<span class="catalyst-tag clickable" onclick="window.wisdomAtlas.showTrace('${s.catalyst_trace_id}')">VÍA CATALYST [VER TRACE]</span>` : ''}
                                                        </div>
                                                        ${s.creator_decision === 'PENDING' ? `
                                                            <div class="history-actions">
                                                                <button class="atlas-btn tertiary mini" onclick="window.wisdomAtlas.processFeedback('${s.sync_id}', 'REJECTED'); window.wisdomAtlas.showDetail('${nodeId}')">Rechazar</button>
                                                                <button class="atlas-btn primary mini" onclick="window.wisdomAtlas.processFeedback('${s.sync_id}', 'ACCEPTED'); window.wisdomAtlas.showDetail('${nodeId}')">Aprobar Sync</button>
                                                            </div>
                                                        ` : ''}
                                                    </div>
                                                </div>
                                            `;
                    }).join('')}
                                    </div>`
                }
                            </div>
                        </div>

                        <div class="actions-footer">
                            <button class="atlas-btn secondary close-btn">Cerrar</button>
                            ${node.node_type === 'LEARNING' ?
                    `<button class="atlas-btn primary simulate-btn" data-id="${node.source_ref_id}">Proyectar Táctica</button>` : ''}
                        </div>
                    </div>
                </div>
            `;

            // Tab Logic
            const infoBtn = overlay.querySelector('#tab-info-btn');
            const historyBtn = overlay.querySelector('#tab-history-btn');
            const infoContent = overlay.querySelector('#tab-info-content');
            const historyContent = overlay.querySelector('#tab-history-content');

            infoBtn.onclick = () => {
                infoBtn.classList.add('active');
                historyBtn.classList.remove('active');
                infoContent.style.display = 'block';
                historyContent.style.display = 'none';
            };

            historyBtn.onclick = () => {
                historyBtn.classList.add('active');
                infoBtn.classList.remove('active');
                infoContent.style.display = 'none';
                historyContent.style.display = 'block';
            };

            overlay.querySelector('.close-detail').onclick = () => overlay.style.display = 'none';
            overlay.querySelector('.close-btn').onclick = () => overlay.style.display = 'none';

            const simBtn = overlay.querySelector('.simulate-btn');
            if (simBtn) {
                simBtn.onclick = () => {
                    alert(`Iniciando simulación de impacto para el recurso ${node.source_ref_id}...`);
                    overlay.style.display = 'none';
                };
            }
        } catch (err) {
            console.error("Detail load failed", err);
            overlay.innerHTML = `<div class="atlas-node-detail"><div class="error-state">Error al cargar evidencia: ${err.message}</div><button class="atlas-btn secondary close-panel-btn">Cerrar</button></div>`;
            overlay.querySelector('.close-panel-btn').onclick = () => overlay.style.display = 'none';
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
    async showTrace(traceId) {
        // --- OMNI_CATALYST_TRACE_AUDIT_DEEP_LINK ---
        const overlay = document.createElement('div');
        overlay.className = 'atlas-overlay trace-inspector-overlay';
        overlay.innerHTML = `
            <div class="atlas-node-detail trace-inspector-panel">
                <button class="close-detail" id="close-trace">×</button>
                <div class="detail-content">
                    <div style="font-size:0.6rem; color: #4ade80; font-weight:700; display:flex; justify-content:space-between;">
                        <span>CATALYST TRACE AUDIT</span>
                        <span>TRACE_ID: ${traceId}</span>
                    </div>
                    <h2 style="margin-top:10px;">Forensics of Acceleration</h2>
                    <div id="trace-payload" style="margin-top:20px;">
                        <div class="loading-spinner">Retrieveing stored trace...</div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
        document.getElementById('close-trace').onclick = () => overlay.remove();

        try {
            const res = await fetch(`/api/v1/governance/catalyst/trace/${traceId}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omniweb_token')}` }
            });
            const data = await res.json();

            const container = document.getElementById('trace-payload');
            if (data.status === 'success') {
                container.innerHTML = data.payload.map(evt => {
                    const refs = JSON.parse(evt.evidence_refs);
                    let structuredHTML = '';

                    // Compact Audit View for Catalyst Events
                    if (evt.decision_type.includes('INVOKE')) {
                        structuredHTML = `
                            <div class="audit-field"><label>MODE:</label> <span>${refs.translation_mode ? 'Spec Translation' : 'Tactical Acceleration'}</span></div>
                            <div class="audit-field"><label>INPUT SUMMARY:</label> <p>${refs.objective || 'N/A'}</p></div>
                            <div class="audit-field"><label>BRIDGE:</label> <span>${refs.technical_memory_context ? 'Memory Bridge Connected' : 'Direct Call'}</span></div>
                        `;
                    } else if (evt.decision_type.includes('SUCCESS')) {
                        structuredHTML = `
                            <div class="audit-field"><label>OUTPUT RATIONALE:</label> <p>${refs.rationale || 'N/A'}</p></div>
                            <div class="audit-field"><label>CONFIDENCE:</label> <span class="pill">${Math.round(refs.confidence * 100) || 100}%</span></div>
                            <div class="audit-field"><label>STEPS GENERATED:</label> <span>${(refs.steps || refs.mission_steps || []).length} items</span></div>
                        `;
                    } else if (evt.decision_type.includes('REJECT')) {
                        structuredHTML = `
                            <div class="audit-field" style="color:#ef4444;"><label>POLICY BLOCK:</label> <p>Blocked by security policy gate.</p></div>
                            <div class="audit-field"><label>RAW BLOCKED CONTENT:</label> <pre style="font-size:0.65rem;">${JSON.stringify(refs, null, 2)}</pre></div>
                        `;
                    } else {
                        structuredHTML = `<pre style="font-size:0.65rem; opacity:0.7;">${JSON.stringify(refs, null, 2)}</pre>`;
                    }

                    return `
                        <div class="trace-event-item" style="background:rgba(0,0,0,0.2); padding:15px; border-radius:10px; margin-bottom:15px; border-left:3px solid ${evt.decision_type.includes('SUCCESS') ? '#4ade80' : '#4f46e5'};">
                            <div style="display:flex; justify-content:space-between; margin-bottom:10px;">
                                <span style="font-size:0.65rem; font-weight:800; color:${evt.decision_type.includes('SUCCESS') ? '#4ade80' : '#8b5cf6'}; text-transform:uppercase;">${evt.decision_type.replace('CATALYST_', '')}</span>
                                <span style="font-size:0.6rem; opacity:0.5;">${new Date(evt.created_at).toLocaleTimeString()}</span>
                            </div>
                            <div class="audit-details-grid" style="display:flex; flex-direction:column; gap:8px;">
                                ${structuredHTML}
                            </div>
                        </div>
                    `;
                }).join('');
            } else {
                container.innerHTML = `<div class="empty-evidence">El payload de la traza no está disponible o ha sido rotado por políticas de retención.</div>`;
            }
        } catch (err) {
            document.getElementById('trace-payload').innerHTML = `<div class="empty-evidence">Error en enlace profundo: No se pudo contactar con el Ledger de Gobernanza.</div>`;
        }
    }
}

window.wisdomAtlas = new WisdomAtlas();
