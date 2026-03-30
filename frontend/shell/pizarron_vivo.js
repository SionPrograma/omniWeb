
class PizarronVivoUI {
    constructor() {
        this.id = 'pizarron-vivo-embedded';
    }

    /**
     * Renders the mission dashboard into a specific DOM element.
     * @param {HTMLElement} container - The container where the dashboard will be mounted.
     * @param {Object} data - The mission state data (active_mission).
     */
    renderInto(container, data) {
        if (!container) return;

        const mission = data.mission || data.active_mission || null;

        if (!mission || (mission.status === 'IDLE' || !mission.active_goal)) {
            container.innerHTML = `
                <div class="pizarron-card pizarron-empty-state">
                    <h3 style="color: var(--pizarron-accent); font-family: 'Outfit';">SIN MISIÓN ACTIVA</h3>
                    <p style="font-size: 0.85rem; margin-top: 10px; opacity: 0.6;">
                        OmniWeb está en espera. Inicia una operación técnica para visualizar el dashboard cognitivo aquí.
                    </p>
                </div>
            `;
            return;
        }

        // Mapping real MissionState to UI structure
        const summary = mission.active_goal || "Misión del Sistema";
        const mission_id = mission.mission_id || "N/A";
        const primary_layer = (mission.related_targets && mission.related_targets.length > 0) ? mission.related_targets.join(', ') : 'core-ai-host';
        const microtasks = (mission.completed_steps || []).map(s => `[DONE] ${s}`).concat(mission.pending_steps || []);
        const forbidden_zones = mission.blocked_reasons || [];
        const risk_level = (forbidden_zones.length > 0) ? "BLOQUEADO" : "NOMINAL";

        const maturity = mission.status === 'COMPLETED' ? 'READY' :
            (mission.status === 'PAUSED' ? 'SUPERVISED' :
                (mission.status === 'BLOCKED' ? 'ESCALATE' : 'OPEN'));

        const badgeClass = maturity === 'READY' ? 'badge-ready' :
            (maturity === 'SUPERVISED' ? 'badge-supervised' :
                (maturity === 'ESCALATE' ? 'badge-escalate' : 'badge-ready'));

        const rationale = mission.updated_at ? `Última actualización: ${new Date(mission.updated_at).toLocaleTimeString()}` : "Sincronizado con MissionState";

        container.innerHTML = `
            <div class="pizarron-grid">
                <!-- Mission & Policy -->
                <section class="pizarron-card" style="grid-column: span 2;">
                    <h4><span style="color: var(--pizarron-accent)">⚛</span> Dashboard Cognitivo: ${mission.status}</h4>
                    <div class="pizarron-mission">${summary}</div>
                    <div style="margin-top: 15px; display: flex; gap: 20px; align-items: center; flex-wrap: wrap;">
                        <div class="pizarron-badge ${badgeClass}">${maturity}</div>
                        <div style="font-size: 0.75rem; opacity: 0.8;">Action: <b>${mission.status}</b></div>
                        <div style="font-size: 0.7rem; opacity: 0.5;">ID: <code>${mission_id}</code></div>
                    </div>
                </section>

                <!-- Layers & Dependencies -->
                <section class="pizarron-card">
                    <h4><span style="color: var(--pizarron-accent)">📂</span> Capas Relacionadas</h4>
                    <div style="margin-bottom: 10px;">
                        <span style="font-size: 0.7rem; opacity: 0.6; display: block; margin-bottom: 5px;">TARGETS</span>
                        <div class="pizarron-layers-node" style="border: 1px solid var(--pizarron-accent); color: #fff; font-size: 0.7rem;">${primary_layer}</div>
                    </div>
                    <div class="pizarron-benefit" style="font-size: 0.7rem; line-height: 1.3;">
                        Aislamiento de superficie activo para control de efectos colaterales.
                    </div>
                </section>

                <!-- Microtasks (Plan) -->
                <section class="pizarron-card" style="grid-row: span 2;">
                    <h4><span style="color: var(--pizarron-accent)">⚡</span> Plan de Misión</h4>
                    <div class="pizarron-microtasks">
                        <ul style="list-style: none; padding: 0;">
                            ${microtasks.map(t => {
            const isDone = t.startsWith('[DONE]');
            return `<li style="margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.75rem; ${isDone ? 'opacity: 0.4; text-decoration: line-through;' : ''}">
                                    ${t.replace('[DONE] ', '')}
                                </li>`;
        }).join('')}
                            ${microtasks.length === 0 ? '<li style="opacity: 0.5; font-size: 0.75rem;">Sin pasos definidos.</li>' : ''}
                        </ul>
                    </div>
                </section>

                <!-- Risk & Status -->
                <section class="pizarron-card">
                    <h4><span style="color: var(--pizarron-critical)">🛡</span> Integridad</h4>
                    <div>
                        <span style="font-size: 0.7rem; opacity: 0.6; display: block; margin-bottom: 5px;">RIESGO: ${risk_level}</span>
                        ${forbidden_zones.length > 0 ?
                forbidden_zones.map(z => `<div style="font-size: 0.7rem; color: var(--pizarron-critical); background: rgba(255,0,0,0.1); padding: 6px; border-radius: 4px; border: 1px solid rgba(255,0,0,0.2); margin-top: 5px;">⚠ ${z}</div>`).join('')
                : `<p style="font-size: 0.75rem; color: var(--pizarron-safe);">Sin bloqueos activos.</p>`
            }
                    </div>
                    <div style="margin-top: 10px; font-size: 0.65rem; opacity: 0.4;">
                        ${rationale}
                    </div>
                </section>
            </div>
        `;
    }
}

// Global exposure
window.pizarronUI = new PizarronVivoUI();
