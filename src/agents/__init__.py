"""
Agents Module - Dynamic AI agents for different analysis use cases

Available Agents:
- Persona: Personality & communication style analysis
- Fact Checker: Verify claims against documents
- Interview: Candidate assessment
- Culture: Culture fit analysis
- Sales: Sales conversation signals
- Meeting: Action items & decisions
- Custom: User-defined agents

Usage:
    from src.agents import get_agent_registry, get_agent_runner
    
    registry = get_agent_registry()
    runner = get_agent_runner()
    
    # List agents
    agents = registry.list_agents()
    
    # Run analysis
    result = await runner.run_agent("agent_persona", text)
"""

from .agent_framework import (
    AgentType,
    AgentConfig,
    AgentResult,
    AgentRegistry,
    AgentRunner,
    get_agent_registry,
    get_agent_runner,
)

from .agent_store import (
    AgentStore,
    get_agent_store,
)

from .llm_agent_runner import (
    LLMAgentResult,
    LLMAgentRunner,
    get_llm_agent_runner,
)

from .api_routes import router as agent_router

__all__ = [
    # Core
    "AgentType",
    "AgentConfig", 
    "AgentResult",
    "AgentRegistry",
    "AgentRunner",
    "get_agent_registry",
    "get_agent_runner",
    # Store
    "AgentStore",
    "get_agent_store",
    # LLM Runner
    "LLMAgentResult",
    "LLMAgentRunner", 
    "get_llm_agent_runner",
    # API
    "agent_router",
]

