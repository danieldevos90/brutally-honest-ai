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
const API_BASE = 'http://localhost:8000';

// ============================================
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
app.use('/styles.css', express.static(path.join(__dirname, 'public', 'styles.css')));
app.use('/dynamic-portal.css', express.static(path.join(__dirname, 'public', 'dynamic-portal.css')));
app.use('/manifest.json', express.static(path.join(__dirname, 'public', 'manifest.json')));

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
        extraScripts: ['multi_file_functions.js', 'file_upload_transcription.js', 'devices_manager.js', 'shared.js'],
        extraStyles: []
    });
});

app.get('/documents', requireAuth, (req, res) => {
    res.render('pages/documents', {
        title: 'Documents',
        page: 'documents',
        showInfoBtn: true,
        extraScripts: ['shared.js'],
        extraStyles: []
    });
});

app.get('/profiles', requireAuth, (req, res) => {
    res.render('pages/profiles', {
        title: 'Profiles',
        page: 'profiles',
        showInfoBtn: true,
        extraScripts: ['shared.js'],
        extraStyles: []
    });
});

app.get('/validation', requireAuth, (req, res) => {
    res.render('pages/validation', {
        title: 'Validation',
        page: 'validation',
        showInfoBtn: true,
        extraScripts: ['shared.js'],
        extraStyles: []
    });
});

app.get('/documentation', requireAuth, (req, res) => {
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

// Serve static assets (protected)
app.use(requireAuth, express.static('public'));

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
        const response = await fetch(`${API_BASE}/devices/connect/${encodeURIComponent(deviceId)}`, {
            method: 'POST'
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
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
            return res.status(400).json({ success: false, error: 'No file uploaded' });
        }
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
        res.json(data);
    } catch (error) {
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

app.post('/api/ai/process_with_validation', requireAuth, async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/ai/process_with_validation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(req.body)
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
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
        
        console.log(`📤 Proxying file transcription: ${req.file.originalname} (${req.file.size} bytes)`);
        
        const response = await fetch(`${API_BASE}/ai/transcribe-file`, {
            method: 'POST',
            body: formData,
            headers: formData.getHeaders()
        });
        
        const data = await response.json();
        
        fs.unlink(req.file.path, (err) => {
            if (err) console.error('Error cleaning up file:', err);
        });
        
        res.status(response.status).json(data);
    } catch (error) {
        console.error('File transcription proxy error:', error);
        
        if (req.file && req.file.path) {
            fs.unlink(req.file.path, () => {});
        }
        
        res.status(500).json({ success: false, error: 'File transcription failed: ' + error.message });
    }
});

app.listen(PORT, () => {
    console.log(`\n🎉 Brutally Honest Frontend running on http://localhost:${PORT}`);
    console.log(`📡 WebSocket server on ws://localhost:3002`);
    console.log(`🔐 Multi-user authentication: ENABLED`);
    console.log(`📄 EJS Templates: ENABLED`);
    console.log(`\n👤 Default Admin Account:`);
    console.log(`   Email: admin@brutallyhonest.io`);
    console.log(`   Password: brutallyhonest2024`);
    console.log(`\n📄 Routes: /login, /, /documents, /profiles, /validation, /documentation, /settings\n`);
});
