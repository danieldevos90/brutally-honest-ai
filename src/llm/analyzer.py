"""
Local LLM Analyzer for Fact-Checking and Feedback
Uses Ollama for local LLM inference
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import requests
from ..audio.processor import AudioProcessingResult

logger = logging.getLogger(__name__)

@dataclass
class FactCheckResult:
    """Result of fact-checking analysis"""
    is_accurate: bool
    confidence: float
    issues: List[str]
    corrections: List[str]
    sources: List[str]

@dataclass
class FeedbackResult:
    """Feedback and insights"""
    summary: str
    suggestions: List[str]
    accuracy_score: float
    process_alignment: float
    key_points: List[str]

@dataclass
class AnalysisResult:
    """Complete analysis result"""
    fact_check: FactCheckResult
    feedback: FeedbackResult
    timestamp: datetime
    confidence: float

class LLMAnalyzer:
    """Local LLM analyzer using Ollama"""
    
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model_name = os.getenv("LLM_MODEL", "mistral:7b")
        self.is_initialized = False
        
        # Company knowledge base (this would be loaded from your vector DB)
        self.knowledge_base = self._load_knowledge_base()
    
    async def initialize(self) -> bool:
        """Initialize LLM connection"""
        try:
            logger.info("Initializing LLM analyzer...")
            
            # Check if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                if self.model_name in model_names:
                    logger.info(f"LLM model {self.model_name} is available")
                    self.is_initialized = True
                    return True
                else:
                    logger.warning(f"Model {self.model_name} not found. Available models: {model_names}")
                    # Try to pull the model
                    await self._pull_model()
                    return True
            else:
                logger.error(f"Ollama not accessible at {self.ollama_url}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize LLM analyzer: {e}")
            logger.warning("LLM analyzer will run in offline mode")
            self.is_initialized = False
            return False
    
    async def _pull_model(self):
        """Pull the specified model if not available"""
        try:
            logger.info(f"Pulling model {self.model_name}...")
            response = requests.post(
                f"{self.ollama_url}/api/pull",
                json={"name": self.model_name},
                timeout=300  # 5 minutes timeout for model download
            )
            if response.status_code == 200:
                logger.info(f"Model {self.model_name} pulled successfully")
                self.is_initialized = True
            else:
                logger.error(f"Failed to pull model: {response.text}")
        except Exception as e:
            logger.error(f"Error pulling model: {e}")
    
    def is_ready(self) -> bool:
        """Check if analyzer is ready"""
        return self.is_initialized
    
    async def analyze_transcript(self, audio_result: AudioProcessingResult) -> AnalysisResult:
        """Analyze transcript for fact-checking and feedback"""
        try:
            logger.info("Analyzing transcript with LLM...")
            
            # Perform fact-checking
            fact_check = await self._fact_check_transcript(audio_result.transcript)
            
            # Generate feedback
            feedback = await self._generate_feedback(audio_result)
            
            # Calculate overall confidence
            overall_confidence = (fact_check.confidence + audio_result.confidence) / 2
            
            return AnalysisResult(
                fact_check=fact_check,
                feedback=feedback,
                timestamp=datetime.now(),
                confidence=overall_confidence
            )
            
        except Exception as e:
            logger.error(f"Error analyzing transcript: {e}")
            # Return fallback analysis
            return self._create_fallback_analysis(audio_result)
    
    async def _fact_check_transcript(self, transcript: str) -> FactCheckResult:
        """Perform fact-checking against knowledge base"""
        if not self.is_initialized:
            return self._create_fallback_fact_check()
        
        try:
            # Prepare context from knowledge base
            relevant_context = self._get_relevant_context(transcript)
            
            # Create fact-checking prompt
            prompt = self._create_fact_check_prompt(transcript, relevant_context)
            
            # Query LLM
            response = await self._query_llm(prompt)
            
            # Parse response
            return self._parse_fact_check_response(response)
            
        except Exception as e:
            logger.error(f"Fact-checking error: {e}")
            return self._create_fallback_fact_check()
    
    async def _generate_feedback(self, audio_result: AudioProcessingResult) -> FeedbackResult:
        """Generate feedback and suggestions"""
        if not self.is_initialized:
            return self._create_fallback_feedback()
        
        try:
            # Create feedback prompt
            prompt = self._create_feedback_prompt(audio_result)
            
            # Query LLM
            response = await self._query_llm(prompt)
            
            # Parse response
            return self._parse_feedback_response(response)
            
        except Exception as e:
            logger.error(f"Feedback generation error: {e}")
            return self._create_fallback_feedback()
    
    async def _query_llm(self, prompt: str) -> str:
        """Query local LLM via Ollama"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent results
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"LLM query failed: {response.text}")
                return ""
                
        except Exception as e:
            logger.error(f"LLM query error: {e}")
            return ""
    
    def _create_fact_check_prompt(self, transcript: str, context: str) -> str:
        """Create prompt for brutally honest fact-checking"""
        return f"""
You are a brutally honest fact-checking AI. You ALWAYS start your responses with "Let me be brutally honest..." and then tell the unvarnished truth without sugar-coating anything.

COMPANY KNOWLEDGE:
{context}

STATEMENT TO CHECK:
"{transcript}"

Analyze this statement and respond in JSON format, but make your "brutal_response" field conversational and direct:
{{
    "brutal_response": "Let me be brutally honest... [your direct, honest assessment]",
    "is_accurate": true/false,
    "confidence": 0.0-1.0,
    "issues": ["list of factual issues found"],
    "corrections": ["list of corrections needed"],
    "sources": ["relevant knowledge base sections"],
    "honesty_level": "brutal"
}}

Your brutal_response should:
1. Start with "Let me be brutally honest..."
2. Point out exactly what's wrong or questionable
3. Be direct but not insulting
4. Highlight gaps in reasoning or evidence
5. Call out assumptions or oversimplifications

Examples of brutal honesty:
- "Let me be brutally honest... that statement sounds confident but lacks any supporting evidence."
- "Let me be brutally honest... you're making assumptions that aren't backed by the data we have."
- "Let me be brutally honest... while technically correct, you're missing the bigger picture here."
"""
    
    def _create_feedback_prompt(self, audio_result: AudioProcessingResult) -> str:
        """Create prompt for feedback generation"""
        return f"""
You are a communication coach providing feedback on spoken statements.

TRANSCRIPT: "{audio_result.transcript}"
SPEAKERS: {len(audio_result.speakers)} speaker(s)
DURATION: {audio_result.audio_duration:.1f} seconds

Provide constructive feedback in JSON format:
{{
    "summary": "brief summary of the statement",
    "suggestions": ["list of improvement suggestions"],
    "accuracy_score": 0.0-1.0,
    "process_alignment": 0.0-1.0,
    "key_points": ["main points identified"]
}}

Focus on:
1. Clarity and coherence
2. Completeness of information
3. Professional communication
4. Areas for improvement
"""
    
    def _get_relevant_context(self, transcript: str) -> str:
        """Get relevant context from knowledge base"""
        # This is a simplified version. In production, you'd use vector search
        # with Qdrant or similar to find relevant documents
        
        relevant_docs = []
        transcript_lower = transcript.lower()
        
        for doc in self.knowledge_base:
            # Simple keyword matching (replace with semantic search)
            if any(keyword in transcript_lower for keyword in doc.get("keywords", [])):
                relevant_docs.append(doc["content"])
        
        return "\n\n".join(relevant_docs[:3])  # Limit to top 3 relevant docs
    
    def _parse_fact_check_response(self, response: str) -> FactCheckResult:
        """Parse LLM response for brutally honest fact-checking"""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                # Create a custom FactCheckResult that includes brutal honesty
                result = FactCheckResult(
                    is_accurate=data.get("is_accurate", False),
                    confidence=float(data.get("confidence", 0.5)),
                    issues=data.get("issues", []),
                    corrections=data.get("corrections", []),
                    sources=data.get("sources", [])
                )
                
                # Add brutal honesty response as an additional attribute
                result.brutal_response = data.get("brutal_response", "Let me be brutally honest... I couldn't analyze that properly.")
                result.honesty_level = data.get("honesty_level", "brutal")
                
                return result
            else:
                # Fallback parsing
                return self._create_fallback_fact_check()
                
        except Exception as e:
            logger.error(f"Error parsing fact-check response: {e}")
            return self._create_fallback_fact_check()
    
    def _parse_feedback_response(self, response: str) -> FeedbackResult:
        """Parse LLM response for feedback"""
        try:
            # Try to extract JSON from response
            if "{" in response and "}" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                
                return FeedbackResult(
                    summary=data.get("summary", "No summary available"),
                    suggestions=data.get("suggestions", []),
                    accuracy_score=float(data.get("accuracy_score", 0.7)),
                    process_alignment=float(data.get("process_alignment", 0.7)),
                    key_points=data.get("key_points", [])
                )
            else:
                return self._create_fallback_feedback()
                
        except Exception as e:
            logger.error(f"Error parsing feedback response: {e}")
            return self._create_fallback_feedback()
    
    def _load_knowledge_base(self) -> List[Dict[str, Any]]:
        """Load company knowledge base"""
        # This is a placeholder. In production, you'd load from your vector database
        return [
            {
                "id": "company_policy_1",
                "content": "Company policy states that all customer data must be handled according to GDPR regulations.",
                "keywords": ["gdpr", "data", "privacy", "customer", "policy"]
            },
            {
                "id": "product_info_1", 
                "content": "Our main product is a voice analysis platform that processes audio locally in the EU.",
                "keywords": ["product", "voice", "analysis", "audio", "eu", "local"]
            },
            {
                "id": "process_1",
                "content": "All audio processing must be done locally using Whisper and local LLMs, never cloud services.",
                "keywords": ["audio", "processing", "whisper", "llm", "local", "cloud"]
            }
        ]
    
    def _create_fallback_analysis(self, audio_result: AudioProcessingResult) -> AnalysisResult:
        """Create fallback analysis when LLM is not available"""
        return AnalysisResult(
            fact_check=self._create_fallback_fact_check(),
            feedback=self._create_fallback_feedback(),
            timestamp=datetime.now(),
            confidence=0.5
        )
    
    def _create_fallback_fact_check(self) -> FactCheckResult:
        """Create fallback fact-check result with brutal honesty"""
        result = FactCheckResult(
            is_accurate=True,  # Assume accurate when can't verify
            confidence=0.5,
            issues=["Unable to verify due to system limitations"],
            corrections=["Verify claims independently"],
            sources=["LLM analyzer offline"]
        )
        # Add brutal honesty attributes
        result.brutal_response = "Let me be brutally honest... I can't properly fact-check that right now because my analysis system is offline. Don't take that as validation - you should still verify your claims."
        result.honesty_level = "brutal"
        return result
    
    def _create_fallback_feedback(self) -> FeedbackResult:
        """Create fallback feedback result"""
        return FeedbackResult(
            summary="Audio processed successfully",
            suggestions=["LLM analyzer is offline - limited feedback available"],
            accuracy_score=0.7,
            process_alignment=0.7,
            key_points=["Audio captured and transcribed"]
        )
    
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up LLM analyzer...")
        self.is_initialized = False
