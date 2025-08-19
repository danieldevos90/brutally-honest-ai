"""
Enhanced Voice Insight Platform - With OMI Hardware Support
Includes basic audio processing and OMI DevKit 2 integration
"""

import asyncio
import logging
import tempfile
import os
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv
import serial.tools.list_ports
import serial
import numpy as np

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AudioChunk:
    """Audio data chunk from OMI device"""
    data: bytes
    timestamp: float
    sample_rate: int = 16000
    channels: int = 1

@dataclass
class ProcessingResult:
    """Basic processing result"""
    transcript: str
    duration: float
    timestamp: datetime
    confidence: float = 0.8

class OMIConnector:
    """Simplified OMI DevKit connector"""
    
    def __init__(self):
        self.serial_connection: Optional[serial.Serial] = None
        self.is_streaming = False
        
    def find_omi_device(self) -> Optional[str]:
        """Find OMI device in connected USB devices"""
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # Check for OMI device patterns
            desc = port.description.lower()
            if any(keyword in desc for keyword in ['omi', 'pico', 'rp2040', 'raspberry']):
                return port.device
            
            # Check by VID/PID if available
            if hasattr(port, 'vid') and hasattr(port, 'pid'):
                # Common Raspberry Pi Pico VID/PID
                if port.vid == 0x2E8A and port.pid in [0x0005, 0x000A]:
                    return port.device
        
        return None
    
    async def initialize(self) -> bool:
        """Initialize OMI connection"""
        device_port = self.find_omi_device()
        if not device_port:
            return False
        
        try:
            self.serial_connection = serial.Serial(
                port=device_port,
                baudrate=115200,
                timeout=1.0
            )
            await asyncio.sleep(1)  # Wait for device
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OMI: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.serial_connection is not None and self.serial_connection.is_open
    
    async def stream_audio(self):
        """Stream audio data (simulated for now)"""
        if not self.is_connected():
            return
        
        self.is_streaming = True
        chunk_size = 1024
        
        while self.is_streaming:
            # Simulate audio chunk (in real implementation, read from serial)
            audio_data = np.random.randint(-1000, 1000, chunk_size, dtype=np.int16).tobytes()
            
            yield AudioChunk(
                data=audio_data,
                timestamp=time.time(),
                sample_rate=16000,
                channels=1
            )
            
            await asyncio.sleep(0.1)  # 100ms chunks
    
    def stop_streaming(self):
        """Stop audio streaming"""
        self.is_streaming = False
    
    async def cleanup(self):
        """Cleanup connection"""
        self.stop_streaming()
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()

class BasicProcessor:
    """Basic audio processor (without heavy ML dependencies)"""
    
    def __init__(self):
        self.is_ready = True
    
    async def process_chunk(self, chunk: AudioChunk) -> Optional[ProcessingResult]:
        """Process audio chunk (basic simulation)"""
        # In real implementation, this would use Whisper
        # For now, simulate transcription
        
        if len(chunk.data) < 512:  # Too small
            return None
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Mock transcription based on audio characteristics
        mock_phrases = [
            "Hello, this is a test.",
            "The weather is nice today.",
            "I'm speaking into the OMI device.",
            "Voice recognition is working.",
            "Testing the audio pipeline."
        ]
        
        # Simple "transcription" based on timestamp
        phrase_index = int(chunk.timestamp) % len(mock_phrases)
        transcript = mock_phrases[phrase_index]
        
        return ProcessingResult(
            transcript=transcript,
            duration=len(chunk.data) / (chunk.sample_rate * 2),  # 16-bit = 2 bytes
            timestamp=datetime.now(),
            confidence=0.85
        )

# Global instances
omi_connector = None
audio_processor = None

# Create FastAPI app
app = FastAPI(
    title="Voice Insight Platform - Enhanced",
    description="Enhanced platform with OMI DevKit 2 support",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global omi_connector, audio_processor
    
    logger.info("Starting Enhanced Voice Insight Platform...")
    
    # Initialize OMI connector
    omi_connector = OMIConnector()
    await omi_connector.initialize()
    
    # Initialize basic processor
    audio_processor = BasicProcessor()
    
    logger.info("Platform initialization complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global omi_connector
    
    if omi_connector:
        await omi_connector.cleanup()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Enhanced Voice Insight Platform is running",
        "status": "healthy",
        "version": "enhanced",
        "features": ["omi_integration", "basic_audio_processing", "websocket_streaming"]
    }

@app.get("/api/status")
async def get_status():
    """Get enhanced system status"""
    
    # Test OMI connection
    omi_connected = omi_connector.is_connected() if omi_connector else False
    omi_device = omi_connector.find_omi_device() if omi_connector else None
    
    # Test services
    postgres_ready = True  # Assume ready
    qdrant_ready = False
    ollama_ready = False
    
    try:
        import requests
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
        "omi_device": omi_device,
        "audio_processor": audio_processor.is_ready if audio_processor else False,
        "llm_analyzer": ollama_ready,
        "database": postgres_ready and qdrant_ready,
        "services": {
            "postgres": postgres_ready,
            "qdrant": qdrant_ready,
            "ollama": ollama_ready
        },
        "capabilities": {
            "real_time_streaming": omi_connected,
            "audio_processing": True,
            "transcription": "basic_simulation",
            "fact_checking": ollama_ready
        }
    }

@app.get("/api/omi/ports")
async def list_serial_ports():
    """List available serial ports with OMI detection"""
    try:
        ports = serial.tools.list_ports.comports()
        
        port_list = []
        omi_device = None
        
        for port in ports:
            desc = port.description.lower()
            is_omi = any(keyword in desc for keyword in ['omi', 'pico', 'rp2040', 'raspberry'])
            
            # Also check VID/PID
            if hasattr(port, 'vid') and hasattr(port, 'pid'):
                if port.vid == 0x2E8A and port.pid in [0x0005, 0x000A]:
                    is_omi = True
            
            port_info = {
                "device": port.device,
                "description": port.description,
                "vid": getattr(port, 'vid', None),
                "pid": getattr(port, 'pid', None),
                "is_omi": is_omi,
                "manufacturer": getattr(port, 'manufacturer', None),
                "product": getattr(port, 'product', None)
            }
            port_list.append(port_info)
            
            if is_omi:
                omi_device = port.device
        
        return {
            "ports": port_list,
            "count": len(port_list),
            "omi_detected": omi_device is not None,
            "omi_device": omi_device
        }
    except Exception as e:
        return {"error": str(e), "ports": []}

@app.post("/api/omi/connect")
async def connect_omi():
    """Manually trigger OMI connection"""
    global omi_connector
    
    if not omi_connector:
        omi_connector = OMIConnector()
    
    success = await omi_connector.initialize()
    
    return {
        "success": success,
        "connected": omi_connector.is_connected(),
        "device": omi_connector.find_omi_device()
    }

@app.websocket("/api/audio/stream")
async def websocket_audio_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming"""
    await websocket.accept()
    
    try:
        logger.info("WebSocket connection established for audio streaming")
        
        if not omi_connector or not omi_connector.is_connected():
            await websocket.send_json({
                "type": "error",
                "data": {"message": "OMI device not connected"}
            })
            return
        
        # Start audio streaming
        async for audio_chunk in omi_connector.stream_audio():
            # Process audio chunk
            result = await audio_processor.process_chunk(audio_chunk)
            
            if result:
                # Send transcription
                await websocket.send_json({
                    "type": "transcription",
                    "data": {
                        "text": result.transcript,
                        "duration": result.duration,
                        "confidence": result.confidence,
                        "timestamp": result.timestamp.isoformat()
                    }
                })
                
                # Send basic analysis
                await websocket.send_json({
                    "type": "analysis",
                    "data": {
                        "summary": f"Processed {result.duration:.1f}s of audio",
                        "confidence": result.confidence,
                        "status": "simulated_processing"
                    }
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)}
        })
    finally:
        if omi_connector:
            omi_connector.stop_streaming()

@app.post("/api/audio/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Upload and process audio file"""
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Basic processing (simulate)
        file_size = len(content)
        duration = file_size / (16000 * 2)  # Estimate duration
        
        result = ProcessingResult(
            transcript=f"Uploaded audio file: {file.filename} ({file_size} bytes)",
            duration=duration,
            timestamp=datetime.now(),
            confidence=0.9
        )
        
        # Cleanup
        os.unlink(temp_path)
        
        return {
            "filename": file.filename,
            "size": file_size,
            "transcript": result.transcript,
            "duration": result.duration,
            "confidence": result.confidence,
            "timestamp": result.timestamp.isoformat(),
            "processing": "simulated"
        }
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test/omi")
async def test_omi_connection():
    """Test OMI connection and capabilities"""
    global omi_connector
    
    if not omi_connector:
        omi_connector = OMIConnector()
    
    # Find device
    device = omi_connector.find_omi_device()
    
    # Test connection
    connected = False
    if device:
        connected = await omi_connector.initialize()
    
    return {
        "device_found": device is not None,
        "device_path": device,
        "connection_successful": connected,
        "is_connected": omi_connector.is_connected(),
        "streaming_ready": connected,
        "test_timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    logger.info("Starting Enhanced Voice Insight Platform")
    uvicorn.run(
        "main_enhanced:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
