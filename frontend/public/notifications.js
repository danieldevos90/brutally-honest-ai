// Real-time Notification System for Brutally Honest AI
// Provides toast notifications, progress indicators, and status updates

class NotificationSystem {
    constructor() {
        this.notifications = [];
        this.maxNotifications = 5;
        this.defaultDuration = 5000;
        
        this.init();
    }
    
    init() {
        this.createNotificationContainer();
        this.setupStyles();
        
        console.log('🔔 Notification system initialized');
    }
    
    createNotificationContainer() {
        // Create notification container
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }
    
    setupStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                pointer-events: none;
            }
            
            .notification {
                background: white;
                border-radius: 12px;
                padding: 16px 20px;
                margin-bottom: 12px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
                border-left: 4px solid #3b82f6;
                max-width: 400px;
                min-width: 300px;
                pointer-events: auto;
                transform: translateX(100%);
                opacity: 0;
                transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
                position: relative;
                overflow: hidden;
            }
            
            .notification.show {
                transform: translateX(0);
                opacity: 1;
            }
            
            .notification.hide {
                transform: translateX(100%);
                opacity: 0;
            }
            
            .notification::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, #3b82f6, #8b5cf6);
                transform: scaleX(0);
                transform-origin: left;
                animation: progress var(--duration) linear;
            }
            
            @keyframes progress {
                to { transform: scaleX(1); }
            }
            
            .notification-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 8px;
            }
            
            .notification-title {
                display: flex;
                align-items: center;
                gap: 8px;
                font-weight: 600;
                font-size: 0.95rem;
                color: #1f2937;
            }
            
            .notification-icon {
                width: 20px;
                height: 20px;
                flex-shrink: 0;
            }
            
            .notification-close {
                background: none;
                border: none;
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
                color: #6b7280;
                transition: all 0.2s ease;
            }
            
            .notification-close:hover {
                background: #f3f4f6;
                color: #374151;
            }
            
            .notification-close i {
                width: 16px;
                height: 16px;
            }
            
            .notification-message {
                color: #4b5563;
                font-size: 0.9rem;
                line-height: 1.4;
                margin-bottom: 8px;
            }
            
            .notification-actions {
                display: flex;
                gap: 8px;
                margin-top: 12px;
            }
            
            .notification-btn {
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 0.8rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                border: none;
            }
            
            .notification-btn.primary {
                background: #3b82f6;
                color: white;
            }
            
            .notification-btn.primary:hover {
                background: #2563eb;
            }
            
            .notification-btn.secondary {
                background: #f3f4f6;
                color: #374151;
            }
            
            .notification-btn.secondary:hover {
                background: #e5e7eb;
            }
            
            /* Notification types */
            .notification.success {
                border-left-color: #10b981;
            }
            
            .notification.success::before {
                background: linear-gradient(90deg, #10b981, #34d399);
            }
            
            .notification.error {
                border-left-color: #ef4444;
            }
            
            .notification.error::before {
                background: linear-gradient(90deg, #ef4444, #f87171);
            }
            
            .notification.warning {
                border-left-color: #f59e0b;
            }
            
            .notification.warning::before {
                background: linear-gradient(90deg, #f59e0b, #fbbf24);
            }
            
            .notification.info {
                border-left-color: #3b82f6;
            }
            
            .notification.info::before {
                background: linear-gradient(90deg, #3b82f6, #60a5fa);
            }
            
            /* Progress notification */
            .notification.progress {
                border-left-color: #8b5cf6;
            }
            
            .notification.progress::before {
                background: linear-gradient(90deg, #8b5cf6, #a78bfa);
                animation: none;
                transform: scaleX(var(--progress, 0));
                transition: transform 0.3s ease;
            }
            
            .progress-bar {
                height: 4px;
                background: #e5e7eb;
                border-radius: 2px;
                margin-top: 8px;
                overflow: hidden;
            }
            
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #8b5cf6, #a78bfa);
                border-radius: 2px;
                transition: width 0.3s ease;
                width: 0%;
            }
            
            /* Dark mode */
            @media (prefers-color-scheme: dark) {
                .notification {
                    background: #1f2937;
                    color: #f9fafb;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }
                
                .notification-title {
                    color: #f9fafb;
                }
                
                .notification-message {
                    color: #d1d5db;
                }
                
                .notification-close {
                    color: #9ca3af;
                }
                
                .notification-close:hover {
                    background: #374151;
                    color: #d1d5db;
                }
                
                .notification-btn.secondary {
                    background: #374151;
                    color: #d1d5db;
                }
                
                .notification-btn.secondary:hover {
                    background: #4b5563;
                }
            }
            
            /* Mobile responsive */
            @media (max-width: 480px) {
                .notification-container {
                    top: 10px;
                    right: 10px;
                    left: 10px;
                }
                
                .notification {
                    min-width: auto;
                    max-width: none;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    show(options) {
        const {
            type = 'info',
            title,
            message,
            duration = this.defaultDuration,
            actions = [],
            persistent = false,
            progress = false
        } = options;
        
        const notification = this.createNotification({
            type,
            title,
            message,
            duration,
            actions,
            persistent,
            progress
        });
        
        this.addNotification(notification);
        
        if (!persistent && !progress) {
            setTimeout(() => {
                this.removeNotification(notification.id);
            }, duration);
        }
        
        return notification.id;
    }
    
    createNotification(options) {
        const id = Date.now() + Math.random();
        const { type, title, message, duration, actions, persistent, progress } = options;
        
        const iconMap = {
            success: 'check-circle',
            error: 'alert-circle',
            warning: 'alert-triangle',
            info: 'info',
            progress: 'loader'
        };
        
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.id = `notification-${id}`;
        
        if (!persistent && !progress) {
            notification.style.setProperty('--duration', `${duration}ms`);
        }
        
        notification.innerHTML = `
            <div class="notification-header">
                <div class="notification-title">
                    <i data-lucide="${iconMap[type]}" class="notification-icon"></i>
                    ${title}
                </div>
                <button class="notification-close" onclick="notificationSystem.removeNotification('${id}')">
                    <i data-lucide="x"></i>
                </button>
            </div>
            <div class="notification-message">${message}</div>
            ${progress ? '<div class="progress-bar"><div class="progress-fill"></div></div>' : ''}
            ${actions.length > 0 ? `
                <div class="notification-actions">
                    ${actions.map(action => `
                        <button class="notification-btn ${action.type || 'secondary'}" 
                                onclick="${action.onClick}; notificationSystem.removeNotification('${id}')">
                            ${action.text}
                        </button>
                    `).join('')}
                </div>
            ` : ''}
        `;
        
        return { id, element: notification, type, progress };
    }
    
    addNotification(notification) {
        const container = document.getElementById('notification-container');
        
        // Remove oldest notification if we have too many
        if (this.notifications.length >= this.maxNotifications) {
            const oldest = this.notifications.shift();
            this.removeNotification(oldest.id);
        }
        
        this.notifications.push(notification);
        container.appendChild(notification.element);
        
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // Trigger animation
        setTimeout(() => {
            notification.element.classList.add('show');
        }, 100);
    }
    
    removeNotification(id) {
        const notification = document.getElementById(`notification-${id}`);
        if (notification) {
            notification.classList.add('hide');
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 400);
        }
        
        // Remove from array
        this.notifications = this.notifications.filter(n => n.id !== id);
    }
    
    updateProgress(id, progress, message) {
        const notification = this.notifications.find(n => n.id === id);
        if (notification && notification.progress) {
            const element = notification.element;
            const progressFill = element.querySelector('.progress-fill');
            const messageElement = element.querySelector('.notification-message');
            
            if (progressFill) {
                progressFill.style.width = `${progress}%`;
            }
            
            if (message && messageElement) {
                messageElement.textContent = message;
            }
            
            // Auto-remove when complete
            if (progress >= 100) {
                setTimeout(() => {
                    this.removeNotification(id);
                }, 2000);
            }
        }
    }
    
    success(title, message, options = {}) {
        return this.show({
            type: 'success',
            title,
            message,
            ...options
        });
    }
    
    error(title, message, options = {}) {
        return this.show({
            type: 'error',
            title,
            message,
            duration: 8000, // Longer duration for errors
            ...options
        });
    }
    
    warning(title, message, options = {}) {
        return this.show({
            type: 'warning',
            title,
            message,
            ...options
        });
    }
    
    info(title, message, options = {}) {
        return this.show({
            type: 'info',
            title,
            message,
            ...options
        });
    }
    
    progress(title, message) {
        return this.show({
            type: 'progress',
            title,
            message,
            persistent: true,
            progress: true
        });
    }
    
    clear() {
        this.notifications.forEach(notification => {
            this.removeNotification(notification.id);
        });
        this.notifications = [];
    }
}

// Initialize notification system when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.notificationSystem = new NotificationSystem();
    
    // Minimal welcome - very subtle
    setTimeout(() => {
        console.log('🔔 Notification system ready');
    }, 1000);
});

// Export for global access
window.NotificationSystem = NotificationSystem;
