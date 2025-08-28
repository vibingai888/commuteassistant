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
        
        // Detect mobile device and log for optimization tracking
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        console.log('Device detection:', { isMobile, isTouchDevice, userAgent: navigator.userAgent });
        
        if (isMobile || isTouchDevice) {
            console.log('Mobile/touch device detected - applying mobile optimizations');
            this.uiComponents.log('Mobile device detected - interface optimized for touch');
        }
        
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
        
        // Set up duration slider
        this.setupDurationSlider();
        
        // Test API health
        this.testApiHealth();
        
        // Log successful initialization
        this.uiComponents.log('Frontend loaded successfully');
        if (isMobile || isTouchDevice) {
            this.uiComponents.log('Mobile optimizations applied');
        }
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

    setupDurationSlider() {
        const durationButtons = document.querySelectorAll('.duration-btn');
        const durationDisplay = document.getElementById('durationDisplay');
        const hiddenInput = document.getElementById('minutes');
        
        if (durationButtons.length > 0 && durationDisplay && hiddenInput) {
            console.log('Setting up duration buttons:', durationButtons.length, 'buttons found');
            
            // Set initial active state
            const initialValue = hiddenInput.value;
            const initialButton = document.querySelector(`[data-value="${initialValue}"]`);
            if (initialButton) {
                initialButton.classList.add('active');
                console.log('Set initial active duration button:', initialValue, 'minutes');
            }
            
            durationButtons.forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const value = e.target.getAttribute('data-value');
                    console.log('Duration button clicked:', value, 'minutes');
                    
                    // Update display and hidden input
                    durationDisplay.textContent = value;
                    hiddenInput.value = value;
                    
                    // Update active state
                    durationButtons.forEach(b => b.classList.remove('active'));
                    e.target.classList.add('active');
                    
                    // Log the duration change
                    this.uiComponents.log(`Duration changed to ${value} minutes`);
                    
                    console.log('Duration updated to:', value, 'minutes');
                });
            });
            
            console.log('Duration buttons initialized successfully');
        } else {
            console.warn('Duration elements not found:', {
                buttons: durationButtons.length,
                display: !!durationDisplay,
                input: !!hiddenInput
            });
        }
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
