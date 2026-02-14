// Enhanced Documents Page JavaScript with Multi-file Upload Support
// Uses relative URLs to work through the Node.js proxy in production

let selectedFiles = [];
let uploadResults = { completed: 0, failed: 0, total: 0 };

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (typeof lucide !== 'undefined') lucide.createIcons();
    setupFileUpload();
    loadDocuments();
});

function setupFileUpload() {
    const uploadArea = document.querySelector('.file-upload') || document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    if (!uploadArea || !fileInput) {
        console.warn('Upload elements not found');
        return;
    }
    
    // Drag and drop
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
        handleFiles(e.dataTransfer.files);
    });
    
    // File input - add more files to selection
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

function handleFiles(files) {
    if (files.length === 0) return;
    
    const supportedTypes = ['.txt', '.pdf', '.doc', '.docx'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    for (let file of files) {
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!supportedTypes.includes(extension)) {
            showNotification(`Unsupported: ${file.name}`, 'error');
            continue;
        }
        
        if (file.size > maxSize) {
            showNotification(`Too large: ${file.name} (max 10MB)`, 'error');
            continue;
        }
        
        // Check for duplicates
        if (selectedFiles.some(f => f.name === file.name && f.size === file.size)) {
            continue;
        }
        
        selectedFiles.push(file);
    }
    
    if (selectedFiles.length > 0) {
        showSelectedFiles();
    }
}

function showSelectedFiles() {
    const selectedSection = document.getElementById('selected-files');
    const filesList = document.getElementById('files-list');
    const filesCount = document.getElementById('files-count');
    const uploadArea = document.getElementById('upload-area');
    
    if (!selectedSection || !filesList) return;
    
    selectedSection.style.display = 'block';
    if (uploadArea) uploadArea.style.opacity = '0.6';
    
    // Update count
    if (filesCount) {
        filesCount.textContent = `${selectedFiles.length} file${selectedFiles.length > 1 ? 's' : ''} selected`;
    }
    
    // Update button text
    const uploadBtn = document.getElementById('upload-btn-text');
    if (uploadBtn) {
        uploadBtn.textContent = `Upload ${selectedFiles.length} File${selectedFiles.length > 1 ? 's' : ''}`;
    }
    
    // Render file list
    filesList.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item" style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: var(--color-gray-100); border-radius: 8px;">
            <div style="flex: 1; min-width: 0;">
                <div style="font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(file.name)}</div>
                <div class="text-xs text-muted">${formatFileSize(file.size)} · ${file.name.split('.').pop().toUpperCase()}</div>
            </div>
            <button type="button" onclick="removeFile(${index})" class="btn btn-tertiary btn-sm" style="margin-left: 8px;">
                Remove
            </button>
        </div>
    `).join('');
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    if (selectedFiles.length === 0) {
        clearAllFiles();
    } else {
        showSelectedFiles();
    }
}

function clearAllFiles() {
    selectedFiles = [];
    
    const selectedSection = document.getElementById('selected-files');
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const progressSection = document.getElementById('upload-progress-section');
    
    if (selectedSection) selectedSection.style.display = 'none';
    if (uploadArea) uploadArea.style.opacity = '1';
    if (fileInput) fileInput.value = '';
    if (progressSection) progressSection.style.display = 'none';
}

async function uploadAllFiles() {
    if (selectedFiles.length === 0) return;
    
    const selectedSection = document.getElementById('selected-files');
    const progressSection = document.getElementById('upload-progress-section');
    const progressList = document.getElementById('upload-progress-list');
    const uploadSummary = document.getElementById('upload-summary');
    
    // Hide file selection, show progress
    if (selectedSection) selectedSection.style.display = 'none';
    if (progressSection) progressSection.style.display = 'block';
    if (progressList) progressList.innerHTML = '';
    
    // Reset results
    uploadResults = { completed: 0, failed: 0, total: selectedFiles.length };
    updateUploadSummary();
    
    // Create progress items for all files
    selectedFiles.forEach((file, index) => {
        const progressItem = document.createElement('div');
        progressItem.id = `upload-item-${index}`;
        progressItem.className = 'upload-item';
        progressItem.style.cssText = 'padding: 12px; background: var(--color-gray-100); border-radius: 8px; border-left: 4px solid var(--color-primary);';
        progressItem.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1;">${escapeHtml(file.name)}</span>
                <span class="upload-percent text-sm text-muted" style="margin-left: 8px;">0%</span>
            </div>
            <div style="background: var(--color-gray-200); height: 4px; border-radius: 2px; overflow: hidden;">
                <div class="upload-bar" style="background: var(--color-black); height: 100%; width: 0%; transition: width 0.2s ease;"></div>
            </div>
            <div class="upload-status text-xs text-muted" style="margin-top: 4px;">Waiting...</div>
        `;
        if (progressList) progressList.appendChild(progressItem);
    });
    
    // Upload all files in parallel
    const uploadPromises = selectedFiles.map((file, index) => uploadSingleFile(file, index));
    await Promise.all(uploadPromises);
    
    // Show completion message
    showNotification(`Uploaded ${uploadResults.completed}/${uploadResults.total} files`, 
        uploadResults.failed > 0 ? 'warning' : 'success');
    
    // Reset after delay
    setTimeout(() => {
        clearAllFiles();
        loadDocuments();
    }, 2000);
}

function updateUploadSummary() {
    const summaryEl = document.getElementById('upload-summary');
    if (summaryEl) {
        summaryEl.textContent = `${uploadResults.completed}/${uploadResults.total} completed`;
    }
}

async function uploadSingleFile(file, index) {
    const itemEl = document.getElementById(`upload-item-${index}`);
    const percentEl = itemEl?.querySelector('.upload-percent');
    const barEl = itemEl?.querySelector('.upload-bar');
    const statusEl = itemEl?.querySelector('.upload-status');
    
    try {
        if (statusEl) statusEl.textContent = 'Uploading...';
        
        const formData = new FormData();
        formData.append('file', file);
        
        return new Promise((resolve) => {
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentage = Math.round((e.loaded / e.total) * 100);
                    if (percentEl) percentEl.textContent = `${percentage}%`;
                    if (barEl) barEl.style.width = `${percentage}%`;
                    if (percentage === 100 && statusEl) statusEl.textContent = 'Processing...';
                }
            });
            
            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    try {
                        const result = JSON.parse(xhr.responseText);
                        if (result.success) {
                            if (itemEl) itemEl.style.borderLeftColor = 'var(--color-success, #22c55e)';
                            if (statusEl) statusEl.textContent = `Done · ${result.document?.chunk_count || 0} chunks`;
                            uploadResults.completed++;
                        } else {
                            throw new Error(result.message || 'Upload failed');
                        }
                    } catch (e) {
                        if (itemEl) itemEl.style.borderLeftColor = 'var(--color-error, #ef4444)';
                        if (statusEl) statusEl.textContent = `Error: ${e.message}`;
                        uploadResults.failed++;
                    }
                } else {
                    if (itemEl) itemEl.style.borderLeftColor = 'var(--color-error, #ef4444)';
                    if (statusEl) statusEl.textContent = `Error: HTTP ${xhr.status}`;
                    uploadResults.failed++;
                }
                updateUploadSummary();
                resolve();
            });
            
            xhr.addEventListener('error', () => {
                if (itemEl) itemEl.style.borderLeftColor = 'var(--color-error, #ef4444)';
                if (statusEl) statusEl.textContent = 'Network error';
                uploadResults.failed++;
                updateUploadSummary();
                resolve();
            });
            
            xhr.open('POST', '/documents/upload');
            xhr.send(formData);
        });
        
    } catch (error) {
        console.error('Upload error:', error);
        if (itemEl) itemEl.style.borderLeftColor = 'var(--color-error, #ef4444)';
        if (statusEl) statusEl.textContent = `Error: ${error.message}`;
        uploadResults.failed++;
        updateUploadSummary();
    }
}

// Legacy function aliases for compatibility
function cancelUpload() { clearAllFiles(); }
function uploadWithMetadata() { uploadAllFiles(); }

async function loadDocuments() {
    const listEl = document.getElementById('documents-list');
    if (!listEl) return;
    
    listEl.innerHTML = '<p class="text-center text-muted">Loading documents...</p>';
    
    try {
        const response = await fetch('/documents/list');
        const data = await response.json();
        
        if (data.success && data.documents && data.documents.length > 0) {
            listEl.innerHTML = data.documents.map(doc => `
                <div class="document-item" style="padding: 16px; border-bottom: 1px solid var(--border);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                        <div style="flex: 1;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <strong>${escapeHtml(doc.filename || 'Untitled')}</strong>
                                <span class="badge" style="font-size: 10px;">${doc.file_type || ''}</span>
                            </div>
                            <div class="text-xs text-muted" style="margin-top: 4px;">
                                ${formatFileSize(doc.file_size || 0)} · ${doc.chunk_count || 0} chunks · 
                                ${doc.upload_time ? new Date(doc.upload_time).toLocaleDateString() : ''}
                            </div>
                            ${doc.tags && doc.tags.length > 0 ? `
                                <div style="margin-top: 6px;">
                                    ${doc.tags.map(t => `<span class="badge" style="font-size: 10px; margin-right: 4px;">${escapeHtml(t)}</span>`).join('')}
                                </div>
                            ` : ''}
                        </div>
                        <button onclick="deleteDocument('${doc.id}')" class="btn btn-danger btn-sm">Delete</button>
                    </div>
                </div>
            `).join('');
        } else {
            listEl.innerHTML = '<p class="text-center text-muted p-4">No documents uploaded yet. Upload your first document above.</p>';
        }
    } catch (error) {
        console.error('Error loading documents:', error);
        listEl.innerHTML = '<p class="text-center text-muted p-4">Failed to load documents. Try refreshing.</p>';
    }
}

async function searchDocuments() {
    const query = document.getElementById('doc-search-input')?.value;
    const resultsEl = document.getElementById('search-results');
    if (!query || !resultsEl) return;
    
    resultsEl.innerHTML = '<p class="text-muted">Searching...</p>';
    
    try {
        const response = await fetch(`/documents/search?query=${encodeURIComponent(query)}&limit=5`);
        const data = await response.json();
        
        if (data.success && data.results && data.results.length > 0) {
            resultsEl.innerHTML = data.results.map(r => `
                <div style="text-align: left; padding: 12px; border: 1px solid var(--border); border-radius: 8px; margin-bottom: 8px;">
                    <div class="font-medium">${escapeHtml((r.metadata && r.metadata.filename) || r.filename || 'Document')}</div>
                    <div class="text-sm text-muted mt-1">${escapeHtml(r.content_preview || r.content?.substring(0, 150) || '')}</div>
                    <div class="text-xs text-muted mt-2">Score: ${(r.score * 100).toFixed(1)}%</div>
                </div>
            `).join('');
        } else {
            resultsEl.innerHTML = '<p class="text-muted">No results found.</p>';
        }
    } catch (error) {
        console.error('Search error:', error);
        resultsEl.innerHTML = '<p class="text-muted">Search failed.</p>';
    }
}

window.searchDocuments = searchDocuments;

async function deleteDocument(docId) {
    if (!confirm('Delete this document?')) return;
    
    try {
        const response = await fetch(`/documents/${docId}`, { method: 'DELETE' });
        const data = await response.json();
        if (data.success) {
            showNotification('Document deleted', 'success');
            loadDocuments();
        } else {
            showNotification('Failed to delete document', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('Error deleting document', 'error');
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatFileSize(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function showNotification(message, type) {
    if (typeof Notifications !== 'undefined' && Notifications.show) {
        Notifications.show(message, type);
    } else if (typeof window.showNotification === 'function' && window.showNotification !== showNotification) {
        window.showNotification(message, type);
    } else {
        // Simple fallback
        console.log(`[${type}] ${message}`);
    }
}

// Make functions globally available
window.loadDocuments = loadDocuments;
window.deleteDocument = deleteDocument;
window.uploadWithMetadata = uploadWithMetadata;
window.cancelUpload = cancelUpload;
window.uploadAllFiles = uploadAllFiles;
window.clearAllFiles = clearAllFiles;
window.removeFile = removeFile;

