/**
 * Builder Execution Engine UI Controller
 * Manages the overlay, progress updates, and task control.
 */
class BuilderUI {
    constructor() {
        this.overlay = null;
        this.activeTaskId = null;
        this.statusInterval = null;
    }

    init() {
        this.createOverlay();
    }

    createOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'builder-overlay';
        overlay.innerHTML = `
            <div class="builder-header">
                <h2>OMNI BUILDER</h2>
                <p id="builder-task-title">Initializing Execution Sequence...</p>
                <div class="builder-status" style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                    <span id="builder-status-text">STATUS: PENDING</span>
                    <span id="builder-substep-text" style="opacity: 0.6; font-size: 0.75rem;"></span>
                </div>
            </div>
            
            <div class="builder-progress-container">
                <div class="main-progress-bar">
                    <div class="main-progress-fill" id="builder-main-progress"></div>
                    <div class="scanning-line" id="builder-scan-line"></div>
                </div>
                
                <div class="builder-steps" id="builder-steps-list">
                    <!-- Dynamic steps -->
                </div>
            </div>

            <div id="builder-mutations-container" style="margin-top: 10px; font-size: 0.7rem; max-height: 100px; overflow-y: auto; background: rgba(0,0,0,0.2); border-radius: 4px; padding: 5px; display: none;">
                <h4 style="margin: 0 0 5px 0; font-size: 0.65rem; color: var(--creator-gold);">FILE MUTATIONS</h4>
                <div id="builder-mutations-list"></div>
            </div>

            <div id="builder-preview-panel" style="display: none; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 90%; max-width: 800px; background: #0a0a0f; border: 1px solid var(--creator-gold); border-radius: 12px; padding: 20px; z-index: 6000; box-shadow: 0 0 50px rgba(0,0,0,0.8);">
                <h3 style="color: var(--creator-gold); margin-top: 0;">PATCH PREVIEW</h3>
                <div id="patch-diff-content" style="max-height: 400px; overflow-y: auto; background: #000; color: #fff; font-family: monospace; font-size: 0.8rem; padding: 10px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.1);"></div>
                <div style="margin-top: 20px; display: flex; gap: 15px; justify-content: flex-end;">
                    <button class="builder-btn" id="preview-reject-btn">REJECT PATCH</button>
                    <button class="builder-btn primary" id="preview-approve-btn">APPROVE & APPLY</button>
                </div>
            </div>

            <div class="builder-controls">
                <button class="builder-btn" id="builder-cancel-btn">CANCEL SEQUENCE</button>
                <button class="builder-btn" id="builder-skip-btn" style="display:none;">SKIP MODULE</button>
                <button class="builder-btn primary" id="builder-close-btn" style="display:none;">CLOSE CONSOLE</button>
                <button class="builder-btn" id="builder-retry-btn" style="display:none;">RETRY MODULE</button>
            </div>
        `;
        document.body.appendChild(overlay);
        this.overlay = overlay;

        document.getElementById('builder-cancel-btn').onclick = () => this.cancelExecution();
        document.getElementById('builder-skip-btn').onclick = () => this.skipModule();
        document.getElementById('builder-close-btn').onclick = () => this.hide();
        document.getElementById('builder-retry-btn').onclick = () => this.retryModule();
        document.getElementById('preview-approve-btn').onclick = () => this.decidePreview(true);
        document.getElementById('preview-reject-btn').onclick = () => this.decidePreview(false);
    }

    show(taskId) {
        this.activeTaskId = taskId;
        this.overlay.classList.add('active');
        this.startStatusPolling();
    }

    hide() {
        this.overlay.classList.remove('active');
        this.stopStatusPolling();
    }

    async startStatusPolling() {
        this.stopStatusPolling();
        this.statusInterval = setInterval(() => this.updateStatus(), 1000);
        this.updateStatus(); // Initial call
        document.getElementById('builder-scan-line').style.display = 'block';
    }

    stopStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
        document.getElementById('builder-scan-line').style.display = 'none';
    }

    async updateStatus() {
        if (!this.activeTaskId) return;

        try {
            const response = await fetch(`/api/v1/ai-host/copilot/builder/status/${this.activeTaskId}`, {
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });

            if (!response.ok) {
                console.error('Failed to fetch builder status');
                return;
            }

            const data = await response.json();
            this.renderStatus(data);

            const skipBtn = document.getElementById('builder-skip-btn');
            if (data.status === 'EXECUTING') {
                skipBtn.style.display = 'block';
            } else {
                skipBtn.style.display = 'none';
            }

            if (data.status === 'COMPLETED' || data.status === 'FAILED' || data.status === 'CANCELLED') {
                this.stopStatusPolling();
                document.getElementById('builder-close-btn').style.display = 'block';
                document.getElementById('builder-cancel-btn').style.display = 'none';

                if (data.status === 'FAILED') {
                    document.getElementById('builder-retry-btn').style.display = 'block';
                }
            }

            if (data.status === 'AWAITING_APPROVAL') {
                const currentMod = data.modules.find(m => m.id === data.current_module_id);
                if (currentMod && currentMod.result && currentMod.result.type === 'patch_preview') {
                    this.showPreview(currentMod.result.preview_id);
                }
            } else {
                document.getElementById('builder-preview-panel').style.display = 'none';
            }
        } catch (error) {
            console.error('Error updating builder status:', error);
        }
    }

    renderStatus(data) {
        document.getElementById('builder-task-title').innerText = `${data.title} - ${data.status}`;
        document.getElementById('builder-status-text').innerText = `STATUS: ${data.status}`;
        document.getElementById('builder-main-progress').style.width = `${data.progress}%`;

        if (data.current_submodule) {
            document.getElementById('builder-substep-text').innerText = `NEXT: ${data.current_submodule}`;
        } else {
            document.getElementById('builder-substep-text').innerText = '';
        }

        const stepsList = document.getElementById('builder-steps-list');
        stepsList.innerHTML = data.modules.map((mod, index) => `
            <div class="builder-step ${mod.status.toLowerCase()} ${data.current_module_id === mod.id ? 'active' : ''}">
                <div class="step-indicator">${mod.status === 'COMPLETED' ? '✓' : index + 1}</div>
                <div class="step-info">
                    <div class="step-title">${mod.title}</div>
                    <div class="step-status">${mod.status} - ${Math.round(mod.progress)}%</div>
                    ${mod.result && (mod.result.hot_reload || mod.result.verification) ? `
                        <div class="verification-card" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 8px; margin-top: 8px;">
                            <div style="font-size: 0.6rem; text-transform: uppercase; letter-spacing: 1px; color: var(--creator-gold); margin-bottom: 5px; font-weight: bold;">Auditoría de Integridad (Runtime)</div>
                            ${mod.result.hot_reload ? `
                                <div class="reload-info" style="font-size: 0.65rem; color: var(--accent); font-family: monospace;">
                                    ${mod.result.hot_reload.map(r => {
            const statusText = r.status === 'RELOADED' ? '✓ Module Reloaded' :
                r.status === 'FAILED' ? '✗ Reload Failed' :
                    r.status === 'PROTECTED' ? '🔒 Protected' : '';
            return `<div class="${r.status === 'FAILED' ? 'text-fail' : 'text-pass'}">
                                                ${statusText}: ${r.module}
                                                ${r.status === 'FAILED' ? `<span onclick="window.builderUI.retryReload('${r.module}')" style="text-decoration:underline; cursor:pointer; padding-left:5px; opacity:0.8;">(RETRY)</span>` : ''}
                                            </div>`;
        }).join('')}
                                </div>
                            ` : ''}
                            ${mod.result.verification ? `
                                <div style="font-size: 0.65rem; margin-top: 5px; opacity: 0.8;">
                                    <span style="color: var(--pizarron-safe);">✓ Verified:</span> ${mod.result.verification.message || 'No side effects detected.'}
                                </div>
                            ` : ''}
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('');

        if (data.status === 'EXECUTING') {
            this.fetchMutations(data.id);
        }
    }

    async fetchMutations(taskId) {
        try {
            const res = await fetch(`/api/v1/ai-host/copilot/builder/mutations/${taskId}`, {
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            const mutations = await res.json();
            this.renderMutations(mutations);
        } catch (e) { console.warn("Failed to fetch mutations", e); }
    }

    renderMutations(mutations) {
        const container = document.getElementById('builder-mutations-container');
        const list = document.getElementById('builder-mutations-list');
        if (!mutations || mutations.length === 0) {
            container.style.display = 'none';
            return;
        }
        container.style.display = 'block';
        list.innerHTML = mutations.map(m => {
            const files = JSON.parse(m.files_affected || '[]');
            const statusClass = m.status === 'SUCCESS' ? 'text-pass' : 'text-fail';
            return `
                <div class="mutation-item" style="margin-bottom: 4px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 2px;">
                    <span class="${statusClass}" style="font-weight:bold;">[${m.status}]</span> 
                    ${files.join(', ')}
                </div>
            `;
        }).join('');
    }

    async showPreview(previewId) {
        if (this.currentPreviewId === previewId) return;
        this.currentPreviewId = previewId;

        try {
            const res = await fetch(`/api/v1/ai-host/copilot/builder/preview/${previewId}`, {
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            const preview = await res.json();
            this.renderPreview(preview);
        } catch (e) { console.error("Failed to fetch preview", e); }
    }

    renderPreview(preview) {
        const panel = document.getElementById('builder-preview-panel');
        const content = document.getElementById('patch-diff-content');

        // --- NEW: Sync with Workspace Side Panel ---
        const wsFile = document.getElementById('ws-change-file');
        const wsPath = document.getElementById('ws-change-path');
        const wsContent = document.getElementById('ws-diff-preview-content');
        const wsActions = document.getElementById('ws-change-actions');
        const wsStatus = document.getElementById('ws-change-status');

        if (panel) panel.style.display = 'none';
        if (wsActions) wsActions.style.display = 'flex';

        if (wsStatus) {
            wsStatus.innerHTML = `STATUS: <span style="background: rgba(212, 175, 55, 0.2); color: var(--creator-gold); padding: 2px 6px; border-radius: 3px;">PROPUESTA LISTA</span>`;
        }

        // --- NEW: EVIDENCE LOOP OVERLAY ---
        const reasoningHtml = `
            <div class="evidence-block" style="margin-bottom: 15px; padding: 10px; background: rgba(255,255,255,0.03); border-left: 3px solid var(--creator-gold); border-radius: 4px;">
                <div style="font-size: 0.6rem; text-transform: uppercase; letter-spacing: 1px; color: var(--creator-gold); margin-bottom: 5px; opacity: 0.8;">DIAGNÓSTICO / AUDITORÍA</div>
                <div style="font-size: 0.85rem; line-height: 1.4;">${preview.reasoning || "Análisis operativo estándar del sistema."}</div>
                <div style="margin-top: 8px; display: flex; gap: 10px; align-items: center; opacity: 0.6; font-size: 0.65rem;">
                    <span>TRIGGER: <b>${preview.trigger || "ACTION_INTERNAL"}</b></span>
                    <span>ID: <code>${preview.id.split('-')[0]}</code></span>
                    <span>MISIÓN: <code>${preview.task_id.split('-')[0]}</code></span>
                </div>
            </div>
        `;

        const diffHtml = preview.diffs.map(d => {
            const escape = (unsafe) => unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
            const lines = d.diff_text.split('\n');
            const highlighted = lines.map(line => {
                let cls = "";
                if (line.startsWith('---') || line.startsWith('+++')) cls = "header";
                else if (line.startsWith('@@')) cls = "info";
                else if (line.startsWith('-')) cls = "removed";
                else if (line.startsWith('+')) cls = "added";

                if (cls) return `<div class="diff-line ${cls}">${escape(line)}</div>`;
                else if (line.trim()) return `<div class="diff-line">${escape(line)}</div>`;
                return `<div class="diff-line"></div>`;
            }).join('');

            // Update side panel info if this is the first diff
            if (wsFile && preview.diffs[0] === d) {
                wsFile.innerText = `FILE: ${d.path.split(/[/\\]/).pop()}`;
                wsPath.innerText = `PATH: ${d.path}`;
            }

            return `
                <div class="diff-container" style="margin-bottom: 20px;">
                    <div class="diff-line header" style="border-bottom: 1px solid rgba(212, 175, 55, 0.15); display: flex; align-items: center; justify-content: space-between;">
                        <span>File: ${escape(d.path)}</span>
                        <span style="opacity: 0.6; font-size: 0.6rem;">${escape(d.op_type || 'MODIFY')}</span>
                    </div>
                    <div style="background: rgba(0,0,0,0.2);">
                        ${highlighted}
                    </div>
                </div>
            `;
        }).join('');

        if (content) content.innerHTML = reasoningHtml + diffHtml;
        if (wsContent) wsContent.innerHTML = reasoningHtml + diffHtml;
    }

    async decidePreview(approved) {
        if (!this.currentPreviewId) return;

        const wsStatus = document.getElementById('ws-change-status');
        if (wsStatus && approved) {
            wsStatus.innerHTML = `STATUS: <span style="background: rgba(255, 255, 255, 0.2); color: #fff; padding: 2px 6px; border-radius: 3px;">APLICANDO...</span>`;
        } else if (wsStatus && !approved) {
            wsStatus.innerHTML = `STATUS: <span style="background: rgba(255, 85, 85, 0.2); color: #ff5555; padding: 2px 6px; border-radius: 3px;">RECHAZANDO...</span>`;
        }

        try {
            const res = await fetch(`/api/v1/ai-host/copilot/builder/preview/${this.currentPreviewId}/decide?approved=${approved}`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });

            let data;
            let success = false;
            let errorMessage = "Apply failed via AI Host.";

            try {
                data = await res.json();
                success = !!(data && data.status === 'success' || res.ok);
                if (data && data.detail) errorMessage = data.detail;
            } catch (e) {
                success = res.ok;
            }

            if (!success) {
                throw new Error(errorMessage);
            }

            this.currentPreviewId = null;

            // Clean UI
            const panel = document.getElementById('builder-preview-panel');
            if (panel) panel.style.display = 'none';

            const wsActions = document.getElementById('ws-change-actions');
            if (wsActions) wsActions.style.display = 'none';

            if (wsStatus) {
                if (approved) {
                    wsStatus.innerHTML = `STATUS: <span style="background: rgba(50, 255, 150, 0.2); color: #32ff96; padding: 2px 6px; border-radius: 3px;">APLICADO</span>`;
                } else {
                    wsStatus.innerHTML = `STATUS: <span style="opacity:0.5">STANDBY / DESCARTADO</span>`;
                }
            }

            const wsContent = document.getElementById('ws-diff-preview-content');
            if (wsContent) {
                if (approved) {
                    wsContent.innerHTML = `<p style="opacity: 0.3; text-align: center; margin-top: 20px;">Change applied.</p>`;
                } else {
                    wsContent.innerHTML = `<p style="opacity: 0.3; text-align: center; margin-top: 20px;">Propuesta descartada y limpiada.</p>`;
                    const wsFile = document.getElementById('ws-change-file');
                    const wsPath = document.getElementById('ws-change-path');
                    if (wsFile) wsFile.innerText = 'FILE: No changes pending';
                    if (wsPath) wsPath.innerText = 'PATH: -';
                }
            }

            // --- REFRESH EDITOR ---
            if (approved && window.creatorEditor && window.creatorEditor.currentPath) {
                window.creatorEditor.loadFile(window.creatorEditor.currentPath).then(content => {
                    const wsContentTextarea = document.getElementById('ws-editor-content');
                    if (wsContentTextarea && typeof content === "string") {
                        wsContentTextarea.value = content;
                        // Dispatch input event to refresh buttons state
                        wsContentTextarea.dispatchEvent(new Event('input'));
                    }
                });
            }

            this.updateStatus();
        } catch (e) {
            console.error("Decision failed", e);
            if (wsStatus) {
                wsStatus.innerHTML = `STATUS: <span style="background: rgba(255, 85, 85, 0.2); color: #ff5555; padding: 2px 6px; border-radius: 3px;">FALLÓ: ${e.message}</span>`;
            }
            const wsActions = document.getElementById('ws-change-actions');
            if (wsActions) wsActions.style.display = 'none';
        }
    }

    async cancelExecution() {
        if (!confirm('Are you sure you want to cancel the construction sequence?')) return;

        try {
            await fetch(`/api/v1/ai-host/copilot/builder/control/${this.activeTaskId}?action=cancel`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            this.updateStatus();
        } catch (error) {
            console.error('Failed to cancel execution:', error);
        }
    }

    async retryModule() {
        try {
            await fetch(`/api/v1/ai-host/copilot/builder/control/${this.activeTaskId}?action=retry`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
            this.startStatusPolling();
            document.getElementById('builder-retry-btn').style.display = 'none';
        } catch (error) {
            console.error('Failed to retry module:', error);
        }
    }

    async skipModule() {
        if (!confirm('Override: skip current module?')) return;
        try {
            await fetch(`/api/v1/ai-host/copilot/builder/control/${this.activeTaskId}?action=skip`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer omniweb-dev-secret-token' }
            });
        } catch (error) {
            console.error('Failed to skip module:', error);
        }
    }

    async retryReload(moduleName) {
        try {
            const res = await fetch('/api/v1/ai-host/editor/reload', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer omniweb-dev-secret-token'
                },
                body: JSON.stringify({ module_name: moduleName })
            });
            const data = await res.json();
            if (data.status === 'success') {
                alert(`Module ${moduleName} reloaded successfully.`);
                this.updateStatus();
            }
        } catch (e) {
            alert(`Failed to retry reload: ${e}`);
        }
    }
}

const builderUI = new BuilderUI();
window.builderUI = builderUI;
document.addEventListener('DOMContentLoaded', () => builderUI.init());
