"""
Database Manager for PostgreSQL and Qdrant Vector Database
"""

import asyncio
import logging
import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
from qdrant_client import QdrantClient
from qdrant_client.http import models
from ..audio.processor import AudioProcessingResult
from ..llm.analyzer import AnalysisResult

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL and Qdrant connections"""
    
    def __init__(self):
        # PostgreSQL configuration
        self.pg_host = os.getenv("POSTGRES_HOST", "localhost")
        self.pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.pg_database = os.getenv("POSTGRES_DB", "voice_insight")
        self.pg_user = os.getenv("POSTGRES_USER", "postgres")
        self.pg_password = os.getenv("POSTGRES_PASSWORD", "password")
        
        # Qdrant configuration
        self.qdrant_host = os.getenv("QDRANT_HOST", "localhost")
        self.qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
        self.qdrant_collection = "voice_embeddings"
        
        self.pg_pool = None
        self.qdrant_client = None
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize database connections"""
        try:
            logger.info("Initializing database connections...")
            
            # Initialize PostgreSQL
            await self._init_postgresql()
            
            # Initialize Qdrant
            await self._init_qdrant()
            
            self.is_initialized = True
            logger.info("Database connections initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize databases: {e}")
            return False
    
    async def _init_postgresql(self):
        """Initialize PostgreSQL connection pool"""
        try:
            # Create connection pool
            self.pg_pool = await asyncpg.create_pool(
                host=self.pg_host,
                port=self.pg_port,
                database=self.pg_database,
                user=self.pg_user,
                password=self.pg_password,
                min_size=2,
                max_size=10
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            
            logger.info("PostgreSQL connection established")
            
        except Exception as e:
            logger.error(f"PostgreSQL initialization error: {e}")
            raise
    
    async def _init_qdrant(self):
        """Initialize Qdrant vector database"""
        try:
            # Create Qdrant client
            self.qdrant_client = QdrantClient(
                host=self.qdrant_host,
                port=self.qdrant_port
            )
            
            # Create collection if it doesn't exist
            collections = self.qdrant_client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.qdrant_collection not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=self.qdrant_collection,
                    vectors_config=models.VectorParams(
                        size=384,  # Sentence transformer embedding size
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.qdrant_collection}")
            
            logger.info("Qdrant connection established")
            
        except Exception as e:
            logger.warning(f"Qdrant initialization error: {e}")
            logger.warning("Continuing without vector search capabilities")
            self.qdrant_client = None
    
    async def _create_tables(self):
        """Create database tables"""
        async with self.pg_pool.acquire() as conn:
            # Users table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    username VARCHAR(255) UNIQUE NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id),
                    transcript TEXT NOT NULL,
                    audio_duration FLOAT NOT NULL,
                    speaker_count INTEGER DEFAULT 1,
                    confidence FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Speaker segments table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS speaker_segments (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
                    speaker_id VARCHAR(50) NOT NULL,
                    start_time FLOAT NOT NULL,
                    end_time FLOAT NOT NULL,
                    text TEXT NOT NULL,
                    confidence FLOAT DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Analysis results table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
                    is_accurate BOOLEAN DEFAULT TRUE,
                    fact_check_confidence FLOAT DEFAULT 0.0,
                    issues JSONB DEFAULT '[]',
                    corrections JSONB DEFAULT '[]',
                    sources JSONB DEFAULT '[]',
                    feedback_summary TEXT,
                    suggestions JSONB DEFAULT '[]',
                    accuracy_score FLOAT DEFAULT 0.0,
                    process_alignment FLOAT DEFAULT 0.0,
                    key_points JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_speaker_segments_session_id ON speaker_segments(session_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_analysis_results_session_id ON analysis_results(session_id)")
    
    async def store_session(self, audio_result: AudioProcessingResult, analysis: AnalysisResult) -> str:
        """Store complete session data"""
        if not self.is_initialized:
            raise RuntimeError("Database not initialized")
        
        session_id = str(uuid.uuid4())
        
        async with self.pg_pool.acquire() as conn:
            async with conn.transaction():
                # Insert session
                await conn.execute("""
                    INSERT INTO sessions (id, transcript, audio_duration, speaker_count, confidence)
                    VALUES ($1, $2, $3, $4, $5)
                """, session_id, audio_result.transcript, audio_result.audio_duration, 
                len(audio_result.speakers), audio_result.confidence)
                
                # Insert speaker segments
                for speaker in audio_result.speakers:
                    await conn.execute("""
                        INSERT INTO speaker_segments (session_id, speaker_id, start_time, end_time, text, confidence)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, session_id, speaker.speaker_id, speaker.start_time, 
                    speaker.end_time, speaker.text, speaker.confidence)
                
                # Insert analysis results
                await conn.execute("""
                    INSERT INTO analysis_results (
                        session_id, is_accurate, fact_check_confidence, issues, corrections, sources,
                        feedback_summary, suggestions, accuracy_score, process_alignment, key_points
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """, session_id, analysis.fact_check.is_accurate, analysis.fact_check.confidence,
                analysis.fact_check.issues, analysis.fact_check.corrections, analysis.fact_check.sources,
                analysis.feedback.summary, analysis.feedback.suggestions, analysis.feedback.accuracy_score,
                analysis.feedback.process_alignment, analysis.feedback.key_points)
        
        # Store embeddings in Qdrant if available
        if self.qdrant_client:
            await self._store_embeddings(session_id, audio_result.transcript)
        
        logger.info(f"Session stored with ID: {session_id}")
        return session_id
    
    async def _store_embeddings(self, session_id: str, transcript: str):
        """Store text embeddings in Qdrant"""
        try:
            # This is a placeholder - you'd use a proper embedding model here
            # For now, create a dummy embedding
            embedding = [0.1] * 384  # Placeholder embedding
            
            self.qdrant_client.upsert(
                collection_name=self.qdrant_collection,
                points=[
                    models.PointStruct(
                        id=session_id,
                        vector=embedding,
                        payload={
                            "session_id": session_id,
                            "transcript": transcript,
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                ]
            )
            
        except Exception as e:
            logger.error(f"Error storing embeddings: {e}")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        if not self.is_initialized:
            return None
        
        async with self.pg_pool.acquire() as conn:
            # Get session data
            session = await conn.fetchrow("""
                SELECT s.*, ar.is_accurate, ar.fact_check_confidence, ar.issues, ar.corrections,
                       ar.sources, ar.feedback_summary, ar.suggestions, ar.accuracy_score,
                       ar.process_alignment, ar.key_points
                FROM sessions s
                LEFT JOIN analysis_results ar ON s.id = ar.session_id
                WHERE s.id = $1
            """, session_id)
            
            if not session:
                return None
            
            # Get speaker segments
            speakers = await conn.fetch("""
                SELECT speaker_id, start_time, end_time, text, confidence
                FROM speaker_segments
                WHERE session_id = $1
                ORDER BY start_time
            """, session_id)
            
            return {
                "id": str(session["id"]),
                "transcript": session["transcript"],
                "audio_duration": session["audio_duration"],
                "speaker_count": session["speaker_count"],
                "confidence": session["confidence"],
                "created_at": session["created_at"].isoformat(),
                "speakers": [dict(speaker) for speaker in speakers],
                "analysis": {
                    "is_accurate": session["is_accurate"],
                    "fact_check_confidence": session["fact_check_confidence"],
                    "issues": session["issues"] or [],
                    "corrections": session["corrections"] or [],
                    "sources": session["sources"] or [],
                    "feedback_summary": session["feedback_summary"],
                    "suggestions": session["suggestions"] or [],
                    "accuracy_score": session["accuracy_score"],
                    "process_alignment": session["process_alignment"],
                    "key_points": session["key_points"] or []
                }
            }
    
    async def list_sessions(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """List recent sessions"""
        if not self.is_initialized:
            return []
        
        async with self.pg_pool.acquire() as conn:
            sessions = await conn.fetch("""
                SELECT id, transcript, audio_duration, speaker_count, confidence, created_at
                FROM sessions
                ORDER BY created_at DESC
                LIMIT $1 OFFSET $2
            """, limit, offset)
            
            return [
                {
                    "id": str(session["id"]),
                    "transcript": session["transcript"][:200] + "..." if len(session["transcript"]) > 200 else session["transcript"],
                    "audio_duration": session["audio_duration"],
                    "speaker_count": session["speaker_count"],
                    "confidence": session["confidence"],
                    "created_at": session["created_at"].isoformat()
                }
                for session in sessions
            ]
    
    def is_connected(self) -> bool:
        """Check if database is connected"""
        return self.is_initialized and self.pg_pool is not None
    
    async def cleanup(self):
        """Cleanup database connections"""
        logger.info("Cleaning up database connections...")
        
        if self.pg_pool:
            await self.pg_pool.close()
            self.pg_pool = None
        
        if self.qdrant_client:
            self.qdrant_client.close()
            self.qdrant_client = None
        
        self.is_initialized = False
