// Enhanced Documents Page JavaScript with Profile Linking and Better UX
// Uses relative URLs to work through the Node.js proxy in production

let selectedFiles = [];
let availableProfiles = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    if (typeof lucide !== 'undefined') lucide.createIcons();
    setupFileUpload();
    loadProfiles();
    loadDocuments();
});

// Load all profiles for linking
async function loadProfiles() {
    try {
        const [clients, brands, persons] = await Promise.all([
            fetch('/api/profiles/clients').then(r => r.json()),
            fetch('/api/profiles/brands').then(r => r.json()),
            fetch('/api/profiles/persons').then(r => r.json())
        ]);
        
        availableProfiles = [
            ...(clients.profiles || []).map(p => ({...p, type: 'client'})),
            ...(brands.profiles || []).map(p => ({...p, type: 'brand'})),
            ...(persons.profiles || []).map(p => ({...p, type: 'person'}))
        ];
        
        populateProfileSelect();
    } catch (error) {
        console.error('Error loading profiles:', error);
    }
}

function populateProfileSelect() {
    const select = document.getElementById('doc-profiles');
    if (!select) return;
    
    select.innerHTML = '';
    
    if (availableProfiles.length === 0) {
        select.innerHTML = '<option disabled>No profiles available. Create profiles first.</option>';
        return;
    }
    
    availableProfiles.forEach(profile => {
        const option = document.createElement('option');
        option.value = profile.id;
        option.textContent = `[${profile.type.toUpperCase()}] ${profile.name}`;
        select.appendChild(option);
    });
}

function setupFileUpload() {
    // Support both class-based and ID-based upload areas
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
    
    // File input
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

function handleFiles(files) {
    if (files.length === 0) return;
    
    const supportedTypes = ['.txt', '.pdf', '.doc', '.docx'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    selectedFiles = [];
    
    for (let file of files) {
        const extension = '.' + file.name.split('.').pop().toLowerCase();
        if (!supportedTypes.includes(extension)) {
            alert(`Unsupported file type: ${file.name}`);
            continue;
        }
        
        if (file.size > maxSize) {
            alert(`File too large: ${file.name}. Max 10MB`);
            continue;
        }
        
        selectedFiles.push(file);
    }
    
    if (selectedFiles.length > 0) {
        showMetadataForm();
    }
}

function showMetadataForm() {
    const metadataForm = document.getElementById('metadata-form');
    const uploadArea = document.querySelector('.file-upload') || document.getElementById('upload-area');
    
    if (metadataForm) metadataForm.style.display = 'block';
    if (uploadArea) uploadArea.style.opacity = '0.5';
    
    // Update form title with file count if title element exists
    const fileCount = selectedFiles.length;
    const title = document.querySelector('#metadata-form h3');
    if (title) {
        title.textContent = `Add Metadata for ${fileCount} Document${fileCount > 1 ? 's' : ''}`;
    }
    
    if (typeof lucide !== 'undefined') lucide.createIcons();
}

function cancelUpload() {
    selectedFiles = [];
    
    const metadataForm = document.getElementById('metadata-form');
    const uploadArea = document.querySelector('.file-upload') || document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    if (metadataForm) metadataForm.style.display = 'none';
    if (uploadArea) uploadArea.style.opacity = '1';
    if (fileInput) fileInput.value = '';
    
    // Clear form fields if they exist
    const docTags = document.getElementById('doc-tags');
    const docCategory = document.getElementById('doc-category');
    const docContext = document.getElementById('doc-context');
    const docProfiles = document.getElementById('doc-profiles');
    
    if (docTags) docTags.value = '';
    if (docCategory) docCategory.value = '';
    if (docContext) docContext.value = '';
    if (docProfiles) docProfiles.selectedIndex = -1;
}

async function uploadWithMetadata() {
    if (selectedFiles.length === 0) return;
    
    const docTags = document.getElementById('doc-tags');
    const docCategory = document.getElementById('doc-category');
    const docContext = document.getElementById('doc-context');
    const profileSelect = document.getElementById('doc-profiles');
    
    const tags = docTags ? docTags.value : '';
    const category = docCategory ? docCategory.value : '';
    const context = docContext ? docContext.value : '';
    const selectedProfiles = profileSelect ? Array.from(profileSelect.selectedOptions).map(o => o.value) : [];
    
    // Hide form, show progress
    const metadataForm = document.getElementById('metadata-form');
    const progressDiv = document.getElementById('upload-progress');
    const uploadArea = document.querySelector('.file-upload') || document.getElementById('upload-area');
    
    if (metadataForm) metadataForm.style.display = 'none';
    if (progressDiv) progressDiv.style.display = 'block';
    
    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        await uploadSingleFile(file, tags, category, context, selectedProfiles, i + 1, selectedFiles.length);
    }
    
    // Reset
    if (progressDiv) progressDiv.style.display = 'none';
    if (uploadArea) uploadArea.style.opacity = '1';
    cancelUpload();
    
    // Reload documents
    setTimeout(() => loadDocuments(), 1000);
}

async function uploadSingleFile(file, tags, category, context, profiles, current, total) {
    const statusSpan = document.getElementById('upload-status');
    const percentageSpan = document.getElementById('upload-percentage');
    const progressBar = document.getElementById('progress-bar');
    
    try {
        if (statusSpan) statusSpan.textContent = `Uploading ${current}/${total}: ${file.name}...`;
        
        const formData = new FormData();
        formData.append('file', file);
        if (tags) formData.append('tags', tags);
        if (category) formData.append('category', category);
        if (context) formData.append('context', context);
        
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentage = Math.round((e.loaded / e.total) * 100);
                if (percentageSpan) percentageSpan.textContent = `${percentage}%`;
                if (progressBar) progressBar.style.width = `${percentage}%`;
            }
        });
        
        xhr.open('POST', '/documents/upload');
        
        await new Promise((resolve, reject) => {
            xhr.onload = () => {
                if (xhr.status === 200) {
                    const result = JSON.parse(xhr.responseText);
                    showNotification(`[OK] Uploaded: ${file.name}`, 'success');
                    resolve(result);
                } else {
                    reject(new Error(`Upload failed: ${xhr.status}`));
                }
            };
            xhr.onerror = () => reject(new Error('Upload failed'));
            xhr.send(formData);
        });
        
    } catch (error) {
        console.error('Upload error:', error);
        showNotification(`[ERROR] Failed to upload ${file.name}`, 'error');
    }
}

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
                    <div class="font-medium">${escapeHtml(r.filename || 'Document')}</div>
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

