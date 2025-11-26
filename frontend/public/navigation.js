// Navigation Component - Brutally Honest
// Dynamically renders the navigation bar across all pages

(function() {
    'use strict';

    // Navigation items configuration
    const navItems = [
        { href: '/', icon: 'home', label: 'Home' },
        { href: '/documents', icon: 'file-text', label: 'Documents' },
        { href: '/profiles', icon: 'users', label: 'Profiles' },
        { href: '/validation', icon: 'check-circle', label: 'Validation' },
        { href: '/documentation', icon: 'book-open', label: 'Documentation' },
        { href: '/settings', icon: 'settings', label: 'Settings', hidden: true }
    ];

    // Get current page path
    function getCurrentPath() {
        const path = window.location.pathname;
        // Normalize path - remove trailing slash and .html extension
        return path.replace(/\.html$/, '').replace(/\/$/, '') || '/';
    }

    // Check if a nav item is active
    function isActive(href) {
        const currentPath = getCurrentPath();
        if (href === '/') {
            return currentPath === '/' || currentPath === '/index';
        }
        return currentPath === href || currentPath.startsWith(href + '/');
    }

    // Generate navigation HTML
    function generateNavigationHTML() {
        const navLinksHTML = navItems
            .filter(item => !item.hidden)
            .map(item => {
                const activeClass = isActive(item.href) ? ' active' : '';
                return `
                    <a href="${item.href}" class="nav-link${activeClass}">
                        <i data-lucide="${item.icon}" class="nav-icon"></i>
                        ${item.label}
                    </a>
                `;
            }).join('');

        return `
            <div class="header">
                <div class="logo-title">
                    <img src="logo.svg" alt="Brutally Honest Logo" class="logo">
                    <h1>Brutally Honest</h1>
                </div>
                
                <nav class="nav-menu">
                    ${navLinksHTML}
                    
                    <!-- User Menu -->
                    <div class="user-menu">
                        <button class="user-btn" onclick="toggleUserMenu()">
                            <i data-lucide="user" class="nav-icon"></i>
                            <span id="current-user">Account</span>
                            <i data-lucide="chevron-down" style="width: 14px; height: 14px;"></i>
                        </button>
                        <div class="user-dropdown" id="user-dropdown">
                            <div class="user-info" id="user-info">
                                <span class="user-email" id="user-email">Loading...</span>
                            </div>
                            <a href="/settings" class="dropdown-item">
                                <i data-lucide="settings"></i> Settings
                            </a>
                            <button class="dropdown-item" onclick="logout()">
                                <i data-lucide="log-out"></i> Logout
                            </button>
                        </div>
                    </div>
                </nav>
            </div>
        `;
    }

    // Initialize navigation
    function initNavigation() {
        // Find the navigation placeholder or insert at beginning of container
        const placeholder = document.getElementById('navigation-placeholder');
        const container = document.querySelector('.container');

        if (placeholder) {
            placeholder.outerHTML = generateNavigationHTML();
        } else if (container) {
            // Check if header already exists (fallback for pages not yet updated)
            const existingHeader = container.querySelector('.header');
            if (!existingHeader) {
                container.insertAdjacentHTML('afterbegin', generateNavigationHTML());
            }
        }

        // Initialize Lucide icons after navigation is injected
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // Initialize user info
        initUserInfo();
    }

    // Toggle user dropdown menu
    window.toggleUserMenu = function() {
        const dropdown = document.getElementById('user-dropdown');
        if (dropdown) {
            dropdown.classList.toggle('show');
        }
    };

    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        const userMenu = document.querySelector('.user-menu');
        const dropdown = document.getElementById('user-dropdown');
        
        if (dropdown && userMenu && !userMenu.contains(event.target)) {
            dropdown.classList.remove('show');
        }
    });

    // Initialize user info display
    function initUserInfo() {
        const userEmail = localStorage.getItem('user_email');
        const currentUserSpan = document.getElementById('current-user');
        const userEmailSpan = document.getElementById('user-email');

        if (userEmail) {
            if (currentUserSpan) {
                currentUserSpan.textContent = userEmail.split('@')[0];
            }
            if (userEmailSpan) {
                userEmailSpan.textContent = userEmail;
            }
        }
    }

    // Logout function
    window.logout = function() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_email');
        window.location.href = '/login';
    };

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNavigation);
    } else {
        initNavigation();
    }
})();

