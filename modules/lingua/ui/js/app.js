document.getElementById('translator-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData();
    const url = document.getElementById('youtube-url').value;
    const lang = document.getElementById('target-lang').value;
    const file = document.getElementById('video-file').files[0];

    if (!url && !file) {
        alert("Please provide a YouTube URL or upload a file.");
        return;
    }

    if (url) formData.append('url', url);
    if (file) formData.append('file', file);
    formData.append('target_lang', lang);

    ui.setLoading(true);

    try {
        const { job_id } = await api.startJob(formData);
        pollStatus(job_id);
    } catch (error) {
        alert("Error starting job: " + error.message);
        ui.setLoading(false);
    }
});

async function pollStatus(jobId) {
    const interval = setInterval(async () => {
        try {
            const data = await api.getJobStatus(jobId);
            ui.updateStages(data.progress);

            if (data.status === 'completed') {
                clearInterval(interval);
                ui.showResult(data.result_url);
            } else if (data.status === 'failed') {
                clearInterval(interval);
                alert("Processing failed: " + data.error);
                ui.setLoading(false);
            }
        } catch (error) {
            console.error("Polling error:", error);
            clearInterval(interval);
            ui.setLoading(false);
        }
    }, 2000);
}
