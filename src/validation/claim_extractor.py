"""
Claim Extractor - Extracts factual claims from transcriptions
"""

import logging
import re
from typing import List, Optional
import requests

from documents.schemas import Claim, ClaimType, Entity, create_claim

logger = logging.getLogger(__name__)


class ClaimExtractor:
    """Extract claims from transcription text"""
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        """
        Initialize claim extractor
        
        Args:
            ollama_url: URL for Ollama API
        """
        self.ollama_url = ollama_url
        logger.info("✅ Claim extractor initialized")
    
    async def extract_claims(
        self,
        transcription: str,
        transcription_id: str,
        use_llm: bool = True
    ) -> List[Claim]:
        """
        Extract claims from transcription
        
        Args:
            transcription: The transcribed text
            transcription_id: ID of the transcription
            use_llm: Whether to use LLM for extraction (fallback to rule-based)
        
        Returns:
            List of extracted claims
        """
        logger.info(f"🔍 Extracting claims from transcription: {transcription_id}")
        
        # Try LLM-based extraction first
        if use_llm:
            try:
                claims = await self._extract_with_llm(transcription, transcription_id)
                if claims:
                    logger.info(f"✅ Extracted {len(claims)} claims using LLM")
                    return claims
            except Exception as e:
                logger.warning(f"LLM extraction failed, falling back to rule-based: {e}")
        
        # Fallback to rule-based extraction
        claims = await self._extract_with_rules(transcription, transcription_id)
        logger.info(f"✅ Extracted {len(claims)} claims using rules")
        return claims
    
    async def _extract_with_llm(
        self,
        transcription: str,
        transcription_id: str
    ) -> List[Claim]:
        """Extract claims using LLM"""
        
        # Create prompt for claim extraction
        prompt = f"""Analyze the following transcription and extract factual claims.
        
A factual claim is a statement that can be verified as true or false.

Transcription:
"{transcription}"

Extract all factual claims from this transcription. For each claim, provide:
1. The exact claim text
2. Type: "fact", "opinion", or "prediction"
3. Entities mentioned (people, brands, products, organizations)

Format your response as a list of claims, one per line, in this format:
CLAIM: [claim text] | TYPE: [fact/opinion/prediction] | ENTITIES: [comma-separated entities]

Example:
CLAIM: Praxis has over 150 stores in Netherlands | TYPE: fact | ENTITIES: Praxis, Netherlands
CLAIM: The company will expand next year | TYPE: prediction | ENTITIES: company
"""
        
        # Call Ollama API
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "tinyllama:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 500
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Parse the LLM response
                claims = self._parse_llm_response(response_text, transcription_id)
                return claims
            else:
                logger.warning(f"LLM API returned status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"LLM claim extraction error: {e}")
            return []
    
    def _parse_llm_response(
        self,
        response_text: str,
        transcription_id: str
    ) -> List[Claim]:
        """Parse LLM response to extract claims"""
        claims = []
        
        # Look for CLAIM: pattern
        claim_pattern = r'CLAIM:\s*(.+?)\s*\|\s*TYPE:\s*(\w+)\s*\|\s*ENTITIES:\s*(.+?)(?:\n|$)'
        matches = re.findall(claim_pattern, response_text, re.IGNORECASE)
        
        for i, (claim_text, claim_type, entities_str) in enumerate(matches):
            # Parse claim type
            claim_type_clean = claim_type.lower().strip()
            if claim_type_clean == "fact":
                c_type = ClaimType.FACT
            elif claim_type_clean == "opinion":
                c_type = ClaimType.OPINION
            elif claim_type_clean == "prediction":
                c_type = ClaimType.PREDICTION
            else:
                c_type = ClaimType.STATEMENT
            
            # Parse entities
            entities = []
            if entities_str.strip().lower() != "none":
                entity_names = [e.strip() for e in entities_str.split(',') if e.strip()]
                for entity_name in entity_names:
                    entities.append(Entity(
                        text=entity_name,
                        type="unknown",
                        confidence=0.8,
                        start_pos=0,
                        end_pos=0
                    ))
            
            # Create claim
            claim = create_claim(
                text=claim_text.strip(),
                transcription_id=transcription_id,
                timestamp=0.0,
                claim_type=c_type,
                confidence=0.8
            )
            claim.entities = entities
            claims.append(claim)
        
        return claims
    
    async def _extract_with_rules(
        self,
        transcription: str,
        transcription_id: str
    ) -> List[Claim]:
        """Extract claims using rule-based approach"""
        claims = []
        
        # Split into sentences
        sentences = self._split_into_sentences(transcription)
        
        for i, sentence in enumerate(sentences):
            # Skip very short sentences
            if len(sentence.split()) < 3:
                continue
            
            # Determine if this is a factual claim
            claim_type = self._classify_sentence(sentence)
            
            if claim_type:
                # Extract basic entities
                entities = self._extract_entities(sentence)
                
                claim = create_claim(
                    text=sentence,
                    transcription_id=transcription_id,
                    timestamp=0.0,
                    claim_type=claim_type,
                    confidence=0.6  # Lower confidence for rule-based
                )
                claim.entities = entities
                claims.append(claim)
        
        return claims
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _classify_sentence(self, sentence: str) -> Optional[ClaimType]:
        """Classify sentence type"""
        sentence_lower = sentence.lower()
        
        # Opinion indicators
        opinion_words = ['think', 'believe', 'feel', 'probably', 'maybe', 'seems', 'appears']
        if any(word in sentence_lower for word in opinion_words):
            return ClaimType.OPINION
        
        # Prediction indicators
        prediction_words = ['will', 'going to', 'plan to', 'expect', 'forecast', 'predict']
        if any(word in sentence_lower for word in prediction_words):
            return ClaimType.PREDICTION
        
        # Fact indicators (has specific numbers, names, or declarative statements)
        fact_patterns = [
            r'\d+',  # Contains numbers
            r'(is|are|was|were|has|have|had)\s+\w+',  # Declarative statements
        ]
        
        if any(re.search(pattern, sentence_lower) for pattern in fact_patterns):
            return ClaimType.FACT
        
        # Default to statement
        return ClaimType.STATEMENT
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text (basic approach)"""
        entities = []
        
        # Look for capitalized words (potential proper nouns)
        words = text.split()
        for i, word in enumerate(words):
            # Remove punctuation
            clean_word = re.sub(r'[^\w\s]', '', word)
            
            # Check if it starts with capital and is not first word
            if clean_word and clean_word[0].isupper() and (i > 0 or clean_word.lower() not in ['the', 'a', 'an']):
                # Check if it's not a common word
                if len(clean_word) > 2:
                    entities.append(Entity(
                        text=clean_word,
                        type="organization",  # Default type
                        confidence=0.5,
                        start_pos=0,
                        end_pos=0
                    ))
        
        # Remove duplicates
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity.text.lower() not in seen:
                seen.add(entity.text.lower())
                unique_entities.append(entity)
        
        return unique_entities


# Global extractor instance
_extractor = None


async def get_claim_extractor() -> ClaimExtractor:
    """Get or create the global claim extractor"""
    global _extractor
    if _extractor is None:
        _extractor = ClaimExtractor()
    return _extractor

