/**
 * Feeds Manager for handling podcast discovery and playback
 */

class FeedsManager {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.currentPage = 1;
        this.pageSize = 10;
        this.sortBy = 'created_at';
        this.totalPages = 0;
        this.podcasts = [];
        this.likedPodcasts = new Set();
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadLikedPodcasts();
    }

    setupEventListeners() {
        // Sort by dropdown
        const sortBySelect = document.getElementById('sortBy');
        if (sortBySelect) {
            sortBySelect.addEventListener('change', (e) => {
                this.sortBy = e.target.value;
                this.currentPage = 1;
                this.loadFeeds();
                window.log(`Changed sort order to: ${this.sortBy}`);
            });
        }

        // Refresh button
        const refreshBtn = document.getElementById('refreshFeeds');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.loadFeeds();
                window.log('Refreshed podcast feeds');
            });
        }

        // Pagination buttons
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => {
                if (this.currentPage > 1) {
                    this.currentPage--;
                    this.loadFeeds();
                }
            });
        }
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => {
                if (this.currentPage < this.totalPages) {
                    this.currentPage++;
                    this.loadFeeds();
                }
            });
        }
    }

    async loadFeeds(page = 1, pageSize = 10, sortBy = 'created_at') {
        try {
            this.currentPage = page;
            this.pageSize = pageSize;
            this.sortBy = sortBy;
            
            this.showLoading(true);
            this.showError(false);
            
            window.log(`Loading feeds: page ${page}, size ${pageSize}, sort by ${sortBy}`);
            
            const response = await this.apiClient.getPodcastFeeds(page, pageSize, sortBy);
            
            if (response && response.podcasts) {
                this.podcasts = response.podcasts;
                this.totalPages = Math.ceil(response.total_count / pageSize);
                this.renderFeeds();
                this.updatePagination();
                
                window.log(`Loaded ${this.podcasts.length} podcasts (page ${page} of ${this.totalPages})`);
            } else {
                throw new Error('Invalid response format');
            }
            
        } catch (error) {
            this.showError(true, error.message);
            window.log(`Failed to load feeds: ${error.message}`, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    renderFeeds() {
        const podcastsList = document.getElementById('podcastsList');
        if (!podcastsList) return;
        
        if (this.podcasts.length === 0) {
            podcastsList.innerHTML = '<div class="no-podcasts">No podcasts found. Be the first to create one!</div>';
            return;
        }
        
        const podcastsHTML = this.podcasts.map(podcast => this.createPodcastCard(podcast)).join('');
        podcastsList.innerHTML = podcastsHTML;
        
        // Re-attach event listeners to new elements
        this.attachPodcastEventListeners();
    }

    createPodcastCard(podcast) {
        const isLiked = this.likedPodcasts.has(podcast.id);
        const likeBtnClass = isLiked ? 'like-btn liked' : 'like-btn';
        const likeBtnText = isLiked ? '❤️ Liked' : '🤍 Like';
        
        const duration = this.formatDuration(podcast.duration_seconds);
        const createdDate = new Date(podcast.created_at).toLocaleDateString();
        
        return `
            <div class="podcast-card" data-podcast-id="${podcast.id}">
                <div class="podcast-header">
                    <h3 class="podcast-title">${this.escapeHtml(podcast.topic)}</h3>
                </div>
                
                <div class="podcast-meta">
                    <span>⏱️ ${podcast.minutes} min</span>
                    <span>📅 ${createdDate}</span>
                    <span>📝 ${podcast.word_count} words</span>
                </div>
                
                <div class="podcast-stats">
                    <div class="stat">
                        <span>🎧</span>
                        <span>${podcast.plays}</span>
                    </div>
                    <div class="stat">
                        <span>❤️</span>
                        <span>${podcast.likes}</span>
                    </div>
                    <div class="stat">
                        <span>⏱️</span>
                        <span>${duration}</span>
                    </div>
                </div>
                
                <div class="podcast-actions">
                    <button class="action-btn play-btn" data-podcast-id="${podcast.id}">
                        ▶️ Play
                    </button>
                    <button class="action-btn ${likeBtnClass}" data-podcast-id="${podcast.id}">
                        ${likeBtnText}
                    </button>
                </div>
            </div>
        `;
    }

    attachPodcastEventListeners() {
        // Play buttons
        document.querySelectorAll('.play-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const podcastId = e.target.getAttribute('data-podcast-id');
                this.playPodcast(podcastId);
            });
        });
        
        // Like buttons
        document.querySelectorAll('.like-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const podcastId = e.target.getAttribute('data-podcast-id');
                this.likePodcast(podcastId, e.target);
            });
        });
    }

    async playPodcast(podcastId) {
        try {
            window.log(`Playing podcast ${podcastId}`);
            
            // Get podcast details
            const podcast = this.podcasts.find(p => p.id === podcastId);
            if (!podcast) {
                throw new Error('Podcast not found');
            }
            
            // Switch to create tab to show audio player
            const createTab = document.querySelector('[data-tab="create"]');
            if (createTab) {
                createTab.click();
            }
            
            // Create audio element and play
            const audio = new Audio(`/podcasts/audio/${podcastId}`);
            audio.controls = true;
            
            // Replace existing audio player
            const audioPlayer = document.getElementById('audioPlayer');
            const existingAudio = audioPlayer.querySelector('audio');
            if (existingAudio) {
                existingAudio.remove();
            }
            
            audioPlayer.appendChild(audio);
            audioPlayer.style.display = 'block';
            
            // Update metadata
            const wordsMeta = audioPlayer.querySelector('#wordsMeta');
            const elapsedMeta = audioPlayer.querySelector('#elapsedMeta');
            
            if (wordsMeta) wordsMeta.textContent = `Words: ${podcast.word_count}`;
            if (elapsedMeta) elapsedMeta.textContent = `Duration: ${this.formatDuration(podcast.duration_seconds)}`;
            
            // Play audio
            audio.play().catch(error => {
                window.log(`Failed to play audio: ${error.message}`, 'error');
            });
            
            window.log(`Started playing: ${podcast.topic}`);
            
        } catch (error) {
            window.log(`Failed to play podcast: ${error.message}`, 'error');
        }
    }

    async likePodcast(podcastId, likeBtn) {
        try {
            window.log(`Liking podcast ${podcastId}`);
            
            const response = await this.apiClient.likePodcast(podcastId);
            
            if (response && response.success) {
                // Update like count in UI
                const podcastCard = likeBtn.closest('.podcast-card');
                const statElement = podcastCard.querySelector('.stat:last-child span:last-child');
                if (statElement) {
                    statElement.textContent = response.new_like_count;
                }
                
                // Update button state
                likeBtn.classList.add('liked');
                likeBtn.innerHTML = '❤️ Liked';
                
                // Add to liked set
                this.likedPodcasts.add(podcastId);
                this.saveLikedPodcasts();
                
                window.log(`Podcast ${podcastId} liked successfully`);
            } else {
                throw new Error('Failed to like podcast');
            }
            
        } catch (error) {
            window.log(`Failed to like podcast: ${error.message}`, 'error');
        }
    }

    updatePagination() {
        const pagination = document.getElementById('feedsPagination');
        const pageInfo = document.getElementById('pageInfo');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');
        
        if (!pagination || this.totalPages <= 1) {
            if (pagination) pagination.style.display = 'none';
            return;
        }
        
        pagination.style.display = 'flex';
        
        if (pageInfo) {
            pageInfo.textContent = `Page ${this.currentPage} of ${this.totalPages}`;
        }
        
        if (prevBtn) {
            prevBtn.disabled = this.currentPage <= 1;
        }
        
        if (nextBtn) {
            nextBtn.disabled = this.currentPage >= this.totalPages;
        }
    }

    showLoading(show) {
        const loading = document.getElementById('feedsLoading');
        if (loading) {
            loading.style.display = show ? 'block' : 'none';
        }
    }

    showError(show, message = '') {
        const error = document.getElementById('feedsError');
        if (error) {
            if (show) {
                error.textContent = message || 'Failed to load podcasts';
                error.style.display = 'block';
            } else {
                error.style.display = 'none';
            }
        }
    }

    formatDuration(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    loadLikedPodcasts() {
        try {
            const liked = localStorage.getItem('likedPodcasts');
            if (liked) {
                this.likedPodcasts = new Set(JSON.parse(liked));
            }
        } catch (error) {
            window.log('Failed to load liked podcasts from storage', 'error');
        }
    }

    saveLikedPodcasts() {
        try {
            localStorage.setItem('likedPodcasts', JSON.stringify([...this.likedPodcasts]));
        } catch (error) {
            window.log('Failed to save liked podcasts to storage', 'error');
        }
    }
}
