"""
Pydantic Schemas for Brutally Honest AI API
Proper request/response validation following FastAPI best practices
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConnectionType(str, Enum):
    USB = "usb"
    BLE = "ble"
    NONE = "none"


# ============================================
# BASE SCHEMAS
# ============================================

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    error: Optional[str] = None


# ============================================
# AUTH SCHEMAS
# ============================================

class AuthInfoResponse(BaseModel):
    message: str
    auth_methods: List[str]
    key_format: str
    docs_url: str
    create_key: str


class ApiKeyCreate(BaseModel):
    name: str = Field(default="API Key", min_length=1, max_length=100)


class ApiKeyResponse(BaseModel):
    success: bool
    api_key: str
    name: str
    message: str


class ApiKeyInfo(BaseModel):
    name: str
    created: str
    is_master: bool
    hash_prefix: str


class ApiKeyListResponse(BaseModel):
    keys: List[ApiKeyInfo]


class TokenVerifyResponse(BaseModel):
    valid: bool
    name: Optional[str] = None
    permissions: List[str] = []
    is_master: bool = False


# ============================================
# DEVICE SCHEMAS
# ============================================

class DeviceInfo(BaseModel):
    device_id: str
    description: str
    connection_type: ConnectionType
    confidence: int = Field(ge=0, le=100)
    connected: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class DeviceStatusResponse(BaseModel):
    success: bool
    devices: List[Dict[str, Any]]
    count: int
    active_device: Optional[str] = None
    scan_timestamp: float
    error: Optional[str] = None


class DeviceConnectResponse(BaseModel):
    success: bool
    message: str
    active_device: Optional[str] = None


class SystemStatusResponse(BaseModel):
    device_connected: bool
    connection_type: str
    recording: bool
    files: int
    sd_card_present: bool
    ble_connected: bool
    free_ram: str
    device_model: str
    port: str
    battery_voltage: Optional[float] = None
    battery_percentage: Optional[int] = None
    battery_status: Optional[str] = None
    whisper_ready: bool
    llm_ready: bool
    timestamp: Optional[float] = None


# ============================================
# RECORDING SCHEMAS
# ============================================

class RecordingItem(BaseModel):
    name: str
    size: int
    size_mb: float
    date: Optional[str] = None


class RecordingsListResponse(BaseModel):
    success: bool
    recordings: List[RecordingItem]
    total_files: int
    total_size: int
    total_size_mb: float
    error: Optional[str] = None


class RecordingAnalysisResponse(BaseModel):
    success: bool
    channels: Optional[int] = None
    rate: Optional[int] = None
    bits: Optional[int] = None
    frames: Optional[int] = None
    duration_s: Optional[float] = None
    rms: Optional[int] = None
    peak: Optional[int] = None
    error: Optional[str] = None


# ============================================
# AI PROCESSING SCHEMAS
# ============================================

class AIProcessRequest(BaseModel):
    filename: str = Field(..., min_length=1)
    model: str = Field(default="llama")
    task: str = Field(default="transcribe_and_analyze")


class VoiceAnalysis(BaseModel):
    pitch_hz: float
    pitch_variation: float
    speaking_rate_wpm: float
    pause_ratio: float
    pause_count: int
    speech_rhythm: str
    confidence_indicator: float
    stress_indicator: float
    engagement_indicator: float
    energy_mean_db: float
    duration_seconds: float


class SentenceMood(BaseModel):
    sentence: str
    mood: str
    confidence: float


class TranscriptionResult(BaseModel):
    success: bool
    filename: str
    transcription: Optional[str] = None
    analysis: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    keywords: Optional[List[str]] = None
    fact_check: Optional[str] = None
    brutal_honesty: Optional[str] = None
    credibility_score: Optional[str] = None
    questionable_claims: Optional[List[str]] = None
    corrections: Optional[List[str]] = None
    confidence: Optional[str] = None
    processing_time: Optional[str] = None
    source: Optional[str] = None
    model_used: Optional[str] = None
    task: Optional[str] = None
    error: Optional[str] = None
    
    # Enhanced fields
    voice_analysis: Optional[VoiceAnalysis] = None
    sentence_moods: Optional[List[Dict[str, Any]]] = None
    agents_used: Optional[List[str]] = None
    
    # Document validation fields
    document_validation: Optional[Dict[str, Any]] = None
    validation_score: Optional[str] = None
    fact_check_sources: Optional[List[str]] = None
    contradictions: Optional[List[str]] = None
    supporting_evidence: Optional[List[str]] = None


# ============================================
# ASYNC JOB SCHEMAS
# ============================================

class JobSubmitResponse(BaseModel):
    success: bool
    job_id: str
    message: str
    status_url: str
    filename: str
    file_size: int


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    progress_message: str
    filename: str
    file_size: int
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[TranscriptionResult] = None
    error: Optional[str] = None


class JobListItem(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    filename: str
    created_at: str
    completed_at: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: List[JobListItem]
    total: int


# ============================================
# DOCUMENT SCHEMAS
# ============================================

class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DocumentSearchResult(BaseModel):
    document_id: str
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]


class DocumentSearchResponse(BaseModel):
    success: bool
    query: str
    results: List[DocumentSearchResult]
    total_results: int


class DocumentQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)


class DocumentQueryResponse(BaseModel):
    success: bool
    query: str
    response: str
    sources: List[Dict[str, Any]]
    context_used: int


class DocumentStatsResponse(BaseModel):
    success: bool
    stats: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================
# PROFILE SCHEMAS
# ============================================

class ProfileCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    tags: Optional[str] = None


class ClientProfileCreate(ProfileCreateRequest):
    type: str = Field(..., min_length=1, max_length=50)


class BrandProfileCreate(ProfileCreateRequest):
    values: Optional[str] = None


class PersonProfileCreate(ProfileCreateRequest):
    role: Optional[str] = Field(None, max_length=100)
    company: Optional[str] = Field(None, max_length=200)
    bio: Optional[str] = Field(None, max_length=2000)


class ProfileResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ProfileListResponse(BaseModel):
    success: bool
    profiles: List[Dict[str, Any]]
    count: int


class FactAddRequest(BaseModel):
    statement: str = Field(..., min_length=1, max_length=2000)
    source_id: str = Field(..., min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class FactResponse(BaseModel):
    success: bool
    message: str
    fact: Optional[Dict[str, Any]] = None


# ============================================
# VALIDATION SCHEMAS
# ============================================

class ClaimExtractRequest(BaseModel):
    transcription: str = Field(..., min_length=1)
    transcription_id: str = Field(..., min_length=1)


class ClaimData(BaseModel):
    id: str
    text: str
    type: str
    transcription_id: str
    timestamp: float = 0.0
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class ClaimValidateRequest(BaseModel):
    id: str
    text: str
    type: str = "statement"
    transcription_id: str
    timestamp: float = 0.0
    confidence: float = 1.0


class ValidationTranscriptionRequest(BaseModel):
    transcription: str = Field(..., min_length=1)
    transcription_id: str = Field(..., min_length=1)
    extract_claims: bool = True


class ClaimListResponse(BaseModel):
    success: bool
    claims: List[Dict[str, Any]]
    count: int


class ValidationResultResponse(BaseModel):
    success: bool
    validation: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ValidationReportResponse(BaseModel):
    success: bool
    report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================
# COMMAND SCHEMAS
# ============================================

class DeviceCommandRequest(BaseModel):
    command: str = Field(..., min_length=1, max_length=500)


class DeviceCommandResponse(BaseModel):
    success: bool
    command: str
    response: Optional[str] = None
    error: Optional[str] = None


class ConnectionSwitchRequest(BaseModel):
    type: str = Field(..., pattern="^(usb|ble)$")


class ConnectionSwitchResponse(BaseModel):
    success: bool
    connection_type: str
    message: str
    error: Optional[str] = None


# ============================================
# HISTORY SCHEMAS
# ============================================

class HistoryEntry(BaseModel):
    id: str
    timestamp: str
    originalFilename: str
    savedFilename: str
    filePath: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    title: Optional[str] = None


class HistoryListResponse(BaseModel):
    success: bool
    history: List[HistoryEntry]
    count: Optional[int] = None
    error: Optional[str] = None


class ReanalyzeResponse(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
