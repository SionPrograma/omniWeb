import sys
import os

def fix_main_new():
    file_path = 'frontend/shell/main_new.js'
    # Read as UTF-16
    with open(file_path, 'r', encoding='utf-16') as f:
        content = f.read()
    
    # Sane marker for Fusion
    marker = '/* --- GOVERNANCE FUSION (Unidad 105) --- */'
    if marker not in content:
        print("Marker not found, fallback to renderGovernanceFusion")
        marker = 'async function renderGovernanceFusion('
    
    parts = content.split(marker)
    header = parts[0]
    
    # Reconstruct the remaining 5 functions
    reconstructed = marker + """
    async function renderGovernanceFusion(containerId, targetId, targetType = 'MISSION') {
        const container = document.getElementById(containerId);
        if (!container) return;

        try {
            const res = await fetch(`/api/v1/governance/fusion/${targetId}?target_type=${targetType}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            if (!res.ok) return;

            const snapshot = await res.json();
            const traces = snapshot.traces || [];
            let traceHtml = traces.map(t => `
                <div class="fusion-trace-item">
                    <div class="fusion-trace-header">
                        <span class="fusion-trace-id">[#${t.trace_id}]</span>
                        <span class="fusion-trace-date">${new Date(t.applied_at).toLocaleTimeString()}</span>
                    </div>
                    <div class="fusion-trace-action">${t.creator_action.replace(/_/g, ' ')}</div>
                    <div class="fusion-trace-outcome outcome-${t.outcome_status.toLowerCase()}">${t.outcome_status.replace(/_/g, ' ')}</div>
                </div>
            `).join('');

            container.innerHTML = `
                <div class="governance-fusion-card">
                    <div class="fusion-title">GOVERNANCE FUSION STATUS</div>
                    <div class="fusion-stats-grid">
                        <div class="fusion-stat-item"><span>FRICTION:</span> ${snapshot.friction_score}</div>
                        <div class="fusion-stat-item"><span>RISK:</span> ${snapshot.risk_level}</div>
                        <div class="fusion-stat-item"><span>BASE:</span> ${snapshot.advisory_state}</div>
                    </div>
                    <div class="fusion-traces-list">
                        ${traceHtml || '<div style="opacity:0.5; font-size:0.8rem;">No historical traces found.</div>'}
                    </div>
                    <div class="fusion-action-row">
                        <button class="fusion-btn primary" onclick="window.omniHandleFusionAction('${snapshot.next_action}', '${targetId}', '${targetType}')">
                            ${snapshot.next_action.replace(/_/g, ' ')}
                        </button>
                    </div>
                </div>
            `;
        } catch (err) {
            console.error("Fusion render failed", err);
        }
    }
    window.omniRenderFusion = renderGovernanceFusion;

    window.omniHandleFusionAction = function (action, targetId, targetType) {
        console.log("Fusion Action:", action, targetId);
        if (action === 'OPEN_REBASE_PREVIEW' || action === 'OPEN_REBASE_ADVISOR') {
            if (window.roadmapUI) window.roadmapUI.adjustPlan(targetId);
        } else if (action === 'OPEN_DEBT_COCKPIT' || action === 'REVIEW_DEBT') {
            if (window.roadmapUI) {
                window.roadmapUI.checkDebtCockpit();
            } else {
                window.omniShell.addInput('governance: check_debt');
            }
        } else if (action === 'INSPECT_TIMELINE') {
            window.omniShell.addInput(`governance: inspect_timeline ${targetId}`);
        } else if (action === 'FREEZE_UNTIL_RECOVERY') {
            window.omniShell.addInput(`mission: freeze ${targetId} --reason "Compromiso estructural detectado via Fusion"`);
        } else {
            window.omniShell.addInput(`inspect ${targetType.toLowerCase()} ${targetId}`);
        }

        if (action.includes('DEBT') || action.includes('PREVIEW') || action.includes('TIMELINE') || action.includes('COCKPIT')) {
            window.omniShell.switchView('workspace');
        }
    };

    /* FORENSIC DECISION COCKPIT (Unidad 109) */
    async function renderForensicCockpit() {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) return;

        mainContent.innerHTML = `<div class="forensic-cockpit-container"><h1 style="color:var(--accent); font-family: Outfit; letter-spacing: 2px;">AUDITANDO HISTORIAL FORENSE...</h1></div>`;

        try {
            const res = await fetch(`/api/v1/governance/forensic/cockpit`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            const payload = data.payload;
            const summary = payload.summary;

            let traceRows = payload.traces.map(t => {
                const outcomeClass = t.outcome_status.toLowerCase().replace(/_/g, '-');
                const appliedStr = t.applied_at ? new Date(t.applied_at).toLocaleString() : 'N/A';
                return `
                    <tr class="forensic-trace-row" onclick="window.omniShell.addInput('inspect mission ${t.target_id}'); window.omniShell.switchView('workspace');">
                        <td class="trace-cell-id">#${t.trace_id}</td>
                        <td class="trace-cell-domain">${t.target_domain}</td>
                        <td class="trace-cell-action">${t.creator_action.replace(/_/g, ' ')}</td>
                        <td><span class="outcome-badge outcome-${outcomeClass}">${t.outcome_status.replace(/_/g, ' ')}</span></td>
                        <td class="trace-cell-rationale">${t.rationale_summary || ''}</td>
                        <td class="trace-cell-date">${appliedStr}</td>
                    </tr>
                `;
            }).join('');

            let hotspotsHtml = Object.entries(summary.hotspots).map(([dom, count]) => `
                <div class="hotspot-pill">
                    <span>${dom}</span>
                    <span class="hotspot-count">${count}</span>
                </div>
            `).join('') || '<div class="hotspot-pill">Sin fricción detectada</div>';

            let insightsHtml = payload.insights.map(ins => `<div class="insight-item">${ins}</div>`).join('');

            mainContent.innerHTML = `
                <div class="forensic-cockpit-container">
                    <div class="forensic-header">
                        <div>
                            <h1>CABINA FORENSE DE DECISIONES</h1>
                            <div class="forensic-description">Auditoría global de efectividad estructural: Convirtiendo decisiones del Creador en aprendizaje sistémico.</div>
                        </div>
                    </div>

                    <div class="forensic-summary-row">
                        <div class="forensic-card">
                            <div class="card-label">Decisiones Totales</div>
                            <div class="card-value">${summary.total_decisions}</div>
                            <div class="card-sub">Capturadas en este roadmap</div>
                        </div>
                        <div class="forensic-card">
                            <div class="card-label">Efectividad</div>
                            <div class="card-value text-effective">${summary.outcomes.EFFECTIVE}</div>
                            <div class="card-sub">Alivio estructural confirmado</div>
                        </div>
                        <div class="forensic-card">
                            <div class="card-label">Degradación Post-Acción</div>
                            <div class="card-value text-degraded">${summary.outcomes.DEGRADED}</div>
                            <div class="card-sub">Intervenciones ineficaces</div>
                        </div>
                        <div class="forensic-card">
                            <div class="card-label">Evaluaciones Pendientes</div>
                            <div class="card-value text-pending">${summary.outcomes.PENDING}</div>
                            <div class="card-sub">Esperando señal operativa</div>
                        </div>
                    </div>

                    ${insightsHtml ? `
                    <div class="forensic-insights-box">
                        <div class="card-label" style="color:var(--accent)">Análisis de Patrones</div>
                        <div class="insights-list">${insightsHtml}</div>
                    </div>` : ''}

                    <div>
                        <div class="card-label">Hotspots de Fricción Forense (Degradación por Dominio)</div>
                        <div class="forensic-hotspots">${hotspotsHtml}</div>
                    </div>

                    <div style="margin-top: 1rem;">
                        <div class="forensic-list-header">HISTORIAL FORENSE DETALLADO</div>
                        <div style="overflow-x: auto;">
                            <table class="forensic-trace-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Dominio</th>
                                        <th>Acción</th>
                                        <th>Resultado</th>
                                        <th>Resumen Forense</th>
                                        <th>Fecha</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${traceRows || '<tr><td colspan="6" style="text-align:center; padding: 2rem;">No hay trazas forenses registradas aún.</td></tr>'}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            `;
        } catch (err) {
            console.error(err);
            mainContent.innerHTML = `<div class="forensic-cockpit-container"><h1>ERROR AL CARGAR DASHBOARD FORENSE</h1></div>`;
        }
    }
    window.omniRenderForensicCockpit = renderForensicCockpit;

    /* FRICTION HEATMAP (Unidad 111) */
    async function renderFrictionHeatmap() {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) return;

        mainContent.innerHTML = `<div class="heatmap-container"><h1 style="color:var(--accent); font-family: Outfit; letter-spacing: 2px;">CALCULANDO FRICCIÓN ESTRUCTURAL...</h1></div>`;

        try {
            const res = await fetch(`/api/v1/governance/forensic/heatmap`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            const nodes = data.payload || [];

            let nodesHtml = await Promise.all(nodes.map(async (n) => {
                const bandClass = `band-${n.severity_band.toLowerCase()}`;
                const signals = n.signals;

                // Fetch associated relief proposals
                let reliefHtml = '';
                let statusBadgeHtml = '';
                try {
                    const rRes = await fetch(`/api/v1/governance/forensic/relief/proposals?domain=${n.domain}`, {
                        headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
                    });
                    const rData = await rRes.json();
                    if (rData.payload && rData.payload.length > 0) {
                        const p = rData.payload[0];
                        if (p.status === 'PENDING') {
                            reliefHtml = `
                            <div class="relief-available-badge" onclick="event.stopPropagation(); window.omniRenderReliefPreview('${p.proposal_id}')">
                                🛡️ ALIVIO DISPONIBLE
                            </div>
                            `;
                        } else if (p.status === 'ACCEPTED') {
                            const outcomeEmoji = {
                                'EFFECTIVE_RELIEF': '✅',
                                'PARTIAL_RELIEF': '📈',
                                'NO_VISIBLE_RELIEF': '⏸️',
                                'RELIEF_INEFFECTIVE': '❌',
                                'RESISTANT_HOTSPOT': '🔥',
                                'ESCALATING_DESPITE_RELIEF': '⚠️',
                                'UNDER_OBSERVATION': '🕒',
                                'RELIEF_PENDING': '🕒'
                            }[p.relief_outcome] || '🛡️';

                            statusBadgeHtml = `
                            <div class="stabilization-status-badge ${p.relief_outcome ? p.relief_outcome.toLowerCase() : ''}" onclick="event.stopPropagation(); window.omniRenderReliefPreview('${p.proposal_id}')">
                                <div style="display:flex; align-items:center; gap:5px;">
                                    <span>${outcomeEmoji}</span>
                                    <span>${p.relief_outcome ? p.relief_outcome.replace(/_/g, ' ') : 'STABILIZING'}</span>
                                </div>
                                ${p.baseline_friction_score > 0 ? `<div class="relief-delta">Baseline: ${p.baseline_friction_score.toFixed(0)} pts</div>` : ''}
                            </div>
                           `;
                        }
                    }
                } catch (e) { }

                // Audit Badge logic
                let auditBadgeHtml = '';
                if (n.audit_status === 'ROOT_CAUSE_AUDIT_SUGGESTED') {
                    auditBadgeHtml = `
                    <div class="root-audit-badge" onclick="event.stopPropagation(); window.omniShowRootAuditProposal('${n.domain}')">
                        🔍 SUGGEST AUDIT
                    </div>
                    `;
                } else if (n.audit_status === 'UNDER_FORENSIC_AUDIT') {
                    auditBadgeHtml = `
                    <div class="root-audit-badge under-audit">
                        🔬 AUDIT ACTIVE
                    </div>
                    `;
                }

                return `
                <div class="heatmap-node ${bandClass} ${statusBadgeHtml ? 'under-relief' : ''} ${n.audit_status === 'UNDER_FORENSIC_AUDIT' ? 'under-audit' : ''}" onclick="window.omniShell.addInput('governance: check_debt ${n.domain}'); window.omniShell.switchView('workspace');">
                    <div class="node-severity-indicator"></div>
                    ${reliefHtml}
                    ${statusBadgeHtml}
                    ${auditBadgeHtml}
                    <div class="node-header">
                        <span class="node-domain">${n.domain}</span>
                        <span class="node-score">${n.friction_score.toFixed(0)}</span>
                    </div>
                    <div class="node-rationale">${n.rationale}</div>
                    <div class="node-signals">
                        ${signals.debt_count > 0 ? `<span class="signal-pill">Deuda: ${signals.debt_count}</span>` : ''}
                        ${signals.advisory_count > 0 ? `<span class="signal-pill">Avisos: ${signals.advisory_count}</span>` : ''}
                        ${signals.degraded_traces > 0 ? `<span class="signal-pill">Fallos: ${signals.degraded_traces}</span>` : ''}
                        ${signals.avg_delta !== 0 ? `<span class="signal-pill">Impacto: ${signals.avg_delta > 0 ? '+' : ''}${signals.avg_delta}</span>` : ''}
                    </div>
                    <div class="node-actions">
                        <span class="action-label">${n.recommended_action.replace(/_/g, ' ')}</span>
                        <span class="node-footer-meta">${n.last_updated ? new Date(n.last_updated).toLocaleTimeString() : 'N/A'}</span>
                    </div>
                </div>
                `;
            }));

            mainContent.innerHTML = `
                <div class="heatmap-container">
                    <div class="heatmap-header" style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h2>MAPA DE FRICCIÓN ESTRUCTURAL</h2>
                            <div class="forensic-description">Priorización espacial de riesgo: Consolidando deuda, presión y efectividad forense.</div>
                        </div>
                        <button class="btn-apply" style="width: auto; margin: 0; padding: 10px 20px; background: var(--accent); color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.4);"
                            onclick="creatorEnv.generateFrictionRelief()">SCAN & GENERATE RELIEF</button>
                    </div>
                    <div class="heatmap-grid">
                        ${nodesHtml.join('') || '<div style="grid-column: 1/-1; text-align: center; padding: 3rem; opacity: 0.5;">No hay señales de fricción registradas. El sistema está nominal.</div>'}
                    </div>
                </div>
            `;
        } catch (err) {
            console.error(err);
            mainContent.innerHTML = `<div class="heatmap-container"><h1>ERROR AL CARGAR MAPA DE CALOR</h1></div>`;
        }
    }
    window.omniRenderFrictionHeatmap = renderFrictionHeatmap;

    window.omniShowRootAuditProposal = async function(domain) {
        try {
            const res = await fetch(`/api/v1/governance/forensic/audit/proposals?domain=${domain}`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            if(!data.payload || data.payload.length === 0) {
                const scanRes = await fetch(`/api/v1/governance/forensic/audit/needs`, {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
                });
                const scanData = await scanRes.json();
                const proposal = scanData.payload.find(p => p.source_heatmap_node === domain);
                if(proposal) {
                   renderAuditModal(proposal);
                } else {
                   alert("No se requiere auditoría profunda para este dominio por el momento.");
                }
            } else {
                renderAuditModal(data.payload[0]);
            }
        } catch(e) { console.error(e); }
    };

    function renderAuditModal(p) {
        const modal = document.createElement('div');
        modal.className = 'governance-modal-overlay';
        modal.style = "position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); display:flex; align-items:center; justify-content:center; z-index:10000; backdrop-filter:blur(10px); font-family:'Inter', sans-serif;";
        
        modal.innerHTML = `
            <div class="governance-modal" style="background:#111; border:1px solid #ff3366; width:600px; padding:30px; border-radius:15px; box-shadow: 0 0 50px rgba(255, 51, 102, 0.3);">
                <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px;">
                    <div>
                        <h2 style="color:#ff3366; margin:0; letter-spacing:1px; font-family:'Outfit';">🔬 FORENSIC ROOT CAUSE AUDIT</h2>
                        <div style="font-size:0.8rem; opacity:0.6; margin-top:5px;">TRIGGER: Structural Resistance Detected in <b>${p.source_heatmap_node}</b></div>
                    </div>
                    <div style="background:rgba(255,51,102,0.1); padding:10px; border-radius:8px; text-align:center; border:1px solid rgba(255,51,102,0.3);">
                        <div style="font-size:0.6rem; opacity:0.6;">CONFIDENCE</div>
                        <div style="font-size:1.2rem; font-weight:800; color:#ff3366;">${(p.confidence * 100).toFixed(0)}%</div>
                    </div>
                </div>

                <div style="background:rgba(255,255,255,0.05); padding:20px; border-radius:10px; margin-bottom:20px; border-left:4px solid #ff3366;">
                    <div style="font-size:0.7rem; color:#ff3366; font-weight:800; text-transform:uppercase; margin-bottom:5px;">Rationale</div>
                    <div style="font-size:0.95rem; line-height:1.5;">${p.rationale}</div>
                    <div style="margin-top:10px; font-size:0.8rem; opacity:0.7;">
                        <b>Evidencia:</b> ${p.repeated_failure_count} misiones de alivio previas no lograron estabilizar el dominio.
                    </div>
                </div>

                <div style="margin-bottom:20px;">
                    <div style="font-size:0.7rem; color:#aaa; font-weight:800; text-transform:uppercase; margin-bottom:5px;">Proposed Audit Scope</div>
                    <div style="font-size:0.85rem; background:rgba(0,0,0,0.3); padding:10px; border-radius:5px; border:1px solid rgba(255,255,255,0.1);">
                        ${p.proposed_scope}
                    </div>
                </div>

                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                    <button class="btn-decision-accept" style="background:#ff3366; color:black; font-weight:800; border:none; padding:12px; border-radius:5px; cursor:pointer;">ACCEPT & INVESTIGATE</button>
                    <button class="btn-decision-postpone" style="background:rgba(255,255,255,0.1); color:white; border:none; padding:12px; border-radius:5px; cursor:pointer;">POSTPONE</button>
                    <button class="btn-decision-reject" style="grid-column: 1 / -1; background:transparent; color:#ff3366; border:1px solid #ff3366; padding:10px; border-radius:5px; margin-top:5px; cursor:pointer; font-size:0.8rem;">REJECT AUDIT (STAY TACTICAL)</button>
                </div>
            </div>
        `;

        modal.querySelector('.btn-decision-accept').onclick = async () => {
             const res = await fetch(`/api/v1/governance/forensic/audit/proposals/${p.audit_id}/decision?decision=ACCEPT`, { method: 'POST', headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` } });
            if((await res.json()).status === 'success') {
                modal.remove();
                window.omniRenderFrictionHeatmap();
            }
        };

        modal.querySelector('.btn-decision-postpone').onclick = () => modal.remove();
        modal.querySelector('.btn-decision-reject').onclick = async () => {
             await fetch(`/api/v1/governance/forensic/audit/proposals/${p.audit_id}/decision?decision=REJECT`, { method: 'POST', headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` } });
             modal.remove();
             window.omniRenderFrictionHeatmap();
        };

        document.body.appendChild(modal);
    }
});
"""

    with open('frontend/shell/main_new_fixed.js', 'w', encoding='utf-16') as f:
        f.write(header + reconstructed)
    
    # Overwrite original
    os.replace('frontend/shell/main_new_fixed.js', file_path)
    print("Misión de restauración: main_new.js reparada y conectada.")

if __name__ == "__main__":
    fix_main_new()
