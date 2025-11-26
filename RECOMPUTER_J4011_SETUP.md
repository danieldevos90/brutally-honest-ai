# reComputer J4011 Setup Guide for Brutally Honest AI

## 📋 Overview

This guide will help you set up your **reComputer J4011** (NVIDIA Jetson-based) with the Brutally Honest AI project. The reComputer J4011 runs **NVIDIA JetPack** (Ubuntu-based), which is optimized for AI workloads.

## 🔑 Important Notes

### Understanding the Setup Process

1. **Device OS**: The reComputer J4011 runs **JetPack (Ubuntu)** - this is the operating system ON the device
2. **Host Computer**: You need a computer to flash JetPack TO the device (can be macOS, Windows, or Linux)
3. **Project Setup**: Once JetPack is installed, you'll set up the Brutally Honest AI project ON the device

## 🚀 Part 1: Flashing JetPack to reComputer J4011 (from macOS)

### Option A: Using Ubuntu Live USB (Recommended - Most Reliable)

**This is the most reliable method and doesn't require Docker or VMs.**

1. **Create Ubuntu Live USB**:
   ```bash
   # Download Ubuntu 24.04.3 LTS ISO (latest LTS version)
   # Visit: https://ubuntu.com/download/desktop
   # File size: ~5.9GB
   
   # Create bootable USB using Balena Etcher (macOS)
   # Download: https://www.balena.io/etcher
   ```

2. **Boot from USB**:
   - Insert USB drive
   - Restart Mac and hold `Option` key during boot
   - Select USB drive
   - Choose "Try Ubuntu" (don't install)

3. **Follow Seeed Studio's Guide**:
   - Visit: https://wiki.seeedstudio.com/reComputer_J4012_Flash_Jetpack/
   - Connect reComputer J4011 via USB
   - Follow the flashing instructions from Ubuntu live environment

### Option B: Using Docker (Alternative - May Have Issues)

⚠️ **Note**: Docker on macOS may hang or have issues with privileged mode required for flashing.

If Docker is not responding:
1. Force quit Docker Desktop: `Cmd+Q` or Activity Monitor
2. Restart Docker Desktop
3. Consider using Ubuntu Live USB instead (Option A)

```bash
# 1. Install Docker Desktop for Mac
# Download from: https://www.docker.com/products/docker-desktop

# 2. Pull NVIDIA Jetson SDK Manager Docker image
docker pull nvcr.io/nvidia/l4t-base:r35.2.1

# 3. Run SDK Manager in Docker
docker run -it --rm \
  --privileged \
  -v /dev:/dev \
  -v $(pwd):/workspace \
  nvcr.io/nvidia/l4t-base:r35.2.1 \
  bash

# Inside Docker container, follow Seeed Studio's flashing guide
```

### Option C: Using Virtual Machine (Alternative)

**Using Parallels/VMware Fusion with Ubuntu**:
- Install Ubuntu 24.04 LTS in VM
- Enable USB passthrough for Jetson device
- Follow Seeed Studio's flashing guide from VM

⚠️ **Note**: USB passthrough in VMs can be unreliable. Ubuntu Live USB (Option A) is recommended.

### Option D: Pre-flashed Device

If your reComputer J4011 already has JetPack installed, skip to **Part 2**.

## 🖥️ Part 2: Setting Up Brutally Honest AI on reComputer J4011

Once JetPack is installed and the device is running, SSH into it or connect a monitor/keyboard.

### Step 1: Update System Packages

```bash
# Update package lists
sudo apt-get update
sudo apt-get upgrade -y

# Install essential build tools
sudo apt-get install -y \
    python3-pip \
    python3-venv \
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
    libxext6
```

### Step 2: Install Node.js (for frontend)

```bash
# Install Node.js 18.x LTS (ARM64)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify installation
node --version
npm --version
```

### Step 3: Clone and Setup Project

```bash
# Clone repository (or transfer files via SCP)
git clone <your-repo-url> brutally-honest-ai
cd brutally-honest-ai

# Or if transferring from Mac:
# On Mac: scp -r brutally-honest-ai jetson@<jetson-ip>:~/
```

### Step 4: Run the Jetson Setup Script

```bash
# Make setup script executable
chmod +x setup_recomputer_j4011.sh

# Run the setup script
./setup_recomputer_j4011.sh
```

The script will:
- ✅ Create Python virtual environment
- ✅ Install Python dependencies (ARM64 compatible)
- ✅ Setup frontend dependencies
- ✅ Configure system services
- ✅ Install Ollama (ARM64 version)
- ✅ Download Whisper models
- ✅ Create startup scripts

### Step 5: Manual Configuration (if needed)

```bash
# Create .env file
cp env.example .env

# Edit configuration
nano .env

# Key settings for Jetson:
# - Use localhost for all services
# - Adjust model sizes based on available RAM
# - Consider using smaller Whisper models (base/tiny)
```

### Step 6: Install Ollama (ARM64)

```bash
# Install Ollama for ARM64
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Pull a smaller model optimized for Jetson
ollama pull tinyllama:latest
# or
ollama pull phi:latest  # Microsoft Phi - very efficient
```

### Step 7: Test Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Test Python dependencies
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import whisper; print('Whisper OK')"

# Test Ollama
ollama list
ollama run tinyllama "Hello"
```

## 🎯 Part 3: Running the Application

### Start All Services

```bash
# Use the unified startup script
./start_app.sh

# Or start individually:
# Terminal 1 - Backend
source venv/bin/activate
python api_server.py

# Terminal 2 - Frontend
cd frontend
npm start
```

### Access the Web Interface

Once running, access from any device on your network:
- **Local**: http://localhost:3001
- **Network**: http://<jetson-ip>:3001
- **API Docs**: http://<jetson-ip>:8000/docs

## 🔧 Jetson-Specific Optimizations

### Memory Management

Jetson devices have limited RAM. Optimize by:

```bash
# Use smaller Whisper models
# In your code, use: whisper.load_model("base") or "tiny"

# Use smaller LLM models
# Prefer: tinyllama, phi, or llama2:7b (quantized)

# Enable swap if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### CUDA Acceleration

JetPack includes CUDA. Some packages can use GPU acceleration:

```bash
# Verify CUDA is available
nvcc --version
nvidia-smi

# PyTorch should detect CUDA automatically
python -c "import torch; print(torch.cuda.is_available())"
```

### Performance Tuning

```bash
# Set Jetson to maximum performance mode
sudo nvpmodel -m 0
sudo jetson_clocks

# Check current mode
sudo nvpmodel -q
```

## 🐛 Troubleshooting

### Issue: Package Installation Fails

**Solution**: Some packages may not have ARM64 wheels. Install build dependencies:

```bash
sudo apt-get install -y python3-dev python3-numpy-dev
pip install --no-cache-dir <package-name>
```

### Issue: Out of Memory

**Solution**: Use smaller models and enable swap:

```bash
# Use tiny Whisper model
whisper.load_model("tiny")

# Use smaller LLM
ollama pull tinyllama:latest
```

### Issue: Bluetooth Not Working

**Solution**: Install Bluetooth stack:

```bash
sudo apt-get install -y bluez bluez-tools
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

### Issue: Frontend Build Fails

**Solution**: Increase Node.js memory:

```bash
export NODE_OPTIONS="--max-old-space-size=2048"
npm install
```

## 📱 Connecting ESP32S3 Devices

The reComputer J4011 can connect to ESP32S3 devices via:

1. **Bluetooth**: Built-in Bluetooth support
2. **USB**: Connect ESP32S3 via USB-C adapter
3. **WiFi**: ESP32S3 can connect to Jetson's WiFi network

## 🔄 Auto-Start on Boot

Create a systemd service to auto-start the application:

```bash
# Create service file
sudo nano /etc/systemd/system/brutally-honest-ai.service
```

Add this content:

```ini
[Unit]
Description=Brutally Honest AI Service
After=network.target

[Service]
Type=simple
User=jetson
WorkingDirectory=/home/jetson/brutally-honest-ai
Environment="PATH=/home/jetson/brutally-honest-ai/venv/bin"
ExecStart=/home/jetson/brutally-honest-ai/venv/bin/python api_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable brutally-honest-ai.service
sudo systemctl start brutally-honest-ai.service
```

## 📚 Additional Resources

- **Seeed Studio Wiki**: https://wiki.seeedstudio.com/reComputer_J4012_Flash_Jetpack/
- **NVIDIA Jetson Documentation**: https://developer.nvidia.com/embedded/jetson-linux
- **JetPack SDK**: https://developer.nvidia.com/embedded/jetpack

## ✅ Verification Checklist

- [ ] JetPack installed and device boots
- [ ] Python 3.8+ installed
- [ ] Node.js 18+ installed
- [ ] Project cloned and dependencies installed
- [ ] Ollama installed and model downloaded
- [ ] Whisper model downloaded
- [ ] Backend starts without errors
- [ ] Frontend builds and runs
- [ ] Web interface accessible
- [ ] ESP32S3 can connect (if applicable)

## 🎉 Next Steps

1. Configure your `.env` file with proper settings
2. Test audio recording and transcription
3. Connect your ESP32S3 devices
4. Upload documents to the knowledge base
5. Start using Brutally Honest AI!

---

**Note**: The reComputer J4011 is a powerful edge AI device. With proper optimization, it can run the entire Brutally Honest AI stack efficiently!

