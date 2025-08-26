#!/bin/bash
# ESP32S3 OMI Firmware Deployment Script
# Deploys enhanced firmware to Seeeduino XIAO ESP32S3 Sense

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BOARD="esp32:esp32:XIAO_ESP32S3"
SKETCH_PATH="$(pwd)/esp32s3_ble/esp32s3_ble.ino"
BUILD_PATH="$(pwd)/build"

echo -e "${BLUE}🚀 ESP32S3 OMI Firmware Deployment${NC}"
echo "=================================================="

# Check if Arduino CLI is installed
check_arduino_cli() {
    if ! command -v arduino-cli &> /dev/null; then
        echo -e "${RED}❌ Arduino CLI not found${NC}"
        echo -e "${YELLOW}Installing Arduino CLI...${NC}"
        
        # Install Arduino CLI
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command -v brew &> /dev/null; then
                brew install arduino-cli
            else
                echo -e "${RED}Please install Homebrew first: https://brew.sh${NC}"
                exit 1
            fi
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
            sudo mv bin/arduino-cli /usr/local/bin/
        else
            echo -e "${RED}Please install Arduino CLI manually: https://arduino.github.io/arduino-cli/installation/${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ Arduino CLI found${NC}"
    fi
}

# Initialize Arduino CLI
init_arduino_cli() {
    echo -e "${YELLOW}🔧 Initializing Arduino CLI...${NC}"
    
    # Create config if it doesn't exist
    if [ ! -f ~/.arduino15/arduino-cli.yaml ]; then
        arduino-cli config init
    fi
    
    # Update package index
    arduino-cli core update-index
    
    # Install ESP32 core if not already installed
    if ! arduino-cli core list | grep -q "esp32:esp32"; then
        echo -e "${YELLOW}📦 Installing ESP32 core...${NC}"
        arduino-cli core install esp32:esp32
    else
        echo -e "${GREEN}✅ ESP32 core already installed${NC}"
    fi
}

# Install required libraries
install_libraries() {
    echo -e "${YELLOW}📚 Installing required libraries...${NC}"
    
    # List of required libraries
    libraries=(
        "ESP32 BLE Arduino"
    )
    
    for lib in "${libraries[@]}"; do
        if ! arduino-cli lib list | grep -q "$lib"; then
            echo -e "${YELLOW}Installing $lib...${NC}"
            arduino-cli lib install "$lib" || echo -e "${YELLOW}⚠️  $lib may already be built-in${NC}"
        else
            echo -e "${GREEN}✅ $lib already installed${NC}"
        fi
    done
}

# Detect ESP32S3 device
detect_device() {
    echo -e "${YELLOW}🔍 Detecting ESP32S3 device...${NC}"
    
    # List available ports
    ports=$(arduino-cli board list | grep -E "(tty\.usbmodem|cu\.usbmodem|ttyUSB|ttyACM)" | awk '{print $1}')
    
    if [ -z "$ports" ]; then
        echo -e "${RED}❌ No ESP32S3 device detected${NC}"
        echo -e "${YELLOW}Please ensure:${NC}"
        echo "  1. ESP32S3 is connected via USB-C"
        echo "  2. USB cable supports data transfer"
        echo "  3. Device drivers are installed"
        echo ""
        echo -e "${YELLOW}Available ports:${NC}"
        arduino-cli board list
        exit 1
    fi
    
    # Use first available port
    PORT=$(echo "$ports" | head -n1)
    echo -e "${GREEN}✅ Found ESP32S3 at port: $PORT${NC}"
}

# Compile firmware
compile_firmware() {
    echo -e "${YELLOW}🔨 Compiling firmware...${NC}"
    
    # Create build directory
    mkdir -p "$BUILD_PATH"
    
    # Compile the sketch
    arduino-cli compile \
        --fqbn "$BOARD" \
        --build-path "$BUILD_PATH" \
        --output-dir "$BUILD_PATH" \
        "$SKETCH_PATH"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Compilation successful${NC}"
    else
        echo -e "${RED}❌ Compilation failed${NC}"
        exit 1
    fi
}

# Upload firmware
upload_firmware() {
    echo -e "${YELLOW}📤 Uploading firmware to ESP32S3...${NC}"
    
    arduino-cli upload \
        --fqbn "$BOARD" \
        --port "$PORT" \
        --input-dir "$BUILD_PATH"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Upload successful${NC}"
    else
        echo -e "${RED}❌ Upload failed${NC}"
        echo -e "${YELLOW}Try:${NC}"
        echo "  1. Press and hold BOOT button while connecting USB"
        echo "  2. Reset the device and try again"
        echo "  3. Check if another program is using the serial port"
        exit 1
    fi
}

# Monitor serial output
monitor_serial() {
    echo -e "${YELLOW}📺 Starting serial monitor...${NC}"
    echo -e "${BLUE}Press Ctrl+C to exit monitor${NC}"
    echo "=================================================="
    
    arduino-cli monitor --port "$PORT" --config baudrate=115200
}

# Main deployment process
main() {
    echo -e "${BLUE}Starting deployment process...${NC}"
    echo ""
    
    # Check prerequisites
    check_arduino_cli
    init_arduino_cli
    install_libraries
    
    # Detect device
    detect_device
    
    # Compile and upload
    compile_firmware
    upload_firmware
    
    echo ""
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}Device Information:${NC}"
    echo "  • Board: Seeeduino XIAO ESP32S3 Sense"
    echo "  • Port: $PORT"
    echo "  • Firmware: Enhanced OMI with Whisper support"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo "  1. Insert microSD card"
    echo "  2. Connect to WiFi 'OMI-ESP32S3' (password: brutalhonest)"
    echo "  3. Access web interface at http://192.168.4.1"
    echo "  4. Press button to start recording"
    echo ""
    
    # Ask if user wants to monitor
    read -p "$(echo -e ${YELLOW}Would you like to start serial monitor? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        monitor_serial
    fi
}

# Handle script arguments
case "${1:-}" in
    --compile-only)
        check_arduino_cli
        init_arduino_cli
        install_libraries
        compile_firmware
        echo -e "${GREEN}✅ Compilation completed${NC}"
        ;;
    --upload-only)
        detect_device
        upload_firmware
        echo -e "${GREEN}✅ Upload completed${NC}"
        ;;
    --monitor)
        detect_device
        monitor_serial
        ;;
    --help|-h)
        echo "ESP32S3 OMI Firmware Deployment Script"
        echo ""
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (no args)      Full deployment (compile + upload)"
        echo "  --compile-only Compile firmware only"
        echo "  --upload-only  Upload pre-compiled firmware"
        echo "  --monitor      Start serial monitor"
        echo "  --help, -h     Show this help"
        ;;
    *)
        main
        ;;
esac
