const API_BASE_URL = window.location.origin + "/api/v1/lingua";

const api = {
    async startJob(formData) {
        try {
            const response = await fetch(`${API_BASE_URL}/process/`, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) throw new Error('Failed to start job');
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    async getJobStatus(jobId) {
        try {
            const response = await fetch(`${API_BASE_URL}/process/${jobId}`);
            if (!response.ok) throw new Error('Failed to fetch status');
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
};
