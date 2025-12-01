#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# BRUTALLY HONEST AI - PRODUCTION DEPLOYMENT SCRIPT
# ═══════════════════════════════════════════════════════════════════════════════
# 
# Usage:
#   ./deploy.sh                    # Quick deploy (sync + restart)
#   ./deploy.sh --full             # Full deploy (reinstall deps)
#   ./deploy.sh --release v1.2.3   # Create release and deploy
#   ./deploy.sh --rollback         # Rollback to previous version
#   ./deploy.sh --status           # Check remote status
#   ./deploy.sh --logs             # View remote logs
#
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Remote server settings
REMOTE_HOST="${REMOTE_HOST:-brutally@192.168.2.33}"
REMOTE_DIR="${REMOTE_DIR:-/home/brutally/brutally-honest-ai}"
SUDO_PASS="${SUDO_PASS:-Welcome12!}"

# External access (when not on local network)
EXTERNAL_HOST="${EXTERNAL_HOST:-brutally@brutallyhonest.io}"
SSH_PORT="${SSH_PORT:-22}"

# Local settings
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"
VERSION_FILE="$LOCAL_DIR/VERSION"
CHANGELOG_FILE="$LOCAL_DIR/CHANGELOG.md"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m'

# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "\n${CYAN}━━━ $1 ━━━${NC}"; }

# Get current version from VERSION file or git
get_version() {
    if [ -f "$VERSION_FILE" ]; then
        cat "$VERSION_FILE"
    else
        git describe --tags --always 2>/dev/null || echo "0.0.0-dev"
    fi
}

# Get git info
get_git_info() {
    local branch=$(git branch --show-current 2>/dev/null || echo "unknown")
    local commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
    local dirty=""
    if ! git diff --quiet 2>/dev/null; then
        dirty="-dirty"
    fi
    echo "${branch}@${commit}${dirty}"
}

# Run remote command with sudo (passwordless for systemctl/fuser)
remote_sudo() {
    # Try passwordless first (for allowed commands), fall back to password
    if ssh "$REMOTE_HOST" "sudo -n $1 2>/dev/null"; then
        return 0
    else
        ssh "$REMOTE_HOST" "echo '$SUDO_PASS' | sudo -S $1 2>/dev/null"
    fi
}

# Run remote command
remote_exec() {
    ssh "$REMOTE_HOST" "$1"
}

# Check if we can reach the server
check_connection() {
    log_step "Checking Connection"
    
    # Try local first
    if ssh -o ConnectTimeout=5 -o BatchMode=yes "$REMOTE_HOST" "echo 'ok'" >/dev/null 2>&1; then
        log_success "Connected to $REMOTE_HOST (local network)"
        return 0
    fi
    
    # Try external
    if ssh -o ConnectTimeout=10 -o BatchMode=yes -p "$SSH_PORT" "$EXTERNAL_HOST" "echo 'ok'" >/dev/null 2>&1; then
        REMOTE_HOST="$EXTERNAL_HOST"
        log_success "Connected to $EXTERNAL_HOST (external)"
        return 0
    fi
    
    log_error "Cannot connect to server"
    echo -e "${YELLOW}Tried:${NC}"
    echo "  - $REMOTE_HOST (local)"
    echo "  - $EXTERNAL_HOST (external)"
    echo ""
    echo -e "${YELLOW}Setup SSH key:${NC}"
    echo "  ssh-copy-id $REMOTE_HOST"
    return 1
}

# ─────────────────────────────────────────────────────────────────────────────
# VERSION CONTROL
# ─────────────────────────────────────────────────────────────────────────────

# Create a new release
create_release() {
    local version="$1"
    
    log_step "Creating Release $version"
    
    # Validate version format
    if ! [[ "$version" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$ ]]; then
        log_error "Invalid version format. Use: v1.2.3 or v1.2.3-beta"
        exit 1
    fi
    
    # Remove 'v' prefix if present for VERSION file
    local clean_version="${version#v}"
    
    # Check for uncommitted changes
    if ! git diff --quiet 2>/dev/null; then
        log_warn "You have uncommitted changes"
        read -p "Commit them now? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git add -A
            git commit -m "Release $version"
        else
            log_error "Cannot create release with uncommitted changes"
            exit 1
        fi
    fi
    
    # Update VERSION file
    echo "$clean_version" > "$VERSION_FILE"
    log_info "Updated VERSION to $clean_version"
    
    # Update CHANGELOG if it exists
    if [ -f "$CHANGELOG_FILE" ]; then
        local date=$(date +%Y-%m-%d)
        local temp_file=$(mktemp)
        
        # Add new version header
        echo "## [$clean_version] - $date" > "$temp_file"
        echo "" >> "$temp_file"
        
        # Get commits since last tag
        local last_tag=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
        if [ -n "$last_tag" ]; then
            git log "$last_tag"..HEAD --pretty=format:"- %s" >> "$temp_file"
        else
            git log --pretty=format:"- %s" -10 >> "$temp_file"
        fi
        echo -e "\n" >> "$temp_file"
        
        # Append existing changelog
        if [ -f "$CHANGELOG_FILE" ]; then
            cat "$CHANGELOG_FILE" >> "$temp_file"
        fi
        
        mv "$temp_file" "$CHANGELOG_FILE"
        log_info "Updated CHANGELOG.md"
    fi
    
    # Commit version bump
    git add VERSION CHANGELOG.md 2>/dev/null || true
    git commit -m "Bump version to $version" 2>/dev/null || true
    
    # Create git tag
    git tag -a "$version" -m "Release $version"
    log_success "Created git tag: $version"
    
    # Push to remote
    read -p "Push to remote? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        git push origin main --tags
        log_success "Pushed to remote"
    fi
    
    echo "$version"
}

# ─────────────────────────────────────────────────────────────────────────────
# DEPLOYMENT FUNCTIONS  
# ─────────────────────────────────────────────────────────────────────────────

# Pre-deploy checks
pre_deploy_checks() {
    log_step "Pre-Deploy Checks"
    
    local errors=0
    
    # Check git status
    if ! git diff --quiet 2>/dev/null; then
        log_warn "Uncommitted changes detected"
        git status --short
        echo ""
    fi
    
    # Check required files
    for file in api_server.py frontend/server.js requirements.txt; do
        if [ ! -f "$LOCAL_DIR/$file" ]; then
            log_error "Missing required file: $file"
            ((errors++))
        fi
    done
    
    # Check syntax (Python)
    if command -v python3 &>/dev/null; then
        if ! python3 -m py_compile "$LOCAL_DIR/api_server.py" 2>/dev/null; then
            log_error "Python syntax error in api_server.py"
            ((errors++))
        else
            log_success "Python syntax OK"
        fi
    fi
    
    # Check syntax (Node.js)
    if command -v node &>/dev/null; then
        if ! node --check "$LOCAL_DIR/frontend/server.js" 2>/dev/null; then
            log_error "Node.js syntax error in frontend/server.js"
            ((errors++))
        else
            log_success "Node.js syntax OK"
        fi
    fi
    
    if [ $errors -gt 0 ]; then
        log_error "Pre-deploy checks failed with $errors error(s)"
        exit 1
    fi
    
    log_success "All pre-deploy checks passed"
}

# Sync files to remote
sync_files() {
    log_step "Syncing Files"
    
    local version=$(get_version)
    local git_info=$(get_git_info)
    
    log_info "Deploying version: $version ($git_info)"
    
    rsync -avz --progress --delete \
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
        --exclude 'recordings/*' \
        --exclude 'frontend/data/*' \
        "$LOCAL_DIR/" "$REMOTE_HOST:$REMOTE_DIR/"
    
    # Write deployment info
    remote_exec "echo '{\"version\": \"$version\", \"git\": \"$git_info\", \"deployed_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"deployed_by\": \"$(whoami)\"}' > $REMOTE_DIR/.deployment_info.json"
    
    log_success "Files synced"
}

# Install dependencies
install_deps() {
    log_step "Installing Dependencies"
    
    log_info "Installing Python dependencies..."
    remote_exec "cd $REMOTE_DIR && source venv/bin/activate && pip install -r requirements.txt --quiet"
    
    log_info "Installing Node.js dependencies..."
    remote_exec "cd $REMOTE_DIR/frontend && npm install --silent"
    
    log_success "Dependencies installed"
}

# Restart services
restart_services() {
    log_step "Restarting Services"
    
    # Kill any zombie processes on ports
    remote_sudo "fuser -k 3001/tcp 2>/dev/null || true"
    remote_sudo "fuser -k 3002/tcp 2>/dev/null || true"
    sleep 1
    
    # Restart services
    remote_sudo "systemctl restart brutally-honest-api"
    sleep 2
    remote_sudo "systemctl restart brutally-honest-frontend"
    sleep 3
    
    log_success "Services restarted"
}

# Health check
health_check() {
    log_step "Health Check"
    
    local retries=5
    local wait=3
    
    # Check API
    for i in $(seq 1 $retries); do
        if remote_exec "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/status" | grep -q "200"; then
            log_success "API health check passed"
            break
        fi
        if [ $i -eq $retries ]; then
            log_error "API health check failed after $retries attempts"
            return 1
        fi
        log_info "Waiting for API... ($i/$retries)"
        sleep $wait
    done
    
    # Check Frontend (302 redirect to login is OK)
    for i in $(seq 1 $retries); do
        local frontend_code=$(remote_exec "curl -s -o /dev/null -w '%{http_code}' http://localhost:3001/")
        if [[ "$frontend_code" =~ ^(200|302)$ ]]; then
            log_success "Frontend health check passed (HTTP $frontend_code)"
            break
        fi
        if [ $i -eq $retries ]; then
            log_error "Frontend health check failed after $retries attempts"
            return 1
        fi
        log_info "Waiting for Frontend... ($i/$retries)"
        sleep $wait
    done
    
    # Check service status
    local api_status=$(remote_exec "systemctl is-active brutally-honest-api")
    local frontend_status=$(remote_exec "systemctl is-active brutally-honest-frontend")
    
    echo ""
    echo -e "${BOLD}Service Status:${NC}"
    echo -e "  API:      ${api_status}"
    echo -e "  Frontend: ${frontend_status}"
    
    return 0
}

# Create backup before deploy
create_backup() {
    log_step "Creating Backup"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="${REMOTE_DIR}_backup_${timestamp}"
    
    remote_exec "cp -r $REMOTE_DIR $backup_dir 2>/dev/null || mkdir -p $REMOTE_DIR"
    
    # Keep only last 5 backups
    remote_exec "ls -dt ${REMOTE_DIR}_backup_* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true"
    
    log_success "Backup created: $backup_dir"
}

# Rollback to previous version
rollback() {
    log_step "Rolling Back"
    
    # Find latest backup
    local backup=$(remote_exec "ls -dt ${REMOTE_DIR}_backup_* 2>/dev/null | head -1")
    
    if [ -z "$backup" ]; then
        log_error "No backup found to rollback to"
        exit 1
    fi
    
    log_info "Rolling back to: $backup"
    
    # Stop services
    remote_sudo "systemctl stop brutally-honest-api brutally-honest-frontend"
    
    # Swap directories
    remote_exec "mv $REMOTE_DIR ${REMOTE_DIR}_rollback_$(date +%s)"
    remote_exec "mv $backup $REMOTE_DIR"
    
    # Restart services
    restart_services
    
    log_success "Rollback complete"
    
    # Show new version
    local version=$(remote_exec "cat $REMOTE_DIR/VERSION 2>/dev/null || echo 'unknown'")
    log_info "Now running version: $version"
}

# Show remote status
show_status() {
    log_step "Remote System Status"
    
    echo -e "\n${BOLD}System:${NC}"
    remote_exec "hostname && uname -r"
    
    echo -e "\n${BOLD}Deployment:${NC}"
    remote_exec "cat $REMOTE_DIR/.deployment_info.json 2>/dev/null | python3 -m json.tool 2>/dev/null || echo 'No deployment info'"
    
    echo -e "\n${BOLD}Services:${NC}"
    echo -n "  API:      " && remote_exec "systemctl is-active brutally-honest-api"
    echo -n "  Frontend: " && remote_exec "systemctl is-active brutally-honest-frontend"
    echo -n "  Ollama:   " && remote_exec "pgrep ollama >/dev/null && echo 'active' || echo 'inactive'"
    
    echo -e "\n${BOLD}Resources:${NC}"
    remote_exec "free -h | grep Mem | awk '{print \"  Memory: \" \$3 \"/\" \$2}'"
    remote_exec "df -h $REMOTE_DIR | tail -1 | awk '{print \"  Disk:   \" \$3 \"/\" \$2 \" (\" \$5 \" used)\"}'"
    
    echo -e "\n${BOLD}Ports:${NC}"
    remote_exec "ss -tlnp | grep -E '8000|3001|3002' | awk '{print \"  \" \$4}'"
    
    echo -e "\n${BOLD}Last Logs:${NC}"
    remote_exec "journalctl -u brutally-honest-api -n 3 --no-pager 2>/dev/null | tail -3" || true
}

# Show logs
show_logs() {
    local service="${1:-api}"
    local lines="${2:-50}"
    
    log_step "Logs: brutally-honest-$service"
    
    remote_exec "journalctl -u brutally-honest-$service -n $lines --no-pager"
}

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

print_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║   ____  ____  _   _ _____  _    _    _   __   __                  ║"
    echo "║  | __ )|  _ \| | | |_   _|/ \  | |  | |  \ \ / /                  ║"
    echo "║  |  _ \| |_) | | | | | | / _ \ | |  | |   \ V /                   ║"
    echo "║  | |_) |  _ <| |_| | | |/ ___ \| |__| |___ | |                    ║"
    echo "║  |____/|_| \_\\\\___/  |_/_/   \_\_____\_____|_|   DEPLOY           ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "  Version: ${BOLD}$(get_version)${NC} ($(get_git_info))"
    echo -e "  Target:  ${BOLD}$REMOTE_HOST${NC}"
    echo ""
}

main() {
    cd "$LOCAL_DIR"
    
    # Parse arguments
    local deploy_type="quick"
    local release_version=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --full|-f)
                deploy_type="full"
                shift
                ;;
            --release|-r)
                deploy_type="release"
                release_version="$2"
                shift 2
                ;;
            --rollback)
                deploy_type="rollback"
                shift
                ;;
            --status|-s)
                deploy_type="status"
                shift
                ;;
            --logs|-l)
                deploy_type="logs"
                shift
                ;;
            --logs-frontend)
                deploy_type="logs-frontend"
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --full, -f           Full deployment (reinstall dependencies)"
                echo "  --release VERSION    Create release and deploy (e.g., --release v1.2.3)"
                echo "  --rollback           Rollback to previous version"
                echo "  --status, -s         Show remote system status"
                echo "  --logs, -l           Show API logs"
                echo "  --logs-frontend      Show frontend logs"
                echo "  --help, -h           Show this help"
                echo ""
                echo "Environment variables:"
                echo "  REMOTE_HOST          Remote host (default: brutally@192.168.2.33)"
                echo "  EXTERNAL_HOST        External host (default: brutally@brutallyhonest.io)"
                echo "  SUDO_PASS            Sudo password for remote commands"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    print_banner
    
    case $deploy_type in
        status)
            check_connection
            show_status
            ;;
        logs)
            check_connection
            show_logs "api" 100
            ;;
        logs-frontend)
            check_connection
            show_logs "frontend" 100
            ;;
        rollback)
            check_connection
            rollback
            health_check
            ;;
        release)
            if [ -z "$release_version" ]; then
                log_error "Version required. Usage: $0 --release v1.2.3"
                exit 1
            fi
            create_release "$release_version"
            check_connection
            pre_deploy_checks
            create_backup
            sync_files
            install_deps
            restart_services
            health_check
            ;;
        full)
            check_connection
            pre_deploy_checks
            create_backup
            sync_files
            install_deps
            restart_services
            health_check
            ;;
        quick|*)
            check_connection
            pre_deploy_checks
            sync_files
            restart_services
            health_check
            ;;
    esac
    
    echo ""
    log_success "Deployment complete!"
    echo ""
    echo -e "${BOLD}Access:${NC}"
    echo -e "  Local:    http://192.168.2.33:3001"
    echo -e "  External: http://brutallyhonest.io:3001 (if port forwarded)"
    echo ""
}

main "$@"

