/**
 * Multiple ESP32S3 Devices Manager
 * Handles scanning, connecting, and managing multiple ESP32S3 devices
 */

console.log('Device manager loading...');

// Global variables for device management
let detectedDevices = [];
let selectedDevice = null;
let isConnected = false;
// Note: selectedRecordings is defined in multi_file_functions.js

// Scan for ESP32S3 devices
async function scanForDevices() {
    const scanButton = document.getElementById('scan-devices-btn');
    const devicesList = document.getElementById('devices-list');
    
    // Show loading state
    if (devicesList) {
    devicesList.innerHTML = '<div class="loading-state">Scanning for ESP32S3 devices...</div>';
    }
    if (scanButton) {
        scanButton.disabled = true;
        scanButton.innerHTML = '<i data-lucide="loader" style="width: 16px; height: 16px; margin-right: 6px; animation: spin 1s linear infinite;"></i>Scanning...';
    }
    
    try {
        console.log('[DEVICES] Fetching devices from: /api/devices/status');
        const response = await fetch('/api/devices/status', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            mode: 'cors'
        });
        
        console.log('Response status:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const text = await response.text();
        let result;
        
        try {
            result = JSON.parse(text);
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            console.error('Response text:', text);
            throw new Error('Invalid response format from server');
        }
        
        if (result.success && result.devices) {
            detectedDevices = result.devices;
            renderDevicesList();
            
            // Only show notification for connected/active devices
            const connectedDevices = detectedDevices.filter(device => device.connected || device.is_active);
            
            if (detectedDevices.length === 0) {
                showNotification('No ESP32S3 devices found. Make sure devices are connected via USB or BLE.', 'info');
            } else if (connectedDevices.length > 0) {
                showNotification(`Found ${connectedDevices.length} Brutally Honest AI device(s) connected!`, 'success');
            }
        } else {
            if (devicesList) {
            devicesList.innerHTML = '<div class="empty-state">Failed to scan for devices. Check your connection.</div>';
            }
            showNotification('Failed to scan for devices.', 'error');
        }
        
    } catch (error) {
        console.error('Device scan error:', error);
        if (devicesList) {
        devicesList.innerHTML = '<div class="empty-state">Error scanning for devices. Please try again.</div>';
        }
        showNotification(`Error scanning for devices: ${error.message}`, 'error');
    } finally {
        // Restore scan button
        if (scanButton) {
            scanButton.disabled = false;
            scanButton.innerHTML = '<i data-lucide="search" style="width: 16px; height: 16px; margin-right: 6px;"></i>Scan for Devices';
        }
        lucide.createIcons();
    }
}

// Render the list of detected devices
function renderDevicesList() {
    const devicesList = document.getElementById('devices-list');
    
    // Guard against null element (page may not have devices-list)
    if (!devicesList) {
        console.log('[DEVICES] devices-list element not found on this page');
        return;
    }
    
    if (detectedDevices.length === 0) {
        devicesList.innerHTML = '<div class="empty-state">No ESP32S3 devices detected. Connect your devices and scan again.</div>';
        return;
    }
    
    const devicesHTML = detectedDevices.map((device, index) => {
        const isSelected = selectedDevice && selectedDevice.device_id === device.device_id;
        const isActive = device.is_active;
        const statusClass = device.connected ? (device.recording ? 'recording' : 'connected') : 'disconnected';
        const statusText = device.connected ? (device.recording ? 'Recording' : 'Connected') : 'Disconnected';
        const deviceTypeIcon = device.device_type === 'BLE' ? 'bluetooth' : 'usb';
        
        return `
            <div class="device-item ${isSelected ? 'selected' : ''} ${isActive ? 'active' : ''}" onclick="selectDevice(${index})">
                <div class="device-header">
                    <div class="device-name">
                        <i data-lucide="${deviceTypeIcon}" style="width: 14px; height: 14px; margin-right: 6px;"></i>
                        ${device.description || 'ESP32S3 Device'}
                        ${isActive ? '<span class="active-badge">ACTIVE</span>' : ''}
                    </div>
                    <div class="device-status-badge ${statusClass}">${statusText}</div>
                </div>
                <div class="device-details">
                    <div class="device-port">${device.device_type}: ${device.port}</div>
                    <div class="device-stats">
                        <span>Files: ${device.recordings || 0}</span>
                        <span>Battery: ${device.battery || 'Unknown'}</span>
                        <span>RAM: ${device.free_ram || 'Unknown'}</span>
                        <span>Confidence: ${device.confidence}%</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    devicesList.innerHTML = devicesHTML;
    
    // Refresh Lucide icons
    lucide.createIcons();
}

// Select a device for interaction
function selectDevice(deviceIndex) {
    if (deviceIndex < 0 || deviceIndex >= detectedDevices.length) return;
    
    selectedDevice = detectedDevices[deviceIndex];
    
    // Update visual selection
    renderDevicesList();
    
    // Connect to the selected device
    connectToSelectedDevice();
}

// Connect to device (called by CTA button)
async function connectToDevice() {
    // Open the device selection modal
    openDeviceModal();
}

// Make functions globally accessible
window.connectToDevice = connectToDevice;
window.openDeviceModal = openDeviceModal;
window.closeDeviceModal = closeDeviceModal;
window.scanForDevices = scanForDevices;
window.scanForDevicesInModal = scanForDevicesInModal;
window.selectDevice = selectDevice;
window.selectDeviceFromModal = selectDeviceFromModal;
// toggleRecordingSelection now handled by multi_file_functions.js
window.selectAllRecordings = selectAllRecordings;
window.selectNoneRecordings = selectNoneRecordings;
window.bulkDownloadRecordings = bulkDownloadRecordings;
// Removed bulkProcessWithAI export
window.bulkDeleteRecordings = bulkDeleteRecordings;
window.refreshRecordings = refreshRecordings;
window.renderRecordingsList = renderRecordingsList;
window.loadDeviceRecordings = loadDeviceRecordings;

// New functions for device selection workflow
window.refreshDeviceSelection = refreshDeviceSelection;
window.changeSelectedDevice = changeSelectedDevice;
window.selectDeviceForStatus = selectDeviceForStatus;

// Open device selection modal
function openDeviceModal() {
    const modal = document.getElementById('device-modal');
    modal.style.display = 'flex';
    
    // Auto-scan for devices when modal opens
    scanForDevicesInModal();
}

// Close device selection modal
function closeDeviceModal() {
    const modal = document.getElementById('device-modal');
    modal.style.display = 'none';
}

// Close modal when clicking outside
document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('device-modal');
    if (modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeDeviceModal();
            }
        });
    }
});

// Scan for devices in modal
async function scanForDevicesInModal() {
    const modalDevicesList = document.getElementById('modal-devices-list');
    const scanButton = document.getElementById('scan-devices-modal-btn');
    
    // Show loading state
    if (scanButton) {
        scanButton.disabled = true;
        scanButton.innerHTML = '<i data-lucide="loader-2" style="width: 16px; height: 16px; margin-right: 6px; animation: spin 1s linear infinite;"></i>Scanning...';
    }
    devicesList.innerHTML = '<div class="devices-empty"><span class="loading-dots">Scanning for devices...</span></div>';
    
    try {
        console.log('[DEVICES] Modal: Fetching devices from: /api/devices/status');
        const response = await fetch('/api/devices/status', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            mode: 'cors'
        });
        
        console.log('Modal: Response status:', response.status, response.statusText);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const text = await response.text();
        let data;
        
        try {
            data = JSON.parse(text);
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            console.error('Response text:', text);
            throw new Error('Invalid response format from server');
        }
        
        if (data.success && data.devices) {
            detectedDevices = data.devices;
            renderModalDevicesList();
            
            // Only show notification for connected/active devices
            const connectedDevices = detectedDevices.filter(device => device.connected || device.is_active);
            
            if (detectedDevices.length === 0) {
                showNotification('No ESP32S3 devices found. Please connect your device via USB and try scanning again.', 'info');
            } else if (connectedDevices.length > 0) {
                showNotification(`Found ${connectedDevices.length} Brutally Honest AI device(s) ready to use!`, 'success');
            }
        } else {
            throw new Error(data.error || 'Failed to scan devices');
        }
        
    } catch (error) {
        console.error('Device scan error:', error);
        showNotification(`Scan failed: ${error.message}`, 'error');
        devicesList.innerHTML = `
            <div class="devices-empty">
                <i data-lucide="alert-circle" style="width: 48px; height: 48px; margin-bottom: 15px; color: #ff6b6b;"></i>
                <p>Scan failed</p>
                <p style="font-size: 12px; color: #999;">${error.message}</p>
            </div>
        `;
    } finally {
        // Reset scan button
        if (scanButton) {
            scanButton.disabled = false;
            scanButton.innerHTML = '<i data-lucide="search" style="width: 16px; height: 16px; margin-right: 6px;"></i>Scan for Devices';
        }
        lucide.createIcons();
    }
}

// Render devices list in modal
function renderModalDevicesList() {
    const modalDevicesList = document.getElementById('modal-devices-list');
    
    if (detectedDevices.length === 0) {
        devicesList.innerHTML = `
            <div class="devices-empty">
                <i data-lucide="usb" style="width: 48px; height: 48px; margin-bottom: 15px; color: #ccc;"></i>
                <p>No ESP32S3 devices detected</p>
                <p style="font-size: 12px; color: #999;">Connect your ESP32S3 device via USB and click "Scan for Devices"</p>
            </div>
        `;
        return;
    }
    
    const devicesHTML = detectedDevices.map((device, index) => {
        const isSelected = selectedDevice && selectedDevice.device_id === device.device_id;
        const isActive = device.is_active;
        const deviceTypeIcon = device.device_type === 'BLE' ? 'bluetooth' : 'usb';
        
        return `
        <div class="device-item ${isSelected ? 'selected' : ''} ${isActive ? 'active' : ''}" 
             onclick="selectDeviceFromModal(${index})">
            <div class="device-header">
                <div class="device-name">
                    <i data-lucide="${deviceTypeIcon}" style="width: 16px; height: 16px; margin-right: 8px;"></i>
                    ${device.description || 'ESP32S3 Device'}
                    ${isActive ? '<span class="active-badge">ACTIVE</span>' : ''}
                </div>
                <div class="device-status">
                    <span class="status-badge ${device.connected ? 'connected' : 'disconnected'}">
                        ${device.connected ? 'Available' : 'Disconnected'}
                    </span>
                </div>
            </div>
            <div class="device-details">
                <div class="device-port">${device.device_type}: ${device.port}</div>
                <div class="device-stats">
                    <span><i data-lucide="battery" style="width: 14px; height: 14px; margin-right: 4px;"></i>${device.battery}</span>
                    <span><i data-lucide="folder" style="width: 14px; height: 14px; margin-right: 4px;"></i>${device.recordings} files</span>
                    <span><i data-lucide="signal" style="width: 14px; height: 14px; margin-right: 4px;"></i>${device.confidence}% match</span>
                </div>
            </div>
        </div>
        `;
    }).join('');
    
    devicesList.innerHTML = devicesHTML;
    
    // Refresh Lucide icons
    lucide.createIcons();
}

// Select device from modal and connect
function selectDeviceFromModal(deviceIndex) {
    if (deviceIndex < 0 || deviceIndex >= detectedDevices.length) return;
    
    selectedDevice = detectedDevices[deviceIndex];
    
    // Update visual selection
    renderModalDevicesList();
    
    // Connect to the selected device
    connectToSelectedDevice();
    
    // Close modal after selection
    setTimeout(() => {
        closeDeviceModal();
    }, 500);
}

// Connect to the currently selected device
async function connectToSelectedDevice() {
    if (!selectedDevice) return;
    
    const connectBtn = document.getElementById('connect-cta');
    const connectText = document.getElementById('connect-text');
    
    // Update button to loading state
    connectBtn.disabled = true;
    connectText.textContent = 'Connecting...';
    
    try {
        // Attempt connection using new multi-device API
        const response = await fetch(`/api/devices/connect/${encodeURIComponent(selectedDevice.device_id)}`, { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            // Connection successful
            isConnected = true;
            selectedDevice.connected = true;
            selectedDevice.is_active = true;
            updateConnectionUI(true);
            
            // Show recordings section
            const recordingsSection = document.getElementById('recordings-section');
            recordingsSection.style.display = 'block';
            
            // Show AI Transcription section
            const aiSection = document.getElementById('ai-transcription-section');
            aiSection.style.display = 'block';
            
            // Load recordings for selected device
            loadDeviceRecordings(selectedDevice.device_id);
            
            // Refresh device list to show updated status
            renderDevicesList();
            
            showNotification(`Connected to ${selectedDevice.description}!`, 'success');
        } else {
            throw new Error(result.message || 'Connection failed');
        }
        
    } catch (error) {
        console.error('Connection error:', error);
        showNotification(`Failed to connect: ${error.message}`, 'error');
        updateConnectionUI(false);
    } finally {
        connectBtn.disabled = false;
    }
}

// Update connection UI elements
function updateConnectionUI(connected) {
    const connectBtn = document.getElementById('connect-cta');
    const connectText = document.getElementById('connect-text');
    const statusBar = document.getElementById('connection-status-bar');
    const aiSection = document.getElementById('ai-transcription-section');
    
    if (connected && selectedDevice) {
        // Connected state
        connectBtn.classList.add('connected');
        connectText.textContent = 'Connected';
        statusBar.style.display = 'flex';
        aiSection.style.display = 'block';
        
        // Update status bar info
        document.getElementById('connected-device-name').textContent = selectedDevice.description || 'ESP32S3 Device';
        document.getElementById('battery-status').textContent = selectedDevice.battery || 'Unknown';
        document.getElementById('files-count').textContent = `${selectedDevice.recordings || 0} files`;
        
        // Update icon (if it exists)
        const icon = connectBtn.querySelector('i');
        if (icon) {
            icon.setAttribute('data-lucide', 'check-circle');
        }
        
    } else {
        // Disconnected state
        connectBtn.classList.remove('connected');
        connectText.textContent = 'Connect Device';
        statusBar.style.display = 'none';
        aiSection.style.display = 'none';
        
        // Update icon (if it exists)
        const icon = connectBtn.querySelector('i');
        if (icon) {
            icon.setAttribute('data-lucide', 'usb');
        }
    }
    
    // Refresh Lucide icons
    lucide.createIcons();
}

// Load recordings from the selected device
async function loadDeviceRecordings(deviceId) {
    const recordingsList = document.getElementById('recordings-list');
    recordingsList.innerHTML = '<div class="recordings-empty"><span class="loading-dots">Loading recordings...</span></div>';
    
    try {
        // Select the device first to make it active
        await selectActiveDevice(deviceId);
        
        // Then get recordings from the active device
        const response = await fetch('http://localhost:8000/device/recordings');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const text = await response.text();
        let result;
        
        try {
            result = JSON.parse(text);
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            console.error('Response text:', text);
            throw new Error('Invalid response format from server');
        }
        
        if (result.success && result.recordings) {
            renderRecordingsList(result.recordings);
        } else {
            recordingsList.innerHTML = '<div class="recordings-empty">No recordings found on this device.</div>';
        }
        
    } catch (error) {
        console.error('Error loading device recordings:', error);
        recordingsList.innerHTML = '<div class="recordings-empty">Error loading recordings from device.</div>';
    }
}

// Select a device as the active device on the backend
async function selectActiveDevice(deviceId) {
    try {
        const response = await fetch(`/api/devices/select/${encodeURIComponent(deviceId)}`, { method: 'POST' });
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.message || 'Failed to select device');
        }
        
        console.log(`Selected device as active: ${deviceId}`);
        return true;
    } catch (error) {
        console.error('Error selecting active device:', error);
        throw error;
    }
}

// Render recordings list (reuse existing function but adapt for selected device)
function renderRecordingsList(recordings) {
    const recordingsList = document.getElementById('recordings-list');
    
    if (recordings.length === 0) {
        recordingsList.innerHTML = '<div class="recordings-empty">No recordings found on this device.</div>';
        return;
    }
    
    // Add select all/none controls and bulk actions
    const selectAllHTML = `
        <div class="select-controls">
            <div class="select-buttons">
                <button class="btn btn-select-all" onclick="selectAllRecordings()">
                    <i data-lucide="check-square" style="width: 14px; height: 14px; margin-right: 6px;"></i>
                    Select All
                </button>
                <button class="btn btn-select-none" onclick="selectNoneRecordings()">
                    <i data-lucide="square" style="width: 14px; height: 14px; margin-right: 6px;"></i>
                    Select None
                </button>
            </div>
            <span class="selected-count" id="selected-count">0 selected</span>
        </div>
        <div class="bulk-actions" id="bulk-actions" style="display: none;">
            <button class="btn btn-bulk-download" onclick="bulkDownloadRecordings()">
                <i data-lucide="download" style="width: 14px; height: 14px; margin-right: 6px;"></i>
                Download Selected
            </button>
            <button class="btn btn-bulk-delete" onclick="bulkDeleteRecordings()">
                <i data-lucide="trash-2" style="width: 14px; height: 14px; margin-right: 6px;"></i>
                Delete Selected
            </button>
        </div>
    `;
    
    // Render recordings with checkboxes
    const recordingsHTML = recordings.map(recording => {
        const safeId = createSafeId(recording.name);
        return `
        <div class="recording-card">
            <div class="recording-content">
                <div class="recording-header">
                    <div class="recording-name">
                        <i data-lucide="file-audio" style="width: 14px; height: 14px; margin-right: 6px;"></i>
                        ${recording.name}
                    </div>
                    <div class="recording-size">${(recording.size / 1024 / 1024).toFixed(2)} MB</div>
                </div>
                <div class="recording-actions">
                    <button class="btn-mini recording-select-btn" id="select-${recording.name}" onclick="toggleRecordingSelection('${recording.name}', ${(recording.size / 1024 / 1024).toFixed(2)})" title="Toggle Selection">
                        <i data-lucide="plus" style="width: 16px; height: 16px;"></i>
                    </button>
                    <button class="btn btn-download" onclick="downloadRecording('${recording.name}')">
                        <i data-lucide="download" style="width: 14px; height: 14px; margin-right: 4px;"></i>
                        Download
                    </button>
                    <button class="btn btn-delete" onclick="deleteRecording('${recording.name}')">
                        <i data-lucide="trash-2" style="width: 14px; height: 14px; margin-right: 4px;"></i>
                        Delete
                    </button>
                </div>
            </div>
        </div>
        `;
    }).join('');
    
    recordingsList.innerHTML = selectAllHTML + recordingsHTML;
    
    // Update selected count
    updateSelectedCount();
    
    // Refresh Lucide icons
    lucide.createIcons();
}

// Create a safe ID from recording name
function createSafeId(recordingName) {
    return 'rec-' + recordingName.replace(/[^a-zA-Z0-9-_]/g, '_');
}

// Note: toggleRecordingSelection is now handled by multi_file_functions.js for AI processing

// Select all recordings
function selectAllRecordings() {
    const checkboxes = document.querySelectorAll('.recording-card input[type="checkbox"][data-recording-name]');
    checkboxes.forEach(checkbox => {
        const recordingName = checkbox.getAttribute('data-recording-name');
        if (recordingName) {
            // Use the selectedRecordings from multi_file_functions.js (it's a Map)
            if (typeof selectedRecordings !== 'undefined') {
                selectedRecordings.set(recordingName, {name: recordingName, size_mb: 0});
            }
            checkbox.checked = true;
            checkbox.closest('.recording-card').classList.add('selected');
        }
    });
    updateSelectedCount();
}

// Select none recordings
function selectNoneRecordings() {
    const checkboxes = document.querySelectorAll('.recording-card input[type="checkbox"][data-recording-name]');
    checkboxes.forEach(checkbox => {
        const recordingName = checkbox.getAttribute('data-recording-name');
        if (recordingName) {
            // Use the selectedRecordings from multi_file_functions.js (it's a Map)
            if (typeof selectedRecordings !== 'undefined') {
                selectedRecordings.delete(recordingName);
            }
            checkbox.checked = false;
            checkbox.closest('.recording-card').classList.remove('selected');
        }
    });
    updateSelectedCount();
}

// Update selected count display
function updateSelectedCount() {
    const countElement = document.getElementById('selected-count');
    if (countElement) {
        // Use the selectedRecordings from multi_file_functions.js (it's a Map)
        const count = (typeof selectedRecordings !== 'undefined') ? selectedRecordings.size : 0;
        countElement.textContent = `${count} selected`;
        
        // Show/hide bulk actions based on selection
        updateBulkActions(count > 0);
    }
}

// Update bulk actions visibility
function updateBulkActions(hasSelection) {
    const bulkActions = document.getElementById('bulk-actions');
    if (bulkActions) {
        bulkActions.style.display = hasSelection ? 'flex' : 'none';
    }
}

// Bulk action functions
function bulkDownloadRecordings() {
    // Use the selectedRecordings from multi_file_functions.js (it's a Map)
    const recordings = (typeof selectedRecordings !== 'undefined') ? selectedRecordings : new Map();
    
    if (recordings.size === 0) {
        showNotification('No recordings selected', 'error');
        return;
    }
    
    recordings.forEach((recording, recordingName) => {
        downloadRecording(recordingName);
    });
    
    showNotification(`Downloading ${recordings.size} recordings...`, 'success');
}

// Removed bulkProcessWithAI - use main AI Analysis section instead

function bulkDeleteRecordings() {
    // Use the selectedRecordings from multi_file_functions.js (it's a Map)
    const recordings = (typeof selectedRecordings !== 'undefined') ? selectedRecordings : new Map();
    
    if (recordings.size === 0) {
        showNotification('No recordings selected', 'error');
        return;
    }
    
    if (confirm(`Are you sure you want to delete ${recordings.size} selected recordings? This action cannot be undone.`)) {
        const recordingsToDelete = Array.from(recordings.keys());
        recordingsToDelete.forEach(recordingName => {
            deleteRecording(recordingName);
        });
        
        // Clear selection after deletion
        if (typeof selectedRecordings !== 'undefined') {
            selectedRecordings.clear();
        }
        updateSelectedCount();
        
        showNotification(`Deleting ${recordingsToDelete.length} recordings...`, 'success');
    }
}

// Refresh recordings for the selected device
async function refreshRecordings() {
    if (!selectedDevice) {
        showNotification('Please select a device first.', 'error');
        return;
    }
    
    await loadDeviceRecordings(selectedDevice.port);
}

// Auto-scan for devices on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener for connect button
    const connectButton = document.getElementById('connect-cta');
    if (connectButton) {
        connectButton.addEventListener('click', connectToDevice);
    }
    
    // Add event listener for scan devices modal button
    const scanModalButton = document.getElementById('scan-devices-modal-btn');
    if (scanModalButton) {
        scanModalButton.addEventListener('click', scanForDevicesInModal);
    }
    
    // Add event listener for modal close button
    const modalCloseButton = document.getElementById('modal-close-btn');
    if (modalCloseButton) {
        modalCloseButton.addEventListener('click', closeDeviceModal);
    }
    
    // Add event listener for main scan devices button
    const scanDevicesButton = document.getElementById('scan-devices-btn');
    if (scanDevicesButton) {
        scanDevicesButton.addEventListener('click', scanForDevices);
    }
    
    // Auto-scan after a short delay
    setTimeout(() => {
        scanForDevices();
    }, 1000);
});

// Notification function - uses global notification system from home.js
function showNotification(message, type = 'info') {
    // Use global notification system if available
    if (typeof window.showNotification === 'function' && window.showNotification !== showNotification) {
        window.showNotification(message, type);
        return;
    }
    
    // Fallback: use addNotification from home.js if available
    if (typeof window.addNotification === 'function') {
        window.addNotification(type, message);
        return;
    }
    
    // Last resort fallback - simple alert-style notification
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Add CSS for spinner animation and multi-device styles
const devicesStyle = document.createElement('style');
devicesStyle.textContent = `
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .device-item.active {
        border: 2px solid #10B981;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05));
    }
    
    .active-badge {
        background: #10B981;
        color: white;
        font-size: 10px;
        padding: 2px 6px;
        border-radius: 4px;
        margin-left: 8px;
        font-weight: 600;
    }
    
    .device-item.active .device-name {
        color: #10B981;
        font-weight: 600;
    }
    
    .device-item .device-stats span {
        font-size: 11px;
        color: #666;
        margin-right: 8px;
    }
    
    .device-item .device-stats span:last-child {
        margin-right: 0;
    }
`;
document.head.appendChild(devicesStyle);

// New functions for device selection workflow

// Refresh device selection (alias for scanForDevices)
async function refreshDeviceSelection() {
    await scanForDevices();
}

// Change selected device (show device selection section)
function changeSelectedDevice() {
    // Hide device status section
    const deviceStatusSection = document.getElementById('device-status-section');
    if (deviceStatusSection) {
        deviceStatusSection.style.display = 'none';
    }
    
    // Show device selection section
    const deviceSelectionSection = document.getElementById('device-selection-section');
    if (deviceSelectionSection) {
        deviceSelectionSection.style.display = 'block';
    }
    
    // Refresh device list
    scanForDevices();
}

// Select device for status monitoring (enhanced selectDevice for main page)
async function selectDeviceForStatus(deviceIndex) {
    if (deviceIndex < 0 || deviceIndex >= detectedDevices.length) return;
    
    const device = detectedDevices[deviceIndex];
    selectedDevice = device;
    
    try {
        // Connect to the device
        const response = await fetch(`/api/devices/connect/${encodeURIComponent(device.device_id)}`, { method: 'POST' });
        const result = await response.json();
        
        if (result.success) {
            // Update device as connected and active
            device.connected = true;
            device.is_active = true;
            
            // Update selected device info
            updateSelectedDeviceInfo(device);
            
            // Show device status section
            showDeviceStatusSection();
            
            // Start device monitoring
            startDeviceMonitoring();
            
            // Refresh device list to show updated status
            renderDevicesList();
            
            showNotification(`Connected to ${device.description}!`, 'success');
        } else {
            throw new Error(result.message || 'Connection failed');
        }
        
    } catch (error) {
        console.error('Connection error:', error);
        showNotification(`Failed to connect: ${error.message}`, 'error');
    }
}

// Update selected device info display
function updateSelectedDeviceInfo(device) {
    const selectedDeviceInfo = document.getElementById('selected-device-info');
    const selectedDeviceName = document.getElementById('selected-device-name');
    const selectedDeviceType = document.getElementById('selected-device-type');
    const selectedDevicePort = document.getElementById('selected-device-port');
    const selectedDeviceStatus = document.getElementById('selected-device-status');
    
    if (selectedDeviceInfo && selectedDeviceName && selectedDeviceType && selectedDevicePort && selectedDeviceStatus) {
        selectedDeviceName.textContent = device.description || 'ESP32S3 Device';
        selectedDeviceType.textContent = device.device_type;
        selectedDevicePort.textContent = device.port;
        selectedDeviceStatus.textContent = device.connected ? 'Connected' : 'Disconnected';
        
        selectedDeviceInfo.style.display = 'block';
    }
}

// Show device status section
function showDeviceStatusSection() {
    const deviceSelectionSection = document.getElementById('device-selection-section');
    const deviceStatusSection = document.getElementById('device-status-section');
    
    if (deviceSelectionSection) {
        deviceSelectionSection.style.display = 'none';
    }
    
    if (deviceStatusSection) {
        deviceStatusSection.style.display = 'block';
    }
}

// Override the original selectDevice function to use the new workflow
function selectDevice(deviceIndex) {
    selectDeviceForStatus(deviceIndex);
}

console.log('Device manager loaded successfully');

// Start device monitoring after device selection
function startDeviceMonitoring() {
    // Call the main page functions to start monitoring the selected device
    if (typeof refreshRecordings === 'function') {
        refreshRecordings();
        
        // Set up periodic refresh for recordings (every 30 seconds)
        setInterval(() => {
            const deviceStatusSection = document.getElementById('device-status-section');
            if (deviceStatusSection && deviceStatusSection.style.display !== 'none') {
                refreshRecordings();
            }
        }, 30000);
    }
    
    if (typeof updateDeviceInfo === 'function') {
        updateDeviceInfo();
        
        // Set up periodic refresh for device info (every 10 seconds)
        setInterval(() => {
            const deviceStatusSection = document.getElementById('device-status-section');
            if (deviceStatusSection && deviceStatusSection.style.display !== 'none') {
                updateDeviceInfo();
            }
        }, 10000);
    }
}
