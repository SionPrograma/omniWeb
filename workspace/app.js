// Data extracted from PDF Reference
const systemData = {
    layers: [
        { id: 1, name: "1. Superficie pública", desc: "OmniWord + Omniverse público. Paneles, chips visibles, chat, mapas de actividad, botones y estados." },
        { id: 2, name: "2. IA Host soberana", desc: "OmniWeb. Entiende intención, selecciona estrategia, vigila seguridad, decide qué puede ejecutarse." },
        { id: 3, name: "3. Orquestación cognitiva", desc: "Capability / Cognitive Orchestration Layer. Divide tareas, asigna subagentes, conecta herramientas y unifica resultados." },
        { id: 4, name: "4. Runtime de chips", desc: "Módulos internos, chips del creador, chips públicos y chips de comunidad, todos con contrato, permisos y estados." },
        { id: 5, name: "5. Bridges / Tools", desc: "MCP, APIs, motores open source, RAG, TTS/STT, traductores, runtimes locales, automatizaciones y bases externas." },
        { id: 6, name: "6. Memoria / evidencia", desc: "Bitácora, trazas, métricas, sesiones, observabilidad, evaluación, logs, fallos y conocimiento acumulado." },
        { id: 7, name: "7. Gobernanza", desc: "Policy Layer, permisos, humano en el loop, cuarentena, rollback, visibilidad y control de cambios." }
    ],
    roles: [
        { name: "Analista", desc: "Entiende el problema" },
        { name: "Planner", desc: "Arma pasos" },
        { name: "Builder", desc: "Genera solución" },
        { name: "Reviewer", desc: "Revisa calidad" },
        { name: "Debugger", desc: "Aísla fallos" },
        { name: "Translator", desc: "Opera lenguaje" },
        { name: "Observer", desc: "Mide trazas" },
        { name: "Guardian", desc: "Aplica reglas" }
    ],
    roadmap: [
        { title: "Bloque 1", desc: "Cerrar personalidad, estabilidad y policy del lenguaje" },
        { title: "Bloque 2", desc: "Visualizar chips y estados en Omniverse / HUB" },
        { title: "Bloque 3", desc: "Integrar Stage B opcional con timeout, rollback y fallback" },
        { title: "Bloque 4", desc: "Separar Idiomas (interno) de Lingua (externo/terceros)" },
        { title: "Bloque 5", desc: "Formalizar estándar de chips para comunidad" },
        { title: "Bloque 6", desc: "Abrir Chip Commons / biblioteca viva gobernada" }
    ],
    nodes: {
        "omniverse": {
            title: "OMNIVERSE [SUPERFICIE VIVA]",
            body: "<strong>Superficie viva.</strong><br><br>El espacio vacío-vivo donde los usuarios activan, combinan y expanden chips bajo gobierno de Omni.<br><br><strong>Fases de crecimiento de chip:</strong><br>visible → activo → aumentado cognitivamente → compartible.",
            file_path: "chips/README.md"
        },
        "omniweb": {
            title: "OMNIWEB [IA HOST]",
            body: "<strong>IA Host soberana.</strong><br><br>Interpreta, decide, gobierna y coordina.",
            file_path: "backend/core/main.py"
        },
        "omniword": {
            title: "OMNIWORD [BITÁCORA / PANEL]",
            body: "<strong>Bitácora/panel.</strong><br><br>Muestra chips, estados, actividad y trabajo.",
            file_path: "frontend/shell/index.html"
        },
        "creator": {
            title: "CREATOR MODE",
            body: "<strong>Cabina profunda del creador:</strong><br><br>Edición, permisos, control y aprobación.",
            file_path: "frontend/shell/creator.js"
        },
        "idiomas": {
            title: "CHIP IDIOMAS",
            body: "Gestión de fluidez y traducción Stage A/B.",
            file_path: "chips/chip-idiomas/index.js"
        }
    },
    principles: {
        title: "IDEA CENTRAL",
        content: "OmniWeb gobierna. OmniWord organiza. Omniverse aloja. Los chips ejecutan capacidades. Las capas cognitivas amplían el sistema sin quitar soberanía."
    }
};

// Initialize UI
document.addEventListener('DOMContentLoaded', () => {
    initClock();
    renderLayers();
    renderRoles();
    renderRoadmap();

    // START TELEMETRY BRIDGE (Phase 1 Admission)
    initTelemetryBridge();

    // UI HANDLERS (Phase 2 & 3 Admission)
    setupRepairFlowHandlers();
    setupCopilotHandlers();

    // Auto-collapse secondaries for cleaner start
    setTimeout(() => {
        toggleSection('section-layers');
        toggleSection('section-capabilities');
    }, 1000);
});

function toggleSection(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.toggle('collapsed');
    const trigger = el.querySelector('.collapsible-trigger');
    if (trigger) {
        trigger.innerText = el.classList.contains('collapsed') ? '▶' : '▼';
    }
}

// --- SPATIAL WORKSPACE NAVIGATION (Fix for Mixed State) ---
window.setSpatialView = function (viewId) {
    // Hide all sections
    document.querySelectorAll('.workspace-section').forEach(sec => {
        sec.style.display = 'none';
    });

    // Show target section
    const target = document.getElementById(viewId);
    if (target) {
        target.style.display = 'flex';
    }

    // Update tabs UI
    document.querySelectorAll('.spatial-nav-tabs button').forEach(btn => {
        btn.style.background = 'transparent';
        btn.style.borderColor = 'rgba(255,255,255,0.2)';
        btn.style.color = 'var(--text-muted)';
    });

    const activeTab = document.getElementById('tab-' + viewId);
    if (activeTab) {
        activeTab.style.background = 'rgba(0,255,136,0.1)';
        activeTab.style.borderColor = 'rgba(0,255,136,0.3)';
        activeTab.style.color = 'var(--text-main)';
    }

    // Scroll to top
    const workspace = document.querySelector('.central-workspace');
    if (workspace) workspace.scrollTop = 0;
};

// --- TELEMETRY & LOG BRIDGE ---
let lastLogSyncTime = 0;

function initTelemetryBridge() {
    console.log("[OMNIVERSE] Initializing Telemetry/Log Bridge...");

    const syncState = () => {
        try {
            if (window.parent && window.parent.creatorEnv) {
                const parentEnv = window.parent.creatorEnv;
                if (parentEnv.systemState) {
                    updateVisualTelemetry(parentEnv.systemState);
                    updateTreeDiagnostics(parentEnv.systemState);
                } else {
                    // Fallback: indicate connecting
                    const consoleOutput = document.getElementById('console-output');
                    if (consoleOutput && !consoleOutput.innerText.includes("CONNECTING")) {
                        consoleOutput.innerHTML = `<span style="color:var(--primary-cyan)">> WAITING FOR SHELL HANDSHAKE...</span><br>` + consoleOutput.innerHTML;
                    }
                }
            }
        } catch (e) {
            console.warn("[OMNIVERSE] Telemetry Bridge: parent context inaccessible.");
        }
    };

    const syncLogs = async () => {
        try {
            const response = await fetch('/api/v1/system/logbook/', {
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            const rawData = await response.json();
            const entries = rawData.payload?.payload?.entries || rawData.payload?.entries || rawData.entries || [];

            if (Array.isArray(entries) && entries.length > 0) {
                mirrorLogsToConsole(entries);
            }
        } catch (e) {
            console.warn("[OMNIVERSE] Log mirror failed.");
        }
    };

    // Fast initial sync, then interval
    syncState();
    syncLogs();
    setInterval(syncState, 2000);
    setInterval(syncLogs, 5000); // Polling logs every 5s is safer than extreme high freq
}

function mirrorLogsToConsole(entries) {
    const consoleOutput = document.getElementById('console-output');
    if (!consoleOutput) return;

    // Get only new entries since last sync
    const newEntries = entries.filter(e => e.timestamp > lastLogSyncTime).sort((a, b) => a.timestamp - b.timestamp);
    if (newEntries.length === 0) return;

    newEntries.forEach(entry => {
        const time = new Date(entry.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        let color = '#fff';
        if (entry.type === 'bug') color = 'var(--alert-orange)';
        if (entry.type === 'auto_fix') color = 'var(--secondary-emerald)';
        if (entry.type === 'system_audit') color = 'var(--primary-cyan)';

        const logHtml = `<span style="opacity:0.4;">[${time}]</span> <span style="color:${color}">[${entry.type.toUpperCase()}]</span> ${entry.content}<br>`;
        consoleOutput.innerHTML = logHtml + consoleOutput.innerHTML;

        // --- SPATIAL LOG INJECTION (Safe Step) ---
        injectSpatialSignal(entry);

        // Keep console from overflowing too much
        if (consoleOutput.innerHTML.length > 5000) {
            consoleOutput.innerHTML = consoleOutput.innerHTML.substring(0, 3000);
        }
    });

    lastLogSyncTime = Math.max(...newEntries.map(e => e.timestamp));
}

function injectSpatialSignal(entry) {
    const branches = document.querySelectorAll('.tree-branch > .leaf-node');
    if (branches.length < 3) return;

    let targetBranch = null;

    // Logic to route logs to branches
    if (entry.type === 'bug' || entry.chip_reference) {
        targetBranch = branches[1]; // RAMA B: CHIPS
    } else if (entry.type === 'system_audit' || entry.type === 'auto_fix') {
        targetBranch = branches[2]; // RAMA C: DATA / GOBERNANZA
    }

    if (targetBranch) {
        const p = targetBranch.querySelector('p');
        const originalText = p.innerText;

        // Flash effect
        targetBranch.style.boxShadow = `0 0 15px ${entry.type === 'bug' ? 'var(--alert-orange)' : 'var(--primary-cyan)'}`;
        p.innerHTML = `<span style="color:${entry.type === 'bug' ? 'var(--alert-orange)' : 'var(--primary-cyan)'}">SIGNAL: ${entry.content.substring(0, 30)}...</span>`;

        setTimeout(() => {
            targetBranch.style.boxShadow = '';
            p.innerText = originalText;
        }, 4000);
    }
}

function updateVisualTelemetry(state) {
    if (!state) return;

    // 1. Update Vista Sistema Indicators
    // Core Engine -> Sync with Shell AI status
    const coreNode = document.querySelector('#vista-sistema .cabin-node:nth-child(1)');
    if (coreNode) {
        const dot = coreNode.querySelector('.dot');
        const statusText = coreNode.querySelector('.status-indicator');
        const isOnline = state.ai_host && state.ai_host.status === 'online';
        if (dot) dot.style.background = isOnline ? 'var(--secondary-emerald)' : 'var(--alert-orange)';
        if (statusText) statusText.innerHTML = `<span class="dot" style="background:${isOnline ? 'var(--secondary-emerald)' : 'var(--alert-orange)'}"></span> STATUS: ${isOnline ? 'ACTIVE' : 'OFFLINE'}`;
    }

    // Orchestrator -> Uptime or Branch
    const orchNode = document.querySelector('#vista-sistema .cabin-node:nth-child(2)');
    if (orchNode) {
        const statusText = orchNode.querySelector('.status-indicator');
        if (statusText) statusText.innerHTML = `<span class="dot" style="background:var(--primary-cyan)"></span> MODE: ${state.mode || 'UNKNOWN'}`;
    }

    // Policy Layer -> Threat or Health
    const policyNode = document.querySelector('#vista-sistema .cabin-node:nth-child(3)');
    if (policyNode) {
        const statusText = policyNode.querySelector('.status-indicator');
        const health = state.health || 'nominal';
        const healthColor = health === 'nominal' ? 'var(--secondary-emerald)' : 'var(--alert-orange)';
        if (statusText) statusText.innerHTML = `<span class="dot" style="background:${healthColor}"></span> HEALTH: ${health.toUpperCase()}`;
    }

    // 2. Update System Metrics Header (Enriched Hardening)
    const memEl = document.getElementById('metric-mem');
    const latEl = document.getElementById('metric-lat');
    const verEl = document.getElementById('metric-ver');

    if (memEl && state.memory_usage) memEl.innerText = `${state.memory_usage.rss_mb}MB`;
    if (latEl && state.flow_data && state.flow_data.ai_to_chips) latEl.innerText = `${state.flow_data.ai_to_chips.latency}ms`;
    if (verEl) verEl.innerText = state.version || '1.0.4';

    const govStatus = document.getElementById('gov-status');
    const govLabel = document.getElementById('gov-label');
    if (govStatus && govLabel) {
        const isProcessing = state.status === 'processing' || state.is_healing;
        if (isProcessing) {
            govStatus.classList.add('processing');
            govLabel.innerText = "GOVERNANCE: EVOLVING";
        } else {
            govStatus.classList.remove('processing');
            govLabel.innerText = "GOVERNANCE: NOMINAL";
        }
    }

    // 4. Update Roadmap from Active/Parallel Missions
    const roadmapList = document.getElementById('roadmap-list');
    if (roadmapList && (state.active_mission || (state.parallel_missions && state.parallel_missions.length > 0))) {
        let roadmapHtml = '';
        if (state.active_mission) {
            roadmapHtml += `
                <div class="roadmap-item active">
                    <div class="roadmap-dot active"></div>
                    <div class="roadmap-info">
                        <div class="roadmap-title" style="color:var(--creator-gold)">MISSION: ${state.active_mission.name}</div>
                        <div class="roadmap-desc">ID: ${state.active_mission.mission_id.substring(0, 8)}... | ${state.active_mission.status}</div>
                    </div>
                </div>
            `;
        }
        if (state.parallel_missions) {
            state.parallel_missions.forEach(m => {
                roadmapHtml += `
                    <div class="roadmap-item">
                        <div class="roadmap-dot active"></div>
                        <div class="roadmap-info">
                            <div class="roadmap-title">${m.name}</div>
                            <div class="roadmap-desc">Sincronización paralela activa.</div>
                        </div>
                    </div>
                `;
            });
        }
        // Only update if we have new data to avoid flicker vs static fallback
        if (roadmapHtml) {
            roadmapList.innerHTML = roadmapHtml;
        }
    }

    // 5. Update Capabilities & Registry Panel
    const capGrid = document.getElementById('capabilities-grid');
    if (capGrid && state.chips && state.chips.length > 0) {
        capGrid.innerHTML = state.chips.map(chip => {
            const statusColor = chip.health === 'healthy' ? 'var(--secondary-emerald)' : 'var(--alert-orange)';
            return `
                <div class="capability-card" onclick="creatorAction('inspect', '${chip.slug}')">
                    <div class="cap-header">
                        <span class="cap-name">${chip.name}</span>
                        <span class="status-dot" style="background:${statusColor}"></span>
                    </div>
                    <div class="cap-meta">${chip.type.toUpperCase()} | ${chip.health.toUpperCase()}</div>
                </div>
            `;
        }).join('');
    }

    // 6. Update Audit Ledger
    const auditLedger = document.getElementById('audit-ledger');
    if (auditLedger && state.auditor_summary) {
        const issues = state.auditor_summary.issues || [];
        if (issues.length === 0) {
            auditLedger.innerHTML = '<div class="audit-item success">SISTEMA ÍNTEGRO. No se detectaron deudas estructurales.</div>';
        } else {
            auditLedger.innerHTML = issues.map(issue => `
                <div class="audit-item ${issue.level.toLowerCase()}" onclick="creatorAction('openEvidence', '${issue.sector}')">
                    <div class="audit-header">
                        <span>[${issue.sector}] ${issue.level}</span>
                    </div>
                    <div class="audit-msg">${issue.message}</div>
                </div>
            `).join('');
        }
    }
    // 7. Update Repair Flow Section
    updateRepairFlow(state);
}

function setupCopilotHandlers() {
    const input = document.getElementById('omniverse-copilot-input');
    const sendBtn = document.getElementById('omniverse-copilot-send');

    if (sendBtn && input) {
        sendBtn.addEventListener('click', () => triggerCopilotMessage());
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                triggerCopilotMessage();
            }
        });
    }

    // Mirror messages from shell if they happen there
    // We poll the shell's copilot log every 2 seconds for new messages
    setInterval(() => syncCopilotHistory(), 2000);
}

function triggerCopilotMessage() {
    const input = document.getElementById('omniverse-copilot-input');
    const text = input.value.trim();
    if (!text) return;

    creatorAction('copilot_send', text);
    input.value = '';
}

function syncCopilotHistory() {
    try {
        const shell = window.parent;
        const shellLog = shell.document.getElementById('ws-copilot-log');
        const localLog = document.getElementById('omniverse-copilot-log');

        if (shellLog && localLog) {
            // Simple mirroring strategy: if counts differ, re-render
            const shellMsgs = shellLog.querySelectorAll('.copilot-msg');
            const localMsgs = localLog.querySelectorAll('.msg:not(.system)');

            if (shellMsgs.length > localMsgs.length) {
                const fragment = document.createDocumentFragment();
                for (let i = localMsgs.length; i < shellMsgs.length; i++) {
                    const sMsg = shellMsgs[i];
                    const lMsg = document.createElement('div');
                    lMsg.className = `msg ${sMsg.classList.contains('user') ? 'user' : 'ai'}`;
                    lMsg.innerText = sMsg.innerText;
                    fragment.appendChild(lMsg);
                }
                localLog.appendChild(fragment);
                localLog.scrollTop = localLog.scrollHeight;
            }
        }
    } catch (e) {
        // Parent might be inaccessible in standalone
    }
}

function updateRepairFlow(state) {
    const instruction = document.getElementById('repair-instruction');
    const container = document.getElementById('repair-actions-container');
    const flowSteps = document.querySelectorAll('.flow-step');

    // Detect if there's a real active proposal in the shell's builder
    let activeProposal = null;
    try {
        if (window.parent.builderUI && window.parent.builderUI.currentPreviewId) {
            activeProposal = window.parent.builderUI.currentPreviewId;
        }
    } catch (e) { }

    if (activeProposal) {
        if (instruction) instruction.innerText = "PROPUESTA DE PARCHE DETECTADA. El sistema espera su decisión para proceder.";
        if (container) container.classList.add('waiting-approval');
        // Activate "Propose" step
        flowSteps.forEach((s, idx) => {
            if (idx === 2) s.classList.add('active'); // Step 3: Propose
            else if (idx < 2) s.classList.add('done');
        });
    } else if (state.active_mission) {
        if (instruction) instruction.innerText = `EJECUTANDO: ${state.active_mission.name}. Misión bajo gobierno activo.`;
        flowSteps.forEach((s, idx) => {
            if (idx === 4) s.classList.add('active'); // Step 5: Apply
            else if (idx < 4) s.classList.add('done');
        });
    } else {
        if (instruction) instruction.innerText = "Esperando propuesta de reparación del sistema...";
        if (container) container.classList.remove('waiting-approval');
    }
}

function creatorAction(type, payload) {
    console.log(`[OMNIVERSE] Triggering Creator Action: ${type}`, payload);

    // Governance Pulse Feedback
    const govStatus = document.getElementById('gov-status');
    if (govStatus) {
        govStatus.classList.add('processing');
        setTimeout(() => govStatus.classList.remove('processing'), 2000);
    }

    try {
        const shell = window.parent;
        if (!shell.creatorEnv) return;

        switch (type) {
            case 'inspect':
                // Use the shell's existing inspection logic
                if (shell.creatorEnv.runInspection) {
                    shell.creatorEnv.runInspection(payload);
                    // Also switch back to shell if desired, but user wants Omniverse as analysis surface
                    // For now, only trigger the inspection in the shell's background or console
                }
                break;
            case 'openEvidence':
                if (shell.creatorEnv.openArtifactPreview) {
                    shell.creatorEnv.openArtifactPreview(payload);
                }
                break;
            case 'approve':
            case 'reject':
                const btns = document.querySelectorAll('.btn-action');
                btns.forEach(b => b.classList.add('processing'));
                setTimeout(() => btns.forEach(b => b.classList.remove('processing')), 3000);

                if (shell.builderUI && shell.builderUI.decidePreview) {
                    shell.builderUI.decidePreview(type === 'approve');
                }
                break;
            case 'copilot_send':
                if (shell.creatorEnv && shell.creatorEnv.sendCopilotPrompt) {
                    // We inject the text into the shell's input then trigger the shell's method
                    // to reuse all its context (current file, state, etc.)
                    const shellInput = shell.document.getElementById('ws-copilot-input');
                    if (shellInput) {
                        shellInput.value = payload;
                        shell.creatorEnv.sendCopilotPrompt();
                    }
                }
                break;
            case 'refresh':
                if (shell.creatorEnv.forceSync) {
                    shell.creatorEnv.forceSync();
                }
                break;
        }
    } catch (e) {
        console.warn("[OMNIVERSE] Action failed: Shell context inaccessible.");
    }
}

function updateTreeDiagnostics(state) {
    if (!state) return;

    // --- TRUNK: OMNIVERSE ROOT ---
    const rootNode = document.querySelector('.tree-trunk > .leaf-node');
    if (rootNode) {
        const isOnline = state.ai_host && state.ai_host.status === 'online';
        rootNode.className = `leaf-node ${isOnline ? 'active' : 'offline'}`;
        const p = rootNode.querySelector('p');
        if (p) p.innerText = isOnline ? 'Núcleo Central: ACTIVO' : 'Núcleo Central: DESCONECTADO';
    }

    // --- BRANCHES ---
    const branches = document.querySelectorAll('.tree-branch > .leaf-node');
    if (branches.length >= 3) {
        // RAMA A: UI / SHELL
        const uiBranch = branches[0];
        uiBranch.innerHTML = `<h4>RAMA A: SHELL</h4><p>Estado: NOMINAL</p>`;
        uiBranch.className = 'leaf-node active';

        // RAMA B: LOGIC / CHIPS
        const logicBranch = branches[1];
        const chipsCount = state.chips ? state.chips.length : 0;
        const healthyChips = state.chips ? state.chips.filter(c => c.health === 'healthy').length : 0;
        const logicHealth = (healthyChips === chipsCount) ? 'active' : (healthyChips > 0 ? 'warning' : 'offline');
        logicBranch.innerHTML = `<h4>RAMA B: CHIPS</h4><p>${healthyChips}/${chipsCount} Módulos Saludables</p>`;
        logicBranch.className = `leaf-node ${logicHealth}`;

        // RAMA C: GOBERNANZA / DATA
        const dataBranch = branches[2];
        const isDbOk = state.database && state.database.connected;
        dataBranch.innerHTML = `<h4>RAMA C: DATA</h4><p>${isDbOk ? 'Persistencia: OK' : 'DB Link: FALLIDO'}</p>`;
        dataBranch.className = `leaf-node ${isDbOk ? 'active' : 'offline'}`;
    }

    // --- DIAGNOSTIC CARDS ---
    const diagCards = document.querySelectorAll('.diag-view .diag-card');
    if (diagCards.length >= 2) {
        // Lectura del estado
        const missionInfo = state.active_mission ? `Misión [${state.active_mission.name}] en progreso.` : 'Sin misiones tácticas activas.';
        const latencyVal = state.flow_data?.ai_to_chips?.latency || 0;
        const latencyStatus = latencyVal < 50 ? '<span style="color:var(--secondary-emerald)">[OPTIMAL]</span>' : (latencyVal < 150 ? '<span style="color:var(--primary-cyan)">[NOMINAL]</span>' : '<span style="color:var(--alert-orange)">[CONGESTED]</span>');

        diagCards[0].innerHTML = `
            <h5>Lectura del estado</h5>
            <p>${missionInfo} Salud: ${state.health?.toUpperCase() || 'PENDIENTE'}. Latencia: ${latencyStatus}</p>
        `;

        // Qué ve el humano
        const healingMsg = state.is_healing ? '<span style="color:var(--secondary-emerald)">AUTOCURACIÓN EN PROGRESO.</span>' : 'Gobernanza nominal.';
        diagCards[1].innerHTML = `
            <h5>Análisis de Seguridad</h5>
            <p>${healingMsg} Conexión con AI Host: ${state.ai_host?.status?.toUpperCase() || 'OFFLINE'}.</p>
        `;
        diagCards[1].style.borderColor = state.health === 'error' ? 'var(--alert-orange)' : 'var(--secondary-emerald)';
    }
}


function initClock() {
    const timeDisplay = document.querySelector('.time-display');
    const start = Date.now();

    setInterval(() => {
        const diff = (Date.now() - start) / 1000;
        timeDisplay.textContent = `T+${diff.toFixed(3)}`;
    }, 50); // fast update for futuristic feel
}

function renderLayers() {
    const list = document.getElementById('layers-list');
    systemData.layers.forEach(layer => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${layer.name}</strong>`;
        li.onclick = () => showModal(layer.name, layer.desc);
        list.appendChild(li);
    });
}

function renderRoles() {
    const pool = document.getElementById('roles-list');
    if (!pool) return;
    systemData.roles.forEach(role => {
        const span = document.createElement('span');
        span.textContent = role.name;
        span.classList.add('interactive-step');
        span.onclick = () => showModal(`Rol: ${role.name}`, role.desc);
        pool.appendChild(span);
    });
}

function renderRoadmap() {
    const list = document.getElementById('roadmap-list');
    systemData.roadmap.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${item.title}</strong><br><span style="font-size:0.85em; color:var(--text-muted); opacity:0.8; display:block; margin-top:4px; line-height: 1.3;">${item.desc}</span>`;
        list.appendChild(li);
    });
}

// Interaction
function focusNode(nodeId) {
    const node = systemData.nodes[nodeId];
    if (node) {
        const bodyHtml = `
            <div class="node-info">
                ${node.body}
                ${node.file_path ? `
                    <div class="spatial-actions" style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">
                        <button class="btn-mini primary" onclick="openSpatialEditor('${node.file_path}')">OPEN_LOGIC [${node.file_path}]</button>
                    </div>
                ` : ''}
            </div>
        `;
        showModal(node.title, bodyHtml);
    }

    // Add ping effect to console
    const term = document.getElementById('console-output');
    term.innerHTML = `> PING to ${nodeId.toUpperCase()}... CONNECTION ESTABLISHED.<br>` + term.innerHTML;
}

// --- Spatial Editor Bridge (Block 04) ---
function openSpatialEditor(path) {
    if (!path) return;
    const shell = window.parent;
    const modal = document.getElementById('spatial-editor-modal');
    const textarea = document.getElementById('spatial-editor-textarea');
    const pathLabel = document.getElementById('editor-node-path');
    const status = document.getElementById('editor-status');

    if (modal && textarea && shell.creatorEditor) {
        modal.style.display = 'flex';
        pathLabel.innerText = path;
        status.innerText = "LOADING: Synchronizing with shell authority...";
        textarea.value = ""; // Clear while loading

        shell.creatorEditor.openFile(path, (content) => {
            if (content && typeof content === 'string') {
                textarea.value = content;
                status.innerText = "ONLINE: Governing sector logic.";
            } else if (content && content.error) {
                status.innerText = "ERROR: " + content.error;
            } else {
                status.innerText = "ONLINE: File opened.";
            }
            updateGutter();
        });
    } else {
        console.warn("[OMNIVERSE] Editor Authority not found in Shell.");
    }
}

function closeSpatialEditor() {
    const modal = document.getElementById('spatial-editor-modal');
    if (modal) modal.style.display = 'none';
}

function saveSpatialEditor() {
    const shell = window.parent;
    const path = document.getElementById('editor-node-path').innerText;
    const content = document.getElementById('spatial-editor-textarea').value;
    const status = document.getElementById('editor-status');

    if (shell.creatorEditor && shell.creatorEditor.saveFile) {
        status.innerText = "SAVING: Requesting creator approval...";
        shell.creatorEditor.saveFile(path, content, (success) => {
            if (success) {
                status.innerText = "SUCCESS: Changes registered.";
                setTimeout(() => status.innerText = "ONLINE: Governing sector logic.", 3000);
            } else {
                status.innerText = "SAVE_FAILED: Authority rejected the request.";
            }
        });
    }
}

function updateGutter() {
    const textarea = document.getElementById('spatial-editor-textarea');
    const gutter = document.getElementById('editor-gutter');
    if (!textarea || !gutter) return;

    const lines = textarea.value.split('\n').length;
    let numbers = '';
    for (let i = 1; i <= lines; i++) {
        numbers += i + '<br>';
    }
    gutter.innerHTML = numbers;
}

// Global exposure for onClick handlers
window.openSpatialEditor = openSpatialEditor;
window.closeSpatialEditor = closeSpatialEditor;
window.saveSpatialEditor = saveSpatialEditor;
window.updateGutter = updateGutter;

function showModal(title, body) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = body;
    document.getElementById('detail-modal').classList.add('active');
}

function closeModal() {
    document.getElementById('detail-modal').classList.remove('active');
}

function toggleConsole() {
    const footer = document.querySelector('.sys-footer');
    footer.classList.toggle('hideable');
    if (footer.style.opacity === '0.2') {
        footer.style.opacity = '1';
    } else {
        footer.style.opacity = '0.2';
    }
}
