/**
 * OmniWeb Shell v0.2.0
 * A lightweight, reusable UI wrapper injecting system-level identity and navigation
 * over isolated MPAs (chips) without modifying their HTML.
 */

class OmniShell {
    constructor() {
        this.init();
    }

    init() {
        // Prevent duplicate shells
        if (document.getElementById('omni-shell-root')) return;

        // Create shell container
        const shell = document.createElement('div');
        shell.id = 'omni-shell-root';

        // Load shell CSS dynamically so chips don't need manual <link> updates
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '/core/shared/styles/shell.css';
        document.head.appendChild(link);

        // Shell DOM Structure (A minimalistic floating dock at bottom center)
        shell.innerHTML = `
            <div class="omni-dock">
                <button id="omni-btn-hub" class="omni-dock-btn" title="Volver al Hub Global" aria-label="Dashboard">
                    <span class="omni-logo">🌐</span>
                    <span class="omni-text">OmniWeb</span>
                </button>
            </div>
        `;

        document.body.appendChild(shell);

        // Bind events
        document.getElementById('omni-btn-hub').addEventListener('click', () => {
            // Go back to the dashboard/hub
            window.location.href = '/';
        });
    }
}

export const omniShell = new OmniShell();
