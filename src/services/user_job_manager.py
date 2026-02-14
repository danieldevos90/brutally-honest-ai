"""
User Job Manager - Persistent job storage with user association
Enables real-time sync of upload/transcription status across devices
"""

import json
import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict, field
import uuid

logger = logging.getLogger(__name__)

class JobStatus(str, Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    TRANSCRIPTION = "transcription"
    DOCUMENT_UPLOAD = "document_upload"
    VALIDATION = "validation"

@dataclass
class UserJob:
    """A job associated with a user"""
    id: str
    user_id: str
    job_type: JobType
    status: JobStatus
    filename: str
    file_size: int
    
    # Progress tracking
    progress: int = 0
    progress_message: str = "Queued"
    phase: str = "loading"
    phase_progress: int = 0
    
    # Timestamps
    created_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Results
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Device info
    device_name: Optional[str] = None
    device_id: Optional[str] = None
    
    # Stored file path (for resuming)
    stored_file_path: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "job_type": self.job_type.value if isinstance(self.job_type, JobType) else self.job_type,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "filename": self.filename,
            "file_size": self.file_size,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "phase": self.phase,
            "phase_progress": self.phase_progress,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "device_name": self.device_name,
            "device_id": self.device_id,
            "stored_file_path": self.stored_file_path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserJob":
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            user_id=data.get("user_id", "anonymous"),
            job_type=JobType(data.get("job_type", "transcription")),
            status=JobStatus(data.get("status", "pending")),
            filename=data.get("filename", "unknown"),
            file_size=data.get("file_size", 0),
            progress=data.get("progress", 0),
            progress_message=data.get("progress_message", "Queued"),
            phase=data.get("phase", "loading"),
            phase_progress=data.get("phase_progress", 0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            result=data.get("result"),
            error=data.get("error"),
            device_name=data.get("device_name"),
            device_id=data.get("device_id"),
            stored_file_path=data.get("stored_file_path")
        )


class UserJobManager:
    """
    Manages jobs for users with persistent storage.
    Enables cross-device sync of job status.
    """
    
    def __init__(self, storage_dir: str = None):
        self.storage_dir = Path(storage_dir or os.environ.get(
            "JOB_STORAGE_DIR", 
            Path(__file__).parent.parent.parent / "data" / "jobs"
        ))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # File storage for uploaded files
        self.files_dir = self.storage_dir / "files"
        self.files_dir.mkdir(parents=True, exist_ok=True)
        
        # Jobs storage file
        self.jobs_file = self.storage_dir / "user_jobs.json"
        
        # In-memory cache
        self.jobs: Dict[str, UserJob] = {}
        
        # Load existing jobs
        self._load_jobs()
        
        logger.info(f"📋 UserJobManager initialized - storage: {self.storage_dir}")
    
    def _load_jobs(self):
        """Load jobs from persistent storage"""
        try:
            if self.jobs_file.exists():
                with open(self.jobs_file, 'r') as f:
                    data = json.load(f)
                    for job_id, job_data in data.items():
                        self.jobs[job_id] = UserJob.from_dict(job_data)
                logger.info(f"📂 Loaded {len(self.jobs)} jobs from storage")
        except Exception as e:
            logger.error(f"Error loading jobs: {e}")
    
    def _save_jobs(self):
        """Persist jobs to storage"""
        try:
            data = {job_id: job.to_dict() for job_id, job in self.jobs.items()}
            with open(self.jobs_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving jobs: {e}")
    
    def create_job(
        self,
        user_id: str,
        filename: str,
        file_size: int,
        job_type: JobType = JobType.TRANSCRIPTION,
        device_name: str = None,
        device_id: str = None
    ) -> UserJob:
        """Create a new job for a user"""
        job_id = str(uuid.uuid4())[:8]
        
        job = UserJob(
            id=job_id,
            user_id=user_id,
            job_type=job_type,
            status=JobStatus.PENDING,
            filename=filename,
            file_size=file_size,
            device_name=device_name,
            device_id=device_id
        )
        
        self.jobs[job_id] = job
        self._save_jobs()
        
        logger.info(f"📝 Created job {job_id} for user {user_id}: {filename}")
        return job
    
    def store_file(self, job_id: str, file_data: bytes) -> str:
        """Store uploaded file for later processing"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")
        
        job = self.jobs[job_id]
        
        # Create user directory
        user_dir = self.files_dir / job.user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Store file with job_id prefix
        file_path = user_dir / f"{job_id}_{job.filename}"
        with open(file_path, 'wb') as f:
            f.write(file_data)
        
        job.stored_file_path = str(file_path)
        job.status = JobStatus.PENDING
        job.progress_message = "File stored, ready for processing"
        self._save_jobs()
        
        logger.info(f"💾 Stored file for job {job_id}: {file_path}")
        return str(file_path)
    
    def get_stored_file(self, job_id: str) -> Optional[bytes]:
        """Retrieve stored file data"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        if not job.stored_file_path or not os.path.exists(job.stored_file_path):
            return None
        
        with open(job.stored_file_path, 'rb') as f:
            return f.read()
    
    def update_job(
        self,
        job_id: str,
        status: JobStatus = None,
        progress: int = None,
        progress_message: str = None,
        phase: str = None,
        phase_progress: int = None,
        result: Dict[str, Any] = None,
        error: str = None
    ):
        """Update job status"""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found for update")
            return
        
        job = self.jobs[job_id]
        
        if status:
            job.status = status
            if status == JobStatus.PROCESSING and not job.started_at:
                job.started_at = datetime.now().isoformat()
            if status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                job.completed_at = datetime.now().isoformat()
        
        if progress is not None:
            job.progress = progress
        if progress_message:
            job.progress_message = progress_message
        if phase:
            job.phase = phase
        if phase_progress is not None:
            job.phase_progress = phase_progress
        if result is not None:
            job.result = result
        if error:
            job.error = error
        
        self._save_jobs()
    
    def get_job(self, job_id: str) -> Optional[UserJob]:
        """Get a job by ID"""
        return self.jobs.get(job_id)
    
    def get_user_jobs(
        self,
        user_id: str,
        status_filter: List[JobStatus] = None,
        job_type_filter: JobType = None,
        limit: int = 50,
        include_completed: bool = True
    ) -> List[UserJob]:
        """Get all jobs for a user"""
        user_jobs = []
        
        for job in self.jobs.values():
            if job.user_id != user_id:
                continue
            
            if status_filter and job.status not in status_filter:
                continue
            
            if job_type_filter and job.job_type != job_type_filter:
                continue
            
            if not include_completed and job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                continue
            
            user_jobs.append(job)
        
        # Sort by created_at descending (newest first)
        user_jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return user_jobs[:limit]
    
    def get_active_jobs(self, user_id: str = None) -> List[UserJob]:
        """Get all active (non-completed) jobs, optionally filtered by user"""
        active_statuses = [JobStatus.PENDING, JobStatus.UPLOADING, JobStatus.PROCESSING]
        
        active_jobs = []
        for job in self.jobs.values():
            if job.status in active_statuses:
                if user_id is None or job.user_id == user_id:
                    active_jobs.append(job)
        
        return active_jobs
    
    def get_all_jobs_summary(self) -> Dict[str, Any]:
        """Get summary of all jobs (for admin view)"""
        summary = {
            "total": len(self.jobs),
            "by_status": {},
            "by_user": {},
            "active_count": 0
        }
        
        for job in self.jobs.values():
            # Count by status
            status = job.status.value if isinstance(job.status, JobStatus) else job.status
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Count by user
            summary["by_user"][job.user_id] = summary["by_user"].get(job.user_id, 0) + 1
            
            # Count active
            if job.status in [JobStatus.PENDING, JobStatus.UPLOADING, JobStatus.PROCESSING]:
                summary["active_count"] += 1
        
        return summary
    
    def delete_job(self, job_id: str, delete_file: bool = True) -> bool:
        """Delete a job and optionally its stored file"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        # Delete stored file if requested
        if delete_file and job.stored_file_path and os.path.exists(job.stored_file_path):
            try:
                os.remove(job.stored_file_path)
                logger.info(f"🗑️ Deleted file for job {job_id}")
            except Exception as e:
                logger.error(f"Error deleting file for job {job_id}: {e}")
        
        del self.jobs[job_id]
        self._save_jobs()
        
        logger.info(f"🗑️ Deleted job {job_id}")
        return True
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up completed jobs older than max_age_hours"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_delete = []
        
        for job_id, job in self.jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                if job.completed_at:
                    completed_time = datetime.fromisoformat(job.completed_at)
                    if completed_time < cutoff:
                        to_delete.append(job_id)
        
        for job_id in to_delete:
            self.delete_job(job_id)
        
        if to_delete:
            logger.info(f"🧹 Cleaned up {len(to_delete)} old jobs")


# Singleton instance
_job_manager: Optional[UserJobManager] = None

def get_job_manager() -> UserJobManager:
    """Get the singleton job manager instance"""
    global _job_manager
    if _job_manager is None:
        _job_manager = UserJobManager()
    return _job_manager
