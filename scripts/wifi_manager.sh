#!/bin/bash
# ============================================
# Brutally Honest AI - WiFi Network Manager
# Add, list, and manage WiFi networks for auto-connect
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_help() {
    echo ""
    echo -e "${BLUE}Brutally Honest AI - WiFi Manager${NC}"
    echo "=================================="
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  add <SSID> <password>     Add a new WiFi network"
    echo "  list                      List saved WiFi networks"
    echo "  scan                      Scan for available networks"
    echo "  connect <SSID>            Connect to a saved network"
    echo "  forget <SSID>             Remove a saved network"
    echo "  status                    Show current connection status"
    echo "  priority <SSID> <num>     Set connection priority (higher = preferred)"
    echo ""
    echo "Examples:"
    echo "  $0 add \"Home WiFi\" \"mypassword\""
    echo "  $0 add \"Office\" \"workpass123\""
    echo "  $0 connect \"Home WiFi\""
    echo "  $0 priority \"Home WiFi\" 100"
    echo ""
}

# Check if NetworkManager is available
check_nmcli() {
    if ! command -v nmcli &> /dev/null; then
        echo -e "${RED}❌ NetworkManager (nmcli) not found${NC}"
        echo "Install with: sudo apt install network-manager"
        exit 1
    fi
}

add_network() {
    local SSID="$1"
    local PASSWORD="$2"
    
    if [ -z "$SSID" ] || [ -z "$PASSWORD" ]; then
        echo -e "${RED}❌ Usage: $0 add <SSID> <password>${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Adding WiFi network: $SSID${NC}"
    
    # Check if connection already exists
    if nmcli connection show "$SSID" &> /dev/null; then
        echo -e "${YELLOW}⚠️ Network '$SSID' already exists, updating...${NC}"
        nmcli connection modify "$SSID" \
            wifi-sec.key-mgmt wpa-psk \
            wifi-sec.psk "$PASSWORD" \
            connection.autoconnect yes \
            connection.autoconnect-priority 10
    else
        # Add new connection
        nmcli connection add \
            type wifi \
            con-name "$SSID" \
            ssid "$SSID" \
            wifi-sec.key-mgmt wpa-psk \
            wifi-sec.psk "$PASSWORD" \
            connection.autoconnect yes \
            connection.autoconnect-priority 10
    fi
    
    echo -e "${GREEN}✅ Network '$SSID' added with auto-connect enabled${NC}"
    echo -e "${BLUE}💡 Tip: Use '$0 priority \"$SSID\" 100' to make it preferred${NC}"
}

list_networks() {
    echo -e "${BLUE}Saved WiFi Networks:${NC}"
    echo "===================="
    nmcli connection show | grep wifi | while read -r line; do
        NAME=$(echo "$line" | awk '{print $1}')
        UUID=$(echo "$line" | awk '{print $2}')
        AUTOCONNECT=$(nmcli -g connection.autoconnect connection show "$NAME" 2>/dev/null || echo "unknown")
        PRIORITY=$(nmcli -g connection.autoconnect-priority connection show "$NAME" 2>/dev/null || echo "0")
        
        if [ "$AUTOCONNECT" == "yes" ]; then
            AUTO="${GREEN}auto-connect${NC}"
        else
            AUTO="${YELLOW}manual${NC}"
        fi
        
        printf "  %-25s [priority: %3s] %b\n" "$NAME" "$PRIORITY" "$AUTO"
    done
    echo ""
}

scan_networks() {
    echo -e "${BLUE}Scanning for WiFi networks...${NC}"
    echo "=============================="
    nmcli device wifi rescan 2>/dev/null || true
    sleep 2
    nmcli device wifi list
    echo ""
}

connect_network() {
    local SSID="$1"
    
    if [ -z "$SSID" ]; then
        echo -e "${RED}❌ Usage: $0 connect <SSID>${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Connecting to: $SSID${NC}"
    
    if nmcli connection up "$SSID"; then
        echo -e "${GREEN}✅ Connected to '$SSID'${NC}"
        
        # Restart cloudflared after connection
        echo -e "${BLUE}Restarting cloudflared tunnel...${NC}"
        sudo systemctl restart cloudflared
        sleep 3
        
        if systemctl is-active --quiet cloudflared; then
            echo -e "${GREEN}✅ Cloudflared tunnel reconnected${NC}"
        else
            echo -e "${YELLOW}⚠️ Cloudflared may need manual restart${NC}"
        fi
    else
        echo -e "${RED}❌ Failed to connect to '$SSID'${NC}"
        exit 1
    fi
}

forget_network() {
    local SSID="$1"
    
    if [ -z "$SSID" ]; then
        echo -e "${RED}❌ Usage: $0 forget <SSID>${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Removing network: $SSID${NC}"
    
    if nmcli connection delete "$SSID"; then
        echo -e "${GREEN}✅ Network '$SSID' removed${NC}"
    else
        echo -e "${RED}❌ Failed to remove '$SSID' - may not exist${NC}"
    fi
}

show_status() {
    echo -e "${BLUE}Network Status:${NC}"
    echo "==============="
    echo ""
    
    # Current connection
    CURRENT=$(nmcli -t -f ACTIVE,SSID dev wifi | grep "yes:" | cut -d: -f2)
    if [ -n "$CURRENT" ]; then
        echo -e "  ${GREEN}●${NC} Connected to: ${GREEN}$CURRENT${NC}"
        
        # Get IP address
        IP=$(hostname -I | awk '{print $1}')
        echo -e "  📍 IP Address: $IP"
        
        # Get signal strength
        SIGNAL=$(nmcli -f IN-USE,SIGNAL device wifi | grep "^\*" | awk '{print $2}')
        echo -e "  📶 Signal: ${SIGNAL}%"
    else
        echo -e "  ${RED}○${NC} Not connected to WiFi"
    fi
    
    echo ""
    echo -e "${BLUE}Service Status:${NC}"
    echo "==============="
    
    for service in cloudflared brutally-honest-api brutally-honest-frontend; do
        STATUS=$(systemctl is-active $service 2>/dev/null || echo "not-found")
        if [ "$STATUS" == "active" ]; then
            echo -e "  ${GREEN}●${NC} $service: ${GREEN}running${NC}"
        else
            echo -e "  ${RED}○${NC} $service: ${RED}$STATUS${NC}"
        fi
    done
    
    echo ""
    echo -e "${BLUE}External Access:${NC}"
    echo "================"
    echo "  🌐 https://brutallyhonest.io"
    echo "  🔌 https://api.brutallyhonest.io"
    echo ""
}

set_priority() {
    local SSID="$1"
    local PRIORITY="$2"
    
    if [ -z "$SSID" ] || [ -z "$PRIORITY" ]; then
        echo -e "${RED}❌ Usage: $0 priority <SSID> <number>${NC}"
        echo "Higher numbers = higher priority (preferred network)"
        exit 1
    fi
    
    echo -e "${BLUE}Setting priority for '$SSID' to $PRIORITY${NC}"
    
    if nmcli connection modify "$SSID" connection.autoconnect-priority "$PRIORITY"; then
        echo -e "${GREEN}✅ Priority set. '$SSID' will be preferred when in range.${NC}"
    else
        echo -e "${RED}❌ Failed to set priority${NC}"
    fi
}

# Main
check_nmcli

case "${1:-help}" in
    add)
        add_network "$2" "$3"
        ;;
    list)
        list_networks
        ;;
    scan)
        scan_networks
        ;;
    connect)
        connect_network "$2"
        ;;
    forget)
        forget_network "$2"
        ;;
    status)
        show_status
        ;;
    priority)
        set_priority "$2" "$3"
        ;;
    help|--help|-h|*)
        show_help
        ;;
esac

