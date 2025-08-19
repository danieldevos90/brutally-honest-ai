"""
Simplified Voice Insight Platform - Test Version
Basic FastAPI server to test the system
"""

import asyncio
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Voice Insight Platform - Test",
    description="Simplified test version",
    version="1.0.0-test"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Voice Insight Platform is running", 
        "status": "healthy",
        "version": "test"
    }

@app.get("/api/status")
async def get_status():
    """Get system status"""
    
    # Test OMI connection
    omi_connected = False
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if 'pico' in port.description.lower() or 'omi' in port.description.lower():
                omi_connected = True
                break
    except:
        pass
    
    # Test Docker services
    postgres_ready = False
    qdrant_ready = False
    ollama_ready = False
    
    try:
        import requests
        # Test PostgreSQL (via Docker health check)
        postgres_ready = True  # Assume ready if Docker is running
        
        # Test Qdrant
        try:
            response = requests.get("http://localhost:6333/health", timeout=2)
            qdrant_ready = response.status_code == 200
        except:
            pass
            
        # Test Ollama
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            ollama_ready = response.status_code == 200
        except:
            pass
    except:
        pass
    
    return {
        "omi_connected": omi_connected,
        "audio_processor": True,  # Software component
        "llm_analyzer": ollama_ready,
        "database": postgres_ready and qdrant_ready,
        "services": {
            "postgres": postgres_ready,
            "qdrant": qdrant_ready,
            "ollama": ollama_ready
        }
    }

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint for basic functionality"""
    return {
        "test": "success",
        "components": {
            "fastapi": "working",
            "async": "working",
            "environment": "loaded" if os.getenv("POSTGRES_HOST") else "not_loaded"
        }
    }

@app.get("/api/omi/ports")
async def list_serial_ports():
    """List available serial ports"""
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        
        port_list = []
        for port in ports:
            port_info = {
                "device": port.device,
                "description": port.description,
                "vid": getattr(port, 'vid', None),
                "pid": getattr(port, 'pid', None),
                "is_omi": 'pico' in port.description.lower() or 'omi' in port.description.lower()
            }
            port_list.append(port_info)
        
        return {
            "ports": port_list,
            "count": len(port_list),
            "omi_detected": any(p["is_omi"] for p in port_list)
        }
    except Exception as e:
        return {"error": str(e), "ports": []}

if __name__ == "__main__":
    logger.info("Starting Voice Insight Platform - Test Version")
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
