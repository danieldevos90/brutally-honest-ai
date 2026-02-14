"""
Pydantic Schemas for Brutally Honest AI API
"""

from .api_schemas import (
    # Base
    BaseResponse,
    JobStatus,
    ConnectionType,
    
    # Auth
    AuthInfoResponse,
    ApiKeyCreate,
    ApiKeyResponse,
    ApiKeyInfo,
    ApiKeyListResponse,
    TokenVerifyResponse,
    
    # Device
    DeviceInfo,
    DeviceStatusResponse,
    DeviceConnectResponse,
    SystemStatusResponse,
    
    # Recording
    RecordingItem,
    RecordingsListResponse,
    RecordingAnalysisResponse,
    
    # AI Processing
    AIProcessRequest,
    VoiceAnalysis,
    SentenceMood,
    TranscriptionResult,
    
    # Jobs
    JobSubmitResponse,
    JobStatusResponse,
    JobListItem,
    JobListResponse,
    
    # Documents
    DocumentUploadResponse,
    DocumentSearchResult,
    DocumentSearchResponse,
    DocumentQueryRequest,
    DocumentQueryResponse,
    DocumentStatsResponse,
    
    # Profiles
    ProfileCreateRequest,
    ClientProfileCreate,
    BrandProfileCreate,
    PersonProfileCreate,
    ProfileResponse,
    ProfileListResponse,
    FactAddRequest,
    FactResponse,
    
    # Validation
    ClaimExtractRequest,
    ClaimData,
    ClaimValidateRequest,
    ValidationTranscriptionRequest,
    ClaimListResponse,
    ValidationResultResponse,
    ValidationReportResponse,
    
    # Commands
    DeviceCommandRequest,
    DeviceCommandResponse,
    ConnectionSwitchRequest,
    ConnectionSwitchResponse,
    
    # History
    HistoryEntry,
    HistoryListResponse,
    ReanalyzeResponse,
)

__all__ = [
    # Base
    "BaseResponse",
    "JobStatus",
    "ConnectionType",
    
    # Auth
    "AuthInfoResponse",
    "ApiKeyCreate",
    "ApiKeyResponse",
    "ApiKeyInfo",
    "ApiKeyListResponse",
    "TokenVerifyResponse",
    
    # Device
    "DeviceInfo",
    "DeviceStatusResponse",
    "DeviceConnectResponse",
    "SystemStatusResponse",
    
    # Recording
    "RecordingItem",
    "RecordingsListResponse",
    "RecordingAnalysisResponse",
    
    # AI Processing
    "AIProcessRequest",
    "VoiceAnalysis",
    "SentenceMood",
    "TranscriptionResult",
    
    # Jobs
    "JobSubmitResponse",
    "JobStatusResponse",
    "JobListItem",
    "JobListResponse",
    
    # Documents
    "DocumentUploadResponse",
    "DocumentSearchResult",
    "DocumentSearchResponse",
    "DocumentQueryRequest",
    "DocumentQueryResponse",
    "DocumentStatsResponse",
    
    # Profiles
    "ProfileCreateRequest",
    "ClientProfileCreate",
    "BrandProfileCreate",
    "PersonProfileCreate",
    "ProfileResponse",
    "ProfileListResponse",
    "FactAddRequest",
    "FactResponse",
    
    # Validation
    "ClaimExtractRequest",
    "ClaimData",
    "ClaimValidateRequest",
    "ValidationTranscriptionRequest",
    "ClaimListResponse",
    "ValidationResultResponse",
    "ValidationReportResponse",
    
    # Commands
    "DeviceCommandRequest",
    "DeviceCommandResponse",
    "ConnectionSwitchRequest",
    "ConnectionSwitchResponse",
    
    # History
    "HistoryEntry",
    "HistoryListResponse",
    "ReanalyzeResponse",
]
