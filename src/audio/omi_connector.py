"""
ESP32S3 Brutally Honest AI USB Connector
Handles direct communication with ESP32S3 device via USB serial
"""

import asyncio
import logging
import serial
import serial.tools.list_ports
import struct
import time
import json
from typing import AsyncGenerator, Optional, Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AudioChunk:
    """Audio data chunk from ESP32S3 device"""
    data: bytes
    timestamp: float
    sample_rate: int = 16000
    channels: int = 1
    format: str = "PCM"

@dataclass
class RecordingInfo:
    """Recording file information"""
    name: str
    size: int
    date: Optional[str] = None

class ESP32S3Connector:
    """Connector for ESP32S3 Brutally Honest AI device via USB serial"""
    
    def __init__(self, baudrate: int = 115200):
        """
        Initialize ESP32S3 connector
        
        Args:
            baudrate: Serial communication baud rate (default: 115200)
        """
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.is_streaming = False
        self.is_connected = False
        
        # Device identification
        self.device_port: Optional[str] = None
        self.device_info: Dict[str, Any] = {}
        
        # Audio configuration
        self.sample_rate = 16000  # 16kHz for Whisper
        self.channels = 1  # Mono
        self.bit_depth = 16  # 16-bit PCM
        self.chunk_size = 1024  # Bytes per chunk
        
        # Serialize all serial I/O to avoid overlapping commands from concurrent requests
        self._io_lock = asyncio.Lock()
        
    async def initialize(self) -> bool:
        """Initialize connection to ESP32S3 Brutally Honest AI device"""
        try:
            # Find ESP32S3 device
            device_port = self._find_esp32s3_device()
            if not device_port:
                logger.error("ESP32S3 Brutally Honest AI device not found. Please check USB connection.")
                return False
            
            self.device_port = device_port
            
            # Establish serial connection
            self.serial_connection = serial.Serial(
                port=device_port,
                baudrate=self.baudrate,
                timeout=2.0,
                write_timeout=2.0
            )
            
            # Wait for device to be ready
            await asyncio.sleep(2)
            
            # Clear any existing data
            self.serial_connection.flushInput()
            self.serial_connection.flushOutput()
            
            # Test device communication
            if await self._test_device_communication():
                self.is_connected = True
                logger.info(f"ESP32S3 Brutally Honest AI connected successfully on {device_port}")
                return True
            else:
                logger.error("Failed to communicate with ESP32S3 device")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize ESP32S3 connector: {e}")
            return False
    
    def _find_esp32s3_device(self) -> Optional[str]:
        """Find ESP32S3 device in connected USB devices with comprehensive scanning"""
        ports = serial.tools.list_ports.comports()
        
        logger.info(f"🔍 Scanning {len(ports)} USB ports for ESP32S3 device...")
        
        # Priority 1: Check by VID/PID (most reliable)
        for port in ports:
            if hasattr(port, 'vid') and hasattr(port, 'pid'):
                vid = port.vid
                pid = port.pid
                
                # ESP32S3 specific VID/PIDs
                esp32s3_ids = [
                    (0x303A, 0x1001),  # Espressif ESP32S3 
                    (0x303A, 0x0002),  # Espressif ESP32S3 (alternate)
                    (0x303A, 0x4001),  # Espressif ESP32S3 (JTAG)
                    (0x2886, 0x0045),  # Seeed XIAO ESP32S3
                    (0x2886, 0x8045),  # Seeed XIAO ESP32S3 (alternate)
                ]
                
                for expected_vid, expected_pid in esp32s3_ids:
                    if vid == expected_vid and pid == expected_pid:
                        logger.info(f"✅ Found ESP32S3 by VID/PID: {port.device} (VID:{vid:04X}, PID:{pid:04X})")
                        return port.device
        
        # Priority 2: Check by device description keywords
        esp32_keywords = [
            'esp32', 'esp32s3', 'xiao', 'seeed', 'brutally', 'honest',
            'omi', 'devkit', 'espressif'
        ]
        
        for port in ports:
            if port.description:
                desc_lower = port.description.lower()
                for keyword in esp32_keywords:
                    if keyword in desc_lower:
                        logger.info(f"✅ Found ESP32S3 by description: {port.device} ({port.description})")
                        return port.device
        
        # Priority 3: Check by manufacturer
        esp32_manufacturers = ['espressif', 'seeed', 'seeed studio']
        
        for port in ports:
            if hasattr(port, 'manufacturer') and port.manufacturer:
                manufacturer_lower = port.manufacturer.lower()
                for mfg in esp32_manufacturers:
                    if mfg in manufacturer_lower:
                        logger.info(f"✅ Found ESP32S3 by manufacturer: {port.device} (Mfg: {port.manufacturer})")
                        return port.device
        
        # Priority 4: Check common USB serial patterns (less reliable)
        usb_serial_patterns = [
            '/dev/cu.usbmodem',     # macOS USB modem
            '/dev/cu.usbserial',    # macOS USB serial
            '/dev/ttyUSB',          # Linux USB serial
            '/dev/ttyACM',          # Linux USB ACM
            'COM'                   # Windows COM port
        ]
        
        for port in ports:
            for pattern in usb_serial_patterns:
                if pattern in port.device:
                    # Additional validation for generic patterns
                    if port.description and any(kw in port.description.lower() 
                                              for kw in ['usb', 'serial', 'uart', 'cdc']):
                        logger.info(f"⚠️  Found potential ESP32S3 by pattern: {port.device} ({port.description})")
                        return port.device
        
        # Priority 5: Last resort - try any USB serial device
        logger.warning("🔍 No ESP32S3 device found by standard methods, checking all USB serial devices...")
        for port in ports:
            if port.description and 'usb' in port.description.lower():
                logger.info(f"🔄 Trying generic USB device: {port.device} ({port.description})")
                return port.device
        
        # List all available ports for debugging
        logger.warning("❌ No ESP32S3 device found. Available serial ports:")
        for port in ports:
            vid_str = f"{port.vid:04X}" if hasattr(port, 'vid') and port.vid else 'N/A'
            pid_str = f"{port.pid:04X}" if hasattr(port, 'pid') and port.pid else 'N/A'
            mfg_str = getattr(port, 'manufacturer', 'N/A') or 'N/A'
            logger.warning(f"  📍 {port.device}: {port.description} (VID:{vid_str}, PID:{pid_str}, Mfg:{mfg_str})")
        
        return None
    
    @classmethod
    def get_all_serial_ports(cls) -> List[Dict[str, Any]]:
        """Get detailed information about all available serial ports"""
        ports = serial.tools.list_ports.comports()
        port_list = []
        
        for port in ports:
            vid = getattr(port, 'vid', None)
            pid = getattr(port, 'pid', None)
            manufacturer = getattr(port, 'manufacturer', None)
            
            # Determine if this looks like an ESP32S3 device
            is_esp32s3 = False
            confidence = 0
            
            # Check VID/PID
            if vid and pid:
                esp32s3_ids = [
                    (0x303A, 0x1001), (0x303A, 0x0002), (0x303A, 0x4001),
                    (0x2886, 0x0045), (0x2886, 0x8045)
                ]
                if (vid, pid) in esp32s3_ids:
                    is_esp32s3 = True
                    confidence = 95
            
            # Check description
            if not is_esp32s3 and port.description:
                desc_lower = port.description.lower()
                esp32_keywords = ['esp32', 'esp32s3', 'xiao', 'seeed', 'brutally', 'honest', 'omi', 'devkit']
                if any(kw in desc_lower for kw in esp32_keywords):
                    is_esp32s3 = True
                    confidence = 85
            
            # Check manufacturer
            if not is_esp32s3 and manufacturer:
                mfg_lower = manufacturer.lower()
                if any(mfg in mfg_lower for mfg in ['espressif', 'seeed']):
                    is_esp32s3 = True
                    confidence = 75
            
            # Generic USB serial device
            if not is_esp32s3 and port.description:
                if 'usb' in port.description.lower() and any(kw in port.description.lower() for kw in ['serial', 'uart', 'cdc']):
                    confidence = 30  # Low confidence but possible
            
            port_info = {
                "device": port.device,
                "description": port.description or "Unknown Device",
                "vid": f"{vid:04X}" if vid else None,
                "pid": f"{pid:04X}" if pid else None,
                "vid_decimal": vid,
                "pid_decimal": pid,
                "manufacturer": manufacturer,
                "is_esp32s3": is_esp32s3,
                "confidence": confidence,
                "hwid": getattr(port, 'hwid', None)
            }
            port_list.append(port_info)
        
        # Sort by confidence (ESP32S3 devices first)
        port_list.sort(key=lambda x: x['confidence'], reverse=True)
        return port_list
    
    async def _test_device_communication(self) -> bool:
        """Test communication with ESP32S3 device"""
        try:
            async with self._io_lock:
                # Send status request
                self._send_command("S")
                response = await self._read_response(timeout=3.0)
            
            if response:
                response_str = response.decode('utf-8', errors='ignore')
                logger.info(f"ESP32S3 device response: {response_str}")
                
                # Parse device info
                self.device_info = self._parse_status_response(response_str)
                return True
            
            # Try device info command
            async with self._io_lock:
                self._send_command("I")
                response = await self._read_response(timeout=3.0)
            
            if response:
                response_str = response.decode('utf-8', errors='ignore')
                logger.info(f"ESP32S3 device info: {response_str}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Device communication test error: {e}")
            return False
    
    def _send_command(self, command: str):
        """Send command to ESP32S3 device"""
        if self.serial_connection and self.serial_connection.is_open:
            # Ensure newline termination so firmware readStringUntil('\n') completes
            if not command.endswith('\n'):
                command = command + '\n'
            cmd_bytes = command.encode('utf-8')
            self.serial_connection.write(cmd_bytes)
            self.serial_connection.flush()
    
    def _parse_status_response(self, response: str) -> Dict[str, Any]:
        """Parse status response from ESP32S3 device"""
        status = {}
        for line in response.split('\n'):
            line = line.strip()
            if ':' in line and '- ' in line:
                # Handle lines like "   - Recording: NO"
                key, value = line.split(':', 1)
                key = key.replace('-', '').strip().replace(' ', '_').lower()
                value = value.strip()
                
                # Convert common values
                if value.lower() in ['yes', 'true']:
                    value = True
                elif value.lower() in ['no', 'false']:
                    value = False
                elif value.replace(' KB', '').replace(' MB', '').isdigit():
                    if 'KB' in value or 'MB' in value:
                        # Keep as string for display
                        pass
                    else:
                        value = int(value)
                elif value.isdigit():
                    value = int(value)
                
                status[key] = value
        
        return status
    
    async def _read_response(self, timeout: float = 1.0) -> Optional[bytes]:
        """Read response from OMI device"""
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        
        start_time = time.time()
        response = bytearray()
        
        while time.time() - start_time < timeout:
            if self.serial_connection.in_waiting > 0:
                data = self.serial_connection.read(self.serial_connection.in_waiting)
                response.extend(data)
                
                # Check for complete response (newline terminated)
                if b'\n' in response:
                    return bytes(response)
            
            await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
        
        return bytes(response) if response else None
    
    async def stream_audio(self) -> AsyncGenerator[AudioChunk, None]:
        """Stream audio data from OMI device"""
        if not self.serial_connection or not self.serial_connection.is_open:
            raise RuntimeError("OMI device not connected")
        
        self.is_streaming = True
        logger.info("Starting audio stream from OMI DevKit 2")
        
        # Start audio streaming
        self._send_command("START_AUDIO")
        
        try:
            while self.is_streaming:
                # Read audio data
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    self.audio_buffer.extend(data)
                    
                    # Process complete audio chunks
                    while len(self.audio_buffer) >= self.chunk_size:
                        chunk_data = bytes(self.audio_buffer[:self.chunk_size])
                        self.audio_buffer = self.audio_buffer[self.chunk_size:]
                        
                        # Create audio chunk
                        audio_chunk = AudioChunk(
                            data=chunk_data,
                            timestamp=time.time(),
                            sample_rate=self.sample_rate,
                            channels=self.channels
                        )
                        
                        yield audio_chunk
                
                await asyncio.sleep(0.01)  # Small delay
                
        except Exception as e:
            logger.error(f"Audio streaming error: {e}")
        finally:
            self.is_streaming = False
            self._send_command("STOP_AUDIO")
    
    def stop_streaming(self):
        """Stop audio streaming"""
        self.is_streaming = False
        if self.serial_connection and self.serial_connection.is_open:
            self._send_command("STOP_AUDIO")
    
    def is_device_connected(self) -> bool:
        """Check if ESP32S3 device is connected"""
        return (self.serial_connection is not None and 
                self.serial_connection.is_open and 
                self.is_connected)
    
    async def get_device_status(self) -> Dict[str, Any]:
        """Get device status"""
        if not self.is_device_connected():
            return {"error": "Device not connected"}
        
        async with self._io_lock:
            self._send_command("S")
            response = await self._read_response(timeout=3.0)
        
        if response:
            response_str = response.decode('utf-8', errors='ignore').strip()
            return self._parse_status_response(response_str)
        
        return {"error": "No response from device"}
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        if not self.is_device_connected():
            return {"error": "Device not connected"}
        
        async with self._io_lock:
            self._send_command("I")
            response = await self._read_response(timeout=3.0)
        
        if response:
            info_str = response.decode('utf-8', errors='ignore').strip()
            return {"device_info": info_str, "port": self.device_port}
        
        return {"error": "No response from device"}
    
    async def get_recordings(self) -> List[RecordingInfo]:
        """Get list of recordings from SD card"""
        if not self.is_device_connected():
            return []
        
        async with self._io_lock:
            # Clear any stale data before issuing list command
            try:
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()
            except Exception:
                pass
            self._send_command("L")
            # Small delay to allow firmware to start printing
            await asyncio.sleep(0.15)
            # Listing typically returns multiple lines; read until idle or timeout
            response = await self._read_multiline_text(timeout=5.0, idle_gap=0.3)
        
        recordings = []
        if response:
            response_str = response.decode('utf-8', errors='ignore')
            recordings = self._parse_recordings_response(response_str)
        
        return recordings

    async def _read_multiline_text(self, timeout: float = 2.0, idle_gap: float = 0.2) -> Optional[bytes]:
        """Read text data across multiple lines until idle gap or timeout."""
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        import time as _time
        start = _time.time()
        last_data_time = start
        buf = bytearray()
        while _time.time() - start < timeout:
            if self.serial_connection.in_waiting > 0:
                data = self.serial_connection.read(self.serial_connection.in_waiting)
                if data:
                    buf.extend(data)
                    last_data_time = _time.time()
            else:
                # Break if we've been idle for idle_gap seconds and have some data
                if len(buf) > 0 and _time.time() - last_data_time >= idle_gap:
                    break
                await asyncio.sleep(0.05)
        return bytes(buf) if buf else None
    
    def _parse_recordings_response(self, response: str) -> List[RecordingInfo]:
        """Parse recordings list response"""
        recordings = []
        for line in response.split('\n'):
            line = line.strip()
            if '.wav' in line and 'bytes' in line:
                try:
                    # Parse: "   📄 rec_20240115_121102.wav (171564 bytes)"
                    parts = line.split('(')
                    if len(parts) >= 2:
                        filename = parts[0].replace('📄', '').strip()
                        size_str = parts[1].replace('bytes)', '').strip()
                        size = int(size_str)
                        # Try to derive a date from filename patterns like rec_YYYYMMDD_HHMMSS.wav
                        date_str: Optional[str] = None
                        try:
                            import re
                            m = re.search(r'(\d{8})_(\d{6})', filename)
                            if m:
                                ymd, hms = m.groups()
                                from datetime import datetime
                                dt = datetime.strptime(ymd + hms, '%Y%m%d%H%M%S')
                                date_str = dt.isoformat()
                        except Exception:
                            date_str = None
                        
                        recordings.append(RecordingInfo(
                            name=filename,
                            size=size,
                            date=date_str
                        ))
                except Exception as e:
                    logger.warning(f"Could not parse recording line: {line} ({e})")
        
        return recordings
    
    async def download_file(self, filename: str) -> bytes:
        """Download a file from the ESP32S3 device"""
        if not self.is_device_connected():
            logger.error("Cannot download file - device not connected")
            return None
        
        try:
            logger.info(f"📥 Downloading file: {filename}")
            async with self._io_lock:
                # Clear any stale buffered bytes
                try:
                    self.serial_connection.reset_input_buffer()
                    self.serial_connection.reset_output_buffer()
                except Exception:
                    pass

                # Send download command
                self._send_command(f"D:{filename}")

                # Wait for DOWNLOAD_START and DOWNLOAD_SIZE
                start_seen = False
                file_size: Optional[int] = None
                text_buf = ""
                deadline = time.time() + 6.0
                while time.time() < deadline and (not start_seen or file_size is None):
                    resp = await self._read_response(timeout=0.8)
                    if resp:
                        text_buf += resp.decode('utf-8', errors='ignore')
                        if not start_seen and f"DOWNLOAD_START:{filename}" in text_buf:
                            start_seen = True
                        if file_size is None:
                            import re as _re
                            m = _re.search(r"DOWNLOAD_SIZE:(\d+)", text_buf)
                            if m:
                                try:
                                    file_size = int(m.group(1))
                                except Exception:
                                    file_size = None
                    else:
                        await asyncio.sleep(0.02)

                if not start_seen or file_size is None:
                    logger.error(f"Download handshake failed: start={start_seen}, size={file_size}; buf={text_buf.strip()[:200]}")
                    return None
                logger.info(f"📊 Expected file size: {file_size} bytes")

                # Consume any immediate text after size and align to RIFF
                pre_raw = bytearray()
                pre_deadline = time.time() + 0.5
                while time.time() < pre_deadline:
                    if self.serial_connection.in_waiting > 0:
                        pre_raw.extend(self.serial_connection.read(self.serial_connection.in_waiting))
                    else:
                        await asyncio.sleep(0.01)
                idx = pre_raw.find(b'RIFF')
                pending = bytes(pre_raw[idx:]) if idx >= 0 else b""

                # Read exactly file_size bytes as binary
                file_data = bytearray()
                # If pending already aligned to RIFF, start with it
                if pending:
                    file_data.extend(pending)

                while len(file_data) < file_size:
                    chunk = await self._read_binary_data(timeout=0.6)
                    if not chunk:
                        await asyncio.sleep(0.02)
                        continue
                    # If at start and didn't yet catch RIFF, try to align
                    if len(file_data) == 0:
                        idx = chunk.find(b'RIFF')
                        if idx >= 0:
                            chunk = chunk[idx:]
                    file_data.extend(chunk)
                    if len(file_data) % 4096 == 0:
                        logger.info(f"📥 {len(file_data)}/{file_size} bytes")

                # Optionally read trailing text (DOWNLOAD_END), but don't block download result on it
                tail = await self._read_response(timeout=0.8)
                if tail:
                    tail_s = tail.decode('utf-8', errors='ignore')
                    if f"DOWNLOAD_END:{filename}" in tail_s:
                        logger.info("✅ DOWNLOAD_END received")

                logger.info(f"✅ File downloaded successfully: {len(file_data)} bytes")
                logger.info(f"📈 Download efficiency: {len(file_data)/file_size*100:.1f}% of expected size")
                return bytes(file_data)

        except Exception as e:
            logger.error(f"Failed to download file {filename}: {e}")
            return None

    async def _read_binary_data(self, timeout: float = 1.0) -> Optional[bytes]:
        """Read arbitrary binary data available on the serial buffer within a timeout window."""
        if not self.serial_connection or not self.serial_connection.is_open:
            return None
        start_time = time.time()
        buffer = bytearray()
        # Keep reading what's available for the duration of the timeout window
        while time.time() - start_time < timeout:
            try:
                if self.serial_connection.in_waiting > 0:
                    data = self.serial_connection.read(self.serial_connection.in_waiting)
                    if data:
                        buffer.extend(data)
                        # If we received a good chunk, allow a brief moment for the next burst
                        await asyncio.sleep(0.005)
                        # Return immediately if we already have some bytes; caller loops until size
                        if len(buffer) > 0:
                            return bytes(buffer)
                else:
                    await asyncio.sleep(0.01)
            except Exception as e:
                logger.error(f"Binary read error: {e}")
                break
        return bytes(buffer) if buffer else None
    
    def _create_dummy_wav_data(self, filename: str) -> bytes:
        """Create dummy WAV file data for testing"""
        # Proper WAV header for 16kHz, 16-bit, mono
        sample_rate = 16000
        channels = 1
        bits_per_sample = 16
        duration_seconds = 2
        
        # Calculate sizes
        num_samples = sample_rate * duration_seconds * channels
        data_size = num_samples * (bits_per_sample // 8)
        file_size = 36 + data_size
        
        # WAV header
        wav_header = bytearray()
        wav_header.extend(b'RIFF')                          # ChunkID
        wav_header.extend(file_size.to_bytes(4, 'little')) # ChunkSize
        wav_header.extend(b'WAVE')                          # Format
        wav_header.extend(b'fmt ')                          # Subchunk1ID
        wav_header.extend((16).to_bytes(4, 'little'))       # Subchunk1Size
        wav_header.extend((1).to_bytes(2, 'little'))        # AudioFormat (PCM)
        wav_header.extend(channels.to_bytes(2, 'little'))   # NumChannels
        wav_header.extend(sample_rate.to_bytes(4, 'little')) # SampleRate
        wav_header.extend((sample_rate * channels * bits_per_sample // 8).to_bytes(4, 'little')) # ByteRate
        wav_header.extend((channels * bits_per_sample // 8).to_bytes(2, 'little')) # BlockAlign
        wav_header.extend(bits_per_sample.to_bytes(2, 'little')) # BitsPerSample
        wav_header.extend(b'data')                          # Subchunk2ID
        wav_header.extend(data_size.to_bytes(4, 'little'))  # Subchunk2Size
        
        # Generate some dummy audio data (sine wave for testing)
        import math
        frequency = 440  # A4 note
        dummy_audio = bytearray()
        for i in range(num_samples):
            # Generate sine wave
            sample = int(16000 * math.sin(2 * math.pi * frequency * i / sample_rate))
            dummy_audio.extend(sample.to_bytes(2, 'little', signed=True))
        
        return bytes(wav_header + dummy_audio)
    
    async def delete_file(self, filename: str) -> bool:
        """Delete a file from the ESP32S3 device"""
        if not self.is_device_connected():
            logger.error("Cannot delete file - device not connected")
            return False
        
        try:
            logger.info(f"🗑️ Deleting file: {filename}")
            
            async with self._io_lock:
                # Send delete command (this would need to be implemented in firmware)
                self._send_command(f"DELETE:{filename}")
                response = await self._read_response(timeout=5.0)
            
            if response:
                response_str = response.decode('utf-8', errors='ignore')
                if "deleted" in response_str.lower() or "success" in response_str.lower():
                    logger.info(f"✅ File {filename} deleted successfully")
                    return True
            
            logger.warning(f"❌ Delete failed for {filename}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {e}")
            return False
    
    async def upload_file(self, filename: str, file_data: bytes) -> bool:
        """Upload a file to the ESP32S3 device"""
        if not self.is_device_connected():
            logger.error("Cannot upload file - device not connected")
            return False
        
        try:
            logger.info(f"📤 Uploading file: {filename} ({len(file_data)} bytes)")
            
            async with self._io_lock:
                # Send upload command (this would need to be implemented in firmware)
                self._send_command(f"UPLOAD:{filename}:{len(file_data)}")
                
                # Send file data in chunks
                chunk_size = 1024
                for i in range(0, len(file_data), chunk_size):
                    chunk = file_data[i:i + chunk_size]
                    self.serial_connection.write(chunk)
                    await asyncio.sleep(0.01)  # Small delay between chunks
                
                # Wait for confirmation
                response = await self._read_response(timeout=10.0)
            
            if response:
                response_str = response.decode('utf-8', errors='ignore')
                if "uploaded" in response_str.lower() or "success" in response_str.lower():
                    logger.info(f"✅ File {filename} uploaded successfully")
                    return True
            
            logger.warning(f"❌ Upload failed for {filename}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up OMI connector...")
        
        self.stop_streaming()
        
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
            except Exception as e:
                logger.error(f"Error closing serial connection: {e}")
        
        self.serial_connection = None
