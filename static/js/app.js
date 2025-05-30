// Real-time Whisper Subtitles - JavaScript Application

class RealtimeSubtitlesApp {
    constructor() {
        this.ws = null;
        this.isRecording = false;
        this.autoScroll = true;
        this.segments = [];
        
        this.initializeElements();
        this.setupEventListeners();
        this.loadAudioDevices();
        this.setupWebSocket();
        
        console.log('RealtimeSubtitlesApp initialized');
    }
    
    initializeElements() {
        // Status elements
        this.statusIndicator = document.getElementById('statusIndicator');
        this.statusText = document.getElementById('statusText');
        this.statusDot = document.getElementById('statusDot');
        
        // Control elements
        this.deviceSelect = document.getElementById('deviceSelect');
        this.modelSelect = document.getElementById('modelSelect');
        this.languageSelect = document.getElementById('languageSelect');
        this.startBtn = document.getElementById('startBtn');
        this.stopBtn = document.getElementById('stopBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.refreshDevices = document.getElementById('refreshDevices');
        
        // Subtitle elements
        this.subtitlesDisplay = document.getElementById('subtitlesDisplay');
        this.toggleScrollBtn = document.getElementById('toggleScrollBtn');
        this.fontSizeSelect = document.getElementById('fontSizeSelect');
        
        // Statistics elements
        this.totalSegments = document.getElementById('totalSegments');
        this.totalDuration = document.getElementById('totalDuration');
        this.avgConfidence = document.getElementById('avgConfidence');
        this.sessionDuration = document.getElementById('sessionDuration');
        
        // Loading and toast elements
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingText = document.getElementById('loadingText');
        this.toastContainer = document.getElementById('toastContainer');
    }
    
    setupEventListeners() {
        // Control buttons
        this.startBtn.addEventListener('click', () => this.startRecording());
        this.stopBtn.addEventListener('click', () => this.stopRecording());
        this.clearBtn.addEventListener('click', () => this.clearSubtitles());
        this.refreshDevices.addEventListener('click', () => this.loadAudioDevices());
        
        // Subtitle controls
        this.toggleScrollBtn.addEventListener('click', () => this.toggleAutoScroll());
        this.fontSizeSelect.addEventListener('change', () => this.changeFontSize());
        
        // Window events
        window.addEventListener('beforeunload', () => {
            if (this.isRecording) {
                this.stopRecording();
            }
            if (this.ws) {
                this.ws.close();
            }
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch (e.key) {
                    case 'r':
                        e.preventDefault();
                        if (!this.isRecording) this.startRecording();
                        break;
                    case 's':
                        e.preventDefault();
                        if (this.isRecording) this.stopRecording();
                        break;
                    case 'e':
                        e.preventDefault();
                        this.clearSubtitles();
                        break;
                }
            }
        });
    }
    
    setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.updateStatus('Ready', 'ready');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateStatus('Disconnected', 'error');
            
            // Attempt to reconnect after 3 seconds
            setTimeout(() => {
                if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
                    this.setupWebSocket();
                }
            }, 3000);
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.showToast('WebSocket connection error', 'error');
        };
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'transcription':
                this.addSubtitleSegment(data.segment);
                break;
            case 'status':
                this.updateStatus(data.message, data.status);
                break;
            case 'clear':
                this.clearSubtitlesDisplay();
                break;
            case 'pong':
                // Handle ping/pong for connection health
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }
    
    async loadAudioDevices() {
        try {
            this.showLoading('Loading audio devices...');
            
            const response = await fetch('/api/devices');
            if (!response.ok) throw new Error('Failed to load devices');
            
            const data = await response.json();
            this.populateDeviceSelect(data.devices);
            
            this.hideLoading();
            this.showToast('Audio devices loaded', 'success');
        } catch (error) {
            console.error('Error loading audio devices:', error);
            this.hideLoading();
            this.showToast('Failed to load audio devices', 'error');
        }
    }
    
    populateDeviceSelect(devices) {
        this.deviceSelect.innerHTML = '<option value="">Select audio device...</option>';
        
        devices.forEach(device => {
            const option = document.createElement('option');
            option.value = device.index;
            option.textContent = `${device.name} (${device.channels}ch, ${device.sample_rate}Hz)`;
            this.deviceSelect.appendChild(option);
        });
    }
    
    async startRecording() {
        try {
            const requestData = {
                model_size: this.modelSelect.value,
                language: this.languageSelect.value || null,
                device_index: this.deviceSelect.value ? parseInt(this.deviceSelect.value) : null
            };
            
            this.showLoading('Starting recording...');
            
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to start recording');
            }
            
            this.isRecording = true;
            this.updateUIForRecording(true);
            this.updateStatus('Recording...', 'recording');
            this.hideLoading();
            this.showToast('Recording started', 'success');
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.hideLoading();
            this.showToast(`Failed to start recording: ${error.message}`, 'error');
        }
    }
    
    async stopRecording() {
        try {
            this.showLoading('Stopping recording...');
            
            const response = await fetch('/api/stop', {
                method: 'POST'
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to stop recording');
            }
            
            this.isRecording = false;
            this.updateUIForRecording(false);
            this.updateStatus('Ready', 'ready');
            this.hideLoading();
            this.showToast('Recording stopped', 'success');
            
        } catch (error) {
            console.error('Error stopping recording:', error);
            this.hideLoading();
            this.showToast(`Failed to stop recording: ${error.message}`, 'error');
        }
    }
    
    async clearSubtitles() {
        if (!confirm('Are you sure you want to clear all subtitles?')) {
            return;
        }
        
        try {
            const response = await fetch('/api/clear', {
                method: 'DELETE'
            });
            
            if (!response.ok) throw new Error('Failed to clear subtitles');
            
            this.clearSubtitlesDisplay();
            this.showToast('Subtitles cleared', 'success');
            
        } catch (error) {
            console.error('Error clearing subtitles:', error);
            this.showToast('Failed to clear subtitles', 'error');
        }
    }
    
    clearSubtitlesDisplay() {
        this.segments = [];
        this.subtitlesDisplay.innerHTML = `
            <div class="no-subtitles">
                <i class="fas fa-microphone-slash"></i>
                <p>Start recording to see subtitles here...</p>
            </div>
        `;
        this.updateStatistics();
    }
    
    addSubtitleSegment(segment) {
        this.segments.push(segment);
        
        // Remove "no subtitles" message if present
        if (this.subtitlesDisplay.querySelector('.no-subtitles')) {
            this.subtitlesDisplay.innerHTML = '';
        }
        
        const segmentElement = this.createSubtitleElement(segment);
        this.subtitlesDisplay.appendChild(segmentElement);
        
        // Auto-scroll to bottom
        if (this.autoScroll) {
            this.subtitlesDisplay.scrollTop = this.subtitlesDisplay.scrollHeight;
        }
        
        // Update statistics
        this.updateStatistics();
        
        // Limit segments in display to prevent memory issues
        const maxSegments = 100;
        if (this.subtitlesDisplay.children.length > maxSegments) {
            this.subtitlesDisplay.removeChild(this.subtitlesDisplay.firstChild);
            this.segments = this.segments.slice(-maxSegments);
        }
    }
    
    createSubtitleElement(segment) {
        const element = document.createElement('div');
        element.className = 'subtitle-item';
        
        const startTime = this.formatTime(segment.start_time);
        const endTime = this.formatTime(segment.end_time);
        const confidence = Math.round(segment.confidence * 100);
        const confidenceClass = confidence >= 80 ? 'high' : confidence >= 60 ? 'medium' : 'low';
        
        element.innerHTML = `
            <div class="subtitle-meta">
                <span class="subtitle-time">${startTime} - ${endTime}</span>
                <div class="subtitle-confidence">
                    <span>${confidence}%</span>
                    <div class="confidence-bar">
                        <div class="confidence-fill ${confidenceClass}" style="width: ${confidence}%"></div>
                    </div>
                </div>
            </div>
            <div class="subtitle-text">${this.escapeHtml(segment.text)}</div>
        `;
        
        return element;
    }
    
    toggleAutoScroll() {
        this.autoScroll = !this.autoScroll;
        
        if (this.autoScroll) {
            this.toggleScrollBtn.innerHTML = '<i class="fas fa-pause"></i> Pause Auto-scroll';
            this.subtitlesDisplay.scrollTop = this.subtitlesDisplay.scrollHeight;
        } else {
            this.toggleScrollBtn.innerHTML = '<i class="fas fa-play"></i> Resume Auto-scroll';
        }
    }
    
    changeFontSize() {
        const size = this.fontSizeSelect.value;
        this.subtitlesDisplay.className = this.subtitlesDisplay.className.replace(/font-\w+/g, '');
        this.subtitlesDisplay.classList.add(`font-${size}`);
    }
    
    updateUIForRecording(recording) {
        this.startBtn.disabled = recording;
        this.stopBtn.disabled = !recording;
        this.deviceSelect.disabled = recording;
        this.modelSelect.disabled = recording;
        this.languageSelect.disabled = recording;
    }
    
    updateStatus(text, status) {
        this.statusText.textContent = text;
        this.statusDot.className = `status-dot ${status}`;
    }
    
    updateStatistics() {
        if (this.segments.length === 0) {
            this.totalSegments.textContent = '0';
            this.totalDuration.textContent = '0:00';
            this.avgConfidence.textContent = '0%';
            return;
        }
        
        const totalDuration = this.segments.reduce((sum, seg) => sum + (seg.end_time - seg.start_time), 0);
        const avgConfidence = this.segments.reduce((sum, seg) => sum + seg.confidence, 0) / this.segments.length;
        
        this.totalSegments.textContent = this.segments.length.toString();
        this.totalDuration.textContent = this.formatTime(totalDuration);
        this.avgConfidence.textContent = Math.round(avgConfidence * 100) + '%';
    }
    
    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showLoading(text = 'Loading...') {
        this.loadingText.textContent = text;
        this.loadingOverlay.classList.add('show');
    }
    
    hideLoading() {
        this.loadingOverlay.classList.remove('show');
    }
    
    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        this.toastContainer.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 5000);
        
        // Remove on click
        toast.addEventListener('click', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }
}

// Export functions for inline event handlers
async function exportSubtitles(format) {
    try {
        app.showLoading(`Exporting ${format.toUpperCase()}...`);
        
        const response = await fetch(`/api/export/${format}`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to export ${format}`);
        }
        
        // Create download link
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        
        // Get filename from response headers or use default
        const contentDisposition = response.headers.get('content-disposition');
        let filename = `subtitles.${format}`;
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="(.+)"/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        app.hideLoading();
        app.showToast(`${format.toUpperCase()} exported successfully`, 'success');
        
    } catch (error) {
        console.error(`Error exporting ${format}:`, error);
        app.hideLoading();
        app.showToast(`Failed to export ${format}: ${error.message}`, 'error');
    }
}

// Update session duration every second
function updateSessionDuration() {
    const sessionStart = Date.now();
    
    setInterval(() => {
        const elapsed = Math.floor((Date.now() - sessionStart) / 1000);
        document.getElementById('sessionDuration').textContent = app.formatTime(elapsed);
    }, 1000);
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new RealtimeSubtitlesApp();
    updateSessionDuration();
    
    // Periodic WebSocket health check
    setInterval(() => {
        if (window.app.ws && window.app.ws.readyState === WebSocket.OPEN) {
            window.app.ws.send(JSON.stringify({ type: 'ping' }));
        }
    }, 30000); // Every 30 seconds
});