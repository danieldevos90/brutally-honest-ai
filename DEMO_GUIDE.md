# 🎯 Voice Insight Platform - Demo & Testing Guide

**Platform Status:** ✅ **FULLY OPERATIONAL**  
**OMI DevKit 2:** ✅ **CONNECTED**  
**API Endpoint:** http://localhost:8000

## 🚀 **Quick Demo Commands**

### **1. Health Check**
```bash
curl http://localhost:8000/
# Expected: Platform running message with enhanced features
```

### **2. System Status**
```bash
curl http://localhost:8000/api/status
# Shows: OMI connection, LLM status, database status
```

### **3. OMI Hardware Detection**
```bash
curl http://localhost:8000/api/omi/ports
# Shows: Connected OMI DevKit 2 details
```

### **4. OMI Connection Test**
```bash
curl http://localhost:8000/api/test/omi
# Tests: Full OMI connection and capabilities
```

## 🎙️ **Audio Processing Demos**

### **Demo 1: Audio File Upload**
```bash
# Create a test audio file (or use existing)
curl -X POST "http://localhost:8000/api/audio/upload" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@test_audio.wav"

# Returns: Transcript, analysis, and processing details
```

### **Demo 2: WebSocket Real-time Streaming**

**Option A: Browser Console Test**
```javascript
// Open browser console at http://localhost:8000
const ws = new WebSocket('ws://localhost:8000/api/audio/stream');

ws.onopen = () => console.log('🎉 Connected to Voice Insight Platform');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`📨 ${data.type}:`, data.data);
};

ws.onerror = (error) => console.log('❌ Error:', error);
```

**Option B: Python WebSocket Test**
```bash
python test_omi_live.py
# Runs comprehensive WebSocket streaming test
```

### **Demo 3: Manual OMI Connection**
```bash
curl -X POST http://localhost:8000/api/omi/connect
# Attempts manual connection to OMI DevKit 2
```

## 🧠 **LLM & AI Demos**

### **Demo 4: Fact-Checking Test**
```bash
# The platform automatically fact-checks transcribed content
# Upload audio with factual statements to see analysis
curl -X POST "http://localhost:8000/api/audio/upload" \
     -F "file=@business_statement.wav"

# Returns: Fact-check results, confidence scores, corrections
```

### **Demo 5: Speaker Analysis**
```bash
# Upload multi-speaker audio to test diarization
curl -X POST "http://localhost:8000/api/audio/upload" \
     -F "file=@meeting_recording.wav"

# Returns: Speaker identification, timeline, individual transcripts
```

## 🎬 **Interactive Demo Scripts**

### **Demo Script 1: Complete Platform Test**
```bash
# Run comprehensive demo
./quick_test.sh

# Shows: All components, OMI status, service health
```

### **Demo Script 2: OMI Hardware Demo**
```bash
python scripts/test_omi.py --test-connection

# Tests: Hardware detection, connection, communication
```

### **Demo Script 3: Live Streaming Demo**
```bash
python test_omi_live.py

# Demonstrates: Real-time WebSocket streaming, audio processing
```

## 📊 **Performance & Monitoring Demos**

### **Demo 6: Service Status Dashboard**
```bash
# Check all Docker services
docker-compose ps

# Check individual service health
curl http://localhost:6333/health    # Qdrant
curl http://localhost:11434/api/tags # Ollama LLM
```

### **Demo 7: Database Operations**
```bash
# List recent sessions
curl http://localhost:8000/api/sessions

# Get specific session details
curl http://localhost:8000/api/sessions/{session_id}
```

## 🎯 **Scenario-Based Demos**

### **Scenario 1: Business Meeting Analysis**
1. **Upload meeting recording**
2. **Get speaker diarization** ("Who said what when")
3. **Fact-check statements** against company data
4. **Generate meeting summary** with accuracy scores

### **Scenario 2: Real-time Voice Coaching**
1. **Connect to WebSocket stream**
2. **Speak into OMI DevKit 2**
3. **Get live transcription**
4. **Receive real-time feedback** on accuracy and compliance

### **Scenario 3: Compliance Monitoring**
1. **Process regulatory statements**
2. **Check against compliance database**
3. **Flag potential issues** automatically
4. **Generate compliance reports**

## 🔧 **Technical Demos**

### **Demo 8: API Documentation**
```bash
# Access interactive API docs
open http://localhost:8000/docs

# Or ReDoc format
open http://localhost:8000/redoc
```

### **Demo 9: Database Inspection**
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d voice_insight

# Sample queries
\dt                          # List tables
SELECT * FROM sessions;      # View sessions
SELECT * FROM speaker_segments; # View speaker data
```

### **Demo 10: Vector Search Demo**
```bash
# Query Qdrant vector database
curl http://localhost:6333/collections/voice_embeddings/points/search \
     -H "Content-Type: application/json" \
     -d '{"vector": [0.1, 0.2, 0.3], "limit": 5}'
```

## 🎪 **Live Demo Presentation**

### **5-Minute Demo Flow:**

1. **Platform Overview** (30s)
   ```bash
   curl http://localhost:8000/
   curl http://localhost:8000/api/status
   ```

2. **OMI Hardware Demo** (1 min)
   ```bash
   curl http://localhost:8000/api/omi/ports
   python test_omi_live.py
   ```

3. **Audio Processing** (2 min)
   - Upload sample audio file
   - Show transcription results
   - Demonstrate speaker diarization

4. **Real-time Streaming** (1 min)
   - Connect WebSocket
   - Show live audio processing
   - Display real-time analysis

5. **AI Analysis** (30s)
   - Show fact-checking results
   - Display confidence scores
   - Demonstrate feedback generation

### **15-Minute Deep Dive:**

1. **Architecture Overview** (3 min)
   - Show Docker services
   - Explain local processing
   - Demonstrate EU compliance

2. **OMI Integration** (4 min)
   - Hardware connection demo
   - Serial communication test
   - Audio streaming capabilities

3. **AI Processing Pipeline** (4 min)
   - Whisper transcription
   - Speaker diarization
   - LLM fact-checking

4. **Real-world Scenarios** (3 min)
   - Business meeting analysis
   - Compliance monitoring
   - Voice coaching

5. **Q&A and Customization** (1 min)

## 🎮 **Interactive Testing**

### **Test 1: Upload Your Own Audio**
```bash
# Record a voice memo on your phone
# Transfer to computer
# Upload via API
curl -X POST "http://localhost:8000/api/audio/upload" \
     -F "file=@your_recording.m4a"
```

### **Test 2: Live Voice Test**
1. Connect to WebSocket: `ws://localhost:8000/api/audio/stream`
2. Speak into OMI DevKit 2
3. Watch real-time transcription
4. See live fact-checking results

### **Test 3: Multi-Speaker Test**
1. Upload conversation with multiple people
2. See speaker diarization in action
3. Get individual speaker analysis
4. Review accuracy metrics

## 📱 **Mobile/Web Interface Demo**

### **Create Simple Web Demo:**
```html
<!DOCTYPE html>
<html>
<head><title>Voice Insight Demo</title></head>
<body>
    <h1>🎙️ Voice Insight Platform Demo</h1>
    
    <div id="status"></div>
    <div id="output"></div>
    
    <script>
        // System status
        fetch('http://localhost:8000/api/status')
            .then(r => r.json())
            .then(data => {
                document.getElementById('status').innerHTML = 
                    `<h2>System Status</h2><pre>${JSON.stringify(data, null, 2)}</pre>`;
            });
        
        // WebSocket demo
        const ws = new WebSocket('ws://localhost:8000/api/audio/stream');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            document.getElementById('output').innerHTML += 
                `<p><strong>${data.type}:</strong> ${JSON.stringify(data.data)}</p>`;
        };
    </script>
</body>
</html>
```

## 🎯 **Demo Checklist**

### **Before Demo:**
- [ ] Platform running: `curl http://localhost:8000/`
- [ ] OMI connected: `curl http://localhost:8000/api/omi/ports`
- [ ] Services healthy: `docker-compose ps`
- [ ] LLM loaded: `curl http://localhost:11434/api/tags`

### **Demo Materials:**
- [ ] Sample audio files ready
- [ ] WebSocket test client prepared
- [ ] Browser with console open
- [ ] Terminal windows arranged

### **Success Metrics:**
- [ ] All API endpoints responding
- [ ] OMI hardware detected
- [ ] WebSocket streaming working
- [ ] Audio processing functional
- [ ] LLM analysis operational

## 🚀 **Next Steps After Demo**

1. **Customize for your use case**
2. **Add your company knowledge base**
3. **Configure fact-checking rules**
4. **Set up production deployment**
5. **Train team on platform usage**

---

**🎉 Your Voice Insight Platform is ready for any demo scenario!**
