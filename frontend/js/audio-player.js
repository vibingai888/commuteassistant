/**
 * Audio Player for Podcast Generator
 */

class AudioPlayer {
    constructor(apiClient) {
        this.apiClient = apiClient;
        this.audio = document.getElementById('audio');
        this.audioPlayer = document.getElementById('audioPlayer');
        this.bufferBar = document.getElementById('bufferBar');
        this.wordsMeta = document.getElementById('wordsMeta');
        this.elapsedMeta = document.getElementById('elapsedMeta');
        
        this.segments = [];
        this.blobs = new Map();
        this.inFlight = new Map();
        this.failCounts = new Map();
        this.currentId = 1;
        this.totalListenedSec = 0;
        this.lastPlayStart = null;
        this.wordsSpokenAll = 0;
        this.pendingAutoplay = false;
        this.durationById = new Map();
        this.listenedSet = new Set();
        this.wordsPerSeg = [];
        this.totalWordsAll = 0;
        this.totalGeneratedSec = 0;

        this.setupAudioEvents();
    }

    setupAudioEvents() {
        this.audio.onloadedmetadata = () => { this.updateWordsMeta(); };
        this.audio.ontimeupdate = () => { this.updateWordsMeta(); };
        this.audio.onplay = () => {
            this.lastPlayStart = Date.now();
            // Only fetch next segment when current segment has started playing
            const nextId = this.currentId + 1;
            const next = this.segments.find(s => s.segmentId === nextId);
            if (next && !this.blobs.has(nextId) && !this.inFlight.has(nextId)) {
                this.scheduleFetch(nextId).catch(e => this.log(e.message, 'error'));
            }
        };
        this.audio.onpause = () => {
            if (this.lastPlayStart) {
                this.totalListenedSec += (Date.now() - this.lastPlayStart) / 1000;
                this.lastPlayStart = null;
            }
        };
        this.audio.onended = async () => {
            if (this.lastPlayStart) {
                this.totalListenedSec += (Date.now() - this.lastPlayStart) / 1000;
                this.lastPlayStart = null;
            }
            this.listenedSet.add(this.currentId);
            const next = this.segments.find(s => s.segmentId === this.currentId + 1);
            if (next) {
                this.currentId += 1;
                if (!this.blobs.has(next.segmentId) && !this.inFlight.has(next.segmentId)) {
                    this.scheduleFetch(next.segmentId).catch(e => this.log(e.message, 'error'));
                }
                this.playCurrent();
            } else {
                this.showStatus('Playback complete', 'success');
            }
            this.renderBufferBar();
        };
    }

    async fetchSegment(seg) {
        if (this.blobs.has(seg.segmentId)) return; // already fetched
        
        this.log(`Fetching audio for segment ${seg.segmentId}...`);
        const data = await this.apiClient.generateTTSSegment(seg.segmentId, seg.multiSpeakerMarkup.turns);
        const blob = this.apiClient.base64ToBlob(data.base64, data.mime || 'audio/wav');
        
        this.blobs.set(seg.segmentId, blob);
        
        // Compute duration by decoding metadata in background
        const tmpAudio = new Audio();
        tmpAudio.src = URL.createObjectURL(blob);
        tmpAudio.addEventListener('loadedmetadata', () => {
            this.durationById.set(seg.segmentId, tmpAudio.duration || 0);
            this.updateElapsedMeta();
            URL.revokeObjectURL(tmpAudio.src);
        }, { once: true });
        
        this.renderBufferBar();
        this.log(`Segment ${seg.segmentId} audio ready (${Math.round(blob.size / 1024)} KB)`);
        
        if (seg.segmentId === this.currentId && this.pendingAutoplay) {
            this.pendingAutoplay = false;
            this.playCurrent();
        }
    }

    async scheduleFetch(segmentId) {
        if (this.blobs.has(segmentId)) return Promise.resolve();
        if (this.inFlight.has(segmentId)) return this.inFlight.get(segmentId);
        
        const seg = this.segments.find(s => s.segmentId === segmentId);
        if (!seg) return Promise.resolve();
        
        const attempt = (this.failCounts.get(segmentId) || 0) + 1;
        this.failCounts.set(segmentId, attempt);
        
        const p = this.fetchSegment(seg).catch(err => {
            this.log(`TTS failed for segment ${segmentId}: ${err.message}`, 'error');
            this.inFlight.delete(segmentId);
            throw err;
        }).finally(() => {
            this.inFlight.delete(segmentId);
        });
        
        this.inFlight.set(segmentId, p);
        return p;
    }

    playCurrent() {
        const seg = this.segments.find(s => s.segmentId === this.currentId);
        if (!seg) {
            this.log('No segment to play', 'error');
            return;
        }
        
        const blob = this.blobs.get(seg.segmentId);
        if (!blob) {
            // Show empty slider while buffering and set pending autoplay
            this.pendingAutoplay = true;
            this.audio.removeAttribute('src');
            this.audio.load();
            this.showStatus(`Buffering segment ${seg.segmentId}... <span class="spinner"></span>`, 'loading');
            this.scheduleFetch(seg.segmentId).catch(e => this.log(e.message, 'error'));
            return;
        }
        
        this.pendingAutoplay = false;
        const url = URL.createObjectURL(blob);
        this.audio.src = url;
        this.audioPlayer.style.display = 'block';
        
        this.audio.play().then(() => {
            this.showStatus(`Playing segment ${seg.segmentId}/${this.segments.length}`, 'success');
            this.renderBufferBar();
        }).catch(e => {
            this.log(`Play error: ${e.message}`, 'error');
            this.showStatus(`Click play to continue (segment ${seg.segmentId})`, 'error');
        });
    }

    updateWordsMeta() {
        const idx = this.currentId - 1;
        if (idx < 0 || idx >= this.segments.length) return;
        
        const segTotal = this.wordsPerSeg[idx] || 0;
        const dur = this.audio.duration || 0;
        const cur = this.audio.currentTime || 0;
        const segSpoken = Math.min(segTotal, Math.floor((dur ? cur / dur : 0) * segTotal));
        
        // Compute cumulative: words of fully played previous segments + current spoken
        const prevSum = this.wordsPerSeg.slice(0, idx).reduce((a, b) => a + b, 0);
        this.wordsSpokenAll = prevSum + segSpoken;
        this.wordsMeta.textContent = `Words: ${this.wordsSpokenAll}/${this.totalWordsAll}`;
    }

    updateElapsedMeta() {
        // Show total generated duration (sum of durations for fetched segments)
        this.totalGeneratedSec = Array.from(this.durationById.values()).reduce((a, b) => a + (b || 0), 0);
        this.elapsedMeta.textContent = `Generated: ${this.formatTime(this.totalGeneratedSec)}`;
    }

    formatTime(seconds) {
        if (seconds < 0) return "00:00";
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    renderBufferBar() {
        this.bufferBar.innerHTML = '';
        this.segments.forEach(seg => {
            const el = document.createElement('div');
            let cls = 'buffer-seg ';
            const fetched = this.blobs.has(seg.segmentId);
            const inflight = this.inFlight.has(seg.segmentId);
            const isCurrent = seg.segmentId === this.currentId;
            const listened = this.listenedSet.has(seg.segmentId);
            
            if (isCurrent && !fetched && inflight) cls += 'seg-blink-yellow ';
            else if (isCurrent && fetched) cls += 'seg-blink-green ';
            else if (listened) cls += 'seg-red ';
            else if (fetched) cls += 'seg-green ';
            else if (inflight) cls += 'seg-blink-yellow ';
            else cls += 'seg-gray ';
            
            if (isCurrent) cls += 'current ';
            el.className = cls.trim();
            el.style.width = `${Math.max(6, 100 / this.segments.length - 1)}%`;
            el.title = `Segment ${seg.segmentId} (${this.wordsPerSeg[seg.segmentId - 1]} words)`;
            
            el.addEventListener('click', async () => {
                if (seg.segmentId === this.currentId && this.audio.src) return;
                this.showStatus(`Loading segment ${seg.segmentId}... <span class="spinner"></span>`, 'loading');
                this.currentId = seg.segmentId;
                this.audio.removeAttribute('src');
                this.audio.load();
                this.pendingAutoplay = true;
                await this.scheduleFetch(seg.segmentId);
                this.playCurrent();
            });
            
            this.bufferBar.appendChild(el);
        });
    }

    async loadSegments(segments) {
        this.segments = segments.sort((a, b) => (a.segmentId || 0) - (b.segmentId || 0));
        this.wordsPerSeg = this.segments.map(seg => {
            const turns = seg.multiSpeakerMarkup.turns || [];
            return turns.reduce((acc, t) => acc + (t.text || '').trim().split(/\s+/).filter(Boolean).length, 0);
        });
        this.totalWordsAll = this.wordsPerSeg.reduce((a, b) => a + b, 0);
        
        // Reset state
        this.blobs = new Map();
        this.inFlight = new Map();
        this.failCounts = new Map();
        this.currentId = 1;
        this.totalListenedSec = 0;
        this.lastPlayStart = null;
        this.wordsSpokenAll = 0;
        this.pendingAutoplay = false;
        this.durationById = new Map();
        this.listenedSet = new Set();
        
        this.renderBufferBar();
        this.updateElapsedMeta();
        
        this.log(`Received ${this.segments.length} segment definitions (total words ${this.totalWordsAll})`);
        
        // Start with first segment
        const first = this.segments[0];
        await this.scheduleFetch(first.segmentId);
        this.audioPlayer.style.display = 'block';
        this.playCurrent();
    }

    log(message, type = 'info') {
        // This will be implemented by the main app
        if (window.log) {
            window.log(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }

    showStatus(message, type = 'info') {
        // This will be implemented by the main app
        if (window.showStatus) {
            window.showStatus(message, type);
        }
    }
}

// Export for use in other modules
window.AudioPlayer = AudioPlayer;
