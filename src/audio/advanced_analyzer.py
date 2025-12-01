"""
Advanced Audio Analyzer - Uses pyannote, speechbrain for full interview analysis

Features:
- Speaker diarization (who is speaking when)
- Emotion/mood detection per segment
- Speaker verification (match to known profiles)
- Combined with Whisper transcription
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)

# Track available features
PYANNOTE_AVAILABLE = False
SPEECHBRAIN_AVAILABLE = False

try:
    from pyannote.audio import Pipeline as DiarizationPipeline
    PYANNOTE_AVAILABLE = True
    logger.info("pyannote.audio available for speaker diarization")
except ImportError as e:
    logger.warning(f"pyannote.audio not available: {e}")

try:
    from speechbrain.inference.interfaces import foreign_class
    from speechbrain.inference.classifiers import EncoderClassifier
    SPEECHBRAIN_AVAILABLE = True
    logger.info("speechbrain available for emotion recognition")
except ImportError as e:
    logger.warning(f"speechbrain not available: {e}")


@dataclass
class SpeakerSegment:
    """A segment of speech from one speaker"""
    speaker_id: str
    start_time: float
    end_time: float
    duration: float
    text: str = ""
    emotion: str = "neutral"
    emotion_confidence: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EmotionResult:
    """Emotion detection result"""
    emotion: str  # happy, sad, angry, neutral, fear, disgust, surprise
    confidence: float
    all_scores: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AdvancedAnalysisResult:
    """Complete analysis result combining all features"""
    # Basic info
    audio_duration: float = 0.0
    num_speakers: int = 0
    
    # Speaker diarization
    speakers: List[str] = field(default_factory=list)
    segments: List[SpeakerSegment] = field(default_factory=list)
    speaker_stats: Dict[str, Dict] = field(default_factory=dict)
    
    # Emotion analysis
    overall_emotion: str = "neutral"
    emotion_timeline: List[Dict] = field(default_factory=list)
    
    # Per-speaker emotions
    speaker_emotions: Dict[str, Dict] = field(default_factory=dict)
    
    # Analysis metadata
    analysis_time: float = 0.0
    models_used: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['segments'] = [s.to_dict() if hasattr(s, 'to_dict') else s for s in self.segments]
        return result


class SpeakerDiarizer:
    """
    Speaker diarization using pyannote.audio
    Identifies who is speaking when in an audio file
    """
    
    def __init__(self):
        self.pipeline = None
        self.initialized = False
    
    async def initialize(self, hf_token: str = None):
        """Initialize the diarization pipeline"""
        if not PYANNOTE_AVAILABLE:
            logger.warning("pyannote not available - diarization disabled")
            return False
        
        try:
            # Get token from environment if not provided
            if not hf_token:
                hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
            
            logger.info("Initializing speaker diarization pipeline...")
            
            if hf_token:
                try:
                    # Try the latest model first
                    self.pipeline = DiarizationPipeline.from_pretrained(
                        "pyannote/speaker-diarization-3.1",
                        use_auth_token=hf_token
                    )
                    logger.info("Loaded pyannote/speaker-diarization-3.1")
                except Exception as e:
                    logger.warning(f"Could not load 3.1, trying 3.0: {e}")
                    try:
                        self.pipeline = DiarizationPipeline.from_pretrained(
                            "pyannote/speaker-diarization@2.1",
                            use_auth_token=hf_token
                        )
                        logger.info("Loaded pyannote/speaker-diarization@2.1")
                    except Exception as e2:
                        logger.warning(f"Could not load diarization model: {e2}")
                        self.pipeline = None
            else:
                logger.warning("No HuggingFace token - using fallback diarization")
                self.pipeline = None
            
            self.initialized = True
            logger.info("Speaker diarization initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize diarization: {e}")
            return False
    
    async def diarize(self, audio_path: str) -> List[SpeakerSegment]:
        """
        Perform speaker diarization on audio file
        
        Returns list of segments with speaker labels and timestamps
        """
        if not self.pipeline:
            logger.warning("Diarization pipeline not initialized - using fallback")
            return await self._fallback_diarization(audio_path)
        
        try:
            # Run diarization
            diarization = self.pipeline(audio_path)
            
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append(SpeakerSegment(
                    speaker_id=speaker,
                    start_time=turn.start,
                    end_time=turn.end,
                    duration=turn.end - turn.start
                ))
            
            return segments
            
        except Exception as e:
            logger.error(f"Diarization failed: {e}")
            return await self._fallback_diarization(audio_path)
    
    async def _fallback_diarization(self, audio_path: str) -> List[SpeakerSegment]:
        """Fallback diarization using simple-diarizer or energy-based approach"""
        
        # Try simple-diarizer first
        try:
            from simple_diarizer.diarizer import Diarizer
            from simple_diarizer.utils import combined_waveplot
            
            logger.info("Using simple-diarizer for speaker separation...")
            diar = Diarizer(
                embed_model='xvec',  # or 'ecapa' for better quality
                cluster_method='sc'   # spectral clustering
            )
            
            # Diarize with reasonable defaults
            # For interviews: typically 2-4 speakers max
            try:
                # First try with auto detection using high threshold
                segments_dict = diar.diarize(
                    audio_path, 
                    num_speakers=None,
                    threshold=0.95  # Very high = very few speakers
                )
                # If too many speakers detected, re-run with fixed number
                unique_speakers = len(set(s['label'] for s in segments_dict))
                if unique_speakers > 4:
                    logger.info(f"Re-running diarization (detected {unique_speakers} speakers, limiting to 2)")
                    segments_dict = diar.diarize(audio_path, num_speakers=2)
            except Exception as e:
                # If threshold doesn't work, use fixed number
                logger.warning(f"Auto-detection failed ({e}), using 2 speakers")
                segments_dict = diar.diarize(audio_path, num_speakers=2)
            
            segments = []
            for seg in segments_dict:
                segments.append(SpeakerSegment(
                    speaker_id=f"SPEAKER_{seg['label']:02d}",
                    start_time=seg['start'],
                    end_time=seg['end'],
                    duration=seg['end'] - seg['start']
                ))
            
            if segments:
                logger.info(f"simple-diarizer found {len(set(s.speaker_id for s in segments))} speakers")
                return segments
                
        except ImportError:
            logger.warning("simple-diarizer not available")
        except Exception as e:
            logger.warning(f"simple-diarizer failed: {e}")
        
        # Ultimate fallback: energy-based segmentation
        try:
            import librosa
            import numpy as np
            
            y, sr = librosa.load(audio_path, sr=16000)
            duration = len(y) / sr
            
            # Use voice activity detection to find speech segments
            intervals = librosa.effects.split(y, top_db=25)
            
            if len(intervals) > 1:
                segments = []
                for i, (start, end) in enumerate(intervals):
                    start_time = start / sr
                    end_time = end / sr
                    if end_time - start_time >= 0.5:  # Min 0.5s segments
                        segments.append(SpeakerSegment(
                            speaker_id="SPEAKER_00",  # Can't distinguish speakers
                            start_time=start_time,
                            end_time=end_time,
                            duration=end_time - start_time
                        ))
                return segments if segments else [SpeakerSegment(
                    speaker_id="SPEAKER_00",
                    start_time=0.0,
                    end_time=duration,
                    duration=duration
                )]
            
            return [SpeakerSegment(
                speaker_id="SPEAKER_00",
                start_time=0.0,
                end_time=duration,
                duration=duration
            )]
            
        except Exception as e:
            logger.error(f"Fallback diarization failed: {e}")
            return []


class EmotionRecognizer:
    """
    Speech emotion recognition using SpeechBrain
    Detects emotions from audio segments
    """
    
    # Emotion labels
    EMOTIONS = ["angry", "disgust", "fear", "happy", "neutral", "sad", "surprise"]
    
    def __init__(self):
        self.classifier = None
        self.initialized = False
    
    async def initialize(self):
        """Initialize emotion recognition model"""
        if not SPEECHBRAIN_AVAILABLE:
            logger.warning("speechbrain not available - emotion recognition disabled")
            return False
        
        try:
            logger.info("Initializing emotion recognition model...")
            
            # Load pretrained emotion recognition model
            self.classifier = EncoderClassifier.from_hparams(
                source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
                savedir="pretrained_models/emotion-recognition"
            )
            
            self.initialized = True
            logger.info("Emotion recognition initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize emotion recognition: {e}")
            # Try alternative model
            try:
                self.classifier = foreign_class(
                    source="speechbrain/emotion-recognition-wav2vec2-IEMOCAP",
                    pymodule_file="custom_interface.py",
                    classname="CustomEncoderWav2vec2Classifier"
                )
                self.initialized = True
                return True
            except:
                return False
    
    async def recognize_emotion(self, audio_path: str) -> EmotionResult:
        """
        Recognize emotion from audio file or segment
        """
        if not self.classifier:
            return await self._fallback_emotion(audio_path)
        
        try:
            # Run emotion classification
            out_prob, score, index, text_lab = self.classifier.classify_file(audio_path)
            
            # Get all scores
            all_scores = {}
            for i, emotion in enumerate(self.EMOTIONS):
                if i < len(out_prob[0]):
                    all_scores[emotion] = float(out_prob[0][i])
            
            return EmotionResult(
                emotion=text_lab[0] if text_lab else "neutral",
                confidence=float(score[0]) if score else 0.0,
                all_scores=all_scores
            )
            
        except Exception as e:
            logger.warning(f"Emotion recognition failed: {e}")
            return await self._fallback_emotion(audio_path)
    
    async def _fallback_emotion(self, audio_path: str) -> EmotionResult:
        """Fallback emotion detection based on voice features"""
        try:
            import librosa
            import numpy as np
            
            y, sr = librosa.load(audio_path, sr=16000)
            
            # Extract basic features for emotion estimation
            # High energy + high pitch = possibly excited/angry
            # Low energy + slow = possibly sad
            
            rms = librosa.feature.rms(y=y)[0]
            energy = np.mean(rms)
            
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            avg_pitch = np.mean(pitch_values) if pitch_values else 150
            pitch_var = np.std(pitch_values) if pitch_values else 0
            
            # Simple heuristic emotion detection
            if energy > 0.1 and avg_pitch > 200:
                return EmotionResult(emotion="happy", confidence=0.6)
            elif energy > 0.1 and pitch_var > 50:
                return EmotionResult(emotion="angry", confidence=0.5)
            elif energy < 0.05:
                return EmotionResult(emotion="sad", confidence=0.5)
            else:
                return EmotionResult(emotion="neutral", confidence=0.7)
                
        except Exception as e:
            logger.error(f"Fallback emotion failed: {e}")
            return EmotionResult(emotion="neutral", confidence=0.5)


class AdvancedAudioAnalyzer:
    """
    Complete audio analysis pipeline combining:
    - Speaker diarization
    - Emotion recognition
    - Voice features
    - Transcription alignment
    """
    
    def __init__(self):
        self.diarizer = SpeakerDiarizer()
        self.emotion_recognizer = EmotionRecognizer()
        self.initialized = False
    
    async def initialize(self, hf_token: str = None):
        """Initialize all analysis components"""
        await self.diarizer.initialize(hf_token)
        await self.emotion_recognizer.initialize()
        self.initialized = True
        logger.info("Advanced audio analyzer initialized")
    
    async def analyze(
        self,
        audio_path: str,
        transcription: str = None
    ) -> AdvancedAnalysisResult:
        """
        Perform complete audio analysis
        
        Args:
            audio_path: Path to audio file
            transcription: Optional transcription text
            
        Returns:
            AdvancedAnalysisResult with all analysis data
        """
        import time
        start_time = time.time()
        
        result = AdvancedAnalysisResult()
        
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=16000)
            result.audio_duration = len(y) / sr
        except Exception as e:
            logger.error(f"Failed to load audio: {e}")
            return result
        
        # 1. Speaker diarization
        logger.info("Running speaker diarization...")
        segments = await self.diarizer.diarize(audio_path)
        result.segments = segments
        result.speakers = list(set(s.speaker_id for s in segments))
        result.num_speakers = len(result.speakers)
        result.models_used.append("Speaker Diarization")
        
        # Calculate speaker stats
        for speaker in result.speakers:
            speaker_segments = [s for s in segments if s.speaker_id == speaker]
            total_time = sum(s.duration for s in speaker_segments)
            result.speaker_stats[speaker] = {
                "total_time": round(total_time, 2),
                "percentage": round((total_time / result.audio_duration) * 100, 1) if result.audio_duration > 0 else 0,
                "num_turns": len(speaker_segments)
            }
        
        # 2. Emotion analysis
        logger.info("Running emotion recognition...")
        overall_emotion = await self.emotion_recognizer.recognize_emotion(audio_path)
        result.overall_emotion = overall_emotion.emotion
        result.models_used.append("Emotion Recognition")
        
        # Analyze emotion for each speaker segment (if segments are long enough)
        for i, segment in enumerate(segments):
            if segment.duration >= 1.0:  # Only analyze segments >= 1 second
                try:
                    # Extract segment audio
                    segment_audio = y[int(segment.start_time * sr):int(segment.end_time * sr)]
                    
                    # Save to temp file for analysis
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                        import soundfile as sf
                        sf.write(tmp.name, segment_audio, sr)
                        segment_emotion = await self.emotion_recognizer.recognize_emotion(tmp.name)
                        os.unlink(tmp.name)
                    
                    segment.emotion = segment_emotion.emotion
                    segment.emotion_confidence = segment_emotion.confidence
                    
                    result.emotion_timeline.append({
                        "start": segment.start_time,
                        "end": segment.end_time,
                        "speaker": segment.speaker_id,
                        "emotion": segment_emotion.emotion,
                        "confidence": segment_emotion.confidence
                    })
                    
                except Exception as e:
                    logger.warning(f"Segment emotion analysis failed: {e}")
        
        # 3. Aggregate emotions per speaker
        for speaker in result.speakers:
            speaker_emotions = [s.emotion for s in segments if s.speaker_id == speaker and s.emotion]
            if speaker_emotions:
                from collections import Counter
                emotion_counts = Counter(speaker_emotions)
                dominant_emotion = emotion_counts.most_common(1)[0][0]
                result.speaker_emotions[speaker] = {
                    "dominant": dominant_emotion,
                    "distribution": dict(emotion_counts)
                }
        
        # 4. Align transcription with segments if provided
        if transcription and segments:
            await self._align_transcription(transcription, segments)
        
        result.analysis_time = time.time() - start_time
        logger.info(f"Advanced analysis complete in {result.analysis_time:.2f}s")
        
        return result
    
    async def _align_transcription(
        self,
        transcription: str,
        segments: List[SpeakerSegment]
    ):
        """
        Align transcription text with speaker segments
        Simple approach: distribute words by time proportion
        """
        words = transcription.split()
        if not words or not segments:
            return
        
        total_duration = sum(s.duration for s in segments)
        if total_duration <= 0:
            return
        
        word_idx = 0
        for segment in segments:
            # Estimate words for this segment based on duration proportion
            segment_words = int(len(words) * (segment.duration / total_duration))
            segment_words = max(1, segment_words)  # At least 1 word
            
            segment_text = ' '.join(words[word_idx:word_idx + segment_words])
            segment.text = segment_text
            word_idx += segment_words
        
        # Assign remaining words to last segment
        if word_idx < len(words) and segments:
            segments[-1].text += ' ' + ' '.join(words[word_idx:])


# Global instance
_advanced_analyzer: Optional[AdvancedAudioAnalyzer] = None


async def get_advanced_analyzer() -> AdvancedAudioAnalyzer:
    """Get or create the global advanced analyzer"""
    global _advanced_analyzer
    if _advanced_analyzer is None:
        _advanced_analyzer = AdvancedAudioAnalyzer()
        await _advanced_analyzer.initialize()
    return _advanced_analyzer

