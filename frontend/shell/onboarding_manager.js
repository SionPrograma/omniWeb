/**
 * OMNIWEB — ONBOARDING INFRASTRUCTURE V1
 * BLOCK 03: Chip Ecosystem Tour
 */

class OnboardingManager {
    constructor() {
        this.STORAGE_KEY = 'omni_onboarding_v1';
        this.state = this.loadState();
        this.overlay = null;
        this.card = null;
        this.spotlight = null;
    }

    loadState() {
        const saved = localStorage.getItem(this.STORAGE_KEY);
        return saved ? JSON.parse(saved) : {
            firstVisit: true,
            completed: false,
            completed_b03: true,
            completed_b04: false,
            skipped: false,
            currentStep: 0,
            activeBlock: 'b04', // Block 04 is the new focus
            seenTips: [],
            tourMode: 'user'
        };
    }

    saveState() {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.state));
    }

    isCreator() {
        return document.body.classList.contains('creator-authenticated') ||
            document.body.classList.contains('admin-mode') ||
            !document.body.classList.contains('user-mode');
    }

    init() {
        console.log("[ONBOARDING] Initializing Artifact & Persistence Tour...");
        this.renderOverlay();
        this.state.tourMode = this.isCreator() ? 'creator' : 'user';

        // Chain behavior: If B03 is done but B04 isn't, start B04
        if (this.state.firstVisit && !this.state.completed_b04 && !this.state.skipped) {
            setTimeout(() => this.start(), 3500);
        }
    }

    renderOverlay() {
        if (document.getElementById('onboarding-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'onboarding-overlay';
        overlay.innerHTML = `
            <div class="onboarding-backdrop"></div>
            <div class="onboarding-spotlight" id="onboarding-spotlight"></div>
            <div class="onboarding-card" id="onboarding-card">
                <div id="onboarding-content"></div>
                <div class="onboarding-actions">
                    <button class="onboarding-btn secondary" id="onboarding-skip">SALTAR</button>
                    <div class="onboarding-nav-group">
                        <button class="onboarding-btn secondary" id="onboarding-prev" style="display:none;">ATRÁS</button>
                        <button class="onboarding-btn primary" id="onboarding-next">SIGUIENTE</button>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);

        this.overlay = overlay;
        this.card = document.getElementById('onboarding-card');
        this.spotlight = document.getElementById('onboarding-spotlight');

        document.getElementById('onboarding-skip').onclick = () => this.skip();
        document.getElementById('onboarding-next').onclick = () => this.next();
        document.getElementById('onboarding-prev').onclick = () => this.prev();
    }

    start() {
        this.overlay.classList.add('active');
        this.showStep(this.state.currentStep || 0);
    }

    async showStep(index) {
        const steps = this.getDefinitions();
        if (index >= steps.length) {
            this.finish();
            return;
        }
        if (index < 0) return;

        const step = steps[index];
        this.state.currentStep = index;
        this.saveState();

        // Run before-hook if any
        if (step.onBefore) await step.onBefore();

        const content = document.getElementById('onboarding-content');
        content.innerHTML = `
            <h4>${step.title}</h4>
            <p>${step.desc}</p>
        `;

        document.getElementById('onboarding-prev').style.display = index > 0 ? 'block' : 'none';
        document.getElementById('onboarding-next').textContent = (index === steps.length - 1) ? 'FINALIZAR' : 'SIGUIENTE';

        setTimeout(() => {
            this.applySpotlight(step.targetId);
            this.card.classList.add('visible');
        }, 300); // Wait for potential UI animations (launcher opening)
    }

    applySpotlight(targetId) {
        const target = document.getElementById(targetId) || document.querySelector(targetId);
        if (!target || target.offsetParent === null) {
            console.warn(`[ONBOARDING] Target ${targetId} not found or hidden. Using center.`);
            this.spotlight.style.opacity = '0';
            this.centerCard();
            return;
        }

        this.spotlight.style.opacity = '1';
        this.spotlight.style.display = 'block';
        const rect = target.getBoundingClientRect();
        const padding = 10;

        this.spotlight.style.width = `${rect.width + padding * 2}px`;
        this.spotlight.style.height = `${rect.height + padding * 2}px`;
        this.spotlight.style.top = `${rect.top - padding}px`;
        this.spotlight.style.left = `${rect.left - padding}px`;

        const cardWidth = this.card.offsetWidth;
        const cardHeight = this.card.offsetHeight;
        let cardTop = rect.bottom + padding + 20;
        let cardLeft = rect.left + (rect.width / 2) - (cardWidth / 2);

        if (cardLeft < 20) cardLeft = 20;
        if (cardLeft + cardWidth > window.innerWidth - 20) cardLeft = window.innerWidth - cardWidth - 20;
        if (cardTop + cardHeight > window.innerHeight - 80) {
            cardTop = rect.top - cardHeight - padding - 20;
        }
        if (cardTop < 60) cardTop = 60;

        this.card.style.top = `${cardTop}px`;
        this.card.style.left = `${cardLeft}px`;
        this.card.style.transform = 'none';
    }

    centerCard() {
        this.card.style.top = '50%';
        this.card.style.left = '50%';
        this.card.style.transform = 'translate(-50%, -50%)';
    }

    next() {
        this.showStep(this.state.currentStep + 1);
    }

    prev() {
        this.showStep(this.state.currentStep - 1);
    }

    skip() {
        this.state.skipped = true;
        this.state.firstVisit = false;
        this.saveState();
        if (window.omniShell) window.omniShell.setLauncherActive(false);
        this.close();
    }

    finish() {
        if (this.state.activeBlock === 'b04') {
            this.state.completed_b04 = true;
        } else {
            this.state.completed_b03 = true;
        }
        this.state.completed = true;
        this.state.firstVisit = false;
        this.state.currentStep = 0;
        this.saveState();
        if (window.omniShell) window.omniShell.setLauncherActive(false);
        this.close();
    }

    close() {
        this.overlay.classList.remove('active');
        this.card.classList.remove('visible');
    }

    getDefinitions() {
        const isCreator = this.isCreator();

        // BLOCK 04: ARTIFACT & PERSISTENCE
        return [
            {
                title: "TU ESPACIO PERSONAL",
                desc: isCreator ? "Aquí es donde vuestro trabajo cobra vida. Un entorno seguro y persistente para vuestras misiones." : "Este es vuestro rincón privado. Todo lo que generéis con Omni se guarda aquí automáticamente.",
                targetId: isCreator ? "[data-view='workspace']" : "[data-view='home']",
                onBefore: () => {
                    if (window.omniShell) {
                        window.omniShell.setLauncherActive(false);
                        // Trigger view switch if possible
                        const nav = document.querySelector(isCreator ? "[data-view='workspace']" : "[data-view='home']");
                        if (nav) nav.click();
                    }
                }
            },
            {
                title: "GALERÍA DE RESULTADOS",
                desc: "Cada interacción con un Chip genera un 'Artefacto'. No necesitáis guardar manualmente; Omni lo hace por vos.",
                targetId: "artifact-grid",
                onBefore: () => {
                    if (window.omniShell) window.omniShell.setLauncherActive(false);
                }
            },
            {
                title: "HISTORIAL Y PERSISTENCIA",
                desc: "Los resultados son permanentes. Podéis cerrar la sesión o cambiar de dispositivo; vuestro progreso os seguirá.",
                targetId: "home-artifact-count",
                onBefore: () => {
                    if (window.omniShell) window.omniShell.setLauncherActive(false);
                }
            },
            {
                title: "SOBERANÍA DE DATOS",
                desc: "Vuestros artefactos viven en vuestro espacio. Tenéis el control total sobre qué conservar y qué eliminar.",
                targetId: "artifact-gallery",
                onBefore: () => {
                    if (window.omniShell) window.omniShell.setLauncherActive(false);
                }
            }
        ];
    }
}

window.onboardingManager = new OnboardingManager();
