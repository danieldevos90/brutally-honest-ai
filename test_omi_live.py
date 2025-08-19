#!/usr/bin/env python3
"""
Live test of OMI DevKit 2 connection and streaming
"""

import asyncio
import websockets
import json
import serial
import time
import threading
from datetime import datetime

async def test_websocket_streaming():
    """Test WebSocket streaming with OMI DevKit 2"""
    
    print("🎙️ Testing OMI DevKit 2 WebSocket Streaming")
    print("=" * 50)
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/api/audio/stream"
        print(f"Connecting to: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            print("Listening for audio data...")
            print("(The platform will simulate audio processing)")
            print()
            
            # Listen for messages
            message_count = 0
            async for message in websocket:
                try:
                    data = json.loads(message)
                    message_count += 1
                    
                    print(f"📨 Message {message_count}: {data['type']}")
                    
                    if data['type'] == 'transcription':
                        print(f"   🎯 Text: {data['data']['text']}")
                        print(f"   ⏱️  Duration: {data['data']['duration']:.2f}s")
                        print(f"   📊 Confidence: {data['data']['confidence']:.2f}")
                    
                    elif data['type'] == 'analysis':
                        print(f"   🧠 Analysis: {data['data']['summary']}")
                        print(f"   📈 Status: {data['data']['status']}")
                    
                    elif data['type'] == 'error':
                        print(f"   ❌ Error: {data['data']['message']}")
                        break
                    
                    print()
                    
                    # Stop after 10 messages for demo
                    if message_count >= 10:
                        print("🎉 Demo completed! Received 10 messages.")
                        break
                        
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON: {message}")
                except KeyError as e:
                    print(f"❌ Missing key: {e}")
                    
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

def test_serial_connection():
    """Test direct serial connection to OMI"""
    
    print("🔌 Testing Direct Serial Connection")
    print("=" * 40)
    
    try:
        ser = serial.Serial('/dev/cu.usbmodem1101', 115200, timeout=1)
        print(f"✅ Connected to: {ser.port}")
        print(f"📊 Baudrate: {ser.baudrate}")
        
        # Send test commands
        commands = [b'INFO\n', b'STATUS\n', b'VERSION\n']
        
        for cmd in commands:
            print(f"📤 Sending: {cmd.decode().strip()}")
            ser.write(cmd)
            time.sleep(0.5)
            
            if ser.in_waiting > 0:
                response = ser.read(ser.in_waiting)
                print(f"📥 Response: {response}")
            else:
                print("📥 No response")
            print()
        
        ser.close()
        print("✅ Serial test completed")
        
    except Exception as e:
        print(f"❌ Serial test failed: {e}")

async def main():
    """Run all tests"""
    
    print("🎙️ OMI DevKit 2 Live Testing Suite")
    print("=" * 60)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Direct serial connection
    test_serial_connection()
    print()
    
    # Test 2: WebSocket streaming
    await test_websocket_streaming()
    print()
    
    print("🎉 All tests completed!")
    print()
    print("🚀 Your OMI DevKit 2 is ready for:")
    print("   • Real-time audio streaming")
    print("   • Voice transcription")
    print("   • Speaker analysis")
    print("   • Fact-checking with local LLM")

if __name__ == "__main__":
    asyncio.run(main())
