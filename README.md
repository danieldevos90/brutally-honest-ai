# Voice Insight & Feedback Platform

A secure, EU-based platform that leverages OMI DevKit 2, local LLMs, and voice recognition to provide real-time transcription, speaker identification, fact-checking, and personalized feedback.

## 🎯 Features

- **OMI DevKit 2 Integration**: Direct USB-C connection for high-quality audio capture
- **Real-time Transcription**: Using Whisper for accurate speech-to-text
- **Speaker Diarization**: Identify "who spoke when" with pyannote-audio
- **Local LLM Analysis**: Fact-checking and feedback using Mistral/Phi-3 via Ollama
- **EU-Compliant**: Runs entirely on EU infrastructure, GDPR-compliant
- **Vector Search**: Semantic search with Qdrant for company knowledge
- **WebSocket Streaming**: Real-time audio processing and feedback

## 🏗️ Architecture

```
📱 OMI DevKit 2 (USB-C)
│
├─ 🎙️ Audio Capture → Real-time streaming
│
🔐 FastAPI Backend
│
├─ Audio Processing Pipeline
│   ├─ Whisper Transcription
│   └─ Speaker Diarization (pyannote-audio)
│
├─ Local LLM Analysis
│   ├─ Ollama (Mistral 7B)
│   ├─ Fact Checking
│   └─ Feedback Generation
│
├─ Databases
│   ├─ PostgreSQL (sessions, metadata)
│   └─ Qdrant (vector search)
│
└─ WebSocket API (real-time streaming)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker & Docker Compose
- OMI DevKit 2 connected via USB-C
- 8GB+ RAM (for local LLM)

### 1. Clone and Setup

```bash
git clone <your-repo>
cd brutally-honest-ai

# Run automated setup
python setup.py --setup
```

### 2. Configure Environment

```bash
# Copy environment template
cp env.example .env

# Edit configuration (required)
nano .env
```

**Required Configuration:**
- `HUGGINGFACE_TOKEN`: Get from https://huggingface.co/settings/tokens
- Database passwords and connection details

### 3. Start Services

```bash
# Start all services (PostgreSQL, Qdrant, Ollama)
chmod +x scripts/start_services.sh
./scripts/start_services.sh
```

### 4. Test OMI Connection

```bash
# Check OMI DevKit connection
python scripts/test_omi.py --test-connection
```

### 5. Run the Platform

```bash
# Start the main application
python main.py
```

The platform will be available at: http://localhost:8000

## 🔧 API Endpoints

### Core Endpoints

- `GET /` - Health check
- `GET /api/status` - System status
- `POST /api/audio/upload` - Upload audio file for analysis
- `WebSocket /api/audio/stream` - Real-time audio streaming
- `GET /api/sessions/{id}` - Get session details
- `GET /api/sessions` - List recent sessions

### WebSocket Usage

```javascript
const ws = new WebSocket('ws://localhost:8000/api/audio/stream');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'transcription') {
        console.log('Transcript:', data.data.text);
    } else if (data.type === 'analysis') {
        console.log('Fact Check:', data.data.fact_check);
    }
};
```

## 🎙️ OMI DevKit 2 Integration

### USB-C Connection

The platform connects directly to OMI DevKit 2 via USB-C:

1. **Automatic Detection**: Scans for OMI device on startup
2. **Serial Communication**: Uses standard serial protocol
3. **Audio Streaming**: Real-time PCM audio at 16kHz
4. **Device Commands**: Send configuration and control commands

### Supported Commands

- `INFO` - Get device information
- `AUDIO_CONFIG:16000:1:16` - Configure audio (sample rate:channels:bit depth)
- `START_AUDIO` - Begin audio streaming
- `STOP_AUDIO` - Stop audio streaming

## 🧠 Local LLM Setup

### Ollama Models

The platform uses Ollama for local LLM inference:

```bash
# Pull recommended model
docker exec brutally-honest-ai-ollama-1 ollama pull mistral:7b

# Alternative models
docker exec brutally-honest-ai-ollama-1 ollama pull phi3:mini
docker exec brutally-honest-ai-ollama-1 ollama pull mixtral:8x7b
```

### Model Requirements

| Model | VRAM | RAM | Performance |
|-------|------|-----|-------------|
| Phi-3 Mini | 4GB | 8GB | Fast, CPU-friendly |
| Mistral 7B | 8GB | 16GB | Balanced |
| Mixtral 8x7B | 24GB | 32GB | Best quality |

## 📊 Database Schema

### PostgreSQL Tables

- `sessions` - Audio sessions and metadata
- `speaker_segments` - Speaker diarization results
- `analysis_results` - Fact-checking and feedback
- `users` - User management (optional)

### Qdrant Collections

- `voice_embeddings` - Semantic search for transcripts

## 🔒 Security & Compliance

- **EU-Only Processing**: All data stays within EU
- **No Cloud APIs**: Uses only local models
- **Encrypted Storage**: AES-256 encryption
- **GDPR Compliant**: Full data control and deletion
- **Audit Logging**: Complete access tracking

## 🛠️ Development

### Project Structure

```
brutally-honest-ai/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Service orchestration
├── src/
│   ├── audio/
│   │   ├── omi_connector.py    # OMI DevKit integration
│   │   └── processor.py        # Audio processing pipeline
│   ├── llm/
│   │   └── analyzer.py         # Local LLM analysis
│   ├── database/
│   │   └── manager.py          # Database management
│   └── models/
│       └── schemas.py          # API schemas
└── scripts/
    ├── start_services.sh       # Service startup
    └── test_omi.py            # OMI testing
```

### Testing

```bash
# Test individual components
python setup.py --test

# Test OMI connection
python scripts/test_omi.py --test-connection

# List available serial ports
python scripts/test_omi.py --list-ports
```

## 🐛 Troubleshooting

### OMI DevKit Not Detected

1. Check USB-C connection
2. Verify device appears in system:
   ```bash
   # Linux/macOS
   ls /dev/tty*
   
   # Check USB devices
   lsusb | grep -i pico
   ```
3. Install drivers if needed
4. Try different USB port/cable

### LLM Model Issues

```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Pull model manually
docker exec -it brutally-honest-ai-ollama-1 ollama pull mistral:7b

# Check model size
docker exec -it brutally-honest-ai-ollama-1 ollama list
```

### Database Connection Issues

```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Check Qdrant
curl http://localhost:6333/health
```

## 📈 Performance Optimization

### Hardware Recommendations

- **CPU**: 8+ cores for parallel processing
- **RAM**: 16GB+ (32GB for large models)
- **GPU**: NVIDIA GPU with 8GB+ VRAM (optional but recommended)
- **Storage**: SSD for database and model storage

### Latency Optimization

- Use smaller models (Phi-3 Mini) for faster response
- Enable GPU acceleration for Whisper
- Optimize chunk sizes for real-time processing
- Use connection pooling for databases

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 References

- [OMI DevKit Documentation](https://docs.omi.me/onboarding/omi-devkit-2)
- [OMI GitHub Issues](https://github.com/BasedHardware/omi/issues)
- [OMI Getting Started](https://docs.omi.me/doc/get_started/introduction)