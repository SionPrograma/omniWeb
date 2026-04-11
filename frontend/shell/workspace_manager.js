/**
 * OMNI WORKSPACE MANAGER
 * Block 01: Multi-Window Container Foundation
 */

class WorkspaceManager {
    constructor() {
        this.canvas = document.getElementById('omni-workspace-canvas');
        this.panes = [];
        this.zCounter = 1000;
        this.activePane = null;

        this.init();
    }

    init() {
        // Handle global click to change focus
        document.addEventListener('mousedown', (e) => {
            const pane = e.target.closest('.workspace-pane');
            if (pane) {
                this.focusPane(pane.dataset.paneId);
            }
        });
    }

    showCanvas(show = true) {
        if (this.canvas) {
            this.canvas.style.display = show ? 'block' : 'none';
        }
    }

    createPane(config = {}) {
        const paneId = `pane-${Date.now()}`;
        const title = config.title || 'Omni Pane';
        const type = config.type || 'generic';

        const pane = document.createElement('div');
        pane.className = 'workspace-pane';
        pane.dataset.paneId = paneId;
        pane.dataset.paneType = type;
        pane.style.left = config.x || '100px';
        pane.style.top = config.y || '100px';
        pane.style.width = config.w || '400px';
        pane.style.height = config.h || '300px';
        pane.style.zIndex = ++this.zCounter;

        pane.innerHTML = `
            <div class="pane-header">
                <span class="pane-title">${title}</span>
                <div class="pane-controls">
                    <button class="pane-btn min-btn">_</button>
                    <button class="pane-btn close-btn">✕</button>
                </div>
            </div>
            <div class="pane-content">
                ${config.content || '<div class="loading-indicator">Initializing Pane...</div>'}
            </div>
            <div class="pane-resizer"></div>
        `;

        this.canvas.appendChild(pane);
        this.panes.push({ id: paneId, element: pane });

        this.makeDraggable(pane);
        this.focusPane(paneId);

        // Bind closer
        pane.querySelector('.close-btn').onclick = (e) => {
            e.stopPropagation();
            this.destroyPane(paneId);
        };

        return paneId;
    }

    focusPane(paneId) {
        this.panes.forEach(p => {
            p.element.classList.remove('focused');
            if (p.id === paneId) {
                p.element.classList.add('focused');
                p.element.style.zIndex = ++this.zCounter;
                this.activePane = p;
            }
        });
    }

    destroyPane(paneId) {
        const index = this.panes.findIndex(p => p.id === paneId);
        if (index !== -1) {
            this.panes[index].element.remove();
            this.panes.splice(index, 1);
            this.saveWorkspace(); // PERSISTENCE HOOK: Save on close
        }
        if (this.panes.length === 0) {
            this.showCanvas(false);
        }
    }

    makeDraggable(pane) {
        const header = pane.querySelector('.pane-header');
        let isDragging = false;
        let startX, startY, initialLeft, initialTop;

        header.onmousedown = (e) => {
            if (e.target.closest('.pane-controls')) return;
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            initialLeft = parseInt(pane.style.left);
            initialTop = parseInt(pane.style.top);
            pane.style.transition = 'none';
            this.focusPane(pane.dataset.paneId);
        };

        window.onmousemove = (e) => {
            if (!isDragging) return;
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            pane.style.left = `${initialLeft + dx}px`;
            pane.style.top = `${initialTop + dy}px`;
        };

        window.onmouseup = () => {
            if (isDragging) {
                isDragging = false;
                pane.style.transition = '';
                this.saveWorkspace(); // PERSISTENCE HOOK: Save on drag end
            }
        };
    }

    /**
     * ADAPTIVE PANE INTEGRATION (Block 02)
     * Securely fetches and renders artifact content in a new pane.
     */
    async openArtifact(artifactId, config = {}) {
        // Check if already open to avoid clutter (Sovereign UX Choice)
        const existing = this.panes.find(p => p.artifactId === artifactId);
        if (existing) {
            this.focusPane(existing.id);
            return;
        }

        this.showCanvas(true);
        const paneId = this.createPane({
            title: config.title || 'Cargando Artefacto...',
            type: 'artifact',
            content: config.content || '<div class="loading-indicator">Sincronizando con la bóveda...</div>',
            x: config.x || `${50 + (this.panes.length * 20)}px`,
            y: config.y || `${80 + (this.panes.length * 20)}px`,
            w: config.w,
            h: config.h
        });

        // Store identity for de-duplication
        const paneObj = this.panes.find(p => p.id === paneId);
        paneObj.artifactId = artifactId;

        const paneElement = paneObj.element;
        const contentArea = paneElement.querySelector('.pane-content');
        const titleArea = paneElement.querySelector('.pane-title');

        try {
            const res = await fetch(`/api/v1/auth/artifacts/${artifactId}/content`);
            const data = await res.json();

            if (data.status === 'success') {
                const art = data.artifact;
                titleArea.innerText = art.filename;

                if (art.is_binary) {
                    contentArea.innerHTML = `<img src="data:image/png;base64,${art.content}" class="preview-image" style="width: 100%; border-radius: 8px;"/>`;
                } else {
                    const safeContent = art.content.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                    contentArea.innerHTML = `<pre class="preview-text" style="padding: 15px; font-size: 0.75rem;"><code>${safeContent}</code></pre>`;
                }
                this.saveWorkspace(); // Save once loaded
            } else {
                contentArea.innerHTML = `<div class="error-msg" style="padding: 20px;">No se pudo cargar: ${data.detail || 'Acceso denegado.'}</div>`;
            }
        } catch (e) {
            contentArea.innerHTML = '<div class="error-msg" style="padding: 20px;">Error de conexión con el núcleo.</div>';
        }
    }

    /**
     * WORKSPACE PERSISTENT STATE (Block 03)
     * Serializes current panes and saves to localStorage scoped by Space ID.
     */
    saveWorkspace() {
        if (!window.creatorEnv || !window.creatorEnv.systemState || !window.creatorEnv.systemState.space) return;
        const spaceId = window.creatorEnv.systemState.space.space_id;
        const mode = window.creatorEnv.systemState.user.mode;

        const state = {
            timestamp: Date.now(),
            mode: mode,
            panes: this.panes.map(p => ({
                artifactId: p.artifactId,
                type: p.element.dataset.paneType,
                x: p.element.style.left,
                y: p.element.style.top,
                w: p.element.style.width,
                h: p.element.style.height,
                zIndex: p.element.style.zIndex
            }))
        };

        localStorage.setItem(`omni_workspace_${spaceId}`, JSON.stringify(state));
    }

    async restoreWorkspace() {
        if (!window.creatorEnv || !window.creatorEnv.systemState || !window.creatorEnv.systemState.space) return;
        const spaceId = window.creatorEnv.systemState.space.space_id;
        const raw = localStorage.getItem(`omni_workspace_${spaceId}`);

        if (raw) {
            try {
                const state = JSON.parse(raw);
                if (state.panes && state.panes.length > 0) {
                    this.showCanvas(true);
                    for (const p of state.panes) {
                        if (p.artifactId) {
                            await this.openArtifact(p.artifactId, {
                                x: p.x,
                                y: p.y,
                                w: p.w,
                                h: p.h
                            });
                        }
                    }
                }
            } catch (e) {
                console.error("Workspace Restore Failed", e);
            }
        }
    }
}

// Export instance
window.workspaceManager = new WorkspaceManager();
