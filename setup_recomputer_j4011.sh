#!/bin/bash

# Brutally Honest AI - reComputer J4011 Setup Script
# This script sets up the project on NVIDIA Jetson-based reComputer J4011

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}▶ $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# Check if running on Jetson
check_jetson() {
    log_step "Checking System Architecture"
    
    if [ -f /etc/nv_tegra_release ]; then
        log_success "Detected NVIDIA Jetson device"
        cat /etc/nv_tegra_release
        return 0
    else
        log_warning "Not running on Jetson - some optimizations may not apply"
        return 1
    fi
}

# Check system requirements
check_system() {
    log_step "Checking System Requirements"
    
    # Check Python version
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        log_success "Python found: $PYTHON_VERSION"
        
        # Check if Python 3.8+
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
        
        if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
            log_error "Python 3.8 or higher is required"
            exit 1
        fi
    else
        log_error "Python 3 not found. Install with: sudo apt-get install python3 python3-pip"
        exit 1
    fi
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_success "Node.js found: $NODE_VERSION"
    else
        log_warning "Node.js not found. Will install in next step."
    fi
    
    # Check available memory
    TOTAL_MEM=$(free -m | awk 'NR==2{printf "%.0f", $2}')
    log_info "Total RAM: ${TOTAL_MEM}MB"
    
    if [ "$TOTAL_MEM" -lt 4096 ]; then
        log_warning "Low memory detected. Consider using smaller models (tiny/base)."
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    log_info "Available disk space: ${AVAILABLE_SPACE}GB"
    
    if [ "$AVAILABLE_SPACE" -lt 10 ]; then
        log_warning "Low disk space. Ensure at least 10GB free."
    fi
}

# Install system dependencies
install_system_deps() {
    log_step "Installing System Dependencies"
    
    log_info "Updating package lists..."
    sudo apt-get update
    
    log_info "Installing essential packages..."
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
        curl \
        wget \
        build-essential \
        cmake \
        pkg-config \
        portaudio19-dev \
        libffi-dev \
        libssl-dev \
        ffmpeg \
        libsm6 \
        libxext6 \
        libasound2-dev \
        libportaudio2 \
        libportaudiocpp0 \
        bluez \
        bluez-tools || log_warning "Some packages failed to install"
    
    log_success "System dependencies installed"
}

# Install Node.js
install_nodejs() {
    log_step "Installing Node.js"
    
    if command -v node &> /dev/null; then
        log_info "Node.js already installed: $(node --version)"
        return 0
    fi
    
    log_info "Installing Node.js 18.x LTS..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    sudo apt-get install -y nodejs
    
    log_success "Node.js installed: $(node --version)"
    log_success "npm installed: $(npm --version)"
}

# Setup Python environment
setup_python_env() {
    log_step "Setting Up Python Environment"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    # Install PyTorch for Jetson (if available)
    log_info "Checking PyTorch installation..."
    if ! python -c "import torch" 2>/dev/null; then
        log_info "PyTorch not found. Installing PyTorch for Jetson..."
        # PyTorch for Jetson (pre-built wheels)
        pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu118 || \
        pip install torch torchvision torchaudio || \
        log_warning "PyTorch installation may need manual setup"
    else
        log_success "PyTorch already installed"
    fi
    
    # Install project dependencies
    log_info "Installing Python dependencies..."
    
    # Create a Jetson-optimized requirements file if needed
    if [ -f "requirements_jetson.txt" ]; then
        log_info "Using Jetson-optimized requirements..."
        pip install -r requirements_jetson.txt
    else
        log_info "Installing standard requirements..."
        pip install -r requirements.txt || log_warning "Some packages may have failed"
    fi
    
    # Install additional Jetson-specific packages
    log_info "Installing Jetson-specific packages..."
    pip install numpy --upgrade || true
    
    log_success "Python environment setup complete"
}

# Setup frontend
setup_frontend() {
    log_step "Setting Up Frontend"
    
    if [ ! -d "frontend" ]; then
        log_error "Frontend directory not found"
        return 1
    fi
    
    cd frontend
    
    # Increase Node.js memory for build
    export NODE_OPTIONS="--max-old-space-size=2048"
    
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install
        log_success "Frontend dependencies installed"
    else
        log_info "Frontend dependencies already installed"
    fi
    
    cd ..
    log_success "Frontend setup complete"
}

# Install Ollama
install_ollama() {
    log_step "Installing Ollama"
    
    if command -v ollama &> /dev/null; then
        log_info "Ollama already installed: $(ollama --version)"
    else
        log_info "Installing Ollama for ARM64..."
        curl -fsSL https://ollama.ai/install.sh | sh
        log_success "Ollama installed"
    fi
    
    # Start Ollama service
    if ! pgrep -f "ollama serve" > /dev/null; then
        log_info "Starting Ollama service..."
        ollama serve > /dev/null 2>&1 &
        sleep 3
        log_success "Ollama service started"
    else
        log_info "Ollama service already running"
    fi
    
    # Pull a small model optimized for Jetson
    log_info "Checking for TinyLlama model..."
    if ! ollama list 2>/dev/null | grep -q "tinyllama"; then
        log_info "Pulling TinyLlama model (optimized for Jetson)..."
        ollama pull tinyllama:latest || log_warning "Model pull failed - you can pull manually later"
    else
        log_success "TinyLlama model already available"
    fi
}

# Download Whisper models
setup_whisper() {
    log_step "Setting Up Whisper"
    
    source venv/bin/activate
    
    log_info "Testing Whisper installation..."
    python -c "import whisper; print('Whisper OK')" 2>/dev/null || {
        log_warning "Whisper not installed properly"
        return 1
    }
    
    log_info "Pre-downloading Whisper base model (recommended for Jetson)..."
    python -c "
import whisper
try:
    print('Downloading Whisper base model...')
    model = whisper.load_model('base')
    print('✅ Whisper base model ready')
except Exception as e:
    print(f'⚠️  Model download failed: {e}')
    print('💡 Model will be downloaded on first use')
" || log_warning "Whisper model download had issues"
    
    log_success "Whisper setup complete"
}

# Create startup scripts
create_startup_scripts() {
    log_step "Creating Startup Scripts"
    
    # Create Jetson-optimized startup script
    cat > start_app_jetson.sh << 'EOF'
#!/bin/bash
# Brutally Honest AI - Jetson Startup Script

set -e

echo "🚀 Starting Brutally Honest AI on Jetson..."
echo "=========================================="

# Set Jetson to max performance (optional)
if command -v nvpmodel &> /dev/null; then
    echo "⚡ Setting Jetson to maximum performance mode..."
    sudo nvpmodel -m 0
    sudo jetson_clocks
fi

# Activate virtual environment
source venv/bin/activate

# Start Ollama if not running
if ! pgrep -f "ollama serve" > /dev/null; then
    echo "🦙 Starting Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

# Start backend
echo "📡 Starting backend server..."
python api_server.py &
BACKEND_PID=$!

sleep 3

# Start frontend
echo "🌐 Starting frontend server..."
cd frontend
npm start &
FRONTEND_PID=$!

cd ..

echo ""
echo "✅ Brutally Honest AI is running!"
echo "📡 Backend: http://localhost:8000"
echo "🌐 Frontend: http://localhost:3001"
echo ""
echo "Press Ctrl+C to stop"

# Wait for processes
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
EOF
    
    chmod +x start_app_jetson.sh
    log_success "Startup script created: start_app_jetson.sh"
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating .env file from template..."
        if [ -f "env.example" ]; then
            cp env.example .env
            log_success ".env file created - please edit with your settings"
        fi
    fi
}

# Main installation flow
main() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║   Brutally Honest AI - reComputer J4011 Setup          ║"
    echo "║   NVIDIA Jetson Installation Script                     ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
    
    # Check if running as root
    if [ "$EUID" -eq 0 ]; then
        log_error "Please do not run this script as root"
        exit 1
    fi
    
    # Check Jetson
    check_jetson
    
    # System checks
    check_system
    
    # Ask for confirmation
    echo ""
    read -p "Continue with installation? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installation cancelled"
        exit 0
    fi
    
    # Install system dependencies
    read -p "Install system dependencies? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_system_deps
    fi
    
    # Install Node.js
    if ! command -v node &> /dev/null; then
        read -p "Install Node.js? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_nodejs
        fi
    fi
    
    # Setup Python environment
    read -p "Setup Python environment? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_python_env
    fi
    
    # Setup frontend
    read -p "Setup frontend? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_frontend
    fi
    
    # Install Ollama
    read -p "Install Ollama and download models? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_ollama
    fi
    
    # Setup Whisper
    read -p "Download Whisper models? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_whisper
    fi
    
    # Create startup scripts
    create_startup_scripts
    
    # Installation complete
    echo ""
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║           🎉 INSTALLATION COMPLETE! 🎉                  ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${CYAN}Your Brutally Honest AI system is ready on Jetson!${NC}"
    echo ""
    echo -e "${YELLOW}Quick Start:${NC}"
    echo "1. Edit .env file with your configuration"
    echo "2. Run: ./start_app_jetson.sh"
    echo "3. Open: http://localhost:3001"
    echo ""
    echo -e "${YELLOW}Jetson Optimizations:${NC}"
    echo "• Use 'base' or 'tiny' Whisper models for better performance"
    echo "• Use 'tinyllama' or 'phi' LLM models for lower memory usage"
    echo "• Run 'sudo nvpmodel -m 0 && sudo jetson_clocks' for max performance"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "• Configure your .env file"
    echo "• Connect ESP32S3 devices via Bluetooth or USB"
    echo "• Start using Brutally Honest AI!"
    echo ""
}

# Run main function
main

