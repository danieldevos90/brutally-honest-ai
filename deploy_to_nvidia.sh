#!/bin/bash

# Brutally Honest AI - Remote Nvidia Deployment Script
# Deploys to: brutally@192.168.2.33

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

REMOTE_HOST="brutally@192.168.2.33"
REMOTE_DIR="/home/brutally/brutally-honest-ai"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║      BRUTALLY HONEST AI - NVIDIA DEPLOYMENT                   ║${NC}"
echo -e "${CYAN}║      Target: $REMOTE_HOST                        ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test SSH connection
echo -e "${YELLOW}➤ Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$REMOTE_HOST" "echo 'connected'" >/dev/null 2>&1; then
    echo -e "${RED}✗ SSH connection failed.${NC}"
    echo -e "${YELLOW}Please run: ssh-copy-id -i ~/.ssh/id_ed25519.pub $REMOTE_HOST${NC}"
    exit 1
fi
echo -e "${GREEN}✓ SSH connection successful${NC}"

# Check remote system info
echo -e "\n${YELLOW}➤ Checking remote system...${NC}"
ssh "$REMOTE_HOST" "uname -a && nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo 'No NVIDIA GPU detected via nvidia-smi'"

# Step 1: Create remote directory
echo -e "\n${YELLOW}➤ Step 1: Creating remote directory...${NC}"
ssh "$REMOTE_HOST" "mkdir -p $REMOTE_DIR"
echo -e "${GREEN}✓ Directory created: $REMOTE_DIR${NC}"

# Step 2: Sync project files (excluding large directories)
echo -e "\n${YELLOW}➤ Step 2: Syncing project files...${NC}"
rsync -avz --progress \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude 'node_modules/' \
    --exclude '*.db' \
    --exclude '.git/' \
    --exclude 'models/*.gguf' \
    --exclude 'documents/*' \
    --exclude 'uploads/*' \
    --exclude '.env' \
    --exclude '.env.local' \
    "$LOCAL_DIR/" "$REMOTE_HOST:$REMOTE_DIR/"
echo -e "${GREEN}✓ Files synced${NC}"

# Step 3: Install system dependencies on remote
echo -e "\n${YELLOW}➤ Step 3: Installing system dependencies...${NC}"
ssh "$REMOTE_HOST" << 'REMOTE_SCRIPT'
set -e
echo "Updating package lists..."
sudo apt-get update

echo "Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    ffmpeg \
    portaudio19-dev \
    libsndfile1 \
    libffi-dev \
    libssl-dev \
    git \
    curl \
    wget \
    nodejs \
    npm \
    bluetooth \
    bluez \
    libbluetooth-dev

echo "System dependencies installed!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ System dependencies installed${NC}"

# Step 4: Setup Python environment
echo -e "\n${YELLOW}➤ Step 4: Setting up Python environment...${NC}"
ssh "$REMOTE_HOST" << REMOTE_SCRIPT
set -e
cd $REMOTE_DIR

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and upgrade pip
source venv/bin/activate
pip install --upgrade pip wheel setuptools

# Detect if this is a Jetson (ARM64 with NVIDIA)
if [ -f /etc/nv_tegra_release ]; then
    echo "Detected NVIDIA Jetson - using Jetson-optimized requirements"
    
    # Install PyTorch for Jetson first (if not already)
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 2>/dev/null || true
    
    pip install --no-cache-dir -r requirements_jetson.txt
else
    echo "Standard Linux system - using regular requirements"
    pip install --no-cache-dir -r requirements.txt
fi

echo "Python packages installed!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ Python environment setup complete${NC}"

# Step 5: Setup Ollama for LLM
echo -e "\n${YELLOW}➤ Step 5: Installing Ollama...${NC}"
ssh "$REMOTE_HOST" << 'REMOTE_SCRIPT'
set -e

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "Ollama already installed"
fi

# Start Ollama service
echo "Starting Ollama service..."
sudo systemctl enable ollama 2>/dev/null || true
sudo systemctl start ollama 2>/dev/null || (nohup ollama serve > /dev/null 2>&1 &)
sleep 5

# Pull LLAMA model
echo "Pulling llama2 model (this may take a while)..."
ollama pull llama2:7b || ollama pull tinyllama:latest

echo "Ollama setup complete!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ Ollama installed and model downloaded${NC}"

# Step 6: Setup Node.js frontend
echo -e "\n${YELLOW}➤ Step 6: Setting up frontend...${NC}"
ssh "$REMOTE_HOST" << REMOTE_SCRIPT
set -e
cd $REMOTE_DIR/frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

echo "Frontend setup complete!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ Frontend setup complete${NC}"

# Step 7: Create environment file
echo -e "\n${YELLOW}➤ Step 7: Creating environment configuration...${NC}"
ssh "$REMOTE_HOST" << REMOTE_SCRIPT
set -e
cd $REMOTE_DIR

if [ ! -f ".env" ]; then
    cat > .env << 'ENVFILE'
# Brutally Honest AI Configuration

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Frontend Settings
FRONTEND_PORT=3001

# Whisper Settings
WHISPER_MODEL=base
WHISPER_DEVICE=cuda

# Ollama Settings
OLLAMA_URL=http://localhost:11434
LLM_MODEL=llama2:7b

# Database (optional - uses SQLite by default)
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# POSTGRES_DB=voice_insight
# POSTGRES_USER=postgres
# POSTGRES_PASSWORD=password

# Vector Database (optional)
# QDRANT_HOST=localhost
# QDRANT_PORT=6333
ENVFILE
    echo "Environment file created!"
else
    echo "Environment file already exists"
fi
REMOTE_SCRIPT
echo -e "${GREEN}✓ Environment configured${NC}"

# Step 8: Create systemd services
echo -e "\n${YELLOW}➤ Step 8: Creating system services...${NC}"
ssh "$REMOTE_HOST" << REMOTE_SCRIPT
set -e

# Create API service
sudo tee /etc/systemd/system/brutally-honest-api.service > /dev/null << 'SERVICE'
[Unit]
Description=Brutally Honest AI API Server
After=network.target ollama.service

[Service]
Type=simple
User=brutally
WorkingDirectory=/home/brutally/brutally-honest-ai
Environment=PATH=/home/brutally/brutally-honest-ai/venv/bin
ExecStart=/home/brutally/brutally-honest-ai/venv/bin/python api_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Create Frontend service
sudo tee /etc/systemd/system/brutally-honest-frontend.service > /dev/null << 'SERVICE'
[Unit]
Description=Brutally Honest AI Frontend
After=network.target brutally-honest-api.service

[Service]
Type=simple
User=brutally
WorkingDirectory=/home/brutally/brutally-honest-ai/frontend
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Reload systemd
sudo systemctl daemon-reload
echo "System services created!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ System services created${NC}"

# Step 9: Start services
echo -e "\n${YELLOW}➤ Step 9: Starting services...${NC}"
ssh "$REMOTE_HOST" << 'REMOTE_SCRIPT'
set -e

echo "Starting Brutally Honest AI services..."

# Start and enable services
sudo systemctl enable brutally-honest-api
sudo systemctl enable brutally-honest-frontend

sudo systemctl restart brutally-honest-api
sleep 3
sudo systemctl restart brutally-honest-frontend

# Show status
echo ""
echo "Service Status:"
sudo systemctl status brutally-honest-api --no-pager -l | head -10
echo ""
sudo systemctl status brutally-honest-frontend --no-pager -l | head -10

echo ""
echo "Services started!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ Services started${NC}"

# Final summary
echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ DEPLOYMENT COMPLETE!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Access your Brutally Honest AI:${NC}"
echo -e "  • Frontend:  ${GREEN}http://192.168.2.33:3001${NC}"
echo -e "  • API Docs:  ${GREEN}http://192.168.2.33:8000/docs${NC}"
echo -e "  • Ollama:    ${GREEN}http://192.168.2.33:11434${NC}"
echo ""
echo -e "${YELLOW}Useful commands (on remote):${NC}"
echo -e "  • Check API logs:      sudo journalctl -u brutally-honest-api -f"
echo -e "  • Check frontend logs: sudo journalctl -u brutally-honest-frontend -f"
echo -e "  • Restart API:         sudo systemctl restart brutally-honest-api"
echo -e "  • Restart frontend:    sudo systemctl restart brutally-honest-frontend"
echo ""
echo -e "${GREEN}Enjoy your Brutally Honest AI! 🎯${NC}"


