"""
Tests for Team Dynamics Analyzer
Based on @TheBigFish methodology for High Performing Teams
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestMarkerDetector:
    """Tests for language marker detection"""
    
    @pytest.fixture
    def detector(self):
        from ai.team_dynamics_analyzer import MarkerDetector
        return MarkerDetector()
    
    def test_detect_vulnerability_dutch(self, detector):
        """Test Dutch vulnerability markers"""
        text = "Ik weet het niet, kun je me helpen?"
        markers = detector.detect_all_markers(text)
        assert "vulnerability" in markers
        assert len(markers["vulnerability"]) >= 2
    
    def test_detect_vulnerability_english(self, detector):
        """Test English vulnerability markers"""
        text = "I don't know, can you help me understand this?"
        markers = detector.detect_all_markers(text)
        assert "vulnerability" in markers
    
    def test_detect_blame_frame(self, detector):
        """Test blame frame detection"""
        text = "Why did you let this fail? Who is responsible for this mess?"
        markers = detector.detect_all_markers(text)
        assert "blame_frame" in markers
    
    def test_detect_learning_frame(self, detector):
        """Test learning frame detection"""
        text = "What can we learn from this? That's an interesting point."
        markers = detector.detect_all_markers(text)
        assert "learning_frame" in markers
    
    def test_detect_we_language(self, detector):
        """Test we-language detection"""
        text = "We will make this happen together. Our team is committed."
        markers = detector.detect_all_markers(text)
        assert "we_language" in markers
    
    def test_detect_commitment(self, detector):
        """Test commitment language detection"""
        text = "I'll take this on and deliver by Friday."
        markers = detector.detect_all_markers(text)
        assert "commitment_language" in markers
    
    def test_detect_frames(self, detector):
        """Test frame type detection"""
        from ai.team_dynamics_analyzer import FrameType
        
        text = "I made a mistake here. What can we learn from this?"
        frames = detector.detect_frames(text)
        
        assert FrameType.VULNERABILITY in frames
        assert FrameType.LEARNING in frames
    
    def test_count_pronouns(self, detector):
        """Test pronoun counting"""
        text = "We decided that I should handle this. They were not involved."
        pronouns = detector.count_pronouns(text)
        
        assert pronouns["we"] >= 1
        assert pronouns["i"] >= 1
        assert pronouns["they"] >= 1


class TestInputQualityAnalyzer:
    """Tests for input quality validation"""
    
    @pytest.fixture
    def analyzer(self):
        from ai.team_dynamics_analyzer import InputQualityAnalyzer
        return InputQualityAnalyzer()
    
    def test_empty_input(self, analyzer):
        """Test handling of empty input"""
        from ai.team_dynamics_analyzer import InputQuality
        
        result = analyzer.analyze([])
        
        assert result.quality_level == InputQuality.INSUFFICIENT
        assert not result.meets_minimum_requirements
        assert "No utterances" in str(result.issues)
    
    def test_minimum_requirements(self, analyzer):
        """Test minimum requirements check"""
        from ai.team_dynamics_analyzer import Utterance
        
        # Create minimal valid input
        utterances = []
        for i in range(60):
            speaker = f"speaker_{i % 3}"
            utterances.append(Utterance(
                id=f"u_{i}",
                speaker_id=speaker,
                speaker_name=speaker.title(),
                text=f"This is utterance number {i} with some content."
            ))
        
        result = analyzer.analyze(utterances)
        
        assert result.meets_minimum_requirements
        assert result.total_utterances == 60
        assert result.total_speakers == 3
    
    def test_quality_with_audio_features(self, analyzer):
        """Test quality score with audio features"""
        from ai.team_dynamics_analyzer import Utterance, InputQuality
        
        utterances = []
        for i in range(100):
            speaker = f"speaker_{i % 4}"
            utterances.append(Utterance(
                id=f"u_{i}",
                speaker_id=speaker,
                speaker_name=speaker.title(),
                text=f"Content for utterance {i}.",
                timestamp_start=float(i * 5),
                timestamp_end=float(i * 5 + 4),
                pitch_mean=150.0 + i,
                energy_mean=-15.0
            ))
        
        result = analyzer.analyze(utterances)
        
        assert result.has_audio_features
        assert result.has_timestamps
        assert result.quality_level in [InputQuality.EXCELLENT, InputQuality.GOOD]


class TestDimensionAnalyzers:
    """Tests for individual dimension analyzers"""
    
    @pytest.fixture
    def utterances_safe_team(self):
        """Sample utterances for a psychologically safe team"""
        from ai.team_dynamics_analyzer import Utterance
        
        return [
            Utterance(id="1", speaker_id="ceo", speaker_name="CEO", 
                     text="I'm not sure about this. What do you all think?"),
            Utterance(id="2", speaker_id="member1", speaker_name="Alice",
                     text="I made a mistake on the last project. Here's what I learned."),
            Utterance(id="3", speaker_id="member2", speaker_name="Bob",
                     text="That's an interesting point. Tell me more about that."),
            Utterance(id="4", speaker_id="ceo", speaker_name="CEO",
                     text="What can we learn from this situation?"),
            Utterance(id="5", speaker_id="member1", speaker_name="Alice",
                     text="I don't know the answer, but I'll find out."),
        ] * 20  # Repeat for volume
    
    @pytest.fixture
    def utterances_blame_team(self):
        """Sample utterances for a blame-oriented team"""
        from ai.team_dynamics_analyzer import Utterance
        
        return [
            Utterance(id="1", speaker_id="ceo", speaker_name="CEO",
                     text="Why did you let this happen?"),
            Utterance(id="2", speaker_id="member1", speaker_name="Alice",
                     text="That's not my fault, they should have done it."),
            Utterance(id="3", speaker_id="ceo", speaker_name="CEO",
                     text="Who is responsible for this mess?"),
            Utterance(id="4", speaker_id="member2", speaker_name="Bob",
                     text="I think they dropped the ball on this."),
        ] * 20
    
    def test_psychological_safety_high(self, utterances_safe_team):
        """Test high psychological safety detection"""
        from ai.team_dynamics_analyzer import PsychologicalSafetyAnalyzer
        
        analyzer = PsychologicalSafetyAnalyzer()
        result = analyzer.analyze(utterances_safe_team, {})
        
        assert result.score >= 3.0
        assert len(result.positive_indicators) > 0
    
    def test_psychological_safety_low(self, utterances_blame_team):
        """Test low psychological safety detection"""
        from ai.team_dynamics_analyzer import PsychologicalSafetyAnalyzer
        
        analyzer = PsychologicalSafetyAnalyzer()
        result = analyzer.analyze(utterances_blame_team, {})
        
        assert result.score <= 3.5
        assert len(result.negative_indicators) > 0
    
    def test_collective_ownership_we_language(self):
        """Test collective ownership with we-language"""
        from ai.team_dynamics_analyzer import Utterance, CollectiveOwnershipAnalyzer
        
        utterances = [
            Utterance(id=str(i), speaker_id="speaker", speaker_name="Speaker",
                     text="We will achieve our goals together. Our team is committed.")
            for i in range(50)
        ]
        
        analyzer = CollectiveOwnershipAnalyzer()
        result = analyzer.analyze(utterances, {})
        
        assert result.score >= 3.0
        assert "Strong we-orientation" in str(result.patterns_detected)
    
    def test_learning_adaptation(self):
        """Test learning and adaptation detection"""
        from ai.team_dynamics_analyzer import Utterance, LearningAdaptationAnalyzer
        
        utterances = [
            Utterance(id="1", speaker_id="s1", speaker_name="S1",
                     text="Let's try a new experiment. We expect that this will improve."),
            Utterance(id="2", speaker_id="s2", speaker_name="S2",
                     text="Based on what we learned last time, we should iterate."),
            Utterance(id="3", speaker_id="s1", speaker_name="S1",
                     text="This is a hypothesis we can validate with a pilot."),
        ] * 20
        
        analyzer = LearningAdaptationAnalyzer()
        result = analyzer.analyze(utterances, {})
        
        assert result.score >= 3.0
        assert len(result.positive_indicators) > 0


class TestTeamDynamicsAnalyzer:
    """Tests for the main team dynamics analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        from ai.team_dynamics_analyzer import TeamDynamicsAnalyzer
        return TeamDynamicsAnalyzer()
    
    def test_parse_transcript(self, analyzer):
        """Test transcript parsing"""
        transcript = """
        CEO: Welcome everyone to this meeting.
        Alice: Thanks for having us.
        Bob: I have some updates to share.
        CEO: Great, let's hear it.
        """
        
        utterances = analyzer.parse_transcript(transcript)
        
        assert len(utterances) >= 4
        assert any(u.speaker_name == "CEO" for u in utterances)
        assert any(u.speaker_name == "Alice" for u in utterances)
    
    def test_full_analysis(self, analyzer):
        """Test complete team dynamics analysis"""
        # Create a longer transcript to meet minimum requirements
        base_transcript = """
        CEO: I want to start by saying I don't have all the answers here.
        Alice: That's a great point. What can we learn from the last quarter?
        Bob: I think we should try a new approach. Let's experiment.
        CEO: I agree. We need to work together on this.
        Alice: I'll take responsibility for the next phase.
        Bob: Good point, let me add to that.
        CEO: What do you all see as the main challenges?
        Alice: I'm not sure, but I have some ideas to explore.
        Bob: We can validate that with our customers.
        CEO: Excellent. Let's commit to this strategy.
        """
        # Repeat to meet minimum utterance requirements
        transcript = (base_transcript + "\n") * 10
        
        result = analyzer.analyze_transcript(transcript, leader_name="CEO")
        
        # Check result structure
        assert result.analysis_id is not None
        assert result.input_quality is not None
        assert len(result.dimension_scores) == 6
        assert result.team_score > 0
        
        # Check dimension scores
        for dim_name, score in result.dimension_scores.items():
            assert 1.0 <= score.score <= 5.0
            assert 0.0 <= score.confidence <= 1.0
    
    def test_speaker_stats(self, analyzer):
        """Test speaker statistics calculation"""
        base_transcript = """
        CEO: This is the first statement from the CEO.
        Alice: Alice responds here.
        CEO: CEO speaks again with more words this time.
        Bob: Bob joins the conversation.
        CEO: And the CEO concludes.
        """
        transcript = (base_transcript + "\n") * 15
        
        result = analyzer.analyze_transcript(transcript)
        
        assert len(result.speaker_stats) == 3
        assert "ceo" in result.speaker_stats
        # 3 utterances per repeat * 15 repeats = 45 CEO utterances
        assert result.speaker_stats["ceo"].total_utterances == 45
    
    def test_dominance_index(self, analyzer):
        """Test dominance index calculation"""
        # Unbalanced transcript - CEO dominates
        base_transcript = """
        CEO: Long statement from the CEO with many many many words here.
        CEO: Another long statement from the CEO with more content.
        CEO: Yet another from the CEO with detailed explanation here.
        Alice: Short response.
        CEO: CEO dominates again with lots of content here for sure.
        """
        transcript = (base_transcript + "\n") * 15
        
        result = analyzer.analyze_transcript(transcript)
        
        # CEO dominates, so dominance index should be high
        assert result.dominance_index > 0.5


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_analyze_team_dynamics_function(self):
        """Test the main entry point function"""
        from ai.team_dynamics_analyzer import analyze_team_dynamics
        
        base_transcript = """
        Leader: Welcome to our strategy session.
        Alice: Thanks. I have concerns about the timeline.
        Bob: I agree with that concern. We should discuss.
        Leader: What do you suggest we do differently?
        Alice: Let's try a phased approach. We can learn as we go.
        Leader: Good idea. I'll take ownership of coordinating this.
        """
        transcript = (base_transcript + "\n") * 15
        
        result = await analyze_team_dynamics(transcript, leader_name="Leader")
        
        assert result.team_score > 0
        assert result.input_quality is not None
    
    @pytest.mark.asyncio
    async def test_dutch_transcript(self):
        """Test analysis of Dutch transcript"""
        from ai.team_dynamics_analyzer import analyze_team_dynamics
        
        base_transcript = """
        CEO: Welkom bij de vergadering. Ik weet het niet zeker, wat denken jullie?
        Manager: Goed punt. We kunnen hier veel van leren.
        CEO: Laten we proberen een nieuwe aanpak te testen.
        Manager: Ik neem dit op me voor volgende week.
        CEO: Fantastisch. Samen gaan we dit oplossen.
        """
        transcript = (base_transcript + "\n") * 15
        
        result = await analyze_team_dynamics(transcript, leader_name="CEO")
        
        assert result.team_score > 0
        # Should detect Dutch markers
        assert len(result.dimension_scores) == 6


class TestOutputQuality:
    """Tests for output quality and format"""
    
    @pytest.mark.asyncio
    async def test_output_format(self):
        """Test output format is correct for dialogue"""
        from ai.team_dynamics_analyzer import analyze_team_dynamics
        
        transcript = "CEO: Test statement. Member: Response."
        result = await analyze_team_dynamics(transcript)
        
        output_dict = result.to_dict()
        
        # Check required fields
        assert "analysis_id" in output_dict
        assert "team_score" in output_dict
        assert "dimension_scores" in output_dict
        assert "input_quality" in output_dict
        assert "top_indicators" in output_dict
    
    @pytest.mark.asyncio
    async def test_confidence_levels(self):
        """Test that confidence levels are appropriate"""
        from ai.team_dynamics_analyzer import analyze_team_dynamics
        
        # Short transcript should have low confidence
        short_transcript = "CEO: Hello. Member: Hi."
        result = await analyze_team_dynamics(short_transcript)
        
        # Low volume = low confidence
        for score in result.dimension_scores.values():
            assert score.confidence <= 0.5
    
    @pytest.mark.asyncio
    async def test_explanation_provided(self):
        """Test that explanations are provided for scores"""
        from ai.team_dynamics_analyzer import analyze_team_dynamics
        
        transcript = """
        CEO: We need to learn from our mistakes.
        Member: I agree. Let's experiment with new approaches.
        """ * 30  # Repeat for volume
        
        result = await analyze_team_dynamics(transcript)
        
        for score in result.dimension_scores.values():
            assert score.explanation != ""
            assert len(score.explanation) > 10
