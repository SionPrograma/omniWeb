/**
 * OmniWeb Global State Manager
 * Cada chip utiliza este sistema para autoguardado y restauración.
 */
class StateManager {
    constructor() {
        this.states = {};
    }

    saveState(chipId, data) {
        this.states[chipId] = {
            data: data,
            timestamp: Date.now()
        };
        // Persistencia local inmediata
        localStorage.setItem(`omniweb_chip_${chipId}`, JSON.stringify(this.states[chipId]));
        console.log(`Auto-saved state for ${chipId}`);
    }

    restoreState(chipId) {
        const saved = localStorage.getItem(`omniweb_chip_${chipId}`);
        if (saved) {
            this.states[chipId] = JSON.parse(saved);
            console.log(`Restored state for ${chipId}`);
            return this.states[chipId].data;
        }
        return null;
    }

    clearState(chipId) {
        delete this.states[chipId];
        localStorage.removeItem(`omniweb_chip_${chipId}`);
    }
}

export const stateManager = new StateManager();
