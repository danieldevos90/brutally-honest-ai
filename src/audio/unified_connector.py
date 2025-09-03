"""
Unified Connector for ESP32S3 Brutally Honest AI Device
Provides a single interface for both USB and BLE connections
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from enum import Enum

from .omi_connector import ESP32S3Connector, RecordingInfo
from .bluetooth_connector import BluetoothOMIConnector

logger = logging.getLogger(__name__)

class ConnectionType(Enum):
    USB = "usb"
    BLE = "ble"

@dataclass
class DeviceStatus:
    """Unified device status"""
    connected: bool
    recording: bool
    files: int
    sd_card_present: bool
    ble_connected: bool
    free_ram: int
    connection_type: ConnectionType
    battery_voltage: float = 0.0
    battery_percentage: int = 0
    battery_status: str = "Unknown"
    device_info: Dict[str, Any] = None

class UnifiedESP32S3Connector:
    """Unified connector for ESP32S3 Brutally Honest AI device"""
    
    def __init__(self, preferred_connection: ConnectionType = ConnectionType.USB):
        """
        Initialize unified connector
        
        Args:
            preferred_connection: Preferred connection type (USB or BLE)
        """
        self.preferred_connection = preferred_connection
        self.current_connection: Optional[ConnectionType] = None
        
        # Connection instances
        self.usb_connector: Optional[ESP32S3Connector] = None
        self.ble_connector: Optional[BluetoothOMIConnector] = None
        
        # Status
        self.is_connected = False
        self.device_status: Optional[DeviceStatus] = None
        
    async def initialize(self) -> bool:
        """Initialize connection using preferred method with fallback"""
        logger.info(f"Initializing ESP32S3 connection (preferred: {self.preferred_connection.value})")
        # If already connected, don't re-initialize
        if self.is_connected and self.current_connection is not None:
            logger.info("Already connected; skipping re-initialization")
            return True
        
        # Try preferred connection first
        if self.preferred_connection == ConnectionType.USB:
            if await self._try_usb_connection():
                return True
            logger.info("USB connection failed, trying BLE...")
            return await self._try_ble_connection()
        else:
            if await self._try_ble_connection():
                return True
            logger.info("BLE connection failed, trying USB...")
            return await self._try_usb_connection()
    
    async def _try_usb_connection(self) -> bool:
        """Try to establish USB connection"""
        try:
            self.usb_connector = ESP32S3Connector()
            if await self.usb_connector.initialize():
                self.current_connection = ConnectionType.USB
                self.is_connected = True
                logger.info("✅ USB connection established")
                return True
        except Exception as e:
            logger.error(f"USB connection failed: {e}")
        
        return False
    
    async def _try_ble_connection(self) -> bool:
        """Try to establish BLE connection"""
        try:
            self.ble_connector = BluetoothOMIConnector(connection_type="ble")
            if await self.ble_connector.connect():
                self.current_connection = ConnectionType.BLE
                self.is_connected = True
                logger.info("✅ BLE connection established")
                return True
        except Exception as e:
            logger.error(f"BLE connection failed: {e}")
        
        return False
    
    async def get_device_status(self) -> Optional[DeviceStatus]:
        """Get unified device status"""
        if not self.is_connected:
            return None
        
        try:
            if self.current_connection == ConnectionType.USB and self.usb_connector:
                # Check if USB connector is still connected
                if not self.usb_connector.is_device_connected():
                    self.is_connected = False
                    return None
                
                try:
                    status_data = await self.usb_connector.get_device_status()
                    device_info = await self.usb_connector.get_device_info()
                except Exception as e:
                    # Attempt a one-time automatic reconnect on I/O failures
                    logger.error(f"USB status failed; attempting reconnect: {e}")
                    try:
                        await self.usb_connector.cleanup()
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)
                    if await self.usb_connector.initialize():
                        try:
                            status_data = await self.usb_connector.get_device_status()
                            device_info = await self.usb_connector.get_device_info()
                        except Exception as e2:
                            logger.error(f"USB status failed after reconnect: {e2}")
                            self.is_connected = False
                            return None
                    else:
                        logger.error("USB re-initialization failed during status fetch")
                        self.is_connected = False
                        return None
                
                # Parse battery information from status_data
                battery_info = status_data.get('battery', '')
                battery_voltage = 0.0
                battery_percentage = 0
                battery_status = "Unknown"
                
                if isinstance(battery_info, str) and 'V' in battery_info:
                    # Parse format like "3.85V (75% - GOOD)"
                    try:
                        parts = battery_info.split('V')
                        if len(parts) > 0:
                            battery_voltage = float(parts[0])
                        if '(' in battery_info and '%' in battery_info:
                            pct_part = battery_info.split('(')[1].split('%')[0]
                            battery_percentage = int(pct_part)
                        if '-' in battery_info and ')' in battery_info:
                            status_part = battery_info.split('-')[1].split(')')[0].strip()
                            battery_status = status_part
                    except (ValueError, IndexError):
                        pass
                
                self.device_status = DeviceStatus(
                    connected=True,
                    recording=status_data.get('recording', False),
                    files=status_data.get('files', 0),
                    sd_card_present=status_data.get('sd_card', 'Present') == 'Present',
                    ble_connected=status_data.get('ble_connected', False),
                    free_ram=status_data.get('free_ram', 0),
                    connection_type=ConnectionType.USB,
                    battery_voltage=battery_voltage,
                    battery_percentage=battery_percentage,
                    battery_status=battery_status,
                    device_info=device_info
                )
                
            elif self.current_connection == ConnectionType.BLE and self.ble_connector:
                # BLE status would come from notifications
                # For now, return basic status
                self.device_status = DeviceStatus(
                    connected=True,
                    recording=False,  # Would be updated via BLE notifications
                    files=2,  # Would be updated via BLE notifications
                    sd_card_present=True,
                    ble_connected=True,
                    free_ram=0,
                    connection_type=ConnectionType.BLE,
                    battery_voltage=3.7,  # Default BLE values
                    battery_percentage=75,
                    battery_status="GOOD",
                    device_info={"connection": "BLE", "device": "BrutallyHonestAI"}
                )
            
            return self.device_status
            
        except Exception as e:
            logger.error(f"Failed to get device status: {e}")
            return None
    
    async def get_recordings(self) -> List[RecordingInfo]:
        """Get list of recordings"""
        if not self.is_connected:
            return []
        
        try:
            if self.current_connection == ConnectionType.USB and self.usb_connector:
                # Check if USB connector is still connected
                if not self.usb_connector.is_device_connected():
                    self.is_connected = False
                    return []
                
                try:
                    return await self.usb_connector.get_recordings()
                except Exception as e:
                    # Attempt a one-time automatic reconnect on I/O failures
                    logger.error(f"USB recordings fetch failed; attempting reconnect: {e}")
                    try:
                        await self.usb_connector.cleanup()
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)
                    if await self.usb_connector.initialize():
                        try:
                            return await self.usb_connector.get_recordings()
                        except Exception as e2:
                            logger.error(f"USB recordings fetch failed after reconnect: {e2}")
                            self.is_connected = False
                            return []
                    else:
                        logger.error("USB re-initialization failed during recordings fetch")
                        self.is_connected = False
                        return []
            elif self.current_connection == ConnectionType.BLE and self.ble_connector:
                # BLE recordings would need to be implemented
                # For now, return simulated data based on known recordings
                return [
                    RecordingInfo(name="rec_20240115_121102.wav", size=171564),
                    RecordingInfo(name="rec_20240115_121536.wav", size=239660)
                ]
            
        except Exception as e:
            logger.error(f"Failed to get recordings: {e}")
        
        return []
    
    async def send_command(self, command: str) -> Optional[str]:
        """Send command to device"""
        if not self.is_connected:
            return None
        
        try:
            if self.current_connection == ConnectionType.USB and self.usb_connector:
                # Check if USB connector is still connected
                if not self.usb_connector.is_device_connected():
                    self.is_connected = False
                    return None
                
                try:
                    self.usb_connector._send_command(command)
                    response = await self.usb_connector._read_response(timeout=3.0)
                    if response:
                        return response.decode('utf-8', errors='ignore')
                except Exception as e:
                    logger.error(f"USB command failed; attempting reconnect: {e}")
                    try:
                        await self.usb_connector.cleanup()
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)
                    if await self.usb_connector.initialize():
                        try:
                            self.usb_connector._send_command(command)
                            response = await self.usb_connector._read_response(timeout=3.0)
                            if response:
                                return response.decode('utf-8', errors='ignore')
                        except Exception as e2:
                            logger.error(f"USB command failed after reconnect: {e2}")
                            self.is_connected = False
                            return None
                    else:
                        logger.error("USB re-initialization failed during command send")
                        self.is_connected = False
                        return None
            elif self.current_connection == ConnectionType.BLE and self.ble_connector:
                # BLE commands would need to be implemented
                logger.info(f"BLE command not implemented: {command}")
                return "BLE command not supported"
            
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
        
        return None
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            "connected": self.is_connected,
            "connection_type": self.current_connection.value if self.current_connection else None,
            "preferred_connection": self.preferred_connection.value,
            "usb_available": self.usb_connector is not None,
            "ble_available": self.ble_connector is not None,
            "device_status": self.device_status.__dict__ if self.device_status else None
        }
    
    async def disconnect(self):
        """Disconnect from device"""
        try:
            if self.usb_connector:
                await self.usb_connector.cleanup()
            if self.ble_connector:
                await self.ble_connector.disconnect()
            
            self.is_connected = False
            self.current_connection = None
            self.device_status = None
            logger.info("Disconnected from ESP32S3 device")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def download_file(self, filename: str) -> bytes:
        """Download a file from the ESP32S3 device"""
        if not self.is_connected:
            logger.error("Cannot download file - device not connected")
            return None
        
        try:
            if self.current_connection == ConnectionType.USB and self.usb_connector:
                try:
                    return await self.usb_connector.download_file(filename)
                except Exception as e:
                    logger.error(f"USB download failed; attempting reconnect: {e}")
                    try:
                        await self.usb_connector.cleanup()
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)
                    if await self.usb_connector.initialize():
                        try:
                            return await self.usb_connector.download_file(filename)
                        except Exception as e2:
                            logger.error(f"USB download failed after reconnect: {e2}")
                            self.is_connected = False
                            return None
                    else:
                        logger.error("USB re-initialization failed during download")
                        self.is_connected = False
                        return None
            elif self.current_connection == ConnectionType.BLE and self.ble_connector:
                return await self.ble_connector.download_file(filename)
            else:
                logger.error("No active connection for file download")
                return None
                
        except Exception as e:
            logger.error(f"Failed to download file {filename}: {e}")
            return None
    
    async def delete_file(self, filename: str) -> bool:
        """Delete a file from the ESP32S3 device"""
        if not self.is_connected:
            logger.error("Cannot delete file - device not connected")
            return False
        
        try:
            if self.current_connection == ConnectionType.USB and self.usb_connector:
                try:
                    return await self.usb_connector.delete_file(filename)
                except Exception as e:
                    logger.error(f"USB delete failed; attempting reconnect: {e}")
                    try:
                        await self.usb_connector.cleanup()
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)
                    if await self.usb_connector.initialize():
                        try:
                            return await self.usb_connector.delete_file(filename)
                        except Exception as e2:
                            logger.error(f"USB delete failed after reconnect: {e2}")
                            self.is_connected = False
                            return False
                    else:
                        logger.error("USB re-initialization failed during delete")
                        self.is_connected = False
                        return False
            elif self.current_connection == ConnectionType.BLE and self.ble_connector:
                return await self.ble_connector.delete_file(filename)
            else:
                logger.error("No active connection for file deletion")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file {filename}: {e}")
            return False
    
    async def upload_file(self, filename: str, file_data: bytes) -> bool:
        """Upload a file to the ESP32S3 device"""
        if not self.is_connected:
            logger.error("Cannot upload file - device not connected")
            return False
        
        try:
            if self.current_connection == ConnectionType.USB and self.usb_connector:
                try:
                    return await self.usb_connector.upload_file(filename, file_data)
                except Exception as e:
                    logger.error(f"USB upload failed; attempting reconnect: {e}")
                    try:
                        await self.usb_connector.cleanup()
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)
                    if await self.usb_connector.initialize():
                        try:
                            return await self.usb_connector.upload_file(filename, file_data)
                        except Exception as e2:
                            logger.error(f"USB upload failed after reconnect: {e2}")
                            self.is_connected = False
                            return False
                    else:
                        logger.error("USB re-initialization failed during upload")
                        self.is_connected = False
                        return False
            elif self.current_connection == ConnectionType.BLE and self.ble_connector:
                return await self.ble_connector.upload_file(filename, file_data)
            else:
                logger.error("No active connection for file upload")
                return False
                
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {e}")
            return False

# Example usage
async def main():
    """Example usage of unified connector"""
    connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
    
    try:
        if await connector.initialize():
            print("✅ Connected to ESP32S3 Brutally Honest AI device")
            
            # Get device status
            status = await connector.get_device_status()
            if status:
                print(f"📊 Device Status:")
                print(f"   Recording: {status.recording}")
                print(f"   Files: {status.files}")
                print(f"   Connection: {status.connection_type.value}")
                print(f"   RAM: {status.free_ram} KB")
            
            # Get recordings
            recordings = await connector.get_recordings()
            print(f"📁 Found {len(recordings)} recordings:")
            for rec in recordings:
                print(f"   - {rec.name} ({rec.size / 1024:.1f} KB)")
            
            # Get connection info
            info = connector.get_connection_info()
            print(f"🔗 Connection Info: {info}")
            
        else:
            print("❌ Failed to connect to ESP32S3 device")
    
    finally:
        await connector.disconnect()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
