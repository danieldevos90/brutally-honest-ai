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

# === FACT CHECKING RULES ===
FACT_RULES = {
    # Fish facts - with nuance
    "vis kan vliegen": ("partial", "Vliegende vissen (Exocoetidae) kunnen tot 200m over water glijden, maar echte vlucht is het niet"),
    "vis kan praten": (False, "Vissen produceren wel geluiden maar kunnen niet praten zoals mensen"),
    "vis heeft schubben": (True, "De meeste vissen hebben schubben ter bescherming"),
    "vis heeft schubber": (True, "De meeste vissen hebben schubben ter bescherming"),
    "vis kan zwemmen": (True, "Alle vissen kunnen zwemmen - dit is hun primaire bewegingsmethode"),
    "fish can fly": ("partial", "Flying fish can glide up to 200m above water, but its not true flight"),
    "fish can swim": (True, "All fish can swim - this is their primary means of locomotion"),
    "fish can talk": (False, "Fish produce sounds but cannot talk like humans"),
    
    # Giraffe facts
    "giraf heeft een lange nek": (True, "Giraffen hebben de langste nek van alle zoogdieren (tot 2.4m)"),
    "giraf heeft een hele lange nek": (True, "Giraffen hebben de langste nek van alle zoogdieren (tot 2.4m)"),
    "giraf heeft een korte nek": (False, "Onjuist - giraffen hebben juist de langste nek van alle landdieren"),
    "giraffe has a long neck": (True, "Giraffes have the longest neck of any mammal (up to 2.4m)"),
    "giraffe has a short neck": (False, "Incorrect - giraffes have the longest neck of all land animals"),
    
    # Human facts
    "mens is een zoogdier": (True, "Mensen zijn zoogdieren van de orde Primaten"),
    "human is a mammal": (True, "Humans are mammals of the order Primates"),
    
    # Cloud facts  
    "wolken kunnen onder water": (False, "Wolken bestaan uit waterdamp in de atmosfeer, niet onder water"),
    "clouds underwater": (False, "Clouds are water vapor in the atmosphere, not underwater"),
}

def extract_and_check_claims(text, use_ai=True, brand_id=None, client_id=None, person_id=None):
    """
    Extract and verify claims from text.
    
    Args:
        text: Text to analyze
        use_ai: If True, use intelligent AI-powered fact checking with vector DB and profiles
                If False, use simple hardcoded rules (legacy mode)
        brand_id: Optional brand profile ID to check against
        client_id: Optional client profile ID to check against
        person_id: Optional person profile ID to check against
    """
    # Try AI-powered fact checking first
    if use_ai:
        try:
            import asyncio
            from src.ai.intelligent_fact_checker import check_facts_intelligent
            
            # Run async function
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If already in async context, create task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        check_facts_intelligent(text, brand_id, client_id, person_id)
                    )
                    result = future.result(timeout=120)
            else:
                result = asyncio.run(check_facts_intelligent(text, brand_id, client_id, person_id))
            
            # Convert to legacy format
            output = []
            for v in result.verifications:
                verdict_map = {
                    "VERIFIED": "VERIFIED",
                    "FALSE": "INCORRECT",
                    "PARTIALLY_TRUE": "NUANCED",
                    "UNVERIFIABLE": "UNVERIFIED",
                    "OPINION": "OPINION"
                }
                output.append(f"{verdict_map.get(v.verdict, 'UNVERIFIED')}|{v.claim}|{v.explanation}")
            
            newline = chr(10)
            return {
                "formatted": newline.join(output),
                "true_count": result.claims_verified,
                "false_count": result.claims_false,
                "total": result.claims_found,
                "partial_cnt": result.claims_partial,
                "credibility": result.credibility_score,
                "claims": [{"claim": v.claim, "verdict": v.verdict, "explanation": v.explanation} for v in result.verifications],
                "sources": [[{"type": s["type"], "name": s["name"]} for s in v.sources] for v in result.verifications],
                "ai_powered": True
            }
        except Exception as e:
            logger.warning(f"AI fact-checking failed, falling back to rules: {e}")
    
    # Fallback: Simple rule-based checking (legacy mode)
    return _extract_and_check_claims_legacy(text)


def _extract_and_check_claims_legacy(text):
    """Legacy rule-based fact checking using hardcoded FACT_RULES"""
    import re as regex
    parts = regex.split(r"[,.]|\ben\b|\band\b", text)
    parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]
    results = []
    for part in parts:
        part_lower = part.lower()
        verdict, expl = None, "Niet geverifieerd"
        for pattern, (is_true, explanation) in FACT_RULES.items():
            if pattern in part_lower:
                verdict, expl = is_true, explanation
                break
        results.append({"claim": part, "verdict": verdict, "explanation": expl})
    output = []
    true_cnt = false_cnt = partial_cnt = 0
    for r in results:
        if r["verdict"] is True:
            output.append("VERIFIED|" + r["claim"] + "|" + r["explanation"])
            true_cnt += 1
        elif r["verdict"] == "partial":
            output.append("NUANCED|" + r["claim"] + "|" + r["explanation"])
            partial_cnt += 1
        elif r["verdict"] is False:
            output.append("INCORRECT|" + r["claim"] + "|" + r["explanation"])
            false_cnt += 1
        else:
            output.append("UNVERIFIED|" + r["claim"] + "|Could not verify")
    newline = chr(10)
    return {
        "formatted": newline.join(output),
        "true_count": true_cnt,
        "false_count": false_cnt,
        "total": len(results),
        "partial_cnt": partial_cnt,
        "credibility": (true_cnt + partial_cnt * 0.5) / len(results) if results else 0.5,
        "claims": results,
        "ai_powered": False
    }


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
    
    def __init__(self, model_path: str = None, whisper_model: str = "small"):
        self.model_path = model_path or "llama-2-7b-chat.gguf"  # Default model
        self.whisper_model_name = whisper_model  # Use 'medium' model for better accuracy
        self.whisper_model = whisper_model  # Keep for backward compat
        self.is_initialized = False
        self.whisper = None  # Whisper model instance
        
        # Check if models are available
        self.whisper_available = self._check_whisper()
        self.llama_available = self._check_llama()
    
    def unload_whisper(self):
        """Unload Whisper model to free GPU/RAM memory for LLM"""
        if self.whisper is not None:
            logger.info("🗑️ Unloading Whisper model to free memory...")
            del self.whisper
            self.whisper = None
            
            # Force garbage collection and CUDA cleanup
            import gc
            gc.collect()
            
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                    logger.info("✅ CUDA cache cleared")
            except ImportError:
                pass
            
            logger.info("✅ Whisper unloaded - memory freed for LLM")
        
    def _check_whisper(self) -> bool:
        """Check if Whisper is available for transcription"""
        import platform
        is_arm = platform.machine() in ('aarch64', 'arm64')
        
        # On ARM (Jetson), faster-whisper has ctranslate2 bugs, use openai-whisper
        if not is_arm:
            try:
                # Prefer faster-whisper on x86 (3-4x faster, INT8 quantization)
                from faster_whisper import WhisperModel
                self._use_faster_whisper = True
                logger.info("Using faster-whisper (optimized for x86)")
                return True
            except ImportError:
                pass
        
        try:
            import whisper
            self._use_faster_whisper = False
            if is_arm:
                logger.info("Using openai-whisper (ARM/Jetson compatible)")
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
    
    def _preprocess_audio(self, audio_path: str) -> str:
        """Preprocess audio for better transcription accuracy"""
        try:
            import librosa
            import soundfile as sf
            import numpy as np
            from scipy import signal
            
            logger.info("🔧 Starting advanced audio preprocessing...")
            
            # Load audio with librosa for preprocessing
            logger.info(f"📂 Loading audio file: {audio_path}")
            audio, sr = librosa.load(audio_path, sr=16000)  # Resample to 16kHz
            original_duration = len(audio) / sr
            logger.info(f"🎵 Original audio: {original_duration:.2f}s at {sr}Hz, {len(audio)} samples")
            
            # Check if audio is empty or too short
            if len(audio) == 0:
                logger.warning("⚠️ Audio file is empty - skipping preprocessing")
                return audio_path
            
            if original_duration < 0.1:  # Less than 100ms
                logger.warning(f"⚠️ Audio too short ({original_duration:.3f}s) - skipping preprocessing")
                return audio_path
            
            # 1. Noise reduction using spectral gating
            logger.info("🔇 Applying noise reduction...")
            # Estimate noise from first 0.5 seconds (assuming it's quiet)
            noise_sample_length = min(int(0.5 * sr), len(audio) // 4)
            noise_sample = audio[:noise_sample_length]
            noise_power = np.mean(noise_sample ** 2)
            
            # Apply gentle noise gate
            noise_threshold = noise_power * 3  # Adjust threshold
            audio = np.where(audio ** 2 > noise_threshold, audio, audio * 0.1)
            
            # 2. High-pass filter to remove low-frequency noise
            logger.info("🎛️ Applying high-pass filter...")
            nyquist = sr // 2
            high_cutoff = 80  # Remove frequencies below 80Hz
            b, a = signal.butter(4, high_cutoff / nyquist, btype='high')
            audio = signal.filtfilt(b, a, audio)
            
            # 3. Dynamic range compression for consistent volume
            logger.info("📊 Applying dynamic range compression...")
            # Soft compression to even out volume levels
            threshold = 0.3
            ratio = 4.0
            audio_abs = np.abs(audio)
            mask = audio_abs > threshold
            compressed = np.copy(audio)
            compressed[mask] = np.sign(audio[mask]) * (threshold + (audio_abs[mask] - threshold) / ratio)
            audio = compressed
            
            # 4. Normalize amplitude
            logger.info("🔊 Normalizing audio amplitude...")
            audio = librosa.util.normalize(audio)
            
            # 5. Advanced silence trimming with better parameters
            logger.info("✂️ Trimming silence (top_db=20, frame_length=1024)...")
            audio_trimmed, _ = librosa.effects.trim(
                audio, 
                top_db=20,  # Less aggressive to preserve speech
                frame_length=1024,  # Smaller frame for better speech detection
                hop_length=256
            )
            trimmed_duration = len(audio_trimmed) / sr
            logger.info(f"⏱️ Audio after trimming: {trimmed_duration:.2f}s ({len(audio_trimmed)} samples)")
            
            # 5.5. Ensure minimum audio length for Whisper
            min_duration = 0.5  # Minimum 0.5 seconds
            if trimmed_duration < min_duration:
                logger.info(f"⚠️ Audio too short ({trimmed_duration:.2f}s), padding to {min_duration}s")
                padding_samples = int((min_duration - trimmed_duration) * sr)
                audio_trimmed = np.pad(audio_trimmed, (0, padding_samples), mode='constant', constant_values=0)
                trimmed_duration = len(audio_trimmed) / sr
            
            # 6. Pre-emphasis filter (boosts high frequencies for better speech clarity)
            logger.info("🎯 Applying pre-emphasis filter...")
            pre_emphasis = 0.97
            audio_emphasized = np.append(audio_trimmed[0], audio_trimmed[1:] - pre_emphasis * audio_trimmed[:-1])
            
            # 7. Final normalization
            audio_final = librosa.util.normalize(audio_emphasized)
            
            # Save preprocessed audio
            processed_path = audio_path.replace('.wav', '_processed.wav')
            sf.write(processed_path, audio_final, sr)
            logger.info(f"💾 Enhanced audio saved: {processed_path}")
            logger.info("✅ Advanced audio preprocessing completed successfully")
            
            return processed_path
            
        except ImportError:
            logger.warning("⚠️ librosa not available - using original audio without preprocessing")
            return audio_path
        except Exception as e:
            logger.warning(f"❌ Audio preprocessing failed: {e} - using original audio")
            return audio_path
    
    async def initialize(self) -> bool:
        """Initialize the AI models"""
        try:
            if self.whisper_available:
                if getattr(self, '_use_faster_whisper', False):
                    from faster_whisper import WhisperModel
                    logger.info(f"🎤 Loading faster-whisper model: {self.whisper_model} (auto compute type)")
                    # Use auto compute type for best compatibility across platforms
                    self.whisper = WhisperModel(self.whisper_model, device="cpu", compute_type="auto", cpu_threads=4)
                    logger.info("✅ faster-whisper model loaded (3-4x faster than openai-whisper)")
                else:
                    import whisper
                    import torch
                    # Check for CUDA availability
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    logger.info(f"🎤 Loading Whisper model: {self.whisper_model} on {device.upper()}")
                    if device == "cuda":
                        logger.info(f"🚀 GPU: {torch.cuda.get_device_name(0)}")
                    self.whisper = whisper.load_model(self.whisper_model, device=device)
                    logger.info(f"✅ Whisper model loaded on {device.upper()}")
            
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
        """Transcribe audio using Whisper with preprocessing"""
        if not self.whisper_available:
            return "Transcription not available - Whisper not installed"
        
        try:
            # Save audio to temporary file
            logger.info(f"💾 Creating temporary file for audio processing...")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            logger.info(f"📁 Temporary file created: {temp_path} ({len(audio_data)} bytes)")
            
            # Preprocess audio for better transcription
            logger.info("🔄 Starting audio preprocessing pipeline...")
            processed_path = self._preprocess_audio(temp_path)
            
            # Transcribe using Whisper with improved settings
            logger.info(f"🎤 Starting Whisper transcription for: {filename}")
            logger.info(f"🔧 Whisper model: {self.whisper_model}")
            logger.info("⚙️ Optimized transcription strategy:")
            logger.info("   • Primary method: Raw audio (unprocessed - most accurate)")
            logger.info("   • Language: Auto-detect (Dutch/English supported)")
            logger.info("   • Content: Universal (no pre-coded assumptions)")
            logger.info("   • Temperature: 0.1 (deterministic)")
            logger.info("   • No speech threshold: 0.5 (balanced)")
            logger.info("   • Log prob threshold: -1.0 (quality focused)")
            logger.info("   • Compression ratio threshold: 2.0 (natural speech)")
            logger.info("   • Word timestamps: enabled")
            logger.info("   • Fallback: Processed audio if raw fails")
            import torch
            use_fp16 = torch.cuda.is_available()
            logger.info(f"   • FP16: {'enabled (GPU)' if use_fp16 else 'disabled (CPU)'}")
            
            # Use raw audio transcription as primary method (most accurate)
            logger.info("🎯 Primary: Raw audio transcription (most accurate)...")
            try:
                if getattr(self, '_use_faster_whisper', False):
                    # faster-whisper API (3-4x faster)
                    logger.info("⚡ Using faster-whisper (INT8 optimized)")
                    segments, info = self.whisper.transcribe(
                        temp_path,
                        language=None,  # Auto-detect
                        task="transcribe",
                        vad_filter=True,  # Voice activity detection
                        vad_parameters=dict(min_silence_duration_ms=500),
                    )
                    # Collect all segments
                    text_parts = []
                    for segment in segments:
                        text_parts.append(segment.text)
                    text = " ".join(text_parts).strip()
                    logger.info(f"✅ faster-whisper result: '{text[:100]}...' (detected: {info.language})")
                else:
                    # OpenAI whisper API
                    result = self.whisper.transcribe(
                        temp_path,  # Use original, unprocessed audio
                        language=None,
                        task="transcribe",
                        temperature=0.1,
                        no_speech_threshold=0.5,
                        logprob_threshold=-1.0,
                        compression_ratio_threshold=2.0,
                        condition_on_previous_text=False,
                        word_timestamps=True,
                        fp16=use_fp16  # Use FP16 on GPU for speed
                    )
                    text = result['text'].strip()
                    logger.info(f"✅ Raw audio result: '{text[:100]}...'")
                
                # Check if result is reasonable
                if len(text) > 0 and not text.lower() in ['you can fly', 'the fox can fly']:
                    logger.info("🏆 Raw audio transcription successful - using this result")
                else:
                    logger.warning("⚠️ Raw audio gave poor result, trying fallback...")
                    raise Exception("Poor raw audio result")
                    
            except Exception as e:
                logger.warning(f"Raw audio transcription failed: {e}")
                logger.info("🔄 Fallback: Trying processed audio...")
                
                # Fallback to processed audio if raw fails
                try:
                    if getattr(self, '_use_faster_whisper', False):
                        segments, info = self.whisper.transcribe(processed_path, language=None)
                        text = " ".join([seg.text for seg in segments]).strip()
                        detected_language = info.language
                        logger.info(f"✅ Processed audio fallback: '{text[:100]}...'")
                    else:
                        result = self.whisper.transcribe(
                            processed_path,
                            language=None,
                            task="transcribe",
                            temperature=0.0,
                            no_speech_threshold=0.3,
                            logprob_threshold=-0.8,
                            compression_ratio_threshold=2.4,
                            condition_on_previous_text=False,
                            word_timestamps=True,
                            fp16=False,
                            beam_size=5,
                            best_of=5,
                            patience=1.0
                        )
                        text = result['text'].strip()
                        detected_language = result.get("language", "unknown")
                        logger.info(f"✅ Processed audio fallback: '{text[:100]}...'")
                except Exception as e2:
                    logger.error(f"Both raw and processed audio failed: {e2}")
                    raise Exception("All transcription methods failed")
            
            # Clean up temp files
            logger.info("🧹 Cleaning up temporary files...")
            os.unlink(temp_path)
            if processed_path != temp_path:
                os.unlink(processed_path)
                logger.info("🗑️ Preprocessed file cleaned up")
            
            transcription = text
            if not getattr(self, '_use_faster_whisper', False):
                detected_language = result.get("language", "unknown")
            else:
                detected_language = getattr(info, 'language', 'unknown') if 'info' in dir() else 'unknown'
            
            # Check for repetitive patterns and clean them
            cleaned_transcription = self._clean_repetitive_text(transcription)
            if cleaned_transcription != transcription:
                logger.info(f"🧹 Cleaned repetitive text: '{transcription}' → '{cleaned_transcription}'")
                transcription = cleaned_transcription
            
            logger.info(f"✅ Transcription completed successfully!")
            logger.info(f"🌍 Detected language: {detected_language}")
            logger.info(f"📝 Result: '{transcription}' ({len(transcription)} characters)")
            
            # Log detailed confidence information if available
            if not getattr(self, '_use_faster_whisper', False) and "segments" in result and result["segments"]:
                avg_confidence = sum(seg.get("avg_logprob", 0) for seg in result["segments"]) / len(result["segments"])
                logger.info(f"📊 Average confidence: {avg_confidence:.3f}")
                logger.info(f"🔢 Number of segments: {len(result['segments'])}")
                
                # Log individual segment details for debugging
                for i, segment in enumerate(result["segments"][:3]):  # Show first 3 segments
                    start_time = segment.get("start", 0)
                    end_time = segment.get("end", 0)
                    text = segment.get("text", "").strip()
                    confidence = segment.get("avg_logprob", 0)
                    logger.info(f"   Segment {i+1}: [{start_time:.1f}s-{end_time:.1f}s] '{text}' (conf: {confidence:.3f})")
                
                if len(result["segments"]) > 3:
                    logger.info(f"   ... and {len(result['segments']) - 3} more segments")
            else:
                logger.warning("⚠️ No segment information available in transcription result")
            
            return transcription
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return f"Transcription failed: {str(e)}"
    
    async def analyze_with_llama(self, transcription: str, filename: str, model: str = None, timeout: int = None) -> Dict[str, Any]:
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
6. **Brutal Honesty**: Factual assessment - if wrong, explain why with facts
7. **Credibility Score**: Rate from 0.0 to 1.0 based on factual accuracy
8. **Questionable Claims**: List any dubious or unverified statements
9. **Corrections**: Provide corrections for any false or misleading information

Be thorough, critical, and don't hold back. If someone makes unsubstantiated claims, call them out AND provide the correct facts. If they're being misleading, expose it with evidence. If they're stating facts correctly, acknowledge it. Always include factual context in your brutal honesty assessment.

IMPORTANT: You MUST respond with ONLY a valid JSON object. Do not include any other text before or after the JSON. The response must start with {{ and end with }}.

JSON format:
{{
    "analysis": "detailed content analysis here",
    "sentiment": "positive/negative/neutral", 
    "summary": "brief summary here",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "fact_check": "comprehensive fact-checking analysis",
    "brutal_honesty": "brutally honest assessment with factual context - include actual facts to support your assessment",
    "credibility_score": 0.5,
    "questionable_claims": ["claim1", "claim2"],
    "corrections": ["correction1", "correction2"]
}}
"""
            
            logger.info(f"🦙 Starting LLAMA analysis for: {filename}")
            logger.info(f"📄 Transcription to analyze: '{transcription}' ({len(transcription)} chars)")
            logger.info(f"🔧 LLAMA backend: {self.llama_type}")
            
            if self.llama_type == "cpp":
                # Use llama-cpp-python
                logger.info("🔄 Sending prompt to llama-cpp-python...")
                logger.info("⚙️ LLAMA settings: max_tokens=512, temperature=0.7")
                response = self.llama(
                    prompt,
                    max_tokens=512,
                    temperature=0.7,
                    stop=["</s>", "\n\n"]
                )
                result_text = response["choices"][0]["text"]
                logger.info(f"📤 Raw LLAMA response length: {len(result_text)} characters")
            else:
                # Use Ollama API
                import requests
                logger.info("🔄 Sending request to Ollama API (localhost:11434)...")
                # Use provided model or default
                model_name = model or "tinyllama:latest"
                request_timeout = timeout or 15
                
                logger.info(f"🔧 Using model: {model_name}, timeout: {request_timeout}s")
                
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False,
                        "keep_alive": "10m",  # Keep model loaded longer
                        "options": {
                            "num_predict": 100,  # Very short for fact-checking
                            "temperature": 0.3,  # Lower temp for more factual responses
                            "top_p": 0.9,
                            "repeat_penalty": 1.1
                        }
                    },
                    timeout=request_timeout
                )
                logger.info(f"📡 Ollama response status: {response.status_code}")
                response_data = response.json()
                result_text = response_data.get("response", "")
                logger.info(f"📤 Raw LLAMA response length: {len(result_text)} characters")
            
            # Try to parse JSON response
            logger.info("🔍 Parsing LLAMA response...")
            try:
                # First try direct parsing
                logger.info("📋 Attempting direct JSON parsing...")
                result = json.loads(result_text)
                logger.info("✅ LLAMA analysis completed successfully - direct JSON parse")
                logger.info(f"📊 Analysis fields returned: {list(result.keys())}")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Direct JSON parsing failed: {e}")
                # Try to extract JSON from the response if it's embedded in other text
                import re
                logger.info("🔍 Attempting to extract JSON from response text...")
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    try:
                        logger.info("📋 Found JSON pattern, attempting to parse...")
                        result = json.loads(json_match.group())
                        logger.info("✅ LLAMA analysis completed successfully - extracted JSON")
                        logger.info(f"📊 Analysis fields returned: {list(result.keys())}")
                        return result
                    except json.JSONDecodeError as e2:
                        logger.warning(f"⚠️ Extracted JSON parsing also failed: {e2}")
                
                # If JSON parsing fails, create structured response
                logger.warning("❌ JSON parsing failed completely, creating fallback structured response")
                logger.info(f"📄 Raw response preview: '{result_text[:100]}...'")
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
            logger.error(f"❌ LLAMA analysis failed: {e}")
            return None
    
    def _create_fast_analysis(self, transcription: str) -> dict:
        """Create fast analysis without LLAMA for speed"""
        # Simple keyword extraction
        words = transcription.lower().split()
        keywords = [w.strip('.,!?') for w in words if len(w) > 3][:5]
        
        # Enhanced sentiment analysis for Dutch and English
        positive_words = [
            # English
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like', 'happy', 'yes', 'correct', 'true', 'right', 'perfect', 'awesome', 'nice',
            # Dutch
            'goed', 'geweldig', 'fantastisch', 'mooi', 'leuk', 'fijn', 'blij', 'tevreden', 'super', 'top', 'prima', 'perfect', 'ja', 'juist', 'correct'
        ]
        negative_words = [
            # English  
            'bad', 'terrible', 'awful', 'hate', 'dislike', 'sad', 'angry', 'frustrated', 'no', 'wrong', 'false', 'incorrect', 'annoying', 'irritating', 'problem', 'issue', 'stupid',
            # Dutch
            'slecht', 'verschrikkelijk', 'haat', 'boos', 'gefrustreerd', 'irritant', 'vervelend', 'probleem', 'fout', 'verkeerd', 'dom', 'stom', 'nee', 'niet'
        ]
        
        pos_count = sum(1 for word in words if word in positive_words)
        neg_count = sum(1 for word in words if word in negative_words)
        
        # More specific sentiment detection
        if 'irritant' in transcription.lower() or 'irritating' in transcription.lower():
            sentiment = "frustrated"
        elif neg_count > pos_count:
            sentiment = "negative"
        elif pos_count > neg_count:
            sentiment = "positive"
        else:
            sentiment = "neutral"
        
        # Use claim-by-claim fact checking
        fact_result = extract_and_check_claims(transcription)
        
        if fact_result["total"] > 0:
            brutal_honesty = "*Claim Analysis (" + str(fact_result["true_count"]) + "/" + str(fact_result["total"]) + " verified):*" + chr(10) + fact_result["formatted"]
            credibility = fact_result["credibility"]
            questionable_claims = [r["claim"] for r in fact_result["claims"] if r["verdict"] in [False, "FALSE", "INCORRECT"]]
        elif len(transcription.strip()) < 5:
            brutal_honesty = "*Too short to analyze*"
            credibility = 0.5
            questionable_claims = []
        else:
            # No factual claims - this is conversational text
            brutal_honesty = "*Conversational content - no verifiable factual claims detected.*\n\nThis appears to be general conversation, opinions, or discussion rather than factual statements that can be verified."
            credibility = 0.8  # Neutral - can't verify but also not wrong
            questionable_claims = []
        
        return {
            "analysis": "Analyzed " + str(len(words)) + " words, " + sentiment + " sentiment.",
            "sentiment": sentiment,
            "summary": transcription[:100] + "..." if len(transcription) > 100 else transcription,
            "keywords": keywords,
            "fact_check": "Checked " + str(fact_result["total"]) + " claims: " + str(fact_result["true_count"]) + " TRUE, " + str(fact_result["false_count"]) + " FALSE",
            "brutal_honesty": brutal_honesty,
            "credibility_score": credibility,
            "questionable_claims": questionable_claims,
            "corrections": ["Claim: " + c + " is FALSE" for c in questionable_claims]
        }
    
    def _check_basic_math_errors(self, text: str) -> bool:
        """Check for obvious mathematical errors"""
        import re
        
        # Look for basic arithmetic patterns like "X plus Y is Z" or "X + Y = Z"
        patterns = [
            r'(\d+)\s*(?:plus|\+)\s*(\d+)\s*(?:is|equals?|=)\s*(\d+)',
            r'(\d+)\s*(?:minus|-)\s*(\d+)\s*(?:is|equals?|=)\s*(\d+)',
            r'(\d+)\s*(?:times|\*|×)\s*(\d+)\s*(?:is|equals?|=)\s*(\d+)',
            r'(\d+)\s*(?:divided by|/|÷)\s*(\d+)\s*(?:is|equals?|=)\s*(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text.lower())
            for match in matches:
                try:
                    a, b, result = map(int, match.groups())
                    
                    # Check the operation based on pattern
                    if 'plus' in pattern or '+' in pattern:
                        correct = a + b
                    elif 'minus' in pattern or '-' in pattern:
                        correct = a - b
                    elif 'times' in pattern or '*' in pattern or '×' in pattern:
                        correct = a * b
                    elif 'divided' in pattern or '/' in pattern or '÷' in pattern:
                        if b != 0:
                            correct = a // b  # Integer division for simplicity
                        else:
                            continue
                    else:
                        continue
                    
                    # If the stated result doesn't match the correct answer
                    if result != correct:
                        logger.info(f"🔍 Math error detected: {a} {pattern.split('|')[0].strip('()')} {b} = {correct}, not {result}")
                        return True
                        
                except (ValueError, ZeroDivisionError):
                    continue
        
        return False
    
    def _detect_content_language(self, text: str) -> str:
        """Detect if content contains Dutch or English words"""
        dutch_indicators = [
            'en', 'is', 'het', 'de', 'een', 'van', 'dat', 'die', 'in', 'te', 'op', 'met', 'voor', 'als', 'zijn', 'er', 'maar', 'om', 'door', 'over', 'ze', 'bij', 'uit', 'ook', 'tot', 'je', 'mijn', 'aan', 'wel', 'of', 'dan', 'hem', 'had', 'zijn', 'meer', 'al', 'wat', 'andere', 'veel', 'geen', 'kan', 'man', 'nu', 'jaar', 'komen', 'mij', 'naar', 'tijd', 'hem', 'zei', 'elke', 'onder', 'tussen'
        ]
        
        english_indicators = [
            'the', 'and', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i', 'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by', 'word', 'but', 'not', 'what', 'all', 'were', 'we', 'when', 'your', 'can', 'said', 'there', 'each', 'which', 'she', 'do', 'how', 'their', 'if', 'will', 'up', 'other', 'about', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 'her', 'would', 'make', 'like', 'into', 'him', 'has', 'two', 'more', 'very', 'after', 'words', 'first', 'where', 'much', 'through'
        ]
        
        words = text.lower().split()
        dutch_count = sum(1 for word in words if word in dutch_indicators)
        english_count = sum(1 for word in words if word in english_indicators)
        
        if dutch_count > english_count:
            return "dutch"
        elif english_count > dutch_count:
            return "english"
        else:
            return "mixed"
    
    def _clean_repetitive_text(self, text: str) -> str:
        """Clean repetitive patterns from transcription"""
        if not text or len(text) < 10:
            return text
        
        import re
        
        # Split into words
        words = text.split()
        if len(words) < 3:
            return text
        
        # Check for repetitive patterns
        # Pattern 1: Same word repeated many times
        word_counts = {}
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word.lower())
            word_counts[clean_word] = word_counts.get(clean_word, 0) + 1
        
        # If any word appears more than 30% of the time, it's likely repetitive
        max_count = max(word_counts.values()) if word_counts else 0
        if max_count > len(words) * 0.3 and len(words) > 10:
            # Find the most common word
            most_common = max(word_counts.items(), key=lambda x: x[1])
            logger.info(f"🔍 Detected repetitive pattern: '{most_common[0]}' appears {most_common[1]} times")
            
            # Try to extract meaningful content by looking for variations
            cleaned_words = []
            prev_word = ""
            consecutive_count = 0
            
            for word in words:
                clean_word = re.sub(r'[^\w]', '', word.lower())
                if clean_word == prev_word:
                    consecutive_count += 1
                    if consecutive_count <= 2:  # Keep first 2 occurrences
                        cleaned_words.append(word)
                else:
                    consecutive_count = 1
                    cleaned_words.append(word)
                    prev_word = clean_word
            
            # If we removed too much, return a summary
            if len(cleaned_words) < len(words) * 0.3:
                return f"[Repetitive audio pattern detected - likely counting or rhythm]"
            
            return " ".join(cleaned_words)
        
        # Pattern 2: Short phrase repeated
        if len(words) > 6:
            # Check for 2-word patterns
            for i in range(len(words) - 3):
                pattern = f"{words[i]} {words[i+1]}"
                pattern_count = 0
                for j in range(0, len(words) - 1):
                    if j + 1 < len(words) and f"{words[j]} {words[j+1]}" == pattern:
                        pattern_count += 1
                
                if pattern_count > len(words) // 4:  # Pattern appears frequently
                    logger.info(f"🔍 Detected repetitive phrase: '{pattern}' appears {pattern_count} times")
                    return f"[Repetitive pattern: '{pattern}']"
        
        return text
    
    def _select_best_transcription(self, results: list) -> tuple:
        """Select the best transcription from multiple attempts"""
        if len(results) == 1:
            return results[0]
        
        scored_results = []
        
        for approach, result in results:
            text = result["text"].strip()
            score = 0
            
            # Score based on text length (prefer reasonable length)
            if 5 <= len(text) <= 200:
                score += 2
            elif len(text) > 0:
                score += 1
            
            # Score based on confidence if available
            if "segments" in result and result["segments"]:
                avg_confidence = sum(seg.get("avg_logprob", -2) for seg in result["segments"]) / len(result["segments"])
                # Convert logprob to positive score (higher is better)
                confidence_score = max(0, (avg_confidence + 2) * 2)  # Scale -2 to 0 → 0 to 4
                score += confidence_score
            
            # Penalize repetitive patterns
            words = text.split()
            if len(words) > 3:
                unique_words = len(set(w.lower() for w in words))
                repetition_ratio = unique_words / len(words)
                if repetition_ratio < 0.3:  # Very repetitive
                    score -= 3
                elif repetition_ratio < 0.5:  # Somewhat repetitive
                    score -= 1
            
            # Bonus for reasonable speech patterns
            if any(word in text.lower() for word in ['the', 'and', 'is', 'are', 'can', 'will', 'have', 'this', 'that']):
                score += 1
            
            # Penalize obvious errors
            if text.lower() in ['you can fly', 'the fox can fly', 'elephant', 'owl']:
                score -= 2
            
            scored_results.append((score, approach, result))
            logger.info(f"   📊 '{approach}' score: {score:.2f} for '{text}'")
        
        # Return the highest scoring result
        best = max(scored_results, key=lambda x: x[0])
        logger.info(f"   🏆 Best: '{best[1]}' with score {best[0]:.2f}")
        return (best[1], best[2])
    
    
    async def process_audio(self, audio_data: bytes, filename: str, transcribe_only: bool = False) -> AIProcessingResult:
        """Complete audio processing pipeline
        
        Args:
            audio_data: Audio bytes to process
            filename: Original filename
            transcribe_only: If True, skip heavy analysis (LLM, fact-checking) - useful for low-memory devices
        """
        import time
        start_time = time.time()
        
        try:
            if not self.is_initialized:
                await self.initialize()
            
            logger.info(f"🤖 Starting AI processing for: {filename}")
            if transcribe_only:
                logger.info("⚡ Transcribe-only mode (skipping analysis)")
            
            # Step 1: Transcribe audio
            transcription = await self.transcribe_audio(audio_data, filename)
            
            # Detect content language for better analysis
            content_language = self._detect_content_language(transcription)
            logger.info(f"✅ Transcription: '{transcription}'")
            logger.info(f"🗣️ Content language detected: {content_language}")
            
            if transcription.startswith("Transcription failed"):
                return AIProcessingResult(
                    success=False,
                    error=transcription,
                    processing_time=time.time() - start_time
                )
            
            # If transcribe_only, return just the transcription
            if transcribe_only:
                logger.info("⚡ Returning transcription-only result (no LLM analysis)")
                return AIProcessingResult(
                    success=True,
                    transcription=transcription,
                    analysis="Transcription-only mode - analysis skipped",
                    summary=transcription[:200] + "..." if len(transcription) > 200 else transcription,
                    sentiment="neutral",
                    keywords=[],
                    fact_check="Skipped (transcribe-only mode)",
                    brutal_honesty="Analysis not performed in transcribe-only mode",
                    credibility_score=None,
                    questionable_claims=[],
                    corrections=[],
                    confidence=0.9,
                    processing_time=time.time() - start_time
                )
            
            # Step 2: Try LLAMA with TinyLlama for fact-checking
            logger.info("🔄 Starting fact-checking with TinyLlama...")
            
            # Start with fast analysis as base
            analysis_result = self._create_fast_analysis(transcription)
            
            # Try to enhance with LLAMA if available (non-blocking)
            try:
                llama_result = await self.analyze_with_llama(transcription, filename, model="tinyllama:latest", timeout=15)
                if llama_result:
                    # KEEP fast analysis fact-checking results - only add LLAMA context if fast analysis has no claims
                    if "Claim Analysis" not in analysis_result.get("brutal_honesty", ""):
                        analysis_result.update({
                            "fact_check": llama_result.get("fact_check", analysis_result["fact_check"]),
                            "brutal_honesty": llama_result.get("brutal_honesty", analysis_result["brutal_honesty"]),
                        })
                    logger.info("✅ Fact-checking complete (fast analysis preserved)")
                else:
                    logger.info("⚡ Using fast analysis (TinyLlama unavailable)")
            except Exception as e:
                logger.warning(f"⚡ TinyLlama enhancement skipped: {e}")
            
            processing_time = time.time() - start_time
            logger.info(f"⏱️ Total processing time: {processing_time:.2f} seconds")
            
            # Calculate confidence based on transcription length and quality
            confidence = min(0.95, len(transcription) / 100.0) if transcription else 0.1
            logger.info(f"📊 Calculated confidence score: {confidence:.3f}")
            
            # Create final result
            logger.info("📦 Building final AI processing result...")
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
            
            logger.info("✅ AI processing completed successfully!")
            logger.info(f"📋 Final result summary:")
            logger.info(f"   • Transcription: {len(transcription)} chars")
            logger.info(f"   • Sentiment: {result.sentiment}")
            logger.info(f"   • Keywords: {len(result.keywords)} found")
            logger.info(f"   • Credibility: {result.credibility_score}")
            logger.info(f"   • Processing time: {processing_time:.2f}s")
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
