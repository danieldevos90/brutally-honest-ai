"""
Transcription API endpoints for ESP32S3 recordings
Provides endpoints to download and transcribe recordings using Whisper AI
"""

import asyncio
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import json

from ..audio.unified_connector import UnifiedESP32S3Connector, ConnectionType
from ..audio.processor import AudioProcessor
from ..models.schemas import TranscriptionResult, RecordingAnalysis

logger = logging.getLogger(__name__)

# Response models
class TranscriptionResponse(BaseModel):
    success: bool
    filename: str
    transcript: str
    duration_s: float
    confidence: float
    speakers: List[Dict[str, Any]]
    error: Optional[str] = None

class RecordingListResponse(BaseModel):
    success: bool
    recordings: List[Dict[str, Any]]
    total_count: int
    error: Optional[str] = None

class DownloadResponse(BaseModel):
    success: bool
    filename: str
    size_bytes: int
    duration_s: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    error: Optional[str] = None

# Global instances (should be managed by dependency injection in production)
_connector: Optional[UnifiedESP32S3Connector] = None
_audio_processor: Optional[AudioProcessor] = None

async def get_connector() -> UnifiedESP32S3Connector:
    """Get or create connector instance"""
    global _connector
    if _connector is None:
        _connector = UnifiedESP32S3Connector(preferred_connection=ConnectionType.USB)
        await _connector.initialize()
    return _connector

async def get_audio_processor() -> AudioProcessor:
    """Get or create audio processor instance"""
    global _audio_processor
    if _audio_processor is None:
        _audio_processor = AudioProcessor()
        await _audio_processor.initialize()
    return _audio_processor

# Create router
router = APIRouter(prefix="/transcription", tags=["transcription"])

@router.get("/recordings", response_model=RecordingListResponse)
async def list_recordings():
    """List all available recordings on the ESP32S3 device"""
    try:
        connector = await get_connector()
        recordings = await connector.get_recordings()
        
        recordings_data = []
        for rec in recordings:
            recordings_data.append({
                "name": rec.name,
                "size": rec.size,
                "size_mb": round(rec.size / (1024 * 1024), 2),
                "date": getattr(rec, 'date', None)
            })
        
        return RecordingListResponse(
            success=True,
            recordings=recordings_data,
            total_count=len(recordings_data)
        )
        
    except Exception as e:
        logger.error(f"Failed to list recordings: {e}")
        return RecordingListResponse(
            success=False,
            recordings=[],
            total_count=0,
            error=str(e)
        )

@router.get("/download/{filename}", response_model=DownloadResponse)
async def download_recording(filename: str):
    """Download a specific recording from the ESP32S3 device"""
    try:
        connector = await get_connector()
        
        # Download file
        file_data = await connector.download_file(filename)
        if not file_data:
            raise HTTPException(status_code=404, detail=f"Recording {filename} not found")
        
        # Analyze WAV file if possible
        duration_s = None
        sample_rate = None
        channels = None
        
        try:
            # Save to temp file for analysis
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name
            
            # Analyze WAV properties
            import wave
            with wave.open(temp_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                duration_s = frames / sample_rate if sample_rate > 0 else None
            
            # Cleanup temp file
            os.unlink(temp_path)
            
        except Exception as e:
            logger.warning(f"Could not analyze WAV file {filename}: {e}")
        
        return DownloadResponse(
            success=True,
            filename=filename,
            size_bytes=len(file_data),
            duration_s=duration_s,
            sample_rate=sample_rate,
            channels=channels
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download recording {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transcribe/{filename}", response_model=TranscriptionResponse)
async def transcribe_recording(filename: str, background_tasks: BackgroundTasks):
    """Download and transcribe a specific recording using Whisper AI"""
    try:
        connector = await get_connector()
        processor = await get_audio_processor()
        
        # Download file
        logger.info(f"Downloading {filename} for transcription...")
        file_data = await connector.download_file(filename)
        if not file_data:
            raise HTTPException(status_code=404, detail=f"Recording {filename} not found")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(file_data)
            temp_path = temp_file.name
        
        try:
            # Transcribe with Whisper AI
            logger.info(f"Transcribing {filename} with Whisper AI...")
            result = await processor.process_file(temp_path)
            
            # Format speakers data
            speakers_data = []
            for speaker in result.speakers:
                speakers_data.append({
                    "speaker_id": speaker.speaker_id,
                    "start_time": speaker.start_time,
                    "end_time": speaker.end_time,
                    "text": speaker.text,
                    "confidence": speaker.confidence
                })
            
            # Schedule cleanup of temp file
            background_tasks.add_task(os.unlink, temp_path)
            
            return TranscriptionResponse(
                success=True,
                filename=filename,
                transcript=result.transcript,
                duration_s=result.audio_duration,
                confidence=result.confidence,
                speakers=speakers_data
            )
            
        except Exception as e:
            # Cleanup temp file on error
            try:
                os.unlink(temp_path)
            except:
                pass
            raise e
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to transcribe recording {filename}: {e}")
        return TranscriptionResponse(
            success=False,
            filename=filename,
            transcript="",
            duration_s=0.0,
            confidence=0.0,
            speakers=[],
            error=str(e)
        )

@router.post("/transcribe-latest", response_model=TranscriptionResponse)
async def transcribe_latest_recording(background_tasks: BackgroundTasks):
    """Download and transcribe the latest recording"""
    try:
        connector = await get_connector()
        
        # Get recordings list
        recordings = await connector.get_recordings()
        if not recordings:
            raise HTTPException(status_code=404, detail="No recordings found")
        
        # Get latest recording (assuming sorted by name/date)
        latest = recordings[-1]
        
        # Transcribe it
        return await transcribe_recording(latest.name, background_tasks)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to transcribe latest recording: {e}")
        return TranscriptionResponse(
            success=False,
            filename="",
            transcript="",
            duration_s=0.0,
            confidence=0.0,
            speakers=[],
            error=str(e)
        )

@router.get("/status")
async def get_transcription_status():
    """Get transcription system status"""
    try:
        connector = await get_connector()
        processor = await get_audio_processor()
        
        device_status = await connector.get_device_status()
        
        return {
            "success": True,
            "device_connected": device_status.connected if device_status else False,
            "connection_type": device_status.connection_type.value if device_status else None,
            "whisper_ready": processor.is_ready(),
            "whisper_model": processor.whisper_model_name,
            "recordings_available": device_status.files if device_status else 0
        }
        
    except Exception as e:
        logger.error(f"Failed to get transcription status: {e}")
        return {
            "success": False,
            "error": str(e),
            "device_connected": False,
            "whisper_ready": False
        }

@router.post("/batch-transcribe")
async def batch_transcribe_all(background_tasks: BackgroundTasks):
    """Download and transcribe all recordings (use with caution for many files)"""
    try:
        connector = await get_connector()
        processor = await get_audio_processor()
        
        # Get all recordings
        recordings = await connector.get_recordings()
        if not recordings:
            return {"success": True, "message": "No recordings to transcribe", "results": []}
        
        # Limit to prevent overwhelming the system
        if len(recordings) > 10:
            raise HTTPException(
                status_code=400, 
                detail=f"Too many recordings ({len(recordings)}). Maximum 10 allowed for batch processing."
            )
        
        results = []
        for recording in recordings:
            try:
                # Use the existing transcribe endpoint logic
                response = await transcribe_recording(recording.name, background_tasks)
                results.append(response.dict())
                
            except Exception as e:
                logger.error(f"Failed to transcribe {recording.name}: {e}")
                results.append({
                    "success": False,
                    "filename": recording.name,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": f"Processed {len(recordings)} recordings",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed batch transcription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Cleanup function for graceful shutdown
async def cleanup_transcription_resources():
    """Cleanup transcription resources"""
    global _connector, _audio_processor
    
    if _audio_processor:
        await _audio_processor.cleanup()
        _audio_processor = None
    
    if _connector:
        await _connector.disconnect()
        _connector = None
