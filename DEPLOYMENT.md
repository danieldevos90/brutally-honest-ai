# Brutally Honest AI - Production Deployment Guide

## Quick Start

```bash
# 1. Clone and setup
git clone <repo-url>
cd brutally-honest-ai

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Configure environment
cp .env.production .env
# CRITICAL: Edit .env and change ALL security values

# 5. Start services
./start_production.sh
```

## Pre-Deployment Checklist

### Security (CRITICAL)

- [ ] **MASTER_API_KEY**: Generate secure random key
  ```bash
  python -c "import secrets; print('bh_' + secrets.token_hex(24))"
  ```

- [ ] **ADMIN_PASSWORD**: Set strong password (16+ chars)

- [ ] **JWT_SECRET_KEY**: Generate secure random secret
  ```bash
  python -c "import secrets; print(secrets.token_hex(32))"
  ```

- [ ] **ALLOWED_ORIGINS**: Set to exact production domains (no wildcards)

- [ ] **HTTPS**: Enable SSL certificates
  - Configure SSL_CERT_PATH and SSL_KEY_PATH
  - Use Let's Encrypt or commercial CA

- [ ] **Firewall**: Block direct access to API port from public
  - Only allow through reverse proxy

### Infrastructure

- [ ] **Reverse Proxy**: Set up nginx/caddy in front
- [ ] **Database**: Configure PostgreSQL (optional)
- [ ] **Vector DB**: Configure Qdrant (optional, for document search)
- [ ] **Storage**: Configure persistent storage paths
- [ ] **Logs**: Configure log rotation

### Monitoring

- [ ] Health check endpoint: `/health`
- [ ] Set up uptime monitoring
- [ ] Configure log aggregation
- [ ] Set up alerting for errors

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `MASTER_API_KEY` | Yes | Master API key for admin operations |
| `ADMIN_PASSWORD` | Yes | Admin user password for frontend |
| `JWT_SECRET_KEY` | Yes | Secret for JWT token signing |
| `ALLOWED_ORIGINS` | Yes | Comma-separated allowed CORS origins |
| `API_PORT` | No | API server port (default: 8000) |
| `FRONTEND_PORT` | No | Frontend port (default: 3001) |
| `WORKERS` | No | Uvicorn worker count (default: 4) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

## API Authentication

### For External Clients

All API requests require authentication via:

1. **Bearer Token** (recommended):
   ```
   Authorization: Bearer bh_your_api_key_here
   ```

2. **X-API-Key Header**:
   ```
   X-API-Key: bh_your_api_key_here
   ```

### Creating API Keys

```bash
# Using master key
curl -X POST "https://api.yourdomain.com/auth/keys?name=MyApp" \
  -H "Authorization: Bearer $MASTER_API_KEY"
```

### Localhost Bypass

Requests from `127.0.0.1` and `localhost` are trusted and bypass auth.
This is for local development only - disable in production if needed.

## Rate Limits

| Endpoint Type | Limit | Window |
|--------------|-------|--------|
| General | 500 requests | 15 minutes |
| Authentication | 10 attempts | 15 minutes |
| File Upload | 50 uploads | 1 hour |

## Nginx Configuration Example

```nginx
upstream brutallyhonest_api {
    server 127.0.0.1:8000;
}

upstream brutallyhonest_frontend {
    server 127.0.0.1:3001;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";

    location / {
        proxy_pass http://brutallyhonest_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running transcriptions
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}

server {
    listen 443 ssl http2;
    server_name app.yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    location / {
        proxy_pass http://brutallyhonest_frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Systemd Service (Linux)

Create `/etc/systemd/system/brutallyhonest.service`:

```ini
[Unit]
Description=Brutally Honest AI Server
After=network.target

[Service]
Type=simple
User=brutallyhonest
Group=brutallyhonest
WorkingDirectory=/opt/brutallyhonest
ExecStart=/opt/brutallyhonest/start_production.sh
Restart=always
RestartSec=10
Environment="PATH=/opt/brutallyhonest/venv/bin:/usr/local/bin:/usr/bin"

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable brutallyhonest
sudo systemctl start brutallyhonest
```

## Troubleshooting

### API won't start

1. Check port availability: `lsof -i :8000`
2. Check logs: `tail -f /var/log/brutallyhonest/api.log`
3. Verify environment: `source venv/bin/activate && python -c "from api_server import app"`

### Authentication fails

1. Verify API key format starts with `bh_`
2. Check ALLOWED_ORIGINS matches request origin
3. Verify key is not expired/deleted

### Performance issues

1. Increase WORKERS (2-4 × CPU cores)
2. Enable async file I/O
3. Use connection pooling for database
4. Consider CDN for static assets

## Support

- Documentation: `/docs` endpoint
- Health Check: `/health` endpoint
- API Info: `/auth/info` endpoint
