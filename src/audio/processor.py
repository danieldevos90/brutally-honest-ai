"""
Audio Processing Pipeline
Handles transcription, speaker diarization, and audio analysis
"""

import asyncio
import logging
import tempfile
import os
import time
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
        self.min_chunk_duration = 1.0  # Minimum 1 second for processing
        self.max_chunk_duration = 300.0  # Maximum 5 minutes before forced processing
        
        # User-controlled recording mode
        self.user_controlled_mode = True  # Process on start/stop commands
        
        # Real-time processing state
        self.audio_buffer = bytearray()
        self.processing_buffer = []
        self.last_processed_time = 0.0
        
        # Sentence accumulation for better transcription
        self.sentence_buffer = ""
        self.last_complete_sentence = ""
    
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
        """Process real-time audio chunk - in user-controlled mode, just buffer until stop"""
        if not self.is_ready():
            return None
        
        try:
            # Add chunk to buffer
            self.audio_buffer.extend(audio_chunk.data)
            
            # Check if we have enough data to process
            buffer_duration = len(self.audio_buffer) / (audio_chunk.sample_rate * 2)  # 16-bit = 2 bytes
            
            # In user-controlled mode, only process if we exceed max duration (safety)
            if self.user_controlled_mode:
                if buffer_duration >= self.max_chunk_duration:
                    # Force processing to prevent memory issues
                    return await self._process_buffer(audio_chunk)
                else:
                    # Just buffer, don't process until user stops
                    return None
            
            # Legacy mode: Process if we have minimum duration OR if we've exceeded max duration
            should_process = (buffer_duration >= self.min_chunk_duration or 
                            buffer_duration >= self.max_chunk_duration)
            
            if not should_process:
                return None
            
            return await self._process_buffer(audio_chunk)
            
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
            return None
    
    async def _process_buffer(self, audio_chunk: AudioChunk) -> Optional[AudioProcessingResult]:
        """Process the current audio buffer"""
        try:
            # Convert buffer to numpy array
            audio_data = np.frombuffer(self.audio_buffer, dtype=np.int16).astype(np.float32) / 32768.0
            buffer_duration = len(self.audio_buffer) / (audio_chunk.sample_rate * 2)  # 16-bit = 2 bytes
            
            # Save to temporary file for Whisper
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, audio_chunk.sample_rate)
                temp_path = temp_file.name
            
            try:
                # Transcribe chunk with improved settings
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")  # Suppress FP16 warnings
                    result = self.whisper_model.transcribe(
                        temp_path,
                        language="en",  # Force English
                        task="transcribe",
                        temperature=0.0,  # More deterministic
                        no_speech_threshold=0.6,  # Higher threshold for silence
                        logprob_threshold=-1.0,
                        compression_ratio_threshold=2.4,
                        condition_on_previous_text=True,  # Use context from previous text
                        initial_prompt=self.sentence_buffer  # Provide context
                    )
                
                transcript = result["text"].strip()
                
                if transcript:
                    # In user-controlled mode, always consider the complete buffer as final
                    if self.user_controlled_mode:
                        # Process the entire buffer as one complete segment
                        final_transcript = transcript
                        is_complete = True  # User stopped, so it's complete
                        # Clear all buffers since user stopped recording
                        self.sentence_buffer = ""
                        self.audio_buffer = bytearray()
                    else:
                        # Legacy mode: accumulate sentences
                        self.sentence_buffer = self._accumulate_sentence(transcript)
                        is_complete = self._is_complete_sentence(self.sentence_buffer)
                        
                        if is_complete:
                            final_transcript = self.sentence_buffer
                            self.sentence_buffer = ""
                            self.audio_buffer = bytearray()
                        else:
                            final_transcript = transcript
                            overlap_samples = int(audio_chunk.sample_rate * 2.0 * 2)  # 2 second overlap
                            self.audio_buffer = self.audio_buffer[-overlap_samples:]
                    
                    # Simple speaker detection (single speaker for real-time)
                    current_speaker = "SPEAKER_00"
                    
                    return AudioProcessingResult(
                        transcript=final_transcript,
                        speakers=[SpeakerSegment(
                            speaker_id=current_speaker,
                            start_time=audio_chunk.timestamp,
                            end_time=audio_chunk.timestamp + buffer_duration,
                            text=final_transcript,
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
            logger.error(f"Error processing buffer: {e}")
            return None
    
    async def process_on_stop(self) -> Optional[AudioProcessingResult]:
        """Process the current buffer when user stops recording"""
        if not self.is_ready() or len(self.audio_buffer) == 0:
            return None
        
        try:
            # Create a dummy audio chunk for processing
            dummy_chunk = AudioChunk(
                data=b'',  # Empty, we'll use the buffer
                timestamp=time.time(),
                sample_rate=self.target_sample_rate,
                channels=1
            )
            
            # Process whatever we have in the buffer
            result = await self._process_buffer(dummy_chunk)
            return result
            
        except Exception as e:
            logger.error(f"Error processing on stop: {e}")
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
    
    def _accumulate_sentence(self, new_transcript: str) -> str:
        """Accumulate transcript fragments into coherent sentences"""
        if not new_transcript:
            return self.sentence_buffer
        
        # Clean up the new transcript
        new_transcript = new_transcript.strip()
        
        # If sentence buffer is empty, start with new transcript
        if not self.sentence_buffer:
            return new_transcript
        
        # Check if new transcript is a continuation or a new sentence
        # Simple heuristic: if it starts with lowercase, it's likely a continuation
        if new_transcript and new_transcript[0].islower():
            # Continuation - add with space
            return f"{self.sentence_buffer} {new_transcript}"
        else:
            # New sentence - check if previous was complete
            if self._is_complete_sentence(self.sentence_buffer):
                # Previous was complete, start new sentence
                return new_transcript
            else:
                # Previous wasn't complete, continue building
                return f"{self.sentence_buffer} {new_transcript}"
    
    def _is_complete_sentence(self, text: str) -> bool:
        """Check if text represents a complete conversation segment for 2+ minute chunks"""
        if not text:
            return False
        
        # Clean up text
        text = text.strip()
        
        # Must have minimum length for meaningful analysis
        if len(text) < 10:
            return False
        
        # Check for definitive sentence-ending punctuation
        if text.endswith(('.', '!', '?')):
            return True
        
        # For longer chunks, look for conversation completeness indicators
        words = text.split()
        
        # Must have substantial content (at least 15 words for 2-minute chunks)
        if len(words) < 15:
            return False
        
        # Check for conversation completion patterns
        complete_patterns = [
            # Multiple sentences (look for internal punctuation)
            lambda t: any(punct in t for punct in ['. ', '! ', '? ']),
            # Natural conversation endings
            lambda t: any(ending in t.lower() for ending in [
                'thank you', 'that\'s all', 'that\'s it', 'in conclusion', 
                'to summarize', 'that\'s my point', 'that\'s what I think'
            ]),
            # Question-answer patterns
            lambda t: '?' in t and len(t.split('?')) > 1,
        ]
        
        # Check if any pattern matches
        for pattern in complete_patterns:
            if pattern(text):
                return True
        
        # For very long content (50+ words), consider it a complete segment
        if len(words) >= 50:
            return True
        
        return False
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up audio processor...")
        
        # Clear buffers
        self.audio_buffer = bytearray()
        self.processing_buffer = []
        self.sentence_buffer = ""
        self.last_complete_sentence = ""
        
        # Models will be garbage collected
        self.whisper_model = None
        self.diarization_pipeline = None
        self.is_initialized = False
