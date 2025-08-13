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

        modeSwitch.addEventListener('change', () => {
            const mode = modeSwitch.checked ? 'gcp' : 'localhost';
            this.apiClient.setApiMode(mode);
            this.updateApiUrlDisplay();
            this.log(`Switched to ${mode} API`);
        });

        advancedMode.addEventListener('change', () => {
            customGroup.style.display = advancedMode.checked ? 'grid' : 'none';
            if (!advancedMode.checked) {
                // Reset to default mode
                const modeSwitch = document.getElementById('modeSwitch');
                const mode = modeSwitch.checked ? 'gcp' : 'localhost';
                this.apiClient.setApiMode(mode);
            }
            this.updateApiUrlDisplay();
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

        const modeSwitch = document.getElementById('modeSwitch');
        const advancedMode = document.getElementById('advancedMode');
        const apiUrlInput = document.getElementById('apiUrlInput');

        if (savedAdvanced === 'true' && savedUrl) {
            advancedMode.checked = true;
            apiUrlInput.value = savedUrl;
            document.getElementById('customGroup').style.display = 'grid';
        } else if (savedMode === 'gcp') {
            modeSwitch.checked = true;
        }

        this.updateApiUrlDisplay();
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
        this.showStatus('Generating chunked script...', 'loading');
        
        try {
            await this.streamGenerate(topic, minutes);
        } catch (error) {
            this.log(`Error: ${error.message}`, 'error');
            this.showStatus(`Error: ${error.message}`, 'error');
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = '🎵 Generate Podcast';
        }
    }

    async streamGenerate(topic, minutes) {
        const data = await this.apiClient.generateScriptChunked(topic, minutes);
        const segments = (data.segments || []).sort((a, b) => (a.segmentId || 0) - (b.segmentId || 0));
        
        if (!segments.length) {
            throw new Error('No segments returned');
        }

        // Initialize audio player with segments
        if (window.audioPlayer) {
            await window.audioPlayer.loadSegments(segments);
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
}

// Export for use in other modules
window.UIComponents = UIComponents;
