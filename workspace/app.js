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
            body: "<strong>Superficie viva.</strong><br><br>El espacio vacío-vivo donde los usuarios activan, combinan y expanden chips bajo gobierno de Omni.<br><br><strong>Fases de crecimiento de chip:</strong><br>visible → activo → aumentado cognitivamente → compartible."
        },
        "omniweb": {
            title: "OMNIWEB [IA HOST]",
            body: "<strong>IA Host soberana.</strong><br><br>Interpreta, decide, gobierna y coordina."
        },
        "omniword": {
            title: "OMNIWORD [BITÁCORA / PANEL]",
            body: "<strong>Bitácora/panel.</strong><br><br>Muestra chips, estados, actividad y trabajo."
        },
        "creator": {
            title: "CREATOR MODE",
            body: "<strong>Cabina profunda del creador:</strong><br><br>Edición, permisos, control y aprobación."
        },
        "commons": {
            title: "CHIP COMMONS",
            body: "<strong>Biblioteca viva de chips</strong> reutilizables creados por el ecosistema."
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
});

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
    const data = systemData.nodes[nodeId];
    if (data) {
        showModal(data.title, data.body);
    }

    // Add ping effect to console
    const term = document.getElementById('console-output');
    term.innerHTML = `> PING to ${nodeId.toUpperCase()}... CONNECTION ESTABLISHED.<br>` + term.innerHTML;
}

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
