# 🎙️ SD Card Recordings Web Interface

A comprehensive web interface to view, download, and listen to recordings stored on your ESP32 device's SD card.

## ✨ Features

- **📋 View Recordings**: List all WAV files on the SD card with details
- **📥 Download Files**: Download recordings from SD card to your computer
- **🎵 Audio Playback**: Listen to recordings directly in the browser
- **📊 File Management**: See file sizes, timestamps, and download status
- **🔄 Real-time Updates**: Refresh recordings list from device
- **📱 Responsive Design**: Works on desktop and mobile devices

## 🚀 Quick Start

### Method 1: Use the Enhanced List Script
```bash
# List recordings and see options
python3 list_recordings.py

# Start web interface
python3 list_recordings.py --web
```

### Method 2: Direct Web Server
```bash
# Install dependencies
pip3 install -r requirements_web.txt

# Start web server
python3 sd_recordings_server.py

# Or use the startup script
./start_recordings_web.sh
```

### Method 3: One-Click Startup
```bash
# Make executable and run
chmod +x start_recordings_web.sh
./start_recordings_web.sh
```

## 🌐 Web Interface

Once started, open your browser to: **http://localhost:5000**

### Interface Features

#### 📊 Dashboard
- **Connection Status**: Shows if ESP32 device is connected
- **Recordings Count**: Total number of files on SD card
- **Storage Info**: Total size of all recordings

#### 📁 Recordings List
Each recording shows:
- **Filename**: With timestamp information
- **File Size**: In MB and bytes
- **Date/Time**: When the recording was made
- **Status**: Downloaded locally or on device only
- **Actions**: Play, Download, or View Info buttons

#### 🎵 Audio Player
- **Built-in Player**: HTML5 audio player for downloaded files
- **Playback Controls**: Play, pause, seek, volume
- **File Information**: Shows recording details while playing

## 📱 Device Connection

### USB Connection (Recommended)
1. Connect ESP32 via USB cable
2. Device should appear on `/dev/cu.usbmodem2101` (macOS) or `/dev/ttyUSB0` (Linux)
3. Web interface will automatically detect connection

### WiFi AP Mode (Alternative)
If USB isn't working, use the device's WiFi hotspot:
1. Device creates WiFi network: `BrutallyHonestAI`
2. Password: `brutal123`
3. Connect and go to: `http://192.168.4.1`

## 🛠️ Command Line Options

### Enhanced List Script
```bash
# Basic listing
python3 list_recordings.py

# Specify custom port
python3 list_recordings.py --port /dev/ttyUSB0

# Download specific file
python3 list_recordings.py --download rec_20241201_143022.wav

# Download all recordings
python3 list_recordings.py --download-all

# Start web interface
python3 list_recordings.py --web

# Custom port and baud rate
python3 list_recordings.py --port /dev/ttyUSB0 --baudrate 115200 --web
```

### Direct Web Server
```bash
# Basic startup
python3 sd_recordings_server.py

# The server runs on http://localhost:5000
```

## 📂 File Organization

### Downloads Directory
```
downloads/
├── sd_recordings/          # Downloaded WAV files
│   ├── rec_20241201_143022.wav
│   ├── rec_20241201_144530.wav
│   └── ...
└── recordings/             # Alternative download location
    └── ...
```

### Recording Filename Format
- **Pattern**: `rec_YYYYMMDD_HHMMSS.wav`
- **Example**: `rec_20241201_143022.wav` = December 1, 2024 at 2:30:22 PM

## 🔧 Technical Details

### Supported Audio Format
- **Format**: WAV (Waveform Audio File Format)
- **Sample Rate**: 16 kHz (typically)
- **Bit Depth**: 16-bit
- **Channels**: Mono
- **Codec**: PCM (uncompressed)

### Serial Communication
- **Baud Rate**: 115200
- **Commands**:
  - `L` - List files on SD card
  - `D<filename>` - Download specific file (if implemented in firmware)

### Web Server
- **Framework**: Flask (Python)
- **Port**: 5000
- **CORS**: Enabled for cross-origin requests
- **File Serving**: Direct WAV file streaming

## 🐛 Troubleshooting

### Connection Issues
```bash
# Check if device is connected
ls /dev/cu.usbmodem* # macOS
ls /dev/ttyUSB* # Linux

# Check permissions (Linux)
sudo chmod 666 /dev/ttyUSB0

# Try different baud rates
python3 list_recordings.py --baudrate 9600
```

### Web Interface Issues
```bash
# Check if port 5000 is available
lsof -i :5000

# Install missing dependencies
pip3 install pyserial flask flask-cors

# Check Python version (requires 3.6+)
python3 --version
```

### Audio Playback Issues
- **Browser Compatibility**: Use Chrome, Firefox, or Safari
- **File Format**: Ensure files are valid WAV format
- **Download First**: Files must be downloaded before playback
- **File Size**: Large files may take time to load

### Device Not Responding
1. **Reconnect USB**: Unplug and reconnect device
2. **Reset Device**: Press reset button on ESP32
3. **Check Firmware**: Ensure latest firmware is installed
4. **Try WiFi Mode**: Use AP mode as alternative

## 📋 Requirements

### Python Dependencies
```
pyserial>=3.5      # Serial communication
flask>=2.0.0       # Web framework
flask-cors>=3.0.0  # Cross-origin requests
```

### System Requirements
- **Python**: 3.6 or higher
- **Operating System**: macOS, Linux, or Windows
- **USB Port**: For device connection
- **Web Browser**: Modern browser with HTML5 audio support

## 🔄 Integration with Main System

This web interface integrates with the main Brutally Honest AI system:

### Existing Integration Points
- **Frontend Server**: Can be integrated with existing `frontend/server.js`
- **Main Backend**: Compatible with `main.py` and `main_enhanced.py`
- **Local Hub**: Works alongside `local_hub/hub_server.py`

### API Endpoints
```
GET  /api/recordings          # List all recordings
POST /api/download/<filename> # Download specific recording
GET  /api/recording/<filename> # Serve downloaded recording
GET  /api/refresh             # Force refresh recordings list
```

## 🚀 Future Enhancements

### Planned Features
- **🔄 Auto-sync**: Automatic download of new recordings
- **🗑️ Delete Files**: Remove recordings from SD card
- **📊 Analytics**: Recording statistics and insights
- **🔍 Search**: Find recordings by date/time
- **📤 Export**: Batch export in different formats
- **🎛️ Settings**: Configure device and download preferences

### Firmware Enhancements Needed
- **Direct Download**: Serial command for file transfer
- **File Management**: Delete, rename operations
- **Metadata**: Recording duration, quality info
- **Streaming**: Real-time audio streaming

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify device connection and firmware
3. Check Python dependencies and versions
4. Review system logs for error messages

## 🎯 Usage Examples

### Basic Workflow
1. **Connect Device**: Plug in ESP32 via USB
2. **Start Web Server**: Run `./start_recordings_web.sh`
3. **Open Browser**: Go to `http://localhost:5000`
4. **View Recordings**: See all files on SD card
5. **Download Files**: Click download buttons for files you want
6. **Play Audio**: Click play buttons for downloaded files

### Advanced Usage
```bash
# Check recordings from command line
python3 list_recordings.py

# Download all recordings in batch
python3 list_recordings.py --download-all

# Start web server with custom settings
python3 sd_recordings_server.py
```

This web interface provides a complete solution for managing your ESP32 SD card recordings with an intuitive, modern web interface! 🎉
