import { navigation } from '/core/navigation/nav-system.js';
import { stateManager } from '/core/state/state-manager.js';

// ---- Config & Initialization ----
const CHIP_ID = 'programacion';

// Edu Content Database
const contentDB = {
    fundamentos: {
        title: "Fundamentos de Sistemas",
        subtitle: "Cómo pensar proyectos reales.",
        cards: [
            {
                type: "logic",
                title: "1. El Problema",
                body: "Todo software nace para resolver un problema. Antes de escribir código, define exactamennte **QUÉ** estás resolviendo. Un 'chip' no es solo un botón, es un micro-sistema cerrado con una meta clara.",
                code: "// Ejemplo Mental\nProblema: \"Pierdo dinero sin darme cuenta\"\nSolución: Chip-Finanzas\nAlcance Limitado: Solo tracking manual de gastos, sin bancos API."
            },
            {
                type: "",
                title: "2. Datos & Estado",
                body: "Un programa es una máquina que transforma datos. El Estado (State) es la memoria viva de tu app. Tienes que saber qué datos necesitas persistir y cuáles son temporales (en la vista).",
                code: "let state = { transactions: [], balance: 0 };"
            }
        ]
    },
    logica: {
        title: "Lógica & Flujo",
        subtitle: "El camino de los datos desde la acción hasta la memoria.",
        cards: [
            {
                type: "logic",
                title: "El Ciclo de Interacción",
                body: "Todo flujo lógico básico sigue 3 pasos: Evento -> Procesamiento -> Renderizado. Cuando el usuario hace click, capturas los datos, aplicas la regla de negocio y redibujas la vista.",
                code: "btn.addEventListener('click', () => {\n  1. Capturar(input);\n  2. Regla(Sumar Ahorro);\n  3. Render(Update DOM);\n});"
            },
            {
                type: "logic",
                title: "Desacoplar Lógica",
                body: "No mezcles la matemática o las peticiones de red dentro del evento de un botón. Extrae tu lógica a funciones puras reusables."
            }
        ]
    },
    arquitectura: {
        title: "Arquitectura",
        subtitle: "Cómo estructuramos OmniWeb.",
        cards: [
            {
                type: "architecture",
                title: "Módulos y Core (El Corazón)",
                body: "Para evitar el 'Código Espagueti', usamos módulos independientes (Chips) que se conectan a un Core Compartido. El Core maneja lo transversal (Navegación, Memoria).",
                code: "├── core/           # Lo que todos comparten\n│   ├── navigation/ # Sabe a dónde ir\n│   └── state/      # Guarda cosas al salir\n└── chips/          # Casos de uso aislados\n    ├── finanzas/\n    └── reparto/"
            },
            {
                type: "architecture",
                title: "Principio de Responsabilidad Única",
                body: "Cada archivo hace UNA sola cosa. `style.css` se ve bonito, `app.js` ejecuta lógica y `index.html` pone la estructura. Nunca mezcles estilos en JS."
            }
        ]
    },
    tecnologias: {
        title: "Tecnologías & Ejecución",
        subtitle: "Las herramientas del arte.",
        cards: [
            {
                type: "tools",
                title: "Vanilla First",
                body: "Para aprender de verdad, empezamos con Vanilla JS, HTML y CSS. Sin React, sin Tailwind. Así entiendes el DOM real y cómo funciona la web desnuda."
            },
            {
                type: "tools",
                title: "Backend Limpio (FastAPI)",
                body: "El backend solo existe para servir archivos, registrar módulos activos y dar seguridad al sistema global. Python con FastAPI es rápido, tipado y claro.",
                code: "@app.get(\"/\")\nasync def root():\n    return FileResponse(\"frontend/dashboard/index.html\")"
            }
        ]
    },
    herramientas: {
        title: "Herramientas del Día a Día",
        subtitle: "Cómo construimos sin volvernos locos.",
        cards: [
            {
                type: "tools",
                title: "Git & Version Control",
                body: "Git no es solo para guardar código, es la historia de tu software. 'Ramas' te permiten jugar sin romper la rama principal. (Ej. `branch architecture`)."
            },
            {
                type: "tools",
                title: "Consola de Desarrollo",
                body: "El Developer Tools del navegador (F12) es tu mejor amigo. Usa `console.log()` inteligentemente y aprende a leer la pestaña 'Network' y 'Application' (Local Storage)."
            }
        ]
    }
};

let currentState = {
    activeTopic: 'fundamentos'
};

// ---- DOM Elements ----
const btnBack = document.getElementById('btn-back');
const topicBtns = document.querySelectorAll('.topic-btn');
const contentDisplay = document.getElementById('content-display');

// ---- Initialization ----
function init() {
    navigation.navigateTo(CHIP_ID);

    // Try to restore previous session state
    const savedState = stateManager.restoreState(CHIP_ID);
    if (savedState && savedState.activeTopic && contentDB[savedState.activeTopic]) {
        currentState.activeTopic = savedState.activeTopic;
    }

    renderContent(currentState.activeTopic);
    updateActiveButton(currentState.activeTopic);
    setupEventListeners();
}

// ---- UI Logic ----
function renderContent(topicKey) {
    const data = contentDB[topicKey];
    if (!data) return;

    let html = `
        <h2 class="module-title">${data.title}</h2>
        <p class="module-subtitle">${data.subtitle}</p>
    `;

    data.cards.forEach(card => {
        const typeClass = card.type || 'info-card';
        html += `
            <div class="info-card ${typeClass}">
                <h3 class="card-title">${card.title}</h3>
                <p class="card-content">${card.body}</p>
                ${card.code ? `<div class="code-block">${card.code}</div>` : ''}
            </div>
        `;
    });

    contentDisplay.innerHTML = html;
}

function updateActiveButton(topicKey) {
    topicBtns.forEach(btn => {
        if (btn.getAttribute('data-topic') === topicKey) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

function changeTopic(topicKey) {
    currentState.activeTopic = topicKey;
    updateActiveButton(topicKey);
    renderContent(topicKey);

    // Save state
    stateManager.saveState(CHIP_ID, currentState);
}

// ---- Event Listeners ----
function setupEventListeners() {
    // Top-bar navigation
    btnBack.addEventListener('click', () => {
        window.location.href = '/';
    });

    // Sidebar navigation
    topicBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            const topic = e.currentTarget.getAttribute('data-topic');
            changeTopic(topic);
        });
    });
}

// Boot
document.addEventListener('DOMContentLoaded', init);
