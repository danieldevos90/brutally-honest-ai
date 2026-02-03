// VERSION: 2.1.0 - Build 2026-02-03 - Added Queue System
console.log("File Upload Transcription v2.1.0 loaded");
// File Upload Transcription Functions
// Allows transcribing audio files directly without a connected device

// Global state for uploaded files
let uploadedFiles = new Map(); // file.name -> File object

// ============================================
// UPLOAD QUEUE SYSTEM - Prevents Server Overload
// ============================================

class UploadQueue {
    constructor(maxConcurrent = 2) {
        this.maxConcurrent = maxConcurrent;
        this.activeJobs = 0;
        this.queue = [];
        this.results = [];
        this.onProgress = null;
        this.onComplete = null;
    }
    
    add(job) {
        return new Promise((resolve, reject) => {
            this.queue.push({ job, resolve, reject });
            this.processNext();
        });
    }
    
    async processNext() {
        if (this.activeJobs >= this.maxConcurrent || this.queue.length === 0) {
            return;
        }
        
        const { job, resolve, reject } = this.queue.shift();
        this.activeJobs++;
        
        try {
            const result = await job();
            this.results.push(result);
            resolve(result);
        } catch (error) {
            reject(error);
        } finally {
            this.activeJobs--;
            this.processNext();
            
            // Check if all done
            if (this.activeJobs === 0 && this.queue.length === 0 && this.onComplete) {
                this.onComplete(this.results);
            }
        }
    }
    
    clear() {
        this.queue = [];
        this.results = [];
    }
    
    get pending() {
        return this.queue.length;
    }
    
    get active() {
        return this.activeJobs;
    }
}

// Global upload queue - max 2 concurrent uploads to prevent overload
const uploadQueue = new UploadQueue(2);

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
    const saveOnlyBtn = document.getElementById('upload-save-only-btn');
    const countBadge = document.getElementById('files-count-badge');
    
    if (uploadedFiles.size === 0) {
        if (displayDiv) displayDiv.style.display = 'none';
        if (transcribeBtn) {
            transcribeBtn.disabled = true;
            const btnText = transcribeBtn.querySelector('.btn-text');
            if (btnText) btnText.textContent = 'Select files to transcribe';
        }
        if (saveOnlyBtn) {
            saveOnlyBtn.disabled = true;
        }
        return;
    }
    
    if (displayDiv) displayDiv.style.display = 'block';
    
    // Build enhanced file list HTML
    let listHtml = '';
    let totalSize = 0;
    
    uploadedFiles.forEach((file, filename) => {
        totalSize += file.size;
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const ext = filename.split('.').pop().toUpperCase();
        
        listHtml += `
            <div class="file-item">
                <div class="file-icon">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
                    </svg>
                </div>
                <div class="file-info">
                    <div class="file-name" title="${filename}">${filename}</div>
                    <div class="file-size">${sizeMB} MB • ${ext}</div>
                </div>
                <button class="file-remove" onclick="removeUploadedFile('${filename.replace(/'/g, "\\'")}')" title="Remove" aria-label="Remove ${filename}">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        `;
    });
    
    if (listDiv) listDiv.innerHTML = listHtml;
    
    // Update count badge
    if (countBadge) countBadge.textContent = uploadedFiles.size;
    
    // Update summary bar
    const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);
    if (summaryDiv) {
        const summaryText = summaryDiv.querySelector('.summary-text');
        const summarySize = summaryDiv.querySelector('.summary-size');
        if (summaryText) summaryText.textContent = `${uploadedFiles.size} file${uploadedFiles.size > 1 ? 's' : ''} selected`;
        if (summarySize) summarySize.textContent = `${totalSizeMB} MB`;
        // Fallback for old structure
        if (!summaryText && !summarySize) {
            summaryDiv.innerHTML = `
                <span class="summary-text">${uploadedFiles.size} file${uploadedFiles.size > 1 ? 's' : ''} selected</span>
                <span class="summary-size">${totalSizeMB} MB</span>
            `;
        }
    }
    
    // Update transcribe button
    if (transcribeBtn) {
        transcribeBtn.disabled = false;
        const btnText = transcribeBtn.querySelector('.btn-text');
        if (btnText) {
            btnText.textContent = `Transcribe ${uploadedFiles.size} file${uploadedFiles.size > 1 ? 's' : ''}`;
        } else {
            // Fallback for old button structure
            transcribeBtn.innerHTML = `
                <svg class="btn-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.581-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
                </svg>
                <span class="btn-text">Transcribe ${uploadedFiles.size} file${uploadedFiles.size > 1 ? 's' : ''}</span>
            `;
        }
    }
    
    if (saveOnlyBtn) {
        saveOnlyBtn.disabled = false;
    }
    
    // Recreate Lucide icons if available
    if (typeof lucide !== 'undefined') lucide.createIcons();
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
    
    // Show loading state with enhanced UI
    const loadingDiv = document.getElementById('transcription-loading');
    const resultsDiv = document.getElementById('transcription-results');
    const transcribeBtn = document.getElementById('upload-transcribe-btn');
    const filesDisplay = document.getElementById('uploaded-files-display');
    
    if (loadingDiv) loadingDiv.style.display = 'block';
    if (resultsDiv) resultsDiv.style.display = 'none';
    if (filesDisplay) filesDisplay.style.opacity = '0.6';
    
    if (transcribeBtn) {
        transcribeBtn.disabled = true;
        const btnText = transcribeBtn.querySelector('.btn-text');
        const btnIcon = transcribeBtn.querySelector('.btn-icon');
        if (btnText) btnText.textContent = 'Processing...';
        if (btnIcon) btnIcon.style.animation = 'spin 1s linear infinite';
    }
    
    // Update processing UI elements
    updateProcessingUI('Preparing upload...', files[0]?.name || 'files', 0, files.length);
    
    // Initialize logs
    clearProcessLogs();
    addProcessLog(`🚀 Queuing ${files.length} file(s) for processing (max 2 concurrent)`);
    
    // Clear previous queue results
    uploadQueue.clear();
    
    // Create jobs for each file
    const jobPromises = files.map((file, index) => {
        return uploadQueue.add(async () => {
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            addProcessLog(`📤 [${index + 1}/${files.length}] Uploading: ${file.name} (${sizeMB} MB)`);
            
            // Update button with queue status
            if (transcribeBtn) {
                const pending = uploadQueue.pending;
                const active = uploadQueue.active;
                transcribeBtn.innerHTML = `<i data-lucide="loader-2" style="width: 16px; height: 16px; margin-right: 6px; animation: spin 1s linear infinite;"></i>Processing ${active} / Queued ${pending}`;
            }
            
            try {
                // Create FormData for upload
                const formData = new FormData();
                formData.append('file', file);
                formData.append('validate_documents', validateDocuments.toString());
                
                // Submit to ASYNC transcription endpoint
                const submitResponse = await fetch('/api/ai/transcribe-file-async', {
                    method: 'POST',
                    body: formData
                });
                
                if (!submitResponse.ok) {
                    const errorText = await submitResponse.text();
                    throw new Error(errorText);
                }
                
                const submitResult = await submitResponse.json();
                const jobId = submitResult.job_id;
                
                addProcessLog(`⏳ [${file.name}] Job ${jobId.slice(0, 8)}... queued`);
                
                // Poll for job completion
                let jobComplete = false;
                let lastProgress = 0;
                
                while (!jobComplete) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    
                    const statusResponse = await fetch(`/api/ai/jobs/${jobId}`);
                    if (!statusResponse.ok) {
                        throw new Error('Failed to get job status');
                    }
                    
                    const jobStatus = await statusResponse.json();
                    
                    // Update progress if changed significantly
                    if (jobStatus.progress - lastProgress >= 10) {
                        lastProgress = jobStatus.progress;
                        addProcessLog(`⚙️ [${file.name}] ${jobStatus.progress}%`);
                    }
                    
                    if (jobStatus.status === 'completed') {
                        jobComplete = true;
                        const result = jobStatus.result;
                        result.filename = file.name;
                        addProcessLog(`✅ [${file.name}] Complete`);
                        return result;
                        
                    } else if (jobStatus.status === 'failed') {
                        jobComplete = true;
                        addProcessLog(`❌ [${file.name}] Failed: ${jobStatus.error}`);
                        return {
                            filename: file.name,
                            success: false,
                            error: jobStatus.error
                        };
                    }
                }
                
            } catch (error) {
                console.error(`Error processing ${file.name}:`, error);
                addProcessLog(`❌ [${file.name}] Error: ${error.message}`);
                return {
                    filename: file.name,
                    success: false,
                    error: error.message
                };
            }
        });
    });
    
    // Wait for all jobs to complete
    const allResults = await Promise.all(jobPromises);
    
    // Hide loading state
    if (loadingDiv) loadingDiv.style.display = 'none';
    if (filesDisplay) filesDisplay.style.opacity = '1';
    
    // Reset button
    if (transcribeBtn) {
        transcribeBtn.disabled = false;
        const btnText = transcribeBtn.querySelector('.btn-text');
        const btnIcon = transcribeBtn.querySelector('.btn-icon');
        if (btnText) btnText.textContent = `Transcribe ${uploadedFiles.size} file${uploadedFiles.size > 1 ? 's' : ''}`;
        if (btnIcon) btnIcon.style.animation = '';
    }
    
    // Display results
    addProcessLog(`🎉 All ${files.length} file(s) processed!`);
    displayUploadTranscriptionResults(allResults);
    
    // Show success notification
    const successCount = allResults.filter(r => r.success !== false).length;
    if (successCount > 0) {
        showNotification('success', `Successfully processed ${successCount} of ${files.length} file(s)`);
    }
    
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

// Enhanced UI update function for processing state
function updateProcessingUI(stage, filename, progress, queuePending) {
    const stageEl = document.getElementById('processing-stage');
    const fileEl = document.getElementById('processing-file');
    const progressBar = document.getElementById('progress-bar');
    const progressPercent = document.getElementById('progress-percent');
    const progressEta = document.getElementById('progress-eta');
    const queueCount = document.getElementById('queue-pending-count');
    
    if (stageEl) stageEl.textContent = stage;
    if (fileEl) fileEl.textContent = filename;
    if (progressBar) progressBar.style.width = `${progress}%`;
    if (progressPercent) progressPercent.textContent = `${Math.round(progress)}%`;
    if (queueCount) queueCount.textContent = `${queuePending} in queue`;
    
    // Estimate ETA based on progress
    if (progressEta) {
        if (progress < 10) {
            progressEta.textContent = 'Estimating...';
        } else if (progress >= 100) {
            progressEta.textContent = 'Complete';
        } else {
            progressEta.textContent = 'Processing audio...';
        }
    }
}

// ============================================
// SAVE ONLY (NO TRANSCRIPTION)
// ============================================

async function saveUploadedFilesOnly() {
    if (uploadedFiles.size === 0) {
        showNotification('error', 'Please select at least one audio file');
        return;
    }
    
    const files = Array.from(uploadedFiles.values());
    const saveBtn = document.getElementById('upload-save-only-btn');
    const transcribeBtn = document.getElementById('upload-transcribe-btn');
    
    // Show loading state
    saveBtn.disabled = true;
    transcribeBtn.disabled = true;
    saveBtn.innerHTML = '<i data-lucide="loader-2" style="width: 16px; height: 16px; margin-right: 6px; animation: spin 1s linear infinite;"></i>Saving...';
    
    let savedCount = 0;
    let errorCount = 0;
    
    // Save each file
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        
        try {
            // Create FormData for upload
            const formData = new FormData();
            formData.append('file', file);
            formData.append('title', file.name);
            
            // Submit to save-only endpoint
            const response = await fetch('/api/save-recording', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText);
            }
            
            const result = await response.json();
            
            if (result.success) {
                savedCount++;
                console.log(`Saved: ${file.name} -> ${result.filename}`);
            } else {
                errorCount++;
            }
            
        } catch (error) {
            console.error(`Error saving ${file.name}:`, error);
            errorCount++;
        }
    }
    
    // Reset buttons
    saveBtn.disabled = false;
    transcribeBtn.disabled = false;
    saveBtn.innerHTML = '<i data-lucide="save" style="width: 16px; height: 16px; margin-right: 6px;"></i>Save Only (transcribe later)';
    
    // Show result notification
    if (savedCount > 0) {
        showNotification('success', `Saved ${savedCount} recording(s). Use Re-analyze in History to transcribe later.`);
        
        // Clear the uploaded files
        uploadedFiles.clear();
        updateUploadedFilesDisplay();
        
        // Refresh history if the function exists
        if (typeof loadTranscriptionHistory === 'function') {
            loadTranscriptionHistory();
        } else if (typeof window.loadHistory === 'function') {
            window.loadHistory();
        }
    }
    
    if (errorCount > 0) {
        showNotification('error', `Failed to save ${errorCount} file(s)`);
    }
    
    lucide.createIcons();
}

// Make save function globally available
window.saveUploadedFilesOnly = saveUploadedFilesOnly;

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
                        <strong style="color: #333;">Brutal Honest Reply:</strong>
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
                            <strong style="color: #333;">Document Validation:</strong>
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
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
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
        
        // Create MediaRecorder - if mimeType is empty, let browser choose
        try {
            if (mimeType) {
        mediaRecorder = new MediaRecorder(stream, { mimeType });
            } else {
                mediaRecorder = new MediaRecorder(stream);
            }
        } catch (e) {
            console.error('MediaRecorder creation failed:', e);
            // Try without options as fallback
            mediaRecorder = new MediaRecorder(stream);
        }
        
        const actualMimeType = mediaRecorder.mimeType || mimeType || 'audio/webm';
        console.log('MediaRecorder using:', actualMimeType);
        
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };
        
        mediaRecorder.onstop = async () => {
            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
            
            // Create blob from chunks - use actual mime type from recorder
            const finalMimeType = mediaRecorder.mimeType || actualMimeType;
            const audioBlob = new Blob(audioChunks, { type: finalMimeType });
            
            // Generate filename with timestamp
            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
            const extension = finalMimeType.includes('webm') ? 'webm' : 
                              finalMimeType.includes('mp4') ? 'm4a' : 
                              finalMimeType.includes('mp4a') ? 'm4a' :
                              finalMimeType.includes('aac') ? 'aac' :
                              finalMimeType.includes('ogg') ? 'ogg' : 'wav';
            const filename = `recording_${timestamp}.${extension}`;
            
            // Create File object from Blob
            const file = new File([audioBlob], filename, { type: finalMimeType });
            window.lastRecordedFile = file; // Store for later use
            
            console.log('Recording stopped:', filename, 'Size:', audioBlob.size, 'Type:', finalMimeType);
            
            // Show the recent recording preview
            const recentRecording = document.getElementById('recent-recording');
            const playback = document.getElementById('recording-playback');
            const statusBadge = document.getElementById('recent-recording-status');
            
            if (recentRecording && playback) {
                // Create URL for playback
                const audioUrl = URL.createObjectURL(audioBlob);
                playback.src = audioUrl;
                recentRecording.style.display = 'block';
                if (statusBadge) {
                    statusBadge.textContent = 'Saving...';
                    statusBadge.className = 'status-badge pending';
                }
            }
            
            // Show saving notification
            if (typeof addNotification === 'function') {
                addNotification('progress', `Saving: ${filename}`);
            } else {
                showNotification('info', `Saving recording to server...`);
            }
            
            // Auto-upload to server
            try {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('filename', filename);
                
                const response = await fetch('/api/recordings/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const result = await response.json();
                    console.log('Recording uploaded successfully:', result);
                    
                    // Update status badge
                    if (statusBadge) {
                        statusBadge.textContent = 'Saved';
                        statusBadge.className = 'status-badge saved';
                    }
                    
                    // Show success notification
                    if (typeof addNotification === 'function') {
                        addNotification('success', `Recording saved: ${filename}`);
                    } else {
                        showNotification('success', `Recording saved: ${filename}`);
                    }
                    
                    // Refresh recordings list
                    if (typeof loadTranscriptionHistory === 'function') {
                        await loadTranscriptionHistory();
                    }
                    
                    // DON'T auto-switch tabs - stay on record tab to show the preview
                    
                } else {
                    const errorText = await response.text();
                    console.error('Upload failed:', response.status, errorText);
                    
                    // Update status badge
                    if (statusBadge) {
                        statusBadge.textContent = 'Error';
                        statusBadge.className = 'status-badge error';
                    }
                    
                    if (typeof addNotification === 'function') {
                        addNotification('error', `Failed to save: ${response.statusText}`);
                    } else {
                        showNotification('error', `Failed to save recording: ${response.statusText}`);
                    }
                    
                    // Fallback: keep in local storage
            uploadedFiles.set(filename, file);
            updateUploadedFilesDisplay();
                }
            } catch (uploadError) {
                console.error('Upload error:', uploadError);
                
                // Update status badge
                if (statusBadge) {
                    statusBadge.textContent = 'Error';
                    statusBadge.className = 'status-badge error';
                }
                
                if (typeof addNotification === 'function') {
                    addNotification('error', `Upload error: ${uploadError.message}`);
                } else {
                    showNotification('error', `Upload error: ${uploadError.message}`);
                }
                
                // Fallback: keep in local storage
                uploadedFiles.set(filename, file);
                updateUploadedFilesDisplay();
            }
        };
        
        // Start recording
        mediaRecorder.start(1000); // Collect data every second
        isRecording = true;
        recordingStartTime = Date.now();
        
        // Update UI
        updateRecordingUI(true);
        startRecordingTimer();
        
    } catch (error) {
        console.error('Error starting recording:', error.name, error.message, error);
        
        if (error.name === 'NotAllowedError') {
            showNotification('error', 'Microphone access denied. Please allow microphone access to record.');
        } else if (error.name === 'NotFoundError') {
            showNotification('error', 'No microphone found. Please connect a microphone.');
        } else if (error.name === 'NotSupportedError') {
            showNotification('error', 'Audio format not supported. Try a different browser.');
        } else if (error.name === 'NotReadableError') {
            showNotification('error', 'Microphone is in use by another application.');
        } else if (error.name === 'AbortError') {
            showNotification('error', 'Recording was aborted. Please try again.');
        } else {
            showNotification('error', `Recording error: ${error.name || 'Unknown'} - ${error.message || 'Please check microphone permissions'}`);
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
    // Check if MediaRecorder is available
    if (typeof MediaRecorder === 'undefined') {
        console.error('MediaRecorder not supported');
        return '';
    }
    
    // iOS Safari prefers mp4, put it first for iOS
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) || 
                  (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    
    const types = isIOS ? [
        'audio/mp4',
        'audio/mp4;codecs=mp4a.40.2',
        'audio/aac',
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/wav'
    ] : [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/mp4',
        'audio/ogg;codecs=opus',
        'audio/ogg',
        'audio/wav'
    ];
    
    for (const type of types) {
        try {
        if (MediaRecorder.isTypeSupported(type)) {
                console.log('Using audio format:', type);
            return type;
            }
        } catch (e) {
            console.warn('Error checking mime type:', type, e);
        }
    }
    
    // Try without specifying mimeType (let browser choose)
    console.warn('No specific mime type supported, using browser default');
    return '';
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
            recordBtn.style.color = '#fff';
        } else {
            recordBtn.classList.remove('recording');
            recordBtn.style.background = '';
            recordBtn.style.color = '';
        }
        
        // Update button text directly if no separate record-text element
        if (!recordText) {
            recordBtn.textContent = recording ? 'Stop Recording' : 'Start Recording';
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

// Functions for recent recording preview
window.transcribeLastRecording = async function() {
    if (!window.lastRecordedFile) {
        showNotification('error', 'No recording to transcribe');
        return;
    }
    
    // Add to uploaded files and trigger transcription
    uploadedFiles.clear();
    uploadedFiles.set(window.lastRecordedFile.name, window.lastRecordedFile);
    updateUploadedFilesDisplay();
    
    // Switch to upload tab and start transcription
    if (typeof switchTab === 'function') {
        switchTab('upload');
    }
    
    // Start transcription after a brief delay
    setTimeout(() => {
        transcribeUploadedFiles();
    }, 500);
};

window.discardLastRecording = async function() {
    if (!confirm('Discard this recording?')) return;
    
    const recentRecording = document.getElementById('recent-recording');
    const playback = document.getElementById('recording-playback');
    
    if (playback) {
        playback.pause();
        playback.src = '';
    }
    
    if (recentRecording) {
        recentRecording.style.display = 'none';
    }
    
    window.lastRecordedFile = null;
    
    if (typeof addNotification === 'function') {
        addNotification('info', 'Recording discarded');
    } else {
        showNotification('info', 'Recording discarded');
    }
};


// Show toast when recording is saved
if (typeof showToast === 'function') {
    // Patch the recording save
    const origAddRecording = typeof addRecordingToList === 'function' ? addRecordingToList : null;
    if (origAddRecording) {
        window.addRecordingToList = function(...args) {
            const result = origAddRecording.apply(this, args);
            showToast('Recording saved!', 'success');
            return result;
        };
    }
}
