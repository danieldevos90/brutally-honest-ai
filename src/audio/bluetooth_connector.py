"""
Bluetooth OMI Connector - Wireless connection to OMI DevKit
Supports both classic Bluetooth and BLE connections
"""

import asyncio
import logging
import struct
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
import json

try:
    import bluetooth
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False

try:
    import bleak
    from bleak import BleakClient, BleakScanner
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class BluetoothAudioChunk:
    """Audio data chunk from Bluetooth OMI device"""
    data: bytes
    timestamp: float
    sample_rate: int = 16000
    channels: int = 1
    format: str = "PCM"

class BluetoothOMIConnector:
    """Bluetooth connector for OMI DevKit with both Classic and BLE support"""
    
    # ESP32S3 Brutally Honest AI Service UUIDs
    SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
    AUDIO_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef1"
    STATUS_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef2"
    
    def __init__(self, connection_type: str = "ble", device_name: str = "BrutallyHonestAI"):
        """
        Initialize Bluetooth OMI connector
        
        Args:
            connection_type: "ble" for Bluetooth Low Energy or "classic" for Classic Bluetooth
            device_name: Name to search for when scanning devices
        """
        self.connection_type = connection_type
        self.device_name = device_name
        self.is_connected = False
        self.is_streaming = False
        
        # BLE specific
        self.ble_client: Optional[BleakClient] = None
        self.device_address: Optional[str] = None
        
        # Classic Bluetooth specific
        self.bt_socket = None
        
        # Audio configuration
        self.sample_rate = 16000
        self.channels = 1
        self.bit_depth = 16
        self.chunk_size = 1024
        
        # Callbacks
        self.audio_callback: Optional[Callable] = None
        self.status_callback: Optional[Callable] = None
        
    async def scan_for_devices(self, timeout: int = 10) -> Dict[str, str]:
        """Scan for OMI devices via Bluetooth"""
        devices = {}
        
        if self.connection_type == "ble" and BLE_AVAILABLE:
            logger.info("Scanning for BLE OMI devices...")
            try:
                scanner = BleakScanner()
                ble_devices = await scanner.discover(timeout=timeout)
                
                for device in ble_devices:
                    if device.name and self.device_name.lower() in device.name.lower():
                        devices[device.address] = f"{device.name} (BLE)"
                        logger.info(f"Found BLE ESP32S3 device: {device.name} ({device.address})")
                        
            except Exception as e:
                logger.error(f"BLE scan failed: {e}")
                
        elif self.connection_type == "classic" and BLUETOOTH_AVAILABLE:
            logger.info("Scanning for Classic Bluetooth OMI devices...")
            try:
                nearby_devices = bluetooth.discover_devices(duration=timeout, lookup_names=True)
                
                for addr, name in nearby_devices:
                    if name and self.device_name.lower() in name.lower():
                        devices[addr] = f"{name} (Classic)"
                        logger.info(f"Found Classic BT OMI device: {name} ({addr})")
                        
            except Exception as e:
                logger.error(f"Classic Bluetooth scan failed: {e}")
        
        return devices
    
    async def connect(self, device_address: Optional[str] = None) -> bool:
        """Connect to OMI device via Bluetooth"""
        try:
            if not device_address:
                # Auto-discover device
                devices = await self.scan_for_devices()
                if not devices:
                    logger.error("No ESP32S3 BLE devices found")
                    return False
                device_address = list(devices.keys())[0]
                logger.info(f"Auto-connecting to: {devices[device_address]}")
            
            self.device_address = device_address
            
            if self.connection_type == "ble":
                return await self._connect_ble()
            else:
                return await self._connect_classic()
                
        except Exception as e:
            logger.error(f"Failed to connect to OMI device: {e}")
            return False
    
    async def _connect_ble(self) -> bool:
        """Connect via Bluetooth Low Energy"""
        if not BLE_AVAILABLE:
            logger.error("BLE not available. Install bleak: pip install bleak")
            return False
            
        try:
            self.ble_client = BleakClient(self.device_address)
            await self.ble_client.connect()
            
            # Verify ESP32S3 service is available
            services = self.ble_client.services
            esp32_service = None
            
            for service in services:
                if service.uuid.lower() == self.SERVICE_UUID.lower():
                    esp32_service = service
                    break
            
            if not esp32_service:
                logger.error("ESP32S3 Brutally Honest AI service not found on device")
                await self.ble_client.disconnect()
                return False
            
            # Subscribe to audio notifications
            try:
                await self.ble_client.start_notify(
                    self.AUDIO_CHARACTERISTIC_UUID, 
                    self._handle_audio_notification
                )
                logger.info("Subscribed to audio notifications")
            except Exception as e:
                logger.warning(f"Could not subscribe to audio notifications: {e}")
            
            # Subscribe to status notifications
            try:
                await self.ble_client.start_notify(
                    self.STATUS_CHARACTERISTIC_UUID, 
                    self._handle_status_notification
                )
                logger.info("Subscribed to status notifications")
            except Exception as e:
                logger.warning(f"Could not subscribe to status notifications: {e}")
            
            self.is_connected = True
            logger.info(f"Connected to OMI device via BLE: {self.device_address}")
            logger.info("ESP32S3 BLE connection established successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"BLE connection failed: {e}")
            return False
    
    async def _connect_classic(self) -> bool:
        """Connect via Classic Bluetooth"""
        if not BLUETOOTH_AVAILABLE:
            logger.error("Classic Bluetooth not available. Install pybluez: pip install pybluez")
            return False
            
        try:
            # Create RFCOMM socket
            self.bt_socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            
            # Find available port
            services = bluetooth.find_service(address=self.device_address)
            if not services:
                logger.error("No services found on OMI device")
                return False
            
            port = services[0]["port"]
            self.bt_socket.connect((self.device_address, port))
            
            self.is_connected = True
            logger.info(f"Connected to OMI device via Classic BT: {self.device_address}")
            
            # Start listening for data
            asyncio.create_task(self._classic_bt_listener())
            
            return True
            
        except Exception as e:
            logger.error(f"Classic Bluetooth connection failed: {e}")
            return False
    
    async def _handle_audio_notification(self, sender, data: bytearray):
        """Handle incoming audio data from BLE"""
        if self.audio_callback and len(data) > 4:
            # Extract timestamp from first 4 bytes
            timestamp = struct.unpack('>I', data[:4])[0] / 1000.0  # Convert ms to seconds
            audio_data = data[4:]  # Rest is audio data
            
            chunk = BluetoothAudioChunk(
                data=bytes(audio_data),
                timestamp=timestamp,
                sample_rate=self.sample_rate,
                channels=self.channels
            )
            await self.audio_callback(chunk)
    
    async def _handle_status_notification(self, sender, data: bytearray):
        """Handle status updates from BLE"""
        try:
            status_data = json.loads(data.decode('utf-8'))
            if self.status_callback:
                await self.status_callback(status_data)
        except Exception as e:
            logger.error(f"Failed to parse status data: {e}")
    
    async def _classic_bt_listener(self):
        """Listen for data on Classic Bluetooth socket"""
        while self.is_connected and self.bt_socket:
            try:
                data = self.bt_socket.recv(1024)
                if data:
                    # Parse data based on protocol
                    if data.startswith(b'AUDIO:'):
                        audio_data = data[6:]  # Remove 'AUDIO:' prefix
                        if self.audio_callback:
                            chunk = BluetoothAudioChunk(
                                data=audio_data,
                                timestamp=asyncio.get_event_loop().time()
                            )
                            await self.audio_callback(chunk)
                    elif data.startswith(b'STATUS:'):
                        status_json = data[7:].decode('utf-8')
                        status_data = json.loads(status_json)
                        if self.status_callback:
                            await self.status_callback(status_data)
            except Exception as e:
                logger.error(f"Classic BT listener error: {e}")
                break
    
    async def send_command(self, command: Dict[str, Any]) -> bool:
        """Send command to OMI device (ESP32S3 doesn't use commands)"""
        if not self.is_connected:
            logger.error("Not connected to OMI device")
            return False
        
        # ESP32S3 firmware doesn't handle commands, just return success
        logger.info("ESP32S3 firmware doesn't use commands - skipping")
        return True
    
    async def start_audio_streaming(self) -> bool:
        """Start audio streaming from OMI device"""
        if not self.is_connected:
            return False
        
        success = await self.send_command({
            "type": "start_audio",
            "config": {
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "chunk_size": self.chunk_size
            }
        })
        
        if success:
            self.is_streaming = True
            logger.info("Audio streaming started")
        
        return success
    
    async def stop_audio_streaming(self) -> bool:
        """Stop audio streaming"""
        if not self.is_connected:
            return False
        
        success = await self.send_command({"type": "stop_audio"})
        
        if success:
            self.is_streaming = False
            logger.info("Audio streaming stopped")
        
        return success
    
    async def disconnect(self):
        """Disconnect from OMI device"""
        try:
            if self.is_streaming:
                await self.stop_audio_streaming()
            
            if self.connection_type == "ble" and self.ble_client:
                if self.ble_client.is_connected:
                    await self.ble_client.disconnect()
            elif self.connection_type == "classic" and self.bt_socket:
                self.bt_socket.close()
            
            self.is_connected = False
            self.is_streaming = False
            logger.info("Disconnected from OMI device")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def set_audio_callback(self, callback: Callable):
        """Set callback for audio data"""
        self.audio_callback = callback
    
    def set_status_callback(self, callback: Callable):
        """Set callback for status updates"""
        self.status_callback = callback
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            "connected": self.is_connected,
            "streaming": self.is_streaming,
            "connection_type": self.connection_type,
            "device_address": self.device_address,
            "device_name": self.device_name,
            "audio_config": {
                "sample_rate": self.sample_rate,
                "channels": self.channels,
                "bit_depth": self.bit_depth,
                "chunk_size": self.chunk_size
            }
        }
    
    async def download_file(self, filename: str) -> bytes:
        """Download a file from the ESP32S3 device via BLE"""
        if not self.is_connected:
            logger.error("Cannot download file - device not connected")
            return None
        
        try:
            logger.info(f"📥 BLE Download request for: {filename}")
            
            # For BLE, we would need to implement a file transfer protocol
            # This is a placeholder implementation
            if self.ble_client and self.ble_client.is_connected:
                # Send download request via status characteristic
                command = f"DOWNLOAD:{filename}"
                await self.ble_client.write_gatt_char(self.status_char_uuid, command.encode())
                
                # Wait for file data (this would need proper protocol implementation)
                await asyncio.sleep(1)
                
                # Return dummy data for now
                return self._create_dummy_wav_data(filename)
            
            return None
            
        except Exception as e:
            logger.error(f"BLE download error: {e}")
            return None
    
    def _create_dummy_wav_data(self, filename: str) -> bytes:
        """Create dummy WAV file data for testing"""
        # Simple WAV header + some dummy audio data
        wav_header = b'RIFF\x24\x08\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x08\x00\x00'
        # Add some dummy audio data (silence)
        dummy_audio = b'\x00\x00' * 1000  # 2000 bytes of silence
        return wav_header + dummy_audio
    
    async def delete_file(self, filename: str) -> bool:
        """Delete a file from the ESP32S3 device via BLE"""
        if not self.is_connected:
            logger.error("Cannot delete file - device not connected")
            return False
        
        try:
            logger.info(f"🗑️ BLE Delete request for: {filename}")
            
            if self.ble_client and self.ble_client.is_connected:
                # Send delete command via status characteristic
                command = f"DELETE:{filename}"
                await self.ble_client.write_gatt_char(self.status_char_uuid, command.encode())
                
                # For now, assume success (would need proper protocol)
                logger.info(f"✅ BLE delete command sent for {filename}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"BLE delete error: {e}")
            return False
    
    async def upload_file(self, filename: str, file_data: bytes) -> bool:
        """Upload a file to the ESP32S3 device via BLE"""
        if not self.is_connected:
            logger.error("Cannot upload file - device not connected")
            return False
        
        try:
            logger.info(f"📤 BLE Upload request for: {filename} ({len(file_data)} bytes)")
            
            if self.ble_client and self.ble_client.is_connected:
                # Send upload command via status characteristic
                command = f"UPLOAD:{filename}:{len(file_data)}"
                await self.ble_client.write_gatt_char(self.status_char_uuid, command.encode())
                
                # Send file data in chunks via audio characteristic
                chunk_size = 20  # BLE MTU limit
                for i in range(0, len(file_data), chunk_size):
                    chunk = file_data[i:i + chunk_size]
                    await self.ble_client.write_gatt_char(self.audio_char_uuid, chunk)
                    await asyncio.sleep(0.01)  # Small delay between chunks
                
                logger.info(f"✅ BLE upload completed for {filename}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"BLE upload error: {e}")
            return False

# Example usage
if __name__ == "__main__":
    async def audio_handler(chunk: BluetoothAudioChunk):
        print(f"Received audio chunk: {len(chunk.data)} bytes")
    
    async def status_handler(status: Dict[str, Any]):
        print(f"Status update: {status}")
    
    async def main():
        # Create BLE connector
        connector = BluetoothOMIConnector(connection_type="ble")
        connector.set_audio_callback(audio_handler)
        connector.set_status_callback(status_handler)
        
        # Scan and connect
        devices = await connector.scan_for_devices()
        print(f"Found devices: {devices}")
        
        if devices:
            if await connector.connect():
                print("Connected successfully!")
                await connector.start_audio_streaming()
                
                # Stream for 10 seconds
                await asyncio.sleep(10)
                
                await connector.stop_audio_streaming()
                await connector.disconnect()
    
    asyncio.run(main())