#!/usr/bin/env python3
"""
Brutally Honest AI - Bridge Server
Connects ESP32S3 device with Web Interface
"""

import asyncio
import websockets
import serial
import serial.tools.list_ports
import json
import threading
import queue
import time
from datetime import datetime
import requests
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
WEBSOCKET_PORT = 8765
SERIAL_BAUDRATE = 115200
ESP32_API_URL = "http://192.168.4.1"  # ESP32 AP mode IP

class BrutalHonestBridge:
    def __init__(self):
        self.websocket_clients = set()
        self.serial_port = None
        self.serial_thread = None
        self.message_queue = queue.Queue()
        self.running = False
        self.device_connected = False
        self.last_status = {
            "device": "disconnected",
            "recording": False,
            "battery": 100,
            "signal": "strong",
            "files": []
        }
        
    def find_esp32_port(self):
        """Find ESP32 serial port automatically"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # Check for ESP32 identifiers
            if any(x in port.description.lower() for x in ['esp32', 'cp210', 'ch340', 'ch9102']):
                return port.device
            # Check for Silicon Labs or WCH chips
            if port.vid == 0x10C4 or port.vid == 0x1A86:
                return port.device
        return None
        
    def connect_serial(self):
        """Connect to ESP32 via serial"""
        port = self.find_esp32_port()
        if not port:
            print("ESP32 not found on any serial port")
            return False
            
        try:
            self.serial_port = serial.Serial(port, SERIAL_BAUDRATE, timeout=1)
            print(f"Connected to ESP32 on {port}")
            self.device_connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to serial port: {e}")
            return False
            
    def serial_reader(self):
        """Read data from serial port"""
        while self.running:
            if not self.serial_port or not self.serial_port.is_open:
                time.sleep(1)
                if not self.connect_serial():
                    continue
                    
            try:
                if self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8').strip()
                    if line:
                        self.process_serial_data(line)
            except Exception as e:
                print(f"Serial read error: {e}")
                self.device_connected = False
                self.serial_port = None
                time.sleep(1)
                
    def process_serial_data(self, data):
        """Process data from ESP32"""
        try:
            # Parse different message types from ESP32
            if data.startswith("[STATUS]"):
                status = data.replace("[STATUS]", "").strip()
                self.update_status("recording", status == "RECORDING")
                
            elif data.startswith("[FILE_SAVED]"):
                filename = data.replace("[FILE_SAVED]", "").strip()
                self.broadcast_message({
                    "type": "file_saved",
                    "filename": filename,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif data.startswith("[TRANSCRIPTION]"):
                text = data.replace("[TRANSCRIPTION]", "").strip()
                self.broadcast_message({
                    "type": "transcription",
                    "text": text,
                    "timestamp": datetime.now().isoformat()
                })
                
            elif data.startswith("[BATTERY]"):
                level = int(data.replace("[BATTERY]", "").strip())
                self.update_status("battery", level)
                
            # Log all serial data for debugging
            print(f"Serial: {data}")
            
        except Exception as e:
            print(f"Error processing serial data: {e}")
            
    def update_status(self, key, value):
        """Update status and broadcast changes"""
        if self.last_status.get(key) != value:
            self.last_status[key] = value
            self.broadcast_status()
            
    def broadcast_status(self):
        """Broadcast current status to all websocket clients"""
        self.broadcast_message({
            "type": "status",
            "data": self.last_status
        })
        
    def broadcast_message(self, message):
        """Send message to all connected websocket clients"""
        if self.websocket_clients:
            asyncio.create_task(self._broadcast(json.dumps(message)))
            
    async def _broadcast(self, message):
        """Async broadcast to websocket clients"""
        if self.websocket_clients:
            await asyncio.gather(
                *[client.send(message) for client in self.websocket_clients],
                return_exceptions=True
            )
            
    async def websocket_handler(self, websocket, path):
        """Handle websocket connections"""
        # Register client
        self.websocket_clients.add(websocket)
        print(f"Client connected. Total clients: {len(self.websocket_clients)}")
        
        # Send initial status
        await websocket.send(json.dumps({
            "type": "status",
            "data": self.last_status
        }))
        
        try:
            async for message in websocket:
                data = json.loads(message)
                await self.handle_websocket_message(websocket, data)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Unregister client
            self.websocket_clients.remove(websocket)
            print(f"Client disconnected. Total clients: {len(self.websocket_clients)}")
            
    async def handle_websocket_message(self, websocket, data):
        """Handle messages from web interface"""
        msg_type = data.get('type')
        
        if msg_type == 'start_recording':
            # Send command to ESP32
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(b"START_RECORDING\n")
                
        elif msg_type == 'stop_recording':
            # Send command to ESP32
            if self.serial_port and self.serial_port.is_open:
                self.serial_port.write(b"STOP_RECORDING\n")
                
        elif msg_type == 'get_files':
            # Try to get files from ESP32 web server
            await self.fetch_files_from_esp32()
            
        elif msg_type == 'download_file':
            filename = data.get('filename')
            if filename:
                await self.download_file_from_esp32(filename, websocket)
                
    async def fetch_files_from_esp32(self):
        """Fetch file list from ESP32 web server"""
        try:
            # First try WiFi connection
            response = requests.get(f"{ESP32_API_URL}/list", timeout=5)
            if response.status_code == 200:
                files = response.json()
                self.last_status['files'] = files
                self.broadcast_status()
                return
        except:
            pass
            
        # Fallback to serial command
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.write(b"LIST_FILES\n")
            
    async def download_file_from_esp32(self, filename, websocket):
        """Download file from ESP32 and send to client"""
        try:
            # Try WiFi download
            response = requests.get(f"{ESP32_API_URL}/download?file={filename}", timeout=30)
            if response.status_code == 200:
                # Send file data to client
                await websocket.send(json.dumps({
                    "type": "file_data",
                    "filename": filename,
                    "data": response.content.hex()  # Convert to hex for JSON
                }))
                return
        except:
            pass
            
        # Fallback notification
        await websocket.send(json.dumps({
            "type": "error",
            "message": f"Failed to download {filename}"
        }))
        
    async def start_websocket_server(self):
        """Start the websocket server"""
        print(f"Starting WebSocket server on port {WEBSOCKET_PORT}")
        async with websockets.serve(self.websocket_handler, "localhost", WEBSOCKET_PORT):
            await asyncio.Future()  # Run forever
            
    def start(self):
        """Start the bridge server"""
        print("Brutally Honest AI Bridge Server")
        print("================================")
        
        self.running = True
        
        # Start serial reader thread
        self.serial_thread = threading.Thread(target=self.serial_reader)
        self.serial_thread.start()
        
        # Try initial connection
        self.connect_serial()
        
        # Start websocket server
        try:
            asyncio.run(self.start_websocket_server())
        except KeyboardInterrupt:
            print("\nShutting down...")
            
        self.running = False
        if self.serial_thread:
            self.serial_thread.join()
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            
if __name__ == "__main__":
    bridge = BrutalHonestBridge()
    bridge.start()
