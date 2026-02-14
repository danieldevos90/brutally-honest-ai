"""
Tests for Comprehensive Analyzer
Validates full-spectrum audio/text analysis capabilities
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestSentimentAnalyzer:
    """Tests for advanced sentiment analysis"""
    
    @pytest.fixture
    def analyzer(self):
        from ai.comprehensive_analyzer import AdvancedSentimentAnalyzer
        return AdvancedSentimentAnalyzer()
    
    @pytest.mark.asyncio
    async def test_positive_sentiment(self, analyzer):
        """Test detection of positive sentiment"""
        text = "I am very happy with this excellent service. The team did an amazing job!"
        result = await analyzer.analyze(text)
        
        assert result.overall.value in ["positive", "very_positive"]
        assert result.positivity_score > 0
        assert len(result.positive_indicators) > 0
    
    @pytest.mark.asyncio
    async def test_negative_sentiment(self, analyzer):
        """Test detection of negative sentiment"""
        text = "This is terrible. I am very disappointed and frustrated with the poor quality."
        result = await analyzer.analyze(text)
        
        assert result.overall.value in ["negative", "very_negative"]
        assert result.positivity_score < 0
        assert len(result.negative_indicators) > 0
    
    @pytest.mark.asyncio
    async def test_neutral_sentiment(self, analyzer):
        """Test detection of neutral sentiment"""
        text = "The meeting is scheduled for tomorrow at 3pm. Please bring the documents."
        result = await analyzer.analyze(text)
        
        assert result.overall.value == "neutral"
        assert abs(result.positivity_score) < 0.3
    
    @pytest.mark.asyncio
    async def test_mixed_sentiment(self, analyzer):
        """Test detection of mixed sentiment"""
        text = "I loved the product quality, but the delivery was terrible and very late."
        result = await analyzer.analyze(text)
        
        # Should detect both positive and negative indicators
        assert len(result.positive_indicators) > 0
        assert len(result.negative_indicators) > 0
    
    @pytest.mark.asyncio
    async def test_dutch_sentiment(self, analyzer):
        """Test sentiment analysis with Dutch text"""
        text = "Dit is echt geweldig! Ik ben heel blij met het resultaat."
        result = await analyzer.analyze(text)
        
        assert result.overall.value in ["positive", "very_positive", "neutral"]
    
    @pytest.mark.asyncio
    async def test_empty_text(self, analyzer):
        """Test handling of empty text"""
        result = await analyzer.analyze("")
        
        assert result.overall.value == "neutral"
        assert result.confidence == 0.0


class TestEmotionAnalyzer:
    """Tests for emotion analysis"""
    
    @pytest.fixture
    def analyzer(self):
        from ai.comprehensive_analyzer import EmotionAnalyzer
        return EmotionAnalyzer()
    
    @pytest.mark.asyncio
    async def test_happy_emotion(self, analyzer):
        """Test detection of happiness"""
        text = "I am so happy and delighted with this wonderful surprise!"
        result = await analyzer.analyze(text)
        
        assert result.primary_emotion.value in ["happy", "excited"]
    
    @pytest.mark.asyncio
    async def test_angry_emotion(self, analyzer):
        """Test detection of anger"""
        text = "This is ridiculous! I am absolutely furious about this terrible service!"
        result = await analyzer.analyze(text)
        
        assert result.primary_emotion.value in ["angry", "frustrated"]
    
    @pytest.mark.asyncio
    async def test_sad_emotion(self, analyzer):
        """Test detection of sadness"""
        text = "I feel so sad and disappointed. Unfortunately, this didn't work out."
        result = await analyzer.analyze(text)
        
        assert result.primary_emotion.value in ["sad", "neutral"]
    
    @pytest.mark.asyncio
    async def test_confident_emotion(self, analyzer):
        """Test detection of confidence"""
        text = "I am absolutely certain this will work. There is no doubt about it."
        result = await analyzer.analyze(text)
        
        assert result.primary_emotion.value in ["confident", "neutral"]
    
    @pytest.mark.asyncio
    async def test_anxious_emotion(self, analyzer):
        """Test detection of anxiety"""
        text = "I am worried and nervous about what might happen. What if it fails?"
        result = await analyzer.analyze(text)
        
        assert result.primary_emotion.value in ["anxious", "fearful", "neutral"]
    
    @pytest.mark.asyncio
    async def test_voice_emotion_integration(self, analyzer):
        """Test emotion analysis with voice features"""
        text = "This is quite stressful."
        voice_features = {
            "pitch_mean_hz": 200,
            "pitch_std_hz": 50,
            "energy_mean": -5,
            "speaking_rate_wpm": 180,
            "pause_ratio": 0.1,
            "confidence_score": 0.3,
            "stress_indicator": 0.8
        }
        
        result = await analyzer.analyze(text, voice_features)
        
        # Should incorporate voice features
        assert result.voice_emotion is not None or result.text_emotion is not None


class TestContextAnalyzer:
    """Tests for context analysis"""
    
    @pytest.fixture
    def analyzer(self):
        from ai.comprehensive_analyzer import ContextAnalyzer
        # Create new instance which initializes the dictionaries
        analyzer = ContextAnalyzer()
        return analyzer
    
    @pytest.mark.asyncio
    async def test_business_domain(self, analyzer):
        """Test business domain detection"""
        text = "Our sales revenue increased significantly. The customer strategy is working well."
        result = await analyzer.analyze(text)
        
        assert result.domain == "business"
    
    @pytest.mark.asyncio
    async def test_technical_domain(self, analyzer):
        """Test technical domain detection"""
        text = "The API endpoint returns JSON data. We need to optimize the database query."
        result = await analyzer.analyze(text)
        
        assert result.domain == "technical"
    
    @pytest.mark.asyncio
    async def test_language_detection_english(self, analyzer):
        """Test English language detection"""
        text = "The quick brown fox jumps over the lazy dog."
        result = await analyzer.analyze(text)
        
        assert result.language == "english"
    
    @pytest.mark.asyncio
    async def test_language_detection_dutch(self, analyzer):
        """Test Dutch language detection"""
        text = "De snelle bruine vos springt over de luie hond."
        result = await analyzer.analyze(text)
        
        assert result.language == "dutch"
    
    @pytest.mark.asyncio
    async def test_topic_extraction(self, analyzer):
        """Test topic extraction"""
        text = "Machine learning and artificial intelligence are transforming technology."
        result = await analyzer.analyze(text)
        
        assert len(result.topics) > 0
    
    @pytest.mark.asyncio
    async def test_entity_extraction(self, analyzer):
        """Test entity extraction"""
        text = "Microsoft announced 500 million dollars in revenue. John Smith is the CEO."
        result = await analyzer.analyze(text)
        
        assert len(result.entities) > 0
    
    @pytest.mark.asyncio
    async def test_formality_formal(self, analyzer):
        """Test formal text detection"""
        text = "Therefore, I would like to furthermore express my regards regarding this matter."
        result = await analyzer.analyze(text)
        
        assert result.formality_score > 0.5
    
    @pytest.mark.asyncio
    async def test_formality_informal(self, analyzer):
        """Test informal text detection"""
        text = "Yeah, that's kinda cool. Gonna check it out later, okay?"
        result = await analyzer.analyze(text)
        
        assert result.formality_score < 0.5


class TestComprehensiveAnalyzer:
    """Tests for the full comprehensive analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        from ai.comprehensive_analyzer import ComprehensiveAnalyzer
        return ComprehensiveAnalyzer()
    
    @pytest.mark.asyncio
    async def test_full_analysis(self, analyzer):
        """Test complete analysis pipeline"""
        text = """
        Hello everyone, I am very happy to present our quarterly results today.
        Our revenue increased by 25% compared to last year. The team did an amazing job.
        However, we also faced some challenges with supply chain issues.
        Looking forward, I am confident we will achieve our goals.
        """
        
        result = await analyzer.analyze(text, include_fact_check=False)
        
        # Check all components are present
        assert result.transcription == text
        assert result.sentiment is not None
        assert result.emotion is not None
        assert result.context is not None
        assert result.quality is not None
        
        # Check quality metrics
        assert result.quality.quality_score > 0
        assert result.quality.transcription_available == True
        assert result.quality.sentiment_analysis_available == True
    
    @pytest.mark.asyncio
    async def test_analysis_quality_scoring(self, analyzer):
        """Test quality scoring"""
        text = "This is a test with positive sentiment and clear context."
        
        result = await analyzer.analyze(text, include_fact_check=False)
        
        assert result.quality is not None
        assert 0 <= result.quality.quality_score <= 100
        assert result.quality.overall_quality is not None
    
    @pytest.mark.asyncio
    async def test_analysis_without_audio(self, analyzer):
        """Test analysis works without audio"""
        text = "Text-only analysis should still work for sentiment and context."
        
        result = await analyzer.analyze(text, include_fact_check=False)
        
        assert result.sentiment is not None
        assert result.context is not None
        # Voice analysis should not be available
        assert result.voice_features is None
    
    @pytest.mark.asyncio
    async def test_summary_generation(self, analyzer):
        """Test summary is generated"""
        text = "I am very happy about the excellent results we achieved this quarter."
        
        result = await analyzer.analyze(text, include_fact_check=False)
        
        assert result.summary is not None
        assert len(result.summary) > 0
    
    @pytest.mark.asyncio
    async def test_result_serialization(self, analyzer):
        """Test result can be serialized to dict"""
        text = "Test serialization of analysis results."
        
        result = await analyzer.analyze(text, include_fact_check=False)
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "analysis_id" in result_dict
        assert "transcription" in result_dict
        assert "sentiment" in result_dict
        assert "quality" in result_dict


class TestQualityMetrics:
    """Tests for quality metrics"""
    
    @pytest.mark.asyncio
    async def test_quality_levels(self):
        """Test different quality levels are assigned correctly"""
        from ai.comprehensive_analyzer import AnalysisQuality, QualityMetrics
        
        # High quality
        high_quality = QualityMetrics(
            overall_quality=AnalysisQuality.EXCELLENT,
            quality_score=90
        )
        assert high_quality.overall_quality == AnalysisQuality.EXCELLENT
        
        # Low quality
        low_quality = QualityMetrics(
            overall_quality=AnalysisQuality.BASIC,
            quality_score=20
        )
        assert low_quality.overall_quality == AnalysisQuality.BASIC
    
    @pytest.mark.asyncio
    async def test_quality_dict_serialization(self):
        """Test quality metrics serialization"""
        from ai.comprehensive_analyzer import AnalysisQuality, QualityMetrics
        
        quality = QualityMetrics(
            overall_quality=AnalysisQuality.GOOD,
            quality_score=75,
            transcription_available=True,
            sentiment_analysis_available=True
        )
        
        quality_dict = quality.to_dict()
        
        assert isinstance(quality_dict, dict)
        assert quality_dict["overall_quality"] == "good"
        assert quality_dict["quality_score"] == 75
        assert quality_dict["components"]["transcription"] == True


class TestIntegration:
    """Integration tests for the analyze_recording function"""
    
    @pytest.mark.asyncio
    async def test_analyze_recording_function(self):
        """Test the main entry point function"""
        from ai.comprehensive_analyzer import analyze_recording
        
        text = """
        Good morning! Today we will discuss our new product launch.
        I am excited about the opportunities ahead.
        The market research shows positive trends.
        """
        
        result = await analyze_recording(
            transcription=text,
            include_fact_check=False
        )
        
        assert result.analysis_id is not None
        assert result.transcription == text
        assert result.quality is not None
    
    @pytest.mark.asyncio
    async def test_dutch_text_analysis(self):
        """Test analysis of Dutch text"""
        from ai.comprehensive_analyzer import analyze_recording
        
        text = """
        Goedemorgen allemaal! Vandaag bespreken we de nieuwe strategie.
        Ik ben erg blij met de resultaten van vorig kwartaal.
        We hebben een omzetstijging van 20 procent gerealiseerd.
        """
        
        result = await analyze_recording(
            transcription=text,
            include_fact_check=False
        )
        
        assert result.context.language == "dutch"
        assert result.sentiment is not None
