#!/bin/bash

# Brutally Honest AI - Deploy Landing Site to Vercel
# Domain: brutallyhonest.io

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║      BRUTALLY HONEST - VERCEL LANDING PAGE DEPLOYMENT         ║${NC}"
echo -e "${CYAN}║      Domain: brutallyhonest.io                                ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

LANDING_DIR="$(cd "$(dirname "$0")/landing-site" && pwd)"
cd "$LANDING_DIR"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}Installing Vercel CLI...${NC}"
    npm install -g vercel
fi

# Build first
echo -e "${YELLOW}➤ Building project...${NC}"
npm run build
echo -e "${GREEN}✓ Build successful${NC}"
echo ""

echo -e "${YELLOW}➤ Deploying to Vercel...${NC}"

# Deploy
if [ "$1" == "--prod" ] || [ "$1" == "-p" ]; then
    echo -e "${GREEN}Deploying to production...${NC}"
    vercel --prod --yes
else
    echo -e "${YELLOW}Deploying preview (use --prod for production)...${NC}"
    vercel --yes
fi

echo ""
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}Domain Setup Instructions:${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  1. Go to Vercel Dashboard → Your Project → Settings → Domains"
echo -e "  2. Add: ${GREEN}brutallyhonest.io${NC}"
echo -e "  3. Follow Vercel DNS instructions (or use Cloudflare)"
echo ""
echo -e "${CYAN}Architecture:${NC}"
echo -e "  • ${GREEN}brutallyhonest.io${NC}      → Vercel (This landing page)"
echo -e "  • ${GREEN}app.brutallyhonest.io${NC}  → NVIDIA Server (Full application)"
echo ""
echo -e "${CYAN}For app subdomain setup, see: docs/DEPLOYMENT_ARCHITECTURE.md${NC}"
