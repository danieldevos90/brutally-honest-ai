"""
Comprehensive Analysis Module for Brutally Honest AI
Integrates all analysis capabilities for full-spectrum audio/transcript analysis

Features:
- Voice analysis (pitch, pace, pauses, energy)
- ML-based sentiment analysis
- Emotion detection (voice + text combined)
- Context-aware fact checking
- Quality metrics and scoring
- Speaker profiling
"""

import asyncio
import logging
import time
import os
import json
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AnalysisQuality(str, Enum):
    """Analysis quality levels"""
    EXCELLENT = "excellent"  # All features available, high confidence
    GOOD = "good"           # Most features, moderate confidence
    PARTIAL = "partial"     # Some features missing or low confidence
    BASIC = "basic"         # Only basic analysis available
    FAILED = "failed"       # Analysis failed


class Sentiment(str, Enum):
    """Sentiment categories"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"
    MIXED = "mixed"


class Emotion(str, Enum):
    """Emotion categories"""
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    FEARFUL = "fearful"
    SURPRISED = "surprised"
    DISGUSTED = "disgusted"
    CONFIDENT = "confident"
    ANXIOUS = "anxious"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    """Detailed sentiment analysis result"""
    overall: Sentiment
    confidence: float  # 0-1
    positivity_score: float  # -1 to 1
    subjectivity: float  # 0-1 (0=objective, 1=subjective)
    emotional_intensity: float  # 0-1
    
    # Breakdown by category
    positive_indicators: List[str] = field(default_factory=list)
    negative_indicators: List[str] = field(default_factory=list)
    
    # Sentence-level analysis
    sentence_sentiments: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall.value,
            "confidence": round(self.confidence, 3),
            "positivity_score": round(self.positivity_score, 3),
            "subjectivity": round(self.subjectivity, 3),
            "emotional_intensity": round(self.emotional_intensity, 3),
            "positive_indicators": self.positive_indicators,
            "negative_indicators": self.negative_indicators,
            "sentence_count": len(self.sentence_sentiments),
            "sentences": self.sentence_sentiments[:5]  # Top 5 for brevity
        }


@dataclass
class EmotionResult:
    """Emotion analysis result combining voice and text"""
    primary_emotion: Emotion
    secondary_emotion: Optional[Emotion] = None
    confidence: float = 0.0
    
    # Source breakdown
    voice_emotion: Optional[str] = None
    voice_confidence: float = 0.0
    text_emotion: Optional[str] = None
    text_confidence: float = 0.0
    
    # Emotion scores
    emotion_scores: Dict[str, float] = field(default_factory=dict)
    
    # Indicators
    indicators: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "primary_emotion": self.primary_emotion.value,
            "secondary_emotion": self.secondary_emotion.value if self.secondary_emotion else None,
            "confidence": round(self.confidence, 3),
            "voice_emotion": self.voice_emotion,
            "voice_confidence": round(self.voice_confidence, 3),
            "text_emotion": self.text_emotion,
            "text_confidence": round(self.text_confidence, 3),
            "emotion_scores": {k: round(v, 3) for k, v in self.emotion_scores.items()},
            "indicators": self.indicators[:5]
        }


@dataclass
class ContextAnalysis:
    """Context analysis result"""
    topics: List[str] = field(default_factory=list)
    entities: List[Dict[str, str]] = field(default_factory=list)  # {type, name, count}
    key_phrases: List[str] = field(default_factory=list)
    domain: str = "general"  # business, technical, casual, formal, etc.
    language: str = "unknown"
    formality_score: float = 0.5  # 0=informal, 1=formal
    
    # Related context from knowledge base
    related_documents: List[str] = field(default_factory=list)
    related_profiles: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topics": self.topics,
            "entities": self.entities,
            "key_phrases": self.key_phrases,
            "domain": self.domain,
            "language": self.language,
            "formality_score": round(self.formality_score, 3),
            "related_documents": self.related_documents[:5],
            "related_profiles": self.related_profiles[:5]
        }


@dataclass
class QualityMetrics:
    """Analysis quality metrics"""
    overall_quality: AnalysisQuality
    quality_score: float  # 0-100
    
    # Component availability
    transcription_available: bool = False
    voice_analysis_available: bool = False
    sentiment_analysis_available: bool = False
    emotion_analysis_available: bool = False
    fact_check_available: bool = False
    context_analysis_available: bool = False
    
    # Confidence scores
    transcription_confidence: float = 0.0
    voice_confidence: float = 0.0
    sentiment_confidence: float = 0.0
    overall_confidence: float = 0.0
    
    # Audio quality indicators
    audio_quality: str = "unknown"  # excellent, good, fair, poor
    speech_clarity: float = 0.0
    noise_level: float = 0.0
    
    # Issues detected
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_quality": self.overall_quality.value,
            "quality_score": round(self.quality_score, 1),
            "components": {
                "transcription": self.transcription_available,
                "voice_analysis": self.voice_analysis_available,
                "sentiment": self.sentiment_analysis_available,
                "emotion": self.emotion_analysis_available,
                "fact_check": self.fact_check_available,
                "context": self.context_analysis_available
            },
            "confidence": {
                "transcription": round(self.transcription_confidence, 3),
                "voice": round(self.voice_confidence, 3),
                "sentiment": round(self.sentiment_confidence, 3),
                "overall": round(self.overall_confidence, 3)
            },
            "audio": {
                "quality": self.audio_quality,
                "speech_clarity": round(self.speech_clarity, 3),
                "noise_level": round(self.noise_level, 3)
            },
            "issues": self.issues,
            "recommendations": self.recommendations
        }


@dataclass
class ComprehensiveAnalysisResult:
    """Complete analysis result with all components"""
    # Identification
    analysis_id: str
    timestamp: str
    processing_time_seconds: float
    
    # Core content
    transcription: str
    summary: Optional[str] = None
    
    # Analysis components
    sentiment: Optional[SentimentResult] = None
    emotion: Optional[EmotionResult] = None
    context: Optional[ContextAnalysis] = None
    voice_features: Optional[Dict[str, Any]] = None
    
    # Fact checking
    fact_check_result: Optional[Dict[str, Any]] = None
    credibility_score: float = 0.5
    
    # Quality
    quality: Optional[QualityMetrics] = None
    
    # Keywords and topics
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    
    # Speaker info
    speaker_count: int = 1
    speakers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Raw data for further processing
    raw_analysis: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp,
            "processing_time_seconds": round(self.processing_time_seconds, 2),
            "transcription": self.transcription,
            "summary": self.summary,
            "sentiment": self.sentiment.to_dict() if self.sentiment else None,
            "emotion": self.emotion.to_dict() if self.emotion else None,
            "context": self.context.to_dict() if self.context else None,
            "voice_features": self.voice_features,
            "fact_check": self.fact_check_result,
            "credibility_score": round(self.credibility_score, 3),
            "quality": self.quality.to_dict() if self.quality else None,
            "keywords": self.keywords,
            "topics": self.topics,
            "speaker_count": self.speaker_count,
            "speakers": self.speakers
        }


class AdvancedSentimentAnalyzer:
    """Advanced sentiment analysis using multiple methods"""
    
    # Expanded sentiment lexicons (Dutch + English)
    POSITIVE_WORDS = {
        # English
        "excellent", "amazing", "wonderful", "fantastic", "great", "good", "love", "loved",
        "happy", "pleased", "delighted", "satisfied", "excited", "thrilled", "quality",
        "perfect", "beautiful", "brilliant", "outstanding", "superb", "awesome",
        "impressive", "remarkable", "successful", "positive", "beneficial",
        "helpful", "valuable", "effective", "efficient", "innovative", "best",
        # Dutch
        "uitstekend", "geweldig", "fantastisch", "prachtig", "goed", "fijn",
        "blij", "tevreden", "enthousiast", "perfect", "mooi", "briljant",
        "succesvol", "positief", "waardevol", "effectief", "innovatief",
        "leuk", "gezellig", "prettig", "aangenaam"
    }
    
    NEGATIVE_WORDS = {
        # English
        "terrible", "awful", "horrible", "bad", "poor", "hate", "angry",
        "disappointed", "frustrated", "annoyed", "upset", "sad", "worried",
        "concerned", "problem", "issue", "fail", "failure", "wrong", "error",
        "difficult", "hard", "impossible", "never", "worst", "useless",
        "broken", "damaged", "lost", "missing", "delayed", "cancelled",
        # Dutch
        "verschrikkelijk", "vreselijk", "slecht", "teleurgesteld", "gefrustreerd",
        "boos", "verdrietig", "bezorgd", "probleem", "fout", "moeilijk",
        "onmogelijk", "nooit", "slechtste", "nutteloos", "kapot", "verloren",
        "vervelend", "lastig", "stom", "irritant"
    }
    
    INTENSIFIERS = {
        "very", "extremely", "incredibly", "absolutely", "completely", "totally",
        "really", "so", "quite", "rather", "particularly", "especially",
        "heel", "erg", "zeer", "ontzettend", "absoluut", "volledig"
    }
    
    NEGATORS = {
        "not", "no", "never", "neither", "none", "nothing", "nobody",
        "nowhere", "hardly", "barely", "scarcely", "seldom",
        "niet", "geen", "nooit", "nergens", "nauwelijks"
    }
    
    def __init__(self):
        self.transformer_model = None
        self._load_transformer_model()
    
    def _load_transformer_model(self):
        """Try to load transformer-based sentiment model"""
        try:
            from transformers import pipeline
            # Use multilingual sentiment model
            self.transformer_model = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                top_k=None
            )
            logger.info("✅ Transformer sentiment model loaded")
        except Exception as e:
            logger.warning(f"Transformer model not available, using lexicon-based: {e}")
            self.transformer_model = None
    
    async def analyze(self, text: str) -> SentimentResult:
        """Perform comprehensive sentiment analysis"""
        if not text or not text.strip():
            return SentimentResult(
                overall=Sentiment.NEUTRAL,
                confidence=0.0,
                positivity_score=0.0,
                subjectivity=0.0,
                emotional_intensity=0.0
            )
        
        # Split into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Analyze each sentence
        sentence_results = []
        for sentence in sentences:
            result = await self._analyze_sentence(sentence)
            sentence_results.append(result)
        
        # Aggregate results
        return self._aggregate_results(sentence_results, text)
    
    async def _analyze_sentence(self, sentence: str) -> Dict[str, Any]:
        """Analyze a single sentence"""
        words = sentence.lower().split()
        
        # Lexicon-based analysis
        positive_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
        negative_count = sum(1 for w in words if w in self.NEGATIVE_WORDS)
        intensifier_count = sum(1 for w in words if w in self.INTENSIFIERS)
        negator_count = sum(1 for w in words if w in self.NEGATORS)
        
        # Adjust for negators
        if negator_count % 2 == 1:  # Odd number of negators flips sentiment
            positive_count, negative_count = negative_count, positive_count
        
        # Apply intensifiers
        intensity = 1.0 + (intensifier_count * 0.3)
        
        # Calculate scores
        total_sentiment_words = positive_count + negative_count
        if total_sentiment_words > 0:
            positivity = ((positive_count - negative_count) / total_sentiment_words) * intensity
            confidence = min(1.0, total_sentiment_words / len(words) if words else 0)
        else:
            positivity = 0.0
            confidence = 0.3
        
        # Determine sentiment
        if positivity > 0.5:
            sentiment = "very_positive"
        elif positivity > 0.1:
            sentiment = "positive"
        elif positivity < -0.5:
            sentiment = "very_negative"
        elif positivity < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Get transformer prediction if available
        transformer_result = None
        if self.transformer_model:
            try:
                result = self.transformer_model(sentence[:512])  # Max 512 chars
                if result:
                    transformer_result = result[0]
            except Exception as e:
                logger.debug(f"Transformer analysis failed: {e}")
        
        return {
            "sentence": sentence,
            "sentiment": sentiment,
            "positivity": positivity,
            "confidence": confidence,
            "intensity": intensity,
            "positive_words": positive_count,
            "negative_words": negative_count,
            "transformer_result": transformer_result
        }
    
    def _aggregate_results(
        self, 
        sentence_results: List[Dict[str, Any]], 
        full_text: str
    ) -> SentimentResult:
        """Aggregate sentence-level results"""
        if not sentence_results:
            return SentimentResult(
                overall=Sentiment.NEUTRAL,
                confidence=0.0,
                positivity_score=0.0,
                subjectivity=0.0,
                emotional_intensity=0.0
            )
        
        # Calculate aggregates
        positivity_scores = [r["positivity"] for r in sentence_results]
        confidence_scores = [r["confidence"] for r in sentence_results]
        intensities = [r["intensity"] for r in sentence_results]
        
        avg_positivity = sum(positivity_scores) / len(positivity_scores)
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        avg_intensity = sum(intensities) / len(intensities)
        
        # Check for mixed sentiment
        has_positive = any(r["sentiment"] in ["positive", "very_positive"] for r in sentence_results)
        has_negative = any(r["sentiment"] in ["negative", "very_negative"] for r in sentence_results)
        
        # Determine overall sentiment
        if has_positive and has_negative:
            overall = Sentiment.MIXED
        elif avg_positivity > 0.5:
            overall = Sentiment.VERY_POSITIVE
        elif avg_positivity > 0.1:
            overall = Sentiment.POSITIVE
        elif avg_positivity < -0.5:
            overall = Sentiment.VERY_NEGATIVE
        elif avg_positivity < -0.1:
            overall = Sentiment.NEGATIVE
        else:
            overall = Sentiment.NEUTRAL
        
        # Collect indicators
        positive_indicators = []
        negative_indicators = []
        for word in full_text.lower().split():
            if word in self.POSITIVE_WORDS:
                positive_indicators.append(word)
            elif word in self.NEGATIVE_WORDS:
                negative_indicators.append(word)
        
        # Estimate subjectivity (more sentiment words = more subjective)
        word_count = len(full_text.split())
        sentiment_density = (len(positive_indicators) + len(negative_indicators)) / word_count if word_count > 0 else 0
        subjectivity = min(1.0, sentiment_density * 5)  # Scale up
        
        return SentimentResult(
            overall=overall,
            confidence=avg_confidence,
            positivity_score=avg_positivity,
            subjectivity=subjectivity,
            emotional_intensity=avg_intensity - 1.0,  # Normalize intensity
            positive_indicators=list(set(positive_indicators))[:10],
            negative_indicators=list(set(negative_indicators))[:10],
            sentence_sentiments=[
                {"sentence": r["sentence"][:100], "sentiment": r["sentiment"], "score": r["positivity"]}
                for r in sentence_results[:10]
            ]
        )


class EmotionAnalyzer:
    """Emotion analysis combining voice and text cues"""
    
    # Emotion patterns in text
    EMOTION_PATTERNS = {
        Emotion.HAPPY: {
            "words": ["happy", "joy", "delighted", "pleased", "cheerful", "blij", "vrolijk", "gelukkig"],
            "phrases": ["so happy", "really pleased", "love it", "heel blij", "erg tevreden"],
            "voice_indicators": {"high_pitch": True, "high_energy": True, "fast_pace": True}
        },
        Emotion.SAD: {
            "words": ["sad", "unhappy", "disappointed", "upset", "verdrietig", "teleurgesteld"],
            "phrases": ["feel bad", "so sad", "unfortunately", "helaas", "jammer"],
            "voice_indicators": {"low_pitch": True, "low_energy": True, "slow_pace": True}
        },
        Emotion.ANGRY: {
            "words": ["angry", "furious", "annoyed", "frustrated", "boos", "kwaad", "geïrriteerd"],
            "phrases": ["so angry", "can't believe", "ridiculous", "onacceptabel"],
            "voice_indicators": {"high_pitch": True, "high_energy": True, "fast_pace": True}
        },
        Emotion.FEARFUL: {
            "words": ["afraid", "scared", "worried", "anxious", "nervous", "bang", "ongerust"],
            "phrases": ["scared that", "worried about", "what if", "bezorgd over"],
            "voice_indicators": {"high_pitch": True, "varied_pitch": True, "hesitant": True}
        },
        Emotion.SURPRISED: {
            "words": ["surprised", "shocked", "amazed", "astonished", "verrast", "verbaasd"],
            "phrases": ["can't believe", "didn't expect", "wow", "wauw"],
            "voice_indicators": {"pitch_spike": True, "energy_spike": True}
        },
        Emotion.CONFIDENT: {
            "words": ["confident", "certain", "sure", "definitely", "clearly", "zeker", "duidelijk"],
            "phrases": ["i'm sure", "no doubt", "definitely", "absoluut"],
            "voice_indicators": {"steady_pitch": True, "moderate_energy": True, "steady_pace": True}
        },
        Emotion.ANXIOUS: {
            "words": ["anxious", "stressed", "tense", "uneasy", "gestrest", "gespannen"],
            "phrases": ["stress", "pressure", "deadline", "worried about"],
            "voice_indicators": {"high_pitch": True, "fast_pace": True, "many_pauses": True}
        },
        Emotion.EXCITED: {
            "words": ["excited", "thrilled", "eager", "enthusiastic", "enthousiast", "opgewonden"],
            "phrases": ["can't wait", "so excited", "looking forward"],
            "voice_indicators": {"high_pitch": True, "high_energy": True, "fast_pace": True}
        },
        Emotion.FRUSTRATED: {
            "words": ["frustrated", "stuck", "blocked", "difficult", "gefrustreerd", "moeilijk"],
            "phrases": ["so frustrating", "doesn't work", "can't figure out"],
            "voice_indicators": {"varied_pitch": True, "high_energy": True, "many_pauses": True}
        }
    }
    
    async def analyze(
        self, 
        text: str, 
        voice_features: Optional[Dict[str, Any]] = None
    ) -> EmotionResult:
        """Analyze emotions from text and optional voice features"""
        
        text_emotions = await self._analyze_text_emotions(text)
        voice_emotions = self._analyze_voice_emotions(voice_features) if voice_features else {}
        
        # Combine results
        return self._combine_emotions(text_emotions, voice_emotions)
    
    async def _analyze_text_emotions(self, text: str) -> Dict[Emotion, float]:
        """Analyze emotions from text"""
        text_lower = text.lower()
        emotion_scores = {e: 0.0 for e in Emotion}
        
        for emotion, patterns in self.EMOTION_PATTERNS.items():
            score = 0.0
            
            # Check words
            for word in patterns.get("words", []):
                if word in text_lower:
                    score += 0.3
            
            # Check phrases
            for phrase in patterns.get("phrases", []):
                if phrase in text_lower:
                    score += 0.5
            
            emotion_scores[emotion] = min(1.0, score)
        
        # Normalize if any scores
        max_score = max(emotion_scores.values())
        if max_score > 0:
            for emotion in emotion_scores:
                emotion_scores[emotion] /= max_score
        
        return emotion_scores
    
    def _analyze_voice_emotions(self, voice_features: Dict[str, Any]) -> Dict[Emotion, float]:
        """Analyze emotions from voice features"""
        voice_emotions = {e: 0.0 for e in Emotion}
        
        pitch_mean = voice_features.get("pitch_mean_hz", 0)
        pitch_std = voice_features.get("pitch_std_hz", 0)
        energy_mean = voice_features.get("energy_mean", 0)
        speaking_rate = voice_features.get("speaking_rate_wpm", 0)
        pause_ratio = voice_features.get("pause_ratio", 0)
        confidence_score = voice_features.get("confidence_score", 0.5)
        stress_indicator = voice_features.get("stress_indicator", 0.5)
        
        # Infer emotions from voice characteristics
        
        # High stress + high pitch = anxious or angry
        if stress_indicator > 0.7 and pitch_mean > 180:
            voice_emotions[Emotion.ANXIOUS] = stress_indicator
            voice_emotions[Emotion.ANGRY] = stress_indicator * 0.5
        
        # High confidence + moderate energy = confident
        if confidence_score > 0.7:
            voice_emotions[Emotion.CONFIDENT] = confidence_score
        
        # Low energy + low pitch = sad
        if energy_mean < -20 and pitch_mean < 150:
            voice_emotions[Emotion.SAD] = 0.7
        
        # High energy + high pitch + fast pace = excited or happy
        if energy_mean > -10 and pitch_mean > 170 and speaking_rate > 150:
            voice_emotions[Emotion.EXCITED] = 0.7
            voice_emotions[Emotion.HAPPY] = 0.6
        
        # Many pauses + varied pitch = frustrated or uncertain
        if pause_ratio > 0.25 and pitch_std > 40:
            voice_emotions[Emotion.FRUSTRATED] = 0.6
        
        return voice_emotions
    
    def _combine_emotions(
        self, 
        text_emotions: Dict[Emotion, float], 
        voice_emotions: Dict[Emotion, float]
    ) -> EmotionResult:
        """Combine text and voice emotion analysis"""
        
        # Weight: text 60%, voice 40% (text is more reliable)
        combined = {}
        for emotion in Emotion:
            text_score = text_emotions.get(emotion, 0.0)
            voice_score = voice_emotions.get(emotion, 0.0)
            combined[emotion] = text_score * 0.6 + voice_score * 0.4
        
        # Find primary and secondary emotions
        sorted_emotions = sorted(combined.items(), key=lambda x: x[1], reverse=True)
        
        primary = sorted_emotions[0][0] if sorted_emotions[0][1] > 0 else Emotion.NEUTRAL
        primary_score = sorted_emotions[0][1]
        
        secondary = None
        secondary_score = 0.0
        if len(sorted_emotions) > 1 and sorted_emotions[1][1] > 0.3:
            secondary = sorted_emotions[1][0]
            secondary_score = sorted_emotions[1][1]
        
        # Get best text and voice emotions
        text_best = max(text_emotions.items(), key=lambda x: x[1])
        voice_best = max(voice_emotions.items(), key=lambda x: x[1]) if voice_emotions else (Emotion.NEUTRAL, 0.0)
        
        # Collect indicators
        indicators = []
        if primary_score > 0:
            indicators.append(f"Primary: {primary.value} ({primary_score:.2f})")
        if secondary and secondary_score > 0:
            indicators.append(f"Secondary: {secondary.value} ({secondary_score:.2f})")
        if text_best[1] > 0:
            indicators.append(f"Text suggests: {text_best[0].value}")
        if voice_best[1] > 0:
            indicators.append(f"Voice suggests: {voice_best[0].value}")
        
        return EmotionResult(
            primary_emotion=primary,
            secondary_emotion=secondary,
            confidence=primary_score,
            voice_emotion=voice_best[0].value if voice_best[1] > 0 else None,
            voice_confidence=voice_best[1],
            text_emotion=text_best[0].value if text_best[1] > 0 else None,
            text_confidence=text_best[1],
            emotion_scores={e.value: s for e, s in combined.items() if s > 0},
            indicators=indicators
        )


class ContextAnalyzer:
    """Context and topic analysis"""
    
    def __init__(self):
        self.domain_keywords = {
            "business": {"revenue", "profit", "market", "sales", "customer", "client", "strategy",
                        "omzet", "winst", "markt", "verkoop", "klant", "strategie"},
            "technical": {"system", "software", "data", "api", "code", "algorithm", "database",
                         "systeem", "technisch", "gegevens", "programmeren"},
            "legal": {"contract", "agreement", "law", "compliance", "rights", "terms",
                     "overeenkomst", "wet", "rechten", "voorwaarden"},
            "medical": {"health", "patient", "treatment", "diagnosis", "symptoms",
                       "gezondheid", "patiënt", "behandeling", "diagnose"},
            "financial": {"investment", "budget", "cost", "expense", "financial", "capital",
                         "investering", "kosten", "financieel", "kapitaal"},
            "hr": {"employee", "team", "performance", "hire", "talent", "culture",
                  "medewerker", "prestatie", "talentmanagement", "cultuur"}
        }
        
        self.formality_formal = {"therefore", "consequently", "furthermore", "hereby", "regarding",
                                "derhalve", "hierbij", "betreffende"}
        self.formality_informal = {"gonna", "wanna", "kinda", "yeah", "okay", "cool", "awesome",
                                   "beetje", "gewoon", "echt", "super", "tof"}
    
    async def analyze(self, text: str) -> ContextAnalysis:
        """Analyze context and topics from text"""
        words = text.lower().split()
        
        # Detect domain
        domain = await self._detect_domain(words)
        
        # Extract topics
        topics = await self._extract_topics(text)
        
        # Extract entities
        entities = await self._extract_entities(text)
        
        # Extract key phrases
        key_phrases = await self._extract_key_phrases(text)
        
        # Detect language
        language = self._detect_language(text)
        
        # Analyze formality
        formality = self._analyze_formality(words)
        
        return ContextAnalysis(
            topics=topics,
            entities=entities,
            key_phrases=key_phrases,
            domain=domain,
            language=language,
            formality_score=formality
        )
    
    async def _detect_domain(self, words: List[str]) -> str:
        """Detect the domain/context of the text"""
        domain_scores = {}
        words_set = set(words)
        
        for domain, keywords in self.domain_keywords.items():
            score = len(words_set & keywords)
            domain_scores[domain] = score
        
        if not domain_scores:
            return "general"
        
        best_domain = max(domain_scores, key=domain_scores.get)
        return best_domain if domain_scores[best_domain] > 0 else "general"
    
    async def _extract_topics(self, text: str) -> List[str]:
        """Extract main topics from text"""
        # Simple frequency-based topic extraction
        import re
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Filter common words
        stopwords = {"this", "that", "with", "from", "have", "been", "were", "they",
                    "their", "what", "when", "where", "which", "would", "could",
                    "should", "there", "these", "those", "about", "into", "your",
                    "also", "just", "very", "some", "more", "than", "then"}
        
        words = [w for w in words if w not in stopwords]
        
        # Count frequencies
        from collections import Counter
        word_counts = Counter(words)
        
        # Return top topics
        return [word for word, count in word_counts.most_common(5)]
    
    async def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract named entities from text"""
        entities = []
        
        # Simple pattern-based entity extraction
        import re
        
        # Numbers (potential quantities, amounts)
        numbers = re.findall(r'\b\d+(?:[.,]\d+)?(?:\s*(?:euro|dollar|%|percent|miljoen|billion|million))?\b', text, re.IGNORECASE)
        for num in numbers[:5]:
            entities.append({"type": "number", "name": num.strip(), "count": 1})
        
        # Capitalized words (potential names, organizations)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        unique_names = list(set(capitalized))[:5]
        for name in unique_names:
            if len(name) > 2:
                entities.append({"type": "name", "name": name, "count": capitalized.count(name)})
        
        return entities
    
    async def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        import re
        
        # Extract noun phrases (simplified)
        # Look for adjective + noun patterns
        phrases = re.findall(r'\b(?:very |really |extremely )?[a-zA-Z]+(?:ly)?\s+[a-zA-Z]+(?:s|tion|ment|ness)?\b', text.lower())
        
        # Filter and deduplicate
        unique_phrases = list(set(phrases))[:10]
        
        return unique_phrases
    
    def _detect_language(self, text: str) -> str:
        """Detect the language of the text"""
        dutch_words = {"de", "het", "een", "van", "en", "is", "dat", "op", "voor", "zijn", "met"}
        english_words = {"the", "a", "an", "of", "and", "is", "that", "on", "for", "are", "with"}
        german_words = {"der", "die", "das", "und", "ist", "für", "mit", "auf"}
        
        words = set(text.lower().split())
        
        dutch_count = len(words & dutch_words)
        english_count = len(words & english_words)
        german_count = len(words & german_words)
        
        if dutch_count > english_count and dutch_count > german_count:
            return "dutch"
        elif german_count > english_count:
            return "german"
        else:
            return "english"
    
    def _analyze_formality(self, words: List[str]) -> float:
        """Analyze formality level (0=informal, 1=formal)"""
        words_set = set(words)
        formal_count = len(words_set & self.formality_formal)
        informal_count = len(words_set & self.formality_informal)
        
        total = formal_count + informal_count
        if total == 0:
            return 0.5  # Neutral
        
        return formal_count / total


class ComprehensiveAnalyzer:
    """Main comprehensive analyzer that orchestrates all analysis components"""
    
    def __init__(self):
        self.sentiment_analyzer = AdvancedSentimentAnalyzer()
        self.emotion_analyzer = EmotionAnalyzer()
        self.context_analyzer = ContextAnalyzer()
        
        # Voice analyzer (imported from audio module)
        self.voice_analyzer = None
        self._init_voice_analyzer()
        
        # Fact checker
        self.fact_checker = None
        
        logger.info("✅ Comprehensive analyzer initialized")
    
    def _init_voice_analyzer(self):
        """Initialize voice analyzer if available"""
        try:
            from audio.voice_analyzer import get_voice_analyzer
            self.voice_analyzer = get_voice_analyzer()
            logger.info("✅ Voice analyzer loaded")
        except Exception as e:
            logger.warning(f"Voice analyzer not available: {e}")
    
    async def analyze(
        self,
        transcription: str,
        audio_path: Optional[str] = None,
        audio_data: Optional[bytes] = None,
        include_fact_check: bool = True,
        brand_id: Optional[str] = None,
        client_id: Optional[str] = None,
        person_id: Optional[str] = None
    ) -> ComprehensiveAnalysisResult:
        """
        Perform comprehensive analysis on transcription and optional audio
        
        Args:
            transcription: Text transcription to analyze
            audio_path: Optional path to audio file for voice analysis
            audio_data: Optional raw audio bytes
            include_fact_check: Whether to include fact checking
            brand_id: Optional brand profile for context
            client_id: Optional client profile for context
            person_id: Optional person profile for context
            
        Returns:
            ComprehensiveAnalysisResult with all analysis components
        """
        import uuid
        start_time = time.time()
        
        analysis_id = str(uuid.uuid4())[:8]
        
        # Initialize result
        result = ComprehensiveAnalysisResult(
            analysis_id=analysis_id,
            timestamp=datetime.now().isoformat(),
            processing_time_seconds=0,
            transcription=transcription
        )
        
        quality = QualityMetrics(
            overall_quality=AnalysisQuality.BASIC,
            quality_score=0
        )
        
        issues = []
        recommendations = []
        components_available = 0
        confidence_sum = 0.0
        
        # 1. Sentiment Analysis
        try:
            sentiment = await self.sentiment_analyzer.analyze(transcription)
            result.sentiment = sentiment
            quality.sentiment_analysis_available = True
            quality.sentiment_confidence = sentiment.confidence
            components_available += 1
            confidence_sum += sentiment.confidence
            logger.info(f"Sentiment: {sentiment.overall.value} ({sentiment.confidence:.2f})")
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            issues.append(f"Sentiment analysis failed: {str(e)}")
        
        # 2. Voice Analysis (if audio available)
        voice_features = None
        if audio_path or audio_data:
            try:
                # Save audio_data to temp file if needed
                temp_path = audio_path
                if audio_data and not audio_path:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as f:
                        f.write(audio_data)
                        temp_path = f.name
                
                if self.voice_analyzer and temp_path:
                    features = await self.voice_analyzer.analyze_audio(
                        temp_path,
                        transcript=transcription
                    )
                    voice_features = features.to_dict()
                    result.voice_features = voice_features
                    quality.voice_analysis_available = True
                    quality.voice_confidence = features.confidence_score
                    components_available += 1
                    confidence_sum += features.confidence_score
                    
                    # Assess audio quality
                    if features.energy_mean > -10:
                        quality.audio_quality = "excellent"
                    elif features.energy_mean > -20:
                        quality.audio_quality = "good"
                    elif features.energy_mean > -30:
                        quality.audio_quality = "fair"
                    else:
                        quality.audio_quality = "poor"
                        issues.append("Low audio quality detected")
                    
                    quality.speech_clarity = features.confidence_score
                    
                    logger.info(f"Voice: pitch={features.pitch_mean_hz:.1f}Hz, rate={features.speaking_rate_wpm:.0f}wpm")
                
                # Cleanup temp file
                if audio_data and not audio_path and temp_path:
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                        
            except Exception as e:
                logger.error(f"Voice analysis failed: {e}")
                issues.append(f"Voice analysis failed: {str(e)}")
        else:
            recommendations.append("Provide audio file for voice analysis")
        
        # 3. Emotion Analysis (combining voice + text)
        try:
            emotion = await self.emotion_analyzer.analyze(transcription, voice_features)
            result.emotion = emotion
            quality.emotion_analysis_available = True
            components_available += 1
            confidence_sum += emotion.confidence
            logger.info(f"Emotion: {emotion.primary_emotion.value} ({emotion.confidence:.2f})")
        except Exception as e:
            logger.error(f"Emotion analysis failed: {e}")
            issues.append(f"Emotion analysis failed: {str(e)}")
        
        # 4. Context Analysis
        try:
            context = await self.context_analyzer.analyze(transcription)
            result.context = context
            result.topics = context.topics
            result.keywords = context.key_phrases[:10]
            quality.context_analysis_available = True
            components_available += 1
            logger.info(f"Context: domain={context.domain}, language={context.language}")
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            issues.append(f"Context analysis failed: {str(e)}")
        
        # 5. Fact Checking
        if include_fact_check:
            try:
                from ai.llama_processor import extract_and_check_claims
                
                fact_result = extract_and_check_claims(
                    transcription,
                    use_ai=True,
                    brand_id=brand_id,
                    client_id=client_id,
                    person_id=person_id
                )
                
                result.fact_check_result = fact_result
                result.credibility_score = fact_result.get("credibility", 0.5)
                quality.fact_check_available = True
                components_available += 1
                
                if fact_result.get("ai_powered"):
                    logger.info(f"Fact check: {fact_result.get('total', 0)} claims, credibility={result.credibility_score:.2f}")
                else:
                    recommendations.append("Enable AI-powered fact checking for better results")
                    
            except Exception as e:
                logger.warning(f"Fact checking failed: {e}")
                issues.append(f"Fact checking unavailable: {str(e)}")
        
        # 6. Generate Summary
        try:
            result.summary = self._generate_summary(result)
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
        
        # Calculate quality metrics
        quality.transcription_available = bool(transcription)
        quality.transcription_confidence = 0.9 if transcription else 0.0
        components_available += 1 if transcription else 0
        confidence_sum += quality.transcription_confidence
        
        # Overall confidence
        if components_available > 0:
            quality.overall_confidence = confidence_sum / components_available
        
        # Quality score (0-100)
        max_components = 6  # transcription, sentiment, voice, emotion, context, fact-check
        quality.quality_score = (components_available / max_components) * 100 * quality.overall_confidence
        
        # Determine quality level
        if quality.quality_score >= 80:
            quality.overall_quality = AnalysisQuality.EXCELLENT
        elif quality.quality_score >= 60:
            quality.overall_quality = AnalysisQuality.GOOD
        elif quality.quality_score >= 40:
            quality.overall_quality = AnalysisQuality.PARTIAL
        else:
            quality.overall_quality = AnalysisQuality.BASIC
        
        quality.issues = issues
        quality.recommendations = recommendations
        result.quality = quality
        
        # Processing time
        result.processing_time_seconds = time.time() - start_time
        
        logger.info(f"Analysis complete: quality={quality.overall_quality.value} ({quality.quality_score:.1f}), time={result.processing_time_seconds:.2f}s")
        
        return result
    
    def _generate_summary(self, result: ComprehensiveAnalysisResult) -> str:
        """Generate a brief summary of the analysis"""
        parts = []
        
        # Sentiment summary
        if result.sentiment:
            parts.append(f"Sentiment: {result.sentiment.overall.value}")
        
        # Emotion summary
        if result.emotion:
            parts.append(f"Emotion: {result.emotion.primary_emotion.value}")
        
        # Context summary
        if result.context:
            parts.append(f"Domain: {result.context.domain}")
            if result.context.topics:
                parts.append(f"Topics: {', '.join(result.context.topics[:3])}")
        
        # Credibility
        if result.credibility_score:
            parts.append(f"Credibility: {result.credibility_score:.0%}")
        
        return " | ".join(parts) if parts else "Analysis complete"


# Global instance
_comprehensive_analyzer: Optional[ComprehensiveAnalyzer] = None


def get_comprehensive_analyzer() -> ComprehensiveAnalyzer:
    """Get or create the comprehensive analyzer singleton"""
    global _comprehensive_analyzer
    if _comprehensive_analyzer is None:
        _comprehensive_analyzer = ComprehensiveAnalyzer()
    return _comprehensive_analyzer


async def analyze_recording(
    transcription: str,
    audio_path: Optional[str] = None,
    audio_data: Optional[bytes] = None,
    include_fact_check: bool = True,
    brand_id: Optional[str] = None,
    client_id: Optional[str] = None,
    person_id: Optional[str] = None
) -> ComprehensiveAnalysisResult:
    """
    Convenience function to analyze a recording
    
    This is the main entry point for comprehensive analysis.
    """
    analyzer = get_comprehensive_analyzer()
    return await analyzer.analyze(
        transcription=transcription,
        audio_path=audio_path,
        audio_data=audio_data,
        include_fact_check=include_fact_check,
        brand_id=brand_id,
        client_id=client_id,
        person_id=person_id
    )
