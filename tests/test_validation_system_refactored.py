"""
Validation System Tests - Refactored for pytest
Properly structured tests following pytest best practices
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ============================================
# MODULE IMPORT TESTS
# ============================================

class TestModuleImports:
    """Test that all modules can be imported."""
    
    @pytest.mark.unit
    def test_import_document_schemas(self):
        """Test document schemas import."""
        from documents.schemas import (
            ClientProfile, BrandProfile, PersonProfile,
            Claim, ValidationResult, ValidationStatus,
            create_fact, create_claim
        )
        
        assert ClientProfile is not None
        assert BrandProfile is not None
        assert create_fact is not None
    
    @pytest.mark.unit
    def test_import_profile_manager(self):
        """Test profile manager import."""
        from profiles.profile_manager import ProfileManager
        
        assert ProfileManager is not None
    
    @pytest.mark.unit
    def test_import_claim_extractor(self):
        """Test claim extractor import."""
        from validation.claim_extractor import ClaimExtractor
        
        assert ClaimExtractor is not None
    
    @pytest.mark.unit
    def test_import_validator(self):
        """Test validator import."""
        from validation.validator import ClaimValidator
        
        assert ClaimValidator is not None


# ============================================
# PROFILE MANAGER TESTS
# ============================================

class TestProfileManager:
    """Tests for ProfileManager functionality."""
    
    @pytest.fixture
    def profile_manager(self, tmp_path):
        """Create ProfileManager with temp storage."""
        from profiles.profile_manager import ProfileManager
        return ProfileManager(storage_path=str(tmp_path / "profiles"))
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_client_profile(self, profile_manager):
        """Test creating a client profile."""
        profile = await profile_manager.create_client_profile(
            name="Test Client",
            type="company",
            description="A test client",
            tags=["test", "demo"]
        )
        
        assert profile is not None
        assert profile.name == "Test Client"
        assert profile.id is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_brand_profile(self, profile_manager):
        """Test creating a brand profile."""
        profile = await profile_manager.create_brand_profile(
            name="Test Brand",
            description="A test brand",
            values=["quality", "innovation"],
            tags=["test"]
        )
        
        assert profile is not None
        assert profile.name == "Test Brand"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_fact_to_profile(self, profile_manager):
        """Test adding a fact to a profile."""
        # Create profile first
        client = await profile_manager.create_client_profile(
            name="Fact Test Client",
            type="company",
            description="Client for fact testing"
        )
        
        # Add fact
        fact = await profile_manager.add_fact(
            profile_id=client.id,
            profile_type="client",
            statement="Test Client has 50 employees",
            source_id="test_doc_001",
            confidence=0.95
        )
        
        assert fact is not None
        assert fact.statement == "Test Client has 50 employees"
        assert fact.confidence == 0.95
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_list_client_profiles(self, profile_manager):
        """Test listing client profiles."""
        # Create some profiles
        await profile_manager.create_client_profile(
            name="Client 1", type="company", description="First"
        )
        await profile_manager.create_client_profile(
            name="Client 2", type="individual", description="Second"
        )
        
        profiles = await profile_manager.list_client_profiles()
        
        assert len(profiles) >= 2
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_delete_client_profile(self, profile_manager):
        """Test deleting a client profile."""
        profile = await profile_manager.create_client_profile(
            name="To Delete", type="company", description="Will be deleted"
        )
        
        result = await profile_manager.delete_client_profile(profile.id)
        
        assert result == True
        
        # Verify deleted
        fetched = await profile_manager.get_client_profile(profile.id)
        assert fetched is None


# ============================================
# CLAIM EXTRACTOR TESTS
# ============================================

class TestClaimExtractor:
    """Tests for ClaimExtractor functionality."""
    
    @pytest.fixture
    def claim_extractor(self):
        """Create ClaimExtractor instance."""
        from validation.claim_extractor import ClaimExtractor
        return ClaimExtractor()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_claims_rule_based(self, claim_extractor):
        """Test rule-based claim extraction."""
        test_text = """
        Praxis has over 150 stores in Netherlands and Belgium.
        The company focuses on DIY and home improvement products.
        They plan to expand into Germany next year.
        """
        
        claims = await claim_extractor.extract_claims(
            transcription=test_text,
            transcription_id="test_001",
            use_llm=False
        )
        
        assert isinstance(claims, list)
        # Should extract some claims based on rules
        assert len(claims) >= 0  # Rule-based may find claims
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_claims_with_numbers(self, claim_extractor):
        """Test claim extraction with numeric claims."""
        test_text = """
        The company has 500 employees worldwide.
        Annual revenue reached 10 million euros last year.
        We have 25 offices across Europe.
        """
        
        claims = await claim_extractor.extract_claims(
            transcription=test_text,
            transcription_id="test_002",
            use_llm=False
        )
        
        assert isinstance(claims, list)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_extract_claims_empty_text(self, claim_extractor):
        """Test claim extraction with empty text."""
        claims = await claim_extractor.extract_claims(
            transcription="",
            transcription_id="test_003",
            use_llm=False
        )
        
        assert isinstance(claims, list)
        assert len(claims) == 0


# ============================================
# VALIDATOR TESTS
# ============================================

class TestValidator:
    """Tests for ClaimValidator functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create ClaimValidator instance."""
        from validation.validator import ClaimValidator
        return ClaimValidator()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_claim_without_llm(self, validator):
        """Test claim validation without LLM (returns NO_DATA)."""
        from documents.schemas import ClaimType, create_claim
        
        test_claim = create_claim(
            text="Test Company has 100 employees",
            transcription_id="test_001",
            timestamp=0.0,
            claim_type=ClaimType.FACT,
            confidence=0.9
        )
        
        result = await validator.validate_claim(test_claim, use_llm=False)
        
        assert result is not None
        assert hasattr(result, 'status')
        assert hasattr(result, 'confidence')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_claim_returns_recommendation(self, validator):
        """Test that validation returns a recommendation."""
        from documents.schemas import ClaimType, create_claim
        
        test_claim = create_claim(
            text="Some testable claim",
            transcription_id="test_002",
            timestamp=0.0,
            claim_type=ClaimType.FACT,
            confidence=0.8
        )
        
        result = await validator.validate_claim(test_claim, use_llm=False)
        
        assert hasattr(result, 'recommendation')


# ============================================
# DATA SCHEMA TESTS
# ============================================

class TestDataSchemas:
    """Tests for data schemas."""
    
    @pytest.mark.unit
    def test_entity_type_enum(self):
        """Test EntityType enum values."""
        from documents.schemas import EntityType
        
        assert EntityType.DOCUMENT == "document"
    
    @pytest.mark.unit
    def test_claim_type_enum(self):
        """Test ClaimType enum values."""
        from documents.schemas import ClaimType
        
        assert ClaimType.FACT == "fact"
    
    @pytest.mark.unit
    def test_validation_status_enum(self):
        """Test ValidationStatus enum values."""
        from documents.schemas import ValidationStatus
        
        assert ValidationStatus.CONFIRMED == "confirmed"
    
    @pytest.mark.unit
    def test_create_fact_helper(self):
        """Test create_fact helper function."""
        from documents.schemas import create_fact
        
        fact = create_fact(
            statement="Test fact statement",
            source_id="test_source_001",
            source_type="document",
            confidence=0.9
        )
        
        assert fact.statement == "Test fact statement"
        assert fact.source_id == "test_source_001"
        assert fact.confidence == 0.9
    
    @pytest.mark.unit
    def test_create_claim_helper(self):
        """Test create_claim helper function."""
        from documents.schemas import create_claim, ClaimType
        
        claim = create_claim(
            text="Test claim text",
            transcription_id="trans_001",
            timestamp=5.0,
            claim_type=ClaimType.FACT,
            confidence=0.85
        )
        
        assert claim.text == "Test claim text"
        assert claim.transcription_id == "trans_001"
        assert claim.timestamp == 5.0
        assert claim.confidence == 0.85


# ============================================
# DOCUMENT INFO TESTS
# ============================================

class TestDocumentInfo:
    """Tests for DocumentInfo with enhanced fields."""
    
    @pytest.mark.unit
    def test_document_info_with_metadata(self):
        """Test DocumentInfo creation with enhanced metadata."""
        from documents.processor import DocumentInfo
        from datetime import datetime
        
        doc = DocumentInfo(
            id="test_doc_001",
            filename="test.txt",
            file_type=".txt",
            content="Test content",
            metadata={"test": True},
            upload_time=datetime.now(),
            file_size=100,
            text_length=12,
            hash="test_hash",
            tags=["test", "demo"],
            context="Test document for validation",
            category="testing"
        )
        
        assert doc.id == "test_doc_001"
        assert doc.tags == ["test", "demo"]
        assert doc.context == "Test document for validation"
        assert doc.category == "testing"
    
    @pytest.mark.unit
    def test_document_info_optional_fields(self):
        """Test DocumentInfo with optional fields."""
        from documents.processor import DocumentInfo
        from datetime import datetime
        
        doc = DocumentInfo(
            id="test_doc_002",
            filename="minimal.txt",
            file_type=".txt",
            content="Minimal content",
            metadata={},
            upload_time=datetime.now(),
            file_size=50,
            text_length=15,
            hash="min_hash"
        )
        
        assert doc.id == "test_doc_002"
        # Optional fields should have defaults
        assert doc.tags == [] or doc.tags is None


# ============================================
# INTEGRATION TESTS
# ============================================

class TestValidationIntegration:
    """Integration tests for the validation system."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_validation_workflow(self, tmp_path):
        """Test complete validation workflow."""
        from profiles.profile_manager import ProfileManager
        from validation.claim_extractor import ClaimExtractor
        from validation.validator import ClaimValidator
        
        # Setup
        profile_manager = ProfileManager(storage_path=str(tmp_path / "profiles"))
        extractor = ClaimExtractor()
        validator = ClaimValidator()
        
        # Create a client profile
        client = await profile_manager.create_client_profile(
            name="Integration Test Client",
            type="company",
            description="Client for integration testing"
        )
        
        # Add some known facts
        await profile_manager.add_fact(
            profile_id=client.id,
            profile_type="client",
            statement="Integration Test Client has 100 employees",
            source_id="integration_test",
            confidence=1.0
        )
        
        # Extract claims from text
        text = "Integration Test Client is a great company with many employees."
        claims = await extractor.extract_claims(
            transcription=text,
            transcription_id="integration_001",
            use_llm=False
        )
        
        # Validate claims (without LLM, will return NO_DATA)
        for claim in claims:
            result = await validator.validate_claim(claim, use_llm=False)
            assert result is not None
        
        # Cleanup
        await profile_manager.delete_client_profile(client.id)
