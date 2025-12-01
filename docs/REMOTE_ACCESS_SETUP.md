# Remote Access Setup Guide

Deploy to your Brutally Honest AI system from anywhere in the world.

---

## 🚀 Quick Reference

| Access | Local Network | External (Port Forwarded) |
|--------|---------------|---------------------------|
| **SSH** | `ssh brutally@192.168.2.33` | `ssh brutally@brutallyhonest.io -p 22` |
| **Frontend** | http://192.168.2.33:3001 | http://brutallyhonest.io:3001 |
| **API** | http://192.168.2.33:8000 | http://brutallyhonest.io:8000 |
| **API Docs** | http://192.168.2.33:8000/docs | http://brutallyhonest.io:8000/docs |

**Credentials:**
- Username: `brutally`
- Password: `Welcome12!`

---

## 🚀 Deployment Commands

```bash
# Quick deploy (sync files + restart)
./deploy.sh

# Full deploy (reinstall dependencies)
./deploy.sh --full

# Create release and deploy
./deploy.sh --release v1.2.3

# Rollback to previous version
./deploy.sh --rollback

# Check status
./deploy.sh --status

# View logs
./deploy.sh --logs
./deploy.sh --logs-frontend
```

---

## 🔧 Setting Up External Access (brutallyhonest.io)

Since `brutallyhonest.io` is behind Cloudflare (which only proxies HTTP/HTTPS), you need ONE of these options for SSH and direct port access:

### Option A: Cloudflare DNS-Only Subdomain (Recommended)

1. Go to Cloudflare Dashboard → DNS
2. Create a new A record:
   - Name: `ssh` (or `server`)
   - IPv4: Your public IP (find it at https://whatismyip.com)
   - Proxy status: **DNS only** (gray cloud, NOT orange)
3. Set up port forwarding on your router (see below)
4. Now you can SSH via: `ssh brutally@ssh.brutallyhonest.io`

### Option B: Port Forwarding on Router

Forward these ports on your router to `192.168.2.33`:

| External Port | Internal Port | Service |
|---------------|---------------|---------|
| 22 (or 2222) | 22 | SSH |
| 3001 | 3001 | Frontend |
| 8000 | 8000 | API |

**Router setup:**
1. Log into router admin (usually http://192.168.1.1 or http://192.168.2.1)
2. Find "Port Forwarding" or "NAT" settings
3. Add the rules above pointing to `192.168.2.33`

### Option C: Cloudflare Tunnel (Most Secure, No Port Forwarding)

See the Cloudflare Tunnel section below for full setup.

---

## 🔐 First-Time SSH Key Setup

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "brutally-deploy"

# Copy your SSH key to the server (local network)
ssh-copy-id brutally@192.168.2.33
# Password: Welcome12!

# Verify passwordless login works
ssh brutally@192.168.2.33 "echo 'SSH key setup successful!'"

# For external access (after port forwarding):
ssh-copy-id -p 22 brutally@brutallyhonest.io
```

---

## Alternative Access Methods

### Quick Comparison

| Method | Difficulty | Security | Speed | Requirements |
|--------|------------|----------|-------|--------------|
| **Direct (brutallyhonest.io)** | ⭐ Easy | ⭐⭐ Medium | Fast | SSH key |
| **Tailscale** | ⭐ Easy | ⭐⭐⭐ High | Fast | Account + App |
| **Cloudflare Tunnel** | ⭐⭐ Medium | ⭐⭐⭐ High | Fast | Domain + Cloudflare |
| **Port Forwarding** | ⭐⭐ Medium | ⭐⭐ Medium | Fast | Router Access |
| **Jump Host** | ⭐⭐⭐ Advanced | ⭐⭐⭐ High | Medium | VPS/Server |

---

## 🛡️ Option 1: Tailscale (Recommended for Secure Access)

Tailscale creates a secure mesh VPN that "just works". Best for personal/small team use.

### Setup on Remote Device (Jetson/Server)

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate (opens browser or shows URL)
sudo tailscale up

# Note your machine name (e.g., "brutally-jetson")
tailscale status
```

### Setup on Your Local Machine

1. Download Tailscale from https://tailscale.com/download
2. Sign in with same account
3. Both machines now see each other!

### Deploy via Tailscale

```bash
# Using the script
./ota_deploy.sh --tailscale brutally-jetson

# Or set environment variable
export TAILSCALE_HOST="brutally-jetson"
./ota_deploy.sh
```

### Web Interface

In the deployment page, select **Tailscale** and enter your machine name.

---

## ☁️ Option 2: Cloudflare Tunnel (Free, No Port Forwarding)

Cloudflare Tunnel creates a secure connection without opening any ports.

### Prerequisites
- A domain name (can be free from Freenom, or use any domain)
- Cloudflare account (free)

### Setup on Remote Device

```bash
# Download cloudflared (ARM64 for Jetson)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# For x86_64 servers:
# curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared

# Login to Cloudflare
cloudflared tunnel login

# Create a tunnel
cloudflared tunnel create brutally-ssh

# Create config file
mkdir -p ~/.cloudflared
cat > ~/.cloudflared/config.yml << EOF
tunnel: brutally-ssh
credentials-file: /home/brutally/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: ssh.yourdomain.com
    service: ssh://localhost:22
  - service: http_status:404
EOF

# Route DNS
cloudflared tunnel route dns brutally-ssh ssh.yourdomain.com

# Run the tunnel (or create systemd service)
cloudflared tunnel run brutally-ssh
```

### Create Systemd Service (Auto-start)

```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
```

### Setup on Local Machine

```bash
# Install cloudflared
# macOS:
brew install cloudflared

# Or download from:
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

### Deploy via Cloudflare

```bash
# Using the script
./ota_deploy.sh --cloudflare ssh.yourdomain.com

# Or set environment variable  
export CLOUDFLARE_HOST="ssh.yourdomain.com"
./ota_deploy.sh
```

---

## 📡 Option 3: Port Forwarding + Dynamic DNS

Traditional method - forward SSH port through your router.

### Step 1: Configure Router

1. Log into your router admin panel (usually 192.168.1.1)
2. Find "Port Forwarding" or "Virtual Server"
3. Add a rule:
   - External Port: 2222 (or any unused port, avoid 22)
   - Internal IP: Your Jetson's local IP
   - Internal Port: 22
   - Protocol: TCP

### Step 2: Set Up Dynamic DNS (if your IP changes)

Free options:
- **DuckDNS** (https://www.duckdns.org)
- **No-IP** (https://www.noip.com)
- **Dynu** (https://www.dynu.com)

Example with DuckDNS:

```bash
# On your Jetson, create update script
cat > ~/duckdns-update.sh << 'EOF'
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=YOUR_DOMAIN&token=YOUR_TOKEN&ip=" | curl -k -o ~/duckdns.log -K -
EOF

chmod +x ~/duckdns-update.sh

# Add to crontab (updates every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * ~/duckdns-update.sh") | crontab -
```

### Deploy via Port Forwarding

```bash
# Using the script
./ota_deploy.sh -h brutally@yourdomain.duckdns.org -p 2222

# Or with environment variables
export REMOTE_HOST="brutally@yourdomain.duckdns.org"
export SSH_PORT="2222"
./ota_deploy.sh
```

---

## 🔀 Option 4: Jump Host / Bastion

Use an intermediate server (VPS) to reach your internal network.

### Architecture

```
Your Machine → Jump Host (VPS) → Internal Jetson
                  ↓
            (SSH ProxyJump)
```

### Setup

1. Have a VPS with public IP (DigitalOcean, Linode, AWS, etc.)
2. Set up SSH from Jump Host to internal Jetson
3. Deploy:

```bash
./ota_deploy.sh -J user@bastion.example.com -h brutally@internal-ip
```

---

## 🔐 SSH Key Setup

All methods require passwordless SSH. Set this up first:

```bash
# Generate key if you don't have one
ssh-keygen -t ed25519 -C "brutally-deploy"

# Copy to remote device
ssh-copy-id brutally@brutallyhonest.io
# Enter password when prompted: welcome12!

# Test passwordless login
ssh brutally@brutallyhonest.io "echo 'Success!'"
```

---

## 🖥️ Using the Web Interface

1. Go to **http://localhost:3001/deployment** (or your frontend URL)
2. Select your access method tab
3. Fill in the configuration
4. Click **Save & Test Configuration**
5. Use **Quick Deploy** or **Full Deploy**

---

## Troubleshooting

### Connection Timeout

```bash
# Test SSH connection directly
ssh -v brutally@brutallyhonest.io

# Check if port is open
nc -zv brutallyhonest.io 22
```

### Permission Denied

```bash
# Make sure SSH key is added
ssh-add -l

# Re-copy the key
ssh-copy-id -i ~/.ssh/id_ed25519 brutally@brutallyhonest.io
```

### Tailscale Not Connecting

```bash
# Check status
tailscale status

# Re-authenticate
sudo tailscale up --reset
```

### Cloudflare Tunnel Issues

```bash
# Check tunnel status
cloudflared tunnel info brutally-ssh

# Check logs
sudo journalctl -u cloudflared -f
```

---

## Security Best Practices

1. **Use SSH keys** - Never password authentication over internet
2. **Use non-standard ports** - Makes scanning harder
3. **Enable fail2ban** - Block brute force attempts
4. **Keep software updated** - Regular security patches
5. **Use Tailscale/Cloudflare** - They handle encryption and auth

```bash
# Install fail2ban on Jetson
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

---

## Service Management on Remote

```bash
# SSH into the server
ssh brutally@brutallyhonest.io

# Check service status
sudo systemctl status brutally-honest-api
sudo systemctl status brutally-honest-frontend

# View logs
sudo journalctl -u brutally-honest-api -f
sudo journalctl -u brutally-honest-frontend -f

# Restart services
sudo systemctl restart brutally-honest-api
sudo systemctl restart brutally-honest-frontend
```
