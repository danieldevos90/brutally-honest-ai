// File Upload Transcription Functions
// Allows transcribing audio files directly without a connected device

// Global state for uploaded files
let uploadedFiles = new Map(); // file.name -> File object

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

function showNotification(type, message) {
    // Use existing notification system if available
    if (typeof window.showNotification === 'function') {
        window.showNotification(type, message);
        return;
    }
    
    // Fallback to alert
    if (type === 'error') {
        alert('Error: ' + message.replace(/<br>/g, '\n'));
    } else {
        alert(message.replace(/<br>/g, '\n'));
    }
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

