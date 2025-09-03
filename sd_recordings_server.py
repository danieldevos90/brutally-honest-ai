#!/usr/bin/env python3
"""
SD Card Recordings Web Server
Provides web interface to view, download, and listen to SD card recordings
"""

import serial
import time
import os
import json
import re
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, send_file, request
from flask_cors import CORS
import threading
import queue

app = Flask(__name__)
CORS(app)

class SDRecordingsManager:
    def __init__(self, port='/dev/cu.usbmodem2101', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.recordings_cache = []
        self.last_update = 0
        self.cache_duration = 30  # seconds
        self.downloads_dir = Path('downloads/sd_recordings')
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        
    def connect_to_device(self):
        """Connect to the ESP32 device"""
        try:
            ser = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)  # Wait for device to initialize
            return ser
        except serial.SerialException as e:
            print(f"❌ Error connecting to device: {e}")
            return None
    
    def list_sd_recordings(self, force_refresh=False):
        """Get list of recordings from SD card"""
        current_time = time.time()
        
        # Return cached data if still valid
        if not force_refresh and (current_time - self.last_update) < self.cache_duration:
            return self.recordings_cache
        
        ser = self.connect_to_device()
        if not ser:
            return []
        
        try:
            # Clear buffer
            ser.reset_input_buffer()
            
            # Send list command
            print("📤 Sending 'L' command to list SD card files...")
            ser.write(b'L')
            
            # Read response
            time.sleep(1)  # Give device time to respond
            
            recordings = []
            response_complete = False
            start_time = time.time()
            
            while not response_complete and (time.time() - start_time) < 5:
                if ser.in_waiting:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"Device: {line}")
                        
                        # Parse recording file info
                        if line.startswith('/recordings/') and '.wav' in line:
                            # Extract filename and size from line like: "/recordings/rec_20241201_143022.wav (1234 bytes)"
                            match = re.match(r'(/recordings/[^(]+\.wav)\s*\((\d+)\s*bytes\)', line)
                            if match:
                                filename = match.group(1)
                                size = int(match.group(2))
                                
                                # Extract timestamp from filename
                                timestamp_match = re.search(r'rec_(\d{8})_(\d{6})\.wav', filename)
                                if timestamp_match:
                                    date_str = timestamp_match.group(1)
                                    time_str = timestamp_match.group(2)
                                    try:
                                        timestamp = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                                    except:
                                        timestamp = datetime.now()
                                else:
                                    timestamp = datetime.now()
                                
                                recordings.append({
                                    'filename': os.path.basename(filename),
                                    'full_path': filename,
                                    'size': size,
                                    'size_mb': round(size / (1024 * 1024), 2),
                                    'timestamp': timestamp.isoformat(),
                                    'date_formatted': timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                                    'downloaded': self.is_file_downloaded(os.path.basename(filename))
                                })
                        
                        if "Total files:" in line:
                            response_complete = True
                else:
                    time.sleep(0.1)
            
            # Sort by timestamp (newest first)
            recordings.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Update cache
            self.recordings_cache = recordings
            self.last_update = current_time
            
            return recordings
            
        except Exception as e:
            print(f"❌ Error listing recordings: {e}")
            return []
        finally:
            if ser and ser.is_open:
                ser.close()
    
    def download_recording(self, filename):
        """Download a recording from SD card"""
        ser = self.connect_to_device()
        if not ser:
            return None
        
        try:
            # Clear buffer
            ser.reset_input_buffer()
            
            # Send download command
            download_cmd = f'D{filename}'
            print(f"📤 Sending download command: {download_cmd}")
            ser.write(download_cmd.encode())
            
            # Wait for response
            time.sleep(0.5)
            
            # Read file data
            file_data = bytearray()
            start_time = time.time()
            timeout = 30  # 30 second timeout
            
            print("📥 Receiving file data...")
            while (time.time() - start_time) < timeout:
                if ser.in_waiting:
                    chunk = ser.read(ser.in_waiting)
                    file_data.extend(chunk)
                    
                    # Check for end marker (you might need to adjust this based on your firmware)
                    if b'FILE_END' in chunk or len(file_data) > 10 * 1024 * 1024:  # 10MB max
                        break
                else:
                    time.sleep(0.1)
            
            if file_data:
                # Save to downloads directory
                local_path = self.downloads_dir / filename
                with open(local_path, 'wb') as f:
                    # Remove any text markers from the beginning/end
                    clean_data = file_data
                    if clean_data.startswith(b'FILE_START'):
                        clean_data = clean_data[10:]
                    if clean_data.endswith(b'FILE_END'):
                        clean_data = clean_data[:-8]
                    
                    f.write(clean_data)
                
                print(f"✅ Downloaded {filename} ({len(file_data)} bytes)")
                return local_path
            else:
                print("❌ No data received")
                return None
                
        except Exception as e:
            print(f"❌ Error downloading recording: {e}")
            return None
        finally:
            if ser and ser.is_open:
                ser.close()
    
    def is_file_downloaded(self, filename):
        """Check if file is already downloaded locally"""
        local_path = self.downloads_dir / filename
        return local_path.exists()
    
    def get_local_file_path(self, filename):
        """Get path to local downloaded file"""
        local_path = self.downloads_dir / filename
        return local_path if local_path.exists() else None

# Global manager instance
recordings_manager = SDRecordingsManager()

@app.route('/')
def index():
    """Main page"""
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SD Card Recordings</title>
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
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header p {
            opacity: 0.8;
            font-size: 1.1rem;
        }
        
        .controls {
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-primary {
            background: #007bff;
            color: white;
        }
        
        .btn-primary:hover {
            background: #0056b3;
            transform: translateY(-2px);
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-success:hover {
            background: #1e7e34;
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #545b62;
        }
        
        .status {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #dc3545;
        }
        
        .status-dot.connected {
            background: #28a745;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        
        .recordings-grid {
            padding: 30px;
        }
        
        .recordings-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }
        
        .recordings-count {
            color: #6c757d;
            font-size: 14px;
        }
        
        .recording-card {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .recording-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        }
        
        .recording-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .recording-info h3 {
            color: #2c3e50;
            margin-bottom: 5px;
            font-size: 1.1rem;
        }
        
        .recording-meta {
            color: #6c757d;
            font-size: 13px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .recording-actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        
        .btn-sm {
            padding: 8px 16px;
            font-size: 12px;
        }
        
        .audio-player {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        
        .audio-player audio {
            width: 100%;
            margin-bottom: 10px;
        }
        
        .audio-info {
            font-size: 12px;
            color: #6c757d;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #6c757d;
        }
        
        .spinner {
            display: inline-block;
            width: 30px;
            height: 30px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 30px;
            color: #6c757d;
        }
        
        .empty-state h3 {
            margin-bottom: 10px;
            color: #495057;
        }
        
        @media (max-width: 768px) {
            .controls {
                flex-direction: column;
                align-items: stretch;
            }
            
            .recording-header {
                flex-direction: column;
                gap: 15px;
            }
            
            .recording-actions {
                justify-content: flex-start;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ SD Card Recordings</h1>
            <p>View, download, and listen to your device recordings</p>
        </div>
        
        <div class="controls">
            <div class="status">
                <div class="status-dot" id="connection-status"></div>
                <span id="connection-text">Checking connection...</span>
            </div>
            
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button class="btn btn-primary" onclick="refreshRecordings()">
                    🔄 Refresh List
                </button>
                <button class="btn btn-secondary" onclick="downloadAll()">
                    📥 Download All
                </button>
            </div>
        </div>
        
        <div class="recordings-grid">
            <div class="recordings-header">
                <h2>Recordings</h2>
                <div class="recordings-count" id="recordings-count">Loading...</div>
            </div>
            
            <div id="recordings-container">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading recordings...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let recordings = [];
        
        // Load recordings on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadRecordings();
        });
        
        async function loadRecordings() {
            try {
                const response = await fetch('/api/recordings');
                const data = await response.json();
                
                if (data.success) {
                    recordings = data.recordings;
                    updateConnectionStatus(true);
                    renderRecordings();
                } else {
                    updateConnectionStatus(false);
                    showError(data.error || 'Failed to load recordings');
                }
            } catch (error) {
                updateConnectionStatus(false);
                showError('Connection error: ' + error.message);
            }
        }
        
        function updateConnectionStatus(connected) {
            const statusDot = document.getElementById('connection-status');
            const statusText = document.getElementById('connection-text');
            
            if (connected) {
                statusDot.classList.add('connected');
                statusText.textContent = 'Device connected';
            } else {
                statusDot.classList.remove('connected');
                statusText.textContent = 'Device disconnected';
            }
        }
        
        function renderRecordings() {
            const container = document.getElementById('recordings-container');
            const countEl = document.getElementById('recordings-count');
            
            countEl.textContent = `${recordings.length} recording${recordings.length !== 1 ? 's' : ''}`;
            
            if (recordings.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <h3>No recordings found</h3>
                        <p>No recordings were found on the SD card. Make sure your device is connected and has recorded audio files.</p>
                    </div>
                `;
                return;
            }
            
            container.innerHTML = recordings.map(recording => `
                <div class="recording-card">
                    <div class="recording-header">
                        <div class="recording-info">
                            <h3>${recording.filename}</h3>
                            <div class="recording-meta">
                                <span>📅 ${recording.date_formatted}</span>
                                <span>📊 ${recording.size_mb} MB</span>
                                <span>💾 ${recording.downloaded ? 'Downloaded' : 'On device'}</span>
                            </div>
                        </div>
                        
                        <div class="recording-actions">
                            ${recording.downloaded ? 
                                `<button class="btn btn-success btn-sm" onclick="playRecording('${recording.filename}')">
                                    ▶️ Play
                                </button>` : 
                                `<button class="btn btn-primary btn-sm" onclick="downloadRecording('${recording.filename}')">
                                    📥 Download
                                </button>`
                            }
                            <button class="btn btn-secondary btn-sm" onclick="showRecordingInfo('${recording.filename}')">
                                ℹ️ Info
                            </button>
                        </div>
                    </div>
                    
                    <div class="audio-player" id="player-${recording.filename.replace(/[^a-zA-Z0-9]/g, '_')}">
                        <audio controls>
                            <source src="/api/recording/${recording.filename}" type="audio/wav">
                            Your browser does not support the audio element.
                        </audio>
                        <div class="audio-info">
                            <strong>File:</strong> ${recording.filename} | 
                            <strong>Size:</strong> ${recording.size_mb} MB | 
                            <strong>Recorded:</strong> ${recording.date_formatted}
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        async function refreshRecordings() {
            const container = document.getElementById('recordings-container');
            container.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Refreshing recordings...</p>
                </div>
            `;
            
            await loadRecordings();
        }
        
        async function downloadRecording(filename) {
            try {
                const button = event.target;
                const originalText = button.innerHTML;
                button.innerHTML = '⏳ Downloading...';
                button.disabled = true;
                
                const response = await fetch(`/api/download/${filename}`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.success) {
                    // Refresh the recordings list to update download status
                    await loadRecordings();
                    alert(`✅ ${filename} downloaded successfully!`);
                } else {
                    alert(`❌ Download failed: ${data.error}`);
                }
            } catch (error) {
                alert(`❌ Download error: ${error.message}`);
            }
        }
        
        function playRecording(filename) {
            const playerId = `player-${filename.replace(/[^a-zA-Z0-9]/g, '_')}`;
            const player = document.getElementById(playerId);
            
            if (player.style.display === 'none' || !player.style.display) {
                player.style.display = 'block';
                const audio = player.querySelector('audio');
                audio.load(); // Reload the audio element
            } else {
                player.style.display = 'none';
            }
        }
        
        function showRecordingInfo(filename) {
            const recording = recordings.find(r => r.filename === filename);
            if (recording) {
                alert(`📋 Recording Information\\n\\n` +
                      `Filename: ${recording.filename}\\n` +
                      `Size: ${recording.size_mb} MB (${recording.size} bytes)\\n` +
                      `Recorded: ${recording.date_formatted}\\n` +
                      `Status: ${recording.downloaded ? 'Downloaded locally' : 'On SD card only'}\\n` +
                      `Path: ${recording.full_path}`);
            }
        }
        
        async function downloadAll() {
            if (confirm(`Download all ${recordings.length} recordings? This may take a while.`)) {
                const undownloaded = recordings.filter(r => !r.downloaded);
                
                for (let i = 0; i < undownloaded.length; i++) {
                    const recording = undownloaded[i];
                    try {
                        console.log(`Downloading ${i + 1}/${undownloaded.length}: ${recording.filename}`);
                        const response = await fetch(`/api/download/${recording.filename}`, {
                            method: 'POST'
                        });
                        const data = await response.json();
                        
                        if (!data.success) {
                            console.error(`Failed to download ${recording.filename}: ${data.error}`);
                        }
                    } catch (error) {
                        console.error(`Error downloading ${recording.filename}: ${error.message}`);
                    }
                }
                
                // Refresh the list
                await loadRecordings();
                alert('✅ Batch download completed!');
            }
        }
        
        function showError(message) {
            const container = document.getElementById('recordings-container');
            container.innerHTML = `
                <div class="empty-state">
                    <h3>❌ Error</h3>
                    <p>${message}</p>
                    <button class="btn btn-primary" onclick="loadRecordings()" style="margin-top: 15px;">
                        🔄 Try Again
                    </button>
                </div>
            `;
        }
    </script>
</body>
</html>
    '''

@app.route('/api/recordings')
def api_recordings():
    """Get list of recordings from SD card"""
    try:
        recordings = recordings_manager.list_sd_recordings()
        return jsonify({
            'success': True,
            'recordings': recordings,
            'count': len(recordings)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download/<filename>', methods=['POST'])
def api_download_recording(filename):
    """Download a recording from SD card"""
    try:
        local_path = recordings_manager.download_recording(filename)
        if local_path:
            return jsonify({
                'success': True,
                'message': f'Downloaded {filename}',
                'local_path': str(local_path)
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to download recording'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/recording/<filename>')
def serve_recording(filename):
    """Serve a downloaded recording file"""
    try:
        local_path = recordings_manager.get_local_file_path(filename)
        if local_path and local_path.exists():
            return send_file(local_path, as_attachment=False, mimetype='audio/wav')
        else:
            return jsonify({
                'error': 'Recording not found locally. Download it first.'
            }), 404
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/refresh')
def api_refresh():
    """Force refresh the recordings list"""
    try:
        recordings = recordings_manager.list_sd_recordings(force_refresh=True)
        return jsonify({
            'success': True,
            'recordings': recordings,
            'count': len(recordings)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🎙️  SD Card Recordings Server")
    print("=" * 50)
    print(f"📡 Device port: {recordings_manager.port}")
    print(f"📁 Downloads directory: {recordings_manager.downloads_dir}")
    print(f"🌐 Web interface: http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
