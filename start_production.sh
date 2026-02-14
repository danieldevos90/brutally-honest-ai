#!/bin/bash
# ============================================
# PRODUCTION STARTUP SCRIPT
# Brutally Honest AI - Production Deployment
# ============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Brutally Honest AI - Production Mode${NC}"
echo "=================================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check for .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.production template...${NC}"
        cp .env.production .env
        echo -e "${RED}⚠️  IMPORTANT: Edit .env and update the security settings before running in production!${NC}"
        exit 1
    else
        echo -e "${RED}❌ No .env or .env.production file found!${NC}"
        exit 1
    fi
fi

# Source environment variables
set -a
source .env
set +a

# Validate critical environment variables
if [[ "${MASTER_API_KEY}" == *"CHANGE_THIS"* ]]; then
    echo -e "${RED}❌ ERROR: MASTER_API_KEY has not been changed from default!${NC}"
    echo "   Please update .env with a secure API key."
    exit 1
fi

if [[ "${ADMIN_PASSWORD}" == *"CHANGE_THIS"* ]]; then
    echo -e "${RED}❌ ERROR: ADMIN_PASSWORD has not been changed from default!${NC}"
    echo "   Please update .env with a secure password."
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found. Creating one...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Create required directories
echo -e "${GREEN}📁 Creating storage directories...${NC}"
mkdir -p "${STORAGE_PATH:-./data}" 
mkdir -p "${RECORDINGS_PATH:-./data/recordings}"
mkdir -p "${DOCUMENTS_PATH:-./data/documents}"
mkdir -p "${LOG_FILE%/*}" 2>/dev/null || true

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port in use
    else
        return 1  # Port free
    fi
}

# Check if API port is available
API_PORT=${API_PORT:-8000}
if check_port $API_PORT; then
    echo -e "${YELLOW}⚠️  Port $API_PORT is already in use${NC}"
    echo "   Kill the existing process or change API_PORT in .env"
    exit 1
fi

# Check if Frontend port is available
FRONTEND_PORT=${FRONTEND_PORT:-3001}
if check_port $FRONTEND_PORT; then
    echo -e "${YELLOW}⚠️  Port $FRONTEND_PORT is already in use${NC}"
    echo "   Kill the existing process or change FRONTEND_PORT in .env"
    exit 1
fi

# Start API server
echo -e "${GREEN}🔧 Starting API server on port $API_PORT...${NC}"

WORKERS=${WORKERS:-4}
API_HOST=${API_HOST:-0.0.0.0}

if [ "${ENABLE_HTTPS}" = "true" ] && [ -f "${SSL_CERT_PATH}" ] && [ -f "${SSL_KEY_PATH}" ]; then
    echo -e "${GREEN}🔒 HTTPS enabled${NC}"
    uvicorn api_server:app \
        --host $API_HOST \
        --port $API_PORT \
        --workers $WORKERS \
        --ssl-keyfile "$SSL_KEY_PATH" \
        --ssl-certfile "$SSL_CERT_PATH" \
        --log-level ${LOG_LEVEL:-info} &
else
    echo -e "${YELLOW}⚠️  Running without HTTPS (not recommended for production)${NC}"
    uvicorn api_server:app \
        --host $API_HOST \
        --port $API_PORT \
        --workers $WORKERS \
        --log-level ${LOG_LEVEL:-info} &
fi

API_PID=$!
echo "   API Server PID: $API_PID"

# Wait for API to start
sleep 2
if ! kill -0 $API_PID 2>/dev/null; then
    echo -e "${RED}❌ API server failed to start${NC}"
    exit 1
fi

# Start Frontend server
echo -e "${GREEN}🌐 Starting Frontend server on port $FRONTEND_PORT...${NC}"
cd frontend
FRONTEND_HOST=${FRONTEND_HOST:-0.0.0.0}
PORT=$FRONTEND_PORT HOST=$FRONTEND_HOST node server.js &
FRONTEND_PID=$!
echo "   Frontend Server PID: $FRONTEND_PID"
cd ..

# Wait for Frontend to start
sleep 2
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Frontend server failed to start${NC}"
    kill $API_PID 2>/dev/null
    exit 1
fi

# Display status
echo ""
echo -e "${GREEN}✅ Brutally Honest AI is running!${NC}"
echo "=================================================="
echo -e "   API Server:      http://$API_HOST:$API_PORT"
echo -e "   Frontend:        http://$FRONTEND_HOST:$FRONTEND_PORT"
echo -e "   API Docs:        http://$API_HOST:$API_PORT/docs"
echo -e "   Health Check:    http://$API_HOST:$API_PORT/health"
echo ""
echo -e "   API PID: $API_PID"
echo -e "   Frontend PID: $FRONTEND_PID"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Trap for cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Shutting down services...${NC}"
    kill $API_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ All services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for processes
wait
