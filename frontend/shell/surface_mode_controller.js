/**
 * BLOCK 01: SURFACE MODE CONTROLLER
 * Decoupled from creator.js to manage mode-based UI visibility.
 */
class SurfaceModeController {
    constructor(parentEnv) {
        this.parentEnv = parentEnv;
        this.lastMode = null;
    }

    applySurfaceRestrictions(mode) {
        if (mode === this.lastMode) return;
        this.lastMode = mode;

        console.log(`[SURFACE_CONTROLLER] Transitioning Surface for Mode: ${mode}`);

        const isPublic = (mode === 'PUBLIC');

        // 1. Mission Control & Workspace Nav Items
        const missionNav = document.querySelector('[data-view="mission"]');
        const workspaceNav = document.querySelector('[data-view="workspace"]');
        const homeNav = document.querySelector('[data-view="home"]');

        if (missionNav) missionNav.style.display = isPublic ? 'none' : 'flex';
        if (workspaceNav) workspaceNav.style.display = isPublic ? 'none' : 'flex';
        if (homeNav) homeNav.style.display = isPublic ? 'flex' : 'none';

        // 1b. Greeting & Persona Header
        const greeting = document.getElementById('greeting');
        const personaHeader = document.querySelector('.public-persona-header');
        if (greeting) greeting.style.display = isPublic ? 'none' : 'block';
        if (personaHeader) personaHeader.style.display = isPublic ? 'flex' : 'none';

        // 2. Audit Drawer (Halt physical existence if public)
        const auditDrawer = document.getElementById('audit-drawer-container');
        if (auditDrawer) auditDrawer.style.display = isPublic ? 'none' : 'block';

        // 3. Visual Annotator
        const annotator = document.getElementById('visual-annotator');
        if (annotator) annotator.style.display = 'none'; // Keep hidden unless active

        // 4. Simplified Launcher
        this.filterLauncherForPublic(isPublic);

        // 5. Cockpit Tabs
        const cockpitTabs = document.querySelector('.cockpit-tabs-container');
        if (cockpitTabs) cockpitTabs.style.display = isPublic ? 'none' : 'flex';
    }

    filterLauncherForPublic(isPublic) {
        document.querySelectorAll('.chip-launcher-item').forEach(item => {
            const chipSlug = item.dataset.chip;
            // Only allow safe, consumer-facing chips in public mode
            const safeChips = ['finanzas', 'lingua', 'idiomas']; // Add more as we productize

            if (isPublic && chipSlug && !safeChips.includes(chipSlug)) {
                item.style.display = 'none';
            } else {
                item.style.display = 'flex';
            }
        });
    }
}

// Ensure the class is available globally
window.SurfaceModeController = SurfaceModeController;
