"""
Unified Data Store - Persistent Vector Database with User/Brand/Client Settings
Uses Qdrant for vector storage with persistent data on disk
"""

import asyncio
import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

# Data directory for persistent storage
DATA_DIR = Path(os.getenv("DATA_DIR", "/home/brutally/brutally-honest-ai/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class UserSettings:
    """User-specific settings"""
    id: str
    email: str
    name: str
    role: str = "user"
    preferences: Dict[str, Any] = field(default_factory=dict)
    default_brand_id: Optional[str] = None
    notification_settings: Dict[str, bool] = field(default_factory=lambda: {
        "email_notifications": True,
        "transcription_complete": True,
        "validation_alerts": True
    })
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class BrandSettings:
    """Brand-specific settings and configuration"""
    id: str
    name: str
    description: str = ""
    owner_id: str = ""  # User who created the brand
    
    # Brand voice settings
    tone: str = "professional"  # professional, casual, formal, friendly
    language: str = "en"
    
    # Validation settings
    fact_check_enabled: bool = True
    document_validation_enabled: bool = True
    strict_mode: bool = False
    
    # Custom prompts
    custom_system_prompt: Optional[str] = None
    brutal_honesty_level: int = 5  # 1-10 scale
    
    # Associated data
    client_ids: List[str] = field(default_factory=list)
    document_ids: List[str] = field(default_factory=list)
    profile_ids: List[str] = field(default_factory=list)
    
    # Keywords and topics for this brand
    keywords: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass 
class ClientSettings:
    """Client (customer) specific settings"""
    id: str
    name: str
    brand_id: str  # Associated brand
    type: str = "business"  # business, individual, agency
    description: str = ""
    
    # Contact info
    contact_email: Optional[str] = None
    contact_name: Optional[str] = None
    
    # Client-specific settings
    preferred_tone: Optional[str] = None  # Override brand tone
    special_instructions: Optional[str] = None
    
    # Associated data
    profile_ids: List[str] = field(default_factory=list)
    document_ids: List[str] = field(default_factory=list)
    recording_ids: List[str] = field(default_factory=list)
    
    # Tags and metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class ProfileSettings:
    """Person profile settings"""
    id: str
    name: str
    client_id: Optional[str] = None  # Associated client
    brand_id: Optional[str] = None   # Associated brand
    
    role: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    
    # Voice profile
    voice_characteristics: Dict[str, Any] = field(default_factory=dict)
    speaking_style: Optional[str] = None
    
    # Credibility tracking
    credibility_score: float = 1.0
    total_transcriptions: int = 0
    verified_statements: int = 0
    
    # Associated recordings
    recording_ids: List[str] = field(default_factory=list)
    
    # Tags and metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class RecordingEntry:
    """Recording metadata"""
    id: str
    filename: str
    file_path: str
    
    user_id: Optional[str] = None
    brand_id: Optional[str] = None
    client_id: Optional[str] = None
    profile_id: Optional[str] = None
    
    # Recording info
    duration: Optional[float] = None
    size: int = 0
    format: str = "webm"
    source: str = "browser"  # browser, device, upload
    
    # Transcription results
    transcription: Optional[str] = None
    transcription_status: str = "pending"  # pending, processing, completed, failed
    sentiment: Optional[str] = None
    confidence: Optional[float] = None
    keywords: List[str] = field(default_factory=list)
    
    # Validation results
    validation_status: Optional[str] = None
    validation_score: Optional[float] = None
    claims_found: int = 0
    claims_verified: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


class DataStore:
    """Unified data store for all application data"""
    
    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        self.users_dir = self.data_dir / "users"
        self.brands_dir = self.data_dir / "brands"
        self.clients_dir = self.data_dir / "clients"
        self.profiles_dir = self.data_dir / "profiles"
        self.recordings_dir = self.data_dir / "recordings"
        
        for d in [self.users_dir, self.brands_dir, self.clients_dir, 
                  self.profiles_dir, self.recordings_dir]:
            d.mkdir(exist_ok=True)
        
        # Vector store reference
        self.vector_store = None
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the data store"""
        try:
            logger.info("Initializing data store...")
            
            # Initialize vector store for semantic search
            from documents.vector_store import get_vector_store
            self.vector_store = await get_vector_store()
            
            self.is_initialized = True
            logger.info("Data store initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize data store: {e}")
            # Continue without vector store
            self.is_initialized = True
            return True
    
    # ============================================================================
    # USER METHODS
    # ============================================================================
    
    async def create_user(self, email: str, name: str, role: str = "user") -> UserSettings:
        """Create a new user"""
        user = UserSettings(
            id=str(uuid.uuid4()),
            email=email,
            name=name,
            role=role
        )
        await self._save_json(self.users_dir / f"{user.id}.json", user.to_dict())
        logger.info(f"Created user: {name} ({user.id})")
        return user
    
    async def get_user(self, user_id: str) -> Optional[UserSettings]:
        """Get user by ID"""
        data = await self._load_json(self.users_dir / f"{user_id}.json")
        if data:
            return UserSettings(**data)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserSettings]:
        """Get user by email"""
        for f in self.users_dir.glob("*.json"):
            data = await self._load_json(f)
            if data and data.get("email") == email:
                return UserSettings(**data)
        return None
    
    async def update_user(self, user_id: str, **kwargs) -> Optional[UserSettings]:
        """Update user settings"""
        user = await self.get_user(user_id)
        if not user:
            return None
        
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.now().isoformat()
        await self._save_json(self.users_dir / f"{user.id}.json", user.to_dict())
        return user
    
    async def list_users(self) -> List[UserSettings]:
        """List all users"""
        users = []
        for f in self.users_dir.glob("*.json"):
            data = await self._load_json(f)
            if data:
                users.append(UserSettings(**data))
        return users
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        path = self.users_dir / f"{user_id}.json"
        if path.exists():
            path.unlink()
            logger.info(f"Deleted user: {user_id}")
            return True
        return False
    
    # ============================================================================
    # BRAND METHODS
    # ============================================================================
    
    async def create_brand(self, name: str, owner_id: str, **kwargs) -> BrandSettings:
        """Create a new brand"""
        brand = BrandSettings(
            id=str(uuid.uuid4()),
            name=name,
            owner_id=owner_id,
            **kwargs
        )
        await self._save_json(self.brands_dir / f"{brand.id}.json", brand.to_dict())
        logger.info(f"Created brand: {name} ({brand.id})")
        return brand
    
    async def get_brand(self, brand_id: str) -> Optional[BrandSettings]:
        """Get brand by ID"""
        data = await self._load_json(self.brands_dir / f"{brand_id}.json")
        if data:
            return BrandSettings(**data)
        return None
    
    async def update_brand(self, brand_id: str, **kwargs) -> Optional[BrandSettings]:
        """Update brand settings"""
        brand = await self.get_brand(brand_id)
        if not brand:
            return None
        
        for key, value in kwargs.items():
            if hasattr(brand, key):
                setattr(brand, key, value)
        
        brand.updated_at = datetime.now().isoformat()
        await self._save_json(self.brands_dir / f"{brand.id}.json", brand.to_dict())
        return brand
    
    async def list_brands(self, owner_id: Optional[str] = None) -> List[BrandSettings]:
        """List all brands, optionally filtered by owner"""
        brands = []
        for f in self.brands_dir.glob("*.json"):
            data = await self._load_json(f)
            if data:
                if owner_id is None or data.get("owner_id") == owner_id:
                    brands.append(BrandSettings(**data))
        return brands
    
    async def delete_brand(self, brand_id: str) -> bool:
        """Delete a brand"""
        path = self.brands_dir / f"{brand_id}.json"
        if path.exists():
            path.unlink()
            logger.info(f"Deleted brand: {brand_id}")
            return True
        return False
    
    # ============================================================================
    # CLIENT METHODS
    # ============================================================================
    
    async def create_client(self, name: str, brand_id: str, **kwargs) -> ClientSettings:
        """Create a new client"""
        client = ClientSettings(
            id=str(uuid.uuid4()),
            name=name,
            brand_id=brand_id,
            **kwargs
        )
        await self._save_json(self.clients_dir / f"{client.id}.json", client.to_dict())
        
        # Update brand's client list
        brand = await self.get_brand(brand_id)
        if brand and client.id not in brand.client_ids:
            brand.client_ids.append(client.id)
            await self.update_brand(brand_id, client_ids=brand.client_ids)
        
        logger.info(f"Created client: {name} ({client.id})")
        return client
    
    async def get_client(self, client_id: str) -> Optional[ClientSettings]:
        """Get client by ID"""
        data = await self._load_json(self.clients_dir / f"{client_id}.json")
        if data:
            return ClientSettings(**data)
        return None
    
    async def update_client(self, client_id: str, **kwargs) -> Optional[ClientSettings]:
        """Update client settings"""
        client = await self.get_client(client_id)
        if not client:
            return None
        
        for key, value in kwargs.items():
            if hasattr(client, key):
                setattr(client, key, value)
        
        client.updated_at = datetime.now().isoformat()
        await self._save_json(self.clients_dir / f"{client.id}.json", client.to_dict())
        return client
    
    async def list_clients(self, brand_id: Optional[str] = None) -> List[ClientSettings]:
        """List all clients, optionally filtered by brand"""
        clients = []
        for f in self.clients_dir.glob("*.json"):
            data = await self._load_json(f)
            if data:
                if brand_id is None or data.get("brand_id") == brand_id:
                    clients.append(ClientSettings(**data))
        return clients
    
    async def delete_client(self, client_id: str) -> bool:
        """Delete a client"""
        client = await self.get_client(client_id)
        if client:
            # Remove from brand's client list
            brand = await self.get_brand(client.brand_id)
            if brand and client_id in brand.client_ids:
                brand.client_ids.remove(client_id)
                await self.update_brand(client.brand_id, client_ids=brand.client_ids)
        
        path = self.clients_dir / f"{client_id}.json"
        if path.exists():
            path.unlink()
            logger.info(f"Deleted client: {client_id}")
            return True
        return False
    
    # ============================================================================
    # PROFILE METHODS
    # ============================================================================
    
    async def create_profile(self, name: str, **kwargs) -> ProfileSettings:
        """Create a new profile"""
        profile = ProfileSettings(
            id=str(uuid.uuid4()),
            name=name,
            **kwargs
        )
        await self._save_json(self.profiles_dir / f"{profile.id}.json", profile.to_dict())
        logger.info(f"Created profile: {name} ({profile.id})")
        return profile
    
    async def get_profile(self, profile_id: str) -> Optional[ProfileSettings]:
        """Get profile by ID"""
        data = await self._load_json(self.profiles_dir / f"{profile_id}.json")
        if data:
            return ProfileSettings(**data)
        return None
    
    async def update_profile(self, profile_id: str, **kwargs) -> Optional[ProfileSettings]:
        """Update profile settings"""
        profile = await self.get_profile(profile_id)
        if not profile:
            return None
        
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now().isoformat()
        await self._save_json(self.profiles_dir / f"{profile.id}.json", profile.to_dict())
        return profile
    
    async def list_profiles(self, client_id: Optional[str] = None, 
                           brand_id: Optional[str] = None) -> List[ProfileSettings]:
        """List all profiles, optionally filtered"""
        profiles = []
        for f in self.profiles_dir.glob("*.json"):
            data = await self._load_json(f)
            if data:
                if client_id and data.get("client_id") != client_id:
                    continue
                if brand_id and data.get("brand_id") != brand_id:
                    continue
                profiles.append(ProfileSettings(**data))
        return profiles
    
    async def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile"""
        path = self.profiles_dir / f"{profile_id}.json"
        if path.exists():
            path.unlink()
            logger.info(f"Deleted profile: {profile_id}")
            return True
        return False
    
    # ============================================================================
    # RECORDING METHODS
    # ============================================================================
    
    async def create_recording(self, filename: str, file_path: str, **kwargs) -> RecordingEntry:
        """Create a new recording entry"""
        recording = RecordingEntry(
            id=str(uuid.uuid4()),
            filename=filename,
            file_path=file_path,
            **kwargs
        )
        await self._save_json(self.recordings_dir / f"{recording.id}.json", recording.to_dict())
        logger.info(f"Created recording: {filename} ({recording.id})")
        return recording
    
    async def get_recording(self, recording_id: str) -> Optional[RecordingEntry]:
        """Get recording by ID"""
        data = await self._load_json(self.recordings_dir / f"{recording_id}.json")
        if data:
            return RecordingEntry(**data)
        return None
    
    async def update_recording(self, recording_id: str, **kwargs) -> Optional[RecordingEntry]:
        """Update recording entry"""
        recording = await self.get_recording(recording_id)
        if not recording:
            return None
        
        for key, value in kwargs.items():
            if hasattr(recording, key):
                setattr(recording, key, value)
        
        recording.updated_at = datetime.now().isoformat()
        await self._save_json(self.recordings_dir / f"{recording.id}.json", recording.to_dict())
        return recording
    
    async def list_recordings(self, user_id: Optional[str] = None,
                             brand_id: Optional[str] = None,
                             client_id: Optional[str] = None,
                             limit: int = 100) -> List[RecordingEntry]:
        """List recordings with optional filters"""
        recordings = []
        for f in sorted(self.recordings_dir.glob("*.json"), 
                       key=lambda x: x.stat().st_mtime, reverse=True):
            if len(recordings) >= limit:
                break
            data = await self._load_json(f)
            if data:
                if user_id and data.get("user_id") != user_id:
                    continue
                if brand_id and data.get("brand_id") != brand_id:
                    continue
                if client_id and data.get("client_id") != client_id:
                    continue
                recordings.append(RecordingEntry(**data))
        return recordings
    
    async def delete_recording(self, recording_id: str) -> bool:
        """Delete a recording entry"""
        path = self.recordings_dir / f"{recording_id}.json"
        if path.exists():
            path.unlink()
            logger.info(f"Deleted recording: {recording_id}")
            return True
        return False
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    async def _save_json(self, path: Path, data: Dict) -> bool:
        """Save data to JSON file"""
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Failed to save {path}: {e}")
            return False
    
    async def _load_json(self, path: Path) -> Optional[Dict]:
        """Load data from JSON file"""
        try:
            if path.exists():
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
        return None
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get data store statistics"""
        return {
            "users": len(list(self.users_dir.glob("*.json"))),
            "brands": len(list(self.brands_dir.glob("*.json"))),
            "clients": len(list(self.clients_dir.glob("*.json"))),
            "profiles": len(list(self.profiles_dir.glob("*.json"))),
            "recordings": len(list(self.recordings_dir.glob("*.json"))),
            "data_dir": str(self.data_dir)
        }


# Global data store instance
_data_store = None

async def get_data_store() -> DataStore:
    """Get or create the global data store"""
    global _data_store
    if _data_store is None:
        _data_store = DataStore()
        await _data_store.initialize()
    return _data_store

