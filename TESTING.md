# Testing Guide - Voice Insight Platform

This guide covers comprehensive testing of the Voice Insight Platform with OMI DevKit 2.

## 🧪 Testing Overview

### Test Categories
1. **Environment Setup** - Verify all dependencies
2. **OMI Hardware** - Test USB-C connection and audio capture
3. **Audio Processing** - Test transcription and speaker diarization
4. **LLM Analysis** - Test fact-checking and feedback
5. **Database** - Test data storage and retrieval
6. **API Endpoints** - Test REST API and WebSocket
7. **Integration** - End-to-end testing

## 🔧 Pre-Test Setup

### 1. Install Dependencies
```bash
# Run automated setup
python setup.py --setup

# Verify installation
pip list | grep -E "(whisper|torch|fastapi|asyncpg|qdrant)"
```

### 2. Configure Environment
```bash
# Copy and edit environment file
cp env.example .env
nano .env

# Required: Set HUGGINGFACE_TOKEN for speaker diarization
# Get token from: https://huggingface.co/settings/tokens
```

### 3. Start Services
```bash
# Start all backend services
./scripts/start_services.sh

# Verify services are running
docker-compose ps
```

## 🎙️ Testing OMI DevKit 2

### Test 1: Hardware Detection
```bash
# List all serial ports
python scripts/test_omi.py --list-ports

# Expected output: Should show your OMI device
# Example: /dev/ttyACM0: OMI DevKit or similar
```

### Test 2: OMI Connection
```bash
# Test OMI connection and communication
python scripts/test_omi.py --test-connection

# Expected output:
# ✅ OMI DevKit connected successfully!
# Device info: {...}
# ✅ Audio streaming test completed
```

### Test 3: Manual OMI Testing
```python
# Create test_manual_omi.py
import asyncio
from src.audio.omi_connector import OMIDevKitConnector

async def test_omi():
    connector = OMIDevKitConnector()
    
    if await connector.initialize():
        print("✅ OMI connected")
        
        # Test device info
        info = await connector.get_device_info()
        print(f"Device info: {info}")
        
        # Test short audio capture
        print("Recording 3 seconds of audio...")
        chunk_count = 0
        async for chunk in connector.stream_audio():
            chunk_count += 1
            print(f"Chunk {chunk_count}: {len(chunk.data)} bytes")
            if chunk_count >= 10:
                connector.stop_streaming()
                break
        
        await connector.cleanup()
    else:
        print("❌ Failed to connect to OMI")

# Run: python -c "import asyncio; from test_manual_omi import test_omi; asyncio.run(test_omi())"
```

## 🎵 Testing Audio Processing

### Test 4: Whisper Transcription
```bash
# Test with sample audio file
python -c "
import asyncio
from src.audio.processor import AudioProcessor

async def test_whisper():
    processor = AudioProcessor()
    await processor.initialize()
    
    # You'll need a test audio file
    # result = await processor.process_file('test_audio.wav')
    # print(f'Transcript: {result.transcript}')
    
    await processor.cleanup()

asyncio.run(test_whisper())
"
```

### Test 5: Speaker Diarization
```bash
# Test speaker diarization (requires HUGGINGFACE_TOKEN)
python -c "
import os
print('HF Token set:', 'HUGGINGFACE_TOKEN' in os.environ)
"
```

## 🧠 Testing LLM Analysis

### Test 6: Ollama Connection
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Test model availability
docker exec brutally-honest-ai-ollama-1 ollama list

# Pull model if needed
docker exec brutally-honest-ai-ollama-1 ollama pull mistral:7b
```

### Test 7: LLM Analysis
```python
# Create test_llm.py
import asyncio
from src.llm.analyzer import LLMAnalyzer
from src.audio.processor import AudioProcessingResult, SpeakerSegment
from datetime import datetime

async def test_llm():
    analyzer = LLMAnalyzer()
    
    if await analyzer.initialize():
        print("✅ LLM analyzer initialized")
        
        # Create mock audio result
        mock_result = AudioProcessingResult(
            transcript="Our company processes all data locally in the EU for GDPR compliance.",
            speakers=[SpeakerSegment(
                speaker_id="SPEAKER_00",
                start_time=0.0,
                end_time=5.0,
                text="Our company processes all data locally in the EU for GDPR compliance.",
                confidence=0.9
            )],
            audio_duration=5.0,
            timestamp=datetime.now(),
            confidence=0.9
        )
        
        # Test analysis
        analysis = await analyzer.analyze_transcript(mock_result)
        print(f"Fact check: {analysis.fact_check.is_accurate}")
        print(f"Feedback: {analysis.feedback.summary}")
        
        await analyzer.cleanup()
    else:
        print("❌ LLM analyzer failed to initialize")

# Run: python -c "import asyncio; from test_llm import test_llm; asyncio.run(test_llm())"
```

## 💾 Testing Database

### Test 8: Database Connection
```bash
# Test PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Test Qdrant
curl http://localhost:6333/health

# Test database initialization
python setup.py --test
```

### Test 9: Database Operations
```python
# Create test_db.py
import asyncio
from src.database.manager import DatabaseManager
from src.audio.processor import AudioProcessingResult, SpeakerSegment
from src.llm.analyzer import AnalysisResult, FactCheckResult, FeedbackResult
from datetime import datetime

async def test_database():
    db = DatabaseManager()
    
    if await db.initialize():
        print("✅ Database connected")
        
        # Create mock data
        audio_result = AudioProcessingResult(
            transcript="Test transcript",
            speakers=[SpeakerSegment("SPEAKER_00", 0.0, 5.0, "Test transcript", 0.9)],
            audio_duration=5.0,
            timestamp=datetime.now(),
            confidence=0.9
        )
        
        analysis = AnalysisResult(
            fact_check=FactCheckResult(True, 0.9, [], [], []),
            feedback=FeedbackResult("Test feedback", [], 0.8, 0.8, []),
            timestamp=datetime.now(),
            confidence=0.9
        )
        
        # Store session
        session_id = await db.store_session(audio_result, analysis)
        print(f"✅ Session stored: {session_id}")
        
        # Retrieve session
        session = await db.get_session(session_id)
        print(f"✅ Session retrieved: {session['transcript'][:50]}...")
        
        await db.cleanup()
    else:
        print("❌ Database connection failed")

# Run: python -c "import asyncio; from test_db import test_database; asyncio.run(test_database())"
```

## 🌐 Testing API Endpoints

### Test 10: Start the Application
```bash
# Start the main application
python main.py

# Should see:
# INFO: Started server process
# INFO: Waiting for application startup.
# INFO: Application startup complete.
# INFO: Uvicorn running on http://0.0.0.0:8000
```

### Test 11: Health Check
```bash
# Test basic health endpoint
curl http://localhost:8000/

# Expected: {"message": "Voice Insight Platform is running", "status": "healthy"}
```

### Test 12: System Status
```bash
# Check system status
curl http://localhost:8000/api/status

# Expected JSON with component status:
# {
#   "omi_connected": true/false,
#   "audio_processor": true/false,
#   "llm_analyzer": true/false,
#   "database": true/false
# }
```

### Test 13: Audio Upload API
```bash
# Test with a sample audio file (you'll need to create one)
curl -X POST "http://localhost:8000/api/audio/upload" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_audio.wav"

# Expected: JSON response with transcript and analysis
```

### Test 14: WebSocket Connection
```javascript
// Create test_websocket.html
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Test</title>
</head>
<body>
    <div id="output"></div>
    <script>
        const ws = new WebSocket('ws://localhost:8000/api/audio/stream');
        const output = document.getElementById('output');
        
        ws.onopen = function(event) {
            output.innerHTML += '<p>✅ WebSocket connected</p>';
        };
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            output.innerHTML += `<p>Received: ${data.type} - ${JSON.stringify(data.data)}</p>`;
        };
        
        ws.onerror = function(error) {
            output.innerHTML += `<p>❌ WebSocket error: ${error}</p>`;
        };
        
        ws.onclose = function(event) {
            output.innerHTML += '<p>WebSocket closed</p>';
        };
    </script>
</body>
</html>

// Open in browser: file://path/to/test_websocket.html
```

## 🔄 Integration Testing

### Test 15: End-to-End Test
```python
# Create test_e2e.py
import asyncio
import aiohttp
import json
from pathlib import Path

async def test_end_to_end():
    """Complete end-to-end test"""
    
    # 1. Check system status
    async with aiohttp.ClientSession() as session:
        async with session.get('http://localhost:8000/api/status') as resp:
            status = await resp.json()
            print(f"System status: {status}")
            
            if not all(status.values()):
                print("❌ Some components are not ready")
                return
    
    # 2. Test WebSocket connection
    import websockets
    
    try:
        async with websockets.connect('ws://localhost:8000/api/audio/stream') as websocket:
            print("✅ WebSocket connected")
            
            # Wait for a message (timeout after 5 seconds)
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(message)
                print(f"Received message: {data['type']}")
            except asyncio.TimeoutError:
                print("⏰ No message received (expected if no OMI audio)")
                
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
    
    print("✅ End-to-end test completed")

# Run: python -c "import asyncio; from test_e2e import test_end_to_end; asyncio.run(test_end_to_end())"
```

## 🐛 Troubleshooting Tests

### Common Issues and Solutions

#### OMI Not Detected
```bash
# Check USB devices
lsusb | grep -i pico

# Check serial ports
ls /dev/tty* | grep -E "(ACM|USB)"

# Check permissions
sudo chmod 666 /dev/ttyACM0  # Adjust device name
```

#### LLM Model Issues
```bash
# Check Ollama logs
docker logs brutally-honest-ai-ollama-1

# Manually pull model
docker exec -it brutally-honest-ai-ollama-1 ollama pull mistral:7b

# Test model directly
docker exec -it brutally-honest-ai-ollama-1 ollama run mistral:7b "Hello, how are you?"
```

#### Database Connection Issues
```bash
# Check PostgreSQL logs
docker logs brutally-honest-ai-postgres-1

# Check Qdrant logs
docker logs brutally-honest-ai-qdrant-1

# Reset databases
docker-compose down -v
docker-compose up -d postgres qdrant
```

#### Audio Processing Issues
```bash
# Check if ffmpeg is installed
ffmpeg -version

# Test Whisper directly
python -c "import whisper; model = whisper.load_model('base'); print('Whisper loaded')"

# Check PyTorch
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
```

## 📊 Performance Testing

### Test 16: Audio Processing Latency
```python
# Create test_performance.py
import asyncio
import time
from src.audio.processor import AudioProcessor

async def test_latency():
    processor = AudioProcessor()
    await processor.initialize()
    
    # Test with different audio lengths
    test_files = ["short.wav", "medium.wav", "long.wav"]  # You'll need these
    
    for file in test_files:
        if Path(file).exists():
            start_time = time.time()
            result = await processor.process_file(file)
            end_time = time.time()
            
            processing_time = end_time - start_time
            audio_duration = result.audio_duration
            real_time_factor = processing_time / audio_duration
            
            print(f"{file}: {processing_time:.2f}s processing, {audio_duration:.2f}s audio")
            print(f"Real-time factor: {real_time_factor:.2f}x")
    
    await processor.cleanup()

# Run: python -c "import asyncio; from test_performance import test_latency; asyncio.run(test_latency())"
```

## ✅ Test Checklist

- [ ] Environment setup completed
- [ ] OMI DevKit 2 detected and connected
- [ ] Audio streaming from OMI working
- [ ] Whisper transcription working
- [ ] Speaker diarization working (if HF token set)
- [ ] Ollama LLM responding
- [ ] PostgreSQL connected
- [ ] Qdrant connected
- [ ] FastAPI server starting
- [ ] Health endpoints responding
- [ ] WebSocket connection working
- [ ] Audio upload API working
- [ ] Database storage/retrieval working
- [ ] End-to-end pipeline working

## 🚀 Automated Test Suite

Run all tests with:
```bash
# Create and run comprehensive test
python setup.py --test
python scripts/test_omi.py --test-connection
curl http://localhost:8000/api/status
```

This testing guide ensures your Voice Insight Platform is working correctly with your OMI DevKit 2!
