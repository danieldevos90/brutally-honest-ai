# ESP32S3 OMI Firmware Installation Guide

## Quick Deployment

### 1. Connect Your Device
1. Connect your **Seeeduino XIAO ESP32S3 Sense** to your computer via USB-C
2. Ensure the **Expansion Board** is properly attached
3. Insert a **microSD card** (formatted as FAT32)

### 2. Deploy Firmware
```bash
cd omi_firmware
./deploy.sh
```

The script will automatically:
- ✅ Install required dependencies
- ✅ Compile the firmware
- ✅ Upload to your device
- ✅ Start serial monitor (optional)

### 3. Verify Installation
After deployment, you should see:
- Device creates WiFi hotspot: **"OMI-ESP32S3"**
- LED blinks slowly when ready
- Serial output shows initialization messages

## Manual Installation (Alternative)

### Prerequisites
- Arduino IDE 2.0+ or Arduino CLI
- ESP32 board package
- USB-C cable (data capable)

### Arduino IDE Method
1. Open Arduino IDE
2. Install ESP32 board package:
   - File → Preferences → Additional Board Manager URLs
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Tools → Board → Boards Manager → Search "ESP32" → Install

3. Select Board:
   - Tools → Board → ESP32 Arduino → XIAO_ESP32S3

4. Open firmware:
   - File → Open → `esp32s3_ble/esp32s3_ble.ino`

5. Upload:
   - Sketch → Upload

## Troubleshooting

### Device Not Detected
```bash
# Check connected devices
ls /dev/cu.* | grep usb
# or
arduino-cli board list
```

**Solutions:**
- Try different USB-C cable
- Press and hold BOOT button while connecting
- Install CH340/CP210x drivers if needed

### Compilation Errors
```bash
# Update ESP32 core
arduino-cli core update-index
arduino-cli core upgrade esp32:esp32
```

### Upload Failures
1. **Hold BOOT button** during upload
2. **Reset device** and try again
3. **Check port permissions** (Linux/macOS):
   ```bash
   sudo chmod 666 /dev/ttyUSB0  # or your port
   ```

### Memory Issues
If you get memory errors:
- Ensure PSRAM is enabled in board settings
- Use "Huge APP" partition scheme
- Close other applications using serial ports

## Post-Installation

### 1. Connect to Device
- WiFi SSID: **OMI-ESP32S3**
- Password: **brutalhonest**
- Web Interface: **http://192.168.4.1**

### 2. Test Recording
1. Press button on expansion board
2. Speak for a few seconds
3. Press button again to stop
4. Check web interface for recorded files

### 3. Setup Whisper (Optional)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start companion script
python esp32s3_companion.py --connection wifi
```

## Hardware Verification

### Pin Connections (Auto-configured)
- ✅ Button: Pin 1 (Expansion Board)
- ✅ Display Power: Pin 6 (Expansion Board)
- ✅ SD Card: Pins 8,9,10,21 (Expansion Board)
- ✅ Microphone: I2S Pins 41,42,2 (Built-in)

### LED Status Indicators
- **5 Quick Blinks**: Startup complete
- **Slow Blink**: Ready, waiting for connection
- **Fast Blink**: Recording in progress
- **Solid ON**: BLE connected

## Support

### Serial Monitor
```bash
# View device logs
./deploy.sh --monitor
# or
arduino-cli monitor --port /dev/cu.usbmodem* --config baudrate=115200
```

### Web API Status
```bash
curl http://192.168.4.1/status
```

### Common Issues
1. **No WiFi hotspot**: Check serial output for errors
2. **No SD card**: Verify card is inserted and formatted
3. **No audio**: Check microphone isn't blocked
4. **Button not working**: Verify expansion board connection

For more help, check the serial monitor output at 115200 baud.
