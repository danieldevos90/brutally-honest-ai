"""
Agent API Routes - CRUD endpoints for managing agents

Endpoints:
- GET /agents - List all agents
- GET /agents/{id} - Get specific agent
- POST /agents - Create new agent
- PUT /agents/{id} - Update agent
- DELETE /agents/{id} - Delete agent
- POST /agents/analyze - Run agent analysis on text
- POST /agents/auto-analyze - Auto-select and run agents
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])


# Pydantic models for API
class AgentCreate(BaseModel):
    """Request model for creating an agent"""
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="What this agent does")
    agent_type: str = Field(default="custom", description="Agent type")
    focus_areas: List[str] = Field(default=[], description="Areas to focus on")
    positive_patterns: List[str] = Field(default=[], description="Positive signals to detect")
    negative_patterns: List[str] = Field(default=[], description="Red flags to detect")
    system_prompt: str = Field(default="", description="System prompt for LLM")
    analysis_prompt: str = Field(default="", description="Analysis prompt for LLM")
    output_fields: List[str] = Field(default=[], description="Fields to include in output")
    brand_id: Optional[str] = Field(default=None, description="Associated brand")
    client_id: Optional[str] = Field(default=None, description="Associated client")


class AgentUpdate(BaseModel):
    """Request model for updating an agent"""
    name: Optional[str] = None
    description: Optional[str] = None
    focus_areas: Optional[List[str]] = None
    positive_patterns: Optional[List[str]] = None
    negative_patterns: Optional[List[str]] = None
    system_prompt: Optional[str] = None
    analysis_prompt: Optional[str] = None


class AnalyzeRequest(BaseModel):
    """Request model for running analysis"""
    text: str = Field(..., description="Text to analyze")
    agent_ids: List[str] = Field(default=[], description="Agent IDs to use (empty for auto)")
    context: dict = Field(default={}, description="Additional context")
    brand_id: Optional[str] = Field(default=None, description="Brand context")


class AgentResponse(BaseModel):
    """Response model for agent"""
    id: str
    name: str
    agent_type: str
    description: str
    focus_areas: List[str]
    brand_id: Optional[str]
    client_id: Optional[str]


# API Endpoints
@router.get("")
async def list_agents(
    brand_id: Optional[str] = None,
    client_id: Optional[str] = None,
    agent_type: Optional[str] = None
):
    """List all available agents"""
    try:
        from .agent_store import get_agent_store
        from . import get_agent_registry
        
        store = await get_agent_store()
        registry = get_agent_registry()
        
        # Get agents from both registry (built-in) and store (custom)
        builtin_agents = [a.to_dict() for a in registry.list_agents()]
        stored_agents = await store.list_agents(brand_id, client_id, agent_type)
        
        # Combine, avoiding duplicates
        all_agents = {a["id"]: a for a in builtin_agents}
        for a in stored_agents:
            all_agents[a["id"]] = a
        
        return {
            "success": True,
            "agents": list(all_agents.values()),
            "total": len(all_agents)
        }
        
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    """Get a specific agent by ID"""
    try:
        from .agent_store import get_agent_store
        from . import get_agent_registry
        
        # Try registry first
        registry = get_agent_registry()
        agent = registry.get(agent_id)
        if agent:
            return {"success": True, "agent": agent.to_dict()}
        
        # Try store
        store = await get_agent_store()
        agent = await store.get_agent(agent_id)
        if agent:
            return {"success": True, "agent": agent}
        
        raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_agent(agent: AgentCreate):
    """Create a new custom agent"""
    try:
        from .agent_store import get_agent_store
        from . import get_agent_registry
        import uuid
        
        # Create agent config
        agent_config = {
            "id": f"agent_custom_{uuid.uuid4().hex[:8]}",
            "name": agent.name,
            "agent_type": agent.agent_type,
            "description": agent.description,
            "focus_areas": agent.focus_areas,
            "positive_patterns": agent.positive_patterns,
            "negative_patterns": agent.negative_patterns,
            "system_prompt": agent.system_prompt,
            "analysis_prompt": agent.analysis_prompt,
            "output_fields": agent.output_fields,
            "brand_id": agent.brand_id,
            "client_id": agent.client_id,
        }
        
        # Save to store
        store = await get_agent_store()
        agent_id = await store.save_agent(agent_config)
        
        # Also register in memory
        registry = get_agent_registry()
        from .agent_framework import AgentConfig, AgentType
        registry.register(AgentConfig(
            id=agent_id,
            name=agent.name,
            agent_type=AgentType.CUSTOM,
            description=agent.description,
            focus_areas=agent.focus_areas,
            positive_patterns=agent.positive_patterns,
            negative_patterns=agent.negative_patterns,
            system_prompt=agent.system_prompt,
            brand_id=agent.brand_id,
            client_id=agent.client_id,
        ))
        
        return {
            "success": True,
            "message": f"Agent '{agent.name}' created",
            "agent_id": agent_id
        }
        
    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{agent_id}")
async def update_agent(agent_id: str, updates: AgentUpdate):
    """Update an existing agent"""
    try:
        from .agent_store import get_agent_store
        
        store = await get_agent_store()
        existing = await store.get_agent(agent_id)
        
        if not existing:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
        # Apply updates
        update_dict = updates.dict(exclude_none=True)
        for key, value in update_dict.items():
            existing[key] = value
        
        # Save
        await store.save_agent(existing)
        
        return {
            "success": True,
            "message": f"Agent '{agent_id}' updated"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete an agent"""
    try:
        from .agent_store import get_agent_store
        
        store = await get_agent_store()
        success = await store.delete_agent(agent_id)
        
        if success:
            return {"success": True, "message": f"Agent '{agent_id}' deleted"}
        else:
            raise HTTPException(status_code=404, detail=f"Agent not found: {agent_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete agent: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_text(request: AnalyzeRequest):
    """Run agent analysis on text"""
    try:
        from .llm_agent_runner import get_llm_agent_runner
        from .agent_store import get_agent_store
        from . import get_agent_registry
        
        runner = await get_llm_agent_runner()
        registry = get_agent_registry()
        store = await get_agent_store()
        
        # Get agents to run
        agents = []
        for agent_id in request.agent_ids:
            # Try registry
            agent = registry.get(agent_id)
            if agent:
                agents.append(agent.to_dict())
            else:
                # Try store
                agent = await store.get_agent(agent_id)
                if agent:
                    agents.append(agent)
        
        if not agents:
            raise HTTPException(status_code=400, detail="No valid agents specified")
        
        # Run analysis
        results = await runner.run_multi_agent(agents, request.text, request.context)
        
        # Combine results
        combined = runner.combine_results(results)
        
        # Format for response
        agent_results = []
        for agent_id, result in results.items():
            agent_results.append({
                "agent_id": result.agent_id,
                "agent_name": result.agent_name,
                "summary": result.summary,
                "insights": result.insights,
                "positive_signals": result.positive_matches,
                "concerns": result.negative_matches,
                "recommendations": result.recommendations,
                "confidence": result.confidence,
                "processing_time": result.processing_time,
            })
        
        return {
            "success": True,
            "analysis": {
                "agents_run": len(agents),
                "results": agent_results,
                "combined": combined
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-analyze")
async def auto_analyze(request: AnalyzeRequest):
    """Auto-select relevant agents and run analysis"""
    try:
        from . import get_agent_runner, get_agent_registry
        from .llm_agent_runner import get_llm_agent_runner
        from .agent_store import get_agent_store
        
        # Auto-select agents based on content
        basic_runner = get_agent_runner()
        selected_ids = await basic_runner.auto_select_agents(request.text)
        
        # If brand specified, also include brand-specific agents
        if request.brand_id:
            store = await get_agent_store()
            brand_agents = await store.get_agents_for_brand(request.brand_id)
            for agent in brand_agents:
                if agent["id"] not in selected_ids:
                    selected_ids.append(agent["id"])
        
        # Get full agent configs
        registry = get_agent_registry()
        store = await get_agent_store()
        agents = []
        
        for agent_id in selected_ids:
            agent = registry.get(agent_id)
            if agent:
                agents.append(agent.to_dict())
            else:
                agent = await store.get_agent(agent_id)
                if agent:
                    agents.append(agent)
        
        # Run LLM analysis
        llm_runner = await get_llm_agent_runner()
        results = await llm_runner.run_multi_agent(agents, request.text, request.context)
        combined = llm_runner.combine_results(results)
        
        return {
            "success": True,
            "auto_selected_agents": selected_ids,
            "analysis": {
                "agents_run": len(agents),
                "combined_insights": combined["all_insights"],
                "combined_recommendations": combined["all_recommendations"],
                "concerns": combined["all_concerns"],
                "summaries": combined["summaries"],
                "processing_time": combined["total_processing_time"]
            }
        }
        
    except Exception as e:
        logger.error(f"Auto-analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clone/{source_agent_id}")
async def clone_agent(
    source_agent_id: str,
    brand_id: str,
    customizations: dict = Body(default={})
):
    """Clone an agent and customize for a brand"""
    try:
        from .agent_store import get_agent_store
        
        store = await get_agent_store()
        new_id = await store.clone_agent_for_brand(
            source_agent_id,
            brand_id,
            customizations
        )
        
        return {
            "success": True,
            "message": f"Agent cloned for brand {brand_id}",
            "new_agent_id": new_id
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Clone failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

