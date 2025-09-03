#!/usr/bin/env python3
"""
Brutally Honest AI - REST API Server
Provides HTTP endpoints for the frontend using the src/ structure
"""

import asyncio
import sys
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import Response
import uvicorn
import logging
from typing import Optional, Dict, Any, List
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from audio.unified_connector import UnifiedESP32S3Connector, ConnectionType
from models.schemas import RecordingInfo
from ai.llama_processor import get_processor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Brutally Honest AI API",
    description="REST API for ESP32S3 Brutally Honest AI device management",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connector instance
connector: Optional[UnifiedESP32S3Connector] = None

async def get_connector() -> UnifiedESP32S3Connector:
    """Get or create the unified connector"""
    global connector
    if connector is None:
        connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
        await connector.initialize()
    return connector

@app.on_event("startup")
async def startup_event():
    """Initialize the connector on startup"""
    logger.info("🚀 Starting Brutally Honest AI API Server...")
    try:
        await get_connector()
        logger.info("✅ Connector initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize connector: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down API server...")
    global connector
    if connector:
        await connector.disconnect()
        logger.info("✅ Connector disconnected")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Brutally Honest AI API Server", "version": "1.0.0"}

@app.get("/status")
async def get_status():
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

@app.get("/scan_ports")
async def scan_ports():
    """Scan for available serial ports with detailed ESP32S3 detection"""
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

@app.post("/ai/process")
async def process_with_ai(request_data: Dict[str, Any]):
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
    print("🎯 Starting Brutally Honest AI API Server...")
    print("📡 API will be available at: http://localhost:8000")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    print("📚 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )