"""
Device Service - Business logic for ESP32S3 device management
Separates device operations from HTTP route handlers
"""

import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DeviceStatus:
    """Device status data transfer object."""
    device_id: str
    connected: bool
    connection_type: str
    recording: bool
    files: int
    sd_card_present: bool
    ble_connected: bool
    free_ram: int
    battery_voltage: Optional[float] = None
    battery_percentage: Optional[int] = None
    battery_status: Optional[str] = None
    device_model: str = "ESP32S3"
    port: str = "N/A"


class DeviceService:
    """Service layer for device management operations."""
    
    def __init__(self, device_manager=None):
        self._device_manager = device_manager
        self._connector = None
    
    async def get_device_manager(self):
        """Get or initialize device manager."""
        if self._device_manager is None:
            from audio.multi_device_manager import get_device_manager
            self._device_manager = get_device_manager()
        return self._device_manager
    
    async def get_connector(self):
        """Get or initialize device connector."""
        if self._connector is None:
            from audio.unified_connector import UnifiedESP32S3Connector, ConnectionType
            
            manager = await self.get_device_manager()
            active_connector = manager.get_active_connector()
            if active_connector:
                self._connector = active_connector
            else:
                self._connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
                await self._connector.initialize()
        return self._connector
    
    async def scan_devices(self) -> List[Dict[str, Any]]:
        """Scan for available ESP32S3 devices."""
        try:
            manager = await self.get_device_manager()
            devices = await manager.scan_for_devices()
            await manager.refresh_device_status()
            
            return manager.get_devices_list()
        except Exception as e:
            logger.error(f"Failed to scan devices: {e}")
            return []
    
    async def get_active_device_id(self) -> Optional[str]:
        """Get the currently active device ID."""
        manager = await self.get_device_manager()
        return manager.active_device_id
    
    async def connect_device(self, device_id: str) -> bool:
        """Connect to a specific device."""
        try:
            manager = await self.get_device_manager()
            success = await manager.connect_device(device_id)
            
            if success:
                logger.info(f"Connected to device: {device_id}")
            else:
                logger.warning(f"Failed to connect to device: {device_id}")
            
            return success
        except Exception as e:
            logger.error(f"Connection error for device {device_id}: {e}")
            return False
    
    async def disconnect_device(self, device_id: str) -> bool:
        """Disconnect from a specific device."""
        try:
            manager = await self.get_device_manager()
            success = await manager.disconnect_device(device_id)
            
            if success:
                logger.info(f"Disconnected from device: {device_id}")
            
            return success
        except Exception as e:
            logger.error(f"Disconnect error for device {device_id}: {e}")
            return False
    
    async def disconnect_all(self) -> None:
        """Disconnect from all devices."""
        try:
            manager = await self.get_device_manager()
            await manager.disconnect_all()
            logger.info("Disconnected from all devices")
        except Exception as e:
            logger.error(f"Error disconnecting all devices: {e}")
    
    async def select_device(self, device_id: str) -> bool:
        """Select a device as active."""
        try:
            manager = await self.get_device_manager()
            return manager.select_device(device_id)
        except Exception as e:
            logger.error(f"Error selecting device {device_id}: {e}")
            return False
    
    async def get_device_status(self) -> Optional[DeviceStatus]:
        """Get status of the currently connected device."""
        try:
            conn = await self.get_connector()
            status = await conn.get_device_status()
            
            if status and status.connected:
                return DeviceStatus(
                    device_id=status.device_info.get('port', 'unknown'),
                    connected=status.connected,
                    connection_type=conn.current_connection.value if conn.current_connection else "none",
                    recording=status.recording,
                    files=status.files,
                    sd_card_present=status.sd_card_present,
                    ble_connected=status.ble_connected,
                    free_ram=status.free_ram,
                    battery_voltage=status.battery_voltage,
                    battery_percentage=status.battery_percentage,
                    battery_status=status.battery_status,
                    device_model=status.device_info.get('device_model', 'ESP32S3'),
                    port=status.device_info.get('port', 'N/A')
                )
            return None
        except Exception as e:
            logger.error(f"Error getting device status: {e}")
            return None
    
    async def get_recordings(self) -> List[Dict[str, Any]]:
        """Get list of recordings from the device."""
        try:
            conn = await self.get_connector()
            recordings = await conn.get_recordings()
            
            return [
                {
                    "name": rec.name,
                    "size": rec.size,
                    "size_mb": round(rec.size / (1024 * 1024), 2),
                    "date": rec.date if hasattr(rec, 'date') else None
                }
                for rec in recordings
            ]
        except Exception as e:
            logger.error(f"Error getting recordings: {e}")
            return []
    
    async def download_recording(self, filename: str) -> Optional[bytes]:
        """Download a recording from the device."""
        try:
            conn = await self.get_connector()
            return await conn.download_file(filename)
        except Exception as e:
            logger.error(f"Error downloading recording {filename}: {e}")
            return None
    
    async def delete_recording(self, filename: str) -> bool:
        """Delete a recording from the device."""
        try:
            conn = await self.get_connector()
            return await conn.delete_file(filename)
        except Exception as e:
            logger.error(f"Error deleting recording {filename}: {e}")
            return False
    
    async def send_command(self, command: str) -> Optional[str]:
        """Send a command to the device."""
        try:
            conn = await self.get_connector()
            return await conn.send_command(command)
        except Exception as e:
            logger.error(f"Error sending command '{command}': {e}")
            return None


# Singleton instance
_device_service: Optional[DeviceService] = None


def get_device_service() -> DeviceService:
    """Get the device service singleton."""
    global _device_service
    if _device_service is None:
        _device_service = DeviceService()
    return _device_service
