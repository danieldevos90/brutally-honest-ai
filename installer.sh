#!/bin/bash

# Brutally Honest AI - Interactive Installer
# ========================================
# Automated setup for ESP32S3 Bluetooth voice analysis system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ASCII Art Banner
print_banner() {
    echo -e "${PURPLE}"
    echo "██████╗ ██████╗ ██╗   ██╗████████╗ █████╗ ██╗         █████╗ ██╗"
    echo "██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔══██╗██║        ██╔══██╗██║"
    echo "██████╔╝██████╔╝██║   ██║   ██║   ███████║██║        ███████║██║"
    echo "██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══██║██║        ██╔══██║██║"
    echo "██████╔╝██║  ██║╚██████╔╝   ██║   ██║  ██║███████╗   ██║  ██║██║"
    echo "╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚══════╝   ╚═╝  ╚═╝╚═╝"
    echo -e "${NC}"
    echo -e "${CYAN}🤖 Brutally Honest AI - ESP32S3 Voice Analysis System${NC}"
    echo -e "${YELLOW}Interactive Installation & Setup${NC}"
    echo ""
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# Progress indicator
show_progress() {
    local duration=$1
    local message=$2
    echo -n -e "${CYAN}$message${NC}"
    for i in $(seq 1 $duration); do
        echo -n "."
        sleep 1
    done
    echo " Done!"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Interactive prompts
ask_yes_no() {
    local question=$1
    local default=${2:-"y"}
    
    if [[ $default == "y" ]]; then
        prompt="[Y/n]"
    else
        prompt="[y/N]"
    fi
    
    while true; do
        echo -n -e "${YELLOW}$question $prompt: ${NC}"
        read -r answer
        
        # Use default if empty
        if [[ -z $answer ]]; then
            answer=$default
        fi
        
        case $answer in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

# Get user input with default
ask_input() {
    local question=$1
    local default=$2
    
    echo -n -e "${YELLOW}$question${NC}"
    if [[ -n $default ]]; then
        echo -n -e " ${CYAN}[$default]${NC}"
    fi
    echo -n ": "
    
    read -r answer
    if [[ -z $answer && -n $default ]]; then
        echo "$default"
    else
        echo "$answer"
    fi
}

# Check system requirements
check_system() {
    log_step "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        log_success "macOS detected"
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        log_success "Linux detected"
        OS="linux"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python $PYTHON_VERSION found"
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_VERSION=$(python --version | cut -d' ' -f2)
        log_success "Python $PYTHON_VERSION found"
        PYTHON_CMD="python"
    else
        log_error "Python not found. Please install Python 3.8 or higher."
        exit 1
    fi
    
    # Check Node.js
    if command_exists node; then
        NODE_VERSION=$(node --version)
        log_success "Node.js $NODE_VERSION found"
    else
        log_warning "Node.js not found. Will install via package manager."
        INSTALL_NODE=true
    fi
    
    # Check npm
    if command_exists npm; then
        NPM_VERSION=$(npm --version)
        log_success "npm $NPM_VERSION found"
    else
        log_warning "npm not found. Will install with Node.js."
    fi
    
    # Check git
    if command_exists git; then
        log_success "Git found"
    else
        log_error "Git not found. Please install Git first."
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    log_step "Installing system dependencies..."
    
    if [[ $OS == "macos" ]]; then
        # Check for Homebrew
        if ! command_exists brew; then
            log_info "Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        if [[ $INSTALL_NODE == true ]]; then
            log_info "Installing Node.js via Homebrew..."
            brew install node
        fi
        
        # Install other dependencies
        log_info "Installing additional dependencies..."
        brew install portaudio pkg-config
        
    elif [[ $OS == "linux" ]]; then
        log_info "Updating package manager..."
        sudo apt-get update
        
        if [[ $INSTALL_NODE == true ]]; then
            log_info "Installing Node.js..."
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
        fi
        
        # Install other dependencies
        log_info "Installing additional dependencies..."
        sudo apt-get install -y portaudio19-dev python3-dev python3-pip python3-venv pkg-config
    fi
    
    log_success "System dependencies installed"
}

# Setup Python virtual environment
setup_python_env() {
    log_step "Setting up Python virtual environment..."
    
    if [[ ! -d "venv" ]]; then
        log_info "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    log_info "Installing Python dependencies..."
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    else
        log_warning "requirements.txt not found, installing basic dependencies..."
        pip install fastapi uvicorn websockets bleak pyaudio whisper torch torchaudio
    fi
    
    log_success "Python environment setup complete"
}

# Setup frontend
setup_frontend() {
    log_step "Setting up frontend..."
    
    if [[ -d "frontend" ]]; then
        cd frontend
        
        log_info "Installing frontend dependencies..."
        npm install
        
        log_success "Frontend setup complete"
        cd ..
    else
        log_warning "Frontend directory not found"
    fi
}

# Configure ESP32S3
configure_esp32s3() {
    log_step "ESP32S3 Configuration"
    
    echo -e "${CYAN}ESP32S3 Setup Instructions:${NC}"
    echo "1. Connect your ESP32S3 via USB-C"
    echo "2. The firmware should already be flashed"
    echo "3. Device will advertise as: OMI-ESP32S3-BrutalAI"
    echo ""
    
    if ask_yes_no "Do you want to flash new firmware to ESP32S3?"; then
        setup_esp32s3_firmware
    fi
}

# Setup ESP32S3 firmware
setup_esp32s3_firmware() {
    log_info "Setting up ESP32S3 firmware..."
    
    # Check if arduino-cli is installed
    if ! command_exists arduino-cli; then
        log_info "Installing Arduino CLI..."
        if [[ $OS == "macos" ]]; then
            brew install arduino-cli
        else
            curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh
            sudo mv bin/arduino-cli /usr/local/bin/
        fi
    fi
    
    # Setup Arduino CLI
    log_info "Configuring Arduino CLI..."
    arduino-cli core update-index
    arduino-cli core install esp32:esp32
    
    # Check for ESP32S3 firmware
    if [[ -f "omi_firmware/esp32s3_ble/esp32s3_ble.ino" ]]; then
        log_info "Compiling ESP32S3 firmware..."
        cd omi_firmware/esp32s3_ble
        arduino-cli compile --fqbn esp32:esp32:esp32s3 esp32s3_ble.ino
        
        echo -e "${YELLOW}To upload firmware:${NC}"
        echo "1. Hold BOOT button on ESP32S3"
        echo "2. Press RESET while holding BOOT"
        echo "3. Release BOOT button"
        echo "4. Press Enter to continue..."
        read -r
        
        arduino-cli upload -p /dev/cu.usbmodem* --fqbn esp32:esp32:esp32s3 esp32s3_ble.ino
        cd ../..
        
        log_success "ESP32S3 firmware uploaded"
    else
        log_warning "ESP32S3 firmware not found"
    fi
}

# Test system
test_system() {
    log_step "Testing system components..."
    
    # Test Python imports
    log_info "Testing Python dependencies..."
    source venv/bin/activate
    $PYTHON_CMD -c "
import sys
sys.path.append('src')
try:
    from audio.bluetooth_connector import BluetoothOMIConnector
    print('✅ Bluetooth connector imported successfully')
except Exception as e:
    print(f'❌ Bluetooth import failed: {e}')
    
try:
    import whisper
    print('✅ Whisper imported successfully')
except Exception as e:
    print(f'❌ Whisper import failed: {e}')
"
    
    # Test ESP32S3 connection
    log_info "Testing ESP32S3 connection..."
    $PYTHON_CMD -c "
import asyncio
import sys
sys.path.append('src')
from audio.bluetooth_connector import BluetoothOMIConnector

async def test_esp32s3():
    try:
        connector = BluetoothOMIConnector(connection_type='ble', device_name='OMI-ESP32S3-BrutalAI')
        devices = await connector.scan_for_devices(timeout=5)
        if devices:
            print(f'✅ Found {len(devices)} ESP32S3 device(s)')
            for addr, name in devices.items():
                print(f'   - {name} ({addr})')
        else:
            print('❌ No ESP32S3 devices found')
            print('💡 Make sure ESP32S3 is powered on and advertising')
    except Exception as e:
        print(f'❌ ESP32S3 test failed: {e}')

asyncio.run(test_esp32s3())
"
    
    # Test frontend if it exists
    if [[ -d "frontend" ]]; then
        log_info "Testing frontend setup..."
        cd frontend
        if [[ -f "package.json" ]]; then
            echo "✅ Frontend package.json found"
            if [[ -d "node_modules" ]]; then
                echo "✅ Frontend dependencies installed"
            else
                echo "❌ Frontend dependencies missing"
            fi
        else
            echo "❌ Frontend package.json missing"
        fi
        cd ..
    fi
    
    log_success "System test complete"
}

# Create startup scripts
create_startup_scripts() {
    log_step "Creating startup scripts..."
    
    # Backend startup script
    cat > start_backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Brutally Honest AI Backend..."
source venv/bin/activate
python main_enhanced.py
EOF
    chmod +x start_backend.sh
    
    # Frontend startup script
    cat > start_frontend.sh << 'EOF'
#!/bin/bash
echo "🌐 Starting Brutally Honest AI Frontend..."
cd frontend
npm start
EOF
    chmod +x start_frontend.sh
    
    # Combined startup script
    cat > start_all.sh << 'EOF'
#!/bin/bash
echo "🎉 Starting Brutally Honest AI System..."
echo "======================================"

# Start backend in background
echo "Starting backend..."
source venv/bin/activate
python main_enhanced.py &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 8

# Start frontend in background
echo "Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!

# Wait for frontend to start
echo "Waiting for frontend to load..."
sleep 5

# Test services
echo ""
echo "🔍 Testing Services..."
echo "====================="

# Test backend
if curl -s http://localhost:8000/api/status >/dev/null; then
    echo "✅ Backend: http://localhost:8000 (Running)"
else
    echo "❌ Backend: Failed to start"
fi

# Test frontend
if curl -s http://localhost:3000 >/dev/null; then
    echo "✅ Frontend: http://localhost:3000 (Running)"
    echo ""
    echo "🌐 Opening frontend in browser..."
    if command -v open >/dev/null; then
        open http://localhost:3000
    elif command -v xdg-open >/dev/null; then
        xdg-open http://localhost:3000
    fi
else
    echo "❌ Frontend: Failed to start"
fi

echo ""
echo "🎯 System Ready!"
echo "================"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for interrupt
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
EOF
    chmod +x start_all.sh
    
    log_success "Startup scripts created"
}

# Main installation flow
main() {
    print_banner
    
    echo -e "${CYAN}Welcome to the Brutally Honest AI installer!${NC}"
    echo "This script will set up your ESP32S3 voice analysis system."
    echo ""
    
    if ! ask_yes_no "Continue with installation?"; then
        echo "Installation cancelled."
        exit 0
    fi
    
    echo ""
    log_step "Starting installation process..."
    
    # System checks
    check_system
    echo ""
    
    # Install dependencies
    if ask_yes_no "Install system dependencies?"; then
        install_system_deps
        echo ""
    fi
    
    # Python environment
    if ask_yes_no "Setup Python virtual environment?"; then
        setup_python_env
        echo ""
    fi
    
    # Frontend setup
    if ask_yes_no "Setup frontend?"; then
        setup_frontend
        echo ""
    fi
    
    # ESP32S3 configuration
    if ask_yes_no "Configure ESP32S3?"; then
        configure_esp32s3
        echo ""
    fi
    
    # Create startup scripts
    if ask_yes_no "Create startup scripts?"; then
        create_startup_scripts
        echo ""
    fi
    
    # Test system
    if ask_yes_no "Test system components?"; then
        test_system
        echo ""
    fi
    
    # Installation complete
    echo -e "${GREEN}"
    echo "🎉 INSTALLATION COMPLETE!"
    echo "========================="
    echo -e "${NC}"
    echo -e "${CYAN}Your Brutally Honest AI system is ready!${NC}"
    echo ""
    echo -e "${YELLOW}Quick Start:${NC}"
    echo "1. Run: ./start_all.sh"
    echo "2. Open: http://localhost:3000"
    echo "3. Click 'Start Recording'"
    echo "4. Speak into your ESP32S3"
    echo ""
    echo -e "${YELLOW}Individual Services:${NC}"
    echo "• Backend only: ./start_backend.sh"
    echo "• Frontend only: ./start_frontend.sh"
    echo ""
    echo -e "${YELLOW}ESP32S3 Device:${NC}"
    echo "• Name: OMI-ESP32S3-BrutalAI"
    echo "• Connection: Automatic via Bluetooth"
    echo ""
    
    if ask_yes_no "Start the system now?"; then
        echo ""
        log_info "Starting Brutally Honest AI system..."
        ./start_all.sh
    else
        echo ""
        echo -e "${CYAN}Run './start_all.sh' when you're ready to begin!${NC}"
    fi
}

# Run main function
main "$@"
