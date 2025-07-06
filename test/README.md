# RAG-YouTube Test Suite

## Overview

This directory contains comprehensive tests for the FAISS-based RAG system.

## Test Files

### Core Tests
- **test_suite.py** - Main test runner that executes all tests
- **test_vector_store.py** - Tests FAISS vector store functionality
- **test_agent_qa.py** - Tests AgentQA with various configurations
- **test_chains.py** - Tests chain parameters and configurations  
- **test_end_to_end.py** - End-to-end tests with real SpotGamma data

### Working Tests
- **test_basic_functionality.py** - ✅ Functional test demonstrating working RAG
- **test_minimal.py** - ✅ Minimal test for debugging
- **test_faiss_simple.py** - ✅ Simple vector store test

### Utility Files
- **test_helpers.py** - Helper functions for test configuration
- **run_tests.sh** - Bash script to run all tests
- **compare.py** - Existing benchmark comparison tool

## Running Tests

### Quick Test (Recommended)
```bash
# From project root
python3 test/test_basic_functionality.py
```

### Full Test Suite
```bash
# From project root  
python3 test/test_suite.py
```

### Individual Tests
```bash
# From project root
python3 test/test_vector_store.py
python3 test/test_minimal.py
```

## Test Results Summary

### ✅ Working Components
- **Vector Store**: FAISS index with 2,413 documents loaded
- **Document Retrieval**: Accurate similarity search with scores
- **Basic Q&A**: Successfully answers questions about gamma, 0DTE options
- **Source Attribution**: Returns relevant YouTube video sources

### ⚠️ Known Issues
- **OpenAI o3 Constraints**: No temperature parameter support
- **Chain Interface Mismatch**: Some chain classes need `run()` vs `invoke()` methods
- **Parameter Mismatches**: `chain` vs `chain_type` property inconsistencies

### 📊 Performance Metrics
- **Database Size**: 2,413 SpotGamma video chunks indexed
- **Query Response**: Sub-5 second responses for most queries
- **Relevance**: High-quality results for financial options trading queries

## Next Steps

1. **Start Web Application**: Test browser-based interface
2. **Fix Chain Interfaces**: Resolve `run()` vs `invoke()` method mismatches  
3. **Integration Testing**: Test full pipeline with web interface
4. **Performance Optimization**: Optimize for production deployment