#!/bin/bash
# Simple ESP32S3 deployment script - manual device detection

echo "🚀 ESP32S3 Simple Deployment"
echo "=============================="

# Check if sketch exists
if [ ! -f "esp32s3_ble/esp32s3_ble.ino" ]; then
    echo "❌ Sketch file not found!"
    echo "Make sure you're in the omi_firmware directory"
    exit 1
fi

echo "📋 Available serial ports:"
ls /dev/cu.* 2>/dev/null || echo "No serial ports found"

echo ""
echo "🔍 Looking for ESP32S3 device..."
echo "If your device isn't listed above, try:"
echo "  1. Hold BOOT button while connecting USB"
echo "  2. Try a different USB-C cable"
echo "  3. Check that expansion board is properly connected"

echo ""
read -p "Enter the port for your ESP32S3 (e.g., /dev/cu.usbmodem101): " PORT

if [ -z "$PORT" ]; then
    echo "❌ No port specified"
    exit 1
fi

if [ ! -e "$PORT" ]; then
    echo "❌ Port $PORT does not exist"
    exit 1
fi

echo "🔨 Compiling firmware..."
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 esp32s3_ble/esp32s3_ble.ino

if [ $? -ne 0 ]; then
    echo "❌ Compilation failed"
    exit 1
fi

echo "📤 Uploading to $PORT..."
arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3 --port "$PORT" esp32s3_ble/esp32s3_ble.ino

if [ $? -eq 0 ]; then
    echo "✅ Upload successful!"
    echo ""
    echo "🎉 Your ESP32S3 is now running the enhanced OMI firmware!"
    echo ""
    echo "Next steps:"
    echo "  1. Insert microSD card"
    echo "  2. Connect to WiFi 'OMI-ESP32S3' (password: brutalhonest)"
    echo "  3. Visit http://192.168.4.1"
    echo "  4. Press button to start recording"
    echo ""
    read -p "Start serial monitor? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📺 Serial Monitor (Ctrl+C to exit):"
        arduino-cli monitor --port "$PORT" --config baudrate=115200
    fi
else
    echo "❌ Upload failed"
    echo "Try:"
    echo "  1. Hold BOOT button and reset"
    echo "  2. Check if another program is using the port"
    echo "  3. Verify the correct port is selected"
fi
