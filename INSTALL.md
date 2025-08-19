# Voice Insight Platform - Installation Guide

## Quick Installation

This project includes a comprehensive installation script that sets up everything automatically on any computer.

### One-Command Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd brutally-honest-ai

# Run the installation script
./install.sh
```

That's it! The script will:

✅ **Detect your operating system** (Linux, macOS, Windows)  
✅ **Install all system dependencies** (Python, Node.js, Docker, ffmpeg, etc.)  
✅ **Set up Python virtual environment** with all required packages  
✅ **Install Node.js dependencies** for the frontend  
✅ **Configure Docker services** (PostgreSQL, Qdrant, Ollama)  
✅ **Download the LLM model** (Mistral 7B)  
✅ **Set up USB permissions** for OMI DevKit (Linux)  
✅ **Initialize the database**  
✅ **Create startup scripts**  
✅ **Test the installation**  

## Supported Operating Systems

- **Linux**: Ubuntu/Debian, CentOS/RHEL, Arch Linux
- **macOS**: Intel and Apple Silicon
- **Windows**: WSL2 recommended

## System Requirements

- **RAM**: 8GB minimum, 16GB+ recommended
- **Storage**: 10GB free space
- **CPU**: 4+ cores recommended
- **USB**: USB-C port for OMI DevKit 2

## After Installation

1. **Configure Environment**:
   ```bash
   nano .env
   ```
   - Add your Hugging Face token
   - Update any other settings

2. **Connect OMI DevKit 2** via USB-C

3. **Start the Platform**:
   ```bash
   ./start.sh
   ```

4. **Access the Platform**: http://localhost:8000

5. **Stop the Platform**:
   ```bash
   ./stop.sh
   ```

## Manual Installation

If you prefer manual installation or the script doesn't work for your system, follow the detailed instructions in [README.md](README.md).

## Troubleshooting

### Common Issues

**Docker Permission Denied (Linux)**:
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

**OMI DevKit Not Detected**:
```bash
# Check USB connection
python setup.py --check-omi

# List available ports
ls /dev/tty*
```

**LLM Model Issues**:
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Manually pull model
docker-compose exec ollama ollama pull mistral:7b
```

**Database Connection Issues**:
```bash
# Check PostgreSQL
docker-compose exec postgres pg_isready -U postgres

# Check Qdrant
curl http://localhost:6333/health
```

### Getting Help

1. Check the [README.md](README.md) for detailed documentation
2. Run the test suite: `python setup.py --test`
3. Check Docker logs: `docker-compose logs`
4. Verify services: `docker-compose ps`

## What the Script Installs

### System Dependencies
- Python 3.8+ with pip and venv
- Node.js and npm
- Docker and Docker Compose
- ffmpeg (audio processing)
- portaudio (audio I/O)
- libsndfile (audio file handling)
- libusb (USB device access)
- Build tools (gcc, make, etc.)

### Python Packages
- FastAPI and Uvicorn (web framework)
- OpenAI Whisper (speech recognition)
- PyAnnote Audio (speaker diarization)
- Ollama (local LLM integration)
- PostgreSQL and Qdrant clients
- Audio processing libraries
- USB/Serial communication tools

### Docker Services
- **PostgreSQL**: Database for sessions and metadata
- **Qdrant**: Vector database for semantic search
- **Ollama**: Local LLM inference server

### Models Downloaded
- **Whisper Base**: Speech-to-text model
- **Mistral 7B**: Local language model
- **PyAnnote Models**: Speaker diarization models

## Security Features

- Runs entirely locally (no cloud APIs)
- EU-compliant data processing
- Encrypted database storage
- Secure USB device access
- Generated random secrets
- User permission management

---

**Total Installation Time**: 10-30 minutes (depending on internet speed)  
**Disk Space Used**: ~8-12GB (including models)  
**Memory Usage**: ~4-8GB during operation  
