class PizarronVivoUI {
    constructor() {
        this.id = 'pizarron-vivo-embedded';
        this.lastDataHash = null;
        this.selectedNodeId = null;
        this.activeMissionId = null;
        this.portfolioMount = null;

        // PHASE 64: Start drift monitoring poll
        this.startDriftAlertPolling();
    }

    startDriftAlertPolling() {
        setInterval(async () => {
            try {
                const res = await fetch('/api/v1/ai-host/execution/portfolio/drift/alerts', {
                    headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
                });
                const data = await res.json();
                if (data.status === 'success' && data.alerts.length > 0) {
                    data.alerts.forEach(alert => this.showDriftToast(alert));
                    // Refresh portfolio if visible
                    if (this.loadPortfolioDrift) this.loadPortfolioDrift();
                }
            } catch (err) {
                console.debug("Alert polling failed", err);
            }
        }, 30000); // 30 seconds
    }

    showDriftToast(alert) {
        const toast = document.createElement('div');
        const severityColor = {
            'CRITICAL': '#ff4444',
            'WARNING': '#ffcc00',
            'ATTENTION': '#00e5ff'
        }[alert.severity] || '#fff';

        toast.style = `
            position: fixed; top: 20px; right: 20px; width: 300px;
            background: rgba(20, 20, 30, 0.85); backdrop-filter: blur(12px);
            border-left: 4px solid ${severityColor}; border-radius: 8px;
            padding: 12px; color: #fff; z-index: 10000;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            font-family: 'Outfit', sans-serif; cursor: pointer;
            animation: drift-toast-in 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28);
            display: flex; flex-direction: column; gap: 6px;
        `;

        toast.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.6rem; color:${severityColor}; font-weight:bold; letter-spacing:1px;">⚠️ COGNITIVE DRIFT: ${alert.severity}</span>
                <span style="font-size:0.5rem; opacity:0.5;" onclick="this.parentElement.parentElement.remove()">✕</span>
            </div>
            <div style="font-size:0.75rem; font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${alert.goal}</div>
            <div style="font-size:0.65rem; color:#ccc; line-height:1.2;"><b>Motivo:</b> ${alert.reason}</div>
            <div style="margin-top:4px; display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.6rem; color:#888;">ID: ${alert.mission_id.substring(0, 8)}</span>
                <span style="font-size:0.6rem; color:${severityColor}; text-decoration:underline;">REVISAR AHORA</span>
            </div>
        `;

        // Inject animation if not exists
        if (!document.getElementById('drift-toast-styles')) {
            const styles = document.createElement('style');
            styles.id = 'drift-toast-styles';
            styles.textContent = `
                @keyframes drift-toast-in {
                    from { transform: translateX(120%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(styles);
        }

        toast.onclick = () => {
            if (this.loadMultimodalReport) {
                this.loadMultimodalReport(alert.mission_id);
                toast.style.transform = 'translateX(120%)';
                setTimeout(() => toast.remove(), 400);
            }
        };

        document.body.appendChild(toast);
        setTimeout(() => { if (toast.parentElement) toast.style.transform = 'translateX(120%)'; }, 7000);
        setTimeout(() => { if (toast.parentElement) toast.remove(); }, 7500);
    }

    renderMissionTelemetry(events) {
        if (!events || events.length === 0) return '';

        return `
            <div class="pizarron-card" style="margin-bottom: 20px; border-left: 3px solid var(--pizarron-accent);">
                <h4 style="font-size: 0.75rem; color: var(--pizarron-accent); text-transform: uppercase; margin-bottom: 15px; font-family: 'Outfit'; letter-spacing: 1px;">Mission Timeline (Telemetría)</h4>
                <div class="telemetry-list" style="display:flex; flex-direction: column; gap: 10px;">
                    ${events.map(e => `
                        <div class="telemetry-item" style="font-size: 0.75rem; display: flex; gap: 12px; align-items: flex-start;">
                            <div class="telemetry-severity" style="width: 4px; height: 100%; min-height: 20px; border-radius: 2px; background: ${e.severity === 'ERROR' ? '#ff4444' : (e.severity === 'WARNING' ? '#ffaa00' : '#32ff96')}; opacity: 0.6; flex-shrink: 0;"></div>
                            <div style="flex: 1;">
                                <div style="display:flex; justify-content: space-between; margin-bottom: 2px;">
                                    <span style="font-weight: 600; color: #fff; font-size: 0.7rem;">${e.event_type.replace(/_/g, ' ').toUpperCase()}</span>
                                    <div style="display:flex; align-items: center; gap: 8px;">
                                        ${e.source_actor && e.source_actor !== 'system' ? `<span style="font-size: 0.55rem; background: rgba(255,255,255,0.05); padding: 1px 4px; border-radius: 3px; color: var(--pizarron-accent); border: 1px solid rgba(50,255,150,0.1); font-family: monospace;">${e.source_actor}</span>` : ''}
                                        <span style="opacity: 0.4; font-size: 0.6rem;">${new Date(e.timestamp).toLocaleTimeString()}</span>
                                    </div>
                                </div>
                                <div style="color: #ccc; opacity: 0.8; line-height: 1.3; font-size: 0.7rem;">${e.message}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderRecentTelemetry(pulse) {
        if (!pulse || pulse.length === 0) return '';
        return `
            <div style="margin-top: 30px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 20px; text-align: left;">
                <h4 style="font-size: 0.65rem; color: #888; text-transform: uppercase; margin-bottom: 12px;">Últimos Eventos de Sistema</h4>
                <div style="max-height: 150px; overflow-y: auto;">
                    ${pulse.map(e => `
                        <div style="font-size: 0.7rem; margin-bottom: 8px; display:flex; gap: 8px; opacity: 0.7; align-items: center;">
                            <span style="color: #888;">[${new Date(e.timestamp).toLocaleTimeString()}]</span>
                            <span style="color: ${e.severity === 'ERROR' ? '#ff4444' : '#32ff96'}; font-weight: bold; font-family: monospace; font-size: 0.6rem; border: 1px solid rgba(255,255,255,0.05); padding: 0 3px; border-radius: 2px;">${(e.source_actor || 'sys').substring(0, 12)}</span>
                            <span style="color: #fff; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">${e.message}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderPortfolio(container, state) {
        if (!container || !state) return;
        this.portfolioMount = container;

        const active = state.active_mission;
        const parallel = (state.parallel_missions || []).filter(p => !active || p.id !== active.mission_id);
        const archived = state.archived_missions || [];
        const completed = state.completed_missions || [];
        const locks = state.resource_locks || [];
        const pulse = state.portfolio_pulse || [];

        // Helper for status colors
        const getStatusColor = (status) => {
            if (status === 'RUNNING') return '#32ff96';
            if (status === 'BLOCKED') return '#ffaa00';
            if (status === 'FAILED') return '#ff4444';
            if (status === 'COMPLETED') return 'var(--pizarron-accent)';
            return '#aaa';
        };

        const renderMissionCard = (m, isFocus = false) => {
            const mId = m.id || m.mission_id;
            const mGoal = m.active_goal || m.goal;
            const mStatus = m.status;
            const mUpdated = m.updated || m.last_focused;
            const mPriority = m.priority_class || 'NORMAL';
            const mReadiness = m.readiness_state || 'READY';
            const mScore = m.priority_score || 0;

            const getPriorityColor = (p) => {
                if (p === 'URGENT') return '#ff003c';
                if (p === 'HIGH') return '#ff8800';
                if (p === 'BACKGROUND') return '#555';
                return '#aaa';
            };

            const getReadinessColor = (r) => {
                if (r === 'READY') return '#32ff96';
                if (r === 'WAITING_RESOURCE') return '#0096ff';
                if (r === 'PAUSED_BY_GOVERNANCE') return '#ffaa00';
                if (r === 'BLOCKED_BY_ERROR') return '#ff4444';
                return '#888';
            };

            return `
                <div class="mission-portfolio-card ${isFocus ? 'focus' : ''}" 
                     onclick="window.omniShell.addInput('switch mission ${mId}')"
                     style="background: rgba(255,255,255,0.03); border: 1px solid ${isFocus ? 'var(--pizarron-accent)' : 'rgba(255,255,255,0.05)'}; padding: 12px; border-radius: 8px; margin-bottom: 10px; cursor: pointer; transition: all 0.3s; position: relative; overflow: hidden; border-left: 4px solid ${isFocus ? 'var(--pizarron-accent)' : getStatusColor(mStatus)};">
                    <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 0.55rem; color: #888; font-family: monospace;">#${mId.substring(0, 8)}</span>
                        <span style="font-size: 0.6rem; color: ${getStatusColor(mStatus)}; font-weight: bold; text-transform: uppercase;">${mStatus} ${isFocus ? '[FOCUS]' : ''}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #fff; font-weight: 600; margin-bottom: 8px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${mGoal}</div>
                    
                    <div style="display:flex; gap: 8px; margin-bottom: 8px;">
                        <span style="font-size: 0.5rem; background: ${getPriorityColor(mPriority)}; color: #fff; padding: 1px 4px; border-radius: 3px; font-weight: bold; text-transform: uppercase;">${mPriority}</span>
                        <span style="font-size: 0.5rem; background: rgba(255,255,255,0.05); border: 1px solid ${getReadinessColor(mReadiness)}; color: ${getReadinessColor(mReadiness)}; padding: 1px 4px; border-radius: 3px; font-weight: bold;">${mReadiness.replace(/_/g, ' ')}</span>
                    </div>

                    <div style="display:flex; justify-content: space-between; font-size: 0.65rem; opacity: 0.7; align-items: center;">
                        <span>Score: ${mScore.toFixed(1)}</span>
                        <span>Ref: ${mUpdated ? new Date(mUpdated).toLocaleTimeString() : 'N/A'}</span>
                    </div>
                </div>
            `;
        };

        container.innerHTML = `
            <div class="portfolio-dashboard" style="padding: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px;">
                
                ${state.recommended_focus ? `
                    <div class="recommended-focus-banner" 
                         onclick="window.omniShell.addInput('switch mission ${state.recommended_focus.id}')"
                         style="grid-column: 1 / -1; background: linear-gradient(90deg, rgba(50,255,150,0.1), transparent); border: 1px solid rgba(50,255,150,0.2); padding: 15px; border-radius: 12px; display: flex; align-items: center; gap: 15px; cursor: pointer; animation: pulse-glow 2s infinite;">
                        <div style="width: 40px; height: 40px; border-radius: 20px; background: rgba(50,255,150,0.2); display: flex; align-items: center; justify-content: center; color: var(--pizarron-accent); font-size: 1.2rem;">
                            <span class="icon">🎯</span>
                        </div>
                        <div style="flex:1;">
                            <div style="font-size: 0.65rem; color: var(--pizarron-accent); font-weight: bold; text-transform: uppercase;">FOCO RECOMENDADO</div>
                            <div style="font-size: 0.9rem; color: #fff; font-weight: 600;">${state.recommended_focus.goal}</div>
                            <div style="font-size: 0.7rem; color: #888;">${state.recommended_focus.reason} — Haz clic para cambiar el foco.</div>
                        </div>
                        <div style="font-size: 0.7rem; color: var(--pizarron-accent); border: 1px solid var(--pizarron-accent); padding: 4px 10px; border-radius: 5px;">CAMBIAR FOCO</div>
                    </div>
                ` : ''}

                <style>
                @keyframes pulse-glow {
                    0% { box-shadow: 0 0 0 0 rgba(50,255,150,0.1); }
                    70% { box-shadow: 0 0 0 10px rgba(50,255,150,0); }
                    100% { box-shadow: 0 0 0 0 rgba(50,255,150,0); }
                }
                </style>

                <!-- Column 1: LIVE CLUSTER (Misiones Activas y en Foco) -->
                <div class="portfolio-column">
                    <h3 style="color: var(--pizarron-accent); margin-bottom: 15px; font-family: 'Outfit'; font-size: 0.9rem; border-bottom: 1px solid rgba(50, 255, 150, 0.2); padding-bottom: 8px; display: flex; justify-content: space-between;">
                        <span>CLUSTER EN VIVO</span>
                        <span style="opacity: 0.5; font-size: 0.7rem;">${(active ? 1 : 0) + parallel.filter(p => p.status === 'RUNNING').length}</span>
                    </h3>
                    ${active ? renderMissionCard(active, true) : ''}
                    ${parallel.filter(p => p.status === 'RUNNING').map(p => renderMissionCard(p)).join('')}
                    ${(!active && parallel.filter(p => p.status === 'RUNNING').length === 0) ? '<div style="opacity: 0.3; font-size: 0.75rem; text-align:center; padding: 20px; border: 1px dashed #333;">SIN ACTIVIDAD VIVA</div>' : ''}
                </div>

                <!-- Column 2: BLOCKS & CONFLICTS -->
                <div class="portfolio-column">
                    <h3 style="color: #ffaa00; margin-bottom: 15px; font-family: 'Outfit'; font-size: 0.9rem; border-bottom: 1px solid rgba(255, 170, 0, 0.2); padding-bottom: 8px; display: flex; justify-content: space-between;">
                        <span>BLOQUEOS & ESPERA</span>
                        <span style="opacity: 0.5; font-size: 0.7rem;">${parallel.filter(p => p.status === 'BLOCKED').length}</span>
                    </h3>
                    ${parallel.filter(p => p.status === 'BLOCKED').map(p => renderMissionCard(p)).join('')}
                    ${(parallel.filter(p => p.status === 'BLOCKED').length === 0) ? '<div style="opacity: 0.3; font-size: 0.75rem; text-align:center; padding: 20px; border: 1px dashed #333;">FLUJO LIBRE</div>' : ''}
                    
                    <div style="margin-top: 20px; border: 1px solid rgba(255,170,0,0.1); border-radius: 6px; padding: 10px; background: rgba(255,170,0,0.02);">
                        <h4 style="font-size: 0.65rem; color: #ffaa00; text-transform: uppercase; margin-bottom: 8px;">Resource Conflict Trace</h4>
                        ${locks.length === 0 ? '<div style="font-size: 0.6rem; opacity: 0.4;">Sin semáforos activos.</div>' : locks.map(l => `
                            <div style="font-size: 0.65rem; margin-bottom: 4px; display:flex; justify-content: space-between; font-family: monospace;">
                                <span style="color: #ffaa00;">${l.resource_key}</span>
                                <span style="opacity: 0.6;">⏼ ${l.mission_id.substring(0, 8)}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Column 3: ARCHIVE & HISTORY -->
                <div class="portfolio-column">
                    <h3 style="color: #888; margin-bottom: 15px; font-family: 'Outfit'; font-size: 0.9rem; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 8px;">
                        HISTORIAL OPERATIVO
                    </h3>
                    <div style="max-height: 400px; overflow-y: auto; padding-right: 5px;">
                        <div style="margin-bottom: 15px;">
                            <h4 style="font-size: 0.6rem; opacity: 0.5; margin-bottom: 8px;">RECIÉN COMPLETADAS</h4>
                            ${completed.map(m => renderMissionCard(m)).join('')}
                        </div>
                    </div>

                    <!-- Portfolio Pulse (Phase: MISSION CRITICAL TELEMETRY) -->
                    <div style="margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px;">
                        <h4 style="font-size: 0.6rem; color: var(--pizarron-accent); text-transform: uppercase; margin-bottom: 10px; letter-spacing: 0.5px;">Global Mission Pulse</h4>
                        <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; font-size: 0.65rem; line-height: 1.4; max-height: 120px; overflow-y: auto;">
                            ${pulse.length === 0 ? '<div style="opacity: 0.3;">Esperando eventos de sistema...</div>' : pulse.map(e => `
                                <div style="margin-bottom: 6px; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 4px;">
                                    <span style="opacity: 0.4;">[${new Date(e.timestamp).toLocaleTimeString()}]</span>
                                    <span style="color: ${e.severity === 'ERROR' ? '#ff4444' : '#32ff96'};"> ${e.event_type}</span>
                                    <div style="opacity: 0.7;">${e.message}</div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
            <div style="padding: 15px 20px; border-top: 1px solid rgba(255,255,255,0.05); display: flex; gap: 12px;">
                <button class="ws-btn" onclick="window.omniShell.addInput('mission portfolio rebase')" style="font-size: 0.6rem;">REBASE GLOBAL</button>
                <button class="ws-btn" onclick="window.omniShell.addInput('mission cleanup archived')" style="font-size: 0.6rem;">LIMPIAR HISTORIAL</button>
                <div style="margin-left: auto; font-size: 0.6rem; opacity: 0.4; align-self: center;">Sincronización: Nominal</div>
            </div>
        `;
    }

    renderInto(container, data) {
        if (!container || !data) return;
        const mission = data.mission || data.active_mission || null;

        const currentHash = JSON.stringify(mission) + this.selectedNodeId + (data.proposals ? data.proposals.length : 0);
        if (this.lastDataHash === currentHash) return;
        this.lastDataHash = currentHash;

        if (!mission || (mission.status === 'IDLE' || mission.status === 'COMPLETED' || !mission.active_goal)) {
            const handoff = data.last_handoff || null;
            if (handoff) {
                container.innerHTML = this.renderHandoffCard(handoff);
                return;
            }
            container.innerHTML = `
                <div class="pizarron-card pizarron-empty-state">
                    <h3 style="color: var(--pizarron-accent); font-family: 'Outfit';">SIN MISIÓN ACTIVA</h3>
                    <p style="font-size: 0.85rem; margin-top: 10px; opacity: 0.6;">OmniWeb está en espera.</p>
                    ${this.renderRecentTelemetry(data.portfolio_pulse || [])}
                </div>
            `;
            return;
        }

        // Auto-trigger wisdom, replay and simulation for root
        if (mission.mission_id) {
            setTimeout(() => {
                this.loadPreventiveWisdom(mission.mission_id);
                this.loadCognitiveReplay(mission.mission_id);
                this.loadMissionSimulation(mission.mission_id);
            }, 500);
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

        // Operational Context (Ergonomics Phase 21)
        const opCtx = mission.context_snap?.operational_context;
        if (opCtx) {
            const ctxMap = {
                'CORRECTION': { label: 'CORRECCIÓN', icon: '🔧', color: '#ffcc00' },
                'BRANCH': { label: 'RAMIFICACIÓN', icon: '🌿', color: '#00ff88' },
                'FOLLOWUP': { label: 'CONTINUACIÓN', icon: '⏭️', color: '#00ccff' },
                'REORIENT': { label: 'RE-ORIENTACIÓN', icon: '🎯', color: '#ff8800' }
            };
            if (ctxMap[opCtx]) paramBadges.unshift(ctxMap[opCtx]);
        }

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

        const renderVisualEvidence = (vCtx) => {
            if (!vCtx || !vCtx.source_image) return '';
            const hyp = vCtx.hypothesis || { description: "Analizando síntomas visuales...", layer: "N/A" };
            const annotations = vCtx.annotations || [];

            return `
                <div class="inspector-section visual-evidence" style="background: rgba(255,170,0,0.05); padding: 12px; border-radius: 8px; border: 1px solid rgba(255,170,0,0.1); margin-bottom: 12px;">
                    <div style="display:flex; align-items:center; gap: 8px; margin-bottom: 10px;">
                        <span style="font-size: 1rem;">📸</span>
                        <span class="section-title" style="color: #ffaa00; margin-bottom: 0;">EVIDENCIA RECOLECTADA</span>
                    </div>
                    
                    <div style="display:flex; gap: 15px; align-items: flex-start;">
                        <div class="pizarron-annotated-preview" style="position: relative; width: 100px; height: 100px; background: #000; border-radius: 6px; overflow: hidden; border: 2px solid rgba(255,170,0,0.2); flex-shrink: 0;">
                            <img src="${vCtx.source_image}" style="width:100%; height:100%; object-fit: cover;" alt="Visual Evidence">
                            ${annotations.map((a, idx) => {
                if (a.type === 'point') return `<div style="position:absolute; left:${a.x}%; top:${a.y}%; width:10px; height:10px; background:#ffaa00; border:1px solid #fff; border-radius:50%; transform:translate(-50%, -50%); box-shadow:0 0 5px #ffaa00; z-index:5;"></div>`;
                if (a.type === 'box') return `<div style="position:absolute; left:${a.x}%; top:${a.y}%; width:${a.w}%; height:${a.h}%; border:1px solid #32ff96; background:rgba(50,255,150,0.2); z-index:4;"></div>`;
                return '';
            }).join('')}
                        </div>
                        <div style="flex:1;">
                            <div style="font-size: 0.65rem; color: #ffaa00; font-weight: bold; margin-bottom: 4px;">🎯 FOCO DEL DIAGNÓSTICO:</div>
                            <p style="font-size: 0.75rem; margin: 0; line-height: 1.3; font-family: 'Outfit';">
                                ${annotations.length > 0 ? (annotations.map(a => a.comment).join(' | ')) : hyp.description}
                            </p>
                            <div style="font-size: 0.6rem; opacity: 0.6; margin-top: 6px;">
                                <span style="background:rgba(255,255,255,0.05); padding:1px 6px; border-radius:10px; border:1px solid rgba(255,255,255,0.1);">
                                    🛰️ Hipótesis Swarm: <b>${hyp.layer}</b> (Confianza: ${Math.round(hyp.confidence * 100)}%)
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        };

        const renderVisualHistory = (history) => {
            if (!history || history.length < 2) return ''; // Solo mostrar si hay evolución

            return `
                <div class="inspector-section visual-history" style="margin-top: 20px; border-top: 1px solid rgba(255,170,0,0.1); padding-top: 15px;">
                    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom: 10px;">
                        <span class="section-title" style="color: #ffaa00; margin-bottom:0;">EVOLUCIÓN MULTIMODAL (DIFF VISUAL)</span>
                        <div style="display:flex; gap: 8px; font-size: 0.5rem; opacity: 0.7;">
                            <span style="color:#00ff88;">● Nueva</span>
                            <span style="color:#ff4444;">● Eliminada</span>
                            <span style="color:#ffaa00;">● Persistente</span>
                        </div>
                    </div>
                    
                    <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 15px;">
                        ${history.map((h, idx) => {
                const diff = h.visual_diff || null;
                const shift = h.hypothesis?.shift_detected || null;

                return `
                            <div style="display: flex; gap: 12px; opacity: ${idx === history.length - 1 ? 1 : 0.6}; transition: opacity 0.3s;">
                                <div style="display: flex; flex-direction: column; align-items: center;">
                                    <div style="width: 8px; height: 8px; border-radius: 50%; background: ${idx === 0 ? '#00e5ff' : (h.event === 'GATE_DECISION' ? '#ff4444' : '#ffaa00')}; border: 1px solid rgba(255,255,255,0.2);"></div>
                                    ${idx < history.length - 1 ? `<div style="width: 1px; flex: 1; background: rgba(255,255,255,0.1); margin: 4px 10px;"></div>` : ''}
                                </div>
                                <div style="flex: 1; background: rgba(255,255,255,0.02); padding: 8px; border-radius: 8px; border: 1px solid ${diff?.has_shift ? '#00ff88' : 'rgba(255,170,0,0.1)'};">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                        <b style="font-size: 0.6rem; color: #ffaa00;">${h.event.toUpperCase()}</b>
                                        <span style="font-size: 0.55rem; opacity: 0.4;">${h.timestamp.split('T')[1].split('.')[0]}</span>
                                    </div>
                                    
                                    <div style="display: flex; gap: 10px;">
                                        <!-- COMPARISON OVERLAY THUMBNAIL -->
                                        <div style="position: relative; width: 60px; height: 60px; border-radius: 4px; overflow: hidden; border: 1px solid rgba(255,170,0,0.3); flex-shrink: 0; background: #000;">
                                            <img src="${mission.visual_context.source_image}" style="width:100%; height:100%; object-fit: cover; opacity: 0.4;">
                                            
                                            ${/* Render Diff Markers */ ''}
                                            ${diff ? `
                                                ${(diff.removed_regions || []).map(r => `<div style="position:absolute; left:${r.x}%; top:${r.y}%; width:4px; height:4px; background:#ff4444; border-radius:50%; transform:translate(-50%, -50%); box-shadow: 0 0 5px #ff4444;"></div>`).join('')}
                                                ${(diff.persistent_regions || []).map(r => `<div style="position:absolute; left:${r.x}%; top:${r.y}%; width:2px; height:2px; background:#ffaa00; border-radius:50%; transform:translate(-50%, -50%);"></div>`).join('')}
                                                ${(diff.added_regions || []).map(r => `<div style="position:absolute; left:${r.x}%; top:${r.y}%; width:6px; height:6px; background:#00ff88; border-radius:50%; transform:translate(-50%, -50%); border: 1px solid #fff; box-shadow: 0 0 8px #00ff88;"></div>`).join('')}
                                            ` : `
                                                ${(h.annotations || []).map(a => `<div style="position:absolute; left:${a.x}%; top:${a.y}%; width:4px; height:4px; background:#ffaa00; border-radius:50%; transform:translate(-50%, -50%);"></div>`).join('')}
                                            `}
                                        </div>
                                        
                                        <div style="flex: 1;">
                                            <div style="font-size: 0.65rem; color: #eee; line-height: 1.2; font-family:'Outfit';">
                                                ${h.hypothesis?.description || "Análisis operativo."}
                                            </div>
                                            
                                            ${shift ? `<div style="font-size: 0.55rem; color: #00ff88; background: rgba(0,255,136,0.05); padding: 2px 5px; border-radius: 4px; display: inline-block; margin-top: 4px; border: 1px solid rgba(0,255,136,0.1);">🛰️ ${shift}</div>` : ''}
                                            
                                            ${h.creator_comment ? `<div style="font-size: 0.6rem; color: #00e5ff; margin-top: 4px; font-style: italic;">💬 "${h.creator_comment}"</div>` : ''}
                                            
                                            ${diff ? `
                                                <div style="display:flex; gap: 8px; margin-top: 6px; font-size: 0.5rem; opacity: 0.6;">
                                                    <span>+${diff.added_count} focalizadas</span>
                                                    <span>-${diff.removed_count} descartadas</span>
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
            }).join('')}
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

                    ${(node.id === executionTree.root.id) ? `
                        <!-- PHASE 70: PRE-MISSION PREVENTIVE WISDOM -->
                        <div id="preventive-wisdom-container" style="margin-bottom: 12px; display: none;">
                            <!-- Will be injected by loadPreventiveWisdom -->
                        </div>
                        <!-- PHASE 72: COGNITIVE FORESIGHT (WHAT-IF SIMULATION) -->
                        <div id="mission-simulation-container" style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; display: none;">
                             <!-- Simulation scenarios -->
                        </div>

                        <!-- PHASE 71: COGNITIVE REPLAY (FORENSIC REPLAY) -->
                        <div id="cognitive-replay-container" style="margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; display: none;">
                             <!-- Scrubber and step description -->
                        </div>
                        ${renderVisualEvidence(mission.visual_context)}
                    ` : ''}

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

                    <div id="mm-timeline-container" style="display:flex; flex-direction:column; gap:12px; max-height: 100vh; overflow-y: auto; padding-right:10px;">
                <div style="display:flex; gap:8px; margin-bottom:8px; align-items:center;">
                    <div style="font-size:0.5rem; color:#888; text-transform:uppercase;">Filtrar Archivo</div>
                    <input type="text" id="mm-archive-search" placeholder="Buscar por capa, error o comentario..." 
                           style="background:rgba(255,255,255,0.05); border:1px solid rgba(255,255,255,0.1); color:#fff; font-size:0.6rem; padding:4px 8px; border-radius:4px; flex-grow:1; outline:none;"
                           onkeyup="if(event.key === 'Enter') window.omniPizarron.searchMissionArchive('${report.mission_id}', this.value)">
                    <button class="pizarron-btn-mini" onclick="window.omniPizarron.searchMissionArchive('${report.mission_id}', document.getElementById('mm-archive-search').value)" style="margin:0;">🔍 BUSCAR</button>
                </div>
                <div id="mm-timeline-nodes-list" style="display:flex; flex-direction:column; gap:12px;">
                    ${report.timeline.map(node => this.renderTimelineNode(node)).join('')}
                </div>
            </div>
            <!-- PHASE 21: GOVERNANCE CONSOLIDATED DASHBOARD -->
                        <div class="inspector-section" style="background: rgba(0,0,0,0.3); border-radius: 12px; padding: 15px; border: 1px solid rgba(0,255,136,0.3); box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
                            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px;">
                                <div style="display: flex; flex-direction: column;">
                                    <span style="font-size: 0.55rem; color: #888; letter-spacing: 1px; font-weight: bold;">OMNI-SHIELD v1.0</span>
                                    <span style="font-size: 1rem; color: #fff; font-weight: bold; letter-spacing: -0.5px;">ESTADO DE SALUD</span>
                                </div>
                                <div id="governance-pulse" style="width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: rgba(0,255,136,0.1); border: 2px solid ${params.risk_consumed >= (params.risk_budget || 10) ? '#ffaa00' : params.cooldown_active ? '#00e5ff' : '#00ff88'}; box-shadow: 0 0 20px ${params.risk_consumed >= (params.risk_budget || 10) ? '#ffaa0033' : '#00ff8833'}; animation: pulse ${mission.status === 'OPEN' ? '1s' : '3s'} infinite;">
                                    <span style="font-size: 1.2rem;">${mission.status === 'OPEN' ? '🔥' : '🛡️'}</span>
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
                    
                    <!-- PHASE 21: MULTIMODAL APPROVAL EVIDENCE -->
                    ${ev.gate_decision ? `
                        <div class="inspector-section approval-evidence" style="background: rgba(255,170,0,0.05); border: 1px solid rgba(255,170,0,0.2); border-radius: 8px; padding: 12px; margin-bottom: 15px;">
                            <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                                <div style="display:flex; align-items: center; gap: 6px;">
                                    <span style="font-size: 1rem;">⚖️</span>
                                    <b style="color: #ffaa00; font-size: 0.75rem;">PROTOCOLO DE GOBERNANZA: ${ev.gate_decision.status}</b>
                                </div>
                                <span style="font-size: 0.6rem; padding: 2px 8px; border-radius: 10px; background: ${ev.gate_decision.danger_level === 'CRITICAL' ? '#ff0055' : '#ffaa00'}; color: #fff; font-weight: bold;">
                                    ${ev.gate_decision.danger_level}
                                </span>
                            </div>
                            
                            ${ev.gate_decision.visual_context ? `
                                <div style="display:flex; gap: 12px; margin: 10px 0; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px;">
                                    <div style="position: relative; width: 60px; height: 60px; border-radius: 4px; overflow: hidden; border: 1px solid rgba(255,170,0,0.3); flex-shrink: 0;">
                                        <img src="${ev.gate_decision.visual_context.source_image}" style="width:100%; height:100%; object-fit: cover;">
                                        ${(ev.gate_decision.visual_context.annotations || []).map(a => `<div style="position:absolute; left:${a.x}%; top:${a.y}%; width:4px; height:4px; background:#ffaa00; border-radius:50%; transform:translate(-50%, -50%);"></div>`).join('')}
                                    </div>
                                    <div style="flex:1;">
                                        <div style="font-size: 0.6rem; color: #aaa; margin-bottom: 2px;">EVIDENCIA VINCULADA:</div>
                                        <div style="font-size: 0.7rem; color: #fff; font-family: 'Outfit';">
                                            ${ev.gate_decision.visual_context.hypothesis?.description || "Análisis visual adjunto."}
                                        </div>
                                    </div>
                                </div>
                            ` : ''}

                            <div style="font-size: 0.65rem; color: #ddd; background: rgba(255,255,255,0.03); padding: 8px; border-radius: 4px; margin-top: 5px; border-left: 2px solid #ffaa00;">
                                <b style="opacity: 0.7;">RAZÓN OPERATIVA:</b> ${ev.gate_decision.blocking_reason || ev.gate_decision.result_summary}
                            </div>
                            
                            ${ev.gate_decision.status === 'awaiting_human_approval' ? `
                                <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 8px;">
                                    <button onclick="window.omniShell.addInput('approve ${ev.gate_decision.proposal_id}')" class="pizarron-btn-mini" style="background:#00ff88; color:#000; width:100%;">APROBAR CAMBIO</button>
                                    <div style="display: flex; gap: 8px;">
                                        <button onclick="window.omniShell.addInput('reject ${ev.gate_decision.proposal_id}')" class="pizarron-btn-mini" style="background:#ff4444; color:#fff; flex:1;">RECHAZAR</button>
                                        ${ev.gate_decision.visual_context ? `
                                            <button onclick="window.creatorEnv.openReAnnotation('${ev.gate_decision.visual_context.media_id}', '${node.id}')" class="pizarron-btn-mini" style="background:#00e5ff; color:#000; flex:1;">CORREGIR FOCO VISUAL</button>
                                        ` : ''}
                                    </div>
                                </div>
                            ` : ''}
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

                    ${(node.id === executionTree.root.id) ? renderVisualHistory(mission.multimodal_history) : ''}

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
                <!-- CAPA 5 (PHASE 80): DEEP RECOVERY PANEL -->
                ${this.renderRecoveryPanel(mission)}

                <!-- CAPA 1 & 3 (PHASE 80): CONSTITUTION AUDIT PANEL -->
                ${this.renderConstitutionAudit(mission)}

                <!-- Header Card -->
                <section class="pizarron-card" style="grid-column: span 2;">
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px; margin-bottom: 10px;">
                        <h4 style="margin: 0;"><span style="color: var(--pizarron-accent)">🎯</span> Misión en Foco</h4>
                        <span class="status-badge status-${mission.status.toLowerCase()}">${mission.status}</span>
                    </div>

                    ${data.parallel_missions && data.parallel_missions.length > 0 ? `
                        <div class="pizarron-parallel-monitor" style="margin-bottom: 12px; padding: 6px 10px; background: rgba(0,255,136,0.05); border: 1px solid rgba(0,255,136,0.2); border-radius: 4px;">
                            <div style="font-size: 0.55rem; color: #00ff88; font-weight: bold; letter-spacing: 1px; margin-bottom: 4px; display: flex; align-items: center; gap: 5px;">
                                <span>⚡</span> EJECUCIÓN EN PARALELO
                            </div>
                            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                                ${data.parallel_missions.map(p => `
                                    <div style="display: flex; align-items: center; gap: 6px; background: rgba(0,255,136,0.1); padding: 2px 8px; border-radius: 4px; border: 1px solid rgba(0,255,136,0.1);">
                                        <span style="font-size: 0.65rem; color: #eee;">${p.goal}</span>
                                        <button class="pizarron-btn-mini" style="background: rgba(0,255,136,0.2); color: #00ff88; border: 1px solid rgba(0,255,136,0.3); padding: 0 4px; font-size: 0.5rem;" onclick="window.omniShell.addInput('switch focus ${p.id}')">Foco</button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
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
                    
                    <!-- Mission Critical Telemetry (Phase: MISSION CRITICAL TELEMETRY) -->
                    ${this.renderMissionTelemetry(data.mission_events || [])}

                    <!-- PHASE 21: MISSION HIERARCHY & GRAPH -->
                    ${mission.hierarchy ? `
                        <div class="pizarron-hierarchy" style="margin-top: 12px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px solid rgba(255,170,0,0.15);">
                            <div style="font-size: 0.55rem; color: #ffaa00; font-weight: bold; letter-spacing: 1px; margin-bottom: 8px; display: flex; align-items: center; gap: 5px;">
                                <span>🌳</span> GRAFO DE MISIÓN
                            </div>
                            
                            <!-- Branch Context (Retried from / Branched from) -->
                            ${mission.hierarchy.retried_from ? `
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px; opacity: 0.5; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">
                                    <div style="font-size: 0.45rem; color: #aaa; background: #222; padding: 1px 4px; border-radius: 2px;">RE-INTENTO DE</div>
                                    <div style="font-size: 0.55rem; color: #999; font-style: italic;">
                                        ${mission.hierarchy.retried_from.goal}
                                    </div>
                                </div>
                            ` : ''}

                            ${mission.hierarchy.branched_from ? `
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px; opacity: 0.5; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 4px;">
                                    <div style="font-size: 0.45rem; color: #aaa; background: #222; padding: 1px 4px; border-radius: 2px;">RAMA DE</div>
                                    <div style="font-size: 0.55rem; color: #999; font-style: italic;">
                                        ${mission.hierarchy.branched_from.goal}
                                    </div>
                                </div>
                            ` : ''}

                            <!-- Parent -->
                            ${mission.hierarchy.parent ? `
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px; opacity: 0.7;">
                                    <div style="font-size: 0.6rem; color: #fff; background: #333; padding: 2px 6px; border-radius: 4px;">PADRE</div>
                                    <div style="font-size: 0.65rem; color: #00ccff; font-weight: bold; cursor: pointer;" onclick="window.omniShell.addInput('switch mission ${mission.hierarchy.parent.id}')">
                                        ${mission.hierarchy.parent.goal}
                                    </div>
                                    <span class="status-badge status-${mission.hierarchy.parent.status.toLowerCase()}" style="font-size: 0.45rem;">${mission.hierarchy.parent.status}</span>
                                </div>
                                <div style="height: 10px; border-left: 1px dashed rgba(255,255,255,0.2); margin-left: 15px; margin-bottom: 5px;"></div>
                            ` : ''}

                            <!-- Current (Self) -->
                            <div style="display: flex; align-items: center; gap: 8px; background: rgba(255,170,0,0.1); padding: 5px; border-radius: 4px; border: 1px solid rgba(255,170,0,0.3);">
                                <div style="font-size: 0.6rem; color: #000; background: #ffaa00; padding: 2px 6px; border-radius: 4px; font-weight: bold;">ACTUAL</div>
                                <div style="font-size: 0.7rem; color: #fff; font-weight: bold; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                    ${mission.active_goal}
                                </div>
                            </div>

                            <!-- Dependencies (Blocked by) -->
                            ${mission.hierarchy.dependencies && mission.hierarchy.dependencies.length > 0 ? `
                                <div style="margin-top: 10px; padding-left: 15px;">
                                    <div style="font-size: 0.55rem; color: #ff4444; margin-bottom: 4px;">DEPENDENCIAS (BLOQUEANTES)</div>
                                    ${mission.hierarchy.dependencies.map(d => `
                                        <div style="display: flex; align-items: center; gap: 6px; font-size: 0.6rem; color: #eee; margin-bottom: 2px;">
                                            <span style="color: #ff4444;">⛓</span>
                                            <span style="opacity: 0.8;">${d.goal}</span>
                                            <span class="status-badge status-${d.status.toLowerCase()}" style="font-size: 0.4rem;">${d.status}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : ''}

                            <!-- Sub-missions -->
                            ${mission.hierarchy.sub_missions && mission.hierarchy.sub_missions.length > 0 ? `
                                <div style="margin-top: 10px; padding-left: 15px; border-left: 1px dashed rgba(0,255,136,0.3);">
                                    <div style="font-size: 0.55rem; color: #00ff88; margin-bottom: 4px;">SUB-MISIONES</div>
                                    ${mission.hierarchy.sub_missions.map(s => {
            const isArchived = ["ARCHIVED", "ROLLED_BACK", "SUPERSEDED"].includes(s.status);
            return `
                                            <div style="display: flex; align-items: center; gap: 6px; font-size: 0.6rem; color: #eee; margin-bottom: 4px; cursor: pointer; transition: transform 0.2s; opacity: ${isArchived ? '0.4' : '1'}" onclick="window.omniShell.addInput('switch focus ${s.id}')" onmouseover="this.style.transform='translateX(5px)'" onmouseout="this.style.transform='translateX(0)'">
                                                <span style="color: ${isArchived ? '#666' : '#00ff88'};">${isArchived ? '⊘' : '↳'}</span>
                                                <span style="opacity: ${isArchived ? '0.6' : '0.9'}; text-decoration: ${isArchived ? 'line-through' : 'none'};">${s.goal}</span>
                                                <span class="status-badge status-${s.status.toLowerCase()}" style="font-size: 0.4rem;">${s.status}</span>
                                            </div>
                                        `;
        }).join('')}
                                </div>
                            ` : ''}
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
                            <h4 style="margin: 0;"><span style="color: var(--pizarron-accent)">🔒</span> Checkpoints</h4>
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
                    <section class="pizarron-card" id="mission-compact-digest-ws-section" style="border-left: 3px solid var(--pizarron-accent);">
                        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                            <h4 style="margin: 0;"><span style="color: var(--pizarron-accent)">📋</span> RESUMEN OPERATIVO</h4>
                            <span style="font-size: 0.5rem; opacity: 0.5; background: rgba(50,255,150,0.1); padding: 1px 4px; border-radius: 3px;">PHASE 53: COMPACT</span>
                        </div>
                        
                        ${mission.compact_digest ? `
                            <div style="font-size: 0.7rem; color: #fff; line-height: 1.4;">
                                <div style="font-weight: 600; color: #fff; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 8px;">
                                    ${mission.compact_digest.goal_compact}
                                </div>
                                
                                <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 15px;">
                                    <div style="background: rgba(255,255,255,0.03); padding: 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                                        <div style="font-size: 0.5rem; color: #888; text-transform: uppercase; margin-bottom: 4px;">Gobernanza</div>
                                        <div style="font-size: 0.8rem; font-weight: bold; color: ${mission.compact_digest.governance_score > 0.8 ? '#00ff88' : '#ffaa00'};">
                                            ${(mission.compact_digest.governance_score * 100).toFixed(0)}% <small style="font-weight: normal; opacity: 0.6;">Health</small>
                                        </div>
                                    </div>
                                    <div style="background: rgba(255,255,255,0.03); padding: 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                                        <div style="font-size: 0.5rem; color: #888; text-transform: uppercase; margin-bottom: 4px;">Presteza</div>
                                        <div style="font-size: 0.7rem; font-weight: bold; color: #fff;">
                                            ${mission.compact_digest.readiness.replace(/_/g, ' ')}
                                        </div>
                                    </div>
                                </div>

                                ${mission.compact_digest.active_constraints && mission.compact_digest.active_constraints.length > 0 ? `
                                    <div style="margin-bottom: 12px;">
                                        <div style="font-size: 0.5rem; color: #ffaa00; font-weight: bold; margin-bottom: 5px;">RESTRICCIONES ACTIVAS</div>
                                        <div style="display:flex; flex-wrap: wrap; gap: 5px;">
                                            ${mission.compact_digest.active_constraints.map(c => `
                                                <span style="font-size: 0.55rem; background: rgba(255,170,0,0.1); color: #ffaa00; padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(255,170,0,0.2);">${c}</span>
                                            `).join('')}
                                        </div>
                                    </div>
                                ` : ''}

                                ${mission.compact_digest.multimodal_summary ? `
                                    <div style="margin-bottom: 12px; background: rgba(0,150,255,0.05); border: 1px solid rgba(0,150,255,0.2); padding: 8px; border-radius: 6px;">
                                        <div style="font-size: 0.5rem; color: #00ccff; font-weight: bold; margin-bottom: 3px;">GUÍA MULTIMODAL</div>
                                        <div style="font-size: 0.65rem; color: #ddd; font-style: italic;">"${mission.compact_digest.multimodal_summary}"</div>
                                    </div>
                                ` : ''}

                                <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.05);">
                                    <div style="font-size: 0.5rem; color: var(--pizarron-accent); font-weight: bold; margin-bottom: 5px;">PRÓXIMA ACCIÓN SUGERIDA</div>
                                    <div style="font-size: 0.7rem; color: #fff; background: rgba(50,255,150,0.05); padding: 8px; border-radius: 6px; border-left: 3px solid var(--pizarron-accent);">
                                        🚀 ${mission.compact_digest.next_step_hint}
                                    </div>
                                </div>
                                
                                ${mission.compact_digest.latest_incident ? `
                                    <div style="margin-top: 10px; font-size: 0.6rem; color: #ff4444; opacity: 0.8; background: rgba(255,68,68,0.05); padding: 5px; border-radius: 4px;">
                                        <b>ÚLTIMO INCIDENTE:</b> ${mission.compact_digest.latest_incident}
                                    </div>
                                ` : ''}
                            </div>
                        ` : `
                            <div style="opacity: 0.3; font-size: 0.7rem; font-style: italic;">
                                Compactando contexto operativo...
                            </div>
                        `}
                    </section>
                    <section class="pizarron-card">
                        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <h4 style="margin: 0;"><span style="color: #ffaa00">🔒</span> Resource Locks</h4>
                            <span style="font-size: 0.5rem; opacity: 0.4;">GOVERNANCE</span>
                        </div>
                        <div style="max-height: 150px; overflow-y: auto; font-size: 0.65rem;">
                            ${(!data.resource_locks || data.resource_locks.length === 0) ? '<div style="opacity:0.3; padding: 5px;">Sin bloqueos activos.</div>' :
                data.resource_locks.map(lock => {
                    const isActive = lock.status === 'ACQUIRED';
                    const missionIdShort = lock.mission_id ? lock.mission_id.substring(0, 8) : 'SYSTEM';
                    return `
                                    <div style="padding: 6px; border-bottom: 1px solid rgba(255,255,255,0.05); background: ${isActive ? 'rgba(255,170,0,0.05)' : 'transparent'};">
                                        <div style="display:flex; justify-content: space-between; margin-bottom: 2px;">
                                            <b style="color: ${isActive ? '#ffaa00' : '#888'}; font-family: monospace;">${lock.resource_key}</b>
                                            <span style="font-size: 0.55rem; color: ${isActive ? '#ffaa00' : '#888'}; font-weight: bold;">[${lock.status}]</span>
                                        </div>
                                        <div style="display:flex; gap: 8px; opacity: 0.7; font-size: 0.6rem;">
                                            <span>Misión: <span style="text-decoration: underline; cursor:pointer;" onclick="window.omniShell.addInput('switch mission ${lock.mission_id}')">${missionIdShort}</span></span>
                                            <span>Tipo: ${lock.lock_type}</span>
                                        </div>
                                        <div style="font-size: 0.55rem; opacity: 0.5; margin-top: 2px;">${lock.reason || ''}</div>
                                        ${lock.released_at ? `<div style="font-size: 0.5rem; opacity:0.4; text-align: right;">Released: ${new Date(lock.released_at).toLocaleTimeString()}</div>` : ''}
                                    </div>
                                `;
                }).join('')}
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

                <!-- MULTIMODAL MISSION REPORT — Visible cuando hay historia multimodal -->
                ${mission.multimodal_history && mission.multimodal_history.length > 0 ? `
                <section class="pizarron-card" style="grid-column: span 2;" id="mm-report-section">
                    <div class="mm-report-header">
                        <h4>
                            <span>🎬</span>
                            TIMELINE MULTIMODAL
                        </h4>
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span class="mm-report-goal">${mission.active_goal || ''}</span>
                            <button class="mm-report-btn" id="mm-load-report-btn"
                                onclick="(function(btn){ btn.classList.add('loading'); btn.innerText='...'; window.pizarronUI.loadMultimodalReport('${mission.mission_id}').then(()=>{ btn.classList.remove('loading'); btn.innerText='🎬 REPORTE'; }); })(this)">
                                🎬 REPORTE
                            </button>
                            <button class="mm-report-btn" id="mm-load-briefing-btn" style="background: var(--pizarron-accent); color: #000;"
                                onclick="(function(btn){ btn.classList.add('loading'); btn.innerText='...'; window.pizarronUI.loadMissionBriefing('${mission.mission_id}').then(()=>{ btn.classList.remove('loading'); btn.innerText='📋 BRIEFING'; }); })(this)">
                                📋 BRIEFING
                            </button>
                        </div>
                    </div>
                    <div id="mm-report-zone">
                        <div class="mm-empty-state">
                            📸 ${mission.multimodal_history.length} evento(s) multimodal(es) registrado(s).
                            <br>Presiona <b>VER REPORTE</b> para ver el ciclo completo consolidado.
                        </div>
                    </div>
                </section>
                ` : ''}

            </div>
        `;
    }

    // CAPA 5 (PHASE 80): DEEP RECOVERY PANEL
    renderConstitutionAudit(mission) {
        if (!mission || !mission.last_audit_report) return '';
        const audit = mission.last_audit_report;
        const statusColor = audit.status === 'GREEN' ? '#00ff88' : (audit.status === 'YELLOW' ? '#ffaa00' : '#ff4444');
        const icon = audit.status === 'GREEN' ? '🟢' : (audit.status === 'YELLOW' ? '🟡' : '🔴');

        return `
        <div id="constitution-audit-panel" class="pizarron-card" style="grid-column: span 2; border-color: ${statusColor}33; background: ${statusColor}05;">
            <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid ${statusColor}22; padding-bottom: 8px;">
                <div style="display:flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.1rem;">⚖️</span>
                    <div>
                        <div style="font-size: 0.7rem; font-weight: bold; color: ${statusColor}; text-transform: uppercase; letter-spacing: 1px;">Constitución de Autonomía: ${audit.status}</div>
                        <div style="font-size: 0.5rem; color: #888;">Salud Constitucional: ${(audit.health_score * 100).toFixed(0)}% | Auditoría Integral</div>
                    </div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1.5fr; gap: 15px;">
                <!-- Decision Matrix Column -->
                <div style="background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.05);">
                    <div style="font-size: 0.45rem; color: #aaa; text-transform: uppercase; margin-bottom: 8px; font-weight: bold;">⚖️ Matriz de Gobernanza</div>
                    <div style="display: flex; flex-direction: column; gap: 6px;">
                        ${Object.entries(audit.decision_matrix).map(([level, actions]) => `
                            <div>
                                <div style="font-size: 0.4rem; color: #888; text-transform: uppercase;">${level.replace('_', ' ')}</div>
                                <div style="font-size: 0.55rem; color: #ddd; font-family: monospace;">${actions.join(', ')}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Findings Column -->
                <div>
                    <div style="font-size: 0.45rem; color: #aaa; text-transform: uppercase; margin-bottom: 8px; font-weight: bold;">⚠️ Hallazgos y Lagunas</div>
                    ${audit.detected_issues.length > 0 ? `
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            ${audit.detected_issues.map(issue => `
                                <div style="background: rgba(255,170,0,0.05); border: 1px solid rgba(255,170,0,0.15); padding: 8px; border-radius: 4px;">
                                    <div style="font-size: 0.55rem; color: #ffaa00; font-weight: bold;">[${issue.surface}] ${issue.finding}</div>
                                    <div style="font-size: 0.5rem; color: #aaa; margin-top: 4px; font-style: italic;">Hardening: ${issue.recommendation}</div>
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <div style="padding: 10px; background: rgba(0,255,136,0.05); color: #00ff88; font-size: 0.55rem; border-radius: 4px; text-align: center;">
                            No se detectaron contradicciones operativas. Marco legal consistente.
                        </div>
                    `}
                </div>
            </div>
            
            <div style="margin-top: 12px; font-size: 0.45rem; color: #666; font-style: italic; text-align: right;">
                Auditado el ${audit.timestamp} | Basado en el Marco Legal de OmniWeb (PHASE 80)
            </div>
        </div>
        `;
    }

    renderRecoveryPanel(mission) {
        if (!mission || !mission.last_recovery) return '';

        const rec = mission.last_recovery;

        return `
        <div id="recovery-strategy-panel" style="background: linear-gradient(135deg, rgba(0,255,136,0.1) 0%, rgba(0,136,255,0.05) 100%); border: 1px solid rgba(0,255,136,0.3); border-radius: 8px; padding: 12px; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,1.3); animation: fadeIn 0.5s ease-out;">
            <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display:flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2rem;">🔋</span>
                    <div>
                        <div style="font-size: 0.75rem; font-weight: bold; color: #00ff88; text-transform: uppercase; letter-spacing: 1px;">Misión Recuperada</div>
                        <div style="font-size: 0.5rem; color: #888;">Estado de Continuidad Cognitiva: ${rec.recovery_status}</div>
                    </div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px;">
                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                    <div style="font-size: 0.4rem; color: #888; text-transform: uppercase; margin-bottom: 4px;">Foco Rehidratado</div>
                    <div style="font-size: 0.55rem; color: #ddd; font-family: monospace;">${rec.focal_context}</div>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 6px;">
                    <div style="font-size: 0.4rem; color: #888; text-transform: uppercase; margin-bottom: 4px;">Deriva al Reinicio</div>
                    <div style="font-size: 0.55rem; color: ${rec.drift_on_recovery > 50 ? '#ff4444' : '#00ff88'}; font-weight: bold;">
                        ${rec.drift_on_recovery.toFixed(1)}
                    </div>
                </div>
            </div>

            ${rec.suggested_path ? `
            <div style="background: rgba(255,255,255,0.03); border: 1px dashed rgba(255,255,255,0.1); padding: 10px; border-radius: 6px; margin-bottom: 12px;">
                <div style="font-size: 0.45rem; color: #00ff88; font-weight: bold; margin-bottom: 6px; display:flex; align-items: center; gap: 4px;">
                    🎯 RUTA DE CONTINUIDAD SUGERIDA
                </div>
                <div style="font-size: 0.65rem; color: #fff; font-weight: bold; margin-bottom: 4px;">${rec.suggested_path.label}</div>
                <div style="font-size: 0.5rem; color: #aaa; line-height: 1.3;">${rec.suggested_path.reasoning}</div>
                
                ${rec.is_auto_eligible ? `
                <div style="margin-top: 8px; background: rgba(0,255,136,0.1); border: 1px solid rgba(0,255,136,0.2); padding: 5px; border-radius: 4px; font-size: 0.4rem; color: #00ff88; text-align: center; font-weight: bold;">
                    🚀 AUTO-RECOVERY ELIGIBLE: CONFIGURADO PARA CONTINUACIÓN SEGURA
                </div>
                ` : ''}
            </div>
            ` : ''}

            <div style="display:flex; gap: 8px; justify-content: flex-end;">
                <button onclick="this.parentElement.parentElement.remove()" style="background: transparent; border: 1px solid rgba(255,255,255,0.2); color: #888; border-radius: 4px; padding: 4px 10px; font-size: 0.45rem; cursor: pointer;">Descartar</button>
                <button onclick="this.parentElement.parentElement.remove()" style="background: #00ff88; border: none; color: #002211; border-radius: 4px; padding: 4px 12px; font-size: 0.45rem; font-weight: bold; cursor: pointer;">Confirmar Reanudación</button>
            </div>
        </div>
        `;
    }

    selectNode(nodeId) {
        this.selectedNodeId = (this.selectedNodeId === nodeId) ? null : nodeId;
        if (window.creator && window.creator.systemState) {
            window.creator.renderWorkspaceMissionDashboard(window.creator.systemState);
        }
    }

    // ================================================================
    // CAPA 1+2+3 — MULTIMODAL MISSION REPORT TIMELINE
    // Conecta con el endpoint existente (/mission/{id}/report)
    // y renderiza la narrativa visual consolidada del ciclo multimodal.
    // ================================================================

    async loadMissionSimulation(missionId) {
        const container = document.getElementById('mission-simulation-container');
        if (!container) return;

        try {
            const res = await fetch(`/api/mission/${missionId}/simulate`);
            if (!res.ok) return;
            const scenarios = await res.json();

            if (scenarios && scenarios.length > 0) {
                this.renderSimulationPanel(scenarios, container);
            }
        } catch (e) {
            console.error("[MISSION_SIMULATION] Error:", e);
        }
    }

    renderSimulationPanel(scenarios, container) {
        container.style.display = 'block';

        container.innerHTML = `
            <div style="margin-bottom: 8px; display:flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0,229,255,0.1); padding-bottom: 4px;">
                <span style="font-size: 0.65rem; color: #00e5ff; font-weight: bold; font-family: 'Outfit';">🔍 LABORATORIO DE ESTRATEGIA: WHAT-IF</span>
                <span class="status-badge" style="background: rgba(0,229,255,0.1); color: #00e5ff; border: none; font-size: 0.45rem;">PREDICTIVE FORESIGHT</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 10px; margin-top: 10px;">
                ${scenarios.map(s => {
            const driftColor = s.projected_drift > 60 ? '#ff4444' : s.projected_drift > 30 ? '#ffcc00' : '#00ff88';
            const riskColor = s.risk_level === 'HIGH' ? '#ff4444' : s.risk_level === 'MEDIUM' ? '#ffcc00' : '#00e5ff';

            const audit = s.autonomy_audit || { level: 'UNKNOWN', reason: 'No audit data' };
            const auditColors = {
                'AUTO_SAFE_THEORETICAL': '#00ff88',
                'HUMAN_CONFIRM': '#ffcc00',
                'GATE_REQUIRED': '#ffaa00',
                'PIN_REQUIRED': '#ff0055',
                'NEVER_AUTO': '#ff4444'
            };
            const auditColor = auditColors[audit.level] || '#aaa';
            const isPenalized = s.source === 'HISTORICAL' && s.confidence < 0.7;
            const consensus = s.consensus || null;

            const consensusColors = {
                'STRONG_CONSENSUS': '#00ff88',
                'PARTIAL_SUPPORT': '#00e5ff',
                'DIVIDED_CONFLICT': '#ffaa00',
                'NEUTRAL': '#aaa',
                'AGNOSTIC': '#666'
            };
            const cColor = consensus ? (consensusColors[consensus.status] || '#888') : '#444';

            return `
                        <div class="simulation-card animate-slide-in" style="background: rgba(255,255,255,0.03); border: 1px solid ${isPenalized ? 'rgba(255,68,68,0.3)' : (s.is_recommended ? 'rgba(0,255,136,0.3)' : 'rgba(255,255,255,0.05)')}; border-radius: 8px; padding: 10px; position: relative; overflow: hidden;">
                            ${s.is_recommended ? `<div style="position: absolute; top:0; right:0; background: #00ff88; color:#000; font-size: 0.45rem; padding: 2px 6px; font-weight: bold; border-bottom-left-radius: 4px;">RECOMENDADO</div>` : ''}
                            ${isPenalized ? `<div style="position: absolute; top:0; right:0; background: #ff4444; color:#fff; font-size: 0.45rem; padding: 2px 6px; font-weight: bold; border-bottom-left-radius: 4px;">⚠️ PENALIZADO (HEALING)</div>` : ''}
                            
                            <div style="font-size: 0.65rem; font-weight: bold; color: #fff; margin-bottom: 6px;">${s.label}</div>

                            ${consensus ? `
                            <div style="margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                                <span class="status-badge" style="background: ${cColor}22; color: ${cColor}; border: 1px solid ${cColor}44; font-size: 0.4rem; padding: 1px 4px;">
                                     🛡️ CONSENSO: ${consensus.status.replace(/_/g, ' ')}
                                </span>
                                <span style="font-size: 0.4rem; color: #888;">(Signatarios: ${consensus.votes.length})</span>
                            </div>
                            ` : ''}
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px;">
                                <div style="background: rgba(0,0,0,0.2); padding: 5px; border-radius: 4px; text-align: center;">
                                    <div style="font-size: 0.45rem; opacity: 0.5; text-transform: uppercase;">Drift Proyectado</div>
                                    <div style="font-size: 0.8rem; color: ${driftColor}; font-weight: bold;">${s.projected_drift.toFixed(0)}</div>
                                </div>
                                <div style="background: rgba(0,0,0,0.2); padding: 5px; border-radius: 4px; text-align: center;">
                                    <div style="font-size: 0.45rem; opacity: 0.5; text-transform: uppercase;">Mejora (Delta)</div>
                                    <div style="font-size: 0.8rem; color: #00ff88; font-weight: bold;">+${s.projected_delta.toFixed(0)}</div>
                                </div>
                            </div>
                            
                            <div style="font-size: 0.58rem; color: #aaa; margin-bottom: 8px; line-height: 1.3;">
                                ${s.reasoning}
                            </div>

                            ${s.historical_experience && s.historical_experience.lessons.length > 0 ? `
                            <div style="margin-bottom: 8px; background: rgba(0,255,136,0.05); border: 1px solid rgba(0,255,136,0.1); padding: 6px; border-radius: 4px;">
                                <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                    <span style="font-size: 0.45rem; color: ${s.historical_experience.status === 'SUPPORTED' ? '#00ff88' : '#ffaa00'}; font-weight: bold; text-transform: uppercase;">
                                        💼 EVIDENCIA HISTÓRICA: ${s.historical_experience.status}
                                    </span>
                                </div>
                                <div style="font-size: 0.38rem; color: #888; line-height: 1.2;">
                                    ${s.historical_experience.lessons.map(l => `• ${l.summary}`).join('<br>')}
                                </div>
                                <div style="margin-top: 4px; font-size: 0.35rem; color: #555; font-style: italic;">
                                    ${s.historical_experience.basis}
                                </div>
                            </div>
                            ` : (s.historical_experience ? `
                            <div style="margin-bottom: 8px; font-size: 0.35rem; color: #555; text-align: center;">
                                <i>Sin precedentes históricos registrados para esta capa.</i>
                            </div>
                            ` : '')}

                            ${s.collateral_risk ? `
                            <div style="margin-bottom: 8px; background: rgba(0,0,0,0.2); padding: 6px; border-radius: 4px;">
                                <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                    <span style="font-size: 0.45rem; color: #ffaa00; font-weight: bold; text-transform: uppercase;">RIESGO COLATERAL: ${s.risk_level}</span>
                                    <span style="font-size: 0.45rem; color: #888;">Nivel: ${s.risk_score}%</span>
                                </div>
                                <div style="height: 3px; background: rgba(255,255,255,0.05); border-radius: 2px; overflow: hidden;">
                                    <div style="height: 100%; width: ${s.risk_score}%; background: ${s.risk_score > 60 ? '#ff4444' : '#ffaa00'};"></div>
                                </div>
                                ${s.collateral_risk.sources.length > 0 ? `
                                <div style="margin-top: 4px; font-size: 0.38rem; color: #888; display: flex; gap: 4px; flex-wrap: wrap;">
                                    ${s.collateral_risk.sources.map(src => `<span style="border: 1px solid rgba(255,255,255,0.1); padding: 1px 3px; border-radius: 2px;">${src}</span>`).join('')}
                                </div>
                                ` : ''}
                            </div>
                            ` : ''}

                            ${s.net_value !== undefined ? `
                            <div style="margin-bottom: 8px; text-align: center;">
                                <div style="font-size: 0.42rem; color: #888; text-transform: uppercase;">Valor Estratégico Neto</div>
                                <div style="font-size: 0.9rem; color: ${s.net_value > 30 ? '#00ff88' : (s.net_value > 0 ? '#ffaa00' : '#ff4444')}; font-weight: bold;">
                                    ${s.net_value > 0 ? '+' : ''}${s.net_value.toFixed(0)}
                                </div>
                            </div>
                            ` : ''}

                            ${consensus && consensus.votes.length > 0 ? `
                                <div style="font-size: 0.45rem; color: #666; background: rgba(0,0,0,0.1); padding: 4px; border-radius: 4px; margin-bottom: 8px;">
                                    ${consensus.votes.map(v => `<div style="margin-bottom: 2px;">• <b>${v.auditor}:</b> ${v.reason}</div>`).join('')}
                                </div>
                            ` : ''}

                            <div style="background: rgba(0,0,0,0.2); padding: 6px; border-radius: 4px; margin-bottom: 8px; border-left: 2px solid ${auditColor};">
                                <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                                    <span style="font-size: 0.45rem; color: ${auditColor}; font-weight: bold; text-transform: uppercase;">POLÍTICA: ${audit.level.replace(/_/g, ' ')}</span>
                                </div>
                                <div style="font-size: 0.5rem; color: #aaa; font-style: italic;">"${audit.reason}"</div>
                            </div>
                            
                            <div style="display:flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px;">
                                <div style="display:flex; gap: 10px; align-items: center;">
                                    <span style="font-size: 0.5rem; color: ${riskColor}; font-weight: bold;">RIESGO: ${s.risk_level}</span>
                                    <span style="font-size: 0.5rem; color: #888;">Confianza: ${(s.confidence * 100).toFixed(0)}%</span>
                                </div>
                                <button class="pizarron-btn-mini" style="margin:0; background: ${s.is_recommended ? 'rgba(0,255,136,0.1)' : 'rgba(255,255,255,0.05)'}; color: ${s.is_recommended ? '#00ff88' : '#eee'}; border-color: ${s.is_recommended ? '#00ff88' : '#444'};"
                                        onclick="window.omniShell.addInput('correct mission alignment to ${s.action}')">
                                    SOLICITAR
                                </button>
                            </div>
                        </div>
                    `;
        }).join('')}
            </div>
            <div style="margin-top: 8px; font-size: 0.5rem; opacity: 0.3; font-style: italic; text-align: center;">
                Simulaciones basadas en modelos estocásticos de deriva y ROI histórico.
            </div>
        `;
    }

    // ================================================================
    // PHASE 71 — COGNITIVE REPLAY & FORENSIC AUDIT
    // ================================================================

    async loadCognitiveReplay(missionId) {
        const container = document.getElementById('cognitive-replay-container');
        if (!container) return;

        try {
            const res = await fetch(`/api/mission/${missionId}/replay`);
            if (!res.ok) return;
            const trace = await res.json();

            if (trace && trace.length > 0) {
                this.renderReplayControls(trace, container);
            }
        } catch (e) {
            console.error("[COGNITIVE_REPLAY] Error:", e);
        }
    }

    renderReplayControls(trace, container) {
        container.style.display = 'block';

        let currentStep = trace.length;

        const renderStepContent = (stepIdx) => {
            const step = trace[stepIdx];
            const isRescue = step.is_rescue;
            const driftSeverity = step.drift_score > 60 ? 'critical' : step.drift_score > 30 ? 'warning' : 'aligned';
            const driftColor = driftSeverity === 'critical' ? '#ff4444' : driftSeverity === 'warning' ? '#ffcc00' : '#00ff88';

            return `
                <div class="replay-step-viewer animate-fade-in" style="background: rgba(255,255,255,0.03); border-radius: 6px; padding: 10px; border-left: 3px solid ${isRescue ? '#00ff88' : 'var(--pizarron-accent)'};">
                    <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 0.6rem; font-weight: bold; color: ${isRescue ? '#00ff88' : '#aaa'};">
                            EVENTO [${step.step}/${trace.length}]: ${step.event}
                        </span>
                        <span style="font-size: 0.55rem; opacity: 0.4;">${new Date(step.timestamp).toLocaleTimeString()}</span>
                    </div>
                    
                    <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 8px;">
                        <div style="background: rgba(0,0,0,0.2); padding: 5px; border-radius: 4px;">
                            <div style="font-size: 0.45rem; opacity: 0.5; text-transform: uppercase;">Original Target</div>
                            <div style="font-size: 0.6rem; color: #fff; font-family: monospace;">${step.original_focus}</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.05); padding: 5px; border-radius: 4px;">
                            <div style="font-size: 0.45rem; opacity: 0.5; text-transform: uppercase;">Active Focus</div>
                            <div style="font-size: 0.6rem; color: var(--pizarron-accent); font-weight: bold; font-family: monospace;">${step.current_focus}</div>
                        </div>
                    </div>

                    <div style="font-size: 0.6rem; color: #eee; line-height: 1.4; font-style: italic; margin-bottom: 10px; padding: 5px; background: rgba(0,0,0,0.1); border-radius: 4px;">
                        "${step.description}"
                    </div>

                    <div style="margin-top: 10px; display:flex; flex-direction: column; gap: 8px;">
                        <div style="display:flex; align-items: center; gap: 10px;">
                            <input type="range" class="replay-scrubber" min="0" max="${trace.length - 1}" value="${stepIdx}" style="flex:1; cursor: pointer;">
                            <div style="font-size: 0.6rem; color: #aaa; width: 40px; text-align: right;">${step.step}/${trace.length}</div>
                        </div>
                        <div style="font-size: 0.5rem; text-align: right; opacity: 0.4;">Mueve el scrubber para rebobinar la misión</div>
                    </div>
                </div>
            `;
        };

        const updateContent = (idx) => {
            container.innerHTML = renderStepContent(idx);
            const slider = container.querySelector('.replay-scrubber');
            if (slider) {
                slider.oninput = (e) => {
                    updateContent(parseInt(e.target.value));
                };
            }
        };

        updateContent(currentStep - 1);
    }

    async loadMissionBriefing(missionId) {
        const mount = document.getElementById('ws-mission-mount');
        const reportZone = mount?.querySelector('#mm-report-zone');
        if (reportZone) reportZone.innerHTML = '<div class="mm-empty-state">⏳ Generando briefing ejecutivo...</div>';

        try {
            const res = await fetch(`/api/v1/ai-host/execution/mission/${missionId}/briefing`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            if (!res.ok) throw new Error("Briefing failed");
            const data = await res.json();
            if (reportZone) reportZone.innerHTML = this.renderMissionBriefing(data.handoff, data.exportable_markdown);
        } catch (err) {
            if (reportZone) reportZone.innerHTML = '<div class="mm-empty-state">⚠️ Error al generar briefing.</div>';
        }
    }

    renderMissionBriefing(handoff, md) {
        return `
            <div class="mission-briefing-container" style="padding: 20px; color: #eee; font-family: 'Outfit', sans-serif;">
                <div style="display:flex; justify-content: space-between; align-items: start; margin-bottom: 20px;">
                    <div>
                        <h2 style="margin:0; color:var(--pizarron-accent);">${handoff.briefing_title}</h2>
                        <p style="margin:5px 0; opacity: 0.6; font-size: 0.8rem;">ID: ${handoff.mission_id} | Finalizado: ${new Date(handoff.created_at).toLocaleString()}</p>
                    </div>
                    <button class="mm-report-btn" style="background: rgba(255,255,255,0.1);" onclick="navigator.clipboard.writeText(\`${md.replace(/`/g, '\\`').replace(/\$/g, '\\$')}\`).then(()=>alert('Copiado al portapapeles (Markdown)'))">
                        📎 COPIAR MARKDOWN
                    </button>
                </div>

                <div style="display:grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                    <div class="briefing-main">
                        <section style="margin-bottom: 20px;">
                            <h4 style="color:#fff; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px;">🎯 OBJETIVO Y ALCANCE</h4>
                            <p style="font-size: 0.9rem; line-height:1.6;">${handoff.goal}</p>
                        </section>

                        <section style="margin-bottom: 20px;">
                            <h4 style="color:#fff; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px;">📝 RESUMEN EJECUTIVO</h4>
                            <p style="font-size: 0.9rem; line-height:1.6;">${handoff.executive_summary}</p>
                        </section>

                        <section style="margin-bottom: 20px;">
                            <h4 style="color:#fff; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px;">🛠️ IMPACTO TÉCNICO Y RESULTADOS</h4>
                            <p style="font-size: 0.85rem; line-height:1.5; white-space: pre-wrap; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 6px;">${handoff.technical_impact}</p>
                        </section>
                    </div>

                    <div class="briefing-side">
                        <section style="margin-bottom: 20px; background: rgba(0,255,136,0.03); padding: 10px; border-radius: 8px; border: 1px solid rgba(0,255,136,0.1);">
                            <h4 style="color:#00ff88; font-size: 0.7rem; margin-top:0;">🛡️ GOBERNANZA</h4>
                            <div style="font-size: 1.2rem; font-weight: bold;">${(handoff.governance_footprint.score * 100).toFixed(0)}% <span style="font-size:0.6rem; opacity:0.6;">Integridad</span></div>
                            ${handoff.recovery_events.length > 0 ? `
                                <div style="margin-top:10px; font-size: 0.65rem; color:#ffcc00;">
                                    ⚠️ ${handoff.recovery_events.length} incidentes gestionados.
                                </div>
                            ` : ''}
                        </section>

                        <section style="margin-bottom: 20px;">
                            <h4 style="color:#ffaa00; font-size: 0.7rem;">⚖️ DECISIONES CLAVE</h4>
                            <ul style="font-size: 0.7rem; padding-left: 15px; opacity: 0.8;">
                                ${handoff.key_decisions.map(d => `<li>${d}</li>`).join('') || '<li>Uso de protocolos estándar.</li>'}
                            </ul>
                        </section>

                        <section>
                            <h4 style="color:var(--pizarron-accent); font-size: 0.7rem;">🚀 SIGUIENTES PASOS</h4>
                            <ul style="font-size: 0.7rem; padding-left: 15px; color: var(--pizarron-accent);">
                                ${handoff.next_steps.map(s => `<li>${s}</li>`).join('')}
                            </ul>
                        </section>
                    </div>
                </div>
            </div>
        `;
    }

    renderDriftBadge(drift) {
        const colors = {
            'ALIGNED': '#00ff88', 'MINOR_SHIFT': '#00e5ff', 'ATTENTION_REQUIRED': '#ffcc00',
            'DRIFT_WARNING': '#ff7700', 'CRITICAL_DRIFT': '#ff4444'
        };
        const color = colors[drift.status] || '#fff';
        const trace = drift.causal_chain || [];

        return `
            <div style="background:rgba(0,0,0,0.3); border:1px solid ${color}33; border-radius:6px; padding:8px; margin-bottom:12px; border-left:3px solid ${color};">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <span style="font-size:0.6rem; color:${color}; font-weight:bold;">🧠 COGNITIVE DRIFT: ${drift.status}</span>
                    <span style="font-size:0.45rem; color:rgba(255,255,255,0.3);">SCORE: ${drift.drift_score}</span>
                </div>
                
                ${trace.length > 0 ? `
                    <div style="background:rgba(255,255,255,0.03); padding:5px; border-radius:4px; margin-bottom:8px; border:1px dashed rgba(255,255,255,0.05);">
                        <div style="font-size:0.45rem; color:#888; margin-bottom:4px; text-transform:uppercase;">🗙 Trazabilidad Forense</div>
                        ${trace.map(t => `
                            <div style="font-size:0.48rem; display:flex; gap:6px; opacity:0.8;">
                                <span style="color:${t.role?.includes('TRIGGER') ? '#ff4444' : '#00e5ff'}; font-weight:bold;">[${t.role?.split(' ')[0]}]</span>
                                <span style="color:#fff;">${t.event}</span>
                                <span style="color:rgba(255,255,255,0.3);">(${t.layer})</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}

                ${drift.suggested_actions?.length > 0 ? `
                    <div style="display:flex; flex-direction:column; gap:6px;">
                        <span style="font-size:0.5rem; color:#fff; font-weight:bold; text-transform:uppercase;">⚡ Sugerencias de Re-alineación</span>
                        ${drift.suggested_actions.map(action => `
                            <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.05); padding:6px; border-radius:4px; border:1px solid rgba(255,255,255,0.1);">
                                <div style="flex-grow:1; display:flex; flex-direction:column;">
                                    <span style="font-size:0.55rem; color:#fff; font-weight:bold;">${action.label}</span>
                                    <span style="font-size:0.42rem; color:rgba(255,255,255,0.4); margin-bottom:4px;">${action.description}</span>
                                    ${action.forecast ? `
                                        <div style="font-size:0.45rem; color:${action.forecast.source === 'HISTORICAL' ? '#00ff88' : '#888'}; background:rgba(255,255,255,0.03); padding:2px 4px; border-radius:2px; display:inline-block; border:1px solid rgba(255,255,255,0.05);">
                                            🔮 FORECAST: <b>${action.forecast.current_drift}</b> ➔ <b>${action.forecast.predicted_drift.toFixed(0)}</b> DRIFT 
                                            <span style="opacity:0.6; margin-left:4px;">(Impacto: -${action.forecast.delta.toFixed(0)} | Conf: ${action.forecast.confidence.toFixed(1)})</span>
                                        </div>
                                    ` : ''}
                                </div>
                                <button style="background:${color}; border:none; color:#000; font-size:0.45rem; font-weight:bold; padding:3px 6px; border-radius:3px; cursor:pointer; font-family:'Outfit'; align-self:center;"
                                        onclick="window.omniPizarron.executeDriftCorrection('${drift.mission_id}', ${JSON.stringify(action).replace(/"/g, '&quot;')})">
                                    EJECUTAR
                                </button>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                
                <div style="margin-top:6px; border-top:1px solid rgba(255,255,255,0.05); padding-top:4px; display:flex; gap:10px;">
                    <span style="font-size:0.4rem; color:#888;">Foco Original: <b>${drift.original_focus}</b></span>
                    <span style="font-size:0.4rem; color:#888;">Foco Actual: <b>${drift.current_focus}</b></span>
                </div>
            </div>
        `;
    }

    async executeDriftCorrection(missionId, action) {
        if (!confirm(`¿Confirmas la ejecución de la acción táctica: ${action.label}?`)) return;
        try {
            const res = await fetch(`/api/v1/ai-host/execution/mission/${missionId}/drift/correct`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                },
                body: JSON.stringify(action)
            });
            const data = await res.json();
            if (data.status === 'success') {
                const audit = data.result.performance_audit;
                const roiMsg = `✅ Realineación: ${data.result.message}\n\n` +
                    `📈 ROI DE RESCATE:\n` +
                    `• Drift Before: ${audit.drift_before}\n` +
                    `• Drift After: ${audit.drift_after}\n` +
                    `• Mejora (Delta): ${audit.delta.toFixed(1)}\n` +
                    `• Clase de Impacto: ${audit.impact}`;
                alert(roiMsg);
                // Refresh both the report and the portfolio health dashboard
                this.loadMultimodalReport(missionId);
                if (this.loadPortfolioDrift) this.loadPortfolioDrift();
            } else {
                alert(`⚠️ Fallo: ${data.result.message}`);
            }
        } catch (err) { console.error("Correction failed", err); }
    }

    async loadPortfolioDrift() {
        const mount = document.getElementById('ws-mission-mount');
        if (!mount) return;

        try {
            const res = await fetch('/api/v1/ai-host/execution/portfolio/drift/health', {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();
            if (data.status === 'success') {
                this.renderPortfolioDriftDashboard(data.portfolio, mount);
            }
        } catch (err) {
            console.error("Portfolio drift load failed", err);
        }
    }

    renderPortfolioDriftDashboard(portfolio, mount) {
        const section = document.createElement('div');
        section.id = 'cognitive-health-dashboard';
        section.style = "margin-bottom:20px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.05); border-radius:8px; padding:10px;";

        const colors = {
            'ALIGNED': '#00ff88', 'MINOR_SHIFT': '#00e5ff',
            'ATTENTION_REQUIRED': '#ffcc00', 'DRIFT_WARNING': '#ff7700', 'CRITICAL_DRIFT': '#ff4444',
            'HEALING': '#00e5ff'
        };

        section.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:5px;">
                <span style="font-size:0.65rem; color:#fff; font-weight:bold; font-family:'Outfit';">🧠 PORTFOLIO COGNITIVE HEALTH</span>
                <span style="font-size:0.5rem; color:rgba(255,255,255,0.3); text-transform:uppercase;">Explica: Portfolio Audit</span>
            </div>
            <div style="display:flex; flex-direction:column; gap:6px;">
                ${portfolio.length === 0 ? '<div style="font-size:0.55rem; color:#666;">No hay misiones activas para analizar.</div>' : ''}
                ${portfolio.map(m => `
                    <div style="display:flex; gap:8px; align-items:center; background:rgba(0,0,0,0.2); padding:6px; border-radius:6px; border-left:3px solid ${colors[m.drift] || '#fff'}; cursor:pointer;"
                         onclick="window.omniPizarron.loadMultimodalReport('${m.mission_id}')">
                        <div style="flex-grow:1; display:flex; flex-direction:column; gap:2px; min-width:0;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-size:0.55rem; color:#fff; font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${m.goal}</span>
                                <span style="font-size:0.45rem; color:${colors[m.drift]}; font-weight:bold;">${m.drift}</span>
                            </div>
                            <div style="display:flex; gap:10px; font-size:0.45rem; color:rgba(255,255,255,0.4);">
                                <span>ID: ${m.mission_id.substring(0, 8)}</span>
                                <span>SCORE: <b style="color:#fff;">${m.drift_score}</b></span>
                                <span>FOCO: <b style="color:#888;">${m.current_focus}</b></span>
                            </div>
                            ${m.urgency === 'HIGH' ? `<div style="font-size:0.42rem; color:#ffcc00; font-family:'Outfit';">⚡ Sugerencia: <b>${m.suggested_action}</b></div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Insert at the beginning of the mount
        const existing = document.getElementById('cognitive-health-dashboard');
        if (existing) existing.remove();
        mount.prepend(section);
    }

    async loadMultimodalReport(missionId) {
        const mount = document.getElementById('ws-mission-mount');
        if (!mount) return;

        // Show loading state in the report zone
        const reportZone = mount.querySelector('#mm-report-zone');
        if (reportZone) {
            reportZone.innerHTML = '<div class="mm-empty-state">⏳ Cargando reporte multimodal...</div>';
        }

        try {
            const res = await fetch(`/api/v1/ai-host/execution/mission/${missionId}/report`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}`
                }
            });

            if (!res.ok) {
                if (reportZone) reportZone.innerHTML = `<div class="mm-empty-state">⚠️ Reporte no disponible (${res.status})</div>`;
                return;
            }

            const data = await res.json();
            const report = data.report;

            if (!report) {
                if (reportZone) reportZone.innerHTML = '<div class="mm-empty-state">Sin datos de reporte para esta misión.</div>';
                return;
            }

            if (reportZone) {
                reportZone.innerHTML = this.renderMultimodalReportTimeline(report);
            }
        } catch (err) {
            console.error('[MULTIMODAL_REPORT] Error fetching report:', err);
            if (reportZone) reportZone.innerHTML = `<div class="mm-empty-state">Error de conexión con el núcleo.</div>`;
        }
    }

    get EVENT_META() {
        return {
            'INITIAL_CAPTURE': { icon: '📸', title: 'Evidencia Inicial', type: 'input' },
            'RE_ORIENTATION': { icon: '🔁', title: 'Re-orientación Visual', type: 'correction' },
            'GATE_DECISION': { icon: '⚖️', title: 'Decisión de Gate', type: 'governance' },
        };
    }

    renderTimelineNode(node) {
        const meta = this.EVENT_META[node.event] || { icon: '●', title: node.event, type: 'input' };
        const ts = node.timestamp ? node.timestamp.split('T')[1]?.split('.')[0] || '' : '';
        const diff = node.visual_diff;
        const shift = node.hypothesis?.shift_detected;
        const hyp = node.hypothesis?.description || '';
        const comment = node.description || node.creator_comment || '';

        const isCritical = node.relevance === "CRITICAL";
        const isRecovered = !!node.retrieval_metadata;
        let relBadge = isCritical
            ? `<span style="background:var(--pizarron-accent); color:#000; font-size:0.45rem; padding:1px 4px; border-radius:3px; font-weight:bold; margin-left:8px; vertical-align:middle;">ACTIVA</span>`
            : `<span style="background:rgba(255,255,255,0.05); color:rgba(255,255,255,0.3); font-size:0.45rem; padding:1px 4px; border-radius:3px; margin-left:8px; vertical-align:middle; border: 1px solid rgba(255,255,255,0.05);">ARCHIVO</span>`;

        if (isRecovered) {
            relBadge = `<span style="background:#00e5ff; color:#000; font-size:0.45rem; padding:1px 4px; border-radius:3px; font-weight:bold; margin-left:8px; vertical-align:middle;">🔄 RECUPERADA</span>`;
        }

        const nodeOpacity = (isCritical || isRecovered) ? '1' : '0.65';

        return `
            <div class="mm-node type-${meta.type}" style="opacity: ${nodeOpacity}; transition: opacity 0.3s ease;">
                <div class="mm-node-dot" style="${isCritical ? 'background:var(--pizarron-accent); box-shadow:0 0 5px var(--pizarron-accent);' : (isRecovered ? 'background:#00e5ff; box-shadow:0 0 5px #00e5ff;' : '')}"></div>
                <div class="mm-node-header">
                    <div class="mm-node-title">
                        <span>${meta.icon}</span>
                        <span>${meta.title}</span>
                        ${relBadge}
                    </div>
                    <span class="mm-node-ts">${ts}</span>
                </div>
                <div class="mm-node-body">
                    ${hyp ? `<div style="margin-bottom:3px; opacity:0.85;">${hyp}</div>` : ''}
                    ${comment ? `<div style="color:#00e5ff; font-style:italic; font-size:0.58rem;">💬 "${comment}"</div>` : ''}
                    ${node.retrieval_metadata ? `
                        <div style="background:rgba(0,229,255,0.03); border:1px solid rgba(0,229,255,0.1); border-radius:4px; padding:4px; margin-top:5px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                                <div style="color:#00e5ff; font-size:0.5rem; font-weight:bold; text-transform:uppercase;">⚡ IMPACTO ESTRATÉGICO</div>
                                ${(!node.retrieval_metadata.validation_status || node.retrieval_metadata.validation_status === 'PENDING') ? `
                                    <div style="display:flex; gap:4px;">
                                        <button class="pizarron-btn-mini" style="background:#00ff8822; border-color:#00ff8844; color:#00ff88; margin:0; padding:1px 6px;" onclick="window.omniPizarron.validateRecall('${node.mission_id}', '${node.id}', true)">✅ VALIDAR</button>
                                        <button class="pizarron-btn-mini" style="background:#ff444422; border-color:#ff444444; color:#ff4444; margin:0; padding:1px 6px;" onclick="window.omniPizarron.validateRecall('${node.mission_id}', '${node.id}', false)">❌ RECHAZAR</button>
                                    </div>
                                ` : `
                                    <span style="font-size:0.45rem; opacity:0.6; color:${node.retrieval_metadata.validation_status === 'VALIDATED' ? '#00ff88' : '#ff4444'}">
                                        ${node.retrieval_metadata.validation_status === 'VALIDATED' ? '✓ VERIFICADA' : '🗙 EXCLUIDA'}
                                    </span>
                                `}
                            </div>
                            <div style="color:#ccc; font-size:0.55rem; margin:2px 0;"><b>Refuerzo:</b> ${node.retrieval_metadata.cognitive_impact?.reinforced_strategy || 'Análisis contextual'}</div>
                            <div style="color:rgba(255,255,255,0.4); font-size:0.5rem; font-style:italic;">"${node.retrieval_metadata.cognitive_impact?.historical_insight}"</div>
                            <div style="font-size:0.45rem; color:#888; margin-top:2px;">Match: ${node.retrieval_metadata.match_reason} | Influencia: ${node.retrieval_metadata.cognitive_impact?.influence}</div>
                        </div>
                    ` : ''}
                    ${node.relevance !== 'CRITICAL' ? `
                        <div style="margin-top:5px; border-top:1px solid rgba(255,255,255,0.05); padding-top:4px; display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-size:0.45rem; color:#666; text-transform:uppercase; letter-spacing:0.5px;">Control Manual</span>
                            ${node.manual_reactivation?.active ? `
                                <button class="pizarron-btn-mini" style="background:#00e5ff22; border-color:#00e5ff44; color:#00e5ff; margin:0; font-size:0.45rem;" onclick="window.omniPizarron.reactivateSnapshot('${node.mission_id}', '${node.id}', false)">✓ ACTIVA (QUITAR)</button>
                            ` : `
                                <button class="pizarron-btn-mini" style="background:rgba(255,255,255,0.05); border-color:rgba(255,255,255,0.1); color:#888; margin:0; font-size:0.45rem;" onclick="window.omniPizarron.reactivateSnapshot('${node.mission_id}', '${node.id}', true)">⚡ RE-ACTIVAR</button>
                            `}
                        </div>
                    ` : ''}
                    ${diff ? `
                        <div class="mm-diff-pill">
                            <span class="mm-diff-added">+${diff.added_count || 0} añadidas</span>
                            <span class="mm-diff-removed">-${diff.removed_count || 0} descartadas</span>
                            ${diff.persistent_count ? `<span class="mm-diff-pers">= ${diff.persistent_count} persisten</span>` : ''}
                        </div>
                    ` : ''}
                    ${shift ? `<div class="mm-shift-badge">🛰️ ${shift}</div>` : ''}
                    ${node.diff_summary ? `<div class="mm-shift-badge" style="color:#ffaa00; background:rgba(255,170,0,0.05); border-color:rgba(255,170,0,0.15);">Δ ${node.diff_summary}</div>` : ''}
                </div>
            </div>
        `;
    }

    renderTechNode(tech) {
        if (!tech || !tech.layer) return '';
        const confidence = tech.confidence === 'high' ? '🟢 ALTA' : tech.confidence === 'medium' ? '🟡 MEDIA' : '🔴 BAJA';
        return `
            <div class="mm-node type-technical">
                <div class="mm-node-dot"></div>
                <div class="mm-node-header">
                    <div class="mm-node-title"><span>🎯</span><span>Target Técnico Refinado</span></div>
                </div>
                <div class="mm-tech-box">
                    <div class="tech-row"><span class="tech-key">CAPA</span><span class="tech-val">${tech.layer}</span></div>
                    ${tech.component ? `<div class="tech-row"><span class="tech-key">COMPONENTE</span><span class="tech-val">${tech.component}</span></div>` : ''}
                    ${tech.route ? `<div class="tech-row"><span class="tech-key">RUTA</span><span class="tech-val" style="font-size:0.52rem">${tech.route}</span></div>` : ''}
                    ${tech.issue_type ? `<div class="tech-row"><span class="tech-key">TIPO</span><span class="tech-val">${tech.issue_type}</span></div>` : ''}
                    <div class="tech-row"><span class="tech-key">CONFIANZA</span><span class="tech-val">${confidence}</span></div>
                    ${tech.roadmap_hint ? `<div style="font-size:0.55rem; color:rgba(255,255,255,0.4); margin-top:4px; font-style:italic;">💡 ${tech.roadmap_hint}</div>` : ''}
                </div>
            </div>
        `;
    }

    renderRescueNode(rescue) {
        if (!rescue) return '';
        const trace = rescue.trace?.chosen_path || null;
        return `
            <div class="mm-node type-rescue">
                <div class="mm-node-dot"></div>
                <div class="mm-node-header">
                    <div class="mm-node-title"><span>⚛</span><span>Rescate / Propuesta Final</span></div>
                </div>
                <div class="mm-node-body">
                    <div style="color:#32ff96; margin-bottom:3px;">${rescue.step || 'Acción de rescate'}</div>
                    ${rescue.summary ? `<div style="opacity:0.7; font-size:0.58rem;">${rescue.summary}</div>` : ''}
                    ${trace ? `<div class="mm-shift-badge" style="color:#32ff96; background:rgba(50,255,150,0.05); border-color:rgba(50,255,150,0.15); margin-top:4px;">🎯 Path elegido: ${trace}</div>` : ''}
                </div>
            </div>
        `;
    }

    renderGovNode(gov, decisions) {
        if (!gov && !decisions?.length) return '';
        const decisionList = (decisions || []).filter(Boolean);
        return `
            <div class="mm-node type-governance">
                <div class="mm-node-dot"></div>
                <div class="mm-node-header">
                    <div class="mm-node-title"><span>⚖️</span><span>Contexto de Gobernanza</span></div>
                </div>
                <div class="mm-governance-bar">
                    <span class="gov-label">SALUD:</span>
                    <span class="gov-val">${gov?.health || 'N/A'}</span>
                    <span class="gov-label" style="margin-left:8px;">APROBACIÓN:</span>
                    <span class="gov-val">${gov?.approval_required ? 'REQUERIDA' : 'LIBRE'}</span>
                </div>
                ${decisionList.length > 0 ? `
                    <div style="margin-top:5px; font-size:0.55rem; color:rgba(255,255,255,0.5);">
                        Decisiones: ${decisionList.slice(0, 3).join(' · ')}
                    </div>
                ` : ''}
            </div>
        `;
    }

    renderMultimodalReportTimeline(report) {
        const timeline = report.timeline || [];
        const tech = report.technical_refinement || null;
        const rescue = (report.rescue_impact || [])[0] || null;
        const gov = report.governance || null;
        const goal = report.goal || 'Misión sin objetivo registrado';
        const status = report.status || 'unknown';

        const statusColor = {
            'open': '#0096ff', 'active': '#0096ff',
            'completed': '#00ff88', 'closed': '#00ff88',
            'paused': '#ffcc00', 'failed': '#ff4444'
        }[status?.toLowerCase()] || '#fff';

        const noTimeline = timeline.length === 0;

        return `
            <div class="mm-report-container" style="padding:4px 2px;">
                ${report.drift ? this.renderDriftBadge(report.drift) : ''}
                <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
                    <div style="font-size:0.58rem; color:rgba(255,255,255,0.35); font-family:'Outfit'; max-width:70%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${goal}">
                        GOAL: ${goal}
                    </div>
                    <div style="font-size:0.55rem; padding:2px 8px; border-radius:8px; background:rgba(0,0,0,0.3); border:1px solid ${statusColor}; color:${statusColor}; font-weight:bold;">
                        ${status.toUpperCase()}
                    </div>
                </div>

                ${noTimeline
                ? `<div class="mm-empty-state">Sin eventos multimodales registrados en esta misión.</div>`
                : `
                    <div style="background:rgba(0,0,0,0.2); border:1px solid rgba(255,255,255,0.05); padding:8px; border-radius:6px; margin-bottom:12px; display:flex; gap:8px; align-items:center;">
                        <input type="text" id="mm-archive-search-${report.mission_id}" placeholder="Búsqueda profunda en archivo..." 
                               style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); color:#fff; font-size:0.6rem; padding:4px 8px; border-radius:4px; flex-grow:1; outline:none;"
                               onkeyup="if(event.key === 'Enter') window.omniPizarron.searchMissionArchive('${report.mission_id}', this.value)">
                        <button class="pizarron-btn-mini" onclick="window.omniPizarron.searchMissionArchive('${report.mission_id}', document.getElementById('mm-archive-search-${report.mission_id}').value)" style="margin:0; background:rgba(0,229,255,0.1); border-color:rgba(0,229,255,0.2); color:#00e5ff;">🔍 BUSCAR</button>
                    </div>
                    <div class="mm-timeline">
                        ${timeline.map((n, i) => this.renderTimelineNode(n)).join('')}
                        ${this.renderTechNode(tech)}
                        ${this.renderRescueNode(rescue)}
                        ${this.renderGovNode(gov, gov?.decisions)}
                    </div>`
            }

                <div style="margin-top:8px; font-size:0.5rem; color:rgba(255,255,255,0.2); text-align:right; font-family:'Courier New';">
                    🔒 OmniWeb Multimodal Report v1 · ${timeline.length} evento(s)
                </div>
            </div>
        `;
    }

    renderHandoffCard(handoff) {
        if (!handoff) return '';
        const milestones = handoff.timeline_milestones || [];
        const nextSteps = handoff.next_steps || [];

        return `
            <div class="pizarron-card handoff-card animate-slide-in" style="border-left: 4px solid #00ff88; background: rgba(0,255,136,0.03);">
                <div style="display:flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div>
                        <h4 style="margin:0; color: #00ff88; font-family: 'Outfit';">MISIÓN CERRADA: HANDOFF</h4>
                        <span style="font-size: 0.6rem; opacity: 0.6; text-transform: uppercase; letter-spacing: 1px;">ID: ${handoff.mission_id.substring(0, 8)}...</span>
                    </div>
                    <span style="font-size: 1.2rem;">📦</span>
                </div>

                <div class="handoff-section" style="margin-bottom: 15px;">
                    <b style="font-size: 0.85rem; display: block; margin-bottom: 5px; color: #fff;">${handoff.goal}</b>
                    <p style="font-size: 0.75rem; color: #ccc; margin: 0; line-height: 1.4;">${handoff.executive_summary}</p>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div class="handoff-sub-section">
                        <span class="section-title" style="color: #00ff88; font-size:0.55rem;">HITOS DE LOGROS</span>
                        <ul style="padding-left: 15px; margin: 5px 0; font-size: 0.65rem; color: #aaa; list-style-type: none;">
                            ${milestones.map(m => `<li style="margin-bottom:3px;">${m}</li>`).join('')}
                        </ul>
                    </div>
                    <div class="handoff-sub-section">
                        <span class="section-title" style="color: #00ccff; font-size:0.55rem;">SIGUIENTES PASOS</span>
                        <ul style="padding-left: 0; margin: 5px 0; font-size: 0.65rem; color: #00ccff; list-style-type: none;">
                            ${nextSteps.map(s => `<li style="margin-bottom:3px;">➔ ${s}</li>`).join('')}
                        </ul>
                    </div>
                </div>

                <div class="handoff-footer" style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 0.6rem; color: #888;">
                        Gobernanza: <span style="color: #00ff88;">NOMINAL</span>
                    </div>
                    <button class="pizarron-btn-mini" style="background: rgba(0,255,136,0.1); border: 1px solid #00ff88; color: #00ff88; margin: 0;" onclick="window.omniShell.addInput('list chips')">IR A CHIPS</button>
                </div>
            </div>
        `;
    }

    async validateRecall(missionId, snapshotId, approved) {
        try {
            const res = await fetch(`/api/v1/ai-host/execution/mission/${missionId}/recall/validate?snapshot_id=${snapshotId}&approved=${approved}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            if (res.ok) {
                this.loadMultimodalReport(missionId);
            }
        } catch (err) {
            console.error("Recall validation failed", err);
        }
    }

    async reactivateSnapshot(missionId, snapshotId, active) {
        try {
            const res = await fetch(`/api/v1/ai-host/execution/mission/${missionId}/recall/reactivate?snapshot_id=${snapshotId}&active=${active}&reason=Intervención manual en cockpit`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            if (res.ok) {
                this.loadMultimodalReport(missionId);
            }
        } catch (err) {
            console.error("Manual reactivation failed", err);
        }
    }

    async searchMissionArchive(missionId, query) {
        if (!query) {
            this.loadMultimodalReport(missionId);
            return;
        }
        try {
            const res = await fetch(`/api/v1/ai-host/execution/mission/${missionId}/multimodal/report`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const data = await res.json();

            // PHASE 61: Inject Drift Analysis
            const driftRes = await fetch(`/api/v1/ai-host/execution/mission/${missionId}/drift`, {
                headers: { 'Authorization': `Bearer ${localStorage.getItem('omni_token') || 'omniweb-dev-secret-token'}` }
            });
            const driftData = await driftRes.json();
            if (driftData.status === 'success') {
                data.report.drift = driftData.report;
            }

            if (data.status === 'success') {
                const reportZone = document.querySelector('.mm-report-container');
                if (reportZone) {
                    // Update only the timeline part to show search results
                    const timelineList = reportZone.querySelector('.mm-timeline');
                    if (timelineList) {
                        timelineList.innerHTML = `
                            <div style="background:rgba(0,150,255,0.05); border:1px solid rgba(0,150,255,0.1); padding:6px; border-radius:4px; margin-bottom:10px; font-size:0.55rem; color:#0096ff; font-weight:bold;">
                                🔎 ${data.count} resultados para "${query}"
                            </div>
                            <div class="mm-timeline">
                                ${data.results.map(n => this.renderTimelineNode(n)).join('')}
                            </div>
                        `;
                        // Note: I need an instance for renderTimelineNode if it was internal, but it was defined inside the main method in the previous view. 
                        // I'll fix the structure to make renderTimelineNode a class method.
                    }
                }
            }
        } catch (err) {
            console.error("Search failed", err);
        }
    }
}

window.pizarronUI = new PizarronVivoUI();
window.omniPizarron = window.pizarronUI;
