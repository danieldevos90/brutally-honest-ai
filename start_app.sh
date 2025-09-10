#!/bin/bash

# Brutally Honest AI - Unified Startup Script
# This script starts both the backend API server and frontend web server

set -e

echo "🚀 Starting Brutally Honest AI Application..."
echo "=================================================="
echo -e "${BLUE}🆕 NEW: Document Knowledge Base Feature${NC}"
echo -e "${BLUE}   📄 Upload TXT, PDF, DOC, DOCX files${NC}"
echo -e "${BLUE}   🔍 AI-powered document search & Q&A${NC}"
echo -e "${BLUE}   🧠 Vector database with LLAMA integration${NC}"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        echo "🔌 Stopping backend server (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "🌐 Stopping frontend server (PID: $FRONTEND_PID)"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$WHISPER_PRELOAD_PID" ]; then
        echo "🎤 Stopping Whisper preload (PID: $WHISPER_PRELOAD_PID)"
        kill $WHISPER_PRELOAD_PID 2>/dev/null || true
    fi
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}🐍 Activating virtual environment...${NC}"
source venv/bin/activate

# Check and install Python dependencies
echo -e "${BLUE}📦 Checking Python dependencies...${NC}"
MISSING_DEPS=0

# Check core dependencies
if ! pip list | grep -q "fastapi"; then
    echo -e "${YELLOW}⚠️  FastAPI not found${NC}"
    MISSING_DEPS=1
fi

if ! pip list | grep -q "qdrant-client"; then
    echo -e "${YELLOW}⚠️  Qdrant client not found${NC}"
    MISSING_DEPS=1
fi

if ! pip list | grep -q "sentence-transformers"; then
    echo -e "${YELLOW}⚠️  Sentence transformers not found${NC}"
    MISSING_DEPS=1
fi

# Check document processing dependencies
if ! pip list | grep -q "PyPDF2\|pdfplumber"; then
    echo -e "${YELLOW}⚠️  PDF processing libraries not found${NC}"
    MISSING_DEPS=1
fi

if ! pip list | grep -q "python-docx\|docx2txt"; then
    echo -e "${YELLOW}⚠️  DOC/DOCX processing libraries not found${NC}"
    MISSING_DEPS=1
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo -e "${YELLOW}📦 Installing missing Python dependencies...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${GREEN}✅ All Python dependencies are installed${NC}"
fi

# Upgrade pip if needed
echo -e "${BLUE}🔧 Ensuring pip is up to date...${NC}"
pip install --upgrade pip > /dev/null 2>&1

# Check if node_modules exists in frontend
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
fi

# Kill any existing processes on the ports we need
echo -e "${BLUE}🔍 Checking for existing processes on ports 8000 and 3001...${NC}"

# Kill process on port 8000 (backend)
EXISTING_BACKEND=$(lsof -ti:8000 2>/dev/null || true)
if [ ! -z "$EXISTING_BACKEND" ]; then
    echo "🔌 Stopping existing backend process on port 8000"
    kill -9 $EXISTING_BACKEND 2>/dev/null || true
    sleep 2
fi

# Kill process on port 3001 (frontend)
EXISTING_FRONTEND=$(lsof -ti:3001 2>/dev/null || true)
if [ ! -z "$EXISTING_FRONTEND" ]; then
    echo "🌐 Stopping existing frontend process on port 3001"
    kill -9 $EXISTING_FRONTEND 2>/dev/null || true
    sleep 2
fi

echo -e "${GREEN}✅ Ports cleared${NC}"

# Test document processing feature
echo -e "${BLUE}🧪 Testing document processing feature...${NC}"
python -c "
import sys
sys.path.insert(0, 'src')

# Test document processor
try:
    from documents.processor import DocumentProcessor
    print('✅ Document processor module loaded')
except ImportError as e:
    print(f'❌ Document processor failed: {e}')
    sys.exit(1)

# Test vector store
try:
    from documents.vector_store import VectorStore
    print('✅ Vector store module loaded')
except ImportError as e:
    print(f'❌ Vector store failed: {e}')
    sys.exit(1)

# Test sentence transformers
try:
    from sentence_transformers import SentenceTransformer
    print('✅ Sentence transformers available')
except ImportError as e:
    print(f'❌ Sentence transformers failed: {e}')
    sys.exit(1)

# Test qdrant client
try:
    from qdrant_client import QdrantClient
    print('✅ Qdrant client available')
except ImportError as e:
    print(f'❌ Qdrant client failed: {e}')
    sys.exit(1)

# Test document processing libraries
pdf_support = False
doc_support = False

try:
    import PyPDF2
    pdf_support = True
    print('✅ PyPDF2 available for PDF processing')
except ImportError:
    try:
        import pdfplumber
        pdf_support = True
        print('✅ pdfplumber available for PDF processing')
    except ImportError:
        print('⚠️  No PDF processing library found')

try:
    import docx2txt
    doc_support = True
    print('✅ docx2txt available for DOC/DOCX processing')
except ImportError:
    try:
        from docx import Document
        doc_support = True
        print('✅ python-docx available for DOCX processing')
    except ImportError:
        print('⚠️  No DOC/DOCX processing library found')

if pdf_support and doc_support:
    print('🎉 All document processing features are ready!')
else:
    print('⚠️  Some document formats may not be supported')

print('✅ Document processing feature initialization complete')
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Document processing feature ready${NC}"
    
    # Run a quick integration test
    echo -e "${BLUE}🧪 Running document processing integration test...${NC}"
    if python test_documents.py > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Document processing integration test passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Document processing integration test had issues${NC}"
        echo -e "${BLUE}💡 Feature should still work, but check logs if you encounter problems${NC}"
    fi
else
    echo -e "${RED}❌ Document processing feature failed initialization${NC}"
    echo -e "${YELLOW}💡 Try running: pip install -r requirements.txt${NC}"
    exit 1
fi

# Check if LLAMA model is available
echo -e "${BLUE}🦙 Checking LLAMA model availability...${NC}"
if command -v ollama >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Ollama found - starting service${NC}"
    # Start Ollama in background if not running
    if ! pgrep -f "ollama serve" > /dev/null; then
        ollama serve &
        sleep 3
    fi
    
    # Check if model is available
    if ! ollama list | grep -q "tinyllama:latest"; then
        echo -e "${YELLOW}⚠️  TinyLlama model not found - pulling tinyllama:latest${NC}"
        ollama pull tinyllama:latest
    fi
    
    # Pre-warm the model for faster responses
    echo -e "${BLUE}🔥 Pre-warming TinyLlama model...${NC}"
    curl -s -X POST http://localhost:11434/api/generate \
        -d '{"model": "tinyllama:latest", "prompt": "Ready", "stream": false, "keep_alive": "10m", "options": {"num_predict": 1}}' \
        --max-time 30 > /dev/null 2>&1 &
    
    echo -e "${GREEN}✅ TinyLlama model warming in background${NC}"
elif [ -f "models/llama-2-7b-chat.gguf" ]; then
    echo -e "${GREEN}✅ GGUF model found${NC}"
else
    echo -e "${YELLOW}⚠️  No LLAMA model found - transcription may fail${NC}"
    echo -e "${BLUE}💡 Run the install script to set up LLAMA: ./install_brutally_honest.sh${NC}"
fi

# Pre-load Whisper model to avoid first-use download delay
echo -e "${BLUE}🎤 Pre-loading Whisper model (medium)...${NC}"
python -c "
import whisper
import sys
try:
    print('📥 Downloading Whisper medium model (1.42GB)...')
    model = whisper.load_model('medium')
    print('✅ Whisper medium model loaded successfully')
except Exception as e:
    print(f'⚠️  Whisper model preload failed: {e}')
    print('💡 Model will be downloaded on first use')
" &
WHISPER_PRELOAD_PID=$!

# Show progress while Whisper downloads
echo -e "${YELLOW}⏳ Whisper model downloading in background...${NC}"

# Start backend in background
python api_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Start frontend
echo -e "${BLUE}🌐 Starting frontend web server...${NC}"
cd frontend

# Start frontend in background
npm start &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 3

# Check if frontend started successfully
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Frontend failed to start${NC}"
    cleanup
    exit 1
fi

cd ..

echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"

# Wait for Whisper preload to complete (with timeout)
if [ ! -z "$WHISPER_PRELOAD_PID" ]; then
    echo -e "${BLUE}⏳ Waiting for Whisper model preload to complete...${NC}"
    
    # Wait up to 120 seconds for Whisper preload
    TIMEOUT=120
    ELAPSED=0
    while kill -0 $WHISPER_PRELOAD_PID 2>/dev/null && [ $ELAPSED -lt $TIMEOUT ]; do
        sleep 5
        ELAPSED=$((ELAPSED + 5))
        echo -e "${YELLOW}⏳ Still downloading Whisper model... (${ELAPSED}s/${TIMEOUT}s)${NC}"
    done
    
    if kill -0 $WHISPER_PRELOAD_PID 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Whisper preload taking longer than expected - continuing anyway${NC}"
        kill $WHISPER_PRELOAD_PID 2>/dev/null || true
    else
        echo -e "${GREEN}✅ Whisper model preload completed${NC}"
    fi
fi

echo ""
echo -e "${GREEN}🎉 Brutally Honest AI is now running!${NC}"
echo "=================================================="
echo -e "${BLUE}📡 Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}🌐 Frontend Web:${NC} http://localhost:3001"
echo -e "${BLUE}📄 Document KB:${NC} http://localhost:3001/documents.html"
echo -e "${BLUE}📚 API Docs:${NC} http://localhost:8000/docs"
echo -e "${BLUE}🔌 WebSocket:${NC} ws://localhost:8000/ws"
echo ""
echo -e "${GREEN}🆕 NEW FEATURES:${NC}"
echo -e "${BLUE}   📄 Document Upload:${NC} Upload TXT, PDF, DOC, DOCX files"
echo -e "${BLUE}   🔍 AI-Powered Search:${NC} Ask questions about your documents"
echo -e "${BLUE}   🧠 Vector Database:${NC} Semantic search with LLAMA integration"
echo ""
echo -e "${YELLOW}💡 Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
