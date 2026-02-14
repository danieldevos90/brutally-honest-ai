"""
Pytest Configuration and Fixtures for Brutally Honest AI
"""

import pytest
import sys
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================
# ASYNC CONFIGURATION
# ============================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================
# API CLIENT FIXTURES
# ============================================

@pytest.fixture
async def async_client():
    """Async test client for FastAPI."""
    from httpx import AsyncClient, ASGITransport
    from api_server import app
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def sync_client():
    """Sync test client for FastAPI (for simpler tests)."""
    from fastapi.testclient import TestClient
    from api_server import app
    
    return TestClient(app)


# ============================================
# MOCK FIXTURES
# ============================================

@pytest.fixture
def mock_device_manager(mocker):
    """Mock device manager to avoid hardware dependencies."""
    mock_manager = MagicMock()
    mock_manager.scan_for_devices = AsyncMock(return_value=[])
    mock_manager.get_devices_list = MagicMock(return_value=[])
    mock_manager.connect_device = AsyncMock(return_value=True)
    mock_manager.disconnect_device = AsyncMock(return_value=True)
    mock_manager.disconnect_all = AsyncMock()
    mock_manager.active_device_id = None
    mock_manager.refresh_device_status = AsyncMock()
    
    mocker.patch('api_server.get_device_manager_instance', return_value=mock_manager)
    mocker.patch('api_server.get_device_manager', return_value=mock_manager)
    
    return mock_manager


@pytest.fixture
def mock_connector(mocker):
    """Mock ESP32 connector."""
    mock_conn = MagicMock()
    mock_conn.is_connected = True
    mock_conn.current_connection = MagicMock(value="usb")
    mock_conn.initialize = AsyncMock(return_value=True)
    mock_conn.disconnect = AsyncMock()
    mock_conn.get_device_status = AsyncMock(return_value=MagicMock(
        connected=True,
        recording=False,
        files=5,
        sd_card_present=True,
        ble_connected=False,
        free_ram=50000,
        device_info={"device_model": "ESP32S3", "port": "/dev/ttyUSB0"},
        battery_voltage=3.7,
        battery_percentage=85,
        battery_status="charging"
    ))
    mock_conn.get_recordings = AsyncMock(return_value=[])
    
    mocker.patch('api_server.get_connector', AsyncMock(return_value=mock_conn))
    
    return mock_conn


@pytest.fixture
def mock_processor(mocker):
    """Mock LLAMA processor."""
    mock_proc = MagicMock()
    mock_proc.process_audio = AsyncMock(return_value=MagicMock(
        success=True,
        transcription="Test transcription",
        analysis="Test analysis",
        summary="Test summary",
        sentiment="positive",
        keywords=["test", "audio"],
        fact_check="No issues found",
        brutal_honesty="Everything checks out",
        credibility_score=0.95,
        questionable_claims=[],
        corrections=[],
        confidence=0.9,
        processing_time=2.5,
        error=None
    ))
    
    mocker.patch('api_server.get_processor', AsyncMock(return_value=mock_proc))
    
    return mock_proc


@pytest.fixture
def mock_enhanced_processor(mocker):
    """Mock enhanced processor with document validation."""
    mock_proc = MagicMock()
    mock_proc.process_audio_with_validation = AsyncMock(return_value=MagicMock(
        success=True,
        transcription="Test transcription with validation",
        analysis="Test analysis",
        summary="Test summary",
        sentiment="positive",
        keywords=["test", "validation"],
        fact_check="Validated against documents",
        brutal_honesty="Matches knowledge base",
        credibility_score=0.98,
        questionable_claims=[],
        corrections=[],
        confidence=0.95,
        processing_time=3.0,
        document_validation={"status": "validated"},
        validation_score=0.98,
        fact_check_sources=["doc1.pdf"],
        contradictions=[],
        supporting_evidence=["Evidence from doc1"],
        error=None
    ))
    
    mocker.patch('api_server.get_enhanced_processor', AsyncMock(return_value=mock_proc))
    
    return mock_proc


@pytest.fixture
def mock_vector_store(mocker):
    """Mock vector store for document operations."""
    mock_store = MagicMock()
    mock_store.store_document = AsyncMock(return_value=True)
    mock_store.search_documents = AsyncMock(return_value=[])
    mock_store.get_collection_stats = AsyncMock(return_value={"total_chunks": 0})
    mock_store.delete_document = AsyncMock(return_value=True)
    
    mocker.patch('api_server.get_vector_store', AsyncMock(return_value=mock_store))
    
    return mock_store


@pytest.fixture
def mock_document_processor(mocker):
    """Mock document processor."""
    mock_proc = MagicMock()
    mock_proc.process_document = AsyncMock(return_value=MagicMock(
        id="test-doc-001",
        filename="test.pdf",
        file_type=".pdf",
        file_size=1024,
        text_length=500,
        upload_time=MagicMock(isoformat=lambda: "2024-01-01T00:00:00"),
        tags=[],
        context=None,
        category=None,
        related_documents=[],
        content="Test document content"
    ))
    
    mocker.patch('api_server.get_document_processor', AsyncMock(return_value=mock_proc))
    
    return mock_proc


# ============================================
# TEST DATA FIXTURES
# ============================================

@pytest.fixture
def sample_audio_data():
    """Generate sample WAV audio data."""
    import struct
    
    # Create a simple WAV header + silent audio
    sample_rate = 16000
    channels = 1
    bits_per_sample = 16
    duration_seconds = 1
    
    num_samples = sample_rate * duration_seconds
    data_size = num_samples * channels * (bits_per_sample // 8)
    
    # WAV header
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        36 + data_size,
        b'WAVE',
        b'fmt ',
        16,  # Subchunk1Size
        1,   # AudioFormat (PCM)
        channels,
        sample_rate,
        sample_rate * channels * bits_per_sample // 8,
        channels * bits_per_sample // 8,
        bits_per_sample,
        b'data',
        data_size
    )
    
    # Silent audio data
    audio_data = bytes(data_size)
    
    return header + audio_data


@pytest.fixture
def sample_transcription():
    """Sample transcription text for testing."""
    return """
    Hello, this is a test transcription.
    The company has over 100 employees.
    We are based in Amsterdam, Netherlands.
    Our revenue last year was 5 million euros.
    """


@pytest.fixture
def sample_claims():
    """Sample claims for validation testing."""
    return [
        {
            "id": "claim-001",
            "text": "The company has over 100 employees",
            "type": "fact",
            "transcription_id": "test-001",
            "timestamp": 5.0,
            "confidence": 0.9
        },
        {
            "id": "claim-002",
            "text": "We are based in Amsterdam, Netherlands",
            "type": "fact",
            "transcription_id": "test-001",
            "timestamp": 10.0,
            "confidence": 0.95
        },
        {
            "id": "claim-003",
            "text": "Our revenue last year was 5 million euros",
            "type": "statistic",
            "transcription_id": "test-001",
            "timestamp": 15.0,
            "confidence": 0.85
        }
    ]


@pytest.fixture
def auth_headers():
    """Generate valid auth headers for testing."""
    # This uses the internal bypass for localhost
    return {"X-Forwarded-For": "127.0.0.1"}


@pytest.fixture
def api_key_headers():
    """Generate API key headers for external testing."""
    import os
    api_key = os.environ.get("TEST_API_KEY", "bh_test_key_for_testing_only")
    return {"Authorization": f"Bearer {api_key}"}


# ============================================
# CLEANUP FIXTURES
# ============================================

@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for test files."""
    test_dir = tmp_path / "test_data"
    test_dir.mkdir()
    yield test_dir
    # Cleanup is automatic with tmp_path


@pytest.fixture(autouse=True)
def reset_api_keys():
    """Reset API keys state before each test."""
    yield
    # Could reset api_keys dict here if needed


# ============================================
# PARAMETRIZE HELPERS
# ============================================

def audio_formats():
    """Return list of supported audio formats for parametrization."""
    return [".wav", ".mp3", ".m4a", ".ogg", ".flac", ".webm", ".mp4"]


def document_formats():
    """Return list of supported document formats for parametrization."""
    return [".txt", ".pdf", ".doc", ".docx"]
