"""
LLM Agent Runner - Uses LLAMA/Gemini for intelligent agent analysis

Each agent's system_prompt guides the LLM to analyze text from that perspective.
Combines pattern matching with deep LLM understanding.
"""

import logging
import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LLMAgentResult:
    """Result from LLM-powered agent analysis"""
    agent_id: str
    agent_name: str
    agent_type: str
    
    # LLM Analysis
    summary: str = ""
    detailed_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Structured findings
    findings: List[Dict[str, Any]] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    
    # Pattern matches (from rule-based)
    positive_matches: List[str] = field(default_factory=list)
    negative_matches: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    follow_up_questions: List[str] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    processing_time: float = 0.0
    llm_used: str = ""


class LLMAgentRunner:
    """
    Runs agents using LLM for deep analysis.
    
    Flow:
    1. Load agent config (patterns, prompts, focus areas)
    2. Run pattern matching for quick signals
    3. Send to LLM with agent's system prompt for deep analysis
    4. Combine and structure results
    """
    
    def __init__(self, llm_processor=None):
        self.llm = llm_processor
        logger.info("LLMAgentRunner initialized")
    
    async def initialize_llm(self):
        """Initialize LLM processor if not provided"""
        if self.llm is None:
            try:
                # Try to import the existing LLAMA processor
                import sys
                sys.path.insert(0, "/home/brutally/brutally-honest-ai")
                from src.ai.llama_processor import get_llama_processor
                self.llm = await get_llama_processor()
                logger.info("LLM processor initialized")
            except Exception as e:
                logger.warning(f"Could not initialize LLM: {e}")
    
    async def run_agent(
        self,
        agent_config: Dict[str, Any],
        text: str,
        context: Dict[str, Any] = None
    ) -> LLMAgentResult:
        """
        Run an agent analysis on text.
        
        Args:
            agent_config: Agent configuration dict
            text: Text to analyze
            context: Optional context (brand info, role requirements, etc.)
        """
        start_time = time.time()
        
        result = LLMAgentResult(
            agent_id=agent_config.get("id", "unknown"),
            agent_name=agent_config.get("name", "Unknown Agent"),
            agent_type=agent_config.get("agent_type", "custom"),
        )
        
        text_lower = text.lower()
        
        # Step 1: Pattern matching (fast, rule-based)
        for pattern in agent_config.get("positive_patterns", []):
            if pattern.lower() in text_lower:
                result.positive_matches.append(pattern)
        
        for pattern in agent_config.get("negative_patterns", []):
            if pattern.lower() in text_lower:
                result.negative_matches.append(pattern)
        
        # Step 2: LLM Analysis (deep understanding)
        if self.llm:
            llm_result = await self._run_llm_analysis(agent_config, text, context)
            result.summary = llm_result.get("summary", "")
            result.detailed_analysis = llm_result.get("analysis", {})
            result.insights = llm_result.get("insights", [])
            result.scores = llm_result.get("scores", {})
            result.recommendations = llm_result.get("recommendations", [])
            result.follow_up_questions = llm_result.get("follow_up_questions", [])
            result.llm_used = "llama"
        else:
            # Fallback: Generate basic insights from patterns
            result.summary = self._generate_pattern_summary(result, agent_config)
            result.insights = self._generate_pattern_insights(result)
        
        # Calculate confidence
        result.confidence = self._calculate_confidence(result, agent_config)
        result.processing_time = time.time() - start_time
        
        return result
    
    async def _run_llm_analysis(
        self,
        agent_config: Dict[str, Any],
        text: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run LLM analysis with agent's prompts"""
        
        system_prompt = agent_config.get("system_prompt", "")
        analysis_prompt = agent_config.get("analysis_prompt", "")
        focus_areas = agent_config.get("focus_areas", [])
        output_fields = agent_config.get("output_fields", [])
        
        # Build the analysis prompt
        prompt = f"""
{system_prompt}

FOCUS AREAS: {', '.join(focus_areas)}

TEXT TO ANALYZE:
\"\"\"
{text}
\"\"\"

{analysis_prompt if analysis_prompt else ""}

Please provide your analysis in the following JSON format:
{{
    "summary": "2-3 sentence summary of key findings",
    "analysis": {{
        {', '.join([f'"{field}": "your analysis"' for field in output_fields]) if output_fields else '"key_points": []'}
    }},
    "insights": ["insight 1", "insight 2", ...],
    "scores": {{"overall": 0.0-1.0, ...}},
    "recommendations": ["recommendation 1", ...],
    "follow_up_questions": ["question to ask", ...]
}}

CONTEXT: {json.dumps(context) if context else "None provided"}

Respond ONLY with valid JSON.
"""
        
        try:
            # Call LLM
            response = await self.llm.generate(prompt)
            
            # Parse JSON response
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
        
        return {}
    
    def _generate_pattern_summary(
        self,
        result: LLMAgentResult,
        agent_config: Dict[str, Any]
    ) -> str:
        """Generate summary from pattern matches"""
        parts = []
        
        if result.positive_matches:
            parts.append(f"Found {len(result.positive_matches)} positive signals")
        
        if result.negative_matches:
            parts.append(f"Detected {len(result.negative_matches)} potential concerns")
        
        if not parts:
            parts.append("No specific patterns detected")
        
        return ". ".join(parts) + "."
    
    def _generate_pattern_insights(self, result: LLMAgentResult) -> List[str]:
        """Generate insights from pattern matches"""
        insights = []
        
        if result.positive_matches:
            insights.append(f"Positive indicators: {', '.join(result.positive_matches[:3])}")
        
        if result.negative_matches:
            insights.append(f"Areas of concern: {', '.join(result.negative_matches[:3])}")
        
        if len(result.positive_matches) > len(result.negative_matches):
            insights.append("Overall positive pattern distribution")
        elif result.negative_matches:
            insights.append("Some concerns warrant further investigation")
        
        return insights
    
    def _calculate_confidence(
        self,
        result: LLMAgentResult,
        agent_config: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the analysis"""
        # Base confidence from pattern matches
        total_patterns = (
            len(agent_config.get("positive_patterns", [])) +
            len(agent_config.get("negative_patterns", []))
        )
        
        if total_patterns > 0:
            matches = len(result.positive_matches) + len(result.negative_matches)
            pattern_confidence = min(1.0, matches / (total_patterns * 0.3))
        else:
            pattern_confidence = 0.5
        
        # Boost confidence if LLM was used
        if result.llm_used:
            return min(1.0, pattern_confidence + 0.2)
        
        return pattern_confidence
    
    async def run_multi_agent(
        self,
        agents: List[Dict[str, Any]],
        text: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, LLMAgentResult]:
        """Run multiple agents and combine results"""
        results = {}
        
        for agent in agents:
            try:
                result = await self.run_agent(agent, text, context)
                results[agent.get("id", "unknown")] = result
            except Exception as e:
                logger.error(f"Agent {agent.get('name')} failed: {e}")
        
        return results
    
    def combine_results(
        self,
        results: Dict[str, LLMAgentResult]
    ) -> Dict[str, Any]:
        """Combine multiple agent results into unified analysis"""
        combined = {
            "agents_run": list(results.keys()),
            "summaries": {},
            "all_insights": [],
            "all_recommendations": [],
            "all_concerns": [],
            "overall_scores": {},
            "total_processing_time": 0,
        }
        
        for agent_id, result in results.items():
            combined["summaries"][result.agent_name] = result.summary
            combined["all_insights"].extend(result.insights)
            combined["all_recommendations"].extend(result.recommendations)
            combined["all_concerns"].extend(result.negative_matches)
            combined["total_processing_time"] += result.processing_time
            
            for score_name, score_value in result.scores.items():
                key = f"{result.agent_name}_{score_name}"
                combined["overall_scores"][key] = score_value
        
        # Deduplicate
        combined["all_insights"] = list(set(combined["all_insights"]))
        combined["all_recommendations"] = list(set(combined["all_recommendations"]))
        combined["all_concerns"] = list(set(combined["all_concerns"]))
        
        return combined


# Singleton
_llm_runner: Optional[LLMAgentRunner] = None


async def get_llm_agent_runner() -> LLMAgentRunner:
    """Get singleton LLMAgentRunner"""
    global _llm_runner
    if _llm_runner is None:
        _llm_runner = LLMAgentRunner()
        await _llm_runner.initialize_llm()
    return _llm_runner

