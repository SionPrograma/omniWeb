document.getElementById('translator-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData();
    const url = document.getElementById('youtube-url').value;
    const lang = document.getElementById('target-lang').value;
    const file = document.getElementById('video-file').files[0];

    if (!url && !file) {
        ui.addLog("Error: No input provided (URL or File).", "error");
        alert("Please provide a YouTube URL or upload a file.");
        return;
    }

    if (url) formData.append('url', url);
    if (file) formData.append('file', file);
    formData.append('target_lang', lang);

    ui.setLoading(true);
    ui.addLog(`Starting job for ${url ? 'URL' : 'Uploaded File'}...`, 'system');

    try {
        const { job_id } = await api.startJob(formData);
        ui.addLog(`Job created: ${job_id}`, 'info');
        pollStatus(job_id);
    } catch (error) {
        ui.addLog(`Error starting job: ${error.message}`, 'error');
        alert("Error starting job: " + error.message);
        ui.setLoading(false);
    }
});

let lastStages = new Set();

async function pollStatus(jobId) {
    const interval = setInterval(async () => {
        try {
            const data = await api.getJobStatus(jobId);
            ui.updateStages(data.progress);

            // Log stage changes
            data.progress.forEach(progressItem => {
                const stageKey = `${progressItem.stage}-${progressItem.percent}`;
                if (progressItem.percent > 0 && !lastStages.has(stageKey)) {
                    lastStages.add(stageKey);
                    const statusMsg = progressItem.percent === 100
                        ? `Stage ${progressItem.stage.toUpperCase()} completed.`
                        : `Processing ${progressItem.stage.toUpperCase()}: ${progressItem.status}`;
                    ui.addLog(statusMsg, progressItem.percent === 100 ? 'success' : 'info');
                }
            });

            if (data.status === 'completed' || data.status === 'partial_success') {
                clearInterval(interval);
                ui.showResult(data.result_url, data.status, data.error);
                lastStages.clear();
            } else if (data.status === 'failed') {
                clearInterval(interval);
                ui.addLog(`Process failed: ${data.error}`, 'error');
                alert("Processing failed: " + data.error);
                ui.setLoading(false);
                lastStages.clear();
            }
        } catch (error) {
            console.error("Polling error:", error);
            ui.addLog(`Communication error: ${error.message}`, "error");
            clearInterval(interval);
            ui.setLoading(false);
            lastStages.clear();
        }
    }, 2000);
}
