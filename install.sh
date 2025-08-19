#!/bin/bash

# Voice Insight Platform - Complete Installation Script
# This script installs the entire project on any computer

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons"
        log_info "Please run as a regular user. The script will ask for sudo when needed."
        exit 1
    fi
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        if command -v apt-get &> /dev/null; then
            DISTRO="debian"
        elif command -v yum &> /dev/null; then
            DISTRO="redhat"
        elif command -v pacman &> /dev/null; then
            DISTRO="arch"
        else
            DISTRO="unknown"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        DISTRO="windows"
    else
        OS="unknown"
        DISTRO="unknown"
    fi
    
    log_info "Detected OS: $OS ($DISTRO)"
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check available memory
    if [[ "$OS" == "linux" ]]; then
        TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    elif [[ "$OS" == "macos" ]]; then
        TOTAL_MEM=$(( $(sysctl -n hw.memsize) / 1024 / 1024 / 1024 ))
    else
        TOTAL_MEM=8  # Assume 8GB if we can't detect
    fi
    
    if [[ $TOTAL_MEM -lt 8 ]]; then
        log_warning "System has ${TOTAL_MEM}GB RAM. 8GB+ recommended for optimal performance."
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "System has ${TOTAL_MEM}GB RAM - sufficient for the platform"
    fi
    
    # Check disk space (need at least 10GB)
    AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $AVAILABLE_SPACE -lt 10 ]]; then
        log_error "Insufficient disk space. Need at least 10GB, have ${AVAILABLE_SPACE}GB"
        exit 1
    fi
    
    log_success "System requirements check passed"
}

# Install system dependencies
install_system_deps() {
    log_info "Installing system dependencies..."
    
    case $DISTRO in
        "debian")
            sudo apt-get update
            sudo apt-get install -y \
                curl \
                wget \
                git \
                build-essential \
                python3 \
                python3-pip \
                python3-venv \
                python3-dev \
                ffmpeg \
                portaudio19-dev \
                libsndfile1-dev \
                libasound2-dev \
                libusb-1.0-0-dev \
                udev \
                nodejs \
                npm \
                ca-certificates \
                gnupg \
                lsb-release
            ;;
        "redhat")
            sudo yum update -y
            sudo yum install -y \
                curl \
                wget \
                git \
                gcc \
                gcc-c++ \
                make \
                python3 \
                python3-pip \
                python3-devel \
                ffmpeg \
                portaudio-devel \
                libsndfile-devel \
                alsa-lib-devel \
                libusb1-devel \
                nodejs \
                npm
            ;;
        "arch")
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm \
                curl \
                wget \
                git \
                base-devel \
                python \
                python-pip \
                ffmpeg \
                portaudio \
                libsndfile \
                alsa-lib \
                libusb \
                nodejs \
                npm
            ;;
        "macos")
            # Check if Homebrew is installed
            if ! command -v brew &> /dev/null; then
                log_info "Installing Homebrew..."
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            
            brew update
            brew install \
                python@3.11 \
                ffmpeg \
                portaudio \
                libsndfile \
                libusb \
                node \
                git \
                curl \
                wget
            ;;
        *)
            log_warning "Unknown distribution. Please install the following manually:"
            log_warning "- Python 3.8+"
            log_warning "- pip"
            log_warning "- ffmpeg"
            log_warning "- portaudio development libraries"
            log_warning "- libsndfile development libraries"
            log_warning "- libusb development libraries"
            log_warning "- Node.js and npm"
            log_warning "- git, curl, wget"
            read -p "Have you installed these dependencies? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
            ;;
    esac
    
    log_success "System dependencies installed"
}

# Install Docker
install_docker() {
    log_info "Installing Docker..."
    
    if command -v docker &> /dev/null; then
        log_info "Docker already installed"
        return
    fi
    
    case $DISTRO in
        "debian")
            # Add Docker's official GPG key
            sudo mkdir -p /etc/apt/keyrings
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
            
            # Add Docker repository
            echo \
                "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
                $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        "redhat")
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            ;;
        "arch")
            sudo pacman -S --noconfirm docker docker-compose
            ;;
        "macos")
            log_info "Please install Docker Desktop for Mac from: https://docs.docker.com/desktop/mac/install/"
            log_info "After installation, start Docker Desktop and return here."
            read -p "Press Enter when Docker Desktop is running..."
            ;;
        *)
            log_error "Please install Docker manually for your system"
            exit 1
            ;;
    esac
    
    # Add user to docker group (Linux only)
    if [[ "$OS" == "linux" ]]; then
        sudo usermod -aG docker $USER
        log_warning "You've been added to the docker group. You may need to log out and back in for this to take effect."
    fi
    
    # Start Docker service
    if [[ "$OS" == "linux" ]]; then
        sudo systemctl enable docker
        sudo systemctl start docker
    fi
    
    log_success "Docker installed successfully"
}

# Setup Python environment
setup_python() {
    log_info "Setting up Python environment..."
    
    # Check Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    REQUIRED_VERSION="3.8"
    
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
        log_error "Python 3.8+ is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    log_success "Python version check passed: $PYTHON_VERSION"
    
    # Create virtual environment
    if [[ ! -d "venv" ]]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    log_success "Python environment setup complete"
}

# Setup Node.js environment
setup_nodejs() {
    log_info "Setting up Node.js environment..."
    
    cd frontend
    
    # Install Node.js dependencies
    log_info "Installing Node.js dependencies..."
    npm install
    
    cd ..
    
    log_success "Node.js environment setup complete"
}

# Setup environment configuration
setup_environment() {
    log_info "Setting up environment configuration..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        log_info "Creating .env file from template..."
        cp env.example .env
        
        # Generate random secrets
        SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
        JWT_SECRET=$(openssl rand -hex 32 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex(32))")
        
        # Update .env with generated secrets
        sed -i.bak "s/your_secret_key_here/$SECRET_KEY/" .env
        sed -i.bak "s/your_jwt_secret_here/$JWT_SECRET/" .env
        rm .env.bak 2>/dev/null || true
        
        log_success ".env file created with generated secrets"
        log_warning "Please edit .env file to add your Hugging Face token and other configuration"
    else
        log_info ".env file already exists"
    fi
}

# Setup USB permissions for OMI DevKit
setup_usb_permissions() {
    if [[ "$OS" != "linux" ]]; then
        return
    fi
    
    log_info "Setting up USB permissions for OMI DevKit..."
    
    # Create udev rule for OMI DevKit
    sudo tee /etc/udev/rules.d/99-omi-devkit.rules > /dev/null << 'EOF'
# OMI DevKit 2 - Raspberry Pi Pico
SUBSYSTEM=="usb", ATTRS{idVendor}=="2e8a", ATTRS{idProduct}=="0005", MODE="0666", GROUP="plugdev"
SUBSYSTEM=="tty", ATTRS{idVendor}=="2e8a", ATTRS{idProduct}=="0005", MODE="0666", GROUP="plugdev"

# Generic USB-to-Serial adapters
SUBSYSTEM=="tty", ATTRS{interface}=="*Serial*", MODE="0666", GROUP="plugdev"
EOF
    
    # Add user to plugdev group
    sudo usermod -aG plugdev $USER
    
    # Reload udev rules
    sudo udevadm control --reload-rules
    sudo udevadm trigger
    
    log_success "USB permissions configured for OMI DevKit"
}

# Start Docker services
start_services() {
    log_info "Starting Docker services..."
    
    # Start databases and Ollama
    docker-compose up -d postgres qdrant ollama
    
    # Wait for services to be healthy
    log_info "Waiting for services to start..."
    sleep 10
    
    # Check service health
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
            log_success "PostgreSQL is ready"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_error "PostgreSQL failed to start"
            exit 1
        fi
        sleep 2
    done
    
    for i in {1..30}; do
        if curl -s http://localhost:6333/health >/dev/null 2>&1; then
            log_success "Qdrant is ready"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_error "Qdrant failed to start"
            exit 1
        fi
        sleep 2
    done
    
    for i in {1..30}; do
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            log_success "Ollama is ready"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_error "Ollama failed to start"
            exit 1
        fi
        sleep 2
    done
}

# Download LLM model
download_llm_model() {
    log_info "Downloading LLM model (this may take several minutes)..."
    
    # Pull Mistral 7B model
    docker-compose exec ollama ollama pull mistral:7b
    
    log_success "LLM model downloaded successfully"
}

# Initialize database
init_database() {
    log_info "Initializing database..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run database initialization
    python setup.py --setup
    
    log_success "Database initialized"
}

# Test installation
test_installation() {
    log_info "Testing installation..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Test components
    python setup.py --test
    
    # Test OMI connection
    python setup.py --check-omi
    
    log_success "Installation test completed"
}

# Create startup scripts
create_startup_scripts() {
    log_info "Creating startup scripts..."
    
    # Create start script
    cat > start.sh << 'EOF'
#!/bin/bash
# Start Voice Insight Platform

echo "Starting Voice Insight Platform..."

# Start Docker services
docker-compose up -d

# Wait for services
sleep 10

# Activate Python environment
source venv/bin/activate

# Start the application
python main.py
EOF
    
    chmod +x start.sh
    
    # Create stop script
    cat > stop.sh << 'EOF'
#!/bin/bash
# Stop Voice Insight Platform

echo "Stopping Voice Insight Platform..."

# Stop Docker services
docker-compose down

echo "Platform stopped"
EOF
    
    chmod +x stop.sh
    
    log_success "Startup scripts created"
}

# Main installation function
main() {
    echo "=================================================="
    echo "  Voice Insight Platform - Installation Script"
    echo "=================================================="
    echo
    
    check_root
    detect_os
    check_requirements
    
    log_info "Starting installation process..."
    
    # Install system dependencies
    install_system_deps
    
    # Install Docker
    install_docker
    
    # Setup Python environment
    setup_python
    
    # Setup Node.js environment
    setup_nodejs
    
    # Setup environment configuration
    setup_environment
    
    # Setup USB permissions (Linux only)
    setup_usb_permissions
    
    # Start Docker services
    start_services
    
    # Download LLM model
    download_llm_model
    
    # Initialize database
    init_database
    
    # Create startup scripts
    create_startup_scripts
    
    # Test installation
    test_installation
    
    echo
    echo "=================================================="
    echo "  Installation Complete!"
    echo "=================================================="
    echo
    log_success "Voice Insight Platform has been successfully installed!"
    echo
    echo "Next steps:"
    echo "1. Edit .env file with your configuration:"
    echo "   - Add your Hugging Face token"
    echo "   - Update any other settings as needed"
    echo
    echo "2. Connect your OMI DevKit 2 via USB-C"
    echo
    echo "3. Start the platform:"
    echo "   ./start.sh"
    echo
    echo "4. Access the platform at: http://localhost:8000"
    echo
    echo "5. To stop the platform:"
    echo "   ./stop.sh"
    echo
    if [[ "$OS" == "linux" ]]; then
        echo "Note: You may need to log out and back in for Docker permissions to take effect."
    fi
    echo
    echo "For troubleshooting, check the README.md file."
    echo "=================================================="
}

# Run main function
main "$@"
