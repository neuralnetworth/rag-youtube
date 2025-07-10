# RAG-YouTube

A modern RAG (Retrieval-Augmented Generation) system that builds searchable knowledge bases from YouTube channel videos. Features a FastAPI backend with real-time streaming responses and a clean web interface for asking questions about video content.

## 🚀 Quick Start

### ⚡ Super Quick Setup

```bash
# 1. Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup
git clone [your-repo] rag-youtube-channelname
cd rag-youtube-channelname
uv sync

# 3. Configure API keys
cp .env.sample .env
# Edit .env: add GOOGLE_API_KEY and OPENAI_API_KEY

# 4. Start the web interface
# Linux/macOS:
./run_fastapi.sh
# Windows PowerShell:
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
# Alternative (all platforms):
uv run uvicorn src.api.main:app --reload

# 5. Open http://localhost:8000 in your browser
```

### ✨ Key Features

**🎯 Modern FastAPI Implementation**
- ✅ Real-time streaming responses
- ✅ Clean, responsive web interface
- ✅ Direct OpenAI integration (no LangChain complexity)
- ✅ Sub-5 second response times

**💡 Smart & Simple**
- ✅ FAISS vector search (CPU-optimized)
- ✅ Source attribution with YouTube links
- ✅ Minimal dependencies
- ✅ Works with existing SpotGamma data

## 📚 Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[Documentation Index](docs/)** - Start here for all documentation
- **[FAISS-RAG Architecture](docs/faiss-rag/)** - Core system documentation
- **[Content Filtering Guide](docs/content-filtering/)** - Filtering system details
- **[Setup Guide](docs/faiss-rag/setup-guide.md)** - Detailed installation instructions

## 📁 Repository Structure

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
├── test/                  # ✅ Comprehensive test suite
│   ├── test_basic_functionality_fastapi.py  # ✅ Core FastAPI tests
│   ├── test_comprehensive.py                # ✅ Complete system validation
│   ├── test_pytest_core.py                  # ✅ Modern pytest-based tests
│   ├── test_performance.py                  # ✅ Performance benchmarking
│   ├── test_fastapi.py                      # API endpoint integration tests
│   ├── run_all_tests.py                     # Master test runner
│   ├── conftest.py                          # Pytest configuration
│   └── [legacy tests]                       # LangChain-based tests
├── docs/faiss-rag/        # ✅ Implementation documentation
├── captions/              # Downloaded video captions
├── db/                    # FAISS vector database
├── .env                   # API keys
└── rag-youtube.conf       # System configuration
```

## 🛠️ Setup Instructions

### Prerequisites

1. **UV Package Manager**: Install from https://docs.astral.sh/uv/
2. **YouTube Data API Key**: Get from Google Developer Console
3. **OpenAI API Key** (for Option 1) or **Ollama** (for Option 2)

### Option 1: Lightweight Setup (FAISS + OpenAI)

```bash
# 1. Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and configure
git clone [your-repo] rag-youtube-channelname
cd rag-youtube-channelname

# 3. Create virtual environment and install dependencies
uv sync

# 4. Configure API keys
cp .env.sample .env
# Edit .env: add GOOGLE_API_KEY and OPENAI_API_KEY

# 5. Verify configuration
# rag-youtube.conf should have:
# llm=openai
# openai_model=gpt-4.1-2025-04-14
# [Embeddings]
# model=openai:text-embedding-3-small
```

### Option 2: Full Setup (ChromaDB + Local)

```bash
# 1. Install with full dependencies (GPU support)
uv sync --extra full

# 2. Install Ollama (optional)
# Download from ollama.ai and pull models
ollama pull mistral:latest

# 3. Configure for local embeddings
# Edit rag-youtube.conf:
# [Embeddings]
# model=all-MiniLM-L6-v2
```

## 📊 Process Your YouTube Channel

### 1. List Channel Videos

```bash
# Get channel video list (using any video ID from the channel)
GOOGLE_API_KEY=your_key uv run python src/data_pipeline/list_videos.py VIDEO_ID_FROM_CHANNEL
```

### 2. Download Captions

```bash
# Download all video captions (may take 10+ minutes for large channels)
uv run python src/data_pipeline/download_captions.py
```

### 3. Fetch Playlist Data (Optional but Recommended)

```bash
# Retrieve playlist information for better filtering
GOOGLE_API_KEY=your_key uv run python src/data_pipeline/playlist_fetcher.py
```

### 4. Load Into Vector Database

```bash
# For FAISS setup (includes enhanced metadata)
uv run python src/data_pipeline/document_loader_faiss.py

# For ChromaDB setup  
uv run python src/legacy/document_loader.py
```

The document loader automatically:
- Infers video categories (daily updates, educational, interviews, special events)
- Calculates quality scores based on transcript density
- Associates videos with their YouTube playlists
- Tracks caption availability

## 🧪 Testing Your Setup

### ⚡ Quick Start Testing

```bash
# Essential test (fastest) - start here
./test_runner.sh quick

# Complete system validation with detailed reporting
./test_runner.sh full

# Performance benchmarks and load testing
./test_runner.sh performance

# Modern pytest-based tests
./test_runner.sh pytest --verbose
```

### 🎯 Comprehensive Test Suite

The project includes a modern, well-organized test suite with multiple categories:

#### **Core Tests (Production Ready)**
```bash
# Core FastAPI functionality
uv run python test/test_basic_functionality_fastapi.py

# Complete system validation (all components)
uv run python test/test_comprehensive.py

# Modern pytest-based tests with fixtures
uv run pytest test/test_pytest_core.py -v
```

#### **Performance & Integration**
```bash
# Performance benchmarking (response times, memory, concurrent users)
uv run python test/test_performance.py

# API integration tests (requires running server)
uv run python test/test_fastapi.py
```

#### **Test Categories**
- **🚀 Core FastAPI Tests**: Essential production functionality
- **🔬 Comprehensive Tests**: Complete system validation with detailed reporting  
- **⚡ Pytest Tests**: Modern test patterns with fixtures and markers
- **📊 Performance Tests**: Benchmarking and load testing
- **🌐 API Integration**: Endpoint testing (requires server)
- **🔧 Legacy Tests**: LangChain-based components

### 📋 Test Results Summary

**Current Status**: ✅ All 12 comprehensive tests PASSING (145s total)

- **Vector Store**: 26+ documents loaded and searchable
- **Multi-Provider LLM**: OpenAI + Gemini working with optimized parameters
- **Response Times**: Sub-5 seconds for Q&A, <1s for vector search
- **Streaming**: Real-time responses with <1s first token latency
- **Filtering**: Advanced document filtering by category, quality, captions
- **Error Handling**: Comprehensive edge cases and failure scenarios

### 🛠️ Development Testing

```bash
# Run specific test categories
uv run python test/run_all_tests.py --category "Core FastAPI Tests"

# Pytest with filtering (skip slow tests)
uv run pytest test/ -m "not slow" --tb=short

# Test-driven development
uv run pytest test/test_pytest_core.py -k "test_specific_feature" -v

# Full validation before deployment
./test_runner.sh all
```

See **[test/README.md](test/README.md)** for complete testing documentation.

## 🌐 Web Interface

**✅ Status**: Modern FastAPI web interface is complete and ready to use!

### Starting the Server
```bash
# Linux/macOS (quick start):
./run_fastapi.sh

# Windows PowerShell:
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Alternative (all platforms):
uv run uvicorn src.api.main:app --reload
```

### Access Points
- **Web UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **System Stats**: http://localhost:8000/api/stats

### Features
- ⚡ **Real-time streaming** responses
- 🎯 **Source attribution** with YouTube links
- 📱 **Responsive design** for mobile/desktop
- 🔍 **Example questions** for SpotGamma content
- ⚙️ **Configurable** search parameters
- 🎨 **Advanced filtering** by category, quality, playlist, and date

### Content Filtering

The web interface includes powerful filtering options to refine your searches:

#### Filter Types

1. **Caption Filter**
   - Toggle "Require captions" to only search videos with transcripts
   - Shows caption coverage (e.g., "192/341 videos")

2. **Category Filter**
   - Daily Updates: Market analysis and daily recaps
   - Educational: Tutorial and explainer content
   - Interviews: Conversations and discussions
   - Special Events: OPEX, earnings, major market events

3. **Quality Filter**
   - High: Dense technical content (120+ WPM, 5+ technical terms)
   - Medium: Moderate technical content (80+ WPM, 2+ technical terms)
   - Low: Basic content (40+ WPM)

4. **Playlist Filter**
   - Multi-select dropdown showing all channel playlists
   - Hold Ctrl/Cmd to select multiple playlists
   - Shows video count per playlist

5. **Date Range Filter**
   - Select start and end dates to filter by publication date
   - Shows available date range for the channel

#### Using Filters

1. **Apply Filters**: Select your desired filters before asking a question
2. **Clear Filters**: Click "Clear Filters" button to reset all selections
3. **Combine Filters**: All filters work together (AND logic)
4. **Performance**: Filters use 3x over-fetching to ensure quality results

## 📺 Multi-Channel Support

Create separate instances for different YouTube channels:

```bash
# Clone per channel approach (recommended)
workspace/
├── rag-youtube-spotgamma/      # Financial analysis channel
├── rag-youtube-educational/    # Educational content
└── rag-youtube-tech/          # Tech tutorials

# Each instance runs independently with its own:
# - videos.json and captions/
# - Vector database (db/)
# - Configuration (rag-youtube.conf)
# - Can run on different ports simultaneously
```

## 🔧 Configuration

Key configuration options in `rag-youtube.conf`:

```ini
[General]
llm=openai                    # ollama, openai
openai_model=gpt-4.1-2025-04-14   # GPT-4.1 recommended for RAG
port=5555                    # Web interface port

[Embeddings]
model=openai:text-embedding-3-small  # or all-MiniLM-L6-v2, nomic:...

[Search]
search_type=similarity       # similarity, mmr, similarity_score_threshold
document_count=5            # Number of documents to retrieve
chunk_size=1000            # Text chunk size for processing
```

### Model Selection Strategy

We switched from OpenAI o3 to GPT-4.1 for RAG synthesis tasks. The o3 model is optimized for complex reasoning but not ideal for generating conversational responses from retrieved content.

- **Current Choice**: GPT-4.1 for reliable answer generation from document context
- **Future Flexibility**: Architecture supports experimenting with different models for different pipeline stages
- **Comprehensive Analysis**: See `docs/model-strategy.md` for detailed model comparison and selection criteria

### LLM Parameter Optimization (2025)

The system uses optimal parameter handling based on extensive research into model-specific requirements and limitations.

#### Temperature Parameter Handling

**Key Finding**: Never use global temperature settings. Model defaults are optimal.

- **All Models**: Use native default temperatures (no global LLM_TEMPERATURE in .env)
- **OpenAI o3**: Temperature parameter NOT supported (causes API errors)
- **OpenAI GPT-4.1**: Supports temperature, default 1.0 is optimal
- **Google Gemini**: Supports temperature, model defaults work best
- **Override**: Only when explicitly requested by user per-request

#### Token Limit Optimization

**Key Finding**: Model-specific parameter handling prevents API errors.

- **Gemini Models**: NEVER set max_output_tokens (known API bug with 2.5 Pro)
- **OpenAI GPT-4.1**: Safe to use max_tokens parameter (default: unlimited)
- **OpenAI o3**: Use max_completion_tokens (NOT max_tokens)
- **Best Practice**: Let all models use their native defaults

#### Documentation

Comprehensive guides available:
- `docs/temperature-parameter-guide.md` - Temperature optimization research
- `docs/gemini-token-optimization.md` - Gemini-specific token handling
- `docs/openai-token-optimization.md` - OpenAI parameter comparison

This approach ensures maximum compatibility and performance across all supported LLM providers.

## 🔄 Migration Between Setups

Move from CPU (FAISS) to GPU (ChromaDB) setup:

```bash
# Migrate existing embeddings (preserves your work)
./src/migrate_faiss_to_chroma.py --source-dir db --target-dir db_chroma

# Update configuration to use local embeddings
# Update requirements.txt for ChromaDB dependencies
```

## 🎯 Current Status

### ✅ Production Ready Features
- **FastAPI Web Interface**: Modern, responsive UI with real-time streaming ⚡
- **SpotGamma Knowledge Base**: 341 videos processed, 192 with captions, 2,413 document chunks
- **FAISS Vector Store**: CPU-optimized, fast similarity search
- **OpenAI Integration**: GPT-4.1 for reliable answer generation
- **Source Attribution**: Direct YouTube links with relevance scores
- **Clean Dependencies**: No LangChain complexity, minimal requirements

### 🚀 Performance
- **Sub-5 second** response times
- **Real-time streaming** for immediate feedback
- **2,413 documents** searchable instantly
- **Mobile-friendly** responsive design

### 📊 Example Use Cases
Ask questions like:
- "What is gamma in options trading?"
- "How do gamma squeezes work?"
- "What does SpotGamma say about 0DTE options?"
- "Explain dealer gamma positioning"


## 🤝 Contributing

1. **Test First**: Run `uv run python test/test_basic_functionality_fastapi.py`
2. **Follow Patterns**: Use the clean FastAPI architecture in `src/api/`
3. **Add Tests**: Include tests for new features
4. **Update Docs**: Keep documentation current

## 🔧 Troubleshooting

### Common Issues

**Dependencies**: If `uv sync` fails, ensure you have Python 3.8+ and try:
```bash
rm -rf .venv && uv sync
```

**Server won't start**: Check that port 8000 is available:
```bash
lsof -i :8000  # Kill any processes using port 8000
```

**No answers**: Verify your OpenAI API key in `.env` and test with:
```bash
uv run python test/test_basic_functionality_fastapi.py
```

## 📚 Learn More

- **Test Documentation**: See `test/README.md`
- **FastAPI Migration**: See `docs/faiss-rag/` for the complete rewrite plan
  - `faiss-design.md` - System architecture
  - `faiss-feature.md` - Feature specifications
  - `faiss-implementation.md` - Step-by-step implementation guide
- **Model Selection**: See `docs/model-strategy.md` for comprehensive model comparison and selection criteria
- **Playlist Features**: See `docs/playlist/` for content organization plans
- **Development Guide**: See `CLAUDE.md` for Claude-specific instructions

---

Built for analyzing financial YouTube channels like SpotGamma, but adaptable to any content domain.