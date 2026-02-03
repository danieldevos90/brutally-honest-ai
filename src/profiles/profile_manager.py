"""
Profile Manager - Manages client, brand, and person profiles
"""

import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from documents.schemas import (
    ClientProfile, BrandProfile, PersonProfile,
    Fact, create_fact
)

logger = logging.getLogger(__name__)


class ProfileManager:
    """Manager for client, brand, and person profiles"""
    
    def __init__(self, storage_path: str = None):
        """
        Initialize profile manager
        
        Args:
            storage_path: Directory to store profile JSON files
        """
        if storage_path is None:
            # Use data/profiles relative to project root
            project_root = Path(__file__).parent.parent.parent
            storage_path = project_root / "data" / "profiles"
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)
        logger.info(f"📂 Profile storage: {self.storage_path}")
        
        # Create subdirectories for each profile type
        self.clients_path = self.storage_path / "clients"
        self.brands_path = self.storage_path / "brands"
        self.persons_path = self.storage_path / "persons"
        
        self.clients_path.mkdir(exist_ok=True)
        self.brands_path.mkdir(exist_ok=True)
        self.persons_path.mkdir(exist_ok=True)
        
        logger.info("✅ Profile manager initialized")
    
    # ============================================================================
    # CLIENT PROFILE METHODS
    # ============================================================================
    
    async def create_client_profile(
        self,
        name: str,
        type: str,
        description: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ClientProfile:
        """Create a new client profile"""
        profile = ClientProfile(
            id=str(uuid.uuid4()),
            name=name,
            type=type,
            description=description,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        await self._save_profile(profile, "client")
        logger.info(f"✅ Created client profile: {name} ({profile.id})")
        return profile
    
    async def get_client_profile(self, profile_id: str) -> Optional[ClientProfile]:
        """Get a client profile by ID"""
        return await self._load_profile(profile_id, "client")
    
    async def list_client_profiles(self) -> List[ClientProfile]:
        """List all client profiles"""
        return await self._list_profiles("client")
    
    async def update_client_profile(
        self,
        profile_id: str,
        name: Optional[str] = None,
        type: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> ClientProfile:
        """Update a client profile"""
        profile = await self.get_client_profile(profile_id)
        if not profile:
            raise ValueError(f"Client profile {profile_id} not found")
        
        if name:
            profile.name = name
        if type:
            profile.type = type
        if description:
            profile.description = description
        if tags is not None:
            profile.tags = tags
        
        profile.updated_at = datetime.now()
        await self._save_profile(profile, "client")
        logger.info(f"✅ Updated client profile: {profile.name}")
        return profile
    
    async def delete_client_profile(self, profile_id: str) -> bool:
        """Delete a client profile"""
        return await self._delete_profile(profile_id, "client")
    
    # ============================================================================
    # BRAND PROFILE METHODS
    # ============================================================================
    
    async def create_brand_profile(
        self,
        name: str,
        description: str,
        values: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> BrandProfile:
        """Create a new brand profile"""
        profile = BrandProfile(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            values=values or [],
            tags=tags or [],
            metadata=metadata or {}
        )
        
        await self._save_profile(profile, "brand")
        logger.info(f"✅ Created brand profile: {name} ({profile.id})")
        return profile
    
    async def get_brand_profile(self, profile_id: str) -> Optional[BrandProfile]:
        """Get a brand profile by ID"""
        return await self._load_profile(profile_id, "brand")
    
    async def list_brand_profiles(self) -> List[BrandProfile]:
        """List all brand profiles"""
        return await self._list_profiles("brand")
    
    async def update_brand_profile(
        self,
        profile_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        values: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> BrandProfile:
        """Update a brand profile"""
        profile = await self.get_brand_profile(profile_id)
        if not profile:
            raise ValueError(f"Brand profile {profile_id} not found")
        
        if name:
            profile.name = name
        if description:
            profile.description = description
        if values is not None:
            profile.values = values
        if tags is not None:
            profile.tags = tags
        
        profile.updated_at = datetime.now()
        await self._save_profile(profile, "brand")
        logger.info(f"✅ Updated brand profile: {profile.name}")
        return profile
    
    async def delete_brand_profile(self, profile_id: str) -> bool:
        """Delete a brand profile"""
        return await self._delete_profile(profile_id, "brand")
    
    # ============================================================================
    # PERSON PROFILE METHODS
    # ============================================================================
    
    async def create_person_profile(
        self,
        name: str,
        role: Optional[str] = None,
        company: Optional[str] = None,
        bio: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PersonProfile:
        """Create a new person profile"""
        profile = PersonProfile(
            id=str(uuid.uuid4()),
            name=name,
            role=role,
            company=company,
            bio=bio,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        await self._save_profile(profile, "person")
        logger.info(f"✅ Created person profile: {name} ({profile.id})")
        return profile
    
    async def get_person_profile(self, profile_id: str) -> Optional[PersonProfile]:
        """Get a person profile by ID"""
        return await self._load_profile(profile_id, "person")
    
    async def list_person_profiles(self) -> List[PersonProfile]:
        """List all person profiles"""
        return await self._list_profiles("person")
    
    async def update_person_profile(
        self,
        profile_id: str,
        name: Optional[str] = None,
        role: Optional[str] = None,
        company: Optional[str] = None,
        bio: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> PersonProfile:
        """Update a person profile"""
        profile = await self.get_person_profile(profile_id)
        if not profile:
            raise ValueError(f"Person profile {profile_id} not found")
        
        if name:
            profile.name = name
        if role is not None:
            profile.role = role
        if company is not None:
            profile.company = company
        if bio is not None:
            profile.bio = bio
        if tags is not None:
            profile.tags = tags
        
        profile.updated_at = datetime.now()
        await self._save_profile(profile, "person")
        logger.info(f"✅ Updated person profile: {profile.name}")
        return profile
    
    async def delete_person_profile(self, profile_id: str) -> bool:
        """Delete a person profile"""
        return await self._delete_profile(profile_id, "person")
    
    # ============================================================================
    # FACT MANAGEMENT METHODS
    # ============================================================================
    
    async def add_fact(
        self,
        profile_id: str,
        profile_type: str,
        statement: str,
        source_id: str,
        source_type: str = "manual",
        confidence: float = 1.0,
        verified: bool = False
    ) -> Fact:
        """Add a fact to a profile"""
        # Get the profile
        profile = await self._load_profile(profile_id, profile_type)
        if not profile:
            raise ValueError(f"{profile_type.title()} profile {profile_id} not found")
        
        # Create fact
        fact = create_fact(
            statement=statement,
            source_id=source_id,
            source_type=source_type,
            confidence=confidence,
            verified=verified
        )
        
        # Add to profile
        profile.facts.append(fact)
        profile.updated_at = datetime.now()
        
        # Save profile
        await self._save_profile(profile, profile_type)
        logger.info(f"✅ Added fact to {profile_type} profile: {profile.name}")
        return fact
    
    async def remove_fact(
        self,
        profile_id: str,
        profile_type: str,
        fact_id: str
    ) -> bool:
        """Remove a fact from a profile"""
        profile = await self._load_profile(profile_id, profile_type)
        if not profile:
            return False
        
        # Find and remove fact
        original_count = len(profile.facts)
        profile.facts = [f for f in profile.facts if f.id != fact_id]
        
        if len(profile.facts) < original_count:
            profile.updated_at = datetime.now()
            await self._save_profile(profile, profile_type)
            logger.info(f"✅ Removed fact from {profile_type} profile: {profile.name}")
            return True
        
        return False
    
    async def update_fact(
        self,
        profile_id: str,
        profile_type: str,
        fact_id: str,
        statement: Optional[str] = None,
        confidence: Optional[float] = None,
        verified: Optional[bool] = None
    ) -> Optional[Fact]:
        """Update a fact in a profile"""
        profile = await self._load_profile(profile_id, profile_type)
        if not profile:
            return None
        
        # Find fact
        fact = next((f for f in profile.facts if f.id == fact_id), None)
        if not fact:
            return None
        
        # Update fact
        if statement is not None:
            fact.statement = statement
        if confidence is not None:
            fact.confidence = confidence
        if verified is not None:
            fact.verified = verified
        
        fact.updated_at = datetime.now()
        profile.updated_at = datetime.now()
        
        await self._save_profile(profile, profile_type)
        logger.info(f"✅ Updated fact in {profile_type} profile: {profile.name}")
        return fact
    
    # ============================================================================
    # PRIVATE HELPER METHODS
    # ============================================================================
    
    def _get_profile_path(self, profile_id: str, profile_type: str) -> Path:
        """Get the file path for a profile"""
        if profile_type == "client":
            return self.clients_path / f"{profile_id}.json"
        elif profile_type == "brand":
            return self.brands_path / f"{profile_id}.json"
        elif profile_type == "person":
            return self.persons_path / f"{profile_id}.json"
        else:
            raise ValueError(f"Unknown profile type: {profile_type}")
    
    async def _save_profile(self, profile, profile_type: str):
        """Save a profile to JSON file"""
        file_path = self._get_profile_path(profile.id, profile_type)
        
        with open(file_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
    
    async def _load_profile(self, profile_id: str, profile_type: str):
        """Load a profile from JSON file"""
        file_path = self._get_profile_path(profile_id, profile_type)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert back to profile object
            if profile_type == "client":
                return self._dict_to_client_profile(data)
            elif profile_type == "brand":
                return self._dict_to_brand_profile(data)
            elif profile_type == "person":
                return self._dict_to_person_profile(data)
        except Exception as e:
            logger.error(f"Failed to load {profile_type} profile {profile_id}: {e}")
            return None
    
    async def _list_profiles(self, profile_type: str) -> List:
        """List all profiles of a type"""
        if profile_type == "client":
            path = self.clients_path
        elif profile_type == "brand":
            path = self.brands_path
        elif profile_type == "person":
            path = self.persons_path
        else:
            return []
        
        profiles = []
        for file_path in path.glob("*.json"):
            profile = await self._load_profile(file_path.stem, profile_type)
            if profile:
                profiles.append(profile)
        
        return profiles
    
    async def _delete_profile(self, profile_id: str, profile_type: str) -> bool:
        """Delete a profile"""
        file_path = self._get_profile_path(profile_id, profile_type)
        
        if file_path.exists():
            file_path.unlink()
            logger.info(f"✅ Deleted {profile_type} profile: {profile_id}")
            return True
        
        return False
    
    def _dict_to_client_profile(self, data: Dict) -> ClientProfile:
        """Convert dictionary to ClientProfile"""
        # Convert facts
        facts = [self._dict_to_fact(f) for f in data.get('facts', [])]
        
        return ClientProfile(
            id=data['id'],
            name=data['name'],
            type=data['type'],
            description=data['description'],
            tags=data.get('tags', []),
            facts=facts,
            documents=data.get('documents', []),
            preferences=data.get('preferences', {}),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
    
    def _dict_to_brand_profile(self, data: Dict) -> BrandProfile:
        """Convert dictionary to BrandProfile"""
        facts = [self._dict_to_fact(f) for f in data.get('facts', [])]
        
        return BrandProfile(
            id=data['id'],
            name=data['name'],
            description=data['description'],
            values=data.get('values', []),
            official_statements=data.get('official_statements', []),
            guidelines=data.get('guidelines', []),
            facts=facts,
            tags=data.get('tags', []),
            documents=data.get('documents', []),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
    
    def _dict_to_person_profile(self, data: Dict) -> PersonProfile:
        """Convert dictionary to PersonProfile"""
        facts = [self._dict_to_fact(f) for f in data.get('facts', [])]
        
        return PersonProfile(
            id=data['id'],
            name=data['name'],
            role=data.get('role'),
            company=data.get('company'),
            bio=data.get('bio'),
            known_statements=data.get('known_statements', []),
            credibility_score=data.get('credibility_score', 1.0),
            transcriptions=data.get('transcriptions', []),
            facts=facts,
            tags=data.get('tags', []),
            metadata=data.get('metadata', {}),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at'])
        )
    
    def _dict_to_fact(self, data: Dict) -> Fact:
        """Convert dictionary to Fact"""
        return Fact(
            id=data['id'],
            statement=data['statement'],
            confidence=data['confidence'],
            source_type=data['source_type'],
            source_id=data['source_id'],
            verified=data['verified'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            tags=data.get('tags', []),
            metadata=data.get('metadata', {})
        )


# Global profile manager instance
_profile_manager = None


async def get_profile_manager() -> ProfileManager:
    """Get or create the global profile manager"""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager

