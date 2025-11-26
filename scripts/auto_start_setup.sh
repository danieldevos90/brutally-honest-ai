#!/bin/bash
# ============================================
# Brutally Honest AI - Auto-Start Setup Script
# Run this ON the reComputer J4011 to ensure:
# 1. All services start automatically on boot
# 2. Network auto-reconnects when location changes
# 3. Services auto-restart if they fail
# ============================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Brutally Honest AI - Auto-Start Setup         ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Don't run as root. Run as regular user with sudo access.${NC}"
    exit 1
fi

USER_HOME="/home/brutally"
PROJECT_DIR="$USER_HOME/brutally-honest-ai"

echo -e "${BLUE}📁 Project directory: $PROJECT_DIR${NC}"
echo ""

# ============================================
# STEP 1: Create/Update API Service
# ============================================
echo -e "${YELLOW}[1/6] Setting up API Service...${NC}"

sudo tee /etc/systemd/system/brutally-honest-api.service > /dev/null << 'EOF'
[Unit]
Description=Brutally Honest AI API Server
After=network-online.target ollama.service
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
User=brutally
WorkingDirectory=/home/brutally/brutally-honest-ai
Environment=PATH=/home/brutally/brutally-honest-ai/venv/bin:/usr/bin
Environment=PYTHONPATH=/home/brutally/brutally-honest-ai:/home/brutally/brutally-honest-ai/src
Environment=API_MASTER_KEY=bh_brutallyhonest_master_key_2024
EnvironmentFile=-/home/brutally/brutally-honest-ai/.env
ExecStart=/home/brutally/brutally-honest-ai/venv/bin/python api_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ API service configured${NC}"

# ============================================
# STEP 2: Create/Update Frontend Service
# ============================================
echo -e "${YELLOW}[2/6] Setting up Frontend Service...${NC}"

sudo tee /etc/systemd/system/brutally-honest-frontend.service > /dev/null << 'EOF'
[Unit]
Description=Brutally Honest AI Frontend
After=network-online.target brutally-honest-api.service
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
User=brutally
WorkingDirectory=/home/brutally/brutally-honest-ai/frontend
Environment=PATH=/usr/bin:/usr/local/bin
Environment=NODE_ENV=production
ExecStart=/usr/bin/node server.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Frontend service configured${NC}"

# ============================================
# STEP 3: Create/Update Ollama Service
# ============================================
echo -e "${YELLOW}[3/6] Setting up Ollama Service...${NC}"

sudo tee /etc/systemd/system/ollama.service > /dev/null << 'EOF'
[Unit]
Description=Ollama LLM Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=brutally
ExecStart=/usr/local/bin/ollama serve
Restart=always
RestartSec=10
Environment=OLLAMA_HOST=0.0.0.0:11434
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Ollama service configured${NC}"

# ============================================
# STEP 4: Create Network Reconnection Service
# ============================================
echo -e "${YELLOW}[4/6] Setting up Network Reconnection Service...${NC}"

# Create the network watchdog script
sudo tee /usr/local/bin/brutally-network-watchdog.sh > /dev/null << 'EOF'
#!/bin/bash
# Network watchdog script for Brutally Honest AI
# Monitors network connectivity and restarts services when connection is restored

LOG_FILE="/var/log/brutally-network-watchdog.log"
CHECK_INTERVAL=30
INTERNET_CHECK_HOST="1.1.1.1"
CLOUDFLARE_CHECK_URL="https://api.cloudflare.com/cdn-cgi/trace"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

check_internet() {
    ping -c 1 -W 5 "$INTERNET_CHECK_HOST" > /dev/null 2>&1
    return $?
}

check_cloudflared() {
    systemctl is-active --quiet cloudflared
    return $?
}

restart_cloudflared() {
    log "🔄 Restarting cloudflared service..."
    systemctl restart cloudflared
    sleep 5
    if check_cloudflared; then
        log "✅ cloudflared restarted successfully"
        return 0
    else
        log "❌ cloudflared failed to restart"
        return 1
    fi
}

# Track previous state
LAST_INTERNET_STATE="unknown"
CONSECUTIVE_FAILURES=0

log "🚀 Starting Brutally Honest Network Watchdog"

while true; do
    if check_internet; then
        if [ "$LAST_INTERNET_STATE" != "connected" ]; then
            log "🌐 Internet connection established"
            
            # Wait a moment for network to stabilize
            sleep 5
            
            # Check and restart cloudflared if needed
            if ! check_cloudflared; then
                log "⚠️ cloudflared not running, starting..."
                restart_cloudflared
            else
                # Even if running, restart to update connection
                log "🔄 Refreshing cloudflared connection after network change..."
                restart_cloudflared
            fi
            
            LAST_INTERNET_STATE="connected"
        fi
        CONSECUTIVE_FAILURES=0
    else
        CONSECUTIVE_FAILURES=$((CONSECUTIVE_FAILURES + 1))
        if [ "$LAST_INTERNET_STATE" != "disconnected" ] || [ $((CONSECUTIVE_FAILURES % 10)) -eq 0 ]; then
            log "⚠️ No internet connection (attempt $CONSECUTIVE_FAILURES)"
        fi
        LAST_INTERNET_STATE="disconnected"
    fi
    
    sleep "$CHECK_INTERVAL"
done
EOF

sudo chmod +x /usr/local/bin/brutally-network-watchdog.sh

# Create systemd service for network watchdog
sudo tee /etc/systemd/system/brutally-network-watchdog.service > /dev/null << 'EOF'
[Unit]
Description=Brutally Honest AI Network Watchdog
After=network.target
Wants=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/brutally-network-watchdog.sh
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✅ Network watchdog service configured${NC}"

# ============================================
# STEP 5: Setup NetworkManager for Auto-Connect
# ============================================
echo -e "${YELLOW}[5/6] Configuring NetworkManager for auto-connect...${NC}"

# Create NetworkManager dispatcher script for automatic reconnection
sudo tee /etc/NetworkManager/dispatcher.d/99-brutally-reconnect > /dev/null << 'EOF'
#!/bin/bash
# NetworkManager dispatcher script
# Automatically restarts cloudflared when network connection changes

INTERFACE="$1"
STATUS="$2"
LOG_FILE="/var/log/brutally-network-watchdog.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - [NM-Dispatch] $1" >> "$LOG_FILE"
}

case "$STATUS" in
    up|dhcp4-change|dhcp6-change)
        log "Network interface $INTERFACE is up/changed - restarting cloudflared"
        sleep 5
        systemctl restart cloudflared
        ;;
    down|pre-down)
        log "Network interface $INTERFACE going down"
        ;;
esac

exit 0
EOF

sudo chmod +x /etc/NetworkManager/dispatcher.d/99-brutally-reconnect

# Configure NetworkManager to auto-connect to known networks
# This creates a connection profile that auto-connects
if command -v nmcli &> /dev/null; then
    echo -e "${BLUE}   Configuring NetworkManager auto-connect...${NC}"
    # Enable auto-connect for ethernet
    nmcli general logging level DEBUG domains ALL 2>/dev/null || true
    nmcli connection modify "$(nmcli -t -f NAME con show --active | head -1)" connection.autoconnect yes 2>/dev/null || true
fi

echo -e "${GREEN}✅ NetworkManager auto-connect configured${NC}"

# ============================================
# STEP 6: Enable and Start All Services
# ============================================
echo -e "${YELLOW}[6/6] Enabling and starting all services...${NC}"

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable all services to start on boot
sudo systemctl enable ollama.service
sudo systemctl enable brutally-honest-api.service
sudo systemctl enable brutally-honest-frontend.service
sudo systemctl enable cloudflared.service
sudo systemctl enable brutally-network-watchdog.service

echo -e "${GREEN}✅ All services enabled for auto-start${NC}"

# Start/restart all services
echo -e "${BLUE}   Starting services...${NC}"
sudo systemctl restart ollama.service
sleep 3
sudo systemctl restart brutally-honest-api.service
sleep 2
sudo systemctl restart brutally-honest-frontend.service
sleep 2
sudo systemctl restart cloudflared.service
sudo systemctl restart brutally-network-watchdog.service

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ Auto-Start Setup Complete!                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services Status:${NC}"
echo ""

# Show status of all services
for service in ollama brutally-honest-api brutally-honest-frontend cloudflared brutally-network-watchdog; do
    STATUS=$(systemctl is-active $service.service 2>/dev/null || echo "not-found")
    ENABLED=$(systemctl is-enabled $service.service 2>/dev/null || echo "not-found")
    
    if [ "$STATUS" == "active" ]; then
        STATUS_COLOR="${GREEN}●${NC}"
    else
        STATUS_COLOR="${RED}○${NC}"
    fi
    
    if [ "$ENABLED" == "enabled" ]; then
        ENABLED_TEXT="${GREEN}enabled${NC}"
    else
        ENABLED_TEXT="${YELLOW}disabled${NC}"
    fi
    
    printf "  ${STATUS_COLOR} %-30s [%s] %s\n" "$service" "$ENABLED_TEXT" "$STATUS"
done

echo ""
echo -e "${BLUE}What this setup provides:${NC}"
echo "  🚀 All services auto-start on boot"
echo "  🔄 Services auto-restart if they crash"
echo "  🌐 Network watchdog monitors connectivity"
echo "  📡 cloudflared auto-reconnects when network changes"
echo "  🔗 NetworkManager auto-connects to known WiFi networks"
echo ""
echo -e "${YELLOW}View logs:${NC}"
echo "  sudo journalctl -u brutally-honest-api -f"
echo "  sudo journalctl -u brutally-honest-frontend -f"
echo "  sudo journalctl -u cloudflared -f"
echo "  tail -f /var/log/brutally-network-watchdog.log"
echo ""
echo -e "${YELLOW}Manual controls:${NC}"
echo "  sudo systemctl restart brutally-honest-api"
echo "  sudo systemctl restart brutally-honest-frontend"
echo "  sudo systemctl restart cloudflared"
echo ""

