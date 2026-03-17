/**
 * Mobile Creator Workflow Orchestrator
 * Manages real-time monitoring of AI transformations and patch status.
 */
class MobileWorkflow {
    constructor() {
        this.activeTaskId = null;
        this.pollingInterval = null;
        this.layer = document.getElementById('mobile-workflow-layer');
        this.statusBadge = document.querySelector('.mw-status-badge');
        this.patchStatus = document.querySelector('.mw-patch-status');
        this.proposalInfo = document.querySelector('.mw-proposal-info');
    }

    init() {
        console.log("[MW] Mobile Workflow initialized.");
        this.startTaskMonitoring();
    }

    startTaskMonitoring() {
        // Poll for active builder tasks
        setInterval(async () => {
            if (this.activeTaskId) return; // Already tracking a task

            try {
                const res = await fetch('/api/v1/builder/active');
                const tasks = await res.json();
                if (tasks && tasks.length > 0) {
                    this.trackTask(tasks[0].task_id);
                }
            } catch (err) {
                console.warn("[MW] Could not poll active tasks.");
            }
        }, 5000);
    }

    async trackTask(taskId) {
        this.activeTaskId = taskId;
        this.showLayer(true);
        this.updateStatus('active', 'AI TRANSFORMATION ACTIVE');

        if (this.pollingInterval) clearInterval(this.pollingInterval);

        this.pollingInterval = setInterval(async () => {
            try {
                const res = await fetch(`/api/v1/builder/status/${taskId}`);
                if (!res.ok) {
                    this.stopTracking('failed', 'TASK LOST');
                    return;
                }
                const status = await res.json();

                this.updateUI(status);

                if (['completed', 'failed', 'cancelled'].includes(status.state)) {
                    this.stopTracking(status.state, status.state.toUpperCase());
                }
            } catch (err) {
                this.stopTracking('failed', 'POLLING ERROR');
            }
        }, 2000);
    }

    updateUI(status) {
        this.patchStatus.textContent = status.last_output || 'Processing...';
        this.proposalInfo.textContent = `Task: ${status.goal || 'Optimizing...'}`;

        const stateMap = {
            'executing': 'active',
            'pending': 'pending',
            'failed': 'failed',
            'completed': 'active'
        };
        this.updateStatus(stateMap[status.state] || 'pending', status.state.toUpperCase());
    }

    updateStatus(className, text) {
        if (!this.statusBadge) return;
        this.statusBadge.className = 'mw-status-badge ' + className;
        this.statusBadge.textContent = text;
    }

    showLayer(show) {
        if (!this.layer) return;
        if (show) {
            this.layer.classList.add('active');
            this.layer.style.display = 'block';
        } else {
            this.layer.classList.remove('active');
            setTimeout(() => this.layer.style.display = 'none', 300);
        }
    }

    stopTracking(finalState, finalMsg) {
        clearInterval(this.pollingInterval);
        this.pollingInterval = null;
        this.updateStatus(finalState, finalMsg);

        setTimeout(() => {
            this.showLayer(false);
            this.activeTaskId = null;
        }, 5000); // Keep visible for 5s after completion
    }

    // Public actions for buttons
    async retryTask() {
        if (!this.activeTaskId) return;
        try {
            await fetch(`/api/v1/builder/control/${this.activeTaskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'retry' })
            });
        } catch (err) {
            alert("Retry failed.");
        }
    }

    async cancelTask() {
        if (!this.activeTaskId) return;
        try {
            await fetch(`/api/v1/builder/control/${this.activeTaskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'cancel' })
            });
            this.stopTracking('failed', 'CANCELLED');
        } catch (err) {
            alert("Cancel failed.");
        }
    }

    async approveTask() {
        if (!this.activeTaskId) return;
        try {
            await fetch(`/api/v1/builder/control/${this.activeTaskId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'approve' })
            });
            this.updateStatus('active', 'APPROVED - STARTING');
        } catch (err) {
            alert("Approval failed.");
        }
    }
}

window.mobileWorkflow = new MobileWorkflow();
document.addEventListener('DOMContentLoaded', () => {
    if (window.innerWidth <= 768) {
        window.mobileWorkflow.init();
    }
});
