const getApiBaseUrl = () => {
    // Stage-ready URL resolution (v2.1 Hardening)
    const chipSlug = "lingua";
    const apiPathSub = `/api/v1/${chipSlug}`;

    // If we're on localhost but not 8000 (e.g. dev server), default to 8000
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        if (window.location.port !== '8000') {
            return "http://localhost:8000" + apiPathSub;
        }
    }

    // Dynamic base path detection (Proxy-Hardened)
    // If the window path is e.g. /omniweb/lingua/index.html, we need to extract /omniweb
    const currentPath = window.location.pathname;
    const pathParts = currentPath.split('/');
    const chipIdx = pathParts.indexOf(chipSlug);

    if (chipIdx !== -1) {
        const basePath = pathParts.slice(0, chipIdx).join('/');
        // Ensure it doesn't double-slash or end in slash
        return window.location.origin + (basePath === "" || basePath === "/" ? "" : basePath) + apiPathSub;
    }

    // Default to relative resolution
    return window.location.origin + apiPathSub;
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
    },

    async getAudit() {
        try {
            const response = await fetch(`${API_BASE_URL}/process/governance/audit`);
            if (!response.ok) throw new Error('Acceso a auditoría denegado o error de red');
            return await response.json();
        } catch (error) {
            console.error('API Error (Audit):', error);
            throw error;
        }
    },

    async getArchive(jobId) {
        try {
            const response = await fetch(`${API_BASE_URL}/process/${jobId}/archive`);
            if (!response.ok) throw new Error('Error al generar exportación');
            return await response.json();
        } catch (error) {
            console.error('API Error (Archive):', error);
            throw error;
        }
    },

    async warmup() {
        try {
            const response = await fetch(`${API_BASE_URL}/process/system/warmup`, { method: 'POST' });
            return await response.json();
        } catch (error) {
            console.warn('Warmup failed, will load on demand:', error);
        }
    },

    async getForgeStats() {
        try {
            const globalBase = API_BASE_URL.replace('/lingua', '/ai-host');
            const response = await fetch(`${globalBase}/forge/comparison`);
            if (!response.ok) throw new Error('Forge accessibility error');
            return await response.json();
        } catch (error) {
            console.error('Forge API Error:', error);
            throw error;
        }
    },

    async getForgeRecommendations(lens = 'balanced') {
        try {
            const globalBase = API_BASE_URL.replace('/lingua', '/ai-host');
            const response = await fetch(`${globalBase}/forge/recommendations?lens=${lens}`);
            if (!response.ok) throw new Error('Forge Recommendations accessibility error');
            return await response.json();
        } catch (error) {
            console.error('Forge Recommendations API Error:', error);
            throw error;
        }
    },

    async createSwapRequest(data) {
        try {
            const globalBase = API_BASE_URL.replace('/lingua', '/ai-host');
            const response = await fetch(`${globalBase}/forge/requests/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            return await response.json();
        } catch (error) {
            console.error('Create Swap Request Error:', error);
            throw error;
        }
    },

    async listSwapRequests() {
        try {
            const globalBase = API_BASE_URL.replace('/lingua', '/ai-host');
            const response = await fetch(`${globalBase}/forge/requests`);
            return await response.json();
        } catch (error) {
            console.error('List Swap Requests Error:', error);
            throw error;
        }
    },

    async applySwapRequest(id) {
        try {
            const globalBase = API_BASE_URL.replace('/lingua', '/ai-host');
            const response = await fetch(`${globalBase}/forge/requests/${id}/apply`, { method: 'POST' });
            return await response.json();
        } catch (error) {
            console.error('Apply Swap Request Error:', error);
            throw error;
        }
    },

    async getSwapReplay(id) {
        try {
            const globalBase = API_BASE_URL.replace('/lingua', '/ai-host');
            const response = await fetch(`${globalBase}/forge/requests/${id}/replay`);
            return await response.json();
        } catch (error) {
            console.error('Get Swap Replay Error:', error);
            throw error;
        }
    },

    async getForgeAffinities(capability = null) {
        try {
            const globalBase = API_BASE_URL.replace('/lingua', '/ai-host');
            const url = capability ? `${globalBase}/forge/affinities?capability=${capability}` : `${globalBase}/forge/affinities`;
            const response = await fetch(url);
            return await response.json();
        } catch (error) {
            console.error('Get Forge Affinities Error:', error);
            throw error;
        }
    },

    async getForgeSynergies(chip = 'lingua') {
        try {
            const globalBase = API_BASE_URL.replace('/lingua', '/ai-host');
            const response = await fetch(`${globalBase}/forge/synergies?chip=${chip}`);
            return await response.json();
        } catch (error) {
            console.error('Get Forge Synergies Error:', error);
            throw error;
        }
    },

    async getForgeStructuralDebt(capability = null) {
        try {
            const globalBase = API_BASE_URL.replace('/lingua', '/ai-host');
            const url = capability ? `${globalBase}/forge/structural-debt?capability=${capability}` : `${globalBase}/forge/structural-debt`;
            const response = await fetch(url);
            return await response.json();
        } catch (error) {
            console.error('Get Forge Structural Debt Error:', error);
            throw error;
        }
    },

    async getForgeStrategicDrift(capability = null) {
        try {
            const globalBase = API_BASE_URL.replace('/lingua', '/ai-host');
            const url = capability ? `${globalBase}/forge/drift?capability=${capability}` : `${globalBase}/forge/drift`;
            const response = await fetch(url);
            return await response.json();
        } catch (error) {
            console.error('Get Forge Strategic Drift Error:', error);
            throw error;
        }
    },
};
