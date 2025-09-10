const express = require('express');
const path = require('path');
const cors = require('cors');
const multer = require('multer');
const WebSocket = require('ws');

const app = express();
const PORT = process.env.PORT || 3000;
const API_BASE = 'http://localhost:8000'; // API server port

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

// Serve the documents page
app.get('/documents', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'documents.html'));
});

// API proxy endpoints for Brutally Honest AI

// Device management endpoints
app.get('/api/devices/status', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/devices/status`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Devices status proxy error:', error);
        res.status(500).json({ error: 'Failed to get devices status' });
    }
});

app.post('/api/devices/connect/:deviceId', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const deviceId = decodeURIComponent(req.params.deviceId);
        const response = await fetch(`${API_BASE}/devices/connect/${encodeURIComponent(deviceId)}`, {
            method: 'POST'
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Device connect proxy error:', error);
        res.status(500).json({ error: 'Failed to connect device' });
    }
});

app.post('/api/devices/disconnect/:deviceId', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const deviceId = decodeURIComponent(req.params.deviceId);
        const response = await fetch(`${API_BASE}/devices/disconnect/${encodeURIComponent(deviceId)}`, {
            method: 'POST'
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Device disconnect proxy error:', error);
        res.status(500).json({ error: 'Failed to disconnect device' });
    }
});

app.post('/api/devices/select/:deviceId', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const deviceId = decodeURIComponent(req.params.deviceId);
        const response = await fetch(`${API_BASE}/devices/select/${encodeURIComponent(deviceId)}`, {
            method: 'POST'
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Device select proxy error:', error);
        res.status(500).json({ error: 'Failed to select device' });
    }
});

app.get('/api/status', async (req, res) => {
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
        // Return default status if bridge server is not running
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

// Scan serial ports (proxy to backend)
app.get('/api/scan_ports', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/scan_ports`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.json({ count: 0, ports: [], error: error.message });
    }
});

// Connect device (proxy to backend)
app.post('/api/connect_device', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/connect_device`, { method: 'POST' });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        res.json({ success: false, message: `Connection failed: ${error.message}` });
    }
});

// Connection info (convenience proxy)
app.get('/api/connection/info', async (req, res) => {
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

app.get('/api/omi/ports', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/scan_ports`);
        const data = await response.json();
        
        // Transform bridge server response to match frontend expectations
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
        res.json({
            count: 0,
            omi_detected: false,
            omi_device: null,
            ports: []
        });
    }
});

app.get('/api/test/omi', async (req, res) => {
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

app.post('/api/omi/connect', async (req, res) => {
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
        res.json({
            success: false,
            message: `Connection failed: ${error.message}`
        });
    }
});

// BLE connection endpoint
app.post('/api/ble/connect', async (req, res) => {
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
            res.json({
                success: false,
                message: data.error || 'BLE connection failed'
            });
        }
    } catch (error) {
        res.json({
            success: false,
            message: `BLE connection failed: ${error.message}`
        });
    }
});

// USB connection endpoint
app.post('/api/usb/connect', async (req, res) => {
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
            res.json({
                success: false,
                message: data.error || 'USB connection failed'
            });
        }
    } catch (error) {
        res.json({
            success: false,
            message: `USB connection failed: ${error.message}`
        });
    }
});

// BLE device info endpoint  
app.get('/api/ble/info', async (req, res) => {
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
            res.json({
                error: 'Device connection failed',
                details: data.error || 'Device not connected'
            });
        }
    } catch (error) {
        res.json({
            error: 'Failed to get device info',
            details: error.message
        });
    }
});

// Device recordings endpoint (proxy to backend)
app.get('/api/device/recordings', async (req, res) => {
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
            res.json({
                success: false,
                error: 'Failed to get recordings',
                details: data.error || 'Device not connected'
            });
        }
    } catch (error) {
        res.json({
            success: false,
            error: 'Failed to get recordings',
            details: error.message
        });
    }
});

// BLE recordings list endpoint
app.get('/api/ble/recordings', async (req, res) => {
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
            res.json({
                recordings: [],
                total_files: 0,
                total_size: 0,
                error: data.error || 'Failed to get recordings'
            });
        }
    } catch (error) {
        res.json({
            recordings: [],
            total_files: 0,
            total_size: 0,
            error: error.message
        });
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

// Document management endpoints
app.post('/documents/upload', upload.single('file'), async (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ success: false, error: 'No file uploaded' });
        }

        const fetch = (await import('node-fetch')).default;
        const FormData = (await import('form-data')).default;
        const fs = require('fs');

        // Create form data for API server
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

        // Clean up uploaded file
        fs.unlink(req.file.path, (err) => {
            if (err) console.error('Error cleaning up file:', err);
        });

        res.json(data);
    } catch (error) {
        console.error('Document upload proxy error:', error);
        res.status(500).json({ success: false, error: 'Document upload failed' });
    }
});

app.get('/documents/search', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const query = req.query.query;
        const limit = req.query.limit || 5;
        
        const response = await fetch(`${API_BASE}/documents/search?query=${encodeURIComponent(query)}&limit=${limit}`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Document search proxy error:', error);
        res.status(500).json({ success: false, error: 'Document search failed' });
    }
});

app.post('/documents/query', async (req, res) => {
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
        console.error('Document query proxy error:', error);
        res.status(500).json({ success: false, error: 'Document query failed' });
    }
});

app.get('/documents/stats', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/documents/stats`);
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Document stats proxy error:', error);
        res.status(500).json({ success: false, error: 'Failed to get document stats' });
    }
});

app.delete('/documents/:documentId', async (req, res) => {
    try {
        const fetch = (await import('node-fetch')).default;
        const documentId = req.params.documentId;
        const response = await fetch(`${API_BASE}/documents/${documentId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        res.json(data);
    } catch (error) {
        console.error('Document delete proxy error:', error);
        res.status(500).json({ success: false, error: 'Document deletion failed' });
    }
});

// Enhanced AI processing with document validation
app.post('/api/ai/process_with_validation', async (req, res) => {
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
        console.error('Enhanced AI processing proxy error:', error);
        res.status(500).json({ success: false, error: 'Enhanced AI processing failed' });
    }
});

// WebSocket proxy for real-time streaming
const wss = new WebSocket.Server({ port: 3001 });

wss.on('connection', (ws) => {
    console.log('Frontend WebSocket client connected');
    
    // Connect to API server WebSocket
    const backendWs = new WebSocket('ws://localhost:8000/ws');
    
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

// Recording download endpoint - proxy to API server
app.get('/api/recordings/download/:filename', async (req, res) => {
    try {
        const filename = req.params.filename;
        console.log(`Proxying download request for: ${filename}`);
        
        // Proxy to the API server
        const response = await fetch(`${API_BASE}/device/recordings/download/${encodeURIComponent(filename)}`);
        
        if (response.ok) {
            // Stream the file response
            const contentType = response.headers.get('content-type') || 'audio/wav';
            const contentDisposition = response.headers.get('content-disposition');
            
            res.setHeader('Content-Type', contentType);
            if (contentDisposition) {
                res.setHeader('Content-Disposition', contentDisposition);
            }
            
            response.body.pipe(res);
        } else {
            const errorData = await response.json();
            res.status(response.status).json(errorData);
        }
        
    } catch (error) {
        console.error('Download proxy error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Alias: Device-prefixed recording download endpoint for compatibility with frontend HTML
app.get('/api/device/recordings/download/:filename', async (req, res) => {
    try {
        const filename = req.params.filename;
        console.log(`Proxying device download request for: ${filename}`);
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/device/recordings/download/${encodeURIComponent(filename)}`);
        
        if (response.ok) {
            const contentType = response.headers.get('content-type') || 'audio/wav';
            const contentDisposition = response.headers.get('content-disposition');
            res.setHeader('Content-Type', contentType);
            if (contentDisposition) {
                res.setHeader('Content-Disposition', contentDisposition);
            }
            response.body.pipe(res);
        } else {
            const text = await response.text();
            res.status(response.status).send(text);
        }
    } catch (error) {
        console.error('Device download proxy error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// Recording delete endpoint - proxy to API server
app.delete('/api/recordings/:filename', async (req, res) => {
    try {
        const filename = req.params.filename;
        console.log(`Proxying delete request for: ${filename}`);
        
        // Proxy to the API server
        const response = await fetch(`${API_BASE}/device/recordings/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        res.status(response.status).json(data);
        
    } catch (error) {
        console.error('Delete proxy error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Alias: Device-prefixed delete endpoint
app.delete('/api/device/recordings/:filename', async (req, res) => {
    try {
        const filename = req.params.filename;
        console.log(`Proxying device delete request for: ${filename}`);
        const fetch = (await import('node-fetch')).default;
        const response = await fetch(`${API_BASE}/device/recordings/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        res.status(response.status).json(data);
    } catch (error) {
        console.error('Device delete proxy error:', error);
        res.status(500).json({ success: false, error: error.message });
    }
});

// AI processing endpoint - proxy to API server
app.post('/api/ai/process', async (req, res) => {
    try {
        const { filename, model, task } = req.body;
        console.log(`Proxying AI processing request: ${filename} with ${model}`);
        
        // Proxy to the API server for real LLAMA processing
        const response = await fetch(`${API_BASE}/ai/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename, model, task })
        });
        
        const data = await response.json();
        res.status(response.status).json(data);
        
    } catch (error) {
        console.error('AI processing proxy error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.listen(PORT, () => {
    console.log(`Voice Insight Frontend running on http://localhost:${PORT}`);
    console.log(`WebSocket server running on ws://localhost:3001`);
    console.log(`Connecting to Brutally Honest AI API server at ${API_BASE}`);
});
