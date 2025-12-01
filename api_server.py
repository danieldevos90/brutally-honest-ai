#!/usr/bin/env python3
"""
Brutally Honest AI - REST API Server
Provides HTTP endpoints for the frontend using the src/ structure
With Bearer Token Authentication for external API access
"""

import asyncio
import sys
import time
import os
import secrets
import hashlib
import uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Depends, Request, Security, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import Response, HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.docs import get_swagger_ui_html
import uvicorn
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
from enum import Enum
# Recording storage
RECORDINGS_DIR = Path(__file__).parent / "recordings"
HISTORY_FILE = Path(__file__).parent / "data" / "transcription_history.json"
RECORDINGS_DIR.mkdir(exist_ok=True)
(Path(__file__).parent / "data").mkdir(exist_ok=True)
if not HISTORY_FILE.exists():
    HISTORY_FILE.write_text("[]")


def save_transcription_result(filename: str, audio_data: bytes, result: dict):
    """Save audio file and transcription result for history"""
    try:
        import json
        from datetime import datetime
        import uuid
        
        # Save audio file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        audio_path = RECORDINGS_DIR / safe_filename
        audio_path.write_bytes(audio_data)
        logger.info(f"Saved recording: {audio_path}")
        
        # Add to history
        history = json.loads(HISTORY_FILE.read_text())
        history.append({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "originalFilename": filename,
            "savedFilename": safe_filename,
            "filePath": str(audio_path),
            "result": result
        })
        HISTORY_FILE.write_text(json.dumps(history, indent=2))
        logger.info(f"Updated transcription history: {len(history)} entries")
    except Exception as e:
        logger.error(f"Failed to save transcription result: {e}")
# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from audio.unified_connector import UnifiedESP32S3Connector, ConnectionType
from audio.multi_device_manager import get_device_manager, MultiDeviceManager
from audio.voice_analyzer import VoiceFeatures, get_voice_analyzer
from models.schemas import RecordingInfo
from ai.llama_processor import get_processor
from ai.enhanced_processor import get_enhanced_processor
from documents.processor import get_document_processor, DocumentInfo
from documents.vector_store import get_vector_store
from analysis.interview_analyzer import get_interview_analyzer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# API KEY / BEARER TOKEN AUTHENTICATION
# ============================================

# API Configuration
API_MASTER_KEY = os.environ.get("API_MASTER_KEY", "bh_" + secrets.token_hex(24))
API_KEYS_FILE = Path(__file__).parent / ".api_keys.json"

# Store API keys in memory (loaded from file)
api_keys: Dict[str, Dict[str, Any]] = {}

# ============================================
# BACKGROUND JOB SYSTEM
# ============================================

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Store jobs in memory (job_id -> job_data)
transcription_jobs: Dict[str, Dict[str, Any]] = {}

def create_job(filename: str, file_size: int, validate_documents: bool = False) -> str:
    """Create a new transcription job and return job ID"""
    job_id = str(uuid.uuid4())[:8]  # Short ID for convenience
    transcription_jobs[job_id] = {
        "id": job_id,
        "status": JobStatus.PENDING,
        "filename": filename,
        "file_size": file_size,
        "validate_documents": validate_documents,
        "created_at": datetime.now().isoformat(),
        "started_at": None,
        "completed_at": None,
        "progress": 0,
        "progress_message": "Queued for processing",
        "result": None,
        "error": None
    }
    return job_id

def update_job_status(job_id: str, status: JobStatus, progress: int = None, 
                      progress_message: str = None, result: dict = None, error: str = None):
    """Update job status"""
    if job_id in transcription_jobs:
        job = transcription_jobs[job_id]
        job["status"] = status
        if progress is not None:
            job["progress"] = progress
        if progress_message:
            job["progress_message"] = progress_message
        if status == JobStatus.PROCESSING and job["started_at"] is None:
            job["started_at"] = datetime.now().isoformat()
        if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job["completed_at"] = datetime.now().isoformat()
        if result:
            job["result"] = result
        if error:
            job["error"] = error

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job by ID"""
    return transcription_jobs.get(job_id)

def cleanup_old_jobs(max_age_hours: int = 24):
    """Remove jobs older than max_age_hours"""
    cutoff = datetime.now() - timedelta(hours=max_age_hours)
    to_remove = []
    for job_id, job in transcription_jobs.items():
        created = datetime.fromisoformat(job["created_at"])
        if created < cutoff:
            to_remove.append(job_id)
    for job_id in to_remove:
        del transcription_jobs[job_id]
    if to_remove:
        logger.info(f"🧹 Cleaned up {len(to_remove)} old jobs")

# ============================================
# API KEY FUNCTIONS
# ============================================

def load_api_keys():
    """Load API keys from file"""
    global api_keys
    if API_KEYS_FILE.exists():
        try:
            with open(API_KEYS_FILE, "r") as f:
                api_keys = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")
            api_keys = {}
    
    # Always ensure master key exists
    master_key_hash = hashlib.sha256(API_MASTER_KEY.encode()).hexdigest()
    api_keys[master_key_hash] = {
        "name": "Master Key",
        "created": datetime.now().isoformat(),
        "permissions": ["*"],
        "is_master": True
    }

def save_api_keys():
    """Save API keys to file"""
    try:
        with open(API_KEYS_FILE, "w") as f:
            json.dump(api_keys, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save API keys: {e}")

def generate_api_key(name: str = "API Key") -> str:
    """Generate a new API key"""
    key = "bh_" + secrets.token_hex(24)
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    api_keys[key_hash] = {
        "name": name,
        "created": datetime.now().isoformat(),
        "permissions": ["*"],
        "is_master": False
    }
    save_api_keys()
    return key

def verify_api_key(key: str) -> Optional[Dict[str, Any]]:
    """Verify an API key and return its info"""
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    return api_keys.get(key_hash)

def revoke_api_key(key: str) -> bool:
    """Revoke an API key"""
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    if key_hash in api_keys and not api_keys[key_hash].get("is_master"):
        del api_keys[key_hash]
        save_api_keys()
        return True
    return False

# Security scheme
security = HTTPBearer(auto_error=False)

async def get_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[Dict[str, Any]]:
    """
    Verify API key from Bearer token or allow internal requests
    """
    # Allow internal requests from localhost (frontend proxy)
    client_host = request.client.host if request.client else ""
    if client_host in ["127.0.0.1", "localhost", "::1"]:
        return {"name": "Internal", "permissions": ["*"], "internal": True}
    
    # Check Bearer token
    if credentials:
        key_info = verify_api_key(credentials.credentials)
        if key_info:
            return key_info
    
    # Check X-API-Key header as fallback
    api_key_header = request.headers.get("X-API-Key")
    if api_key_header:
        key_info = verify_api_key(api_key_header)
        if key_info:
            return key_info
    
    return None

async def require_api_key(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Dict[str, Any]:
    """
    Require valid API key - raises 401 if not authenticated
    """
    key_info = await get_api_key(request, credentials)
    if not key_info:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Use Bearer token or X-API-Key header.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return key_info

# Load API keys on startup
load_api_keys()

# FastAPI app
app = FastAPI(
    title="Brutally Honest AI API",
    description="""
## REST API for Brutally Honest AI Platform

### Authentication
All endpoints require authentication via Bearer token:
```
Authorization: Bearer bh_your_api_key_here
```

Or via X-API-Key header:
```
X-API-Key: bh_your_api_key_here
```

### Getting Started
1. Use the master API key shown in the console on startup
2. Or create a new key via POST /auth/keys

### API Documentation
- Interactive docs: /docs
- ReDoc: /redoc
    """,
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Swagger UI with white/light theme
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    html = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_ui_parameters={
            "syntaxHighlight.theme": "agate",
            "persistAuthorization": True,
        },
    )
    # Inject custom CSS for white/light theme
    custom_css = """
    <style>
        body { background-color: #ffffff !important; color: #333333 !important; }
        .swagger-ui { background-color: #ffffff !important; }
        .swagger-ui .topbar { background-color: #ffffff !important; border-bottom: 1px solid #e0e0e0 !important; }
        .swagger-ui .topbar .download-url-wrapper { background-color: #ffffff !important; }
        .swagger-ui .topbar .download-url-wrapper input { background-color: #ffffff !important; color: #333333 !important; border: 1px solid #e0e0e0 !important; }
        .swagger-ui .info { background-color: #ffffff !important; color: #333333 !important; }
        .swagger-ui .info .title { color: #333333 !important; }
        .swagger-ui .info .description { color: #555555 !important; }
        .swagger-ui .scheme-container { background-color: #f5f5f5 !important; }
        .swagger-ui .opblock { background-color: #ffffff !important; border: 1px solid #e0e0e0 !important; }
        .swagger-ui .opblock.opblock-get { border-color: #61affe !important; background-color: #ffffff !important; }
        .swagger-ui .opblock.opblock-post { border-color: #49cc90 !important; background-color: #ffffff !important; }
        .swagger-ui .opblock.opblock-put { border-color: #fca130 !important; background-color: #ffffff !important; }
        .swagger-ui .opblock.opblock-delete { border-color: #f93e3e !important; background-color: #ffffff !important; }
        .swagger-ui .opblock .opblock-summary { color: #333333 !important; }
        .swagger-ui .opblock .opblock-summary-method { color: #ffffff !important; }
        .swagger-ui .opblock-body { background-color: #ffffff !important; color: #333333 !important; }
        .swagger-ui .opblock-description-wrapper { color: #555555 !important; }
        .swagger-ui .parameter__name { color: #333333 !important; }
        .swagger-ui .parameter__type { color: #666666 !important; }
        .swagger-ui .parameter__in { color: #666666 !important; }
        .swagger-ui .response-col_status { color: #333333 !important; }
        .swagger-ui .response-col_description { color: #555555 !important; }
        .swagger-ui .model-box { background-color: #ffffff !important; color: #333333 !important; }
        .swagger-ui .model-title { color: #333333 !important; }
        .swagger-ui .prop-name { color: #333333 !important; }
        .swagger-ui .prop-type { color: #666666 !important; }
        .swagger-ui .prop-format { color: #999999 !important; }
        .swagger-ui .btn { background-color: #4CAF50 !important; color: #ffffff !important; }
        .swagger-ui .btn.execute { background-color: #4CAF50 !important; }
        .swagger-ui .btn.cancel { background-color: #f44336 !important; }
        .swagger-ui input[type="text"], .swagger-ui input[type="password"], .swagger-ui textarea, .swagger-ui select { background-color: #ffffff !important; color: #333333 !important; border: 1px solid #e0e0e0 !important; }
        .swagger-ui .response-content-type { color: #333333 !important; }
        .swagger-ui .highlight-code { background-color: #f5f5f5 !important; }
        .swagger-ui .microlight { background-color: #f5f5f5 !important; color: #333333 !important; }
        .swagger-ui code { background-color: #f5f5f5 !important; color: #333333 !important; }
        .swagger-ui pre { background-color: #f5f5f5 !important; color: #333333 !important; }
        .swagger-ui .markdown p, .swagger-ui .markdown pre, .swagger-ui .markdown code { color: #333333 !important; }
        .swagger-ui .markdown pre { background-color: #f5f5f5 !important; }
        .swagger-ui .scheme-container { background-color: #f5f5f5 !important; }
        .swagger-ui .auth-wrapper { background-color: #ffffff !important; }
        .swagger-ui .auth-btn-wrapper { background-color: #ffffff !important; }
        .swagger-ui .authorization__btn { background-color: #4CAF50 !important; color: #ffffff !important; }
        .swagger-ui .authorization__btn.locked { background-color: #f44336 !important; }
        .swagger-ui .authorization__btn.unlocked { background-color: #4CAF50 !important; }
    </style>
    """
    html_body = html.body.decode("utf-8")
    # Insert custom CSS before closing head tag
    html_body = html_body.replace("</head>", custom_css + "</head>")
    return HTMLResponse(content=html_body)

# ============================================
# AUTH ENDPOINTS (Public)
# ============================================

@app.get("/auth/info", tags=["Authentication"])
async def auth_info():
    """Get authentication information and API key format"""
    return {
        "message": "Brutally Honest AI API",
        "auth_methods": [
            "Bearer token in Authorization header",
            "X-API-Key header"
        ],
        "key_format": "bh_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "docs_url": "/docs",
        "create_key": "POST /auth/keys (requires master key)"
    }

@app.post("/auth/keys", tags=["Authentication"])
async def create_api_key(
    name: str = "API Key",
    api_key: Dict[str, Any] = Depends(require_api_key)
):
    """Create a new API key (requires authentication with existing key)"""
    if not api_key.get("is_master") and not api_key.get("internal"):
        # Only master key or internal can create new keys
        raise HTTPException(status_code=403, detail="Only master key can create new API keys")
    
    new_key = generate_api_key(name)
    return {
        "success": True,
        "api_key": new_key,
        "name": name,
        "message": "Store this key securely - it won't be shown again!"
    }

@app.get("/auth/keys", tags=["Authentication"])
async def list_api_keys(api_key: Dict[str, Any] = Depends(require_api_key)):
    """List all API keys (hashed, without actual keys)"""
    if not api_key.get("is_master") and not api_key.get("internal"):
        raise HTTPException(status_code=403, detail="Only master key can list API keys")
    
    return {
        "keys": [
            {
                "name": info["name"],
                "created": info["created"],
                "is_master": info.get("is_master", False),
                "hash_prefix": key_hash[:12] + "..."
            }
            for key_hash, info in api_keys.items()
        ]
    }

@app.delete("/auth/keys/{key_prefix}", tags=["Authentication"])
async def delete_api_key(
    key_prefix: str,
    api_key: Dict[str, Any] = Depends(require_api_key)
):
    """Revoke an API key by its hash prefix"""
    if not api_key.get("is_master") and not api_key.get("internal"):
        raise HTTPException(status_code=403, detail="Only master key can delete API keys")
    
    # Find key by prefix
    for key_hash in list(api_keys.keys()):
        if key_hash.startswith(key_prefix):
            if api_keys[key_hash].get("is_master"):
                raise HTTPException(status_code=403, detail="Cannot delete master key")
            del api_keys[key_hash]
            save_api_keys()
            return {"success": True, "message": "API key revoked"}
    
    raise HTTPException(status_code=404, detail="API key not found")

@app.get("/auth/verify", tags=["Authentication"])
async def verify_token(api_key: Dict[str, Any] = Depends(require_api_key)):
    """Verify current API key is valid"""
    return {
        "valid": True,
        "name": api_key.get("name"),
        "permissions": api_key.get("permissions", []),
        "is_master": api_key.get("is_master", False)
    }

# Global connector instance (legacy - kept for backward compatibility)
connector: Optional[UnifiedESP32S3Connector] = None

# Global device manager
device_manager: Optional[MultiDeviceManager] = None

async def get_connector() -> UnifiedESP32S3Connector:
    """Get or create the unified connector (legacy method)"""
    global connector
    if connector is None:
        # Try to get active device from device manager first
        manager = get_device_manager()
        active_connector = manager.get_active_connector()
        if active_connector:
            connector = active_connector
            return connector
        
        # Fallback to old behavior
        connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
        await connector.initialize()
    return connector

def get_device_manager_instance() -> MultiDeviceManager:
    """Get or create the device manager"""
    global device_manager
    if device_manager is None:
        device_manager = get_device_manager()
    return device_manager

@app.on_event("startup")
async def startup_event():
    """Initialize the device manager on startup"""
    logger.info("🚀 Starting Brutally Honest AI API Server...")
    try:
        # Initialize device manager
        manager = get_device_manager_instance()
        logger.info("✅ Device manager initialized successfully")
        
        # Auto-scan for devices
        devices = await manager.scan_for_devices()
        logger.info(f"📱 Found {len(devices)} ESP32S3 devices")
        
        # Auto-connect to first available device (legacy behavior)
        if devices:
            first_device = devices[0]
            if first_device.confidence > 70:
                logger.info(f"🔌 Auto-connecting to {first_device.description}...")
                await manager.connect_device(first_device.device_id)
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize device manager: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down API server...")
    try:
        # Disconnect all devices
        manager = get_device_manager_instance()
        await manager.disconnect_all()
        logger.info("✅ All devices disconnected")
        
        # Legacy connector cleanup
        global connector
        if connector:
            await connector.disconnect()
            logger.info("✅ Legacy connector disconnected")
    except Exception as e:
        logger.error(f"❌ Shutdown error: {e}")

@app.get("/", tags=["General"])
async def root():
    """Root endpoint - public info"""
    return {
        "message": "Brutally Honest AI API Server",
        "version": "2.0.0",
        "auth_required": True,
        "docs": "/docs",
        "auth_info": "/auth/info"
    }

@app.get("/health", tags=["General"])
async def health():
    """Health check endpoint - public"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/status", tags=["System"])
async def get_status(api_key: Dict[str, Any] = Depends(require_api_key)):
    """Get overall system status"""
    try:
        conn = await get_connector()
        device_status = await conn.get_device_status()
        
        if device_status:
            return {
                "device_connected": device_status.connected,
                "connection_type": conn.current_connection.value if conn.current_connection else "none",
                "recording": device_status.recording,
                "files": device_status.files,
                "sd_card_present": device_status.sd_card_present,
                "ble_connected": device_status.ble_connected,
                "free_ram": str(device_status.free_ram),
                "device_model": device_status.device_info.get('device_model', 'ESP32S3') if device_status.device_info else 'ESP32S3',
                "port": device_status.device_info.get('port', 'N/A') if device_status.device_info else 'N/A',
                "battery_voltage": device_status.battery_voltage,
                "battery_percentage": device_status.battery_percentage,
                "battery_status": device_status.battery_status,
                "whisper_ready": False,  # Not implemented yet
                "llm_ready": False,      # Not implemented yet
                "timestamp": None  # Add timestamp if needed
            }
        else:
            return {
                "device_connected": False,
                "connection_type": "none",
                "recording": False,
                "files": 0,
                "sd_card_present": False,
                "ble_connected": False,
                "free_ram": "N/A",
                "device_model": "N/A",
                "port": "N/A",
                "whisper_ready": False,
                "llm_ready": False,
                "timestamp": None
            }
    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get device status: {str(e)}")

@app.get("/devices/status", tags=["Devices"])
async def get_devices_status(api_key: Dict[str, Any] = Depends(require_api_key)):
    """Get status of all detected ESP32S3 devices"""
    try:
        manager = get_device_manager_instance()
        devices = await manager.scan_for_devices()
        
        # Refresh status for connected devices
        await manager.refresh_device_status()
        
        devices_list = manager.get_devices_list()
        
        return {
            "success": True,
            "devices": devices_list,
            "count": len(devices_list),
            "active_device": manager.active_device_id,
            "scan_timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to get devices status: {e}")
        return {
            "success": False,
            "devices": [],
            "count": 0,
            "active_device": None,
            "error": str(e)
        }

@app.post("/devices/connect/{device_id:path}", tags=["Devices"])
async def connect_to_device(device_id: str, api_key: Dict[str, Any] = Depends(require_api_key)):
    """Connect to a specific device"""
    try:
        # URL decode the device ID
        from urllib.parse import unquote
        device_id = unquote(device_id)
        
        manager = get_device_manager_instance()
        success = await manager.connect_device(device_id)
        
        if success:
            return {
                "success": True,
                "message": f"Connected to device {device_id}",
                "active_device": device_id
            }
        else:
            return {
                "success": False,
                "message": f"Failed to connect to device {device_id}"
            }
    except Exception as e:
        logger.error(f"Failed to connect to device {device_id}: {e}")
        return {
            "success": False,
            "message": f"Connection error: {str(e)}"
        }

@app.post("/devices/disconnect/{device_id:path}", tags=["Devices"])
async def disconnect_from_device(device_id: str, api_key: Dict[str, Any] = Depends(require_api_key)):
    """Disconnect from a specific device"""
    try:
        # URL decode the device ID
        from urllib.parse import unquote
        device_id = unquote(device_id)
        
        manager = get_device_manager_instance()
        success = await manager.disconnect_device(device_id)
        
        return {
            "success": success,
            "message": f"Disconnected from device {device_id}" if success else f"Failed to disconnect from device {device_id}"
        }
    except Exception as e:
        logger.error(f"Failed to disconnect from device {device_id}: {e}")
        return {
            "success": False,
            "message": f"Disconnect error: {str(e)}"
        }

@app.post("/devices/select/{device_id:path}", tags=["Devices"])
async def select_device(device_id: str, api_key: Dict[str, Any] = Depends(require_api_key)):
    """Select a device as the active device"""
    try:
        # URL decode the device ID
        from urllib.parse import unquote
        device_id = unquote(device_id)
        
        manager = get_device_manager_instance()
        success = manager.select_device(device_id)
        
        if success:
            return {
                "success": True,
                "message": f"Selected device {device_id} as active",
                "active_device": device_id
            }
        else:
            return {
                "success": False,
                "message": f"Failed to select device {device_id} (not connected?)"
            }
    except Exception as e:
        logger.error(f"Failed to select device {device_id}: {e}")
        return {
            "success": False,
            "message": f"Selection error: {str(e)}"
        }

@app.get("/scan_ports")
async def scan_ports():
    """Scan for available serial ports with detailed ESP32S3 detection (legacy endpoint)"""
    try:
        from src.audio.omi_connector import ESP32S3Connector
        
        # Get detailed port information
        ports = ESP32S3Connector.get_all_serial_ports()
        
        # Find the best ESP32S3 candidate
        esp32s3_device = None
        for port in ports:
            if port['is_esp32s3'] and port['confidence'] > 70:
                esp32s3_device = port['device']
                break
        
        return {
            "ports": ports,
            "count": len(ports),
            "esp32s3_detected": esp32s3_device is not None,
            "esp32s3_device": esp32s3_device,
            "scan_timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to scan ports: {e}")
        return {
            "ports": [],
            "count": 0,
            "esp32s3_detected": False,
            "esp32s3_device": None,
            "error": str(e)
        }

@app.post("/connect_device")
async def connect_device():
    """Connect to the ESP32S3 device"""
    try:
        conn = await get_connector()
        # If already connected, treat as success
        if conn.is_connected:
            return {
                "success": True,
                "message": f"Already connected via {conn.current_connection.value}",
                "connection_type": conn.current_connection.value
            }
        if await conn.initialize():
            return {
                "success": True,
                "message": f"Connected via {conn.current_connection.value}",
                "connection_type": conn.current_connection.value
            }
        else:
            return {
                "success": False,
                "message": "Failed to connect to device"
            }
    except Exception as e:
        logger.error(f"Failed to connect device: {e}")
        return {
            "success": False,
            "message": f"Connection error: {str(e)}"
        }

@app.get("/test_device")
async def test_device():
    """Test device connection and capabilities"""
    try:
        conn = await get_connector()
        device_status = await conn.get_device_status()
        
        if device_status and device_status.connected:
            return {
                "device_found": True,
                "connection_successful": True,
                "streaming_ready": True,
                "device_path": device_status.port,
                "connection_type": conn.current_connection.value
            }
        else:
            return {
                "device_found": False,
                "connection_successful": False,
                "streaming_ready": False,
                "device_path": None,
                "connection_type": "none"
            }
    except Exception as e:
        logger.error(f"Failed to test device: {e}")
        return {
            "device_found": False,
            "connection_successful": False,
            "streaming_ready": False,
            "device_path": None,
            "connection_type": "none"
        }

@app.get("/device/info")
async def get_device_info():
    """Get detailed device information"""
    try:
        conn = await get_connector()
        device_status = await conn.get_device_status()
        
        if device_status and device_status.connected:
            return {
                "success": True,
                "device_info": {
                    "device_name": "BrutallyHonestAI",
                    "device_model": device_status.device_info.get('device_model', 'ESP32S3'),
                    "connection_type": conn.current_connection.value,
                    "port": device_status.device_info.get('port', 'N/A'),
                    "recording": device_status.recording,
                    "files": device_status.files,
                    "sd_card_present": device_status.sd_card_present,
                    "ble_connected": device_status.ble_connected,
                    "free_ram": str(device_status.free_ram),
                    "battery_voltage": device_status.battery_voltage,
                    "battery_percentage": device_status.battery_percentage,
                    "battery_status": device_status.battery_status,
                    "storage_used": "N/A",   # Could be calculated from recordings
                    "uptime": device_status.device_info.get('uptime', 'N/A'),
                    "firmware_version": "1.0.0",
                    "is_recording": device_status.recording,
                    "recording_count": device_status.files
                }
            }
        else:
            return {
                "success": False,
                "error": "Device not connected"
            }
    except Exception as e:
        logger.error(f"Failed to get device info: {e}")
        return {
            "success": False,
            "error": f"Failed to get device info: {str(e)}"
        }

@app.get("/device/recordings")
async def get_recordings():
    """Get list of recordings from the device"""
    try:
        conn = await get_connector()
        recordings = await conn.get_recordings()
        
        total_size = sum(rec.size for rec in recordings)
        
        return {
            "success": True,
            "recordings": [
                {
                    "name": rec.name,
                    "size": rec.size,
                    "size_mb": round(rec.size / (1024 * 1024), 2),
                    # Use 'date' string if available (frontend expects 'date')
                    "date": rec.date if hasattr(rec, 'date') else None
                }
                for rec in recordings
            ],
            "total_files": len(recordings),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
    except Exception as e:
        logger.error(f"Failed to get recordings: {e}")
        return {
            "success": False,
            "error": f"Failed to get recordings: {str(e)}",
            "recordings": [],
            "total_files": 0,
            "total_size": 0
        }

@app.get("/device/recordings/download/{filename}")
async def download_recording(filename: str):
    """Download a recording file from the ESP32S3 device"""
    try:
        logger.info(f"📥 Download request for: {filename}")
        
        conn = await get_connector()
        
        # Get file data from device via serial command
        file_data = await conn.download_file(filename)
        
        if file_data:
            # Return file as streaming response
            from fastapi.responses import StreamingResponse
            import io
            
            return StreamingResponse(
                io.BytesIO(file_data),
                media_type="audio/wav",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Length": str(len(file_data))
                }
            )
        else:
            return {"success": False, "error": "File not found or download failed"}
            
    except Exception as e:
        logger.error(f"Download error: {e}")
        return {"success": False, "error": str(e)}

@app.get("/device/recordings/analyze/{filename}")
async def analyze_recording(filename: str):
    """Analyze a WAV via HTTP path: duration, RMS, peak"""
    try:
        conn = await get_connector()
        file_data = await conn.download_file(filename)
        if not file_data:
            return {"success": False, "error": "Download failed"}

        # Parse WAV in-memory
        import io, wave, math
        bio = io.BytesIO(file_data)
        try:
            w = wave.open(bio, 'rb')
            ch = w.getnchannels(); rate = w.getframerate(); width = w.getsampwidth(); frames = w.getnframes()
            # up to 10 seconds
            n = min(frames, rate * 10)
            data = w.readframes(n)
            w.close()
        except Exception as we:
            return {"success": False, "error": f"WAV parse error: {we}"}

        import array
        if width != 2:
            return {"success": False, "error": f"Unsupported sample width: {width}"}
        samples = array.array('h', data)
        if len(samples) == 0:
            return {"success": True, "channels": ch, "rate": rate, "bits": width * 8, "frames": frames, "duration_s": round(frames / rate, 2), "rms": 0, "peak": 0}
        rms = int(math.sqrt(sum(s * s for s in samples) / len(samples)))
        peak = max(abs(s) for s in samples)
        return {
            "success": True,
            "channels": ch,
            "rate": rate,
            "bits": width * 8,
            "frames": frames,
            "duration_s": round(frames / rate, 2),
            "rms": rms,
            "peak": peak
        }
    except Exception as e:
        logger.error(f"Analyze error: {e}")
        return {"success": False, "error": str(e)}

@app.delete("/device/recordings/{filename}")
async def delete_recording(filename: str):
    """Delete a recording file from the ESP32S3 device"""
    try:
        logger.info(f"🗑️ Delete request for: {filename}")
        
        conn = await get_connector()
        success = await conn.delete_file(filename)
        
        if success:
            return {"success": True, "message": f"File {filename} deleted successfully"}
        else:
            return {"success": False, "error": "File deletion failed"}
            
    except Exception as e:
        logger.error(f"Delete error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/device/recordings/upload")
async def upload_recording(file: UploadFile = File(...)):
    """Upload a recording file to the ESP32S3 device"""
    try:
        logger.info(f"📤 Upload request for: {file.filename}")
        
        # Read file data
        file_data = await file.read()
        
        conn = await get_connector()
        success = await conn.upload_file(file.filename, file_data)
        
        if success:
            return {"success": True, "message": f"File {file.filename} uploaded successfully"}
        else:
            return {"success": False, "error": "File upload failed"}
            
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/ai/process", tags=["AI Processing"])
async def process_with_ai(request_data: Dict[str, Any], api_key: Dict[str, Any] = Depends(require_api_key)):
    """Process audio file with LLAMA AI"""
    try:
        filename = request_data.get("filename", "")
        model = request_data.get("model", "llama")
        task = request_data.get("task", "transcribe_and_analyze")
        
        logger.info(f"🤖 AI processing request: {filename} with {model}")
        
        # Get the audio file data
        conn = await get_connector()
        audio_data = await conn.download_file(filename)
        
        if not audio_data:
            return {
                "success": False,
                "error": f"Could not retrieve audio file: {filename}"
            }
        
        # Process with LLAMA
        processor = await get_processor()
        result = await processor.process_audio(audio_data, filename)
        
        if result.success:
            return {
                "success": True,
                "filename": filename,
                "transcription": result.transcription,
                "analysis": result.analysis,
                "summary": result.summary,
                "sentiment": result.sentiment,
                "keywords": result.keywords,
                "fact_check": result.fact_check,
                "brutal_honesty": result.brutal_honesty,
                "credibility_score": f"{result.credibility_score * 100:.1f}%" if result.credibility_score else "N/A",
                "questionable_claims": result.questionable_claims,
                "corrections": result.corrections,
                "confidence": f"{result.confidence * 100:.1f}%" if result.confidence else "N/A",
                "processing_time": f"{result.processing_time:.2f}s" if result.processing_time else "N/A",
                "model_used": model,
                "task": task
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "filename": filename,
                "model_used": model
            }
            
    except Exception as e:
        logger.error(f"AI processing error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.post("/ai/transcribe-file", tags=["AI Processing"])
async def transcribe_uploaded_file(
    file: UploadFile = File(...),
    validate_documents: bool = Form(False),
    api_key: Dict[str, Any] = Depends(require_api_key)
):
    """
    Transcribe an uploaded audio file directly without requiring a connected device.
    Supports WAV, MP3, M4A, OGG, FLAC audio formats.
    """
    try:
        logger.info(f"📤 Direct file transcription request: {file.filename}")
        
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = Path(file.filename).suffix.lower()
        supported_formats = {'.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm', '.mp4'}
        
        if file_ext not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported audio format: {file_ext}. Supported: {', '.join(supported_formats)}"
            )
        
        # Read file data
        audio_data = await file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        if len(audio_data) > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(status_code=400, detail="File too large (max 100MB)")
        
        logger.info(f"📁 File received: {file.filename} ({len(audio_data)} bytes)")
        
        # Process with LLAMA processor
        if validate_documents:
            # Use enhanced processor with document validation
            enhanced_processor = await get_enhanced_processor()
            result = await enhanced_processor.process_audio_with_validation(audio_data, file.filename)
        else:
            # Use standard processor
            processor = await get_processor()
            result = await processor.process_audio(audio_data, file.filename)
        
        if result.success:
            response_data = {
                "success": True,
                "filename": file.filename,
                "transcription": result.transcription,
                "analysis": result.analysis,
                "summary": result.summary,
                "sentiment": result.sentiment,
                "keywords": result.keywords,
                "fact_check": result.fact_check,
                "brutal_honesty": result.brutal_honesty,
                "credibility_score": f"{result.credibility_score * 100:.1f}%" if result.credibility_score else "N/A",
                "questionable_claims": result.questionable_claims,
                "corrections": result.corrections,
                "confidence": f"{result.confidence * 100:.1f}%" if result.confidence else "N/A",
                "processing_time": f"{result.processing_time:.2f}s" if result.processing_time else "N/A",
                "source": "file_upload"
            }
            
            # Add document validation fields if enabled
            if validate_documents and hasattr(result, 'document_validation'):
                response_data.update({
                    "document_validation": result.document_validation,
                    "validation_score": f"{result.validation_score * 100:.1f}%" if hasattr(result, 'validation_score') and result.validation_score else "N/A",
                    "fact_check_sources": result.fact_check_sources if hasattr(result, 'fact_check_sources') else [],
                    "contradictions": result.contradictions if hasattr(result, 'contradictions') else [],
                    "supporting_evidence": result.supporting_evidence if hasattr(result, 'supporting_evidence') else []
                })
            
            return response_data
        else:
            return {
                "success": False,
                "error": result.error,
                "filename": file.filename
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File transcription error: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

# ============================================
# ASYNC TRANSCRIPTION (Background Jobs)
# ============================================

async def process_transcription_job(job_id: str, audio_data: bytes, filename: str, validate_documents: bool):
    """Background task to process transcription with voice analysis"""
    temp_audio_path = None
    try:
        update_job_status(job_id, JobStatus.PROCESSING, 10, "Loading AI models...")
        
        # Get processor
        if validate_documents:
            update_job_status(job_id, JobStatus.PROCESSING, 20, "Loading enhanced processor with document validation...")
            processor = await get_enhanced_processor()
        else:
            update_job_status(job_id, JobStatus.PROCESSING, 20, "Loading Whisper AI model...")
            processor = await get_processor()
        
        update_job_status(job_id, JobStatus.PROCESSING, 40, "Processing audio file...")
        
        # Process audio
        if validate_documents:
            result = await processor.process_audio_with_validation(audio_data, filename)
        else:
            result = await processor.process_audio(audio_data, filename)
        
        update_job_status(job_id, JobStatus.PROCESSING, 70, "Analyzing voice characteristics...")
        
        # Voice analysis - save audio temporarily
        voice_analysis = None
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp.write(audio_data)
                temp_audio_path = tmp.name
            
            voice_analyzer = get_voice_analyzer()
            word_count = len(result.transcription.split()) if result.transcription else 0
            voice_features = await voice_analyzer.analyze_audio(
                temp_audio_path,
                transcript=result.transcription,
                word_count=word_count
            )
            voice_analysis = voice_features.to_dict()
            logger.info(f"Voice analysis: pitch={voice_features.pitch_mean_hz:.1f}Hz, "
                       f"rate={voice_features.speaking_rate_wpm:.0f}wpm, "
                       f"confidence={voice_features.confidence_score:.2f}")
        except Exception as e:
            logger.warning(f"Voice analysis failed (non-critical): {e}")
        
        update_job_status(job_id, JobStatus.PROCESSING, 90, "Generating analysis...")
        
        if result.success:
            response_data = {
                "success": True,
                "filename": filename,
                "transcription": result.transcription,
                "analysis": result.analysis,
                "summary": result.summary,
                "sentiment": result.sentiment,
                "keywords": result.keywords,
                "fact_check": result.fact_check,
                "brutal_honesty": result.brutal_honesty,
                "credibility_score": f"{result.credibility_score * 100:.1f}%" if result.credibility_score else "N/A",
                "questionable_claims": result.questionable_claims,
                "corrections": result.corrections,
                "confidence": f"{result.confidence * 100:.1f}%" if result.confidence else "N/A",
                "processing_time": f"{result.processing_time:.2f}s" if result.processing_time else "N/A",
                "source": "file_upload_async"
            }
            
            # Add voice analysis if available
            if voice_analysis:
                response_data["voice_analysis"] = {
                    "pitch_hz": round(voice_analysis.get('pitch_mean_hz', 0), 1),
                    "pitch_variation": round(voice_analysis.get('pitch_std_hz', 0), 1),
                    "speaking_rate_wpm": round(voice_analysis.get('speaking_rate_wpm', 0), 0),
                    "pause_ratio": round(voice_analysis.get('pause_ratio', 0), 2),
                    "pause_count": voice_analysis.get('pause_count', 0),
                    "speech_rhythm": voice_analysis.get('speech_rhythm', 'unknown'),
                    "confidence_indicator": round(voice_analysis.get('confidence_score', 0.5), 2),
                    "stress_indicator": round(voice_analysis.get('stress_indicator', 0.5), 2),
                    "engagement_indicator": round(voice_analysis.get('engagement_indicator', 0.5), 2),
                    "energy_mean_db": round(voice_analysis.get('energy_mean', 0), 1),
                    "duration_seconds": round(voice_analysis.get('duration_seconds', 0), 1)
                }
            
            # Add mood analysis per sentence
            try:
                from src.audio.voice_analyzer import get_mood_analyzer
                mood_analyzer = get_mood_analyzer()
                sentence_moods = mood_analyzer.analyze_text_moods(result.transcription or "")
                response_data["sentence_moods"] = [m.to_dict() for m in sentence_moods]
            except Exception as e:
                logger.warning(f"Mood analysis failed: {e}")
                response_data["sentence_moods"] = []
            
            # Add agents used
            agents_used = ["Whisper STT", "LLAMA Analysis"]
            if voice_analysis:
                agents_used.append("Voice Analyzer")
            if validate_documents:
                agents_used.append("Document Validator")
            response_data["agents_used"] = agents_used
            
            if validate_documents and hasattr(result, 'document_validation'):
                response_data.update({
                    "document_validation": result.document_validation,
                    "validation_score": f"{result.validation_score * 100:.1f}%" if hasattr(result, 'validation_score') and result.validation_score else "N/A",
                    "fact_check_sources": result.fact_check_sources if hasattr(result, 'fact_check_sources') else [],
                    "contradictions": result.contradictions if hasattr(result, 'contradictions') else [],
                    "supporting_evidence": result.supporting_evidence if hasattr(result, 'supporting_evidence') else []
                })
            
            update_job_status(job_id, JobStatus.COMPLETED, 100, "Transcription complete!", result=response_data)
            # Save recording and result for history
            save_transcription_result(filename, audio_data, response_data)
            logger.info(f"Job {job_id} completed successfully")
        else:
            update_job_status(job_id, JobStatus.FAILED, 100, "Transcription failed", error=result.error)
            logger.error(f"Job {job_id} failed: {result.error}")
            
    except Exception as e:
        logger.error(f"Job {job_id} error: {e}")
        update_job_status(job_id, JobStatus.FAILED, 100, f"Error: {str(e)}", error=str(e))
    finally:
        # Clean up temp file
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.unlink(temp_audio_path)
            except:
                pass

@app.post("/ai/transcribe-file-async", tags=["AI Processing - Async"])
async def transcribe_file_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    validate_documents: bool = Form(False),
    api_key: Dict[str, Any] = Depends(require_api_key)
):
    """
    Submit an audio file for async transcription. Returns a job ID immediately.
    Poll /ai/jobs/{job_id} to get status and results.
    
    This endpoint is recommended for large files or when using Cloudflare proxy
    to avoid timeout issues.
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = Path(file.filename).suffix.lower()
        supported_formats = {'.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm', '.mp4'}
        
        if file_ext not in supported_formats:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {file_ext}. Supported: {', '.join(supported_formats)}"
            )
        
        # Read file data
        audio_data = await file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        if len(audio_data) > 500 * 1024 * 1024:  # 500MB limit for async
            raise HTTPException(status_code=400, detail="File too large (max 500MB)")
        
        # Create job
        job_id = create_job(file.filename, len(audio_data), validate_documents)
        logger.info(f"📤 Created async transcription job {job_id} for: {file.filename} ({len(audio_data)} bytes)")
        
        # Schedule background task
        background_tasks.add_task(
            process_transcription_job,
            job_id,
            audio_data,
            file.filename,
            validate_documents
        )
        
        # Return job ID immediately
        return {
            "success": True,
            "job_id": job_id,
            "message": "Transcription job submitted",
            "status_url": f"/ai/jobs/{job_id}",
            "filename": file.filename,
            "file_size": len(audio_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Async transcription submission error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit job: {str(e)}")

@app.get("/ai/jobs/{job_id}", tags=["AI Processing - Async"])
async def get_job_status(job_id: str, api_key: Dict[str, Any] = Depends(require_api_key)):
    """
    Get the status and results of a transcription job.
    
    Poll this endpoint to check progress. When status is 'completed',
    the result field contains the full transcription data.
    """
    job = get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "job_id": job["id"],
        "status": job["status"],
        "progress": job["progress"],
        "progress_message": job["progress_message"],
        "filename": job["filename"],
        "file_size": job["file_size"],
        "created_at": job["created_at"],
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
        "result": job["result"] if job["status"] == JobStatus.COMPLETED else None,
        "error": job["error"] if job["status"] == JobStatus.FAILED else None
    }

@app.get("/ai/jobs", tags=["AI Processing - Async"])
async def list_jobs(api_key: Dict[str, Any] = Depends(require_api_key)):
    """List all transcription jobs (recent first)"""
    # Cleanup old jobs first
    cleanup_old_jobs()
    
    jobs = sorted(
        transcription_jobs.values(),
        key=lambda x: x["created_at"],
        reverse=True
    )[:50]  # Return max 50 jobs
    
    return {
        "jobs": [{
            "job_id": j["id"],
            "status": j["status"],
            "progress": j["progress"],
            "filename": j["filename"],
            "created_at": j["created_at"],
            "completed_at": j["completed_at"]
        } for j in jobs],
        "total": len(transcription_jobs)
    }

@app.delete("/ai/jobs/{job_id}", tags=["AI Processing - Async"])
async def delete_job(job_id: str, api_key: Dict[str, Any] = Depends(require_api_key)):
    """Delete a transcription job"""
    if job_id not in transcription_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    del transcription_jobs[job_id]
    return {"success": True, "message": f"Job {job_id} deleted"}

@app.post("/device/command")
async def send_command(command_data: Dict[str, Any]):
    """Send a command to the device"""
    try:
        command = command_data.get("command", "")
        if not command:
            raise HTTPException(status_code=400, detail="Command is required")
        
        conn = await get_connector()
        response = await conn.send_command(command)
        
        return {
            "success": True,
            "command": command,
            "response": response
        }
    except Exception as e:
        logger.error(f"Failed to send command: {e}")
        return {
            "success": False,
            "error": f"Failed to send command: {str(e)}"
        }

@app.post("/connection/switch")
async def switch_connection(connection_data: Dict[str, Any]):
    """Switch connection type (USB/BLE)"""
    try:
        connection_type = connection_data.get("type", "usb").lower()
        
        if connection_type == "ble":
            new_type = ConnectionType.BLE
        elif connection_type == "usb":
            new_type = ConnectionType.USB
        else:
            raise HTTPException(status_code=400, detail="Invalid connection type. Use 'usb' or 'ble'")
        
        global connector
        if connector:
            await connector.disconnect()
        
        connector = UnifiedESP32S3Connector(preferred_connection=new_type)
        success = await connector.initialize()
        
        return {
            "success": success,
            "connection_type": connector.current_connection.value if connector.current_connection else "none",
            "message": f"Switched to {new_type.value}" if success else f"Failed to switch to {new_type.value}"
        }
    except Exception as e:
        logger.error(f"Failed to switch connection: {e}")
        return {
            "success": False,
            "error": f"Failed to switch connection: {str(e)}"
        }

# Document Management Endpoints

@app.post("/documents/upload", tags=["Documents"])
async def upload_document(
    file: UploadFile = File(...),
    tags: Optional[str] = Form(None),
    context: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    related_documents: Optional[str] = Form(None),
    api_key: Dict[str, Any] = Depends(require_api_key)
):
    """Upload and process a document (txt, pdf, doc, docx) with optional metadata"""
    try:
        logger.info(f"📄 Document upload request: {file.filename}")
        
        # Validate file type
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = Path(file.filename).suffix.lower()
        supported_formats = {'.txt', '.pdf', '.doc', '.docx'}
        
        if file_ext not in supported_formats:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {file_ext}. Supported: {', '.join(supported_formats)}"
            )
        
        # Read file data
        file_data = await file.read()
        
        if len(file_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        if len(file_data) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")
        
        # Process document
        processor = await get_document_processor()
        doc_info = await processor.process_document(file_data, file.filename)
        
        # Add tags and metadata
        if tags:
            doc_info.tags = [t.strip() for t in tags.split(',') if t.strip()]
        if context:
            doc_info.context = context
        if category:
            doc_info.category = category
        if related_documents:
            doc_info.related_documents = [d.strip() for d in related_documents.split(',') if d.strip()]
        
        # Store in vector database
        vector_store = await get_vector_store()
        success = await vector_store.store_document(doc_info)
        
        if success:
            return {
                "success": True,
                "message": f"Document {file.filename} uploaded and processed successfully",
                "document": {
                    "id": doc_info.id,
                    "filename": doc_info.filename,
                    "file_type": doc_info.file_type,
                    "file_size": doc_info.file_size,
                    "text_length": doc_info.text_length,
                    "upload_time": doc_info.upload_time.isoformat(),
                    "tags": doc_info.tags,
                    "context": doc_info.context,
                    "category": doc_info.category,
                    "related_documents": doc_info.related_documents,
                    "content_preview": doc_info.content[:200] + "..." if len(doc_info.content) > 200 else doc_info.content
                }
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to store document in vector database")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")

@app.get("/documents/list", tags=["Documents"])
async def list_documents(tags: Optional[str] = None, category: Optional[str] = None, api_key: Dict[str, Any] = Depends(require_api_key)):
    """List all documents with optional filtering by tags or category"""
    try:
        vector_store = await get_vector_store()
        stats = await vector_store.get_collection_stats()
        
        # For now, return basic stats
        # In a production system, you'd implement proper document listing with filtering
        return {
            "success": True,
            "total_documents": stats.get("total_chunks", 0),
            "message": "Document listing available. Use /documents/search to query specific documents."
        }
        
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.get("/documents/search", tags=["Documents"])
async def search_documents(query: str, limit: int = 5, api_key: Dict[str, Any] = Depends(require_api_key)):
    """Search documents using vector similarity"""
    try:
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        logger.info(f"🔍 Document search: {query}")
        
        vector_store = await get_vector_store()
        results = await vector_store.search_documents(query.strip(), limit=limit)
        
        return {
            "success": True,
            "query": query,
            "results": [
                {
                    "document_id": result.document_id,
                    "chunk_id": result.chunk_id,
                    "content": result.content,
                    "score": result.score,
                    "metadata": result.metadata
                }
                for result in results
            ],
            "total_results": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/documents/query")
async def query_documents_with_llama(request_data: Dict[str, Any]):
    """Query documents and get LLAMA AI response based on retrieved context"""
    try:
        query = request_data.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        logger.info(f"🤖 Document query with LLAMA: {query}")
        
        # Search for relevant documents
        vector_store = await get_vector_store()
        search_results = await vector_store.search_documents(query, limit=5)
        
        if not search_results:
            return {
                "success": True,
                "query": query,
                "response": "I couldn't find any relevant documents to answer your question. Please upload some documents first.",
                "sources": []
            }
        
        # Prepare context from search results
        context_parts = []
        sources = []
        
        for result in search_results:
            context_parts.append(f"Document: {result.metadata.get('filename', 'Unknown')}\nContent: {result.content}")
            sources.append({
                "filename": result.metadata.get('filename', 'Unknown'),
                "score": result.score,
                "content_preview": result.content[:100] + "..." if len(result.content) > 100 else result.content
            })
        
        context = "\n\n".join(context_parts)
        
        # Generate LLAMA response
        processor = await get_processor()
        
        # Create a prompt for document-based Q&A
        prompt = f"""Based on the following documents, please answer the user's question. Be brutally honest and factual.

Documents:
{context}

User Question: {query}

Please provide a comprehensive answer based on the document content. If the documents don't contain enough information to answer the question, say so clearly."""
        
        # Use LLAMA to generate response
        try:
            if hasattr(processor, 'llama') and processor.llama:
                if processor.llama_type == "ollama":
                    # Use Ollama
                    import requests
                    ollama_response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "llama2",
                            "prompt": prompt,
                            "stream": False
                        },
                        timeout=30
                    )
                    
                    if ollama_response.status_code == 200:
                        response_text = ollama_response.json().get("response", "No response generated")
                    else:
                        response_text = "Error: Could not generate response from LLAMA model"
                        
                else:
                    # Use llama-cpp-python
                    response = processor.llama(prompt, max_tokens=500, temperature=0.7)
                    response_text = response["choices"][0]["text"].strip()
            else:
                response_text = "LLAMA model not available. Here are the relevant document excerpts I found:\n\n" + context[:1000]
        
        except Exception as llama_error:
            logger.warning(f"LLAMA processing failed: {llama_error}")
            response_text = f"I found relevant information in your documents, but couldn't process it with AI. Here's what I found:\n\n{context[:1000]}"
        
        return {
            "success": True,
            "query": query,
            "response": response_text,
            "sources": sources,
            "context_used": len(context_parts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document query error: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/documents/stats")
async def get_document_stats():
    """Get statistics about stored documents"""
    try:
        vector_store = await get_vector_store()
        stats = await vector_store.get_collection_stats()
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its chunks"""
    try:
        logger.info(f"🗑️ Delete document request: {document_id}")
        
        vector_store = await get_vector_store()
        success = await vector_store.delete_document(document_id)
        
        if success:
            return {
                "success": True,
                "message": f"Document {document_id} deleted successfully"
            }
        else:
            return {
                "success": False,
                "message": f"Failed to delete document {document_id}"
            }
            
    except Exception as e:
        logger.error(f"Document deletion error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Profile Management Endpoints

@app.post("/profiles/clients")
async def create_client_profile_endpoint(
    name: str,
    type: str,
    description: str,
    tags: Optional[str] = None
):
    """Create a new client profile"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        tag_list = [t.strip() for t in tags.split(',')] if tags else []
        
        profile = await manager.create_client_profile(
            name=name,
            type=type,
            description=description,
            tags=tag_list
        )
        
        return {
            "success": True,
            "message": f"Client profile '{name}' created successfully",
            "profile": profile.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to create client profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles/clients")
async def list_client_profiles_endpoint():
    """List all client profiles"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        profiles = await manager.list_client_profiles()
        
        return {
            "success": True,
            "profiles": [p.to_dict() for p in profiles],
            "count": len(profiles)
        }
    except Exception as e:
        logger.error(f"Failed to list client profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles/clients/{profile_id}")
async def get_client_profile_endpoint(profile_id: str):
    """Get a specific client profile"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        profile = await manager.get_client_profile(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "profile": profile.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get client profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/profiles/clients/{profile_id}/facts")
async def add_fact_to_client_endpoint(
    profile_id: str,
    statement: str,
    source_id: str,
    confidence: float = 1.0
):
    """Add a fact to a client profile"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        fact = await manager.add_fact(
            profile_id=profile_id,
            profile_type="client",
            statement=statement,
            source_id=source_id,
            confidence=confidence
        )
        
        return {
            "success": True,
            "message": "Fact added successfully",
            "fact": fact.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to add fact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/profiles/clients/{profile_id}")
async def delete_client_profile_endpoint(profile_id: str):
    """Delete a client profile"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        success = await manager.delete_client_profile(profile_id)
        
        if success:
            return {"success": True, "message": "Profile deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Profile not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Brand Profile Endpoints

@app.post("/profiles/brands")
async def create_brand_profile_endpoint(
    name: str,
    description: str,
    values: Optional[str] = None,
    tags: Optional[str] = None
):
    """Create a new brand profile"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        value_list = [v.strip() for v in values.split(',')] if values else []
        tag_list = [t.strip() for t in tags.split(',')] if tags else []
        
        profile = await manager.create_brand_profile(
            name=name,
            description=description,
            values=value_list,
            tags=tag_list
        )
        
        return {
            "success": True,
            "message": f"Brand profile '{name}' created successfully",
            "profile": profile.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to create brand profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles/brands")
async def list_brand_profiles_endpoint():
    """List all brand profiles"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        profiles = await manager.list_brand_profiles()
        
        return {
            "success": True,
            "profiles": [p.to_dict() for p in profiles],
            "count": len(profiles)
        }
    except Exception as e:
        logger.error(f"Failed to list brand profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles/brands/{profile_id}")
async def get_brand_profile_endpoint(profile_id: str):
    """Get a specific brand profile"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        profile = await manager.get_brand_profile(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "profile": profile.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get brand profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/profiles/brands/{profile_id}/facts")
async def add_fact_to_brand_endpoint(
    profile_id: str,
    statement: str,
    source_id: str,
    confidence: float = 1.0
):
    """Add a fact to a brand profile"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        fact = await manager.add_fact(
            profile_id=profile_id,
            profile_type="brand",
            statement=statement,
            source_id=source_id,
            confidence=confidence
        )
        
        return {
            "success": True,
            "message": "Fact added successfully",
            "fact": fact.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to add fact: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Person Profile Endpoints

@app.post("/profiles/persons")
async def create_person_profile_endpoint(
    name: str,
    role: Optional[str] = None,
    company: Optional[str] = None,
    bio: Optional[str] = None,
    tags: Optional[str] = None
):
    """Create a new person profile"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        tag_list = [t.strip() for t in tags.split(',')] if tags else []
        
        profile = await manager.create_person_profile(
            name=name,
            role=role,
            company=company,
            bio=bio,
            tags=tag_list
        )
        
        return {
            "success": True,
            "message": f"Person profile '{name}' created successfully",
            "profile": profile.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to create person profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles/persons")
async def list_person_profiles_endpoint():
    """List all person profiles"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        profiles = await manager.list_person_profiles()
        
        return {
            "success": True,
            "profiles": [p.to_dict() for p in profiles],
            "count": len(profiles)
        }
    except Exception as e:
        logger.error(f"Failed to list person profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/profiles/persons/{profile_id}")
async def get_person_profile_endpoint(profile_id: str):
    """Get a specific person profile"""
    try:
        from profiles.profile_manager import get_profile_manager
        
        manager = await get_profile_manager()
        profile = await manager.get_person_profile(profile_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "success": True,
            "profile": profile.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get person profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Validation Endpoints

@app.post("/validation/extract-claims")
async def extract_claims_endpoint(
    transcription: str,
    transcription_id: str
):
    """Extract claims from a transcription"""
    try:
        from validation.claim_extractor import get_claim_extractor
        
        extractor = await get_claim_extractor()
        claims = await extractor.extract_claims(transcription, transcription_id)
        
        return {
            "success": True,
            "claims": [c.to_dict() for c in claims],
            "count": len(claims)
        }
    except Exception as e:
        logger.error(f"Failed to extract claims: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validation/validate-claim")
async def validate_claim_endpoint(claim_data: Dict[str, Any]):
    """Validate a single claim against knowledge base"""
    try:
        from validation.validator import get_validator
        from documents.schemas import Claim, ClaimType
        
        # Reconstruct claim from data
        claim = Claim(
            id=claim_data.get("id", ""),
            text=claim_data.get("text", ""),
            type=ClaimType(claim_data.get("type", "statement")),
            transcription_id=claim_data.get("transcription_id", ""),
            timestamp=claim_data.get("timestamp", 0.0),
            confidence=claim_data.get("confidence", 1.0)
        )
        
        validator = await get_validator()
        result = await validator.validate_claim(claim)
        
        return {
            "success": True,
            "validation": result.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to validate claim: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/validation/validate-transcription")
async def validate_transcription_endpoint(
    transcription: str,
    transcription_id: str,
    extract_claims: bool = True
):
    """Extract claims and validate a complete transcription"""
    try:
        from validation.claim_extractor import get_claim_extractor
        from validation.validator import get_validator
        
        logger.info(f"🔍 Validating transcription: {transcription_id}")
        
        # Extract claims
        if extract_claims:
            extractor = await get_claim_extractor()
            claims = await extractor.extract_claims(transcription, transcription_id)
        else:
            claims = []
        
        # Validate transcription
        validator = await get_validator()
        report = await validator.validate_transcription(
            transcription_id=transcription_id,
            transcription_text=transcription,
            claims=claims
        )
        
        return {
            "success": True,
            "report": report.to_dict()
        }
    except Exception as e:
        logger.error(f"Failed to validate transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/validation/report/{transcription_id}")
async def get_validation_report_endpoint(transcription_id: str):
    """Get validation report for a transcription"""
    try:
        # In a production system, you'd load this from a database
        # For now, return a message
        return {
            "success": False,
            "message": "Validation reports are generated on-demand. Use POST /validation/validate-transcription"
        }
    except Exception as e:
        logger.error(f"Failed to get validation report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Processing Endpoints

@app.post("/ai/process_with_validation")
async def process_with_document_validation(request_data: Dict[str, Any]):
    """Process audio file with LLAMA AI and validate against uploaded documents"""
    try:
        filename = request_data.get("filename", "")
        model = request_data.get("model", "llama")
        
        logger.info(f"🤖📚 Enhanced AI processing with document validation: {filename}")
        
        # Get the audio file data
        conn = await get_connector()
        audio_data = await conn.download_file(filename)
        
        if not audio_data:
            return {
                "success": False,
                "error": f"Could not retrieve audio file: {filename}"
            }
        
        # Process with enhanced LLAMA processor (includes document validation)
        enhanced_processor = await get_enhanced_processor()
        result = await enhanced_processor.process_audio_with_validation(audio_data, filename)
        
        if result.success:
            return {
                "success": True,
                "filename": filename,
                "transcription": result.transcription,
                "analysis": result.analysis,
                "summary": result.summary,
                "sentiment": result.sentiment,
                "keywords": result.keywords,
                "fact_check": result.fact_check,
                "brutal_honesty": result.brutal_honesty,
                "credibility_score": f"{result.credibility_score * 100:.1f}%" if result.credibility_score else "N/A",
                "questionable_claims": result.questionable_claims,
                "corrections": result.corrections,
                "confidence": f"{result.confidence * 100:.1f}%" if result.confidence else "N/A",
                "processing_time": f"{result.processing_time:.2f}s" if result.processing_time else "N/A",
                
                # Enhanced validation fields
                "document_validation": result.document_validation,
                "validation_score": f"{result.validation_score * 100:.1f}%" if result.validation_score else "N/A",
                "fact_check_sources": result.fact_check_sources,
                "contradictions": result.contradictions,
                "supporting_evidence": result.supporting_evidence,
                
                "model_used": model,
                "validation_enabled": True
            }
        else:
            return {
                "success": False,
                "error": result.error,
                "filename": filename,
                "model_used": model,
                "validation_enabled": True
            }
            
    except Exception as e:
        logger.error(f"Enhanced AI processing error: {e}")
        return {
            "success": False,
            "error": str(e),
            "validation_enabled": False
        }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    logger.info("WebSocket client connected")
    
    try:
        conn = await get_connector()
        
        # Send initial status
        device_status = await conn.get_device_status()
        if device_status:
            await websocket.send_text(json.dumps({
                "type": "status",
                "data": {
                    "connected": device_status.connected,
                    "recording": device_status.recording,
                    "files": device_status.files,
                    "connection_type": conn.current_connection.value if conn.current_connection else "none"
                }
            }))
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for client messages or send periodic updates
                data = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                message = json.loads(data)
                
                if message.get("type") == "get_status":
                    device_status = await conn.get_device_status()
                    if device_status:
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "data": {
                                "connected": device_status.connected,
                                "recording": device_status.recording,
                                "files": device_status.files,
                                "connection_type": conn.current_connection.value if conn.current_connection else "none"
                            }
                        }))
                
            except asyncio.TimeoutError:
                # Send periodic status update
                device_status = await conn.get_device_status()
                if device_status:
                    await websocket.send_text(json.dumps({
                        "type": "status_update",
                        "data": {
                            "connected": device_status.connected,
                            "recording": device_status.recording,
                            "files": device_status.files,
                            "connection_type": conn.current_connection.value if conn.current_connection else "none"
                        }
                    }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 BRUTALLY HONEST AI - API SERVER")
    print("="*60)
    print(f"📡 API URL: http://localhost:8000")
    print(f"📚 API Docs: http://localhost:8000/docs")
    print(f"🔌 WebSocket: ws://localhost:8000/ws")
    print("="*60)
    print("🔐 AUTHENTICATION")
    print("="*60)
    print(f"🔑 Master API Key: {API_MASTER_KEY}")
    print("")
    print("Use in requests:")
    print(f"  Authorization: Bearer {API_MASTER_KEY}")
    print("  OR")
    print(f"  X-API-Key: {API_MASTER_KEY}")
    print("="*60 + "\n")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
# ===== Transcription History Endpoint =====
@app.get("/api/transcription-history")
async def get_transcription_history():
    """Get all transcription history with saved recordings"""
    try:
        import json
        history = json.loads(HISTORY_FILE.read_text())
        return {"success": True, "history": list(reversed(history))}  # Most recent first
    except Exception as e:
        logger.error(f"Failed to get transcription history: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/recordings/{filename}")
async def get_recording(filename: str):
    """Download a saved recording"""
    from fastapi.responses import FileResponse
    file_path = RECORDINGS_DIR / filename
    if file_path.exists():
        return FileResponse(file_path, media_type="audio/webm", filename=filename)
    return {"success": False, "error": "Recording not found"}

@app.post("/api/save-recording")
async def save_recording_only(
    file: UploadFile = File(...),
    title: str = Form(None)
):
    """
    Save a recording WITHOUT transcription.
    The recording will be stored and can be transcribed later via re-analyze.
    """
    try:
        # Read file data
        audio_data = await file.read()
        
        if len(audio_data) == 0:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
        original_ext = Path(file.filename).suffix if file.filename else ".webm"
        safe_filename = f"recording_{timestamp}{original_ext}"
        
        # Save audio file
        audio_path = RECORDINGS_DIR / safe_filename
        audio_path.write_bytes(audio_data)
        logger.info(f"💾 Saved recording (no transcription): {audio_path}")
        
        # Create history entry with pending status
        entry_id = str(int(datetime.now().timestamp() * 1000))
        history = json.loads(HISTORY_FILE.read_text())
        
        new_entry = {
            "id": entry_id,
            "timestamp": datetime.now().isoformat(),
            "originalFilename": file.filename or safe_filename,
            "savedFilename": safe_filename,
            "filePath": str(audio_path),
            "title": title or f"Recording {timestamp}",
            "status": "saved",  # Not transcribed yet
            "result": None  # No transcription result yet
        }
        
        history.append(new_entry)
        HISTORY_FILE.write_text(json.dumps(history, indent=2))
        
        # Also save to frontend history
        frontend_history_file = Path(__file__).parent / "frontend" / "data" / "transcription_history.json"
        if frontend_history_file.exists():
            try:
                frontend_history = json.loads(frontend_history_file.read_text())
                frontend_history.append(new_entry)
                frontend_history_file.write_text(json.dumps(frontend_history, indent=2))
            except Exception as fe_err:
                logger.warning(f"Could not update frontend history: {fe_err}")
        
        return {
            "success": True,
            "id": entry_id,
            "filename": safe_filename,
            "size": len(audio_data),
            "message": "Recording saved. Use Re-analyze to transcribe later."
        }
        
    except Exception as e:
        logger.error(f"Save recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reanalyze/{id}")
async def reanalyze_transcription(id: str):
    """Re-analyze an existing transcription with updated fact-checker, or transcribe if not done yet."""
    try:
        # Load history
        history = json.loads(HISTORY_FILE.read_text())
        entry = next((e for e in history if e["id"] == id), None)
        
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        
        # Check if we need to transcribe first
        result = entry.get("result") or {}
        transcription = result.get("transcription", "")
        
        if not transcription:
            # No transcription yet - do full transcription
            file_path = entry.get("filePath")
            if not file_path or not Path(file_path).exists():
                raise HTTPException(status_code=400, detail="Audio file not found")
            
            logger.info(f"Transcribing file: {file_path}")
            
            # Read audio file and transcribe
            from src.ai.llama_processor import LLAMAProcessor
            processor = LLAMAProcessor()
            await processor.initialize()
            
            try:
                audio_data = Path(file_path).read_bytes()
                filename = Path(file_path).name
                proc_result = await processor.process_audio(audio_data, filename)
                
                if proc_result.success:
                    result = {
                        "transcription": proc_result.transcription,
                        "analysis": proc_result.analysis,
                        "summary": proc_result.summary,
                        "sentiment": proc_result.sentiment,
                        "keywords": proc_result.keywords,
                        "fact_check": proc_result.fact_check,
                        "brutal_honesty": proc_result.brutal_honesty,
                        "credibility_score": proc_result.credibility_score,
                        "confidence": proc_result.confidence,
                        "processing_time": proc_result.processing_time
                    }
                    transcription = proc_result.transcription
                else:
                    raise HTTPException(status_code=500, detail=f"Transcription failed: {proc_result.error}")
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Transcription error: {e}")
                raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
        
        if not transcription:
            raise HTTPException(status_code=400, detail="Could not transcribe audio")
        
        # Re-run fact checking using IntelligentFactChecker (LLAMA-powered)
        from src.ai.intelligent_fact_checker import IntelligentFactChecker
        
        fact_checker = IntelligentFactChecker()
        await fact_checker.initialize()
        fact_result = await fact_checker.check_facts(transcription)
        
        if fact_result.claims_found > 0:
            brutal_honesty = f"*Claim Analysis ({fact_result.claims_verified}/{fact_result.claims_found} verified):*\n{fact_result.summary}"
            credibility = fact_result.credibility_score
        else:
            brutal_honesty = "*No verifiable claims detected* - Only conversational content, opinions, or questions found."
            credibility = None  # N/A when nothing to verify
        
        # Update the entry
        if entry.get("result") is None:
            entry["result"] = result
        entry["result"]["brutal_honesty"] = brutal_honesty
        entry["result"]["credibility_score"] = credibility
        entry["result"]["fact_check"] = f"Re-analyzed: {fact_result.claims_false} false claims out of {fact_result.claims_found}"
        entry["status"] = "completed"
        
        # Save to both API and frontend history files
        HISTORY_FILE.write_text(json.dumps(history, indent=2))
        
        # Also update frontend history
        frontend_history_file = Path(__file__).parent / "frontend" / "data" / "transcription_history.json"
        if frontend_history_file.exists():
            try:
                frontend_history = json.loads(frontend_history_file.read_text())
                for fe in frontend_history:
                    if fe["id"] == id:
                        fe["result"] = entry["result"]
                        fe["status"] = "completed"
                        break
                frontend_history_file.write_text(json.dumps(frontend_history, indent=2))
            except Exception as fe_err:
                logger.warning(f"Could not update frontend history: {fe_err}")
        
        return {"success": True, "result": entry["result"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Re-analyze error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
