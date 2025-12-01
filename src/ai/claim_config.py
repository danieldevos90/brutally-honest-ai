"""
Claim Extraction Configuration - Scalable & Configurable

This module provides configurable settings for claim extraction.
Patterns can be updated here without changing the core logic.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set
import json
import os
import logging

logger = logging.getLogger(__name__)

@dataclass
class ClaimExtractionConfig:
    """Configuration for claim extraction - easily extensible"""
    
    # Minimum requirements for a sentence to be considered a potential claim
    min_sentence_length: int = 15
    min_word_count: int = 3
    max_claims_to_extract: int = 5
    
    # Skip patterns by language (conversational/non-factual indicators)
    skip_patterns: Dict[str, List[str]] = field(default_factory=lambda: {
        "universal": [
            r'\?$',  # Questions end with ?
            r'^[\W]*$',  # Empty or only punctuation
        ],
        "en": [
            r'^(hi|hello|hey|okay|ok|yes|no|um|uh|well|so|and|but|then|like)\b',
            r'^(i think|i believe|i feel|maybe|perhaps|probably|i guess|i want|i need|i wish|i hope)\b',
            r'^(what|how|why|where|when|who|which|could|would|should|can|will|do you)\b',
            r'\b(annoying|boring|interesting|nice|cool|awesome|terrible|great)\b',  # Subjective
        ],
        "nl": [
            r'^(ja|nee|nou|dus|en|of|maar|want|hoi|hallo|hey|oké|ok|even|eens)\b',
            r'^(ik denk|ik geloof|ik voel|misschien|wellicht|waarschijnlijk|ik wil|ik moet|ik hoop)\b',
            r'^(wat|hoe|waarom|waar|wanneer|wie|welke|zou|kan|zal|wil|kun je|moet je)\b',
            r'\b(vervelend|saai|interessant|leuk|gaaf|geweldig|verschrikkelijk|mooi)\b',  # Subjective
        ],
        "de": [
            r'^(ja|nein|also|und|oder|aber|weil|hallo|hey|okay|ok)\b',
            r'^(ich denke|ich glaube|ich fühle|vielleicht|wahrscheinlich|ich will|ich muss)\b',
            r'^(was|wie|warum|wo|wann|wer|welche|könnte|würde|sollte|kann|wird)\b',
        ],
        "meta": [
            # Recording/testing meta-talk (all languages)
            r'\b(recording|opname|aufnahme|test|testen|testing)\b',
            r'\b(start|stop|begin|einde|end)\s*(recording|opname)\b',
        ]
    })
    
    # Fact indicators - patterns that suggest verifiable information
    fact_indicators: Dict[str, List[str]] = field(default_factory=lambda: {
        "numbers": [
            r'\b\d+([.,]\d+)?(%|\s*percent|\s*procent)?\b',  # Numbers, percentages
            r'\b(million|miljoen|billion|miljard|thousand|duizend|hundred|honderd)\b',
        ],
        "absolutes": [
            r'\b(always|never|all|every|none|no one|everyone)\b',
            r'\b(altijd|nooit|alle|elk|geen|niemand|iedereen)\b',
        ],
        "definitions": [
            r'\b(is|are|was|were)\s+(a|an|the|defined as)\b',
            r'\b(is|zijn|was|waren|wordt|worden)\s+(een|de|het)\b',
        ],
        "sources": [
            r'\b(according to|based on|research|study|survey|report|data|statistics)\b',
            r'\b(volgens|gebaseerd op|onderzoek|studie|enquête|rapport|gegevens|statistieken)\b',
        ],
        "historical": [
            r'\b(founded|established|created|invented|discovered|built|started)\s+in\s+\d{4}\b',
            r'\b(opgericht|gevestigd|gemaakt|uitgevonden|ontdekt|gebouwd|gestart)\s+in\s+\d{4}\b',
        ],
        "locations": [
            r'\b(located|based|situated|headquartered)\s+(in|at)\b',
            r'\b(gelegen|gevestigd|gezeteld)\s+(in|te|bij)\b',
        ],
        "measurements": [
            r'\b\d+\s*(km|miles?|meters?|feet|inches|cm|mm|kg|lbs?|pounds?|grams?)\b',
            r'\b\d+\s*(years?|months?|days?|hours?|minutes?|seconds?)\b',
            r'\b\d+\s*(jaar|maanden?|dagen?|uren?|minuten?|seconden?)\b',
        ],
        "comparisons": [
            r'\b(more than|less than|greater than|smaller than|bigger than|faster than)\b',
            r'\b(meer dan|minder dan|groter dan|kleiner dan|sneller dan)\b',
        ],
        "proper_nouns": [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',  # Multi-word proper nouns (Company Name)
        ]
    })
    
    # Claim type classifications
    claim_types: Dict[str, List[str]] = field(default_factory=lambda: {
        "statistical": ["percent", "procent", "%", "average", "median", "gemiddelde"],
        "historical": ["founded", "invented", "discovered", "opgericht", "uitgevonden"],
        "scientific": ["research", "study", "proven", "onderzoek", "bewezen"],
        "financial": ["cost", "price", "worth", "revenue", "profit", "kost", "prijs", "waarde"],
        "geographical": ["located", "capital", "population", "gelegen", "hoofdstad", "bevolking"],
    })


# Singleton instance
_config_instance = None

def get_claim_config() -> ClaimExtractionConfig:
    """Get the claim extraction configuration (singleton)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ClaimExtractionConfig()
        
        # Try to load custom config from file
        config_path = os.path.join(os.path.dirname(__file__), "claim_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    custom_config = json.load(f)
                    # Merge custom patterns
                    for key, value in custom_config.items():
                        if hasattr(_config_instance, key):
                            if isinstance(value, dict):
                                getattr(_config_instance, key).update(value)
                            else:
                                setattr(_config_instance, key, value)
                    logger.info(f"✅ Loaded custom claim config from {config_path}")
            except Exception as e:
                logger.warning(f"Could not load custom claim config: {e}")
    
    return _config_instance


def add_skip_pattern(language: str, pattern: str):
    """Dynamically add a skip pattern"""
    config = get_claim_config()
    if language not in config.skip_patterns:
        config.skip_patterns[language] = []
    config.skip_patterns[language].append(pattern)
    logger.info(f"Added skip pattern for {language}: {pattern}")


def add_fact_indicator(category: str, pattern: str):
    """Dynamically add a fact indicator"""
    config = get_claim_config()
    if category not in config.fact_indicators:
        config.fact_indicators[category] = []
    config.fact_indicators[category].append(pattern)
    logger.info(f"Added fact indicator for {category}: {pattern}")

