"""
LLAMA AI Processing Module for Brutally Honest AI
Handles audio transcription and analysis using local LLAMA models
"""

import asyncio
import logging
import json
import tempfile
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class AIProcessingResult:
    """Result from AI processing with fact-checking"""
    success: bool
    transcription: Optional[str] = None
    analysis: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    keywords: Optional[list] = None
    fact_check: Optional[str] = None
    brutal_honesty: Optional[str] = None
    credibility_score: Optional[float] = None
    questionable_claims: Optional[list] = None
    corrections: Optional[list] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None

class LLAMAProcessor:
    """LLAMA AI processor for audio analysis"""
    
    def __init__(self, model_path: str = None, whisper_model: str = "base"):
        self.model_path = model_path or "llama-2-7b-chat.gguf"  # Default model
        self.whisper_model = whisper_model
        self.is_initialized = False
        
        # Check if models are available
        self.whisper_available = self._check_whisper()
        self.llama_available = self._check_llama()
        
    def _check_whisper(self) -> bool:
        """Check if Whisper is available for transcription"""
        try:
            import whisper
            return True
        except ImportError:
            logger.warning("Whisper not available - install with: pip install openai-whisper")
            return False
    
    def _check_llama(self) -> bool:
        """Check if LLAMA is available"""
        try:
            # Check for llama-cpp-python
            import llama_cpp
            return True
        except ImportError:
            try:
                # Check for ollama
                import requests
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                return response.status_code == 200
            except:
                logger.warning("LLAMA not available - install llama-cpp-python or run Ollama")
                return False
    
    async def initialize(self) -> bool:
        """Initialize the AI models"""
        try:
            if self.whisper_available:
                import whisper
                logger.info(f"🎤 Loading Whisper model: {self.whisper_model}")
                self.whisper = whisper.load_model(self.whisper_model)
                logger.info("✅ Whisper model loaded successfully")
            
            if self.llama_available:
                try:
                    # Try llama-cpp-python first
                    from llama_cpp import Llama
                    logger.info(f"🦙 Loading LLAMA model: {self.model_path}")
                    self.llama = Llama(
                        model_path=self.model_path,
                        n_ctx=2048,  # Context window
                        n_threads=4,  # CPU threads
                        verbose=False
                    )
                    self.llama_type = "cpp"
                    logger.info("✅ LLAMA model loaded successfully")
                except Exception as e:
                    # Fall back to Ollama
                    logger.info("📡 Using Ollama for LLAMA processing")
                    self.llama_type = "ollama"
                    self.llama = None
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI models: {e}")
            return False
    
    async def transcribe_audio(self, audio_data: bytes, filename: str = "audio.wav") -> str:
        """Transcribe audio using Whisper"""
        if not self.whisper_available:
            return "Transcription not available - Whisper not installed"
        
        try:
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Transcribe using Whisper
            logger.info(f"🎤 Transcribing audio: {filename}")
            result = self.whisper.transcribe(temp_path)
            
            # Clean up temp file
            os.unlink(temp_path)
            
            transcription = result["text"].strip()
            logger.info(f"✅ Transcription completed: {len(transcription)} characters")
            
            return transcription
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return f"Transcription failed: {str(e)}"
    
    async def analyze_with_llama(self, transcription: str, filename: str) -> Dict[str, Any]:
        """Analyze transcription using LLAMA with fact-checking"""
        if not self.llama_available:
            return {
                "analysis": "LLAMA analysis not available - model not loaded",
                "sentiment": "neutral",
                "summary": "Analysis unavailable",
                "keywords": [],
                "fact_check": "Fact-checking unavailable",
                "brutal_honesty": "Analysis system not available",
                "credibility_score": 0.5,
                "questionable_claims": [],
                "corrections": []
            }
        
        try:
            # Create enhanced analysis prompt with fact-checking
            prompt = f"""
You are a brutally honest AI fact-checker and analyst. Analyze this audio transcription and provide comprehensive insights with fact-checking:

Transcription: "{transcription}"

Your task is to be BRUTALLY HONEST and fact-check every claim. Please provide:

1. **Content Analysis**: Brief analysis of the content and context
2. **Sentiment**: Overall emotional tone (positive, negative, neutral)
3. **Summary**: Concise 1-2 sentence summary
4. **Keywords**: Key topics mentioned
5. **Fact Check**: Rigorous fact-checking of all claims made
6. **Brutal Honesty**: Your brutally honest assessment of the speaker's credibility and accuracy
7. **Credibility Score**: Rate from 0.0 to 1.0 based on factual accuracy
8. **Questionable Claims**: List any dubious or unverified statements
9. **Corrections**: Provide corrections for any false or misleading information

Be thorough, critical, and don't hold back. If someone makes unsubstantiated claims, call them out. If they're being misleading, expose it. If they're stating facts correctly, acknowledge it.

Respond in JSON format:
{{
    "analysis": "detailed content analysis here",
    "sentiment": "positive/negative/neutral",
    "summary": "brief summary here",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "fact_check": "comprehensive fact-checking analysis",
    "brutal_honesty": "brutally honest assessment of credibility and accuracy",
    "credibility_score": 0.0-1.0,
    "questionable_claims": ["claim1", "claim2"],
    "corrections": ["correction1", "correction2"]
}}
"""
            
            logger.info(f"🦙 Analyzing transcription with LLAMA: {filename}")
            
            if self.llama_type == "cpp":
                # Use llama-cpp-python
                response = self.llama(
                    prompt,
                    max_tokens=512,
                    temperature=0.7,
                    stop=["</s>", "\n\n"]
                )
                result_text = response["choices"][0]["text"]
            else:
                # Use Ollama API
                import requests
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama2:7b",  # Use the specific model we have
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=30
                )
                response_data = response.json()
                result_text = response_data.get("response", "")
            
            # Try to parse JSON response
            try:
                result = json.loads(result_text)
                logger.info("✅ LLAMA analysis completed successfully")
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured response
                logger.warning("LLAMA response not in JSON format, creating structured response")
                return {
                    "analysis": result_text,
                    "sentiment": "neutral",
                    "summary": result_text[:100] + "..." if len(result_text) > 100 else result_text,
                    "keywords": [],
                    "fact_check": "Unable to parse fact-check results from LLAMA response",
                    "brutal_honesty": result_text[:200] + "..." if len(result_text) > 200 else result_text,
                    "credibility_score": 0.5,
                    "questionable_claims": [],
                    "corrections": []
                }
                
        except Exception as e:
            logger.error(f"LLAMA analysis failed: {e}")
            return {
                "analysis": f"Analysis failed: {str(e)}",
                "sentiment": "neutral",
                "summary": "Analysis unavailable",
                "keywords": [],
                "fact_check": f"Fact-checking failed: {str(e)}",
                "brutal_honesty": "Unable to provide brutal honesty assessment due to system error",
                "credibility_score": 0.0,
                "questionable_claims": [],
                "corrections": []
            }
    
    async def process_audio(self, audio_data: bytes, filename: str) -> AIProcessingResult:
        """Complete audio processing pipeline"""
        import time
        start_time = time.time()
        
        try:
            if not self.is_initialized:
                await self.initialize()
            
            logger.info(f"🤖 Starting AI processing for: {filename}")
            
            # Step 1: Transcribe audio
            transcription = await self.transcribe_audio(audio_data, filename)
            
            if transcription.startswith("Transcription failed"):
                return AIProcessingResult(
                    success=False,
                    error=transcription,
                    processing_time=time.time() - start_time
                )
            
            # Step 2: Analyze with LLAMA
            analysis_result = await self.analyze_with_llama(transcription, filename)
            
            processing_time = time.time() - start_time
            
            # Calculate confidence based on transcription length and quality
            confidence = min(0.95, len(transcription) / 100.0) if transcription else 0.1
            
            result = AIProcessingResult(
                success=True,
                transcription=transcription,
                analysis=analysis_result.get("analysis", "No analysis available"),
                summary=analysis_result.get("summary", "No summary available"),
                sentiment=analysis_result.get("sentiment", "neutral"),
                keywords=analysis_result.get("keywords", []),
                fact_check=analysis_result.get("fact_check", "No fact-checking performed"),
                brutal_honesty=analysis_result.get("brutal_honesty", "No brutal honesty assessment available"),
                credibility_score=analysis_result.get("credibility_score", 0.5),
                questionable_claims=analysis_result.get("questionable_claims", []),
                corrections=analysis_result.get("corrections", []),
                confidence=confidence,
                processing_time=processing_time
            )
            
            logger.info(f"✅ AI processing completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            return AIProcessingResult(
                success=False,
                error=str(e),
                processing_time=time.time() - start_time
            )

# Global processor instance
_processor = None

async def get_processor() -> LLAMAProcessor:
    """Get or create the global LLAMA processor"""
    global _processor
    if _processor is None:
        _processor = LLAMAProcessor()
        await _processor.initialize()
    return _processor

# Example usage
async def main():
    """Example usage of LLAMA processor"""
    processor = await get_processor()
    
    # Test with dummy audio data
    dummy_wav = b"RIFF" + b"\x00" * 100  # Dummy WAV data
    result = await processor.process_audio(dummy_wav, "test.wav")
    
    print(f"Success: {result.success}")
    if result.success:
        print(f"Transcription: {result.transcription}")
        print(f"Analysis: {result.analysis}")
        print(f"Sentiment: {result.sentiment}")
        print(f"Processing time: {result.processing_time:.2f}s")
    else:
        print(f"Error: {result.error}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
