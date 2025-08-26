# ESP32S3 Enhanced OMI Firmware

Enhanced firmware for Seeeduino XIAO ESP32S3 Sense with Expansion Board featuring button-controlled recording, display control, SD storage, WiFi sync, and Whisper transcription.

## Features

- ✅ **Button-Controlled Recording**: Press button to start/stop recording
- ✅ **Display Control**: Display turns on when button is pressed
- ✅ **MicroSD Storage**: Audio files saved as WAV format
- ✅ **WiFi Access Point**: Device creates WiFi hotspot for file access
- ✅ **BLE Connectivity**: Real-time audio streaming via Bluetooth
- ✅ **Voice Activity Detection**: Automatic detection of speech in recordings
- ✅ **Whisper Transcription**: AI-powered speech-to-text via companion script
- ✅ **File Sync**: Download recordings via WiFi or BLE

## Hardware Requirements

### Required Components
1. **Seeed Studio XIAO ESP32S3 Sense** - Main microcontroller with built-in microphone
2. **Seeeduino XIAO Expansion Board** - Provides button, display connector, and SD card slot

### Pin Configuration
```
ESP32S3 Sense + Expansion Board:
- Button: Pin 1 (with internal pullup)
- Display Power: Pin 6 (controls display on/off)
- SD Card CS: Pin 21
- SD Card MOSI: Pin 10
- SD Card MISO: Pin 9
- SD Card SCK: Pin 8
- Built-in Microphone: I2S (Pins 41, 42, 2)
- Built-in LED: LED_BUILTIN
```

## Installation

### 1. Arduino IDE Setup
1. Install ESP32 board package in Arduino IDE
2. Select board: "XIAO_ESP32S3"
3. Install required libraries:
   - ESP32 BLE Arduino
   - SD library (built-in)
   - WiFi library (built-in)
   - WebServer library (built-in)

### 2. Upload Firmware
1. Connect ESP32S3 to computer via USB-C
2. Open `esp32s3_ble.ino` in Arduino IDE
3. Select correct port and board
4. Upload firmware

### 3. Python Companion Setup (Optional)
For Whisper transcription support:

```bash
cd omi_firmware
pip install -r requirements.txt
python esp32s3_companion.py --connection wifi
```

## Usage

### Basic Operation
1. **Power On**: Device starts and creates WiFi hotspot "OMI-ESP32S3"
2. **Button Press**: Press button to turn on display and start recording
3. **Recording**: LED blinks fast during recording (max 30 seconds)
4. **Stop Recording**: Press button again or wait for timeout
5. **File Storage**: Audio saved to SD card as WAV file

### WiFi Access
- **SSID**: OMI-ESP32S3
- **Password**: brutalhonest
- **IP Address**: 192.168.4.1

#### Web Interface Endpoints
- `http://192.168.4.1/` - Main page
- `http://192.168.4.1/status` - Device status JSON
- `http://192.168.4.1/list` - List audio files
- `http://192.168.4.1/transcriptions` - List transcription files
- `http://192.168.4.1/download?file=filename.wav` - Download audio file

### BLE Connection
- **Device Name**: OMI-ESP32S3-BrutalAI
- **Service UUID**: 12345678-1234-1234-1234-123456789abc

#### BLE Characteristics
- **Audio Stream**: 12345678-1234-1234-1234-123456789abd
- **Status**: 12345678-1234-1234-1234-123456789abe
- **File Transfer**: 12345678-1234-1234-1234-123456789abf
- **Transcription**: 12345678-1234-1234-1234-123456789ac0

## File Formats

### Audio Files
- **Format**: WAV (16-bit PCM)
- **Sample Rate**: 16 kHz
- **Channels**: Mono
- **Location**: `/recordings/rec_N.wav`

### Transcription Files
- **Format**: Plain text
- **Content**: Timestamp, recording filename, transcription
- **Location**: `/recordings/rec_N.txt`

## Whisper Transcription

### Companion Script Usage
```bash
# WiFi connection (recommended)
python esp32s3_companion.py --connection wifi --ip 192.168.4.1

# BLE connection
python esp32s3_companion.py --connection ble --device "OMI-ESP32S3-BrutalAI"

# Custom Whisper model
python esp32s3_companion.py --model large --connection wifi
```

### Supported Whisper Models
- `tiny` - Fastest, least accurate
- `base` - Good balance (default)
- `small` - Better accuracy
- `medium` - High accuracy
- `large` - Best accuracy, slowest

## LED Status Indicators

- **Solid ON**: BLE connected
- **Fast Blink (100ms)**: Recording in progress
- **Slow Blink (1000ms)**: Not connected, ready for connection
- **5 Quick Blinks**: Device ready after startup

## Voice Activity Detection

The firmware includes simple energy-based voice activity detection:
- **Threshold**: Configurable via `voiceThreshold` variable
- **Detection**: Triggers transcription request when voice is detected
- **Status**: Available via BLE status characteristic and web API

## Troubleshooting

### Common Issues

1. **SD Card Not Detected**
   - Check SD card is properly inserted
   - Verify SD card is formatted (FAT32 recommended)
   - Check pin connections

2. **WiFi Connection Issues**
   - Device creates its own hotspot, don't connect to existing WiFi
   - Default IP: 192.168.4.1
   - Password: brutalhonest

3. **BLE Connection Problems**
   - Ensure device is in range
   - Check device name matches "OMI-ESP32S3-BrutalAI"
   - Restart device if BLE becomes unresponsive

4. **Recording Issues**
   - Check microphone is not blocked
   - Verify SD card has sufficient space
   - Button debouncing: wait 200ms between presses

5. **Transcription Not Working**
   - Ensure companion script is running
   - Check WiFi/BLE connection to device
   - Verify Whisper model is properly installed

### Debug Information
- **Serial Monitor**: 115200 baud rate
- **Status API**: `http://192.168.4.1/status`
- **Memory Usage**: Available in status JSON

## Technical Specifications

- **Audio Buffer**: 1024 samples per chunk
- **Recording Duration**: 30 seconds maximum
- **Sample Rate**: 16 kHz
- **Bit Depth**: 16-bit
- **Memory**: Uses PSRAM when available
- **File System**: SD card (FAT32)
- **WiFi**: 802.11 b/g/n Access Point mode
- **BLE**: Bluetooth 5.0 LE

## Development

### Customization
Key parameters can be modified in the firmware:
- `RECORDING_DURATION_MS`: Maximum recording length
- `SAMPLE_RATE`: Audio sample rate
- `voiceThreshold`: Voice activity detection sensitivity
- `ssid`/`password`: WiFi credentials

### Adding Features
The modular design allows easy extension:
- Additional BLE characteristics
- New web API endpoints
- Enhanced audio processing
- Custom file formats

## License

This project is part of the Brutally Honest AI system. See main project license for details.
