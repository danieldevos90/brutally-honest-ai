"""
Team Dynamics Analyzer - @TheBigFish AI Methodology
Based on the 6 dimensions of High Performing Teams

This module implements team dynamics analysis for:
- Team diagnosis and development
- Leadership feedback
- Culture scanning

Output: Probabilistic scores (1-5) per dimension based on:
- Language usage (utterance-level)
- Interaction patterns (sequence-level)
- Audiometry (prosody analysis, optional)

IMPORTANT PRINCIPLES:
- No truth claims - measures behavioral manifestations
- Output is a mirror for dialogue, not HR assessment
- Aggregation over multiple meetings is essential
- Sequence analysis required (not just single utterances)
"""

import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)


# ============================================
# ENUMS AND CONSTANTS
# ============================================

class Dimension(str, Enum):
    """The 6 dimensions of High Performing Teams"""
    PSYCHOLOGICAL_SAFETY = "psychological_safety"
    COLLECTIVE_OWNERSHIP = "collective_ownership"
    CONSTRUCTIVE_COLLABORATION = "constructive_collaboration"
    LEARNING_ADAPTATION = "learning_adaptation"
    ENERGY_ENGAGEMENT = "energy_engagement"
    STRUCTURE_RELIABILITY = "structure_reliability"


class InputQuality(str, Enum):
    """Input data quality levels"""
    EXCELLENT = "excellent"  # Full audio + transcript + speaker ID
    GOOD = "good"           # Transcript + speaker ID
    ACCEPTABLE = "acceptable"  # Transcript only
    INSUFFICIENT = "insufficient"  # Not enough data


class FrameType(str, Enum):
    """Frame types detected in speech"""
    VULNERABILITY = "vulnerability"
    LEARNING = "learning"
    BLAME = "blame"
    OPENING = "opening"
    COMMITMENT = "commitment"
    CHALLENGE = "challenge"
    ACKNOWLEDGEMENT = "acknowledgement"
    STRATEGY = "strategy"
    CELEBRATION = "celebration"


# ============================================
# LANGUAGE MARKERS (Dutch + English)
# ============================================

LANGUAGE_MARKERS = {
    # Dimension 1: Psychological Safety
    "vulnerability": {
        "nl": [
            "ik weet het niet", "ik snap dit nog niet", "kun je me helpen",
            "ik heb een fout gemaakt", "ik begrijp het niet", "help me",
            "ik twijfel", "ben ik de enige", "eerlijk gezegd", "ik moet bekennen"
        ],
        "en": [
            "i don't know", "i'm not sure", "can you help me", "i made a mistake",
            "i don't understand", "help me", "i'm struggling", "honestly",
            "i have to admit", "i was wrong"
        ]
    },
    "learning_frame": {
        "nl": [
            "wat kunnen we hiervan leren", "interessant punt", "vertel eens meer",
            "wat zien jullie", "hoe kijken jullie hiernaar", "goed punt",
            "daar had ik niet aan gedacht", "laten we dit onderzoeken"
        ],
        "en": [
            "what can we learn from this", "interesting point", "tell me more",
            "what do you see", "how do you look at this", "good point",
            "i hadn't thought of that", "let's explore this"
        ]
    },
    "blame_frame": {
        "nl": [
            "waarom heb jij", "hoe kon dit fout gaan", "wie heeft dit laten liggen",
            "dat is jouw verantwoordelijkheid", "je had moeten", "dit is niet mijn schuld",
            "waarom niet", "wie is hier verantwoordelijk"
        ],
        "en": [
            "why did you", "how could this go wrong", "who dropped the ball",
            "that's your responsibility", "you should have", "this is not my fault",
            "why not", "who is responsible"
        ]
    },
    
    # Dimension 2: Collective Ownership
    "we_language": {
        "nl": ["wij gaan", "onze klant", "we hebben afgesproken", "ons team", "samen", "wij"],
        "en": ["we will", "our customer", "we agreed", "our team", "together", "we"]
    },
    "they_language": {
        "nl": ["zij moeten", "ik weet niet wat zij", "dat is hun probleem", "zij"],
        "en": ["they should", "i don't know what they", "that's their problem", "they"]
    },
    "commitment_language": {
        "nl": [
            "ik neem dit op me", "ik ga dit oplossen", "ik zorg ervoor",
            "voor datum", "mijn verantwoordelijkheid", "ik commit me"
        ],
        "en": [
            "i'll take this", "i'll solve this", "i'll make sure",
            "by date", "my responsibility", "i commit"
        ]
    },
    "strategy_reference": {
        "nl": ["strategie", "doelen", "kpi", "klantwaarde", "prioriteit", "roadmap", "visie"],
        "en": ["strategy", "goals", "kpi", "customer value", "priority", "roadmap", "vision"]
    },
    
    # Dimension 3: Constructive Collaboration
    "challenge_language": {
        "nl": [
            "ik zie dat anders", "ik ben het niet eens", "heb je overwogen",
            "wat als", "daar ben ik kritisch over", "laat me devil's advocate spelen"
        ],
        "en": [
            "i see it differently", "i disagree", "have you considered",
            "what if", "i'm critical about", "let me play devil's advocate"
        ]
    },
    "acknowledgement_language": {
        "nl": [
            "goed punt", "dank dat je dat zegt", "mee eens", "sterke observatie",
            "interessant perspectief", "daar heb je gelijk in"
        ],
        "en": [
            "good point", "thanks for saying that", "i agree", "strong observation",
            "interesting perspective", "you're right about that"
        ]
    },
    "bridge_language": {
        "nl": ["ik hoor x én y", "aan de ene kant", "tegelijkertijd", "beide punten"],
        "en": ["i hear both", "on one hand", "at the same time", "both points"]
    },
    
    # Dimension 4: Learning & Adaptation
    "experiment_language": {
        "nl": [
            "we verwachten dat", "laten we proberen", "hypothese", "test",
            "experiment", "valideren", "itereren", "pilot"
        ],
        "en": [
            "we expect that", "let's try", "hypothesis", "test",
            "experiment", "validate", "iterate", "pilot"
        ]
    },
    "learning_loop": {
        "nl": [
            "wat hebben we geleerd", "vorige keer", "bijstellen", "aanpassen",
            "reflectie", "evaluatie", "lessons learned"
        ],
        "en": [
            "what did we learn", "last time", "adjust", "adapt",
            "reflection", "evaluation", "lessons learned"
        ]
    },
    
    # Dimension 5: Energy & Engagement
    "meaning_markers": {
        "nl": ["trots", "impact", "waarde", "betekenis", "verschil maken", "ertoe doen"],
        "en": ["proud", "impact", "value", "meaning", "make a difference", "matters"]
    },
    "celebration_language": {
        "nl": ["goed gedaan", "gefeliciteerd", "super", "fantastisch", "geweldig"],
        "en": ["well done", "congratulations", "great", "fantastic", "amazing"]
    },
    
    # Dimension 6: Structure & Reliability
    "decision_language": {
        "nl": ["we besluiten", "jij pakt dit op", "afgesproken", "deadline", "actie"],
        "en": ["we decide", "you'll take this", "agreed", "deadline", "action"]
    },
    "clarity_language": {
        "nl": ["wie is verantwoordelijk", "wanneer", "wat betekent af", "next steps"],
        "en": ["who is responsible", "when", "what does done mean", "next steps"]
    }
}


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class Utterance:
    """A single speech utterance/turn"""
    id: str
    speaker_id: str
    speaker_name: Optional[str]
    text: str
    timestamp_start: float = 0.0
    timestamp_end: float = 0.0
    
    # Audio features (optional)
    pitch_mean: Optional[float] = None
    pitch_variation: Optional[float] = None
    energy_mean: Optional[float] = None
    speaking_rate: Optional[float] = None
    
    # Detected markers
    markers: List[str] = field(default_factory=list)
    frames: List[FrameType] = field(default_factory=list)


@dataclass
class SpeakerStats:
    """Statistics per speaker"""
    speaker_id: str
    speaker_name: Optional[str]
    total_utterances: int = 0
    total_words: int = 0
    total_speaking_time: float = 0.0
    
    # Markers by type
    marker_counts: Dict[str, int] = field(default_factory=dict)
    
    # Interaction stats
    interruptions_made: int = 0
    interruptions_received: int = 0
    questions_asked: int = 0
    
    # Pronoun usage
    we_count: int = 0
    i_count: int = 0
    they_count: int = 0


@dataclass
class DimensionScore:
    """Score for a single dimension"""
    dimension: Dimension
    score: float  # 1-5
    confidence: float  # 0-1
    
    # Evidence
    positive_indicators: List[str] = field(default_factory=list)
    negative_indicators: List[str] = field(default_factory=list)
    patterns_detected: List[str] = field(default_factory=list)
    
    # Explanation
    explanation: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "score": round(self.score, 2),
            "confidence": round(self.confidence, 2),
            "positive_indicators": self.positive_indicators[:5],
            "negative_indicators": self.negative_indicators[:5],
            "patterns": self.patterns_detected[:5],
            "explanation": self.explanation
        }


@dataclass
class InputQualityReport:
    """Report on input data quality"""
    quality_level: InputQuality
    quality_score: float  # 0-100
    
    # Data availability
    has_transcript: bool = False
    has_speaker_identification: bool = False
    has_audio_features: bool = False
    has_timestamps: bool = False
    
    # Data volume
    total_utterances: int = 0
    total_speakers: int = 0
    total_duration_minutes: float = 0.0
    
    # Issues
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Minimum requirements
    meets_minimum_requirements: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality_level": self.quality_level.value,
            "quality_score": round(self.quality_score, 1),
            "data_availability": {
                "transcript": self.has_transcript,
                "speaker_identification": self.has_speaker_identification,
                "audio_features": self.has_audio_features,
                "timestamps": self.has_timestamps
            },
            "volume": {
                "utterances": self.total_utterances,
                "speakers": self.total_speakers,
                "duration_minutes": round(self.total_duration_minutes, 1)
            },
            "meets_minimum_requirements": self.meets_minimum_requirements,
            "issues": self.issues,
            "recommendations": self.recommendations
        }


@dataclass
class TeamDynamicsResult:
    """Complete team dynamics analysis result"""
    analysis_id: str
    timestamp: str
    
    # Input quality
    input_quality: InputQualityReport
    
    # Dimension scores
    dimension_scores: Dict[str, DimensionScore] = field(default_factory=dict)
    
    # Overall team score (weighted average)
    team_score: float = 0.0
    team_score_confidence: float = 0.0
    
    # Speaker analysis
    speaker_stats: Dict[str, SpeakerStats] = field(default_factory=dict)
    
    # Key patterns
    dominance_index: float = 0.0  # 0 = balanced, 1 = one person dominates
    interaction_balance: float = 0.0  # 0-1
    
    # CEO/Leader specific (if identified)
    leader_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Top indicators across all dimensions
    top_indicators: List[str] = field(default_factory=list)
    
    # Processing info
    processing_time_seconds: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp,
            "input_quality": self.input_quality.to_dict(),
            "team_score": round(self.team_score, 2),
            "team_score_confidence": round(self.team_score_confidence, 2),
            "dimension_scores": {
                k: v.to_dict() for k, v in self.dimension_scores.items()
            },
            "speaker_count": len(self.speaker_stats),
            "dominance_index": round(self.dominance_index, 3),
            "interaction_balance": round(self.interaction_balance, 3),
            "leader_patterns": self.leader_patterns,
            "top_indicators": self.top_indicators[:10],
            "processing_time_seconds": round(self.processing_time_seconds, 2)
        }


# ============================================
# MARKER DETECTOR
# ============================================

class MarkerDetector:
    """Detects language markers in text"""
    
    def __init__(self):
        self.markers = LANGUAGE_MARKERS
    
    def detect_all_markers(self, text: str) -> Dict[str, List[str]]:
        """Detect all markers in text"""
        text_lower = text.lower()
        found = {}
        
        for marker_type, languages in self.markers.items():
            found[marker_type] = []
            
            for lang, patterns in languages.items():
                for pattern in patterns:
                    if pattern in text_lower:
                        found[marker_type].append(pattern)
        
        return {k: v for k, v in found.items() if v}
    
    def detect_frames(self, text: str) -> List[FrameType]:
        """Detect frame types in utterance"""
        markers = self.detect_all_markers(text)
        frames = []
        
        if markers.get("vulnerability"):
            frames.append(FrameType.VULNERABILITY)
        if markers.get("learning_frame") or markers.get("learning_loop"):
            frames.append(FrameType.LEARNING)
        if markers.get("blame_frame"):
            frames.append(FrameType.BLAME)
        if markers.get("commitment_language"):
            frames.append(FrameType.COMMITMENT)
        if markers.get("challenge_language"):
            frames.append(FrameType.CHALLENGE)
        if markers.get("acknowledgement_language"):
            frames.append(FrameType.ACKNOWLEDGEMENT)
        if markers.get("strategy_reference"):
            frames.append(FrameType.STRATEGY)
        if markers.get("celebration_language"):
            frames.append(FrameType.CELEBRATION)
        
        return frames
    
    def count_pronouns(self, text: str) -> Dict[str, int]:
        """Count pronoun usage"""
        text_lower = text.lower()
        words = text_lower.split()
        
        we_words = {"we", "wij", "ons", "onze", "our", "us"}
        i_words = {"ik", "i", "mij", "me", "my", "mijn", "mine"}
        they_words = {"zij", "they", "hun", "their", "them"}
        
        return {
            "we": sum(1 for w in words if w in we_words),
            "i": sum(1 for w in words if w in i_words),
            "they": sum(1 for w in words if w in they_words)
        }


# ============================================
# INPUT QUALITY ANALYZER
# ============================================

class InputQualityAnalyzer:
    """Analyzes and validates input data quality"""
    
    # Minimum requirements for valid analysis
    MIN_UTTERANCES = 50
    MIN_SPEAKERS = 2
    MIN_DURATION_MINUTES = 10
    RECOMMENDED_MEETINGS = 6
    RECOMMENDED_HOURS = 8
    
    def analyze(self, utterances: List[Utterance]) -> InputQualityReport:
        """Analyze input data quality"""
        report = InputQualityReport(
            quality_level=InputQuality.INSUFFICIENT,
            quality_score=0
        )
        
        if not utterances:
            report.issues.append("No utterances provided")
            report.recommendations.append("Provide transcribed meeting data")
            return report
        
        # Check data availability
        report.has_transcript = all(u.text.strip() for u in utterances)
        report.has_speaker_identification = all(u.speaker_id for u in utterances)
        report.has_timestamps = all(u.timestamp_end > u.timestamp_start for u in utterances)
        report.has_audio_features = any(u.pitch_mean is not None for u in utterances)
        
        # Calculate volume metrics
        report.total_utterances = len(utterances)
        speakers = set(u.speaker_id for u in utterances if u.speaker_id)
        report.total_speakers = len(speakers)
        
        if report.has_timestamps:
            total_seconds = sum(u.timestamp_end - u.timestamp_start for u in utterances)
            report.total_duration_minutes = total_seconds / 60
        else:
            # Estimate from word count
            total_words = sum(len(u.text.split()) for u in utterances)
            report.total_duration_minutes = total_words / 150  # ~150 words/min
        
        # Check minimum requirements
        issues = []
        recommendations = []
        
        if report.total_utterances < self.MIN_UTTERANCES:
            issues.append(f"Insufficient utterances: {report.total_utterances} (min: {self.MIN_UTTERANCES})")
            recommendations.append("Include more meeting data for reliable analysis")
        
        if report.total_speakers < self.MIN_SPEAKERS:
            issues.append(f"Insufficient speakers: {report.total_speakers} (min: {self.MIN_SPEAKERS})")
            recommendations.append("Include multi-speaker meetings")
        
        if not report.has_speaker_identification:
            issues.append("No speaker identification available")
            recommendations.append("Add speaker diarization for individual scores")
        
        if not report.has_audio_features:
            recommendations.append("Add audio analysis for prosody-based insights")
        
        if report.total_duration_minutes < self.MIN_DURATION_MINUTES:
            issues.append(f"Short duration: {report.total_duration_minutes:.1f} min (min: {self.MIN_DURATION_MINUTES})")
        
        report.issues = issues
        report.recommendations = recommendations
        
        # Determine quality level and score
        score = 0
        
        if report.has_transcript:
            score += 25
        if report.has_speaker_identification:
            score += 25
        if report.has_timestamps:
            score += 15
        if report.has_audio_features:
            score += 15
        
        # Volume bonus
        if report.total_utterances >= self.MIN_UTTERANCES:
            score += 10
        if report.total_speakers >= 3:
            score += 5
        if report.total_duration_minutes >= 30:
            score += 5
        
        report.quality_score = min(100, score)
        
        # Determine level
        if score >= 80 and len(issues) == 0:
            report.quality_level = InputQuality.EXCELLENT
        elif score >= 60 and len(issues) <= 1:
            report.quality_level = InputQuality.GOOD
        elif score >= 40:
            report.quality_level = InputQuality.ACCEPTABLE
        else:
            report.quality_level = InputQuality.INSUFFICIENT
        
        report.meets_minimum_requirements = (
            report.total_utterances >= self.MIN_UTTERANCES and
            report.total_speakers >= self.MIN_SPEAKERS and
            report.has_transcript
        )
        
        return report


# ============================================
# DIMENSION ANALYZERS
# ============================================

class DimensionAnalyzer:
    """Base class for dimension analyzers"""
    
    def __init__(self):
        self.marker_detector = MarkerDetector()
    
    def analyze(
        self, 
        utterances: List[Utterance],
        speaker_stats: Dict[str, SpeakerStats]
    ) -> DimensionScore:
        raise NotImplementedError


class PsychologicalSafetyAnalyzer(DimensionAnalyzer):
    """
    Dimension 1: Psychologische veiligheid & open prestatiedialoog
    
    Measures:
    - Vulnerability language
    - Learning vs blame frames
    - Response to tension
    - Speaking time distribution
    - CEO curiosity vs control
    """
    
    def analyze(
        self, 
        utterances: List[Utterance],
        speaker_stats: Dict[str, SpeakerStats]
    ) -> DimensionScore:
        positive = []
        negative = []
        patterns = []
        
        vulnerability_count = 0
        learning_frame_count = 0
        blame_frame_count = 0
        
        for u in utterances:
            markers = self.marker_detector.detect_all_markers(u.text)
            
            if markers.get("vulnerability"):
                vulnerability_count += 1
                positive.extend([f"Vulnerability: '{m}'" for m in markers["vulnerability"][:1]])
            
            if markers.get("learning_frame"):
                learning_frame_count += 1
                positive.extend([f"Learning frame: '{m}'" for m in markers["learning_frame"][:1]])
            
            if markers.get("blame_frame"):
                blame_frame_count += 1
                negative.extend([f"Blame frame: '{m}'" for m in markers["blame_frame"][:1]])
        
        # Calculate scores
        total = len(utterances)
        if total == 0:
            return DimensionScore(
                dimension=Dimension.PSYCHOLOGICAL_SAFETY,
                score=3.0,
                confidence=0.0,
                explanation="Insufficient data"
            )
        
        # Vulnerability ratio (should be present but not excessive)
        vuln_ratio = vulnerability_count / total
        if 0.05 <= vuln_ratio <= 0.20:
            patterns.append(f"Healthy vulnerability level ({vuln_ratio:.1%})")
        elif vuln_ratio < 0.02:
            patterns.append(f"Low vulnerability signals ({vuln_ratio:.1%}) - may indicate low safety")
        
        # Learning vs Blame ratio
        if learning_frame_count + blame_frame_count > 0:
            learn_blame_ratio = learning_frame_count / (learning_frame_count + blame_frame_count)
            if learn_blame_ratio > 0.7:
                patterns.append(f"Strong learning orientation ({learn_blame_ratio:.1%})")
            elif learn_blame_ratio < 0.3:
                patterns.append(f"Blame-dominant culture ({1-learn_blame_ratio:.1%})")
        
        # Speaking time distribution (from speaker stats)
        if len(speaker_stats) > 1:
            speaking_times = [s.total_speaking_time for s in speaker_stats.values()]
            if speaking_times:
                max_time = max(speaking_times)
                total_time = sum(speaking_times)
                dominance = max_time / total_time if total_time > 0 else 0
                if dominance > 0.5:
                    patterns.append(f"Unbalanced speaking time (one person: {dominance:.1%})")
                else:
                    patterns.append(f"Balanced speaking distribution")
        
        # Calculate score (1-5)
        score = 3.0  # Start neutral
        
        # Positive adjustments
        score += min(0.5, vuln_ratio * 5)  # Up to +0.5 for vulnerability
        score += min(0.5, learning_frame_count / (total * 0.1))  # Up to +0.5 for learning
        
        # Negative adjustments
        score -= min(1.0, blame_frame_count / (total * 0.05))  # Down for blame
        
        # Clamp to 1-5
        score = max(1.0, min(5.0, score))
        
        # Confidence based on data volume
        confidence = min(1.0, total / 100)
        
        return DimensionScore(
            dimension=Dimension.PSYCHOLOGICAL_SAFETY,
            score=score,
            confidence=confidence,
            positive_indicators=list(set(positive))[:5],
            negative_indicators=list(set(negative))[:5],
            patterns_detected=patterns,
            explanation=f"Based on {vulnerability_count} vulnerability signals, {learning_frame_count} learning frames, {blame_frame_count} blame frames"
        )


class CollectiveOwnershipAnalyzer(DimensionAnalyzer):
    """
    Dimension 2: Collectieve ambitie & ownership
    
    Measures:
    - We/I/They pronoun ratio
    - Commitment statements
    - Strategy references
    - Follow-through patterns
    """
    
    def analyze(
        self, 
        utterances: List[Utterance],
        speaker_stats: Dict[str, SpeakerStats]
    ) -> DimensionScore:
        positive = []
        negative = []
        patterns = []
        
        total_we = 0
        total_i = 0
        total_they = 0
        commitment_count = 0
        strategy_count = 0
        
        for u in utterances:
            # Pronoun analysis
            pronouns = self.marker_detector.count_pronouns(u.text)
            total_we += pronouns["we"]
            total_i += pronouns["i"]
            total_they += pronouns["they"]
            
            # Marker analysis
            markers = self.marker_detector.detect_all_markers(u.text)
            
            if markers.get("commitment_language"):
                commitment_count += 1
                positive.extend([f"Commitment: '{m}'" for m in markers["commitment_language"][:1]])
            
            if markers.get("strategy_reference"):
                strategy_count += 1
                positive.extend([f"Strategy ref: '{m}'" for m in markers["strategy_reference"][:1]])
            
            if markers.get("they_language"):
                negative.extend([f"They-language: '{m}'" for m in markers["they_language"][:1]])
        
        # Calculate pronoun ratio
        total_pronouns = total_we + total_i + total_they
        if total_pronouns > 0:
            we_ratio = total_we / total_pronouns
            they_ratio = total_they / total_pronouns
            
            if we_ratio > 0.5:
                patterns.append(f"Strong we-orientation ({we_ratio:.1%})")
            elif we_ratio < 0.2:
                patterns.append(f"Low collective language ({we_ratio:.1%})")
            
            if they_ratio > 0.3:
                patterns.append(f"High they-language ({they_ratio:.1%}) - may indicate siloed thinking")
        
        # Commitment density
        total = len(utterances)
        if total > 0:
            commitment_density = commitment_count / total
            if commitment_density > 0.1:
                patterns.append(f"High commitment language ({commitment_density:.1%})")
        
        # Calculate score
        score = 3.0
        
        if total_pronouns > 0:
            score += (total_we / total_pronouns - 0.33) * 2  # Adjust for we-language
            score -= (total_they / total_pronouns) * 1.5  # Penalize they-language
        
        if total > 0:
            score += min(0.5, commitment_count / total * 5)
            score += min(0.3, strategy_count / total * 3)
        
        score = max(1.0, min(5.0, score))
        confidence = min(1.0, total / 100)
        
        return DimensionScore(
            dimension=Dimension.COLLECTIVE_OWNERSHIP,
            score=score,
            confidence=confidence,
            positive_indicators=list(set(positive))[:5],
            negative_indicators=list(set(negative))[:5],
            patterns_detected=patterns,
            explanation=f"We/I/They ratio: {total_we}/{total_i}/{total_they}, {commitment_count} commitments, {strategy_count} strategy refs"
        )


class ConstructiveCollaborationAnalyzer(DimensionAnalyzer):
    """
    Dimension 3: Constructieve samenwerking & benutten van verschil
    
    Measures:
    - Challenge ratio (constructive disagreement)
    - Acknowledgement markers
    - Bridge language
    - Perspective integration
    """
    
    def analyze(
        self, 
        utterances: List[Utterance],
        speaker_stats: Dict[str, SpeakerStats]
    ) -> DimensionScore:
        positive = []
        negative = []
        patterns = []
        
        challenge_count = 0
        acknowledgement_count = 0
        bridge_count = 0
        
        for u in utterances:
            markers = self.marker_detector.detect_all_markers(u.text)
            
            if markers.get("challenge_language"):
                challenge_count += 1
                positive.extend([f"Challenge: '{m}'" for m in markers["challenge_language"][:1]])
            
            if markers.get("acknowledgement_language"):
                acknowledgement_count += 1
                positive.extend([f"Acknowledgement: '{m}'" for m in markers["acknowledgement_language"][:1]])
            
            if markers.get("bridge_language"):
                bridge_count += 1
                positive.extend([f"Bridge: '{m}'" for m in markers["bridge_language"][:1]])
        
        total = len(utterances)
        if total > 0:
            # Challenge ratio
            challenge_ratio = challenge_count / total
            if 0.05 <= challenge_ratio <= 0.20:
                patterns.append(f"Healthy challenge level ({challenge_ratio:.1%})")
            elif challenge_ratio < 0.02:
                patterns.append(f"Low challenge ({challenge_ratio:.1%}) - may indicate groupthink")
            elif challenge_ratio > 0.25:
                patterns.append(f"High challenge ({challenge_ratio:.1%}) - check for conflict")
            
            # Acknowledgement ratio
            ack_ratio = acknowledgement_count / total
            if ack_ratio > 0.1:
                patterns.append(f"Good acknowledgement culture ({ack_ratio:.1%})")
        
        # Calculate score
        score = 3.0
        
        if total > 0:
            # Balanced challenge is positive
            if 0.05 <= challenge_count / total <= 0.20:
                score += 0.5
            elif challenge_count / total > 0.25:
                score -= 0.3  # Too much might be conflict
            
            score += min(0.5, acknowledgement_count / total * 5)
            score += min(0.3, bridge_count / total * 10)
        
        score = max(1.0, min(5.0, score))
        confidence = min(1.0, total / 100)
        
        return DimensionScore(
            dimension=Dimension.CONSTRUCTIVE_COLLABORATION,
            score=score,
            confidence=confidence,
            positive_indicators=list(set(positive))[:5],
            negative_indicators=list(set(negative))[:5],
            patterns_detected=patterns,
            explanation=f"{challenge_count} challenges, {acknowledgement_count} acknowledgements, {bridge_count} bridges"
        )


class LearningAdaptationAnalyzer(DimensionAnalyzer):
    """
    Dimension 4: Leren, bijsturen & adaptief werken
    
    Measures:
    - Learning loop density
    - Experiment language
    - Follow-up consistency
    - Sentiment shift after failure
    """
    
    def analyze(
        self, 
        utterances: List[Utterance],
        speaker_stats: Dict[str, SpeakerStats]
    ) -> DimensionScore:
        positive = []
        negative = []
        patterns = []
        
        experiment_count = 0
        learning_loop_count = 0
        
        for u in utterances:
            markers = self.marker_detector.detect_all_markers(u.text)
            
            if markers.get("experiment_language"):
                experiment_count += 1
                positive.extend([f"Experiment: '{m}'" for m in markers["experiment_language"][:1]])
            
            if markers.get("learning_loop"):
                learning_loop_count += 1
                positive.extend([f"Learning loop: '{m}'" for m in markers["learning_loop"][:1]])
        
        total = len(utterances)
        if total > 0:
            experiment_density = experiment_count / total
            learning_density = learning_loop_count / total
            
            if experiment_density > 0.05:
                patterns.append(f"Experiment-oriented culture ({experiment_density:.1%})")
            
            if learning_density > 0.05:
                patterns.append(f"Active learning loops ({learning_density:.1%})")
            
            if experiment_density < 0.01 and learning_density < 0.01:
                patterns.append("Limited learning/experiment language detected")
        
        # Calculate score
        score = 3.0
        
        if total > 0:
            score += min(0.7, experiment_count / total * 10)
            score += min(0.7, learning_loop_count / total * 10)
        
        score = max(1.0, min(5.0, score))
        confidence = min(1.0, total / 100)
        
        return DimensionScore(
            dimension=Dimension.LEARNING_ADAPTATION,
            score=score,
            confidence=confidence,
            positive_indicators=list(set(positive))[:5],
            negative_indicators=list(set(negative))[:5],
            patterns_detected=patterns,
            explanation=f"{experiment_count} experiment refs, {learning_loop_count} learning loops"
        )


class EnergyEngagementAnalyzer(DimensionAnalyzer):
    """
    Dimension 5: Energie, betrokkenheid & betekenis
    
    Measures:
    - Prosody (pitch, tempo, volume variation)
    - Valence/emotional trends
    - Meaning markers
    - Celebration signals
    """
    
    def analyze(
        self, 
        utterances: List[Utterance],
        speaker_stats: Dict[str, SpeakerStats]
    ) -> DimensionScore:
        positive = []
        negative = []
        patterns = []
        
        meaning_count = 0
        celebration_count = 0
        
        # Collect audio features if available
        pitches = []
        energies = []
        
        for u in utterances:
            markers = self.marker_detector.detect_all_markers(u.text)
            
            if markers.get("meaning_markers"):
                meaning_count += 1
                positive.extend([f"Meaning: '{m}'" for m in markers["meaning_markers"][:1]])
            
            if markers.get("celebration_language"):
                celebration_count += 1
                positive.extend([f"Celebration: '{m}'" for m in markers["celebration_language"][:1]])
            
            # Collect audio features
            if u.pitch_mean is not None:
                pitches.append(u.pitch_mean)
            if u.energy_mean is not None:
                energies.append(u.energy_mean)
        
        total = len(utterances)
        
        # Analyze prosody if available
        has_audio = len(pitches) > 10
        if has_audio:
            import numpy as np
            pitch_variation = np.std(pitches)
            energy_variation = np.std(energies) if energies else 0
            
            if pitch_variation > 30:
                patterns.append(f"High pitch variation ({pitch_variation:.1f}Hz) - engaged")
            elif pitch_variation < 10:
                patterns.append(f"Low pitch variation ({pitch_variation:.1f}Hz) - may indicate low energy")
        
        if total > 0:
            meaning_density = meaning_count / total
            celebration_density = celebration_count / total
            
            if meaning_density > 0.05:
                patterns.append(f"Strong meaning references ({meaning_density:.1%})")
            
            if celebration_density > 0.02:
                patterns.append(f"Celebration culture present ({celebration_density:.1%})")
        
        # Calculate score
        score = 3.0
        
        if total > 0:
            score += min(0.5, meaning_count / total * 10)
            score += min(0.5, celebration_count / total * 20)
        
        # Audio-based adjustment
        if has_audio:
            import numpy as np
            if np.std(pitches) > 25:
                score += 0.3
        
        score = max(1.0, min(5.0, score))
        confidence = min(1.0, total / 100) * (1.2 if has_audio else 1.0)
        confidence = min(1.0, confidence)
        
        return DimensionScore(
            dimension=Dimension.ENERGY_ENGAGEMENT,
            score=score,
            confidence=confidence,
            positive_indicators=list(set(positive))[:5],
            negative_indicators=list(set(negative))[:5],
            patterns_detected=patterns,
            explanation=f"{meaning_count} meaning refs, {celebration_count} celebrations" + 
                       (f", audio analysis included" if has_audio else ", no audio data")
        )


class StructureReliabilityAnalyzer(DimensionAnalyzer):
    """
    Dimension 6: Structuur, helderheid & betrouwbaarheid van afspraken
    
    Note: This dimension is deliberately limited in linguistic analysis
    as execution/reliability cannot be fully derived from language alone.
    This is deepened in feedback sessions.
    
    Measures:
    - Decision language
    - Action/ownership statements
    - Open ends without owner/deadline
    - Repeated discussions on past decisions
    """
    
    def analyze(
        self, 
        utterances: List[Utterance],
        speaker_stats: Dict[str, SpeakerStats]
    ) -> DimensionScore:
        positive = []
        negative = []
        patterns = []
        
        decision_count = 0
        clarity_count = 0
        
        for u in utterances:
            markers = self.marker_detector.detect_all_markers(u.text)
            
            if markers.get("decision_language"):
                decision_count += 1
                positive.extend([f"Decision: '{m}'" for m in markers["decision_language"][:1]])
            
            if markers.get("clarity_language"):
                clarity_count += 1
                positive.extend([f"Clarity: '{m}'" for m in markers["clarity_language"][:1]])
        
        total = len(utterances)
        
        if total > 0:
            decision_density = decision_count / total
            
            if decision_density > 0.05:
                patterns.append(f"Clear decision-making language ({decision_density:.1%})")
            elif decision_density < 0.01:
                patterns.append("Low decision/action language")
        
        # This dimension has inherent limitations
        patterns.append("NOTE: Execution reliability requires feedback session validation")
        
        # Calculate score (with lower confidence due to limitations)
        score = 3.0
        
        if total > 0:
            score += min(0.5, decision_count / total * 10)
            score += min(0.3, clarity_count / total * 10)
        
        score = max(1.0, min(5.0, score))
        
        # Lower confidence for this dimension
        confidence = min(0.7, total / 150)  # Max 0.7 due to inherent limitations
        
        return DimensionScore(
            dimension=Dimension.STRUCTURE_RELIABILITY,
            score=score,
            confidence=confidence,
            positive_indicators=list(set(positive))[:5],
            negative_indicators=list(set(negative))[:5],
            patterns_detected=patterns,
            explanation=f"{decision_count} decisions, {clarity_count} clarity markers. Limited by linguistic analysis - validate in feedback session."
        )


# ============================================
# MAIN ANALYZER
# ============================================

class TeamDynamicsAnalyzer:
    """
    Main Team Dynamics Analyzer
    
    Implements the @TheBigFish methodology for analyzing
    High Performing Teams across 6 dimensions.
    """
    
    def __init__(self):
        self.marker_detector = MarkerDetector()
        self.quality_analyzer = InputQualityAnalyzer()
        
        # Dimension analyzers
        self.dimension_analyzers = {
            Dimension.PSYCHOLOGICAL_SAFETY: PsychologicalSafetyAnalyzer(),
            Dimension.COLLECTIVE_OWNERSHIP: CollectiveOwnershipAnalyzer(),
            Dimension.CONSTRUCTIVE_COLLABORATION: ConstructiveCollaborationAnalyzer(),
            Dimension.LEARNING_ADAPTATION: LearningAdaptationAnalyzer(),
            Dimension.ENERGY_ENGAGEMENT: EnergyEngagementAnalyzer(),
            Dimension.STRUCTURE_RELIABILITY: StructureReliabilityAnalyzer(),
        }
        
        logger.info("✅ Team Dynamics Analyzer initialized (6 dimensions)")
    
    def parse_transcript(
        self,
        transcript: str,
        speaker_pattern: Optional[str] = None
    ) -> List[Utterance]:
        """
        Parse a transcript into utterances.
        
        Supports formats like:
        - "Speaker Name: text"
        - "[Speaker] text"
        - "SPEAKER: text"
        """
        utterances = []
        
        # Try to detect speaker pattern
        patterns = [
            r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:\s*(.+)$',  # Name: text
            r'^\[([^\]]+)\]\s*(.+)$',  # [Speaker] text
            r'^([A-Z]+)\s*:\s*(.+)$',  # SPEAKER: text
        ]
        
        lines = transcript.strip().split('\n')
        current_speaker = "Unknown"
        utterance_id = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            speaker_found = False
            for pattern in patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    current_speaker = match.group(1)
                    text = match.group(2)
                    speaker_found = True
                    break
            
            if not speaker_found:
                text = line
            
            utterance_id += 1
            utterances.append(Utterance(
                id=f"u_{utterance_id}",
                speaker_id=current_speaker.lower().replace(" ", "_"),
                speaker_name=current_speaker,
                text=text
            ))
        
        return utterances
    
    def calculate_speaker_stats(
        self,
        utterances: List[Utterance]
    ) -> Dict[str, SpeakerStats]:
        """Calculate statistics per speaker"""
        stats = {}
        
        for u in utterances:
            if u.speaker_id not in stats:
                stats[u.speaker_id] = SpeakerStats(
                    speaker_id=u.speaker_id,
                    speaker_name=u.speaker_name
                )
            
            s = stats[u.speaker_id]
            s.total_utterances += 1
            s.total_words += len(u.text.split())
            s.total_speaking_time += u.timestamp_end - u.timestamp_start
            
            # Count markers
            markers = self.marker_detector.detect_all_markers(u.text)
            for marker_type, found in markers.items():
                s.marker_counts[marker_type] = s.marker_counts.get(marker_type, 0) + len(found)
            
            # Count pronouns
            pronouns = self.marker_detector.count_pronouns(u.text)
            s.we_count += pronouns["we"]
            s.i_count += pronouns["i"]
            s.they_count += pronouns["they"]
            
            # Count questions
            if "?" in u.text:
                s.questions_asked += 1
        
        return stats
    
    def analyze(
        self,
        utterances: List[Utterance],
        leader_id: Optional[str] = None
    ) -> TeamDynamicsResult:
        """
        Perform full team dynamics analysis.
        
        Args:
            utterances: List of parsed utterances
            leader_id: Optional speaker ID of the CEO/leader for specific analysis
            
        Returns:
            TeamDynamicsResult with scores for all 6 dimensions
        """
        import uuid
        import time
        
        start_time = time.time()
        
        result = TeamDynamicsResult(
            analysis_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now().isoformat(),
            input_quality=InputQualityReport(
                quality_level=InputQuality.INSUFFICIENT,
                quality_score=0
            )
        )
        
        # Analyze input quality
        result.input_quality = self.quality_analyzer.analyze(utterances)
        
        if not result.input_quality.meets_minimum_requirements:
            logger.warning("Input does not meet minimum requirements")
            result.processing_time_seconds = time.time() - start_time
            return result
        
        # Calculate speaker stats
        result.speaker_stats = self.calculate_speaker_stats(utterances)
        
        # Calculate dominance index
        if result.speaker_stats:
            word_counts = [s.total_words for s in result.speaker_stats.values()]
            total_words = sum(word_counts)
            if total_words > 0:
                max_words = max(word_counts)
                result.dominance_index = max_words / total_words
                
                # Interaction balance (how evenly distributed)
                n_speakers = len(word_counts)
                if n_speakers > 1:
                    expected = total_words / n_speakers
                    variance = sum((w - expected) ** 2 for w in word_counts) / n_speakers
                    result.interaction_balance = 1 - min(1, variance / (expected ** 2))
        
        # Analyze each dimension
        for dimension, analyzer in self.dimension_analyzers.items():
            try:
                score = analyzer.analyze(utterances, result.speaker_stats)
                result.dimension_scores[dimension.value] = score
            except Exception as e:
                logger.error(f"Error analyzing {dimension.value}: {e}")
        
        # Calculate team score (weighted average)
        if result.dimension_scores:
            weights = {
                Dimension.PSYCHOLOGICAL_SAFETY.value: 1.2,  # Most important
                Dimension.COLLECTIVE_OWNERSHIP.value: 1.0,
                Dimension.CONSTRUCTIVE_COLLABORATION.value: 1.0,
                Dimension.LEARNING_ADAPTATION.value: 1.0,
                Dimension.ENERGY_ENGAGEMENT.value: 0.8,
                Dimension.STRUCTURE_RELIABILITY.value: 0.8,  # Lower weight due to limitations
            }
            
            weighted_sum = 0
            weight_total = 0
            confidence_sum = 0
            
            for dim_name, score in result.dimension_scores.items():
                w = weights.get(dim_name, 1.0)
                weighted_sum += score.score * w * score.confidence
                weight_total += w * score.confidence
                confidence_sum += score.confidence
            
            if weight_total > 0:
                result.team_score = weighted_sum / weight_total
                result.team_score_confidence = confidence_sum / len(result.dimension_scores)
        
        # Collect top indicators
        all_indicators = []
        for score in result.dimension_scores.values():
            all_indicators.extend(score.positive_indicators)
            all_indicators.extend([f"⚠️ {i}" for i in score.negative_indicators])
        result.top_indicators = all_indicators[:10]
        
        # Leader-specific analysis
        if leader_id and leader_id in result.speaker_stats:
            leader_stats = result.speaker_stats[leader_id]
            result.leader_patterns = {
                "speaking_share": leader_stats.total_words / sum(s.total_words for s in result.speaker_stats.values()) if result.speaker_stats else 0,
                "questions_asked": leader_stats.questions_asked,
                "we_language_ratio": leader_stats.we_count / (leader_stats.we_count + leader_stats.i_count + leader_stats.they_count + 1),
                "vulnerability_signals": leader_stats.marker_counts.get("vulnerability", 0),
                "learning_frames": leader_stats.marker_counts.get("learning_frame", 0),
            }
        
        result.processing_time_seconds = time.time() - start_time
        
        logger.info(f"Team dynamics analysis complete: team score={result.team_score:.2f}, confidence={result.team_score_confidence:.2f}")
        
        return result
    
    def analyze_transcript(
        self,
        transcript: str,
        leader_name: Optional[str] = None
    ) -> TeamDynamicsResult:
        """
        Convenience method to analyze a raw transcript.
        
        Args:
            transcript: Raw meeting transcript
            leader_name: Optional name of CEO/leader in the transcript
            
        Returns:
            TeamDynamicsResult
        """
        utterances = self.parse_transcript(transcript)
        leader_id = leader_name.lower().replace(" ", "_") if leader_name else None
        return self.analyze(utterances, leader_id)


# ============================================
# GLOBAL INSTANCE
# ============================================

_team_dynamics_analyzer: Optional[TeamDynamicsAnalyzer] = None


def get_team_dynamics_analyzer() -> TeamDynamicsAnalyzer:
    """Get or create the team dynamics analyzer singleton"""
    global _team_dynamics_analyzer
    if _team_dynamics_analyzer is None:
        _team_dynamics_analyzer = TeamDynamicsAnalyzer()
    return _team_dynamics_analyzer


async def analyze_team_dynamics(
    transcript: str,
    leader_name: Optional[str] = None
) -> TeamDynamicsResult:
    """
    Analyze team dynamics from a meeting transcript.
    
    This is the main entry point for team dynamics analysis.
    
    Args:
        transcript: Meeting transcript (with speaker labels)
        leader_name: Optional name of the CEO/leader
        
    Returns:
        TeamDynamicsResult with scores for all 6 dimensions
    """
    analyzer = get_team_dynamics_analyzer()
    return analyzer.analyze_transcript(transcript, leader_name)
