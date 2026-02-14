"""
Transcription Service - Business logic for AI transcription
Separates transcription operations from HTTP route handlers
"""

import logging
import uuid
import os
import tempfile
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TranscriptionJob:
    """Transcription job data."""
    id: str
    status: JobStatus
    filename: str
    file_size: int
    validate_documents: bool = False
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: int = 0
    progress_message: str = "Queued for processing"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class TranscriptionResult:
    """Transcription result data."""
    success: bool
    transcription: Optional[str] = None
    analysis: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    keywords: Optional[List[str]] = None
    fact_check: Optional[str] = None
    brutal_honesty: Optional[str] = None
    credibility_score: Optional[float] = None
    questionable_claims: Optional[List[str]] = None
    corrections: Optional[List[str]] = None
    confidence: Optional[float] = None
    processing_time: Optional[float] = None
    error: Optional[str] = None
    
    # Voice analysis
    voice_analysis: Optional[Dict[str, Any]] = None
    sentence_moods: Optional[List[Dict[str, Any]]] = None
    
    # Document validation
    document_validation: Optional[Dict[str, Any]] = None
    validation_score: Optional[float] = None
    fact_check_sources: Optional[List[str]] = None
    contradictions: Optional[List[str]] = None
    supporting_evidence: Optional[List[str]] = None


class TranscriptionService:
    """Service layer for transcription operations."""
    
    def __init__(self):
        self._jobs: Dict[str, TranscriptionJob] = {}
        self._processor = None
        self._enhanced_processor = None
        self._voice_analyzer = None
    
    async def get_processor(self):
        """Get or initialize the LLAMA processor."""
        if self._processor is None:
            from ai.llama_processor import get_processor
            self._processor = await get_processor()
        return self._processor
    
    async def get_enhanced_processor(self):
        """Get or initialize the enhanced processor with document validation."""
        if self._enhanced_processor is None:
            from ai.enhanced_processor import get_enhanced_processor
            self._enhanced_processor = await get_enhanced_processor()
        return self._enhanced_processor
    
    async def get_voice_analyzer(self):
        """Get or initialize the voice analyzer."""
        if self._voice_analyzer is None:
            from audio.voice_analyzer import get_voice_analyzer
            self._voice_analyzer = get_voice_analyzer()
        return self._voice_analyzer
    
    def create_job(self, filename: str, file_size: int, validate_documents: bool = False) -> str:
        """Create a new transcription job."""
        job_id = str(uuid.uuid4())[:8]
        
        job = TranscriptionJob(
            id=job_id,
            status=JobStatus.PENDING,
            filename=filename,
            file_size=file_size,
            validate_documents=validate_documents
        )
        
        self._jobs[job_id] = job
        logger.info(f"Created transcription job: {job_id} for file: {filename}")
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[TranscriptionJob]:
        """Get a job by ID."""
        return self._jobs.get(job_id)
    
    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        progress: Optional[int] = None,
        progress_message: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """Update job status."""
        job = self._jobs.get(job_id)
        if not job:
            return
        
        if status:
            job.status = status
            if status == JobStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.now().isoformat()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                job.completed_at = datetime.now().isoformat()
        
        if progress is not None:
            job.progress = progress
        if progress_message:
            job.progress_message = progress_message
        if result:
            job.result = result
        if error:
            job.error = error
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False
    
    def list_jobs(self, limit: int = 50) -> List[TranscriptionJob]:
        """List recent jobs."""
        jobs = sorted(
            self._jobs.values(),
            key=lambda x: x.created_at,
            reverse=True
        )
        return jobs[:limit]
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove jobs older than max_age_hours."""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []
        
        for job_id, job in self._jobs.items():
            try:
                created = datetime.fromisoformat(job.created_at)
                if created < cutoff:
                    to_remove.append(job_id)
            except Exception:
                pass
        
        for job_id in to_remove:
            del self._jobs[job_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")
        
        return len(to_remove)
    
    async def transcribe(
        self,
        audio_data: bytes,
        filename: str,
        validate_documents: bool = False
    ) -> TranscriptionResult:
        """Transcribe audio data."""
        try:
            if validate_documents:
                processor = await self.get_enhanced_processor()
                result = await processor.process_audio_with_validation(audio_data, filename)
            else:
                processor = await self.get_processor()
                result = await processor.process_audio(audio_data, filename)
            
            if result.success:
                return TranscriptionResult(
                    success=True,
                    transcription=result.transcription,
                    analysis=result.analysis,
                    summary=result.summary,
                    sentiment=result.sentiment,
                    keywords=result.keywords,
                    fact_check=result.fact_check,
                    brutal_honesty=result.brutal_honesty,
                    credibility_score=result.credibility_score,
                    questionable_claims=result.questionable_claims,
                    corrections=result.corrections,
                    confidence=result.confidence,
                    processing_time=result.processing_time,
                    document_validation=getattr(result, 'document_validation', None),
                    validation_score=getattr(result, 'validation_score', None),
                    fact_check_sources=getattr(result, 'fact_check_sources', None),
                    contradictions=getattr(result, 'contradictions', None),
                    supporting_evidence=getattr(result, 'supporting_evidence', None)
                )
            else:
                return TranscriptionResult(success=False, error=result.error)
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return TranscriptionResult(success=False, error=str(e))
    
    async def analyze_voice(
        self,
        audio_data: bytes,
        transcript: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Analyze voice characteristics from audio."""
        temp_path = None
        try:
            # Save to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
                tmp.write(audio_data)
                temp_path = tmp.name
            
            analyzer = await self.get_voice_analyzer()
            word_count = len(transcript.split()) if transcript else 0
            
            features = await analyzer.analyze_audio(
                temp_path,
                transcript=transcript,
                word_count=word_count
            )
            
            return features.to_dict()
            
        except Exception as e:
            logger.warning(f"Voice analysis failed: {e}")
            return None
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass


# Singleton instance
_transcription_service: Optional[TranscriptionService] = None


def get_transcription_service() -> TranscriptionService:
    """Get the transcription service singleton."""
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
