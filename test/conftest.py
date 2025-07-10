"""
pytest configuration and fixtures for RAG-YouTube test suite.
"""
import pytest
import sys
import os
import asyncio
from typing import Generator, Any

# Add src to path for all tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.config import Config
from api.rag_engine import RAGEngine
from vector_stores.faiss import FAISSVectorStore
from data_pipeline.metadata_enhancer import MetadataEnhancer
from api.filters import DocumentFilter


@pytest.fixture(scope="session")
def config() -> Config:
    """Provide a Config instance for all tests."""
    return Config()


@pytest.fixture(scope="session")
def vector_store(config: Config) -> FAISSVectorStore:
    """Provide a FAISS vector store instance."""
    store = FAISSVectorStore(config)
    
    # Try to load existing index
    if os.path.exists('db/faiss.index'):
        store.load_index()
    else:
        pytest.skip("No FAISS index found - run document_loader_faiss.py first")
    
    return store


@pytest.fixture(scope="session")
def rag_engine(config: Config) -> RAGEngine:
    """Provide a RAG engine instance."""
    return RAGEngine(config)


@pytest.fixture
def metadata_enhancer() -> MetadataEnhancer:
    """Provide a metadata enhancer instance."""
    return MetadataEnhancer()


@pytest.fixture
def document_filter() -> DocumentFilter:
    """Provide a document filter instance."""
    return DocumentFilter()


@pytest.fixture
def sample_documents() -> list:
    """Provide sample documents for testing."""
    return [
        {
            'content': 'Daily market update content with gamma analysis',
            'score': 0.9,
            'metadata': {
                'title': 'Daily Market Update: SPY Levels',
                'url': 'https://www.youtube.com/watch?v=test1',
                'has_captions': True,
                'category': 'daily_update',
                'quality_score': 'high',
                'published_date': '2024-01-15',
                'duration': '00:15:30',
                'word_count': 2500
            }
        },
        {
            'content': 'Educational content about options Greeks',
            'score': 0.8,
            'metadata': {
                'title': 'Understanding Options Greeks',
                'url': 'https://www.youtube.com/watch?v=test2',
                'has_captions': False,
                'category': 'educational',
                'quality_score': 'medium',
                'published_date': '2024-01-20',
                'duration': '00:12:00',
                'word_count': 1800
            }
        },
        {
            'content': 'Interview with market maker about gamma',
            'score': 0.85,
            'metadata': {
                'title': 'Interview: Market Maker Insights',
                'url': 'https://www.youtube.com/watch?v=test3',
                'has_captions': True,
                'category': 'interview',
                'quality_score': 'high',
                'published_date': '2024-01-10',
                'duration': '00:25:00',
                'word_count': 4000
            }
        }
    ]


@pytest.fixture
def sample_metadata() -> dict:
    """Provide sample metadata for testing."""
    return {
        'title': 'Test Video Title',
        'description': 'Test description with gamma delta theta keywords',
        'duration': '00:10:00',
        'word_count': 1500,
        'has_captions': True,
        'published_date': '2024-01-15',
        'content': 'This is test content covering gamma delta theta vega implied volatility options trading concepts.'
    }


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Pytest markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "api: marks tests that require external API calls"
    )
    config.addinivalue_line(
        "markers", "server: marks tests that require a running server"
    )


# Pytest collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark slow tests
        if "slow" in item.name or "comprehensive" in item.name:
            item.add_marker(pytest.mark.slow)
        
        # Mark integration tests
        if "integration" in item.name or "end_to_end" in item.name:
            item.add_marker(pytest.mark.integration)
        
        # Mark API tests
        if "api" in item.name or "llm" in item.name:
            item.add_marker(pytest.mark.api)
        
        # Mark server tests
        if "fastapi" in item.name or "server" in item.name:
            item.add_marker(pytest.mark.server)


# Skip conditions
def pytest_runtest_setup(item):
    """Skip tests based on conditions."""
    # Skip server tests if no server is running
    if "server" in [mark.name for mark in item.iter_markers()]:
        try:
            import httpx
            import asyncio
            
            async def check_server():
                async with httpx.AsyncClient() as client:
                    response = await client.get("http://localhost:8000/api/health", timeout=2.0)
                    return response.status_code == 200
            
            if not asyncio.run(check_server()):
                pytest.skip("FastAPI server not running")
        except Exception:
            pytest.skip("Cannot check server status")
    
    # Skip API tests if no API keys
    if "api" in [mark.name for mark in item.iter_markers()]:
        if not (os.getenv('OPENAI_API_KEY') or os.getenv('GOOGLE_API_KEY')):
            pytest.skip("No API keys configured")


# Custom assertions
def assert_valid_source(source):
    """Assert that a source has required fields."""
    assert 'content' in source
    assert 'score' in source
    assert 'metadata' in source
    assert isinstance(source['score'], (int, float))
    assert len(source['content']) > 0


def assert_valid_rag_result(result):
    """Assert that a RAG result has required fields."""
    assert 'answer' in result
    assert 'sources' in result
    assert 'processing_time' in result
    assert len(result['answer']) > 0
    assert isinstance(result['sources'], list)
    assert isinstance(result['processing_time'], (int, float))
    
    for source in result['sources']:
        assert_valid_source(source)


# Make custom assertions available to all tests
pytest.assert_valid_source = assert_valid_source
pytest.assert_valid_rag_result = assert_valid_rag_result