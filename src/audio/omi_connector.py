"""
OMI DevKit 2 USB-C Connector
Handles direct communication with OMI hardware via USB-C
"""

import asyncio
import logging
import serial
import serial.tools.list_ports
import struct
import time
from typing import AsyncGenerator, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class AudioChunk:
    """Audio data chunk from OMI device"""
    data: bytes
    timestamp: float
    sample_rate: int = 16000
    channels: int = 1
    format: str = "PCM"

class OMIDevKitConnector:
    """Connector for OMI DevKit 2 via USB-C"""
    
    def __init__(self, vendor_id: int = 0x2E8A, product_id: int = 0x0005):
        """
        Initialize OMI connector
        
        Args:
            vendor_id: USB vendor ID for OMI device (Raspberry Pi Pico default)
            product_id: USB product ID for OMI device
        """
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.serial_connection: Optional[serial.Serial] = None
        self.is_streaming = False
        self.audio_buffer = bytearray()
        
        # Audio configuration
        self.sample_rate = 16000  # 16kHz for Whisper
        self.channels = 1  # Mono
        self.bit_depth = 16  # 16-bit PCM
        self.chunk_size = 1024  # Bytes per chunk
        
    async def initialize(self) -> bool:
        """Initialize connection to OMI DevKit"""
        try:
            # Find OMI device
            device_port = self._find_omi_device()
            if not device_port:
                logger.error("OMI DevKit 2 not found. Please check USB-C connection.")
                return False
            
            # Establish serial connection
            self.serial_connection = serial.Serial(
                port=device_port,
                baudrate=115200,  # Standard baud rate for OMI
                timeout=1.0,
                write_timeout=1.0
            )
            
            # Wait for device to be ready
            await asyncio.sleep(2)
            
            # Send initialization command
            if await self._initialize_device():
                logger.info(f"OMI DevKit 2 connected successfully on {device_port}")
                return True
            else:
                logger.error("Failed to initialize OMI device")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize OMI connector: {e}")
            return False
    
    def _find_omi_device(self) -> Optional[str]:
        """Find OMI device in connected USB devices"""
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # Check for OMI device by vendor/product ID
            if (hasattr(port, 'vid') and hasattr(port, 'pid') and
                port.vid == self.vendor_id and port.pid == self.product_id):
                return port.device
            
            # Fallback: check device description
            if port.description and 'omi' in port.description.lower():
                return port.device
                
            # Check for Raspberry Pi Pico (OMI DevKit 2 base)
            if port.description and 'pico' in port.description.lower():
                return port.device
        
        # List all available ports for debugging
        logger.info("Available serial ports:")
        for port in ports:
            logger.info(f"  {port.device}: {port.description} (VID: {getattr(port, 'vid', 'N/A')}, PID: {getattr(port, 'pid', 'N/A')})")
        
        return None
    
    async def _initialize_device(self) -> bool:
        """Send initialization commands to OMI device"""
        try:
            # Send device info request
            self._send_command("INFO")
            response = await self._read_response(timeout=3.0)
            
            if response and b"OMI" in response:
                logger.info(f"OMI device info: {response.decode('utf-8', errors='ignore')}")
                
                # Configure audio settings
                audio_config = f"AUDIO_CONFIG:{self.sample_rate}:{self.channels}:{self.bit_depth}"
                self._send_command(audio_config)
                
                config_response = await self._read_response(timeout=2.0)
                if config_response and b"OK" in config_response:
                    logger.info("OMI audio configuration successful")
                    return True
                else:
                    logger.warning("OMI audio configuration may have failed")
                    return True  # Continue anyway
            
            return False
            
        except Exception as e:
            logger.error(f"Device initialization error: {e}")
            return False
    
    def _send_command(self, command: str):
        """Send command to OMI device"""
        if self.serial_connection and self.serial_connection.is_open:
            cmd_bytes = f"{command}\n".encode('utf-8')
            self.serial_connection.write(cmd_bytes)
            self.serial_connection.flush()
    
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
    
    def is_connected(self) -> bool:
        """Check if OMI device is connected"""
        return (self.serial_connection is not None and 
                self.serial_connection.is_open)
    
    async def get_device_info(self) -> Dict[str, Any]:
        """Get device information"""
        if not self.is_connected():
            return {"error": "Device not connected"}
        
        self._send_command("INFO")
        response = await self._read_response(timeout=2.0)
        
        if response:
            info_str = response.decode('utf-8', errors='ignore').strip()
            return {"device_info": info_str}
        
        return {"error": "No response from device"}
    
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
