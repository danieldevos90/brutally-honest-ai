# Brutally Honest AI - System Architecture

## High-Level Architecture Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                    USER INTERFACES                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐          │
│  │   Browser    │   │  Mobile App  │   │  ESP32 BLE   │   │  External    │          │
│  │ (Web Client) │   │   (Future)   │   │   Device     │   │  API Client  │          │
│  └──────┬───────┘   └──────────────┘   └──────┬───────┘   └──────┬───────┘          │
│         │                                      │                   │                  │
└─────────┼──────────────────────────────────────┼───────────────────┼──────────────────┘
          │                                      │                   │
          ▼                                      ▼                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (Node.js/Express)                              │
│                                   Port 3001                                          │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Login/    │  │    Home     │  │  Documents  │  │  Profiles   │  │ Validation │ │
│  │    Auth     │  │  (Record,   │  │  (Upload,   │  │  (Clients,  │  │   (Claim   │ │
│  │   Session   │  │   Upload,   │  │   Store,    │  │   Brands,   │  │   Check)   │ │
│  │  Management │  │   History)  │  │   Search)   │  │   Persons)  │  │            │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │
│                                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                            Static Files & EJS Templates                          │ │
│  │  • design-system.css  • home.js  • notifications.js  • devices_manager.js       │ │
│  │  • styles.css         • app.js   • profiles.js       • file_upload_*.js         │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         │ HTTP/REST Proxy
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND API (FastAPI/Python)                            │
│                                    Port 8000                                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                              REST API Endpoints                                  │ │
│  │  POST /api/transcribe       - Transcribe audio with fact-checking               │ │
│  │  POST /api/transcribe/job   - Async transcription (background job)              │ │
│  │  GET  /api/jobs/{id}        - Check job status                                  │ │
│  │  POST /api/documents/upload - Upload documents for validation                   │ │
│  │  GET  /api/documents        - List stored documents                             │ │
│  │  POST /api/validate         - Validate claims against documents                 │ │
│  │  POST /api/profiles/*       - CRUD operations for profiles                      │ │
│  │  GET  /api/devices/status   - ESP32 device status                               │ │
│  │  POST /api/keys/generate    - Generate API keys for external access             │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           Bearer Token Authentication                            │ │
│  │  • API Key Generation & Validation                                              │ │
│  │  • Master Key for admin operations                                              │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                 CORE PROCESSING MODULES                              │
│                                    (src/ directory)                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐            │
│  │   AI Processing   │    │ Document Processing│    │  Validation       │            │
│  │   (src/ai/)       │    │  (src/documents/)  │    │  (src/validation/)│            │
│  │                   │    │                    │    │                   │            │
│  │  • llama_processor│    │  • processor.py    │    │  • claim_extractor│            │
│  │  • enhanced_      │    │  • vector_store.py │    │  • validator.py   │            │
│  │    processor      │    │  • schemas.py      │    │                   │            │
│  └─────────┬─────────┘    └─────────┬──────────┘    └─────────┬─────────┘            │
│            │                        │                         │                      │
│            ▼                        ▼                         ▼                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                           PROCESSING PIPELINE                                    │ │
│  │                                                                                  │ │
│  │   1. Audio Input ──▶ 2. Whisper Transcription ──▶ 3. Claim Extraction          │ │
│  │                                                          │                       │ │
│  │   4. Fact Checking ◀── Vector Search (Documents) ◀──────┘                       │ │
│  │          │                                                                       │ │
│  │          ▼                                                                       │ │
│  │   5. LLAMA Analysis ──▶ 6. Generate Brutal Honesty Response                     │ │
│  │                                                                                  │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                       │
│  ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐            │
│  │   Audio Module    │    │  Profile Manager  │    │  Database Layer   │            │
│  │   (src/audio/)    │    │  (src/profiles/)  │    │  (src/database/)  │            │
│  │                   │    │                    │    │                   │            │
│  │  • multi_device_  │    │  • profile_manager │    │  • manager.py     │            │
│  │    manager        │    │    - clients       │    │  • data_store.py  │            │
│  │  • unified_       │    │    - brands        │    │                   │            │
│  │    connector      │    │    - persons       │    │                   │            │
│  │  • omi_connector  │    │                    │    │                   │            │
│  └───────────────────┘    └───────────────────┘    └───────────────────┘            │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                 DATA STORAGE LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐            │
│  │   File System     │    │   Vector Database │    │   SQLite/Postgres │            │
│  │                   │    │      (Qdrant)     │    │                   │            │
│  │  • /recordings/   │    │                   │    │  • brutally_      │            │
│  │  • /documents/    │    │  • Document       │    │    honest.db      │            │
│  │  • /profiles/     │    │    embeddings     │    │  • User sessions  │            │
│  │  • /data/         │    │  • Similarity     │    │  • API keys       │            │
│  │    transcription_ │    │    search         │    │                   │            │
│  │    history.json   │    │                   │    │                   │            │
│  └───────────────────┘    └───────────────────┘    └───────────────────┘            │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                 EXTERNAL SERVICES                                    │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│  ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐            │
│  │  Whisper Model    │    │   LLAMA / Gemini  │    │   ESP32S3 Device  │            │
│  │   (Local/API)     │    │   (Local/API)     │    │   (BLE Audio)     │            │
│  │                   │    │                   │    │                   │            │
│  │  • Speech-to-text │    │  • Fact analysis  │    │  • PDM Microphone │            │
│  │  • Multi-language │    │  • Claim checking │    │  • Real-time      │            │
│  │    support        │    │  • Response       │    │    streaming      │            │
│  │                   │    │    generation     │    │                   │            │
│  └───────────────────┘    └───────────────────┘    └───────────────────┘            │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagrams

### 1. Recording & Transcription Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  User    │    │ Browser  │    │ Frontend │    │ Backend  │    │ Whisper  │
│ Records  │───▶│MediaRecorder│──▶│ server.js│──▶│api_server│──▶│  Model   │
│  Audio   │    │ API      │    │ :3001    │    │ :8000    │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                      │               │               │
                                      │               │               │
                                      ▼               ▼               ▼
                              ┌──────────┐    ┌──────────┐    ┌──────────┐
                              │  Save    │    │  Process │    │  Return  │
                              │ Recording│    │  Claims  │    │  Text    │
                              └──────────┘    └──────────┘    └──────────┘
                                                    │
                                                    ▼
                                             ┌──────────┐
                                             │ LLAMA    │
                                             │ Fact     │
                                             │ Check    │
                                             └──────────┘
                                                    │
                                                    ▼
                                             ┌──────────┐
                                             │ Return   │
                                             │ Analysis │
                                             │ + Claims │
                                             └──────────┘
```

### 2. Document Validation Flow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       Document Upload & Validation                        │
└──────────────────────────────────────────────────────────────────────────┘

   Upload Document              Process & Store              Use for Validation
        │                            │                              │
        ▼                            ▼                              ▼
┌──────────────┐           ┌──────────────┐              ┌──────────────┐
│  PDF/TXT/    │           │   Extract    │              │   Compare    │
│  DOCX File   │──────────▶│   Text &     │─────────────▶│   Claims vs  │
│              │           │   Chunk      │              │   Documents  │
└──────────────┘           └──────────────┘              └──────────────┘
                                  │                              │
                                  ▼                              ▼
                           ┌──────────────┐              ┌──────────────┐
                           │  Generate    │              │   Return     │
                           │  Embeddings  │              │   Validated  │
                           │  (Vector DB) │              │   Results    │
                           └──────────────┘              └──────────────┘
```

### 3. Claim Verification Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           CLAIM VERIFICATION PIPELINE                            │
└─────────────────────────────────────────────────────────────────────────────────┘

Input Text: "Een vis kan vliegen, een vis kan praten, een giraf heeft lange nek"
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │   CLAIM EXTRACTION  │
                            │   Split by , . en   │
                            └─────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            ▼                          ▼                          ▼
    ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
    │ Claim 1:      │          │ Claim 2:      │          │ Claim 3:      │
    │ "vis kan      │          │ "vis kan      │          │ "giraf heeft  │
    │  vliegen"     │          │  praten"      │          │  lange nek"   │
    └───────┬───────┘          └───────┬───────┘          └───────┬───────┘
            │                          │                          │
            ▼                          ▼                          ▼
    ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
    │ FACT CHECK    │          │ FACT CHECK    │          │ FACT CHECK    │
    │ Knowledge DB  │          │ Knowledge DB  │          │ Knowledge DB  │
    │ + Documents   │          │ + Documents   │          │ + Documents   │
    └───────┬───────┘          └───────┬───────┘          └───────┬───────┘
            │                          │                          │
            ▼                          ▼                          ▼
    ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
    │   NUANCED     │          │   INCORRECT   │          │   VERIFIED    │
    │   (partial)   │          │   (false)     │          │   (true)      │
    │               │          │               │          │               │
    │ Flying fish   │          │ Fish produce  │          │ Giraffes have │
    │ can glide     │          │ sounds but    │          │ longest neck  │
    │ 200m, not fly │          │ can't talk    │          │ (up to 2.4m)  │
    └───────────────┘          └───────────────┘          └───────────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       ▼
                            ┌─────────────────────┐
                            │   AGGREGATE RESULT  │
                            │   Credibility: 63%  │
                            │   2/4 verified      │
                            └─────────────────────┘
```

## Component Details

### Frontend Components (Node.js/Express - Port 3001)

| Component | File | Purpose |
|-----------|------|---------|
| Server | `server.js` | Express server, routing, auth, API proxy |
| Layout | `layout.ejs` | Main template with nav, footer |
| Home | `home.ejs` + `home.js` | Record/Upload/History/ESP32 tabs |
| Profiles | `profiles.ejs` + `profiles.js` | Client/Brand/Person management |
| Documents | `documents.ejs` | Document upload & management |
| Validation | `validation.ejs` | Claim validation interface |
| Design System | `design-system.css` | Unified styling, components |
| Notifications | `notifications.js` | Toast notification system |
| Device Manager | `devices_manager.js` | ESP32 BLE device handling |

### Backend Components (FastAPI/Python - Port 8000)

| Component | File | Purpose |
|-----------|------|---------|
| API Server | `api_server.py` | Main REST API endpoints |
| LLAMA Processor | `src/ai/llama_processor.py` | Fact checking, claim analysis |
| Enhanced Processor | `src/ai/enhanced_processor.py` | Advanced analysis |
| Document Processor | `src/documents/processor.py` | PDF/text extraction |
| Vector Store | `src/documents/vector_store.py` | Qdrant embeddings |
| Profile Manager | `src/profiles/profile_manager.py` | CRUD for profiles |
| Claim Extractor | `src/validation/claim_extractor.py` | Extract claims from text |
| Validator | `src/validation/validator.py` | Validate claims |

### Storage

| Storage Type | Location | Purpose |
|--------------|----------|---------|
| Recordings | `/recordings/` | Saved audio files |
| Documents | `/documents/` | Uploaded documents |
| Profiles | `/profiles/clients,brands,persons/` | Profile JSON files |
| History | `/data/transcription_history.json` | Transcription records |
| Database | `brutally_honest.db` | SQLite (users, keys) |
| Vector DB | Qdrant | Document embeddings |

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        NVIDIA Jetson / Cloud Server                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────┐        ┌────────────────────┐                   │
│  │    systemd         │        │    systemd         │                   │
│  │    brutally-       │        │    brutally-       │                   │
│  │    honest-frontend │        │    honest-api      │                   │
│  │    :3001           │        │    :8000           │                   │
│  └─────────┬──────────┘        └─────────┬──────────┘                   │
│            │                             │                               │
│            └─────────────┬───────────────┘                               │
│                          │                                               │
│                          ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                    Cloudflare Tunnel                                 ││
│  │                    ssh.brutallyhonest.io                            ││
│  │                    brutallyhonest.io                                ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                              Internet                                    │
│                                                                          │
│  Users access via: https://brutallyhonest.io                            │
│  SSH access via:   ssh.brutallyhonest.io                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack Summary

| Layer | Technology |
|-------|------------|
| Frontend | Node.js, Express, EJS, CSS |
| Backend | Python, FastAPI, Uvicorn |
| AI/ML | Whisper (STT), LLAMA/Gemini (Analysis) |
| Vector DB | Qdrant |
| Database | SQLite/PostgreSQL |
| Auth | Session-based (Frontend), Bearer Token (API) |
| Deployment | Systemd, Cloudflare Tunnel |
| Hardware | NVIDIA Jetson, ESP32S3 (BLE audio) |

---

*Document generated: November 28, 2025*
*Version: 6.2.0*

