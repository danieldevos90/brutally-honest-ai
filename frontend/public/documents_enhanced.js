// Enhanced Documents Page JavaScript with Profile Linking and Better UX
// To be integrated into documents.html

const API_BASE = 'http://localhost:8000';
let selectedFiles = [];
let availableProfiles = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    setupFileUpload();
    loadProfiles();
    loadDocuments();
});

// Load all profiles for linking
async function loadProfiles() {
    try {
        const [clients, brands, persons] = await Promise.all([
            fetch(`${API_BASE}/profiles/clients`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/brands`).then(r => r.json()),
            fetch(`${API_BASE}/profiles/persons`).then(r => r.json())
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
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
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
    document.getElementById('metadata-form').style.display = 'block';
    document.getElementById('upload-area').style.opacity = '0.5';
    
    // Update form title with file count
    const fileCount = selectedFiles.length;
    const title = document.querySelector('#metadata-form h3');
    title.textContent = `Add Metadata for ${fileCount} Document${fileCount > 1 ? 's' : ''}`;
    
    lucide.createIcons();
}

function cancelUpload() {
    selectedFiles = [];
    document.getElementById('metadata-form').style.display = 'none';
    document.getElementById('upload-area').style.opacity = '1';
    document.getElementById('file-input').value = '';
    
    // Clear form
    document.getElementById('doc-tags').value = '';
    document.getElementById('doc-category').value = '';
    document.getElementById('doc-context').value = '';
    document.getElementById('doc-profiles').selectedIndex = -1;
}

async function uploadWithMetadata() {
    if (selectedFiles.length === 0) return;
    
    const tags = document.getElementById('doc-tags').value;
    const category = document.getElementById('doc-category').value;
    const context = document.getElementById('doc-context').value;
    const profileSelect = document.getElementById('doc-profiles');
    const selectedProfiles = Array.from(profileSelect.selectedOptions).map(o => o.value);
    
    // Hide form, show progress
    document.getElementById('metadata-form').style.display = 'none';
    const progressDiv = document.getElementById('upload-progress');
    progressDiv.style.display = 'block';
    
    for (let i = 0; i < selectedFiles.length; i++) {
        const file = selectedFiles[i];
        await uploadSingleFile(file, tags, category, context, selectedProfiles, i + 1, selectedFiles.length);
    }
    
    // Reset
    progressDiv.style.display = 'none';
    document.getElementById('upload-area').style.opacity = '1';
    cancelUpload();
    
    // Reload documents
    setTimeout(() => loadDocuments(), 1000);
}

async function uploadSingleFile(file, tags, category, context, profiles, current, total) {
    const statusSpan = document.getElementById('upload-status');
    const percentageSpan = document.getElementById('upload-percentage');
    const progressBar = document.getElementById('progress-bar');
    
    try {
        statusSpan.textContent = `Uploading ${current}/${total}: ${file.name}...`;
        
        const formData = new FormData();
        formData.append('file', file);
        if (tags) formData.append('tags', tags);
        if (category) formData.append('category', category);
        if (context) formData.append('context', context);
        
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentage = Math.round((e.loaded / e.total) * 100);
                percentageSpan.textContent = `${percentage}%`;
                progressBar.style.width = `${percentage}%`;
            }
        });
        
        xhr.open('POST', `${API_BASE}/documents/upload`);
        
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
    // This would load and display uploaded documents
    // Placeholder for now
    console.log('Loading documents...');
}

function showNotification(message, type) {
    if (typeof Notifications !== 'undefined') {
        Notifications.show(message, type);
    } else {
        alert(message);
    }
}

