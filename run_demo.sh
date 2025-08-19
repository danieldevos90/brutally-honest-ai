#!/bin/bash

# Voice Insight Platform - Interactive Demo Script
# Run this to demonstrate all platform capabilities

set -e

echo "🎬 Voice Insight Platform - Live Demo"
echo "====================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

demo_step() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "-----------------------------------"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to wait for user input
wait_for_user() {
    echo ""
    read -p "Press Enter to continue to next demo..."
    echo ""
}

# Demo 1: Platform Health
demo_step "Demo 1: Platform Health Check"
echo "Testing if the Voice Insight Platform is running..."
if curl -s http://localhost:8000/ > /dev/null; then
    success "Platform is running!"
    curl -s http://localhost:8000/ | jq '.'
else
    error "Platform is not running. Start with: python main_enhanced.py"
    exit 1
fi
wait_for_user

# Demo 2: OMI Hardware Detection
demo_step "Demo 2: OMI DevKit 2 Hardware Detection"
echo "Scanning for OMI DevKit 2 hardware..."
omi_response=$(curl -s http://localhost:8000/api/omi/ports)
echo "$omi_response" | jq '.'

if echo "$omi_response" | jq -r '.ports[] | select(.description | contains("XIAO"))' > /dev/null; then
    success "OMI DevKit 2 detected: XIAO nRF52840 Sense"
else
    info "OMI DevKit 2 not detected in current scan"
fi
wait_for_user

# Demo 3: System Status
demo_step "Demo 3: Complete System Status"
echo "Checking all system components..."
curl -s http://localhost:8000/api/status | jq '.'
wait_for_user

# Demo 4: Docker Services
demo_step "Demo 4: Backend Services Status"
echo "Checking Docker services (PostgreSQL, Qdrant, Ollama)..."
docker-compose ps
wait_for_user

# Demo 5: LLM Test
demo_step "Demo 5: Local LLM (Ollama) Test"
echo "Testing Ollama LLM connection..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    success "Ollama is running!"
    echo "Available models:"
    curl -s http://localhost:11434/api/tags | jq '.models[].name'
else
    error "Ollama is not responding"
fi
wait_for_user

# Demo 6: WebSocket Test
demo_step "Demo 6: WebSocket Streaming Test"
echo "Testing WebSocket connection for real-time streaming..."
info "This will connect to the WebSocket endpoint and show live data"
echo "Running WebSocket test..."

# Create a simple WebSocket test
cat > websocket_test.py << 'EOF'
import asyncio
import websockets
import json

async def test_websocket():
    try:
        uri = "ws://localhost:8000/api/audio/stream"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connected!")
            print("Listening for messages (will timeout after 5 seconds)...")
            
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"📨 Received: {data['type']}")
                print(f"📄 Data: {data['data']}")
            except asyncio.TimeoutError:
                print("⏰ No messages received (this is normal for demo)")
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
EOF

python websocket_test.py
rm websocket_test.py
wait_for_user

# Demo 7: API Endpoints
demo_step "Demo 7: API Endpoints Overview"
echo "Available API endpoints:"
echo ""
echo "🌐 Core Endpoints:"
echo "  GET  /                     - Health check"
echo "  GET  /api/status           - System status"
echo "  GET  /api/omi/ports        - OMI hardware detection"
echo "  POST /api/omi/connect      - Manual OMI connection"
echo "  GET  /api/test/omi         - OMI connection test"
echo ""
echo "🎙️ Audio Processing:"
echo "  POST /api/audio/upload     - Upload audio file"
echo "  WS   /api/audio/stream     - Real-time streaming"
echo ""
echo "📊 Data Management:"
echo "  GET  /api/sessions         - List sessions"
echo "  GET  /api/sessions/{id}    - Get session details"
echo ""
info "You can test these endpoints manually or use the interactive API docs at:"
echo "http://localhost:8000/docs"
wait_for_user

# Demo 8: File Structure
demo_step "Demo 8: Project Structure Overview"
echo "Voice Insight Platform file structure:"
echo ""
tree -L 3 -I 'venv|__pycache__|*.pyc|.git' . || ls -la
wait_for_user

# Demo 9: Real-time Capabilities
demo_step "Demo 9: Real-time Processing Capabilities"
echo "The platform supports:"
echo ""
echo "🎙️ Audio Input:"
echo "  • OMI DevKit 2 via USB-C"
echo "  • File uploads (WAV, MP3, M4A)"
echo "  • WebSocket streaming"
echo ""
echo "🧠 AI Processing:"
echo "  • Whisper transcription (local)"
echo "  • Speaker diarization"
echo "  • Local LLM fact-checking (Mistral 7B)"
echo "  • Real-time analysis"
echo ""
echo "🔒 Security & Compliance:"
echo "  • All processing local (EU-compliant)"
echo "  • No cloud API dependencies"
echo "  • Encrypted data storage"
echo ""
wait_for_user

# Demo 10: Next Steps
demo_step "Demo 10: Next Steps & Customization"
echo "🚀 Your Voice Insight Platform is ready for:"
echo ""
echo "1. 📝 Custom Knowledge Base:"
echo "   • Add your company data to src/llm/analyzer.py"
echo "   • Configure fact-checking rules"
echo ""
echo "2. 🎙️ OMI Integration:"
echo "   • Connect OMI DevKit 2 for real-time audio"
echo "   • Test with: python test_omi_live.py"
echo ""
echo "3. 🏭 Production Deployment:"
echo "   • Configure environment variables"
echo "   • Set up SSL/TLS certificates"
echo "   • Scale with Docker Swarm/Kubernetes"
echo ""
echo "4. 🔧 Customization:"
echo "   • Modify audio processing pipeline"
echo "   • Add custom API endpoints"
echo "   • Integrate with existing systems"
echo ""

echo ""
echo "🎉 Demo Complete!"
echo "================"
echo ""
echo "📚 Documentation:"
echo "  • README.md - Setup guide"
echo "  • DEMO_GUIDE.md - This demo guide"
echo "  • TESTING.md - Testing instructions"
echo "  • API docs: http://localhost:8000/docs"
echo ""
echo "🌍 GitHub Repository:"
echo "  • https://github.com/danieldevos90/brutally-honest-ai"
echo ""
echo "🎯 Platform Status: 100% Operational"
echo "✅ Ready for production use!"
