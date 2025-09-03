#!/bin/bash

# LLAMA Model Setup Script for Brutally Honest AI
# This script sets up LLAMA for transcription and analysis

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🦙 LLAMA Model Setup for Brutally Honest AI${NC}"
echo "=================================================="

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "mac"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
echo -e "${GREEN}✓ Detected OS: $OS${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run: python -m venv venv${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Installing LLAMA dependencies...${NC}"

# Activate virtual environment and install LLAMA dependencies
if [[ "$OS" == "windows" ]]; then
    ./venv/Scripts/activate && pip install llama-cpp-python transformers torch
else
    source venv/bin/activate && pip install llama-cpp-python transformers torch
fi

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create models directory
mkdir -p models

# Choose setup method
echo -e "\n${YELLOW}Choose LLAMA setup method:${NC}"
echo -e "  1) Use Ollama (recommended - easier setup)"
echo -e "  2) Download GGUF model file (more control, larger download)"
echo -e "  3) Skip model setup (install dependencies only)"
read -p "Select option (1-3): " LLAMA_CHOICE

case $LLAMA_CHOICE in
    1)
        echo -e "${GREEN}Setting up Ollama...${NC}"
        
        # Install Ollama if not present
        if ! command_exists ollama; then
            echo "Installing Ollama..."
            case $OS in
                mac)
                    if command_exists brew; then
                        brew install ollama
                    else
                        echo "Installing Ollama manually..."
                        curl -fsSL https://ollama.ai/install.sh | sh
                    fi
                    ;;
                linux)
                    curl -fsSL https://ollama.ai/install.sh | sh
                    ;;
                windows)
                    echo -e "${YELLOW}Please download Ollama from https://ollama.ai/download${NC}"
                    echo -e "${YELLOW}After installation, run: ollama pull llama2:7b${NC}"
                    exit 0
                    ;;
            esac
        else
            echo -e "${GREEN}✅ Ollama already installed${NC}"
        fi
        
        # Start Ollama service and pull model
        if [[ "$OS" != "windows" ]]; then
            echo "Starting Ollama service..."
            
            # Kill any existing ollama processes
            pkill -f "ollama serve" 2>/dev/null || true
            sleep 2
            
            # Start Ollama in background
            ollama serve &
            OLLAMA_PID=$!
            sleep 5
            
            echo "Pulling LLAMA model (this may take a few minutes)..."
            if ollama pull llama2:7b; then
                echo -e "${GREEN}✅ LLAMA model downloaded successfully${NC}"
            else
                echo -e "${RED}❌ Failed to download model${NC}"
                kill $OLLAMA_PID 2>/dev/null || true
                exit 1
            fi
            
            # Keep Ollama running
            echo -e "${GREEN}✅ Ollama service started (PID: $OLLAMA_PID)${NC}"
            echo -e "${BLUE}💡 Ollama will continue running in the background${NC}"
        fi
        ;;
    2)
        echo -e "${GREEN}Downloading GGUF model...${NC}"
        
        # Download a quantized LLAMA model (smaller but still good quality)
        if [ ! -f "models/llama-2-7b-chat.gguf" ]; then
            echo "Downloading LLAMA 2 7B Chat model (quantized, ~4GB)..."
            echo "This may take 10-30 minutes depending on your internet speed..."
            
            if curl -L --progress-bar -o models/llama-2-7b-chat.gguf \
                "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.q4_0.gguf"; then
                echo -e "${GREEN}✅ LLAMA model downloaded successfully${NC}"
            else
                echo -e "${RED}❌ Failed to download model${NC}"
                exit 1
            fi
        else
            echo -e "${GREEN}✅ LLAMA model already exists${NC}"
        fi
        ;;
    3)
        echo -e "${YELLOW}Skipping model setup${NC}"
        echo -e "${BLUE}💡 You can run this script again later to set up the model${NC}"
        ;;
    *)
        echo -e "${RED}Invalid selection${NC}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}🎉 LLAMA setup complete!${NC}"
echo "=================================================="

if [ "$LLAMA_CHOICE" = "1" ]; then
    echo -e "${BLUE}📡 Ollama service is running${NC}"
    echo -e "${BLUE}🔌 API endpoint: http://localhost:11434${NC}"
elif [ "$LLAMA_CHOICE" = "2" ]; then
    echo -e "${BLUE}📁 Model location: models/llama-2-7b-chat.gguf${NC}"
fi

echo -e "\n${YELLOW}Next steps:${NC}"
echo -e "  1. Start the application: ./start_app.sh"
echo -e "  2. Test transcription with audio files"
echo -e "  3. Check the logs for any LLAMA-related errors"

echo -e "\n${GREEN}Transcription should now work properly! 🎯${NC}"
