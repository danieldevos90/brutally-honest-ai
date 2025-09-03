#!/bin/bash
"""
Start SD Card Recordings Web Interface
"""

echo "🎙️  Starting SD Card Recordings Web Interface"
echo "=============================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if required packages are installed
python3 -c "import serial, flask, flask_cors" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required packages..."
    pip3 install pyserial flask flask-cors
fi

# Start the web server
echo "🌐 Starting web server at http://localhost:5000"
echo "📱 Connect your ESP32 device via USB"
echo "🔌 Default port: /dev/cu.usbmodem2101"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 sd_recordings_server.py
