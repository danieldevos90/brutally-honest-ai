"""
Service Layer for Brutally Honest AI
Separates business logic from route handlers following best practices
"""

from .audio_service import AudioService
from .device_service import DeviceService
from .transcription_service import TranscriptionService
from .upload_queue_manager import (
    UploadQueueManager,
    get_queue_manager,
    initialize_queue_manager,
    QueueItem,
    QueueItemStatus,
    QueuePriority,
    ProcessingType,
    GPUResourceManager
)

__all__ = [
    "AudioService",
    "DeviceService", 
    "TranscriptionService",
    "UploadQueueManager",
    "get_queue_manager",
    "initialize_queue_manager",
    "QueueItem",
    "QueueItemStatus",
    "QueuePriority",
    "ProcessingType",
    "GPUResourceManager",
]
