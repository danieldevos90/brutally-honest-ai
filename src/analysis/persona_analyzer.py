"""
Persona Analyzer - Extracts personality traits and communication style from speech

Instead of just fact-checking, this analyzes:
- Communication style (analytical, assertive, collaborative, expressive)
- Values and beliefs (extracted from "I believe" statements)
- Speech patterns (I vs We focus, confidence indicators)
- Personality traits for interview/conversation analysis
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class CommunicationStyle(Enum):
    ANALYTICAL = "analytical"      # Data-focused, logical
    ASSERTIVE = "assertive"        # Confident, action-oriented
    COLLABORATIVE = "collaborative" # Team-focused, inclusive
    EXPRESSIVE = "expressive"      # Emotional, values-driven


@dataclass
class PersonaProfile:
    """Complete persona profile extracted from speech"""
    name: str = "Unknown Speaker"
    
    # Communication Style Scores (0-1)
    assertiveness: float = 0.0
    collaboration: float = 0.0
    analytical: float = 0.0
    expressive: float = 0.0
    
    # Speech Pattern Counts
    i_statements: int = 0
    we_statements: int = 0
    belief_statements: int = 0
    certainty_words: int = 0
    hedging_words: int = 0
    
    # Extracted Content
    stated_values: List[str] = field(default_factory=list)
    key_themes: List[str] = field(default_factory=list)
    quantitative_claims: List[str] = field(default_factory=list)
    
    # Derived Insights
    primary_style: Optional[CommunicationStyle] = None
    focus_type: str = "balanced"  # self-focused, team-focused, balanced
    confidence_level: str = "moderate"  # high, moderate, low


class PersonaAnalyzer:
    """
    Analyzes speech/transcription to build personality profiles.
    
    Key insight: "I believe" statements reveal VALUES, not just opinions.
    """
    
    # Marker patterns for classification
    BELIEF_MARKERS = [
        "i believe", "i think", "i feel", "in my opinion", 
        "i value", "i care about", "what matters to me"
    ]
    
    ASSERTIVE_MARKERS = [
        "i will", "i am confident", "i can", "i achieved",
        "i led", "i drove", "i delivered", "definitely", "absolutely"
    ]
    
    COLLABORATIVE_MARKERS = [
        "we ", "our ", "team", "together", "collaborate",
        "partnership", "collectively", "shared"
    ]
    
    ANALYTICAL_MARKERS = [
        "data", "percent", "number", "metric", "measure",
        "analysis", "evidence", "research", "%", "roi"
    ]
    
    EXPRESSIVE_MARKERS = [
        "passionate", "love", "excited", "feel strongly",
        "care deeply", "believe strongly", "important to me"
    ]
    
    HEDGING_MARKERS = [
        "maybe", "perhaps", "might", "possibly", "i guess",
        "kind of", "sort of", "probably"
    ]
    
    CERTAINTY_MARKERS = [
        "definitely", "absolutely", "certainly", "confident",
        "sure", "clearly", "obviously", "undoubtedly"
    ]
    
    THEME_KEYWORDS = {
        "leadership": ["led", "managed", "directed", "leadership", "headed"],
        "data-driven": ["data", "metric", "analytics", "measure", "kpi"],
        "innovation": ["creative", "innovation", "new", "novel", "solution"],
        "growth": ["growth", "increase", "scale", "expand", "improve"],
        "collaboration": ["team", "together", "collaborate", "partner"],
        "customer-focus": ["customer", "client", "user", "service"],
        "results-oriented": ["achieved", "delivered", "accomplished", "results"],
        "strategic": ["strategy", "strategic", "vision", "long-term"],
    }
    
    def __init__(self):
        logger.info("PersonaAnalyzer initialized")
    
    def analyze(self, text: str, speaker_name: Optional[str] = None) -> PersonaProfile:
        """
        Analyze text and build comprehensive persona profile.
        
        Args:
            text: Transcription or speech text
            speaker_name: Optional known speaker name
            
        Returns:
            PersonaProfile with all extracted traits
        """
        text_lower = text.lower()
        sentences = self._split_sentences(text)
        
        profile = PersonaProfile()
        
        # Extract or detect speaker name
        profile.name = speaker_name or self._extract_name(text) or "Unknown Speaker"
        
        # Count speech patterns
        profile.i_statements = len(re.findall(r"\bi [a-z]+", text_lower))
        profile.we_statements = len(re.findall(r"\bwe [a-z]+", text_lower))
        profile.belief_statements = self._count_markers(text_lower, self.BELIEF_MARKERS)
        profile.certainty_words = self._count_markers(text_lower, self.CERTAINTY_MARKERS)
        profile.hedging_words = self._count_markers(text_lower, self.HEDGING_MARKERS)
        
        # Extract values from belief statements
        profile.stated_values = self._extract_values(sentences)
        
        # Extract quantitative claims
        profile.quantitative_claims = self._extract_quantitative(sentences)
        
        # Calculate style scores
        total = len(sentences) or 1
        profile.assertiveness = min(1.0, self._count_markers(text_lower, self.ASSERTIVE_MARKERS) / total * 1.5)
        profile.collaboration = min(1.0, self._count_markers(text_lower, self.COLLABORATIVE_MARKERS) / total * 1.5)
        profile.analytical = min(1.0, self._count_markers(text_lower, self.ANALYTICAL_MARKERS) / total * 1.5)
        profile.expressive = min(1.0, self._count_markers(text_lower, self.EXPRESSIVE_MARKERS) / total * 1.5)
        
        # Extract themes
        profile.key_themes = self._extract_themes(text_lower)
        
        # Determine primary style
        profile.primary_style = self._determine_style(profile)
        
        # Determine focus type
        profile.focus_type = self._determine_focus(profile)
        
        # Determine confidence level
        profile.confidence_level = self._determine_confidence(profile)
        
        return profile
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract speaker name from text"""
        patterns = [
            r"my name is ([A-Z][a-z]+ [A-Z][a-z]+)",
            r"i'm ([A-Z][a-z]+ [A-Z][a-z]+)",
            r"this is ([A-Z][a-z]+ [A-Z][a-z]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).title()
        return None
    
    def _count_markers(self, text: str, markers: List[str]) -> int:
        """Count occurrences of marker phrases"""
        return sum(1 for m in markers if m in text)
    
    def _extract_values(self, sentences: List[str]) -> List[str]:
        """Extract values from belief/opinion statements"""
        values = []
        patterns = [
            r"i believe (?:strongly )?in (.+)",
            r"i think (.+) is (?:really )?important",
            r"i value (.+)",
            r"i care (?:deeply )?about (.+)",
            r"what matters (?:most )?to me is (.+)",
        ]
        
        for sent in sentences:
            sent_lower = sent.lower()
            for pattern in patterns:
                match = re.search(pattern, sent_lower)
                if match:
                    value = match.group(1).strip()
                    # Clean up the value
                    value = re.sub(r"\s+and\s+.*$", "", value)  # Stop at "and"
                    value = value[:60]  # Limit length
                    if value and len(value) > 3:
                        values.append(value)
                    break
        
        return values
    
    def _extract_quantitative(self, sentences: List[str]) -> List[str]:
        """Extract quantitative claims (numbers, percentages)"""
        claims = []
        for sent in sentences:
            if re.search(r"\d+%|\d+ percent|\$\d+|\d+ years?", sent, re.IGNORECASE):
                claims.append(sent[:100])
        return claims
    
    def _extract_themes(self, text: str) -> List[str]:
        """Extract key themes from text"""
        themes = []
        for theme, keywords in self.THEME_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                themes.append(theme)
        return themes
    
    def _determine_style(self, profile: PersonaProfile) -> CommunicationStyle:
        """Determine primary communication style"""
        scores = {
            CommunicationStyle.ANALYTICAL: profile.analytical,
            CommunicationStyle.ASSERTIVE: profile.assertiveness,
            CommunicationStyle.COLLABORATIVE: profile.collaboration,
            CommunicationStyle.EXPRESSIVE: profile.expressive,
        }
        return max(scores, key=scores.get)
    
    def _determine_focus(self, profile: PersonaProfile) -> str:
        """Determine if speaker is self-focused or team-focused"""
        total = profile.i_statements + profile.we_statements
        if total == 0:
            return "balanced"
        
        i_ratio = profile.i_statements / total
        if i_ratio > 0.7:
            return "self-focused"
        elif i_ratio < 0.3:
            return "team-focused"
        return "balanced"
    
    def _determine_confidence(self, profile: PersonaProfile) -> str:
        """Determine confidence level from language"""
        if profile.certainty_words > profile.hedging_words * 2:
            return "high"
        elif profile.hedging_words > profile.certainty_words * 2:
            return "low"
        return "moderate"
    
    def get_summary(self, profile: PersonaProfile) -> Dict[str, Any]:
        """Generate structured summary for API/frontend"""
        return {
            "speaker": profile.name,
            "communication_style": profile.primary_style.value if profile.primary_style else "unknown",
            "focus": profile.focus_type,
            "confidence": profile.confidence_level,
            "style_scores": {
                "assertiveness": round(profile.assertiveness, 2),
                "collaboration": round(profile.collaboration, 2),
                "analytical": round(profile.analytical, 2),
                "expressive": round(profile.expressive, 2),
            },
            "speech_patterns": {
                "i_statements": profile.i_statements,
                "we_statements": profile.we_statements,
                "belief_statements": profile.belief_statements,
                "certainty_words": profile.certainty_words,
                "hedging_words": profile.hedging_words,
            },
            "values": profile.stated_values,
            "themes": profile.key_themes,
            "quantitative_claims": profile.quantitative_claims,
            "insights": self._generate_insights(profile),
        }
    
    def _generate_insights(self, profile: PersonaProfile) -> List[str]:
        """Generate human-readable insights"""
        insights = []
        
        # Style insight
        if profile.primary_style == CommunicationStyle.ANALYTICAL:
            insights.append("Values data and evidence in decision-making")
        elif profile.primary_style == CommunicationStyle.ASSERTIVE:
            insights.append("Confident and action-oriented communicator")
        elif profile.primary_style == CommunicationStyle.COLLABORATIVE:
            insights.append("Emphasizes teamwork and shared success")
        elif profile.primary_style == CommunicationStyle.EXPRESSIVE:
            insights.append("Values-driven and emotionally engaged")
        
        # Focus insight
        if profile.focus_type == "self-focused":
            insights.append("Tends to speak from personal perspective (high 'I' usage)")
        elif profile.focus_type == "team-focused":
            insights.append("Emphasizes collective achievements (high 'we' usage)")
        
        # Values insight
        if profile.stated_values:
            insights.append(f"Explicitly values: {', '.join(profile.stated_values[:3])}")
        
        # Confidence insight
        if profile.confidence_level == "high":
            insights.append("Uses confident, certain language")
        elif profile.confidence_level == "low":
            insights.append("Uses hedging language - may indicate uncertainty or caution")
        
        return insights


# Singleton accessor
_persona_analyzer: Optional[PersonaAnalyzer] = None

def get_persona_analyzer() -> PersonaAnalyzer:
    """Get singleton PersonaAnalyzer instance"""
    global _persona_analyzer
    if _persona_analyzer is None:
        _persona_analyzer = PersonaAnalyzer()
    return _persona_analyzer

