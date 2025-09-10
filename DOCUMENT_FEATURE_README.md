# Document Knowledge Base Feature

## Overview

The Brutally Honest AI system now includes a powerful document upload and AI-powered query feature. Users can upload documents (TXT, PDF, DOC, DOCX) which are processed, stored in a vector database, and made searchable using AI.

## Features

### 📄 Document Processing
- **Supported Formats**: TXT, PDF, DOC, DOCX
- **File Size Limit**: 10MB per document
- **Text Extraction**: Automatic text extraction from all supported formats
- **Smart Chunking**: Documents are split into overlapping chunks for better retrieval

### 🔍 Vector Search
- **Semantic Search**: Uses sentence-transformers for vector embeddings
- **Vector Database**: Qdrant for efficient similarity search
- **Intelligent Chunking**: 500-character chunks with 50-character overlap
- **High Accuracy**: Cosine similarity matching with configurable thresholds

### 🤖 AI Integration
- **LLAMA Integration**: Connects with existing LLAMA AI processor
- **Context-Aware Responses**: AI answers based on retrieved document content
- **Source Attribution**: Shows which documents were used for answers
- **Brutally Honest**: Maintains the system's signature honest AI responses

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

The following new dependencies are included:
- `qdrant-client==1.6.9` - Vector database client
- `sentence-transformers==2.2.2` - Text embeddings
- `PyPDF2==3.0.1` - PDF processing
- `pdfplumber==0.10.0` - Advanced PDF text extraction
- `python-docx==0.8.11` - DOCX processing
- `docx2txt==0.8` - DOC/DOCX text extraction

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

Required packages (already in package.json):
- `form-data` - For file upload handling
- `multer` - File upload middleware

## Usage

### 1. Start the Services

```bash
# Terminal 1: Start API server
python api_server.py

# Terminal 2: Start frontend server
cd frontend
npm start
```

### 2. Access the Document Feature

1. Open your browser to `http://localhost:3000`
2. Click the document icon (📄) next to "Brutally Honest AI" in the header
3. Or directly visit `http://localhost:3000/documents.html`

### 3. Upload Documents

1. **Drag & Drop**: Drag files directly onto the upload area
2. **Click to Upload**: Click the upload area to select files
3. **Multiple Files**: Upload multiple documents at once
4. **Progress Tracking**: Real-time upload progress with status updates

### 4. Query Documents

1. **Ask Questions**: Type questions in natural language
2. **AI Responses**: Get intelligent answers based on document content
3. **Source Attribution**: See which documents were used for the answer
4. **Relevance Scoring**: View similarity scores for source material

## API Endpoints

### Document Management

- `POST /documents/upload` - Upload and process documents
- `GET /documents/search?query=...&limit=5` - Search documents
- `POST /documents/query` - Query with LLAMA AI response
- `GET /documents/stats` - Get collection statistics
- `DELETE /documents/{document_id}` - Delete a document

### Example API Usage

```bash
# Upload a document
curl -X POST -F "file=@document.pdf" http://localhost:8000/documents/upload

# Search documents
curl "http://localhost:8000/documents/search?query=machine%20learning&limit=3"

# Query with AI
curl -X POST -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}' \
  http://localhost:8000/documents/query
```

## Architecture

### Backend Components

1. **Document Processor** (`src/documents/processor.py`)
   - Text extraction from multiple formats
   - File validation and preprocessing
   - Metadata generation

2. **Vector Store** (`src/documents/vector_store.py`)
   - Qdrant integration for vector storage
   - Sentence-transformers for embeddings
   - Semantic search and retrieval

3. **API Integration** (`api_server.py`)
   - RESTful endpoints for document operations
   - LLAMA AI integration for query responses
   - Error handling and validation

### Frontend Components

1. **Document UI** (`frontend/public/documents.html`)
   - Clean, consistent styling matching main app
   - Drag & drop file upload
   - Real-time query interface
   - Statistics dashboard

2. **Server Proxy** (`frontend/server.js`)
   - File upload handling with multer
   - API proxy to backend services
   - Error handling and cleanup

## Configuration

### Vector Database Settings

```python
# In src/documents/vector_store.py
CHUNK_SIZE = 500  # Characters per chunk
CHUNK_OVERLAP = 50  # Overlap between chunks
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # Sentence transformer model
VECTOR_SIZE = 384  # Embedding dimensions
```

### File Upload Limits

```python
# In api_server.py
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
SUPPORTED_FORMATS = {'.txt', '.pdf', '.doc', '.docx'}
```

## Testing

Run the test suite to verify the feature works:

```bash
python test_documents.py
```

The test covers:
- Document text extraction
- Vector storage and retrieval
- Semantic search functionality
- Collection statistics
- Document deletion

## Troubleshooting

### Common Issues

1. **PDF Processing Errors**
   ```bash
   pip install pdfplumber PyPDF2
   ```

2. **DOC/DOCX Processing Errors**
   ```bash
   pip install python-docx docx2txt
   ```

3. **Vector Database Issues**
   ```bash
   pip install qdrant-client sentence-transformers
   ```

4. **LLAMA Integration Issues**
   - Ensure Ollama is running: `ollama serve`
   - Or install llama-cpp-python for local models

### Performance Tips

1. **Large Documents**: Break into smaller files for better processing
2. **Memory Usage**: The vector database runs in-memory by default
3. **Search Quality**: Use specific, detailed queries for better results
4. **Upload Speed**: Smaller files upload and process faster

## Security Considerations

1. **File Validation**: Only supported file types are processed
2. **Size Limits**: 10MB maximum file size prevents abuse
3. **Content Scanning**: Text is extracted and stored, not original files
4. **Local Processing**: All processing happens locally, no external APIs

## Future Enhancements

- [ ] Persistent vector database storage
- [ ] Document versioning and updates
- [ ] Advanced metadata extraction
- [ ] OCR support for scanned documents
- [ ] Batch document processing
- [ ] Document categorization and tagging
- [ ] Export search results
- [ ] Document preview functionality

## Integration with Existing Features

The document feature seamlessly integrates with:
- **LLAMA AI Processor**: Uses existing AI infrastructure
- **Web Interface**: Consistent styling and navigation
- **API Architecture**: Follows established patterns
- **Error Handling**: Unified error reporting
- **Logging**: Comprehensive logging for debugging

This feature transforms Brutally Honest AI from an audio-focused system into a comprehensive knowledge management platform while maintaining its signature honest and direct AI responses.
