# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

RAG-YouTube is a Python-based RAG (Retrieval-Augmented Generation) application that builds a knowledge base from YouTube channel videos. It downloads captions, processes them with embeddings, and provides a web interface for asking questions about the content.

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
GOOGLE_API_KEY=XXXX uv run python src/list_videos.py VIDEO_ID

# Download captions for all videos
uv run python src/download_captions.py

# Load documents into vector database
# For FAISS setup:
uv run python src/document_loader_faiss.py
# For ChromaDB setup:
uv run python src/document_loader.py
```

### Running the Application
```bash
# Web interface removed - use command line for now
# Test basic functionality
python3 test/test_basic_functionality.py

# Future FastAPI app (see docs/faiss-rag/)
# python3 src/main.py
```

### Database Operations
```bash
# Create monitoring database
make createdb

# Reset document loading (clears vector database)
make load

# Migrate from FAISS to ChromaDB (preserves embeddings)
./src/migrate_faiss_to_chroma.py --source-dir db --target-dir db_chroma
```

### Testing and Validation
```bash
# Test basic RAG functionality (recommended first test)
python3 test/test_basic_functionality.py

# Run minimal vector search test
python3 test/test_minimal.py

# Run comprehensive test suite
python3 test/test_suite.py

# Run benchmarks comparing different configurations
make compare
```

### Testing Approach
- **Primary test**: ALWAYS run `python3 test/test_basic_functionality.py` first
- **Focus on integration tests** - End-to-end RAG functionality is what matters
- **Test failures in unit tests are often interface mismatches, not functional issues**

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

- **Current Status**: Removed old Bottle.py + Vue.js setup
- **Future**: FastAPI backend with vanilla JavaScript frontend (see docs/faiss-rag/)
- **Database**: SQLite for monitoring and vector storage (FAISS/ChromaDB)

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
# Quick functionality test
uv run python test/test_basic_functionality.py

# Test vector search directly
uv run python test/test_minimal.py

# Run comprehensive test suite
uv run python test/test_suite.py
```

### Known Issues
- **RESOLVED: OpenAI o3 issues**: Fixed by switching to GPT-4.1 model (gpt-4.1-2025-04-14)
- **No Web Interface**: Old Bottle setup removed, FastAPI replacement ready for implementation
- **Chain interface mismatches**: `run()` vs `invoke()` method inconsistencies between FAISS and ChromaDB agents
- **Solution**: Complete FastAPI implementation documented in `docs/faiss-rag/`

## Development Notes

### File Structure
```
rag-youtube/
├── src/                    # Core Python modules
│   ├── *_faiss.py         # FAISS implementation (lightweight)
│   ├── *.py               # ChromaDB implementation (full-featured)
│   └── utils/             # Utility functions
├── test/                   # Test suite
│   ├── test_basic_functionality.py  # ✅ Main integration test
│   ├── test_suite.py              # Legacy unit tests
│   ├── test_ask.py               # Legacy web interface test
│   └── test_summary.md           # Test status documentation
├── docs/                   # Documentation
│   ├── faiss-rag/         # FastAPI migration plan
│   │   ├── faiss-design.md
│   │   ├── faiss-feature.md
│   │   └── faiss-implementation.md
│   ├── playlist/          # Playlist features
│   └── model-strategy.md  # Model selection analysis
├── prompts/               # Customizable LLM prompts
├── captions/              # Downloaded video captions (created during setup)
├── db/                    # Vector database storage (created during setup)
├── .env                   # API keys configuration
├── rag-youtube.conf       # System configuration
└── requirements.txt       # Dependencies (cleaned up)
```

### Dependencies
- Python 3.x with LangChain ecosystem
- OpenAI API for LLM and embeddings
- FAISS for vector storage (CPU-optimized)
- yt-dlp for video caption downloading
- Optional: ChromaDB for GPU-optimized deployments
- Optional: Ollama for local LLM inference

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
./src/migrate_faiss_to_chroma.py

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
./src/list_videos.py [VIDEO_ID]
./src/download_captions.py  # This may take time for large channels
./src/document_loader.py
./src/app.py
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