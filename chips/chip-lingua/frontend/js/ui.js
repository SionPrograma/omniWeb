const ui = {
    elements: {
        form: document.getElementById('translator-form'),
        urlInput: document.getElementById('youtube-url'),
        fileInput: document.getElementById('video-file'),
        dropZone: document.getElementById('drop-zone'),
        fileName: document.getElementById('file-name'),
        langSelect: document.getElementById('target-lang'),
        submitBtn: document.getElementById('submit-btn'),
        statusContainer: document.getElementById('status-container'),
        stagesList: document.getElementById('stages-list'),
        resultContainer: document.getElementById('result-container'),
        resultAudio: document.getElementById('result-audio'),
        downloadLink: document.getElementById('download-link')
    },

    updateStages(progress) {
        this.elements.statusContainer.style.display = 'block';
        this.elements.stagesList.innerHTML = '';

        progress.forEach(stage => {
            const stageEl = document.createElement('div');
            stageEl.className = `stage-item ${stage.percent === 100 ? 'completed' : stage.percent > 0 ? 'processing' : ''}`;

            stageEl.innerHTML = `
                <div class="stage-icon">
                    ${stage.percent === 100 ? '<i class="fas fa-check"></i>' : '<i class="fas fa-spinner fa-spin"></i>'}
                </div>
                <div class="stage-details">
                    <div class="stage-name">${stage.stage.replace(/_/g, ' ').toUpperCase()}</div>
                    <div class="stage-status">${stage.status} (${stage.percent}%)</div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: ${stage.percent}%"></div>
                    </div>
                </div>
            `;
            this.elements.stagesList.appendChild(stageEl);
        });
    },

    showResult(url) {
        this.elements.resultContainer.style.display = 'block';
        const fullUrl = `http://localhost:8000${url}`;
        this.elements.resultAudio.src = fullUrl;
        this.elements.downloadLink.href = fullUrl;
        this.elements.submitBtn.disabled = false;
        this.elements.submitBtn.innerHTML = '<span>Translate & Narrate</span>';
    },

    setLoading(isLoading) {
        this.elements.submitBtn.disabled = isLoading;
        if (isLoading) {
            this.elements.submitBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Initializing...';
            this.elements.resultContainer.style.display = 'none';
        }
    }
};

// Drag and Drop Logic
ui.elements.dropZone.addEventListener('click', () => ui.elements.fileInput.click());

ui.elements.dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    ui.elements.dropZone.classList.add('active');
});

ui.elements.dropZone.addEventListener('dragleave', () => {
    ui.elements.dropZone.classList.remove('active');
});

ui.elements.dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    ui.elements.dropZone.classList.remove('active');
    if (e.dataTransfer.files.length) {
        ui.elements.fileInput.files = e.dataTransfer.files;
        updateFileLabel();
    }
});

ui.elements.fileInput.addEventListener('change', updateFileLabel);

function updateFileLabel() {
    if (ui.elements.fileInput.files.length) {
        ui.elements.fileName.textContent = `Selected: ${ui.elements.fileInput.files[0].name}`;
        ui.elements.fileName.style.display = 'block';
    }
}
