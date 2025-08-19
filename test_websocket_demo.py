#!/usr/bin/env python3
"""
Test the WebSocket demo functionality
"""

import asyncio
import websockets
import json

async def test_websocket_demo():
    """Test the WebSocket demo with proper message handling"""
    
    print("🧪 Testing WebSocket Demo...")
    print("=" * 40)
    
    try:
        # Connect to WebSocket
        uri = "ws://localhost:8000/api/audio/stream"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to WebSocket!")
            
            # Listen for messages
            message_count = 0
            max_messages = 10  # Limit messages for demo
            
            async for message in websocket:
                message_count += 1
                
                try:
                    data = json.loads(message)
                    print(f"\n📨 Message {message_count}: {data['type']}")
                    
                    if data['type'] == 'connection':
                        print(f"   🔗 {data['data']}")
                    
                    elif data['type'] == 'error':
                        print(f"   ❌ {data['data']['message']}")
                    
                    elif data['type'] == 'audio_start':
                        print(f"   🎤 {data['data']['message']}")
                    
                    elif data['type'] == 'transcript':
                        print(f"   🤖 Whisper: \"{data['data']}\"")
                    
                    elif data['type'] == 'analysis':
                        brutal_response = data['data'].get('brutal_response', 'No brutal response')
                        confidence = data['data'].get('confidence', 0)
                        print(f"   🧠 Llama: {brutal_response}")
                        print(f"   📊 Confidence: {confidence * 100:.1f}%")
                        
                        # This is the final message, so we can break
                        print("\n🎉 Demo completed successfully!")
                        break
                    
                    else:
                        print(f"   📄 Data: {data['data']}")
                
                except json.JSONDecodeError:
                    print(f"   ⚠️  Non-JSON message: {message[:100]}...")
                
                if message_count >= max_messages:
                    print(f"\n⏰ Reached maximum messages ({max_messages})")
                    break
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    print("\n✅ WebSocket demo test completed!")
    return True

if __name__ == "__main__":
    print("🎙️ Voice Insight Platform - WebSocket Demo Test")
    print("=" * 50)
    
    # Wait a moment for backend to start
    print("⏳ Waiting for backend to start...")
    asyncio.get_event_loop().run_until_complete(asyncio.sleep(3))
    
    # Run the test
    success = asyncio.get_event_loop().run_until_complete(test_websocket_demo())
    
    if success:
        print("\n🎯 Your live demo is ready!")
        print("   Frontend: http://localhost:3000")
        print("   Click '🎬 Start Live Demo' to see the magic!")
    else:
        print("\n❌ Demo test failed. Check backend logs.")
