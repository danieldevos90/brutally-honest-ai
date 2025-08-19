const express = require('express');
const path = require('path');
const cors = require('cors');
const multer = require('multer');
const WebSocket = require('ws');

const app = express();
const PORT = process.env.PORT || 3000;
const API_BASE = 'http://localhost:8000';

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Multer for file uploads
const upload = multer({ 
    dest: 'uploads/',
    limits: { fileSize: 50 * 1024 * 1024 } // 50MB limit
});

// Serve the main page
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// API proxy endpoints
app.get('/api/status', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch status', details: error.message });
    }
});

app.get('/api/omi/ports', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/api/omi/ports`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch OMI ports', details: error.message });
    }
});

app.get('/api/test/omi', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/api/test/omi`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to test OMI', details: error.message });
    }
});

app.post('/api/omi/connect', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/api/omi/connect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to connect OMI', details: error.message });
    }
});

// Audio upload endpoint
app.post('/api/audio/upload', upload.single('audio'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No audio file provided' });
        }

        const FormData = (await import('form-data')).default;
        const fs = require('fs');
        const fetch = (await import('node-fetch')).default;
        
        const formData = new FormData();
        formData.append('file', fs.createReadStream(req.file.path), req.file.originalname);

        const response = await fetch(`${API_BASE}/api/audio/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        // Clean up uploaded file
        fs.unlinkSync(req.file.path);
        
        res.json(data);
    } catch (error) {
        res.status(500).json({ error: 'Failed to process audio', details: error.message });
    }
});

// WebSocket proxy for real-time streaming
const wss = new WebSocket.Server({ port: 3001 });

wss.on('connection', (ws) => {
    console.log('Frontend WebSocket client connected');
    
    // Connect to backend WebSocket
    const backendWs = new WebSocket('ws://localhost:8000/api/audio/stream');
    
    backendWs.on('open', () => {
        console.log('Connected to backend WebSocket');
        ws.send(JSON.stringify({ type: 'connection', data: 'Connected to Voice Insight Platform' }));
    });
    
    backendWs.on('message', (data) => {
        // Forward backend messages to frontend
        console.log('Backend message:', data.toString());
        ws.send(data);
    });
    
    backendWs.on('close', () => {
        console.log('Backend WebSocket connection closed');
        ws.send(JSON.stringify({ type: 'connection', data: 'Disconnected from backend' }));
    });
    
    backendWs.on('error', (error) => {
        console.error('Backend WebSocket error:', error);
        ws.send(JSON.stringify({ type: 'error', data: `Backend connection error: ${error.message}` }));
    });
    
    // Forward frontend messages to backend
    ws.on('message', (message) => {
        console.log('Frontend message:', message.toString());
        if (backendWs.readyState === WebSocket.OPEN) {
            backendWs.send(message);
        }
    });
    
    ws.on('close', () => {
        console.log('Frontend WebSocket client disconnected');
        if (backendWs.readyState === WebSocket.OPEN) {
            backendWs.close();
        }
    });
    
    ws.on('error', (error) => {
        console.error('Frontend WebSocket error:', error);
    });
});

app.listen(PORT, () => {
    console.log(`🎙️  Voice Insight Frontend running on http://localhost:${PORT}`);
    console.log(`📡 WebSocket server running on ws://localhost:3001`);
    console.log(`🔗 Connecting to backend at ${API_BASE}`);
});
