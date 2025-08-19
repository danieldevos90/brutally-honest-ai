"""
Simple Voice Recording with Brutal Honesty
Just records between start/stop, transcribes, and gives brutal feedback
"""

import asyncio
import logging
import os
import tempfile
import time
import json
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import pyaudio
import wave
import whisper
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Brutally Honest Voice Recorder",
    description="Simple recording with brutal feedback",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
whisper_model = None
recording_state = {
    "is_recording": False,
    "audio_frames": [],
    "sample_rate": 16000,
    "channels": 1,
    "format": pyaudio.paInt16,
    "chunk_size": 1024,
    "stream": None,
    "audio": None
}

@app.on_event("startup")
async def startup_event():
    """Load Whisper model on startup"""
    global whisper_model
    logger.info("Loading Whisper model...")
    whisper_model = whisper.load_model("base")
    logger.info("Whisper model loaded successfully")

@app.get("/")
async def root():
    """Health check"""
    return {"message": "Simple Voice Recorder is running", "status": "healthy"}

@app.websocket("/api/audio/stream")
async def websocket_audio_stream(websocket: WebSocket):
    """WebSocket endpoint for recording control"""
    await websocket.accept()
    
    try:
        logger.info("WebSocket connection established")
        
        # Send connection message
        await websocket.send_json({
            "type": "connection",
            "data": "Connected to Simple Voice Recorder"
        })
        
        await websocket.send_json({
            "type": "info",
            "data": {"message": "Ready! Click Start to record, Stop to transcribe."}
        })
        
        while True:
            # Wait for commands
            message = await websocket.receive_text()
            data = json.loads(message)
            action = data.get("action")
            
            if action == "start_recording":
                await start_recording(websocket)
            
            elif action == "stop_recording":
                await stop_recording(websocket)
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        # Clean up if recording was in progress
        if recording_state["is_recording"]:
            stop_audio_stream()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "data": {"message": str(e)}
        })

async def start_recording(websocket: WebSocket):
    """Start recording audio"""
    if recording_state["is_recording"]:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Already recording"}
        })
        return
    
    try:
        # Initialize PyAudio
        recording_state["audio"] = pyaudio.PyAudio()
        recording_state["audio_frames"] = []
        
        # Open audio stream
        recording_state["stream"] = recording_state["audio"].open(
            format=recording_state["format"],
            channels=recording_state["channels"],
            rate=recording_state["sample_rate"],
            input=True,
            frames_per_buffer=recording_state["chunk_size"],
            stream_callback=audio_callback
        )
        
        recording_state["is_recording"] = True
        recording_state["stream"].start_stream()
        
        await websocket.send_json({
            "type": "recording_start",
            "data": {"message": "🎤 Recording... Click Stop when done!"}
        })
        
        logger.info("Recording started")
        
    except Exception as e:
        logger.error(f"Failed to start recording: {e}")
        await websocket.send_json({
            "type": "error",
            "data": {"message": f"Failed to start recording: {e}"}
        })

def audio_callback(in_data, frame_count, time_info, status):
    """Callback for audio stream - just store the audio data"""
    if recording_state["is_recording"]:
        recording_state["audio_frames"].append(in_data)
    return (in_data, pyaudio.paContinue)

async def stop_recording(websocket: WebSocket):
    """Stop recording and process the audio"""
    if not recording_state["is_recording"]:
        await websocket.send_json({
            "type": "error",
            "data": {"message": "Not recording"}
        })
        return
    
    try:
        # Stop recording
        recording_state["is_recording"] = False
        stop_audio_stream()
        
        await websocket.send_json({
            "type": "recording_stop",
            "data": {"message": "⏹️ Stopped. Processing audio..."}
        })
        
        # Save audio to temporary WAV file
        temp_wav = save_audio_to_file()
        
        if temp_wav and os.path.exists(temp_wav):
            # Transcribe with Whisper
            logger.info("Transcribing audio...")
            result = whisper_model.transcribe(temp_wav, language="en")
            transcript = result["text"].strip()
            
            # Clean up temp file
            os.unlink(temp_wav)
            
            if transcript:
                # Send transcript
                await websocket.send_json({
                    "type": "transcript",
                    "data": transcript
                })
                
                # Generate brutal honesty response
                brutal_response = await get_brutal_response(transcript)
                
                # Send analysis
                await websocket.send_json({
                    "type": "analysis",
                    "data": {
                        "brutal_response": brutal_response,
                        "confidence": 0.9,
                        "status": "complete"
                    }
                })
            else:
                await websocket.send_json({
                    "type": "error",
                    "data": {"message": "No speech detected in audio"}
                })
        else:
            await websocket.send_json({
                "type": "error",
                "data": {"message": "No audio was recorded"}
            })
            
    except Exception as e:
        logger.error(f"Error processing recording: {e}")
        await websocket.send_json({
            "type": "error",
            "data": {"message": f"Processing error: {e}"}
        })

def stop_audio_stream():
    """Stop and cleanup audio stream"""
    if recording_state["stream"]:
        recording_state["stream"].stop_stream()
        recording_state["stream"].close()
        recording_state["stream"] = None
    
    if recording_state["audio"]:
        recording_state["audio"].terminate()
        recording_state["audio"] = None

def save_audio_to_file():
    """Save recorded audio frames to WAV file"""
    if not recording_state["audio_frames"]:
        return None
    
    try:
        # Create temporary WAV file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Write WAV file
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(recording_state["channels"])
            wf.setsampwidth(pyaudio.get_sample_size(recording_state["format"]))
            wf.setframerate(recording_state["sample_rate"])
            wf.writeframes(b''.join(recording_state["audio_frames"]))
        
        logger.info(f"Saved audio to: {temp_path}")
        return temp_path
        
    except Exception as e:
        logger.error(f"Failed to save audio: {e}")
        return None

async def get_brutal_response(transcript: str) -> str:
    """Generate brutal honesty response - can be replaced with real LLM"""
    # Try to use Ollama if available
    try:
        import requests
        
        prompt = f"""You are a brutally honest AI. You ALWAYS start your responses with "Let me be brutally honest..." 
        and then tell the unvarnished truth without sugar-coating anything.
        
        User said: "{transcript}"
        
        Respond with brutal honesty about what they said. Point out any:
        - Logical flaws
        - Incorrect facts
        - Questionable assumptions
        - Missing context
        - Overconfident claims
        
        Be direct but not insulting. Focus on the content, not the person."""
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral:7b",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get("response", get_fallback_response(transcript))
        else:
            return get_fallback_response(transcript)
            
    except Exception as e:
        logger.warning(f"LLM not available: {e}")
        return get_fallback_response(transcript)

def get_fallback_response(transcript: str) -> str:
    """Fallback brutal responses when LLM is not available"""
    # Check for common incorrect statements
    lower_transcript = transcript.lower()
    
    if "elephant" in lower_transcript and "small" in lower_transcript:
        return "Let me be brutally honest... Elephants are NOT small animals. They're the largest land mammals on Earth, weighing up to 6,000 kg. That's a fundamental factual error that undermines your credibility."
    
    elif "always" in lower_transcript or "never" in lower_transcript or "everyone" in lower_transcript:
        return f"Let me be brutally honest... Using absolute terms like 'always', 'never', or 'everyone' in '{transcript}' is intellectually lazy. Real life has nuance, exceptions, and complexity. Your oversimplification weakens your argument."
    
    elif "best" in lower_transcript or "worst" in lower_transcript:
        return f"Let me be brutally honest... Claiming something is 'the best' or 'the worst' without evidence is just opinion masquerading as fact. What metrics are you using? Where's your data?"
    
    elif len(transcript.split()) < 5:
        return f"Let me be brutally honest... '{transcript}' is too vague to analyze properly. You're not giving me enough context to provide meaningful feedback. Try being more specific."
    
    else:
        return f"Let me be brutally honest... '{transcript}' sounds like an assertion without supporting evidence. In a world full of misinformation, you need to back up your claims with facts, not just confidence."

if __name__ == "__main__":
    logger.info("Starting Simple Voice Recorder")
    uvicorn.run(
        "main_simple_record:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )
