#!/bin/bash

# Brutally Honest AI - Domain Setup Script
# This script configures both Vercel (landing) and Cloudflare (app) domains

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║          BRUTALLY HONEST AI - DOMAIN CONFIGURATION            ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ============================================
# VERCEL - Landing Page (brutallyhonest.io)
# ============================================
echo -e "${YELLOW}═══ VERCEL: Landing Page Setup ═══${NC}"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}Vercel CLI not found. Installing...${NC}"
    npm install -g vercel
fi

# Deploy landing site
LANDING_DIR="$(dirname "$0")/landing-site"
if [ -d "$LANDING_DIR" ]; then
    echo -e "${GREEN}✓ Landing site directory found${NC}"
    cd "$LANDING_DIR"
    
    # Link project if not already linked
    if [ ! -d ".vercel" ]; then
        echo -e "${YELLOW}Linking Vercel project...${NC}"
        vercel link --yes
    fi
    
    # Deploy to production
    echo -e "${YELLOW}Deploying to Vercel production...${NC}"
    vercel --prod
    
    echo -e "${GREEN}✓ Landing site deployed to Vercel${NC}"
else
    echo -e "${RED}Landing site directory not found at $LANDING_DIR${NC}"
    exit 1
fi

cd "$(dirname "$0")"

# ============================================
# CLOUDFLARE - App Tunnel (app.brutallyhonest.io)
# ============================================
echo ""
echo -e "${YELLOW}═══ CLOUDFLARE: App Tunnel Setup ═══${NC}"

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo -e "${RED}cloudflared not found. Please install from: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/${NC}"
    exit 1
fi

# Check tunnel status
TUNNEL_NAME="brutally-honest"
echo -e "${YELLOW}Checking tunnel '$TUNNEL_NAME'...${NC}"

if cloudflared tunnel list 2>/dev/null | grep -q "$TUNNEL_NAME"; then
    echo -e "${GREEN}✓ Tunnel '$TUNNEL_NAME' exists${NC}"
    
    # Route app subdomain to tunnel
    echo -e "${YELLOW}Configuring DNS route for app.brutallyhonest.io...${NC}"
    cloudflared tunnel route dns --overwrite-dns "$TUNNEL_NAME" app.brutallyhonest.io
    echo -e "${GREEN}✓ app.brutallyhonest.io routed to tunnel${NC}"
else
    echo -e "${RED}Tunnel '$TUNNEL_NAME' not found.${NC}"
    echo -e "${YELLOW}Creating tunnel...${NC}"
    cloudflared tunnel create "$TUNNEL_NAME"
    cloudflared tunnel route dns "$TUNNEL_NAME" app.brutallyhonest.io
fi

# ============================================
# DNS CONFIGURATION INSTRUCTIONS
# ============================================
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}         MANUAL DNS CONFIGURATION REQUIRED                     ${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "In your Cloudflare Dashboard (dash.cloudflare.com), add these DNS records:"
echo ""
echo -e "${YELLOW}For brutallyhonest.io (Vercel Landing Page):${NC}"
echo -e "  Type: A     Name: @     Content: 76.76.21.21     Proxy: DNS only"
echo -e "  Type: CNAME Name: www   Content: cname.vercel-dns.com  Proxy: DNS only"
echo ""
echo -e "${YELLOW}For app.brutallyhonest.io (NVIDIA Server via Tunnel):${NC}"
echo -e "  Type: CNAME Name: app   Content: ${TUNNEL_NAME}.cfargotunnel.com  Proxy: Proxied ✓"
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}               SETUP COMPLETE!                                  ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "URLs:"
echo -e "  Landing Page: https://brutallyhonest.io"
echo -e "  Application:  https://app.brutallyhonest.io"
echo ""

