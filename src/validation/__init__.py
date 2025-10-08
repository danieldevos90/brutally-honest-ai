"""
Validation Module
Handles claim extraction and validation against knowledge base
"""

from .claim_extractor import ClaimExtractor, get_claim_extractor
from .validator import ClaimValidator, get_validator

__all__ = ['ClaimExtractor', 'get_claim_extractor', 'ClaimValidator', 'get_validator']

