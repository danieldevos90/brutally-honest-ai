# Interview Analysis Platform - Feature Roadmap

## Vision Statement
A platform that records interviews and conversations between people to determine:
- **Personas & Personality** - Communication style, thought patterns
- **Cognitive Abilities** - Analytical thinking, problem-solving approach
- **Emotional Intelligence (EQ)** - Self-awareness, empathy indicators
- **Communication Style** - Clarity, structure, persuasiveness
- **Voice Characteristics** - Speaker identification, mood, stress, pace

## Current Architecture Status

### ✅ Fully Implemented
- Basic transcription (Whisper)
- Speaker diarization (pyannote) - multi-speaker detection
- Profile hierarchy (Clients → Brands → Persons)
- Document storage with vector embeddings
- Fact checking for claims
- Recording management

### 🟡 Partially Implemented (Schema Exists, Logic Missing)
- Voice characteristics storage
- Credibility scoring
- Transcription → Profile linking

### ❌ Not Yet Implemented
- Voice emotion/mood detection
- Speaking pace/rhythm analysis
- Personality extraction
- Cognitive assessment
- EQ indicators
- Brand-specific LLM fine-tuning
- Interview-specific workflow

---

## Phase 1: Voice Analysis Enhancement (Week 1-2)

### 1.1 Voice Feature Extraction
```python
@dataclass
class VoiceFeatures:
    """Extracted voice characteristics"""
    speaker_id: str
    
    # Acoustic features
    pitch_mean: float           # Average pitch (Hz)
    pitch_std: float            # Pitch variation
    speaking_rate: float        # Words per minute
    pause_frequency: float      # Pauses per minute
    pause_avg_duration: float   # Average pause length
    
    # Energy/Volume
    volume_mean: float          # Average loudness
    volume_variation: float     # Dynamic range
    
    # Rhythm
    speech_rhythm: str          # "steady", "varied", "hesitant"
    articulation_rate: float    # Syllables per second
    
    # Derived indicators
    confidence_indicator: float  # 0-1 based on voice patterns
    stress_indicator: float      # 0-1 based on pitch/pace changes
    engagement_indicator: float  # 0-1 based on energy/rhythm
```

### 1.2 Implementation
- Use **librosa** for pitch extraction
- Use **webrtcvad** for speech/silence segmentation
- Calculate speaking rate from Whisper timestamps

---

## Phase 2: Emotion & Mood Detection (Week 2-3)

### 2.1 Audio Emotion Model
```python
@dataclass
class EmotionAnalysis:
    """Emotion detected from voice"""
    timestamp: float
    speaker_id: str
    
    # Primary emotions (probability)
    neutral: float
    happy: float
    sad: float
    angry: float
    fearful: float
    surprised: float
    
    # Derived mood
    overall_mood: str  # "positive", "neutral", "negative", "mixed"
    confidence: float
    
    # Interview-specific
    engagement_level: str  # "high", "medium", "low"
    stress_level: str      # "relaxed", "normal", "stressed"
```

### 2.2 Implementation Options
1. **SpeechBrain** - emotion recognition models
2. **Wav2Vec2** with emotion classification head
3. **OpenVoice** for voice analysis
4. **Hume AI API** (external, high quality)

---

## Phase 3: Persona & Personality Extraction (Week 3-4)

### 3.1 Interview Analysis Schema
```python
@dataclass
class InterviewSession:
    """Complete interview analysis"""
    id: str
    recording_id: str
    brand_id: Optional[str]
    client_id: Optional[str]
    
    # Participants
    participants: List[ParticipantAnalysis]
    
    # Session metadata
    duration: float
    date: datetime
    interview_type: str  # "behavioral", "technical", "conversational"
    
    # Extracted insights
    topics_discussed: List[str]
    key_statements: List[Statement]
    action_items: List[str]
    
    # Overall assessment
    session_quality: float
    engagement_score: float

@dataclass
class ParticipantAnalysis:
    """Analysis of individual participant"""
    person_id: str
    name: str
    role: str  # "interviewer", "candidate", "participant"
    
    # Voice profile
    voice_features: VoiceFeatures
    emotion_timeline: List[EmotionAnalysis]
    
    # Communication analysis
    communication_style: CommunicationStyle
    
    # Personality indicators
    personality_traits: PersonalityTraits
    
    # Cognitive indicators
    cognitive_indicators: CognitiveIndicators
    
    # EQ indicators
    eq_indicators: EQIndicators

@dataclass
class CommunicationStyle:
    """Communication pattern analysis"""
    clarity_score: float        # 0-1 how clear their communication
    structure_score: float      # 0-1 organized thinking
    conciseness_score: float    # 0-1 gets to the point
    
    # Patterns
    uses_examples: bool
    asks_clarifying_questions: bool
    interruption_frequency: float
    
    # Style type
    style_type: str  # "analytical", "driver", "expressive", "amiable"
    
@dataclass
class PersonalityTraits:
    """Big Five personality indicators from speech"""
    openness: float         # Intellectual curiosity
    conscientiousness: float # Organization, dependability
    extraversion: float     # Energy, talkativeness
    agreeableness: float    # Cooperation, trust
    neuroticism: float      # Emotional stability (inverse)
    
    # Confidence in assessment
    confidence: float
    evidence: List[str]     # Supporting observations

@dataclass
class CognitiveIndicators:
    """Cognitive ability indicators"""
    analytical_thinking: float    # Breaks down problems
    abstract_reasoning: float     # Handles concepts
    verbal_fluency: float         # Vocabulary, articulation
    memory_recall: float          # References past info
    problem_solving: float        # Approaches solutions
    
    # Learning style
    learning_style: str  # "visual", "auditory", "kinesthetic", "reading"
    
    # Evidence
    evidence: List[str]

@dataclass
class EQIndicators:
    """Emotional Intelligence indicators"""
    self_awareness: float       # Discusses own emotions
    self_regulation: float      # Controls reactions
    motivation: float           # Drive, enthusiasm
    empathy: float              # Understands others
    social_skills: float        # Communication, conflict
    
    # Evidence
    evidence: List[str]
```

### 3.2 Implementation with LLM
```python
class PersonaExtractor:
    """Extract persona from transcription + voice features"""
    
    async def analyze_participant(
        self,
        transcript_segments: List[SpeakerSegment],
        voice_features: VoiceFeatures,
        emotions: List[EmotionAnalysis]
    ) -> ParticipantAnalysis:
        
        # 1. Analyze communication style from transcript
        style = await self._analyze_communication(transcript_segments)
        
        # 2. Extract personality from content + delivery
        personality = await self._extract_personality(
            transcript_segments, 
            voice_features
        )
        
        # 3. Assess cognitive indicators
        cognitive = await self._assess_cognitive(transcript_segments)
        
        # 4. Assess EQ indicators
        eq = await self._assess_eq(transcript_segments, emotions)
        
        return ParticipantAnalysis(...)
    
    async def _extract_personality(self, segments, voice):
        """Use LLM to extract Big Five traits"""
        prompt = f"""
        Analyze this interview transcript and voice characteristics 
        to assess Big Five personality traits.
        
        Transcript:
        {self._format_segments(segments)}
        
        Voice characteristics:
        - Speaking rate: {voice.speaking_rate} wpm
        - Pitch variation: {voice.pitch_std}
        - Pause frequency: {voice.pause_frequency}
        
        For each trait (0-1 scale), provide:
        1. Score
        2. Evidence from the conversation
        
        Traits: Openness, Conscientiousness, Extraversion, 
                Agreeableness, Neuroticism (emotional stability)
        """
        # Call LLAMA/Gemini
        return await self.llm.analyze(prompt)
```

---

## Phase 4: Brand-Specific Training (Week 4-5)

### 4.1 Brand Context Integration
```python
class BrandContextManager:
    """Manage brand-specific context for analysis"""
    
    def __init__(self, brand_id: str):
        self.brand_id = brand_id
        self.vector_store = get_vector_store()
    
    async def load_brand_context(self) -> BrandContext:
        """Load all brand documents and guidelines"""
        # Get brand profile
        brand = await profile_manager.get_brand_profile(self.brand_id)
        
        # Get related documents
        docs = await self.vector_store.search(
            f"brand:{self.brand_id}",
            limit=100
        )
        
        return BrandContext(
            brand=brand,
            values=brand.values,
            guidelines=brand.guidelines,
            documents=docs,
            terminology=self._extract_terminology(docs)
        )
    
    async def validate_against_brand(
        self, 
        statement: str
    ) -> BrandValidation:
        """Check if statement aligns with brand values"""
        context = await self.load_brand_context()
        
        # Search for relevant brand info
        relevant = await self.vector_store.search(
            statement, 
            filter={"brand_id": self.brand_id}
        )
        
        # Use LLM to check alignment
        return await self._check_alignment(statement, relevant)
```

### 4.2 Per-Brand LLM Enhancement
```python
class BrandAwareLLM:
    """LLM with brand-specific context"""
    
    async def analyze_with_brand_context(
        self,
        transcript: str,
        brand_id: str
    ) -> BrandAwareAnalysis:
        # Load brand context
        context = await self.brand_manager.load_brand_context(brand_id)
        
        # Create brand-aware prompt
        system_prompt = f"""
        You are analyzing an interview for {context.brand.name}.
        
        Brand values: {', '.join(context.values)}
        Brand guidelines: {context.guidelines}
        
        When analyzing, consider:
        1. Alignment with brand values
        2. Use of brand terminology
        3. Adherence to guidelines
        """
        
        return await self.llm.analyze(
            system_prompt=system_prompt,
            user_prompt=transcript
        )
```

---

## Phase 5: Complete Interview Workflow (Week 5-6)

### 5.1 Interview Analysis Pipeline
```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTERVIEW ANALYSIS PIPELINE                           │
└─────────────────────────────────────────────────────────────────────────┘

 1. RECORD                2. PROCESS              3. ANALYZE
 ────────                 ─────────              ─────────
 │ Audio   │───────────▶│ Transcribe│──────────▶│ Extract  │
 │ Upload  │             │ Diarize   │           │ Personas │
 │         │             │ Features  │           │ Assess   │
 └─────────┘             └───────────┘           └──────────┘
                               │                      │
                               │                      │
 4. STORE                 ◀────┴──────────────────────┘
 ─────────
 │ Save to    │
 │ Profile    │
 │ Vector DB  │
 └────────────┘
      │
      ▼
 5. REPORT
 ─────────
 │ Generate    │
 │ Interview   │
 │ Summary     │
 │ Insights    │
 └─────────────┘
```

### 5.2 Frontend Integration
- Interview setup wizard
- Real-time participant identification
- Live emotion indicators
- Post-interview report generation
- Comparison across interviews

---

## Implementation Priority

### Sprint 1 (High Priority)
1. ✅ Voice feature extraction (pitch, pace, pauses)
2. ✅ Link recordings to person profiles
3. ✅ Basic emotion detection

### Sprint 2 (Medium Priority)
4. Communication style analysis
5. LLM-based personality extraction
6. Interview session management

### Sprint 3 (Enhancement)
7. Brand context integration
8. EQ and cognitive indicators
9. Comprehensive reporting

### Sprint 4 (Polish)
10. Voice ID / speaker recognition
11. Real-time feedback
12. Historical comparison

---

## Required Dependencies
```
# Audio analysis
librosa>=0.10.0
webrtcvad>=2.0.10
pyannote.audio>=3.0.0

# Emotion detection
speechbrain>=0.5.0
# OR
transformers>=4.30.0  # for wav2vec2-emotion

# LLM
llama-cpp-python>=0.2.0
google-generativeai>=0.3.0  # Gemini

# Voice features
praat-parselmouth>=0.4.0  # Pitch analysis
```

---

## Next Steps

1. **Start with Voice Features** - Extract pitch, pace, pauses from recordings
2. **Link Data** - Connect recordings → persons → brands
3. **Build Analysis Engine** - Create persona extraction prompts
4. **Test with Real Interviews** - Validate accuracy
5. **Iterate** - Refine based on feedback

---

*Document created: November 28, 2025*
*Version: 1.0*

