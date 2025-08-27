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
        console.log('PodcastApp.init() started');
        
        // Initialize API client
        this.apiClient = new ApiClient();
        console.log('API client initialized');
        
        // Initialize audio player
        this.audioPlayer = new AudioPlayer(this.apiClient);
        console.log('Audio player initialized:', this.audioPlayer);
        
        // Initialize UI components
        this.uiComponents = new UIComponents(this.apiClient);
        console.log('UI components initialized');
        
        // Initialize feeds manager
        this.feedsManager = new FeedsManager(this.apiClient);
        console.log('Feeds manager initialized');
        
        // Set up global functions for cross-module communication
        window.log = (message, type) => this.uiComponents.log(message, type);
        window.showStatus = (message, type) => this.uiComponents.showStatus(message, type);
        window.audioPlayer = this.audioPlayer; // Make audio player globally accessible
        console.log('Global audio player set:', window.audioPlayer);
        console.log('Global audio player loadSegments method:', typeof window.audioPlayer.loadSegments);
        
        // Set up tab navigation
        this.setupTabNavigation();
        
        // Test API health
        this.testApiHealth();
        
        // Log successful initialization
        this.uiComponents.log('Frontend loaded successfully');
        console.log('PodcastApp.init() completed');
    }

    setupTabNavigation() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');
        
        console.log('Setting up tab navigation with', tabBtns.length, 'buttons');
        
        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const targetTab = btn.getAttribute('data-tab');
                console.log('Tab clicked:', targetTab);
                
                // Update active tab button
                tabBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Update active tab content
                tabContents.forEach(content => {
                    content.classList.remove('active');
                    if (content.id === `${targetTab}-tab`) {
                        content.classList.add('active');
                        console.log('Activated tab content:', content.id);
                    }
                });
                
                // Load feeds if switching to feeds tab
                if (targetTab === 'feeds') {
                    console.log('Switching to feeds tab, loading feeds...');
                    this.loadFeeds();
                }
                
                this.uiComponents.log(`Switched to ${targetTab} tab`);
            });
        });
    }

    async loadFeeds() {
        try {
            console.log('loadFeeds called');
            this.uiComponents.log('Loading podcast feeds...');
            await this.feedsManager.loadFeeds(this.currentPage, this.pageSize, this.sortBy);
        } catch (error) {
            console.error('Error in loadFeeds:', error);
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
