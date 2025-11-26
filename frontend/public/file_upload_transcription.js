// File Upload Transcription Functions
// Allows transcribing audio files directly without a connected device

// Global state for uploaded files
let uploadedFiles = new Map(); // file.name -> File object

// Global state for audio recording
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let recordingStartTime = null;
let recordingTimer = null;

// ============================================
// PROCESS LOG FUNCTIONS (Global)
// ============================================

window.clearProcessLogs = function() {
    const logContent = document.getElementById('log-content');
    const resultsLogContent = document.getElementById('results-log-content');
    if (logContent) logContent.innerHTML = '';
    if (resultsLogContent) resultsLogContent.innerHTML = '';
};

window.addProcessLog = function(message) {
    const logContent = document.getElementById('log-content');
    const resultsLogContent = document.getElementById('results-log-content');
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `<div style="margin-bottom: 4px;"><span style="color: #888;">[${timestamp}]</span> ${message}</div>`;
    
    if (logContent) {
        logContent.innerHTML += logEntry;
        logContent.scrollTop = logContent.scrollHeight;
    }
    if (resultsLogContent) {
        resultsLogContent.innerHTML += logEntry;
        resultsLogContent.scrollTop = resultsLogContent.scrollHeight;
    }
};

window.toggleProcessLogs = function() {
    const processLogs = document.getElementById('process-logs');
    const resultsLogs = document.getElementById('results-process-logs');
    
    if (processLogs) {
        processLogs.style.display = processLogs.style.display === 'none' ? 'block' : 'none';
    }
    if (resultsLogs) {
        resultsLogs.style.display = resultsLogs.style.display === 'none' ? 'block' : 'none';
    }
};

// Also available without window prefix
const clearProcessLogs = window.clearProcessLogs;
const addProcessLog = window.addProcessLog;
const toggleProcessLogs = window.toggleProcessLogs;

// ============================================
// TAB SWITCHING
// ============================================

function switchTranscriptionTab(tab) {
    const deviceTab = document.getElementById('tab-device');
    const uploadTab = document.getElementById('tab-upload');
    const deviceContent = document.getElementById('tab-content-device');
    const uploadContent = document.getElementById('tab-content-upload');
    
    if (tab === 'device') {
        deviceTab.classList.add('active');
        uploadTab.classList.remove('active');
        deviceContent.style.display = 'block';
        uploadContent.style.display = 'none';
        
        // Update selected files display visibility based on selections
        const selectedFilesDisplay = document.getElementById('selected-files-display');
        if (selectedFilesDisplay && typeof selectedRecordings !== 'undefined') {
            selectedFilesDisplay.style.display = selectedRecordings.size > 0 ? 'block' : 'none';
        }
    } else {
        deviceTab.classList.remove('active');
        uploadTab.classList.add('active');
        deviceContent.style.display = 'none';
        uploadContent.style.display = 'block';
    }
    
    lucide.createIcons();
}

// ============================================
// DRAG AND DROP HANDLERS
// ============================================

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    const dropzone = document.getElementById('file-upload-area');
    dropzone.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    const dropzone = document.getElementById('file-upload-area');
    dropzone.classList.remove('dragover');
}

function handleFileDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    const dropzone = document.getElementById('file-upload-area');
    dropzone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    processUploadedFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    processUploadedFiles(files);
}

// ============================================
// FILE PROCESSING
// ============================================

function processUploadedFiles(files) {
    const supportedFormats = ['.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm', '.mp4'];
    const maxSize = 100 * 1024 * 1024; // 100MB
    
    let addedCount = 0;
    let errors = [];
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        
        // Check format
        if (!supportedFormats.includes(ext)) {
            errors.push(`${file.name}: Unsupported format (${ext})`);
            continue;
        }
        
        // Check size
        if (file.size > maxSize) {
            errors.push(`${file.name}: File too large (max 100MB)`);
            continue;
        }
        
        // Check if already added
        if (uploadedFiles.has(file.name)) {
            continue; // Silently skip duplicates
        }
        
        uploadedFiles.set(file.name, file);
        addedCount++;
    }
    
    // Show errors if any
    if (errors.length > 0) {
        showNotification('error', errors.join('<br>'));
    }
    
    updateUploadedFilesDisplay();
    
    // Clear the file input
    const fileInput = document.getElementById('file-upload-input');
    if (fileInput) fileInput.value = '';
}

// ============================================
// UI UPDATES
// ============================================

function updateUploadedFilesDisplay() {
    const displayDiv = document.getElementById('uploaded-files-display');
    const listDiv = document.getElementById('uploaded-files-list');
    const summaryDiv = document.getElementById('uploaded-files-summary');
    const transcribeBtn = document.getElementById('upload-transcribe-btn');
    
    if (uploadedFiles.size === 0) {
        displayDiv.style.display = 'none';
        transcribeBtn.disabled = true;
        transcribeBtn.innerHTML = '<i data-lucide="wand-2" style="width: 16px; height: 16px; margin-right: 6px;"></i>Select files to transcribe';
        lucide.createIcons();
        return;
    }
    
    displayDiv.style.display = 'block';
    
    // Build file list HTML
    let listHtml = '';
    let totalSize = 0;
    
    uploadedFiles.forEach((file, filename) => {
        totalSize += file.size;
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        
        listHtml += `
            <div class="uploaded-file-item">
                <div class="uploaded-file-info">
                    <div class="uploaded-file-icon">
                        <i data-lucide="file-audio"></i>
                    </div>
                    <div class="uploaded-file-details">
                        <div class="uploaded-file-name" title="${filename}">${filename}</div>
                        <div class="uploaded-file-size">${sizeMB} MB</div>
                    </div>
                </div>
                <button class="uploaded-file-remove" onclick="removeUploadedFile('${filename}')" title="Remove">
                    <i data-lucide="x" style="width: 16px; height: 16px;"></i>
                </button>
            </div>
        `;
    });
    
    listDiv.innerHTML = listHtml;
    
    // Update summary
    const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);
    summaryDiv.textContent = `${uploadedFiles.size} file(s) selected • ${totalSizeMB} MB total`;
    
    // Update button
    transcribeBtn.disabled = false;
    transcribeBtn.innerHTML = `<i data-lucide="wand-2" style="width: 16px; height: 16px; margin-right: 6px;"></i>Transcribe ${uploadedFiles.size} file(s)`;
    
    lucide.createIcons();
}

function removeUploadedFile(filename) {
    uploadedFiles.delete(filename);
    updateUploadedFilesDisplay();
}

function clearUploadedFiles() {
    uploadedFiles.clear();
    updateUploadedFilesDisplay();
}

// ============================================
// TRANSCRIPTION
// ============================================

async function transcribeUploadedFiles() {
    if (uploadedFiles.size === 0) {
        showNotification('error', 'Please select at least one audio file');
        return;
    }
    
    const files = Array.from(uploadedFiles.values());
    const validateDocuments = document.getElementById('upload-enable-document-validation')?.checked || false;
    
    // Show loading state
    const loadingDiv = document.getElementById('transcription-loading');
    const resultsDiv = document.getElementById('transcription-results');
    const transcribeBtn = document.getElementById('upload-transcribe-btn');
    
    loadingDiv.style.display = 'block';
    resultsDiv.style.display = 'none';
    transcribeBtn.disabled = true;
    transcribeBtn.innerHTML = '<i data-lucide="loader-2" style="width: 16px; height: 16px; margin-right: 6px; animation: spin 1s linear infinite;"></i>Processing...';
    
    // Initialize logs
    clearProcessLogs();
    addProcessLog(`<i data-lucide="files" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Processing ${files.length} uploaded file(s)`);
    addProcessLog(`<i data-lucide="mic" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Initializing Whisper AI...`);
    
    let allResults = [];
    
    // Process each file
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        
        addProcessLog(`<i data-lucide="upload" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Uploading ${i + 1}/${files.length}: ${file.name}`);
        addProcessLog(`<i data-lucide="file" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>File size: ${sizeMB} MB`);
        
        try {
            // Create FormData for upload
            const formData = new FormData();
            formData.append('file', file);
            formData.append('validate_documents', validateDocuments.toString());
            
            // Send to transcription endpoint
            const response = await fetch('/api/ai/transcribe-file', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                result.filename = file.name;
                allResults.push(result);
                
                if (result.success) {
                    addProcessLog(`<i data-lucide="check" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Completed ${file.name}`);
                } else {
                    addProcessLog(`<i data-lucide="alert-circle" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Warning for ${file.name}: ${result.error || 'Unknown error'}`);
                }
            } else {
                const errorText = await response.text();
                console.error(`Transcription failed for ${file.name}:`, errorText);
                addProcessLog(`<i data-lucide="x" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Failed ${file.name}: ${errorText}`);
                
                allResults.push({
                    filename: file.name,
                    success: false,
                    error: errorText
                });
            }
        } catch (error) {
            console.error(`Error processing ${file.name}:`, error);
            addProcessLog(`<i data-lucide="x" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>Error ${file.name}: ${error.message}`);
            
            allResults.push({
                filename: file.name,
                success: false,
                error: error.message
            });
        }
    }
    
    // Hide loading state
    loadingDiv.style.display = 'none';
    
    // Reset button
    transcribeBtn.disabled = false;
    transcribeBtn.innerHTML = `<i data-lucide="wand-2" style="width: 16px; height: 16px; margin-right: 6px;"></i>Transcribe ${uploadedFiles.size} file(s)`;
    
    // Display results
    addProcessLog(`<i data-lucide="check-circle" style="width: 12px; height: 12px; display: inline-block; margin-right: 4px;"></i>All files processed`);
    displayUploadTranscriptionResults(allResults);
    
    lucide.createIcons();
}

function displayUploadTranscriptionResults(results) {
    const resultsDiv = document.getElementById('transcription-results');
    const clearBtn = document.getElementById('clear-results-btn');
    
    if (!resultsDiv) return;
    
    // Build results HTML
    let contentHtml = `
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <h3 style="margin: 0; color: #333;">Transcription Results</h3>
            <span style="margin-left: 10px; font-size: 12px; background: #f0f0f0; padding: 2px 8px; border-radius: 10px; color: #666;">
                ${results.filter(r => r.success).length}/${results.length} successful
            </span>
            <button onclick="toggleProcessLogs()" style="background: none; border: none; cursor: pointer; color: #666; margin-left: auto; padding: 0;" title="Show processing logs">
                <i data-lucide="info" style="width: 16px; height: 16px;"></i>
            </button>
        </div>
    `;
    
    results.forEach((result, index) => {
        if (result.success === false || !result.success) {
            // Error result
            contentHtml += `
                <div style="background: #fee; border: 1px solid #fcc; padding: 12px; border-radius: 8px; margin-bottom: 15px; font-size: 14px;">
                    <div style="font-weight: 500; color: #c53030; margin-bottom: 8px; display: flex; align-items: center;">
                        <i data-lucide="x-circle" style="width: 16px; height: 16px; margin-right: 6px;"></i>
                        ${result.filename} - Processing Failed
                    </div>
                    <div style="color: #666;">Error: ${result.error || 'Unknown error'}</div>
                </div>
            `;
        } else {
            // Success result
            contentHtml += `
                <div style="background: #f8f9fa; border: 1px solid #e9ecef; padding: 16px; border-radius: 8px; margin-bottom: 15px; font-size: 14px;">
                    <div style="font-weight: 500; color: #333; margin-bottom: 12px; display: flex; align-items: center; flex-wrap: wrap; gap: 8px;">
                        <i data-lucide="file-audio" style="width: 16px; height: 16px;"></i>
                        <span>${result.filename}</span>
                        <span style="font-size: 11px; background: #e3f2fd; color: #1976d2; padding: 2px 6px; border-radius: 4px;">Upload</span>
                        ${result.processing_time ? `<span style="font-size: 11px; background: #f5f5f5; color: #666; padding: 2px 6px; border-radius: 4px;">${result.processing_time}</span>` : ''}
                    </div>
                    
                    <div style="margin-bottom: 12px;">
                        <strong style="color: #333;">Transcript:</strong>
                        <div style="color: #333; margin-top: 4px; background: white; padding: 10px; border-radius: 6px; border: 1px solid #eee;">
                            ${result.transcription || '<em style="color: #999;">No transcription available</em>'}
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; margin-bottom: 12px;">
                        <strong style="color: #333;">Sentiment:</strong>
                        <span style="color: #555;">${result.sentiment || 'neutral'}</span>
                        
                        <strong style="color: #333;">Confidence:</strong>
                        <span style="color: #555;">${result.confidence || 'N/A'}</span>
                        
                        <strong style="color: #333;">Credibility:</strong>
                        <span style="color: #555;">${result.credibility_score || 'N/A'}</span>
                    </div>
                    
                    <div style="border-top: 1px solid #eee; padding-top: 12px;">
                        <strong style="color: #333;">🔥 Brutal Honest Reply:</strong>
                        <div style="color: #555; margin-top: 6px; line-height: 1.5; background: #fffbf0; padding: 10px; border-radius: 6px; border-left: 3px solid #f59e0b;">
                            ${result.brutal_honesty || '<em style="color: #999;">Analysis not available</em>'}
                        </div>
                    </div>
                    
                    ${result.keywords && result.keywords.length > 0 ? `
                        <div style="margin-top: 12px;">
                            <strong style="color: #333; font-size: 12px;">Keywords:</strong>
                            <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px;">
                                ${result.keywords.map(k => `<span style="font-size: 11px; background: #e8e8e8; color: #666; padding: 2px 8px; border-radius: 10px;">${k}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                    
                    ${result.document_validation ? `
                        <div style="margin-top: 12px; border-top: 1px solid #eee; padding-top: 12px;">
                            <strong style="color: #333;">📚 Document Validation:</strong>
                            <div style="color: #555; margin-top: 4px;">
                                ${result.document_validation}
                            </div>
                            ${result.validation_score ? `<div style="margin-top: 4px; font-size: 12px; color: #666;">Score: ${result.validation_score}</div>` : ''}
                        </div>
                    ` : ''}
                </div>
            `;
        }
    });
    
    // Add expandable logs section
    contentHtml += `
        <div id="results-process-logs" style="display: none; margin-bottom: 15px; text-align: left; background: #f8f9fa; padding: 15px; border-radius: 8px; max-height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px; border: 1px solid #ddd;">
            <div style="text-align: center; margin-bottom: 10px; font-weight: bold; color: #333;">Processing Logs</div>
            <div id="results-log-content" style="color: #555; line-height: 1.4;">
                ${document.getElementById('process-logs')?.innerHTML || ''}
            </div>
        </div>
    `;
    
    resultsDiv.innerHTML = contentHtml;
    resultsDiv.style.display = 'block';
    
    if (clearBtn) clearBtn.style.display = 'inline-flex';
    
    lucide.createIcons();
}

// ============================================
// HELPER FUNCTIONS
// ============================================

function showNotification(typeOrMessage, message) {
    // Support both (type, message) and (message, type) patterns
    let type = 'info';
    let msg = message;
    
    if (typeof message === 'undefined') {
        // Single argument - just the message
        msg = typeOrMessage;
    } else if (['success', 'error', 'warning', 'info'].includes(typeOrMessage)) {
        type = typeOrMessage;
        msg = message;
    } else {
        msg = typeOrMessage;
        if (['success', 'error', 'warning', 'info'].includes(message)) {
            type = message;
            msg = typeOrMessage;
        }
    }
    
    // Use notification system if available
    if (typeof window.notificationSystem !== 'undefined' && window.notificationSystem) {
        const titleMap = {
            success: '✅ Success',
            error: '❌ Error',
            warning: '⚠️ Warning',
            info: 'ℹ️ Info'
        };
        window.notificationSystem[type](titleMap[type], msg.replace(/<br>/g, '\n'));
        return;
    }
    
    // Fallback to alert
    if (type === 'error') {
        alert('Error: ' + msg.replace(/<br>/g, '\n'));
    } else {
        alert(msg.replace(/<br>/g, '\n'));
    }
}

// ============================================
// AUDIO RECORDING (Mobile Support)
// ============================================

// Check if recording is supported (requires HTTPS or localhost)
function isRecordingSupported() {
    // Check for secure context (HTTPS or localhost)
    const isSecure = window.isSecureContext || 
                     location.protocol === 'https:' || 
                     location.hostname === 'localhost' || 
                     location.hostname === '127.0.0.1';
    
    // Check for mediaDevices API
    const hasMediaDevices = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    
    // Check for MediaRecorder
    const hasMediaRecorder = typeof MediaRecorder !== 'undefined';
    
    return isSecure && hasMediaDevices && hasMediaRecorder;
}

async function startRecording() {
    try {
        // Check if recording is supported
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            // Not a secure context - show helpful message
            const isHTTP = location.protocol === 'http:' && location.hostname !== 'localhost';
            if (isHTTP) {
                showNotification('error', 'Recording requires HTTPS. Please access via https:// or use localhost.');
                console.error('Recording requires secure context (HTTPS). Current protocol:', location.protocol);
            } else {
                showNotification('error', 'Recording not supported in this browser.');
            }
            return;
        }
        
        // Request microphone permission
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 44100
            } 
        });
        
        // Determine best supported format
        const mimeType = getSupportedMimeType();
        
        mediaRecorder = new MediaRecorder(stream, { mimeType });
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            
            // Create blob from chunks
            const audioBlob = new Blob(audioChunks, { type: mimeType });
            
            // Generate filename with timestamp
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const extension = mimeType.includes('webm') ? 'webm' : 
                              mimeType.includes('mp4') ? 'm4a' : 
                              mimeType.includes('ogg') ? 'ogg' : 'wav';
            const filename = `recording_${timestamp}.${extension}`;
            
            // Create File object from Blob
            const file = new File([audioBlob], filename, { type: mimeType });
            
            // Add to uploaded files
            uploadedFiles.set(filename, file);
            updateUploadedFilesDisplay();
            
            showNotification('success', `Recording saved: ${filename}`);
        };
        
        // Start recording
        mediaRecorder.start(1000); // Collect data every second
        isRecording = true;
        recordingStartTime = Date.now();
        
        // Update UI
        updateRecordingUI(true);
        startRecordingTimer();
        
    } catch (error) {
        console.error('Error starting recording:', error);
        
        if (error.name === 'NotAllowedError') {
            showNotification('error', 'Microphone access denied. Please allow microphone access to record.');
        } else if (error.name === 'NotFoundError') {
            showNotification('error', 'No microphone found. Please connect a microphone.');
        } else {
            showNotification('error', `Recording error: ${error.message}`);
        }
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        
        // Update UI
        updateRecordingUI(false);
        stopRecordingTimer();
    }
}

function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

function getSupportedMimeType() {
    const types = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/ogg;codecs=opus',
        'audio/ogg',
        'audio/wav'
    ];
    
    for (const type of types) {
        if (MediaRecorder.isTypeSupported(type)) {
            return type;
        }
    }
    
    return 'audio/webm'; // Fallback
}

function updateRecordingUI(recording) {
    const recordBtn = document.getElementById('record-btn');
    const recordIcon = document.getElementById('record-icon');
    const recordText = document.getElementById('record-text');
    const recordTimer = document.getElementById('record-timer');
    const recordIndicator = document.getElementById('recording-indicator');
    const recordSection = document.getElementById('record-section');
    
    if (recordBtn) {
        if (recording) {
            recordBtn.classList.add('recording');
            recordBtn.style.background = '#dc2626';
        } else {
            recordBtn.classList.remove('recording');
            recordBtn.style.background = '#333';
        }
    }
    
    if (recordIcon) {
        recordIcon.setAttribute('data-lucide', recording ? 'square' : 'mic');
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
    }
    
    if (recordText) {
        recordText.textContent = recording ? 'Stop Recording' : 'Start Recording';
    }
    
    if (recordTimer) {
        recordTimer.style.display = recording ? 'inline' : 'none';
        if (!recording) recordTimer.textContent = '';
    }
    
    // Update recording indicator
    if (recordIndicator) {
        recordIndicator.style.display = recording ? 'block' : 'none';
    }
    
    // Update record section styling
    if (recordSection) {
        if (recording) {
            recordSection.classList.add('recording-active');
        } else {
            recordSection.classList.remove('recording-active');
        }
    }
}

function startRecordingTimer() {
    const timerEl = document.getElementById('record-timer');
    if (!timerEl) return;
    
    recordingTimer = setInterval(() => {
        if (!recordingStartTime) return;
        
        const elapsed = Math.floor((Date.now() - recordingStartTime) / 1000);
        const mins = Math.floor(elapsed / 60).toString().padStart(2, '0');
        const secs = (elapsed % 60).toString().padStart(2, '0');
        timerEl.textContent = `${mins}:${secs}`;
    }, 1000);
}

function stopRecordingTimer() {
    if (recordingTimer) {
        clearInterval(recordingTimer);
        recordingTimer = null;
    }
    recordingStartTime = null;
}

// Check if recording is supported
function isRecordingSupported() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder);
}

// Make functions globally available
window.switchTranscriptionTab = switchTranscriptionTab;
window.handleDragOver = handleDragOver;
window.handleDragLeave = handleDragLeave;
window.handleFileDrop = handleFileDrop;
window.handleFileSelect = handleFileSelect;
window.removeUploadedFile = removeUploadedFile;
window.clearUploadedFiles = clearUploadedFiles;
window.transcribeUploadedFiles = transcribeUploadedFiles;
window.startRecording = startRecording;
window.stopRecording = stopRecording;
window.toggleRecording = toggleRecording;
window.isRecordingSupported = isRecordingSupported;

