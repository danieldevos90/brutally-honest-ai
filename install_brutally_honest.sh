#!/bin/bash

# Brutally Honest AI - Easy Installer for XIAO ESP32S3 Sense + Expansion Board
# This script installs everything needed for non-technical users

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          BRUTALLY HONEST AI - EASY INSTALLER               ║${NC}"
echo -e "${BLUE}║      For XIAO ESP32S3 Sense + Expansion Board             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

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

# Step 1: Check and install dependencies
echo -e "\n${YELLOW}Step 1: Checking dependencies...${NC}"

# Check for Python
if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 not found. Installing...${NC}"
    case $OS in
        mac)
            if ! command_exists brew; then
                echo "Installing Homebrew first..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            brew install python3
            ;;
        linux)
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip
            ;;
        windows)
            echo "Please install Python 3 from https://www.python.org/downloads/"
            exit 1
            ;;
    esac
else
    echo -e "${GREEN}✓ Python 3 found${NC}"
fi

# Check for Arduino CLI
if ! command_exists arduino-cli; then
    echo -e "${RED}✗ Arduino CLI not found. Installing...${NC}"
    case $OS in
        mac)
            brew install arduino-cli
            ;;
        linux)
            curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
            sudo mv bin/arduino-cli /usr/local/bin/
            ;;
        windows)
            echo "Please download Arduino CLI from https://arduino.github.io/arduino-cli/latest/installation/"
            exit 1
            ;;
    esac
else
    echo -e "${GREEN}✓ Arduino CLI found${NC}"
fi

# Step 2: Setup Arduino CLI
echo -e "\n${YELLOW}Step 2: Setting up Arduino CLI...${NC}"

# Initialize Arduino CLI
arduino-cli config init

# Add ESP32 board support
echo -e "Adding ESP32 board support..."
arduino-cli config add board_manager.additional_urls https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json

# Update core index
arduino-cli core update-index

# Install ESP32 core
if ! arduino-cli core list | grep -q "esp32:esp32"; then
    echo -e "Installing ESP32 core..."
    arduino-cli core install esp32:esp32
else
    echo -e "${GREEN}✓ ESP32 core already installed${NC}"
fi

# Install required libraries
echo -e "\n${YELLOW}Step 3: Installing Arduino libraries...${NC}"

libraries=(
    "U8g2"
    "ArduinoJson"
)

for lib in "${libraries[@]}"; do
    echo -e "Installing $lib..."
    arduino-cli lib install "$lib" || true
done

# Step 4: Setup Python environment
echo -e "\n${YELLOW}Step 4: Setting up Python environment...${NC}"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install requirements
echo "Installing Python dependencies..."
if [[ "$OS" == "windows" ]]; then
    ./venv/Scripts/activate && pip install -r requirements.txt
else
    source venv/bin/activate && pip install -r requirements.txt
fi

# Step 4.5: Setup LLAMA model
echo -e "\n${YELLOW}Step 4.5: Setting up LLAMA model...${NC}"

# Create models directory
mkdir -p models

# Check if we should use Ollama or download GGUF model
echo -e "Choose LLAMA setup method:"
echo -e "  1) Use Ollama (recommended - easier setup)"
echo -e "  2) Download GGUF model file (more control)"
read -p "Select option (1-2): " LLAMA_CHOICE

case $LLAMA_CHOICE in
    1)
        echo -e "${GREEN}Setting up Ollama...${NC}"
        # Install Ollama if not present
        if ! command_exists ollama; then
            echo "Installing Ollama..."
            case $OS in
                mac)
                    brew install ollama
                    ;;
                linux)
                    curl -fsSL https://ollama.ai/install.sh | sh
                    ;;
                windows)
                    echo "Please download Ollama from https://ollama.ai/download"
                    echo "Then run: ollama pull llama2:7b"
                    ;;
            esac
        fi
        
        # Start Ollama service and pull model
        if [[ "$OS" != "windows" ]]; then
            echo "Starting Ollama service..."
            ollama serve &
            sleep 5
            echo "Pulling LLAMA model..."
            ollama pull llama2:7b
        fi
        ;;
    2)
        echo -e "${GREEN}Downloading GGUF model...${NC}"
        # Download a small LLAMA model
        if [ ! -f "models/llama-2-7b-chat.gguf" ]; then
            echo "Downloading LLAMA 2 7B Chat model (this may take a while)..."
            curl -L -o models/llama-2-7b-chat.gguf "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.q4_0.gguf"
        else
            echo -e "${GREEN}✓ LLAMA model already downloaded${NC}"
        fi
        ;;
    *)
        echo -e "${YELLOW}Skipping LLAMA setup - you can set it up later${NC}"
        ;;
esac

# Step 5: Detect connected device
echo -e "\n${YELLOW}Step 5: Looking for XIAO ESP32S3...${NC}"

echo -e "${BLUE}Please ensure your XIAO ESP32S3 is connected via USB-C cable${NC}"
echo -e "${YELLOW}If device is not detected:${NC}"
echo -e "  1. Hold the BOOT button on the ESP32S3"
echo -e "  2. While holding BOOT, press and release RESET"
echo -e "  3. Keep holding BOOT for 2-3 seconds"
echo -e "  4. Release BOOT button"
echo ""

# Wait for device
DEVICE_PORT=""
RETRY_COUNT=0
MAX_RETRIES=30

while [ -z "$DEVICE_PORT" ] && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if [[ "$OS" == "mac" ]]; then
        DEVICE_PORT=$(ls /dev/cu.usbmodem* 2>/dev/null | head -n1)
    elif [[ "$OS" == "linux" ]]; then
        DEVICE_PORT=$(ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | head -n1)
    elif [[ "$OS" == "windows" ]]; then
        # Windows COM port detection would need PowerShell
        echo "Please check Device Manager for COM port"
        read -p "Enter COM port (e.g., COM3): " DEVICE_PORT
        break
    fi
    
    if [ -z "$DEVICE_PORT" ]; then
        echo -ne "\rSearching for device... ($((RETRY_COUNT+1))/$MAX_RETRIES)"
        sleep 1
        RETRY_COUNT=$((RETRY_COUNT+1))
    fi
done

echo ""

if [ -z "$DEVICE_PORT" ]; then
    echo -e "${RED}✗ No device found. Please check connection and try again.${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Device found on: $DEVICE_PORT${NC}"
fi

# Step 6: Choose firmware version
echo -e "\n${YELLOW}Step 6: Choose firmware version:${NC}"
echo -e "  1) Full firmware (Recording, WiFi, BLE, Web interface)"
echo -e "  2) Simple toggle recording test (for testing)"
echo -e "  3) Basic OLED test (for troubleshooting)"
read -p "Select option (1-3): " FIRMWARE_CHOICE

FIRMWARE_PATH=""
case $FIRMWARE_CHOICE in
    1)
        FIRMWARE_PATH="omi_firmware/esp32s3_ble/esp32s3_ble.ino"
        echo -e "${GREEN}Selected: Full firmware${NC}"
        ;;
    2)
        FIRMWARE_PATH="omi_firmware/test_toggle_recording/test_toggle_recording.ino"
        echo -e "${GREEN}Selected: Toggle recording test${NC}"
        ;;
    3)
        FIRMWARE_PATH="omi_firmware/test_oled_official/test_oled_official.ino"
        echo -e "${GREEN}Selected: OLED test${NC}"
        ;;
    *)
        echo -e "${RED}Invalid selection${NC}"
        exit 1
        ;;
esac

# Step 7: Compile firmware
echo -e "\n${YELLOW}Step 7: Compiling firmware...${NC}"
arduino-cli compile --fqbn esp32:esp32:XIAO_ESP32S3 "$FIRMWARE_PATH"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Firmware compiled successfully${NC}"
else
    echo -e "${RED}✗ Compilation failed${NC}"
    exit 1
fi

# Step 8: Upload firmware
echo -e "\n${YELLOW}Step 8: Uploading firmware to device...${NC}"
echo -e "${BLUE}Note: If upload fails, put device in BOOT mode (see Step 5)${NC}"

arduino-cli upload --fqbn esp32:esp32:XIAO_ESP32S3 --port "$DEVICE_PORT" "$FIRMWARE_PATH"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Firmware uploaded successfully!${NC}"
else
    echo -e "${RED}✗ Upload failed. Try putting device in BOOT mode.${NC}"
    exit 1
fi

# Step 9: Start services (if full firmware)
if [ "$FIRMWARE_CHOICE" = "1" ]; then
    echo -e "\n${YELLOW}Step 9: Starting services...${NC}"
    
    # Install additional Python dependencies for bridge
    echo -e "Installing bridge server dependencies..."
    if [[ "$OS" == "windows" ]]; then
        ./venv/Scripts/pip install websockets pyserial requests
    else
        source venv/bin/activate && pip install websockets pyserial requests
    fi
    
    # Start companion script
    echo -e "Starting Whisper transcription service..."
    if [[ "$OS" == "windows" ]]; then
        start cmd /k "cd omi_firmware && ..\venv\Scripts\python esp32s3_companion.py"
    else
        cd omi_firmware && ../venv/bin/python esp32s3_companion.py &
        cd ..
    fi
    
    # Start bridge server
    echo -e "Starting bridge server..."
    if [[ "$OS" == "windows" ]]; then
        start cmd /k "venv\Scripts\python bridge_server.py"
    else
        ./venv/bin/python bridge_server.py &
    fi
    
    # Start web interface
    echo -e "Starting web interface..."
    cd frontend
    if command_exists npm; then
        npm install
        npm start &
    else
        echo -e "${YELLOW}Node.js not found. Web interface requires Node.js${NC}"
        echo -e "Visit https://nodejs.org to install"
    fi
    cd ..
fi

# Step 10: Display success message
echo -e "\n${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ INSTALLATION COMPLETE!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}Your Brutally Honest AI device is ready!${NC}"
echo -e "\n${YELLOW}How to use:${NC}"
echo -e "  • The OLED display should show 'Brutal Honest Query'"
echo -e "  • Press the button once to START recording"
echo -e "  • Press again to STOP recording"
echo -e "  • LED blinks while recording"
echo -e "  • Recordings are saved to SD card"

if [ "$FIRMWARE_CHOICE" = "1" ]; then
    echo -e "\n${YELLOW}Access points:${NC}"
    echo -e "  • WiFi AP: SSID='OMI-ESP32S3', Password='brutalhonest'"
    echo -e "  • Web interface: http://localhost:3000"
    echo -e "  • Device web server: http://192.168.4.1 (when connected to AP)"
fi

echo -e "\n${YELLOW}Troubleshooting:${NC}"
echo -e "  • If display doesn't work: Run this script again and choose option 3"
echo -e "  • If button doesn't respond: Check you're pressing the user button (D1)"
echo -e "  • For logs: arduino-cli monitor --port $DEVICE_PORT"

echo -e "\n${GREEN}Enjoy your Brutally Honest AI device! 🎯${NC}"
