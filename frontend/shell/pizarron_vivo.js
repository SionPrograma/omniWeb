
class PizarronVivoUI {
    constructor() {
        this.id = 'pizarron-vivo-embedded';
        this.lastDataHash = null;
        this.selectedNodeId = null;
    }

    renderInto(container, data) {
        if (!container || !data) return;
        const mission = data.mission || data.active_mission || null;

        const currentHash = JSON.stringify(mission) + this.selectedNodeId + (data.proposals ? data.proposals.length : 0);
        if (this.lastDataHash === currentHash) return;
        this.lastDataHash = currentHash;

        if (!mission || (mission.status === 'IDLE' || !mission.active_goal)) {
            container.innerHTML = `
                <div class="pizarron-card pizarron-empty-state">
                    <h3 style="color: var(--pizarron-accent); font-family: 'Outfit';">SIN MISIÓN ACTIVA</h3>
                    <p style="font-size: 0.85rem; margin-top: 10px; opacity: 0.6;">OmniWeb está en espera.</p>
                </div>
            `;
            return;
        }

        const executionTree = (mission.context_snap && mission.context_snap.tree) ? mission.context_snap.tree : null;
        const summary = mission.active_goal || "Misión del Sistema";
        const forbidden_zones = mission.blocked_reasons || [];
        const risk_level = (forbidden_zones.length > 0) ? "BLOQUEADO" : "NOMINAL";

        // Operational Parameters (Phase 18)
        const params = mission.parameters || {};
        const paramBadges = [];
        if (params.conservative_mode) paramBadges.push({ label: 'CONSERVADOR', icon: '🛡️', color: '#00ccff' });
        if (params.audit_only) paramBadges.push({ label: 'SÓLO AUDITORÍA', icon: '🔍', color: '#ffcc00' });
        if (params.roadmap_first) paramBadges.push({ label: 'ROADMAP-FIRST', icon: '🗺️', color: '#ff8800' });
        if (params.aggressiveness === 'surgical') paramBadges.push({ label: 'M. QUIRÚRGICO', icon: '🔪', color: '#ff4444' });
        if (params.forbidden_paths?.length > 0) paramBadges.push({ label: 'RUTAS PROTEGIDAS', icon: '🚫', color: '#ff0055' });
        if (params.forbidden_layers?.length > 0) paramBadges.push({ label: 'CAPAS BLOQUEADAS', icon: '⛔', color: '#ff0055' });
        if (params.frozen_paths?.length > 0 || params.frozen_layers?.length > 0) paramBadges.push({ label: 'SECTOR CONGELADO', icon: '❄️', color: '#00e5ff' });

        const renderTreeNode = (node, depth = 0) => {
            const hasChildren = node.children && node.children.length > 0;
            const isSelected = String(node.id) === String(this.selectedNodeId);

            let statusIcon = '○';
            if (node.status === 'COMPLETED') statusIcon = '✓';
            else if (node.status === 'ACTIVE') statusIcon = '⚛';
            else if (node.status === 'RECOVERING') statusIcon = '⚛';
            else if (node.status === 'FAILED') statusIcon = '✖';
            else if (node.status === 'NEEDS_REVIEW') statusIcon = '⚠';

            return `
                <div class="pizarron-tree-node depth-${depth} pizarron-status-${node.status.toLowerCase()} ${isSelected ? 'selected' : ''}" 
                     onclick="window.pizarronUI.selectNode('${node.id}')"
                     style="margin-left: ${depth * 12}px; border-left: ${depth > 0 ? '1px solid rgba(255,255,255,0.1)' : 'none'}; cursor: pointer;">
                    <div style="display:flex; align-items: center; gap: 8px;">
                        <span class="status-icon">${statusIcon}</span>
                        <span class="node-label" style="font-weight: ${depth === 0 ? 'bold' : 'normal'};">
                            ${node.label} ${node.status === 'RECOVERING' ? '<span class="recovery-text">RESCATANDO...</span>' : (depth === 0 ? '⬡' : '')}
                        </span>
                    </div>
                    ${!isSelected && node.evidence ? `<div style="font-size: 0.6rem; opacity: 0.3; margin-left: 22px;">${node.evidence.substring(0, 30)}...</div>` : ''}
                </div>
                ${hasChildren ? `<div>${node.children.map(child => renderTreeNode(child, depth + 1)).join('')}</div>` : ''}
            `;
        };

        const renderCognitiveTrace = (trace) => {
            if (!trace) return '';
            const risks = trace.risks_detected || [];
            const hasHighRiskHistory = risks.includes('high_impact_radius');

            const items = [
                ...(hasHighRiskHistory ? [{ label: 'ALERTA HISTÓRICA', val: 'Detectados incidentes críticos previos en esta zona.', icon: '🚨', color: '#ff4444', weight: 'bold' }] : []),
                { label: 'HIPÓTESIS', val: trace.main_hypothesis, icon: '💡' },
                { label: 'ALTERNATIVAS', val: (trace.alternatives_considered || []).join(', '), icon: '📋' },
                { label: 'RIESGOS', val: risks.join(', '), icon: '⚠️', color: '#ffcc00' },
                { label: 'ELEGIDO', val: trace.chosen_path, icon: '🎯', weight: 'bold' },
                { label: 'DESCARTADO', val: (trace.discarded_paths || []).join(', '), icon: '🚫', opacity: 0.5 },
                { label: 'RESULTADO', val: trace.final_outcome, icon: '🏁' }
            ];

            return `
                <div class="inspector-section cognitive-trace">
                    <span class="section-title">RAZONAMIENTO COGNITIVO</span>
                    <div style="margin-top: 10px; border-left: 2px solid rgba(255,255,255,0.1); padding-left: 15px; display: flex; flex-direction: column; gap: 12px;">
                        ${items.map(item => `
                            <div style="font-size: 0.65rem; line-height: 1.2; ${item.opacity ? `opacity: ${item.opacity};` : ''}">
                                <div style="display:flex; align-items: center; gap: 6px; margin-bottom: 2px;">
                                    <span>${item.icon}</span>
                                    <b style="color: rgba(255,255,255,0.4); font-size: 0.55rem; letter-spacing: 0.5px;">${item.label}</b>
                                </div>
                                <div style="color: ${item.color || '#fff'}; font-weight: ${item.weight || 'normal'};">${item.val || 'N/A'}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        };

        const renderInspector = (node) => {
            const ev = node.deep_evidence || {};
            const hasDiff = ev.diff || (ev.changes && ev.changes.length > 0);
            const trace = ev.cognitive_trace || (ev.constructor_proposal && ev.constructor_proposal.cognitive_trace) || (ev.rescue_result && ev.rescue_result.cognitive_trace);

            return `
                <div class="pizarron-inspector animate-slide-in">
                    <div style="display:flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                        <div style="display:flex; flex-direction:column;">
                            <h4 style="margin:0; color: var(--pizarron-accent); font-family: 'Outfit';">INSPECTOR: ${node.label}</h4>
                            <div style="display:flex; gap: 6px; align-items: center;">
                                <span class="status-badge status-${node.status.toLowerCase()}">${node.status}</span>
                                ${node.id === executionTree.root.id && params.conservative_mode ? `<span style="font-size:0.5rem; background:#0096ff; color:#fff; padding:2px 4px; border-radius:3px;">🛡️ CONSERVADOR</span>` : ''}
                            </div>
                        </div>
                        <span style="font-size: 0.6rem; opacity: 0.4;">ID: ${node.id}</span>
                    </div>

                    ${(node.id === executionTree.root.id) && (params.constraints?.length > 0 || params.forbidden_paths?.length > 0 || params.forbidden_layers?.length > 0 || params.success_criteria?.length > 0) ? `
                        <div class="inspector-section" style="background: rgba(255,255,255,0.02); border-radius: 8px; padding: 10px; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.05);">
                            <span class="section-title">REGLAS DE GOBERNANZA</span>
                            <div style="margin-top: 8px; display: flex; flex-direction: column; gap: 6px;">
                                ${(params.forbidden_paths || []).map(p => `
                                    <div style="font-size: 0.65rem; color: #ff0055; display:flex; gap: 5px; font-weight: bold;">
                                        <span>🚫 NO TOCAR:</span> <span>${p}</span>
                                    </div>
                                `).join('')}
                                ${(params.forbidden_layers || []).map(l => `
                                    <div style="font-size: 0.65rem; color: #ff4444; display:flex; gap: 5px;">
                                        <span>⛔ CAPA BLOQUEADA:</span> <span>${l.toUpperCase()}</span>
                                    </div>
                                `).join('')}
                                ${(params.frozen_paths || []).map(p => `
                                    <div style="font-size: 0.65rem; color: #00e5ff; display:flex; gap: 5px; font-weight: bold;">
                                        <span>❄️ CONGELADO:</span> <span>${p}</span>
                                    </div>
                                `).join('')}
                                ${(params.frozen_layers || []).map(l => `
                                    <div style="font-size: 0.65rem; color: #00e5ff; display:flex; gap: 5px;">
                                        <span>💎 CAPA CONGELADA:</span> <span>${l.toUpperCase()}</span>
                                    </div>
                                `).join('')}
                                ${(params.allowed_paths || []).map(p => `
                                    <div style="font-size: 0.65rem; color: #00ccff; display:flex; gap: 5px;">
                                        <span>📏 ALCANCE FIJO:</span> <span>${p}</span>
                                    </div>
                                `).join('')}
                                ${(mission.context_snap?.governance_profiles || []).map(name => `
                                    <div style="font-size: 0.65rem; color: #ffcc00; display:flex; gap: 5px; border-left: 2px solid #ffcc00; padding-left: 5px; margin-top: 2px;">
                                        <span>📜 PERFIL:</span> <span style="font-weight: bold;">${name}</span>
                                    </div>
                                `).join('')}

                                <!-- PHASE 21: CREATOR-ONLY PIN OVERRIDE -->
                                ${params.hard_override_granted ? `
                                    <div style="margin-top: 8px; background: rgba(0, 255, 136, 0.1); border: 1px solid #00ff88; border-radius: 4px; padding: 6px; display: flex; align-items: center; gap: 8px; animation: glow-green 2s infinite;">
                                        <span style="font-size: 1rem;">🔓</span>
                                        <div style="display: flex; flex-direction: column;">
                                            <span style="font-size: 0.65rem; color: #00ff88; font-weight: bold;">AUTORIDAD REFORZADA: PIN VALIDADO</span>
                                            <span style="font-size: 0.55rem; color: #aaa;">Barreras extremas levantadas para esta misión.</span>
                                        </div>
                                    </div>
                                ` : mission.status === "PAUSED" && node?.result_summary?.includes("PIN") ? `
                                    <div style="margin-top: 8px; background: rgba(255, 0, 85, 0.1); border: 1px solid #ff0055; border-radius: 4px; padding: 6px; display: flex; align-items: center; gap: 8px; animation: glow-red 1.5s infinite;">
                                        <span style="font-size: 1.2rem;">🔒</span>
                                        <div style="display: flex; flex-direction: column;">
                                            <span style="font-size: 0.65rem; color: #ff0055; font-weight: bold;">AUTORIDAD REFORZADA REQUERIDA</span>
                                            <span style="font-size: 0.55rem; color: #aaa;">Acción de riesgo EXTREMO. Inyectar PIN en comandos.</span>
                                        </div>
                                    </div>
                                ` : ''}

                                <!-- PHASE 21: COOLDOWN / STABILIZATION BADGE -->
                                ${params.cooldown_active ? `
                                    <div style="margin-top: 8px; background: rgba(0, 229, 255, 0.1); border: 1px solid #00e5ff; border-radius: 4px; padding: 6px; display: flex; align-items: center; gap: 8px; animation: glow-blue 2s infinite;">
                                        <span style="font-size: 1rem;">❄️</span>
                                        <div style="display: flex; flex-direction: column;">
                                            <span style="font-size: 0.65rem; color: #00e5ff; font-weight: bold;">ENFRIAMIENTO ACTIVO</span>
                                            <span style="font-size: 0.55rem; color: #aaa;">Estabilizando sistema tras ${params.consecutive_mutations || 5} mutaciones.</span>
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${(params.constraints || []).map(c => `
                                    <div style="font-size: 0.65rem; color: #aaa; display:flex; gap: 5px;">
                                        <span>○</span> <span>${c}</span>
                                    </div>
                                `).join('')}
                                
                                ${(params.success_criteria || []).map(s => `
                                    <div style="font-size: 0.65rem; color: #00ff88; display:flex; gap: 5px;">
                                        <span>🎯</span> <span>${s}</span>
                                    </div>
                                `).join('')}

                                <!-- PHASE 21: AUTONOMY BOUNDARY METER -->
                                <div style="margin-top: 10px; border-top: 1px solid #333; padding-top: 5px;">
                                    <div style="font-size: 0.6rem; color: #aaa; margin-bottom: 3px; display: flex; justify-content: space-between;">
                                        <span>🧪 PRESUPUESTO DE RIESGO</span>
                                        <span>${params.risk_consumed || 0} / ${params.risk_budget || 10}</span>
                                    </div>
                                    <div style="height: 4px; background: #222; border-radius: 2px; overflow: hidden; width: 100%;">
                                        <div style="height: 100%; width: ${Math.min(100, ((params.risk_consumed || 0) / (params.risk_budget || 10)) * 100)}%; background: ${(params.risk_consumed || 0) >= (params.risk_budget || 10) ? '#ff4444' : (params.risk_consumed || 0) > (params.risk_budget || 10) * 0.7 ? '#ffaa00' : '#00e5ff'}; transition: width 0.3s ease;"></div>
                                    </div>
                                </div>

                                <!-- PHASE 21: DRIFT DETECTOR -->
                                ${(mission.context_snap?.drift_alerts || []).length > 0 ? `
                                    <div style="margin-top: 15px; border-top: 1px dashed #444; padding-top: 8px;">
                                        <div style="font-size: 0.65rem; color: #ff0055; font-weight: bold; margin-bottom: 5px; display: flex; align-items: center; gap: 5px;">
                                            <span style="display:inline-block; width: 8px; height: 8px; background: #ff0055; border-radius: 50%; box-shadow: 0 0 10px #ff0055; animation: pulse 1.5s infinite;"></span>
                                            📡 DETECTOR DE DERIVA
                                        </div>
                                        <div style="display: flex; flex-direction: column; gap: 4px;">
                                            ${(mission.context_snap.drift_alerts).slice(-3).map(a => `
                                                <div style="font-size: 0.6rem; background: rgba(0,0,0,0.2); padding: 5px; border-radius: 4px; border-left: 2px solid ${a.severity === 'CRITICAL' ? '#ff0055' : a.severity === 'WARNING' ? '#ffcc00' : '#00e5ff'};">
                                                    <div style="display: flex; justify-content: space-between; color: ${a.severity === 'CRITICAL' ? '#ff4444' : '#fff'};">
                                                        <b>${a.type}</b>
                                                        <span style="opacity: 0.5;">${a.timestamp.split('T')[1].split(':')[0]}</span>
                                                    </div>
                                                    <div style="color: #aaa; margin-top: 2px; font-size: 0.55rem;">${a.message}</div>
                                                    <div style="color: #666; font-style: italic; margin-top: 2px; font-size: 0.5rem;">💡 Sugerencia: ${a.suggestion}</div>
                                                </div>
                                            `).reverse().join('')}
                                        </div>
                                    </div>
                                ` : ''}

                                <style>
                                    @keyframes pulse {
                                        0% { opacity: 1; transform: scale(1); }
                                        50% { opacity: 0.5; transform: scale(0.8); }
                                        100% { opacity: 1; transform: scale(1); }
                                    }
                                </style>
                            </div>
                        </div>
            ` : ''}

                    <div class="inspector-content" style="display: flex; flex-direction: column; gap: 15px; max-height: 80vh; overflow-y: auto; padding-right: 10px;">
                        
                        <!-- PHASE 21: GOVERNANCE CONSOLIDATED DASHBOARD -->
                        <div class="inspector-section" style="background: rgba(0,0,0,0.3); border-radius: 12px; padding: 15px; border: 1px solid rgba(0,255,136,0.3); box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                                <div style="display: flex; flex-direction: column;">
                                    <span style="font-size: 0.55rem; color: #888; letter-spacing: 1px; font-weight: bold;">OMNI-SHIELD v1.0</span>
                                    <span style="font-size: 1rem; color: #fff; font-weight: bold; letter-spacing: -0.5px;">ESTADO DE SALUD</span>
                                </div>
                                <div id="governance-pulse" style="width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(0,255,136,0.1); border: 2px solid ${params.risk_consumed >= (params.risk_budget || 10) ? '#ffaa00' : params.cooldown_active ? '#00e5ff' : '#00ff88'}; box-shadow: 0 0 20px ${params.risk_consumed >= (params.risk_budget || 10) ? '#ffaa0033' : '#00ff8833'}; animation: pulse 2s infinite;">
                                    <span style="font-size: 1.2rem;">🛡️</span>
                                </div>
                            </div>

                            <!-- Master Health Status (Synthesized) -->
                            <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                                <div style="display: flex; align-items: baseline; gap: 8px;">
                                    <span style="font-size: 1.2rem; font-weight: 800; color: ${params.risk_consumed >= (params.risk_budget || 10) ? '#ffaa00' : params.cooldown_active ? '#00e5ff' : (mission.context_snap?.drift_alerts || []).length > 0 ? '#ffcc00' : '#00ff88'}">
                                        ${params.risk_consumed >= (params.risk_budget || 10) ? 'AUTONOMÍA AGOTADA' : params.cooldown_active ? 'ESTABILIZACIÓN' : (mission.context_snap?.drift_alerts || []).length > 0 ? 'RIESGO OPERATIVO' : 'SISTEMA SEGURO'}
                                    </span>
                                </div>
                                <div style="font-size: 0.7rem; color: #aaa; margin-top: 5px;">
                                    💡 <b>Recomendación:</b> ${params.risk_consumed >= (params.risk_budget || 10) ? 'Inyectar autoridad o cerrar tanda.' : params.cooldown_active ? 'Asegurar firmeza antes de reanudar.' : (mission.context_snap?.drift_alerts || []).length > 0 ? 'Revisar Detector de Deriva.' : 'Continuar bajo régimen constitucional.'}
                                </div>
                            </div>

                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                                <div style="background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px; border: 1px solid #333;">
                                    <span style="font-size: 0.55rem; color: #666; display: block; margin-bottom: 2px;">CONSTITUCIÓN</span>
                                    <span style="font-size: 0.65rem; color: #ffcc00; font-weight: bold;">${mission.context_snap?.governance_profiles?.[0] || 'Dinámica'}</span>
                                </div>
                                <div style="background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px; border: 1px solid #333;">
                                    <span style="font-size: 0.55rem; color: #666; display: block; margin-bottom: 2px;">AUTONOMÍA</span>
                                    <span style="font-size: 0.65rem; color: #fff;">${((params.risk_consumed || 0) / (params.risk_budget || 10) * 100).toFixed(0)}% Utilizado</span>
                                </div>
                            </div>
                        </div>

                        <div class="inspector-section" style="background: rgba(255,255,255,0.01); border-radius: 8px; padding: 10px; border: 1px dashed rgba(22,255,188,0.2);">
                            <span class="section-title" style="color: #00ffcc; font-size: 0.7rem; letter-spacing: 1px;">⚙️ CAPAS ACTIVAS</span>
                            <div style="margin-top: 8px; display: flex; flex-direction: column; gap: 4px;">

                    ${(node.id === executionTree.root.id) && (params.parameter_history?.length > 0) ? `
                        <div class="inspector-section" style="background: rgba(255,255,255,0.01); border-radius: 8px; padding: 10px; margin-bottom: 12px; border: 1px dashed rgba(22,255,188,0.3); box-shadow: inset 0 0 10px rgba(0,255,188,0.05);">
                            <span class="section-title" style="color: #00ffcc;">📜 HISTORIAL DE CONSTITUCIÓN</span>
                            <div style="margin-top: 8px; display: flex; flex-direction: column; gap: 4px;">
                                ${(params.parameter_history || []).slice(-3).map(h => `
                                    <div style="font-size: 0.55rem; color: #88ffcc; opacity: 0.9; padding: 4px; background: rgba(0,255,200,0.05); border-radius: 4px;">
                                        <span style="opacity:0.6;">[${h.timestamp.split('T')[1].split(':')[0]}:${h.timestamp.split('T')[1].split(':')[1]}]</span> 
                                        <b>${h.parameter}:</b> <span style="opacity:0.5;">${JSON.stringify(h.from)}</span> ➔ <span style="color:#00ff88;">${JSON.stringify(h.to)}</span>
                                    </div>
                                `).reverse().join('')}
                            </div>
                        </div>
                    ` : ''}

                    ${node.status === 'FAILED' ? `
                        <div class="inspector-action-bar">
                            <button onclick="window.omniShell.addInput('rescue job ${node.id}')" class="pizarron-btn-mini rescue-btn">⚛ REINTENTAR CONTEXTUAL</button>
                            <p style="font-size: 0.6rem; margin-top: 5px; opacity: 0.5;">Lanzar Shadow de Rescate sobre este nodo.</p>
                        </div>
                    ` : ''}

                    ${node.status === 'NEEDS_REVIEW' && ev.rescue_result ? `
                        <div class="inspector-action-bar" style="background: rgba(255, 170, 0, 0.05); padding: 10px; border-radius: 8px;">
                            <span style="color: #ffaa00; font-size: 0.65rem; font-weight: bold; display: block; margin-bottom: 8px;">AUDITORÍA DE RESCATE REQUERIDA</span>
                            <button onclick="window.omniShell.addInput('approve rescue ${node.id}')" class="pizarron-btn-mini" style="background: #00ff88; color: #000; width: 100%;">✓ APROBAR Y APLICAR FIX</button>
                        </div>
                    ` : ''}
                    
                    ${ev.self_correction_applied ? `
                        <div class="inspector-section" style="background: rgba(0, 255, 150, 0.05); border: 1px solid var(--pizarron-node-success); border-radius: 6px; padding: 10px; margin-bottom: 12px;">
                            <div style="display:flex; align-items: center; gap: 6px;">
                                <span style="font-size: 1rem;">🔄</span>
                                <b style="color: var(--pizarron-node-success); font-size: 0.7rem;">PROCESO: AUTO-CORRECCIÓN APLICADA</b>
                            </div>
                            <p style="font-size: 0.65rem; color: #aaa; margin-top: 4px;">El Swarm detectó una propuesta inicial frágil y generó un redraft automático más prudente.</p>
                        </div>
                    ` : ''}

                    ${ev.multi_agent_conflict ? `
                        <div class="inspector-section conflict-box animate-pulse" style="background: rgba(255, 50, 50, 0.1); border: 2px solid #ff4444; border-radius: 8px; padding: 12px; margin-bottom: 12px;">
                            <div style="display:flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                                <span style="font-size: 1.2rem;">⚔️</span>
                                <b style="color: #ff4444; font-size: 0.75rem;">CONFLICTO MULTI-AGENTE: ${ev.multi_agent_conflict.type.toUpperCase()}</b>
                            </div>
                            <p style="font-size: 0.7rem; margin: 4px 0; color: #fff;">${ev.multi_agent_conflict.explanation}</p>
                            <div style="margin-top: 10px; font-size: 0.6rem; opacity: 0.8; background: rgba(255,255,255,0.05); padding: 8px; border-radius: 4px;">
                                <b style="color: var(--pizarron-accent);">ESTRATEGIA RECOMENDADA:</b> ${ev.multi_agent_conflict.resolution_strategy.toUpperCase()}
                            </div>
                        </div>
                    ` : ''}

                    <div class="inspector-section">
                        <span class="section-title">EVIDENCIA OPERATIVA</span>
                        <p style="font-size: 0.75rem; margin-top: 5px; color: #ddd;">${node.evidence || ev.summary || "No hay resultados registrados."}</p>
                    </div>

                    ${renderCognitiveTrace(trace)}

                    ${ev.output || ev.trace ? `
                        <div class="inspector-section">
                            <span class="section-title">TRAZA DE EJECUCIÓN</span>
                            <pre class="inspector-pre">${ev.output || ev.trace}</pre>
                        </div>
                    ` : ''}

                    ${hasDiff ? `
                        <div class="inspector-section">
                            <span class="section-title">EVOLUCIÓN DE CÓDIGO (DIFF)</span>
                            <div class="inspector-diff">
                                ${ev.diff ? `<pre style="color: #00ff88; font-size: 0.65rem; background: rgba(0,255,136,0.05); padding: 8px; border-radius: 4px;">${ev.diff}</pre>` :
                        (ev.changes || []).map(c => `<div style="font-size: 0.65rem; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);"><b>${c.file}:</b> ${c.explanation}</div>`).join('')}
                            </div>
                            <button onclick="window.omniShell.addInput('view diff ${node.id}')" class="pizarron-btn-mini">EXAMINAR EN EDITOR</button>
                        </div>
                    ` : ''}

                    ${node.status === 'FAILED' ? `
                        <div class="inspector-section critical">
                            <span class="section-title" style="color: #ff4444;">DETALLE DEL FALLO</span>
                            <pre class="inspector-pre" style="color: #ff4444; border-color: rgba(255,0,0,0.2);">${ev.error || "Error no especificado."}</pre>
                        </div>
                    ` : ''}
                </div>
            `;
        };

        const findNodeById = (root, id) => {
            if (String(root.id) === String(id)) return root;
            if (root.children) {
                for (let child of root.children) {
                    const found = findNodeById(child, id);
                    if (found) return found;
                }
            }
            return null;
        };

        const selectedNode = this.selectedNodeId && executionTree ? findNodeById(executionTree.root, this.selectedNodeId) : null;

        container.innerHTML = `
            <style>
                .pizarron-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
                @media (max-width: 768px) { .pizarron-grid { grid-template-columns: 1fr; } }
                .pizarron-card { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06); padding: 15px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); backdrop-filter: blur(8px); min-width: 0; }
                .pizarron-tree-node { padding: 6px 10px; margin-bottom: 2px; border-radius: 4px; transition: all 0.2s; border-left: 2px solid transparent; }
                .pizarron-tree-node:hover { background: rgba(255,255,255,0.05); }
                .pizarron-tree-node.selected { background: rgba(0, 150, 255, 0.1); border-left: 2px solid var(--pizarron-accent); }
                .pizarron-inspector { padding: 15px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; height: 100%; min-height: 200px; overflow-y: auto; }
                .inspector-section { margin-bottom: 15px; }
                .section-title { font-size: 0.6rem; opacity: 0.4; letter-spacing: 1px; font-weight: bold; text-transform: uppercase; }
                .inspector-pre { background: rgba(0,0,0,0.3); padding: 10px; border-radius: 4px; font-size: 0.65rem; border: 1px solid rgba(255,255,255,0.05); overflow-x: auto; margin-top: 5px; font-family: 'Fira Code', monospace; line-height: 1.4; color: #acc; }
                .pizarron-btn-mini { background: var(--pizarron-accent); color: #000; border: none; padding: 5px 10px; border-radius: 4px; font-size: 0.65rem; cursor: pointer; margin-top: 10px; font-weight: bold; transition: opacity 0.2s; }
                .pizarron-btn-mini:hover { opacity: 0.8; }
                .animate-slide-in { animation: slideIn 0.3s ease-out; }
                @keyframes slideIn { from { opacity: 0; transform: translateX(10px); } to { opacity: 1; transform: translateX(0); } }
                .pizarron-status-active { animation: pulse-active 2s infinite; }
                .pizarron-status-recovering { animation: pulse-recovery 1.5s infinite; border-left-color: #ffcc00 !important; }
                @keyframes pulse-active { 0% { background: rgba(0, 150, 255, 0.05); } 50% { background: rgba(0, 150, 255, 0.15); } 100% { background: rgba(0, 150, 255, 0.05); } }
                @keyframes pulse-recovery { 0% { background: rgba(255, 200, 0, 0.05); } 50% { background: rgba(255, 200, 0, 0.2); } 100% { background: rgba(255, 200, 0, 0.05); } }
                .status-badge { font-size: 0.55rem; padding: 2px 6px; border-radius: 10px; font-weight: bold; width: fit-content; margin-top: 4px; text-transform: uppercase; }
                .status-failed { background: rgba(255, 0, 0, 0.2); color: #ff4444; }
                .status-completed { background: rgba(0, 255, 136, 0.2); color: #00ff88; }
                .status-recovering { background: rgba(255, 200, 0, 0.2); color: #ffcc00; }
                .status-active { background: rgba(0, 150, 255, 0.2); color: #0096ff; }
                .recovery-text { color: #ffcc00; font-size: 0.6rem; margin-left: 10px; font-weight: bold; letter-spacing: 1px; }
                .rescue-btn { background: #ffcc00 !important; color: #000 !important; width: 100%; padding: 10px !important; margin-bottom: 10px; box-shadow: 0 4px 10px rgba(255,200,0,0.2); }
                .inspector-action-bar { border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 15px; margin-bottom: 15px; }
            </style>
            <div class="pizarron-grid">
                <!-- Header Card -->
                <section class="pizarron-card" style="grid-column: span 2;">
                    <h4><span style="color: var(--pizarron-accent)">⚛</span> Dashboard Cognitivo: ${mission.status}</h4>
                    <div class="pizarron-mission" style="display: flex; justify-content: space-between; align-items: flex-start; gap: 20px;">
                        <div style="flex: 1;">${summary}</div>
                        ${paramBadges.length > 0 ? `
                        <div style="display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end;">
                            ${paramBadges.map(b => `
                                <div style="display: flex; align-items: center; gap: 4px; background: rgba(255,255,255,0.05); border: 1px solid ${b.color}; padding: 3px 8px; border-radius: 6px; font-size: 0.55rem; color: ${b.color}; font-weight: bold; letter-spacing: 0.5px;">
                                    <span>${b.icon}</span>
                                    <span>${b.label}</span>
                                </div>
                            `).join('')}
                        </div>
                        ` : ''}
                    </div>
                    
                    ${mission.telemetry_snap ? `
                        <div class="pizarron-telemetry" style="margin-top: 10px; padding: 8px; background: rgba(255,255,255,0.03); border-radius: 4px; border-left: 3px solid ${mission.telemetry_snap.status_color || 'var(--pizarron-accent)'}; font-size: 0.75rem;">
                            <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                <span style="opacity: 0.6; font-size: 0.6rem; letter-spacing: 1px;">SINCRO TELEMETRÍA</span>
                                <span style="font-size: 0.6rem; opacity: 0.4;">Sync: ${mission.telemetry_snap.last_sync}</span>
                            </div>
                            <div style="font-weight: bold; color: ${mission.telemetry_snap.status_color || '#fff'};">${mission.telemetry_snap.last_event || 'Sincronizando...'}</div>
                            ${mission.telemetry_snap.current_evidence ? `<div style="font-size: 0.65rem; color: #fff; margin-top: 4px; opacity: 0.7; font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">⚡ ${mission.telemetry_snap.current_evidence}</div>` : ''}
                        </div>
                    ` : ''}
                </section>

                <!-- Plan & Inspector Row -->
                <section class="pizarron-card" style="grid-column: span ${selectedNode ? '1' : '2'}; grid-row: span 2;">
                    <h4><span style="color: var(--pizarron-accent)">⚡</span> Plan de Ejecución</h4>
                    <div class="pizarron-tree-container" style="margin-top: 12px; max-height: 480px; overflow-y: auto;">
                        ${executionTree ? renderTreeNode(executionTree.root) : '<p style="opacity: 0.4; font-size: 0.75rem;">Generando roadmap jerárquico...</p>'}
                    </div>
                </section>

                ${selectedNode ? `
                    <section class="pizarron-card" style="grid-column: span 1; grid-row: span 2;">
                        ${renderInspector(selectedNode)}
                    </section>
                ` : `
                    <section class="pizarron-card">
                        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <h4 style="margin:0;"><span style="color: var(--pizarron-accent)">🔒</span> Checkpoints</h4>
                            <button onclick="window.omniShell.addInput('checkpoint mission')" class="pizarron-btn-mini" style="background: rgba(255,204,0,0.1); border: 1px solid #ffcc00; color: #ffcc00;">+ CREAR</button>
                        </div>
                        <div style="max-height: 100px; overflow-y: auto; font-size: 0.65rem;">
                            ${(mission.context_snap.checkpoints || []).length === 0 ? '<div style="opacity:0.3; padding: 5px;">Sin snapshots.</div>' :
                mission.context_snap.checkpoints.slice().reverse().map(cp => `
                                <div style="display:flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05);">
                                    <span title="${cp.label}">${cp.id}</span>
                                    <button onclick="window.omniShell.addInput('rollback mission ${cp.id}')" class="pizarron-btn-mini" style="background: #ff4444; color: #fff; padding: 1px 4px;">ROLLBACK</button>
                                </div>
                            `).join('')}
                        </div>
                    </section>
                    <section class="pizarron-card">
                        <h4><span style="color: var(--pizarron-accent)">📂</span> Contexto</h4>
                        <div style="font-size: 0.7rem; color: #aaa;">
                            <span style="display:block; margin-bottom:4px;">TARGETS: ${mission.related_targets.join(', ') || 'Global'}</span>
                            <span>RIESGO: ${risk_level}</span>
                            <div style="margin-top:8px; opacity:0.6; font-size:0.6rem;">
                                ${forbidden_zones.length > 0 ? forbidden_zones.map(z => `<div>⚠ ${z}</div>`).join('') : 'Sin zonas prohibidas.'}
                            </div>
                        </div>
                    </section>
                `}

                <!-- Proposals Block -->
                ${data.proposals && data.proposals.length > 0 ? `
                <section class="pizarron-card" style="grid-column: span 2;">
                    <h4><span style="color: var(--pizarron-accent)">🛠</span> Propuestas de Mejora (${data.proposals.length})</h4>
                    <div style="max-height: 180px; overflow-y: auto; margin-top: 8px;">
                        ${data.proposals.map(p => `
                            <div class="shadow-item shadow-constructor" style="background: rgba(255,255,255,0.02); padding: 8px; border-radius: 4px; margin-bottom: 5px; border: 1px solid rgba(255,255,255,0.05);">
                                <div style="display:flex; justify-content: space-between; font-size: 0.6rem; opacity: 0.5; margin-bottom: 4px;">
                                    <span>${p.proposal_id}</span>
                                    <span>PENDIENTE</span>
                                </div>
                                <div style="font-size: 0.75rem;"><b>${p.action_type}:</b> ${p.targets[0]}</div>
                                <div style="margin-top: 6px;">
                                    <button onclick="window.omniShell.addInput('approve ${p.proposal_id}')" style="background: #00ff88; color: #000; border: none; padding: 3px 8px; border-radius: 3px; font-size: 0.6rem; cursor: pointer; font-weight: bold;">APROBAR</button>
                                    <button onclick="window.omniShell.addInput('reject ${p.proposal_id}')" style="background: #ff4444; color: #fff; border: none; padding: 3px 8px; border-radius: 3px; font-size: 0.6rem; cursor: pointer; margin-left: 5px;">RECHAZAR</button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </section>
                ` : ''}
            </div>
        `;
    }

    selectNode(nodeId) {
        this.selectedNodeId = (this.selectedNodeId === nodeId) ? null : nodeId;
        if (window.creator && window.creator.systemState) {
            window.creator.renderWorkspaceMissionDashboard(window.creator.systemState);
        }
    }
}

window.pizarronUI = new PizarronVivoUI();
