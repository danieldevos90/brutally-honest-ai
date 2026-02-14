"""
Audio Service - Business logic for audio processing
Separates audio operations from HTTP route handlers
"""

import logging
import io
import wave
import math
import array
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AudioAnalysis:
    """Audio analysis result."""
    channels: int
    sample_rate: int
    bits: int
    frames: int
    duration_seconds: float
    rms: int
    peak: int


class AudioService:
    """Service layer for audio processing operations."""
    
    SUPPORTED_FORMATS = {'.wav', '.mp3', '.m4a', '.ogg', '.flac', '.webm', '.mp4'}
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_ASYNC_FILE_SIZE = 500 * 1024 * 1024  # 500MB
    
    def validate_audio_file(self, filename: str, file_size: int, async_mode: bool = False) -> Optional[str]:
        """
        Validate audio file.
        Returns error message if invalid, None if valid.
        """
        if not filename:
            return "No filename provided"
        
        # Check extension
        ext = '.' + filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        if ext not in self.SUPPORTED_FORMATS:
            return f"Unsupported format: {ext}. Supported: {', '.join(self.SUPPORTED_FORMATS)}"
        
        # Check size
        if file_size == 0:
            return "Empty file"
        
        max_size = self.MAX_ASYNC_FILE_SIZE if async_mode else self.MAX_FILE_SIZE
        if file_size > max_size:
            return f"File too large (max {max_size // (1024*1024)}MB)"
        
        return None
    
    def analyze_wav(self, audio_data: bytes, max_duration_seconds: int = 10) -> Optional[AudioAnalysis]:
        """Analyze WAV audio file."""
        try:
            bio = io.BytesIO(audio_data)
            with wave.open(bio, 'rb') as w:
                channels = w.getnchannels()
                rate = w.getframerate()
                width = w.getsampwidth()
                frames = w.getnframes()
                
                # Read up to max_duration_seconds
                n = min(frames, rate * max_duration_seconds)
                data = w.readframes(n)
            
            if width != 2:
                logger.warning(f"Unsupported sample width: {width}")
                return None
            
            samples = array.array('h', data)
            
            if len(samples) == 0:
                return AudioAnalysis(
                    channels=channels,
                    sample_rate=rate,
                    bits=width * 8,
                    frames=frames,
                    duration_seconds=round(frames / rate, 2),
                    rms=0,
                    peak=0
                )
            
            # Calculate RMS and peak
            rms = int(math.sqrt(sum(s * s for s in samples) / len(samples)))
            peak = max(abs(s) for s in samples)
            
            return AudioAnalysis(
                channels=channels,
                sample_rate=rate,
                bits=width * 8,
                frames=frames,
                duration_seconds=round(frames / rate, 2),
                rms=rms,
                peak=peak
            )
            
        except Exception as e:
            logger.error(f"Error analyzing WAV: {e}")
            return None
    
    @staticmethod
    def get_audio_level(samples: list, threshold: int = 500) -> str:
        """Get human-readable audio level description."""
        if not samples:
            return "silent"
        
        avg_level = sum(abs(s) for s in samples) / len(samples)
        
        if avg_level < threshold:
            return "very quiet"
        elif avg_level < threshold * 5:
            return "quiet"
        elif avg_level < threshold * 20:
            return "normal"
        elif avg_level < threshold * 50:
            return "loud"
        else:
            return "very loud"


# Singleton instance
_audio_service: Optional[AudioService] = None


def get_audio_service() -> AudioService:
    """Get the audio service singleton."""
    global _audio_service
    if _audio_service is None:
        _audio_service = AudioService()
    return _audio_service
