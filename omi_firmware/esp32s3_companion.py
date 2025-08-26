#!/usr/bin/env python3
"""
ESP32S3 OMI Companion Script
Connects to ESP32S3 device via BLE or WiFi for Whisper transcription
"""

import asyncio
import json
import requests
import wave
import numpy as np
import whisper
import argparse
import sys
import time
from pathlib import Path
from bleak import BleakClient, BleakScanner
import threading

class ESP32S3Companion:
    def __init__(self, connection_type="wifi", device_ip="192.168.4.1", device_name="OMI-ESP32S3-BrutalAI"):
        self.connection_type = connection_type
        self.device_ip = device_ip
        self.device_name = device_name
        self.whisper_model = None
        self.ble_client = None
        self.running = False
        
        # BLE UUIDs (must match ESP32S3 firmware)
        self.SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
        self.AUDIO_CHAR_UUID = "12345678-1234-1234-1234-123456789abd"
        self.STATUS_CHAR_UUID = "12345678-1234-1234-1234-123456789abe"
        self.FILE_CHAR_UUID = "12345678-1234-1234-1234-123456789abf"
        self.TRANSCRIPTION_CHAR_UUID = "12345678-1234-1234-1234-123456789ac0"
        
        # Audio buffer for BLE streaming
        self.audio_buffer = []
        self.sample_rate = 16000
        
    async def initialize_whisper(self, model_size="base"):
        """Initialize Whisper model"""
        print(f"Loading Whisper model: {model_size}")
        try:
            self.whisper_model = whisper.load_model(model_size)
            print("Whisper model loaded successfully")
            return True
        except Exception as e:
            print(f"Failed to load Whisper model: {e}")
            return False
    
    async def connect_wifi(self):
        """Connect to ESP32S3 via WiFi"""
        print(f"Connecting to ESP32S3 via WiFi at {self.device_ip}")
        try:
            response = requests.get(f"http://{self.device_ip}/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                print(f"Connected to ESP32S3: {status}")
                return True
        except Exception as e:
            print(f"WiFi connection failed: {e}")
        return False
    
    async def scan_and_connect_ble(self):
        """Scan for and connect to ESP32S3 via BLE"""
        print(f"Scanning for BLE device: {self.device_name}")
        
        devices = await BleakScanner.discover()
        target_device = None
        
        for device in devices:
            if device.name and self.device_name in device.name:
                target_device = device
                break
        
        if not target_device:
            print(f"Device {self.device_name} not found")
            return False
        
        print(f"Found device: {target_device.name} ({target_device.address})")
        
        try:
            self.ble_client = BleakClient(target_device.address)
            await self.ble_client.connect()
            print("BLE connected successfully")
            
            # Subscribe to notifications
            await self.ble_client.start_notify(self.STATUS_CHAR_UUID, self.on_status_notification)
            await self.ble_client.start_notify(self.TRANSCRIPTION_CHAR_UUID, self.on_transcription_request)
            await self.ble_client.start_notify(self.AUDIO_CHAR_UUID, self.on_audio_data)
            
            return True
        except Exception as e:
            print(f"BLE connection failed: {e}")
            return False
    
    async def on_status_notification(self, sender, data):
        """Handle status notifications from ESP32S3"""
        status = data.decode('utf-8')
        print(f"Status: {status}")
    
    async def on_transcription_request(self, sender, data):
        """Handle transcription requests from ESP32S3"""
        request = data.decode('utf-8')
        print(f"Transcription request: {request}")
        
        if request.startswith("TRANSCRIBE_REQUEST:"):
            parts = request.split(":")
            if len(parts) >= 3:
                filename = parts[1]
                sample_count = int(parts[2])
                await self.process_transcription_request(filename, sample_count)
    
    async def on_audio_data(self, sender, data):
        """Handle real-time audio data from ESP32S3"""
        if len(data) >= 4:
            # Extract timestamp (first 4 bytes)
            timestamp = int.from_bytes(data[:4], byteorder='big')
            # Extract audio data (remaining bytes)
            audio_data = np.frombuffer(data[4:], dtype=np.int16)
            self.audio_buffer.extend(audio_data)
    
    async def process_transcription_request(self, filename, sample_count):
        """Process transcription request for a recorded file"""
        if not self.whisper_model:
            print("Whisper model not loaded")
            return
        
        print(f"Processing transcription for {filename} ({sample_count} samples)")
        
        if self.connection_type == "wifi":
            # Download file via WiFi
            audio_data = await self.download_audio_file_wifi(filename)
        else:
            # Use buffered audio data from BLE
            audio_data = np.array(self.audio_buffer[-sample_count:], dtype=np.float32)
            self.audio_buffer.clear()
        
        if audio_data is not None:
            transcription = await self.transcribe_audio(audio_data)
            await self.send_transcription_result(transcription)
    
    async def download_audio_file_wifi(self, filename):
        """Download audio file from ESP32S3 via WiFi"""
        try:
            url = f"http://{self.device_ip}/download?file={filename.split('/')[-1]}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Save temporary file
                temp_file = Path(f"/tmp/{filename.split('/')[-1]}")
                with open(temp_file, 'wb') as f:
                    f.write(response.content)
                
                # Load audio data
                with wave.open(str(temp_file), 'rb') as wav_file:
                    frames = wav_file.readframes(wav_file.getnframes())
                    audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Clean up
                temp_file.unlink()
                return audio_data
        except Exception as e:
            print(f"Failed to download audio file: {e}")
        return None
    
    async def transcribe_audio(self, audio_data):
        """Transcribe audio using Whisper"""
        try:
            print("Transcribing audio...")
            # Whisper expects audio normalized to [-1, 1]
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            
            # Ensure audio is the right length (pad or trim)
            if len(audio_data) < self.sample_rate:  # Less than 1 second
                audio_data = np.pad(audio_data, (0, self.sample_rate - len(audio_data)))
            
            result = self.whisper_model.transcribe(audio_data, language="en")
            transcription = result["text"].strip()
            print(f"Transcription: {transcription}")
            return transcription
        except Exception as e:
            print(f"Transcription failed: {e}")
            return ""
    
    async def send_transcription_result(self, transcription):
        """Send transcription result back to ESP32S3"""
        if self.connection_type == "ble" and self.ble_client:
            try:
                result = f"TRANSCRIPTION:{transcription}"
                await self.ble_client.write_gatt_char(self.TRANSCRIPTION_CHAR_UUID, result.encode('utf-8'))
                print("Transcription sent via BLE")
            except Exception as e:
                print(f"Failed to send transcription via BLE: {e}")
        else:
            print(f"Transcription result: {transcription}")
    
    async def monitor_device(self):
        """Monitor device for new recordings and transcription requests"""
        print("Monitoring device for recordings...")
        self.running = True
        
        while self.running:
            if self.connection_type == "wifi":
                await self.check_wifi_status()
            
            await asyncio.sleep(2)
    
    async def check_wifi_status(self):
        """Check WiFi device status and process new files"""
        try:
            response = requests.get(f"http://{self.device_ip}/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                
                # Check for new recordings
                files_response = requests.get(f"http://{self.device_ip}/list", timeout=5)
                if files_response.status_code == 200:
                    files = files_response.json()
                    
                    # Process any new .wav files
                    for file_info in files:
                        filename = file_info["name"]
                        if filename.endswith(".wav"):
                            # Check if transcription already exists
                            transcription_file = filename.replace(".wav", ".txt")
                            transcription_exists = any(f["name"] == transcription_file for f in files)
                            
                            if not transcription_exists:
                                print(f"New recording found: {filename}")
                                audio_data = await self.download_audio_file_wifi(filename)
                                if audio_data is not None:
                                    transcription = await self.transcribe_audio(audio_data)
                                    # Note: In WiFi mode, transcription is saved by ESP32S3
                                    print(f"Transcription for {filename}: {transcription}")
        except Exception as e:
            pass  # Ignore connection errors during monitoring
    
    async def run(self):
        """Main run loop"""
        print("Starting ESP32S3 Companion...")
        
        # Initialize Whisper
        if not await self.initialize_whisper():
            return False
        
        # Connect to device
        if self.connection_type == "wifi":
            if not await self.connect_wifi():
                return False
        else:
            if not await self.scan_and_connect_ble():
                return False
        
        # Start monitoring
        await self.monitor_device()
        
        return True
    
    async def stop(self):
        """Stop the companion"""
        self.running = False
        if self.ble_client and self.ble_client.is_connected:
            await self.ble_client.disconnect()

async def main():
    parser = argparse.ArgumentParser(description="ESP32S3 OMI Companion for Whisper Transcription")
    parser.add_argument("--connection", choices=["wifi", "ble"], default="wifi", 
                       help="Connection type (default: wifi)")
    parser.add_argument("--ip", default="192.168.4.1", 
                       help="ESP32S3 IP address for WiFi connection (default: 192.168.4.1)")
    parser.add_argument("--device", default="OMI-ESP32S3-BrutalAI", 
                       help="BLE device name (default: OMI-ESP32S3-BrutalAI)")
    parser.add_argument("--model", default="base", 
                       help="Whisper model size (default: base)")
    
    args = parser.parse_args()
    
    companion = ESP32S3Companion(
        connection_type=args.connection,
        device_ip=args.ip,
        device_name=args.device
    )
    
    try:
        await companion.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        await companion.stop()

if __name__ == "__main__":
    asyncio.run(main())
