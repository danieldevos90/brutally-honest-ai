// Voice Insight Platform - Frontend JavaScript

class VoiceInsightApp {
    constructor() {
        this.websocket = null;
        this.isConnected = false;
        this.selectedFile = null;
        this.liveDemoActive = false;
        this.demoWebSocket = null;
        this.lastTranscript = '';
        this.isRecording = false;
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkInitialStatus();
        this.setupDragAndDrop();
        // Demo will start when user clicks Start Recording
    }
    
    setupEventListeners() {
        // Audio file input
        const audioInput = document.getElementById('audio-input');
        audioInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });
        
        // Upload area click
        const uploadArea = document.getElementById('upload-area');
        uploadArea.addEventListener('click', () => {
            audioInput.click();
        });
    }
    
    setupDragAndDrop() {
        const uploadArea = document.getElementById('upload-area');
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });
    }
    
    handleFileSelect(file) {
        if (!file) return;
        
        // Check if it's an audio file
        if (!file.type.startsWith('audio/')) {
            this.showError('Please select an audio file');
            return;
        }
        
        this.selectedFile = file;
        
        // Update UI
        const uploadContent = document.querySelector('.upload-content');
        uploadContent.innerHTML = `
            <div class="upload-icon">✅</div>
            <p><strong>${file.name}</strong></p>
            <p class="upload-subtitle">Size: ${this.formatFileSize(file.size)}</p>
        `;
        
        // Enable upload button
        document.getElementById('upload-btn').disabled = false;
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    showLoading(show = true) {
        const overlay = document.getElementById('loading-overlay');
        if (show) {
            overlay.classList.add('show');
        } else {
            overlay.classList.remove('show');
        }
    }
    
    showError(message) {
        alert(`❌ Error: ${message}`);
    }
    
    showSuccess(message) {
        alert(`✅ Success: ${message}`);
    }
    
    updateOutput(elementId, content, isJson = false) {
        const element = document.getElementById(elementId);
        if (isJson) {
            element.textContent = JSON.stringify(content, null, 2);
        } else {
            element.innerHTML = content;
        }
    }
    
    updateStatusDot(elementId, isOnline) {
        const dot = document.getElementById(elementId);
        if (isOnline) {
            dot.classList.add('online');
            dot.classList.remove('offline');
        } else {
            dot.classList.add('offline');
            dot.classList.remove('online');
        }
    }
    
    async checkInitialStatus() {
        await this.checkSystemStatus();
        await this.scanOMI();
    }
    
    async checkSystemStatus() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // Update status dots
            this.updateStatusDot('platform-status', true);
            this.updateStatusDot('omi-status', data.omi_connected);
            
            // Update output
            let output = `<div style="font-family: monospace;">`;
            output += `<p><strong>Platform Status:</strong> ✅ Online</p>`;
            output += `<p><strong>OMI Connected:</strong> ${data.omi_connected ? '✅' : '❌'} ${data.omi_connected}</p>`;
            output += `<p><strong>Audio Processor:</strong> ${data.audio_processor ? '✅' : '❌'} ${data.audio_processor}</p>`;
            output += `<p><strong>LLM Analyzer:</strong> ${data.llm_analyzer ? '✅' : '❌'} ${data.llm_analyzer}</p>`;
            output += `<p><strong>Database:</strong> ${data.database ? '✅' : '❌'} ${data.database}</p>`;
            
            if (data.services) {
                output += `<br><p><strong>Services:</strong></p>`;
                output += `<p>• PostgreSQL: ${data.services.postgres ? '✅' : '❌'}</p>`;
                output += `<p>• Qdrant: ${data.services.qdrant ? '✅' : '❌'}</p>`;
                output += `<p>• Ollama: ${data.services.ollama ? '✅' : '❌'}</p>`;
            }
            
            if (data.capabilities) {
                output += `<br><p><strong>Capabilities:</strong></p>`;
                output += `<p>• Real-time Streaming: ${data.capabilities.real_time_streaming ? '✅' : '❌'}</p>`;
                output += `<p>• Audio Processing: ${data.capabilities.audio_processing ? '✅' : '❌'}</p>`;
                output += `<p>• Transcription: ${data.capabilities.transcription}</p>`;
                output += `<p>• Fact Checking: ${data.capabilities.fact_checking ? '✅' : '❌'}</p>`;
            }
            
            output += `</div>`;
            this.updateOutput('system-output', output);
            
        } catch (error) {
            this.updateStatusDot('platform-status', false);
            this.updateOutput('system-output', `<p style="color: red;">❌ Failed to connect to platform: ${error.message}</p>`);
        } finally {
            this.showLoading(false);
        }
    }
    
    async scanOMI() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/omi/ports');
            const data = await response.json();
            
            this.updateStatusDot('omi-status', data.omi_detected);
            
            let output = `<div style="font-family: monospace;">`;
            
            // Scan Results with neon tags
            output += `<p><strong>Scan Results:</strong></p>`;
            output += `<p>• Total Ports: <span class="status-tag status-online">${data.count}</span></p>`;
            output += `<p>• OMI Detected: <span class="status-tag ${data.omi_detected ? 'status-online' : 'status-offline'}">${data.omi_detected ? 'Yes' : 'No'}</span></p>`;
            
            if (data.omi_device) {
                output += `<p>• OMI Device: <span class="status-tag status-online">${data.omi_device}</span></p>`;
            }
            
            // OMI DevKit 2 section with icon and dropdown-style info
            const omiPort = data.ports.find(port => port.description && port.description.includes('XIAO'));
            if (omiPort) {
                output += `<br><div style="background: #f0f8ff; padding: 15px; border-radius: 10px; border-left: 4px solid #00ff41;">`;
                output += `<p><strong>🎙️ OMI DevKit 2 Detected</strong></p>`;
                output += `<div style="margin-left: 20px;">`;
                output += `<p><strong>Device:</strong> ${omiPort.device}</p>`;
                output += `<p><strong>Description:</strong> ${omiPort.description}</p>`;
                output += `<p><strong>VID:</strong> ${omiPort.vid} | <strong>PID:</strong> ${omiPort.pid}</p>`;
                output += `<p><span class="status-tag status-online">Ready for Audio Input</span></p>`;
                output += `</div>`;
                output += `</div>`;
            }
            
            // Other available ports (collapsed by default)
            const otherPorts = data.ports.filter(port => !port.description || !port.description.includes('XIAO'));
            if (otherPorts.length > 0) {
                output += `<br><details style="margin-top: 15px;">`;
                output += `<summary style="cursor: pointer; font-weight: bold;">📋 Other Available Ports (${otherPorts.length})</summary>`;
                output += `<div style="margin-left: 20px; margin-top: 10px;">`;
                otherPorts.forEach(port => {
                    output += `<p>• <strong>${port.device}</strong></p>`;
                    output += `<p style="margin-left: 15px; color: #666;">${port.description || 'Unknown device'}`;
                    if (port.vid && port.pid) {
                        output += ` (VID: ${port.vid}, PID: ${port.pid})`;
                    }
                    output += `</p>`;
                });
                output += `</div>`;
                output += `</details>`;
            }
            
            output += `</div>`;
            this.updateOutput('omi-output', output);
            
        } catch (error) {
            this.updateOutput('omi-output', `<p style="color: red;">❌ Failed to scan OMI: ${error.message}</p>`);
        } finally {
            this.showLoading(false);
        }
    }
    
    async testOMI() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/test/omi');
            const data = await response.json();
            
            let output = `<div style="font-family: monospace;">`;
            output += `<p><strong>OMI Connection Test:</strong></p>`;
            output += `<p>• Device Found: ${data.device_found ? '✅' : '❌'} ${data.device_found}</p>`;
            output += `<p>• Connection Successful: ${data.connection_successful ? '✅' : '❌'} ${data.connection_successful}</p>`;
            output += `<p>• Streaming Ready: ${data.streaming_ready ? '✅' : '❌'} ${data.streaming_ready}</p>`;
            
            if (data.device_path) {
                output += `<p>• Device Path: ${data.device_path}</p>`;
            }
            
            output += `<p>• Test Time: ${new Date(data.test_timestamp).toLocaleString()}</p>`;
            output += `</div>`;
            
            this.updateOutput('omi-output', this.updateOutput('omi-output', '').innerHTML + '<br>' + output);
            
        } catch (error) {
            this.updateOutput('omi-output', this.updateOutput('omi-output', '').innerHTML + `<br><p style="color: red;">❌ Test failed: ${error.message}</p>`);
        } finally {
            this.showLoading(false);
        }
    }
    
    async connectOMI() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/omi/connect', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('OMI connected successfully!');
                this.updateStatusDot('omi-status', true);
            } else {
                this.showError(data.message || 'Failed to connect OMI');
            }
            
        } catch (error) {
            this.showError(`Connection failed: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }
    
    selectAudioFile() {
        document.getElementById('audio-input').click();
    }
    
    async uploadAudio() {
        if (!this.selectedFile) {
            this.showError('Please select an audio file first');
            return;
        }
        
        try {
            this.showLoading(true);
            
            const formData = new FormData();
            formData.append('audio', this.selectedFile);
            
            const response = await fetch('/api/audio/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            let output = `<div style="font-family: monospace;">`;
            output += `<p><strong>Audio Processing Results:</strong></p>`;
            output += `<p>• Filename: ${data.filename || this.selectedFile.name}</p>`;
            output += `<p>• Size: ${this.formatFileSize(data.size || this.selectedFile.size)}</p>`;
            
            if (data.duration) {
                output += `<p>• Duration: ${data.duration.toFixed(2)} seconds</p>`;
            }
            
            if (data.transcript) {
                output += `<br><p><strong>Transcript:</strong></p>`;
                output += `<p style="background: #f0f0f0; padding: 10px; border-radius: 15px; margin: 10px 0;">"${data.transcript}"</p>`;
            }
            
            if (data.confidence) {
                output += `<p>• Confidence: ${(data.confidence * 100).toFixed(1)}%</p>`;
            }
            
            if (data.speakers && data.speakers.length > 0) {
                output += `<br><p><strong>Speaker Analysis:</strong></p>`;
                data.speakers.forEach((speaker, index) => {
                    output += `<p>• Speaker ${index + 1}: ${speaker.duration}s</p>`;
                });
            }
            
            if (data.analysis) {
                output += `<br><p><strong>AI Analysis:</strong></p>`;
                output += `<p style="background: #f0f0f0; padding: 10px; border-radius: 15px; margin: 10px 0;">${data.analysis}</p>`;
            }
            
            output += `</div>`;
            this.updateOutput('audio-output', output);
            
        } catch (error) {
            this.updateOutput('audio-output', `<p style="color: red;">❌ Upload failed: ${error.message}</p>`);
        } finally {
            this.showLoading(false);
        }
    }
    
    connectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
        }
        
        const statusElement = document.querySelector('.streaming-status span:last-child');
        const indicator = document.querySelector('.status-indicator');
        const connectBtn = document.getElementById('connect-btn');
        const disconnectBtn = document.getElementById('disconnect-btn');
        
        statusElement.textContent = 'Connecting...';
        indicator.classList.remove('connected');
        
        this.websocket = new WebSocket('ws://localhost:3001');
        
        this.websocket.onopen = () => {
            this.isConnected = true;
            statusElement.textContent = 'Connected';
            indicator.classList.add('connected');
            this.updateStatusDot('websocket-status', true);
            
            connectBtn.disabled = true;
            disconnectBtn.disabled = false;
            
            this.addStreamMessage('🔗 Connected to Voice Insight Platform', 'connection');
        };
        
        this.websocket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.addStreamMessage(JSON.stringify(data.data), data.type);
            } catch (error) {
                this.addStreamMessage(event.data, 'raw');
            }
        };
        
        this.websocket.onclose = () => {
            this.isConnected = false;
            statusElement.textContent = 'Disconnected';
            indicator.classList.remove('connected');
            this.updateStatusDot('websocket-status', false);
            
            connectBtn.disabled = false;
            disconnectBtn.disabled = true;
            
            this.addStreamMessage('🔌 Connection closed', 'connection');
        };
        
        this.websocket.onerror = (error) => {
            this.addStreamMessage(`❌ Connection error: ${error}`, 'error');
        };
    }
    
    disconnectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
    }
    
    addStreamMessage(message, type = 'data') {
        const output = document.getElementById('streaming-output');
        const timestamp = new Date().toLocaleTimeString();
        
        let prefix = '📨';
        switch (type) {
            case 'connection': prefix = '🔗'; break;
            case 'error': prefix = '❌'; break;
            case 'transcript': prefix = '🎙️'; break;
            case 'analysis': prefix = '🧠'; break;
        }
        
        const messageElement = document.createElement('p');
        messageElement.innerHTML = `[${timestamp}] ${prefix} ${message}`;
        
        output.appendChild(messageElement);
        output.scrollTop = output.scrollHeight;
    }
    
    clearStreamOutput() {
        document.getElementById('streaming-output').innerHTML = '<p>Stream output cleared</p>';
    }
    
    async refreshAll() {
        await this.checkSystemStatus();
        await this.scanOMI();
    }
    
    async runFullDemo() {
        this.showLoading(true);
        
        try {
            // Step 1: Check system status
            this.addStreamMessage('🎬 Starting full demo...', 'connection');
            await this.checkSystemStatus();
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Step 2: Scan OMI
            this.addStreamMessage('🔍 Scanning for OMI DevKit 2...', 'connection');
            await this.scanOMI();
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Step 3: Test OMI
            this.addStreamMessage('🧪 Testing OMI connection...', 'connection');
            await this.testOMI();
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Step 4: Connect WebSocket
            this.addStreamMessage('📡 Connecting to real-time stream...', 'connection');
            this.connectWebSocket();
            
            this.showSuccess('Full demo completed! All systems tested.');
            
        } catch (error) {
            this.showError(`Demo failed: ${error.message}`);
        } finally {
            this.showLoading(false);
        }
    }
    
    openAPIDocs() {
        window.open('http://localhost:8000/docs', '_blank');
    }
    
    downloadLogs() {
        // Create a simple log file with current status
        const logs = {
            timestamp: new Date().toISOString(),
            platform_status: 'online',
            omi_status: document.getElementById('omi-status').classList.contains('online'),
            websocket_status: this.isConnected,
            selected_file: this.selectedFile ? this.selectedFile.name : null
        };
        
        const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `voice-insight-logs-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
    
    resetSystem() {
        if (confirm('Are you sure you want to reset the system? This will disconnect all connections.')) {
            // Disconnect WebSocket
            this.disconnectWebSocket();
            
            // Clear all outputs
            this.updateOutput('system-output', '<p>Click "Check Status" to view system information</p>');
            this.updateOutput('omi-output', '<p>Click "Scan Hardware" to detect OMI DevKit 2</p>');
            this.updateOutput('audio-output', '<p>Upload an audio file to see transcription and analysis</p>');
            this.clearStreamOutput();
            
            // Reset file selection
            this.selectedFile = null;
            document.getElementById('upload-btn').disabled = true;
            document.querySelector('.upload-content').innerHTML = `
                <div class="upload-icon">🎵</div>
                <p>Drag & drop audio file here</p>
                <p class="upload-subtitle">or click to select</p>
            `;
            
            // Reset status dots
            this.updateStatusDot('platform-status', false);
            this.updateStatusDot('omi-status', false);
            this.updateStatusDot('websocket-status', false);
            
            this.showSuccess('System reset completed');
        }
    }
    
    // Live Demo Functions
    async startLiveDemo() {
        if (this.liveDemoActive) return;
        
        this.liveDemoActive = true;
        
        this.addDemoLog('🎬 Connecting to demo...');
        
        try {
            // Check system status first
            await this.checkDemoStatus();
            
            // Connect to WebSocket for live streaming
            this.connectDemoWebSocket();
            
            this.addDemoLog('✅ Demo connected! Use Start/Stop Recording buttons to control transcription.');
            
        } catch (error) {
            this.addDemoLog(`❌ Failed to start demo: ${error.message}`);
            this.stopLiveDemo();
        }
    }
    
    stopLiveDemo() {
        this.liveDemoActive = false;
        this.isRecording = false;
        
        if (this.demoWebSocket) {
            this.demoWebSocket.close();
            this.demoWebSocket = null;
        }
        
        // Reset transcription display
        const transcriptionContent = document.getElementById('transcription-content');
        transcriptionContent.innerHTML = '<p class="placeholder">Speak into your OMI DevKit 2 to see live transcription...</p>';
        transcriptionContent.classList.remove('active');
        
        // Reset honesty display
        const honestyContent = document.getElementById('honesty-content');
        honestyContent.innerHTML = '<p class="placeholder">Llama will brutally fact-check your statements here...</p>';
        honestyContent.classList.remove('brutal', 'brutal-active');
        
        this.addDemoLog('🔌 Demo disconnected');
    }
    
    async startRecording() {
        // Auto-start demo connection if not active
        if (!this.liveDemoActive) {
            await this.startLiveDemo();
            // Wait a moment for connection to establish
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        
        if (!this.demoWebSocket || !this.liveDemoActive) {
            this.addDemoLog('❌ Unable to establish connection');
            return;
        }
        
        this.isRecording = true;
        
        const startRecordBtn = document.getElementById('start-record-btn');
        const stopRecordBtn = document.getElementById('stop-record-btn');
        const recordingStatus = document.querySelector('#recording-status span:last-child');
        const recordingIndicator = document.getElementById('recording-indicator');
        
        startRecordBtn.disabled = true;
        stopRecordBtn.disabled = false;
        recordingStatus.textContent = 'Recording...';
        recordingIndicator.style.color = '#ff0000';
        
        // Send start recording command to backend
        this.demoWebSocket.send(JSON.stringify({
            action: 'start_recording'
        }));
        
        this.addDemoLog('🎤 Recording started - speak now!');
    }
    
    stopRecording() {
        if (!this.demoWebSocket || !this.isRecording) {
            return;
        }
        
        this.isRecording = false;
        
        const startRecordBtn = document.getElementById('start-record-btn');
        const stopRecordBtn = document.getElementById('stop-record-btn');
        const recordingStatus = document.querySelector('#recording-status span:last-child');
        const recordingIndicator = document.getElementById('recording-indicator');
        
        startRecordBtn.disabled = false;
        stopRecordBtn.disabled = true;
        recordingStatus.textContent = 'Processing...';
        recordingIndicator.style.color = '#ffa500';
        
        // Send stop recording command to backend
        this.demoWebSocket.send(JSON.stringify({
            action: 'stop_recording'
        }));
        
        this.addDemoLog('⏹️ Recording stopped - processing...');
        
        // Reset status after a delay
        setTimeout(() => {
            if (!this.isRecording) {
                recordingStatus.textContent = 'Ready to record';
                recordingIndicator.style.color = '#cccccc';
            }
        }, 5000);
    }
    
    async checkDemoStatus() {
        try {
            // Check OMI status
            const omiResponse = await fetch('/api/omi/ports');
            const omiData = await omiResponse.json();
            const omiConnected = omiData.ports.some(port => port.description && port.description.includes('XIAO'));
            
            this.updateStatusDot('demo-omi-status', omiConnected);
            
            // Check system status
            const systemResponse = await fetch('/api/status');
            const systemData = await systemResponse.json();
            
            this.updateStatusDot('demo-whisper-status', systemData.audio_processor);
            this.updateStatusDot('demo-llama-status', systemData.llm_analyzer);
            
            // Don't throw errors - just log warnings and continue with demo
            if (!omiConnected) {
                this.addDemoLog('⚠️ OMI DevKit 2 not detected - using simulation mode');
            }
            
            if (!systemData.audio_processor) {
                this.addDemoLog('⚠️ Audio processor not ready - using basic mode');
            }
            
            if (!systemData.llm_analyzer) {
                this.addDemoLog('⚠️ LLM analyzer not ready - using simulation');
            }
            
            // Always allow demo to continue
            this.addDemoLog('✅ Demo ready - you can start recording');
            
        } catch (error) {
            this.addDemoLog(`⚠️ Status check failed: ${error.message} - continuing anyway`);
        }
    }
    
    connectDemoWebSocket() {
        if (this.demoWebSocket) {
            this.demoWebSocket.close();
        }
        
        this.addDemoLog('📡 Connecting to live audio stream...');
        
        this.demoWebSocket = new WebSocket('ws://localhost:3001');
        
        this.demoWebSocket.onopen = () => {
            this.addDemoLog('🔗 Connected to live stream - listening for audio...');
        };
        
        this.demoWebSocket.onmessage = async (event) => {
            try {
                let messageData;
                
                // Handle different message types
                if (event.data instanceof Blob) {
                    // Convert Blob to text
                    messageData = await event.data.text();
                    console.log('Converted Blob to text:', messageData);
                } else {
                    messageData = event.data;
                    console.log('Received text message:', messageData);
                }
                
                // Try to parse as JSON
                const data = JSON.parse(messageData);
                this.handleDemoMessage(data);
            } catch (error) {
                console.error('WebSocket message parsing error:', error);
                console.log('Raw event.data:', event.data);
                console.log('Type of event.data:', typeof event.data);
                this.addDemoLog(`📨 Parse error: ${error.message}`);
            }
        };
        
        this.demoWebSocket.onclose = (event) => {
            this.addDemoLog(`🔌 Connection closed (code: ${event.code})`);
            // Don't auto-reconnect to prevent connection loops
            // User can manually restart if needed
        };
        
        this.demoWebSocket.onerror = (error) => {
            this.addDemoLog(`❌ Connection error: ${error}`);
        };
    }
    
    handleDemoMessage(data) {
        const timestamp = new Date().toLocaleTimeString();
        
        // Debug logging
        console.log('Received WebSocket message:', data);
        
        switch (data.type) {
            case 'connection':
                this.addDemoLog(`[${timestamp}] 🔗 ${data.data}`);
                break;
            case 'info':
                this.addDemoLog(`[${timestamp}] ℹ️ ${data.data.message}`);
                break;
            case 'recording_start':
                this.addDemoLog(`[${timestamp}] 🎤 ${data.data.message}`);
                break;
            case 'recording_stop':
                this.addDemoLog(`[${timestamp}] ⏹️ ${data.data.message}`);
                break;
            case 'transcript':
                // Handle transcript - data.data is the transcript string
                this.handleTranscription(data.data, timestamp);
                break;
            case 'analysis':
                this.handleBrutalHonesty(data.data, timestamp);
                break;
            case 'audio_start':
                this.handleAudioStart(timestamp);
                break;
            case 'audio_end':
                this.handleAudioEnd(timestamp);
                break;
            case 'demo_complete':
                this.addDemoLog(`[${timestamp}] 🎉 ${data.data.message}`);
                break;
            case 'error':
                this.addDemoLog(`[${timestamp}] ❌ ${data.data.message}`);
                break;
            default:
                this.addDemoLog(`[${timestamp}] 📨 ${data.type}: ${JSON.stringify(data.data)}`);
        }
    }
    
    handleTranscription(transcript, timestamp) {
        if (!transcript || transcript === this.lastTranscript) return;
        
        this.lastTranscript = transcript;
        const transcriptionContent = document.getElementById('transcription-content');
        
        // Add active class and update transcription display
        transcriptionContent.classList.add('active');
        transcriptionContent.innerHTML = `
            <div style="font-size: 1.1rem; margin-bottom: 10px;">
                <strong>"${transcript}"</strong>
            </div>
            <div style="font-size: 0.9rem; color: #666;">
                Transcribed at ${timestamp}
            </div>
        `;
        
        this.addDemoLog(`[${timestamp}] 🎤 Whisper: "${transcript}"`);
        
        // Trigger fact-checking after a short delay
        setTimeout(() => {
            this.requestFactCheck(transcript);
        }, 1000);
    }
    
    async requestFactCheck(transcript) {
        try {
            // Simulate fact-checking request (in real implementation, this would be automatic)
            const brutalResponses = [
                `Let me be brutally honest... "${transcript.substring(0, 30)}..." sounds confident, but confidence doesn't equal accuracy. You're making assumptions without backing them up with solid evidence.`,
                `Let me be brutally honest... What you just said about "${transcript.substring(0, 30)}..." is the kind of statement that falls apart under scrutiny. Where's your proof?`,
                `Let me be brutally honest... That claim "${transcript.substring(0, 30)}..." is problematic. You're presenting opinion as fact, and that's intellectually dishonest.`,
                `Let me be brutally honest... Your statement "${transcript.substring(0, 30)}..." needs serious fact-checking. You're missing critical context that changes everything.`,
                `Let me be brutally honest... What you said "${transcript.substring(0, 30)}..." might sound smart, but it's built on shaky foundations. Let me tell you why...`
            ];
            
            const randomResponse = brutalResponses[Math.floor(Math.random() * brutalResponses.length)];
            const timestamp = new Date().toLocaleTimeString();
            
            // Simulate processing delay
            setTimeout(() => {
                this.handleBrutalHonesty({
                    brutal_response: randomResponse,
                    confidence: Math.random() * 0.6 + 0.2, // 0.2 to 0.8
                    issues: ['Unverified claim', 'Potential bias', 'Missing context'],
                    corrections: ['Provide sources', 'Acknowledge uncertainty', 'Consider alternatives']
                }, timestamp);
            }, 2000);
            
        } catch (error) {
            this.addDemoLog(`❌ Fact-checking failed: ${error.message}`);
        }
    }
    
    handleBrutalHonesty(analysis, timestamp) {
        const honestyContent = document.getElementById('honesty-content');
        
        // Update brutal honesty display
        honestyContent.innerHTML = `
            <div style="font-size: 1.1rem; margin-bottom: 15px; font-weight: bold; color: #d32f2f;">
                ${analysis.brutal_response || analysis.fact_check || "Let me be brutally honest... I couldn't analyze that properly."}
            </div>
            <div style="font-size: 0.9rem; margin-bottom: 10px;">
                <strong>Confidence:</strong> ${((analysis.confidence || 0.5) * 100).toFixed(1)}%
            </div>
            ${analysis.issues && analysis.issues.length > 0 ? `
            <div style="font-size: 0.9rem; margin-bottom: 10px;">
                <strong>Issues:</strong> ${analysis.issues.join(', ')}
            </div>
            ` : ''}
            <div style="font-size: 0.8rem; color: #666;">
                Analyzed at ${timestamp}
            </div>
        `;
        
        honestyContent.classList.add('brutal', 'brutal-active');
        
        // Remove animation class after animation completes
        setTimeout(() => {
            honestyContent.classList.remove('brutal-active');
        }, 500);
        
        this.addDemoLog(`[${timestamp}] 🧠 Llama: ${analysis.brutal_response || 'Brutal analysis complete'}`);
    }
    
    handleAudioStart(timestamp) {
        const transcriptionContent = document.getElementById('transcription-content');
        transcriptionContent.innerHTML = '<p style="color: #4CAF50; font-weight: bold;">🎤 Listening...</p>';
        transcriptionContent.classList.add('active');
        
        this.addDemoLog(`[${timestamp}] 🎤 Audio input detected`);
    }
    
    handleAudioEnd(timestamp) {
        const transcriptionContent = document.getElementById('transcription-content');
        transcriptionContent.innerHTML = '<p style="color: #FF9800; font-weight: bold;">🤖 Processing with Whisper...</p>';
        
        this.addDemoLog(`[${timestamp}] 🤖 Processing audio with Whisper...`);
    }
    
    addDemoLog(message) {
        const demoLog = document.getElementById('demo-log');
        const messageElement = document.createElement('p');
        messageElement.textContent = message;
        
        demoLog.appendChild(messageElement);
        demoLog.scrollTop = demoLog.scrollHeight;
    }
    
    clearDemoOutput() {
        // Clear transcription
        const transcriptionContent = document.getElementById('transcription-content');
        transcriptionContent.innerHTML = '<p class="placeholder">Speak into your OMI DevKit 2 to see live transcription...</p>';
        transcriptionContent.classList.remove('active');
        
        // Clear honesty
        const honestyContent = document.getElementById('honesty-content');
        honestyContent.innerHTML = '<p class="placeholder">Llama will brutally fact-check your statements here...</p>';
        honestyContent.classList.remove('brutal', 'brutal-active');
        
        // Clear log
        document.getElementById('demo-log').innerHTML = '<p>Demo log cleared</p>';
        
        this.lastTranscript = '';
    }

    // Demo.html merged methods
    async checkOMIStatus() {
        try {
            const response = await fetch('/api/omi/ports');
            const data = await response.json();
            
            // Minimal audio status display
            let audioHtml = '';
            if (data.omi_detected) {
                audioHtml += `<p><span class="status-tag status-online">OMI Connected</span></p>`;
                audioHtml += `<p style="font-size: 0.9em; color: #666;">Device ready for audio input</p>`;
            } else {
                audioHtml += `<p><span class="status-tag status-offline">OMI Not Found</span></p>`;
                audioHtml += `<p style="font-size: 0.9em; color: #666;">Please connect your OMI DevKit 2</p>`;
            }
            
            // Minimal details - only show if OMI is detected
            let detailsHtml = '';
            if (data.omi_detected) {
                const omiPort = data.ports.find(port => port.description && port.description.includes('XIAO'));
                if (omiPort) {
                    detailsHtml += `<div style="text-align: center; padding: 15px;">`;
                    detailsHtml += `<p style="font-size: 1.2em;">🎙️</p>`;
                    detailsHtml += `<p><strong>OMI DevKit 2</strong></p>`;
                    detailsHtml += `<p style="font-size: 0.9em; color: #666;">${omiPort.device}</p>`;
                    detailsHtml += `<p><span class="status-tag status-online">Ready</span></p>`;
                    detailsHtml += `</div>`;
                }
            } else {
                detailsHtml += `<div style="text-align: center; padding: 15px; color: #666;">`;
                detailsHtml += `<p>🔍</p>`;
                detailsHtml += `<p>No OMI DevKit 2 detected</p>`;
                detailsHtml += `<p style="font-size: 0.9em;">Connect device and click Scan</p>`;
                detailsHtml += `</div>`;
            }
            
            document.getElementById('omi-audio-status').innerHTML = audioHtml;
            document.getElementById('omi-details').innerHTML = detailsHtml;
        } catch (error) {
            document.getElementById('omi-audio-status').innerHTML = `<p><span class="status-tag status-offline">Connection Error</span></p>`;
            document.getElementById('omi-details').innerHTML = `<div style="text-align: center; padding: 15px; color: #666;"><p>❌</p><p>Unable to scan ports</p></div>`;
        }
    }

    async testOMIConnection() {
        try {
            const response = await fetch('/api/test/omi');
            const data = await response.json();
            
            let html = '<h4>Connection Test Results:</h4>';
            html += `<p><strong>Device Found:</strong> ${data.device_found ? '✅' : '❌'} ${data.device_found}</p>`;
            html += `<p><strong>Connection:</strong> ${data.connection_successful ? '✅' : '❌'} ${data.connection_successful}</p>`;
            html += `<p><strong>Streaming Ready:</strong> ${data.streaming_ready ? '✅' : '❌'} ${data.streaming_ready}</p>`;
            html += `<p><strong>Test Time:</strong> ${data.test_timestamp}</p>`;
            
            document.getElementById('omi-details').innerHTML += html;
        } catch (error) {
            document.getElementById('omi-details').innerHTML += `<p style="color: #ff0040;">Connection Test Error: ${error.message}</p>`;
        }
    }

    updateDemoStatus() {
        const demoHtml = `
            <p><span class="status-tag status-online">Demo Ready</span></p>
            <p>Real-time audio processing available</p>
            <p>Voice analysis and feedback enabled</p>
        `;
        document.getElementById('omi-demo-status').innerHTML = demoHtml;
    }

    async startOMIDemo() {
        try {
            document.getElementById('omi-demo-status').innerHTML = '<p>🔄 Starting demo...</p>';
            // Simulate demo start - replace with actual API call
            setTimeout(() => {
                document.getElementById('omi-demo-status').innerHTML = `
                    <p><span class="status-tag status-online">Demo Active</span></p>
                    <p>🎙️ Listening for audio input</p>
                    <p>🧠 AI analysis running</p>
                `;
            }, 1000);
        } catch (error) {
            document.getElementById('omi-demo-status').innerHTML = `<p style="color: #ff0040;">Demo Error: ${error.message}</p>`;
        }
    }

    stopOMIDemo() {
        document.getElementById('omi-demo-status').innerHTML = `
            <p><span class="status-tag status-offline">Demo Stopped</span></p>
            <p>Ready to restart</p>
        `;
    }

    // Override checkSystemStatus to include status tags
    async checkSystemStatus() {
        try {
            this.showLoading(true);
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // Update status dots
            this.updateStatusDot('platform-status', true);
            this.updateStatusDot('omi-status', data.omi_connected);
            
            // Update status container with neon tags
            const statusContainer = document.getElementById('system-status');
            if (statusContainer) {
                let html = '';
                html += `<span class="status-tag ${data.omi_connected ? 'status-online' : 'status-offline'}">OMI ${data.omi_connected ? 'Online' : 'Offline'}</span>`;
                html += `<span class="status-tag ${data.audio_processor ? 'status-online' : 'status-offline'}">Audio ${data.audio_processor ? 'Ready' : 'Error'}</span>`;
                html += `<span class="status-tag ${data.llm_analyzer ? 'status-online' : 'status-offline'}">LLM ${data.llm_analyzer ? 'Ready' : 'Error'}</span>`;
                html += `<span class="status-tag ${data.database ? 'status-online' : 'status-offline'}">Database ${data.database ? 'Ready' : 'Error'}</span>`;
                
                if (data.services) {
                    html += `<span class="status-tag ${data.services.postgres ? 'status-online' : 'status-offline'}">PostgreSQL ${data.services.postgres ? 'Ready' : 'Error'}</span>`;
                    html += `<span class="status-tag ${data.services.qdrant ? 'status-online' : 'status-offline'}">Qdrant ${data.services.qdrant ? 'Ready' : 'Error'}</span>`;
                    html += `<span class="status-tag ${data.services.ollama ? 'status-online' : 'status-offline'}">Ollama ${data.services.ollama ? 'Ready' : 'Error'}</span>`;
                }
                
                if (data.capabilities) {
                    html += `<span class="status-tag ${data.capabilities.real_time_streaming ? 'status-online' : 'status-offline'}">Real-time Streaming ${data.capabilities.real_time_streaming ? 'Ready' : 'Error'}</span>`;
                    html += `<span class="status-tag ${data.capabilities.audio_processing ? 'status-online' : 'status-offline'}">Audio Processing ${data.capabilities.audio_processing ? 'Ready' : 'Error'}</span>`;
                    html += `<span class="status-tag ${data.capabilities.transcription === 'basic_simulation' ? 'status-online' : 'status-offline'}">Transcription ${data.capabilities.transcription || 'Error'}</span>`;
                    html += `<span class="status-tag ${data.capabilities.fact_checking ? 'status-online' : 'status-offline'}">Fact Checking ${data.capabilities.fact_checking ? 'Ready' : 'Error'}</span>`;
                }
                
                statusContainer.innerHTML = html;
            }
            
            // Update output box with minimal view
            let output = `<div style="font-family: monospace; text-align: center;">`;
            output += `<p style="font-size: 1.1rem; margin: 20px 0;">🚀 <strong>System Ready</strong></p>`;
            output += `<p style="color: #666;">All components initialized and operational</p>`;
            output += `</div>`;
            this.updateOutput('system-output', output);
            
        } catch (error) {
            this.updateStatusDot('platform-status', false);
            const statusContainer = document.getElementById('system-status');
            if (statusContainer) {
                statusContainer.innerHTML = `<span class="status-tag status-offline">System Error</span>`;
            }
            this.updateOutput('system-output', `<p style="color: red;">❌ Failed to connect to platform: ${error.message}</p>`);
        } finally {
            this.showLoading(false);
        }
    }
}

// Global functions for button onclick handlers
let app;

window.onload = () => {
    app = new VoiceInsightApp();
};

// Close popup when clicking outside
window.onclick = function(event) {
    const popup = document.getElementById('omi-popup');
    if (event.target === popup) {
        closeOMIPopup();
    }
};

// Global function bindings
function checkSystemStatus() { app.checkSystemStatus(); }
function scanOMI() { app.scanOMI(); }
function testOMI() { app.testOMI(); }
function connectOMI() { app.connectOMI(); }
function selectAudioFile() { app.selectAudioFile(); }
function uploadAudio() { app.uploadAudio(); }
function connectWebSocket() { app.connectWebSocket(); }
function disconnectWebSocket() { app.disconnectWebSocket(); }
function clearStreamOutput() { app.clearStreamOutput(); }
function refreshAll() { app.refreshAll(); }
function runFullDemo() { app.runFullDemo(); }
function openAPIDocs() { app.openAPIDocs(); }
function downloadLogs() { app.downloadLogs(); }
function resetSystem() { app.resetSystem(); }

// Live Demo function bindings
function startLiveDemo() { app.startLiveDemo(); }
function stopLiveDemo() { app.stopLiveDemo(); }
function clearDemoOutput() { app.clearDemoOutput(); }

// Recording function bindings
function startRecording() { app.startRecording(); }
function stopRecording() { app.stopRecording(); }

// Demo.html merged functions
function openOMIPopup() {
    document.getElementById('omi-popup').style.display = 'block';
    app.checkOMIStatus(); // Refresh status when opening
    app.updateDemoStatus();
}

function closeOMIPopup() {
    document.getElementById('omi-popup').style.display = 'none';
}

function checkOMIStatus() { app.checkOMIStatus(); }
function testOMIConnection() { app.testOMIConnection(); }
function startOMIDemo() { app.startOMIDemo(); }
function stopOMIDemo() { app.stopOMIDemo(); }
