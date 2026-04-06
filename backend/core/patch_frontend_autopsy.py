import codecs
import os

def patch_frontend():
    file_path = 'frontend/shell/main_new.js'
    with codecs.open(file_path, 'r', 'utf-16') as f:
        content = f.read()

    # 1. Update renderForensicCockpit to include Autopsies
    old_code = """        mainContent.innerHTML = `<div class="forensic-cockpit-container"><h1 style="color:var(--accent); font-family: Outfit; letter-spacing: 2px;">AUDITANDO HISTORIAL FORENSE...</h1></div>`;"""
    
    # We will replace the whole function body or a large part of it to include the fetch
    
    start_tag = 'async function renderForensicCockpit() {'
    end_tag = 'window.omniRenderForensicCockpit = renderForensicCockpit;'
    
    autopsy_logic = """
    async function renderForensicCockpit() {
        const mainContent = document.getElementById('main-content');
        if (!mainContent) return;

        mainContent.innerHTML = `<div class="forensic-cockpit-container"><h1 style="color:var(--accent); font-family: Outfit; letter-spacing: 2px;">AUDITANDO HISTORIAL FORENSE...</h1></div>`;

        try {
            const [tracesRes, autopsiesRes] = await Promise.all([
                fetch('/api/v1/governance/traces'),
                fetch('/api/v1/governance/forensic/autopsy')
            ]);
            
            const tracesData = await tracesRes.json();
            const autopsiesData = await autopsiesRes.json();
            
            const traces = tracesData.payload || [];
            const autopsies = autopsiesData.payload || [];

            // Calculate stats
            const effective = traces.filter(t => t.outcome === 'EFFECTIVE_RELIEF').length;
            const resistant = traces.filter(t => t.outcome === 'RESISTANT_HOTSPOT').length;

            let html = `
            <div class="forensic-cockpit-container">
                <div class="forensic-header">
                    <div>
                        <h1>STRATEGIC GOVERNANCE COCKPIT</h1>
                        <p class="forensic-description">Análisis de efectividad de alivio, resistencia estructural y autopsias de experimentos tácticos.</p>
                    </div>
                </div>

                <div class="forensic-summary-row">
                    <div class="forensic-card">
                        <div class="card-label">Intervenciones Totales</div>
                        <div class="card-value">${traces.length}</div>
                        <div class="card-sub">Traces registrados</div>
                    </div>
                    <div class="forensic-card">
                        <div class="card-label">Efectividad Alivio</div>
                        <div class="card-value text-effective">${Math.round((effective/Math.max(1, traces.length))*100)}%</div>
                        <div class="card-sub">${effective} misiones con éxito</div>
                    </div>
                    <div class="forensic-card">
                        <div class="card-label">Resistencia Crítica</div>
                        <div class="card-value text-degraded">${resistant}</div>
                        <div class="card-sub">Hotspots persistentes</div>
                    </div>
                </div>

                <div class="forensic-list-header">ÚLTIMOS EVENTOS FORENSES</div>
                <table class="forensic-trace-table">
                    <thead>
                        <tr>
                            <th>TRACE ID</th>
                            <th>DOMINIO</th>
                            <th>ACCIÓN</th>
                            <th>OUTCOME</th>
                            <th>RATIONALE / INSIGHT</th>
                            <th>FECHA</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${traces.slice(0, 10).map(t => `
                            <tr class="forensic-trace-row">
                                <td class="trace-cell-id">${t.trace_id.slice(0,8)}</td>
                                <td class="trace-cell-domain">${t.target_domain}</td>
                                <td class="trace-cell-action">${t.action_type}</td>
                                <td><span class="outcome-badge outcome-${t.outcome === 'EFFECTIVE_RELIEF' ? 'effective' : (t.outcome === 'RESISTANT_HOTSPOT' ? 'degraded' : 'pending')}">${t.outcome}</span></td>
                                <td class="trace-cell-rationale">${t.rationale}</td>
                                <td class="trace-cell-date">${new Date(t.timestamp).toLocaleString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>

                <div class="autopsy-section">
                    <div class="forensic-list-header">AUTOPSIAS FORENSES DE RAMAS (EXPERIMENTOS)</div>
                    <div class="autopsy-grid">
                        ${autopsies.length === 0 ? '<p style="color:var(--text-muted)">No hay autopsias completadas aún.</p>' : 
                        autopsies.map(a => `
                            <div class="autopsy-card" onclick="window.omniShowAutopsy('${a.autopsy_id}')">
                                <span class="autopsy-badge badge-${a.final_branch_outcome.toLowerCase()}">${a.final_branch_outcome}</span>
                                <div class="autopsy-title">${a.branch_goal_summary}</div>
                                <div class="autopsy-meta">Branch: ${a.branch_id} | ${new Date(a.created_at).toLocaleDateString()}</div>
                                <div class="autopsy-summary"><strong>Hallazgo Principal:</strong> ${a.structural_findings[0] || 'Nominal.'}</div>
                                <div class="autopsy-stats">
                                    <div class="stat-item"><span class="stat-val">${a.affected_domains.length}</span>Dominios</div>
                                    <div class="stat-item"><span class="stat-val">${Math.round(a.confidence * 100)}%</span>Confianza</div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>`;

            mainContent.innerHTML = html;

            // Global modal for detailed autopsy
            window.omniShowAutopsy = async (autopsyId) => {
                const autopsy = autopsies.find(a => a.autopsy_id === autopsyId);
                if (!autopsy) return;

                const modal = document.createElement('div');
                modal.className = 'governance-modal';
                modal.style.display = 'flex';
                modal.innerHTML = `
                    <div class="governance-modal-content" style="max-width: 800px; border-left: 8px solid var(--accent);">
                        <h2 style="font-family: Outfit; color: var(--accent);">AUTOPSIA FORENSE: ${autopsy.branch_id}</h2>
                        <div class="modal-body">
                            <div style="margin-bottom: 2rem; padding: 1rem; background: rgba(255,255,255,0.05); border-radius: 8px;">
                                <h3 style="font-size: 0.9rem; color: var(--text-muted); text-transform: uppercase;">Lecciones Aprendidas</h3>
                                <ul style="margin-top: 0.5rem; color: var(--text-primary);">
                                    ${autopsy.lessons_learned.map(l => `<li>${l}</li>`).join('')}
                                </ul>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                                <div>
                                    <h4 style="font-size: 0.8rem; color: var(--text-muted);">Hallazgos Estructurales</h4>
                                    <p style="font-size: 0.9rem;">${autopsy.structural_findings.join('<br>')}</p>
                                </div>
                                <div>
                                    <h4 style="font-size: 0.8rem; color: var(--text-muted);">Seguimiento Recomendado</h4>
                                    <p style="font-size: 0.9rem; color: var(--accent);">${autopsy.recommended_followup.join('<br>')}</p>
                                </div>
                            </div>

                            <div style="margin-top: 2rem;">
                                <h4 style="font-size: 0.8rem; color: var(--text-muted);">Hotspots Detectados en Rama</h4>
                                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;">
                                    ${autopsy.hotspot_history.map(h => `<span class="hotspot-pill">${h.domain} <i style="color:var(--accent)">${h.outcome}</i></span>`).join('')}
                                </div>
                            </div>
                        </div>
                        <div class="modal-actions" style="margin-top: 2.5rem; border-top: 1px solid var(--border-subtle); padding-top: 1rem;">
                            <button onclick="this.closest('.governance-modal').remove()" style="background: var(--bg-tertiary); border: 1px solid var(--accent); color: var(--accent); padding: 0.75rem 2rem; border-radius: 4px; cursor: pointer;">CERRAR AUTOPSIA</button>
                        </div>
                    </div>
                `;
                document.body.appendChild(modal);
            };

        } catch (err) {
            console.error(err);
            mainContent.innerHTML = `<div class="forensic-cockpit-container"><h1>ERROR AL CARGAR DASHBOARD FORENSE</h1></div>`;
        }
    }
    """

    # Direct replacement of the function
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)
    
    if start_idx != -1 and end_idx != -1:
        new_content = content[:start_idx] + autopsy_logic + content[end_idx:]
        with codecs.open(file_path, 'w', 'utf-16') as f:
            f.write(new_content)
        print("Frontend patched successfully.")
    else:
        print(f"Marker not found: {start_idx}, {end_idx}")

if __name__ == "__main__":
    patch_frontend()
