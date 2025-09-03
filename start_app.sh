#!/bin/bash

# Brutally Honest AI - Unified Startup Script
# This script starts both the backend API server and frontend web server

set -e

echo "🚀 Starting Brutally Honest AI Application..."
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
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run: python -m venv venv${NC}"
    exit 1
fi

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

# Activate virtual environment and start backend
echo -e "${BLUE}🔌 Starting backend API server...${NC}"
source venv/bin/activate

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
    if ! ollama list | grep -q "llama2:7b"; then
        echo -e "${YELLOW}⚠️  LLAMA model not found - pulling llama2:7b${NC}"
        ollama pull llama2:7b
    fi
elif [ -f "models/llama-2-7b-chat.gguf" ]; then
    echo -e "${GREEN}✅ GGUF model found${NC}"
else
    echo -e "${YELLOW}⚠️  No LLAMA model found - transcription may fail${NC}"
    echo -e "${BLUE}💡 Run the install script to set up LLAMA: ./install_brutally_honest.sh${NC}"
fi

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

echo ""
echo -e "${GREEN}🎉 Brutally Honest AI is now running!${NC}"
echo "=================================================="
echo -e "${BLUE}📡 Backend API:${NC} http://localhost:8000"
echo -e "${BLUE}🌐 Frontend Web:${NC} http://localhost:3001"
echo -e "${BLUE}📚 API Docs:${NC} http://localhost:8000/docs"
echo -e "${BLUE}🔌 WebSocket:${NC} ws://localhost:8000/ws"
echo ""
echo -e "${YELLOW}💡 Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
