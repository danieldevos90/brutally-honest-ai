"""
Vector Database Integration for Document Storage and Retrieval
Uses Qdrant for vector storage and similarity search
"""

import asyncio
import logging
import json
import os
import numpy as np
import re
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
    
    def __init__(self, collection_name: str = "documents", data_dir: str = None):
        self.collection_name = collection_name
        self.is_initialized = False
        self.client = None
        self.embedding_model = None
        self.documents = {}  # Track uploaded documents: {doc_id: doc_info}
        # Prevent concurrent writers corrupting local JSON registry/chunk files.
        self._local_write_lock = asyncio.Lock()
        
        # Set up persistent storage directory
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        self.data_dir = data_dir
        self.qdrant_path = os.path.join(data_dir, 'qdrant_storage')
        self.documents_file = os.path.join(data_dir, 'documents_registry.json')
        self.local_chunks_dir = os.path.join(data_dir, 'documents_chunks')
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.qdrant_path, exist_ok=True)
        os.makedirs(self.local_chunks_dir, exist_ok=True)
        
        # Load existing document registry
        self._load_documents_registry()
        
        # Check available libraries
        self.qdrant_available = self._check_qdrant()
        self.embedding_available = self._check_embeddings()

        # Allow forcing a mode via env var. This is useful on constrained devices (Jetson)
        # where the embedded Qdrant+embeddings path can be slow or unstable under concurrency.
        forced_mode = (os.environ.get("BH_VECTOR_STORE_MODE") or os.environ.get("VECTOR_STORE_MODE") or "").strip().lower()
        if forced_mode in ("local", "qdrant"):
            self.mode = forced_mode
            logger.info(f"Vector store forced mode via env: {self.mode}")
        else:
            # If Qdrant/embeddings aren't available, fall back to a lightweight local store so
            # document upload and validation can still work (with naive keyword search).
            self.mode = "qdrant" if (self.qdrant_available and self.embedding_available) else "local"
    
    def _load_documents_registry(self):
        """Load document registry from disk"""
        try:
            if os.path.exists(self.documents_file):
                with open(self.documents_file, 'r') as f:
                    self.documents = json.load(f)
                logger.info(f"📂 Loaded {len(self.documents)} documents from registry")
        except Exception as e:
            logger.warning(f"Failed to load documents registry: {e}")
            self.documents = {}
    
    def _save_documents_registry(self):
        """Save document registry to disk"""
        try:
            tmp_path = f"{self.documents_file}.tmp"
            with open(tmp_path, "w") as f:
                # Avoid pretty-print here; this file can grow and we want it fast/atomic.
                json.dump(self.documents, f, default=str)
            os.replace(tmp_path, self.documents_file)
            logger.info(f"💾 Saved {len(self.documents)} documents to registry")
        except Exception as e:
            logger.error(f"Failed to save documents registry: {e}")
        
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
            logger.info("SentenceTransformers available")
            return True
        except ImportError as e:
            logger.warning(f"SentenceTransformers not available - install with: pip install sentence-transformers (ImportError: {e})")
            return False
        except Exception as e:
            logger.warning(f"SentenceTransformers check failed with {type(e).__name__}: {e}")
            return False
    
    async def initialize(self) -> bool:
        """Initialize the vector store"""
        try:
            if self.mode == "local":
                self.is_initialized = True
                logger.info("✅ Vector store initialized in LOCAL fallback mode")
                return True
            
            logger.info("🔧 Initializing vector store...")
            
            # Initialize Qdrant client (in-memory for now)
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            # Use persistent storage on disk
            self.client = QdrantClient(path=self.qdrant_path)
            logger.info(f"📂 Qdrant using persistent storage at: {self.qdrant_path}")
            
            # Initialize embedding model on CPU to save GPU memory for Whisper
            from sentence_transformers import SentenceTransformer
            logger.info("🧠 Loading embedding model (CPU to save GPU for Whisper)...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')  # Lightweight model on CPU
            
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

    def _local_chunks_path(self, document_id: str) -> str:
        return os.path.join(self.local_chunks_dir, f"{document_id}.json")

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", (text or "").lower())

    def _local_score(self, query: str, content: str) -> float:
        q = set(self._tokenize(query))
        if not q:
            return 0.0
        c = set(self._tokenize(content))
        overlap = len(q & c)
        return overlap / max(1, len(q))
    
    async def store_document(self, doc_info: DocumentInfo) -> bool:
        """Store a document in the vector database"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            logger.info(f"📚 Storing document: {doc_info.filename}")
            
            # Split document into chunks
            chunks = self._chunk_text(doc_info.content)
            logger.info(f"📄 Split into {len(chunks)} chunks")

            if self.mode == "local":
                local_chunks = []
                for i, chunk_text in enumerate(chunks):
                    # Avoid uuid4() here: on some embedded Linux setups it can be surprisingly slow
                    # (entropy / getrandom() behavior). Deterministic IDs are fine for local mode.
                    chunk_id = f"{doc_info.id}:chunk:{i}"
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
                        "related_documents": doc_info.related_documents if doc_info.related_documents else [],
                    }
                    local_chunks.append(
                        {
                            "chunk_id": chunk_id,
                            "content": chunk_text,
                            "metadata": chunk_metadata,
                        }
                    )

                async with self._local_write_lock:
                    # Persist chunk data (atomic write)
                    chunks_path = self._local_chunks_path(doc_info.id)
                    tmp_chunks_path = f"{chunks_path}.tmp"
                    with open(tmp_chunks_path, "w") as f:
                        json.dump(local_chunks, f)
                    os.replace(tmp_chunks_path, chunks_path)

                    # Track document in registry
                    self.documents[doc_info.id] = {
                        "id": doc_info.id,
                        "filename": doc_info.filename,
                        "file_type": doc_info.file_type,
                        "file_size": doc_info.file_size,
                        "text_length": len(doc_info.content),
                        "upload_time": doc_info.upload_time.isoformat(),
                        "tags": doc_info.tags if doc_info.tags else [],
                        "category": doc_info.category,
                        "chunk_count": len(local_chunks),
                    }
                    self._save_documents_registry()

                logger.info(f"✅ Stored {len(local_chunks)} chunks for document (local): {doc_info.filename}")
                return True
            
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
            
            # Track document in registry
            self.documents[doc_info.id] = {
                "id": doc_info.id,
                "filename": doc_info.filename,
                "file_type": doc_info.file_type,
                "file_size": doc_info.file_size,
                "text_length": len(doc_info.content),
                "upload_time": doc_info.upload_time.isoformat(),
                "tags": doc_info.tags if doc_info.tags else [],
                "category": doc_info.category,
                "chunk_count": len(points)
            }
            
            # Save registry to disk for persistence
            self._save_documents_registry()
            
            logger.info(f"✅ Stored {len(points)} chunks for document: {doc_info.filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store document {doc_info.filename}: {e}")
            return False
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all stored documents"""
        return list(self.documents.values())
    
    async def search_documents(self, query: str, limit: int = 5, score_threshold: float = 0.3) -> List[SearchResult]:
        """Search for relevant document chunks"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            logger.info(f"🔍 Searching for: {query}")

            if self.mode == "local":
                results: List[SearchResult] = []
                for doc_id, doc_meta in self.documents.items():
                    chunks_path = self._local_chunks_path(doc_id)
                    if not os.path.exists(chunks_path):
                        continue
                    try:
                        with open(chunks_path, "r") as f:
                            chunks = json.load(f)
                    except Exception:
                        continue
                    for ch in chunks:
                        score = self._local_score(query, ch.get("content", ""))
                        if score < score_threshold:
                            continue
                        md = ch.get("metadata") or {}
                        results.append(
                            SearchResult(
                                document_id=md.get("document_id", doc_id),
                                chunk_id=ch.get("chunk_id", ""),
                                content=ch.get("content", ""),
                                score=float(score),
                                metadata=md,
                            )
                        )

                results.sort(key=lambda r: r.score, reverse=True)
                return results[:limit]
            
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
            if self.mode == "local":
                chunks_path = self._local_chunks_path(document_id)
                if not os.path.exists(chunks_path):
                    return []
                with open(chunks_path, "r") as f:
                    chunks = json.load(f)
                results = [
                    SearchResult(
                        document_id=document_id,
                        chunk_id=ch.get("chunk_id", ""),
                        content=ch.get("content", ""),
                        score=1.0,
                        metadata=ch.get("metadata") or {},
                    )
                    for ch in chunks
                ]
                results.sort(key=lambda x: x.metadata.get("chunk_index", 0))
                return results

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
            if self.mode == "local":
                try:
                    chunks_path = self._local_chunks_path(document_id)
                    if os.path.exists(chunks_path):
                        os.remove(chunks_path)
                except Exception:
                    pass

                if document_id in self.documents:
                    del self.documents[document_id]
                    self._save_documents_registry()
                return True

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
            
            # Remove from registry
            if document_id in self.documents:
                del self.documents[document_id]
                self._save_documents_registry()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            return False
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the document collection"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            if self.mode == "local":
                total_chunks = sum(int(d.get("chunk_count", 0) or 0) for d in self.documents.values())
                return {
                    "total_chunks": total_chunks,
                    "vector_size": None,
                    "distance_metric": None,
                    "collection_name": self.collection_name,
                    "mode": "local",
                }

            collection_info = self.client.get_collection(self.collection_name)
            
            return {
                "total_chunks": collection_info.points_count,
                "vector_size": collection_info.config.params.vectors.size,
                "distance_metric": collection_info.config.params.vectors.distance.name,
                "collection_name": self.collection_name,
                "mode": "qdrant",
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
