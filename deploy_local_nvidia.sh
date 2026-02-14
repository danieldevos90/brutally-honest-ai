#!/bin/bash

# Brutally Honest AI - Local Network NVIDIA Deployment Script
# Deploys to an NVIDIA device on your local network
# Supports Jetson (Orin Nano, etc.) or any Linux machine with NVIDIA GPU

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration - Set these or pass as environment variables
NVIDIA_HOST="${NVIDIA_HOST:-}"
NVIDIA_USER="${NVIDIA_USER:-brutally}"
NVIDIA_DIR="${NVIDIA_DIR:-/home/${NVIDIA_USER}/brutally-honest-ai}"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   BRUTALLY HONEST AI - LOCAL NVIDIA DEPLOYMENT                ║${NC}"
echo -e "${CYAN}║   Multi-Device Queue & Vector Database Ready                  ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================
# STEP 0: Network Discovery & Configuration
# ============================================

if [ -z "$NVIDIA_HOST" ]; then
    echo -e "${YELLOW}➤ No NVIDIA_HOST specified. Let's find your NVIDIA device...${NC}"
    echo ""
    
    # Try to discover devices on local network
    echo -e "${BLUE}Scanning local network for potential NVIDIA/Jetson devices...${NC}"
    
    # Common Jetson hostnames and patterns
    FOUND_HOSTS=()
    
    # Check for common Jetson hostnames
    for hostname in "jetson" "nvidia-jetson" "orin-nano" "jetson-nano" "brutally" "brutallyhonest"; do
        if ping -c 1 -W 1 "$hostname.local" &>/dev/null 2>&1; then
            echo -e "${GREEN}  ✓ Found: $hostname.local${NC}"
            FOUND_HOSTS+=("$hostname.local")
        fi
    done
    
    # Quick scan of common local IPs
    echo -e "${BLUE}Checking common local IP ranges...${NC}"
    LOCAL_SUBNET=$(ip route 2>/dev/null | grep "src" | head -1 | awk '{print $1}' || echo "192.168.1.0/24")
    
    # Let user input manually if not found
    if [ ${#FOUND_HOSTS[@]} -eq 0 ]; then
        echo -e "${YELLOW}No devices found automatically.${NC}"
        echo ""
        echo "Please enter your NVIDIA device's IP address or hostname:"
        echo "Examples:"
        echo "  - 192.168.1.100"
        echo "  - 10.0.0.50"
        echo "  - jetson.local"
        echo "  - nvidia-orin.local"
        echo ""
        read -p "NVIDIA Host: " NVIDIA_HOST
    else
        echo ""
        echo "Found devices:"
        select host in "${FOUND_HOSTS[@]}" "Enter manually"; do
            if [ "$host" == "Enter manually" ]; then
                read -p "NVIDIA Host: " NVIDIA_HOST
            else
                NVIDIA_HOST="$host"
            fi
            break
        done
    fi
fi

if [ -z "$NVIDIA_HOST" ]; then
    echo -e "${RED}✗ No host specified. Exiting.${NC}"
    exit 1
fi

REMOTE_HOST="${NVIDIA_USER}@${NVIDIA_HOST}"

echo ""
echo -e "${CYAN}Deployment Configuration:${NC}"
echo -e "  Target Host: ${GREEN}$NVIDIA_HOST${NC}"
echo -e "  SSH User:    ${GREEN}$NVIDIA_USER${NC}"
echo -e "  Remote Dir:  ${GREEN}$NVIDIA_DIR${NC}"
echo -e "  Local Dir:   ${GREEN}$LOCAL_DIR${NC}"
echo ""

# ============================================
# STEP 1: Test SSH Connection
# ============================================
echo -e "${YELLOW}➤ Step 1: Testing SSH connection to $NVIDIA_HOST...${NC}"

# First try without password (key-based)
if ssh -o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no "$REMOTE_HOST" "echo 'connected'" >/dev/null 2>&1; then
    echo -e "${GREEN}✓ SSH connection successful (key-based auth)${NC}"
else
    echo -e "${YELLOW}Key-based auth failed. Trying password auth...${NC}"
    echo ""
    echo "Please enter the password for $REMOTE_HOST:"
    
    # Test with password prompt
    if ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no "$REMOTE_HOST" "echo 'connected'"; then
        echo -e "${GREEN}✓ SSH connection successful (password auth)${NC}"
        echo ""
        echo -e "${YELLOW}Tip: For faster future deployments, run:${NC}"
        echo -e "  ssh-copy-id $REMOTE_HOST"
    else
        echo -e "${RED}✗ SSH connection failed.${NC}"
        echo ""
        echo "Please ensure:"
        echo "  1. The device is powered on and connected to the network"
        echo "  2. SSH is enabled on the device"
        echo "  3. The username and IP are correct"
        echo ""
        echo "For Jetson devices, default credentials are often:"
        echo "  Username: nvidia or jetson"
        echo "  Password: nvidia or jetson"
        exit 1
    fi
fi

# ============================================
# STEP 2: Check Remote System
# ============================================
echo -e "\n${YELLOW}➤ Step 2: Checking remote system...${NC}"

SYSTEM_INFO=$(ssh "$REMOTE_HOST" "
    echo '=== System Info ==='
    uname -a
    echo ''
    echo '=== GPU Info ==='
    if command -v nvidia-smi &>/dev/null; then
        nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || echo 'nvidia-smi available but query failed'
    elif [ -f /etc/nv_tegra_release ]; then
        cat /etc/nv_tegra_release
        echo 'Jetson device detected (tegra)'
    else
        echo 'No NVIDIA GPU detected'
    fi
    echo ''
    echo '=== Memory ==='
    free -h | head -2
    echo ''
    echo '=== Disk Space ==='
    df -h / | tail -1
")

echo "$SYSTEM_INFO"

# ============================================
# STEP 3: Create Remote Directory
# ============================================
echo -e "\n${YELLOW}➤ Step 3: Creating remote directory...${NC}"
ssh "$REMOTE_HOST" "mkdir -p $NVIDIA_DIR"
echo -e "${GREEN}✓ Directory created: $NVIDIA_DIR${NC}"

# ============================================
# STEP 4: Sync Project Files
# ============================================
echo -e "\n${YELLOW}➤ Step 4: Syncing project files...${NC}"
echo "This may take a few minutes for the first sync..."

# Persist history/recordings across deploys:
# - Keep state under $NVIDIA_STATE_DIR (outside the repo)
# - Use symlinks inside the repo so existing code keeps working
NVIDIA_STATE_DIR="${NVIDIA_STATE_DIR:-/home/${NVIDIA_USER}/.brutally-honest-ai-state}"

rsync -avz --progress --keep-dirlinks \
    --exclude 'venv/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude 'node_modules/' \
    --exclude '*.db' \
    --exclude '.git/' \
    --exclude 'models/*.gguf' \
    --exclude 'documents/*' \
    --exclude 'uploads/*' \
    --exclude 'data/' \
    --exclude 'recordings/' \
    --exclude 'frontend/uploads/recordings/' \
    --exclude '.env' \
    --exclude '.env.local' \
    --exclude '.env.backup' \
    --exclude 'data/qdrant_storage/*' \
    "$LOCAL_DIR/" "$REMOTE_HOST:$NVIDIA_DIR/"
    
echo -e "${GREEN}✓ Files synced${NC}"

# Ensure persistent state folders + symlinks exist (no sudo required)
echo -e "\n${YELLOW}➤ Step 4b: Ensuring persistent state (history + recordings)...${NC}"
ssh "$REMOTE_HOST" << REMOTE_SCRIPT
set -e
mkdir -p "$NVIDIA_STATE_DIR/data" "$NVIDIA_STATE_DIR/recordings" "$NVIDIA_STATE_DIR/frontend_uploads_recordings"
cd "$NVIDIA_DIR"

# Migrate existing state if it's currently a real directory in the repo (first-run safety)
if [ -d "data" ] && [ ! -L "data" ]; then
  cp -a "data/." "$NVIDIA_STATE_DIR/data/" 2>/dev/null || true
  rm -rf "data"
fi
if [ -d "recordings" ] && [ ! -L "recordings" ]; then
  cp -a "recordings/." "$NVIDIA_STATE_DIR/recordings/" 2>/dev/null || true
  rm -rf "recordings"
fi
mkdir -p "frontend/uploads"
if [ -d "frontend/uploads/recordings" ] && [ ! -L "frontend/uploads/recordings" ]; then
  cp -a "frontend/uploads/recordings/." "$NVIDIA_STATE_DIR/frontend_uploads_recordings/" 2>/dev/null || true
  rm -rf "frontend/uploads/recordings"
fi

ln -sfn "$NVIDIA_STATE_DIR/data" "data"
ln -sfn "$NVIDIA_STATE_DIR/recordings" "recordings"
ln -sfn "$NVIDIA_STATE_DIR/frontend_uploads_recordings" "frontend/uploads/recordings"

# Ensure JSON exists so UI never shows "gone" due to missing file
if [ ! -f "data/transcription_history.json" ]; then echo "[]" > "data/transcription_history.json"; fi
if [ ! -f "data/validation_history.json" ]; then echo "[]" > "data/validation_history.json"; fi
REMOTE_SCRIPT
echo -e "${GREEN}✓ Persistent state configured at: $NVIDIA_STATE_DIR${NC}"

# ============================================
# STEP 5: Install System Dependencies
# ============================================
echo -e "\n${YELLOW}➤ Step 5: Installing system dependencies...${NC}"
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
    wget

# Check if Node.js is installed, if not install it
if ! command -v node &>/dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "System dependencies installed!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ System dependencies installed${NC}"

# ============================================
# STEP 6: Setup Python Environment
# ============================================
echo -e "\n${YELLOW}➤ Step 6: Setting up Python environment...${NC}"
ssh "$REMOTE_HOST" << REMOTE_SCRIPT
set -e
cd $NVIDIA_DIR

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and upgrade pip
source venv/bin/activate
pip install --upgrade pip wheel setuptools

# Detect if this is a Jetson (ARM64 with NVIDIA Tegra)
if [ -f /etc/nv_tegra_release ]; then
    echo "Detected NVIDIA Jetson - using Jetson-optimized requirements"
    
    # On Jetson, PyTorch is pre-installed or needs special wheels
    # Try to use the Jetson-optimized requirements
    if [ -f "requirements_jetson.txt" ]; then
        pip install --no-cache-dir -r requirements_jetson.txt
    else
        pip install --no-cache-dir -r requirements.txt
    fi
else
    echo "Standard Linux system - using regular requirements"
    pip install --no-cache-dir -r requirements.txt
fi

echo "Python packages installed!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ Python environment setup complete${NC}"

# ============================================
# STEP 7: Install Ollama for LLM
# ============================================
echo -e "\n${YELLOW}➤ Step 7: Installing/Updating Ollama...${NC}"
ssh "$REMOTE_HOST" << 'REMOTE_SCRIPT'
set -e

# Check if Ollama is installed
if ! command -v ollama &>/dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
else
    echo "Ollama already installed: $(ollama --version 2>/dev/null || echo 'version unknown')"
fi

# Start Ollama service
echo "Starting Ollama service..."
if systemctl is-active --quiet ollama 2>/dev/null; then
    echo "Ollama service already running"
else
    sudo systemctl enable ollama 2>/dev/null || true
    sudo systemctl start ollama 2>/dev/null || (nohup ollama serve > /dev/null 2>&1 &)
fi
sleep 3

# Pull a lightweight model for Jetson/low memory devices
echo "Pulling tinyllama model (fast, low memory)..."
ollama pull tinyllama:latest 2>/dev/null || echo "Model pull skipped or already present"

echo "Ollama setup complete!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ Ollama installed${NC}"

# ============================================
# STEP 8: Setup Node.js Frontend
# ============================================
echo -e "\n${YELLOW}➤ Step 8: Setting up frontend...${NC}"
ssh "$REMOTE_HOST" << REMOTE_SCRIPT
set -e
cd $NVIDIA_DIR/frontend

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install --legacy-peer-deps

echo "Frontend setup complete!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ Frontend setup complete${NC}"

# ============================================
# STEP 9: Create Environment Configuration
# ============================================
echo -e "\n${YELLOW}➤ Step 9: Creating environment configuration...${NC}"
ssh "$REMOTE_HOST" << REMOTE_SCRIPT
set -e
cd $NVIDIA_DIR

# Create or update .env file
API_MASTER_KEY="bh_$(python3 -c 'import secrets; print(secrets.token_hex(24))')"

cat > .env << ENVFILE
# Brutally Honest AI Configuration - Local Network Deployment
# Generated by deploy_local_nvidia.sh

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_MASTER_KEY=$API_MASTER_KEY

# Frontend Settings
FRONTEND_PORT=3001
PORT=3001
FRONTEND_HOST=0.0.0.0
API_BASE=http://localhost:8000

# Whisper Settings (use smaller model for Jetson)
WHISPER_MODEL=base
WHISPER_DEVICE=cuda

# Ollama Settings
OLLAMA_URL=http://localhost:11434
LLM_MODEL=tinyllama:latest

# Queue Settings
MAX_CONCURRENT_PROCESSING=2
GPU_CONCURRENT_LIMIT=1
MIN_GPU_MEMORY_GB=0.5

# Vector Database (local Qdrant)
QDRANT_PATH=./data/qdrant_storage

# Document Processing
DOCUMENT_UPLOAD_MAX_SIZE_MB=50
AUDIO_UPLOAD_MAX_SIZE_MB=100
ENVFILE

echo ""
echo "Generated API_MASTER_KEY: $API_MASTER_KEY"
echo "Save this key somewhere safe if you plan to call the API directly."
echo ""

echo "Environment file created!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ Environment configured${NC}"

# ============================================
# STEP 10: Create Systemd Services
# ============================================
echo -e "\n${YELLOW}➤ Step 10: Creating system services...${NC}"
ssh "$REMOTE_HOST" << REMOTE_SCRIPT
set -e

# Create API service
sudo tee /etc/systemd/system/brutally-honest-api.service > /dev/null << SERVICE
[Unit]
Description=Brutally Honest AI API Server
After=network.target ollama.service

[Service]
Type=simple
User=$NVIDIA_USER
WorkingDirectory=$NVIDIA_DIR
EnvironmentFile=$NVIDIA_DIR/.env
Environment=PATH=$NVIDIA_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$NVIDIA_DIR/venv/bin/python api_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Create Frontend service
sudo tee /etc/systemd/system/brutally-honest-frontend.service > /dev/null << SERVICE
[Unit]
Description=Brutally Honest AI Frontend
After=network.target brutally-honest-api.service

[Service]
Type=simple
User=$NVIDIA_USER
WorkingDirectory=$NVIDIA_DIR/frontend
EnvironmentFile=$NVIDIA_DIR/.env
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Reload systemd
sudo systemctl daemon-reload
echo "System services created!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ System services created${NC}"

# ============================================
# STEP 11: Start Services
# ============================================
echo -e "\n${YELLOW}➤ Step 11: Starting services...${NC}"
ssh "$REMOTE_HOST" << 'REMOTE_SCRIPT'
set -e

echo "Starting Brutally Honest AI services..."

# Enable and start services
sudo systemctl enable brutally-honest-api
sudo systemctl enable brutally-honest-frontend

sudo systemctl restart brutally-honest-api
sleep 5
sudo systemctl restart brutally-honest-frontend

# Check status
echo ""
echo "=== API Service Status ==="
sudo systemctl status brutally-honest-api --no-pager -l | head -15 || true

echo ""
echo "=== Frontend Service Status ==="
sudo systemctl status brutally-honest-frontend --no-pager -l | head -15 || true

echo ""
echo "Services started!"
REMOTE_SCRIPT
echo -e "${GREEN}✓ Services started${NC}"

# ============================================
# STEP 12: Upload Word Documents to Vector DB
# ============================================
echo -e "\n${YELLOW}➤ Step 12: Checking Word documents for vector database...${NC}"

# Get the API key from the remote server
API_KEY=$(ssh "$REMOTE_HOST" "cd $NVIDIA_DIR && source venv/bin/activate && python3 -c \"
import json
from pathlib import Path
keys_file = Path('.api_keys.json')
if keys_file.exists():
    keys = json.loads(keys_file.read_text())
    for k,v in keys.items():
        if v.get('permissions') == 'all':
            print(k)
            break
else:
    print('')
\" 2>/dev/null" || echo "")

if [ -n "$API_KEY" ]; then
    echo -e "${GREEN}Found API key for document upload${NC}"
    
    # Check if Word documents exist locally
    DOC1="$LOCAL_DIR/SAMENVATTING 2.0 AI BF INPUT ONTWERPPRINCIPES 15 DEC 2025.docx"
    DOC2="$LOCAL_DIR/Teamdynamiek en CEO 2.0 driving High Performing Teams 15 DEC 2025.docx"
    
    if [ -f "$DOC1" ] && [ -f "$DOC2" ]; then
        echo "Word documents found. They can be uploaded via the API:"
        echo ""
        echo "  Upload Command:"
        echo "  curl -X POST \"http://$NVIDIA_HOST:8000/documents/upload\" \\"
        echo "    -H \"Authorization: Bearer $API_KEY\" \\"
        echo "    -F \"file=@document.docx\" \\"
        echo "    -F \"category=knowledge_base\""
    fi
else
    echo -e "${YELLOW}API key not found yet (service may still be starting)${NC}"
fi

# ============================================
# FINAL SUMMARY
# ============================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ LOCAL NETWORK DEPLOYMENT COMPLETE!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}🌐 Access Your Brutally Honest AI:${NC}"
echo -e "  • Frontend:    ${GREEN}http://$NVIDIA_HOST:3001${NC}"
echo -e "  • API Docs:    ${GREEN}http://$NVIDIA_HOST:8000/docs${NC}"
echo -e "  • API Health:  ${GREEN}http://$NVIDIA_HOST:8000/health${NC}"
echo ""
echo -e "${BLUE}📋 Queue Management (Multi-Device):${NC}"
echo -e "  • Queue Stats: ${GREEN}http://$NVIDIA_HOST:8000/queue/stats${NC}"
echo -e "  • GPU Status:  ${GREEN}http://$NVIDIA_HOST:8000/gpu/status${NC}"
echo ""
echo -e "${BLUE}📤 Upload Endpoints:${NC}"
echo -e "  • Audio Queue: ${GREEN}POST http://$NVIDIA_HOST:8000/queue/upload/transcription${NC}"
echo -e "  • Doc Queue:   ${GREEN}POST http://$NVIDIA_HOST:8000/queue/upload/document${NC}"
echo ""
echo -e "${YELLOW}📖 Useful Commands (run on NVIDIA device):${NC}"
echo -e "  • Check API logs:      sudo journalctl -u brutally-honest-api -f"
echo -e "  • Check frontend logs: sudo journalctl -u brutally-honest-frontend -f"
echo -e "  • Restart API:         sudo systemctl restart brutally-honest-api"
echo -e "  • Restart frontend:    sudo systemctl restart brutally-honest-frontend"
echo -e "  • Check GPU:           nvidia-smi"
echo ""
echo -e "${YELLOW}📄 Upload Word Documents to Vector DB:${NC}"
echo -e "  curl -X POST \"http://$NVIDIA_HOST:8000/queue/upload/document\" \\"
echo -e "    -H \"Authorization: Bearer YOUR_API_KEY\" \\"
echo -e "    -F \"file=@'SAMENVATTING 2.0 AI BF INPUT ONTWERPPRINCIPES 15 DEC 2025.docx'\" \\"
echo -e "    -F \"category=knowledge_base\" \\"
echo -e "    -F \"tags=dutch,ai,design,principles\""
echo ""
echo -e "${GREEN}🎯 Enjoy your Brutally Honest AI on local network!${NC}"
