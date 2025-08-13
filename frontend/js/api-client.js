/**
 * API Client for Podcast Generator
 */

class ApiClient {
    constructor() {
        this.baseUrl = this.getDefaultApiUrl();
        this.loadApiSettings();
    }

    getDefaultApiUrl() {
        // Detect if running from file:// protocol
        if (window.location.protocol === 'file:') {
            return 'http://localhost:8080';
        }
        return window.location.origin;
    }

    loadApiSettings() {
        const savedUrl = localStorage.getItem('customApiUrl');
        const savedMode = localStorage.getItem('apiMode');
        const savedAdvanced = localStorage.getItem('advancedMode');

        if (savedAdvanced === 'true' && savedUrl) {
            this.baseUrl = savedUrl;
        } else if (savedMode === 'gcp') {
            this.baseUrl = 'https://podcast-generator-api-wychcrdora-uc.a.run.app'; 
        } else {
            this.baseUrl = 'http://localhost:8080';
        }
    }

    setApiUrl(url) {
        this.baseUrl = url;
        localStorage.setItem('customApiUrl', url);
        localStorage.setItem('apiMode', 'custom');
        localStorage.setItem('advancedMode', 'true');
    }

    setApiMode(mode) {
        if (mode === 'gcp') {
            this.baseUrl = 'https://podcast-generator-api-wychcrdora-uc.a.run.app'; 
            localStorage.setItem('apiMode', 'gcp');
            localStorage.setItem('advancedMode', 'false');
        } else {
            this.baseUrl = 'http://localhost:8080';
            localStorage.setItem('apiMode', 'localhost');
            localStorage.setItem('advancedMode', 'false');
        }
    }

    getBaseUrl() {
        return this.baseUrl;
    }

    async healthCheck() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return response.ok;
        } catch (error) {
            console.error('Health check failed:', error);
            return false;
        }
    }

    async generateScriptChunked(topic, minutes) {
        const response = await fetch(`${this.baseUrl}/generate-script-chunked/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ topic, minutes })
        });

        if (!response.ok) {
            throw new Error(`Script request failed: HTTP ${response.status}`);
        }

        return await response.json();
    }

    async generateTTSSegment(segmentId, turns) {
        const response = await fetch(`${this.baseUrl}/tts-segment/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ segmentId, turns })
        });

        if (!response.ok) {
            throw new Error(`TTS failed for segment ${segmentId}: HTTP ${response.status}`);
        }

        return await response.json();
    }

    async getSuggestions() {
        try {
            const response = await fetch(`${this.baseUrl}/suggestions`);
            if (response.ok) {
                const data = await response.json();
                return data.suggestions || [];
            }
        } catch (error) {
            console.error('Failed to fetch suggestions:', error);
        }
        
        // Return default suggestions if API fails
        return [
            "AI in Healthcare",
            "Climate Change Solutions", 
            "The History of Las Vegas",
            "Space Exploration",
            "Digital Privacy",
            "Renewable Energy",
            "Mental Health Awareness",
            "Cybersecurity Trends",
            "Sustainable Living",
            "Artificial Intelligence Ethics"
        ];
    }

    base64ToBlob(base64, mimeType) {
        const byteCharacters = atob(base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        return new Blob([byteArray], { type: mimeType || 'audio/wav' });
    }
}

// Export for use in other modules
window.ApiClient = ApiClient;
