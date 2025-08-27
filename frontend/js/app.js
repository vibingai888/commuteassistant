/**
 * Main Application for Podcast Generator
 */

class PodcastApp {
    constructor() {
        this.apiClient = null;
        this.audioPlayer = null;
        this.uiComponents = null;
        this.feedsManager = null;
        this.currentPage = 1;
        this.pageSize = 10;
        this.sortBy = 'created_at';
        this.init();
    }

    init() {
        // Initialize API client
        this.apiClient = new ApiClient();
        
        // Initialize audio player
        this.audioPlayer = new AudioPlayer(this.apiClient);
        
        // Initialize UI components
        this.uiComponents = new UIComponents(this.apiClient);
        
        // Initialize feeds manager
        this.feedsManager = new FeedsManager(this.apiClient);
        
        // Set up global functions for cross-module communication
        window.log = (message, type) => this.uiComponents.log(message, type);
        window.showStatus = (message, type) => this.uiComponents.showStatus(message, type);
        window.audioPlayer = this.audioPlayer; // Make audio player globally accessible
        
        // Set up tab navigation
        this.setupTabNavigation();
        
        // Test API health
        this.testApiHealth();
        
        // Log successful initialization
        this.uiComponents.log('Frontend loaded successfully');
    }

    setupTabNavigation() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.getAttribute('data-tab');
                
                // Update active tab button
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Update active tab content
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if (content.id === `${targetTab}-tab`) {
                        content.classList.add('active');
                    }
                });
                
                // Load feeds if switching to feeds tab
                if (targetTab === 'feeds') {
                    this.loadFeeds();
                }
                
                this.uiComponents.log(`Switched to ${targetTab} tab`);
            });
        });
    }

    async loadFeeds() {
        try {
            this.uiComponents.log('Loading podcast feeds...');
            await this.feedsManager.loadFeeds(this.currentPage, this.pageSize, this.sortBy);
        } catch (error) {
            this.uiComponents.log(`Failed to load feeds: ${error.message}`, 'error');
        }
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
