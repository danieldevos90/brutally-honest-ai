# Quick Start: Building the Validation System

## 🎯 What You Have Now

✅ **Fixed**: Document upload working with proper UUID support
✅ **Created**: Comprehensive roadmap (`KNOWLEDGE_BASE_ROADMAP.md`)
✅ **Created**: Enhanced data schemas (`src/documents/schemas.py`)
✅ **Working**: Basic document storage and vector search

## 🚀 Next Steps to Build Validation System

### Phase 1: Enable Tags & Metadata (1-2 days)

**Goal**: Allow users to tag documents and add context

#### 1. Update API Endpoint
Edit `/Users/danieldevos/Documents/ALT F AWESOME/brutally-honest-ai/api_server.py`:

```python
# Add tags to document upload
@app.post("/documents/upload")
async def upload_document(
    file: UploadFile,
    tags: Optional[str] = Form(None),  # Comma-separated tags
    context: Optional[str] = Form(None),  # Context description
    category: Optional[str] = Form(None)  # Document category
):
    # Parse tags
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    
    # Process document...
    # Add tags and metadata to DocumentInfo
    doc_info.tags = tag_list
    doc_info.context = context
    # ...
```

#### 2. Update Frontend UI
Edit `frontend/public/documents.html` to add:
- Tag input field
- Context text area
- Category dropdown
- Display tags in document list

### Phase 2: Simple Claim Validation (3-5 days)

**Goal**: Basic fact-checking of transcriptions

#### 1. Create Validation Module
Create `src/validation/claim_validator.py`:

```python
"""
Simple claim validation against documents
"""

from src.documents.vector_store import get_vector_store
from src.documents.schemas import Claim, ValidationResult, ValidationStatus

async def validate_claim(claim_text: str, confidence_threshold: float = 0.7):
    """
    Validate a claim against the knowledge base
    
    Args:
        claim_text: The claim to validate
        confidence_threshold: Minimum similarity score
    
    Returns:
        ValidationResult
    """
    # Get vector store
    vector_store = await get_vector_store()
    
    # Search for similar content
    results = await vector_store.search_documents(
        query=claim_text,
        limit=5,
        score_threshold=confidence_threshold
    )
    
    # Determine validation status
    if not results:
        status = ValidationStatus.NO_DATA
    elif results[0].score > 0.9:
        status = ValidationStatus.CONFIRMED
    elif results[0].score > confidence_threshold:
        status = ValidationStatus.UNCERTAIN
    else:
        status = ValidationStatus.NO_DATA
    
    # Create result
    return ValidationResult(
        claim=create_claim(claim_text, "manual", 0.0),
        status=status,
        confidence=results[0].score if results else 0.0,
        evidence=[
            create_evidence(
                source_type="document",
                source_id=r.document_id,
                content=r.content,
                similarity_score=r.score,
                supports_claim=True
            )
            for r in results
        ]
    )
```

#### 2. Add API Endpoint
Add to `api_server.py`:

```python
@app.post("/ai/validate-claim")
async def validate_claim_endpoint(claim: str):
    """Validate a single claim"""
    from src.validation.claim_validator import validate_claim
    
    result = await validate_claim(claim)
    return result.to_dict()

@app.post("/ai/validate-transcription")
async def validate_transcription_endpoint(transcription_id: str):
    """Validate all claims in a transcription"""
    # Get transcription
    # Extract claims
    # Validate each claim
    # Return report
    pass
```

#### 3. Update UI
Add validation button to transcription results that shows:
- Claims found
- Validation status (confirmed/contradicted/uncertain)
- Supporting evidence from documents
- Confidence scores

### Phase 3: Client Profiles (1 week)

**Goal**: Store client information for validation

#### 1. Create Profile Manager
Create `src/profiles/profile_manager.py`:

```python
"""
Profile management system
"""

from src.documents.schemas import ClientProfile, BrandProfile, PersonProfile
import json
from pathlib import Path

class ProfileManager:
    def __init__(self, storage_path: str = "profiles"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
    
    async def create_client_profile(self, name: str, type: str, 
                                   description: str) -> ClientProfile:
        """Create a new client profile"""
        import uuid
        profile = ClientProfile(
            id=str(uuid.uuid4()),
            name=name,
            type=type,
            description=description
        )
        await self._save_profile(profile)
        return profile
    
    async def add_fact_to_profile(self, profile_id: str, 
                                  fact_statement: str, source_id: str):
        """Add a fact to a profile"""
        from src.documents.schemas import create_fact
        
        profile = await self.get_profile(profile_id)
        fact = create_fact(fact_statement, source_id, "manual")
        profile.facts.append(fact)
        await self._save_profile(profile)
    
    async def _save_profile(self, profile):
        """Save profile to JSON"""
        file_path = self.storage_path / f"{profile.id}.json"
        with open(file_path, 'w') as f:
            json.dump(profile.to_dict(), f, indent=2)
    
    async def get_profile(self, profile_id: str):
        """Load profile from JSON"""
        file_path = self.storage_path / f"{profile_id}.json"
        with open(file_path, 'r') as f:
            data = json.load(f)
            # Convert back to profile object
            # ...
```

#### 2. Add Profile API Endpoints
```python
@app.post("/profiles/clients")
async def create_client_profile(name: str, type: str, description: str):
    """Create a new client profile"""
    # ...

@app.get("/profiles/clients")
async def list_client_profiles():
    """List all client profiles"""
    # ...

@app.post("/profiles/clients/{id}/facts")
async def add_fact_to_profile(id: str, statement: str, source_id: str):
    """Add a fact to a profile"""
    # ...
```

#### 3. Create Profile UI Page
Create `frontend/public/profiles.html`:
- List profiles
- Create new profile
- Add facts to profile
- Link documents to profile

## 📋 Example Workflow

### Scenario: Validate Brand Claims

1. **Setup Knowledge Base**:
   ```
   - Upload brand guidelines document
   - Tag it: "brand, guidelines, official"
   - Add context: "Official Praxis brand guidelines 2025"
   ```

2. **Create Brand Profile**:
   ```
   - Name: "Praxis"
   - Type: "brand"
   - Description: "Dutch DIY retail chain"
   - Add facts:
     * "Praxis focuses on DIY and home improvement"
     * "Praxis has over 150 stores in Netherlands and Belgium"
   ```

3. **Process Transcription**:
   ```
   Transcription: "Praxis has 200 stores across Europe"
   
   Validation:
   - Claim extracted: "Praxis has 200 stores across Europe"
   - Search knowledge base...
   - Found: "Praxis has over 150 stores in Netherlands and Belgium"
   - Status: CONTRADICTED
   - Confidence: 0.85
   - Evidence: [fact from profile]
   - Warning: "Claim contradicts known facts about store count"
   ```

4. **Review Results**:
   - See validation report
   - Review evidence
   - Mark claim as incorrect
   - Update credibility score

## 🎨 UI Mockup

### Document Upload (Enhanced)
```
┌─────────────────────────────────────┐
│ Upload Document                      │
├─────────────────────────────────────┤
│ File: [Choose File]                 │
│                                      │
│ Tags: [brand, policy, 2025]         │
│                                      │
│ Category: [Brand Guidelines ▼]      │
│                                      │
│ Context:                             │
│ ┌─────────────────────────────────┐ │
│ │ Official brand guidelines...    │ │
│ └─────────────────────────────────┘ │
│                                      │
│ [Upload]                             │
└─────────────────────────────────────┘
```

### Validation Results
```
┌─────────────────────────────────────┐
│ Validation Report                    │
├─────────────────────────────────────┤
│ Transcription: rec_20100411...       │
│ Overall Credibility: 75%             │
│                                      │
│ Claims Found: 3                      │
│                                      │
│ ⚠️ Claim 1 (CONTRADICTED)           │
│ "Praxis has 200 stores..."          │
│ Evidence:                            │
│ • Document: brand_guidelines.pdf    │
│   "150 stores in NL/BE"             │
│   Similarity: 85%                   │
│                                      │
│ ✅ Claim 2 (CONFIRMED)               │
│ "Praxis focuses on DIY..."          │
│ Evidence:                            │
│ • Profile: Praxis Brand             │
│   "DIY and home improvement"        │
│   Similarity: 95%                   │
│                                      │
│ ❓ Claim 3 (UNCERTAIN)               │
│ "New stores opening in 2025..."     │
│ No matching data found              │
└─────────────────────────────────────┘
```

## 🛠️ Development Priority

1. ✅ **Week 1**: Add tags and metadata to documents
2. ⏳ **Week 2**: Basic claim validation API
3. ⏳ **Week 3**: Validation UI and results display
4. ⏳ **Week 4**: Client profile system
5. ⏳ **Week 5**: Profile UI and fact management
6. ⏳ **Week 6**: Full validation pipeline integration

## 📚 Resources Created

1. **KNOWLEDGE_BASE_ROADMAP.md** - Complete feature roadmap
2. **src/documents/schemas.py** - Data models for all entities
3. **QUICK_START_VALIDATION.md** - This file (implementation guide)

## 🤝 Need Help?

When implementing:
- Start small with tags and metadata
- Test validation with simple examples first
- Build UI incrementally
- Use the schemas as a reference
- Keep vector search at the core

The system is architected to grow:
- Documents → Tags → Profiles → Validation → Advanced Features

Start with Phase 1 and build from there! 🚀

