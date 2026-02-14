#!/bin/bash
# ============================================
# BRUTALLY HONEST AI - HEADLESS NETWORK SETUP
# ============================================
# This script helps set up the Jetson in new environments
# without a monitor/keyboard using:
# 1. Ethernet with auto-DHCP
# 2. USB Gadget mode (direct laptop connection)
# 3. WiFi hotspot fallback
# 4. Bluetooth PAN (if available)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     BRUTALLY HONEST AI - HEADLESS NETWORK SETUP             ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"

# ============================================
# OPTION 1: ETHERNET AUTO-DHCP (Recommended)
# ============================================
setup_ethernet_dhcp() {
    echo -e "${GREEN}Setting up Ethernet with DHCP...${NC}"
    
    # Create NetworkManager connection for auto-DHCP on any ethernet
    cat > /etc/NetworkManager/system-connections/auto-ethernet.nmconnection << 'EOF'
[connection]
id=auto-ethernet
type=ethernet
autoconnect=true
autoconnect-priority=100

[ethernet]

[ipv4]
method=auto

[ipv6]
method=auto
EOF
    
    chmod 600 /etc/NetworkManager/system-connections/auto-ethernet.nmconnection
    nmcli connection reload
    echo -e "${GREEN}✓ Ethernet auto-DHCP configured${NC}"
}

# ============================================
# OPTION 2: USB GADGET MODE (Direct laptop connection)
# ============================================
setup_usb_gadget() {
    echo -e "${GREEN}Setting up USB Gadget mode for direct laptop connection...${NC}"
    
    # Enable USB gadget ethernet (works on Jetson Nano/Orin)
    if [ -f /opt/nvidia/l4t-usb-device-mode/nv-l4t-usb-device-mode-config.sh ]; then
        # NVIDIA's built-in USB device mode
        /opt/nvidia/l4t-usb-device-mode/nv-l4t-usb-device-mode-config.sh --enable-rndis
        echo -e "${GREEN}✓ USB RNDIS gadget enabled${NC}"
        echo -e "${YELLOW}Connect USB-C to laptop. Jetson will appear at 192.168.55.1${NC}"
    else
        # Manual USB gadget setup
        modprobe libcomposite
        
        # Create gadget
        GADGET_DIR=/sys/kernel/config/usb_gadget/brutally
        mkdir -p $GADGET_DIR
        cd $GADGET_DIR
        
        echo 0x1d6b > idVendor  # Linux Foundation
        echo 0x0104 > idProduct # Multifunction Composite Gadget
        echo 0x0100 > bcdDevice
        echo 0x0200 > bcdUSB
        
        mkdir -p strings/0x409
        echo "BrutallyHonestAI" > strings/0x409/manufacturer
        echo "Jetson Network" > strings/0x409/product
        
        # RNDIS function (Windows compatible)
        mkdir -p functions/rndis.usb0
        
        # ECM function (Mac/Linux compatible)
        mkdir -p functions/ecm.usb0
        
        mkdir -p configs/c.1/strings/0x409
        echo "RNDIS+ECM" > configs/c.1/strings/0x409/configuration
        
        ln -sf functions/rndis.usb0 configs/c.1/
        ln -sf functions/ecm.usb0 configs/c.1/
        
        # Enable gadget
        UDC=$(ls /sys/class/udc | head -1)
        echo $UDC > UDC
        
        # Configure IP
        ip addr add 192.168.55.1/24 dev usb0 2>/dev/null || true
        ip link set usb0 up
        
        echo -e "${GREEN}✓ USB gadget configured at 192.168.55.1${NC}"
    fi
}

# ============================================
# OPTION 3: WIFI HOTSPOT FALLBACK
# ============================================
setup_wifi_hotspot() {
    echo -e "${GREEN}Setting up WiFi Hotspot fallback...${NC}"
    
    SSID="BrutallyHonest-Setup"
    PASSWORD="brutally2024"
    
    # Create hotspot connection
    nmcli connection delete "$SSID" 2>/dev/null || true
    nmcli connection add type wifi ifname wlan0 con-name "$SSID" \
        autoconnect no \
        ssid "$SSID" \
        mode ap \
        ipv4.method shared \
        wifi-sec.key-mgmt wpa-psk \
        wifi-sec.psk "$PASSWORD"
    
    echo -e "${GREEN}✓ WiFi Hotspot configured${NC}"
    echo -e "${YELLOW}SSID: $SSID${NC}"
    echo -e "${YELLOW}Password: $PASSWORD${NC}"
    echo -e "${YELLOW}Jetson IP: 10.42.0.1 (when hotspot active)${NC}"
}

# ============================================
# OPTION 4: BLUETOOTH PAN (Personal Area Network)
# ============================================
setup_bluetooth_pan() {
    echo -e "${GREEN}Setting up Bluetooth PAN...${NC}"
    
    # Check if Bluetooth is available
    if ! command -v bluetoothctl &> /dev/null; then
        echo -e "${RED}Bluetooth not available on this device${NC}"
        return 1
    fi
    
    # Enable Bluetooth
    systemctl enable bluetooth
    systemctl start bluetooth
    
    # Make discoverable
    bluetoothctl << EOF
power on
discoverable on
pairable on
agent on
default-agent
EOF
    
    # Install bt-pan if needed
    if ! command -v bt-pan &> /dev/null; then
        apt-get update && apt-get install -y bluez-tools
    fi
    
    # Create NAP service
    cat > /etc/systemd/system/bt-pan.service << 'EOF'
[Unit]
Description=Bluetooth PAN Network
After=bluetooth.service
Requires=bluetooth.service

[Service]
Type=simple
ExecStart=/usr/bin/bt-network -s nap pan0
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl enable bt-pan
    systemctl start bt-pan
    
    echo -e "${GREEN}✓ Bluetooth PAN configured${NC}"
    echo -e "${YELLOW}Pair your phone/laptop via Bluetooth to share internet${NC}"
}

# ============================================
# OPTION 5: STATIC IP FALLBACK
# ============================================
setup_static_fallback() {
    echo -e "${GREEN}Setting up static IP fallback...${NC}"
    
    # If DHCP fails after 30 seconds, use static IP
    cat > /etc/NetworkManager/dispatcher.d/99-static-fallback << 'EOF'
#!/bin/bash
IFACE=$1
ACTION=$2

if [ "$ACTION" = "dhcp4-change" ] || [ "$ACTION" = "up" ]; then
    # Check if we got an IP via DHCP
    IP=$(ip addr show $IFACE | grep "inet " | awk '{print $2}')
    if [ -z "$IP" ]; then
        # No DHCP, set static IP
        ip addr add 192.168.1.100/24 dev $IFACE
        echo "Static fallback IP set on $IFACE"
    fi
fi
EOF
    
    chmod +x /etc/NetworkManager/dispatcher.d/99-static-fallback
    echo -e "${GREEN}✓ Static fallback configured (192.168.1.100)${NC}"
}

# ============================================
# AUTO-START SERVICES
# ============================================
setup_autostart() {
    echo -e "${GREEN}Setting up auto-start for Brutally Honest services...${NC}"
    
    cat > /etc/systemd/system/brutally-honest.service << 'EOF'
[Unit]
Description=Brutally Honest AI API Server
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=brutally
WorkingDirectory=/home/brutally/brutally-honest-ai
Environment="PATH=/home/brutally/brutally-honest-ai/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/brutally/brutally-honest-ai/venv/bin/uvicorn api_server:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable brutally-honest
    
    echo -e "${GREEN}✓ Auto-start service configured${NC}"
}

# ============================================
# MDNS/AVAHI FOR DISCOVERY
# ============================================
setup_mdns() {
    echo -e "${GREEN}Setting up mDNS for easy discovery...${NC}"
    
    apt-get update && apt-get install -y avahi-daemon avahi-utils
    
    # Configure Avahi
    cat > /etc/avahi/services/brutally-honest.service << 'EOF'
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>Brutally Honest AI</name>
  <service>
    <type>_http._tcp</type>
    <port>8000</port>
    <txt-record>path=/docs</txt-record>
  </service>
  <service>
    <type>_ssh._tcp</type>
    <port>22</port>
  </service>
</service-group>
EOF
    
    systemctl enable avahi-daemon
    systemctl restart avahi-daemon
    
    HOSTNAME=$(hostname)
    echo -e "${GREEN}✓ mDNS configured${NC}"
    echo -e "${YELLOW}Device will be discoverable as: ${HOSTNAME}.local${NC}"
}

# ============================================
# MAIN MENU
# ============================================
case "${1:-all}" in
    ethernet)
        setup_ethernet_dhcp
        ;;
    usb)
        setup_usb_gadget
        ;;
    hotspot)
        setup_wifi_hotspot
        ;;
    bluetooth)
        setup_bluetooth_pan
        ;;
    static)
        setup_static_fallback
        ;;
    mdns)
        setup_mdns
        ;;
    autostart)
        setup_autostart
        ;;
    all)
        echo -e "${CYAN}Setting up ALL headless network options...${NC}"
        setup_ethernet_dhcp
        setup_static_fallback
        setup_mdns
        setup_autostart
        echo ""
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                    SETUP COMPLETE!                           ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "Connection options in new environments:"
        echo -e "  1. ${CYAN}Ethernet${NC}: Just plug in - auto DHCP"
        echo -e "  2. ${CYAN}USB-C${NC}: Connect to laptop - 192.168.55.1"
        echo -e "  3. ${CYAN}Static IP${NC}: 192.168.1.100 (if no DHCP)"
        echo -e "  4. ${CYAN}mDNS${NC}: $(hostname).local"
        echo ""
        echo -e "Run additional options:"
        echo -e "  ${YELLOW}./headless_network_setup.sh usb${NC}      - USB gadget mode"
        echo -e "  ${YELLOW}./headless_network_setup.sh hotspot${NC}  - WiFi hotspot"
        echo -e "  ${YELLOW}./headless_network_setup.sh bluetooth${NC} - Bluetooth PAN"
        ;;
    *)
        echo "Usage: $0 {ethernet|usb|hotspot|bluetooth|static|mdns|autostart|all}"
        exit 1
        ;;
esac
