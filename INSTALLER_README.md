# Brutally Honest AI - Easy Installation Guide

## 🎯 What This Does

This installer sets up your **XIAO ESP32S3 Sense + Expansion Board** to become a **Brutally Honest AI** device that:
- Records audio when you press the button
- Shows "Brutal Honest Query" on the OLED display
- Saves recordings to SD card
- Transcribes speech using Whisper AI
- Syncs recordings with your computer
- Provides a web interface for management

## 📋 Prerequisites

### Hardware Required
- **Seeed Studio XIAO ESP32S3 Sense**
- **XIAO Expansion Board** (with OLED display)
- **Micro SD Card** (formatted as FAT32)
- **USB-C Cable** (data cable, not charging-only)

### Software Will Be Installed
The installer will automatically install:
- Arduino CLI
- ESP32 board support
- Required Arduino libraries
- Python dependencies
- Web interface

## 🚀 Quick Start

### For Mac/Linux Users
```bash
# Download and run the installer
./install_brutally_honest.sh
```

### For Windows Users
```cmd
# Run the installer
install_brutally_honest.bat
```

## 📱 Installation Steps

### Step 1: Connect Your Device
1. Insert the micro SD card into the expansion board
2. Connect XIAO ESP32S3 to the expansion board
3. Connect to your computer via USB-C cable

### Step 2: Run the Installer
The installer will:
1. Check and install dependencies
2. Setup Arduino environment
3. Detect your device
4. Compile the firmware
5. Upload to your device
6. Start all services

### Step 3: If Device Not Detected
Put device in BOOT mode:
1. **Hold** the BOOT button on ESP32S3
2. **Press and release** RESET while holding BOOT
3. **Keep holding** BOOT for 2-3 seconds
4. **Release** BOOT button

## 🎮 Using Your Device

### Basic Operation
- **First click**: Start recording (LED blinks)
- **Second click**: Stop recording
- Display shows "Brutal Honest Query"
- Recordings saved to SD card

### Status Indicators
- **LED blinking**: Recording in progress
- **Buzzer beep**: Button press confirmed
- **Display**: Shows current status

## 🌐 Accessing Your Recordings

### Method 1: WiFi Access Point
1. Connect to WiFi: `OMI-ESP32S3`
2. Password: `brutalhonest`
3. Open browser: `http://192.168.4.1`

### Method 2: Web Interface
1. Open browser: `http://localhost:3000`
2. View recordings and transcriptions
3. Download audio files

### Method 3: SD Card
1. Remove SD card from device
2. Insert into computer
3. Files in `/recordings` folder

## 🛠️ Troubleshooting

### Display Not Working
- Run installer again, choose option 3 (OLED test)
- Check expansion board connection
- Ensure OLED display ribbon cable is connected

### Button Not Responding
- Make sure you're pressing the user button (D1)
- Check serial monitor for debug info
- Try the toggle recording test (option 2)

### Device Keeps Disconnecting
1. Use BOOT mode for upload
2. Try different USB cable
3. Use powered USB hub

### Recordings Not Saving
- Check SD card is formatted as FAT32
- Ensure SD card is properly inserted
- Maximum 32GB SD cards supported

## 📊 Monitoring Your Device

View debug information:
```bash
# Mac/Linux
arduino-cli monitor --port /dev/cu.usbmodem*

# Windows
arduino-cli monitor --port COM3
```

## 🔧 Advanced Configuration

### Change WiFi Credentials
Edit `omi_firmware/esp32s3_ble/esp32s3_ble.ino`:
```cpp
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_PASSWORD";
```

### Adjust Recording Settings
```cpp
#define RECORDING_DURATION_MS 30000  // 30 seconds max
#define SAMPLE_RATE 16000           // Audio quality
```

## 📱 Mobile App Integration

The device supports BLE connections:
- Service UUID: `12345678-1234-1234-1234-123456789abc`
- Audio streaming and control
- Real-time transcriptions

## 🆘 Getting Help

1. Check serial monitor output
2. Review [GitHub Issues](https://github.com/yourusername/brutally-honest-ai)
3. Join our Discord community

## 🎉 Success Checklist

- [ ] OLED displays "Brutal Honest Query"
- [ ] Button starts/stops recording
- [ ] LED blinks during recording
- [ ] Buzzer beeps on button press
- [ ] Recordings save to SD card
- [ ] Web interface accessible
- [ ] Transcriptions working

Enjoy your Brutally Honest AI device! 🚀
