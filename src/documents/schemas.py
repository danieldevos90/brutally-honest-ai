"""
Enhanced Data Schemas for Knowledge Base & Validation System
Includes support for profiles, tags, validation, and fact-checking
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class EntityType(str, Enum):
    """Types of entities in the system"""
    DOCUMENT = "document"
    CLIENT = "client"
    BRAND = "brand"
    PERSON = "person"
    USE_CASE = "use_case"


class ClaimType(str, Enum):
    """Types of claims found in transcriptions"""
    FACT = "fact"
    OPINION = "opinion"
    PREDICTION = "prediction"
    STATEMENT = "statement"


class ValidationStatus(str, Enum):
    """Status of a validation result"""
    CONFIRMED = "confirmed"
    CONTRADICTED = "contradicted"
    UNCERTAIN = "uncertain"
    NO_DATA = "no_data"
    PENDING = "pending"


class FactSeverity(str, Enum):
    """Severity level for validation rules"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


# ============================================================================
# DOCUMENT SCHEMAS (Enhanced)
# ============================================================================

@dataclass
class DocumentMetadata:
    """Enhanced metadata for documents"""
    tags: List[str] = field(default_factory=list)
    context_description: Optional[str] = None
    author: Optional[str] = None
    date: Optional[datetime] = None
    version: Optional[str] = None
    category: Optional[str] = None
    related_documents: List[str] = field(default_factory=list)
    parent_document: Optional[str] = None
    linked_profiles: List[str] = field(default_factory=list)  # IDs of related profiles
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'tags': self.tags,
            'context_description': self.context_description,
            'author': self.author,
            'date': self.date.isoformat() if self.date else None,
            'version': self.version,
            'category': self.category,
            'related_documents': self.related_documents,
            'parent_document': self.parent_document,
            'linked_profiles': self.linked_profiles,
            'custom_fields': self.custom_fields
        }


@dataclass
class DocumentInfo:
    """Enhanced document information with rich metadata"""
    id: str
    filename: str
    file_type: str
    content: str
    metadata: DocumentMetadata
    upload_time: datetime
    file_size: int
    text_length: int
    hash: str
    
    # Optional fields for enhanced functionality
    tags: List[str] = field(default_factory=list)
    context: Optional[str] = None


# ============================================================================
# PROFILE SCHEMAS
# ============================================================================

@dataclass
class Fact:
    """A factual statement with source and verification"""
    id: str
    statement: str
    confidence: float  # 0.0-1.0
    source_type: str  # "document", "transcription", "manual"
    source_id: str
    verified: bool
    created_at: datetime
    updated_at: datetime
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'statement': self.statement,
            'confidence': self.confidence,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'verified': self.verified,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'tags': self.tags,
            'metadata': self.metadata
        }


@dataclass
class ClientProfile:
    """Profile for a client or customer"""
    id: str
    name: str
    type: str  # "individual", "company", "brand"
    description: str
    tags: List[str] = field(default_factory=list)
    facts: List[Fact] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)  # Document IDs
    preferences: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'tags': self.tags,
            'facts': [f.to_dict() for f in self.facts],
            'documents': self.documents,
            'preferences': self.preferences,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class BrandProfile:
    """Profile for a brand or company"""
    id: str
    name: str
    description: str
    values: List[str] = field(default_factory=list)
    official_statements: List[str] = field(default_factory=list)
    guidelines: List[str] = field(default_factory=list)
    facts: List[Fact] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    documents: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'values': self.values,
            'official_statements': self.official_statements,
            'guidelines': self.guidelines,
            'facts': [f.to_dict() for f in self.facts],
            'tags': self.tags,
            'documents': self.documents,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class PersonProfile:
    """Profile for a specific person"""
    id: str
    name: str
    role: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    known_statements: List[str] = field(default_factory=list)
    credibility_score: float = 1.0  # 0.0-1.0
    transcriptions: List[str] = field(default_factory=list)  # Transcription IDs
    facts: List[Fact] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'company': self.company,
            'bio': self.bio,
            'known_statements': self.known_statements,
            'credibility_score': self.credibility_score,
            'transcriptions': self.transcriptions,
            'facts': [f.to_dict() for f in self.facts],
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# ============================================================================
# VALIDATION SCHEMAS
# ============================================================================

@dataclass
class Entity:
    """An entity extracted from text (person, brand, product, etc.)"""
    text: str
    type: str  # "person", "brand", "product", "organization", etc.
    confidence: float
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Claim:
    """A claim extracted from transcription"""
    id: str
    text: str
    type: ClaimType
    transcription_id: str
    timestamp: float  # Position in audio (seconds)
    confidence: float
    entities: List[Entity] = field(default_factory=list)
    speaker: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'text': self.text,
            'type': self.type.value,
            'entities': [e.__dict__ for e in self.entities],
            'transcription_id': self.transcription_id,
            'timestamp': self.timestamp,
            'confidence': self.confidence,
            'speaker': self.speaker,
            'metadata': self.metadata
        }


@dataclass
class Evidence:
    """Evidence supporting or contradicting a claim"""
    source_type: str  # "document", "profile", "transcription"
    source_id: str
    content: str
    similarity_score: float
    page: Optional[int] = None
    supports_claim: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_type': self.source_type,
            'source_id': self.source_id,
            'content': self.content,
            'similarity_score': self.similarity_score,
            'page': self.page,
            'supports_claim': self.supports_claim,
            'metadata': self.metadata
        }


@dataclass
class ValidationResult:
    """Result of validating a claim against knowledge base"""
    claim: Claim
    status: ValidationStatus
    confidence: float
    supporting_facts: List[Fact] = field(default_factory=list)
    contradicting_facts: List[Fact] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    recommendation: str = ""
    validation_time: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'claim': self.claim.to_dict(),
            'status': self.status.value,
            'confidence': self.confidence,
            'supporting_facts': [f.to_dict() for f in self.supporting_facts],
            'contradicting_facts': [f.to_dict() for f in self.contradicting_facts],
            'evidence': [e.to_dict() for e in self.evidence],
            'recommendation': self.recommendation,
            'validation_time': self.validation_time.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ValidationReport:
    """Complete validation report for a transcription"""
    id: str
    transcription_id: str
    transcription_text: str
    claims: List[Claim] = field(default_factory=list)
    validations: List[ValidationResult] = field(default_factory=list)
    overall_credibility: float = 1.0  # 0.0-1.0
    summary: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'transcription_id': self.transcription_id,
            'transcription_text': self.transcription_text,
            'claims': [c.to_dict() for c in self.claims],
            'validations': [v.to_dict() for v in self.validations],
            'overall_credibility': self.overall_credibility,
            'summary': self.summary,
            'warnings': self.warnings,
            'errors': self.errors,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


# ============================================================================
# USE CASE SCHEMAS
# ============================================================================

@dataclass
class ValidationRule:
    """A rule for validating content"""
    id: str
    name: str
    description: str
    field: str
    condition: str  # "contains", "equals", "matches_pattern", etc.
    value: Any
    severity: FactSeverity
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'field': self.field,
            'condition': self.condition,
            'value': self.value,
            'severity': self.severity.value,
            'enabled': self.enabled,
            'metadata': self.metadata
        }


@dataclass
class UseCase:
    """A use case template for validation"""
    id: str
    name: str
    description: str
    type: str  # "brand-validation", "contract-review", etc.
    validation_rules: List[ValidationRule] = field(default_factory=list)
    required_profiles: List[str] = field(default_factory=list)
    required_documents: List[str] = field(default_factory=list)
    confidence_threshold: float = 0.7
    tags: List[str] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'validation_rules': [r.to_dict() for r in self.validation_rules],
            'required_profiles': self.required_profiles,
            'required_documents': self.required_documents,
            'confidence_threshold': self.confidence_threshold,
            'tags': self.tags,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_fact(statement: str, source_id: str, source_type: str = "manual", 
                confidence: float = 1.0, verified: bool = False) -> Fact:
    """Helper function to create a new fact"""
    import uuid
    return Fact(
        id=str(uuid.uuid4()),
        statement=statement,
        confidence=confidence,
        source_type=source_type,
        source_id=source_id,
        verified=verified,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def create_claim(text: str, transcription_id: str, timestamp: float = 0.0,
                 claim_type: ClaimType = ClaimType.STATEMENT, 
                 confidence: float = 1.0) -> Claim:
    """Helper function to create a new claim"""
    import uuid
    return Claim(
        id=str(uuid.uuid4()),
        text=text,
        type=claim_type,
        transcription_id=transcription_id,
        timestamp=timestamp,
        confidence=confidence
    )


def create_evidence(source_type: str, source_id: str, content: str,
                   similarity_score: float, supports_claim: bool = True) -> Evidence:
    """Helper function to create evidence"""
    return Evidence(
        source_type=source_type,
        source_id=source_id,
        content=content,
        similarity_score=similarity_score,
        supports_claim=supports_claim
    )

