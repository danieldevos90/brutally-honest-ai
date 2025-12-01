# Brutally Honest AI - Project Structure

## Directory Overview

```
brutally-honest-ai/
├── frontend/               # Node.js web application
│   ├── public/            # Static assets (CSS, JS, HTML)
│   ├── views/             # EJS templates
│   └── server.js          # Express server
│
├── src/                   # Python backend source code
│   ├── agents/           # AI agent framework
│   ├── ai/               # AI processors (Whisper, LLAMA)
│   ├── analysis/         # Interview and persona analyzers
│   ├── api/              # API endpoints
│   ├── audio/            # Audio processing & device connectivity
│   ├── database/         # SQLite database management
│   ├── deployment/       # OTA deployment management
│   ├── documents/        # Document processing & vector store
│   ├── llm/              # LLM analysis
│   ├── profiles/         # Profile management
│   └── validation/       # Fact-checking validation
│
├── docs/                  # Documentation
├── scripts/              # Utility scripts
├── installer/            # Platform installers
├── omi_firmware/         # ESP32S3 firmware code
├── profiles/             # User profile data
└── models/               # AI model files
```

## Key Files

### Entry Points
| File | Description |
|------|-------------|
| `main_unified.py` | Main Python backend entry point |
| `api_server.py` | REST API server |
| `frontend/server.js` | Node.js frontend server |

### Configuration
| File | Description |
|------|-------------|
| `requirements.txt` | Python dependencies |
| `requirements_web.txt` | Web-specific dependencies |
| `requirements_jetson.txt` | Jetson-specific dependencies |
| `env.example` | Environment variable template |
| `docker-compose.yml` | Docker configuration |
| `Dockerfile` | Docker image definition |

### Scripts
| Script | Purpose |
|--------|---------|
| `start_app.sh` / `start_app.bat` | Start the application |
| `setup_llama.sh` | Setup LLAMA model |
| `deploy_to_nvidia.sh` | Deploy to NVIDIA Jetson |
| `ota_deploy.sh` | Over-the-air deployment |
| `install_brutally_honest.sh` | Installation script |

## Frontend Structure

### Design System
The frontend uses a centralized design system with CSS custom properties (tokens):

```
frontend/public/
├── design-system.css     # Design tokens & base styles (LOAD FIRST)
├── styles.css            # Component-specific styles
├── dynamic-portal.css    # Portal-specific styles
└── *.js                  # JavaScript modules
```

### CSS Token Categories
- **Colors**: `--color-*`, `--bg-*`, `--text-*`, `--border-*`
- **Spacing**: `--space-*` (0-24 scale)
- **Typography**: `--text-*` (sizes), `--font-*` (weights)
- **Borders**: `--radius-*`, `--border-*`
- **Shadows**: `--shadow-*`
- **Z-Index**: `--z-*`

### Using Design Tokens
```css
/* Use tokens instead of hardcoded values */
.my-component {
  background: var(--bg-secondary);
  color: var(--text-primary);
  padding: var(--space-4);
  border-radius: var(--radius-md);
}
```

### Utility Classes Available
```html
<!-- Layout -->
<div class="flex items-center justify-center gap-4">

<!-- Text -->
<p class="text-center text-tertiary text-sm">

<!-- Spacing -->
<div class="p-4 mt-2 mb-4">

<!-- Background -->
<div class="bg-secondary rounded-lg">
```

## Backend Structure

### Source Modules (`src/`)

| Module | Responsibility |
|--------|---------------|
| `agents/` | AI agent orchestration framework |
| `ai/` | Whisper transcription, LLAMA processing |
| `analysis/` | Interview analysis, persona detection |
| `audio/` | BLE/USB device connectivity, audio processing |
| `database/` | SQLite data persistence |
| `documents/` | PDF/document processing, embeddings |
| `validation/` | Fact-checking against knowledge base |

### API Endpoints
Main API server runs on port 5001 (configurable).
Frontend server runs on port 3000.

## Development Guidelines

### Adding New Styles
1. Check if design token exists in `design-system.css`
2. Use existing utility classes when possible
3. Add component styles to `styles.css`
4. Never use hardcoded colors - use `var(--color-*)` tokens

### Theme Support
The design system supports:
- Light mode (default)
- Dark mode (`data-theme="dark"` or `class="dark-mode"`)
- System preference detection

### Adding New Features
1. Backend logic goes in `src/` (Python)
2. API endpoints go in `api_server.py` or `src/api/`
3. Frontend pages go in `frontend/views/pages/`
4. Static assets go in `frontend/public/`

## Environment Variables
See `env.example` for required environment variables:
- `GEMINI_KEY` - Google Gemini API key
- Database paths
- Port configurations

## Running the Application

### Development
```bash
# Backend
python main_unified.py

# Frontend  
cd frontend && npm start
```

### Production
```bash
./start_app.sh
```

### Docker
```bash
docker-compose up
```

## 🚀 Deployment

### Deployment Commands
```bash
# Quick deploy (sync files + restart)
./deploy.sh

# Full deploy (reinstall dependencies)
./deploy.sh --full

# Create versioned release and deploy
./deploy.sh --release v1.2.3

# Rollback to previous version
./deploy.sh --rollback

# Check remote status
./deploy.sh --status

# View logs
./deploy.sh --logs
./deploy.sh --logs-frontend
```

### Version Control
- Version tracked in `VERSION` file
- Changes documented in `CHANGELOG.md`
- Git tags for releases (e.g., `v1.2.3`)
- Automatic backups before each deploy
- Rollback support to previous versions

### Remote Server
| Setting | Value |
|---------|-------|
| **Local** | `brutally@192.168.2.33` |
| **External** | `brutallyhonest.io` |
| **Frontend** | Port 3001 |
| **API** | Port 8000 |
| **WebSocket** | Port 3002 |

### First-Time Setup
```bash
# Copy SSH key for passwordless auth
ssh-copy-id brutally@192.168.2.33

# Verify connection
./deploy.sh --status
```

See `docs/REMOTE_ACCESS_SETUP.md` for external access configuration.

