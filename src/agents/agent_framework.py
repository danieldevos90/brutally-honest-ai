"""
Agent Framework - Dynamic AI agents stored in vector database

Each agent has:
- A specific focus/use case
- Custom prompts and rules
- Analysis patterns to look for
- Output structure

Agents can be:
- Pre-built (persona, fact-check, interview, etc.)
- Custom (created per brand/client)
- Combined for multi-perspective analysis
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime
import json
import uuid

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Built-in agent types"""
    PERSONA = "persona"              # Personality & communication analysis
    FACT_CHECKER = "fact_checker"    # Verify claims against documents
    INTERVIEW = "interview"          # Candidate assessment
    CULTURE = "culture"              # Culture fit analysis
    SALES = "sales"                  # Sales conversation analysis
    MEETING = "meeting"              # Meeting insights
    CUSTOM = "custom"                # User-defined


@dataclass
class AgentConfig:
    """Configuration for an analysis agent"""
    id: str
    name: str
    agent_type: AgentType
    description: str
    
    # What this agent looks for
    focus_areas: List[str] = field(default_factory=list)
    
    # Patterns to detect (stored as embeddings in vector DB)
    positive_patterns: List[str] = field(default_factory=list)  # Good signals
    negative_patterns: List[str] = field(default_factory=list)  # Red flags
    neutral_patterns: List[str] = field(default_factory=list)   # Just note
    
    # Custom prompts for LLM
    system_prompt: str = ""
    analysis_prompt: str = ""
    
    # Output configuration
    output_fields: List[str] = field(default_factory=list)
    scoring_rubric: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    brand_id: Optional[str] = None  # If brand-specific
    client_id: Optional[str] = None  # If client-specific
    created_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "agent_type": self.agent_type.value,
            "description": self.description,
            "focus_areas": self.focus_areas,
            "positive_patterns": self.positive_patterns,
            "negative_patterns": self.negative_patterns,
            "neutral_patterns": self.neutral_patterns,
            "system_prompt": self.system_prompt,
            "analysis_prompt": self.analysis_prompt,
            "output_fields": self.output_fields,
            "scoring_rubric": self.scoring_rubric,
            "brand_id": self.brand_id,
            "client_id": self.client_id,
            "created_at": self.created_at.isoformat(),
            "version": self.version,
        }


@dataclass 
class AgentResult:
    """Result from an agent analysis"""
    agent_id: str
    agent_name: str
    agent_type: str
    
    # Findings
    findings: List[Dict[str, Any]] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    
    # Detected patterns
    positive_matches: List[str] = field(default_factory=list)
    negative_matches: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    processing_time: float = 0.0


class AgentRegistry:
    """Registry of available agents - can load from vector DB"""
    
    def __init__(self):
        self.agents: Dict[str, AgentConfig] = {}
        self._load_builtin_agents()
        logger.info(f"AgentRegistry initialized with {len(self.agents)} agents")
    
    def _load_builtin_agents(self):
        """Load pre-configured agents"""
        
        # PERSONA AGENT
        self.register(AgentConfig(
            id="agent_persona",
            name="Persona Analyzer",
            agent_type=AgentType.PERSONA,
            description="Analyzes personality traits, communication style, and values",
            focus_areas=[
                "communication_style",
                "values_and_beliefs", 
                "confidence_level",
                "emotional_intelligence",
                "leadership_traits"
            ],
            positive_patterns=[
                "i believe strongly in",
                "our team achieved",
                "we collaborated",
                "data shows",
                "i take responsibility"
            ],
            negative_patterns=[
                "it wasn't my fault",
                "they made me",
                "i guess maybe",
                "i don't know"
            ],
            output_fields=[
                "communication_style",
                "primary_values",
                "confidence_score",
                "collaboration_score",
                "key_traits"
            ],
            system_prompt="""You are a personality analyst. Analyze speech patterns to understand:
- Communication style (analytical, assertive, collaborative, expressive)
- Core values (what they believe in, care about)
- Confidence level (certain vs hedging language)
- Self vs team focus (I vs We statements)
Provide insights about who this person IS, not just what they say.""",
        ))
        
        # FACT CHECKER AGENT
        self.register(AgentConfig(
            id="agent_factcheck",
            name="Fact Checker",
            agent_type=AgentType.FACT_CHECKER,
            description="Verifies claims against uploaded documents and knowledge base",
            focus_areas=[
                "quantitative_claims",
                "verifiable_statements",
                "source_attribution",
                "contradictions"
            ],
            positive_patterns=[
                "according to",
                "the data shows",
                "research indicates",
                "documented in"
            ],
            negative_patterns=[
                "everyone knows",
                "they say",
                "i heard that",
                "probably"
            ],
            output_fields=[
                "verified_claims",
                "unverified_claims",
                "contradictions",
                "missing_sources",
                "credibility_score"
            ],
            system_prompt="""You are a fact-checker. For each claim:
1. Identify if it's verifiable (factual) or opinion
2. Search for supporting/contradicting evidence
3. Note claims that need source attribution
4. Flag potential exaggerations or misstatements
Be thorough but fair - distinguish between lies and honest mistakes.""",
        ))
        
        # INTERVIEW AGENT
        self.register(AgentConfig(
            id="agent_interview",
            name="Interview Analyzer",
            agent_type=AgentType.INTERVIEW,
            description="Assesses candidates in job interviews",
            focus_areas=[
                "relevant_experience",
                "culture_fit",
                "red_flags",
                "growth_potential",
                "communication_skills"
            ],
            positive_patterns=[
                "i learned from",
                "we achieved together",
                "i take ownership",
                "measurable results",
                "i adapted when"
            ],
            negative_patterns=[
                "my boss was terrible",
                "it wasn't fair",
                "they didn't appreciate",
                "i was the only one",
                "that's not my job"
            ],
            output_fields=[
                "experience_match",
                "culture_fit_score",
                "red_flags",
                "strengths",
                "development_areas",
                "recommended_questions"
            ],
            scoring_rubric={
                "experience_relevance": {"weight": 0.3, "scale": "1-10"},
                "communication": {"weight": 0.2, "scale": "1-10"},
                "culture_fit": {"weight": 0.25, "scale": "1-10"},
                "growth_mindset": {"weight": 0.15, "scale": "1-10"},
                "red_flags": {"weight": 0.1, "scale": "0-5", "inverse": True},
            },
            system_prompt="""You are an interview analyst helping assess candidates.
Look for:
- STAR method responses (Situation, Task, Action, Result)
- Specific examples vs vague claims
- Ownership language vs blame shifting
- Growth mindset vs fixed mindset
- Cultural alignment signals
Flag red flags but also note potential that might be developed.""",
        ))
        
        # CULTURE FIT AGENT
        self.register(AgentConfig(
            id="agent_culture",
            name="Culture Analyzer",
            agent_type=AgentType.CULTURE,
            description="Analyzes alignment with company culture and values",
            focus_areas=[
                "values_alignment",
                "work_style",
                "collaboration_approach",
                "communication_norms",
                "conflict_handling"
            ],
            positive_patterns=[
                "i value",
                "important to me",
                "i prefer working",
                "my ideal team"
            ],
            negative_patterns=[
                "i don't like",
                "i can't work with",
                "that's not how i"
            ],
            output_fields=[
                "values_match",
                "work_style",
                "collaboration_preference",
                "potential_friction",
                "culture_score"
            ],
            system_prompt="""You are analyzing cultural fit. Extract:
- What values does this person express?
- How do they prefer to work (autonomous vs collaborative)?
- How do they handle conflict or disagreement?
- What motivates them?
Compare against the company culture profile if provided.""",
        ))
        
        # SALES CONVERSATION AGENT
        self.register(AgentConfig(
            id="agent_sales",
            name="Sales Analyzer",
            agent_type=AgentType.SALES,
            description="Analyzes sales conversations for signals and opportunities",
            focus_areas=[
                "buying_signals",
                "objections",
                "pain_points",
                "decision_criteria",
                "next_steps"
            ],
            positive_patterns=[
                "we need",
                "our budget is",
                "by when can",
                "who else should",
                "let's schedule"
            ],
            negative_patterns=[
                "we're just looking",
                "send me info",
                "not right now",
                "need to think"
            ],
            output_fields=[
                "buying_stage",
                "pain_points",
                "objections",
                "decision_makers",
                "next_actions",
                "deal_score"
            ],
            system_prompt="""You are a sales conversation analyst. Identify:
- Buying signals (urgency, budget mentions, timeline)
- Objections and concerns
- Pain points the prospect mentioned
- Who the decision makers are
- What next steps were agreed
Provide actionable insights for the sales rep.""",
        ))
        
        # MEETING INSIGHTS AGENT
        self.register(AgentConfig(
            id="agent_meeting",
            name="Meeting Analyzer",
            agent_type=AgentType.MEETING,
            description="Extracts insights and action items from meetings",
            focus_areas=[
                "decisions_made",
                "action_items",
                "key_discussions",
                "participant_contributions",
                "follow_ups"
            ],
            positive_patterns=[
                "we decided",
                "action item",
                "i will",
                "by next week",
                "agreed that"
            ],
            neutral_patterns=[
                "we discussed",
                "the question is",
                "we need to decide"
            ],
            output_fields=[
                "summary",
                "decisions",
                "action_items",
                "open_questions",
                "participant_summary"
            ],
            system_prompt="""You are a meeting analyst. Extract:
- Key decisions that were made
- Action items with owners and deadlines
- Important discussion points
- Open questions that need follow-up
- Who contributed what
Create a useful meeting summary.""",
        ))
    
    def register(self, config: AgentConfig):
        """Register an agent"""
        self.agents[config.id] = config
        logger.info(f"Registered agent: {config.name} ({config.id})")
    
    def get(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def list_agents(self, agent_type: Optional[AgentType] = None) -> List[AgentConfig]:
        """List all agents, optionally filtered by type"""
        if agent_type:
            return [a for a in self.agents.values() if a.agent_type == agent_type]
        return list(self.agents.values())
    
    def create_custom_agent(
        self,
        name: str,
        description: str,
        focus_areas: List[str],
        positive_patterns: List[str] = None,
        negative_patterns: List[str] = None,
        system_prompt: str = "",
        brand_id: str = None,
        client_id: str = None,
    ) -> AgentConfig:
        """Create a custom agent for specific use case"""
        agent = AgentConfig(
            id=f"agent_custom_{uuid.uuid4().hex[:8]}",
            name=name,
            agent_type=AgentType.CUSTOM,
            description=description,
            focus_areas=focus_areas,
            positive_patterns=positive_patterns or [],
            negative_patterns=negative_patterns or [],
            system_prompt=system_prompt,
            brand_id=brand_id,
            client_id=client_id,
        )
        self.register(agent)
        return agent


class AgentRunner:
    """Runs agents against transcriptions/text"""
    
    def __init__(self, registry: AgentRegistry, llm_processor=None, vector_store=None):
        self.registry = registry
        self.llm = llm_processor
        self.vector_store = vector_store
        logger.info("AgentRunner initialized")
    
    async def run_agent(
        self,
        agent_id: str,
        text: str,
        context: Dict[str, Any] = None
    ) -> AgentResult:
        """Run a single agent on text"""
        import time
        start = time.time()
        
        agent = self.registry.get(agent_id)
        if not agent:
            raise ValueError(f"Agent not found: {agent_id}")
        
        result = AgentResult(
            agent_id=agent.id,
            agent_name=agent.name,
            agent_type=agent.agent_type.value,
        )
        
        text_lower = text.lower()
        
        # Pattern matching
        for pattern in agent.positive_patterns:
            if pattern.lower() in text_lower:
                result.positive_matches.append(pattern)
        
        for pattern in agent.negative_patterns:
            if pattern.lower() in text_lower:
                result.negative_matches.append(pattern)
        
        # Generate insights based on matches
        if result.positive_matches:
            result.insights.append(
                f"Positive signals: {', '.join(result.positive_matches[:3])}"
            )
        
        if result.negative_matches:
            result.insights.append(
                f"Watch for: {', '.join(result.negative_matches[:3])}"
            )
        
        # Calculate simple confidence
        total_patterns = len(agent.positive_patterns) + len(agent.negative_patterns)
        if total_patterns > 0:
            matches = len(result.positive_matches) + len(result.negative_matches)
            result.confidence = min(1.0, matches / (total_patterns * 0.3))
        
        # TODO: If LLM available, use it for deeper analysis
        # if self.llm:
        #     llm_result = await self.llm.analyze(text, agent.system_prompt)
        #     result.findings = llm_result.findings
        
        result.processing_time = time.time() - start
        return result
    
    async def run_multiple(
        self,
        agent_ids: List[str],
        text: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, AgentResult]:
        """Run multiple agents and combine results"""
        results = {}
        for agent_id in agent_ids:
            try:
                results[agent_id] = await self.run_agent(agent_id, text, context)
            except Exception as e:
                logger.error(f"Agent {agent_id} failed: {e}")
        return results
    
    async def auto_select_agents(self, text: str) -> List[str]:
        """Automatically select relevant agents based on content"""
        text_lower = text.lower()
        selected = []
        
        # Always include persona for speech analysis
        selected.append("agent_persona")
        
        # Interview context
        if any(w in text_lower for w in ["interview", "position", "role", "hiring"]):
            selected.append("agent_interview")
            selected.append("agent_culture")
        
        # Sales context
        if any(w in text_lower for w in ["price", "budget", "buy", "purchase", "demo"]):
            selected.append("agent_sales")
        
        # Meeting context
        if any(w in text_lower for w in ["meeting", "agenda", "action item", "next steps"]):
            selected.append("agent_meeting")
        
        # Always check facts if there are numbers/claims
        if any(c in text for c in ["%", "percent", "million", "thousand"]):
            selected.append("agent_factcheck")
        
        return list(set(selected))


# Singleton instances
_registry: Optional[AgentRegistry] = None
_runner: Optional[AgentRunner] = None


def get_agent_registry() -> AgentRegistry:
    """Get singleton registry"""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def get_agent_runner() -> AgentRunner:
    """Get singleton runner"""
    global _runner
    if _runner is None:
        _runner = AgentRunner(get_agent_registry())
    return _runner

