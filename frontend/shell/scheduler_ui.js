class SchedulerUI {
    constructor() {
        this.activeSchedule = null;
    }

    renderSchedule(container, schedule, backlog = []) {
        if (!container || !schedule) return;
        this.activeSchedule = schedule;

        const missions = schedule.missions || [];
        const analysis = schedule.analysis || {};
        const stateClass = `state-${schedule.status.toLowerCase()}`;

        let html = `
            <div class="intake-card animate-slide-in scheduler-card">
                <div class="intake-header" style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 20px;">
                    <div>
                        <div class="intake-branding">TACTICAL SCHEDULER v1.0</div>
                        <div class="intake-title">${schedule.name.toUpperCase()}</div>
                    </div>
                    <div style="display:flex; gap: 8px;">
                        <button class="handoff-mini-btn" onclick="window.schedulerUI.refreshSchedule('${schedule.schedule_id}')">REFRESCAR</button>
                        <button class="handoff-mini-btn" onclick="window.pizarronUI.loadBacklog()" style="opacity:0.6">← VOLVER</button>
                    </div>
                </div>

                <div class="scheduler-layout" style="display: grid; grid-template-columns: 1fr 300px; gap: 20px;">
                    <!-- LEFT: SEQUENCE LIST -->
                    <div class="scheduler-sequence">
                        <h4 style="font-size: 0.7rem; color: #888; text-transform: uppercase; margin-bottom: 15px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px;">Secuencia de Ejecución</h4>
                        <div class="sequence-list" id="scheduler-sequence-list" style="display: flex; flex-direction: column; gap: 10px;">
                            ${missions.length === 0 ? '<div style="opacity:0.3; padding: 20px; border: 1px dashed #444; border-radius: 8px; text-align: center; font-size: 0.8rem;">No hay misiones en la secuencia.</div>' : ''}
                            ${missions.map((m, idx) => this.renderMissionItem(m, idx, schedule.schedule_id)).join('')}
                        </div>

                        ${backlog.length > 0 ? `
                            <div style="margin-top: 25px;">
                                <h4 style="font-size: 0.7rem; color: #888; text-transform: uppercase; margin-bottom: 10px; opacity: 0.6;">Añadir desde la Cola</h4>
                                <div style="display:flex; gap: 10px; overflow-x: auto; padding-bottom: 10px;">
                                    ${backlog.filter(h => !missions.find(m => m.handoff_id === h.handoff_id)).map(h => `
                                        <div class="mini-handoff-pill" onclick="window.schedulerUI.addToSchedule('${schedule.schedule_id}', '${h.handoff_id}')">
                                            <span>${h.briefing_title.substring(0, 20)}...</span>
                                            <span style="color:var(--pizarron-accent)">+</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>

                    <!-- RIGHT: ANALYSIS PANEL -->
                    <div class="scheduler-analysis" style="background: rgba(0,0,0,0.2); border-radius: 10px; padding: 15px; border: 1px solid rgba(255,255,255,0.05);">
                        <h4 style="font-size: 0.75rem; color: var(--pizarron-accent); text-transform: uppercase; margin-bottom: 15px; font-family: 'Outfit';">Análisis de Integridad</h4>
                        
                        <!-- Conflict Counter -->
                        <div style="display:flex; justify-content: space-between; margin-bottom: 15px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px;">
                            <div style="text-align: center; flex: 1;">
                                <div style="font-size: 1.2rem; font-weight: bold; color: ${analysis.conflicts && analysis.conflicts.length > 0 ? '#ff4444' : '#32ff96'}">${(analysis.conflicts || []).length}</div>
                                <div style="font-size: 0.55rem; color: #888;">CONFLICTOS</div>
                            </div>
                            <div style="width:1px; background: rgba(255,255,255,0.1); margin: 0 10px;"></div>
                            <div style="text-align: center; flex: 1;">
                                <div style="font-size: 1.2rem; font-weight: bold; color: ${analysis.dependencies && analysis.dependencies.length > 0 ? '#00e5ff' : '#888'}">${(analysis.dependencies || []).length}</div>
                                <div style="font-size: 0.55rem; color: #888;">DEPENDENCIAS</div>
                            </div>
                        </div>

                        <!-- Warnings & Suggestions -->
                        <div class="analysis-feedback" style="display: flex; flex-direction: column; gap: 12px;">
                            ${(analysis.conflicts || []).map(c => `
                                <div style="background: rgba(255,68,68,0.1); border-left: 3px solid #ff4444; padding: 8px; border-radius: 4px; font-size: 0.65rem; line-height: 1.3;">
                                    <b style="color:#ff4444;">COLISIÓN DE SUPERFICIE:</b> ${c}
                                </div>
                            `).join('')}

                            ${(analysis.dependencies || []).map(d => `
                                <div style="background: rgba(0,229,255,0.1); border-left: 3px solid #00e5ff; padding: 8px; border-radius: 4px; font-size: 0.65rem; line-height: 1.3;">
                                    <b style="color:#00e5ff;">DEPENDENCIA DETECTADA:</b> ${d}
                                </div>
                            `).join('')}

                            ${missions.length > 0 && (analysis.conflicts || []).length === 0 ? `
                                <div style="background: rgba(50,255,150,0.1); border-left: 3px solid #32ff96; padding: 8px; border-radius: 4px; font-size: 0.65rem; line-height: 1.3; color: #32ff96;">
                                    ✓ Secuencia validada para ejecución paralela u ordenada. No se detectan bloqueos técnicos inmediatos.
                                </div>
                            ` : ''}
                        </div>

                        ${this.renderProposedSequence(schedule)}

                        <!-- Suggestions Layer (Phase: RESOLUTION ENGINE) -->
                        <div class="scheduler-suggestions" style="margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px;">
                            <h5 style="font-size: 0.65rem; color: var(--pizarron-accent); text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.5px;">ESTRATEGIA TÁCTICA (PRESCRICTIVA)</h5>
                            <div style="display: flex; flex-direction: column; gap: 10px;">
                                ${this.renderSuggestions(schedule.suggestions || [])}
                            </div>
                        </div>

                        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.05);">
                             <div style="font-size: 0.6rem; color: #888; margin-bottom: 10px;">ESTADO DE PREPARACIÓN</div>
                             <div style="height: 6px; background: rgba(255,255,255,0.05); border-radius: 3px; overflow: hidden; margin-bottom: 5px;">
                                 <div style="width: ${schedule.readiness_state === 'READY' ? '100%' : '30%'}; height: 100%; background: ${schedule.readiness_state === 'READY' ? 'var(--pizarron-accent)' : '#ffaa00'}; transition: width 0.5s;"></div>
                             </div>
                             <div style="font-size: 0.55rem; color: ${schedule.readiness_state === 'READY' ? 'var(--pizarron-accent)' : '#ffaa00'}; display: flex; justify-content: space-between; font-weight: bold;">
                                 <span>${schedule.readiness_state === 'READY' ? 'LISTO PARA LANZAMIENTO' : 'BLOQUEADO POR GOBERNANZA'}</span>
                                 <span>${schedule.readiness_state === 'READY' ? '100%' : 'GATED'}</span>
                             </div>
                        </div>

                        <button class="intake-btn ${schedule.readiness_state === 'READY' ? 'btn-confirm' : ''}" 
                                style="width: 100%; margin-top: 20px; font-size: 0.75rem; border-radius: 6px; 
                                       background: ${schedule.readiness_state === 'READY' ? '' : 'rgba(255,255,255,0.05)'};
                                       color: ${schedule.readiness_state === 'READY' ? '' : '#666'};
                                       border: ${schedule.readiness_state === 'READY' ? '' : '1px solid rgba(255,255,255,0.1)'}"
                                onclick="window.schedulerUI.executeSchedule('${schedule.schedule_id}')"
                                ${schedule.readiness_state !== 'READY' || missions.length === 0 ? 'disabled' : ''}>
                            GOVERNED LAUNCH (SECUENCIA)
                        </button>
                        ${schedule.readiness_state !== 'READY' ? `
                           <div style="font-size: 0.5rem; color: #ff4444; text-align: center; margin-top: 8px; opacity: 0.8;">
                               ⚠️ REQUIERE RESOLUCIÓN DE GATES PENDIENTES
                           </div>
                        ` : ''}
                    </div>
                </div>
            </div>

            <style>
                .mini-handoff-pill {
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 20px;
                    padding: 4px 10px;
                    font-size: 0.6rem;
                    white-space: nowrap;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    transition: all 0.2s;
                }
                .mini-handoff-pill:hover {
                    background: rgba(50,255,150,0.1);
                    border-color: var(--pizarron-accent);
                }
                .mission-order-pill {
                    width: 20px;
                    height: 20px;
                    border-radius: 10px;
                    background: rgba(255,255,255,0.1);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.6rem;
                    font-weight: bold;
                    color: var(--pizarron-accent);
                }
            </style>
        `;

        container.innerHTML = html;
    }

    renderProposedSequence(schedule) {
        if (!schedule.sequence_proposal || !schedule.sequence_proposal.suggested_order) return '';

        const proposal = schedule.sequence_proposal;
        const isSame = JSON.stringify(schedule.ordered_handoff_ids) === JSON.stringify(proposal.suggested_order);

        if (isSame) return '';

        return `
            <div class="sequence-proposal-banner" style="background: rgba(50,255,150,0.05); border: 1px solid rgba(50,255,150,0.2); border-radius: 8px; padding: 12px; margin-bottom: 20px;">
                <div style="font-size: 0.65rem; color: var(--pizarron-accent); font-weight: bold; margin-bottom: 8px;">
                    OPTIMIZACIÓN DISPONIBLE (${(proposal.confidence * 100).toFixed(0)}% Confianza)
                </div>
                <div style="font-size: 0.65rem; color: #ccc; line-height: 1.3; margin-bottom: 12px;">${proposal.rationale}</div>
                
                <div style="display:flex; flex-direction: column; gap: 4px; margin-bottom: 12px;">
                    <div style="font-size: 0.55rem; color: #888; text-transform: uppercase;">Nuevo Flujo Propuesto:</div>
                    <div style="display:flex; flex-wrap: wrap; gap: 5px; align-items: center;">
                        ${proposal.suggested_order.map((id, idx) => `
                            <span style="background: rgba(50,255,150,0.1); border: 1px solid rgba(50,255,150,0.2); padding: 2px 6px; border-radius: 4px; font-size: 0.5rem; font-family: monospace; color: var(--pizarron-accent);">
                                ${idx + 1}. ${id.substring(0, 6)}
                            </span>
                        `).join('<span style="opacity:0.3; font-size:0.5rem;">→</span>')}
                    </div>
                </div>

                <div style="display:flex; gap: 8px;">
                    <button class="handoff-mini-btn action-primary" 
                            style="flex: 1;"
                            onclick="window.omniShell.addInput('APPLY RECOMMENDED SEQUENCE SCHEDULE ${schedule.schedule_id}')">
                        APLICAR ORDEN PROPUESTO
                    </button>
                    <button class="handoff-mini-btn" style="flex: 0.3;" onclick="this.parentElement.parentElement.remove()">IGNORAR</button>
                </div>
            </div>
        `;
    }

    renderSuggestions(suggestions) {
        if (!suggestions || suggestions.length === 0) {
            return '<div style="font-size: 0.65rem; opacity: 0.4; text-align: center; padding: 10px; border: 1px dashed #333; border-radius: 6px;">En espera de desvíos tácticos...</div>';
        }

        return suggestions.map(s => {
            let color = 'var(--pizarron-accent)';
            if (s.impact === 'high') color = 'var(--creator-gold)';
            if (s.impact === 'critical') color = '#ff4444';

            return `
                <div class="tactical-suggestion-item" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-left: 3px solid ${color}; padding: 10px; border-radius: 4px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 5px;">
                        <b style="font-size: 0.65rem; color: ${color}; letter-spacing: 0.5px;">${s.label.toUpperCase()}</b>
                        <span style="font-size: 0.5rem; opacity: 0.5;">ID: ${s.suggestion_id.substring(0, 4)}</span>
                    </div>
                    <div style="font-size: 0.65rem; color: #ccc; line-height: 1.3; margin-bottom: 8px;">${s.rationale}</div>
                    <button class="handoff-mini-btn" 
                            style="width: 100%; border-color: ${color}; color: ${color}; font-weight: bold;" 
                            onclick="window.omniShell.addInput('${s.action_cmd}')">
                        APLICAR RESOLUCIÓN
                    </button>
                </div>
            `;
        }).join('');
    }

    renderMissionItem(mission, index, scheduleId) {
        const risk = (mission.risk_level || 'low').toLowerCase();
        const riskColor = risk === 'high' || risk === 'critical' ? '#ff4444' : (risk === 'medium' ? '#ffaa00' : '#32ff96');

        const audit = (this.activeSchedule.launch_audit && this.activeSchedule.launch_audit[mission.handoff_id]) || { is_ready: false, rationale: 'Audit pending...', blocks: [] };
        const gateColor = audit.is_ready ? '#32ff96' : '#ff4444';

        return `
            <div class="scheduler-mission-item" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; padding: 12px; display: flex; align-items: center; gap: 15px; position: relative;">
                <div class="mission-order-pill">${index + 1}</div>
                <div style="flex: 1;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size: 0.8rem; font-weight: bold; color: #fff;">${mission.briefing_title}</span>
                        <span style="font-size: 0.55rem; color: ${gateColor}; font-weight: bold; background: ${gateColor}22; padding: 2px 6px; border-radius: 4px; border: 1px solid ${gateColor}44;">
                            ${audit.is_ready ? 'READY' : (audit.blocks[0] || 'LOCKED')}
                        </span>
                    </div>
                    <div style="font-size: 0.6rem; color: #888; margin-top: 5px;">
                        Surface: <span style="color: #ccc;">${mission.surface_affected.join(', ')}</span> 
                        <span style="margin: 0 8px; opacity: 0.2;">|</span>
                        Risk: <span style="color: ${riskColor};">${risk.toUpperCase()}</span>
                    </div>
                    ${!audit.is_ready ? `
                        <div style="font-size: 0.55rem; color: #ffaa00; margin-top: 5px; font-style: italic;">
                            → ${audit.rationale}
                        </div>
                    ` : ''}
                </div>
                <div style="display:flex; gap: 5px;">
                    <button class="handoff-mini-btn" onclick="window.schedulerUI.moveMission('${scheduleId}', '${mission.handoff_id}', 'up')" ${index === 0 ? 'disabled' : ''}>↑</button>
                    <button class="handoff-mini-btn" onclick="window.schedulerUI.moveMission('${scheduleId}', '${mission.handoff_id}', 'down')" ${index === this.activeSchedule.missions.length - 1 ? 'disabled' : ''}>↓</button>
                    <button class="handoff-mini-btn" style="color:#ff4444;" onclick="window.schedulerUI.removeFromSchedule('${scheduleId}', '${mission.handoff_id}')">✕</button>
                </div>
            </div>
        `;
    }

    // ACTIONS
    addToSchedule(scheduleId, handoffId) {
        if (window.omniShell) {
            window.omniShell.addInput(`ADD TO MISSION SCHEDULE HANDOFF ${handoffId}`);
        }
    }

    removeFromSchedule(scheduleId, handoffId) {
        // Logic to remove... we'll just use a reorder command with the filtered list
        const newSeq = this.activeSchedule.handoff_ids.filter(id => id !== handoffId);
        this.updateSequence(scheduleId, newSeq);
    }

    moveMission(scheduleId, handoffId, direction) {
        const seq = [...this.activeSchedule.handoff_ids];
        const idx = seq.indexOf(handoffId);
        if (idx === -1) return;

        if (direction === 'up' && idx > 0) {
            const temp = seq[idx - 1];
            seq[idx - 1] = seq[idx];
            seq[idx] = temp;
        } else if (direction === 'down' && idx < seq.length - 1) {
            const temp = seq[idx + 1];
            seq[idx + 1] = seq[idx];
            seq[idx] = temp;
        }

        this.updateSequence(scheduleId, seq);
    }

    updateSequence(scheduleId, sequence) {
        if (window.omniShell) {
            const seqStr = sequence.join(',');
            window.omniShell.addInput(`REORDER MISSION SCHEDULE ${scheduleId} SEQUENCE ${seqStr}`);
        }
    }

    refreshSchedule(scheduleId) {
        if (window.omniShell) {
            window.omniShell.addInput(`SHOW MISSION SCHEDULE`);
        }
    }

    executeSchedule(scheduleId) {
        if (window.omniShell) {
            window.omniShell.addInput(`EXECUTE MISSION SCHEDULE ${scheduleId}`);
        }
    }
}

window.schedulerUI = new SchedulerUI();
