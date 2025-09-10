# Multi-Device Support for Brutally Honest AI

## Overview

The Brutally Honest AI system now supports connecting to multiple ESP32S3 devices simultaneously. This enhancement allows users to manage multiple devices, switch between them, and perform operations on the selected active device.

## Features

### ✅ Multiple Device Detection
- **USB Devices**: Automatically detects ESP32S3 devices connected via USB
- **BLE Devices**: Scans for Bluetooth Low Energy ESP32S3 devices
- **Smart Detection**: Uses VID/PID, device descriptions, and manufacturer info for accurate identification
- **Confidence Scoring**: Each device gets a confidence score (0-100%) for ESP32S3 compatibility

### ✅ Device Management
- **Connect/Disconnect**: Individual device connection management
- **Active Device Selection**: Select which device to use for operations
- **Status Monitoring**: Real-time status updates for all connected devices
- **Device Information**: Battery, recording status, file count, and connection type

### ✅ Enhanced UI
- **Device List**: Visual list showing all detected devices
- **Connection Status**: Clear indicators for connected/disconnected/recording states
- **Device Types**: Icons differentiate between USB and BLE connections
- **Active Device Highlighting**: Visual indication of the currently active device

## API Endpoints

### New Multi-Device Endpoints

- `GET /devices/status` - Get status of all detected devices
- `POST /devices/connect/{device_id}` - Connect to a specific device
- `POST /devices/disconnect/{device_id}` - Disconnect from a specific device
- `POST /devices/select/{device_id}` - Select a device as active

### Legacy Compatibility

All existing endpoints continue to work and automatically use the currently active device:
- `GET /device/info` - Uses active device
- `GET /device/recordings` - Uses active device
- `POST /connect_device` - Connects to first available device

## Architecture

### Backend Components

1. **MultiDeviceManager** (`src/audio/multi_device_manager.py`)
   - Manages multiple device connections
   - Handles device scanning and status updates
   - Maintains active device selection

2. **Enhanced API Server** (`api_server.py`)
   - New multi-device endpoints
   - Backward compatibility with existing endpoints
   - Auto-initialization and cleanup

3. **Unified Connector** (existing, enhanced)
   - Individual device connection management
   - USB and BLE support per device

### Frontend Components

1. **Device Manager** (`frontend/public/devices_manager.js`)
   - Enhanced device scanning and selection
   - Multi-device UI rendering
   - Connection management

2. **Visual Enhancements**
   - Device type icons (USB/BLE)
   - Active device highlighting
   - Connection status badges
   - Confidence indicators

## Usage

### For Users

1. **Device Detection**: The system automatically scans for devices on startup
2. **Device Selection**: Click on any detected device to connect
3. **Active Device**: The selected device becomes active for all operations
4. **Multiple Connections**: Connect to multiple devices simultaneously
5. **Device Switching**: Switch between connected devices as needed

### For Developers

```python
from audio.multi_device_manager import get_device_manager

# Get device manager
manager = get_device_manager()

# Scan for devices
devices = await manager.scan_for_devices()

# Connect to a device
await manager.connect_device(device_id)

# Select active device
manager.select_device(device_id)

# Get active connector
connector = manager.get_active_connector()
```

## Device Identification

The system uses multiple methods to identify ESP32S3 devices:

### Priority 1: VID/PID (Most Reliable)
- `0x303A:0x1001` - Espressif ESP32S3
- `0x303A:0x0002` - Espressif ESP32S3 (alternate)
- `0x303A:0x4001` - Espressif ESP32S3 (JTAG)
- `0x2886:0x0045` - Seeed XIAO ESP32S3
- `0x2886:0x8045` - Seeed XIAO ESP32S3 (alternate)

### Priority 2: Device Description Keywords
- esp32, esp32s3, xiao, seeed, brutally, honest, omi, devkit, espressif

### Priority 3: Manufacturer
- Espressif, Seeed, Seeed Studio

### Priority 4: Generic USB Serial Patterns
- /dev/cu.usbmodem (macOS)
- /dev/ttyUSB (Linux)
- COM (Windows)

## Backward Compatibility

The multi-device system is fully backward compatible:

- **Existing Code**: All existing code continues to work unchanged
- **Single Device Mode**: If only one device is connected, behavior is identical to before
- **Auto-Selection**: First high-confidence device is automatically selected
- **Legacy Endpoints**: All existing API endpoints work with the active device

## Configuration

No additional configuration is required. The system automatically:
- Detects available devices
- Manages connections
- Handles device switching
- Maintains backward compatibility

## Benefits

1. **Scalability**: Support for multiple ESP32S3 devices
2. **Flexibility**: Switch between devices without reconnection
3. **Reliability**: Better device detection and connection management
4. **User Experience**: Clear visual feedback and device management
5. **Developer Experience**: Simple API for multi-device operations

## Future Enhancements

- **Device Naming**: Custom names for devices
- **Device Groups**: Organize devices into groups
- **Simultaneous Operations**: Perform operations on multiple devices
- **Device Profiles**: Save device-specific settings
- **Advanced Filtering**: Filter devices by type, status, or capabilities
