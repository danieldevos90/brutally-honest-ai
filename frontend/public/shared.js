// Shared JavaScript functionality for Brutally Honest AI

// API Base URL
const API_BASE = 'http://localhost:8000';

// ============================================
// USER MENU FUNCTIONS
// ============================================

function toggleUserMenu() {
    const dropdown = document.getElementById('user-dropdown');
    if (dropdown) {
        dropdown.classList.toggle('show');
    }
}

async function logout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch (e) {
        console.error('Logout error:', e);
    }
    window.location.href = '/login';
}

async function loadUserInfo() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();
        if (data.authenticated && data.user) {
            const currentUserEl = document.getElementById('current-user');
            const userEmailEl = document.getElementById('user-email');
            if (currentUserEl) currentUserEl.textContent = data.user.name || 'Account';
            if (userEmailEl) userEmailEl.textContent = data.user.email;
            
            // Store user role for other scripts to use
            window.currentUser = data.user;
            
            // Show/hide admin-only elements
            if (data.user.role === 'admin') {
                document.querySelectorAll('.admin-only').forEach(el => {
                    el.style.display = '';
                });
                // Specifically show deploy nav link
                const deployNav = document.getElementById('nav-deploy');
                if (deployNav) deployNav.style.display = '';
            } else {
                document.querySelectorAll('.admin-only').forEach(el => {
                    el.style.display = 'none';
                });
            }
        }
    } catch (e) {
        console.error('Error loading user info:', e);
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.user-menu')) {
        const dropdown = document.getElementById('user-dropdown');
        if (dropdown) dropdown.classList.remove('show');
    }
});

// ============================================
// NOTIFICATION SYSTEM
// ============================================

function showNotification(message, type = 'info') {
    if (typeof Notifications !== 'undefined' && Notifications.show) {
        Notifications.show(message, type);
    } else {
        // Fallback simple notification
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            background: ${type === 'error' ? '#ff4444' : type === 'success' ? '#22c55e' : '#333'};
            color: white;
            z-index: 10000;
            font-size: 14px;
            animation: slideIn 0.3s ease;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ============================================
// CONNECTION INFO
// ============================================

let connectionInfoErrorCount = 0;
const MAX_CONNECTION_ERRORS = 3;

async function updateConnectionInfo() {
    const connectionInfoEl = document.getElementById('connection-info');
    if (!connectionInfoEl) return;
    
    // Stop polling if we've had too many errors (backend not available)
    if (connectionInfoErrorCount >= MAX_CONNECTION_ERRORS) {
        connectionInfoEl.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch('/api/connection/info');
        
        if (!response.ok) {
            connectionInfoErrorCount++;
            connectionInfoEl.style.display = 'none';
            return;
        }
        
        const data = await response.json();
        connectionInfoErrorCount = 0; // Reset on success
        
        if (data.connected) {
            connectionInfoEl.style.display = 'flex';
            
            const connectionTypeEl = document.getElementById('connection-type');
            const batteryTextEl = document.getElementById('battery-text');
            const signalTextEl = document.getElementById('signal-text');
            
            if (connectionTypeEl) {
                connectionTypeEl.textContent = data.connection_type === 'ble' ? 'Bluetooth' : 'USB';
            }
            if (batteryTextEl) {
                batteryTextEl.textContent = data.battery_level + '%';
            }
            if (signalTextEl) {
                const signalStrength = data.signal_strength || 4;
                signalTextEl.textContent = signalStrength >= 4 ? 'Strong' : signalStrength >= 2 ? 'Medium' : 'Weak';
            }
        } else {
            connectionInfoEl.style.display = 'none';
        }
    } catch (e) {
        connectionInfoErrorCount++;
        connectionInfoEl.style.display = 'none';
        // Silent fail - don't spam console
    }
}

// ============================================
// INFO MODAL BASE
// ============================================

function showInfoModal(title, content) {
    const modal = document.createElement('div');
    modal.className = 'info-modal';
    modal.innerHTML = `
        <div class="info-modal-content">
            <button class="info-modal-close" onclick="this.closest('.info-modal').remove()">&times;</button>
            <h2>${title}</h2>
            ${content}
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

// ============================================
// MOBILE HAMBURGER MENU
// ============================================

function injectHamburgerMenu() {
    // Check if already exists
    if (document.getElementById('hamburger-btn')) return;
    
    const header = document.querySelector('.header');
    if (!header) return;
    
    // Create hamburger button
    const btn = document.createElement('button');
    btn.className = 'hamburger-btn';
    btn.id = 'hamburger-btn';
    btn.setAttribute('aria-label', 'Open menu');
    btn.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="4" x2="20" y1="12" y2="12"></line>
            <line x1="4" x2="20" y1="6" y2="6"></line>
            <line x1="4" x2="20" y1="18" y2="18"></line>
        </svg>
    `;
    btn.onclick = toggleMobileDrawer;
    header.appendChild(btn);
    
    // Create drawer if it doesn't exist
    if (!document.getElementById('mobile-drawer')) {
        createMobileDrawer();
    }
    
    console.log('🍔 Mobile menu ready');
}

function createMobileDrawer() {
    // Create overlay
    const overlay = document.createElement('div');
    overlay.className = 'mobile-drawer-overlay';
    overlay.id = 'mobile-drawer-overlay';
    overlay.onclick = closeMobileDrawer;
    document.body.appendChild(overlay);
    
    // Create drawer
    const drawer = document.createElement('div');
    drawer.className = 'mobile-drawer';
    drawer.id = 'mobile-drawer';
    
    const currentPath = window.location.pathname;
    const isActive = (path) => currentPath === path ? 'active' : '';
    
    drawer.innerHTML = `
        <div class="drawer-header">
            <div class="drawer-logo">
                <img src="/logo.svg" alt="Logo">
                <h2>Brutally Honest</h2>
            </div>
            <button class="drawer-close-btn" onclick="closeMobileDrawer()" aria-label="Close">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
        </div>
        <nav class="drawer-nav">
            <a href="/" class="drawer-nav-link ${isActive('/')}">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"></path><path d="M3 10a2 2 0 0 1 .709-1.528l7-6a2 2 0 0 1 2.582 0l7 6A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path></svg>
                Home
            </a>
            <a href="/documents" class="drawer-nav-link ${isActive('/documents')}">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"></path><path d="M14 2v4a2 2 0 0 0 2 2h4"></path></svg>
                Documents
            </a>
            <a href="/profiles" class="drawer-nav-link ${isActive('/profiles')}">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M22 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                Profiles
            </a>
            <a href="/validation" class="drawer-nav-link ${isActive('/validation')}">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                Validation
            </a>
            <a href="/documentation" class="drawer-nav-link ${isActive('/documentation')}">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg>
                Documentation
            </a>
            <a href="/settings" class="drawer-nav-link ${isActive('/settings')}">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                Settings
            </a>
        </nav>
        <div class="drawer-footer">
            <button class="drawer-action-btn logout" onclick="logout()">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
                Logout
            </button>
        </div>
    `;
    document.body.appendChild(drawer);
}

function toggleMobileDrawer() {
    const drawer = document.getElementById('mobile-drawer');
    const overlay = document.getElementById('mobile-drawer-overlay');
    if (drawer && overlay) {
        drawer.classList.toggle('open');
        overlay.classList.toggle('show');
        document.body.classList.toggle('drawer-open');
    }
}

function closeMobileDrawer() {
    const drawer = document.getElementById('mobile-drawer');
    const overlay = document.getElementById('mobile-drawer-overlay');
    if (drawer && overlay) {
        drawer.classList.remove('open');
        overlay.classList.remove('show');
        document.body.classList.remove('drawer-open');
    }
}

// Close on escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeMobileDrawer();
});

// Close on resize to desktop
window.addEventListener('resize', () => {
    if (window.innerWidth > 768) closeMobileDrawer();
});

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Inject hamburger menu for mobile
    injectHamburgerMenu();
    
    // Load user info
    loadUserInfo();
    
    // Start connection info updates
    updateConnectionInfo();
    setInterval(updateConnectionInfo, 10000);
});


// === HISTORY LOADER ===
// === HISTORY LOADER - Visual Design System ===
window.loadHistory = async function() {
    var c = document.getElementById('history-list');
    if (!c) return;
    c.innerHTML = '<p class="text-center text-muted">Loading...</p>';
    try {
        var r = await fetch('/api/transcription-history');
        var d = await r.json();
        if (d.success && d.history && d.history.length > 0) {
            c.innerHTML = d.history.map(function(i) {
                var date = new Date(i.timestamp);
                var dateStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
                var filename = i.savedFilename || i.originalFilename;
                var res = i.result || {};
                
                // Parse brutal honesty for claim analysis
                var claimsHtml = '';
                var bh = res.brutal_honesty || '';
                if (bh.includes('Claim Analysis') || bh.includes('VERIFIED|') || bh.includes('NUANCED|') || bh.includes('INCORRECT|') || bh.includes('YES ') || bh.includes('NO ')) {
                    var lines = bh.split(String.fromCharCode(10));
                    claimsHtml = '<div class="flex flex-col gap-2 mt-4">';
                    for (var j = 0; j < lines.length; j++) {
                        var line = lines[j].trim();
                        if (!line) continue;
                        if (line.includes('Claim Analysis')) {
                            claimsHtml += '<div class="text-xs font-medium text-muted mb-2">' + line.replace(/\*/g, '') + '</div>';
                        } else if (line.startsWith('VERIFIED|')) {
                            var parts = line.split('|');
                            claimsHtml += '<div class="claim-card claim-card-verified"><div class="flex items-center gap-3"><div class="claim-icon claim-icon-verified"><span style="font-size: 14px;">✓</span></div><div class="flex-1"><div class="claim-title">' + (parts[1] || '') + '</div><div class="claim-description">' + (parts[2] || '') + '</div></div></div></div>';
                        } else if (line.startsWith('NUANCED|')) {
                            var parts = line.split('|');
                            claimsHtml += '<div class="claim-card claim-card-nuanced"><div class="flex items-center gap-3"><div class="claim-icon claim-icon-nuanced"><span style="font-size: 14px;">~</span></div><div class="flex-1"><div class="claim-title">' + (parts[1] || '') + '</div><div class="claim-description claim-description-nuanced">' + (parts[2] || '') + '</div></div></div></div>';
                        } else if (line.startsWith('INCORRECT|')) {
                            var parts = line.split('|');
                            claimsHtml += '<div class="claim-card claim-card-incorrect"><div class="flex items-center gap-3"><div class="claim-icon claim-icon-incorrect"><span style="font-size: 14px;">✗</span></div><div class="flex-1"><div class="claim-title">' + (parts[1] || '') + '</div><div class="claim-description claim-description-incorrect">' + (parts[2] || '') + '</div></div></div></div>';
                        } else if (line.startsWith('UNVERIFIED|')) {
                            var parts = line.split('|');
                            claimsHtml += '<div class="claim-card claim-card-unverified"><div class="flex items-center gap-3"><div class="claim-icon claim-icon-unverified"><span style="font-size: 14px;">?</span></div><div class="flex-1"><div class="claim-title">' + (parts[1] || '') + '</div><div class="claim-description">' + (parts[2] || '') + '</div></div></div></div>';
                        } else if (line.startsWith('TRUE:') || line.includes('-> TRUE')) {
                            var parts = line.replace('TRUE: ', '').split(' - ');
                            claimsHtml += '<div class="claim-badge claim-badge-verified"><span style="font-weight: 600;">✓</span><span class="text-sm font-medium">' + parts[0] + '</span>' + (parts[1] ? '<span class="text-xs text-muted" style="margin-left: 8px;">' + parts[1] + '</span>' : '') + '</div>';
                        } else if (line.startsWith('NUANCE:')) {
                            var parts = line.replace('NUANCE: ', '').split(' - ');
                            claimsHtml += '<div class="claim-badge claim-badge-nuanced"><span style="font-weight: 600;">~</span><span class="text-sm font-medium">' + parts[0] + '</span>' + (parts[1] ? '<span class="text-xs" style="margin-left: 8px;">' + parts[1] + '</span>' : '') + '</div>';
                        } else if (line.startsWith('FALSE:') || line.startsWith('NO ') || line.includes('-> FALSE')) {
                            var parts = line.replace('NO ', '').split('(');
                            var claim = parts[0].replace('-> FALSE', '').trim();
                            var reason = parts[1] ? parts[1].replace(')', '') : '';
                            claimsHtml += '<div class="claim-badge claim-badge-incorrect"><span style="font-weight: 600;">✗</span><span class="text-sm">' + claim + '</span>' + (reason ? '<span class="text-xs text-muted" style="margin-left: 8px;">→ ' + reason + '</span>' : '') + '</div>';
                        } else if (line.startsWith('? ')) {
                            claimsHtml += '<div class="claim-badge claim-badge-nuanced"><span style="font-weight: 600;">?</span><span class="text-sm">' + line.replace('? ', '') + '</span></div>';
                        }
                    }
                    claimsHtml += '</div>';
                } else if (bh) {
                    claimsHtml = '<div class="text-sm text-muted mt-2" style="font-style: italic;">' + bh + '</div>';
                }
                
                // Check if this is a saved-only recording (not yet transcribed)
                var isSavedOnly = i.status === 'saved' || (!res.transcription && !res.brutal_honesty);
                
                // Credibility bar - handle null/undefined for N/A
                var cred = res.credibility_score;
                var credPct = (cred !== null && cred !== undefined && typeof cred === 'number') ? Math.round(cred * 100) : null;
                var credClass = credPct === null ? 'neutral' : (cred >= 0.7 ? 'success' : cred >= 0.4 ? 'warning' : 'error');
                var credDisplay = credPct !== null ? credPct + '%' : 'N/A';
                
                // For saved-only recordings, show a simpler UI
                if (isSavedOnly) {
                    return '<div class="recording-item recording-item-saved">' +
                        '<div class="recording-header">' +
                        '<div class="recording-info"><span class="recording-name">' + i.originalFilename + '</span><span class="text-xs text-muted">' + dateStr + '</span><span class="badge badge-saved" style="background: #fef3c7; color: #92400e; margin-left: 8px;">Saved - Not Transcribed</span></div>' +
                        '<div class="recording-actions">' +
                        '<a href="/api/recordings/' + filename + '" download class="btn btn-secondary btn-sm">Download</a>' +
                        '<button onclick="reanalyzeRecording(\'' + i.id + '\')" class="btn btn-primary btn-sm" style="background: #2563eb;">Transcribe Now</button>' +
                        '<button onclick="deleteRecording(\'' + i.id + '\')" class="btn btn-danger btn-sm">Delete</button>' +
                        '</div></div>' +
                        '<div class="recording-transcript" style="color: #666; font-style: italic; background: #f9fafb;">Click "Transcribe Now" to process this recording with AI transcription and fact-checking.</div>' +
                        '</div>';
                }
                
                return '<div class="recording-item">' +
                    // Header with name and buttons
                    '<div class="recording-header">' +
                    '<div class="recording-info"><span class="recording-name">' + i.originalFilename + '</span><span class="text-xs text-muted">' + dateStr + '</span></div>' +
                    '<div class="recording-actions">' +
                    '<a href="/api/recordings/' + filename + '" download class="btn btn-secondary btn-sm">Download</a>' +
                    '<button onclick="reanalyzeRecording(\'' + i.id + '\')" class="btn btn-primary btn-sm">Re-analyze</button>' +
                    '<button onclick="deleteRecording(\'' + i.id + '\')" class="btn btn-danger btn-sm">Delete</button>' +
                    '</div></div>' +
                    
                    // Transcription
                    '<div class="recording-transcript">' + (res.transcription || 'No transcription') + '</div>' +
                    
                    // Stats row
                    '<div class="recording-badges">' +
                    '<span class="badge">' + (res.sentiment || 'neutral') + '</span>' +
                    '<span class="badge">Conf: ' + (res.confidence ? (typeof res.confidence === 'string' ? res.confidence : Math.round(res.confidence * 100) + '%') : 'N/A') + '</span>' +
                    '<span class="badge cred-badge-' + credClass + '">Cred: ' + credDisplay + '</span>' +
                    '<span class="badge">Time: ' + (res.processing_time ? typeof res.processing_time === 'number' ? res.processing_time.toFixed(1) : res.processing_time + 's' : 'N/A') + '</span>' +
                    '</div>' +
                    
                    // Credibility bar (only if we have a score)
                    (credPct !== null ? '<div class="cred-bar"><div class="cred-bar-fill cred-bar-' + credClass + '" style="width: ' + credPct + '%;"></div></div>' : '') +
                    
                    // Claims analysis
                    claimsHtml +
                    
                    // Keywords
                    (res.keywords && res.keywords.length > 0 ? '<div class="text-xs text-muted mt-4">Keywords: ' + res.keywords.join(', ') + '</div>' : '') +
                    '</div>';
            }).join('');
        } else {
            c.innerHTML = '<p class="text-center text-muted">No recordings yet</p>';
        }
    } catch(e) {
        console.error('History error:', e);
        c.innerHTML = '<p style="color: var(--color-danger);">Error loading history</p>';
    }
};

window.deleteRecording = async function(id) {
    if (!confirm('Delete this recording?')) return;
    try {
        var r = await fetch('/api/transcription-history/' + id, { method: 'DELETE' });
        var d = await r.json();
        if (d.success) loadHistory();
    } catch(e) { alert('Delete failed'); }
};

document.addEventListener('DOMContentLoaded', function() { setTimeout(loadHistory, 500); });
window.addEventListener('pageshow', function() { setTimeout(loadHistory, 500); });

// Tab switching for transcription page
window.switchTranscriptionTab = function(tab) {
    console.log('Switching to tab:', tab);
    
    // Update tab buttons (both old and new class)
    document.querySelectorAll('.tab, .transcription-tab').forEach(function(t) { 
        t.classList.remove('active'); 
    });
    var activeTab = document.getElementById('tab-' + tab);
    if (activeTab) activeTab.classList.add('active');
    
    // Hide all tabs
    var uploadTab = document.getElementById('tab-content-upload');
    var deviceTab = document.getElementById('tab-content-device');
    var recordingsTab = document.getElementById('tab-content-recordings');
    
    if (uploadTab) uploadTab.style.display = 'none';
    if (deviceTab) deviceTab.style.display = 'none';
    if (recordingsTab) recordingsTab.style.display = 'none';
    
    // Show selected
    if (tab === 'upload' && uploadTab) uploadTab.style.display = 'block';
    if (tab === 'device' && deviceTab) deviceTab.style.display = 'block';
    if (tab === 'recordings' && recordingsTab) {
        recordingsTab.style.display = 'block';
        if (typeof loadHistory === 'function') loadHistory();
    }
    
    // ESP notification
    var espNotif = document.getElementById('esp-notification');
    if (espNotif) espNotif.style.display = (tab === 'device') ? 'block' : 'none';
};

// === PROFILES TAB SWITCHING ===
window.switchProfileType = function(type) {
    window.currentProfileType = type;
    
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(function(btn) {
        btn.classList.remove('active');
    });
    var activeTab = document.getElementById('tab-' + type);
    if (activeTab) activeTab.classList.add('active');
    
    // Show/hide fields
    var clientFields = document.getElementById('client-fields');
    var personFields = document.getElementById('person-fields');
    var personCompanyField = document.getElementById('person-company-field');
    var brandValuesField = document.getElementById('brand-values-field');
    
    if (clientFields) clientFields.style.display = 'none';
    if (personFields) personFields.style.display = 'none';
    if (personCompanyField) personCompanyField.style.display = 'none';
    if (brandValuesField) brandValuesField.style.display = 'none';
    
    if (type === 'clients') {
        if (clientFields) clientFields.style.display = 'flex';
        document.getElementById('create-profile-title').textContent = 'Create Client Profile';
        document.getElementById('profiles-list-title').textContent = 'Client Profiles';
    } else if (type === 'brands') {
        if (brandValuesField) brandValuesField.style.display = 'flex';
        document.getElementById('create-profile-title').textContent = 'Create Brand Profile';
        document.getElementById('profiles-list-title').textContent = 'Brand Profiles';
    } else if (type === 'persons') {
        if (personFields) personFields.style.display = 'flex';
        if (personCompanyField) personCompanyField.style.display = 'flex';
        document.getElementById('create-profile-title').textContent = 'Create Person Profile';
        document.getElementById('profiles-list-title').textContent = 'Person Profiles';
    }
    
    if (typeof loadProfiles === 'function') loadProfiles();
    var form = document.getElementById('create-profile-form');
    if (form) form.reset();
};

// === DOCUMENTS TAB SWITCHING ===
window.switchDocTab = function(tab) {
    document.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
    var activeTab = document.getElementById('tab-' + tab);
    if (activeTab) activeTab.classList.add('active');
    
    var uploadTab = document.getElementById('tab-content-upload');
    var libraryTab = document.getElementById('tab-content-library');
    if (uploadTab) uploadTab.style.display = (tab === 'upload') ? 'block' : 'none';
    if (libraryTab) libraryTab.style.display = (tab === 'library') ? 'block' : 'none';
    
    if (tab === 'library' && typeof loadDocuments === 'function') loadDocuments();
};

// === SETTINGS TAB SWITCHING ===
window.switchSettingsTab = function(tab) {
    document.querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
    var activeTab = document.getElementById('tab-' + tab);
    if (activeTab) activeTab.classList.add('active');
    
    var accountTab = document.getElementById('tab-content-account');
    var prefsTab = document.getElementById('tab-content-preferences');
    var apiTab = document.getElementById('tab-content-api');
    if (accountTab) accountTab.style.display = (tab === 'account') ? 'block' : 'none';
    if (prefsTab) prefsTab.style.display = (tab === 'preferences') ? 'block' : 'none';
    if (apiTab) apiTab.style.display = (tab === 'api') ? 'block' : 'none';
};

// === SETTINGS FUNCTIONS ===
window.saveAccountSettings = function(e) {
    e.preventDefault();
    showNotification('Account settings saved', 'success');
};

window.savePreferences = function(e) {
    e.preventDefault();
    showNotification('Preferences saved', 'success');
};

window.copyApiKey = function() {
    var input = document.getElementById('api-key');
    if (input) {
        navigator.clipboard.writeText(input.value);
        showNotification('API key copied to clipboard', 'success');
    }
};

window.regenerateApiKey = function() {
    if (confirm('Are you sure? This will invalidate your current key.')) {
        showNotification('API key regenerated', 'success');
    }
};

// === URL-BASED TAB NAVIGATION ===
(function() {
    // Get tab from URL hash or path
    function getTabFromUrl() {
        var hash = window.location.hash.replace('#', '');
        if (hash) return hash;
        
        var path = window.location.pathname;
        var parts = path.split('/').filter(function(p) { return p; });
        if (parts.length > 1) return parts[parts.length - 1];
        return null;
    }
    
    // Update URL when tab changes
    function updateUrl(tab) {
        if (history.pushState) {
            var newHash = '#' + tab;
            if (window.location.hash !== newHash) {
                history.pushState(null, null, newHash);
            }
        }
    }
    
    // Override tab switching to update URL
    var origSwitchTranscriptionTab = window.switchTranscriptionTab;
    window.switchTranscriptionTab = function(tab) {
        updateUrl(tab);
        if (origSwitchTranscriptionTab) origSwitchTranscriptionTab(tab);
    };
    
    var origSwitchDocTab = window.switchDocTab;
    window.switchDocTab = function(tab) {
        updateUrl(tab);
        if (origSwitchDocTab) origSwitchDocTab(tab);
    };
    
    var origSwitchSettingsTab = window.switchSettingsTab;
    window.switchSettingsTab = function(tab) {
        updateUrl(tab);
        if (origSwitchSettingsTab) origSwitchSettingsTab(tab);
    };
    
    var origSwitchProfileType = window.switchProfileType;
    window.switchProfileType = function(tab) {
        updateUrl(tab);
        if (origSwitchProfileType) origSwitchProfileType(tab);
    };
    
    // On page load, activate tab from URL
    window.addEventListener('DOMContentLoaded', function() {
        var tab = getTabFromUrl();
        if (tab) {
            setTimeout(function() {
                // Try each tab switcher
                if (document.getElementById('tab-' + tab)) {
                    if (typeof switchTranscriptionTab === 'function' && document.getElementById('tab-content-' + tab)) {
                        switchTranscriptionTab(tab);
                    } else if (typeof switchDocTab === 'function') {
                        switchDocTab(tab);
                    } else if (typeof switchSettingsTab === 'function') {
                        switchSettingsTab(tab);
                    } else if (typeof switchProfileType === 'function') {
                        switchProfileType(tab);
                    }
                }
            }, 100);
        }
    });
    
    // Handle browser back/forward
    window.addEventListener('popstate', function() {
        var tab = getTabFromUrl();
        if (tab && document.getElementById('tab-' + tab)) {
            // Trigger without updating URL again
            var btn = document.getElementById('tab-' + tab);
            if (btn) btn.click();
        }
    });
})();

// === RE-ANALYZE FUNCTION ===
window.reanalyzeRecording = async function(id) {
    showNotification('Re-analyzing...', 'info');
    try {
        var response = await fetch('/api/reanalyze/' + id, { method: 'POST' });
        var data = await response.json();
        if (data.success) {
            showNotification('Re-analysis complete!', 'success');
            loadHistory();
        } else {
            showNotification('Re-analysis failed: ' + (data.detail || 'Unknown error'), 'error');
        }
    } catch (e) {
        showNotification('Error: ' + e.message, 'error');
    }
};
