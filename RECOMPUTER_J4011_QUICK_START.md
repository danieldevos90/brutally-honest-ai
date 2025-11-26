# reComputer J4011 - Quick Start Guide

## 🚀 Fast Setup (5 Minutes)

### Prerequisites
- reComputer J4011 with JetPack installed
- Internet connection
- SSH access or direct terminal access

### Step 1: Clone & Setup
```bash
git clone <your-repo> brutally-honest-ai
cd brutally-honest-ai
chmod +x setup_recomputer_j4011.sh
./setup_recomputer_j4011.sh
```

### Step 2: Configure
```bash
cp env.example .env
nano .env  # Edit with your settings
```

### Step 3: Run
```bash
./start_app_jetson.sh
```

### Step 4: Access
- Frontend: http://localhost:3001
- API: http://localhost:8000/docs

## 📋 Flashing JetPack from macOS

### Option 1: Docker (Recommended)
```bash
# Install Docker Desktop
# Pull Jetson SDK Manager image
docker pull nvcr.io/nvidia/l4t-base:r35.2.1

# Run SDK Manager
docker run -it --rm --privileged -v /dev:/dev nvcr.io/nvidia/l4t-base:r35.2.1 bash
```

### Option 2: Ubuntu Live USB (Recommended)
1. Download Ubuntu 24.04.3 LTS ISO (~5.9GB) from https://ubuntu.com/download/desktop
2. Create bootable USB with Balena Etcher
3. Boot from USB (hold Option key on Mac, choose "Try Ubuntu")
4. Follow: https://wiki.seeedstudio.com/reComputer_J4012_Flash_Jetpack/

## ⚡ Performance Tips

```bash
# Max performance mode
sudo nvpmodel -m 0
sudo jetson_clocks

# Use smaller models
whisper.load_model("base")  # Instead of "medium"
ollama pull tinyllama:latest  # Instead of larger models
```

## 🔧 Common Issues

**Out of Memory?**
- Use `tiny` Whisper model
- Use `tinyllama` LLM
- Enable swap: `sudo fallocate -l 4G /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`

**Package Installation Fails?**
```bash
sudo apt-get install python3-dev build-essential
pip install --no-cache-dir <package>
```

**Bluetooth Not Working?**
```bash
sudo apt-get install bluez bluez-tools
sudo systemctl enable bluetooth
sudo systemctl start bluetooth
```

## 📚 Full Documentation

See `RECOMPUTER_J4011_SETUP.md` for complete guide.

