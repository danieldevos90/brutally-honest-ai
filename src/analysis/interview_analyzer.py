"""
Interview Analyzer
Links recordings to persons, extracts insights, and builds profiles over time
"""

import asyncio
import logging
import json
import os
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

# Import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from audio.voice_analyzer import VoiceFeatures, get_voice_analyzer, get_voice_profiler
from profiles.profile_manager import get_profile_manager


@dataclass
class ParticipantInsight:
    """Insights extracted for a participant in an interview"""
    person_id: Optional[str] = None
    name: str = "Unknown"
    role: str = "participant"  # interviewer, candidate, participant
    
    # Voice analysis
    voice_features: Optional[Dict[str, Any]] = None
    
    # Communication analysis
    word_count: int = 0
    speaking_time_seconds: float = 0.0
    speaking_percentage: float = 0.0
    
    # Derived insights
    communication_style: str = "unknown"  # analytical, driver, expressive, amiable
    confidence_level: str = "medium"       # low, medium, high
    engagement_level: str = "medium"       # low, medium, high
    
    # Key statements
    key_statements: List[str] = field(default_factory=list)
    topics_discussed: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InterviewAnalysis:
    """Complete analysis of an interview session"""
    id: str
    recording_id: str
    
    # Context
    client_id: Optional[str] = None
    brand_id: Optional[str] = None
    interview_type: str = "general"  # behavioral, technical, conversational
    
    # Participants
    participants: List[ParticipantInsight] = field(default_factory=list)
    
    # Session data
    duration_seconds: float = 0.0
    transcript: str = ""
    
    # Extracted insights
    summary: str = ""
    key_topics: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    
    # Quality metrics
    conversation_balance: float = 0.5  # 0 = one-sided, 1 = balanced
    engagement_score: float = 0.5
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['participants'] = [p.to_dict() if hasattr(p, 'to_dict') else p for p in self.participants]
        return result


class InterviewAnalyzer:
    """
    Analyzes interview recordings and links to person profiles
    """
    
    def __init__(self, storage_path: str = "data/interviews"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.voice_analyzer = get_voice_analyzer()
        self.voice_profiler = get_voice_profiler()
        
        logger.info("Interview analyzer initialized")
    
    async def analyze_interview(
        self,
        recording_id: str,
        audio_path: str,
        transcript: str,
        speaker_segments: List[Dict[str, Any]],
        client_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        interview_type: str = "general"
    ) -> InterviewAnalysis:
        """
        Perform complete interview analysis
        
        Args:
            recording_id: ID of the recording
            audio_path: Path to audio file
            transcript: Full transcript
            speaker_segments: List of speaker segments with speaker_id, start, end, text
            client_id: Optional client context
            brand_id: Optional brand context
            interview_type: Type of interview
            
        Returns:
            Complete InterviewAnalysis
        """
        analysis = InterviewAnalysis(
            id=str(uuid.uuid4()),
            recording_id=recording_id,
            client_id=client_id,
            brand_id=brand_id,
            interview_type=interview_type,
            transcript=transcript
        )
        
        # Get audio duration
        try:
            import librosa
            y, sr = librosa.load(audio_path, sr=16000)
            analysis.duration_seconds = len(y) / sr
        except:
            analysis.duration_seconds = sum(s.get('end_time', 0) for s in speaker_segments)
        
        # Analyze each speaker
        speakers_data = {}
        for segment in speaker_segments:
            speaker_id = segment.get('speaker_id', 'SPEAKER_00')
            if speaker_id not in speakers_data:
                speakers_data[speaker_id] = {
                    'segments': [],
                    'total_text': '',
                    'total_time': 0.0
                }
            
            speakers_data[speaker_id]['segments'].append(segment)
            speakers_data[speaker_id]['total_text'] += ' ' + segment.get('text', '')
            speakers_data[speaker_id]['total_time'] += (
                segment.get('end_time', 0) - segment.get('start_time', 0)
            )
        
        # Analyze voice features for entire audio
        voice_features = await self.voice_analyzer.analyze_audio(
            audio_path,
            transcript=transcript,
            word_count=len(transcript.split())
        )
        
        # Create participant insights
        for speaker_id, data in speakers_data.items():
            # Try to match to known person
            matched_person_id, confidence = await self.voice_profiler.match_speaker(
                audio_path,
                threshold=0.6
            )
            
            # Get person name if matched
            person_name = speaker_id
            if matched_person_id:
                profile_manager = await get_profile_manager()
                person = await profile_manager.get_person_profile(matched_person_id)
                if person:
                    person_name = person.name
            
            # Calculate speaking percentage
            speaking_pct = (data['total_time'] / analysis.duration_seconds * 100 
                          if analysis.duration_seconds > 0 else 0)
            
            # Determine communication style from patterns
            word_count = len(data['total_text'].split())
            style = self._determine_communication_style(
                word_count, 
                data['total_time'],
                voice_features
            )
            
            participant = ParticipantInsight(
                person_id=matched_person_id,
                name=person_name,
                role=self._guess_role(speaker_id, len(speakers_data)),
                voice_features=voice_features.to_dict(),
                word_count=word_count,
                speaking_time_seconds=data['total_time'],
                speaking_percentage=speaking_pct,
                communication_style=style,
                confidence_level=self._level_from_score(voice_features.confidence_score),
                engagement_level=self._level_from_score(voice_features.engagement_indicator),
                key_statements=self._extract_key_statements(data['total_text'])
            )
            
            analysis.participants.append(participant)
        
        # Calculate conversation balance
        if len(analysis.participants) >= 2:
            times = [p.speaking_time_seconds for p in analysis.participants]
            max_time = max(times)
            min_time = min(times)
            analysis.conversation_balance = min_time / max_time if max_time > 0 else 0.5
        
        # Calculate overall engagement
        engagements = [p.engagement_level for p in analysis.participants]
        engagement_scores = {'low': 0.33, 'medium': 0.66, 'high': 1.0}
        avg_engagement = sum(engagement_scores.get(e, 0.5) for e in engagements) / len(engagements)
        analysis.engagement_score = avg_engagement
        
        # Extract topics
        analysis.key_topics = self._extract_topics(transcript)
        
        # Generate summary
        analysis.summary = self._generate_summary(analysis)
        
        # Save analysis
        await self._save_analysis(analysis)
        
        # Link to person profiles
        await self._link_to_profiles(analysis)
        
        logger.info(f"Interview analysis complete: {len(analysis.participants)} participants, "
                   f"{analysis.duration_seconds:.1f}s duration")
        
        return analysis
    
    def _determine_communication_style(
        self, 
        word_count: int, 
        speaking_time: float,
        voice: VoiceFeatures
    ) -> str:
        """Determine communication style from patterns"""
        if speaking_time == 0:
            return "unknown"
        
        wpm = (word_count / speaking_time) * 60 if speaking_time > 0 else 0
        
        # Fast + high energy = Driver/Expressive
        # Slow + measured = Analytical/Amiable
        if wpm > 160:
            if voice.energy_std > 5:
                return "expressive"
            else:
                return "driver"
        else:
            if voice.pause_ratio > 0.2:
                return "analytical"
            else:
                return "amiable"
    
    def _level_from_score(self, score: float) -> str:
        """Convert 0-1 score to low/medium/high"""
        if score < 0.4:
            return "low"
        elif score < 0.7:
            return "medium"
        else:
            return "high"
    
    def _guess_role(self, speaker_id: str, total_speakers: int) -> str:
        """Guess role based on speaker ID"""
        if total_speakers == 2:
            if speaker_id == "SPEAKER_00":
                return "interviewer"
            else:
                return "candidate"
        return "participant"
    
    def _extract_key_statements(self, text: str, max_statements: int = 5) -> List[str]:
        """Extract key statements from text"""
        # Simple extraction: sentences with key indicators
        sentences = text.replace('!', '.').replace('?', '.').split('.')
        key_indicators = [
            'i think', 'i believe', 'important', 'key', 'main', 
            'challenge', 'success', 'learn', 'improve', 'goal'
        ]
        
        key_statements = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:
                lower = sentence.lower()
                if any(ind in lower for ind in key_indicators):
                    key_statements.append(sentence)
                    if len(key_statements) >= max_statements:
                        break
        
        return key_statements
    
    def _extract_topics(self, transcript: str) -> List[str]:
        """Extract main topics from transcript"""
        # Simple keyword extraction
        # In production, use TF-IDF or LLM
        words = transcript.lower().split()
        
        # Filter common words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                    'could', 'should', 'may', 'might', 'can', 'to', 'of', 'in',
                    'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'and',
                    'or', 'but', 'if', 'then', 'that', 'this', 'it', 'its'}
        
        word_freq = {}
        for word in words:
            word = ''.join(c for c in word if c.isalnum())
            if len(word) > 3 and word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Top topics
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:10]]
    
    def _generate_summary(self, analysis: InterviewAnalysis) -> str:
        """Generate a summary of the interview"""
        parts = []
        
        # Duration
        mins = int(analysis.duration_seconds // 60)
        secs = int(analysis.duration_seconds % 60)
        parts.append(f"{mins}m {secs}s interview with {len(analysis.participants)} participant(s)")
        
        # Participants
        for p in analysis.participants:
            parts.append(f"- {p.name} ({p.role}): {p.word_count} words, "
                        f"{p.speaking_percentage:.0f}% of conversation, "
                        f"{p.confidence_level} confidence")
        
        # Balance
        if analysis.conversation_balance < 0.3:
            parts.append("Note: Conversation was one-sided")
        elif analysis.conversation_balance > 0.7:
            parts.append("Note: Well-balanced conversation")
        
        # Topics
        if analysis.key_topics:
            parts.append(f"Main topics: {', '.join(analysis.key_topics[:5])}")
        
        return "\n".join(parts)
    
    async def _save_analysis(self, analysis: InterviewAnalysis):
        """Save analysis to storage"""
        path = self.storage_path / f"{analysis.id}.json"
        with open(path, 'w') as f:
            json.dump(analysis.to_dict(), f, indent=2)
    
    async def _link_to_profiles(self, analysis: InterviewAnalysis):
        """Link analysis results to person profiles"""
        profile_manager = await get_profile_manager()
        
        for participant in analysis.participants:
            if participant.person_id:
                try:
                    # Get person profile
                    person = await profile_manager.get_person_profile(participant.person_id)
                    if person:
                        # Add transcription reference
                        if analysis.recording_id not in person.transcriptions:
                            person.transcriptions.append(analysis.recording_id)
                        
                        # Update metadata with voice characteristics
                        if 'voice_profile' not in person.metadata:
                            person.metadata['voice_profile'] = {}
                        
                        # Update voice profile (average with existing)
                        if participant.voice_features:
                            existing = person.metadata.get('voice_profile', {})
                            for key, value in participant.voice_features.items():
                                if isinstance(value, (int, float)) and value > 0:
                                    if key in existing and existing[key] > 0:
                                        # Running average
                                        existing[key] = (existing[key] + value) / 2
                                    else:
                                        existing[key] = value
                            person.metadata['voice_profile'] = existing
                        
                        # Save updated profile
                        await profile_manager.update_person_profile(
                            participant.person_id,
                            bio=person.bio  # Trigger save
                        )
                        
                        logger.info(f"Linked recording to person profile: {person.name}")
                        
                except Exception as e:
                    logger.warning(f"Failed to link to profile {participant.person_id}: {e}")
    
    async def get_analysis(self, analysis_id: str) -> Optional[InterviewAnalysis]:
        """Load an analysis from storage"""
        path = self.storage_path / f"{analysis_id}.json"
        if not path.exists():
            return None
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return InterviewAnalysis(**data)
    
    async def list_analyses(
        self, 
        client_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        limit: int = 50
    ) -> List[InterviewAnalysis]:
        """List analyses with optional filtering"""
        analyses = []
        
        for path in sorted(self.storage_path.glob("*.json"), reverse=True):
            if len(analyses) >= limit:
                break
            
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                
                # Filter
                if client_id and data.get('client_id') != client_id:
                    continue
                if brand_id and data.get('brand_id') != brand_id:
                    continue
                
                analyses.append(InterviewAnalysis(**data))
            except Exception as e:
                logger.warning(f"Failed to load analysis {path}: {e}")
        
        return analyses


# Global instance
_interview_analyzer: Optional[InterviewAnalyzer] = None


async def get_interview_analyzer() -> InterviewAnalyzer:
    """Get or create global interview analyzer"""
    global _interview_analyzer
    if _interview_analyzer is None:
        _interview_analyzer = InterviewAnalyzer()
    return _interview_analyzer

