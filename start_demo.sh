#!/bin/bash

echo "🎙️ Starting Voice Insight Platform Demo"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run setup.py first.${NC}"
    exit 1
fi

# Check if frontend directory exists
if [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Frontend directory not found.${NC}"
    exit 1
fi

echo -e "${BLUE}🐳 Checking Docker services...${NC}"
docker-compose ps

echo ""
echo -e "${BLUE}🚀 Starting Backend (FastAPI)...${NC}"
source venv/bin/activate
python main_enhanced.py &
BACKEND_PID=$!

echo "Backend started with PID: $BACKEND_PID"
echo "Waiting for backend to initialize..."
sleep 5

echo ""
echo -e "${BLUE}🌐 Starting Frontend (Node.js)...${NC}"
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "Frontend started with PID: $FRONTEND_PID"
echo "Waiting for frontend to initialize..."
sleep 3

echo ""
echo -e "${GREEN}✅ Demo Platform Started Successfully!${NC}"
echo ""
echo -e "${YELLOW}🎯 Demo URLs:${NC}"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}🎬 To run the demo:${NC}"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Click '🎬 Start Live Demo'"
echo "   3. Watch Whisper transcribe and Llama fact-check!"
echo ""
echo -e "${YELLOW}📊 System Status:${NC}"
curl -s http://localhost:8000/api/status | jq '.' 2>/dev/null || echo "Backend starting..."
echo ""
echo -e "${YELLOW}🎙️ OMI Status:${NC}"
curl -s http://localhost:8000/api/omi/ports | jq '.omi_detected, .omi_device' 2>/dev/null || echo "Backend starting..."
echo ""
echo -e "${GREEN}🎉 Your brutally honest AI demo is ready!${NC}"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap 'echo ""; echo "🛑 Stopping services..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "✅ All services stopped"; exit 0' INT

# Keep script running
wait
