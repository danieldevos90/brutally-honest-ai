"""
Vector Database Integration for Document Storage and Retrieval
Uses Qdrant for vector storage and similarity search
"""

import asyncio
import logging
import json
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import uuid

from .processor import DocumentInfo

logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """A chunk of text from a document with vector embedding"""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    start_pos: int
    end_pos: int
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = None

@dataclass
class SearchResult:
    """Result from vector search"""
    document_id: str
    chunk_id: str
    content: str
    score: float
    metadata: Dict[str, Any]

class VectorStore:
    """Vector database for document storage and retrieval"""
    
    def __init__(self, collection_name: str = "documents"):
        self.collection_name = collection_name
        self.is_initialized = False
        self.client = None
        self.embedding_model = None
        
        # Check available libraries
        self.qdrant_available = self._check_qdrant()
        self.embedding_available = self._check_embeddings()
        
    def _check_qdrant(self) -> bool:
        """Check if Qdrant is available"""
        try:
            from qdrant_client import QdrantClient
            return True
        except ImportError:
            logger.warning("Qdrant not available - install with: pip install qdrant-client")
            return False
    
    def _check_embeddings(self) -> bool:
        """Check if embedding models are available"""
        try:
            from sentence_transformers import SentenceTransformer
            return True
        except ImportError:
            logger.warning("SentenceTransformers not available - install with: pip install sentence-transformers")
            return False
    
    async def initialize(self) -> bool:
        """Initialize the vector store"""
        try:
            if not self.qdrant_available:
                logger.error("Qdrant client not available")
                return False
            
            if not self.embedding_available:
                logger.error("Embedding models not available")
                return False
            
            logger.info("🔧 Initializing vector store...")
            
            # Initialize Qdrant client (in-memory for now)
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            self.client = QdrantClient(":memory:")  # Use in-memory storage for simplicity
            
            # Initialize embedding model
            from sentence_transformers import SentenceTransformer
            logger.info("🧠 Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight model
            
            # Create collection if it doesn't exist
            try:
                collection_info = self.client.get_collection(self.collection_name)
                logger.info(f"📚 Using existing collection: {self.collection_name}")
            except:
                # Create new collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=384,  # all-MiniLM-L6-v2 embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"📚 Created new collection: {self.collection_name}")
            
            self.is_initialized = True
            logger.info("✅ Vector store initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            return False
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                search_start = max(start + chunk_size - 100, start)
                sentence_end = -1
                
                for i in range(end, search_start, -1):
                    if text[i] in '.!?':
                        sentence_end = i + 1
                        break
                
                if sentence_end > start:
                    end = sentence_end
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position with overlap
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")
        
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    async def store_document(self, doc_info: DocumentInfo) -> bool:
        """Store a document in the vector database"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            logger.info(f"📚 Storing document: {doc_info.filename}")
            
            # Split document into chunks
            chunks = self._chunk_text(doc_info.content)
            logger.info(f"📄 Split into {len(chunks)} chunks")
            
            # Process each chunk
            points = []
            for i, chunk_text in enumerate(chunks):
                # Generate chunk ID as a proper UUID
                chunk_id = str(uuid.uuid4())
                
                # Generate embedding
                embedding = self._generate_embedding(chunk_text)
                
                # Create chunk metadata
                chunk_metadata = {
                    "document_id": doc_info.id,
                    "chunk_index": i,
                    "filename": doc_info.filename,
                    "file_type": doc_info.file_type,
                    "upload_time": doc_info.upload_time.isoformat(),
                    "content_preview": chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text,
                    "chunk_length": len(chunk_text),
                    "tags": doc_info.tags if doc_info.tags else [],
                    "context": doc_info.context,
                    "category": doc_info.category,
                    "related_documents": doc_info.related_documents if doc_info.related_documents else []
                }
                
                # Create point for Qdrant
                from qdrant_client.models import PointStruct
                point = PointStruct(
                    id=chunk_id,
                    vector=embedding,
                    payload={
                        "content": chunk_text,
                        "metadata": chunk_metadata
                    }
                )
                points.append(point)
            
            # Store in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"✅ Stored {len(points)} chunks for document: {doc_info.filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document {doc_info.filename}: {e}")
            return False
    
    async def search_documents(self, query: str, limit: int = 5, score_threshold: float = 0.7) -> List[SearchResult]:
        """Search for relevant document chunks"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            logger.info(f"🔍 Searching for: {query}")
            
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Search in Qdrant
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                score_threshold=score_threshold
            )
            
            # Convert to SearchResult objects
            results = []
            for result in search_results:
                search_result = SearchResult(
                    document_id=result.payload["metadata"]["document_id"],
                    chunk_id=result.id,
                    content=result.payload["content"],
                    score=result.score,
                    metadata=result.payload["metadata"]
                )
                results.append(search_result)
            
            logger.info(f"🎯 Found {len(results)} relevant chunks")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def get_document_chunks(self, document_id: str) -> List[SearchResult]:
        """Get all chunks for a specific document"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Search with filter for specific document
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="metadata.document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
            
            search_results = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_condition,
                limit=100
            )
            
            # Convert to SearchResult objects
            results = []
            for result in search_results[0]:  # scroll returns (points, next_page_offset)
                search_result = SearchResult(
                    document_id=result.payload["metadata"]["document_id"],
                    chunk_id=result.id,
                    content=result.payload["content"],
                    score=1.0,  # No scoring for direct retrieval
                    metadata=result.payload["metadata"]
                )
                results.append(search_result)
            
            # Sort by chunk index
            results.sort(key=lambda x: x.metadata.get("chunk_index", 0))
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to get document chunks: {e}")
            return []
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete all chunks for a document"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Get all chunk IDs for the document
            chunks = await self.get_document_chunks(document_id)
            chunk_ids = [chunk.chunk_id for chunk in chunks]
            
            if chunk_ids:
                # Delete from Qdrant
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=chunk_ids
                )
                
                logger.info(f"🗑️ Deleted {len(chunk_ids)} chunks for document: {document_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "total_chunks": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.name,
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

# Global vector store instance
_vector_store = None

async def get_vector_store() -> VectorStore:
    """Get or create the global vector store"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
        await _vector_store.initialize()
    return _vector_store
