"""
LLM Client - Unified interface for LLM inference
Supports Ollama (local) and Gemini (API)
"""

import os
import logging
import json
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseLLMClient(ABC):
    """Base class for LLM clients"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        pass
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        pass
    
    @abstractmethod
    def is_ready(self) -> bool:
        pass


class OllamaClient(BaseLLMClient):
    """Ollama-based LLM client for local inference"""
    
    def __init__(self, model: str = None):
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.getenv("LLM_MODEL", "llama3.2:3b")
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Check if Ollama is available and model is loaded"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        models = [m["name"] for m in data.get("models", [])]
                        
                        # Check for exact match or prefix match
                        model_available = any(
                            self.model in m or m.startswith(self.model.split(":")[0])
                            for m in models
                        )
                        
                        if model_available:
                            logger.info(f"✅ Ollama ready with model: {self.model}")
                            self.is_initialized = True
                            return True
                        else:
                            logger.warning(f"Model {self.model} not found. Available: {models}")
                            # Try to use any available model
                            if models:
                                self.model = models[0]
                                logger.info(f"Using available model: {self.model}")
                                self.is_initialized = True
                                return True
                            return False
                    else:
                        logger.error(f"Ollama not responding: {resp.status}")
                        return False
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False
    
    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text using Ollama"""
        if not self.is_initialized:
            await self.initialize()
        
        if not self.is_initialized:
            raise RuntimeError("Ollama not available")
        
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 2000
                }
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("response", "")
                    else:
                        error = await resp.text()
                        logger.error(f"Ollama error: {error}")
                        return ""
        except Exception as e:
            logger.error(f"Ollama generate failed: {e}")
            return ""
    
    def is_ready(self) -> bool:
        return self.is_initialized


class GeminiClient(BaseLLMClient):
    """Google Gemini API client"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = "gemini-1.5-flash"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Check if Gemini API key is configured"""
        if not self.api_key:
            logger.warning("Gemini API key not configured (set GEMINI_KEY)")
            return False
        
        # Test the API
        try:
            test_response = await self.generate("Say 'OK' if you can hear me.", None)
            if test_response:
                logger.info("✅ Gemini API initialized")
                self.is_initialized = True
                return True
        except Exception as e:
            logger.warning(f"Gemini API test failed: {e}")
        
        return False
    
    async def generate(self, prompt: str, system_prompt: str = None) -> str:
        """Generate text using Gemini API"""
        if not self.api_key:
            raise RuntimeError("Gemini API key not configured")
        
        try:
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            
            # Build content
            parts = []
            if system_prompt:
                parts.append({"text": f"System: {system_prompt}\n\n"})
            parts.append({"text": prompt})
            
            payload = {
                "contents": [{"parts": parts}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 2000,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                return parts[0].get("text", "")
                    else:
                        error = await resp.text()
                        logger.error(f"Gemini API error: {error}")
        except Exception as e:
            logger.error(f"Gemini generate failed: {e}")
        
        return ""
    
    def is_ready(self) -> bool:
        return self.is_initialized


async def get_llm_client(prefer_local: bool = True) -> Optional[BaseLLMClient]:
    """
    Get the best available LLM client.
    
    Args:
        prefer_local: If True (default), only use local Ollama. 
                      If False, try Gemini first then Ollama.
    """
    # Always try local Ollama first (privacy-first approach)
    if prefer_local:
        client = OllamaClient()
        if await client.initialize():
            logger.info("✅ Using LOCAL LLAMA (Ollama) for AI processing")
            return client
        logger.warning("Local Ollama not available")
        return None
    
    # Only if prefer_local is False, try cloud APIs
    gemini_key = os.getenv("GEMINI_KEY") or os.getenv("GOOGLE_API_KEY")
    if gemini_key:
        client = GeminiClient()
        if await client.initialize():
            return client
    
    # Fall back to Ollama
    client = OllamaClient()
    if await client.initialize():
        return client
    
    logger.warning("No LLM client available")
    return None

