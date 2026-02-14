"""
Intelligent Fact Checker - Uses LLAMA + Vector Database + Profiles

Instead of hardcoded rules, this:
1. Extracts claims from transcription using LLAMA
2. Searches vector database for relevant documents
3. Retrieves brand/client/person profile facts
4. Uses LLAMA to verify claims against retrieved context
5. Returns structured verification with sources
"""

import asyncio
import logging
import json
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ClaimVerification:
    """Result of verifying a single claim"""
    claim: str
    verdict: str  # "VERIFIED", "FALSE", "PARTIALLY_TRUE", "UNVERIFIABLE", "OPINION"
    confidence: float
    explanation: str
    sources: List[Dict[str, str]] = field(default_factory=list)  # [{"type": "document", "name": "...", "excerpt": "..."}]
    

@dataclass
class FactCheckResult:
    """Complete fact-checking result"""
    claims_found: int
    claims_verified: int
    claims_false: int
    claims_partial: int
    claims_unverifiable: int
    claims_opinion: int
    credibility_score: Optional[float]  # None when no claims to verify
    verifications: List[ClaimVerification] = field(default_factory=list)
    summary: str = ""
    processing_time: float = 0.0


class IntelligentFactChecker:
    """
    AI-powered fact checker using LLAMA and vector database
    """
    
    def __init__(self):
        self.llm = None
        self.vector_store = None
        self.profile_manager = None
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize all components"""
        try:
            # Import and initialize LLM (local only - no cloud APIs)
            try:
                from src.llm.llm_client import get_llm_client
                self.llm = await get_llm_client(prefer_local=True)  # Only use local LLAMA
                if self.llm:
                    logger.info(f"✅ LOCAL LLAMA initialized for fact-checking")
                else:
                    logger.warning("Local LLAMA (Ollama) not available for fact-checking")
            except Exception as e:
                logger.warning(f"LLM initialization failed: {e}")
            
            # Import and initialize vector store
            try:
                from src.documents.vector_store import get_vector_store
                self.vector_store = await get_vector_store()
                logger.info("✅ Vector store initialized for fact-checking")
            except Exception as e:
                logger.warning(f"Vector store not available: {e}")
            
            # Import and initialize profile manager
            try:
                from src.profiles.profile_manager import get_profile_manager
                self.profile_manager = await get_profile_manager()
                logger.info("✅ Profile manager initialized for fact-checking")
            except Exception as e:
                logger.warning(f"Profile manager not available: {e}")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize IntelligentFactChecker: {e}")
            return False
    
    async def check_facts(
        self,
        text: str,
        brand_id: Optional[str] = None,
        client_id: Optional[str] = None,
        person_id: Optional[str] = None
    ) -> FactCheckResult:
        """
        Main fact-checking function
        
        Args:
            text: Transcription text to fact-check
            brand_id: Optional brand profile to check against
            client_id: Optional client profile to check against
            person_id: Optional person profile to check against
        """
        import time
        start_time = time.time()
        
        # Check available memory before running LLM operations
        # TinyLlama needs ~637MB, so 0.7GB threshold is safe
        try:
            import psutil
            available_gb = psutil.virtual_memory().available / (1024**3)
            if available_gb < 0.7:
                logger.warning(f"⚠️ Low memory ({available_gb:.1f}GB) - skipping fact-checking to prevent OOM")
                return FactCheckResult(
                    claims_found=0,
                    claims_verified=0,
                    claims_false=0,
                    claims_partial=0,
                    claims_unverifiable=0,
                    claims_opinion=0,
                    credibility_score=0.5,
                    summary=f"Fact-checking skipped (low memory: {available_gb:.1f}GB available)",
                    processing_time=time.time() - start_time
                )
        except ImportError:
            pass  # psutil not available, continue anyway
        
        if not self.is_initialized:
            await self.initialize()
        
        # Step 1: Extract claims from text
        claims = await self._extract_claims(text)
        logger.info(f"📋 Extracted {len(claims)} claims from transcription")
        
        if not claims:
            return FactCheckResult(
                claims_found=0,
                claims_verified=0,
                claims_false=0,
                claims_partial=0,
                claims_unverifiable=0,
                claims_opinion=0,
                credibility_score=None,  # N/A when no claims to verify
                summary="No verifiable factual claims detected. This transcription contains only conversational content, opinions, or questions - nothing to fact-check.",
                processing_time=time.time() - start_time
            )
        
        # Step 2: Gather context from various sources
        context = await self._gather_context(claims, brand_id, client_id, person_id)
        logger.info(f"📚 Gathered context from {len(context)} sources")
        
        # Step 3: Verify each claim
        verifications = []
        for claim in claims:
            verification = await self._verify_claim(claim, context)
            verifications.append(verification)
        
        # Step 4: Calculate scores
        verified = sum(1 for v in verifications if v.verdict == "VERIFIED")
        false = sum(1 for v in verifications if v.verdict == "FALSE")
        partial = sum(1 for v in verifications if v.verdict == "PARTIALLY_TRUE")
        unverifiable = sum(1 for v in verifications if v.verdict == "UNVERIFIABLE")
        opinion = sum(1 for v in verifications if v.verdict == "OPINION")
        
        # Credibility score: verified=1.0, partial=0.5, opinion=0.7, unverifiable=0.5, false=0.0
        if len(claims) > 0:
            score = (verified * 1.0 + partial * 0.5 + opinion * 0.7 + unverifiable * 0.5) / len(claims)
        else:
            score = 0.7
        
        # Generate summary
        summary = await self._generate_summary(verifications, score)
        
        result = FactCheckResult(
            claims_found=len(claims),
            claims_verified=verified,
            claims_false=false,
            claims_partial=partial,
            claims_unverifiable=unverifiable,
            claims_opinion=opinion,
            credibility_score=score,
            verifications=verifications,
            summary=summary,
            processing_time=time.time() - start_time
        )
        
        logger.info(f"✅ Fact-check complete: {verified}/{len(claims)} verified, credibility: {score:.2f}")
        return result
    
    async def _extract_claims(self, text: str) -> List[str]:
        """Extract factual claims from text using LLAMA (Ollama)"""
        
        # Always try LLAMA first - it's smarter than regex
        claims = await self._extract_claims_with_llama(text)
        if claims is not None:
            return claims
        
        # Fallback to config-based extraction only if LLAMA completely fails
        logger.warning("LLAMA claim extraction failed, using config-based fallback")
        return self._config_based_claim_extraction(text)
    
    async def _extract_claims_with_llama(self, text: str) -> Optional[List[str]]:
        """Use LLAMA via Ollama to intelligently extract claims"""
        import aiohttp
        
        # Check memory before calling Ollama (TinyLlama needs ~637MB)
        try:
            import psutil
            available_gb = psutil.virtual_memory().available / (1024**3)
            if available_gb < 0.7:
                logger.warning(f"⚠️ Low memory ({available_gb:.1f}GB) - skipping LLAMA claim extraction")
                return None
        except ImportError:
            pass
        
        prompt = f"""Extract ALL factual claims from this text. A factual claim is ANY statement that can be checked as TRUE or FALSE.

Text: "{text}"

IMPORTANT RULES:
1. Extract EVERY verifiable statement - about animals, people, companies, stores, products, facts
2. Include claims about businesses (e.g., "Store X has no products" is a claim)
3. Include claims about animals (e.g., "Fish can fly" is a claim)
4. Keep claims in the ORIGINAL LANGUAGE (Dutch stays Dutch)
5. Return ONLY a JSON array of strings, nothing else

Examples:
- "De vis kan vliegen en Praxis heeft geen spullen" → ["De vis kan vliegen", "Praxis heeft geen spullen"]
- "Apple was founded in 1976" → ["Apple was founded in 1976"]
- "I think it is nice" → []

JSON array:"""

        try:
            # Try using the initialized LLM client first
            if self.llm:
                response = await self.llm.generate(prompt)
                logger.debug(f"🔍 LLAMA raw response: {response[:200]}...")
                claims = self._parse_claims_json(response)
                logger.debug(f"🔍 Parsed claims: {claims}")
                if claims is not None:
                    logger.info(f"✅ LLAMA extracted {len(claims)} claims via LLM client")
                    return claims
                else:
                    logger.warning(f"⚠️ Failed to parse claims from LLAMA response: {response[:100]}...")
            
            # Direct Ollama call as backup
            ollama_url = "http://localhost:11434/api/generate"
            model = os.environ.get("LLM_MODEL", "llama3.2:3b")
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temp for consistent extraction
                    "num_predict": 300,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                # Increased timeout for slower Jetson hardware
                async with session.post(ollama_url, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response = data.get("response", "")
                        claims = self._parse_claims_json(response)
                        if claims is not None:
                            logger.info(f"✅ LLAMA extracted {len(claims)} claims via direct Ollama")
                            return claims
                    else:
                        logger.warning(f"Ollama returned status {resp.status}")
                        
        except Exception as e:
            logger.warning(f"LLAMA claim extraction error: {e}")
        
        return None
    
    def _parse_claims_json(self, response: str) -> Optional[List[str]]:
        """Parse JSON array from LLAMA response - handles both string arrays and object arrays"""
        try:
            # Try to find JSON array in response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                claims_data = json.loads(json_match.group())
                if isinstance(claims_data, list):
                    valid_claims = []
                    for item in claims_data:
                        claim_text = None
                        # Handle string items: ["claim1", "claim2"]
                        if isinstance(item, str):
                            claim_text = item.strip()
                        # Handle object items: [{"claim": "..."}, {"claim": "..."}]
                        elif isinstance(item, dict):
                            claim_text = item.get("claim", item.get("text", item.get("statement", ""))).strip()
                        
                        # Add if valid (min 5 chars to catch short Dutch claims)
                        if claim_text and len(claim_text) >= 5:
                            valid_claims.append(claim_text)
                    
                    return valid_claims[:5]  # Max 5 claims
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error parsing claims: {e}")
        return None
    
    def _config_based_claim_extraction(self, text: str) -> List[str]:
        """Fallback: use configurable patterns for claim extraction"""
        try:
            from src.ai.claim_config import get_claim_config
            config = get_claim_config()
        except ImportError:
            # If config not available, use hardcoded defaults
            return self._simple_claim_extraction(text)
        
        sentences = re.split(r'[.!?]+', text)
        claims = []
        
        # Flatten all skip patterns
        all_skip_patterns = []
        for patterns in config.skip_patterns.values():
            all_skip_patterns.extend(patterns)
        
        # Flatten all fact indicators
        all_fact_indicators = []
        for patterns in config.fact_indicators.values():
            all_fact_indicators.extend(patterns)
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Check minimum requirements
            if len(sentence) < config.min_sentence_length:
                continue
            if len(sentence.split()) < config.min_word_count:
                continue
            
            lower_sentence = sentence.lower()
            
            # Skip if matches any skip pattern
            if any(re.search(p, lower_sentence) for p in all_skip_patterns):
                continue
            
            # Must have at least one fact indicator
            if any(re.search(p, lower_sentence, re.IGNORECASE) for p in all_fact_indicators):
                claims.append(sentence)
        
        return claims[:config.max_claims_to_extract]
    
    def _simple_claim_extraction(self, text: str) -> List[str]:
        """Legacy fallback - delegates to config-based extraction"""
        return self._config_based_claim_extraction(text)
    
    def _legacy_simple_claim_extraction(self, text: str) -> List[str]:
        """Hardcoded fallback if config system fails - only extract VERIFIABLE facts"""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Must be substantial (more than just a few words)
            if len(sentence) < 20:
                continue
            
            word_count = len(sentence.split())
            if word_count < 4:
                continue
            
            lower_sentence = sentence.lower()
            
            # Skip conversational fragments and opinions (English + Dutch)
            skip_patterns = [
                # English conversational
                r'^(hi|hello|hey|okay|ok|yes|no|um|uh|well|so|and|but|or|then)\b',
                r'^(i think|i believe|i feel|maybe|perhaps|probably|i guess|i want|i need|i wish)\b',
                r'^(what|how|why|where|when|who|which|could|would|should|can|will)\b',
                r'\?$',  # Questions
                # Dutch conversational
                r'^(ja|nee|nou|dus|en|of|maar|want|hoi|hallo|hey|oké|ok)\b',
                r'^(ik denk|ik geloof|ik voel|misschien|wellicht|waarschijnlijk|ik wil|ik moet)\b',
                r'^(wat|hoe|waarom|waar|wanneer|wie|welke|zou|kan|zal|wil)\b',
                # Very vague statements
                r'^(it is|het is|this is|dit is|that is|dat is)\s+(all|allemaal|everything|alles|very|heel|so|zo)\b',
                r'\b(vervelend|annoying|boring|saai|interesting|interessant)\b',  # Opinions
                # Recording/testing meta-talk
                r'\b(recording|opname|test|testen|luister|listen)\b',
            ]
            
            if any(re.search(p, lower_sentence) for p in skip_patterns):
                continue
            
            # MUST contain indicators of a factual claim
            # These are words/patterns that suggest verifiable information
            fact_indicators = [
                r'\b\d+\b',  # Contains numbers
                r'\b(percent|procent|%)\b',  # Percentages
                r'\b(million|miljoen|billion|miljard|thousand|duizend)\b',  # Large numbers
                r'\b(always|never|altijd|nooit|every|elk|all|alle)\b',  # Absolute statements
                r'\b(is|are|was|were|heeft|hebben|was|waren|wordt|worden)\s+\w+\s+(the|de|het|a|een)\b',  # Definitional
                r'\b(according to|volgens|based on|gebaseerd op|research|onderzoek|study|studie)\b',  # Sources
                r'\b(founded|opgericht|established|gevestigd|created|gemaakt)\b',  # Historical
                r'\b(located|gelegen|based in|gevestigd in)\b',  # Location facts
                r'\b(costs?|kost|price|prijs|worth|waard)\b',  # Financial
                r'\b(invented|uitgevonden|discovered|ontdekt|developed|ontwikkeld)\b',  # Discoveries
            ]
            
            # Only include if it contains a fact indicator
            if any(re.search(p, lower_sentence) for p in fact_indicators):
                claims.append(sentence)
        
        return claims[:5]  # Limit to 5 actual claims
    
    async def _gather_context(
        self,
        claims: List[str],
        brand_id: Optional[str],
        client_id: Optional[str],
        person_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Gather relevant context from documents and profiles"""
        context = []
        
        # Search vector database for relevant documents
        if self.vector_store:
            for claim in claims[:5]:  # Limit searches
                try:
                    results = await self.vector_store.search_documents(claim, limit=3)
                    for result in results:
                        context.append({
                            "type": "document",
                            "source": result.metadata.get("filename", "Unknown"),
                            "content": result.content,
                            "score": result.score
                        })
                except Exception as e:
                    logger.warning(f"Vector search failed for claim: {e}")
        
        # Get brand profile facts
        if self.profile_manager and brand_id:
            try:
                brand = await self.profile_manager.get_brand_profile(brand_id)
                if brand:
                    # Add official statements
                    for statement in brand.official_statements:
                        context.append({
                            "type": "brand_statement",
                            "source": f"Brand: {brand.name}",
                            "content": statement,
                            "score": 1.0
                        })
                    # Add facts
                    for fact in brand.facts:
                        context.append({
                            "type": "brand_fact",
                            "source": f"Brand: {brand.name}",
                            "content": fact.statement,
                            "score": fact.confidence
                        })
                    # Add values and guidelines
                    context.append({
                        "type": "brand_values",
                        "source": f"Brand: {brand.name}",
                        "content": f"Values: {', '.join(brand.values)}. Guidelines: {', '.join(brand.guidelines)}",
                        "score": 1.0
                    })
            except Exception as e:
                logger.warning(f"Failed to get brand profile: {e}")
        
        # Get client profile facts
        if self.profile_manager and client_id:
            try:
                client = await self.profile_manager.get_client_profile(client_id)
                if client:
                    for fact in client.facts:
                        context.append({
                            "type": "client_fact",
                            "source": f"Client: {client.name}",
                            "content": fact.statement,
                            "score": fact.confidence
                        })
            except Exception as e:
                logger.warning(f"Failed to get client profile: {e}")
        
        # Get person profile facts
        if self.profile_manager and person_id:
            try:
                person = await self.profile_manager.get_person_profile(person_id)
                if person:
                    for fact in person.facts:
                        context.append({
                            "type": "person_fact",
                            "source": f"Person: {person.name}",
                            "content": fact.statement,
                            "score": fact.confidence
                        })
                    for statement in person.known_statements:
                        context.append({
                            "type": "person_statement",
                            "source": f"Person: {person.name}",
                            "content": statement,
                            "score": 1.0
                        })
            except Exception as e:
                logger.warning(f"Failed to get person profile: {e}")
        
        # Deduplicate and sort by score
        seen = set()
        unique_context = []
        for ctx in context:
            key = ctx["content"][:100]  # First 100 chars as key
            if key not in seen:
                seen.add(key)
                unique_context.append(ctx)
        
        unique_context.sort(key=lambda x: x.get("score", 0), reverse=True)
        return unique_context[:20]  # Limit context size
    
    async def _verify_claim(
        self,
        claim: str,
        context: List[Dict[str, Any]]
    ) -> ClaimVerification:
        """Verify a single claim against available context"""
        
        if not self.llm:
            # Fallback: no verification possible
            return ClaimVerification(
                claim=claim,
                verdict="UNVERIFIABLE",
                confidence=0.5,
                explanation="No AI model available for verification",
                sources=[]
            )
        
        # Build context string
        context_str = ""
        if context:
            context_str = "\n\nAVAILABLE CONTEXT:\n"
            for i, ctx in enumerate(context[:10], 1):  # Limit to 10 context items
                context_str += f"\n[Source {i}: {ctx['type']} - {ctx['source']}]\n{ctx['content'][:500]}\n"
        
        prompt = """You are a fact-checker. Verify this claim using the provided context.

CLAIM TO VERIFY:
\"\"\"{claim}\"\"\"
{context}

INSTRUCTIONS:
1. Compare the claim against the available context
2. If no relevant context, use your knowledge but mark as lower confidence
3. Consider partial truths and nuances

Respond with ONLY valid JSON in this format:
{{
    "verdict": "VERIFIED" | "FALSE" | "PARTIALLY_TRUE" | "UNVERIFIABLE" | "OPINION",
    "confidence": 0.0 to 1.0,
    "explanation": "Brief explanation of your verdict",
    "supporting_sources": ["Source 1 name", "Source 2 name"]
}}
"""
        
        try:
            response = await self.llm.generate(
                prompt.format(claim=claim, context=context_str if context else "\n\nNo specific context available.")
            )
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                
                # Build sources list
                sources = []
                for source_name in result.get("supporting_sources", []):
                    for ctx in context:
                        if ctx["source"] in source_name or source_name in ctx["source"]:
                            sources.append({
                                "type": ctx["type"],
                                "name": ctx["source"],
                                "excerpt": ctx["content"][:200]
                            })
                            break
                
                return ClaimVerification(
                    claim=claim,
                    verdict=result.get("verdict", "UNVERIFIABLE"),
                    confidence=result.get("confidence", 0.5),
                    explanation=result.get("explanation", ""),
                    sources=sources
                )
                
        except Exception as e:
            logger.warning(f"Claim verification failed: {e}")
        
        return ClaimVerification(
            claim=claim,
            verdict="UNVERIFIABLE",
            confidence=0.5,
            explanation="Verification failed",
            sources=[]
        )
    
    async def _generate_summary(
        self,
        verifications: List[ClaimVerification],
        credibility_score: Optional[float]
    ) -> str:
        """Generate a summary of the fact-check results"""
        
        parts = []
        
        verified = [v for v in verifications if v.verdict == "VERIFIED"]
        false = [v for v in verifications if v.verdict == "FALSE"]
        partial = [v for v in verifications if v.verdict == "PARTIALLY_TRUE"]
        
        if verified:
            parts.append(f"✅ {len(verified)} claim(s) verified")
        if false:
            parts.append(f"❌ {len(false)} claim(s) false")
        if partial:
            parts.append(f"⚠️ {len(partial)} claim(s) partially true")
        
        summary = ", ".join(parts) if parts else "No claims to verify"
        if credibility_score is not None:
            summary += f". Credibility score: {credibility_score:.0%}"
        
        # Add specific false claims
        if false:
            summary += f"\n\n**False claims detected:**\n"
            for v in false[:3]:
                summary += f"- {v.claim}: {v.explanation}\n"
        
        return summary
    
    def format_for_display(self, result: FactCheckResult) -> str:
        """Format result for display in UI"""
        lines = []
        
        lines.append(f"*Claim Analysis ({result.claims_verified}/{result.claims_found} verified):*")
        
        for v in result.verifications:
            icon = {
                "VERIFIED": "✅",
                "FALSE": "❌",
                "PARTIALLY_TRUE": "⚠️",
                "UNVERIFIABLE": "❓",
                "OPINION": "💭"
            }.get(v.verdict, "❓")
            
            lines.append(f"{v.verdict}|{v.claim}|{v.explanation}")
        
        return "\n".join(lines)


# Singleton instance
_fact_checker: Optional[IntelligentFactChecker] = None


async def get_fact_checker() -> IntelligentFactChecker:
    """Get or create the global fact checker"""
    global _fact_checker
    if _fact_checker is None:
        _fact_checker = IntelligentFactChecker()
        await _fact_checker.initialize()
    return _fact_checker


async def check_facts_intelligent(
    text: str,
    brand_id: Optional[str] = None,
    client_id: Optional[str] = None,
    person_id: Optional[str] = None
) -> FactCheckResult:
    """Convenience function to check facts"""
    checker = await get_fact_checker()
    return await checker.check_facts(text, brand_id, client_id, person_id)

