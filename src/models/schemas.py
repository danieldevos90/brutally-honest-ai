"""
Pydantic schemas for API requests and responses
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class AudioAnalysisRequest(BaseModel):
    """Request for audio analysis"""
    file_name: str
    duration: Optional[float] = None
    sample_rate: Optional[int] = 16000

class SpeakerSegmentResponse(BaseModel):
    """Speaker segment in response"""
    speaker_id: str
    start_time: float
    end_time: float
    text: str
    confidence: float

class FactCheckResponse(BaseModel):
    """Fact-checking results"""
    is_accurate: bool
    confidence: float
    issues: List[str]
    corrections: List[str]
    sources: List[str]

class FeedbackResponse(BaseModel):
    """Feedback results"""
    summary: str
    suggestions: List[str]
    accuracy_score: float
    process_alignment: float
    key_points: List[str]

class AnalysisResponse(BaseModel):
    """Complete analysis results"""
    fact_check: FactCheckResponse
    feedback: FeedbackResponse
    confidence: float

class AudioAnalysisResponse(BaseModel):
    """Complete audio analysis response"""
    session_id: str
    transcript: str
    speakers: List[SpeakerSegmentResponse]
    analysis: AnalysisResponse
    timestamp: datetime

class SessionSummary(BaseModel):
    """Session summary for listing"""
    id: str
    transcript: str
    audio_duration: float
    speaker_count: int
    confidence: float
    created_at: datetime

class SessionDetail(BaseModel):
    """Detailed session information"""
    id: str
    transcript: str
    audio_duration: float
    speaker_count: int
    confidence: float
    created_at: datetime
    speakers: List[SpeakerSegmentResponse]
    analysis: AnalysisResponse

class SystemStatus(BaseModel):
    """System status response"""
    omi_connected: bool
    audio_processor: bool
    llm_analyzer: bool
    database: bool

class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    type: str  # "transcription", "analysis", "error"
    data: Dict[str, Any]

class TranscriptionData(BaseModel):
    """Real-time transcription data"""
    text: str
    speaker: Optional[str]
    timestamp: datetime

class AnalysisData(BaseModel):
    """Real-time analysis data"""
    fact_check: FactCheckResponse
    feedback: str
    confidence: float
