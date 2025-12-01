const express = require('express');
const path = require('path');
const cors = require('cors');
const multer = require('multer');
const WebSocket = require('ws');
const crypto = require('crypto');
const fs = require('fs');
const expressLayouts = require('express-ejs-layouts');

const app = express();
const PORT = process.env.PORT || 3001;
// API_BASE can be configured via environment variable for production
// Default to localhost for development
const API_BASE = process.env.API_BASE || 'http://localhost:8000';

// ============================================
// ACTIVITY LOGGING
// ============================================
const ACTIVITY_LOG_FILE = path.join(__dirname, 'data', 'activity.log');
if (!fs.existsSync(path.dirname(ACTIVITY_LOG_FILE))) {
    fs.mkdirSync(path.dirname(ACTIVITY_LOG_FILE), { recursive: true });
}

function logActivity(type, action, details, user = 'anonymous') {
    const timestamp = new Date().toISOString();
    const logEntry = `[${timestamp}] [${type.toUpperCase()}] [${user}] ${action} | ${JSON.stringify(details)}`;
    console.log(`[LOG] ${logEntry}`);
    
    // Append to log file
    try {
        fs.appendFileSync(ACTIVITY_LOG_FILE, logEntry + '\n');
    } catch (e) {
        console.error('Failed to write activity log:', e.message);
    }
}

console.log(`🔗 API Backend URL: ${API_BASE}`);

// Recording storage
const RECORDINGS_DIR = path.join(__dirname, 'uploads', 'recordings');
const HISTORY_FILE = path.join(__dirname, 'data', 'transcription_history.json');
if (!fs.existsSync(RECORDINGS_DIR)) fs.mkdirSync(RECORDINGS_DIR, { recursive: true });
if (!fs.existsSync(path.dirname(HISTORY_FILE))) fs.mkdirSync(path.dirname(HISTORY_FILE), { recursive: true });
if (!fs.existsSync(HISTORY_FILE)) fs.writeFileSync(HISTORY_FILE, '[]');
// ============================================

function saveTranscriptionResult(filename, originalPath, result) {
    try {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const savedFilename = timestamp + '_' + filename;
        const savedPath = path.join(RECORDINGS_DIR, savedFilename);
        fs.copyFileSync(originalPath, savedPath);
        let history = [];
        try { history = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8')); } catch (e) { history = []; }
        history.unshift({
            id: Date.now().toString(),
            timestamp: new Date().toISOString(),
            originalFilename: filename,
            savedFilename: savedFilename,
            fileSize: fs.statSync(savedPath).size,
            result: result
        });
        if (history.length > 100) history = history.slice(0, 100);
        fs.writeFileSync(HISTORY_FILE, JSON.stringify(history, null, 2));
        console.log('[FILE] Saved recording:', savedFilename);
        return savedFilename;
    } catch (e) {
        console.error('Failed to save recording:', e.message);
        return null;
    }
}
// VIEW ENGINE SETUP (EJS)
// ============================================

app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));
app.use(expressLayouts);
app.set('layout', 'layout');
app.set('layout extractScripts', true);
app.set('layout extractStyles', true);

// ============================================
// USER MANAGEMENT SYSTEM
// ============================================

const USERS_FILE = path.join(__dirname, 'users.json');
const SESSIONS_FILE = path.join(__dirname, 'sessions.json');
const LOGS_FILE = path.join(__dirname, 'activity_logs.json');

// ============================================
// ACTIVITY LOGGING SYSTEM
// ============================================

const MAX_LOGS = 500; // Keep last 500 log entries
let activityLogs = [];

function loadLogs() {
    try {
        if (fs.existsSync(LOGS_FILE)) {
            activityLogs = JSON.parse(fs.readFileSync(LOGS_FILE, 'utf8'));
        }
    } catch (e) {
        console.error('Error loading logs:', e);
        activityLogs = [];
    }
}

function saveLogs() {
    try {
        // Keep only last MAX_LOGS entries
        if (activityLogs.length > MAX_LOGS) {
            activityLogs = activityLogs.slice(-MAX_LOGS);
        }
        fs.writeFileSync(LOGS_FILE, JSON.stringify(activityLogs, null, 2));
    } catch (e) {
        console.error('Error saving logs:', e);
    }
}

function addLog(type, action, details = {}, userId = null) {
    const logEntry = {
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        type: type,        // 'transcribe', 'upload', 'device', 'auth', 'system', 'error'
        action: action,    // 'started', 'completed', 'failed', etc.
        details: details,
        userId: userId,
        device: details.device || 'web'
    };
    
    activityLogs.push(logEntry);
    saveLogs();
    
    // Broadcast to WebSocket clients
    broadcastLog(logEntry);
    
    console.log(`[LOG] ${type}/${action}:`, JSON.stringify(details).substring(0, 200));
    return logEntry;
}

function broadcastLog(logEntry) {
    if (wss) {
        const message = JSON.stringify({ type: 'activity_log', data: logEntry });
        wss.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(message);
            }
        });
    }
}

// Load logs on startup
loadLogs();

function loadUsers() {
    try {
        if (fs.existsSync(USERS_FILE)) {
            return JSON.parse(fs.readFileSync(USERS_FILE, 'utf8'));
        }
    } catch (e) {
        console.error('Error loading users:', e);
    }
    return {
        'admin': {
            id: 'admin',
            email: 'admin@brutallyhonest.io',
            password: hashPassword('brutallyhonest2024'),
            name: 'Admin',
            role: 'admin',
            created: new Date().toISOString()
        }
    };
}

function saveUsers(users) {
    try {
        fs.writeFileSync(USERS_FILE, JSON.stringify(users, null, 2));
    } catch (e) {
        console.error('Error saving users:', e);
    }
}

function hashPassword(password) {
    return crypto.createHash('sha256').update(password + 'brutally_salt_2024').digest('hex');
}

function generateSessionToken() {
    return crypto.randomBytes(32).toString('hex');
}

const sessions = new Map();

function loadSessions() {
    try {
        if (fs.existsSync(SESSIONS_FILE)) {
            const data = JSON.parse(fs.readFileSync(SESSIONS_FILE, 'utf8'));
            Object.entries(data).forEach(([token, session]) => {
                if (session.expires > Date.now()) {
                    sessions.set(token, session);
                }
            });
        }
    } catch (e) {
        console.error('Error loading sessions:', e);
    }
}

function saveSessions() {
    try {
        const data = {};
        sessions.forEach((session, token) => {
            data[token] = session;
        });
        fs.writeFileSync(SESSIONS_FILE, JSON.stringify(data, null, 2));
    } catch (e) {
        console.error('Error saving sessions:', e);
    }
}

let users = loadUsers();
loadSessions();

function cookieParser(req, res, next) {
    req.cookies = {};
    const cookieHeader = req.headers.cookie;
    if (cookieHeader) {
        cookieHeader.split(';').forEach(cookie => {
            const [name, value] = cookie.trim().split('=');
            req.cookies[name] = value;
        });
    }
    next();
}

function requireAuth(req, res, next) {
    const sessionToken = req.cookies?.session || req.headers['x-session-token'];
    
    if (sessionToken && sessions.has(sessionToken)) {
        const session = sessions.get(sessionToken);
        if (session.expires > Date.now()) {
            req.session = session;
            req.user = users[session.userId];
            return next();
        }
        sessions.delete(sessionToken);
        saveSessions();
    }
    
    if (req.path.startsWith('/api/') && !req.path.startsWith('/api/auth/')) {
        return res.status(401).json({ error: 'Unauthorized', message: 'Please login first' });
    }
    
    res.redirect('/login');
}

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser);

// Serve public assets without auth
app.use('/logo.svg', express.static(path.join(__dirname, 'public', 'logo.svg')));
app.use('/design-system.css', express.static(path.join(__dirname, 'public', 'design-system.css')));
app.use('/styles.css', express.static(path.join(__dirname, 'public', 'styles.css')));
app.use('/dynamic-portal.css', express.static(path.join(__dirname, 'public', 'dynamic-portal.css')));
app.use('/manifest.json', express.static(path.join(__dirname, 'public', 'manifest.json')));
app.use('/history_v2.js', express.static(path.join(__dirname, 'public', 'history_v2.js')));
app.use('/home.js', express.static(path.join(__dirname, 'public', 'home.js')));
app.use('/profiles.js', express.static(path.join(__dirname, 'public', 'profiles.js')));

// Multer for file uploads
const upload = multer({ 
    dest: 'uploads/',
    limits: { fileSize: 50 * 1024 * 1024 }
});

// ============================================
// AUTH ENDPOINTS
// ============================================

app.get('/login', (req, res) => {
    const sessionToken = req.cookies?.session;
    if (sessionToken && sessions.has(sessionToken)) {
        const session = sessions.get(sessionToken);
        if (session.expires > Date.now()) {
            return res.redirect('/');
        }
    }
    res.render('login', { layout: false });
});

app.post('/api/auth/login', (req, res) => {
    const { email, password, username } = req.body;
    const loginId = email || username;
    
    let user = null;
    for (const [id, u] of Object.entries(users)) {
        if (u.email === loginId || id === loginId) {
            user = u;
            break;
        }
    }
    
    if (user && user.password === hashPassword(password)) {
        const token = generateSessionToken();
        const expires = Date.now() + (24 * 60 * 60 * 1000);
        
        sessions.set(token, {
            userId: user.id,
            email: user.email,
            name: user.name,
            role: user.role,
            created: Date.now(),
            expires: expires
        });
        saveSessions();
        
        // Log successful login
        addLog('auth', 'login_success', { email: user.email, userId: user.id }, user.id);
        
        res.setHeader('Set-Cookie', `session=${token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=86400`);
        res.json({ 
            success: true, 
            message: 'Login successful',
            user: {
                id: user.id,
                email: user.email,
                name: user.name,
                role: user.role
            }
        });
    } else {
        // Log failed login attempt
        addLog('auth', 'login_failed', { attemptedEmail: loginId }, null);
        res.status(401).json({ success: false, message: 'Invalid email or password' });
    }
});

app.post('/api/auth/logout', (req, res) => {
    const sessionToken = req.cookies?.session;
    if (sessionToken) {
        sessions.delete(sessionToken);
        saveSessions();
    }
    res.setHeader('Set-Cookie', 'session=; Path=/; HttpOnly; Max-Age=0');
    res.json({ success: true, message: 'Logged out' });
});

app.get('/api/auth/status', (req, res) => {
    const sessionToken = req.cookies?.session;
    if (sessionToken && sessions.has(sessionToken)) {
        const session = sessions.get(sessionToken);
        if (session.expires > Date.now()) {
            return res.json({ 
                authenticated: true,
                user: {
                    id: session.userId,
                    email: session.email,
                    name: session.name,
                    role: session.role
                }
            });
        }
    }
    res.json({ authenticated: false });
});

app.get('/api/auth/me', requireAuth, (req, res) => {
    res.json({
        id: req.user.id,
        email: req.user.email,
        name: req.user.name,
        role: req.user.role
    });
});

// ============================================
// ACTIVITY LOGS API ENDPOINTS
// ============================================

// Get recent logs
app.get('/api/logs', requireAuth, (req, res) => {
    const { type, limit = 100, since } = req.query;
    
    let logs = [...activityLogs].reverse(); // Most recent first
    
    // Filter by type if specified
    if (type) {
        logs = logs.filter(l => l.type === type);
    }
    
    // Filter by timestamp if specified
    if (since) {
        const sinceDate = new Date(since);
        logs = logs.filter(l => new Date(l.timestamp) > sinceDate);
    }
    
    // Limit results
    logs = logs.slice(0, parseInt(limit));
    
    res.json({
        success: true,
        count: logs.length,
        total: activityLogs.length,
        logs: logs
    });
});

// Get log statistics
app.get('/api/logs/stats', requireAuth, (req, res) => {
    const now = new Date();
    const hourAgo = new Date(now - 60 * 60 * 1000);
    const dayAgo = new Date(now - 24 * 60 * 60 * 1000);
    
    const stats = {
        total: activityLogs.length,
        lastHour: activityLogs.filter(l => new Date(l.timestamp) > hourAgo).length,
        last24h: activityLogs.filter(l => new Date(l.timestamp) > dayAgo).length,
        byType: {},
        byAction: {},
        recentErrors: activityLogs.filter(l => l.type === 'error').slice(-10).reverse()
    };
    
    // Count by type
    activityLogs.forEach(l => {
        stats.byType[l.type] = (stats.byType[l.type] || 0) + 1;
        stats.byAction[l.action] = (stats.byAction[l.action] || 0) + 1;
    });
    
    res.json({ success: true, stats });
});

// Add a log entry (for client-side logging)
app.post('/api/logs', requireAuth, (req, res) => {
    const { type, action, details } = req.body;
    
    if (!type || !action) {
        return res.status(400).json({ error: 'type and action are required' });
    }
    
    const logEntry = addLog(type, action, details || {}, req.user?.id);
    res.json({ success: true, log: logEntry });
});

// Clear logs (admin only)
app.delete('/api/logs', requireAuth, (req, res) => {
    if (req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Admin access required' });
    }
    
    activityLogs = [];
    saveLogs();
    res.json({ success: true, message: 'Logs cleared' });
});

// ============================================
// USER MANAGEMENT ENDPOINTS (Admin only)
// ============================================

app.get('/api/users', requireAuth, (req, res) => {
    if (req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Admin access required' });
    }
    
    const userList = Object.values(users).map(u => ({
        id: u.id,
        email: u.email,
        name: u.name,
        role: u.role,
        created: u.created
    }));
    
    res.json({ users: userList });
});

app.post('/api/users', requireAuth, (req, res) => {
    if (req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Admin access required' });
    }
    
    const { email, password, name, role } = req.body;
    
    if (!email || !password) {
        return res.status(400).json({ error: 'Email and password required' });
    }
    
    for (const u of Object.values(users)) {
        if (u.email === email) {
            return res.status(400).json({ error: 'Email already exists' });
        }
    }
    
    const userId = email.split('@')[0].toLowerCase().replace(/[^a-z0-9]/g, '');
    const newUser = {
        id: userId,
        email: email,
        password: hashPassword(password),
        name: name || email.split('@')[0],
        role: role || 'user',
        created: new Date().toISOString()
    };
    
    users[userId] = newUser;
    saveUsers(users);
    
    res.json({
        success: true,
        user: {
            id: newUser.id,
            email: newUser.email,
            name: newUser.name,
            role: newUser.role
        }
    });
});

app.delete('/api/users/:userId', requireAuth, (req, res) => {
    if (req.user.role !== 'admin') {
        return res.status(403).json({ error: 'Admin access required' });
    }
    
    const { userId } = req.params;
    
    if (userId === 'admin') {
        return res.status(400).json({ error: 'Cannot delete admin user' });
    }
    
    if (users[userId]) {
        delete users[userId];
        saveUsers(users);
        res.json({ success: true, message: 'User deleted' });
    } else {
        res.status(404).json({ error: 'User not found' });
    }
});

app.put('/api/users/:userId', requireAuth, (req, res) => {
    const { userId } = req.params;
    
    if (req.user.role !== 'admin' && req.user.id !== userId) {
        return res.status(403).json({ error: 'Access denied' });
    }
    
    const user = users[userId];
    if (!user) {
        return res.status(404).json({ error: 'User not found' });
    }
    
    const { name, password, role } = req.body;
    
    if (name) user.name = name;
    if (password) user.password = hashPassword(password);
    if (role && req.user.role === 'admin') user.role = role;
    
    saveUsers(users);
    
    res.json({
        success: true,
        user: {
            id: user.id,
            email: user.email,
            name: user.name,
            role: user.role
        }
    });
});

// ============================================
// PROTECTED PAGE ROUTES (EJS Rendered)
// ============================================

app.get('/', requireAuth, (req, res) => {
    res.render('pages/home', {
        title: 'Home',
        page: 'home',
        showInfoBtn: true,
        extraScripts: ['home.js', 'multi_file_functions.js', 'file_upload_transcription_v2.js', 'devices_manager.js', 'shared.js'],
        extraStyles: []
    });
});

app.get('/documents', requireAuth, (req, res) => {
    logActivity('PAGE', 'view', { page: 'documents' }, req.user?.email);
    res.render('pages/documents', {
        title: 'Documents',
        page: 'documents',
        showInfoBtn: true,
        extraScripts: ['shared.js'],
        extraStyles: []
    });
});

app.get('/profiles', requireAuth, (req, res) => {
    logActivity('PAGE', 'view', { page: 'profiles' }, req.user?.email);
    res.render('pages/profiles', {
        title: 'Profiles',
        page: 'profiles',
        showInfoBtn: true,
        extraScripts: ['profiles.js', 'shared.js'],
        extraStyles: []
    });
});

app.get('/validation', requireAuth, (req, res) => {
    logActivity('PAGE', 'view', { page: 'validation' }, req.user?.email);
    res.render('pages/validation', {
        title: 'Validation',
        page: 'validation',
        showInfoBtn: true,
        extraScripts: ['shared.js'],
        extraStyles: []
    });
});

app.get('/documentation', requireAuth, (req, res) => {
    logActivity('PAGE', 'view', { page: 'documentation' }, req.user?.email);
    res.render('pages/documentation', {
        title: 'Documentation',
        page: 'documentation',
        showInfoBtn: false,
        extraScripts: ['shared.js'],
        extraStyles: []
    });
});

app.get('/settings', requireAuth, (req, res) => {
    res.render('pages/settings', {
        title: 'Settings',
        page: 'settings',
        showInfoBtn: false,
        extraScripts: ['shared.js'],
        extraStyles: []
    });
});

// Serve static assets (protected) with no-cache for JS files to prevent stale code
app.use(requireAuth, (req, res, next) => {
    if (req.path.endsWith('.js')) {
        res.setHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
        res.setHeader('Pragma', 'no-cache');
        res.setHeader('Expires', '0');
    }
    next();
}, express.static('public'));

// ============================================
// API PROXY ENDPOINTS (All protected)
// ============================================

app.get('/api/devices/status', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/devices/status`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to get devices status' });
    }
});

app.post('/api/devices/connect/:deviceId', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const deviceId = decodeURIComponent(req.params.deviceId);
        
        addLog('device', 'connect_started', { deviceId }, req.user?.id);
        
        const response = await fetch(`${API_BASE}/devices/connect/${encodeURIComponent(deviceId)}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success !== false) {
            addLog('device', 'connected', { deviceId }, req.user?.id);
        } else {
            addLog('device', 'connect_failed', { deviceId, error: data.error }, req.user?.id);
        }
        
        res.json(data);
    } catch (error) {
        addLog('error', 'device_connect_error', { deviceId: req.params.deviceId, error: error.message }, req.user?.id);
        res.status(500).json({ error: 'Failed to connect device' });
    }
});

app.post('/api/devices/disconnect/:deviceId', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const deviceId = decodeURIComponent(req.params.deviceId);
        const response = await fetch(`${API_BASE}/devices/disconnect/${encodeURIComponent(deviceId)}`, {
            method: 'POST'
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to disconnect device' });
    }
});

app.post('/api/devices/select/:deviceId', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const deviceId = decodeURIComponent(req.params.deviceId);
        const response = await fetch(`${API_BASE}/devices/select/${encodeURIComponent(deviceId)}`, {
            method: 'POST'
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to select device' });
    }
});

app.get('/api/status', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/status`);
        const data = await response.json();
        res.json({
            omi_connected: data.device_connected || false,
            audio_processor: data.whisper_ready || false,
            llm_analyzer: data.llm_ready || false,
            database: true,
            services: {
                postgres: false,
                qdrant: false,
                ollama: data.llm_ready || false
            },
            capabilities: {
                real_time_streaming: data.device_connected || false,
                audio_processing: data.whisper_ready || false,
                transcription: data.whisper_ready ? 'whisper' : 'basic_simulation',
                fact_checking: data.llm_ready || false
            }
        });
    } catch (error) {
        res.json({
            omi_connected: false,
            audio_processor: false,
            llm_analyzer: false,
            database: false,
            services: { postgres: false, qdrant: false, ollama: false },
            capabilities: {
                real_time_streaming: false,
                audio_processing: false,
                transcription: 'offline',
                fact_checking: false
            }
        });
    }
});

app.get('/api/scan_ports', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/scan_ports`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.json({ count: 0, ports: [], error: error.message });
    }
});

app.post('/api/connect_device', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/connect_device`, { method: 'POST' });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.json({ success: false, message: `Connection failed: ${error.message}` });
    }
});

app.get('/api/connection/info', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/device/info`);
        const api = await response.json();
        if (api.success && api.device_info) {
            const d = api.device_info;
            res.json({
                connected: true,
                connection_type: d.connection_type || 'usb',
                battery_level: d.battery_percentage ?? 100,
                signal_strength: 4,
            });
        } else {
            res.json({ connected: false });
        }
    } catch (error) {
        res.json({ connected: false });
    }
});

app.get('/api/omi/ports', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/scan_ports`);
        const data = await response.json();
        const omiDetected = data.ports && data.ports.some(port => 
            port.description && port.description.includes('XIAO')
        );
        res.json({
            count: data.ports ? data.ports.length : 0,
            omi_detected: omiDetected,
            omi_device: omiDetected ? data.ports.find(p => p.description?.includes('XIAO'))?.device : null,
            ports: data.ports || []
        });
    } catch (error) {
        res.json({ count: 0, omi_detected: false, omi_device: null, ports: [] });
    }
});

app.get('/api/test/omi', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/test_device`);
        const data = await response.json();
        res.json({
            device_found: data.device_found || false,
            connection_successful: data.connection_successful || false,
            streaming_ready: data.streaming_ready || false,
            device_path: data.device_path || null,
            test_timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.json({
            device_found: false,
            connection_successful: false,
            streaming_ready: false,
            device_path: null,
            test_timestamp: new Date().toISOString()
        });
    }
});

app.post('/api/omi/connect', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/connect_device`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        res.json({
            success: data.success || false,
            message: data.message || 'Connection attempt completed'
        });
    } catch (error) {
        res.json({ success: false, message: `Connection failed: ${error.message}` });
    }
});

app.post('/api/ble/connect', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/connection/switch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'ble' })
        });
        const data = await response.json();
        if (data.success) {
            res.json({
                success: true,
                message: 'BLE connection established',
                device_name: 'BrutallyHonestAI',
                connection_type: data.connection_type
            });
        } else {
            res.json({ success: false, message: data.error || 'BLE connection failed' });
        }
    } catch (error) {
        res.json({ success: false, message: `BLE connection failed: ${error.message}` });
    }
});

app.post('/api/usb/connect', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/connection/switch`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'usb' })
        });
        const data = await response.json();
        if (data.success) {
            res.json({
                success: true,
                message: 'USB connection established',
                device_name: 'BrutallyHonestAI',
                connection_type: data.connection_type
            });
        } else {
            res.json({ success: false, message: data.error || 'USB connection failed' });
        }
    } catch (error) {
        res.json({ success: false, message: `USB connection failed: ${error.message}` });
    }
});

app.get('/api/ble/info', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/device/info`);
        const data = await response.json();
        if (data.success && data.device_info) {
            res.json({
                device_name: data.device_info.device_name,
                battery_level: data.device_info.battery_level,
                recording_count: data.device_info.recording_count,
                storage_used: data.device_info.storage_used,
                uptime: data.device_info.uptime,
                firmware_version: data.device_info.firmware_version,
                connection_type: data.device_info.connection_type,
                is_recording: data.device_info.is_recording,
                last_updated: new Date().toISOString()
            });
        } else {
            res.json({ error: 'Device connection failed', details: data.error || 'Device not connected' });
        }
    } catch (error) {
        res.json({ error: 'Failed to get device info', details: error.message });
    }
});

app.get('/api/device/recordings', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/device/recordings`);
        const data = await response.json();
        if (data.success) {
            res.json({
                success: true,
                recordings: data.recordings,
                total_files: data.total_files,
                total_size: data.total_size,
                total_size_mb: data.total_size_mb,
                connection_method: 'unified_api',
                last_updated: new Date().toISOString()
            });
        } else {
            res.json({ success: false, error: 'Failed to get recordings', details: data.error || 'Device not connected' });
        }
    } catch (error) {
        res.json({ success: false, error: 'Failed to get recordings', details: error.message });
    }
});

app.get('/api/ble/recordings', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/device/recordings`);
        const data = await response.json();
        if (data.success) {
            res.json({
                recordings: data.recordings,
                total_files: data.total_files,
                total_size: data.total_size,
                connection_method: 'unified_api',
                device_status: `Files: ${data.total_files}, Size: ${data.total_size_mb}MB`
            });
        } else {
            res.json({ recordings: [], total_files: 0, total_size: 0, error: data.error || 'Failed to get recordings' });
        }
    } catch (error) {
        res.json({ recordings: [], total_files: 0, total_size: 0, error: error.message });
    }
});

app.post('/api/audio/upload', requireAuth, upload.single('audio'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No audio file provided' });
        }
        const FormData = (await import('form-data')).default;
        const fetch = (await import('node-fetch')).default;
        const formData = new FormData();
        formData.append('file', fs.createReadStream(req.file.path), req.file.originalname);
        const response = await fetch(`${API_BASE}/api/audio/upload`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        fs.unlinkSync(req.file.path);
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to process audio', details: error.message });
    }
});

// Document management endpoints
app.post('/documents/upload', requireAuth, upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            logActivity('DOCUMENT', 'upload_failed', { error: 'No file uploaded' }, req.user?.email);
            return res.status(400).json({ success: false, error: 'No file uploaded' });
        }
        
        logActivity('DOCUMENT', 'upload_started', { 
            filename: req.file.originalname, 
            size: req.file.size,
            type: req.file.mimetype 
        }, req.user?.email);
        
        const fetch = (await import('node-fetch')).default;
        const FormData = (await import('form-data')).default;
        const formData = new FormData();
        formData.append('file', fs.createReadStream(req.file.path), {
            filename: req.file.originalname,
            contentType: req.file.mimetype
        });
        const response = await fetch(`${API_BASE}/documents/upload`, {
            method: 'POST',
            body: formData,
            headers: formData.getHeaders()
        });
        const data = await response.json();
        fs.unlink(req.file.path, (err) => {
            if (err) console.error('Error cleaning up file:', err);
        });
        
        logActivity('DOCUMENT', 'upload_completed', { 
            filename: req.file.originalname, 
            success: data.success 
        }, req.user?.email);
        
        res.json(data);
    } catch (error) {
        logActivity('DOCUMENT', 'upload_error', { error: error.message }, req.user?.email);
        console.error('Document upload proxy error:', error);
        res.status(500).json({ success: false, error: 'Document upload failed' });
    }
});

app.get('/documents/search', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const query = req.query.query;
        const limit = req.query.limit || 5;
        const response = await fetch(`${API_BASE}/documents/search?query=${encodeURIComponent(query)}&limit=${limit}`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ success: false, error: 'Document search failed' });
    }
});

app.post('/documents/query', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/documents/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body)
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ success: false, error: 'Document query failed' });
    }
});

app.get('/documents/stats', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/documents/stats`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ success: false, error: 'Failed to get document stats' });
    }
});

app.delete('/documents/:documentId', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const documentId = req.params.documentId;
        const response = await fetch(`${API_BASE}/documents/${documentId}`, { method: 'DELETE' });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ success: false, error: 'Document deletion failed' });
    }
});

// ============================================
// PROFILES API PROXY
// ============================================

// Clients
app.get('/api/profiles/clients', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/profiles/clients`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Error fetching clients:', error);
        res.status(500).json({ success: false, error: 'Failed to fetch clients' });
    }
});

app.post('/api/profiles/clients', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const params = new URLSearchParams(req.query);
        const response = await fetch(`${API_BASE}/profiles/clients?${params}`, { method: 'POST' });
        const data = await response.json();
        logActivity('PROFILE', 'client_created', { name: req.query.name }, req.user?.email);
        res.json(data);
    } catch (error) {
        console.error('Error creating client:', error);
        res.status(500).json({ success: false, error: 'Failed to create client' });
    }
});

app.delete('/api/profiles/clients/:id', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/profiles/clients/${req.params.id}`, { method: 'DELETE' });
        const data = await response.json();
        logActivity('PROFILE', 'client_deleted', { id: req.params.id }, req.user?.email);
        res.json(data);
    } catch (error) {
        console.error('Error deleting client:', error);
        res.status(500).json({ success: false, error: 'Failed to delete client' });
    }
});

// Brands
app.get('/api/profiles/brands', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/profiles/brands`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Error fetching brands:', error);
        res.status(500).json({ success: false, error: 'Failed to fetch brands' });
    }
});

app.post('/api/profiles/brands', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const params = new URLSearchParams(req.query);
        const response = await fetch(`${API_BASE}/profiles/brands?${params}`, { method: 'POST' });
        const data = await response.json();
        logActivity('PROFILE', 'brand_created', { name: req.query.name }, req.user?.email);
        res.json(data);
    } catch (error) {
        console.error('Error creating brand:', error);
        res.status(500).json({ success: false, error: 'Failed to create brand' });
    }
});

app.delete('/api/profiles/brands/:id', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/profiles/brands/${req.params.id}`, { method: 'DELETE' });
        const data = await response.json();
        logActivity('PROFILE', 'brand_deleted', { id: req.params.id }, req.user?.email);
        res.json(data);
    } catch (error) {
        console.error('Error deleting brand:', error);
        res.status(500).json({ success: false, error: 'Failed to delete brand' });
    }
});

// Persons
app.get('/api/profiles/persons', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/profiles/persons`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Error fetching persons:', error);
        res.status(500).json({ success: false, error: 'Failed to fetch persons' });
    }
});

app.post('/api/profiles/persons', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const params = new URLSearchParams(req.query);
        const response = await fetch(`${API_BASE}/profiles/persons?${params}`, { method: 'POST' });
        const data = await response.json();
        logActivity('PROFILE', 'person_created', { name: req.query.name }, req.user?.email);
        res.json(data);
    } catch (error) {
        console.error('Error creating person:', error);
        res.status(500).json({ success: false, error: 'Failed to create person' });
    }
});

app.delete('/api/profiles/persons/:id', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/profiles/persons/${req.params.id}`, { method: 'DELETE' });
        const data = await response.json();
        logActivity('PROFILE', 'person_deleted', { id: req.params.id }, req.user?.email);
        res.json(data);
    } catch (error) {
        console.error('Error deleting person:', error);
        res.status(500).json({ success: false, error: 'Failed to delete person' });
    }
});

app.post('/api/ai/process_with_validation', requireAuth, async (req, res) => {
    try {
        logActivity('VALIDATION', 'process_started', { 
            textLength: req.body.text?.length || 0 
        }, req.user?.email);
        
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/ai/process_with_validation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body)
        });
        const data = await response.json();
        
        logActivity('VALIDATION', 'process_completed', { 
            success: data.success,
            claimsFound: data.claims?.length || 0
        }, req.user?.email);
        
        res.json(data);
    } catch (error) {
        logActivity('VALIDATION', 'process_error', { error: error.message }, req.user?.email);
        res.status(500).json({ success: false, error: 'Enhanced AI processing failed' });
    }
});

// WebSocket proxy
const wss = new WebSocket.Server({ port: 3002 });
wss.on('connection', (ws) => {
    console.log('Frontend WebSocket client connected');
    const backendWs = new WebSocket('ws://localhost:8000/ws');
    backendWs.on('open', () => {
        ws.send(JSON.stringify({ type: 'connection', data: 'Connected to Voice Insight Platform' }));
    });
    backendWs.on('message', (data) => { ws.send(data); });
    backendWs.on('close', () => { ws.send(JSON.stringify({ type: 'connection', data: 'Disconnected from backend' })); });
    backendWs.on('error', (error) => { ws.send(JSON.stringify({ type: 'error', data: `Backend connection error: ${error.message}` })); });
    ws.on('message', (message) => { if (backendWs.readyState === WebSocket.OPEN) backendWs.send(message); });
    ws.on('close', () => { if (backendWs.readyState === WebSocket.OPEN) backendWs.close(); });
});

// Recording upload endpoint - saves browser recordings to server
app.post('/api/recordings/upload', requireAuth, upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            logActivity('RECORDING', 'upload_failed', { error: 'No file provided' }, req.user?.email);
            return res.status(400).json({ success: false, error: 'No file uploaded' });
        }
        
        const originalName = req.body.filename || req.file.originalname;
        
        // Ensure recordings directory exists
        if (!fs.existsSync(RECORDINGS_DIR)) {
            fs.mkdirSync(RECORDINGS_DIR, { recursive: true });
        }
        
        // Move file to recordings directory
        const targetPath = path.join(RECORDINGS_DIR, originalName);
        fs.renameSync(req.file.path, targetPath);
        
        logActivity('RECORDING', 'upload_success', { 
            filename: originalName, 
            size: req.file.size,
            source: 'browser'
        }, req.user?.email);
        
        // Save to transcription history
        let history = [];
        try { 
            history = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8')); 
        } catch (e) { 
            history = []; 
        }
        
        const historyEntry = {
            id: Date.now().toString(),
            filename: originalName,
            filePath: targetPath,
            timestamp: new Date().toISOString(),
            status: 'pending',
            source: 'browser_recording',
            size: req.file.size,
            user: req.user?.email || 'unknown',
            transcription: null
        };
        
        history.unshift(historyEntry);
        
        // Keep only last 100 recordings
        if (history.length > 100) {
            history = history.slice(0, 100);
        }
        
        fs.writeFileSync(HISTORY_FILE, JSON.stringify(history, null, 2));
        
        res.json({ 
            success: true, 
            filename: originalName,
            path: targetPath,
            size: req.file.size,
            entry: historyEntry
        });
    } catch (error) {
        console.error('Recording upload error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Recording download/delete endpoints
app.get('/api/recordings/download/:filename', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const filename = req.params.filename;
        const response = await fetch(`${API_BASE}/device/recordings/download/${encodeURIComponent(filename)}`);
        if (response.ok) {
            res.setHeader('Content-Type', response.headers.get('content-type') || 'audio/wav');
            const contentDisposition = response.headers.get('content-disposition');
            if (contentDisposition) res.setHeader('Content-Disposition', contentDisposition);
            response.body.pipe(res);
        } else {
            const errorData = await response.json();
            res.status(response.status).json(errorData);
        }
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

app.get('/api/device/recordings/download/:filename', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const filename = req.params.filename;
        const response = await fetch(`${API_BASE}/device/recordings/download/${encodeURIComponent(filename)}`);
        if (response.ok) {
            res.setHeader('Content-Type', response.headers.get('content-type') || 'audio/wav');
            const contentDisposition = response.headers.get('content-disposition');
            if (contentDisposition) res.setHeader('Content-Disposition', contentDisposition);
            response.body.pipe(res);
        } else {
            res.status(response.status).send(await response.text());
        }
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

app.delete('/api/recordings/:filename', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/device/recordings/${encodeURIComponent(req.params.filename)}`, { method: 'DELETE' });
        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

app.delete('/api/device/recordings/:filename', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/device/recordings/${encodeURIComponent(req.params.filename)}`, { method: 'DELETE' });
        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

app.post('/api/ai/process', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const { filename, model, task } = req.body;
        const response = await fetch(`${API_BASE}/ai/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename, model, task })
        });
        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// Direct file transcription endpoint (no device required)
app.post('/api/ai/transcribe-file', requireAuth, upload.single('file'), async (req, res) => {
    const startTime = Date.now();
    
    try {
        if (!req.file) {
            addLog('transcribe', 'failed', { error: 'No audio file provided' }, req.user?.id);
            return res.status(400).json({ success: false, error: 'No audio file provided' });
        }
        
        // Log transcription start
        addLog('transcribe', 'started', {
            filename: req.file.originalname,
            size: req.file.size,
            mimetype: req.file.mimetype,
            validateDocs: req.body.validate_documents === 'true'
        }, req.user?.id);
        
        const FormData = (await import('form-data')).default;
        const fetch = (await import('node-fetch')).default;
        
        const formData = new FormData();
        formData.append('file', fs.createReadStream(req.file.path), {
            filename: req.file.originalname,
            contentType: req.file.mimetype
        });
        
        const validateDocs = req.body.validate_documents === 'true' || req.body.validate_documents === true;
        formData.append('validate_documents', validateDocs.toString());
        
        console.log(`[TRANSCRIBE] Proxying file transcription: ${req.file.originalname} (${req.file.size} bytes)`);
        
        // Use AbortController for timeout - transcription can take 5+ minutes for long audio
        const AbortController = globalThis.AbortController || (await import('abort-controller')).AbortController;
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 10 * 60 * 1000); // 10 minute timeout
        
        const response = await fetch(`${API_BASE}/ai/transcribe-file`, {
            method: 'POST',
            body: formData,
            headers: formData.getHeaders(),
            signal: controller.signal
        });
        
        clearTimeout(timeout);
        
        const data = await response.json();
        const duration = Date.now() - startTime;
        
        // Log transcription completion
        if (response.ok && data.success !== false) {
            addLog('transcribe', 'completed', {
                filename: req.file.originalname,
                duration: duration,
                transcriptLength: data.transcript?.length || 0,
                validated: validateDocs
            }, req.user?.id);
            // Save recording and result
            saveTranscriptionResult(req.file.originalname, req.file.path, data);
        } else {
            addLog('transcribe', 'failed', {
                filename: req.file.originalname,
                duration: duration,
                error: data.error || 'Unknown error'
            }, req.user?.id);
        }
        
        fs.unlink(req.file.path, (err) => {
            if (err) console.error('Error cleaning up file:', err);
        });
        
        res.status(response.status).json(data);
    } catch (error) {
        const duration = Date.now() - startTime;
        console.error('File transcription proxy error:', error);
        
        // Check if this was a timeout/abort error
        const isTimeout = error.name === 'AbortError' || error.message.includes('aborted');
        const errorMessage = isTimeout 
            ? 'Transcription timed out after 10 minutes. Try using the async API (/api/ai/transcribe-file-async) for long audio files.'
            : 'File transcription failed: ' + error.message;
        
        // Log error
        addLog('error', 'transcription_error', {
            filename: req.file?.originalname,
            duration: duration,
            error: errorMessage,
            isTimeout: isTimeout
        }, req.user?.id);
        
        if (req.file && req.file.path) {
            fs.unlink(req.file.path, () => {});
        }
        
        res.status(isTimeout ? 504 : 500).json({ success: false, error: errorMessage });
    }
});

// ============================================
// ASYNC TRANSCRIPTION ENDPOINTS (Background Jobs)
// ============================================

// Submit async transcription job - returns job ID immediately
app.post('/api/ai/transcribe-file-async', requireAuth, upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ success: false, error: 'No audio file provided' });
        }
        
        const FormData = (await import('form-data')).default;
        const fetch = (await import('node-fetch')).default;
        
        const formData = new FormData();
        formData.append('file', fs.createReadStream(req.file.path), {
            filename: req.file.originalname,
            contentType: req.file.mimetype
        });
        
        const validateDocs = req.body.validate_documents === 'true' || req.body.validate_documents === true;
        formData.append('validate_documents', validateDocs.toString());
        
        console.log(`[TRANSCRIBE] Submitting async transcription job: ${req.file.originalname}`);
        
        // 60 second timeout for job submission (should be fast, just file upload)
        const AbortController = globalThis.AbortController || (await import('abort-controller')).AbortController;
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 60 * 1000);
        
        const response = await fetch(`${API_BASE}/ai/transcribe-file-async`, {
            method: 'POST',
            body: formData,
            headers: formData.getHeaders(),
            signal: controller.signal
        });
        
        clearTimeout(timeout);
        
        const data = await response.json();
        
        // Log job submission
        addLog('transcribe', 'job_submitted', {
            filename: req.file.originalname,
            job_id: data.job_id,
            validateDocs: validateDocs
        }, req.user?.id);
        
        // Clean up uploaded file
        fs.unlink(req.file.path, (err) => {
            if (err) console.error('Error cleaning up file:', err);
        });
        
        res.status(response.status).json(data);
    } catch (error) {
        console.error('Async transcription submission error:', error);
        if (req.file && req.file.path) {
            fs.unlink(req.file.path, () => {});
        }
        res.status(500).json({ success: false, error: 'Failed to submit job: ' + error.message });
    }
});

// Get job status
app.get('/api/ai/jobs/:jobId', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/ai/jobs/${req.params.jobId}`);
        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        console.error('Job status error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// List all jobs
app.get('/api/ai/jobs', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/ai/jobs`);
        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        console.error('List jobs error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Delete a job
app.delete('/api/ai/jobs/:jobId', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/ai/jobs/${req.params.jobId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        console.error('Delete job error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Get transcription history with file sizes
app.get('/api/transcription-history', requireAuth, (req, res) => {
    try {
        const history = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8'));
        // Add file size for each item
        const enrichedHistory = history.map(item => {
            let size = null;
            if (item.filePath && fs.existsSync(item.filePath)) {
                try {
                    const stats = fs.statSync(item.filePath);
                    size = stats.size;
                } catch (e) {}
            }
            return { ...item, size };
        });
        res.json({ success: true, history: enrichedHistory, count: enrichedHistory.length });
    } catch (e) {
        res.json({ success: true, history: [], count: 0 });
    }
});

// Download saved recording
app.get('/api/recordings/:filename', requireAuth, (req, res) => {
    const filePath = path.join(RECORDINGS_DIR, req.params.filename);
    if (fs.existsSync(filePath)) {
        res.download(filePath);
    } else {
        res.status(404).json({ error: 'Recording not found' });
    }
});

// Activity log endpoint (admin only)
app.get('/api/activity-log', requireAuth, (req, res) => {
    if (req.user?.role !== 'admin') {
        return res.status(403).json({ error: 'Admin access required' });
    }
    
    try {
        const lines = req.query.lines || 100;
        if (fs.existsSync(ACTIVITY_LOG_FILE)) {
            const content = fs.readFileSync(ACTIVITY_LOG_FILE, 'utf8');
            const allLines = content.trim().split('\n').filter(l => l);
            const recentLines = allLines.slice(-lines);
            res.json({ 
                success: true, 
                logs: recentLines,
                total: allLines.length,
                showing: recentLines.length
            });
        } else {
            res.json({ success: true, logs: [], total: 0, showing: 0 });
        }
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

// Clear activity log (admin only)
app.delete('/api/activity-log', requireAuth, (req, res) => {
    if (req.user?.role !== 'admin') {
        return res.status(403).json({ error: 'Admin access required' });
    }
    
    try {
        fs.writeFileSync(ACTIVITY_LOG_FILE, '');
        res.json({ success: true, message: 'Activity log cleared' });
    } catch (error) {
        res.status(500).json({ success: false, error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`\n=== Brutally Honest Frontend running on http://localhost:${PORT} ===`);
    console.log(`WebSocket server on ws://localhost:3002`);
    console.log(`Multi-user authentication: ENABLED`);
    console.log(`EJS Templates: ENABLED`);
    console.log(`\nDefault Admin Account:`);
    console.log(`   Email: admin@brutallyhonest.io`);
    console.log(`   Password: brutallyhonest2024`);
    console.log(`\nRoutes: /login, /, /documents, /profiles, /validation, /documentation, /settings\n`);
});

// Delete recording from history
app.delete('/api/transcription-history/:id', requireAuth, (req, res) => {
    try {
        const fs = require('fs');
        const id = req.params.id;
        let history = JSON.parse(fs.readFileSync(HISTORY_FILE, 'utf8'));
        const item = history.find(h => h.id === id);
        
        if (item) {
            // Delete the audio file
            if (item.filePath && fs.existsSync(item.filePath)) {
                fs.unlinkSync(item.filePath);
            }
            // Remove from history
            history = history.filter(h => h.id !== id);
            fs.writeFileSync(HISTORY_FILE, JSON.stringify(history, null, 2));
            res.json({ success: true });
        } else {
            res.json({ success: false, error: 'Not found' });
        }
    } catch (e) {
        console.error('Delete error:', e);
        res.json({ success: false, error: e.message });
    }
});

// Re-analyze endpoint proxy
app.post('/api/reanalyze/:id', requireAuth, async (req, res) => {
    try {
        const response = await fetch(`${API_BASE}/api/reanalyze/${req.params.id}`, {
            method: 'POST'
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Re-analyze error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Alias for re-analyze (used by home.js)
app.post('/api/transcription-history/:id/reanalyze', requireAuth, async (req, res) => {
    try {
        const response = await fetch(`${API_BASE}/api/reanalyze/${req.params.id}`, {
            method: 'POST'
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Re-analyze error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});
