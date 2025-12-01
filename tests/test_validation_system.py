#!/usr/bin/env python3
"""
Test Script for Validation System
Tests all new features: profiles, validation, and enhanced documents
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("🧪 Testing Validation System Components")
print("=" * 60)

# Test 1: Import all modules
print("\n1️⃣ Testing Module Imports...")
try:
    from documents.schemas import (
        ClientProfile, BrandProfile, PersonProfile,
        Claim, ValidationResult, ValidationStatus,
        create_fact, create_claim
    )
    print("   ✅ Document schemas imported")
except Exception as e:
    print(f"   ❌ Failed to import document schemas: {e}")
    sys.exit(1)

try:
    from profiles.profile_manager import ProfileManager
    print("   ✅ Profile manager imported")
except Exception as e:
    print(f"   ❌ Failed to import profile manager: {e}")
    sys.exit(1)

try:
    from validation.claim_extractor import ClaimExtractor
    print("   ✅ Claim extractor imported")
except Exception as e:
    print(f"   ❌ Failed to import claim extractor: {e}")
    sys.exit(1)

try:
    from validation.validator import ClaimValidator
    print("   ✅ Claim validator imported")
except Exception as e:
    print(f"   ❌ Failed to import claim validator: {e}")
    sys.exit(1)

# Test 2: Profile Manager
print("\n2️⃣ Testing Profile Manager...")
async def test_profiles():
    try:
        manager = ProfileManager(storage_path="test_profiles")
        
        # Create client profile
        client = await manager.create_client_profile(
            name="Test Client",
            type="company",
            description="A test client for validation",
            tags=["test", "demo"]
        )
        print(f"   ✅ Created client profile: {client.name} ({client.id})")
        
        # Add fact to client
        fact = await manager.add_fact(
            profile_id=client.id,
            profile_type="client",
            statement="Test Client has 50 employees",
            source_id="test_doc_001",
            confidence=0.95
        )
        print(f"   ✅ Added fact to client: {fact.statement}")
        
        # Create brand profile
        brand = await manager.create_brand_profile(
            name="Test Brand",
            description="A test brand for validation",
            values=["quality", "innovation"],
            tags=["test", "brand"]
        )
        print(f"   ✅ Created brand profile: {brand.name} ({brand.id})")
        
        # List profiles
        clients = await manager.list_client_profiles()
        brands = await manager.list_brand_profiles()
        print(f"   ✅ Listed profiles: {len(clients)} clients, {len(brands)} brands")
        
        # Cleanup
        await manager.delete_client_profile(client.id)
        await manager.delete_brand_profile(brand.id)
        print("   ✅ Cleanup completed")
        
        return True
    except Exception as e:
        print(f"   ❌ Profile manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(test_profiles())
if not result:
    sys.exit(1)

# Test 3: Claim Extractor
print("\n3️⃣ Testing Claim Extractor...")
async def test_claim_extractor():
    try:
        extractor = ClaimExtractor()
        
        test_text = """
        Praxis has over 150 stores in Netherlands and Belgium.
        The company focuses on DIY and home improvement products.
        They plan to expand into Germany next year.
        """
        
        # Test rule-based extraction (no LLM required)
        claims = await extractor.extract_claims(
            transcription=test_text,
            transcription_id="test_001",
            use_llm=False  # Use rule-based for testing
        )
        
        print(f"   ✅ Extracted {len(claims)} claims using rule-based method")
        for i, claim in enumerate(claims, 1):
            print(f"      {i}. [{claim.type.value}] {claim.text[:50]}...")
        
        return True
    except Exception as e:
        print(f"   ❌ Claim extractor test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(test_claim_extractor())
if not result:
    sys.exit(1)

# Test 4: Validator (basic)
print("\n4️⃣ Testing Validator...")
async def test_validator():
    try:
        from documents.schemas import ClaimType
        
        validator = ClaimValidator()
        
        # Create a test claim
        test_claim = create_claim(
            text="Test Company has 100 employees",
            transcription_id="test_001",
            timestamp=0.0,
            claim_type=ClaimType.FACT,
            confidence=0.9
        )
        
        # Validate without LLM (will return NO_DATA since no KB exists)
        result = await validator.validate_claim(test_claim, use_llm=False)
        
        print(f"   ✅ Validation completed: {result.status.value}")
        print(f"      Confidence: {result.confidence:.2f}")
        print(f"      Recommendation: {result.recommendation}")
        
        return True
    except Exception as e:
        print(f"   ❌ Validator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

result = asyncio.run(test_validator())
if not result:
    sys.exit(1)

# Test 5: Document Processor Enhancement
print("\n5️⃣ Testing Enhanced Document Processor...")
try:
    from documents.processor import DocumentInfo
    from datetime import datetime
    
    # Create test document with new fields
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
    
    print(f"   ✅ Document with enhanced metadata:")
    print(f"      Tags: {doc.tags}")
    print(f"      Context: {doc.context}")
    print(f"      Category: {doc.category}")
    
except Exception as e:
    print(f"   ❌ Document processor test failed: {e}")
    sys.exit(1)

# Test 6: Data Schemas
print("\n6️⃣ Testing Data Schemas...")
try:
    from documents.schemas import EntityType, ClaimType, ValidationStatus
    
    # Test enums
    assert EntityType.DOCUMENT == "document"
    assert ClaimType.FACT == "fact"
    assert ValidationStatus.CONFIRMED == "confirmed"
    
    # Test create_fact helper
    fact = create_fact(
        statement="Test fact",
        source_id="test_001",
        source_type="test",
        confidence=0.9
    )
    assert fact.statement == "Test fact"
    assert fact.confidence == 0.9
    
    print("   ✅ All data schemas working correctly")
    
except Exception as e:
    print(f"   ❌ Schema test failed: {e}")
    sys.exit(1)

# Cleanup
print("\n🧹 Cleaning up test data...")
import shutil
test_profile_path = Path("test_profiles")
if test_profile_path.exists():
    shutil.rmtree(test_profile_path)
    print("   ✅ Test profiles directory cleaned")

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print()
print("🎉 Validation system is working correctly!")
print()
print("Next steps:")
print("1. Start the system: ./start_app.sh")
print("2. Test UI at: http://localhost:3001")
print("3. Check profiles page: http://localhost:3001/profiles.html")
print("4. Check validation page: http://localhost:3001/validation.html")
print()

