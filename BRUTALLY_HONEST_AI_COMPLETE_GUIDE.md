# 🤖 Brutally Honest AI - Complete System Guide

## 🎯 **Overview**

Brutally Honest AI is a real-time voice analysis system that combines ESP32S3 hardware with AI-powered transcription and fact-checking. The system captures audio, transcribes speech using Whisper, and provides brutally honest analysis using LLM models.

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ESP32S3       │    │   Bridge        │    │   Frontend      │
│   Hardware      │◄──►│   Server        │◄──►│   Web App       │
│                 │    │                 │    │                 │
│ • Microphone    │    │ • Audio Proc.   │    │ • Live Demo     │
│ • SD Storage    │    │ • Transcription │    │ • Device Status │
│ • BLE/USB       │    │ • LLM Analysis  │    │ • File Manager  │
│ • OLED Display  │    │ • WebSocket     │    │ • Real-time UI  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🔧 **ESP32S3 Complete RTC Firmware**

### **📋 Features**

#### **🎤 Audio Recording System**
- **PDM Microphone Support** - High-quality 16kHz, 16-bit mono recording
- **Real-time Processing** - Live audio streaming via USB and BLE
- **SD Card Storage** - Automatic WAV file creation with timestamps
- **Audio Markers** - `AUDIO_START` and `AUDIO_END` markers for streaming

#### **🕐 Real-Time Clock (RTC)**
- **PCF8563 RTC Module** - Accurate timekeeping with battery backup
- **Timestamp Recording** - Files named with date/time: `rec_YYYYMMDD_HHMMSS.wav`
- **Display Integration** - Live date/time on OLED display
- **Power Loss Recovery** - Automatic time restoration

#### **📱 Bluetooth Low Energy (BLE)**
- **Device Name:** `BrutallyHonestAI`
- **Service UUID:** `12345678-1234-5678-1234-56789abcdef0`
- **Audio Streaming** - Real-time audio transmission in 20-byte chunks
- **Status Broadcasting** - Recording state, file count, device info
- **Auto-reconnection** - Robust connection management

#### **🖥️ OLED Display (128x64)**
- **System Status** - Recording state, file count, BLE connection
- **Real-time Clock** - Date and time display
- **Connection Info** - BLE status and device information
- **User Interface** - Button prompts and status messages

#### **🔘 Button Control**
- **GPIO2 (D2)** - Primary record button with interrupt handling
- **Debouncing** - 200ms debounce delay for reliable operation
- **Visual Feedback** - LED and OLED status updates
- **Dual Detection** - Interrupt + polling for maximum reliability

#### **💡 LED Status System**
- **Recording Indicator** - Blinking during recording
- **Connection Status** - BLE connection feedback
- **System Status** - Boot, ready, and error states
- **Inverted Logic** - Compatible with XIAO ESP32S3 built-in LED

### **📌 Pin Configuration**

```cpp
// Hardware Pins (XIAO ESP32S3 + Expansion Board)
#define BUTTON_PIN 2        // Button(D2) - GPIO2 ✅ FIXED!
#define BUZZER_PIN 3        // Buzzer(A3) - GPIO3  
#define LED_PIN 21          // Built-in LED (inverted logic)
#define SD_CS_PIN 21        // SD card chip select

// PDM Microphone (ESP32S3 Sense)
#define PDM_CLK_PIN 42      // PDM Clock
#define PDM_DATA_PIN 41     // PDM Data

// I2C (Expansion Board)
// SDA: GPIO5, SCL: GPIO4 (default Wire pins)
```

### **🚀 Installation Instructions**

#### **1. Hardware Setup**
```bash
# Required Components:
- XIAO ESP32S3 microcontroller
- XIAO Expansion Board (for OLED, SD, Buzzer)
- MicroSD Card (FAT32 formatted)
- PCF8563 RTC module (I2C)
- Button connected to GPIO2
```

#### **2. Arduino IDE Configuration**
```bash
# Board Settings:
Board: "XIAO_ESP32S3"
USB CDC On Boot: "Enabled"
CPU Frequency: "240MHz (WiFi)"
Flash Mode: "QIO 80MHz"
Flash Size: "8MB (64Mb)"
Partition Scheme: "8M with spiffs (3MB APP/1.5MB SPIFFS)"
PSRAM: "OPI PSRAM"
Upload Speed: "921600"
```

#### **3. Required Libraries**
```bash
# Install via Arduino Library Manager:
- ESP_I2S (ESP32 core)
- U8x8lib (U8g2 library)
- RTClib (Adafruit RTClib)
- SD (ESP32 core)
- BLEDevice (ESP32 core)
- WiFi (ESP32 core)
```

#### **4. Upload Firmware**
```bash
# Navigate to firmware directory
cd omi_firmware/esp32s3_complete_rtc/

# Compile and upload
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 esp32s3_complete_rtc.ino
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3 --port /dev/cu.usbmodem* esp32s3_complete_rtc.ino
```

### **🎮 Usage Instructions**

#### **Basic Operation**
1. **Power On** - Device boots and shows startup sequence
2. **Press Button** - Start/stop recording (GPIO2)
3. **LED Feedback** - Blinking = recording, solid = ready
4. **OLED Display** - Shows time, status, file count
5. **SD Storage** - Files saved as `/recordings/rec_YYYYMMDD_HHMMSS.wav`

#### **Serial Commands** (115200 baud)
```bash
L or l  - List SD card files
S or s  - Device status (recording, files, RAM, BLE)
I or i  - Device information (model, cores, flash, MAC, uptime)
```

#### **BLE Connection**
1. **Scan for "BrutallyHonestAI"** on your device
2. **Connect** - Device shows "BLE Client Connected!"
3. **Audio Stream** - Real-time audio data transmission
4. **Status Updates** - Recording state and file count every 5 seconds

### **🔧 Technical Specifications**

```cpp
// Audio Configuration
#define SAMPLE_RATE 16000   // 16kHz sampling
#define SAMPLE_BITS 16      // 16-bit depth
// Format: WAV PCM Mono

// Memory Usage
Program Storage: ~737KB / 3.3MB (22%)
Dynamic Memory: ~36KB / 327KB (10%)
PSRAM: 8MB available

// File System
SD Card: FAT32 format required
Directory: /recordings/
Filename: rec_YYYYMMDD_HHMMSS.wav
Header: Standard WAV format (44 bytes)
```

---

## 🌐 **Frontend Web Application**

### **📋 Features**

#### **🎤 Live Recording Interface**
- **Real-time Controls** - Start/Stop recording buttons
- **Visual Feedback** - Recording indicator with pulse animation
- **Status Display** - Connection state and recording progress
- **System Log** - Optional detailed logging with timestamps

#### **📊 System Status Dashboard**
- **Backend Status** - API server connection indicator
- **LLM Status** - Ollama/AI model availability
- **Audio Status** - Device connection and streaming capability
- **Connection Info** - Battery, signal strength, connection type

#### **📱 Device Management**
- **ESP32S3 Status** - Real-time device information
- **SD Card Files** - List and manage recordings
- **BLE Connection** - Bluetooth device pairing and info
- **USB Refresh** - Manual device detection

#### **🧠 AI Analysis Display**
- **Live Transcription** - Real-time speech-to-text with Whisper
- **Brutal Honesty** - AI fact-checking and analysis
- **Robot Status** - Processing states with visual indicators
- **Results Container** - Transcript and analysis display

#### **🔗 Connection Management**
- **WebSocket Streaming** - Real-time audio and data transmission
- **Auto-reconnection** - Automatic connection recovery
- **Multiple Protocols** - USB, Bluetooth, and network support
- **Status Broadcasting** - Live updates every 5 seconds

### **🚀 Installation Instructions**

#### **1. Prerequisites**
```bash
# Install Node.js (v16 or higher)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Or on macOS:
brew install node
```

#### **2. Frontend Setup**
```bash
# Navigate to frontend directory
cd frontend/

# Install dependencies
npm install

# Install required packages
npm install express cors multer ws node-fetch form-data
```

#### **3. Start Frontend Server**
```bash
# Development mode
npm start
# or
node server.js

# Production mode
NODE_ENV=production node server.js
```

#### **4. Access Web Interface**
```bash
# Open browser to:
http://localhost:3000

# WebSocket connection:
ws://localhost:3001
```

### **🎮 Usage Instructions**

#### **Live Demo Mode**
1. **Open Web Interface** - Navigate to `http://localhost:3000`
2. **Check System Status** - Verify backend and device connections
3. **Start Recording** - Click "Start Recording" button
4. **Speak Clearly** - Talk into ESP32S3 microphone
5. **View Results** - See live transcription and AI analysis
6. **Stop Recording** - Click "Stop Recording" when finished

#### **Device Management**
1. **USB Connection** - Click "USB Refresh" to detect device
2. **BLE Connection** - Click "Connect BLE" for Bluetooth pairing
3. **File Management** - View SD card recordings in device status
4. **System Log** - Enable for detailed debugging information

### **🔧 API Endpoints**

```javascript
// System Status
GET /api/status
// Response: { omi_connected, audio_processor, llm_analyzer, ... }

// Device Detection
GET /api/omi/ports
// Response: { count, omi_detected, omi_device, ports[] }

// Device Testing
GET /api/test/omi
// Response: { device_found, connection_successful, streaming_ready }

// BLE Connection
POST /api/ble/connect
// Response: { success, message, device_name }

// Device Information
GET /api/ble/info
// Response: { battery_level, recording_count, storage_used, ... }

// Audio Upload
POST /api/audio/upload
// Body: FormData with audio file
// Response: { transcript, analysis, confidence, ... }
```

---

## 🔄 **Bridge Server**

### **📋 Features**

#### **🎤 Audio Processing Pipeline**
- **Real-time Streaming** - USB and BLE audio capture
- **Whisper Integration** - OpenAI Whisper for transcription
- **Buffer Management** - Efficient audio data handling
- **Format Conversion** - WAV processing and optimization

#### **🧠 LLM Integration**
- **Ollama Support** - Local LLM model execution
- **Fact Checking** - Brutal honesty analysis
- **Response Generation** - Contextual AI feedback
- **Model Management** - Automatic model loading

#### **📡 Communication Hub**
- **WebSocket Server** - Real-time client communication
- **REST API** - HTTP endpoints for device management
- **Device Detection** - Automatic ESP32S3 discovery
- **Protocol Bridge** - USB/BLE to WebSocket translation

### **🚀 Installation Instructions**

#### **1. Python Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

#### **2. Required Dependencies**
```bash
# Core packages
pip install fastapi uvicorn websockets
pip install pyserial pyusb bleak
pip install openai-whisper torch
pip install requests aiofiles
```

#### **3. Ollama Setup**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required model
ollama pull llama2
# or
ollama pull mistral
```

#### **4. Start Bridge Server**
```bash
# Run bridge server
python bridge_server.py

# Or with specific port
python bridge_server.py --port 5000
```

### **🔧 Configuration**

```python
# Bridge Server Settings
API_PORT = 5000
WEBSOCKET_PORT = 5000
DEVICE_SCAN_INTERVAL = 5.0
AUDIO_BUFFER_SIZE = 1024
WHISPER_MODEL = "base"
LLM_MODEL = "llama2"
```

---

## 🛠️ **Complete System Setup**

### **🚀 Quick Start (All Components)**

#### **1. Hardware Setup**
```bash
# 1. Assemble ESP32S3 with expansion board
# 2. Insert formatted SD card
# 3. Connect via USB for initial setup
# 4. Upload firmware using Arduino IDE
```

#### **2. Software Installation**
```bash
# Clone repository
git clone <repository-url>
cd brutally-honest-ai

# Install Python dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Node.js dependencies
cd frontend
npm install
cd ..

# Install Ollama and models
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2
```

#### **3. Start All Services**
```bash
# Terminal 1: Bridge Server
python bridge_server.py

# Terminal 2: Frontend Server
cd frontend
npm start

# Terminal 3: Monitor ESP32S3 (optional)
python -c "import serial; s=serial.Serial('/dev/cu.usbmodem*', 115200); [print(s.readline().decode()) for _ in range(100)]"
```

#### **4. Access System**
```bash
# Web Interface
http://localhost:3000

# API Documentation
http://localhost:5000/docs

# Device Serial Monitor
# Use Arduino IDE Serial Monitor at 115200 baud
```

### **🔧 System Configuration**

#### **Environment Variables**
```bash
# Create .env file
cp env.example .env

# Configure settings
WHISPER_MODEL=base
LLM_MODEL=llama2
API_PORT=5000
FRONTEND_PORT=3000
DEVICE_SCAN_INTERVAL=5.0
LOG_LEVEL=INFO
```

#### **Device Settings**
```cpp
// ESP32S3 Configuration (in firmware)
#define SAMPLE_RATE 16000
#define SAMPLE_BITS 16
#define DEVICE_NAME "BrutallyHonestAI"
#define BLE_SERVICE_UUID "12345678-1234-5678-1234-56789abcdef0"
```

### **🎮 Complete Workflow**

#### **Recording and Analysis Process**
1. **Device Ready** - ESP32S3 shows "Ready to record" on OLED
2. **Start Recording** - Press button or use web interface
3. **Audio Capture** - Microphone records to SD card and streams
4. **Real-time Display** - LED blinks, OLED shows "RECORDING..."
5. **Stop Recording** - Press button again or use web interface
6. **Processing** - Bridge server processes audio with Whisper
7. **Transcription** - Speech converted to text
8. **AI Analysis** - LLM provides brutal honesty feedback
9. **Results Display** - Web interface shows transcript and analysis
10. **File Storage** - WAV file saved to SD card with timestamp

#### **Connection Modes**
```bash
# USB Mode (Recommended for development)
- Direct serial connection
- Fastest data transfer
- Real-time debugging
- Power from USB

# BLE Mode (Recommended for production)
- Wireless operation
- Battery powered
- Mobile device compatible
- Automatic reconnection

# Hybrid Mode
- USB for power and debugging
- BLE for wireless data
- Best of both worlds
```

---

## 🐛 **Troubleshooting**

### **ESP32S3 Hardware Issues**

#### **Button Not Working**
```bash
# Check pin configuration
Serial Monitor: "Button initial state: HIGH (not pressed)"

# Test button manually
Press and hold button, check serial output for "Button press confirmed!"

# Verify wiring
GPIO2 (D2) → Button → GND
Internal pullup enabled in firmware
```

#### **Audio Recording Problems**
```bash
# Check SD card
Format as FAT32
Insert properly into expansion board slot
Serial output: "✅ SD card initialized"

# Verify microphone
PDM microphone on ESP32S3 Sense
CLK: GPIO42, DATA: GPIO41
Serial output: "✅ PDM Microphone initialized!"

# Test recording
Press button, check for "🎤 Recording started" message
Files should appear in /recordings/ directory
```

#### **OLED Display Issues**
```bash
# I2C scan
Send 'i' command via serial monitor
Should show I2C devices found

# Check connections
SDA: GPIO5, SCL: GPIO4
3.3V and GND properly connected
Serial output: "✅ OLED initialized"
```

#### **BLE Connection Problems**
```bash
# Reset Bluetooth
Clear Bluetooth cache on client device
Power cycle ESP32S3
Serial output: "📡 BLE Advertising started!"

# Check advertising
Device should appear as "BrutallyHonestAI"
Service UUID: 12345678-1234-5678-1234-56789abcdef0
```

### **Software Issues**

#### **Bridge Server Problems**
```bash
# Check dependencies
pip install -r requirements.txt
python -c "import whisper, torch; print('OK')"

# Test device detection
python -c "import serial.tools.list_ports; print([p.device for p in serial.tools.list_ports.comports()])"

# Verify Ollama
ollama list
ollama run llama2 "Hello"
```

#### **Frontend Connection Issues**
```bash
# Check Node.js version
node --version  # Should be v16+

# Install dependencies
cd frontend
npm install

# Test API connection
curl http://localhost:5000/status
curl http://localhost:3000/api/status
```

#### **WebSocket Problems**
```bash
# Check ports
netstat -an | grep 3001  # WebSocket port
netstat -an | grep 5000  # Bridge server port

# Test WebSocket connection
# Browser console: new WebSocket('ws://localhost:3001')
```

### **Performance Optimization**

#### **Audio Quality**
```cpp
// Increase buffer size for better quality
#define AUDIO_BUFFER_SIZE 2048  // Default: 1024

// Adjust gain for microphone sensitivity
audioBuffer[samplesRead] = (int16_t)(sample >> 12);  // Default: >> 14
```

#### **Memory Management**
```cpp
// Monitor free heap
Serial.print("Free RAM: ");
Serial.print(ESP.getFreeHeap() / 1024);
Serial.println(" KB");

// Use PSRAM for large buffers
if (psramFound()) {
    // Allocate audio buffers in PSRAM
}
```

#### **Power Consumption**
```cpp
// Enable WiFi power saving
WiFi.setSleep(true);

// Reduce CPU frequency when idle
setCpuFrequencyMhz(80);  // Default: 240MHz
```

---

## 📊 **System Monitoring**

### **Device Status Monitoring**
```bash
# ESP32S3 Serial Commands
L - List SD card files
S - Device status (recording, files, RAM, BLE)
I - Device info (model, cores, flash, MAC, uptime)

# Example output:
📊 Device Status:
   - Recording: NO
   - Files: 5
   - SD Card: Present
   - BLE Connected: YES
   - Free RAM: 285 KB
```

### **Web Interface Monitoring**
```javascript
// System status indicators
Backend: Online/Offline
LLM: Online/Offline  
Audio: Online/Offline

// Connection information
Connection: Bluetooth/USB
Battery: 85%
Signal: Strong
```

### **Log Analysis**
```bash
# Bridge server logs
tail -f bridge_server.log

# Frontend server logs
tail -f frontend/server.log

# ESP32S3 serial output
python -c "import serial; s=serial.Serial('/dev/cu.usbmodem*', 115200); [print(s.readline().decode().strip()) for _ in range(100)]"
```

---

## 🔒 **Security Considerations**

### **Network Security**
```bash
# Local network only
Frontend: http://localhost:3000
Bridge API: http://localhost:5000
WebSocket: ws://localhost:3001

# No external network access required
# All processing done locally
```

### **Data Privacy**
```bash
# Audio storage
Files stored locally on SD card
No cloud upload or external transmission
User controls all data

# AI Processing
Whisper runs locally (no OpenAI API)
Ollama runs locally (no external LLM calls)
Complete offline operation
```

### **Device Security**
```bash
# BLE Security
No pairing required for basic operation
Custom service UUIDs
Local network only

# USB Security
Serial communication only
No file system access from host
Read-only device information
```

---

## 📈 **Performance Metrics**

### **Audio Processing**
```bash
Sample Rate: 16kHz
Bit Depth: 16-bit
Channels: Mono
Latency: <100ms (USB), <200ms (BLE)
File Size: ~32KB per minute
```

### **AI Processing**
```bash
Whisper Transcription: 2-5 seconds per minute of audio
LLM Analysis: 3-10 seconds per response
Total Processing: 5-15 seconds end-to-end
Memory Usage: <2GB RAM recommended
```

### **System Resources**
```bash
ESP32S3:
- CPU: 240MHz dual-core
- RAM: 512KB + 8MB PSRAM
- Flash: 8MB
- Power: 100-200mA @ 3.3V

Host System:
- CPU: 2+ cores recommended
- RAM: 4GB+ recommended
- Storage: 10GB+ for models
- Network: Local only
```

---

## 🚀 **Future Enhancements**

### **Planned Features**
- [ ] **Multi-language Support** - Additional Whisper models
- [ ] **Voice Activity Detection** - Automatic recording triggers
- [ ] **Speaker Identification** - Multiple speaker recognition
- [ ] **Real-time Visualization** - Audio waveform display
- [ ] **Mobile App** - Native iOS/Android applications
- [ ] **Cloud Sync** - Optional cloud backup (user controlled)

### **Hardware Upgrades**
- [ ] **Battery Management** - LiPo battery with charging circuit
- [ ] **Improved Microphone** - Higher quality audio capture
- [ ] **Larger Display** - Color OLED or e-ink display
- [ ] **Additional Sensors** - Environmental monitoring
- [ ] **Enclosure Design** - 3D printed protective case

### **Software Improvements**
- [ ] **Model Selection** - Multiple LLM model support
- [ ] **Custom Training** - Fine-tuned models for specific use cases
- [ ] **API Extensions** - RESTful API for third-party integration
- [ ] **Database Integration** - Conversation history and analytics
- [ ] **Export Features** - Multiple output formats (JSON, CSV, PDF)

---

## 📄 **License and Credits**

### **Open Source Components**
- **ESP32 Arduino Core** - Espressif Systems
- **Whisper** - OpenAI (MIT License)
- **Ollama** - Ollama Team (MIT License)
- **U8g2** - olikraus (BSD License)
- **RTClib** - Adafruit (MIT License)

### **Project License**
This project is released under the MIT License. See LICENSE file for details.

### **Contributing**
Contributions welcome! Please read CONTRIBUTING.md for guidelines.

### **Support**
- **Documentation** - This guide and inline code comments
- **Issues** - GitHub issue tracker
- **Community** - Discord/Slack channels
- **Email** - project maintainer contact

---

## 📚 **Additional Resources**

### **Documentation**
- [ESP32S3 Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s3_datasheet_en.pdf)
- [Arduino ESP32 Guide](https://docs.espressif.com/projects/arduino-esp32/en/latest/)
- [Whisper Documentation](https://github.com/openai/whisper)
- [Ollama Documentation](https://ollama.ai/docs)

### **Hardware Suppliers**
- **XIAO ESP32S3** - Seeed Studio, Adafruit, DigiKey
- **Expansion Board** - Seeed Studio official accessory
- **SD Cards** - SanDisk, Samsung (Class 10 recommended)
- **RTC Module** - Adafruit PCF8563, generic I2C modules

### **Development Tools**
- **Arduino IDE** - Official Arduino development environment
- **PlatformIO** - Advanced IDE with better library management
- **Serial Monitor** - Built-in Arduino IDE or external tools
- **Logic Analyzer** - For debugging I2C and SPI communications

---

**🎯 This guide provides complete instructions for building, installing, and operating the Brutally Honest AI system. Follow the sections in order for best results!**
