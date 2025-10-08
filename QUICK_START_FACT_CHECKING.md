# 🚀 Quick Start: Fact-Checking System

## Start Using in 3 Steps

### 1️⃣ Start the System
```bash
./start_app.sh
```

Wait for:
- ✅ Backend API: `http://localhost:8000`
- ✅ Frontend Web: `http://localhost:3001`

---

### 2️⃣ Build Your Knowledge Base (5 minutes)

**Upload Documents:**
1. Open `http://localhost:3001/documents.html`
2. Drag & drop your PDF, DOC, or TXT files
3. Documents are automatically indexed

**Create a Brand Profile:**
1. Open `http://localhost:3001/profiles.html`
2. Click "Brands" tab
3. Fill in:
   - Name: `Praxis`
   - Description: `Dutch DIY retail chain`
   - Values: `quality, DIY, customer-service`
   - Tags: `retail, europe`
4. Click "Create Profile"
5. Add facts:
   - Click "View Details" (or use API)
   - Add: "Praxis has over 150 stores in Netherlands and Belgium"

---

### 3️⃣ Validate Claims

**Quick Test:**
1. Open `http://localhost:3001/validation.html`
2. Enter test text:
   ```
   Praxis has 200 stores across Europe and focuses on DIY products.
   ```
3. Click "Validate Now"
4. See results:
   - ❌ First claim: **CONTRADICTED** (says 200, but you have 150 in KB)
   - ✅ Second claim: **CONFIRMED** (matches "DIY" value)

---

## 🎯 Real-World Example

### Scenario: Validate Interview Claims

**Setup (one time):**
```python
# 1. Upload candidate resume as PDF
# 2. Create person profile:
#    Name: John Doe
#    Role: Senior Developer
#    Company: Previous Corp
# 3. Add facts from resume:
#    "Worked at Previous Corp for 5 years"
#    "Led team of 10 developers"
```

**During Interview:**
```python
# Record and transcribe interview
# System automatically detects claims:
# ✅ "I worked at Previous Corp" → CONFIRMED
# ❌ "I managed 20 developers" → CONTRADICTED (resume says 10)
# ❓ "I increased performance by 300%" → UNCERTAIN (no data)
```

**Result:**
- Overall Credibility: 67%
- 1 contradiction flagged
- Review recommended

---

## 📊 What Gets Validated?

### Automatically Extracted Claims:
- ✅ **Facts**: "Company has X stores"
- ✅ **Numbers**: "Sales increased by 50%"
- ✅ **Relationships**: "Person works at Company"
- ✅ **Properties**: "Brand focuses on DIY"
- ⚠️ **Opinions**: Tagged but not validated as facts
- ⚠️ **Predictions**: Flagged as future statements

### Validation Sources:
1. **Documents**: Uploaded PDFs, DOCs, TXT files
2. **Profiles**: Client/Brand/Person facts
3. **Confidence**: Each source has confidence score
4. **Evidence**: Shows exact text that supports/contradicts

---

## 🎨 Understanding Results

### Status Indicators:

**🟢 CONFIRMED** (Green)
- Claim matches known facts
- High confidence (>85%)
- Evidence shown

**🔴 CONTRADICTED** (Red)  
- Claim conflicts with knowledge base
- **⚠️ WARNING** flagged
- Review recommended

**🟠 UNCERTAIN** (Orange)
- Evidence unclear or conflicting
- Medium confidence (50-75%)
- More data needed

**⚪ NO DATA** (Gray)
- No matching information found
- Add to knowledge base

---

## 💡 Pro Tips

### Building Strong Knowledge Base:

1. **Tag Everything**
   - Use consistent tags: `brand`, `official`, `policy`
   - Makes filtering easier

2. **Add Context**
   - Describe document purpose
   - Helps with relevance matching

3. **Use Facts Wisely**
   - Add specific, verifiable statements
   - Include confidence scores (0.0-1.0)
   - Cite sources

4. **Keep Profiles Updated**
   - Regular fact reviews
   - Remove outdated information

### Getting Best Validation Results:

1. **Clear Transcriptions**
   - Use good audio quality
   - Proper punctuation helps

2. **Specific Claims**
   - "150 stores" validates better than "many stores"
   - Numbers and names are precise

3. **Build Gradually**
   - Start with core facts
   - Expand as you validate

---

## 🔧 API Usage

### Python Example:
```python
import requests

# Validate text
response = requests.post(
    'http://localhost:8000/validation/validate-transcription',
    params={
        'transcription': "Praxis has 200 stores in Europe",
        'transcription_id': "interview_001",
        'extract_claims': 'true'
    }
)

report = response.json()['report']
print(f"Credibility: {report['overall_credibility']*100}%")
for validation in report['validations']:
    print(f"- {validation['claim']['text']}: {validation['status']}")
```

### JavaScript Example:
```javascript
// Validate from frontend
async function validateText(text) {
    const params = new URLSearchParams({
        transcription: text,
        transcription_id: Date.now().toString(),
        extract_claims: 'true'
    });
    
    const response = await fetch(
        `http://localhost:8000/validation/validate-transcription?${params}`,
        { method: 'POST' }
    );
    
    const result = await response.json();
    console.log('Credibility:', result.report.overall_credibility);
}
```

---

## 📱 Pages Overview

### Home (`/index.html`)
- Main dashboard
- Device connections
- Start here

### Documents (`/documents.html`)
- Upload knowledge base documents
- Search uploaded files
- View document stats

### Profiles (`/profiles.html`)  
- **NEW!** Manage clients, brands, persons
- Add facts to profiles
- Track relationships

### Validation (`/validation.html`)
- **NEW!** Quick validation testing
- View validation results
- Knowledge base status

---

## 🎓 Common Use Cases

### 1. Brand Compliance
- Upload brand guidelines
- Create brand profile with values
- Validate customer service transcripts
- **Flag**: Claims that contradict brand values

### 2. Interview Screening
- Upload candidate resume
- Create person profile with resume facts
- Record and validate interview
- **Flag**: Contradictions in experience claims

### 3. Sales Call QA
- Upload product specs and policies
- Create product profiles
- Validate sales call transcripts
- **Flag**: False promises or incorrect specs

### 4. Legal Review
- Upload contracts and agreements
- Create client profiles with terms
- Validate meeting transcripts
- **Flag**: Verbal commitments not in contract

---

## 🐛 Troubleshooting

**"No claims extracted"**
→ Text might be too short. Try 2-3 sentences minimum.

**"No data found"**
→ Add documents and profiles to knowledge base first.

**"Low confidence scores"**
→ Add more specific facts. Use exact wording from docs.

**"Validation slow"**
→ LLM processing takes time. Each claim ~1-2 seconds.

---

## 📈 Next Steps

1. ✅ Start system
2. ✅ Upload 5-10 documents
3. ✅ Create 2-3 profiles
4. ✅ Test with sample text
5. ✅ Integrate into workflow

**You're ready to fact-check at scale! 🎉**

---

## 🔗 Resources

- **Full Features**: See `IMPLEMENTATION_COMPLETE.md`
- **Roadmap**: See `KNOWLEDGE_BASE_ROADMAP.md`
- **API Docs**: `http://localhost:8000/docs`
- **Frontend**: `http://localhost:3001`

---

**Built maintaining your clean, professional style** ✨

