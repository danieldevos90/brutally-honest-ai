"""
Multi-Device Manager for ESP32S3 Brutally Honest AI Devices
Handles multiple device connections and management
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .unified_connector import UnifiedESP32S3Connector, ConnectionType, DeviceStatus
from .omi_connector import ESP32S3Connector
from .bluetooth_connector import BluetoothOMIConnector

logger = logging.getLogger(__name__)

@dataclass
class DeviceInfo:
    """Extended device information for multi-device management"""
    device_id: str  # Unique identifier (port or BLE address)
    device_type: str  # "USB" or "BLE"
    port: str  # Serial port or BLE address
    description: str  # Human-readable description
    connected: bool = False
    recording: bool = False
    recordings: int = 0
    battery: str = "Unknown"
    free_ram: str = "Unknown"
    confidence: int = 0  # Detection confidence (0-100)
    last_seen: float = 0.0  # Timestamp of last successful communication
    connector: Optional[UnifiedESP32S3Connector] = None

class MultiDeviceManager:
    """Manager for multiple ESP32S3 Brutally Honest AI devices"""
    
    def __init__(self):
        """Initialize multi-device manager"""
        self.devices: Dict[str, DeviceInfo] = {}
        self.active_device_id: Optional[str] = None
        self.scan_lock = asyncio.Lock()
        
    async def scan_for_devices(self) -> List[DeviceInfo]:
        """Scan for all available ESP32S3 devices (USB and BLE)"""
        async with self.scan_lock:
            logger.info("🔍 Scanning for ESP32S3 devices...")
            
            # Clear previous scan results but keep connected devices
            new_devices = {}
            for device_id, device in self.devices.items():
                if device.connected and device.connector:
                    new_devices[device_id] = device
            
            # Scan USB devices
            usb_devices = await self._scan_usb_devices()
            for device in usb_devices:
                new_devices[device.device_id] = device
            
            # Scan BLE devices
            ble_devices = await self._scan_ble_devices()
            for device in ble_devices:
                new_devices[device.device_id] = device
            
            self.devices = new_devices
            
            # Update last seen timestamp
            current_time = time.time()
            for device in self.devices.values():
                device.last_seen = current_time
            
            # Count connected vs detected devices
            connected_count = sum(1 for d in self.devices.values() if d.connected)
            detected_count = len(self.devices)
            
            if detected_count > 0:
                if connected_count > 0:
                    logger.info(f"✅ Found {detected_count} ESP32S3 device(s), {connected_count} connected")
                else:
                    logger.info(f"🔍 Found {detected_count} ESP32S3 device(s), none connected")
            else:
                logger.info("🔍 No ESP32S3 devices found")
            return list(self.devices.values())
    
    async def _scan_usb_devices(self) -> List[DeviceInfo]:
        """Scan for USB ESP32S3 devices"""
        usb_devices = []
        
        try:
            # Get all serial ports with ESP32S3 detection
            ports = ESP32S3Connector.get_all_serial_ports()
            
            for port_info in ports:
                # Only include devices that are likely ESP32S3 devices
                # Skip low-confidence generic ports like debug-console, Bluetooth-Incoming-Port
                if not port_info['is_esp32s3'] or port_info['confidence'] < 50:
                    continue
                
                device_id = f"usb_{port_info['device']}"
                
                # Check if this device is already connected
                existing_device = self.devices.get(device_id)
                if existing_device and existing_device.connected:
                    # Update status of connected device
                    await self._update_device_status(existing_device)
                    usb_devices.append(existing_device)
                    continue
                
                # Create new device info for high-confidence ESP32S3 devices only
                device = DeviceInfo(
                    device_id=device_id,
                    device_type="USB",
                    port=port_info['device'],
                    description=port_info['description'],
                    connected=False,
                    confidence=port_info['confidence']
                )
                
                # Try to get basic status without full connection
                if port_info['confidence'] > 70:
                    try:
                        # Quick status check
                        temp_connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
                        # Don't fully initialize, just check if device responds
                        device.connected = False  # Will be set to True when explicitly connected
                    except Exception as e:
                        logger.debug(f"Quick status check failed for {device.port}: {e}")
                
                usb_devices.append(device)
                
        except Exception as e:
            logger.error(f"USB device scan error: {e}")
        
        return usb_devices
    
    async def _scan_ble_devices(self) -> List[DeviceInfo]:
        """Scan for BLE ESP32S3 devices"""
        ble_devices = []
        
        try:
            # Create temporary BLE connector for scanning
            ble_connector = BluetoothOMIConnector(connection_type="ble")
            discovered_devices = await ble_connector.scan_for_devices(timeout=5)
            
            for address, name in discovered_devices.items():
                device_id = f"ble_{address}"
                
                # Check if this device is already connected
                existing_device = self.devices.get(device_id)
                if existing_device and existing_device.connected:
                    # Update status of connected device
                    await self._update_device_status(existing_device)
                    ble_devices.append(existing_device)
                    continue
                
                # Create new device info
                device = DeviceInfo(
                    device_id=device_id,
                    device_type="BLE",
                    port=address,
                    description=f"{name} ({address})",
                    connected=False,
                    confidence=90  # BLE devices found by name have high confidence
                )
                
                ble_devices.append(device)
                
        except Exception as e:
            logger.error(f"BLE device scan error: {e}")
        
        return ble_devices
    
    async def connect_device(self, device_id: str) -> bool:
        """Connect to a specific device"""
        device = self.devices.get(device_id)
        if not device:
            logger.error(f"Device {device_id} not found")
            return False
        
        if device.connected and device.connector:
            logger.info(f"Device {device_id} already connected")
            self.active_device_id = device_id
            return True
        
        try:
            logger.info(f"🔌 Connecting to device {device_id} ({device.description})")
            
            # Create appropriate connector
            if device.device_type == "USB":
                connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
            else:  # BLE
                connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.BLE)
            
            # Initialize connection
            if await connector.initialize():
                device.connector = connector
                device.connected = True
                self.active_device_id = device_id
                
                # Update device status
                await self._update_device_status(device)
                
                logger.info(f"✅ Connected to device {device_id}")
                return True
            else:
                logger.error(f"❌ Failed to connect to device {device_id}")
                return False
                
        except Exception as e:
            logger.error(f"Connection error for device {device_id}: {e}")
            return False
    
    async def disconnect_device(self, device_id: str) -> bool:
        """Disconnect from a specific device"""
        device = self.devices.get(device_id)
        if not device or not device.connected:
            return True
        
        try:
            if device.connector:
                await device.connector.disconnect()
                device.connector = None
            
            device.connected = False
            
            # If this was the active device, clear active device
            if self.active_device_id == device_id:
                self.active_device_id = None
            
            logger.info(f"🔌 Disconnected from device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Disconnect error for device {device_id}: {e}")
            return False
    
    async def disconnect_all(self):
        """Disconnect from all devices"""
        for device_id in list(self.devices.keys()):
            await self.disconnect_device(device_id)
    
    def select_device(self, device_id: str) -> bool:
        """Select a device as the active device"""
        device = self.devices.get(device_id)
        if not device or not device.connected:
            logger.error(f"Cannot select device {device_id}: not connected")
            return False
        
        self.active_device_id = device_id
        logger.info(f"📱 Selected device {device_id} as active")
        return True
    
    def get_active_device(self) -> Optional[DeviceInfo]:
        """Get the currently active device"""
        if self.active_device_id:
            return self.devices.get(self.active_device_id)
        return None
    
    def get_active_connector(self) -> Optional[UnifiedESP32S3Connector]:
        """Get the connector for the active device"""
        active_device = self.get_active_device()
        if active_device and active_device.connected:
            return active_device.connector
        return None
    
    async def _update_device_status(self, device: DeviceInfo):
        """Update status information for a connected device"""
        if not device.connected or not device.connector:
            return
        
        try:
            status = await device.connector.get_device_status()
            if status:
                device.recording = status.recording
                device.recordings = status.files
                device.free_ram = str(status.free_ram)
                
                # Format battery info
                if status.battery_percentage > 0:
                    device.battery = f"{status.battery_percentage}%"
                elif status.battery_voltage > 0:
                    device.battery = f"{status.battery_voltage:.2f}V"
                else:
                    device.battery = status.battery_status
                
                device.last_seen = time.time()
                
        except Exception as e:
            logger.debug(f"Status update failed for device {device.device_id}: {e}")
    
    def get_devices_list(self) -> List[Dict[str, Any]]:
        """Get list of all devices as dictionaries for API response"""
        devices_list = []
        
        for device in self.devices.values():
            device_dict = {
                "device_id": device.device_id,
                "device_type": device.device_type,
                "port": device.port,
                "description": device.description,
                "connected": device.connected,
                "recording": device.recording,
                "recordings": device.recordings,
                "battery": device.battery,
                "free_ram": device.free_ram,
                "confidence": device.confidence,
                "last_seen": device.last_seen,
                "is_active": device.device_id == self.active_device_id
            }
            devices_list.append(device_dict)
        
        # Sort by connection status and confidence
        devices_list.sort(key=lambda x: (x['connected'], x['confidence']), reverse=True)
        return devices_list
    
    async def refresh_device_status(self):
        """Refresh status for all connected devices"""
        for device in self.devices.values():
            if device.connected:
                await self._update_device_status(device)

# Global multi-device manager instance
_device_manager: Optional[MultiDeviceManager] = None

def get_device_manager() -> MultiDeviceManager:
    """Get or create the global device manager"""
    global _device_manager
    if _device_manager is None:
        _device_manager = MultiDeviceManager()
    return _device_manager

# Example usage
async def main():
    """Example usage of multi-device manager"""
    manager = get_device_manager()
    
    try:
        # Scan for devices
        devices = await manager.scan_for_devices()
        print(f"✅ Found {len(devices)} devices:")
        for device in devices:
            print(f"   - {device.description} ({device.device_type}) - Confidence: {device.confidence}%")
        
        # Connect to first available device
        if devices:
            device_id = devices[0].device_id
            if await manager.connect_device(device_id):
                print(f"✅ Connected to {device_id}")
                
                # Get device status
                active_device = manager.get_active_device()
                if active_device:
                    print(f"📊 Active Device: {active_device.description}")
                    print(f"   Recording: {active_device.recording}")
                    print(f"   Files: {active_device.recordings}")
                    print(f"   Battery: {active_device.battery}")
            
    finally:
        await manager.disconnect_all()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
