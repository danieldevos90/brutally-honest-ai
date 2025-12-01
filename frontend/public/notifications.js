// Notification System for Brutally Honest AI
// Uses design-system.css classes - no inline styles

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 5;
        this.defaultDuration = 5000;
        this.init();
    }
    
    init() {
        this.createContainer();
        console.log('Notification system initialized');
    }
    
    createContainer() {
        if (document.getElementById('toast-container')) return;
        
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    show(options) {
        const {
            type = 'info',
            message,
            duration = this.defaultDuration
        } = options;
        
        const id = 'toast-' + Date.now();
        const toast = this.createToast(id, type, message);
        this.addToast(id, toast, duration);
        
        return id;
    }
    
    createToast(id, type, message) {
        const toast = document.createElement('div');
        toast.id = id;
        toast.className = `toast toast-${type}`;
        
        toast.innerHTML = `
            <div class="toast-content">
                <span>${message}</span>
            </div>
            <button class="toast-close btn-tertiary btn-sm" onclick="notificationSystem.dismiss('${id}')">&times;</button>
        `;
        
        return toast;
    }
    
    addToast(id, toast, duration) {
        const container = document.getElementById('toast-container');
        if (!container) return;
        
        // Limit notifications
        if (this.notifications.length >= this.maxNotifications) {
            const oldest = this.notifications.shift();
            this.dismiss(oldest.id);
        }
        
        container.appendChild(toast);
        
        // Animate in
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });
        
        // Auto dismiss
        const timer = setTimeout(() => this.dismiss(id), duration);
        this.notifications.push({ id, timer });
    }
    
    dismiss(id) {
        const toast = document.getElementById(id);
        if (!toast) return;
        
        toast.classList.remove('show');
        toast.classList.add('hiding');
            
        setTimeout(() => toast.remove(), 300);
        
        // Clear timer
        const idx = this.notifications.findIndex(n => n.id === id);
        if (idx > -1) {
            clearTimeout(this.notifications[idx].timer);
            this.notifications.splice(idx, 1);
            }
            }
            
    // Convenience methods
    success(message, options = {}) {
        return this.show({ type: 'success', message, ...options });
    }
    
    error(message, options = {}) {
        return this.show({ type: 'error', message, duration: 8000, ...options });
    }
    
    warning(message, options = {}) {
        return this.show({ type: 'warning', message, duration: 6000, ...options });
    }
    
    info(message, options = {}) {
        return this.show({ type: 'info', message, ...options });
    }
    
    clear() {
        this.notifications.forEach(n => this.dismiss(n.id));
        this.notifications = [];
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.notificationSystem = new NotificationSystem();
});

// Global helper function
window.showNotification = function(type, message, options = {}) {
    if (window.notificationSystem) {
        return window.notificationSystem.show({ type, message, ...options });
    }
};

window.NotificationSystem = NotificationSystem;
