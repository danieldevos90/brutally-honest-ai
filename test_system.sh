#!/bin/bash

# System Test Script for Brutal Honest AI
# ========================================

echo "🧪 BRUTAL HONEST AI SYSTEM TEST"
echo "================================"
echo ""

# Test Backend
echo "1. Testing Backend..."
if curl -s http://localhost:8000/api/status >/dev/null; then
    echo "✅ Backend: Running on http://localhost:8000"
    
    # Check ESP32S3 connection
    ESP32_STATUS=$(curl -s http://localhost:8000/api/status | grep -o '"omi_connected":[^,]*' | cut -d':' -f2)
    if [[ $ESP32_STATUS == "true" ]]; then
        echo "✅ ESP32S3: Connected via Bluetooth"
    else
        echo "❌ ESP32S3: Not connected"
    fi
else
    echo "❌ Backend: Not running"
fi

echo ""

# Test Frontend
echo "2. Testing Frontend..."
if curl -s http://localhost:3000 >/dev/null; then
    echo "✅ Frontend: Running on http://localhost:3000"
else
    echo "❌ Frontend: Not running"
fi

echo ""

# Test ESP32S3 Direct Connection
echo "3. Testing ESP32S3 Direct Connection..."
if [[ -d "venv" ]]; then
    source venv/bin/activate
    python -c "
import asyncio
import sys
sys.path.append('src')
from audio.bluetooth_connector import BluetoothOMIConnector

async def test():
    try:
        connector = BluetoothOMIConnector(connection_type='ble', device_name='OMI-ESP32S3-BrutalAI')
        devices = await connector.scan_for_devices(timeout=3)
        if devices:
            print('✅ ESP32S3: Found and advertising')
        else:
            print('❌ ESP32S3: Not found or not advertising')
    except Exception as e:
        print(f'❌ ESP32S3: Test failed - {e}')

asyncio.run(test())
" 2>/dev/null
else
    echo "❌ Virtual environment not found"
fi

echo ""

# Summary
echo "🎯 SYSTEM SUMMARY"
echo "================="
echo "• Backend API: http://localhost:8000"
echo "• Frontend UI: http://localhost:3000"
echo "• ESP32S3 Device: OMI-ESP32S3-BrutalAI"
echo ""
echo "Ready to use! Click 'Start Recording' in the frontend."
