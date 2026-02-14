#!/bin/bash

# Brutally Honest AI - Document Upload Script
# Uploads Word documents to the vector database

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
API_HOST="${API_HOST:-localhost}"
API_PORT="${API_PORT:-8000}"
API_KEY="${API_KEY:-}"

LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   BRUTALLY HONEST AI - DOCUMENT UPLOAD TO VECTOR DB          ║${NC}"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if API key is provided
if [ -z "$API_KEY" ]; then
    echo -e "${YELLOW}No API_KEY provided. Checking for local API key file...${NC}"
    
    if [ -f "$LOCAL_DIR/.api_keys.json" ]; then
        # Try to extract a key with 'all' permissions
        API_KEY=$(python3 -c "
import json
from pathlib import Path
keys = json.loads(Path('$LOCAL_DIR/.api_keys.json').read_text())
for k,v in keys.items():
    if v.get('permissions') == 'all':
        print(k)
        break
" 2>/dev/null || echo "")
    fi
    
    if [ -z "$API_KEY" ]; then
        echo -e "${RED}No API key found. Please set API_KEY environment variable.${NC}"
        echo ""
        echo "Usage:"
        echo "  API_KEY=your_key API_HOST=192.168.1.100 ./upload_documents.sh"
        exit 1
    fi
    
    echo -e "${GREEN}Found API key from .api_keys.json${NC}"
fi

BASE_URL="http://${API_HOST}:${API_PORT}"

echo -e "${BLUE}API Endpoint: $BASE_URL${NC}"
echo ""

# Test API connection
echo -e "${YELLOW}Testing API connection...${NC}"
if curl -s -f "$BASE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ API is reachable${NC}"
else
    echo -e "${RED}✗ Cannot reach API at $BASE_URL${NC}"
    echo "Make sure the API server is running."
    exit 1
fi

echo ""

# Function to upload a document
upload_document() {
    local file="$1"
    local category="$2"
    local tags="$3"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}✗ File not found: $file${NC}"
        return 1
    fi
    
    filename=$(basename "$file")
    echo -e "${YELLOW}Uploading: $filename${NC}"
    
    # Use the queue endpoint for proper handling
    response=$(curl -s -X POST "$BASE_URL/queue/upload/document" \
        -H "Authorization: Bearer $API_KEY" \
        -F "file=@$file" \
        -F "category=$category" \
        -F "tags=$tags" \
        -F "priority=high")
    
    # Check response
    success=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null || echo "false")
    
    if [ "$success" == "True" ]; then
        queue_id=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('queue_item_id', 'unknown'))" 2>/dev/null)
        echo -e "${GREEN}✓ Queued successfully! Queue ID: $queue_id${NC}"
        
        # Wait for processing
        echo -e "  Waiting for processing..."
        sleep 2
        
        # Check status
        for i in {1..30}; do
            status_response=$(curl -s "$BASE_URL/queue/status/$queue_id" \
                -H "Authorization: Bearer $API_KEY")
            status=$(echo "$status_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status', 'unknown'))" 2>/dev/null)
            progress=$(echo "$status_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('progress', 0))" 2>/dev/null)
            
            if [ "$status" == "completed" ]; then
                echo -e "  ${GREEN}✓ Processing complete!${NC}"
                break
            elif [ "$status" == "failed" ]; then
                error=$(echo "$status_response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('error', 'unknown'))" 2>/dev/null)
                echo -e "  ${RED}✗ Processing failed: $error${NC}"
                break
            else
                echo -e "  Status: $status ($progress%)"
                sleep 2
            fi
        done
    else
        error=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('detail', json.load(sys.stdin).get('error', 'Unknown error')))" 2>/dev/null || echo "$response")
        echo -e "${RED}✗ Upload failed: $error${NC}"
        return 1
    fi
    
    echo ""
}

# Upload the two main documents
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}Uploading Word documents to Vector Database...${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""

# Document 1: AI Design Principles
DOC1="$LOCAL_DIR/SAMENVATTING 2.0 AI BF INPUT ONTWERPPRINCIPES 15 DEC 2025.docx"
if [ -f "$DOC1" ]; then
    upload_document "$DOC1" "knowledge_base" "dutch,ai,design-principles,bf-input,summary"
fi

# Document 2: Team Dynamics
DOC2="$LOCAL_DIR/Teamdynamiek en CEO 2.0 driving High Performing Teams 15 DEC 2025.docx"
if [ -f "$DOC2" ]; then
    upload_document "$DOC2" "knowledge_base" "dutch,team-dynamics,ceo,high-performance,leadership"
fi

# Also check for any other .docx files in the directory
echo -e "${BLUE}Checking for other Word documents...${NC}"
for doc in "$LOCAL_DIR"/*.docx; do
    if [ -f "$doc" ]; then
        filename=$(basename "$doc")
        # Skip the ones we already uploaded
        if [[ "$filename" != "SAMENVATTING"* ]] && [[ "$filename" != "Teamdynamiek"* ]]; then
            echo -e "${YELLOW}Found additional document: $filename${NC}"
            read -p "Upload this document? (y/N): " upload_choice
            if [[ "$upload_choice" =~ ^[Yy]$ ]]; then
                upload_document "$doc" "knowledge_base" "document"
            fi
        fi
    fi
done

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Document upload complete!${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}View uploaded documents:${NC}"
echo -e "  curl -s \"$BASE_URL/documents/list\" -H \"Authorization: Bearer \$API_KEY\" | python3 -m json.tool"
echo ""
echo -e "${BLUE}Search documents:${NC}"
echo -e "  curl -s \"$BASE_URL/documents/search?query=team+dynamics\" -H \"Authorization: Bearer \$API_KEY\" | python3 -m json.tool"
echo ""
echo -e "${BLUE}Query with AI:${NC}"
echo -e "  curl -s -X POST \"$BASE_URL/documents/query\" -H \"Authorization: Bearer \$API_KEY\" \\"
echo -e "    -H \"Content-Type: application/json\" -d '{\"query\": \"What are the design principles?\"}' | python3 -m json.tool"
