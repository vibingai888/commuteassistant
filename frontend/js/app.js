/**
 * Main Application for Podcast Generator
 */

class PodcastApp {
    constructor() {
        this.apiClient = null;
        this.audioPlayer = null;
        this.uiComponents = null;
        this.init();
    }

    init() {
        // Initialize API client
        this.apiClient = new ApiClient();
        
        // Initialize audio player
        this.audioPlayer = new AudioPlayer(this.apiClient);
        
        // Initialize UI components
        this.uiComponents = new UIComponents(this.apiClient);
        
        // Set up global functions for cross-module communication
        window.log = (message, type) => this.uiComponents.log(message, type);
        window.showStatus = (message, type) => this.uiComponents.showStatus(message, type);
        window.audioPlayer = this.audioPlayer; // Make audio player globally accessible
        
        // Test API health
        this.testApiHealth();
        
        // Log successful initialization
        this.uiComponents.log('Frontend loaded successfully');
    }

    async testApiHealth() {
        try {
            const isHealthy = await this.apiClient.healthCheck();
            if (isHealthy) {
                this.uiComponents.log('API health check passed');
            } else {
                this.uiComponents.log('API health check failed', 'error');
            }
        } catch (error) {
            this.uiComponents.log(`API health check error: ${error.message}`, 'error');
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.podcastApp = new PodcastApp();
});
