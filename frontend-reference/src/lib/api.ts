const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001';

class ApiClient {
    private token: string | null = null;

    setToken(token: string) {
        this.token = token;
        if (typeof window !== 'undefined') {
            localStorage.setItem('token', token);
        }
    }

    getToken() {
        if (!this.token && typeof window !== 'undefined') {
            this.token = localStorage.getItem('token');
        }
        return this.token;
    }

    clearToken() {
        this.token = null;
        if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
        }
    }

    private async request(endpoint: string, options: RequestInit = {}) {
        const token = this.getToken();
        const headers: Record<string, string> = {
            'Content-Type': 'application/json',
            ...(options.headers as Record<string, string>),
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}${endpoint}`, {
            ...options,
            headers,
            cache: 'no-store',
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Request failed' }));
            throw new Error(error.message || 'Request failed');
        }

        return response.json();
    }

    // Auth
    async login(username: string, password: string) {
        const data = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password }),
        });
        this.setToken(data.access_token);
        return data;
    }

    async register(userData: any) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    // Aircraft
    async getAircraft() {
        return this.request('/aircraft');
    }

    async getAircraftById(id: string) {
        return this.request(`/aircraft/${id}`);
    }

    async getAircraftStats() {
        return this.request('/aircraft/stats');
    }

    async createAircraft(data: any) {
        return this.request('/aircraft', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateAircraft(id: string, data: any) {
        return this.request(`/aircraft/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async deleteAircraft(id: string) {
        return this.request(`/aircraft/${id}`, {
            method: 'DELETE',
        });
    }

    // Maintenance
    async getMaintenanceLogs() {
        return this.request('/maintenance');
    }

    async getMaintenanceLogById(id: string) {
        return this.request(`/maintenance/${id}`);
    }

    async createMaintenanceLog(data: any) {
        return this.request('/maintenance', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateMaintenanceLog(id: string, data: any) {
        return this.request(`/maintenance/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    // Emergencies
    async getEmergencies() {
        return this.request('/emergencies');
    }

    async getEmergencyById(id: string) {
        return this.request(`/emergencies/${id}`);
    }

    async getActiveEmergencyCount() {
        return this.request('/emergencies/active-count');
    }

    async createEmergency(data: any) {
        return this.request('/emergencies', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateEmergencyStatus(id: string, status: string) {
        return this.request(`/emergencies/${id}/status`, {
            method: 'PATCH',
            body: JSON.stringify({ status }),
        });
    }

    async assignUserToEmergency(id: string, userId: string) {
        return this.request(`/emergencies/${id}/assign`, {
            method: 'POST',
            body: JSON.stringify({ userId }),
        });
    }

    // System Settings
    async getSystemSettings() {
        return this.request('/system-settings');
    }

    async updateSystemSettings(settings: any) {
        return this.request('/system-settings', {
            method: 'PATCH',
            body: JSON.stringify(settings),
        });
    }

    async resetSystemSettings() {
        return this.request('/system-settings/reset', {
            method: 'POST',
        });
    }

    // Documents
    async uploadDocument(formData: FormData) {
        // Note: Content-Type header is not set manually for FormData, browser sets it with boundary
        const token = this.getToken();
        const headers: Record<string, string> = {};

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}/documents/upload`, {
            method: 'POST',
            headers,
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ message: 'Upload failed' }));
            throw new Error(error.message || 'Upload failed');
        }

        return response.json();
    }

    async getDocuments() {
        return this.request('/documents');
    }

    async getDocumentTags() {
        return this.request('/documents/tags');
    }

    async deleteDocument(id: string) {
        return this.request(`/documents/${id}`, {
            method: 'DELETE',
        });
    }

    async getDocumentDownloadUrl(id: string) {
        const token = this.getToken();
        return `${API_URL}/documents/${id}/download?token=${token}`; // Assuming token can be passed via query or handled otherwise for direct links
        // Alternatively, use blob download if auth header is strictly required
    }

    async getDocumentBlobUrl(id: string): Promise<string> {
        const token = this.getToken();
        const headers: Record<string, string> = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}/documents/${id}/download`, {
            headers,
        });

        if (!response.ok) {
            throw new Error('Failed to load document');
        }

        const blob = await response.blob();
        return window.URL.createObjectURL(blob);
    }

    async downloadDocument(id: string, filename: string) {
        const token = this.getToken();
        const headers: Record<string, string> = {};
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_URL}/documents/${id}/download`, {
            headers,
        });

        if (!response.ok) {
            throw new Error('Download failed');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    // Admin
    async getAllUsers() {
        return this.request('/admin/users');
    }

    async createUser(userData: any) {
        return this.request('/admin/users', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    async updateUser(id: string, userData: any) {
        return this.request(`/admin/users/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(userData),
        });
    }

    async deleteUser(id: string) {
        return this.request(`/admin/users/${id}`, {
            method: 'DELETE',
        });
    }

    async assignUserRole(id: string, role: string) {
        return this.request(`/admin/users/${id}/role`, {
            method: 'PATCH',
            body: JSON.stringify({ role }),
        });
    }

    async getSystemStats() {
        return this.request('/admin/stats');
    }

    // Missions
    async getMissions(status?: string) {
        const query = status ? `?status=${status}` : '';
        return this.request(`/missions${query}`);
    }

    async getMissionById(id: string) {
        return this.request(`/missions/${id}`);
    }

    async createMission(data: any) {
        return this.request('/missions', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async updateMission(id: string, data: any) {
        return this.request(`/missions/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    async deleteMission(id: string) {
        return this.request(`/missions/${id}`, {
            method: 'DELETE',
        });
    }

    // Weather
    async getCurrentWeather() {
        return this.request('/weather/current');
    }

    async refreshWeather() {
        return this.request('/weather/refresh', {
            method: 'POST',
        });
    }

    async getWeatherByLocation(lat: number, lon: number) {
        return this.request(`/weather/location?lat=${lat}&lon=${lon}`);
    }

    // Pilot Dashboard
    async getPilotDashboard(forceRefresh = false) {
        const query = forceRefresh ? '?refresh=true' : '';
        return this.request(`/pilot-dashboard${query}`);
    }

    async getPilotAlerts() {
        return this.request('/pilot-dashboard/alerts');
    }

    async acknowledgeMission(missionId: string) {
        return this.request(`/pilot-dashboard/missions/${missionId}/acknowledge`, {
            method: 'PATCH',
        });
    }

    async markAlertRead(alertId: string) {
        return this.request(`/pilot-dashboard/alerts/${alertId}/read`, {
            method: 'PATCH',
        });
    }

    async getMyMissions() {
        return this.request('/missions?status=PLANNED');
    }

    // AI Chat
    async sendChatMessage(message: string): Promise<{ success: boolean; response?: string; error?: string }> {
        return this.request('/ai/chat', {
            method: 'POST',
            body: JSON.stringify({ message }),
        });
    }

    // Trainee Dashboard
    async getTraineeDashboard() {
        return this.request('/trainee/dashboard');
    }

    async getTrainingModules() {
        return this.request('/trainee/modules');
    }

    async getTrainingProgress() {
        return this.request('/trainee/progress');
    }

    async updateTrainingProgress(moduleId: string, completed: boolean, score?: number) {
        return this.request(`/trainee/progress/${moduleId}`, {
            method: 'POST',
            body: JSON.stringify({ completed, score }),
        });
    }

    // Family Dashboard
    async getFamilyDashboard() {
        return this.request('/family/dashboard');
    }

    async getWelfareResources() {
        return this.request('/family/welfare');
    }

    async getFamilyServices() {
        return this.request('/family/services');
    }

    async getFamilyAnnouncements() {
        return this.request('/family/announcements');
    }

    // Emergency Team Dashboard
    async getEmergencyDashboard() {
        return this.request('/emergency-dashboard');
    }

    async getEmergencyTimeline(emergencyId: string) {
        return this.request(`/emergency-dashboard/timeline/${emergencyId}`);
    }

    async addEmergencyTimelineEvent(emergencyId: string, event: string, description?: string) {
        return this.request(`/emergency-dashboard/timeline/${emergencyId}`, {
            method: 'POST',
            body: JSON.stringify({ event, description }),
        });
    }
}

export const api = new ApiClient();

