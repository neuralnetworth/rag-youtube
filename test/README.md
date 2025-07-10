# RAG-YouTube Test Suite

## Overview

Comprehensive test suite for the RAG-YouTube system covering all components from vector storage to multi-provider LLM integration. Tests are organized into categories with different complexity levels and dependencies.

## Test Categories

### 🚀 FastAPI Core Tests (Production Ready)
- **test_basic_functionality_fastapi.py** - ✅ Primary test suite for FastAPI implementation
- **test_filtering.py** - ✅ Document filtering and metadata enhancement tests
- **test_comprehensive.py** - ✅ Complete system test with detailed reporting
- **test_pytest_core.py** - ✅ Modern pytest-based core functionality tests

### 🌐 API Integration Tests
- **test_fastapi.py** - API endpoint tests (requires running server)
- **test_performance.py** - Performance benchmarks and load testing

### 🔧 Legacy Tests (LangChain-based)
- **test_basic_functionality.py** - Original LangChain implementation tests
- **test_minimal.py** - Minimal debugging tests
- **test_faiss_simple.py** - Simple vector store tests
- **test_vector_store.py** - Detailed vector store functionality
- **test_chains.py** - LangChain chain testing
- **test_agent_qa.py** - Agent-based Q&A tests
- **test_end_to_end.py** - End-to-end pipeline tests

### 🛠️ Test Infrastructure
- **conftest.py** - Pytest fixtures and configuration
- **run_all_tests.py** - Master test runner with category organization
- **test_helpers.py** - Utility functions for test setup
- **pytest.ini** - Pytest configuration

## Quick Start

### 1. Essential Test (Start Here)
```bash
# Test core FastAPI functionality
uv run python test/test_basic_functionality_fastapi.py
```

### 2. Full Modern Test Suite
```bash
# Run comprehensive tests
uv run python test/test_comprehensive.py

# Or use pytest for modern test runner
uv run pytest test/test_pytest_core.py -v
```

### 3. Master Test Runner
```bash
# Run all core tests (skips legacy and server tests)
uv run python test/run_all_tests.py --skip-legacy --skip-api

# Run specific category
uv run python test/run_all_tests.py --category "Core FastAPI Tests"

# List available categories
uv run python test/run_all_tests.py --list-categories
```

## Test Types and Usage

### Pytest Integration
```bash
# Install pytest if not available
uv add pytest --dev

# Run with pytest for modern features
uv run pytest test/test_pytest_core.py -v
uv run pytest test/ -m "not slow" --tb=short
uv run pytest test/ -k "test_vector" --verbose
```

### Performance Testing
```bash
# Comprehensive performance benchmarks
uv run python test/test_performance.py

# Memory usage and concurrent user testing included
```

### API Testing (Server Required)
```bash
# Start FastAPI server first
./run_fastapi.sh

# Then run API tests
uv run python test/test_fastapi.py
```

## Test Markers (Pytest)

- **@pytest.mark.slow** - Tests that take >10 seconds
- **@pytest.mark.api** - Tests requiring LLM API calls
- **@pytest.mark.server** - Tests requiring running FastAPI server
- **@pytest.mark.integration** - End-to-end integration tests

Filter tests with: `pytest -m "not slow"` or `pytest -m "api"`

## Current Status

### ✅ Production Ready Components
- **FastAPI Implementation**: Modern async architecture
- **Vector Store**: FAISS with 26+ documents (test data loaded)
- **Multi-Provider LLM**: OpenAI + Gemini support with proper parameter handling
- **Document Filtering**: Advanced filtering by category, quality, captions
- **Real-time Streaming**: Server-sent events for live responses

### 🧪 Test Coverage
- **Core Functionality**: 100% coverage of main RAG pipeline
- **Error Handling**: Comprehensive edge case testing
- **Performance**: Benchmarks for response time and concurrent users
- **Integration**: API endpoints and streaming functionality

### 📊 Performance Metrics (Current Test Data)
- **Database Size**: 26 documents (test video processed)
- **Query Response**: <5 seconds for most queries
- **Vector Search**: <1 second for similarity search
- **Streaming**: <1 second first token latency

### 🚧 Notes for Full Data
To test with complete SpotGamma dataset:
1. Run full data ingestion: `uv run python src/data_pipeline/download_captions.py`
2. Load into vector store: `uv run python src/data_pipeline/document_loader_faiss.py`
3. Expected: 341 videos → ~2,500 document chunks

## Development Workflow

### Adding New Tests
1. Use **test_pytest_core.py** as template for pytest-style tests
2. Add fixtures to **conftest.py** for shared setup
3. Use appropriate markers for test categorization
4. Update **run_all_tests.py** categories if needed

### Test-Driven Development
1. Write tests first in **test_pytest_core.py**
2. Run specific tests: `pytest -k "test_new_feature"`
3. Implement feature until tests pass
4. Add to comprehensive test suite

### Continuous Integration Ready
- All tests designed for CI/CD pipelines
- Proper error handling and timeouts
- Environment-aware test skipping
- Detailed reporting and categorization