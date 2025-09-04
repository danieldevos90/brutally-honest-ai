#!/usr/bin/env python3
"""
Web Interface for ESP32S3 Recording Transcription
Provides a clean web UI to select recordings and run AI transcription
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from audio.unified_connector import UnifiedESP32S3Connector, ConnectionType
from audio.processor import AudioProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="ESP32S3 AI Transcription", version="1.0.0")

# Global instances
connector: Optional[UnifiedESP32S3Connector] = None
audio_processor: Optional[AudioProcessor] = None

# Create templates directory
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)

# Create static directory  
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

# Setup templates and static files
templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

async def get_connector():
    """Get or create connector instance"""
    global connector
    if connector is None:
        connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
        await connector.initialize()
    return connector

async def get_processor():
    """Get or create audio processor instance"""
    global audio_processor
    if audio_processor is None:
        audio_processor = AudioProcessor()
        await audio_processor.initialize()
    return audio_processor

@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup"""
    logger.info("🚀 Starting ESP32S3 AI Transcription Web Interface...")
    try:
        await get_connector()
        await get_processor()
        logger.info("✅ All systems initialized")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global connector, audio_processor
    logger.info("🛑 Shutting down...")
    
    if audio_processor:
        await audio_processor.cleanup()
    if connector:
        await connector.disconnect()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main page with recording selection and transcription interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/recordings")
async def list_recordings():
    """Get list of available recordings"""
    try:
        conn = await get_connector()
        recordings = await conn.get_recordings()
        
        recordings_data = []
        for rec in recordings:
            recordings_data.append({
                "name": rec.name,
                "size": rec.size,
                "size_mb": round(rec.size / (1024 * 1024), 2),
                "date": getattr(rec, 'date', None)
            })
        
        return {
            "success": True,
            "recordings": recordings_data,
            "total": len(recordings_data)
        }
        
    except Exception as e:
        logger.error(f"Failed to list recordings: {e}")
        return {
            "success": False,
            "error": str(e),
            "recordings": [],
            "total": 0
        }

@app.post("/api/transcribe/{filename}")
async def transcribe_recording(filename: str, background_tasks: BackgroundTasks):
    """Transcribe a specific recording"""
    try:
        conn = await get_connector()
        processor = await get_processor()
        
        logger.info(f"🎤 Starting transcription of {filename}...")
        
        # Download file
        file_data = await conn.download_file(filename)
        if not file_data:
            raise HTTPException(status_code=404, detail=f"Recording {filename} not found")
        
        # Save to temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(file_data)
            temp_path = temp_file.name
        
        try:
            # Transcribe
            result = await processor.process_file(temp_path)
            
            # Format response
            response_data = {
                "success": True,
                "filename": filename,
                "transcript": result.transcript,
                "duration_s": result.audio_duration,
                "confidence": result.confidence,
                "speakers": [
                    {
                        "speaker_id": speaker.speaker_id,
                        "start_time": speaker.start_time,
                        "end_time": speaker.end_time,
                        "text": speaker.text,
                        "confidence": speaker.confidence
                    }
                    for speaker in result.speakers
                ],
                "timestamp": result.timestamp.isoformat(),
                "processing_time": "completed"
            }
            
            logger.info(f"✅ Transcription completed for {filename}")
            return response_data
            
        finally:
            # Schedule cleanup
            background_tasks.add_task(os.unlink, temp_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transcription failed for {filename}: {e}")
        return {
            "success": False,
            "filename": filename,
            "error": str(e),
            "transcript": "",
            "duration_s": 0.0,
            "confidence": 0.0,
            "speakers": []
        }

@app.get("/api/status")
async def get_status():
    """Get system status"""
    try:
        conn = await get_connector()
        processor = await get_processor()
        
        device_status = await conn.get_device_status()
        
        return {
            "success": True,
            "device_connected": device_status.connected if device_status else False,
            "connection_type": device_status.connection_type.value if device_status else None,
            "recordings_count": device_status.files if device_status else 0,
            "whisper_ready": processor.is_ready(),
            "whisper_model": processor.whisper_model_name
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "device_connected": False,
            "whisper_ready": False
        }

# Create the HTML template
html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32S3 AI Transcription</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        .header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .content {
            padding: 30px;
        }
        
        .status-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #f8f9fa;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #28a745;
        }
        
        .status-dot.error {
            background: #dc3545;
        }
        
        .recordings-section {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 1.5rem;
            color: #2c3e50;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .recordings-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .recording-card {
            background: #f8f9fa;
            border: 2px solid #e9ecef;
            border-radius: 15px;
            padding: 20px;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .recording-card:hover {
            border-color: #3498db;
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.15);
        }
        
        .recording-card.selected {
            border-color: #3498db;
            background: #f5f5f5;
        }
        
        .recording-name {
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 8px;
        }
        
        .recording-meta {
            color: #6c757d;
            font-size: 0.9rem;
        }
        
        .transcribe-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            text-align: center;
        }
        
        .transcribe-btn {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-bottom: 20px;
        }
        
        .transcribe-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(40, 167, 69, 0.3);
        }
        
        .transcribe-btn:disabled {
            background: #6c757d;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .loading {
            display: none;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin: 20px 0;
        }
        
        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .results {
            display: none;
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-top: 30px;
            border-left: 5px solid #28a745;
        }
        
        .results h3 {
            color: #2c3e50;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .transcript-text {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            font-size: 1.1rem;
            line-height: 1.6;
            color: #2c3e50;
            margin-bottom: 20px;
        }
        
        .metadata {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .meta-item {
            background: #f5f5f5;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        
        .meta-label {
            font-size: 0.9rem;
            color: #6c757d;
            margin-bottom: 5px;
        }
        
        .meta-value {
            font-size: 1.2rem;
            font-weight: 600;
            color: #2c3e50;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 5px solid #dc3545;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎤 ESP32S3 AI Transcription</h1>
            <p>Select a recording and let Whisper AI transcribe it for you</p>
        </div>
        
        <div class="content">
            <div class="status-bar">
                <div class="status-item">
                    <div class="status-dot" id="device-status"></div>
                    <span id="device-text">Checking device...</span>
                </div>
                <div class="status-item">
                    <div class="status-dot" id="whisper-status"></div>
                    <span id="whisper-text">Checking Whisper AI...</span>
                </div>
                <div class="status-item">
                    <span id="recordings-count">0 recordings</span>
                </div>
            </div>
            
            <div class="recordings-section">
                <h2 class="section-title">
                    📁 Available Recordings
                </h2>
                <div class="recordings-grid" id="recordings-grid">
                    <!-- Recordings will be loaded here -->
                </div>
            </div>
            
            <div class="transcribe-section">
                <button class="transcribe-btn" id="transcribe-btn" disabled>
                    Select a recording to transcribe
                </button>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <span>Transcribing with Whisper AI...</span>
                </div>
                
                <div class="results" id="results">
                    <h3>🎯 Transcription Results</h3>
                    <div class="transcript-text" id="transcript-text"></div>
                    <div class="metadata">
                        <div class="meta-item">
                            <div class="meta-label">Duration</div>
                            <div class="meta-value" id="duration">-</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">Confidence</div>
                            <div class="meta-value" id="confidence">-</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">Speakers</div>
                            <div class="meta-value" id="speakers">-</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">File</div>
                            <div class="meta-value" id="filename">-</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let selectedRecording = null;
        
        // Load system status
        async function loadStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                // Update device status
                const deviceStatus = document.getElementById('device-status');
                const deviceText = document.getElementById('device-text');
                if (data.device_connected) {
                    deviceStatus.classList.remove('error');
                    deviceText.textContent = `Device connected (${data.connection_type})`;
                } else {
                    deviceStatus.classList.add('error');
                    deviceText.textContent = 'Device disconnected';
                }
                
                // Update Whisper status
                const whisperStatus = document.getElementById('whisper-status');
                const whisperText = document.getElementById('whisper-text');
                if (data.whisper_ready) {
                    whisperStatus.classList.remove('error');
                    whisperText.textContent = `Whisper AI ready (${data.whisper_model})`;
                } else {
                    whisperStatus.classList.add('error');
                    whisperText.textContent = 'Whisper AI not ready';
                }
                
                // Update recordings count
                document.getElementById('recordings-count').textContent = 
                    `${data.recordings_count} recordings`;
                    
            } catch (error) {
                console.error('Failed to load status:', error);
            }
        }
        
        // Load recordings
        async function loadRecordings() {
            try {
                const response = await fetch('/api/recordings');
                const data = await response.json();
                
                const grid = document.getElementById('recordings-grid');
                grid.innerHTML = '';
                
                if (data.success && data.recordings.length > 0) {
                    data.recordings.forEach(recording => {
                        const card = document.createElement('div');
                        card.className = 'recording-card';
                        card.innerHTML = `
                            <div class="recording-name">${recording.name}</div>
                            <div class="recording-meta">
                                ${recording.size_mb} MB
                                ${recording.date ? '• ' + new Date(recording.date).toLocaleDateString() : ''}
                            </div>
                        `;
                        
                        card.addEventListener('click', () => selectRecording(recording, card));
                        grid.appendChild(card);
                    });
                } else {
                    grid.innerHTML = '<p style="text-align: center; color: #6c757d; grid-column: 1 / -1;">No recordings found</p>';
                }
                
            } catch (error) {
                console.error('Failed to load recordings:', error);
                document.getElementById('recordings-grid').innerHTML = 
                    '<p style="text-align: center; color: #dc3545; grid-column: 1 / -1;">Error loading recordings</p>';
            }
        }
        
        // Select recording
        function selectRecording(recording, cardElement) {
            // Remove previous selection
            document.querySelectorAll('.recording-card').forEach(card => {
                card.classList.remove('selected');
            });
            
            // Select current
            cardElement.classList.add('selected');
            selectedRecording = recording;
            
            // Update button
            const btn = document.getElementById('transcribe-btn');
            btn.textContent = `Transcribe ${recording.name}`;
            btn.disabled = false;
        }
        
        // Transcribe recording
        async function transcribeRecording() {
            if (!selectedRecording) return;
            
            const btn = document.getElementById('transcribe-btn');
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            
            // Show loading
            btn.disabled = true;
            loading.style.display = 'flex';
            results.style.display = 'none';
            
            try {
                const response = await fetch(`/api/transcribe/${selectedRecording.name}`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    // Show results
                    document.getElementById('transcript-text').textContent = data.transcript;
                    document.getElementById('duration').textContent = `${data.duration_s.toFixed(1)}s`;
                    document.getElementById('confidence').textContent = `${(data.confidence * 100).toFixed(1)}%`;
                    document.getElementById('speakers').textContent = data.speakers.length;
                    document.getElementById('filename').textContent = data.filename;
                    
                    results.style.display = 'block';
                } else {
                    // Show error
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'error';
                    errorDiv.textContent = `Error: ${data.error}`;
                    results.parentNode.insertBefore(errorDiv, results);
                    setTimeout(() => errorDiv.remove(), 5000);
                }
                
            } catch (error) {
                console.error('Transcription failed:', error);
                const errorDiv = document.createElement('div');
                errorDiv.className = 'error';
                errorDiv.textContent = `Network error: ${error.message}`;
                results.parentNode.insertBefore(errorDiv, results);
                setTimeout(() => errorDiv.remove(), 5000);
            } finally {
                // Hide loading
                loading.style.display = 'none';
                btn.disabled = false;
                btn.textContent = `Transcribe ${selectedRecording.name}`;
            }
        }
        
        // Event listeners
        document.getElementById('transcribe-btn').addEventListener('click', transcribeRecording);
        
        // Initialize
        loadStatus();
        loadRecordings();
        
        // Refresh every 30 seconds
        setInterval(() => {
            loadStatus();
            loadRecordings();
        }, 30000);
    </script>
</body>
</html>'''

# Write the template file
with open(templates_dir / "index.html", "w") as f:
    f.write(html_template)

if __name__ == "__main__":
    print("🚀 Starting ESP32S3 AI Transcription Web Interface...")
    print("📡 Access at: http://localhost:8080")
    print("🎤 Select recordings and transcribe with Whisper AI")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )
