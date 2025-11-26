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

async function updateConnectionInfo() {
    try {
        const response = await fetch('/api/connection/info');
        const data = await response.json();
        
        const connectionInfoEl = document.getElementById('connection-info');
        if (!connectionInfoEl) return;
        
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
        const connectionInfoEl = document.getElementById('connection-info');
        if (connectionInfoEl) connectionInfoEl.style.display = 'none';
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

