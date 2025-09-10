"""
Document Processing Module for Brutally Honest AI
Handles text extraction from various document formats (txt, pdf, doc, docx)
"""

import asyncio
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class DocumentInfo:
    """Information about a processed document"""
    id: str
    filename: str
    file_type: str
    content: str
    metadata: Dict[str, Any]
    upload_time: datetime
    file_size: int
    text_length: int
    hash: str

class DocumentProcessor:
    """Document processor for extracting text from various formats"""
    
    def __init__(self):
        self.supported_formats = {'.txt', '.pdf', '.doc', '.docx'}
        self.is_initialized = False
        
        # Check available libraries
        self.pdf_available = self._check_pdf_support()
        self.doc_available = self._check_doc_support()
        
    def _check_pdf_support(self) -> bool:
        """Check if PDF processing is available"""
        try:
            import PyPDF2
            return True
        except ImportError:
            try:
                import pdfplumber
                return True
            except ImportError:
                logger.warning("PDF support not available - install PyPDF2 or pdfplumber")
                return False
    
    def _check_doc_support(self) -> bool:
        """Check if DOC/DOCX processing is available"""
        try:
            import python_docx2txt
            return True
        except ImportError:
            try:
                from docx import Document
                return True
            except ImportError:
                logger.warning("DOC/DOCX support not available - install python-docx2txt or python-docx")
                return False
    
    async def initialize(self) -> bool:
        """Initialize the document processor"""
        try:
            logger.info("🔧 Initializing document processor...")
            
            # Log available formats
            available_formats = ['.txt']
            if self.pdf_available:
                available_formats.append('.pdf')
            if self.doc_available:
                available_formats.extend(['.doc', '.docx'])
            
            logger.info(f"📄 Supported formats: {', '.join(available_formats)}")
            
            self.is_initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize document processor: {e}")
            return False
    
    def _get_file_hash(self, content: bytes) -> str:
        """Generate SHA-256 hash of file content"""
        return hashlib.sha256(content).hexdigest()
    
    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode text file with any supported encoding")
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        if not self.pdf_available:
            raise ValueError("PDF processing not available")
        
        text = ""
        
        # Try pdfplumber first (better text extraction)
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                return text.strip()
        except ImportError:
            pass
        
        # Fallback to PyPDF2
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except ImportError:
            raise ValueError("No PDF processing library available")
    
    def _extract_text_from_doc(self, file_path: str) -> str:
        """Extract text from DOC/DOCX file"""
        if not self.doc_available:
            raise ValueError("DOC/DOCX processing not available")
        
        file_ext = Path(file_path).suffix.lower()
        
        # Try python-docx2txt first (simpler)
        try:
            import docx2txt
            text = docx2txt.process(file_path)
            if text and text.strip():
                return text.strip()
        except ImportError:
            pass
        
        # Fallback to python-docx (for DOCX only)
        if file_ext == '.docx':
            try:
                from docx import Document
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
                return text.strip()
            except ImportError:
                pass
        
        raise ValueError(f"Could not extract text from {file_ext} file")
    
    async def process_document(self, file_data: bytes, filename: str) -> DocumentInfo:
        """Process a document and extract text"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            # Get file extension
            file_ext = Path(filename).suffix.lower()
            if file_ext not in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            # Generate file hash and ID
            file_hash = self._get_file_hash(file_data)
            doc_id = f"doc_{file_hash[:16]}"
            
            # Save to temporary file for processing
            with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name
            
            try:
                # Extract text based on file type
                if file_ext == '.txt':
                    content = self._extract_text_from_txt(temp_path)
                elif file_ext == '.pdf':
                    content = self._extract_text_from_pdf(temp_path)
                elif file_ext in ['.doc', '.docx']:
                    content = self._extract_text_from_doc(temp_path)
                else:
                    raise ValueError(f"Unsupported file type: {file_ext}")
                
                # Clean and validate content
                content = content.strip()
                if not content:
                    raise ValueError("No text content found in document")
                
                # Create document info
                doc_info = DocumentInfo(
                    id=doc_id,
                    filename=filename,
                    file_type=file_ext,
                    content=content,
                    metadata={
                        'original_filename': filename,
                        'file_extension': file_ext,
                        'processing_method': 'text_extraction',
                        'content_preview': content[:200] + '...' if len(content) > 200 else content
                    },
                    upload_time=datetime.now(),
                    file_size=len(file_data),
                    text_length=len(content),
                    hash=file_hash
                )
                
                logger.info(f"✅ Processed document: {filename} ({len(content)} chars)")
                return doc_info
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Failed to process document {filename}: {e}")
            raise

# Global processor instance
_processor = None

async def get_document_processor() -> DocumentProcessor:
    """Get or create the global document processor"""
    global _processor
    if _processor is None:
        _processor = DocumentProcessor()
        await _processor.initialize()
    return _processor
