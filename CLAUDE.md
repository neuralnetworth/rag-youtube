# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

RAG-YouTube is a modern Python-based RAG (Retrieval-Augmented Generation) application that builds searchable knowledge bases from YouTube channel videos. It features a FastAPI backend with real-time streaming responses and a clean web interface for asking questions about video content.

## Development Commands

### Setup and Installation

#### Option 1: Lightweight OpenAI + FAISS Setup (No GPU Required)
```bash
# Install UV package manager first
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and create virtual environment
uv sync

# Configure for OpenAI in rag-youtube.conf:
# llm=openai
# openai_model=gpt-4.1-2025-04-14
# [Embeddings]
# model=openai:text-embedding-3-small
```

#### Option 2: Full ChromaDB + Local Embeddings Setup (GPU Recommended)
```bash
# Install with full dependencies (includes ChromaDB, torch, etc.)
uv sync --extra full

# Configure for local embeddings in rag-youtube.conf:
# [Embeddings]
# model=all-MiniLM-L6-v2
```

### Data Preparation
```bash
# List videos from a YouTube channel (requires GOOGLE_API_KEY)
GOOGLE_API_KEY=XXXX uv run python src/data_pipeline/list_videos.py VIDEO_ID

# Download captions for all videos
uv run python src/data_pipeline/download_captions.py

# Load documents into vector database
# For FAISS setup:
uv run python src/data_pipeline/document_loader_faiss.py
# For ChromaDB setup:
uv run python src/legacy/document_loader.py
```

### Running the Application
```bash
# Start FastAPI web interface
# Linux/macOS:
./run_fastapi.sh
# Windows PowerShell:
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
# Alternative (all platforms):
uv run uvicorn src.api.main:app --reload

# Access at http://localhost:8000
# API docs at http://localhost:8000/docs

# Test basic functionality
uv run python test/test_basic_functionality_fastapi.py
```

### Database Operations
```bash
# Create monitoring database
make createdb

# Reset document loading (clears vector database)
make load

# Migrate from FAISS to ChromaDB (preserves embeddings)
./src/vector_stores/migrate_faiss_to_chroma.py --source-dir db --target-dir db_chroma
```

### Testing and Validation
```bash
# Test FastAPI implementation (recommended first test)
uv run python test/test_basic_functionality_fastapi.py

# Test API endpoints (requires server running)
uv run python test/test_fastapi.py

# Legacy tests (require LangChain dependencies)
# uv sync --extra legacy
# uv run python test/test_basic_functionality.py
```

### Testing Approach
- **Primary test**: ALWAYS run `uv run python test/test_basic_functionality_fastapi.py` first
- **Focus on integration tests** - End-to-end RAG functionality is what matters
- **FastAPI tests verify**: API endpoints, streaming, source attribution
- **Legacy tests available** but require additional dependencies

## Architecture

### Core Components

- **Agent System**: Modular agent architecture with base classes and specialized implementations
  - `AgentBase`: Base functionality for all agents (ChromaDB version)
  - `agent_base_faiss.py`: Lightweight FAISS alternative for OpenAI-only setups
  - `AgentQA`: Question-answering agent with retrieval capabilities
  - `AgentEval`: Evaluation and benchmarking agent

- **Chain System**: LangChain-based processing chains for different conversation types
  - `ChainBase`: Base chain functionality and parameter management
  - `chain_qa_base.py`: Basic Q&A chain
  - `chain_qa_sources.py`: Q&A with source citations
  - `chain_qa_conversation.py`: Conversational memory-enabled chain

- **Data Pipeline**: Video processing and knowledge base construction
  - `list_videos.py`: YouTube API integration for channel video discovery
  - `download_captions.py`: Caption/subtitle downloading via yt-dlp
  - `document_loader.py`: Vector database ingestion and chunking

### Web Interface

- **Current Status**: ✅ Modern FastAPI backend with vanilla JavaScript frontend
- **Features**: Real-time streaming, responsive design, source attribution
- **API**: RESTful endpoints with OpenAPI documentation
- **Database**: SQLite for monitoring and FAISS for vector storage

### Configuration System

- Configuration via `rag-youtube.conf` file (copy from `rag-youtube.sample.conf`)
- Supports multiple LLM providers: Ollama (default), OpenAI
- Configurable embeddings: HuggingFace Sentence Transformers (default), OpenAI, Nomic, Ollama
- Adjustable retrieval parameters: chunk size, search type, document count, score thresholds

### Key Features

- **Multi-LLM Support**: Seamless switching between Ollama and OpenAI models
- **Flexible Retrieval**: Multiple search types (similarity, MMR, score threshold)
- **Chain Types**: Basic, sources-enabled, and conversational modes
- **Memory Management**: Buffer, windowed buffer, and summary memory types
- **Custom Prompts**: Editable prompts in `prompts/` directory
- **Evaluation**: Built-in benchmarking and comparison tools
- **Monitoring**: Dashboard for analyzing processing chains and performance

## Current Working State

### SpotGamma Implementation Status
- ✅ **341 SpotGamma videos** listed from channel
- ✅ **192 videos with captions** downloaded and processed
- ✅ **2,413 document chunks** indexed in FAISS vector store
- ✅ **OpenAI GPT-4.1 integration** working (switched from o3 for better RAG performance)
- ✅ **Basic Q&A pipeline** functional with source attribution
- ✅ **Test suite** covering vector store, agent QA, and end-to-end functionality

### Known Working Commands
```bash
# Start web interface
./run_fastapi.sh

# Test FastAPI implementation
uv run python test/test_basic_functionality_fastapi.py

# Test API endpoints
uv run python test/test_fastapi.py

# Access web UI
# http://localhost:8000
```

### Status: ✅ COMPLETE
- **✅ FastAPI Web Interface**: Modern, responsive UI with real-time streaming
- **✅ Clean Dependencies**: No LangChain complexity, minimal requirements
- **✅ Production Ready**: Sub-5 second response times, 2,413 documents indexed
- **✅ Source Attribution**: Direct YouTube links with relevance scores

## Development Notes

### File Structure
```
rag-youtube/
├── src/                    # ✅ Organized Python modules
│   ├── api/               # ✅ FastAPI implementation (production)
│   │   ├── main.py        # FastAPI application
│   │   ├── rag_engine.py  # Simplified RAG logic
│   │   ├── models.py      # Pydantic schemas  
│   │   └── config_fastapi.py # API configuration
│   ├── core/              # ✅ Shared utilities
│   │   ├── config.py      # System configuration
│   │   ├── consts.py      # Constants
│   │   ├── utils.py       # Utility functions
│   │   └── database.py    # Database operations
│   ├── data_pipeline/     # ✅ Data ingestion scripts
│   │   ├── list_videos.py # YouTube video discovery
│   │   ├── download_captions.py # Caption downloading
│   │   ├── downloader.py  # yt-dlp wrapper
│   │   └── document_loader_faiss.py # FAISS loading
│   ├── vector_stores/     # ✅ Vector store implementations
│   │   ├── faiss.py       # FAISS vector store
│   │   └── migrate_faiss_to_chroma.py # Migration utility
│   └── legacy/            # Legacy LangChain implementations
│       ├── agents/        # LangChain agents
│       ├── chains/        # LangChain chains
│       └── document_loader.py # ChromaDB loader
├── static/                # ✅ Web interface
│   ├── index.html         # Main UI
│   ├── style.css          # Styling
│   └── app.js             # Frontend logic with streaming
├── test/                  # Test suite
│   ├── test_basic_functionality_fastapi.py  # ✅ FastAPI tests
│   ├── test_fastapi.py    # API endpoint tests
│   └── [legacy tests]     # LangChain-based tests
├── docs/faiss-rag/        # ✅ Implementation completed
├── captions/              # Downloaded video captions
├── db/                    # FAISS vector database
├── .env                   # API keys configuration
├── rag-youtube.conf       # System configuration
└── pyproject.toml         # Dependencies (cleaned up)
```

### Dependencies
- Python 3.x with FastAPI ecosystem
- OpenAI API for LLM and embeddings
- FAISS for vector storage (CPU-optimized)  
- yt-dlp for video caption downloading
- FastAPI, uvicorn, sse-starlette for web interface
- Optional: Legacy LangChain dependencies for backward compatibility

### Configuration
The system uses a hierarchical configuration approach where runtime parameters can override config file settings, enabling dynamic experimentation through the web interface.

### Model Selection Strategy
We've implemented a flexible model selection approach documented in `docs/model-strategy.md`:

- **Current Setup**: OpenAI GPT-4.1 for RAG synthesis tasks (switched from o3)
- **Reasoning Models**: Use o3 for complex analysis and verification tasks
- **Generative Models**: Use GPT-4.1 for answer synthesis from retrieved content
- **Cost Optimization**: Use GPT-4.1 Mini for summarization tasks
- **Future Experimentation**: Architecture supports multi-model pipelines

### Model Selection Critical Rules
- **NEVER use OpenAI o3 for RAG synthesis** - It's a reasoning model, not generative
- **ALWAYS use GPT-4.1** (gpt-4.1-2025-04-14) for answer generation
- **Parameter compatibility**: GPT-4.1 uses `max_tokens`, o3 uses `max_completion_tokens`
- **Verify changes** with `test_basic_functionality.py` after model modifications

## Dual Setup Support

This codebase supports two deployment modes:

### 1. Lightweight Setup (CPU-friendly)
- Uses OpenAI for both LLM and embeddings
- FAISS for vector storage (no GPU required)
- Minimal dependencies
- Perfect for development/prototyping

### 2. Full Setup (GPU-optimized)
- ChromaDB for vector storage
- Local embeddings (HuggingFace/Sentence Transformers)
- Can use Ollama for local LLM
- Better for production/privacy-sensitive deployments

### Migration Between Setups
Use the provided migration script to preserve embeddings when switching:
```bash
# From FAISS to ChromaDB (when moving to GPU machine)
./src/vector_stores/migrate_faiss_to_chroma.py

# Update config after migration
# Set embeddings model back to local model
# Update db_persist_dir if needed
```

## Working with Multiple YouTube Channels

RAG-YouTube is designed to create knowledge bases from YouTube channels. To work with multiple channels separately, the recommended approach is to use separate repository clones.

### Multi-Channel Architecture

```
workspace/
├── rag-youtube-spotgamma/      # SpotGamma financial analysis
├── rag-youtube-educational/    # Educational content
└── rag-youtube-tech/          # Tech tutorials
```

Each instance:
- Has its own video list, captions, and vector database
- Can run on different ports simultaneously
- Maintains complete data isolation
- Can use different LLM/embedding configurations

### Setting Up a New Channel

```bash
# 1. Clone with descriptive name
git clone [repo-url] rag-youtube-channelname

# 2. Configure the instance
cd rag-youtube-channelname
cp .env.sample .env
# Edit .env with your API keys

# 3. (Optional) Change port for parallel operation
# Edit rag-youtube.conf: port=5556

# 4. Process the channel
./src/data_pipeline/list_videos.py [VIDEO_ID]
./src/data_pipeline/download_captions.py  # This may take time for large channels
./src/data_pipeline/document_loader_faiss.py
./run_fastapi.sh
```

### Important Notes

- **Caption Download Time**: Downloading captions for hundreds of videos can take significant time (10+ minutes for 300+ videos)
- **Storage**: Each channel's captions are saved permanently in `captions/` folder
- **One-Time Investment**: Captions are downloaded once and reused; the script skips already-downloaded videos
- **Video IDs**: Captions are saved by video ID, preventing conflicts even if mixed in one folder

## FastAPI Migration Plan

The current Bottle + Vue.js web interface has significant compatibility issues with LangChain and modern async patterns. A complete rewrite using FastAPI is documented in `docs/faiss-rag/`:

### Migration Overview
1. **Read the documentation first**:
   - `docs/faiss-rag/faiss-design.md` - System architecture and technology decisions
   - `docs/faiss-rag/faiss-feature.md` - Feature specifications and UI mockups
   - `docs/faiss-rag/faiss-implementation.md` - Complete implementation guide with code

2. **Key improvements**:
   - Native async/await support for better performance
   - Direct FAISS integration without complex LangChain chains
   - Simple vanilla JavaScript frontend (no Vue.js complexity)
   - Proper error handling and streaming responses
   - Clean separation of concerns

3. **Implementation approach**:
   - Start with `src/rag_engine.py` for core RAG logic
   - Implement `src/main.py` with FastAPI endpoints
   - Create simple HTML/JS frontend in `static/`
   - Reuse existing FAISS index and metadata

### Development Approach
- **Core RAG**: Fully functional with command-line testing
- **FastAPI Web Interface**: Ready for implementation using `docs/faiss-rag/`
- **Test First**: Always run `python3 test/test_basic_functionality.py` to verify RAG functionality

### Common Pitfalls to Avoid
- ❌ Using o3 for RAG synthesis (returns empty responses)
- ❌ Using Bottle.py (removed - use FastAPI)
- ❌ Overly complex LangChain chain orchestration

### How to Know It's Working
- ✅ `test_basic_functionality.py` passes
- ✅ Returns complete answers with sources
- ✅ Sub-5-second response times
- ✅ Relevant document retrieval