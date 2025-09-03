# ESP32S3 PDM Fixed - Brutally Honest AI Firmware

## 🎯 **Latest Stable Version**

This is the **latest and most stable firmware** for the Brutally Honest AI project, featuring working audio recording, LED animations, and comprehensive I2C diagnostics.

## ✨ **Key Features**

### 🎤 **Working Microphone System**
- **PDM Microphone Support** - Properly configured ESP32-I2S library
- **High-Quality Audio Recording** - 16kHz sample rate, 16-bit depth
- **Automatic Gain Control** - Optimized audio levels
- **SD Card Storage** - WAV file format with timestamps
- **Real-time Audio Processing** - Efficient buffer management

### 💡 **LED Status Indicators**
- **Recording Status** - Visual feedback during audio capture
- **Connection Status** - BLE connection indicators  
- **System Status** - Boot, ready, and error states
- **Customizable Animations** - Smooth LED transitions

### 📡 **Bluetooth Low Energy (BLE)**
- **Device Discovery** - Advertises as "Brutal Honest Query"
- **Audio Streaming** - Real-time audio transmission
- **Status Updates** - Recording state and file count
- **Connection Management** - Automatic reconnection

### 🔧 **Advanced Diagnostics**
- **I2C Scanner** - Comprehensive device detection
- **Hardware Testing** - Multiple pin configurations and speeds
- **Serial Commands** - Interactive diagnostic interface
- **Error Reporting** - Detailed troubleshooting information

## 🚀 **Quick Start**

### **Hardware Requirements**
- **XIAO ESP32S3** microcontroller
- **XIAO Expansion Board** (optional, for OLED display)
- **MicroSD Card** (for audio storage)
- **PDM Microphone** (built-in or external)

### **Installation**
1. **Install Arduino IDE** with ESP32 support
2. **Install Required Libraries:**
   ```
   - ESP_I2S (included with ESP32 core)
   - U8g2 (for OLED display)
   - SD (included with ESP32 core)
   - BLE (included with ESP32 core)
   ```
3. **Upload Firmware:**
   ```bash
   arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 esp32s3_pdm_fixed.ino
   arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3 --port /dev/cu.usbmodem101 esp32s3_pdm_fixed.ino
   ```

### **Board Configuration**
```
Board: "XIAO_ESP32S3"
USB CDC On Boot: "Enabled"
CPU Frequency: "240MHz (WiFi)"
Flash Mode: "QIO 80MHz"
Flash Size: "8MB (64Mb)"
Partition Scheme: "8M with spiffs (3MB APP/1.5MB SPIFFS)"
PSRAM: "OPI PSRAM"
Upload Mode: "UART0 / Hardware CDC"
Upload Speed: "921600"
```

## 🎮 **Usage**

### **Recording Audio**
1. **Power on** the device
2. **Press the button** to start recording
3. **LED indicates** recording status (solid/blinking)
4. **Press again** to stop recording
5. **Files saved** to SD card as `recording_YYYYMMDD_HHMMSS.wav`

### **BLE Connection**
1. **Enable Bluetooth** on your device
2. **Scan for "Brutal Honest Query"**
3. **Connect** to start receiving audio stream
4. **LED shows** connection status

### **Serial Diagnostics**
Connect via serial monitor (115200 baud) and use these commands:
- `scan` or `i2c` - Perform I2C device scan
- `test` - Test different I2C configurations
- `help` - Show available commands

## 🔧 **Technical Specifications**

### **Audio System**
- **Sample Rate:** 16,000 Hz
- **Bit Depth:** 16-bit
- **Channels:** Mono
- **Format:** WAV (PCM)
- **Buffer Size:** 1024 samples
- **Microphone:** PDM interface

### **Pin Configuration**
```cpp
// Audio
#define I2S_WS_PIN    42    // PDM Clock
#define I2S_SD_PIN    41    // PDM Data

// LED
#define LED_PIN       21    // Status LED

// Button
#define BUTTON_PIN    1     // Record button

// SD Card (SPI)
#define SD_CS_PIN     D2    // Chip Select
// MOSI: D10, MISO: D9, SCK: D8

// I2C (for OLED - if expansion board used)
#define OLED_SDA      5     // I2C Data
#define OLED_SCL      4     // I2C Clock
```

### **Memory Usage**
- **Program Storage:** ~22% (737KB / 3.3MB)
- **Dynamic Memory:** ~10% (36KB / 327KB)
- **PSRAM:** 8MB available for audio buffers

## 🐛 **Troubleshooting**

### **Audio Issues**
- **No recording:** Check microphone connection and SD card
- **Poor quality:** Verify sample rate and gain settings
- **File corruption:** Ensure stable power supply

### **BLE Issues**
- **Connection fails:** Reset device and clear Bluetooth cache
- **Audio dropouts:** Check distance and interference

### **Hardware Issues**
- **OLED not working:** Run I2C diagnostic (`scan` command)
- **SD card errors:** Format card as FAT32, check connections
- **LED not working:** Verify LED_PIN connection

### **Serial Commands for Debugging**
```
scan    - Scan I2C bus for devices
test    - Test I2C configurations
help    - Show available commands
```

## 📊 **Status Indicators**

### **LED Patterns**
- **Solid ON:** Recording in progress
- **Slow Blink:** Ready to record
- **Fast Blink:** BLE connected
- **Off:** Standby/Error

### **Serial Output**
- **💚 Status:** Normal operation messages
- **🔍 Scan:** I2C diagnostic results  
- **🎤 Audio:** Recording status updates
- **📡 BLE:** Connection status

## 🔄 **Recent Updates**

### **v2.0 - PDM Fixed (Latest)**
- ✅ **Fixed PDM microphone** - Proper ESP32-I2S integration
- ✅ **Enhanced audio quality** - Optimized buffer management
- ✅ **Improved LED feedback** - Clear status indicators
- ✅ **I2C diagnostics** - Comprehensive hardware testing
- ✅ **Better error handling** - Graceful failure recovery
- ✅ **Serial commands** - Interactive debugging interface

### **Known Issues**
- **OLED Display:** May not work on some expansion boards (I2C hardware issue)
- **Workaround:** Use serial monitor for status instead of OLED

## 📁 **File Structure**
```
esp32s3_pdm_fixed/
├── esp32s3_pdm_fixed.ino    # Main firmware file
└── README.md                # This documentation
```

## 🤝 **Contributing**

This firmware is part of the Brutally Honest AI project. For issues or improvements:
1. Test thoroughly with the diagnostic commands
2. Document any hardware-specific issues
3. Include serial output in bug reports

## 📄 **License**

This project is part of the Brutally Honest AI system. See main project documentation for licensing details.

---

**🎯 This is the recommended firmware version for production use with working microphone and LED features!**