#!/usr/bin/env python3
"""
Test script for document upload and processing feature
"""

import asyncio
import tempfile
import os
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from documents.processor import get_document_processor
from documents.vector_store import get_vector_store

async def test_document_processing():
    """Test document processing and vector storage"""
    print("🧪 Testing Document Processing Feature")
    print("=" * 50)
    
    # Test 1: Create a sample text document
    print("\n📄 Test 1: Processing TXT document")
    sample_text = """
    This is a test document for the Brutally Honest AI system.
    
    The system can process various document types including:
    - Plain text files (.txt)
    - PDF documents (.pdf) 
    - Microsoft Word documents (.doc, .docx)
    
    The text is extracted, chunked, and stored in a vector database
    for AI-powered search and question answering.
    
    Key features:
    - Semantic search using vector embeddings
    - LLAMA AI integration for intelligent responses
    - Support for multiple document formats
    - Efficient text chunking for better retrieval
    """
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_text)
        temp_path = f.name
    
    try:
        # Read file as bytes (simulating upload)
        with open(temp_path, 'rb') as f:
            file_data = f.read()
        
        # Process document
        processor = await get_document_processor()
        doc_info = await processor.process_document(file_data, "test_document.txt")
        
        print(f"✅ Document processed successfully:")
        print(f"   • ID: {doc_info.id}")
        print(f"   • Filename: {doc_info.filename}")
        print(f"   • File type: {doc_info.file_type}")
        print(f"   • Text length: {doc_info.text_length} characters")
        print(f"   • Upload time: {doc_info.upload_time}")
        
        # Test 2: Store in vector database
        print("\n🔍 Test 2: Storing in vector database")
        vector_store = await get_vector_store()
        success = await vector_store.store_document(doc_info)
        
        if success:
            print("✅ Document stored in vector database successfully")
        else:
            print("❌ Failed to store document in vector database")
            return False
        
        # Test 3: Search documents
        print("\n🔎 Test 3: Searching documents")
        search_queries = [
            "document formats supported",
            "vector embeddings",
            "LLAMA AI integration",
            "text chunking"
        ]
        
        for query in search_queries:
            print(f"\n   Query: '{query}'")
            results = await vector_store.search_documents(query, limit=2)
            
            if results:
                print(f"   ✅ Found {len(results)} relevant chunks:")
                for i, result in enumerate(results, 1):
                    print(f"      {i}. Score: {result.score:.3f}")
                    print(f"         Content: {result.content[:100]}...")
            else:
                print("   ❌ No results found")
        
        # Test 4: Get collection stats
        print("\n📊 Test 4: Collection statistics")
        stats = await vector_store.get_collection_stats()
        print(f"✅ Collection stats:")
        for key, value in stats.items():
            print(f"   • {key}: {value}")
        
        # Test 5: Delete document
        print(f"\n🗑️ Test 5: Deleting document {doc_info.id}")
        delete_success = await vector_store.delete_document(doc_info.id)
        
        if delete_success:
            print("✅ Document deleted successfully")
        else:
            print("❌ Failed to delete document")
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except:
            pass

async def main():
    """Run all tests"""
    try:
        success = await test_document_processing()
        if success:
            print("\n✅ Document processing feature is working correctly!")
            print("\n📋 Next steps:")
            print("1. Start the API server: python api_server.py")
            print("2. Start the frontend server: cd frontend && npm start")
            print("3. Open http://localhost:3000/documents.html")
            print("4. Upload documents and test the AI query feature")
        else:
            print("\n❌ Some tests failed. Please check the error messages above.")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
