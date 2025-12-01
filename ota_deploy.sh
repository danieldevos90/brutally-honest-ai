#!/bin/bash

# Brutally Honest AI - OTA Quick Deploy Script
# Fast incremental deployment via SSH

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Default configuration
REMOTE_HOST="${REMOTE_HOST:-brutally@brutallyhonest.io}"
REMOTE_DIR="${REMOTE_DIR:-/home/brutally/brutally-honest-ai}"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

# SSH options (for remote access)
SSH_PORT="${SSH_PORT:-22}"
SSH_KEY="${SSH_KEY:-}"
JUMP_HOST="${JUMP_HOST:-}"
TAILSCALE_HOST="${TAILSCALE_HOST:-}"
CLOUDFLARE_HOST="${CLOUDFLARE_HOST:-}"

# Parse arguments
DEPLOY_TYPE="quick"
RESTART_ONLY=false
SHOW_LOGS=false
SHOW_STATUS=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--full)
            DEPLOY_TYPE="full"
            shift
            ;;
        -r|--restart)
            RESTART_ONLY=true
            shift
            ;;
        -l|--logs)
            SHOW_LOGS=true
            shift
            ;;
        -s|--status)
            SHOW_STATUS=true
            shift
            ;;
        -n|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--host)
            REMOTE_HOST="$2"
            shift 2
            ;;
        -p|--port)
            SSH_PORT="$2"
            shift 2
            ;;
        -i|--identity)
            SSH_KEY="$2"
            shift 2
            ;;
        -J|--jump)
            JUMP_HOST="$2"
            shift 2
            ;;
        --tailscale)
            TAILSCALE_HOST="$2"
            shift 2
            ;;
        --cloudflare)
            CLOUDFLARE_HOST="$2"
            shift 2
            ;;
        --help)
            echo "Brutally Honest AI - OTA Deploy"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Deployment Options:"
            echo "  -f, --full       Full deployment (reinstall dependencies)"
            echo "  -r, --restart    Restart services only (no file sync)"
            echo "  -n, --dry-run    Show what would be synced without doing it"
            echo ""
            echo "Information:"
            echo "  -s, --status     Show remote system status"
            echo "  -l, --logs       Show recent service logs"
            echo "  --help           Show this help"
            echo ""
            echo "Connection Options:"
            echo "  -h, --host       Set remote host (user@host)"
            echo "  -p, --port       SSH port (default: 22)"
            echo "  -i, --identity   SSH key file path"
            echo "  -J, --jump       Jump host for ProxyJump (user@bastion)"
            echo "  --tailscale      Use Tailscale hostname (e.g., brutally-jetson)"
            echo "  --cloudflare     Use Cloudflare tunnel hostname"
            echo ""
            echo "Environment variables:"
            echo "  REMOTE_HOST      Remote host (default: brutally@brutallyhonest.io)"
            echo "  REMOTE_DIR       Remote directory"
            echo "  SSH_PORT         SSH port (default: 22)"
            echo "  SSH_KEY          Path to SSH key"
            echo "  JUMP_HOST        Jump/bastion host"
            echo "  TAILSCALE_HOST   Tailscale machine name"
            echo "  CLOUDFLARE_HOST  Cloudflare tunnel hostname"
            echo ""
            echo "Examples:"
            echo "  # Local network deploy"
            echo "  ./ota_deploy.sh"
            echo ""
            echo "  # Deploy via custom port (port forwarding)"
            echo "  ./ota_deploy.sh -h user@myhost.duckdns.org -p 2222"
            echo ""
            echo "  # Deploy via Tailscale"
            echo "  ./ota_deploy.sh --tailscale brutally-jetson"
            echo ""
            echo "  # Deploy via jump host"
            echo "  ./ota_deploy.sh -J user@bastion.com -h user@internal-ip"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Build SSH options
SSH_OPTS="-o ConnectTimeout=30 -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

if [ -n "$SSH_KEY" ]; then
    SSH_OPTS="$SSH_OPTS -i $SSH_KEY"
fi

if [ "$SSH_PORT" != "22" ]; then
    SSH_OPTS="$SSH_OPTS -p $SSH_PORT"
fi

if [ -n "$JUMP_HOST" ]; then
    SSH_OPTS="$SSH_OPTS -J $JUMP_HOST"
fi

# Handle Tailscale
if [ -n "$TAILSCALE_HOST" ]; then
    USER=$(echo "$REMOTE_HOST" | cut -d'@' -f1)
    REMOTE_HOST="${USER}@${TAILSCALE_HOST}"
    echo -e "${CYAN}Using Tailscale: ${REMOTE_HOST}${NC}"
fi

# Handle Cloudflare Tunnel
if [ -n "$CLOUDFLARE_HOST" ]; then
    USER=$(echo "$REMOTE_HOST" | cut -d'@' -f1)
    REMOTE_HOST="${USER}@${CLOUDFLARE_HOST}"
    SSH_OPTS="$SSH_OPTS -o ProxyCommand='cloudflared access ssh --hostname ${CLOUDFLARE_HOST}'"
    echo -e "${CYAN}Using Cloudflare Tunnel: ${CLOUDFLARE_HOST}${NC}"
fi

# Banner
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║      🚀 BRUTALLY HONEST AI - OTA DEPLOY                       ║"
echo "║      Target: ${REMOTE_HOST}                          ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Test SSH connection
test_ssh() {
    echo -e "${YELLOW}➤ Testing SSH connection to ${REMOTE_HOST}...${NC}"
    if ! ssh $SSH_OPTS "$REMOTE_HOST" "echo 'connected'" >/dev/null 2>&1; then
        echo -e "${RED}✗ SSH connection failed!${NC}"
        echo -e "${YELLOW}Troubleshooting:${NC}"
        echo -e "  1. Make sure SSH key is configured: ssh-copy-id $REMOTE_HOST"
        echo -e "  2. If using Tailscale, ensure both machines are connected"
        echo -e "  3. If using port forwarding, check the port: -p $SSH_PORT"
        echo -e "  4. If using Cloudflare, ensure cloudflared is installed"
        exit 1
    fi
    echo -e "${GREEN}✓ SSH connection OK${NC}"
}

# Show remote system status
show_status() {
    echo -e "\n${CYAN}═══ REMOTE SYSTEM STATUS ═══${NC}\n"
    
    echo -e "${BLUE}System Info:${NC}"
    ssh $SSH_OPTS "$REMOTE_HOST" "hostname && uname -r && uptime -p"
    
    echo -e "\n${BLUE}GPU:${NC}"
    ssh $SSH_OPTS "$REMOTE_HOST" "nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader 2>/dev/null || echo 'No GPU detected'"
    
    echo -e "\n${BLUE}Memory:${NC}"
    ssh $SSH_OPTS "$REMOTE_HOST" "free -h | grep -E 'Mem|Swap'"
    
    echo -e "\n${BLUE}Disk:${NC}"
    ssh $SSH_OPTS "$REMOTE_HOST" "df -h $REMOTE_DIR 2>/dev/null | tail -1"
    
    echo -e "\n${BLUE}Services:${NC}"
    ssh $SSH_OPTS "$REMOTE_HOST" "systemctl is-active brutally-honest-api 2>/dev/null && echo '  API: Running' || echo '  API: Stopped'"
    ssh $SSH_OPTS "$REMOTE_HOST" "systemctl is-active brutally-honest-frontend 2>/dev/null && echo '  Frontend: Running' || echo '  Frontend: Stopped'"
    ssh $SSH_OPTS "$REMOTE_HOST" "pgrep ollama >/dev/null && echo '  Ollama: Running' || echo '  Ollama: Stopped'"
    
    echo -e "\n${BLUE}Last Deployment:${NC}"
    ssh $SSH_OPTS "$REMOTE_HOST" "stat -c '%y' $REMOTE_DIR/.last_deployment 2>/dev/null || echo '  Never deployed via OTA'"
}

# Show service logs
show_logs() {
    echo -e "\n${CYAN}═══ RECENT SERVICE LOGS ═══${NC}\n"
    
    echo -e "${BLUE}--- API Server Logs ---${NC}"
    ssh $SSH_OPTS "$REMOTE_HOST" "sudo journalctl -u brutally-honest-api -n 30 --no-pager 2>/dev/null || echo 'Could not get API logs'"
    
    echo -e "\n${BLUE}--- Frontend Logs ---${NC}"
    ssh $SSH_OPTS "$REMOTE_HOST" "sudo journalctl -u brutally-honest-frontend -n 20 --no-pager 2>/dev/null || echo 'Could not get frontend logs'"
}

# Sync files using rsync
sync_files() {
    echo -e "\n${YELLOW}➤ Syncing files to remote...${NC}"
    
    RSYNC_OPTS="-avz --progress --delete"
    
    if [ "$DRY_RUN" = true ]; then
        RSYNC_OPTS="$RSYNC_OPTS --dry-run"
        echo -e "${MAGENTA}(Dry run - no files will be transferred)${NC}"
    fi
    
    # Build rsync SSH command with all options
    RSYNC_SSH="ssh $SSH_OPTS"
    
    rsync $RSYNC_OPTS \
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
        --exclude '.api_keys.json' \
        --exclude '*.log' \
        --exclude '.DS_Store' \
        --exclude 'installer/' \
        --exclude '*.dmg' \
        -e "$RSYNC_SSH" \
        "$LOCAL_DIR/" "$REMOTE_HOST:$REMOTE_DIR/"
    
    echo -e "${GREEN}✓ Files synced${NC}"
}

# Install Python dependencies
install_python_deps() {
    echo -e "\n${YELLOW}➤ Installing Python dependencies...${NC}"
    
    ssh $SSH_OPTS "$REMOTE_HOST" "cd $REMOTE_DIR && \
        if [ ! -d 'venv' ]; then python3 -m venv venv; fi && \
        source venv/bin/activate && \
        pip install --upgrade pip wheel setuptools && \
        if [ -f /etc/nv_tegra_release ]; then \
            pip install -r requirements_jetson.txt --no-cache-dir; \
        else \
            pip install -r requirements.txt --no-cache-dir; \
        fi"

    echo -e "${GREEN}✓ Python dependencies installed${NC}"
}

# Install Node.js dependencies
install_node_deps() {
    echo -e "\n${YELLOW}➤ Installing Node.js dependencies...${NC}"
    
    ssh $SSH_OPTS "$REMOTE_HOST" "cd $REMOTE_DIR/frontend && npm install"
    
    echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
}

# Restart services
restart_services() {
    echo -e "\n${YELLOW}➤ Restarting services...${NC}"
    
    ssh $SSH_OPTS "$REMOTE_HOST" "sudo systemctl stop brutally-honest-api 2>/dev/null || true && \
        sudo systemctl stop brutally-honest-frontend 2>/dev/null || true && \
        sleep 2 && \
        sudo systemctl start brutally-honest-api && \
        sleep 2 && \
        sudo systemctl start brutally-honest-frontend && \
        echo '' && echo 'Service Status:' && \
        (systemctl is-active brutally-honest-api 2>/dev/null && echo '  ✓ API: Running' || echo '  ✗ API: Not running') && \
        (systemctl is-active brutally-honest-frontend 2>/dev/null && echo '  ✓ Frontend: Running' || echo '  ✗ Frontend: Not running')"

    echo -e "${GREEN}✓ Services restarted${NC}"
}

# Mark deployment
mark_deployment() {
    ssh $SSH_OPTS "$REMOTE_HOST" "touch $REMOTE_DIR/.last_deployment"
}

# Main execution
test_ssh

if [ "$SHOW_STATUS" = true ]; then
    show_status
    exit 0
fi

if [ "$SHOW_LOGS" = true ]; then
    show_logs
    exit 0
fi

if [ "$RESTART_ONLY" = true ]; then
    restart_services
    exit 0
fi

# Quick deploy
if [ "$DEPLOY_TYPE" = "quick" ]; then
    echo -e "\n${MAGENTA}=== QUICK DEPLOY ===${NC}"
    
    sync_files
    
    if [ "$DRY_RUN" = false ]; then
        restart_services
        mark_deployment
    fi
fi

# Full deploy
if [ "$DEPLOY_TYPE" = "full" ]; then
    echo -e "\n${MAGENTA}=== FULL DEPLOY ===${NC}"
    
    # Create backup
    echo -e "\n${YELLOW}➤ Creating backup...${NC}"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    ssh $SSH_OPTS "$REMOTE_HOST" "cp -r $REMOTE_DIR ${REMOTE_DIR}_backup_${TIMESTAMP} 2>/dev/null || mkdir -p $REMOTE_DIR"
    echo -e "${GREEN}✓ Backup created${NC}"
    
    # Stop services first for full deploy
    echo -e "\n${YELLOW}➤ Stopping services for full deploy...${NC}"
    ssh $SSH_OPTS "$REMOTE_HOST" "sudo systemctl stop brutally-honest-api brutally-honest-frontend 2>/dev/null || true"
    
    sync_files
    
    if [ "$DRY_RUN" = false ]; then
        install_python_deps
        install_node_deps
        restart_services
        mark_deployment
    fi
fi

# Final summary
if [ "$DRY_RUN" = false ]; then
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ OTA DEPLOYMENT COMPLETE!${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Access your Brutally Honest AI:${NC}"
    
    # Extract IP from remote host
    REMOTE_IP=$(echo "$REMOTE_HOST" | cut -d'@' -f2)
    echo -e "  • Frontend:  ${GREEN}http://${REMOTE_IP}:3001${NC}"
    echo -e "  • API Docs:  ${GREEN}http://${REMOTE_IP}:8000/docs${NC}"
    echo ""
else
    echo -e "\n${YELLOW}Dry run complete - no changes made${NC}"
fi

