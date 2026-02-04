"""
AI Processing Module for Brutally Honest AI

Modules:
- llama_processor: Core transcription and analysis
- enhanced_processor: Document-validated analysis
- intelligent_fact_checker: AI-powered fact checking
- comprehensive_analyzer: Full-spectrum analysis
- team_dynamics_analyzer: 6-dimension team performance analysis (@TheBigFish methodology)
"""

from .comprehensive_analyzer import (
    ComprehensiveAnalyzer,
    analyze_recording,
    get_comprehensive_analyzer,
    AnalysisQuality,
    Sentiment,
    Emotion,
    SentimentResult,
    EmotionResult,
    ContextAnalysis,
    QualityMetrics,
    ComprehensiveAnalysisResult
)

from .team_dynamics_analyzer import (
    TeamDynamicsAnalyzer,
    analyze_team_dynamics,
    get_team_dynamics_analyzer,
    Dimension,
    InputQuality,
    FrameType,
    Utterance,
    SpeakerStats,
    DimensionScore,
    InputQualityReport,
    TeamDynamicsResult,
    MarkerDetector,
    InputQualityAnalyzer
)

from .llama_processor import LLAMAProcessor, AIProcessingResult, get_processor

__all__ = [
    # Core processing
    'LLAMAProcessor', 'AIProcessingResult', 'get_processor',
    # Comprehensive analysis
    'ComprehensiveAnalyzer', 'analyze_recording', 'get_comprehensive_analyzer',
    # Team dynamics
    'TeamDynamicsAnalyzer', 'analyze_team_dynamics', 'get_team_dynamics_analyzer',
    'Dimension', 'InputQuality', 'FrameType', 'Utterance', 'SpeakerStats',
    'DimensionScore', 'InputQualityReport', 'TeamDynamicsResult'
]
