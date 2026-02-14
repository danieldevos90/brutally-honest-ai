"""
Upload Queue Manager for Multi-Device Concurrent Processing
Handles multiple simultaneous uploads from different ESP32S3 devices
with GPU resource management to prevent overload on NVIDIA systems.
"""

import asyncio
import logging
import os
import time
import uuid
import psutil
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)

# Default minimum memory requirement - can be lowered for systems with limited RAM
DEFAULT_MIN_GPU_MEMORY_GB = float(os.environ.get("MIN_GPU_MEMORY_GB", "0.5"))

class QueuePriority(int, Enum):
    """Priority levels for queue items"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

class QueueItemStatus(str, Enum):
    """Status of queue items"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingType(str, Enum):
    """Type of processing to perform"""
    TRANSCRIPTION = "transcription"
    DOCUMENT = "document"
    DOCUMENT_VECTORIZE = "document_vectorize"
    AUDIO_ANALYSIS = "audio_analysis"

@dataclass
class QueueItem:
    """A single item in the upload queue"""
    id: str
    device_id: str  # Source device (USB, BLE, web upload, etc.)
    filename: str
    data: bytes
    processing_type: ProcessingType
    status: QueueItemStatus = QueueItemStatus.QUEUED
    priority: QueuePriority = QueuePriority.NORMAL
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress: int = 0
    progress_message: str = "Queued for processing"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "filename": self.filename,
            "processing_type": self.processing_type.value,
            "status": self.status.value,
            "priority": self.priority.name,
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
            "started_at": datetime.fromtimestamp(self.started_at).isoformat() if self.started_at else None,
            "completed_at": datetime.fromtimestamp(self.completed_at).isoformat() if self.completed_at else None,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "has_result": self.result is not None,
            "error": self.error,
            "file_size": len(self.data),
            "wait_time_seconds": round((self.started_at or time.time()) - self.created_at, 1),
            "processing_time_seconds": round(self.completed_at - self.started_at, 1) if self.completed_at and self.started_at else None,
            "metadata": self.metadata
        }

@dataclass
class DeviceQueueStats:
    """Statistics for a device's queue"""
    device_id: str
    total_queued: int = 0
    total_processing: int = 0
    total_completed: int = 0
    total_failed: int = 0
    avg_processing_time: float = 0.0
    last_activity: Optional[float] = None

class GPUResourceManager:
    """Manages GPU resources to prevent overload"""
    
    def __init__(self, max_concurrent_gpu_tasks: int = 2, min_available_memory_gb: float = 1.0):
        self.max_concurrent_gpu_tasks = max_concurrent_gpu_tasks
        self.min_available_memory_gb = min_available_memory_gb
        self.current_gpu_tasks = 0
        self.lock = asyncio.Lock()
        self._gpu_available = True
        
    async def can_start_gpu_task(self) -> bool:
        """Check if we can start a new GPU task"""
        async with self.lock:
            if self.current_gpu_tasks >= self.max_concurrent_gpu_tasks:
                return False
            
            # Check available memory
            try:
                available_gb = psutil.virtual_memory().available / (1024**3)
                if available_gb < self.min_available_memory_gb:
                    logger.warning(f"⚠️ Low memory: {available_gb:.2f}GB available, need {self.min_available_memory_gb}GB")
                    return False
            except Exception as e:
                logger.warning(f"Failed to check memory: {e}")
            
            # Try to check NVIDIA GPU memory
            try:
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=memory.available', '--format=csv,nounits,noheader'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    gpu_memory_mb = int(result.stdout.strip().split('\n')[0])
                    gpu_memory_gb = gpu_memory_mb / 1024
                    if gpu_memory_gb < self.min_available_memory_gb:
                        logger.warning(f"⚠️ Low GPU memory: {gpu_memory_gb:.2f}GB available")
                        return False
            except Exception:
                pass  # nvidia-smi not available or failed
            
            return True
    
    async def acquire_gpu(self) -> bool:
        """Acquire GPU resource for processing"""
        async with self.lock:
            if self.current_gpu_tasks < self.max_concurrent_gpu_tasks:
                self.current_gpu_tasks += 1
                logger.info(f"🎮 GPU acquired: {self.current_gpu_tasks}/{self.max_concurrent_gpu_tasks} tasks")
                return True
            return False
    
    async def release_gpu(self):
        """Release GPU resource after processing"""
        async with self.lock:
            if self.current_gpu_tasks > 0:
                self.current_gpu_tasks -= 1
            logger.info(f"🎮 GPU released: {self.current_gpu_tasks}/{self.max_concurrent_gpu_tasks} tasks")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current GPU resource status"""
        status = {
            "current_gpu_tasks": self.current_gpu_tasks,
            "max_concurrent_gpu_tasks": self.max_concurrent_gpu_tasks,
            "gpu_slots_available": self.max_concurrent_gpu_tasks - self.current_gpu_tasks,
            "min_memory_required_gb": self.min_available_memory_gb
        }
        
        # Add system memory info
        try:
            mem = psutil.virtual_memory()
            status["system_memory_available_gb"] = round(mem.available / (1024**3), 2)
            status["system_memory_total_gb"] = round(mem.total / (1024**3), 2)
            status["system_memory_percent_used"] = mem.percent
        except Exception:
            pass
        
        # Add GPU memory info if available
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu', '--format=csv,nounits,noheader'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split(',')
                if len(parts) >= 3:
                    status["gpu_memory_used_mb"] = int(parts[0].strip())
                    status["gpu_memory_total_mb"] = int(parts[1].strip())
                    status["gpu_utilization_percent"] = int(parts[2].strip())
                    status["gpu_available"] = True
        except Exception:
            status["gpu_available"] = False
        
        return status


class UploadQueueManager:
    """
    Manages upload queues for multiple devices with GPU resource management.
    
    Features:
    - Device-specific queues with priority handling
    - GPU resource management to prevent overload
    - Concurrent processing with configurable limits
    - Progress tracking per item
    - Statistics and monitoring
    """
    
    def __init__(
        self,
        max_concurrent_processing: int = 3,
        max_queue_size_per_device: int = 50,
        max_total_queue_size: int = 200,
        gpu_concurrent_limit: int = 2,
        min_gpu_memory_gb: float = DEFAULT_MIN_GPU_MEMORY_GB
    ):
        self.max_concurrent_processing = max_concurrent_processing
        self.max_queue_size_per_device = max_queue_size_per_device
        self.max_total_queue_size = max_total_queue_size
        
        # GPU resource manager
        self.gpu_manager = GPUResourceManager(gpu_concurrent_limit, min_gpu_memory_gb)
        
        # Queues: device_id -> list of QueueItems
        self.queues: Dict[str, List[QueueItem]] = defaultdict(list)
        
        # All items by ID for quick lookup
        self.items: Dict[str, QueueItem] = {}
        
        # Device statistics
        self.device_stats: Dict[str, DeviceQueueStats] = {}
        
        # Processing state
        self.is_running = False
        self.processing_lock = asyncio.Lock()
        self.queue_semaphore = asyncio.Semaphore(max_concurrent_processing)
        
        # Callbacks
        self.process_transcription_callback: Optional[Callable] = None
        self.process_document_callback: Optional[Callable] = None
        
        # Worker task
        self._worker_task: Optional[asyncio.Task] = None
        
        logger.info(f"📋 UploadQueueManager initialized: max_concurrent={max_concurrent_processing}, "
                   f"gpu_limit={gpu_concurrent_limit}, max_queue_per_device={max_queue_size_per_device}")
    
    def set_callbacks(
        self,
        transcription_callback: Optional[Callable] = None,
        document_callback: Optional[Callable] = None
    ):
        """Set processing callbacks"""
        self.process_transcription_callback = transcription_callback
        self.process_document_callback = document_callback
    
    async def start(self):
        """Start the queue worker"""
        if not self.is_running:
            self.is_running = True
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info("🚀 Queue worker started")
    
    async def stop(self):
        """Stop the queue worker"""
        self.is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Queue worker stopped")
    
    def add_item(
        self,
        device_id: str,
        filename: str,
        data: bytes,
        processing_type: ProcessingType,
        priority: QueuePriority = QueuePriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> QueueItem:
        """Add an item to the queue"""
        
        # Check queue limits
        device_queue = self.queues[device_id]
        if len(device_queue) >= self.max_queue_size_per_device:
            raise ValueError(f"Queue full for device {device_id} (max {self.max_queue_size_per_device})")
        
        total_items = sum(len(q) for q in self.queues.values())
        if total_items >= self.max_total_queue_size:
            raise ValueError(f"Total queue full (max {self.max_total_queue_size})")
        
        # Create queue item
        item = QueueItem(
            id=str(uuid.uuid4())[:12],
            device_id=device_id,
            filename=filename,
            data=data,
            processing_type=processing_type,
            priority=priority,
            metadata=metadata or {}
        )
        
        # Add to queues
        device_queue.append(item)
        self.items[item.id] = item
        
        # Sort queue by priority (highest first)
        device_queue.sort(key=lambda x: (x.priority.value, -x.created_at), reverse=True)
        
        # Update device stats
        self._update_device_stats(device_id)
        
        logger.info(f"📥 Queued item {item.id} from device {device_id}: {filename} "
                   f"({len(data)} bytes, {processing_type.value}, priority={priority.name})")
        
        return item
    
    def get_item(self, item_id: str) -> Optional[QueueItem]:
        """Get a queue item by ID"""
        return self.items.get(item_id)
    
    def get_item_status(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a queue item"""
        item = self.items.get(item_id)
        if item:
            result = item.to_dict()
            result["queue_position"] = self._get_queue_position(item)
            return result
        return None
    
    def cancel_item(self, item_id: str) -> bool:
        """Cancel a queued item"""
        item = self.items.get(item_id)
        if item and item.status == QueueItemStatus.QUEUED:
            item.status = QueueItemStatus.CANCELLED
            item.completed_at = time.time()
            # Remove from device queue
            if item.device_id in self.queues:
                self.queues[item.device_id] = [i for i in self.queues[item.device_id] if i.id != item_id]
            logger.info(f"❌ Cancelled item {item_id}")
            return True
        return False
    
    def get_device_queue(self, device_id: str) -> List[Dict[str, Any]]:
        """Get all items in a device's queue"""
        return [item.to_dict() for item in self.queues.get(device_id, [])]
    
    def get_all_queues(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all queues for all devices"""
        return {
            device_id: [item.to_dict() for item in items]
            for device_id, items in self.queues.items()
        }
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get overall queue statistics"""
        all_items = list(self.items.values())
        
        by_status = defaultdict(int)
        by_type = defaultdict(int)
        by_device = defaultdict(int)
        
        for item in all_items:
            by_status[item.status.value] += 1
            by_type[item.processing_type.value] += 1
            by_device[item.device_id] += 1
        
        # Calculate averages
        completed = [i for i in all_items if i.completed_at and i.started_at]
        avg_processing_time = (
            sum(i.completed_at - i.started_at for i in completed) / len(completed)
            if completed else 0
        )
        
        return {
            "total_items": len(all_items),
            "by_status": dict(by_status),
            "by_type": dict(by_type),
            "by_device": dict(by_device),
            "active_devices": len(self.queues),
            "avg_processing_time_seconds": round(avg_processing_time, 2),
            "gpu_status": self.gpu_manager.get_status(),
            "worker_running": self.is_running,
            "max_concurrent_processing": self.max_concurrent_processing,
            "current_processing": self.max_concurrent_processing - self.queue_semaphore._value
        }
    
    def get_device_stats(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific device"""
        if device_id in self.device_stats:
            stats = self.device_stats[device_id]
            return {
                "device_id": stats.device_id,
                "total_queued": stats.total_queued,
                "total_processing": stats.total_processing,
                "total_completed": stats.total_completed,
                "total_failed": stats.total_failed,
                "avg_processing_time_seconds": round(stats.avg_processing_time, 2),
                "last_activity": datetime.fromtimestamp(stats.last_activity).isoformat() if stats.last_activity else None,
                "current_queue_length": len(self.queues.get(device_id, []))
            }
        return None
    
    def cleanup_completed(self, max_age_hours: int = 24):
        """Remove completed items older than max_age_hours"""
        cutoff = time.time() - (max_age_hours * 3600)
        to_remove = []
        
        for item_id, item in self.items.items():
            if item.status in [QueueItemStatus.COMPLETED, QueueItemStatus.FAILED, QueueItemStatus.CANCELLED]:
                if item.completed_at and item.completed_at < cutoff:
                    to_remove.append(item_id)
        
        for item_id in to_remove:
            del self.items[item_id]
        
        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old queue items")
    
    def _get_queue_position(self, item: QueueItem) -> int:
        """Get position of item in its device queue"""
        device_queue = self.queues.get(item.device_id, [])
        for i, q_item in enumerate(device_queue):
            if q_item.id == item.id:
                return i + 1
        return 0
    
    def _update_device_stats(self, device_id: str):
        """Update statistics for a device"""
        if device_id not in self.device_stats:
            self.device_stats[device_id] = DeviceQueueStats(device_id=device_id)
        
        stats = self.device_stats[device_id]
        items = [i for i in self.items.values() if i.device_id == device_id]
        
        stats.total_queued = sum(1 for i in items if i.status == QueueItemStatus.QUEUED)
        stats.total_processing = sum(1 for i in items if i.status == QueueItemStatus.PROCESSING)
        stats.total_completed = sum(1 for i in items if i.status == QueueItemStatus.COMPLETED)
        stats.total_failed = sum(1 for i in items if i.status == QueueItemStatus.FAILED)
        stats.last_activity = time.time()
        
        # Calculate average processing time
        completed = [i for i in items if i.completed_at and i.started_at]
        if completed:
            stats.avg_processing_time = sum(i.completed_at - i.started_at for i in completed) / len(completed)
    
    async def _worker_loop(self):
        """Main worker loop that processes queue items"""
        logger.info("🔄 Queue worker loop started")
        
        while self.is_running:
            try:
                # Find next item to process
                item = await self._get_next_item()
                
                if item:
                    # Process item in background
                    asyncio.create_task(self._process_item(item))
                else:
                    # No items to process, wait a bit
                    await asyncio.sleep(0.5)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue worker error: {e}")
                await asyncio.sleep(1)
    
    async def _get_next_item(self) -> Optional[QueueItem]:
        """Get the next item to process based on priority"""
        async with self.processing_lock:
            # Check if we can process more items
            if not await self.gpu_manager.can_start_gpu_task():
                return None
            
            # Find highest priority queued item across all devices
            best_item = None
            best_priority = -1
            
            for device_id, queue in self.queues.items():
                for item in queue:
                    if item.status == QueueItemStatus.QUEUED:
                        if item.priority.value > best_priority:
                            best_item = item
                            best_priority = item.priority.value
            
            if best_item:
                # Try to acquire semaphore (non-blocking)
                if self.queue_semaphore.locked():
                    return None
                
                await self.queue_semaphore.acquire()
                best_item.status = QueueItemStatus.PROCESSING
                best_item.started_at = time.time()
                best_item.progress = 5
                best_item.progress_message = "Starting processing..."
                
                # Remove from device queue
                if best_item.device_id in self.queues:
                    self.queues[best_item.device_id] = [
                        i for i in self.queues[best_item.device_id] if i.id != best_item.id
                    ]
                
                return best_item
            
            return None
    
    async def _process_item(self, item: QueueItem):
        """Process a single queue item"""
        gpu_acquired = False
        
        try:
            # Acquire GPU resource
            gpu_acquired = await self.gpu_manager.acquire_gpu()
            if not gpu_acquired:
                # Re-queue item
                item.status = QueueItemStatus.QUEUED
                item.started_at = None
                self.queues[item.device_id].append(item)
                self.queue_semaphore.release()
                return
            
            logger.info(f"⚙️ Processing item {item.id}: {item.filename} ({item.processing_type.value})")
            
            item.progress = 10
            item.progress_message = "Processing started..."
            
            # Process based on type
            if item.processing_type == ProcessingType.TRANSCRIPTION:
                if self.process_transcription_callback:
                    result = await self.process_transcription_callback(item)
                    item.result = result
                else:
                    item.error = "Transcription callback not configured"
                    
            elif item.processing_type in [ProcessingType.DOCUMENT, ProcessingType.DOCUMENT_VECTORIZE]:
                if self.process_document_callback:
                    result = await self.process_document_callback(item)
                    item.result = result
                else:
                    item.error = "Document callback not configured"
            
            else:
                item.error = f"Unknown processing type: {item.processing_type}"
            
            # Mark complete
            item.status = QueueItemStatus.COMPLETED if not item.error else QueueItemStatus.FAILED
            item.completed_at = time.time()
            item.progress = 100
            item.progress_message = "Complete" if not item.error else f"Failed: {item.error}"
            
            self._update_device_stats(item.device_id)
            
            processing_time = item.completed_at - item.started_at
            logger.info(f"✅ Completed item {item.id} in {processing_time:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Error processing item {item.id}: {e}")
            item.status = QueueItemStatus.FAILED
            item.completed_at = time.time()
            item.error = str(e)
            item.progress = 100
            item.progress_message = f"Failed: {str(e)}"
            
        finally:
            if gpu_acquired:
                await self.gpu_manager.release_gpu()
            self.queue_semaphore.release()


# Global queue manager instance
_queue_manager: Optional[UploadQueueManager] = None

def get_queue_manager() -> UploadQueueManager:
    """Get or create the global queue manager"""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = UploadQueueManager()
    return _queue_manager

async def initialize_queue_manager(
    transcription_callback: Optional[Callable] = None,
    document_callback: Optional[Callable] = None
) -> UploadQueueManager:
    """Initialize and start the queue manager"""
    manager = get_queue_manager()
    manager.set_callbacks(transcription_callback, document_callback)
    await manager.start()
    return manager
