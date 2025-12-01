# Deployment Architecture

This guide explains how to set up the dual-domain deployment:
- **`brutallyhonest.io`** → Vercel (Landing page/marketing site)
- **`app.brutallyhonest.io`** → NVIDIA server (Full application with local AI)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         INTERNET                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┴────────────────────┐
         │                                         │
         ▼                                         ▼
┌─────────────────────┐               ┌─────────────────────────┐
│   brutallyhonest.io │               │  app.brutallyhonest.io  │
│      (Vercel)       │               │    (Your NVIDIA Server) │
│                     │               │                         │
│  • Landing Page     │               │  • Full Application     │
│  • Marketing        │    Links to   │  • Local Whisper        │
│  • Documentation    │ ────────────► │  • Local Ollama/LLAMA   │
│  • Public Info      │               │  • Voice Processing     │
│                     │               │  • Fact Checking        │
└─────────────────────┘               └─────────────────────────┘
       │                                        │
       │ Hosted on                              │ Runs on
       │ Vercel CDN                             │ Your Hardware
       ▼                                        ▼
┌─────────────────────┐               ┌─────────────────────────┐
│   Static Files      │               │   NVIDIA GPU Server     │
│   - index.html      │               │   - API Server (8000)   │
│   - logo.svg        │               │   - Frontend (3001)     │
│   - vercel.json     │               │   - Ollama (11434)      │
└─────────────────────┘               └─────────────────────────┘
```

---

## Step 1: Quick Setup via CLI

Run the automated setup script:

```bash
./setup_domains.sh
```

This will:
1. Deploy landing site to Vercel
2. Configure Cloudflare tunnel for app subdomain
3. Output DNS instructions for manual configuration

---

## Step 2: Cloudflare DNS Setup

### A. Main Domain (brutallyhonest.io → Vercel)

In Cloudflare Dashboard → DNS, add these records:

| Type | Name | Content | Proxy Status |
|------|------|---------|--------------|
| A | @ | 76.76.21.21 | DNS only (gray) |
| CNAME | www | cname.vercel-dns.com | DNS only (gray) |

### B. App Subdomain (app.brutallyhonest.io → NVIDIA Server via Tunnel)

The app subdomain uses Cloudflare Tunnel (already configured):

| Type | Name | Content | Proxy Status |
|------|------|---------|--------------|
| CNAME | app | brutally-honest.cfargotunnel.com | Proxied (orange) ✓ |

### C. Cloudflare Tunnel Setup (Already Active)

```bash
# On your NVIDIA server
cloudflared tunnel login
cloudflared tunnel create brutally-app

# Create config
cat > ~/.cloudflared/config.yml << EOF
tunnel: brutally-app
credentials-file: /home/brutally/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: app.brutallyhonest.io
    service: http://localhost:3001
  - hostname: api.brutallyhonest.io
    service: http://localhost:8000
  - service: http_status:404
EOF

# Route DNS
cloudflared tunnel route dns brutally-app app.brutallyhonest.io

# Start tunnel
cloudflared tunnel run brutally-app
```

---

## Step 2: Deploy Landing Site to Vercel

### A. Connect Repository

1. Go to [vercel.com](https://vercel.com)
2. Click **Add New** → **Project**
3. Import your Git repository
4. Set **Root Directory** to `landing-site`
5. Framework: **Other** (static site)
6. Click **Deploy**

### B. Configure Custom Domain

1. Go to **Project Settings** → **Domains**
2. Add `brutallyhonest.io`
3. Follow Vercel's DNS instructions:
   - Add CNAME record `@` → `cname.vercel-dns.com`
   - Or use Vercel nameservers

### C. Via CLI

```bash
cd landing-site

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set production domain
vercel --prod
```

---

## Step 3: Deploy Application to NVIDIA Server

### A. Run the Deployment Script

```bash
# From your local machine
./deploy_to_nvidia.sh
```

This will:
1. Sync code to the server
2. Install dependencies
3. Set up systemd services
4. Configure Ollama for local LLM

### B. Configure Server for app.brutallyhonest.io

SSH into your server and update the frontend environment:

```bash
ssh brutally@brutallyhonest.io

# Update frontend configuration
cd /home/brutally/brutally-honest-ai/frontend
echo "PORT=3001" > .env
echo "API_BASE=http://localhost:8000" >> .env

# Restart services
sudo systemctl restart brutally-honest-frontend
```

### C. Set Up HTTPS with Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d app.brutallyhonest.io

# Configure nginx reverse proxy
sudo tee /etc/nginx/sites-available/brutally-honest << 'EOF'
server {
    listen 80;
    server_name app.brutallyhonest.io;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.brutallyhonest.io;

    ssl_certificate /etc/letsencrypt/live/app.brutallyhonest.io/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.brutallyhonest.io/privkey.pem;

    location / {
        proxy_pass http://localhost:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/brutally-honest /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Step 4: Port Forwarding (If Not Using Cloudflare Tunnel)

On your router, forward these ports to your NVIDIA server:

| External Port | Internal Port | Service      |
|--------------|---------------|--------------|
| 80           | 80            | HTTP (nginx) |
| 443          | 443           | HTTPS (nginx)|
| 22 (or 2222) | 22            | SSH          |

---

## Step 5: Verify Setup

### Test Landing Site
```bash
curl -I https://brutallyhonest.io
# Should return 200 OK from Vercel
```

### Test Application
```bash
curl -I https://app.brutallyhonest.io
# Should return 200 OK from your server
```

### Test API
```bash
curl https://app.brutallyhonest.io/api/health
# Should return health status from your API
```

---

## Environment Variables

### Landing Site (Vercel)
No environment variables needed - it's a static site.

### Application Server (.env)

```bash
# /home/brutally/brutally-honest-ai/.env
API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=3001
WHISPER_MODEL=base
WHISPER_DEVICE=cuda
OLLAMA_URL=http://localhost:11434
LLM_MODEL=llama2:7b
```

### Frontend (.env)

```bash
# /home/brutally/brutally-honest-ai/frontend/.env
PORT=3001
API_BASE=http://localhost:8000
```

---

## Troubleshooting

### Landing site not loading
1. Check Vercel deployment logs
2. Verify DNS propagation: `dig brutallyhonest.io`
3. Check SSL certificate status in Vercel dashboard

### App subdomain not working
1. Check DNS: `dig app.brutallyhonest.io`
2. Verify server is running: `ssh brutally@brutallyhonest.io "systemctl status brutally-honest-frontend"`
3. Check firewall: `sudo ufw status`
4. Test locally on server: `curl localhost:3001`

### SSL issues on app subdomain
1. Renew certificates: `sudo certbot renew`
2. Check nginx config: `sudo nginx -t`
3. Verify certificate paths exist

---

## Quick Reference

| Domain | Points To | Purpose |
|--------|-----------|---------|
| `brutallyhonest.io` | Vercel | Landing page |
| `app.brutallyhonest.io` | Your Server | Full application |
| `api.brutallyhonest.io` | Your Server | API endpoints (optional) |

| Service | Port | Description |
|---------|------|-------------|
| Frontend | 3001 | Node.js web app |
| API | 8000 | Python FastAPI |
| Ollama | 11434 | Local LLM |
| nginx | 80/443 | Reverse proxy |

