# 🚀 Quick Start Guide

## 📁 Project Structure

- `docs/` - All documentation files
- `src/` - Python source code
- `frontend/` - Web interface (Node.js)
- `landing-page/` - Marketing landing page
- `omi_firmware/` - ESP32 firmware
- `scripts/` - Utility scripts
- `installer/` - Installation packages

## Running Brutally Honest AI

### Option 1: Use the Unified Startup Script (Recommended)

**For macOS/Linux:**
```bash
./start_app.sh
```

**For Windows:**
```cmd
start_app.bat
```

### Option 2: Manual Startup

**Terminal 1 - Backend:**
```bash
source venv/bin/activate
python api_server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

## 🌐 Access Points

Once both services are running:

- **🌐 Web Interface:** http://localhost:3001
- **📡 API Server:** http://localhost:8000  
- **📚 API Documentation:** http://localhost:8000/docs
- **🔌 WebSocket:** ws://localhost:8000/ws

## 🛑 Stopping Services

- **Unified Script:** Press `Ctrl+C` in the terminal
- **Manual:** Press `Ctrl+C` in each terminal window
- **Windows:** Close the command prompt windows

## 🔧 Troubleshooting

### Transcription Failed: LLAMA Model Not Loaded
If you get "Transcription failed: Load failed; make sure LLAMA is also loaded locally":

```bash
# Quick fix - run the LLAMA setup script
./setup_llama.sh
```

**Or manually install LLAMA:**

**Option 1: Ollama (Recommended)**
```bash
# Install Ollama
brew install ollama  # macOS
# or visit https://ollama.ai/download

# Start service and pull model
ollama serve &
ollama pull llama2:7b
```

**Option 2: Direct Model Download**
```bash
# Install dependencies
pip install llama-cpp-python transformers

# Download model (4GB)
mkdir -p models
curl -L -o models/llama-2-7b-chat.gguf \
  "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.q4_0.gguf"
```

### Port Already in Use Error
If you get "EADDRINUSE" errors:

```bash
# Kill processes on ports 8000 and 3001
lsof -ti:8000 | xargs kill -9
lsof -ti:3001 | xargs kill -9
```

### Missing Dependencies
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies  
cd frontend && npm install
```

### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## 📚 Documentation

All documentation is in the `docs/` folder:

- **Setup Guides:** `RECOMPUTER_J4011_*.md`, `COMPLETE_SYSTEM_GUIDE.md`
- **Features:** `DOCUMENT_FEATURE_README.md`, `MULTI_DEVICE_SUPPORT.md`
- **Development:** `NODEJS_ROUTING_GUIDE.md`, `WHISPER_TRAINING_GUIDE.md`
- **Validation:** `QUICK_START_VALIDATION.md`, `QUICK_START_FACT_CHECKING.md`
