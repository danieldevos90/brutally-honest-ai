"""
Voice Insight & Feedback Platform - Main Application
Secure, EU-based platform for voice analysis using OMI DevKit 2
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pathlib import Path
import os
from dotenv import load_dotenv

from src.audio.omi_connector import OMIDevKitConnector
from src.audio.processor import AudioProcessor
from src.llm.analyzer import LLMAnalyzer
from src.database.manager import DatabaseManager
from src.models.schemas import AudioAnalysisRequest, AudioAnalysisResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
omi_connector = None
audio_processor = None
llm_analyzer = None
db_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global omi_connector, audio_processor, llm_analyzer, db_manager
    
    logger.info("Starting Voice Insight Platform...")
    
    # Initialize components
    try:
        # Database
        db_manager = DatabaseManager()
        await db_manager.initialize()
        
        # OMI DevKit connector
        omi_connector = OMIDevKitConnector()
        await omi_connector.initialize()
        
        # Audio processor
        audio_processor = AudioProcessor()
        await audio_processor.initialize()
        
        # LLM analyzer
        llm_analyzer = LLMAnalyzer()
        await llm_analyzer.initialize()
        
        logger.info("All components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down Voice Insight Platform...")
    if omi_connector:
        await omi_connector.cleanup()
    if audio_processor:
        await audio_processor.cleanup()
    if llm_analyzer:
        await llm_analyzer.cleanup()
    if db_manager:
        await db_manager.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Voice Insight & Feedback Platform",
    description="Secure, EU-based platform for voice analysis using OMI DevKit 2",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Voice Insight Platform is running", "status": "healthy"}

@app.get("/api/status")
async def get_status():
    """Get system status"""
    status = {
        "omi_connected": omi_connector.is_connected() if omi_connector else False,
        "audio_processor": audio_processor.is_ready() if audio_processor else False,
        "llm_analyzer": llm_analyzer.is_ready() if llm_analyzer else False,
        "database": db_manager.is_connected() if db_manager else False
    }
    return status

@app.post("/api/audio/upload", response_model=AudioAnalysisResponse)
async def upload_audio(file: UploadFile = File(...)):
    """Upload and analyze audio file"""
    if not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        # Save uploaded file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process audio
        result = await audio_processor.process_file(temp_path)
        
        # Analyze with LLM
        analysis = await llm_analyzer.analyze_transcript(result)
        
        # Store in database
        session_id = await db_manager.store_session(result, analysis)
        
        # Cleanup temp file
        os.unlink(temp_path)
        
        return AudioAnalysisResponse(
            session_id=session_id,
            transcript=result.transcript,
            speakers=result.speakers,
            analysis=analysis,
            timestamp=result.timestamp
        )
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/api/audio/stream")
async def websocket_audio_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time audio streaming from OMI"""
    await websocket.accept()
    
    try:
        logger.info("WebSocket connection established for audio streaming")
        
        # Start OMI audio streaming
        async for audio_chunk in omi_connector.stream_audio():
            # Process audio chunk
            result = await audio_processor.process_chunk(audio_chunk)
            
            if result:
                # Send transcription back to client
                await websocket.send_json({
                    "type": "transcription",
                    "data": {
                        "text": result.transcript,
                        "speaker": result.current_speaker,
                        "timestamp": result.timestamp.isoformat()
                    }
                })
                
                # Analyze for fact-checking if sentence is complete
                if result.is_complete_sentence:
                    analysis = await llm_analyzer.analyze_transcript(result)
                    await websocket.send_json({
                        "type": "analysis",
                        "data": {
                            "fact_check": analysis.fact_check,
                            "feedback": analysis.feedback,
                            "confidence": analysis.confidence
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

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    session = await db_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.get("/api/sessions")
async def list_sessions(limit: int = 10, offset: int = 0):
    """List recent sessions"""
    sessions = await db_manager.list_sessions(limit=limit, offset=offset)
    return sessions

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
