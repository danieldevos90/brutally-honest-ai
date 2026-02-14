"""
Agent Store - Persists agents in vector database for brand/client specific configurations

Stores:
- Agent configurations (patterns, prompts, rules)
- Brand-specific agents
- Client-specific agents
- Agent embeddings for similarity search
"""

import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import asdict

logger = logging.getLogger(__name__)


class AgentStore:
    """
    Stores and retrieves agents from Qdrant vector database.
    
    Each agent is stored with:
    - Configuration (patterns, prompts, etc.)
    - Embedding of its description for similarity search
    - Brand/client association
    """
    
    COLLECTION_NAME = "agents"
    
    def __init__(self, qdrant_client=None, embedding_model=None):
        self.client = qdrant_client
        self.embedding_model = embedding_model
        self.initialized = False
        logger.info("AgentStore created")
    
    async def initialize(self) -> bool:
        """Initialize connection to Qdrant and ensure collection exists"""
        try:
            # Import here to avoid circular imports
            if self.client is None:
                from qdrant_client import QdrantClient
                self.client = QdrantClient(host="localhost", port=6333)
            
            if self.embedding_model is None:
                from sentence_transformers import SentenceTransformer
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')  # CPU to save GPU for Whisper
            
            # Create collection if not exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self.COLLECTION_NAME not in collection_names:
                from qdrant_client.models import Distance, VectorParams
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created collection: {self.COLLECTION_NAME}")
            
            self.initialized = True
            logger.info("AgentStore initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AgentStore: {e}")
            return False
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        return self.embedding_model.encode(text).tolist()
    
    async def save_agent(self, agent_config: Dict[str, Any]) -> str:
        """
        Save an agent configuration to the vector DB.
        
        Args:
            agent_config: Agent configuration dict (from AgentConfig.to_dict())
            
        Returns:
            Agent ID
        """
        if not self.initialized:
            await self.initialize()
        
        agent_id = agent_config.get("id") or f"agent_{uuid.uuid4().hex[:12]}"
        
        # Create embedding from agent description + focus areas
        embed_text = f"{agent_config.get('name', '')} {agent_config.get('description', '')} {' '.join(agent_config.get('focus_areas', []))}"
        embedding = self._get_embedding(embed_text)
        
        # Store in Qdrant
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[{
                "id": hash(agent_id) % (10**12),  # Qdrant needs numeric ID
                "vector": embedding,
                "payload": {
                    "agent_id": agent_id,
                    "config": json.dumps(agent_config),
                    "brand_id": agent_config.get("brand_id"),
                    "client_id": agent_config.get("client_id"),
                    "agent_type": agent_config.get("agent_type"),
                    "name": agent_config.get("name"),
                    "created_at": datetime.now().isoformat(),
                }
            }]
        )
        
        logger.info(f"Saved agent: {agent_id}")
        return agent_id
    
    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID"""
        if not self.initialized:
            await self.initialize()
        
        # Search by agent_id in payload
        results = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            scroll_filter={
                "must": [{"key": "agent_id", "match": {"value": agent_id}}]
            },
            limit=1
        )
        
        if results[0]:
            payload = results[0][0].payload
            return json.loads(payload.get("config", "{}"))
        
        return None
    
    async def list_agents(
        self,
        brand_id: str = None,
        client_id: str = None,
        agent_type: str = None
    ) -> List[Dict[str, Any]]:
        """List agents with optional filters"""
        if not self.initialized:
            await self.initialize()
        
        # Build filter
        must_conditions = []
        if brand_id:
            must_conditions.append({"key": "brand_id", "match": {"value": brand_id}})
        if client_id:
            must_conditions.append({"key": "client_id", "match": {"value": client_id}})
        if agent_type:
            must_conditions.append({"key": "agent_type", "match": {"value": agent_type}})
        
        scroll_filter = {"must": must_conditions} if must_conditions else None
        
        results = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            scroll_filter=scroll_filter,
            limit=100
        )
        
        agents = []
        for point in results[0]:
            config = json.loads(point.payload.get("config", "{}"))
            agents.append(config)
        
        return agents
    
    async def find_similar_agents(
        self,
        query: str,
        limit: int = 5,
        brand_id: str = None
    ) -> List[Dict[str, Any]]:
        """Find agents similar to a query (useful for auto-selection)"""
        if not self.initialized:
            await self.initialize()
        
        query_embedding = self._get_embedding(query)
        
        # Build filter
        search_filter = None
        if brand_id:
            search_filter = {"must": [{"key": "brand_id", "match": {"value": brand_id}}]}
        
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=search_filter,
            limit=limit
        )
        
        agents = []
        for point in results:
            config = json.loads(point.payload.get("config", "{}"))
            config["_similarity_score"] = point.score
            agents.append(config)
        
        return agents
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Find point ID
            results = self.client.scroll(
                collection_name=self.COLLECTION_NAME,
                scroll_filter={
                    "must": [{"key": "agent_id", "match": {"value": agent_id}}]
                },
                limit=1
            )
            
            if results[0]:
                point_id = results[0][0].id
                self.client.delete(
                    collection_name=self.COLLECTION_NAME,
                    points_selector={"points": [point_id]}
                )
                logger.info(f"Deleted agent: {agent_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            return False
    
    async def get_agents_for_brand(self, brand_id: str) -> List[Dict[str, Any]]:
        """Get all agents configured for a specific brand"""
        return await self.list_agents(brand_id=brand_id)
    
    async def clone_agent_for_brand(
        self,
        source_agent_id: str,
        brand_id: str,
        customizations: Dict[str, Any] = None
    ) -> str:
        """Clone an existing agent and customize for a brand"""
        source = await self.get_agent(source_agent_id)
        if not source:
            raise ValueError(f"Source agent not found: {source_agent_id}")
        
        # Create new agent
        new_agent = source.copy()
        new_agent["id"] = f"agent_{brand_id}_{uuid.uuid4().hex[:8]}"
        new_agent["brand_id"] = brand_id
        new_agent["name"] = f"{source['name']} ({brand_id})"
        
        # Apply customizations
        if customizations:
            for key, value in customizations.items():
                if key in new_agent:
                    if isinstance(new_agent[key], list):
                        new_agent[key].extend(value)
                    else:
                        new_agent[key] = value
        
        return await self.save_agent(new_agent)


# Singleton
_agent_store: Optional[AgentStore] = None


async def get_agent_store() -> AgentStore:
    """Get singleton AgentStore"""
    global _agent_store
    if _agent_store is None:
        _agent_store = AgentStore()
        await _agent_store.initialize()
    return _agent_store

