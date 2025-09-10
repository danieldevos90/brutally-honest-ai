"""
Enhanced LLAMA Processor with Document-Validated Transcription
Integrates document knowledge base with audio transcription for fact-checking
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .llama_processor import LLAMAProcessor, AIProcessingResult
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.documents.vector_store import get_vector_store

logger = logging.getLogger(__name__)

@dataclass
class EnhancedAIResult(AIProcessingResult):
    """Enhanced AI result with document validation"""
    document_validation: Optional[str] = None
    fact_check_sources: Optional[List[Dict[str, Any]]] = None
    validation_score: Optional[float] = None
    contradictions: Optional[List[str]] = None
    supporting_evidence: Optional[List[str]] = None

class DocumentValidatedProcessor(LLAMAProcessor):
    """Enhanced LLAMA processor that validates transcriptions against document knowledge base"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vector_store = None
        
    async def initialize(self) -> bool:
        """Initialize both LLAMA and vector store"""
        # Initialize base LLAMA processor
        base_init = await super().initialize()
        
        if base_init:
            try:
                # Initialize vector store for document validation
                self.vector_store = await get_vector_store()
                logger.info("✅ Document validation system initialized")
                return True
            except Exception as e:
                logger.warning(f"⚠️  Document validation not available: {e}")
                # Still allow basic functionality without document validation
                return True
        
        return False
    
    async def validate_transcription_with_documents(self, transcription: str) -> Dict[str, Any]:
        """Validate transcription content against uploaded documents"""
        if not self.vector_store:
            return {
                "validation_available": False,
                "message": "Document validation not available"
            }
        
        try:
            logger.info("🔍 Validating transcription against document knowledge base...")
            
            # Extract key claims and facts from transcription
            key_phrases = await self._extract_key_claims(transcription)
            
            validation_results = {
                "validation_available": True,
                "supporting_evidence": [],
                "contradictions": [],
                "fact_check_sources": [],
                "validation_score": 0.0,
                "summary": ""
            }
            
            total_claims = len(key_phrases)
            supported_claims = 0
            
            # Check each key claim against documents
            for claim in key_phrases:
                logger.info(f"🔎 Checking claim: {claim[:50]}...")
                
                # Search for relevant documents
                search_results = await self.vector_store.search_documents(
                    claim, 
                    limit=3, 
                    score_threshold=0.6
                )
                
                if search_results:
                    # Analyze if documents support or contradict the claim
                    analysis = await self._analyze_claim_vs_documents(claim, search_results)
                    
                    if analysis["supports"]:
                        validation_results["supporting_evidence"].append({
                            "claim": claim,
                            "evidence": analysis["evidence"],
                            "sources": [r.metadata.get("filename", "Unknown") for r in search_results],
                            "confidence": analysis["confidence"]
                        })
                        supported_claims += 1
                    elif analysis["contradicts"]:
                        validation_results["contradictions"].append({
                            "claim": claim,
                            "contradiction": analysis["contradiction"],
                            "sources": [r.metadata.get("filename", "Unknown") for r in search_results],
                            "confidence": analysis["confidence"]
                        })
                    
                    # Add sources
                    for result in search_results:
                        validation_results["fact_check_sources"].append({
                            "filename": result.metadata.get("filename", "Unknown"),
                            "content_preview": result.content[:200] + "..." if len(result.content) > 200 else result.content,
                            "relevance_score": result.score,
                            "claim_related": claim[:50] + "..."
                        })
            
            # Calculate validation score
            if total_claims > 0:
                validation_results["validation_score"] = supported_claims / total_claims
            
            # Generate summary
            validation_results["summary"] = await self._generate_validation_summary(validation_results)
            
            logger.info(f"✅ Validation complete: {supported_claims}/{total_claims} claims supported")
            return validation_results
            
        except Exception as e:
            logger.error(f"❌ Document validation failed: {e}")
            return {
                "validation_available": False,
                "error": str(e)
            }
    
    async def _extract_key_claims(self, transcription: str) -> List[str]:
        """Extract key factual claims from transcription text"""
        # Simple approach: split into sentences and filter for factual statements
        import re
        
        sentences = re.split(r'[.!?]+', transcription)
        key_claims = []
        
        # Filter for sentences that might contain factual claims
        factual_indicators = [
            r'\b(is|are|was|were|will be|has|have|had)\b',
            r'\b(according to|based on|research shows|studies indicate)\b',
            r'\b(percent|percentage|number|amount|cost|price)\b',
            r'\b(company|organization|government|university)\b',
            r'\b(date|year|month|time|when|where)\b'
        ]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 20:  # Ignore very short sentences
                # Check if sentence contains factual indicators
                for pattern in factual_indicators:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        key_claims.append(sentence)
                        break
        
        # Limit to most important claims
        return key_claims[:10]
    
    async def _analyze_claim_vs_documents(self, claim: str, search_results: List) -> Dict[str, Any]:
        """Analyze if documents support or contradict a claim using LLAMA"""
        try:
            # Prepare context from search results
            context = "\n\n".join([
                f"Document: {result.metadata.get('filename', 'Unknown')}\nContent: {result.content}"
                for result in search_results
            ])
            
            # Create analysis prompt
            prompt = f"""Analyze if the following claim is supported or contradicted by the provided documents.

CLAIM: {claim}

DOCUMENTS:
{context}

Please respond with a JSON-like analysis:
- "supports": true/false (does the document content support this claim?)
- "contradicts": true/false (does the document content contradict this claim?)
- "evidence": "specific text from documents that supports the claim"
- "contradiction": "specific text that contradicts the claim"
- "confidence": 0.0-1.0 (how confident are you in this analysis?)

Be brutally honest and precise. If the documents don't clearly support or contradict the claim, say so."""
            
            # Use LLAMA to analyze
            if hasattr(self, 'llama') and self.llama:
                if self.llama_type == "ollama":
                    import requests
                    response = requests.post(
                        "http://localhost:11434/api/generate",
                        json={
                            "model": "tinyllama:latest",
                            "prompt": prompt,
                            "stream": False
                        },
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        analysis_text = response.json().get("response", "")
                    else:
                        analysis_text = "Analysis failed"
                else:
                    # Use llama-cpp-python
                    response = self.llama(prompt, max_tokens=300, temperature=0.3)
                    analysis_text = response["choices"][0]["text"].strip()
                
                # Parse the analysis (simple keyword-based parsing)
                supports = "supports\": true" in analysis_text.lower() or "supports the claim" in analysis_text.lower()
                contradicts = "contradicts\": true" in analysis_text.lower() or "contradicts the claim" in analysis_text.lower()
                
                return {
                    "supports": supports,
                    "contradicts": contradicts,
                    "evidence": analysis_text if supports else "",
                    "contradiction": analysis_text if contradicts else "",
                    "confidence": 0.7,  # Default confidence
                    "full_analysis": analysis_text
                }
            
            # Fallback: simple keyword matching
            claim_lower = claim.lower()
            context_lower = context.lower()
            
            # Very basic support/contradiction detection
            claim_words = set(claim_lower.split())
            context_words = set(context_lower.split())
            overlap = len(claim_words.intersection(context_words))
            
            supports = overlap > len(claim_words) * 0.3
            
            return {
                "supports": supports,
                "contradicts": False,
                "evidence": "Keyword overlap detected" if supports else "",
                "contradiction": "",
                "confidence": 0.4,  # Low confidence for fallback method
                "full_analysis": "Fallback analysis used"
            }
            
        except Exception as e:
            logger.error(f"Claim analysis failed: {e}")
            return {
                "supports": False,
                "contradicts": False,
                "evidence": "",
                "contradiction": "",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _generate_validation_summary(self, validation_results: Dict[str, Any]) -> str:
        """Generate a human-readable validation summary"""
        supported = len(validation_results["supporting_evidence"])
        contradicted = len(validation_results["contradictions"])
        score = validation_results["validation_score"]
        
        if score >= 0.8:
            summary = f"✅ HIGH VALIDATION: {supported} claims supported by your documents. "
        elif score >= 0.5:
            summary = f"⚠️  PARTIAL VALIDATION: {supported} claims supported, {contradicted} contradicted. "
        else:
            summary = f"❌ LOW VALIDATION: Only {supported} claims supported by your documents. "
        
        if contradicted > 0:
            summary += f"Found {contradicted} potential contradictions that need review. "
        
        if validation_results["fact_check_sources"]:
            unique_sources = set(source["filename"] for source in validation_results["fact_check_sources"])
            summary += f"Checked against {len(unique_sources)} documents."
        
        return summary
    
    async def process_audio_with_validation(self, audio_data: bytes, filename: str) -> EnhancedAIResult:
        """Process audio with document validation"""
        start_time = time.time()
        
        try:
            logger.info(f"🎤 Starting enhanced audio processing with document validation: {filename}")
            
            # First, do standard audio processing
            base_result = await super().process_audio(audio_data, filename)
            
            if not base_result.success:
                return EnhancedAIResult(
                    success=False,
                    error=base_result.error,
                    processing_time=time.time() - start_time
                )
            
            # Then, validate transcription against documents
            logger.info("📚 Validating transcription against document knowledge base...")
            validation_result = await self.validate_transcription_with_documents(base_result.transcription)
            
            # Create enhanced result
            enhanced_result = EnhancedAIResult(
                success=True,
                transcription=base_result.transcription,
                analysis=base_result.analysis,
                summary=base_result.summary,
                sentiment=base_result.sentiment,
                keywords=base_result.keywords,
                fact_check=base_result.fact_check,
                brutal_honesty=base_result.brutal_honesty,
                credibility_score=base_result.credibility_score,
                questionable_claims=base_result.questionable_claims,
                corrections=base_result.corrections,
                confidence=base_result.confidence,
                processing_time=time.time() - start_time,
                
                # Enhanced validation fields
                document_validation=validation_result.get("summary", "No validation available"),
                fact_check_sources=validation_result.get("fact_check_sources", []),
                validation_score=validation_result.get("validation_score", 0.0),
                contradictions=[c["claim"] + " - " + c["contradiction"] for c in validation_result.get("contradictions", [])],
                supporting_evidence=[e["claim"] + " - " + e["evidence"] for e in validation_result.get("supporting_evidence", [])]
            )
            
            # Enhance brutal honesty with document validation
            if validation_result.get("validation_available"):
                enhanced_brutal_honesty = await self._enhance_brutal_honesty_with_validation(
                    base_result.brutal_honesty, 
                    validation_result
                )
                enhanced_result.brutal_honesty = enhanced_brutal_honesty
            
            logger.info("✅ Enhanced audio processing with document validation completed")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Enhanced audio processing failed: {e}")
            return EnhancedAIResult(
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )
    
    async def _enhance_brutal_honesty_with_validation(self, original_honesty: str, validation_result: Dict[str, Any]) -> str:
        """Enhance brutal honesty response with document validation insights"""
        validation_score = validation_result.get("validation_score", 0.0)
        contradictions = validation_result.get("contradictions", [])
        supporting_evidence = validation_result.get("supporting_evidence", [])
        
        enhanced_honesty = original_honesty + "\n\n"
        
        if validation_score >= 0.8:
            enhanced_honesty += "📚 DOCUMENT VALIDATION: Your transcription checks out well against your uploaded documents. "
        elif validation_score >= 0.5:
            enhanced_honesty += "📚 DOCUMENT VALIDATION: Some of your transcription is supported by your documents, but there are gaps. "
        else:
            enhanced_honesty += "📚 DOCUMENT VALIDATION: Your transcription has limited support from your uploaded documents. "
        
        if contradictions:
            enhanced_honesty += f"However, I found {len(contradictions)} potential contradictions that you should review. "
        
        if supporting_evidence:
            enhanced_honesty += f"On the positive side, {len(supporting_evidence)} claims are well-supported by your documents."
        
        return enhanced_honesty

# Global enhanced processor instance
_enhanced_processor = None

async def get_enhanced_processor() -> DocumentValidatedProcessor:
    """Get or create the global enhanced processor"""
    global _enhanced_processor
    if _enhanced_processor is None:
        _enhanced_processor = DocumentValidatedProcessor()
        await _enhanced_processor.initialize()
    return _enhanced_processor
