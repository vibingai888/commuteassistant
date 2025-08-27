/**
 * UI Components for Podcast Generator
 */

class UIComponents {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.setupEventListeners();
        this.loadApiSettings();
        this.loadChips();
    }

    setupEventListeners() {
        // API URL controls
        const modeSwitch = document.getElementById('modeSwitch');
        const advancedMode = document.getElementById('advancedMode');
        const customGroup = document.getElementById('customGroup');
        const apiUrlInput = document.getElementById('apiUrlInput');
        const saveApiUrlBtn = document.getElementById('saveApiUrlBtn');
        const mockBackend = document.getElementById('mockBackend');

        // Mock backend checkbox
        mockBackend.addEventListener('change', () => {
            localStorage.setItem('mockBackend', mockBackend.checked);
            this.log(`Mock backend ${mockBackend.checked ? 'enabled' : 'disabled'}`);
            this.toggleApiControls(mockBackend.checked);
        });

        modeSwitch.addEventListener('change', () => {
            const mode = modeSwitch.checked ? 'gcp' : 'localhost';
            this.apiClient.setApiMode(mode);
            this.updateApiUrlDisplay();
            this.log(`Switched to ${mode} API`);
        });

        advancedMode.addEventListener('change', () => {
            if (!advancedMode.checked) {
                // Reset to default mode
                const modeSwitch = document.getElementById('modeSwitch');
                const mode = modeSwitch.checked ? 'gcp' : 'localhost';
                this.apiClient.setApiMode(mode);
            }
            this.updateApiUrlDisplay();
            this.updateCustomUrlVisibility();
        });

        saveApiUrlBtn.addEventListener('click', () => {
            const url = apiUrlInput.value.trim();
            if (url) {
                this.apiClient.setApiUrl(url);
                this.updateApiUrlDisplay();
                this.log(`Saved custom API URL: ${url}`);
            }
        });

        // Form submission
        const form = document.getElementById('podcastForm');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.handleFormSubmission();
        });

        // Duration input validation
        const minutesInput = document.getElementById('minutes');
        minutesInput.addEventListener('input', () => {
            this.clampMinutesValue();
        });
    }

    loadApiSettings() {
        const savedMode = localStorage.getItem('apiMode');
        const savedAdvanced = localStorage.getItem('advancedMode');
        const savedUrl = localStorage.getItem('customApiUrl');
        const savedMockBackend = localStorage.getItem('mockBackend');

        const modeSwitch = document.getElementById('modeSwitch');
        const advancedMode = document.getElementById('advancedMode');
        const apiUrlInput = document.getElementById('apiUrlInput');
        const mockBackend = document.getElementById('mockBackend');

        if (savedAdvanced === 'true' && savedUrl) {
            advancedMode.checked = true;
            apiUrlInput.value = savedUrl;
            // Don't set display here - let updateCustomUrlVisibility handle it
        } else if (savedMode === 'gcp') {
            modeSwitch.checked = true;
        }

        if (savedMockBackend === 'true') {
            mockBackend.checked = true;
        }

        this.updateApiUrlDisplay();
        this.toggleApiControls(mockBackend.checked);
        
        // Ensure custom URL visibility is properly set after all controls are initialized
        // and after the advanced mode checkbox state is restored
        setTimeout(() => {
            console.log('Initializing custom URL visibility with:', {
                advancedModeChecked: advancedMode.checked,
                mockBackendChecked: mockBackend.checked,
                savedAdvanced: savedAdvanced
            });
            this.updateCustomUrlVisibility();
        }, 200);
    }

    updateApiUrlDisplay() {
        const apiUrlSpan = document.getElementById('apiUrl');
        apiUrlSpan.textContent = this.apiClient.getBaseUrl();
    }

    clampMinutesValue() {
        const input = document.getElementById('minutes');
        let value = parseInt(input.value) || 3;
        value = Math.max(1, Math.min(15, value));
        input.value = value;
        return value;
    }

    async loadChips() {
        try {
            const suggestions = await this.apiClient.getSuggestions();
            // Shuffle and take first 3 unique
            const shuffled = Array.from(new Set(suggestions)).sort(() => Math.random() - 0.5).slice(0, 3);
            
            const chipsDiv = document.getElementById('chips');
            chipsDiv.innerHTML = '';
            
            shuffled.forEach(text => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'chip';
                button.title = text;
                button.textContent = text;
                button.addEventListener('click', () => {
                    document.getElementById('topic').value = text;
                    this.log(`Selected topic chip: ${text}`);
                });
                chipsDiv.appendChild(button);
            });
            
            if (shuffled.length) {
                this.log(`Loaded ${Math.min(3, shuffled.length)} suggestion chips`);
            }
        } catch (e) {
            this.log(`Failed to load suggestions: ${e.message}`, 'error');
        }
    }

    async handleFormSubmission() {
        const topic = document.getElementById('topic').value;
        const minutes = this.clampMinutesValue();
        const mockBackend = document.getElementById('mockBackend').checked;
        
        if (!topic.trim()) {
            this.showStatus('Please enter a topic', 'error');
            return;
        }

        this.hideStatus();
        document.getElementById('audioPlayer').style.display = 'none';
        
        const generateBtn = document.getElementById('generateBtn');
        generateBtn.disabled = true;
        generateBtn.textContent = '🔄 Generating...';
        
        this.log(`Starting podcast generation for topic: "${topic}" (${minutes} minutes)`);
        
        if (mockBackend) {
            this.log('🎭 MOCK MODE ENABLED - Using sample audio segments instead of backend API');
            this.showStatus('🎭 Mock Mode: Loading sample audio segments...', 'loading');
            // Add visual indicator for mock mode
            document.body.classList.add('mock-mode-active');
        } else {
            this.log('🌐 Using real backend API for podcast generation');
            this.showStatus('Generating chunked script...', 'loading');
            document.body.classList.remove('mock-mode-active');
        }
        
        try {
            if (mockBackend) {
                await this.loadMockSegments(topic, minutes);
            } else {
                await this.streamGenerate(topic, minutes);
            }
        } catch (error) {
            this.log(`Error: ${error.message}`, 'error');
            this.showStatus(`Error: ${error.message}`, 'error');
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = '🎵 Generate Podcast';
        }
    }

    async streamGenerate(topic, minutes) {
        try {
            // First, generate the full podcast to store it
            this.log('🎵 Generating full podcast and storing it...');
            const fullPodcast = await this.apiClient.generateFullPodcast(topic, minutes);
            this.log(`✅ Podcast generated and stored with ID: ${fullPodcast.id}`);
            
            // Then get the chunked script for audio player
            this.log('🎵 Getting chunked script for audio player...');
            const data = await this.apiClient.generateScriptChunked(topic, minutes);
            const segments = (data.segments || []).sort((a, b) => (a.segmentId || 0) - (b.segmentId || 0));
            
            if (!segments.length) {
                throw new Error('No segments returned');
            }

            // Initialize audio player with segments
            if (window.audioPlayer) {
                await window.audioPlayer.loadSegments(segments, false); // false = normal mode
            }
            
            // Refresh the feeds to show the new podcast
            this.log('🔄 Refreshing podcast feeds to show new podcast...');
            if (window.podcastApp && window.podcastApp.feedsManager) {
                await window.podcastApp.feedsManager.loadFeeds();
            }
            
            // Show success message
            this.showStatus(`🎉 Podcast generated and stored! You can now find it in the "Discover Podcasts" tab.`, 'success');
            
        } catch (error) {
            this.log(`Error in podcast generation: ${error.message}`, 'error');
            throw error;
        }
    }

    async loadMockSegments(topic, minutes) {
        console.log('🎭 Loading mock segments for topic:', topic, 'duration:', minutes, 'minutes');
        this.log('🎭 Creating mock segment data structure...');
        
        // Create mock segments data structure
        const mockSegments = [];
        const totalSegments = 15; // We have 15 sample audio files
        
        for (let i = 1; i <= totalSegments; i++) {
            const audioUrl = `test_audio_segments/segment ${i}.wav`;
            console.log(`Creating mock segment ${i} with audio URL: ${audioUrl}`);
            
            mockSegments.push({
                segmentId: i,
                multiSpeakerMarkup: {
                    turns: [
                        {
                            speaker: 'Host',
                            text: `This is mock segment ${i} for the topic "${topic}". This is a sample audio segment that would normally be generated by the backend.`,
                            startTime: (i - 1) * 10, // Mock timing
                            endTime: i * 10
                        }
                    ]
                },
                audioData: null, // Will be loaded from file
                audioUrl: audioUrl
            });
        }
        
        console.log(`Created ${mockSegments.length} mock segments`);
        console.log('First mock segment:', mockSegments[0]);
        this.log(`🎭 Created ${mockSegments.length} mock segments with sample audio files`);
        
        // Initialize audio player with mock segments
        if (window.audioPlayer) {
            console.log('Calling audioPlayer.loadSegments with mock mode enabled');
            this.log('🎭 Loading mock segments into audio player...');
            await window.audioPlayer.loadSegments(mockSegments, true); // true = mock mode
            this.log('🎭 Mock segments loaded successfully! Audio player ready.');
        } else {
            console.error('Audio player not available!');
            this.log('❌ Error: Audio player not available', 'error');
        }
    }

    log(message, type = 'info') {
        const logsDiv = document.getElementById('logs');
        const timestamp = new Date().toLocaleTimeString();
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${type}`;
        logEntry.textContent = `[${timestamp}] ${message}`;
        
        logsDiv.appendChild(logEntry);
        logsDiv.scrollTop = logsDiv.scrollHeight;
        
        console.log(`[${type.toUpperCase()}] ${message}`);
    }

    showStatus(message, type = 'info') {
        const statusDiv = document.getElementById('status');
        statusDiv.textContent = message;
        statusDiv.className = `status ${type}`;
        statusDiv.style.display = 'block';
    }

    hideStatus() {
        const statusDiv = document.getElementById('status');
        statusDiv.style.display = 'none';
    }

    toggleApiControls(mockModeEnabled) {
        // Hide/show the toggle row (Localhost/GCP switch)
        const toggleGroup = document.getElementById('toggleGroup');
        if (toggleGroup) {
            if (mockModeEnabled) {
                toggleGroup.style.opacity = '0';
                setTimeout(() => {
                    toggleGroup.style.display = 'none';
                }, 300);
            } else {
                toggleGroup.style.display = 'flex';
                setTimeout(() => {
                    toggleGroup.style.opacity = '1';
                }, 10);
            }
        }
        
        // Hide/show the advanced mode checkbox
        const advancedGroup = document.querySelector('.advanced-group');
        if (advancedGroup) {
            if (mockModeEnabled) {
                advancedGroup.style.opacity = '0';
                setTimeout(() => {
                    advancedGroup.style.display = 'none';
                }, 300);
            } else {
                advancedGroup.style.display = 'block';
                setTimeout(() => {
                    advancedGroup.style.opacity = '1';
                }, 10);
            }
        }
        
        // Handle custom URL group - only show if advanced mode is checked AND mock mode is disabled
        this.updateCustomUrlVisibility();
        
        // Update the API URL display
        if (mockModeEnabled) {
            const apiUrlSpan = document.getElementById('apiUrl');
            if (apiUrlSpan) {
                apiUrlSpan.textContent = '🎭 Mock Mode - No API calls';
                apiUrlSpan.classList.add('mock-mode');
            }
            
            // Add a helpful message about hidden controls
            this.log('🎭 API controls hidden - Mock mode is active');
        } else {
            const apiUrlSpan = document.getElementById('apiUrl');
            if (apiUrlSpan) {
                apiUrlSpan.classList.remove('mock-mode');
                this.updateApiUrlDisplay();
            }
            
            // Log when API controls are restored
            this.log('🌐 API controls restored - Backend mode is active');
        }
    }

    updateCustomUrlVisibility() {
        const customGroup = document.getElementById('customGroup');
        const advancedMode = document.getElementById('advancedMode');
        const mockBackend = document.getElementById('mockBackend');
        
        console.log('updateCustomUrlVisibility called:', {
            customGroup: !!customGroup,
            advancedModeChecked: advancedMode?.checked,
            mockBackendChecked: mockBackend?.checked
        });
        
        if (customGroup) {
            const shouldShow = advancedMode.checked && !mockBackend.checked;
            console.log('Custom URL should show:', shouldShow);
            
            if (shouldShow) {
                console.log('Showing custom URL group');
                customGroup.style.display = 'grid';
                setTimeout(() => {
                    customGroup.style.opacity = '1';
                }, 10);
            } else {
                console.log('Hiding custom URL group');
                customGroup.style.opacity = '0';
                setTimeout(() => {
                    customGroup.style.display = 'none';
                }, 300);
            }
        } else {
            console.error('Custom group element not found!');
        }
    }
}

// Export for use in other modules
window.UIComponents = UIComponents;
