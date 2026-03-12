const getApiBaseUrl = () => {
    // Robust detection for local mode vs server mode
    if (window.location.protocol === 'file:') {
        return "http://localhost:8000/api/v1/lingua";
    }

    // If hosted by FastAPI, use standard relative API path
    return window.location.origin + "/api/v1/lingua";
};

const API_BASE_URL = getApiBaseUrl();

const api = {
    async startJob(formData) {
        try {
            const response = await fetch(`${API_BASE_URL}/process/`, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to start job');
            }
            return await response.json();
        } catch (error) {
            console.error('API Error (Start):', error);
            throw error;
        }
    },

    async getJobStatus(jobId) {
        try {
            const response = await fetch(`${API_BASE_URL}/process/${jobId}`);
            if (!response.ok) throw new Error('Failed to fetch status');
            return await response.json();
        } catch (error) {
            console.error('API Error (Status):', error);
            throw error;
        }
    }
};
