"""
Voice Feature Analyzer
Extracts pitch, pace, pauses, and other voice characteristics from audio
"""

import asyncio
import logging
import tempfile
import os
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

# Optional imports with fallbacks
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("librosa not available - voice analysis limited")

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    logger.warning("webrtcvad not available - pause detection limited")


@dataclass
class VoiceFeatures:
    """Extracted voice characteristics from audio"""
    
    # Identification
    speaker_id: str = "unknown"
    segment_start: float = 0.0
    segment_end: float = 0.0
    
    # Pitch (fundamental frequency)
    pitch_mean_hz: float = 0.0          # Average pitch in Hz
    pitch_std_hz: float = 0.0           # Pitch variation
    pitch_min_hz: float = 0.0           # Minimum pitch
    pitch_max_hz: float = 0.0           # Maximum pitch
    pitch_range_hz: float = 0.0         # Range of pitch
    
    # Speaking rate
    speaking_rate_wpm: float = 0.0      # Words per minute (from transcript)
    syllables_per_second: float = 0.0   # Estimated syllable rate
    articulation_rate: float = 0.0      # Speech excluding pauses
    
    # Pauses
    pause_count: int = 0                # Number of pauses detected
    pause_total_duration: float = 0.0   # Total pause time
    pause_avg_duration: float = 0.0     # Average pause length
    pause_ratio: float = 0.0            # Pause time / total time
    
    # Energy/Volume
    energy_mean: float = 0.0            # Average energy (dB)
    energy_std: float = 0.0             # Energy variation
    energy_max: float = 0.0             # Peak energy
    dynamic_range: float = 0.0          # Max - min energy
    
    # Rhythm indicators
    speech_rhythm: str = "unknown"      # "steady", "varied", "hesitant"
    tempo_variability: float = 0.0      # How much pace changes
    
    # Derived confidence indicators
    confidence_score: float = 0.5       # 0-1, based on voice patterns
    stress_indicator: float = 0.5       # 0-1, based on pitch/pace
    engagement_indicator: float = 0.5   # 0-1, based on energy/rhythm
    
    # Metadata
    duration_seconds: float = 0.0
    sample_rate: int = 16000
    analysis_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VoiceFeatures':
        return cls(**data)


@dataclass
class PauseSegment:
    """A detected pause in speech"""
    start: float
    end: float
    duration: float


class VoiceAnalyzer:
    """Analyzes voice characteristics from audio files"""
    
    def __init__(self):
        self.sample_rate = 16000
        self.frame_length = 2048
        self.hop_length = 512
        
        # VAD settings
        self.vad_aggressiveness = 2  # 0-3, higher = more aggressive
        self.min_pause_duration = 0.3  # Minimum pause length in seconds
        
        logger.info(f"Voice analyzer initialized (librosa={LIBROSA_AVAILABLE}, vad={VAD_AVAILABLE})")
    
    async def analyze_audio(
        self,
        audio_path: str,
        transcript: Optional[str] = None,
        word_count: Optional[int] = None,
        speaker_id: str = "unknown"
    ) -> VoiceFeatures:
        """
        Analyze voice features from an audio file
        
        Args:
            audio_path: Path to audio file
            transcript: Optional transcript for word count
            word_count: Optional pre-counted words
            speaker_id: Speaker identifier
            
        Returns:
            VoiceFeatures with extracted characteristics
        """
        features = VoiceFeatures(speaker_id=speaker_id)
        
        if not LIBROSA_AVAILABLE:
            logger.warning("Librosa not available, returning basic features")
            return features
        
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=self.sample_rate)
            duration = len(y) / sr
            
            features.duration_seconds = duration
            features.sample_rate = sr
            features.segment_start = 0.0
            features.segment_end = duration
            
            # Extract all features
            await self._extract_pitch_features(y, sr, features)
            await self._extract_energy_features(y, sr, features)
            await self._extract_pause_features(y, sr, features)
            
            # Calculate speaking rate if transcript available
            if transcript:
                word_count = len(transcript.split())
            if word_count and duration > 0:
                speech_duration = duration - features.pause_total_duration
                if speech_duration > 0:
                    features.speaking_rate_wpm = (word_count / speech_duration) * 60
                    features.articulation_rate = word_count / speech_duration
                else:
                    features.speaking_rate_wpm = (word_count / duration) * 60
            
            # Estimate syllables (rough: ~1.5 syllables per word in English)
            if word_count:
                syllables = word_count * 1.5
                speech_duration = duration - features.pause_total_duration
                if speech_duration > 0:
                    features.syllables_per_second = syllables / speech_duration
            
            # Calculate derived indicators
            self._calculate_derived_indicators(features)
            
            logger.info(f"Voice analysis complete: pitch={features.pitch_mean_hz:.1f}Hz, "
                       f"rate={features.speaking_rate_wpm:.0f}wpm, "
                       f"pauses={features.pause_count}")
            
            return features
            
        except Exception as e:
            logger.error(f"Voice analysis failed: {e}")
            return features
    
    async def _extract_pitch_features(
        self, 
        y: np.ndarray, 
        sr: int, 
        features: VoiceFeatures
    ):
        """Extract pitch (fundamental frequency) features"""
        try:
            # Extract pitch using librosa's piptrack
            pitches, magnitudes = librosa.piptrack(
                y=y, 
                sr=sr,
                fmin=50,   # Min human voice ~75Hz
                fmax=500   # Max typical speaking ~300Hz
            )
            
            # Get pitch values where magnitude is significant
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            if pitch_values:
                pitch_array = np.array(pitch_values)
                features.pitch_mean_hz = float(np.mean(pitch_array))
                features.pitch_std_hz = float(np.std(pitch_array))
                features.pitch_min_hz = float(np.min(pitch_array))
                features.pitch_max_hz = float(np.max(pitch_array))
                features.pitch_range_hz = features.pitch_max_hz - features.pitch_min_hz
                
        except Exception as e:
            logger.warning(f"Pitch extraction failed: {e}")
    
    async def _extract_energy_features(
        self, 
        y: np.ndarray, 
        sr: int, 
        features: VoiceFeatures
    ):
        """Extract energy/volume features"""
        try:
            # RMS energy
            rms = librosa.feature.rms(y=y, frame_length=self.frame_length, hop_length=self.hop_length)[0]
            
            # Convert to dB
            rms_db = librosa.amplitude_to_db(rms, ref=np.max)
            
            features.energy_mean = float(np.mean(rms_db))
            features.energy_std = float(np.std(rms_db))
            features.energy_max = float(np.max(rms_db))
            features.dynamic_range = float(np.max(rms_db) - np.min(rms_db))
            
        except Exception as e:
            logger.warning(f"Energy extraction failed: {e}")
    
    async def _extract_pause_features(
        self, 
        y: np.ndarray, 
        sr: int, 
        features: VoiceFeatures
    ):
        """Extract pause/silence features"""
        try:
            # Use librosa's split to find non-silent intervals
            intervals = librosa.effects.split(y, top_db=30)
            
            if len(intervals) > 1:
                pauses = []
                for i in range(1, len(intervals)):
                    pause_start = intervals[i-1][1] / sr
                    pause_end = intervals[i][0] / sr
                    pause_duration = pause_end - pause_start
                    
                    if pause_duration >= self.min_pause_duration:
                        pauses.append(PauseSegment(
                            start=pause_start,
                            end=pause_end,
                            duration=pause_duration
                        ))
                
                features.pause_count = len(pauses)
                if pauses:
                    total_pause = sum(p.duration for p in pauses)
                    features.pause_total_duration = total_pause
                    features.pause_avg_duration = total_pause / len(pauses)
                    features.pause_ratio = total_pause / features.duration_seconds
            
            # Determine rhythm from pause patterns
            if features.pause_ratio > 0.3:
                features.speech_rhythm = "hesitant"
            elif features.pause_ratio > 0.15:
                features.speech_rhythm = "varied"
            else:
                features.speech_rhythm = "steady"
            
            # Tempo variability from pause distribution
            if features.pause_count > 1:
                pause_durations = [p.duration for p in pauses] if 'pauses' in dir() and pauses else []
                if pause_durations:
                    features.tempo_variability = float(np.std(pause_durations))
                    
        except Exception as e:
            logger.warning(f"Pause extraction failed: {e}")
    
    def _calculate_derived_indicators(self, features: VoiceFeatures):
        """Calculate confidence, stress, and engagement indicators"""
        
        # Confidence indicator
        # Based on: steady pitch, moderate pace, fewer/shorter pauses
        confidence_factors = []
        
        # Pitch stability (lower variation = more confident)
        if features.pitch_mean_hz > 0:
            pitch_cv = features.pitch_std_hz / features.pitch_mean_hz
            pitch_confidence = max(0, 1 - pitch_cv)
            confidence_factors.append(pitch_confidence)
        
        # Pause ratio (fewer pauses = more confident)
        pause_confidence = max(0, 1 - features.pause_ratio * 2)
        confidence_factors.append(pause_confidence)
        
        # Speaking rate (100-180 wpm is confident range)
        if features.speaking_rate_wpm > 0:
            rate = features.speaking_rate_wpm
            if 100 <= rate <= 180:
                rate_confidence = 1.0
            elif rate < 100:
                rate_confidence = rate / 100
            else:
                rate_confidence = max(0, 1 - (rate - 180) / 100)
            confidence_factors.append(rate_confidence)
        
        if confidence_factors:
            features.confidence_score = sum(confidence_factors) / len(confidence_factors)
        
        # Stress indicator
        # Based on: higher pitch, faster pace, more variation
        stress_factors = []
        
        # Higher pitch indicates stress
        if features.pitch_mean_hz > 0:
            # Typical speaking pitch: male ~120Hz, female ~210Hz
            # Higher = more stressed
            pitch_stress = min(1, features.pitch_mean_hz / 250)
            stress_factors.append(pitch_stress)
        
        # Pitch variation indicates stress
        if features.pitch_std_hz > 0:
            var_stress = min(1, features.pitch_std_hz / 50)
            stress_factors.append(var_stress)
        
        # Fast speaking can indicate stress
        if features.speaking_rate_wpm > 150:
            rate_stress = min(1, (features.speaking_rate_wpm - 150) / 100)
            stress_factors.append(rate_stress)
        
        if stress_factors:
            features.stress_indicator = sum(stress_factors) / len(stress_factors)
        
        # Engagement indicator
        # Based on: energy variation, pitch variation, rhythm
        engagement_factors = []
        
        # Energy variation (more = more engaged)
        if features.dynamic_range > 0:
            energy_engagement = min(1, features.dynamic_range / 30)
            engagement_factors.append(energy_engagement)
        
        # Pitch variation (some variation = engaged, too much = stressed)
        if features.pitch_std_hz > 0:
            pitch_engagement = min(1, features.pitch_std_hz / 30)
            engagement_factors.append(pitch_engagement)
        
        # Speaking rate (moderate = engaged)
        if 120 <= features.speaking_rate_wpm <= 160:
            engagement_factors.append(0.9)
        elif features.speaking_rate_wpm > 0:
            engagement_factors.append(0.5)
        
        if engagement_factors:
            features.engagement_indicator = sum(engagement_factors) / len(engagement_factors)


class VoiceProfiler:
    """Manages voice profiles for speaker identification"""
    
    def __init__(self, profiles_path: str = "profiles/voice"):
        self.profiles_path = profiles_path
        self.analyzer = VoiceAnalyzer()
        self._voice_profiles: Dict[str, VoiceFeatures] = {}
        
        # Create directory if not exists
        import os
        os.makedirs(profiles_path, exist_ok=True)
    
    async def create_voice_profile(
        self,
        person_id: str,
        audio_samples: List[str],
        name: Optional[str] = None
    ) -> VoiceFeatures:
        """
        Create a voice profile from multiple audio samples
        
        Args:
            person_id: ID of the person
            audio_samples: List of paths to audio files
            name: Optional name for logging
            
        Returns:
            Aggregated VoiceFeatures as the voice profile
        """
        all_features = []
        
        for audio_path in audio_samples:
            features = await self.analyzer.analyze_audio(
                audio_path, 
                speaker_id=person_id
            )
            all_features.append(features)
        
        # Aggregate features
        if not all_features:
            return VoiceFeatures(speaker_id=person_id)
        
        # Average numeric features
        profile = VoiceFeatures(speaker_id=person_id)
        
        numeric_fields = [
            'pitch_mean_hz', 'pitch_std_hz', 'pitch_min_hz', 'pitch_max_hz',
            'speaking_rate_wpm', 'energy_mean', 'energy_std',
            'pause_ratio', 'pause_avg_duration'
        ]
        
        for field in numeric_fields:
            values = [getattr(f, field) for f in all_features if getattr(f, field) > 0]
            if values:
                setattr(profile, field, sum(values) / len(values))
        
        # Save profile
        self._voice_profiles[person_id] = profile
        await self._save_profile(person_id, profile)
        
        logger.info(f"Created voice profile for {name or person_id}")
        return profile
    
    async def match_speaker(
        self,
        audio_path: str,
        threshold: float = 0.7
    ) -> Tuple[Optional[str], float]:
        """
        Try to match audio to a known speaker profile
        
        Args:
            audio_path: Path to audio file
            threshold: Minimum similarity score to match
            
        Returns:
            (person_id, confidence) or (None, 0) if no match
        """
        # Analyze the audio
        features = await self.analyzer.analyze_audio(audio_path)
        
        if not self._voice_profiles:
            await self._load_all_profiles()
        
        best_match = None
        best_score = 0.0
        
        for person_id, profile in self._voice_profiles.items():
            score = self._calculate_similarity(features, profile)
            if score > best_score:
                best_score = score
                best_match = person_id
        
        if best_score >= threshold:
            return best_match, best_score
        
        return None, 0.0
    
    def _calculate_similarity(
        self, 
        features: VoiceFeatures, 
        profile: VoiceFeatures
    ) -> float:
        """Calculate similarity between features and a profile"""
        scores = []
        
        # Pitch similarity
        if features.pitch_mean_hz > 0 and profile.pitch_mean_hz > 0:
            pitch_diff = abs(features.pitch_mean_hz - profile.pitch_mean_hz)
            pitch_score = max(0, 1 - pitch_diff / 100)
            scores.append(pitch_score)
        
        # Speaking rate similarity
        if features.speaking_rate_wpm > 0 and profile.speaking_rate_wpm > 0:
            rate_diff = abs(features.speaking_rate_wpm - profile.speaking_rate_wpm)
            rate_score = max(0, 1 - rate_diff / 50)
            scores.append(rate_score)
        
        # Pause pattern similarity
        if features.pause_ratio >= 0 and profile.pause_ratio >= 0:
            pause_diff = abs(features.pause_ratio - profile.pause_ratio)
            pause_score = max(0, 1 - pause_diff)
            scores.append(pause_score)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    async def _save_profile(self, person_id: str, profile: VoiceFeatures):
        """Save voice profile to disk"""
        import json
        path = os.path.join(self.profiles_path, f"{person_id}.json")
        with open(path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
    
    async def _load_all_profiles(self):
        """Load all voice profiles from disk"""
        import json
        import glob
        
        pattern = os.path.join(self.profiles_path, "*.json")
        for path in glob.glob(pattern):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                profile = VoiceFeatures.from_dict(data)
                self._voice_profiles[profile.speaker_id] = profile
            except Exception as e:
                logger.warning(f"Failed to load voice profile {path}: {e}")


@dataclass
class SentenceMood:
    """Mood detected for a sentence"""
    sentence: str
    mood: str  # happy, sad, angry, anxious, confident, uncertain, neutral, frustrated, excited
    confidence: float
    indicators: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sentence": self.sentence,
            "mood": self.mood,
            "confidence": self.confidence,
            "indicators": self.indicators
        }


class MoodAnalyzer:
    """Analyzes mood from text and voice features"""
    
    # Mood keywords/patterns
    MOOD_PATTERNS = {
        "happy": {
            "words": ["happy", "great", "wonderful", "excited", "love", "amazing", "fantastic", "good", "nice", "gezellig", "leuk", "fijn"],
            "phrases": ["i'm happy", "so good", "really great", "i love", "looking forward"]
        },
        "sad": {
            "words": ["sad", "unfortunately", "disappointed", "miss", "sorry", "regret", "verdrietig", "jammer", "helaas"],
            "phrases": ["i'm sad", "feel bad", "too bad", "i miss"]
        },
        "angry": {
            "words": ["angry", "frustrated", "annoyed", "hate", "terrible", "awful", "ridiculous", "boos", "kwaad", "irritant"],
            "phrases": ["so annoying", "can't believe", "makes me angry"]
        },
        "anxious": {
            "words": ["worried", "nervous", "anxious", "stressed", "afraid", "scared", "uncertain", "bang", "onzeker", "stress"],
            "phrases": ["i'm worried", "not sure", "what if", "scared that"]
        },
        "confident": {
            "words": ["confident", "certain", "sure", "definitely", "absolutely", "clearly", "obviously", "zeker", "duidelijk"],
            "phrases": ["i'm confident", "i'm sure", "no doubt", "without question"]
        },
        "uncertain": {
            "words": ["maybe", "perhaps", "might", "possibly", "guess", "think", "misschien", "wellicht", "denk"],
            "phrases": ["i think", "i guess", "not sure", "i don't know"]
        },
        "frustrated": {
            "words": ["vervelend", "frustrating", "annoying", "difficult", "hard", "moeilijk", "lastig"],
            "phrases": ["het is moeilijk", "heel vervelend", "so hard", "i can't"]
        },
        "excited": {
            "words": ["excited", "thrilled", "eager", "enthusiastic", "can't wait", "enthousiast", "spannend"],
            "phrases": ["so excited", "can't wait", "looking forward"]
        }
    }
    
    def analyze_sentence_mood(self, sentence: str) -> SentenceMood:
        """Analyze the mood of a single sentence"""
        text = sentence.lower().strip()
        
        mood_scores = {}
        indicators = []
        
        for mood, patterns in self.MOOD_PATTERNS.items():
            score = 0.0
            
            # Check words
            for word in patterns["words"]:
                if word in text:
                    score += 0.3
                    indicators.append(f"{mood}: '{word}'")
            
            # Check phrases
            for phrase in patterns.get("phrases", []):
                if phrase in text:
                    score += 0.5
                    indicators.append(f"{mood}: '{phrase}'")
            
            mood_scores[mood] = min(1.0, score)
        
        # Find dominant mood
        if mood_scores:
            best_mood = max(mood_scores, key=mood_scores.get)
            best_score = mood_scores[best_mood]
            
            if best_score > 0:
                return SentenceMood(
                    sentence=sentence,
                    mood=best_mood,
                    confidence=best_score,
                    indicators=indicators[:3]  # Top 3 indicators
                )
        
        # Default to neutral
        return SentenceMood(
            sentence=sentence,
            mood="neutral",
            confidence=0.5,
            indicators=[]
        )
    
    def analyze_text_moods(self, text: str) -> List[SentenceMood]:
        """Analyze moods for all sentences in text"""
        import re
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return [self.analyze_sentence_mood(s) for s in sentences]


# Global instances
_voice_analyzer: Optional[VoiceAnalyzer] = None
_voice_profiler: Optional[VoiceProfiler] = None
_mood_analyzer: Optional[MoodAnalyzer] = None


def get_voice_analyzer() -> VoiceAnalyzer:
    """Get or create the global voice analyzer"""
    global _voice_analyzer
    if _voice_analyzer is None:
        _voice_analyzer = VoiceAnalyzer()
    return _voice_analyzer


def get_voice_profiler() -> VoiceProfiler:
    """Get or create the global voice profiler"""
    global _voice_profiler
    if _voice_profiler is None:
        _voice_profiler = VoiceProfiler()
    return _voice_profiler


def get_mood_analyzer() -> MoodAnalyzer:
    """Get or create the global mood analyzer"""
    global _mood_analyzer
    if _mood_analyzer is None:
        _mood_analyzer = MoodAnalyzer()
    return _mood_analyzer

