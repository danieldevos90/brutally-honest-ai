"""
Audio Processing Pipeline
Handles transcription, speaker diarization, and audio analysis
"""

import asyncio
import logging
import tempfile
import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
import torch
import whisper
from pyannote.audio import Pipeline
from pyannote.core import Segment
import librosa
import soundfile as sf
from .omi_connector import AudioChunk

logger = logging.getLogger(__name__)

@dataclass
class SpeakerSegment:
    """Speaker segment information"""
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    confidence: float = 0.0

@dataclass
class AudioProcessingResult:
    """Result of audio processing"""
    transcript: str
    speakers: List[SpeakerSegment]
    audio_duration: float
    timestamp: datetime
    current_speaker: Optional[str] = None
    is_complete_sentence: bool = False
    confidence: float = 0.0

class AudioProcessor:
    """Audio processing pipeline using Whisper and pyannote"""
    
    def __init__(self):
        self.whisper_model = None
        self.diarization_pipeline = None
        self.is_initialized = False
        
        # Processing configuration
        self.whisper_model_name = "base"  # Can be: tiny, base, small, medium, large
        self.target_sample_rate = 16000
        self.min_chunk_duration = 1.0  # Minimum seconds for processing
        
        # Real-time processing state
        self.audio_buffer = bytearray()
        self.processing_buffer = []
        self.last_processed_time = 0.0
    
    async def initialize(self) -> bool:
        """Initialize audio processing models"""
        try:
            logger.info("Initializing audio processing models...")
            
            # Load Whisper model
            logger.info(f"Loading Whisper model: {self.whisper_model_name}")
            self.whisper_model = whisper.load_model(self.whisper_model_name)
            
            # Load speaker diarization pipeline
            logger.info("Loading speaker diarization pipeline...")
            try:
                # Note: This requires a Hugging Face token for pyannote models
                # You can get one at: https://huggingface.co/settings/tokens
                hf_token = os.getenv("HUGGINGFACE_TOKEN")
                if hf_token:
                    self.diarization_pipeline = Pipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token
                    )
                else:
                    logger.warning("No HUGGINGFACE_TOKEN found. Speaker diarization will be disabled.")
                    self.diarization_pipeline = None
                    
            except Exception as e:
                logger.warning(f"Failed to load diarization pipeline: {e}")
                logger.warning("Continuing without speaker diarization...")
                self.diarization_pipeline = None
            
            self.is_initialized = True
            logger.info("Audio processing models initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize audio processor: {e}")
            return False
    
    def is_ready(self) -> bool:
        """Check if processor is ready"""
        return self.is_initialized and self.whisper_model is not None
    
    async def process_file(self, file_path: str) -> AudioProcessingResult:
        """Process complete audio file"""
        if not self.is_ready():
            raise RuntimeError("Audio processor not initialized")
        
        try:
            logger.info(f"Processing audio file: {file_path}")
            
            # Load and preprocess audio
            audio_data, sample_rate = librosa.load(file_path, sr=self.target_sample_rate)
            duration = len(audio_data) / sample_rate
            
            # Transcribe with Whisper
            logger.info("Transcribing audio...")
            result = self.whisper_model.transcribe(file_path)
            transcript = result["text"].strip()
            
            # Speaker diarization
            speakers = []
            if self.diarization_pipeline:
                logger.info("Performing speaker diarization...")
                speakers = await self._perform_diarization(file_path, transcript)
            else:
                # Single speaker fallback
                speakers = [SpeakerSegment(
                    speaker_id="SPEAKER_00",
                    start_time=0.0,
                    end_time=duration,
                    text=transcript,
                    confidence=0.8
                )]
            
            return AudioProcessingResult(
                transcript=transcript,
                speakers=speakers,
                audio_duration=duration,
                timestamp=datetime.now(),
                confidence=result.get("confidence", 0.8)
            )
            
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            raise
    
    async def process_chunk(self, audio_chunk: AudioChunk) -> Optional[AudioProcessingResult]:
        """Process real-time audio chunk"""
        if not self.is_ready():
            return None
        
        try:
            # Add chunk to buffer
            self.audio_buffer.extend(audio_chunk.data)
            
            # Check if we have enough data to process
            buffer_duration = len(self.audio_buffer) / (audio_chunk.sample_rate * 2)  # 16-bit = 2 bytes
            
            if buffer_duration < self.min_chunk_duration:
                return None
            
            # Convert buffer to numpy array
            audio_data = np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Save to temporary file for Whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, audio_chunk.sample_rate)
                temp_path = temp_file.name
            
            try:
                # Transcribe chunk
                result = self.whisper_model.transcribe(temp_path)
                transcript = result["text"].strip()
                
                if transcript:
                    # Determine if this is a complete sentence
                    is_complete = self._is_complete_sentence(transcript)
                    
                    # Simple speaker detection (single speaker for real-time)
                    current_speaker = "SPEAKER_00"
                    
                    # Clear buffer if we processed a complete sentence
                    if is_complete:
                        self.audio_buffer = bytearray()
                    else:
                        # Keep some overlap for context
                        overlap_samples = int(audio_chunk.sample_rate * 0.5 * 2)  # 0.5 second overlap
                        self.audio_buffer = self.audio_buffer[-overlap_samples:]
                    
                    return AudioProcessingResult(
                        transcript=transcript,
                        speakers=[SpeakerSegment(
                            speaker_id=current_speaker,
                            start_time=audio_chunk.timestamp,
                            end_time=audio_chunk.timestamp + buffer_duration,
                            text=transcript,
                            confidence=0.8
                        )],
                        audio_duration=buffer_duration,
                        timestamp=datetime.now(),
                        current_speaker=current_speaker,
                        is_complete_sentence=is_complete,
                        confidence=result.get("confidence", 0.8)
                    )
                
            finally:
                # Cleanup temp file
                os.unlink(temp_path)
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None
    
    async def _perform_diarization(self, file_path: str, transcript: str) -> List[SpeakerSegment]:
        """Perform speaker diarization on audio file"""
        try:
            # Run diarization
            diarization = self.diarization_pipeline(file_path)
            
            # Convert to speaker segments
            speakers = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                # For now, assign entire transcript to each speaker segment
                # In a more sophisticated implementation, you'd align transcript with segments
                segment_text = transcript  # Simplified
                
                speakers.append(SpeakerSegment(
                    speaker_id=speaker,
                    start_time=turn.start,
                    end_time=turn.end,
                    text=segment_text,
                    confidence=0.8
                ))
            
            return speakers
            
        except Exception as e:
            logger.error(f"Diarization error: {e}")
            # Fallback to single speaker
            return [SpeakerSegment(
                speaker_id="SPEAKER_00",
                start_time=0.0,
                end_time=10.0,  # Estimate
                text=transcript,
                confidence=0.5
            )]
    
    def _is_complete_sentence(self, text: str) -> bool:
        """Check if text represents a complete sentence"""
        if not text:
            return False
        
        # Simple heuristics for sentence completion
        text = text.strip()
        
        # Check for sentence-ending punctuation
        if text.endswith(('.', '!', '?')):
            return True
        
        # Check for common sentence patterns
        if len(text.split()) >= 3:  # At least 3 words
            return True
        
        return False
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up audio processor...")
        
        # Clear buffers
        self.audio_buffer = bytearray()
        self.processing_buffer = []
        
        # Models will be garbage collected
        self.whisper_model = None
        self.diarization_pipeline = None
        self.is_initialized = False
