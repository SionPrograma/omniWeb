class RoadmapUI {
    constructor() {
        this.container = null;
        this.roadmapData = null;
        this.currentScenario = 'CURRENT';
        this.activeBranchId = 'main';
        this.branches = [];
    }

    renderInto(container, data) {
        this.container = container;
        this.roadmapData = data;
        this.render();
    }

    async refresh() {
        if (!this.container) return;
        try {
            const res = await fetch(`/api/v1/roadmap/macro?branch_id=${this.activeBranchId}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.roadmapData = await res.json();
            this.render();
        } catch (err) {
            console.warn("Roadmap fallback fetch failed. Waiting for pulse.");
        }
    }

    render() {
        if (!this.container || !this.roadmapData) return;

        const { groups, global_bottlenecks, active_dominance } = this.roadmapData;

        let html = `
            <div class="roadmap-dashboard animate-slide-in">
                <div class="roadmap-header">
                    <div class="roadmap-branding">COGNITIVE ROADMAP v1.0</div>
                    <div class="roadmap-summary-row">
                        <div class="roadmap-stat">
                            <span class="label">DOMINIOS ACTIVOS:</span>
                            <span class="value">${active_dominance.join(', ').toUpperCase() || 'NINGUNO'}</span>
                        </div>
                        <div class="roadmap-stat">
                            <span class="label">BOTELLAS CRÍTICAS:</span>
                            <span class="value" style="color: ${global_bottlenecks.length > 0 ? '#ff4444' : '#32ff96'}">${global_bottlenecks.length}</span>
                        </div>
                    </div>
                </div>

                <div id="synergy-insights-container"></div>
                <div id="tactical-opportunities-container"></div>
                <div id="debt-cockpit-container"></div>
                <div id="sync-audit-container"></div>
                <div id="vision-conflicts-container"></div>
                <div id="roadmap-branch-hud"></div>
                <div id="strategic-sim-hud"></div>

                <div class="roadmap-grid">
                    ${groups.map(g => this.renderGroupCard(g)).join('')}
                </div>
            </div>
        `;

        this.container.innerHTML = html;
        this.container.scrollTop = 0;
        this.checkSynergies();
        this.checkOpportunities();
        this.checkSyncAudit();
        this.checkVisionConflicts();
        this.checkPersonas();
        this.checkSimulations();
        this.checkBranches();
        this.checkDebtCockpit();
    }

    async checkSyncAudit() {
        try {
            const res = await fetch('/api/v1/roadmap/sync/audit', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.syncRelations = await res.json();
            this.renderSyncRelations();
        } catch (err) {
            console.warn("Sync audit failed", err);
        }
    }

    renderSyncRelations() {
        const container = document.getElementById('sync-audit-container');
        if (!container || !this.syncRelations || this.syncRelations.length === 0) return;

        container.innerHTML = `
            <div class="sync-audit-panel animate-fade-in">
                <div class="sync-header">
                    <span class="sync-icon">🔗</span>
                    <span class="sync-title">CROSS-DOMAIN DEPENDENCIES (${this.syncRelations.length})</span>
                </div>
                <div class="sync-grid">
                    ${this.syncRelations.map(rel => `
                        <div class="sync-rel-card sev-${rel.severity}">
                            <div class="rel-domains">${rel.domain_a.toUpperCase()} ⟷ ${rel.domain_b.toUpperCase()}</div>
                            <div class="rel-type">${rel.relation_type.replace('_', ' ')}</div>
                            <div class="rel-rationale">${rel.evidence_summary}</div>
                            <div class="rel-suggested">${rel.suggested_action}</div>
                            <div class="rel-footer">
                                <button class="sync-btn" onclick="window.roadmapUI.suggestSyncMission('${rel.relation_id}')">PLANIFICAR SINCRONIZACIÓN</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    async suggestSyncMission(relationId) {
        try {
            const res = await fetch(`/api/v1/roadmap/sync/${relationId}/suggest`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            if (res.ok) {
                const mission = await res.json();
                const alert = document.createElement('div');
                alert.className = 'authority-success-alert';
                alert.innerText = `Misión de sincronización inyectada.`;
                document.body.appendChild(alert);
                setTimeout(() => alert.remove(), 3000);
            }
        } catch (err) {
            console.error("Sync suggestion failed", err);
        }
    }

    async checkOpportunities() {
        try {
            const res = await fetch('/api/v1/roadmap/opportunities/scan', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.opportunities = await res.json();
            this.renderOpportunities();
        } catch (err) {
            console.warn("Opportunity scan failed", err);
        }
    }

    renderOpportunities() {
        const container = document.getElementById('tactical-opportunities-container');
        if (!container || !this.opportunities || this.opportunities.length === 0) return;

        container.innerHTML = `
            <div class="opportunities-panel animate-fade-in">
                <div class="opportunities-header">
                    <span class="opp-icon">📡</span>
                    <span class="opp-title">TACTICAL OPPORTUNITIES (PREVENTIVE)</span>
                </div>
                <div class="opp-scroll">
                    ${this.opportunities.map(opp => `
                        <div class="opp-card type-${opp.type.toLowerCase()}">
                            <div class="opp-main">
                                <div class="opp-type-label">${opp.type.replace('_', ' ')}: ${opp.surface.toUpperCase()}</div>
                                <div class="opp-rationale">${opp.rationale}</div>
                                <div class="opp-evidence">${opp.evidence_summary}</div>
                            </div>
                            <div class="opp-action">
                                <button class="opp-btn" onclick="window.roadmapUI.convertOpportunity('${opp.opportunity_id}')">CONVERTIR A MISIÓN</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    async convertOpportunity(oppId) {
        const opp = this.opportunities.find(o => o.opportunity_id === oppId);
        if (!opp) return;

        try {
            const res = await fetch(`/api/v1/roadmap/opportunities/${oppId}/convert`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });

            if (res.ok) {
                // Remove from local list
                this.opportunities = this.opportunities.filter(o => o.opportunity_id !== oppId);
                this.renderOpportunities();

                // Show floating confirm
                const alert = document.createElement('div');
                alert.className = 'authority-success-alert';
                alert.innerText = `Misión sugerida inyectada: ${opp.suggested_mission.objective.slice(0, 30)}...`;
                document.body.appendChild(alert);
                setTimeout(() => alert.remove(), 3000);
            }
        } catch (err) {
            console.error("Failed to convert opportunity", err);
        }
    }

    async checkSynergies() {
        try {
            const res = await fetch('/api/v1/roadmap/synergy/analyze', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.synergyInsights = await res.json();
            this.renderSynergySection();
        } catch (err) {
            console.warn("Synergy analysis failed", err);
        }
    }

    renderSynergySection() {
        const container = document.getElementById('synergy-insights-container');
        if (!container || !this.synergyInsights || this.synergyInsights.length === 0) return;

        container.innerHTML = `
            <div class="synergy-insights-panel animate-fade-in">
                <div class="synergy-header">
                    <span class="synergy-icon">✨</span>
                    <span class="synergy-title">OPERATIONAL SYNERGY & REDUNDANCY ALERTS (${this.synergyInsights.length})</span>
                </div>
                <div class="synergy-list">
                    ${this.synergyInsights.map(insight => `
                        <div class="synergy-item relation-${insight.relation_type.toLowerCase()}">
                            <div class="insight-main">
                                <div class="insight-label">${insight.relation_type.replace('_', ' ')}: [${insight.handoff_a.slice(0, 6)}] ↔ [${insight.handoff_b.slice(0, 6)}]</div>
                                <div class="insight-rationale">${insight.rationale}</div>
                                ${insight.keep_separate_reason ? `<div class="insight-warn">BLOQUEO TÁCTICO: ${insight.keep_separate_reason}</div>` : ''}
                            </div>
                            <div class="insight-actions">
                                ${insight.suggested_action === 'MERGE' ?
                `<button class="synergy-btn preview" onclick="window.roadmapUI.previewMerge('${insight.insight_id}')">PREVIEW MERGE</button>` :
                (insight.suggested_action !== 'KEEP_SEPARATE' ? `<button class="synergy-btn apply" onclick="window.roadmapUI.applySynergy('${insight.insight_id}')">${insight.suggested_action.replace('_', ' ')}</button>` : '')
            }
                                <button class="synergy-btn dismiss" onclick="this.closest('.synergy-item').remove()">IGNORAR</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    previewMerge(insightId) {
        const insight = this.synergyInsights.find(i => i.insight_id === insightId);
        if (!insight || !insight.composite_preview) return;

        const modal = document.createElement('div');
        modal.className = 'roadmap-preview-modal merge-preview-overlay animate-fade-in';
        modal.id = 'merge-preview-modal';

        modal.innerHTML = `
            <div class="preview-content merge-layout">
                <div class="preview-header">
                    <h2>PROPUESTA DE FUSIÓN TÁCTICA</h2>
                    <div class="risk-pill ${insight.composite_preview.risk_level}">${insight.composite_preview.risk_level.toUpperCase()}</div>
                </div>

                <div class="merge-compare">
                    <div class="source-item">
                        <div class="item-label">MISIÓN A [${insight.handoff_a.slice(0, 6)}]</div>
                        <div class="item-id-long">${insight.handoff_a}</div>
                    </div>
                    <div class="merge-arrow">→</div>
                    <div class="source-item">
                        <div class="item-label">MISIÓN B [${insight.handoff_b.slice(0, 6)}]</div>
                        <div class="item-id-long">${insight.handoff_b}</div>
                    </div>
                </div>

                <div class="composite-details">
                    <div class="section-title">NUEVO OBJETIVO CONSOLIDADO</div>
                    <div class="composite-objective">${insight.composite_preview.objective.replace(/\n\n/g, '<br><br>')}</div>
                    
                    <div class="section-title">SUPERFICIE COMBINADA</div>
                    <div class="composite-meta">${insight.composite_preview.surface_affected.join(', ')}</div>
                </div>

                <div class="preview-footer">
                    <button class="preview-btn" onclick="document.getElementById('merge-preview-modal').remove()">CANCELAR</button>
                    <button class="preview-btn action-push" onclick="window.roadmapUI.applySynergy('${insightId}')">CONFIRMAR FUSIÓN ATÓMICA</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    async applySynergy(insightId) {
        const insight = this.synergyInsights.find(i => i.insight_id === insightId);
        if (!insight) return;

        try {
            await fetch('/api/v1/roadmap/synergy/apply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify(insight)
            });

            const modal = document.getElementById('merge-preview-modal');
            if (modal) modal.remove();

            this.refresh();
        } catch (err) {
            console.error("Failed to apply synergy", err);
        }
    }

    renderGroupCard(g) {
        const healthClass = `health-${g.health_signal.toLowerCase()}`;
        const readinessClass = `readiness-${g.readiness_state.toLowerCase().replace('_', '-')}`;

        // Audit missions of this group asynchronously
        this.auditGroup(g.group_id);

        return `
            <div class="roadmap-group-card ${healthClass} ${readinessClass}" onclick="window.roadmapUI.inspectGroup('${g.group_id}')">
                <div class="group-header">
                    <div class="group-info">
                        <div class="group-title">${g.title}</div>
                        <div class="launch-readiness-badge">${g.readiness_state.replace('_', ' ')}</div>
                        <!-- In the actual implementation, we might want to iterate over missions in the group 
                             but here we show the primary persona of the group/domain -->
                        <div class="persona-tag role-${(g.primary_persona || 'CREATOR_CORE').toLowerCase()}" style="font-size: 0.6rem; opacity: 0.8; margin-top: 4px;">
                            ${g.primary_persona || 'CREATOR_CORE'}
                        </div>
                    </div>
                    <div id="badge-${g.group_id}" class="constitution-badge">AUDITING...</div>
                </div>

                <div class="readiness-confidence-track">
                    <div class="confidence-fill" style="width: ${g.readiness_score * 100}%"></div>
                </div>

                <div class="group-metrics" style="margin: 15px 0;">
                    <div class="metric-pill active"><span>ACT:</span> ${g.active_count}</div>
                    <div class="metric-pill blocked" style="${g.blocked_count > 0 ? 'color:#ff4444; border-color:#ff4444' : ''}"><span>BLK:</span> ${g.blocked_count}</div>
                    <div class="metric-pill completed"><span>CMP:</span> ${g.completed_recent_count}</div>
                </div>

                <div id="fusion-${g.group_id}" class="fusion-context-container" style="margin-bottom: 12px; display:none;"></div>
                
                <div class="group-actions" style="margin-top: 15px; display: flex; gap: 8px;">
                    <button class="roadmap-mini-btn" onclick="window.roadmapUI.inspectGroup('${g.group_id}', '${g.primary_blocker_id || ''}')">
                        ${g.primary_blocker_id ? 'VER BLOQUEO' : 'INSPEC...'}
                    </button>
                    <button class="roadmap-mini-btn action-primary" onclick="window.roadmapUI.executeRecommended('${g.next_recommended_action}', '${g.group_id}')" style="background: rgba(212, 175, 55, 0.1); border-color: rgba(212, 175, 55, 0.4); color: var(--pizarron-accent);">
                        ${g.next_recommended_action.split(' ')[0].toUpperCase()}
                    </button>
                </div>
            </div>
        `;
    }

    inspectGroup(groupId, blockerId) {
        if (blockerId) {
            window.creatorEnv.openWorkspace('mission');
            if (window.pizarronUI) {
                setTimeout(() => window.pizarronUI.focusHandoff(blockerId), 300);
            }
        } else {
            window.creatorEnv.openWorkspace('mission');
        }
    }

    async executeRecommended(action, groupId) {
        if (action.includes("Empujar")) {
            await this.showPreview(groupId);
            return;
        }

        const surface = groupId.replace('surface_', '');
        if (action.includes("AUDIT CIERRES")) {
            window.omniShell.addInput(`AUDIT BACKLOG FORECLOSURE FOR ${surface}`);
        } else if (action.includes("GOBERNANZA") || action.includes("GATES")) {
            window.omniShell.addInput(`AUDIT LAUNCH READINESS FOR ${surface}`);
        } else {
            window.omniShell.addInput(`INSPECT DOMAIN ${surface}`);
        }
    }

    async showPreview(groupId) {
        try {
            const res = await fetch(`/api/v1/roadmap/preview/${groupId}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const plan = await res.json();
            this.renderPreview(plan);
        } catch (err) {
            console.error("Preview failed", err);
        }
    }

    async moveItem(groupId, id, direction) {
        if (!this.lastPlan) return;

        const items = this.lastPlan.items;
        const index = items.findIndex(i => i.handoff_id === id);
        if (index === -1) return;

        const newIndex = index + direction;
        if (newIndex < 0 || newIndex >= items.length) return;

        const [removed] = items.splice(index, 1);
        items.splice(newIndex, 0, removed);

        // Re-number indexes
        items.forEach((it, i) => it.sequence_index = i + 1);

        // Analyze Impact
        const order = items.map(it => it.handoff_id);
        try {
            const res = await fetch(`/api/v1/roadmap/schedule/${groupId}/reorder/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify(order)
            });
            const analysis = await res.json();
            this.renderPreview(this.lastPlan, analysis);
        } catch (err) {
            console.error("Reorder analysis failed", err);
            this.renderPreview(this.lastPlan);
        }
    }

    async applyReorder(groupId) {
        if (!this.lastPlan) return;
        const order = this.lastPlan.items.map(it => it.handoff_id);
        try {
            await fetch(`/api/v1/roadmap/schedule/${groupId}/reorder/apply`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify(order)
            });
            // Clear and refresh
            let modal = document.getElementById('rebase-preview-modal');
            if (modal) modal.remove();
            this.adjustPlan(groupId);
        } catch (err) {
            console.error("Apply reorder failed", err);
        }
    }

    resetReorder(groupId) {
        let modal = document.getElementById('rebase-preview-modal');
        if (modal) modal.remove();
        this.adjustPlan(groupId);
    }

    renderPreview(plan, analysis = null) {
        this.lastPlan = plan;
        let modal = document.getElementById('rebase-preview-modal');
        if (!modal) {
            modal = document.createElement('div');
            modal.className = 'roadmap-preview-modal animate-fade-in';
            modal.id = 'rebase-preview-modal';
            document.body.appendChild(modal);
        }

        const feasibilityClass = plan.atomic_feasibility > 0.8 ? 'safe' : (plan.atomic_feasibility > 0.4 ? 'warn' : 'critical');

        const analysisHtml = analysis ? `
            <div class="reorder-impact-panel ${analysis.risk_impact}">
                <div class="impact-title">IMPACTO DEL REORDENADO: ${analysis.risk_impact.toUpperCase()}</div>
                <div class="impact-details">
                    ${analysis.newly_ready_ids.length > 0 ? `<span>✅ ${analysis.newly_ready_ids.length} LISTAS</span>` : ''}
                    ${analysis.newly_blocked_ids.length > 0 ? `<span>❌ ${analysis.newly_blocked_ids.length} BLOQUEADAS</span>` : ''}
                    ${analysis.rebase_pressure_delta !== 0 ? `<span>📦 REBASE Δ: ${analysis.rebase_pressure_delta > 0 ? '+' : ''}${analysis.rebase_pressure_delta}</span>` : ''}
                    ${analysis.broken_dependencies.length > 0 ? `<div class="impact-warn">VIOLACIONES: ${analysis.broken_dependencies.length}</div>` : ''}
                </div>
            </div>
        ` : '';

        modal.innerHTML = `
            <div class="preview-content">
                <div class="preview-header">
                    <div class="title-row">
                        <h2>PLAN ATÓMICO: ${plan.domain_name.toUpperCase()}</h2>
                        <div class="feasibility-badge ${feasibilityClass}">FEASIBILITY: ${(plan.atomic_feasibility * 100).toFixed(0)}%</div>
                    </div>
                    <div class="risk-info">${plan.risk_summary}</div>
                </div>

                ${analysisHtml}

                <div class="preview-sequence">
                    <div class="section-title">SECUENCIA DE REBASE Y EMPUJE</div>
                    ${plan.items.map(item => {
            const isNewlyBlocked = analysis?.newly_blocked_ids.includes(item.handoff_id);
            const isNewlyReady = analysis?.newly_ready_ids.includes(item.handoff_id);
            return `
                        <div class="preview-item ${item.rebase_needed ? 'needs-rebase' : ''} ${(item.governance_blocks.length > 0 || isNewlyBlocked) ? 'blocked' : ''} ${isNewlyReady ? 'newly-ready' : ''}">
                            <div class="item-index">#${item.sequence_index}</div>
                            <div class="item-main">
                                <div class="item-title">${item.title}</div>
                                <div class="item-meta">
                                    <span class="risk-pill ${item.risk}">${item.risk.toUpperCase()}</span>
                                    ${item.rebase_needed ? '<span class="status-pill rebase">REBASE REQUIRED</span>' : ''}
                                    ${item.governance_blocks.map(b => `<span class="status-pill block">${b}</span>`).join('')}
                                    ${isNewlyBlocked ? '<span class="status-pill block">BLOCKED BY REORDER</span>' : ''}
                                    ${isNewlyReady ? '<span class="status-pill safe">READY BY REORDER</span>' : ''}
                                </div>
                            </div>
                            <div class="item-actions">
                                <button class="preview-micro-btn" onclick="window.roadmapUI.moveItem('${plan.group_id}', '${item.handoff_id}', -1)">↑</button>
                                <button class="preview-micro-btn" onclick="window.roadmapUI.moveItem('${plan.group_id}', '${item.handoff_id}', 1)">↓</button>
                                <button class="preview-micro-btn" onclick="window.roadmapUI.inspectItem('${item.handoff_id}')">DETALLE</button>
                            </div>
                        </div>
                    `}).join('')}
                </div>

                <div class="preview-footer">
                    <button class="preview-btn" onclick="window.roadmapUI.resetReorder('${plan.group_id}')">${analysis ? 'REVERTIR CAMBIOS' : 'CANCELAR'}</button>
                    ${analysis ? `
                        <button class="preview-btn action-push" onclick="window.roadmapUI.applyReorder('${plan.group_id}')">APLICAR Y GUARDAR</button>
                    ` : `
                        ${plan.atomic_feasibility > 0.8 ? `
                            <button class="preview-btn action-push" onclick="window.roadmapUI.confirmPush('${plan.group_id}')">CONFIRMAR EMPUJE ATÓMICO</button>
                        ` : `
                            <button class="preview-btn action-warn" onclick="window.roadmapUI.adjustPlan('${plan.group_id}')">AJUSTAR PLAN TÁCTICO</button>
                        `}
                    `}
                </div>
            </div>
        `;
    }

    inspectItem(id) {
        document.getElementById('rebase-preview-modal').remove();
        if (window.pizarronUI) {
            window.creatorEnv.openWorkspace('mission');
            setTimeout(() => window.pizarronUI.focusHandoff(id), 300);
        }
    }

    async confirmPush(groupId) {
        document.getElementById('rebase-preview-modal').remove();
        try {
            const res = await fetch(`/api/v1/roadmap/push/start/${groupId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const session = await res.json();
            this.currentPush = session;
            this.renderPushProgress();
            this.autoStep();
        } catch (err) {
            console.error("Push failed to start", err);
        }
    }

    renderPushProgress() {
        let overlay = document.getElementById('push-progress-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'roadmap-preview-modal push-execution';
            overlay.id = 'push-progress-overlay';
            document.body.appendChild(overlay);
        }

        const session = this.currentPush;
        const progress = ((session.current_step_index) / session.steps.length * 100).toFixed(0);

        overlay.innerHTML = `
            <div class="preview-content execution-card">
                <div class="preview-header">
                    <h2>EJECUCIÓN ATÓMICA: ${session.domain_name.toUpperCase()}</h2>
                    <div class="push-status-badge ${session.state.toLowerCase()}">${session.state}</div>
                </div>

                <div class="progress-bar-container">
                    <div class="progress-fill" style="width: ${progress}%"></div>
                    <div class="progress-text">${progress}% COMPLETADO</div>
                </div>

                <div class="execution-steps">
                    ${session.steps.map((step, idx) => `
                        <div class="exec-step ${idx === session.current_step_index ? 'active' : ''} ${step.status.toLowerCase()}">
                            <div class="step-icon">${this.getStepIcon(step.status)}</div>
                            <div class="step-info">
                                <span class="step-type">${step.type}</span>
                                <span class="step-id">${step.handoff_id.slice(0, 6)}</span>
                                ${step.error ? `<div class="step-error">${step.error}</div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>

                ${session.state === 'BLOCKED' ? `
                    <div class="blocked-alert ${session.is_resolvable ? 'resolvable' : ''}">
                        <div class="alert-title">⛔ BLOQUEO DE GOBERNANZA</div>
                        <div class="alert-reason">${session.blocking_reason}</div>
                        <div class="alert-req">REQ: ${session.authority_required}</div>
                        
                        ${session.is_resolvable ? `
                            <div class="authority-injection-box">
                                <input type="password" id="push-pin-input" placeholder="PIN de Creador" maxlength="4">
                                <button class="preview-btn action-push" onclick="window.roadmapUI.submitPushPIN('${session.push_id}')">INYECTAR AUTORIDAD</button>
                            </div>
                        ` : `
                            <button class="preview-btn action-warn" onclick="window.roadmapUI.inspectItem('${session.steps[session.current_step_index].handoff_id}')">RESOLVER EN TABLERO</button>
                        `}
                    </div>
                ` : ''}

                <div class="preview-footer">
                    <button class="preview-btn" onclick="window.roadmapUI.abortPushSession()">ABORTAR PUSH</button>
                    <button class="preview-btn" onclick="window.roadmapUI.fetchForensics('${session.push_id}')">VER FORENSICS</button>
                    ${session.state === 'COMPLETED' ? `
                        <button class="preview-btn action-warn" onclick="window.roadmapUI.solicitarRollback('${session.push_id}')">SOLICITAR ROLLBACK</button>
                        <button class="preview-btn action-push" onclick="document.getElementById('push-progress-overlay').remove()">CERRAR HUD</button>
                    ` : ''}
                </div>
            </div>
        `;
    }

    async solicitarRollback(pushId) {
        try {
            const res = await fetch(`/api/v1/roadmap/push/${pushId}/rollback/preview`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.currentRollback = await res.json();
            this.renderRollbackPreview();
        } catch (err) {
            console.error("Rollback preview failed", err);
        }
    }

    renderRollbackPreview() {
        const rb = this.currentRollback;
        const modal = document.getElementById('push-progress-overlay');
        const card = modal.querySelector('.push-progress-card');

        card.innerHTML = `
            <div class="preview-header">
                <div class="preview-title">PREVIEW DE ROLLBACK</div>
                <div class="preview-domain">ID PUSH: ${rb.push_id.slice(0, 8)}...</div>
            </div>
            <div class="preview-body">
                <p class="rollback-risk ${rb.steps.some(s => !s.revertible) ? 'risk-high' : ''}">
                    ESTADOS A REVERTIR: ${rb.steps.length}
                </p>
                <div class="steps-list">
                    ${rb.steps.map((s, i) => `
                        <div class="push-step ${s.status}">
                            <div class="step-icon">${s.revertible ? '♻️' : '⚠️'}</div>
                            <div class="step-info">
                                <div class="step-label">${s.original_step_type} -> UNDO</div>
                                <div class="step-target">MISS: ${s.handoff_id.slice(0, 6)}...</div>
                                ${!s.revertible ? `<div class="step-error">${s.reason_not_revertible}</div>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="preview-footer">
                <button class="preview-btn" onclick="document.getElementById('push-progress-overlay').remove()">CANCELAR</button>
                <button class="preview-btn action-push" onclick="window.roadmapUI.startRollback()">CONFIRMAR REVERSIÓN</button>
            </div>
        `;
    }

    async startRollback() {
        const rb = this.currentRollback;
        try {
            const res = await fetch(`/api/v1/roadmap/rollback/${rb.rollback_id}/start`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.currentRollback = await res.json();
            this.renderRollbackProgress();
            this.autoRollbackStep();
        } catch (err) {
            console.error("Start rollback failed", err);
        }
    }

    renderRollbackProgress() {
        const rb = this.currentRollback;
        const modal = document.getElementById('push-progress-overlay');
        const card = modal.querySelector('.push-progress-card');

        card.innerHTML = `
            <div class="preview-header">
                <div class="preview-title">EJECUTANDO ROLLBACK</div>
                <div class="preview-status status-${rb.state}">${rb.state}</div>
            </div>
            <div class="preview-body">
                <div class="steps-list">
                    ${rb.steps.map((s, i) => `
                        <div class="push-step ${s.status} ${i === rb.current_step_index ? 'current' : ''}">
                            <div class="step-icon">${this.getStepIcon(s.status)}</div>
                            <div class="step-info">
                                <div class="step-label">REVERTIENDO: ${s.original_step_type}</div>
                                <div class="step-target">${s.handoff_id}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
            <div class="preview-footer">
                ${rb.state === 'COMPLETED' ? `
                    <button class="preview-btn action-push" onclick="document.getElementById('push-progress-overlay').remove()">FINALIZAR</button>
                ` : `
                    <div class="step-loader small"></div>
                `}
            </div>
        `;
    }

    async autoRollbackStep() {
        if (!this.currentRollback || this.currentRollback.state !== 'RUNNING') return;

        try {
            const res = await fetch(`/api/v1/roadmap/rollback/${this.currentRollback.rollback_id}/next`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.currentRollback = await res.json();
            this.renderRollbackProgress();

            if (this.currentRollback.state === 'RUNNING') {
                setTimeout(() => this.autoRollbackStep(), 1000);
            }
        } catch (err) {
            console.error("Rollback step failed", err);
        }
    }

    async fetchForensics(pushId) {
        try {
            const res = await fetch(`/api/v1/roadmap/push/${pushId}/forensics`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            console.table(data);
            alert(`Atomic Push Forensics: ${data.length} eventos registrados.`);
        } catch (err) {
            console.error("Forensics fetch failed", err);
        }
    }

    getStepIcon(status) {
        if (status === 'COMPLETED') return '✅';
        if (status === 'RUNNING') return '<span class="spinner">⚙️</span>';
        if (status === 'FAILED') return '❌';
        if (status === 'BLOCKED') return '⛔';
        return '⚪';
    }

    async autoStep() {
        if (this.currentPush && (this.currentPush.state === 'RUNNING' || this.currentPush.state === 'READY')) {
            // Optional: add a small delay for visibility
            setTimeout(() => this.manualNextStep(), 1000);
        }
    }

    async manualNextStep() {
        if (!this.currentPush) return;
        try {
            const res = await fetch(`/api/v1/roadmap/push/${this.currentPush.push_id}/next`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.currentPush = await res.json();
            this.renderPushProgress();
            if (this.currentPush.state === 'RUNNING') this.autoStep();
        } catch (err) {
            console.error("Step execution failed", err);
        }
    }

    async submitPushPIN(pushId) {
        const pin = document.getElementById('push-pin-input').value;
        if (!pin) return;

        try {
            const res = await fetch(`/api/v1/roadmap/push/${pushId}/authority`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify({ pin })
            });

            if (res.ok) {
                this.currentPush = await res.json();
                this.renderPushProgress();
                if (this.currentPush.state === 'RUNNING') this.autoStep();
            } else {
                const err = await res.json();
                alert(`Error de Autoridad: ${err.detail}`);
            }
        } catch (err) {
            console.error("PIN injection failed", err);
        }
    }

    async abortPushSession() {
        if (!this.currentPush) return;
        await fetch(`/api/v1/roadmap/push/${this.currentPush.push_id}/abort`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
        });
        document.getElementById('push-progress-overlay').remove();
        this.currentPush = null;
    }

    inspectItem(handoffId) {
        if (window.creatorEnv) {
            window.creatorEnv.openWorkspace('mission');
            // Small delay to ensure workspace is ready
            setTimeout(() => {
                const e = new CustomEvent('inspect-mission', { detail: { id: handoffId } });
                window.dispatchEvent(e);
            }, 300);
        }
    }

    async auditGroup(groupId) {
        try {
            const res = await fetch(`/api/v1/roadmap/groups/${groupId}/missions`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const missions = await res.json();
            if (missions.length > 0) {
                const auditRes = await fetch(`/api/v1/handoffs/${missions[0].handoff_id}/audit`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
                });
                const report = await auditRes.json();
                this.renderAuditBadge(groupId, report, missions[0].handoff_id);
            } else {
                this.renderAuditBadge(groupId, { status: "COMPLIANT" });
            }
        } catch (e) { console.error(e); }
    }

    renderAuditBadge(groupId, report, missionId = null) {
        const badge = document.getElementById(`badge-${groupId}`);
        if (!badge) return;
        badge.className = `constitution-badge status-${report.status.toLowerCase()}`;
        badge.innerText = report.status;
        badge.onclick = (e) => {
            e.stopPropagation();
            this.showAuditDetails(report, missionId);
        }
    }

    showAuditDetails(report, missionId) {
        const modal = document.createElement('div');
        modal.className = 'roadmap-preview-modal constitutional-status-overlay animate-fade-in';
        modal.id = 'audit-modal';
        modal.innerHTML = `
            <div class="preview-content">
                <div class="preview-header">
                    <h2>REPORTE DE INTEGRIDAD CONSTITUCIONAL</h2>
                    <div class="status-pill ${report.status.toLowerCase()}">${report.status}</div>
                </div>
                <div class="audit-summary-box">${report.summary}</div>
                <div class="violations-list">
                    ${report.violations.map(v => `
                        <div class="violation-card sev-${v.severity.toLowerCase()}">
                            <div class="v-header">${v.rule_name} [${v.severity}]</div>
                            <div class="v-msg">${v.message}</div>
                            <div class="v-fix">SUGERENCIA: ${v.suggested_fix}</div>
                            ${v.rule_id === 'BRAND_INTEGRITY' ?
                `<button class="fix-btn" onclick="window.roadmapUI.fixBranding('${missionId}')">AUTO-CORREGIR BRANDING</button>` : ''}
                        </div>
                    `).join('')}
                </div>
                <div class="preview-footer">
                    <button class="preview-btn" onclick="document.getElementById('audit-modal').remove()">CERRAR</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    async fixBranding(missionId) {
        try {
            await fetch(`/api/v1/handoffs/${missionId}/fix_branding`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            document.getElementById('audit-modal').remove();
            this.refresh();
        } catch (e) { console.error(e) }
    }

    async checkVisionConflicts() {
        try {
            const res = await fetch('/api/v1/personas/conflicts', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.conflicts = await res.json();
            this.renderVisionConflicts();
        } catch (e) { console.warn(e) }
    }

    async checkPersonas() {
        try {
            const res = await fetch('/api/v1/personas', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.personas = await res.json();
        } catch (e) { console.warn(e) }
    }

    renderVisionConflicts() {
        const container = document.getElementById('vision-conflicts-container');
        if (!container || !this.conflicts || this.conflicts.length === 0) {
            if (container) container.innerHTML = '';
            return;
        }

        container.innerHTML = `
            <div class="vision-conflicts-panel animate-fade-in">
                <div class="conflicts-header">
                    <span class="conf-icon">🎭</span>
                    <span class="conf-title">VISION CONFLICTS & COLLISION MONITOR (${this.conflicts.length})</span>
                </div>
                <div class="conf-list">
                    ${this.conflicts.map(c => `
                        <div class="conflict-item type-${c.type.toLowerCase()}">
                            <div class="conflict-main">
                                <div class="conflict-label">${c.type.replace('_', ' ')}</div>
                                <div class="conflict-desc">${c.description}</div>
                                <div class="conflict-involved">
                                    ${c.personas.map(p => `<span class="persona-tag role-${p.toLowerCase()}">${p}</span>`).join('')}
                                </div>
                            </div>
                            <div class="conflict-actions">
                                <button class="arbitrate-btn" onclick="window.roadmapUI.arbitrateConflict('${c.conflict_id}')">ARBITRAJE CONSTITUCIONAL</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    async arbitrateConflict(cid) {
        try {
            const res = await fetch(`/api/v1/personas/conflicts/${cid}/arbitrate`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const resolution = await res.json();

            // Show result as a floating alert
            const alertBox = document.createElement('div');
            alertBox.className = 'authority-success-alert';
            alertBox.style.background = 'rgba(15, 10, 25, 0.95)';
            alertBox.style.borderColor = 'var(--pizarron-accent)';
            alertBox.innerHTML = `
                <div style="font-weight:bold; color:var(--pizarron-accent); margin-bottom:5px;">${resolution.winner} PREVALECE</div>
                <div style="font-size:0.8rem;">${resolution.rationale}</div>
            `;
            document.body.appendChild(alertBox);
            setTimeout(() => alertBox.remove(), 5000);

            this.refresh();
        } catch (e) { console.error(e) }
    }

    async checkSimulations() {
        try {
            const res = await fetch(`/api/v1/roadmap/simulate?branch_id=${this.activeBranchId}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.simulations = await res.json();
            this.renderSimulationHUD();
        } catch (e) { console.warn("Simulations fetch failed", e); }
    }

    async revertCompensation(branchId, missionId) {
        if (!confirm("¿Estás seguro de REVERTIR esta misión compensatoria? Se eliminará de la rama y se re-auditará el merge gate.")) return;

        try {
            const resp = await fetch(`/api/v1/roadmap/branches/${branchId}/compensations/${missionId}/revert`, { method: 'POST' });
            const data = await resp.json();
            if (data.status === 'success') {
                window.pizarron.showNotification("Misión revertida con éxito.", "success");
                this.closeDiffModal();
                this.refreshBranches();
            } else {
                throw new Error(data.message);
            }
        } catch (err) {
            window.pizarron.showNotification("Error al revertir: " + err.message, "error");
        }
    }

    async refreshBranches() {
        try {
            const res = await fetch('/api/v1/roadmap/branches', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.branches = await res.json();
            this.renderBranchHUD();
        } catch (e) { console.warn("Branches fetch failed", e); }
    }

    async checkBranches() {
        try {
            const res = await fetch('/api/v1/roadmap/branches', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.branches = await res.json();
            this.renderBranchHUD();
        } catch (e) { console.warn("Branches fetch failed", e); }
    }

    async viewStrategicDashboard() {
        const modal = document.createElement('div');
        modal.id = 'strategic-dashboard-modal';
        modal.className = 'omni-modal strategic-dashboard';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>CABINA ESTRATÉGICA DE RAMAS TÁCTICAS</h2>
                    <div class="header-actions">
                        <button class="btn-exceptions-report" onclick="window.roadmapUI.viewExceptionsReport()">⚖️ REPORTE DE EXCEPCIONES</button>
                        <button class="close-btn" onclick="document.getElementById('strategic-dashboard-modal').remove()">×</button>
                    </div>
                </div>
                <div id="strat-dashboard-body" class="modal-body loading">
                    <div class="omni-loader"></div>
                    <p>Sincronizando señales tácticas de todas las ramas...</p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        try {
            const resp = await fetch('/api/v1/roadmap/strategic-dashboard');
            const data = await resp.json();
            this.renderStrategicDashboard(data);

            // PHASE 106 & 107 & 108: ROI Layers
            this.fetchInvestmentAudits();
            this.fetchPredictiveROIs();
            this.fetchAlternativePaths();

            // PHASE 110 & 111: Consensus & Feedback Loop
            this.fetchGovernanceConsensus();
            this.fetchGovernanceRecalibration();
        } catch (err) {
            document.getElementById('strat-dashboard-body').innerHTML = `<p class="error">Error: ${err.message}</p>`;
        }
    }

    renderStrategicDashboard(data) {
        const body = document.getElementById('strat-dashboard-body');
        body.classList.remove('loading');

        body.innerHTML = `
             <div class="strat-header-advice">
                <div class="advice-label">DIAGNÓSTICO GLOBAL:</div>
                <div class="advice-text">${data.focus_recommendation}</div>
            </div>

            <!-- CROSS-BRANCH SYNERGY LAYER (PHASE 104) -->
            <div class="cross-branch-analysis-section">
                <div class="section-title">🕵️ ANÁLISIS TRANSVERSAL DE RAMAS (SYNERGY & COLLISION)</div>
                <div id="cross-branch-synergy-list" class="cb-synergy-list loading-small">
                    <div class="omni-loader"></div>
                    <p>Comparando ramas en paralelo...</p>
                </div>
            </div>

            <!-- CONSOLIDATION LAYER (PHASE 105) -->
            <div id="consolidation-proposals-container" class="consolidation-section animate-fade-in" style="display:none">
                <div class="section-title">💎 OPORTUNIDADES DE CONSOLIDACIÓN (REDUNDANCY RESOLUTION)</div>
                <div id="consolidation-list" class="cb-synergy-list"></div>
            </div>

            <!-- GOVERNANCE DECISION LEDGER (PHASE 109) -->
            <div class="ledger-section animate-fade-in">
                <div class="section-title">📜 LIBRO MAYOR DE DECISIONES ESTRATÉGICAS (GOVERNANCE LEDGER)</div>
                <div class="ledger-controls">
                    <select id="ledger-filter-type" onchange="window.roadmapUI.fetchGovernanceLedger()">
                        <option value="">Todas las Decisiones</option>
                        <option value="STRATEGIC_PIVOT">Pivots Estratégicos</option>
                        <option value="RISK_OVERRIDE">Overrides de Riesgo</option>
                        <option value="ALTERNATIVE_PATH_ACTION">Caminos Alternativos</option>
                        <option value="RELIEF_MISSION_DECISION">Intervenciones de Alivio</option>
                        <option value="CONSOLIDATION">Consolidaciones</option>
                    </select>
                </div>
            <div id="governance-ledger-list" class="ledger-list loading-small">
                    <div class="omni-loader"></div>
                </div>
            </div>

            <!-- GOVERNANCE CONSENSUS ADVISOR (PHASE 110) -->
            <div class="consensus-section animate-slide-up">
                <div class="section-title">🗳️ ASESOR DE CONSENSO Y CRITERIO (GOVERNANCE CONSENSUS)</div>
                <div class="consensus-intro">
                    <p>Análisis de patrones de decisión recurrentes y sugerencias de recalibración táctica.</p>
                </div>
                <div id="consensus-advisory-list" class="consensus-list loading-small">
                    <div class="omni-loader"></div>
                    <p>Auditando el Libro Mayor en busca de sesgos operativos...</p>
                </div>
            </div>

            <!-- GOVERNANCE RECALIBRATION LOOP (PHASE 111) -->
            <div class="recalibration-section animate-slide-up">
                <div class="section-title">⚙️ RETROALIMENTACIÓN Y RECALIBRACIÓN (GOVERNANCE FEEDBACK)</div>
                <div class="recalibration-grid">
                    <div class="recal-column">
                        <div class="column-title">PROPUESTAS DE RECALIBRACIÓN</div>
                        <div id="recalibration-proposals-list" class="recal-list loading-small">
                            <div class="omni-loader"></div>
                        </div>
                    </div>
                    <div class="recal-column">
                        <div class="column-title">PARÁMETROS ACTIVOS</div>
                        <div id="governance-parameters-list" class="param-list">
                            <div class="omni-loader"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- GOVERNANCE CONTEXTUAL MAPPING (PHASE 112) -->
            <div class="contextual-mapping-section animate-slide-up">
                <div class="section-title">🌐 MAPEADO CONTEXTUAL MULTI-PROYECTO (CONTEXTUAL DNA)</div>
                <div class="mapping-intro">
                    <p>OmniWeb detecta similitudes tácticas con otros proyectos para sugerir baselines de gobernanza y aprendizajes reutilizables.</p>
                </div>
                <div id="contextual-mappings-list" class="mapping-list loading-small">
                    <div class="omni-loader"></div>
                    <p>Buscando paralelos en el ecosistema de proyectos...</p>
                </div>
            </div>

            <!-- GOVERNANCE CROSS-PROJECT SEARCH (PHASE 113) -->
            <div class="cross-project-search-section animate-slide-up">
                <div class="section-title">🔍 BÚSQUEDA TRANSVERSAL DE APRENDIZAJES (CROSS-PROJECT)</div>
                <div class="search-controls">
                    <input type="text" id="cp-search-input" placeholder="Buscar por dominio, deuda o patrón táctico..." />
                    <button class="btn-search-cp" onclick="window.roadmapUI.triggerCPSearch()">BUSCAR EN OTROS PROYECTOS</button>
                </div>
                <div id="cross-project-results-list" class="cp-results-list">
                    <p class="intro-msg">Ingresa un contexto para buscar sabiduría reutilizable en el Atlas de OmniWeb.</p>
                </div>
            </div>

            <!-- ORACULAR ALIGNMENT (PHASE 401) -->
            <div class="oracular-alignment-section animate-slide-up">
                <div class="section-title">⚖️ ALINEACIÓN ORACULAR (SIMULACIÓN VS REALIDAD)</div>
                <div class="alignment-intro">
                    <p>OmniWeb cierra el loop táctico comparando las predicciones de sus simulaciones con los resultados reales de las autopsias de ramas.</p>
                </div>
                <div id="oracular-sync-list" class="sync-list loading-small">
                    <div class="omni-loader"></div>
                    <p>Contrastando predicciones con resultados forenses...</p>
                </div>
            </div>

            <div class="strat-grid">
                ${data.active_branches.map(b => `
                    <div class="strat-card ${b.status.toLowerCase()}">
                        <div class="sc-header">
                            <span class="sc-name">${b.name}</span>
                            <div id="roi-badge-${b.branch_id}" class="roi-badge-placeholder"></div>
                            <span class="sc-badge ${b.status.toLowerCase()}">${b.status.replace(/_/g, ' ')}</span>
                        </div>
                        <div class="sc-metrics">
                            <div class="metric">
                                <label>READINESS</label>
                                <div class="m-bar"><div class="m-fill" style="width: ${b.readiness * 100}%"></div></div>
                                <span>${Math.round(b.readiness * 100)}%</span>
                            </div>
                            <div class="metric">
                                <label>FRICCIÓN</label>
                                <div class="m-bar friction"><div class="m-fill" style="width: ${b.friction * 100}%"></div></div>
                                <span>${Math.round(b.friction * 100)}%</span>
                            </div>
                        </div>
                        <div class="sc-signals">
                            <div class="sig">DIFF: <strong>${Math.round(b.divergence * 100)}%</strong></div>
                            <div class="sig">AUDIT: <strong class="${b.constitutional_status.toLowerCase()}">${b.constitutional_status}</strong></div>
                            <div class="sig">COMP: <strong>${b.compensation_effect_summary}</strong></div>
                            <div class="sig">BLOCKERS: <strong class="${b.unresolved_blockers_count > 0 ? 'bad' : 'good'}">${b.unresolved_blockers_count}</strong></div>
                        </div>
                        <div class="sc-rec ${b.recommendation.toLowerCase()}">
                            <strong>RECOMENDACIÓN: ${b.recommendation}</strong>
                            <p>${b.rationale}</p>
                        </div>
                        
                        <!-- ROI SECTION (PHASE 106) -->
                        <div id="roi-report-${b.branch_id}" class="sc-roi-report visible-nominal"></div>
                        
                        <!-- PREDICTIVE ROI SECTION (PHASE 107) -->
                        <div id="predictive-roi-report-${b.branch_id}" class="sc-roi-report predictive animate-fade-in"></div>

                        <!-- ALTERNATIVE PATH SECTION (PHASE 108) -->
                        <div id="alternative-paths-report-${b.branch_id}" class="sc-roi-report alternative animate-fade-in"></div>

                        ${b.drift_alerts && b.drift_alerts.length > 0 ? `
                            <div class="sc-drift-alerts">
                                ${b.drift_alerts.map(d => `
                                    <div class="drift-alert ${d.severity.toLowerCase()}">
                                        <span class="drift-icon">⚠️</span>
                                        <div class="drift-content">
                                            <strong>DERIVA: ${d.drift_type} (${d.affected_domain})</strong>
                                            <p>${d.rationale}</p>
                                            <div class="drift-action">💡 Sugerencia: ${d.suggested_action}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        <div class="sc-actions">
                            ${b.recommendation === 'ESCALATE' ?
                `<button class="arbitrate-btn" onclick="window.roadmapUI.openArbitrationCockpit('${b.branch_id}')">ARBITRAR ESTRATEGIA</button>` :
                `<button onclick="window.roadmapUI.compareBranch('${b.branch_id}')">DETALLE / DIFF</button>`
            }
                            <button class="secondary" onclick="window.roadmapUI.discardBranch('${b.branch_id}')">DESCARTAR</button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Trigger synergy fetch after rendering main dashboard
        this.fetchCrossBranchSynergy();
        this.fetchConsolidationProposals();
        this.fetchInvestmentAudits();
        this.fetchPredictiveROIs();
        this.fetchAlternativePaths();
        this.fetchGovernanceLedger();
        this.fetchGovernanceConsensus();
    }

    async fetchCrossBranchSynergy() {
        const list = document.getElementById('cross-branch-synergy-list');
        try {
            const res = await fetch('/api/v1/governance/synergy/scan', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            this.renderCrossBranchSynergy(data.relations || []);
        } catch (e) {
            if (list) list.innerHTML = `<p class="error">Cross-branch analysis unavailable.</p>`;
        }
    }

    renderCrossBranchSynergy(relations) {
        const list = document.getElementById('cross-branch-synergy-list');
        if (!list) return;
        list.classList.remove('loading-small');

        if (relations.length === 0) {
            list.innerHTML = `<div class="cb-empty-state">No se detectaron colisiones o redundancias entre las ramas activas. El desarrollo paralelo es nominal.</div>`;
            return;
        }

        list.innerHTML = relations.map(r => `
            <div class="cb-relation-card rel-${r.relation_type.toLowerCase()} animate-fade-in">
                <div class="rel-header">
                    <span class="rel-type">${r.relation_type}</span>
                    <span class="rel-conf">${(r.confidence * 100).toFixed(0)}% Conf.</span>
                </div>
                <div class="rel-body">
                    <div class="rel-title">[${r.branch_a_id}] ↔ [${r.branch_b_id}]</div>
                    <div class="rel-rationale">${r.rationale}</div>
                    <div class="rel-domains">DOMINIOS: ${r.affected_domains.join(', ')}</div>
                </div>
                <div class="rel-footer">
                    <div class="rel-rec">💡 RECOMENDACIÓN: ${r.recommended_action}</div>
                    <div class="rel-actions">
                        <button class="rel-btn" onclick="window.roadmapUI.compareBranchPair('${r.branch_a_id}', '${r.branch_b_id}')">EXPLORAR CONFLICTO</button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async fetchConsolidationProposals() {
        try {
            const res = await fetch('/api/v1/governance/consolidation/proposals', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            this.renderConsolidationProposals(data.proposals || []);
        } catch (e) {
            console.warn("Consolidation proposals fetch failed", e);
        }
    }

    renderConsolidationProposals(proposals) {
        const container = document.getElementById('consolidation-proposals-container');
        const list = document.getElementById('consolidation-list');
        if (!container || !list) return;

        if (proposals.length === 0) {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'block';
        list.innerHTML = proposals.map(p => `
            <div class="cb-relation-card rel-synergy consolidation-card animate-slide-up">
                <div class="rel-header">
                    <span class="rel-type">PROPUESTA: ${p.consolidation_type}</span>
                    <span class="rel-conf">${(p.confidence * 100).toFixed(0)}% Match</span>
                </div>
                <div class="rel-body">
                    <div class="rel-title">[${p.secondary_branch_id}] → ABSORBER EN [${p.primary_branch_id}]</div>
                    <div class="rel-rationale">${p.rationale}</div>
                    <div class="rel-gain">✨ GANANCIA: ${p.expected_gain}</div>
                </div>
                <div class="rel-footer">
                    <div class="cons-actions">
                        <button class="cons-btn accept" onclick="window.roadmapUI.actOnConsolidation('${p.consolidation_id}', 'ACCEPT')">ACEPTAR</button>
                        <button class="cons-btn secondary" onclick="window.roadmapUI.actOnConsolidation('${p.consolidation_id}', 'POSTPONE')">POSPONER</button>
                        <button class="cons-btn secondary" onclick="window.roadmapUI.actOnConsolidation('${p.consolidation_id}', 'REJECT')">RECHAZAR</button>
                        <button class="cons-btn escalation" onclick="window.roadmapUI.actOnConsolidation('${p.consolidation_id}', 'ESCALATE')">⚖️ ESCALAR</button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async actOnConsolidation(consId, action) {
        try {
            const resp = await fetch('/api/v1/governance/consolidation/act', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify({ consolidation_id: consId, action })
            });
            const data = await resp.json();
            if (data.status === 'success') {
                window.pizarron.showNotification(`Acción '${action}' registrada.`, "success");
                this.fetchConsolidationProposals();
            }
        } catch (err) {
            window.pizarron.showNotification("Error: " + err.message, "error");
        }
    }

    async fetchInvestmentAudits() {
        try {
            // Trigger scan first
            await fetch('/api/v1/governance/investment/scan', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });

            const res = await fetch('/api/v1/governance/investment/audit', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            this.renderInvestmentAudits(data.audits || []);
        } catch (e) {
            console.warn("Investment audits fetch failed", e);
        }
    }

    renderInvestmentAudits(audits) {
        audits.forEach(audit => {
            const badge = document.getElementById(`roi-badge-${audit.branch_id}`);
            const report = document.getElementById(`roi-report-${audit.branch_id}`);
            if (badge) {
                const bandClass = audit.return_band.toLowerCase().replace(/_/g, '-');
                badge.className = `roi-badge band-${bandClass} animate-fade-in`;
                badge.innerHTML = `RETURN: ${audit.return_band.replace(/_/g, ' ')}`;
                badge.title = `Audit ID: ${audit.audit_id}\nCosto: ${audit.cost_score} | Valor: ${audit.value_score}`;
            }
            if (report) {
                report.innerHTML = `
                    <div class="roi-mini-grid">
                        <div class="roi-item">
                            <span class="label">COSTO TÁCTICO</span>
                            <span class="val">${Math.round(audit.cost_score)}</span>
                        </div>
                        <div class="roi-item">
                            <span class="label">VALOR ESTRUCTURAL</span>
                            <span class="val success">${Math.round(audit.value_score)}</span>
                        </div>
                    </div>
                    <div class="roi-rationale-box">
                        <strong>DIAGNÓSTICO ROI:</strong>
                        <p>${audit.rationale}</p>
                        <div class="roi-rec-text">💡 RECOMENDACIÓN: ${audit.recommendation}</div>
                    </div>
                `;
            }
        });
    }

    async fetchPredictiveROIs() {
        try {
            // Trigger projection scan
            const activeBranches = Array.from(document.querySelectorAll('.strat-card')).map(c => c.querySelector('.sc-actions button')?.onclick?.toString().match(/'(.+?)'/)[1]);
            for (const bid of activeBranches) {
                if (bid) await fetch(`/api/v1/governance/investment/predict/${bid}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
                });
            }

            const res = await fetch('/api/v1/governance/investment/predict/all', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            this.renderPredictiveROIs(data.payload || []);
        } catch (e) {
            console.warn("Predictive ROI fetch failed", e);
        }
    }

    renderPredictiveROIs(projections) {
        projections.forEach(pro => {
            const report = document.getElementById(`predictive-roi-report-${pro.branch_id}`);
            if (report) {
                const bandClass = pro.predicted_return_band.toLowerCase().replace(/_/g, '-');
                report.innerHTML = `
                    <div class="roi-predictive-header">
                        <span class="proi-label">🔮 PREDICTION: ${pro.predicted_return_band.replace(/_/g, ' ')}</span>
                        <div class="proi-confidence">
                            <label>CONFIDENCE</label>
                            <div class="proi-bar"><div class="proi-fill" style="width: ${pro.confidence * 100}%"></div></div>
                        </div>
                    </div>
                    <div class="roi-rationale-box predictive band-${bandClass}">
                        <p class="proi-rationale">${pro.rationale}</p>
                        <div class="proi-evidence">
                            <strong>EVIDENCIA HISTÓRICA:</strong>
                            <div class="evidence-links">
                                ${pro.supporting_evidence.branch_refs.length > 0 ? `<span class="e-tag">Branches: ${pro.supporting_evidence.branch_refs.length}</span>` : ''}
                                ${pro.supporting_evidence.learning_refs.length > 0 ? `<span class="e-tag">Learnings: ${pro.supporting_evidence.learning_refs.length}</span>` : ''}
                                <span class="e-outcome">Pattern Outcome: ${pro.supporting_evidence.historical_merged} MERGE / ${pro.supporting_evidence.historical_discarded} DISCARD</span>
                            </div>
                        </div>
                        <div class="proi-strategy">📍 ESTRATEGIA: <strong>${pro.recommended_strategy}</strong></div>
                    </div>
                `;
            }
        });
    }

    async fetchAlternativePaths() {
        try {
            const activeBranches = Array.from(document.querySelectorAll('.strat-card')).map(c => c.querySelector('.sc-actions button')?.onclick?.toString().match(/'(.+?)'/)[1]);
            for (const bid of activeBranches) {
                if (bid) await fetch(`/api/v1/governance/investment/suggest/${bid}`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
                });
            }

            const res = await fetch('/api/v1/governance/investment/suggest/all', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            this.renderAlternativePaths(data.payload || []);
        } catch (e) {
            console.warn("Alternative paths fetch failed", e);
        }
    }

    renderAlternativePaths(suggestions) {
        suggestions.forEach(sug => {
            const report = document.getElementById(`alternative-paths-report-${sug.branch_id}`);
            if (report) {
                const typeClass = sug.path_type.toLowerCase().replace(/_/g, '-');
                report.innerHTML = `
                    <div class="alt-path-card animate-fade-in">
                        <div class="alt-header">
                            <span class="alt-label">💡 GUIDANCE: ${sug.path_type.replace(/_/g, ' ')}</span>
                            <div class="alt-metrics">
                                <span class="alt-risk-badge">-${Math.round(sug.expected_risk_reduction * 100)}% RISK</span>
                            </div>
                        </div>
                        <div class="alt-content">
                            <strong>RECOMENDACIÓN:</strong>
                            <p>${sug.proposed_strategy}</p>
                            <div class="alt-rationale"><em>${sug.rationale}</em></div>
                            <div class="alt-evidence">
                                <label>EVIDENCIA:</label>
                                <span class="e-tag">Confianza: ${Math.round(sug.confidence * 100)}%</span>
                            </div>
                            <div class="alt-actions">
                                <button class="btn-alt-accept" onclick="window.roadmapUI.submitSuggestionAction('${sug.path_id}', 'ACCEPT')">ACEPTAR RUTA</button>
                                <button class="btn-alt-ignore" onclick="window.roadmapUI.submitSuggestionAction('${sug.path_id}', 'IGNORE')">IGNORAR</button>
                            </div>
                        </div>
                    </div>
                `;
            }
        });
    }

    async submitSuggestionAction(pathId, action) {
        try {
            const resp = await fetch('/api/v1/governance/investment/suggest/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify({ path_id: pathId, action })
            });
            const data = await resp.json();
            if (data.status === 'success') {
                window.pizarron.showNotification(`Guía ${action} registrada.`, "success");
                this.fetchAlternativePaths();
                this.fetchGovernanceLedger(); // Refresh ledger too
            }
        } catch (err) {
            window.pizarron.showNotification("Error: " + err.message, "error");
        }
    }

    async fetchGovernanceLedger() {
        const list = document.getElementById('governance-ledger-list');
        const filterType = document.getElementById('ledger-filter-type')?.value || '';

        try {
            const resp = await fetch(`/api/v1/governance/ledger/all?decision_type=${filterType}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await resp.json();
            if (data.status === 'success') {
                this.renderGovernanceLedger(data.payload);
            }
        } catch (err) {
            if (list) list.innerHTML = `<p class="error">Error cargando ledger: ${err.message}</p>`;
        }
    }

    renderGovernanceLedger(entries) {
        this.ledgerEntries = entries; // Store for inspection
        const list = document.getElementById('governance-ledger-list');
        if (!list) return;
        if (!entries || entries.length === 0) {
            list.innerHTML = '<div class="no-data-ledger">No hay decisiones estratégicas registradas aún.</div>';
            return;
        }

        list.innerHTML = entries.map(e => {
            const date = new Date(e.created_at);
            const dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
            return `
                <div class="ledger-card ${e.active_flag ? 'active' : 'superseded'} sev-${e.severity_context.toLowerCase()}" onclick="window.roadmapUI.inspectLedgerEntry('${e.ledger_id}')">
                    <div class="l-header">
                        <span class="l-id">${e.ledger_id}</span>
                        <span class="l-badge ${e.decision_type.toLowerCase()}">${e.decision_type.replace(/_/g, ' ')}</span>
                        <span class="l-outcome ${e.outcome_state.toLowerCase()}">${e.outcome_state.replace(/_/g, ' ')}</span>
                    </div>
                    <div class="l-body">
                        <div class="l-reason"><strong>${e.action_taken}:</strong> ${e.rationale}</div>
                        <div class="l-meta">
                            <span>Actor: <strong>${e.actor}</strong></span>
                            <span>Target: <strong>${e.target_ref_type} {${e.target_id}}</strong></span>
                            <span>Fecha: <strong>${dateStr}</strong></span>
                        </div>
                    </div>
                    ${!e.active_flag ? `<div class="l-superseded-banner">SUPERADA POR UNA DECISIÓN POSTERIOR</div>` : ''}
                </div>
            `;
        }).join('');
    }

    inspectLedgerEntry(ledgerId) {
        const e = this.ledgerEntries?.find(entry => entry.ledger_id === ledgerId);
        if (!e) return;

        let actions = ``;
        if (e.target_ref_type === 'BRANCH') {
            actions += `<button class="omni-btn-small" onclick="window.roadmapUI.showBranchDiff('${e.target_id}')">IR A RAMA / DIFF</button>`;
        } else if (e.target_ref_type === 'DOMAIN') {
            actions += `<button class="omni-btn-small" onclick="window.pizarron.switchView('governance')">VER HEATMAP (ESTRUCTURAL)</button>`;
        }

        const evidenceKeys = Object.keys(e.evidence_refs);
        const evidenceStr = evidenceKeys.map(k => `<li>${k}: <strong>${e.evidence_refs[k]}</strong></li>`).join('');

        const modal = document.createElement('div');
        modal.id = 'ledger-inspect-modal';
        modal.className = 'omni-modal ledger-inspect';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>DETALLE DE DECISIÓN ESTRATÉGICA</h2>
                    <button onclick="this.closest('.omni-modal').remove()">×</button>
                </div>
                <div class="modal-body">
                    <div class="l-inspect-hero ${e.outcome_state.toLowerCase()}">
                        <div class="l-type">${e.decision_type.replace(/_/g, ' ')}</div>
                        <div class="l-action">${e.action_taken}</div>
                        <div class="l-status-text">ESTADO: ${e.outcome_state.replace(/_/g, ' ')}</div>
                    </div>
                    <div class="l-inspect-section">
                        <label>RATIONALE / CONTEXTO:</label>
                        <p>${e.rationale}</p>
                    </div>
                    <div class="l-inspect-section">
                        <label>EVIDENCIA VINCULADA:</label>
                        <ul class="l-evidence-list">
                            ${evidenceStr}
                        </ul>
                    </div>
                    <div class="l-inspect-actions">
                        ${actions}
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    async fetchGovernanceConsensus() {
        const list = document.getElementById('consensus-advisory-list');
        try {
            // First trigger a scan to ensure freshness
            await fetch('/api/v1/governance/consensus/scan', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });

            const res = await fetch('/api/v1/governance/consensus/all', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            this.renderGovernanceConsensus(data.payload || []);
        } catch (e) {
            if (list) list.innerHTML = `<div class="error-msg">Error de conexión con el Asesor de Consenso.</div>`;
        }
    }

    renderGovernanceConsensus(advisories) {
        const list = document.getElementById('consensus-advisory-list');
        if (!list) return;

        if (advisories.length === 0) {
            list.innerHTML = '<div class="no-data-consensus">No se detectan sesgos operativos persistentes en el criterio actual. Gobernanza equilibrada.</div>';
            return;
        }

        list.innerHTML = advisories.map(a => `
            <div class="consensus-card sev-${a.severity_band.toLowerCase()} animate-fade-in">
                <div class="c-header">
                    <span class="c-type">${a.advisory_type.replace(/_/g, ' ')}</span>
                    <span class="c-conf">${Math.round(a.confidence * 100)}% Confidence</span>
                </div>
                <div class="c-body">
                    <div class="c-summary">${a.pattern_summary}</div>
                    <div class="c-recommendation"><strong>💡 RECALIBRACIÓN:</strong> ${a.recommendation}</div>
                    <div class="c-evidence">Dominios: ${a.affected_domains.join(', ')} | Refs: ${a.ledger_refs.length} decisiones</div>
                </div>
                <div class="c-footer">
                    <button class="c-btn attend" onclick="window.roadmapUI.actOnConsensusAdvisory('${a.advisory_id}', 'ATTEND')">RECALIBRAR CRITERIO</button>
                    <button class="c-btn secondary" onclick="window.roadmapUI.actOnConsensusAdvisory('${a.advisory_id}', 'IGNORE')">IGNORAR SESGO</button>
                    <button class="c-btn secondary" onclick="window.roadmapUI.viewDecisionGroup('${a.ledger_refs.join(',')}')">VER EVIDENCIA</button>
                </div>
            </div>
        `).join('');
    }

    async actOnConsensusAdvisory(advId, action) {
        try {
            const res = await fetch('/api/v1/governance/consensus/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify({ advisory_id: advId, action })
            });
            const data = await res.json();
            if (data.status === 'success') {
                window.pizarron.showNotification(`Sesgo ${action === 'ATTEND' ? 'atendido' : 'ignorado'}.`, "success");
                this.fetchGovernanceConsensus();
                // Also refresh recalibrations if we attended one
                if (action === 'ATTEND') this.fetchGovernanceRecalculation();
            }
        } catch (e) {
            window.pizarron.showNotification("Error: " + e.message, "error");
        }
    }

    async fetchGovernanceRecalculation() {
        // Redirigimos a la versión con el nombre correcto si existe, 
        // pero vamos a uniformizar a Recalculation por Phase 111
        return this.fetchGovernanceRecalibration();
    }

    async fetchGovernanceRecalibration() {
        const pList = document.getElementById('recalibration-proposals-list');
        const paramList = document.getElementById('governance-parameters-list');

        this.fetchContextualMappings(); // PHASE 112
        this.fetchOracularAlignment(); // PHASE 401

        try {
            // 1. Generate new proposals from consensus
            await fetch('/api/v1/governance/recalibration/generate', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });

            // 2. Fetch all proposals
            const pRes = await fetch('/api/v1/governance/recalibration/proposals', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const pData = await pRes.json();
            this.renderRecalculationProposals(pData.payload || []);

            // 3. Fetch parameters
            const paramRes = await fetch('/api/v1/governance/recalibration/parameters', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const paramData = await paramRes.json();
            this.renderGovernanceParameters(paramData.payload || []);

        } catch (e) {
            if (pList) pList.innerHTML = `<div class="error-msg">Error de sincronización.</div>`;
        }
    }

    renderRecalculationProposals(proposals) {
        const container = document.getElementById('recalibration-proposals-list');
        if (!container) return;

        if (proposals.length === 0) {
            container.innerHTML = '<div class="no-data-small">Sin propuestas de ajuste pendientes.</div>';
            return;
        }

        container.innerHTML = proposals.map(p => `
            <div class="recal-proposal-card ${p.status.toLowerCase()}">
                <div class="rp-engine">${p.target_engine}</div>
                <div class="rp-param">${p.param_key}</div>
                <div class="rp-values">
                    <span class="old">${p.current_value.toFixed(2)}</span>
                    <span class="arrow">→</span>
                    <span class="new">${p.proposed_value.toFixed(2)}</span>
                </div>
                <div class="rp-rationale">${p.rationale}</div>
                ${p.status === 'PROPOSED' ? `
                    <div class="rp-actions">
                        <button class="omni-btn-small" onclick="window.roadmapUI.executeRecalibration('${p.recalibration_id}')">APLICAR</button>
                    </div>
                ` : p.status === 'APPROVED' ? `
                    <div class="rp-actions">
                        <button class="omni-btn-small secondary" onclick="window.roadmapUI.revertRecalibration('${p.recalibration_id}')">REVERTIR</button>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    renderGovernanceParameters(params) {
        const container = document.getElementById('governance-parameters-list');
        if (!container) return;

        container.innerHTML = params.map(p => `
            <div class="param-item">
                <div class="pi-info">
                    <span class="pi-key">${p.param_key}</span>
                    <span class="pi-engine">${p.engine_name}</span>
                </div>
                <div class="pi-value ${p.current_value != p.default_value ? 'recalibrated' : ''}">
                    ${p.current_value.toFixed(2)}
                </div>
            </div>
        `).join('');
    }

    async executeRecalibration(rid) {
        try {
            const res = await fetch('/api/v1/governance/recalibration/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify({ recalibration_id: rid })
            });
            if ((await res.json()).status === 'success') {
                window.pizarron.showNotification("Recalibración aplicada con éxito.", "success");
                this.fetchGovernanceRecalculation();
            }
        } catch (e) { }
    }

    // --- PHASE 112: CONTEXTUAL MAPPING METHODS ---

    async fetchContextualMappings() {
        const container = document.getElementById("contextual-mappings-list");
        if (!container) return;
        try {
            // 1. Profile and search for matches
            const profRes = await fetch('/api/v1/governance/mapping/profile', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const profData = await profRes.json();
            if (profData.status === 'success') {
                this.renderContextualMappings(profData.matches);
            }
        } catch (e) {
            container.innerHTML = `<div class="mapping-error">Error al sincronizar con el Atlas de Contextos.</div>`;
        }
    }

    renderContextualMappings(mappings) {
        const container = document.getElementById("contextual-mappings-list");
        if (!container || !mappings) return;

        if (mappings.length === 0) {
            container.innerHTML = `
                <div class="empty-mapping-state animate-fade-in">
                    <div class="mapping-icon">📡</div>
                    <div class="mapping-msg">No se han detectado paralelos tácticos fuertes aún. Trabajando en aislamiento nominal.</div>
                </div>
            `;
            return;
        }

        container.innerHTML = mappings.map(m => {
            const scorePercent = (m.similarity_score * 100).toFixed(0);
            const sharedDomains = m.shared_domains || [];
            const suggestedParams = m.suggested_baseline_params || {};
            const paramKeys = Object.keys(suggestedParams);

            return `
                <div class="mapping-card animate-slide-up">
                    <div class="mapping-header">
                        <div class="mapping-title">🔗 Similitud con Proyecto: ${m.source_project_id}</div>
                        <div class="mapping-badge ${m.match_type.toLowerCase()}">${m.match_type.replace(/_/g, ' ')}</div>
                    </div>
                    <div class="mapping-metrics">
                        <div class="metric-v">
                            <span class="m-label">Afinidad DNA</span>
                            <span class="m-val">${scorePercent}%</span>
                        </div>
                        <div class="metric-v">
                            <span class="m-label">Riesgo Transferencia</span>
                            <span class="m-val">${m.transfer_risk}</span>
                        </div>
                    </div>
                    <div class="mapping-body">
                        <p class="mapping-rationale">${m.rationale}</p>
                        <div class="shared-domains">
                            <strong>Dominios Comunes:</strong> ${sharedDomains.join(', ') || 'Generalistas'}
                        </div>
                        ${paramKeys.length > 0 ? `
                            <div class="suggested-transfer">
                                <div class="transfer-title">PROYECTO EXTERNO SUGIERE BASELINE:</div>
                                <div class="transfer-params">
                                    ${paramKeys.map(k => `
                                        <div class="transfer-param-line">
                                            <span class="pk">${k}:</span>
                                            <span class="pv">${suggestedParams[k]}</span>
                                        </div>
                                    `).join('')}
                                </div>
                                <button class="btn-transfer-accept" onclick="window.roadmapUI.acceptContextualTransfer('${m.mapping_id}')">
                                    ADOPTAR BASELINE BASADO EN EXPERIENCIA
                                </button>
                            </div>
                        ` : '<p class="transfer-msg">Solo aprendizajes abstractos disponibles para este nivel de similitud.</p>'}
                    </div>
                </div>
            `;
        }).join('');
    }

    // --- PHASE 113: CROSS-PROJECT SEARCH METHODS ---

    async triggerCPSearch() {
        const input = document.getElementById("cp-search-input");
        const list = document.getElementById("cross-project-results-list");
        if (!input || !list) return;

        const val = input.value.trim();
        if (!val) return;

        list.innerHTML = `<div class="omni-loader"></div> <p>Recuperando sabiduría del Atlas transversal...</p>`;

        try {
            const res = await fetch(`/api/v1/governance/mapping/search?keywords=${encodeURIComponent(val)}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            if (data.status === 'success') {
                this.renderCPSearchResults(data.payload);
            }
        } catch (e) {
            list.innerHTML = `<div class="search-error">Error al conectar con la memoria transversal.</div>`;
        }
    }

    renderCPSearchResults(results) {
        const list = document.getElementById("cross-project-results-list");
        if (!list) return;

        if (results.length === 0) {
            list.innerHTML = `<p class="no-results-msg">No se han encontrado precedentes tácticos útiles para este contexto. El aislamiento es total.</p>`;
            return;
        }

        list.innerHTML = results.map(r => `
            <div class="cp-search-card animate-slide-up ${r.relevance_band.toLowerCase()}">
                <div class="cps-header">
                    <span class="cps-type-badge">${r.source_object_type}</span>
                    <span class="cps-project">PROYECTO: ${r.source_project_id}</span>
                </div>
                <div class="cps-body">
                    <div class="cps-summary">${r.lesson_summary}</div>
                    <div class="cps-rationale">${r.rationale}</div>
                    <div class="cps-risk">RIESGO TRANSFERENCIA: <span class="rv">${r.transfer_risk}</span></div>
                </div>
                <!-- SIMULATION AREA (PHASE 301) -->
                <div id="sim-result-${r.source_object_id}" class="sim-result-panel" style="display:none;"></div>

                <div class="cps-footer">
                    <div class="cps-actions">
                        <button class="btn-ref-view" onclick="window.roadmapUI.viewCPReference('${r.source_object_id}', '${r.source_object_type}')">VER EVIDENCIA</button>
                        <button class="btn-ref-simulate" onclick="window.roadmapUI.runTacticalSimulation('${r.source_object_id}', '${r.source_object_type}')">SIMULAR IMPACTO</button>
                        <button class="btn-ref-adopt" onclick="window.roadmapUI.adoptCPReference('${r.source_object_id}', 'ADOPTED')">IMPORTAR TÁCTICA</button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    async adoptCPReference(oid, action) {
        try {
            const res = await fetch('/api/v1/governance/mapping/search/action', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify({ search_id: oid, action: action })
            });
            if ((await res.json()).status === 'success') {
                window.pizarron.showNotification(`Precedente ${action === 'ADOPTED' ? 'adoptado' : 'procesado'} como referencia táctica.`, "success");
            }
        } catch (e) { }
    }

    async runTacticalSimulation(oid, type) {
        const panel = document.getElementById(`sim-result-${oid}`);
        if (!panel) return;
        panel.style.display = 'block';
        panel.innerHTML = `<div class="omni-loader small"></div> <p class="sim-loading-msg">Proyectando impacto en contexto actual...</p>`;

        try {
            const res = await fetch('/api/v1/governance/simulation/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify({ source_id: oid, source_type: type })
            });
            const data = await res.json();
            if (data.status === 'success') {
                this.renderSimulationResult(oid, data.payload);
            }
        } catch (e) {
            panel.innerHTML = `<p class="sim-error">Fallo en motor de simulación. Contexto inestable.</p>`;
        }
    }

    renderSimulationResult(oid, sim) {
        const panel = document.getElementById(`sim-result-${oid}`);
        if (!panel) return;

        const outcomeClass = sim.predicted_outcome.toLowerCase();

        panel.innerHTML = `
            <div class="sim-outcome ${outcomeClass}">
                <div class="sim-badge">${sim.predicted_outcome.replace(/_/g, ' ')}</div>
                <div class="sim-metrics-row">
                    <div class="sim-m">CONFIDENCE: <b>${sim.confidence}</b></div>
                    <div class="sim-m">TRANSFER RISK: <b>${sim.transfer_risk}</b></div>
                </div>
                <div class="sim-rationale-text">${sim.rationale}</div>
                <div class="sim-preconditions">
                    <div class="pre-title">PRECONDICIONES RECOMENDADAS:</div>
                    <ul>
                        ${sim.preconditions.map(p => `<li>${p}</li>`).join('')}
                    </ul>
                </div>
                <div class="sim-footer-actions">
                    <button class="btn-sim-accept" onclick="window.roadmapUI.adoptCPReference('${oid}', 'ADOPTED_SIMULATED')">ADOPTAR TRAS SIMULACIÓN</button>
                    <button class="btn-sim-close" onclick="document.getElementById('sim-result-${oid}').style.display='none'">CANCELAR</button>
                </div>
            </div>
        `;
    }

    // --- PHASE 401: ORACULAR ALIGNMENT (REPLAY SYNC) ---

    async fetchOracularAlignment() {
        const list = document.getElementById('oracular-sync-list');
        if (!list) return;

        try {
            const res = await fetch('/api/v1/governance/simulation/sync/list', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            if (data.status === 'success') {
                this.renderOracularAlignment(data.payload);
            }
        } catch (e) { }
    }

    renderOracularAlignment(syncs) {
        const list = document.getElementById('oracular-sync-list');
        if (!list) return;

        if (syncs.length === 0) {
            list.innerHTML = `<p class="no-sync-msg">No hay ciclos de simulación cerrados. El oráculo aún no ha sido contrastado con la realidad.</p>`;
            return;
        }

        list.innerHTML = syncs.map(s => `
            <div class="sync-card ${s.replay_outcome_state.toLowerCase()}">
                <div class="scy-header">
                    <span class="scy-badge">${s.replay_outcome_state.replace(/_/g, ' ')}</span>
                    <span class="scy-id">ID: ${s.sync_id}</span>
                </div>
                <div class="scy-comparison">
                    <div class="scy-box pred">
                        <div class="l">PREDICCIÓN</div>
                        <div class="v">${s.predicted_effect.replace(/_/g, ' ')}</div>
                    </div>
                    <div class="scy-vs">VS</div>
                    <div class="scy-box real">
                        <div class="l">RESULTADO REAL</div>
                        <div class="v">${s.actual_outcome_summary}</div>
                    </div>
                </div>
                <div class="scy-rationale">${s.rationale}</div>
                <div class="scy-footer">
                    <div class="scy-delta">PROPUESTA AJUSTE: <span class="dv ${s.confidence_delta_proposed >= 0 ? 'pos' : 'neg'}">${s.confidence_delta_proposed >= 0 ? '+' : ''}${s.confidence_delta_proposed}</span></div>
                    ${s.creator_action === 'PENDING' ? `
                        <button class="btn-sync-apply" onclick="window.roadmapUI.applyOracularAdjustment('${s.sync_id}')">APLICAR AJUSTE DE CONFIANZA</button>
                    ` : `<span class="sync-done">AJUSTE PROCESADO</span>`}
                </div>
            </div>
        `).join('');
    }

    async applyOracularAdjustment(syncId) {
        try {
            const res = await fetch('/api/v1/governance/simulation/sync/apply', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify({ sync_id: syncId })
            });
            if ((await res.json()).status === 'success') {
                window.pizarron.showNotification("Confianza del oráculo recalibrada con evidencia real.", "success");
                this.fetchOracularAlignment();
            }
        } catch (e) { }
    }

    viewCPReference(oid, type) {
        window.pizarron.showNotification(`Abriendo evidencia de ${type}: [${oid}]. Conexión con Atlas establecida.`, "info");
        // Logic to open Drawer or Dashboard specific view for the object
    }

    async acceptContextualTransfer(mappingId) {
        try {
            const res = await fetch('/api/v1/governance/mapping/transfer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify({ mapping_id: mappingId })
            });
            if ((await res.json()).status === 'success') {
                window.pizarron.showNotification("Baselines contextuales adoptados. Sistema recalibrado por sabiduría externa.", "success");
                this.fetchGovernanceRecalculation(); // Refresh everything
            }
        } catch (e) {
            window.pizarron.showNotification("Error al transferir contexto.", "error");
        }
    }

    async revertRecalibration(rid) {
        try {
            const res = await fetch('/api/v1/governance/recalibration/revert', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify({ recalibration_id: rid })
            });
            if ((await res.json()).status === 'success') {
                window.pizarron.showNotification("Parámetro revertido al valor por defecto.", "info");
                this.fetchGovernanceRecalculation();
            }
        } catch (e) { }
    }

    viewDecisionGroup(refsStr) {
        const refs = refsStr.split(',');
        window.pizarron.showNotification(`Mostrando grupo de ${refs.length} decisiones vinculadas al patrón.`, "info");
        // In a real implementation, this could filter the ledger view
    }

    async openArbitrationCockpit(branchId) {
        const modal = document.createElement('div');
        modal.id = 'arbitration-cockpit-modal';
        modal.className = 'omni-modal arbitration-cockpit';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>CABINA DE ARBITRAJE: CREATOR_CORE</h2>
                    <button class="close-btn" onclick="document.getElementById('arbitration-cockpit-modal').remove()">×</button>
                </div>
                <div id="arb-cockpit-body" class="modal-body loading">
                    <div class="omni-loader"></div>
                    <p>Compilando dossier de escalación...</p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        try {
            const resp = await fetch(`/api/v1/roadmap/branches/${branchId}/dossier`);
            const data = await resp.json();
            this.renderArbitrationDossier(data);
        } catch (err) {
            document.getElementById('arb-cockpit-body').innerHTML = `<p class="error">Error: ${err.message}</p>`;
        }
    }

    renderArbitrationDossier(data) {
        const body = document.getElementById('arb-cockpit-body');
        body.classList.remove('loading');

        body.innerHTML = `
            <div class="arb-grid">
                <div class="arb-dossier-panel">
                    <h3>DOSSIER ESTRATÉGICO</h3>
                    <div class="dossier-item">RAMA: <strong>${data.branch.name}</strong></div>
                    <div class="dossier-item">DIVERGENCIA: <strong>${Math.round(data.branch.divergence_score * 100)}%</strong></div>
                    <div class="dossier-item">STATUS CONSTITUCIONAL: <strong class="${data.branch.constitutional_status.toLowerCase()}">${data.branch.constitutional_status}</strong></div>
                    
                    <div class="dossier-friction-map">
                        <h4>MAPA DE TENSIÓN DE ROLES</h4>
                        ${Object.entries(data.persona_friction_map).map(([role, friction]) => `
                            <div class="f-row">
                                <span>${role}</span>
                                <div class="f-bar"><div class="f-fill" style="width: ${friction * 100}%"></div></div>
                                <strong>${Math.round(friction * 100)}%</strong>
                            </div>
                        `).join('')}
                    </div>

                    <div class="dossier-compensations">
                        <h4>HISTORIAL DE COMPENSACIONES</h4>
                        ${data.compensation_audits.length === 0 ? '<p>Ninguna compensación intentada.</p>' :
                data.compensation_audits.map(a => `
                                <div class="arb-audit-mini">
                                    <span class="st-${a.effectiveness_state.toLowerCase()}">${a.effectiveness_state}</span>
                                    ${a.rationale}
                                </div>
                            `).join('')
            }
                    </div>
                </div>

                <div class="arb-decision-panel">
                    <h3>DECISIÓN DE ARBITRAJE</h3>
                    <div class="arb-recommendation">${data.recommendation}</div>
                    
                    <div class="arb-form">
                        <label>ACCIÓN DE CREATOR_CORE:</label>
                        <select id="arb-decision-select">
                            <option value="APPROVE_ANYWAY">APROBAR (OVERRIDE CONSTITUCIONAL)</option>
                            <option value="APPROVE_WITH_CONDITIONS">APROBAR BAJO CONDICIONES</option>
                            <option value="REQUIRE_FURTHER_COMPENSATION">EXIGIR MÁS SANEAMIENTO</option>
                            <option value="POSTPONE">POSPONER DECISIÓN</option>
                            <option value="REJECT_VETO">VETO ESTRATÉGICO</option>
                        </select>

                        <label>RATIONALE (JUSTIFICACIÓN):</label>
                        <textarea id="arb-rationale" placeholder="Explica la razón del arbitraje para la trazabilidad forense..."></textarea>
                        
                        <label>CONDICIONES (OPCIONAL, UN POR LÍNEA):</label>
                        <textarea id="arb-conditions" placeholder="Ej: Realizar hardening de seguridad en siguiente sprint..."></textarea>

                        <button class="arb-submit-btn" onclick="window.roadmapUI.submitArbitration('${data.branch.branch_id}')">APLICAR ARBITRAJE</button>
                    </div>
                </div>
            </div>
        `;
    }

    async submitArbitration(branchId) {
        const decision = document.getElementById('arb-decision-select').value;
        const rationale = document.getElementById('arb-rationale').value;
        const conditions = document.getElementById('arb-conditions').value.split('\n').filter(l => l.trim() !== '');

        if (!rationale) {
            alert("Debe incluir un RATIONALE para el arbitraje constitucional.");
            return;
        }

        try {
            const resp = await fetch(`/api/v1/roadmap/branches/${branchId}/arbitrate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ decision, rationale, conditions })
            });
            const res = await resp.json();
            if (res.arbitration_id) {
                window.pizarron.showNotification("Arbitraje aplicado con éxito.", "success");
                document.getElementById('arbitration-cockpit-modal').remove();
                if (document.getElementById('strategic-dashboard-modal')) {
                    document.getElementById('strategic-dashboard-modal').remove();
                }
                this.refreshBranches();
            }
        } catch (err) {
            alert("Error al aplicar arbitraje: " + err.message);
        }
    }

    async viewExceptionsReport() {
        const modal = document.createElement('div');
        modal.id = 'exceptions-report-modal';
        modal.className = 'omni-modal exceptions-report';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>REPORTE FORENSE DE EXCEPCIONALIDAD</h2>
                    <button class="close-btn" onclick="document.getElementById('exceptions-report-modal').remove()">×</button>
                </div>
                <div id="exceptions-body" class="modal-body loading">
                    <div class="omni-loader"></div>
                    <p>Rastreando deuda constitucional acumulada...</p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        try {
            const resp = await fetch('/api/v1/roadmap/exceptions-report');
            const data = await resp.json();
            this.renderExceptionsReport(data);
        } catch (err) {
            document.getElementById('exceptions-body').innerHTML = `<p class="error">Error: ${err.message}</p>`;
        }
    }

    renderExceptionsReport(data) {
        const body = document.getElementById('exceptions-body');
        body.classList.remove('loading');

        // Segmenting by triage
        const critical = data.active_exceptions.filter(ex => ex.triage.classification === 'CRITICAL_DEBT');
        const medium = data.active_exceptions.filter(ex => ex.triage.classification === 'MEDIUM_PRIORITY');
        const noise = data.active_exceptions.filter(ex => ex.triage.classification === 'LOW_IMPACT' || ex.triage.classification === 'SIGNAL_NOISE');

        body.innerHTML = `
            <div class="ex-summary">
                <div class="ex-debt-score">PUNTAJE DE DEUDA: <strong>${data.total_debt_score.toFixed(1)}</strong></div>
                <div class="ex-actions-top">
                    <button class="advisory-cockpit-btn" onclick="window.roadmapUI.viewAdvisoryDashboard()">🎯 CABINA DE ASESORÍA</button>
                </div>
            </div>
            
            <div id="ex-triage-container">
                ${critical.length > 0 ? `
                    <div class="triage-section critical">
                        <h3>🔴 DEUDA CONSTITUCIONAL CRÍTICA (${critical.length})</h3>
                        <div class="ex-list">
                            ${critical.map(ex => this.renderExceptionCard(ex, true, data)).join('')}
                        </div>
                    </div>
                ` : ''}

                ${medium.length > 0 ? `
                    <div class="triage-section medium">
                        <h3>🟡 MONITOREO TÁCTICO (${medium.length})</h3>
                        <div class="ex-list">
                            ${medium.map(ex => this.renderExceptionCard(ex, true, data)).join('')}
                        </div>
                    </div>
                ` : ''}

                ${noise.length > 0 ? `
                    <div class="triage-section noise">
                        <div class="section-header-row">
                            <h3>⚪ RUIDO TÉCNICO / BAJO IMPACTO (${noise.length})</h3>
                            <div class="header-actions">
                                <button class="healing-preview-btn" onclick="window.roadmapUI.openHealingPreview()">🔍 SANEAMIENTO</button>
                                <button class="pruning-preview-btn" onclick="window.roadmapUI.openPruningPreview()">🧹 PRUNING</button>
                            </div>
                        </div>
                        <div class="ex-list compact">
                            ${noise.map(ex => this.renderExceptionCard(ex, true, data)).join('')}
                        </div>
                    </div>
                ` : ''}

                ${data.memory_clusters && data.memory_clusters.length > 0 ? `
                    <div class="triage-section memory-clusters">
                        <h3>🧠 MEMORIA DE GOBERNANZA — CLÚSTERS DE DEUDA (${data.memory_clusters.length})</h3>
                        <div class="patterns-grid">
                            ${data.memory_clusters.map(cluster => `
                                <div class="pattern-item risk-${cluster.structural_risk_level.toLowerCase()}">
                                    <div class="p-header">
                                        <span class="p-risk-badge">${cluster.structural_risk_level}</span>
                                        <span class="p-id"> PATRÓN: ${cluster.pattern_id}</span>
                                    </div>
                                    <div class="p-rationale">${cluster.rationale}</div>
                                    ${(() => {
                const advisory = data.advisories.find(a => a.source_pattern_id === cluster.pattern_id);
                if (!advisory) return '';
                return `
                                            <div class="pattern-advisory">
                                                <div class="adv-label">🎯 ASESORÍA OMNIWEB</div>
                                                <div class="adv-type">${advisory.advisory_type.replace(/_/g, ' ')}</div>
                                                <p>${advisory.rationale}</p>
                                                <div class="adv-actions">
                                                    <button class="adv-accept-btn" onclick="window.roadmapUI.acceptAdvisory('${advisory.advisory_id}')">ACEPTAR INTERVENCIÓN</button>
                                                    <button class="adv-ignore-btn" onclick="this.closest('.pattern-advisory').remove()">POSTERGAR</button>
                                                </div>
                                            </div>
                                        `;
            })()}
                                    <div class="p-meta">
                                        <span>🌍 Dominios: ${cluster.affected_domains.join(', ')}</span><br>
                                        <span>⛓️ Señales vinculadas: ${cluster.linked_signal_ids.length}</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <div class="triage-section resolved">
                    <h3>🟢 EXCEPCIONES SANEADAS / HISTÓRICAS (${data.resolved_exceptions.length})</h3>
                    <div class="ex-list">
                        ${data.resolved_exceptions.map(ex => this.renderExceptionCard(ex, false, data)).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    renderExceptionCard(ex, isActive, reportData = null) {
        const triage = ex.triage || { classification: 'UNKNOWN', impact_score: 0 };
        const cluster = reportData && reportData.memory_clusters ?
            reportData.memory_clusters.find(c => c.linked_signal_ids.includes(ex.exception_id)) : null;

        return `
            <div class="ex-card ${isActive ? 'active' : 'resolved'} triage-${triage.classification.toLowerCase()} ${cluster ? 'has-cluster' : ''}">
                <div class="ex-header">
                    <span class="ex-branch">${ex.branch_name}</span>
                    <div class="ex-badges">
                        ${cluster ? `<span class="ex-cluster-badge" title="Patrón estructural detectado: ${cluster.pattern_id}">🧠 LINKED</span>` : ''}
                        <span class="ex-triage-badge">${triage.classification.replace(/_/g, ' ')} [${triage.impact_score.toFixed(1)}]</span>
                    </div>
                </div>
                <div class="ex-rationale">"${ex.rationale}"</div>
                <div class="ex-conditions">
                    <strong>CONDICIONES:</strong>
                    <ul>
                        ${ex.conditions.map(c => `<li>${c}</li>`).join('')}
                    </ul>
                </div>
                <div class="ex-footer">
                    <span class="ex-date">Creada: ${new Date(ex.created_at).toLocaleDateString()}</span>
                    ${isActive ?
                (ex.compliance_state === 'PLANNING' ?
                    `<span class="ex-planning-badge">EN PLANIFICACIÓN...</span>` :
                    `<button class="oracle-btn" onclick="window.roadmapUI.openHealthOracle('exception', '${ex.exception_id}')">🔮 PROYECTAR</button>
                             <button class="recovery-btn" onclick="window.roadmapUI.openRecoveryPreview('${ex.exception_id}')">SANEAMIENTO</button>
                             <button class="resolve-btn" onclick="window.roadmapUI.markExceptionResolved('${ex.exception_id}')">SANEADA</button>
                             <button class="replay-btn" title="Replay Forense" onclick="window.roadmapUI.openForensicsReplay('${ex.exception_id}')">📜</button>`
                ) :
                `<span class="ex-resolved-date">Saneada: ${new Date(ex.resolved_at).toLocaleDateString()}</span>
                 <button class="replay-btn" title="Replay Forense" onclick="window.roadmapUI.openForensicsReplay('${ex.exception_id}')">📜</button>`
            }
                </div>
            </div>
        `;
    }

    async markExceptionResolved(id) {
        if (!confirm("¿Confirmas que las condiciones de esta excepción han sido cumplidas en Main?")) return;

        try {
            const resp = await fetch(`/api/v1/roadmap/exceptions/${id}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ state: 'FULFILLED' })
            });
            const res = await resp.json();
            if (res.status === 'success') {
                window.pizarron.showNotification("Excepción saneada.", "success");
                this.viewExceptionsReport(); // Refresh
            }
        } catch (err) {
            alert("Error: " + err.message);
        }
    }

    async openRecoveryPreview(exceptionId) {
        const modal = document.createElement('div');
        modal.id = 'recovery-preview-modal';
        modal.className = 'omni-modal recovery-preview';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>PLANIFICADOR DE SANEAMIENTO: PREVIEW</h2>
                    <button class="close-btn" onclick="document.getElementById('recovery-preview-modal').remove()">×</button>
                </div>
                <div id="recovery-body" class="modal-body loading">
                    <div class="omni-loader"></div>
                    <p>Diseñando ruta de remediación táctica...</p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        try {
            const resp = await fetch(`/api/v1/roadmap/exceptions/${exceptionId}/recovery`);
            const proposals = await resp.json();
            this.renderRecoveryProposals(proposals);
        } catch (err) {
            document.getElementById('recovery-body').innerHTML = `<p class="error">Error: ${err.message}</p>`;
        }
    }

    renderRecoveryProposals(proposals) {
        const body = document.getElementById('recovery-body');
        body.classList.remove('loading');

        if (proposals.length === 0) {
            body.innerHTML = `<p>No se encontraron rutas de recuperación automáticas para esta excepción.</p>`;
            return;
        }

        body.innerHTML = `
            <div class="recovery-intro">
                OmniWeb propone las siguientes misiones de saneamiento para pagar la deuda constitutional asociada. 
                Ninguna misión se ejecutará automáticamente; deben ser aceptadas para entrar en la cola de Handoffs.
            </div>
            <div class="recovery-grid">
                ${proposals.map(p => `
                    <div class="recovery-card">
                        <div class="rec-header">
                            <span class="rec-type">${p.proposed_mission_type}</span>
                            <span class="rec-risk ${p.suggested_risk.toLowerCase()}">RIESGO: ${p.suggested_risk}</span>
                        </div>
                        <div class="rec-objective">${p.suggested_objective}</div>
                        <div class="rec-rationale">${p.rationale}</div>
                        <div class="rec-details">
                            <div>DOMINIO: <strong>${p.target_domain}</strong></div>
                            <div>REDUCCIÓN DE DEUDA: <strong>${Math.round(p.expected_debt_reduction * 100)}%</strong></div>
                        </div>
                        <button class="rec-inject-btn" onclick='window.roadmapUI.injectRecoveryMission(${JSON.stringify(p)})'>ACEPTAR E INYECTAR</button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async injectRecoveryMission(proposal) {
        try {
            const resp = await fetch('/api/v1/roadmap/recovery/inject', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(proposal)
            });
            const res = await resp.json();
            if (res.status === 'success') {
                window.pizarron.showNotification("Misión de saneamiento inyectada en backlog.", "success");
                document.getElementById('recovery-preview-modal').remove();
                this.viewExceptionsReport(); // Refresh report
            }
        } catch (err) {
            alert("Error al inyectar recovery: " + err.message);
        }
    }

    async openHealthOracle(type, id) {
        const modal = document.createElement('div');
        modal.id = 'oracle-modal';
        modal.className = 'omni-modal oracle-view';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>ORÁCULO DE SALUD CONSTITUCIONAL</h2>
                    <button class="close-btn" onclick="document.getElementById('oracle-modal').remove()">×</button>
                </div>
                <div id="oracle-body" class="modal-body loading">
                    <div class="omni-loader"></div>
                    <p>Consultando líneas de tiempo estratégicas...</p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        try {
            const resp = await fetch(`/api/v1/roadmap/oracle/${type}/${id}`);
            const forecasts = await resp.json();
            this.renderOracleForecasts(forecasts);
        } catch (err) {
            document.getElementById('oracle-body').innerHTML = `<p class="error">Error: ${err.message}</p>`;
        }
    }

    renderOracleForecasts(forecasts) {
        const body = document.getElementById('oracle-body');
        body.classList.remove('loading');

        body.innerHTML = `
            <div class="oracle-intro">
                Análisis comparativo de escenarios futuros según la deuda actual y el drift detectado. 
                Los valores reflejan la degradación sistémica proyectada a 3 misiones.
            </div>
            <div class="oracle-forecast-grid">
                ${forecasts.map(f => `
                    <div class="forecast-card ${f.scenario.toLowerCase()}">
                        <div class="f-header">
                            <span class="f-scenario">${f.scenario.replace(/_/g, ' ')}</span>
                            <span class="f-conf">CONF: ${Math.round(f.confidence * 100)}%</span>
                        </div>
                        <div class="f-metrics">
                            <div class="f-m">
                                <label>DEUDA PROYECTADA</label>
                                <div class="f-val">${f.debt_score.toFixed(1)}</div>
                            </div>
                            <div class="f-m">
                                <label>FRAGILIDAD DOMINIO</label>
                                <div class="f-val">${Math.round(f.domain_fragility * 100)}%</div>
                            </div>
                        </div>
                        <div class="f-rationale">"${f.rationale}"</div>
                        <div class="f-rec">RECOMENDACIÓN: <strong>${f.recommendation.replace(/_/g, ' ')}</strong></div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderBranchHUD() {
        const container = document.getElementById('roadmap-branch-hud');
        if (!container) return;

        container.innerHTML = `
            <div class="branch-hud animate-fade-in">
                <div class="branch-controls">
                    <button class="btn-create-branch" onclick="window.roadmapUI.promptCreateBranch()">+ NUEVA RAMA</button>
                    <button class="btn-strat-dash" onclick="window.roadmapUI.viewStrategicDashboard()">📊 VISTA ESTRATÉGICA</button>
                </div>
                <div class="branch-header">
                    <span class="branch-icon">🌿</span>
                    <span class="branch-title">TACTICAL BRANCHES</span>
                </div>
                <div class="branch-list">
                    ${this.branches.map(b => `
                        <div class="branch-item ${this.activeBranchId === b.branch_id ? 'active' : ''}" 
                             onclick="window.roadmapUI.switchBranch('${b.branch_id}')">
                            <span class="b-name">${b.name}</span>
                            <span class="b-status">${b.status}</span>
                            ${b.branch_id !== 'main' ? `
                                <div class="b-actions">
                                    <button class="diff-btn" title="Ver Diff Táctico" onclick="event.stopPropagation(); window.roadmapUI.showBranchDiff('${b.branch_id}')">DIFF</button>
                                    <button class="merge-btn" onclick="event.stopPropagation(); window.roadmapUI.mergeBranch('${b.branch_id}')">MERGE</button>
                                    <button class="discard-btn" onclick="event.stopPropagation(); window.roadmapUI.discardBranch('${b.branch_id}')">×</button>
                                </div>
                            ` : ''}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    promptCreateBranch() {
        const name = prompt("Nombre de la rama técnica/experimental:");
        if (name) this.createBranch(name);
    }

    async createBranch(name) {
        try {
            const res = await fetch(`/api/v1/roadmap/branches?name=${encodeURIComponent(name)}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const branch = await res.json();
            this.activeBranchId = branch.branch_id;
            this.refresh();
        } catch (e) { console.error(e) }
    }

    async switchBranch(bid) {
        this.activeBranchId = bid;
        this.refresh();
    }

    async mergeBranch(bid) {
        if (!confirm(`¿FUSIONAR rama experimental '${bid}' en el Main Roadmap?\nEsta acción reemplazará la estrategia principal.`)) return;
        try {
            const res = await fetch(`/api/v1/roadmap/branches/${bid}/merge`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            if (data.status === 'BLOCKED') {
                alert(`⛔ MERGE BLOQUEADO POR GOBERNANZA:\n\n${data.reason}`);
                return;
            }
            this.activeBranchId = 'main';
            this.refresh();
        } catch (e) {
            console.error(e);
            alert("Error crítico durante el proceso de merge gobernado.");
        }
    }

    async discardBranch(bid) {
        if (!confirm(`¿DESCARTAR rama '${bid}'? Todos los experimentos tácticos se perderán.`)) return;
        try {
            await fetch(`/api/v1/roadmap/branches/${bid}`, {
                method: 'DELETE',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            if (this.activeBranchId === bid) this.activeBranchId = 'main';
            this.refresh();
        } catch (e) { console.error(e) }
    }

    async injectCompensation(bid, cid) {
        const btn = document.querySelector(`#comp-${cid} .comp-inject-btn`);
        if (btn) btn.innerText = "INYECTANDO...";

        try {
            const res = await fetch(`/api/v1/roadmap/branches/${bid}/compensations/${cid}/inject`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            if (data.status === 'success') {
                alert(`✅ Misión compensatoria inyectada con éxito.\nLa rama se está re-auditando.`);
                // Refresh modal with new data
                this.showBranchDiff(bid);
            } else {
                alert(`Error: ${data.message}`);
                if (btn) btn.innerText = "INYECTAR MISIÓN";
            }
        } catch (e) {
            console.error("Injection failed", e);
            alert("Error crítico en la inyección de compensación.");
        }
    }

    renderSimulationHUD() {
        const container = document.getElementById('strategic-sim-hud');
        if (!container || !this.simulations || this.simulations.length === 0) return;

        const sim = this.simulations.find(s => s.type === this.currentScenario) || this.simulations[0];

        container.innerHTML = `
            <div class="simulation-hud animate-fade-in type-${sim.type.toLowerCase()}">
                <div class="hud-header">
                    <span class="hud-icon">🌌</span>
                    <span class="hud-title">FUTURE SIMULATION: ${sim.name.toUpperCase()}</span>
                    <div class="hud-toggle">
                        ${this.simulations.map(s => `
                            <button class="toggle-btn ${this.currentScenario === s.type ? 'active' : ''}" 
                                onclick="window.roadmapUI.toggleScenario('${s.type}')">${s.type}</button>
                        `).join('')}
                    </div>
                </div>
                <div class="hud-metrics">
                    ${sim.projected_friction.map(m => `
                        <div class="hud-metric-card" style="border-bottom: 2px solid rgba(255,100,50, ${m.score})">
                            <div class="m-val">${Math.round(m.score * 100)}%</div>
                            <div class="m-cat">${m.category} FRICTION</div>
                        </div>
                    `).join('')}
                    <div class="hud-metric-card confidence">
                        <div class="m-val">${Math.round(sim.confidence * 100)}%</div>
                        <div class="m-cat">CONFIDENCE</div>
                    </div>
                </div>
                <div class="hud-summary">${sim.summary}</div>
                <div class="hud-recs">
                    ${sim.recommendations.map(r => `<div class="rec-item">💡 ${r}</div>`).join('')}
                </div>
            </div>
        `;
    }

    async showBranchDiff(bid) {
        try {
            const [diffRes, simRes] = await Promise.all([
                fetch(`/api/v1/roadmap/branches/${bid}/diff`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
                }),
                fetch(`/api/v1/roadmap/branches/${bid}/persona-sim`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
                })
            ]);

            const diff = await diffRes.json();
            const personaSim = await simRes.json();
            this.renderDiffModal(diff, personaSim);
        } catch (e) {
            console.error("Failed to fetch branch data", e);
            alert("No se pudo generar el análisis táctico multi-persona.");
        }
    }

    renderDiffModal(diff, personaSim = null) {
        const modal = document.createElement('div');
        modal.className = 'roadmap-preview-modal diff-overlay animate-fade-in';
        modal.id = 'diff-modal';

        const constClass = `delta-${diff.constitutional_delta.toLowerCase()}`;
        const consensusClass = personaSim ? `consensus-${personaSim.global_consenus.toLowerCase().replace(/_/g, '-')}` : '';

        modal.innerHTML = `
            <div class="preview-content diff-content">
                <div class="preview-header">
                    <div class="diff-branding">OMNIWEB — TACTICAL SNAPSHOT DIFF</div>
                    <h2>DIFF: main ↔ ${diff.target_branch}</h2>
                    <div class="constitutional-delta ${constClass}">
                        GOVERNANCE: ${diff.constitutional_delta}
                    </div>
                </div>

                <div class="diff-summary-bar">
                    <div class="s-delta">
                        <span class="label">FRICTION DELTA</span>
                        <span class="val ${diff.friction_delta < 0 ? 'good' : 'bad'}">${(diff.friction_delta * 100).toFixed(1)}%</span>
                    </div>
                    <div class="s-delta">
                        <span class="label">CONSENSUS</span>
                        <span class="val consensus-label ${consensusClass}">${personaSim?.global_consenus || 'PENDING'}</span>
                    </div>
                </div>

                ${diff.persona_verdict ? `
                    <div class="persona-governance-gate ${diff.persona_verdict.severity}">
                        <div class="gate-status-row">
                            <span class="gate-icon">${diff.persona_verdict.state === 'APPROVED' ? '✅' : '⛔'}</span>
                            <span class="gate-state">${diff.persona_verdict.state.replace(/_/g, ' ')}</span>
                            <span class="gate-bias">BIAS: ${Math.round(diff.persona_verdict.merge_bias_score * 100)}%</span>
                        </div>
                        <div class="gate-rationale">${diff.persona_verdict.rationale}</div>
                        
                        ${diff.compensation_audits && diff.compensation_audits.length > 0 ? `
                            <div class="effectiveness-feed">
                                <div class="feed-label">HISTORIAL DE EFECTIVIDAD:</div>
                                ${diff.compensation_audits.map(a => `
                                    <div class="effect-card ${a.effectiveness_state.toLowerCase()}">
                                        <div class="effect-header">
                                            <span class="effect-badge">${a.effectiveness_state}</span>
                                            <span class="effect-time">${new Date(a.created_at).toLocaleTimeString()}</span>
                                        </div>
                                        <div class="effect-states">
                                            <span class="st st-prev">${a.before_state}</span>
                                            <span class="st-arrow">→</span>
                                            <span class="st st-now">${a.after_state}</span>
                                        </div>
                                        <div class="effect-persona-pills">
                                            ${Object.entries(JSON.parse(a.persona_deltas || '{}')).map(([role, delta]) => `
                                                <span class="p-pill ${delta > 0 ? 'worse' : delta < 0 ? 'better' : 'neutral'}">
                                                    ${role}: ${delta > 0 ? '+' : ''}${Math.round(delta * 100)}%
                                                </span>
                                            `).join('')}
                                        </div>
                                        <div class="effect-rationale">${a.rationale}</div>
                                        <div class="effect-actions">
                                            <div class="effect-advice">SIGUIENTE ACCIÓN: <strong>${a.recommended_next_action}</strong></div>
                                            <button class="revert-btn" onclick="window.roadmapUI.revertCompensation('${diff.target_branch}', '${a.compensation_id}')">REVERTIR</button>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}

                        ${diff.persona_verdict.suggested_missions && diff.persona_verdict.suggested_missions.length > 0 ? `
                            <div class="gate-compensations structured">
                                <strong>RUTAS DE COMPENSACIÓN TÁCTICA:</strong>
                                ${diff.persona_verdict.suggested_missions.map(m => `
                                    <div class="compensation-preview-card" id="comp-${m.compensation_id}">
                                        <div class="cp-header">
                                            <span class="cp-type">${m.type}</span>
                                            <span class="cp-persona">${m.persona_role}</span>
                                        </div>
                                        <div class="cp-obj">${m.objective}</div>
                                        <div class="cp-rationale">${m.rationale}</div>
                                        <div class="cp-impact">PREDICCIÓN: ${m.expected_impact}</div>
                                        ${m.already_exists ? `
                                            <div class="cp-exists-badge">EVITANDO DUPLICADO: MISIÓN EXISTENTE DETECTADA</div>
                                            <button class="comp-inject-btn secondary" onclick="window.roadmapUI.inspectItem('${m.existing_mission_id}')">REVISAR / AMPLIAR EXISTENTE</button>
                                        ` : `
                                            <button class="comp-inject-btn" onclick="window.roadmapUI.injectCompensation('${diff.target_branch}', '${m.compensation_id}')">INYECTAR EN RAMA</button>
                                        `}
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                ` : ''}

                <div class="persona-projection-container">
                    <div class="section-label">PERSONA PROJECTION & эксперт REACTION</div>
                    <div class="persona-grid">
                        ${personaSim?.responses.map(r => `
                            <div class="persona-sim-card">
                                <div class="p-header">
                                    <span class="p-role">${r.role}</span>
                                    <span class="p-score ${r.support_score > 0.7 ? 'good' : r.support_score < 0.4 ? 'bad' : 'warn'}">
                                        ${Math.round(r.support_score * 100)}% Support
                                    </span>
                                </div>
                                <div class="p-friction-bar">
                                    <div class="f-fill" style="width: ${r.friction_score * 100}%; background: ${r.friction_score > 0.5 ? 'var(--pizarron-critical)' : 'var(--pizarron-warn)'}"></div>
                                </div>
                                <div class="p-rationale">${r.rationale}</div>
                                ${r.recommendation ? `<div class="p-rec">💡 ${r.recommendation}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="diff-items-container">
                    ${diff.items.length === 0 ? '<div class="no-diff">No hay cambios tácticos detectados.</div>' : ''}
                    
                    ${['ADDED', 'REMOVED', 'MODIFIED'].map(type => {
            const typeItems = diff.items.filter(i => i.type === type);
            if (typeItems.length === 0) return '';
            return `
                            <div class="diff-group group-${type.toLowerCase()}">
                                <div class="group-label">${type} (${typeItems.length})</div>
                                <div class="group-list">
                                    ${typeItems.map(item => `
                                        <div class="diff-item-card">
                                            <div class="i-header">
                                                <span class="i-icon">${type === 'ADDED' ? '＋' : type === 'REMOVED' ? '－' : '△'}</span>
                                                <span class="i-title">${item.title}</span>
                                            </div>
                                            <div class="i-details">
                                                ${item.delta_details.map(d => `<div class="d-line">• ${d}</div>`).join('')}
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `;
        }).join('')}
                </div>

                <div class="preview-footer diff-footer">
                    <button class="preview-btn secondary" onclick="document.getElementById('diff-modal').remove()">CERRAR</button>
                    <button class="preview-btn danger" onclick="window.roadmapUI.discardBranch('${diff.target_branch}'); document.getElementById('diff-modal').remove()">DESCARTAR RAMA</button>
                    <button class="preview-btn primary" onclick="window.roadmapUI.mergeBranch('${diff.target_branch}'); document.getElementById('diff-modal').remove()">FUSIONAR EN MAIN</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    async openHealingPreview() {
        const modal = document.createElement('div');
        modal.id = 'healing-preview-modal';
        modal.className = 'omni-modal healing-preview';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>PREVIEW: SANEAMIENTO PRUDENTE AGRUPADO</h2>
                    <button class="close-btn" onclick="document.getElementById('healing-preview-modal').remove()">×</button>
                </div>
                <div id="healing-body" class="modal-body loading">
                    <div class="omni-loader"></div>
                    <p>Agrupando señales de bajo impacto...</p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        try {
            const resp = await fetch('/api/v1/roadmap/healing/proposals');
            const proposals = await resp.json();
            this.renderHealingProposals(proposals);
        } catch (err) {
            document.getElementById('healing-body').innerHTML = `<p class="error">Error: ${err.message}</p>`;
        }
    }

    renderHealingProposals(packages) {
        const body = document.getElementById('healing-body');
        body.classList.remove('loading');

        if (packages.length === 0) {
            body.innerHTML = `<p class="empty-msg">No se encontraron señales de ruido agrupables en este momento.</p>`;
            return;
        }

        body.innerHTML = `
            <div class="healing-intro">
                OmniWeb ha detectado clusters de ruido técnico que pueden sanarse en bloque. 
                Revisa y selecciona los paquetes o acciones individuales para inyectar como misiones de limpieza.
            </div>
            <div class="healing-grid">
                ${packages.map(p => `
                    <div class="healing-package-card" id="pkg-${p.package_id}">
                        <div class="p-header">
                            <span class="p-name">${p.name}</span>
                            <span class="p-reduction">REDUCCIÓN DEUDA: ${p.total_impact_reduction.toFixed(1)}</span>
                        </div>
                        <div class="p-rationale">${p.rationale}</div>
                        <div class="p-signals">
                            <strong>SEÑALES INCLUIDAS (${p.signals.length}):</strong>
                            <div class="s-pills">
                                ${p.signals.map(s => `<span class="s-pill">${s}</span>`).join('')}
                            </div>
                        </div>
                        <div class="p-actions">
                            <strong>ACCIONES PROPUESTAS:</strong>
                            ${p.proposed_actions.map(a => `
                                <div class="a-row">
                                    <input type="checkbox" id="check-${a.action_id}" checked>
                                    <div class="a-content">
                                        <div class="a-obj">${a.objective}</div>
                                        <div class="a-rat">${a.rationale}</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                        <button class="p-apply-btn" onclick='window.roadmapUI.applyHealingPackage(${JSON.stringify(p)})'>ACEPTAR LOTE SELECCIONADO</button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    async applyHealingPackage(pkg) {
        const actionIds = pkg.proposed_actions
            .filter(a => document.getElementById(`check-${a.action_id}`).checked)
            .map(a => a.action_id);

        if (actionIds.length === 0) {
            alert("Debe seleccionar al menos una acción para aplicar el saneamiento.");
            return;
        }

        try {
            const resp = await fetch('/api/v1/roadmap/healing/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action_ids: actionIds, package: pkg })
            });
            const res = await resp.json();
            if (res.status === 'success') {
                window.pizarron.showNotification(`Saneamiento inyectado: ${res.injected_actions} misiones creadas.`, "success");
                document.getElementById('healing-preview-modal').remove();
                this.viewExceptionsReport(); // Refresh
            }
        } catch (err) {
            alert("Error al aplicar saneamiento: " + err.message);
        }
    }
    async openPruningPreview() {
        const modal = document.createElement('div');
        modal.id = 'pruning-preview-modal';
        modal.className = 'omni-modal pruning-preview';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>PREVIEW: ARCHIVADO PRUDENTE (PRUNING)</h2>
                    <button class="close-btn" onclick="document.getElementById('pruning-preview-modal').remove()">×</button>
                </div>
                <div id="pruning-body" class="modal-body loading">
                    <div class="omni-loader"></div>
                    <p>Identificando señales estables para archivado...</p>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        try {
            const resp = await fetch('/api/v1/roadmap/pruning/candidates');
            const data = await resp.json();
            this.renderPruningCandidates(data);
        } catch (err) {
            document.getElementById('pruning-body').innerHTML = `<p class="error">Error: ${err.message}</p>`;
        }
    }

    renderPruningCandidates(candidates) {
        const body = document.getElementById('pruning-body');
        body.classList.remove('loading');

        if (candidates.length === 0) {
            body.innerHTML = `<p class="empty-msg">No hay señales suficientemente estables para proponer archivado táctico.</p>`;
            return;
        }

        body.innerHTML = `
            <div class="pruning-intro">
                OmniWeb propone archivar estas señales del panel activo. 
                Son ruidos técnicos que muestran alta estabilidad y bajo o nulo drift asociado en las últimas ramas. 
                <strong>El archivado no borra la evidencia forense; solo limpia la vista activa.</strong>
            </div>
            
            <div class="pruning-grid">
                ${candidates.map(c => `
                    <div class="pruning-card ${c.archive_permission ? '' : 'is-gated'}">
                        <div class="p-check">
                            <input type="checkbox" class="prune-check" value="${c.signal_id}" 
                                   ${c.archive_permission ? 'checked' : 'disabled'}>
                        </div>
                        <div class="p-info">
                            <div class="p-header-row">
                                <span class="p-branch">${c.branch_name}</span>
                                ${!c.archive_permission ? '<span class="p-gated-badge">🚫 BLOQUEO: RECURRENCIA</span>' : ''}
                                ${c.structural_risk_score > 0.8 ? '<span class="p-structural-badge">⚠️ REVISIÓN ESTRUCTURAL</span>' : ''}
                            </div>
                            <div class="p-reason">${c.archive_reason}</div>
                            <div class="p-metrics">
                                <span class="p-badge stability">ESTABILIDAD: ${Math.round(c.stability_score * 100)}%</span>
                                <span class="p-badge drift ${c.structural_risk_score > 0.5 ? 'warn' : 'ok'}">RIESGO ESTRUCTURAL: ${Math.round(c.structural_risk_score * 100)}%</span>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
            
            <div class="pruning-footer">
                <button class="p-cancel-btn" onclick="document.getElementById('pruning-preview-modal').remove()">CANCELAR</button>
                <button class="p-apply-btn" onclick="window.roadmapUI.applyPruning()">ARCHIVAR SELECCIONADAS</button>
            </div>
        `;
    }

    async applyPruning() {
        const checkboxes = document.querySelectorAll('.prune-check:checked');
        const ids = Array.from(checkboxes).map(cb => cb.value);

        if (ids.length === 0) {
            alert("No hay señales seleccionadas.");
            return;
        }

        try {
            const resp = await fetch('/api/v1/roadmap/pruning/apply', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ signal_ids: ids })
            });
            const res = await resp.json();
            if (res.status === 'success') {
                window.pizarron.showNotification(`Archivado completado: ${res.archived_count} señales movidas al histórico.`, "success");
                document.getElementById('pruning-preview-modal').remove();
                this.viewExceptionsReport(); // Refresh
            }
        } catch (err) {
            alert("Error al archivar: " + err.message);
        }
    }

    async openForensicsReplay(signalId) {
        try {
            const data = await this.callAPI(`/api/v1/roadmap/forensics/${signalId}/replay`);
            this.renderForensicsReplay(data);
        } catch (error) {
            window.pizarron.showNotification('Error al reconstruir historia forense', 'error');
        }
    }

    renderForensicsReplay(data) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay forensics-replay active';

        const trajClass = data.trajectory.toLowerCase();

        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h2>REPLAY FORENSE — GOBERNANZA TÁCTICA</h2>
                    <span class="modal-close" onclick="this.closest('.modal-overlay').remove()">×</span>
                </div>
                
                <div class="replay-summary-box">
                    <div class="s-info">
                        <span class="s-label">TRAYECTORIA:</span>
                        <span class="s-val trajectory-badge ${trajClass}">${data.trajectory}</span>
                    </div>
                    <div class="s-info">
                        <span class="s-label">DEUDA ACTUAL:</span>
                        <span class="s-val">${(data.current_debt * 100).toFixed(1)}%</span>
                    </div>
                    <p class="s-summary">${data.summary}</p>
                </div>

                <div class="forensics-timeline">
                    ${data.events.map((ev, index) => `
                        <div class="timeline-item">
                            <div class="t-line"></div>
                            <div class="t-point"></div>
                            <div class="t-content">
                                <div class="t-header">
                                    <span class="t-type ${ev.event_type.toLowerCase()}">${ev.event_type}</span>
                                    <span class="t-time">${new Date(ev.timestamp).toLocaleString()}</span>
                                </div>
                                <div class="t-body">
                                    <h3>${ev.title}</h3>
                                    <p>${ev.description}</p>
                                    ${ev.link_id ? `<button class="t-link-btn" onclick="window.roadmapUI.openLinkedObject('${ev.link_id}', '${ev.event_type}')">VER DETALLE ➔</button>` : ''}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <div class="modal-footer">
                    <button class="p-cancel-btn" onclick="this.closest('.modal-overlay').remove()">CERRAR</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    openLinkedObject(id, type) {
        window.pizarron.showNotification(`Navegando a ${type}: ${id}...`, 'info');
    }

    async callAPI(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return await response.json();
        } catch (e) {
            console.error("API Error:", e);
            throw e;
        }
    }

    async viewAdvisoryDashboard() {
        const body = document.getElementById('exceptions-body');
        body.innerHTML = '<div class="loading-omni">Sincronizando Cabina Estratégica...</div>';
        try {
            const data = await this.callAPI('/api/v1/roadmap/advisory/dashboard');
            this.renderAdvisoryDashboard(data);
        } catch (err) {
            body.innerHTML = `<p class="error">Error: ${err.message}</p>`;
        }
    }

    renderAdvisoryDashboard(advisories) {
        const body = document.getElementById('exceptions-body');

        body.innerHTML = `
            <div class="advisory-cockpit">
                <div class="cockpit-header">
                    <h2>🎯 CABINA DE ASESORÍA ESTRATÉGICA</h2>
                    <button class="back-btn" onclick="window.roadmapUI.viewExceptionsReport()">← VOLVER AL REPORTE</button>
                </div>
                
                <div class="cockpit-stats">
                    <div class="c-stat">Pendientes: ${advisories.filter(a => a.state === 'PENDING').length}</div>
                    <div class="c-stat">En Proceso: ${advisories.filter(a => a.state === 'ACCEPTED').length}</div>
                    <div class="c-stat">Impacto Confirmado: ${advisories.filter(a => a.state.includes('IMPACT')).length}</div>
                </div>

                <div class="advisory-grid">
                    ${advisories.map(adv => this.renderAdvisoryCard(adv)).join('')}
                </div>
            </div>
        `;
    }

    renderAdvisoryCard(adv) {
        const reductionPct = Math.round(adv.observed_reduction * 100);
        const rebaseItems = adv.rebase_impacts || [];

        return `
            <div class="adv-dashboard-card state-${adv.state.toLowerCase()} risk-${adv.risk.toLowerCase()}">
                <div class="adv-card-header">
                    <span class="adv-state-badge">${adv.state.replace(/_/g, ' ')}</span>
                    <span class="adv-risk-badge">${adv.risk}</span>
                </div>
                
                <div class="adv-body">
                    <h3>${adv.type.replace(/_/g, ' ')}</h3>
                    <div class="adv-pattern">Origen: Patrón ${adv.pattern_id}</div>
                    <div class="adv-domains">Dominios: ${adv.domains.join(', ')}</div>
                    
                    <div class="adv-impact-meter">
                        <div class="meter-label">Impacto Real: ${reductionPct}%</div>
                        <div class="meter-bar">
                            <div class="meter-fill" style="width: ${reductionPct}%"></div>
                        </div>
                    </div>

                    ${rebaseItems.length > 0 ? `
                        <div class="adv-rebase-impacts">
                            <label>MISIONES IMPACTADAS (AUTO-REBASE ADVISOR):</label>
                            ${rebaseItems.map(ri => `
                                <div class="rebase-item state-${ri.recommendation_state.toLowerCase()} ${ri.has_active_override ? 'has-override' : ''}">
                                    <div class="ri-header">
                                        <span class="ri-title">${ri.mission_title || ri.affected_handoff_id}</span>
                                        <span class="ri-type">${ri.mission_type || 'PROPOSAL'}</span>
                                    </div>
                                    <div class="ri-action-glow ${ri.suggested_action.toLowerCase()}">${ri.suggested_action.replace(/_/g, ' ')}</div>
                                    <div class="ri-rationale">"${ri.rationale}"</div>
                                    
                                    ${ri.has_active_override ? `
                                        <div class="ri-debt-lifecycle state-${ri.debt_state.toLowerCase()}">
                                            <div class="dl-row">
                                                <span class="dl-label">ESTADO DEUDA:</span>
                                                <span class="dl-value badge-${ri.debt_state.toLowerCase()}">${ri.debt_state}</span>
                                            </div>
                                            ${ri.review_at ? `
                                                <div class="dl-row">
                                                    <span class="dl-label">REVISIÓN:</span>
                                                    <span class="dl-value">${new Date(ri.review_at).toLocaleString()}</span>
                                                </div>
                                            ` : ''}
                                            ${ri.degradation_score > 0 ? `
                                                <div class="dl-row">
                                                    <span class="dl-label">DEGRADACIÓN:</span>
                                                    <div class="dl-score-bar"><div class="dl-score-fill" style="width:${ri.degradation_score * 100}%"></div></div>
                                                </div>
                                            ` : ''}
                                        </div>
                                    ` : ''}

                                    <div class="ri-controls">
                                        ${ri.recommendation_state === 'PENDING' ? `
                                            <button class="ri-btn preview" onclick="window.roadmapUI.openRebasePreview('${ri.recommendation_id}')">INSPECCIONAR IMPACTO</button>
                                            <button class="ri-btn ignore" onclick="window.roadmapUI.updateRebaseRecommendation('${ri.recommendation_id}', 'IGNORED')">IGNORAR</button>
                                        ` : (ri.has_active_override ? `
                                            <button class="ri-btn review" onclick="window.roadmapUI.promptDebtReview('${ri.recommendation_id}')">REVISAR DEUDA</button>
                                        ` : `
                                            <span class="ri-done-badge">${ri.recommendation_state}</span>
                                        `)}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    <div class="adv-recommendation">
                        <div class="rec-label">RECOMENDACIÓN OMNIWEB</div>
                        <strong>${adv.recommendation}</strong>
                    </div>
                </div>

                <div class="adv-card-footer">
                    ${adv.linked_handoff ? `<button class="view-mission-btn" onclick="window.roadmapUI.openLinkedObject('${adv.linked_handoff}', 'mission')">VER MISIÓN ➔</button>` : `<button class="view-pattern-btn" onclick="window.roadmapUI.viewExceptionsReport()">VER PATRÓN 🔍</button>`}
                </div>
            </div>
        `;
    }

    async updateRebaseRecommendation(id, state) {
        try {
            await fetch(`/api/v1/roadmap/advisory/rebase-recommendations/${id}/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ state: state })
            });

            // Close preview modal if any
            const overlay = document.querySelector('.rebase-preview-overlay');
            if (overlay) overlay.remove();

            window.pizarron.showNotification(`Decisión [${state}] registrada correctamente.`, "success");
            this.viewAdvisoryDashboard(); // Refresh
        } catch (err) {
            alert("Error al actualizar recomendación: " + err.message);
        }
    }

    async processOptionSelection(recId, targetId, risk, optionId) {
        if (optionId === 'CONTINUE_AS_IS' && (risk === 'HIGH' || risk === 'CRITICAL')) {
            this.promptRiskOverride(recId, targetId, risk);
        } else {
            // Normal flow (Review, Rebase, Freeze or Low-Risk Continue)
            const state = optionId === 'CONTINUE_AS_IS' ? 'ACCEPTED' : optionId;
            this.updateRebaseRecommendation(recId, state);
        }
    }

    async promptRiskOverride(recId, targetId, risk) {
        const rationale = prompt(`⚠️ RIESGO ESTRUCTURAL ${risk} DETECTADO.\n\nContinuar sin rebase requiere un RATIONALE EXPLÍCITO para Gobernanza.\n\n¿Por qué es necesario aceptar esta deuda técnica ahora?`, "");

        if (!rationale) {
            alert("No se puede emitir un OVERRIDE sin un motivo consciente.");
            return;
        }

        this.applyRiskOverride(recId, targetId, risk, rationale);
    }

    async promptDebtReview(recId) {
        const decision = prompt("REVISIÓN DE DEUDA TÉCNICA:\n\nEscribe una decisión: RENEW (renovar), CLOSE (cerrar), ESCALATE (escalar)", "RENEW");
        if (!decision) return;
        const normalized = decision.toUpperCase();
        if (!['RENEW', 'CLOSE', 'ESCALATE'].includes(normalized)) {
            alert("Decisión no válida. Usa RENEW, CLOSE o ESCALATE.");
            return;
        }

        const rationale = prompt(`Escribe el RATIONALE para la decisión [${normalized}]:`, "");
        if (!rationale) {
            alert("Se requiere rationale para registrar la revisión.");
            return;
        }

        this.applyDebtReview(recId, normalized, rationale);
    }

    async applyDebtReview(recId, decision, rationale) {
        try {
            await fetch(`/api/v1/roadmap/advisory/risk-override/${recId}/review`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ decision, rationale })
            });

            window.pizarron.showNotification(`Revisión [${decision}] registrada.`, "success");
            this.viewAdvisoryDashboard();
        } catch (e) {
            console.error("Debt review failed", e);
        }
    }

    async applyRiskOverride(recId, targetId, risk, rationale) {
        try {
            const resp = await fetch(`/api/v1/roadmap/advisory/risk-override`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    recommendation_id: recId,
                    target_id: targetId,
                    risk_level: risk,
                    rationale: rationale,
                    override_type: "ACCEPTED_RISK",
                    conditions: "Seguimiento manual requerido"
                })
            });

            if (resp.ok) {
                const overlay = document.querySelector('.rebase-preview-overlay');
                if (overlay) overlay.remove();
                window.pizarron.showNotification("DEUDA ACEPTADA: Override registrado constitucionalmente.", "warning");
                this.viewAdvisoryDashboard();
            } else {
                alert("Error al emitir override de riesgo.");
            }
        } catch (e) {
            console.error("Failed to apply risk override", e);
        }
    }

    async openRebasePreview(recId) {
        try {
            const response = await fetch(`/api/v1/roadmap/advisory/rebase-recommendations/${recId}/preview`);
            const preview = await response.json();
            this.renderRebasePreviewModal(preview);
        } catch (e) {
            console.error("Failed to fetch rebase preview", e);
        }
    }

    renderRebasePreviewModal(p) {
        const existing = document.querySelector('.rebase-preview-overlay');
        if (existing) existing.remove();

        const html = `
            <div class="rebase-preview-overlay" onclick="if(event.target === this) this.remove()">
                <div class="rebase-preview-modal">
                    <div class="rebase-preview-header">
                        <h2>REBASE RECOMMENDATION PREVIEW</h2>
                        <div class="rebase-preview-meta">
                            <span>MISIÓN: <strong>${p.target_title}</strong></span>
                            <span>DOMINIO: <strong style="color:var(--accent)">${p.affected_domain}</strong></span>
                            <span>RIESGO: <strong style="color:${p.current_risk_state === 'CRITICAL' ? '#ff3232' : '#ffaa00'}">${p.current_risk_state}</strong></span>
                        </div>
                    </div>
                    
                    <div class="rebase-preview-content">
                        <div style="font-size: 0.85rem; background: rgba(0,212,255,0.05); padding: 12px; border-radius: 8px; border-left: 4px solid var(--accent); margin-bottom: 20px;">
                            <strong>ANÁLISIS DE IMPACTO:</strong> Esta misión está construida sobre un patrón técnico que ha sido declarado obsoleto o comprometido por la advisory <strong>${p.source_advisory_id}</strong>. Continuar sin revisión puede resultar en una divergencia estructural grave.
                        </div>

                        <div class="rebase-comparison-grid">
                            ${p.options.map(opt => `
                                <div class="preview-option-card ${opt.is_recommended ? 'recommended' : ''}">
                                    <div class="option-header">
                                        <span class="option-title">${opt.label}</span>
                                        <div class="option-metrics">
                                            <span class="metric-pill risk-${opt.risk_level.toLowerCase()}">Riesgo: ${opt.risk_level}</span>
                                        </div>
                                    </div>
                                    
                                    <div class="option-rationale">${opt.rationale}</div>
                                    
                                    <div class="option-footer">
                                        <div class="cost-benefit">
                                            <span class="benefit-label">Beneficio: ${opt.expected_benefit}</span>
                                            <span class="cost-label">Coste: ${opt.tactical_cost}</span>
                                        </div>
                                        <button class="apply-option-btn" onclick="window.roadmapUI.processOptionSelection('${p.recommendation_id}', '${p.target_id}', '${p.current_risk_state}', '${opt.option_id}')">
                                            SELECCIONAR
                                        </button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>

                        <div class="pressure-timeline-container">
                            <div class="timeline-header">
                                <h3 style="font-family:'Outfit'; font-size:1rem; color: #fff;">GOVERNANCE PRESSURE TIMELINE</h3>
                                <span class="trajectory-badge ${p.pressure_timeline.trajectory.toLowerCase()}">${p.pressure_timeline.trajectory.replace(/_/g, ' ')}</span>
                            </div>
                            
                            <div class="pressure-events-list">
                                ${[...p.pressure_timeline.events].reverse().map(e => `
                                    <div class="pressure-event-node">
                                        <div class="event-meta">
                                            ${new Date(e.timestamp).toLocaleString()} — ${e.risk_level}
                                        </div>
                                        <div class="event-info">
                                            <span class="event-type-pill">${e.event_type.replace(/_/g, ' ')}</span>
                                            ${e.rationale}
                                            ${e.creator_decision ? ` <span style="color:var(--accent); font-weight:bold;">[DECISIÓN: ${e.creator_decision}]</span>` : ''}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>

                            <div style="margin-top: 15px; font-size: 0.75rem; color: var(--accent); opacity: 0.8; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px;">
                                📡 <strong>REPORTE OMNIWEB:</strong> ${p.pressure_timeline.summary}
                                <span style="float:right; opacity:0.5;">Presión total: ${p.pressure_timeline.duration_hours.toFixed(1)}h</span>
                            </div>
                        </div>
                    </div>

                    <div class="rebase-preview-footer">
                        <button class="close-preview-btn" onclick="this.closest('.rebase-preview-overlay').remove()">CANCELAR</button>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', html);
    }

    async acceptAdvisory(advisoryId) {
        if (!confirm("¿Deseas convertir esta asesoría en una misión estructural real en el Roadmap?")) return;

        try {
            const resp = await fetch('/api/v1/roadmap/advisory/accept', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ advisory_id: advisoryId })
            });
            const res = await resp.json();
            if (res.status === 'success') {
                window.pizarron.showNotification(`Misión estructural inyectada correctamente.`, "success");
                this.viewExceptionsReport(); // Refresh
            }
        } catch (err) {
            alert("Error al inyectar misión: " + err.message);
        }
    }

    async checkDebtCockpit() {
        try {
            const res = await fetch('/api/v1/governance/debt/cockpit', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            this.debtData = await res.json();
            this.renderDebtCockpit();
        } catch (err) {
            console.warn("Debt cockpit fetch failed", err);
        }
    }

    renderDebtCockpit() {
        const container = document.getElementById('debt-cockpit-container');
        if (!container || !this.debtData) return;

        const { summary, domains } = this.debtData;

        if (summary.total_active_debt === 0) {
            container.innerHTML = '';
            return;
        }

        container.innerHTML = `
            <div class="debt-cockpit-panel animate-fade-in">
                <div class="cockpit-header">
                    <div class="cockpit-title">
                        <span class="icon">⚖️</span>
                        <span>GOVERNANCE DEBT COCKPIT</span>
                    </div>
                </div>

                <div class="cockpit-summary-grid">
                    <div class="summary-pill">
                        <span class="val">${summary.total_active_debt}</span>
                        <label>DEUDA ACTIVA</label>
                    </div>
                    <div class="summary-pill ${summary.overdue_count > 0 ? 'urgent' : ''}">
                        <span class="val">${summary.overdue_count}</span>
                        <label>VENCIDAS</label>
                    </div>
                    <div class="summary-pill ${summary.degraded_count > 0 ? 'urgent' : ''}">
                        <span class="val">${summary.degraded_count}</span>
                        <label>DEGRADADAS</label>
                    </div>
                    <div class="summary-pill">
                        <span class="val">${summary.review_due_count}</span>
                        <label>POR REVISAR</label>
                    </div>
                    <div class="summary-pill">
                        <span class="val">${summary.critical_risk_count}</span>
                        <label>RIESGO CRÍTICO</label>
                    </div>
                </div>

                <div class="debt-domains-grid">
                    ${domains.map(dom => `
                        <div class="domain-debt-card status-${dom.status}">
                            <div class="domain-header">
                                <span class="domain-name">${dom.name.toUpperCase()}</span>
                                <span class="domain-burden">CARGA: ${dom.risk_burden.toFixed(1)}</span>
                            </div>
                            <div class="ov-list">
                                ${dom.overrides.map(ov => `
                                    <div class="ov-item lvl-${ov.risk_level}">
                                        <div class="ov-rationale">${ov.rationale}</div>
                                        <div class="ov-meta">
                                            <span class="ov-status-badge state-${ov.debt_state}">${ov.debt_state.replace('_', ' ')}</span>
                                            <span class="ov-target">${ov.target_id.split('-')[0]}</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>

                ${summary.intervention_required.length > 0 ? `
                    <div class="intervention-alerts">
                        <div class="intervention-title">⚠️ INTERVENCIONES REQUERIDAS</div>
                        ${summary.intervention_required.map(alert => `
                            <div class="alert-item lvl-${alert.level}">
                                <div class="alert-info">
                                    <div class="alert-reason">${alert.reason}</div>
                                    <div class="alert-target">TARGET: ${alert.target} | PRÓXIMA ACCIÓN: ${alert.next_step}</div>
                                </div>
                                <button class="ws-btn-mini" style="background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.2); color: #fff;" onclick="window.creatorEnv.openWorkspace('mission')">REVISAR</button>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
}

window.roadmapUI = new RoadmapUI();
