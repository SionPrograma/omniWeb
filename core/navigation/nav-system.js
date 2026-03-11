/**
 * OmniWeb Global Navigation System
 * Permite navegar entre chips, volver atrás y restaurar la última vista usada.
 */
class NavigationSystem {
    constructor() {
        this.history = [];
        this.currentChip = null;
        this.init();
    }

    init() {
        console.log("OmniWeb Navigation Initialized");
        // Restaurar última sesión si existe
        const lastSession = localStorage.getItem('omniweb_last_session');
        if (lastSession) {
            console.log("Restoring last session:", lastSession);
        }
    }

    navigateTo(chipId) {
        if (this.currentChip) {
            this.history.push(this.currentChip);
        }
        this.currentChip = chipId;
        localStorage.setItem('omniweb_last_session', chipId);
        console.log(`Navigating to ${chipId}`);
        // Logic to swap UI would go here
    }

    goBack() {
        if (this.history.length > 0) {
            this.currentChip = this.history.pop();
            console.log(`Returning to ${this.currentChip}`);
        }
    }
}

export const navigation = new NavigationSystem();
