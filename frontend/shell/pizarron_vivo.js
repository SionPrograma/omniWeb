
class PizarronVivoUI {
    constructor() {
        this.overlay = null;
        this.id = 'pizarron-vivo-overlay';
        this._injectHTML();
    }

    _injectHTML() {
        if (document.getElementById(this.id)) return;

        const overlay = document.createElement('div');
        overlay.id = this.id;
        overlay.className = 'pizarron-overlay';
        overlay.innerHTML = `
            <div class="pizarron-header">
                <div>
                    <h2>PIZARRÓN VIVO</h2>
                    <span style="font-size: 0.65rem; opacity: 0.5; letter-spacing: 1px;">ARCHITECTURE INTELLIGENCE BOARD</span>
                </div>
                <button class="pizarron-close-btn" id="pizarron-close">CERRAR INTERFAZ</button>
            </div>
            <div class="pizarron-grid" id="pizarron-content">
                <!-- Dynamic Content Here -->
            </div>
            <div style="margin-top: 20px; text-align: right; opacity: 0.3; font-size: 0.6rem;">
                OmniWeb AI Host Core | Block 13.1 | Manual Apply Loop Ritual
            </div>
        `;
        document.body.appendChild(overlay);
        this.overlay = overlay;

        document.getElementById('pizarron-close').onclick = () => this.hide();
    }

    show(data) {
        // Sanitizar data para evitar crashes por shape incompleto
        if (!data) {
            console.warn("[PIZARRÓN] No hay datos disponibles.");
            return;
        }

        // Si falta task_tree pero hay sombras, crear un task_tree mínimo sintético
        if (!data.task_tree && (data.shadows || data.constructors)) {
            data.task_tree = {
                summary: data.goal || "Misión del Swarm de Sombras",
                mission_id: data.swarm_id || "swarm_gen",
                primary_layer: "distributed/swarm",
                dependencies: [],
                microtasks: [],
                forbidden_zones: [],
                risk_level: "BAJO"
            };
        }

        if (!data.task_tree) {
            console.warn("[PIZARRÓN] No hay datos de árbol semántico disponibles.");
            return;
        }

        this._render(data);
        this.overlay.style.display = 'flex';
    }

    hide() {
        this.overlay.style.display = 'none';
    }

    _render(data) {
        const { task_tree, policy_result, shadows, constructors } = data;
        const container = document.getElementById('pizarron-content');

        // Defaults defensivos
        const summary = (task_tree && task_tree.summary) || "Sin resumen";
        const mission_id = (task_tree && task_tree.mission_id) || "N/A";
        const primary_layer = (task_tree && task_tree.primary_layer) || "core";
        const dependencies = Array.isArray(task_tree && task_tree.dependencies) ? task_tree.dependencies : [];
        const microtasks = Array.isArray(task_tree && task_tree.microtasks) ? task_tree.microtasks : [];
        const forbidden_zones = Array.isArray(task_tree && task_tree.forbidden_zones) ? task_tree.forbidden_zones : [];
        const risk_level = (task_tree && task_tree.risk_level) || "BAJO";

        const badgeClass = (policy_result && policy_result.maturity && policy_result.maturity.includes("READY")) ? 'badge-ready' :
            (policy_result && policy_result.maturity && policy_result.maturity.includes("SUPERVISED")) ? 'badge-supervised' : 'badge-escalate';

        container.innerHTML = `
            <!-- Mission & Policy -->
            <section class="pizarron-card" style="grid-column: span 2;">
                <h4><span style="color: var(--pizarron-accent)">⚛</span> Misión y Política Operativa</h4>
                <div class="pizarron-mission">${summary}</div>
                <div style="margin-top: 15px; display: flex; gap: 20px; align-items: center;">
                    <div class="pizarron-badge ${badgeClass}">${(policy_result && policy_result.maturity) || 'PENDIENTE'}</div>
                    <div style="font-size: 0.8rem; opacity: 0.8;">Action: <b>${(policy_result && policy_result.action) || 'Escaneo Inicial'}</b></div>
                    <div style="font-size: 0.8rem; opacity: 0.8;">ID: <code>${mission_id}</code></div>
                </div>
            </section>

            <!-- Layers & Dependencies -->
            <section class="pizarron-card">
                <h4><span style="color: var(--pizarron-accent)">📂</span> Capas y Dependencias</h4>
                <div style="margin-bottom: 20px;">
                    <span style="font-size: 0.7rem; opacity: 0.6; display: block; margin-bottom: 5px;">CAPA OBJETIVO</span>
                    <div class="pizarron-layers-node" style="border: 1px solid var(--pizarron-accent)">${primary_layer}</div>
                </div>
                <div>
                    <span style="font-size: 0.7rem; opacity: 0.6; display: block; margin-bottom: 5px;">CAPAS RELACIONADAS / DEPENDENCIAS</span>
                    ${dependencies.map(d => `<div class="pizarron-layers-node">${d}</div>`).join('')}
                </div>
                <div class="pizarron-benefit">
                    Esta configuración asegura que el cambio impacte solo en los contratos necesarios, preservando la estabilidad del núcleo.
                </div>
            </section>

            <!-- Microtasks & Shadows -->
            <section class="pizarron-card" style="grid-row: span 2;">
                <h4><span style="color: var(--pizarron-accent)">⚡</span> Micro-tareas y Vigilancia</h4>
                <div class="pizarron-microtasks">
                    <ol>
                        ${microtasks.map(t => `<li>${t}</li>`).join('')}
                    </ol>
                </div>
                
                <div style="margin-top: 30px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--pizarron-border); padding-bottom: 5px; margin-bottom: 15px;">
                        <h5 style="font-size: 0.75rem; color: var(--pizarron-accent); margin:0;">
                            AUDITORES (${(shadows && shadows.length) || 0}) / CONSTRUCTORES (${(constructors && constructors.length) || 0})
                        </h5>
                    </div>

                    <!-- Shadows List (Unified or Split) -->
                    <div class="shadow-list">
                        ${Array.isArray(shadows) ? shadows.map(s => `
                            <div class="shadow-item shadow-auditor">
                                <div class="shadow-header">
                                    <span class="shadow-id">AUDIT: ${s.shadow_id}</span>
                                    <span class="shadow-status status-${s.state}">${s.state}</span>
                                </div>
                                <div class="shadow-task">${s.assigned_microtask}</div>
                                <div class="shadow-findings">${s.current_report ? s.current_report.findings[0] : 'Escaneando...'}</div>
                            </div>
                        `).join('') : ''}

                        ${Array.isArray(constructors) ? constructors.map(c => {
            const gate = c.context && c.context.gate_decision;
            const gateStatusClass = gate ? `status-${gate.status}` : '';

            return `
                            <div class="shadow-item shadow-constructor">
                                <div class="shadow-header">
                                    <span class="shadow-id">CONSTRUCT: ${c.shadow_id}</span>
                                    <span class="shadow-status ${gateStatusClass}">${gate ? gate.status.replace(/_/g, ' ') : c.state}</span>
                                </div>
                                <div class="shadow-task">${c.assigned_microtask}</div>
                                ${c.proposal ? `
                                    <div class="shadow-proposal">
                                        <div class="proposal-file">${c.proposal.target_file} [${c.proposal.target_block}]</div>
                                        <pre class="proposal-diff">${c.proposal.diff_preview}</pre>
                                        
                                        <!-- Approval Gate Info -->
                                        <div class="gate-overlay">
                                            <div class="gate-title">GATE STATUS: ${(gate && gate.result_summary) || 'PENDIENTE'}</div>
                                            ${(gate && gate.blocking_reason) ? `<div style="color: var(--pizarron-critical); font-size: 0.65rem; margin-top: 5px;">⚠ ${gate.blocking_reason}</div>` : ''}
                                            <div class="gate-checks">
                                                <span class="${(gate && gate.audit_confirmed) ? 'check-pass' : 'check-fail'}">AUDIT: ${(gate && gate.audit_confirmed) ? 'OK' : 'MISSING'}</span>
                                                <span class="${(gate && gate.checkpoint_required) ? 'check-info' : ''}">CHECKPOINT: ${(gate && gate.checkpoint_required) ? 'REQ' : 'NA'}</span>
                                            </div>

                                            <!-- Apply Lifecycle (Phase 13) -->
                                            ${(c.context && c.context.apply_record) ? `
                                                <div class="apply-lifecycle">
                                                    <div style="border-top: 1px dashed rgba(255,255,255,0.1); margin: 8px 0; padding-top: 8px;">
                                                        <span style="font-size: 0.65rem; color: var(--pizarron-safe);">🚀 CICLO DE EXECUCIÓN: ${c.state.toUpperCase()}</span>
                                                    </div>
                                                    <div class="lifecycle-details">
                                                        <span>📸 Backup: ${c.context.apply_record.checkpoint}</span>
                                                        <span>✅ Verificado: ${c.context.apply_record.verification}</span>
                                                        <span>👤 Por: ${c.context.apply_record.approver}</span>
                                                    </div>
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                ` : '<div class="shadow-findings">Preparando propuesta...</div>'}
                                ${c.auditor_note ? `<div class="auditor-note">${c.auditor_note}</div>` : ''}
                            </div>
                        `}).join('') : ''}
                    </div>
                </div>
            </section>

            <!-- Risk & Blindaje -->
            <section class="pizarron-card" style="grid-column: span 2;">
                <h4><span style="color: var(--pizarron-critical)">🛡</span> Zonas Blindadas y Riesgo Sistémico</h4>
                <div style="display: flex; gap: 40px;">
                    <div style="flex: 1;">
                        <span style="font-size: 0.7rem; opacity: 0.6; display: block; margin-bottom: 5px;">ZONAS BLINDADAS (NO TOCAR)</span>
                        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                            ${forbidden_zones.map(z => `<span style="font-size: 0.75rem; background: rgba(255,0,0,0.1); padding: 3px 8px; border-radius: 4px; border: 1px solid rgba(255,0,0,0.2)">${z}</span>`).join('')}
                        </div>
                    </div>
                    <div style="flex: 1;">
                        <span style="font-size: 0.7rem; opacity: 0.6; display: block; margin-bottom: 5px;">RAZONAMIENTO DE RIESGO: ${risk_level}</span>
                        <p style="font-size: 0.85rem; margin: 0; color: #b0bac5;">${(policy_result && policy_result.rationale) || 'Análisis de riesgo basado en capas estructurales.'}</p>
                    </div>
                </div>
            </section>
        `;
    }
}

window.pizarronUI = new PizarronVivoUI();
