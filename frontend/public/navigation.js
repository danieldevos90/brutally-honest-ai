// Navigation Component - Brutally Honest
// Dynamically renders the navigation bar and mobile drawer across all pages

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

    // Check if dark mode is active
    function isDarkMode() {
        const theme = document.documentElement.getAttribute('data-theme');
        if (theme === 'dark') return true;
        if (theme === 'light') return false;
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
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
                    <img src="/logo.svg" alt="Brutally Honest Logo" class="logo">
                    <h1>Brutally Honest</h1>
                </div>
                
                <nav class="nav-menu">
                    ${navLinksHTML}
                    
                    <!-- Theme Toggle -->
                    <button class="theme-toggle" onclick="toggleTheme()" title="Toggle dark mode">
                        <i data-lucide="sun" class="theme-icon-light"></i>
                        <i data-lucide="moon" class="theme-icon-dark" style="display: none;"></i>
                    </button>
                    
                    <!-- User Menu -->
                    <div class="user-menu">
                        <button class="user-btn" onclick="toggleUserMenu()">
                            <i data-lucide="user" class="nav-icon"></i>
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
                
                <!-- Hamburger Menu Button (Mobile) -->
                <button class="hamburger-btn" onclick="toggleMobileDrawer()" aria-label="Open menu">
                    <i data-lucide="menu"></i>
                </button>
            </div>
        `;
    }

    // Generate mobile drawer HTML
    function generateMobileDrawerHTML() {
        const drawerNavLinksHTML = navItems
            .filter(item => !item.hidden)
            .map(item => {
                const activeClass = isActive(item.href) ? ' active' : '';
                return `
                    <a href="${item.href}" class="drawer-nav-link${activeClass}">
                        <i data-lucide="${item.icon}"></i>
                        ${item.label}
                    </a>
                `;
            }).join('');

        const darkModeActive = isDarkMode();

        return `
            <!-- Mobile Drawer Overlay -->
            <div class="mobile-drawer-overlay" id="mobile-drawer-overlay" onclick="closeMobileDrawer()"></div>
            
            <!-- Mobile Drawer -->
            <div class="mobile-drawer" id="mobile-drawer">
                <!-- Drawer Header -->
                <div class="drawer-header">
                    <div class="drawer-logo">
                        <img src="/logo.svg" alt="Logo">
                        <h2>Brutally Honest</h2>
                    </div>
                    <button class="drawer-close-btn" onclick="closeMobileDrawer()" aria-label="Close menu">
                        <i data-lucide="x"></i>
                    </button>
                </div>
                
                <!-- Drawer Navigation -->
                <nav class="drawer-nav">
                    ${drawerNavLinksHTML}
                </nav>
                
                <!-- Theme Toggle in Drawer -->
                <div class="drawer-theme-toggle">
                    <div class="drawer-theme-label">
                        <i data-lucide="${darkModeActive ? 'moon' : 'sun'}"></i>
                        <span>${darkModeActive ? 'Dark Mode' : 'Light Mode'}</span>
                    </div>
                    <div class="theme-switch ${darkModeActive ? 'active' : ''}" onclick="toggleThemeFromDrawer()">
                        <div class="theme-switch-knob"></div>
                    </div>
                </div>
                
                <!-- Drawer Footer -->
                <div class="drawer-footer">
                    <div class="drawer-user-section">
                        <div class="drawer-user-info">
                            <div class="drawer-user-avatar">
                                <i data-lucide="user"></i>
                            </div>
                            <div class="drawer-user-details">
                                <div class="drawer-user-name" id="drawer-user-name">Account</div>
                                <div class="drawer-user-email" id="drawer-user-email">user@email.com</div>
                            </div>
                        </div>
                        <div class="drawer-actions">
                            <a href="/settings" class="drawer-action-btn" onclick="closeMobileDrawer()">
                                <i data-lucide="settings"></i>
                                Settings
                            </a>
                            <button class="drawer-action-btn logout" onclick="logout()">
                                <i data-lucide="log-out"></i>
                                Logout
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Toggle mobile drawer
    window.toggleMobileDrawer = function() {
        const drawer = document.getElementById('mobile-drawer');
        const overlay = document.getElementById('mobile-drawer-overlay');
        
        if (drawer && overlay) {
            const isOpen = drawer.classList.contains('open');
            
            if (isOpen) {
                closeMobileDrawer();
            } else {
                drawer.classList.add('open');
                overlay.classList.add('show');
                document.body.classList.add('drawer-open');
            }
        }
    };

    // Close mobile drawer
    window.closeMobileDrawer = function() {
        const drawer = document.getElementById('mobile-drawer');
        const overlay = document.getElementById('mobile-drawer-overlay');
        
        if (drawer && overlay) {
            drawer.classList.remove('open');
            overlay.classList.remove('show');
            document.body.classList.remove('drawer-open');
        }
    };

    // Toggle theme from drawer
    window.toggleThemeFromDrawer = function() {
        toggleTheme();
        
        // Update drawer theme toggle state
        const themeSwitch = document.querySelector('.theme-switch');
        const themeLabel = document.querySelector('.drawer-theme-label span');
        const themeIcon = document.querySelector('.drawer-theme-label i');
        
        const darkModeActive = isDarkMode();
        
        if (themeSwitch) {
            themeSwitch.classList.toggle('active', darkModeActive);
        }
        
        if (themeLabel) {
            themeLabel.textContent = darkModeActive ? 'Dark Mode' : 'Light Mode';
        }
        
        if (themeIcon) {
            themeIcon.setAttribute('data-lucide', darkModeActive ? 'moon' : 'sun');
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
    };

    // Toggle theme
    window.toggleTheme = function() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        let newTheme;
        if (currentTheme === 'dark') {
            newTheme = 'light';
        } else if (currentTheme === 'light') {
            newTheme = 'dark';
        } else {
            // No explicit theme set, toggle from system preference
            newTheme = prefersDark ? 'light' : 'dark';
        }
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update theme toggle icons in header
        updateThemeIcons(newTheme === 'dark');
    };

    // Update theme icons
    function updateThemeIcons(isDark) {
        const lightIcon = document.querySelector('.theme-icon-light');
        const darkIcon = document.querySelector('.theme-icon-dark');
        
        if (lightIcon && darkIcon) {
            lightIcon.style.display = isDark ? 'none' : 'block';
            darkIcon.style.display = isDark ? 'block' : 'none';
        }
    }

    // Apply saved theme on load
    function applySavedTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
            updateThemeIcons(savedTheme === 'dark');
        } else {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            updateThemeIcons(prefersDark);
        }
    }

    // Initialize navigation
    function initNavigation() {
        // Apply saved theme first
        applySavedTheme();
        
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

        // Add mobile drawer to body
        const existingDrawer = document.getElementById('mobile-drawer');
        if (!existingDrawer) {
            document.body.insertAdjacentHTML('beforeend', generateMobileDrawerHTML());
        }

        // Initialize Lucide icons after navigation is injected
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }

        // Initialize user info
        initUserInfo();
        
        // Handle escape key to close drawer
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeMobileDrawer();
            }
        });
        
        // Handle resize - close drawer on desktop
        window.addEventListener('resize', function() {
            if (window.innerWidth > 768) {
                closeMobileDrawer();
            }
        });
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
        const userEmail = localStorage.getItem('user_email') || 'user@example.com';
        const userName = userEmail.split('@')[0];
        
        // Update header
        const currentUserSpan = document.getElementById('current-user');
        const userEmailSpan = document.getElementById('user-email');

        if (currentUserSpan) {
            currentUserSpan.textContent = userName;
        }
        if (userEmailSpan) {
            userEmailSpan.textContent = userEmail;
        }
        
        // Update drawer
        const drawerUserName = document.getElementById('drawer-user-name');
        const drawerUserEmail = document.getElementById('drawer-user-email');
        
        if (drawerUserName) {
            drawerUserName.textContent = userName;
        }
        if (drawerUserEmail) {
            drawerUserEmail.textContent = userEmail;
        }
    }

    // Logout function
    window.logout = function() {
        closeMobileDrawer();
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
