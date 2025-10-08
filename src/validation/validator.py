"""
Claim Validator - Validates claims against knowledge base
"""

import logging
from typing import List, Dict, Any, Optional
import requests

from documents.schemas import (
    Claim, ValidationResult, ValidationStatus, Evidence,
    ValidationReport, create_evidence
)
from documents.vector_store import get_vector_store
from profiles.profile_manager import get_profile_manager

logger = logging.getLogger(__name__)


class ClaimValidator:
    """Validate claims against knowledge base (documents + profiles)"""
    
    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        confidence_threshold: float = 0.7
    ):
        """
        Initialize claim validator
        
        Args:
            ollama_url: URL for Ollama API
            confidence_threshold: Minimum similarity score for matches
        """
        self.ollama_url = ollama_url
        self.confidence_threshold = confidence_threshold
        logger.info("✅ Claim validator initialized")
    
    async def validate_claim(
        self,
        claim: Claim,
        use_llm: bool = True
    ) -> ValidationResult:
        """
        Validate a single claim against knowledge base
        
        Args:
            claim: The claim to validate
            use_llm: Whether to use LLM for validation
        
        Returns:
            ValidationResult with status and evidence
        """
        logger.info(f"🔍 Validating claim: {claim.text[:50]}...")
        
        # Search for supporting/contradicting evidence
        evidence = await self._search_evidence(claim)
        
        if not evidence:
            # No data found
            return ValidationResult(
                claim=claim,
                status=ValidationStatus.NO_DATA,
                confidence=0.0,
                recommendation="No relevant information found in knowledge base"
            )
        
        # Use LLM to analyze evidence if requested
        if use_llm:
            result = await self._validate_with_llm(claim, evidence)
        else:
            result = await self._validate_with_rules(claim, evidence)
        
        logger.info(f"✅ Validation complete: {result.status.value} (confidence: {result.confidence:.2f})")
        return result
    
    async def validate_transcription(
        self,
        transcription_id: str,
        transcription_text: str,
        claims: List[Claim]
    ) -> ValidationReport:
        """
        Validate all claims in a transcription
        
        Args:
            transcription_id: ID of the transcription
            transcription_text: Full transcription text
            claims: List of extracted claims
        
        Returns:
            Complete validation report
        """
        logger.info(f"📋 Validating transcription with {len(claims)} claims")
        
        # Validate each claim
        validations = []
        for claim in claims:
            result = await self.validate_claim(claim)
            validations.append(result)
        
        # Calculate overall credibility
        overall_credibility = self._calculate_overall_credibility(validations)
        
        # Generate summary and warnings
        summary, warnings = self._generate_summary(validations)
        
        report = ValidationReport(
            id=f"report_{transcription_id}",
            transcription_id=transcription_id,
            transcription_text=transcription_text,
            claims=claims,
            validations=validations,
            overall_credibility=overall_credibility,
            summary=summary,
            warnings=warnings
        )
        
        logger.info(f"✅ Validation report generated. Overall credibility: {overall_credibility:.1%}")
        return report
    
    async def _search_evidence(self, claim: Claim) -> List[Evidence]:
        """Search for evidence in documents and profiles"""
        evidence = []
        
        # Search documents
        try:
            vector_store = await get_vector_store()
            doc_results = await vector_store.search_documents(
                query=claim.text,
                limit=5,
                score_threshold=self.confidence_threshold * 0.7  # Slightly lower threshold for initial search
            )
            
            for result in doc_results:
                evidence.append(create_evidence(
                    source_type="document",
                    source_id=result.document_id,
                    content=result.content,
                    similarity_score=result.score,
                    supports_claim=True  # Will be determined by LLM
                ))
                
        except Exception as e:
            logger.warning(f"Document search failed: {e}")
        
        # Search profile facts
        try:
            profile_manager = await get_profile_manager()
            
            # Search all profile types
            for profile_list, profile_type in [
                (await profile_manager.list_client_profiles(), "client"),
                (await profile_manager.list_brand_profiles(), "brand"),
                (await profile_manager.list_person_profiles(), "person")
            ]:
                for profile in profile_list:
                    for fact in profile.facts:
                        # Simple text similarity check
                        if self._text_similarity(claim.text, fact.statement) > 0.5:
                            evidence.append(create_evidence(
                                source_type="profile",
                                source_id=profile.id,
                                content=f"{profile.name}: {fact.statement}",
                                similarity_score=fact.confidence,
                                supports_claim=True
                            ))
        except Exception as e:
            logger.warning(f"Profile search failed: {e}")
        
        return evidence
    
    async def _validate_with_llm(
        self,
        claim: Claim,
        evidence: List[Evidence]
    ) -> ValidationResult:
        """Validate claim using LLM"""
        
        # Create prompt
        evidence_text = "\n".join([
            f"- {e.source_type.upper()}: {e.content[:200]}... (confidence: {e.similarity_score:.2f})"
            for e in evidence[:5]  # Limit to top 5 pieces of evidence
        ])
        
        prompt = f"""Validate the following claim against the provided evidence.

CLAIM: "{claim.text}"

EVIDENCE:
{evidence_text}

Based on this evidence, is the claim:
1. CONFIRMED - Evidence strongly supports the claim
2. CONTRADICTED - Evidence contradicts the claim
3. UNCERTAIN - Evidence is inconclusive or conflicting

Respond with ONE of these words: CONFIRMED, CONTRADICTED, or UNCERTAIN
Then explain why in one sentence.

Format:
STATUS: [CONFIRMED/CONTRADICTED/UNCERTAIN]
REASON: [your explanation]
"""
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": "tinyllama:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 200
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Parse response
                status, reason, confidence = self._parse_validation_response(response_text)
                
                # Categorize evidence
                supporting = []
                contradicting = []
                for e in evidence:
                    if status == ValidationStatus.CONFIRMED:
                        supporting.append(e)
                    elif status == ValidationStatus.CONTRADICTED:
                        contradicting.append(e)
                    else:
                        # Uncertain - evidence could be either
                        supporting.append(e)
                
                return ValidationResult(
                    claim=claim,
                    status=status,
                    confidence=confidence,
                    supporting_facts=[],
                    contradicting_facts=[],
                    evidence=evidence,
                    recommendation=reason
                )
        except Exception as e:
            logger.error(f"LLM validation error: {e}")
        
        # Fallback to rule-based
        return await self._validate_with_rules(claim, evidence)
    
    async def _validate_with_rules(
        self,
        claim: Claim,
        evidence: List[Evidence]
    ) -> ValidationResult:
        """Validate claim using rule-based approach"""
        
        if not evidence:
            return ValidationResult(
                claim=claim,
                status=ValidationStatus.NO_DATA,
                confidence=0.0,
                evidence=[],
                recommendation="No evidence found"
            )
        
        # Calculate average similarity
        avg_similarity = sum(e.similarity_score for e in evidence) / len(evidence)
        
        # Determine status based on similarity
        if avg_similarity > 0.85:
            status = ValidationStatus.CONFIRMED
            recommendation = "High similarity with known facts"
        elif avg_similarity > self.confidence_threshold:
            status = ValidationStatus.UNCERTAIN
            recommendation = "Moderate similarity with known facts"
        else:
            status = ValidationStatus.UNCERTAIN
            recommendation = "Low similarity with known facts"
        
        return ValidationResult(
            claim=claim,
            status=status,
            confidence=avg_similarity,
            evidence=evidence,
            recommendation=recommendation
        )
    
    def _parse_validation_response(self, response_text: str) -> tuple:
        """Parse LLM validation response"""
        import re
        
        # Default values
        status = ValidationStatus.UNCERTAIN
        reason = "Unable to determine"
        confidence = 0.5
        
        # Look for status
        status_match = re.search(r'STATUS:\s*(CONFIRMED|CONTRADICTED|UNCERTAIN)', response_text, re.IGNORECASE)
        if status_match:
            status_str = status_match.group(1).upper()
            if status_str == "CONFIRMED":
                status = ValidationStatus.CONFIRMED
                confidence = 0.85
            elif status_str == "CONTRADICTED":
                status = ValidationStatus.CONTRADICTED
                confidence = 0.85
            else:
                status = ValidationStatus.UNCERTAIN
                confidence = 0.5
        
        # Look for reason
        reason_match = re.search(r'REASON:\s*(.+?)(?:\n|$)', response_text)
        if reason_match:
            reason = reason_match.group(1).strip()
        
        return status, reason, confidence
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_overall_credibility(self, validations: List[ValidationResult]) -> float:
        """Calculate overall credibility score"""
        if not validations:
            return 1.0
        
        # Count different statuses
        confirmed = sum(1 for v in validations if v.status == ValidationStatus.CONFIRMED)
        contradicted = sum(1 for v in validations if v.status == ValidationStatus.CONTRADICTED)
        uncertain = sum(1 for v in validations if v.status == ValidationStatus.UNCERTAIN)
        no_data = sum(1 for v in validations if v.status == ValidationStatus.NO_DATA)
        
        total = len(validations)
        
        # Calculate score
        score = (
            (confirmed * 1.0) +
            (uncertain * 0.5) +
            (no_data * 0.7) +
            (contradicted * 0.0)
        ) / total
        
        return score
    
    def _generate_summary(self, validations: List[ValidationResult]) -> tuple:
        """Generate summary and warnings"""
        confirmed = sum(1 for v in validations if v.status == ValidationStatus.CONFIRMED)
        contradicted = sum(1 for v in validations if v.status == ValidationStatus.CONTRADICTED)
        uncertain = sum(1 for v in validations if v.status == ValidationStatus.UNCERTAIN)
        no_data = sum(1 for v in validations if v.status == ValidationStatus.NO_DATA)
        
        total = len(validations)
        
        summary = f"Validated {total} claim(s): {confirmed} confirmed, {contradicted} contradicted, {uncertain} uncertain, {no_data} no data."
        
        warnings = []
        if contradicted > 0:
            warnings.append(f"⚠️ {contradicted} claim(s) contradict known facts")
        if uncertain > total * 0.5:
            warnings.append(f"⚠️ {uncertain} claim(s) could not be verified with confidence")
        if no_data > total * 0.3:
            warnings.append(f"💡 {no_data} claim(s) have no matching data in knowledge base")
        
        return summary, warnings


# Global validator instance
_validator = None


async def get_validator() -> ClaimValidator:
    """Get or create the global claim validator"""
    global _validator
    if _validator is None:
        _validator = ClaimValidator()
    return _validator

