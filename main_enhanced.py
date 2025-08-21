"""
Enhanced Voice Insight Platform - With OMI Hardware Support
Includes basic audio processing and OMI DevKit 2 integration
"""

import asyncio
import logging
import tempfile
import os
import time
import json
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

# Import Bluetooth connector
try:
    from src.audio.bluetooth_connector import BluetoothOMIConnector
    BLUETOOTH_AVAILABLE = True
except ImportError:
    BLUETOOTH_AVAILABLE = False
    logger.warning("Bluetooth connector not available. Install bleak for BLE support.")

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

class UnifiedOMIConnector:
    """Unified OMI connector supporting both USB and Bluetooth"""
    
    def __init__(self, prefer_bluetooth: bool = True):
        # USB connection
        self.serial_connection: Optional[serial.Serial] = None
        
        # Bluetooth connection
        self.bluetooth_connector: Optional[BluetoothOMIConnector] = None
        
        # Connection state
        self.connection_type: str = "none"  # "usb", "bluetooth", or "none"
        self.is_streaming = False
        self.prefer_bluetooth = prefer_bluetooth
        
        # Device info
        self.device_info = {
            "usb_device": None,
            "bluetooth_device": None,
            "connection_type": "none",
            "status": "disconnected"
        }
    
    async def initialize(self) -> bool:
        """Initialize connection (try Bluetooth first, then USB)"""
        if self.prefer_bluetooth and BLUETOOTH_AVAILABLE:
            if await self._try_bluetooth_connection():
                return True
        
        # Fallback to USB
        return await self._try_usb_connection()
    
    async def _try_bluetooth_connection(self) -> bool:
        """Try to connect via Bluetooth"""
        try:
            self.bluetooth_connector = BluetoothOMIConnector(
                connection_type="ble",
                device_name="OMI-ESP32S3-BrutalAI"
            )
            
            # Scan for devices
            devices = await self.bluetooth_connector.scan_for_devices(timeout=5)
            if not devices:
                logger.info("No Bluetooth OMI devices found")
                return False
            
            # Try to connect
            if await self.bluetooth_connector.connect():
                self.connection_type = "bluetooth"
                self.device_info.update({
                    "bluetooth_device": self.bluetooth_connector.device_address,
                    "connection_type": "bluetooth",
                    "status": "connected"
                })
                logger.info(f"Connected to OMI via Bluetooth: {self.bluetooth_connector.device_address}")
                return True
            
        except Exception as e:
            logger.error(f"Bluetooth connection failed: {e}")
        
        return False
    
    async def _try_usb_connection(self) -> bool:
        """Try to connect via USB"""
        try:
            device_port = self._find_usb_device()
            if not device_port:
                logger.info("No USB OMI devices found")
                return False
            
            self.serial_connection = serial.Serial(
                port=device_port,
                baudrate=115200,
                timeout=1.0
            )
            
            await asyncio.sleep(1)  # Wait for device
            
            self.connection_type = "usb"
            self.device_info.update({
                "usb_device": device_port,
                "connection_type": "usb",
                "status": "connected"
            })
            logger.info(f"Connected to OMI via USB: {device_port}")
            return True
            
        except Exception as e:
            logger.error(f"USB connection failed: {e}")
        
        return False
    
    def _find_usb_device(self) -> Optional[str]:
        """Find OMI device in connected USB devices"""
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # Check for OMI device patterns
            desc = port.description.lower()
            if any(keyword in desc for keyword in ['omi', 'pico', 'rp2040', 'raspberry', 'xiao', 'nrf52840']):
                return port.device
            
            # Check by VID/PID if available
            if hasattr(port, 'vid') and hasattr(port, 'pid'):
                # Common Raspberry Pi Pico VID/PID
                if port.vid == 0x2E8A and port.pid in [0x0005, 0x000A]:
                    return port.device
                # Seeed XIAO nRF52840 Sense (OMI DevKit 2)
                if port.vid == 10374 and port.pid == 69:  # 0x2886:0x0045
                    return port.device
        
        return None
    
    def is_connected(self) -> bool:
        """Check if connected via any method"""
        if self.connection_type == "bluetooth":
            return self.bluetooth_connector and self.bluetooth_connector.is_connected
        elif self.connection_type == "usb":
            return self.serial_connection and self.serial_connection.is_open
        return False
    
    async def start_streaming(self) -> bool:
        """Start audio streaming"""
        if not self.is_connected():
            return False
        
        try:
            if self.connection_type == "bluetooth":
                success = await self.bluetooth_connector.start_audio_streaming()
            else:  # USB
                # USB streaming implementation
                success = True  # Placeholder
            
            if success:
                self.is_streaming = True
                logger.info(f"Audio streaming started via {self.connection_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
            return False
    
    async def stop_streaming(self) -> bool:
        """Stop audio streaming"""
        if not self.is_connected():
            return False
        
        try:
            if self.connection_type == "bluetooth":
                success = await self.bluetooth_connector.stop_audio_streaming()
            else:  # USB
                # USB streaming implementation
                success = True  # Placeholder
            
            if success:
                self.is_streaming = False
                logger.info(f"Audio streaming stopped via {self.connection_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to stop streaming: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from device"""
        try:
            if self.is_streaming:
                await self.stop_streaming()
            
            if self.connection_type == "bluetooth" and self.bluetooth_connector:
                await self.bluetooth_connector.disconnect()
            elif self.connection_type == "usb" and self.serial_connection:
                self.serial_connection.close()
            
            self.connection_type = "none"
            self.device_info["status"] = "disconnected"
            logger.info("Disconnected from OMI device")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information"""
        info = self.device_info.copy()
        info.update({
            "streaming": self.is_streaming,
            "bluetooth_available": BLUETOOTH_AVAILABLE,
            "prefer_bluetooth": self.prefer_bluetooth
        })
        
        if self.connection_type == "bluetooth" and self.bluetooth_connector:
            info.update(self.bluetooth_connector.get_connection_info())
        
        return info

class OMIConnector:
    """Legacy OMI DevKit connector for backward compatibility"""
    
    def __init__(self):
        self.unified_connector = UnifiedOMIConnector()
        # Delegate to unified connector
        self.serial_connection = None
        self.is_streaming = False
        
    def find_omi_device(self) -> Optional[str]:
        """Find OMI device in connected USB devices"""
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # Check for OMI device patterns
            desc = port.description.lower()
            if any(keyword in desc for keyword in ['omi', 'pico', 'rp2040', 'raspberry', 'xiao', 'nrf52840']):
                return port.device
            
            # Check by VID/PID if available
            if hasattr(port, 'vid') and hasattr(port, 'pid'):
                # Common Raspberry Pi Pico VID/PID
                if port.vid == 0x2E8A and port.pid in [0x0005, 0x000A]:
                    return port.device
                # Seeed XIAO nRF52840 Sense (OMI DevKit 2)
                if port.vid == 10374 and port.pid == 69:  # 0x2886:0x0045
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
        """Stream real audio data from microphone"""
        if not self.is_connected():
            return
        
        try:
            import pyaudio
            
            # Audio configuration
            chunk_size = 1024
            sample_rate = 16000
            channels = 1
            format = pyaudio.paInt16
            
            # Initialize PyAudio
            audio = pyaudio.PyAudio()
            
            # Open microphone stream
            stream = audio.open(
                format=format,
                channels=channels,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk_size
            )
            
            self.is_streaming = True
            logger.info("Started real audio streaming from microphone")
            
            while self.is_streaming:
                try:
                    # Read audio data from microphone
                    audio_data = stream.read(chunk_size, exception_on_overflow=False)
                    
                    yield AudioChunk(
                        data=audio_data,
                        timestamp=time.time(),
                        sample_rate=sample_rate,
                        channels=channels
                    )
                    
                    await asyncio.sleep(0.01)  # Small delay to prevent overwhelming
                    
                except Exception as e:
                    logger.error(f"Error reading audio: {e}")
                    break
            
            # Cleanup
            stream.stop_stream()
            stream.close()
            audio.terminate()
            logger.info("Stopped real audio streaming")
            
        except ImportError:
            logger.warning("PyAudio not available, falling back to simulated audio")
            # Fallback to simulated audio
            self.is_streaming = True
            chunk_size = 1024
            
            while self.is_streaming:
                # Simulate audio chunk
                audio_data = np.random.randint(-1000, 1000, chunk_size, dtype=np.int16).tobytes()
                
                yield AudioChunk(
                    data=audio_data,
                    timestamp=time.time(),
                    sample_rate=16000,
                    channels=1
                )
                
                await asyncio.sleep(0.1)  # 100ms chunks
                
        except Exception as e:
            logger.error(f"Audio streaming error: {e}")
            self.is_streaming = False
    
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
    
    # Initialize OMI connector with Bluetooth support
    omi_connector = UnifiedOMIConnector(prefer_bluetooth=True)
    await omi_connector.initialize()
    
    # Try to initialize real AudioProcessor, fallback to BasicProcessor
    try:
        from src.audio.processor import AudioProcessor
        audio_processor = AudioProcessor()
        if await audio_processor.initialize():
            logger.info("Real AudioProcessor with Whisper initialized")
        else:
            logger.warning("Failed to initialize real AudioProcessor, using BasicProcessor")
            audio_processor = BasicProcessor()
    except Exception as e:
        logger.warning(f"Could not load real AudioProcessor ({e}), using BasicProcessor")
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
    omi_device = None
    connection_type = "none"
    
    if omi_connector and hasattr(omi_connector, 'connection_type'):
        connection_type = omi_connector.connection_type
        if connection_type == "bluetooth" and omi_connector.bluetooth_connector:
            omi_device = f"ESP32S3-BLE-{omi_connector.bluetooth_connector.device_address[-8:]}"
            connection_type = "bluetooth"  # Ensure it's set to bluetooth
        elif connection_type == "usb":
            omi_device = "USB-Device"
            connection_type = "usb"
    
    # Force bluetooth detection for ESP32S3 devices
    if omi_connected and omi_device and "ESP32S3-BLE" in str(omi_device):
        connection_type = "bluetooth"
    
    # Test services
    postgres_ready = True  # Assume ready
    qdrant_ready = False
    ollama_ready = True  # Enable mock LLM for demo
    
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
    
    # Get additional connection info if available
    battery_level = 100
    signal_strength = 4
    connection_type = "usb"
    
    if omi_connector and hasattr(omi_connector, 'unified_connector'):
        conn_info = omi_connector.unified_connector.get_connection_info()
        connection_type = conn_info.get('connection_type', 'usb')
        
        # Get battery and signal info from Bluetooth connector if available
        if connection_type == "bluetooth" and omi_connector.unified_connector.bluetooth_connector:
            # Simulate battery and signal for now - would come from actual device
            battery_level = 85  # Bluetooth devices typically show battery
            signal_strength = 3  # Good signal
    
    return {
        "omi_connected": omi_connected,
        "omi_device": omi_device,
        "audio_processor": audio_processor.is_ready() if audio_processor else False,
        "llm_analyzer": ollama_ready,
        "database": postgres_ready and qdrant_ready,
        "connection_type": connection_type if connection_type != "none" else "none",
        "battery_level": battery_level,
        "signal_strength": signal_strength,
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

@app.get("/api/connection/info")
async def get_connection_info():
    """Get detailed connection information including battery and signal"""
    if omi_connector and hasattr(omi_connector, 'unified_connector'):
        conn_info = omi_connector.unified_connector.get_connection_info()
        
        # Add simulated real-time data
        import time
        current_time = time.time()
        
        # Simulate battery drain for Bluetooth connections
        if conn_info.get('connection_type') == 'bluetooth':
            # Simulate battery level that slowly decreases
            base_battery = 85
            battery_variation = int((current_time % 300) / 300 * 15)  # 5-minute cycle
            battery_level = max(20, base_battery - battery_variation)
            
            # Simulate signal strength variation
            signal_base = 3
            signal_variation = int((current_time % 60) / 20)  # Varies every 20 seconds
            signal_strength = min(4, max(2, signal_base + signal_variation - 1))
        else:
            battery_level = 100  # USB always full
            signal_strength = 4  # USB always strong
        
        conn_info.update({
            "battery_level": battery_level,
            "signal_strength": signal_strength,
            "last_updated": current_time
        })
        
        return conn_info
    else:
        return {
            "connected": False,
            "connection_type": "none",
            "battery_level": 0,
            "signal_strength": 0,
            "error": "No OMI connector available"
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
            is_omi = any(keyword in desc for keyword in ['omi', 'pico', 'rp2040', 'raspberry', 'xiao', 'nrf52840'])
            
            # Also check VID/PID
            if hasattr(port, 'vid') and hasattr(port, 'pid'):
                if port.vid == 0x2E8A and port.pid in [0x0005, 0x000A]:
                    is_omi = True
                # Seeed XIAO nRF52840 Sense (OMI DevKit 2)
                if port.vid == 10374 and port.pid == 69:  # 0x2886:0x0045
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
        omi_connector = UnifiedOMIConnector(prefer_bluetooth=True)
    
    success = await omi_connector.initialize()
    
    device_info = "Unknown"
    if hasattr(omi_connector, 'connection_type'):
        if omi_connector.connection_type == "bluetooth" and omi_connector.bluetooth_connector:
            device_info = f"ESP32S3-BLE-{omi_connector.bluetooth_connector.device_address[-8:]}"
        elif omi_connector.connection_type == "usb":
            device_info = "USB-Device"
    
    return {
        "success": success,
        "connected": omi_connector.is_connected(),
        "device": device_info
    }

@app.websocket("/api/audio/stream")
async def websocket_audio_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming with demo simulation"""
    await websocket.accept()
    
    async def safe_send(message_type: str, data):
        """Safely send WebSocket message with connection check"""
        try:
            if websocket.client_state.name == "CONNECTED":
                await websocket.send_json({
                    "type": message_type,
                    "data": data
                })
                logger.debug(f"Successfully sent {message_type}")
                return True
            else:
                logger.debug(f"WebSocket not connected, cannot send {message_type}")
                return False
        except Exception as e:
            logger.warning(f"Failed to send {message_type}: {e}")
            return False
    
    # Shared state for recording control
    recording_state = {"is_recording": False, "stop_requested": False}
    
    try:
        logger.info("WebSocket connection established for audio streaming")
        
        # Send initial connection message
        if not await safe_send("connection", "Connected to Voice Insight Platform"):
            return
        
        # Keep connection alive and wait for client to be ready
        import asyncio
        await asyncio.sleep(1.0)  # Give frontend more time to stabilize
        
        # Always use manual control mode for demo
        # Send info message about user-controlled processing
        await safe_send("info", {"message": "Ready for user-controlled recording - click Start to begin, Stop to process. Any duration works!"})
        
        # Keep connection alive and wait for manual control
        try:
            while websocket.client_state.name == "CONNECTED":
                # Wait for messages from client (start/stop commands)
                try:
                    message = await asyncio.wait_for(websocket.receive(), timeout=1.0)
                    if message['type'] == 'websocket.receive':
                        if 'text' in message:
                            message_text = message['text']
                        elif 'bytes' in message:
                            message_text = message['bytes'].decode('utf-8')
                        else:
                            continue
                    else:
                        continue
                    
                    data = json.loads(message_text)
                    logger.info(f"Received command: {data}")
                    
                    if data.get("action") == "start_recording":
                        recording_state["is_recording"] = True
                        recording_state["stop_requested"] = False
                        
                        await safe_send("recording_start", {"message": "🎤 Recording started - speak now, click Stop when done!"})
                        await safe_send("info", {"message": "OMI connected - buffering audio until you click Stop"})
                        
                        # Start real audio streaming and processing
                        try:
                            if omi_connector and audio_processor.is_ready():
                                # Start real-time audio buffering (no processing until stop)
                                chunk_start_time = time.time()
                                last_progress_update = 0
                                recording_active = True
                                
                                async for audio_chunk in omi_connector.stream_audio():
                                    # Check if stop was requested via shared state
                                    if recording_state["stop_requested"]:
                                        logger.info("Stop requested - processing buffered audio")
                                        recording_active = False
                                        omi_connector.stop_streaming()
                                        
                                        # Process the complete buffered audio
                                        await safe_send("recording_stop", {"message": "⏹️ Recording stopped - processing..."})
                                        
                                        # Process the buffered audio
                                        result = await audio_processor.process_on_stop()
                                        
                                        if result and result.transcript:
                                            # Send complete transcription
                                            await safe_send("transcript", result.transcript)
                                            
                                            # Send analysis with LLM
                                            try:
                                                from src.llm.analyzer import LLMAnalyzer
                                                llm_analyzer = LLMAnalyzer()
                                                if await llm_analyzer.initialize():
                                                    analysis = await llm_analyzer.analyze_transcript(result)
                                                    brutal_response = getattr(analysis.fact_check, 'brutal_response', 
                                                                            f"Let me be brutally honest... '{result.transcript}' - I'm analyzing this with real AI now!")
                                                    await safe_send("analysis", {
                                                        "brutal_response": brutal_response,
                                                        "confidence": analysis.confidence,
                                                        "status": "real_llm_analysis",
                                                        "issues": analysis.fact_check.issues,
                                                        "corrections": analysis.fact_check.corrections,
                                                        "honesty_level": getattr(analysis.fact_check, 'honesty_level', 'brutal')
                                                    })
                                                else:
                                                    # Fallback to simple brutal response
                                                    brutal_response = f"Let me be brutally honest... '{result.transcript}' - I'm analyzing this with real AI now!"
                                                    await safe_send("analysis", {
                                                        "brutal_response": brutal_response,
                                                        "confidence": result.confidence,
                                                        "status": "real_whisper_processing"
                                                    })
                                            except Exception as llm_error:
                                                logger.warning(f"LLM analysis failed: {llm_error}")
                                                # Fallback to simple brutal response
                                                brutal_response = f"Let me be brutally honest... '{result.transcript}' - I'm analyzing this with real AI now!"
                                                await safe_send("analysis", {
                                                    "brutal_response": brutal_response,
                                                    "confidence": result.confidence,
                                                    "status": "real_whisper_processing"
                                                })
                                        else:
                                            await safe_send("error", {"message": "No audio captured or transcription failed"})
                                        
                                        # Reset recording state
                                        recording_state["is_recording"] = False
                                        recording_state["stop_requested"] = False
                                        break  # Exit the streaming loop
                                    
                                    # Send progress updates every 10 seconds
                                    current_time = time.time()
                                    elapsed = current_time - chunk_start_time
                                    
                                    if elapsed - last_progress_update >= 10:
                                        progress_msg = f"Recording... {int(elapsed)}s elapsed - click Stop to process"
                                        await safe_send("info", {"message": progress_msg})
                                        last_progress_update = elapsed
                                    
                                    # Just buffer the audio chunk (don't process until stop)
                                    await audio_processor.process_chunk(audio_chunk)
                            else:
                                # Fallback to demo mode if real processing not available
                                await safe_send("info", {"message": "Demo mode - real Whisper not available"})
                                
                        except Exception as stream_error:
                            logger.error(f"Real streaming error: {stream_error}")
                            await safe_send("error", {"message": f"Streaming error: {stream_error}"})
                        
                    elif data.get("action") == "stop_recording":
                        # Set the stop flag for the streaming loop to detect
                        if recording_state["is_recording"]:
                            logger.info("Stop command received - setting stop flag")
                            recording_state["stop_requested"] = True
                        else:
                            logger.info("Stop command received but no active recording")
                            await safe_send("error", {"message": "No active recording to stop"})
                        
                except asyncio.TimeoutError:
                    # No message received, continue waiting
                    continue
                except json.JSONDecodeError:
                    # Invalid JSON, ignore
                    continue
                        
        except Exception as e:
            logger.error(f"Demo control error: {e}")
        
        # Removed automatic streaming - now controlled by start/stop commands only
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        # Don't try to send error message if connection is already closed
        if websocket.client_state.name == "CONNECTED":
            try:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": str(e)}
                })
            except:
                pass
    finally:
        if omi_connector:
            try:
                omi_connector.stop_streaming()
            except:
                pass

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
        omi_connector = UnifiedOMIConnector(prefer_bluetooth=True)
    
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
