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
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Load user info
    loadUserInfo();
    
    // Start connection info updates
    updateConnectionInfo();
    setInterval(updateConnectionInfo, 10000);
});

