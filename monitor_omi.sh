#!/bin/bash

echo "🔍 Monitoring for OMI DevKit 2 connection..."
echo "Disconnect and reconnect your OMI DevKit 2 now"
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    # Check for new serial ports
    NEW_PORTS=$(ls /dev/cu.* 2>/dev/null | grep -v "debug\|Bluetooth")
    
    if [ ! -z "$NEW_PORTS" ]; then
        echo "🎉 New serial device detected:"
        echo "$NEW_PORTS"
        
        # Test with our API
        echo "Testing with Voice Insight Platform..."
        curl -s http://localhost:8000/api/omi/ports | jq '.omi_detected'
        break
    fi
    
    # Check USB devices
    USB_CHECK=$(system_profiler SPUSBDataType | grep -i "zephyr\|seeed\|xiao")
    if [ ! -z "$USB_CHECK" ]; then
        echo "📱 OMI still in DFU mode - try disconnecting and reconnecting without buttons"
    fi
    
    sleep 2
done
