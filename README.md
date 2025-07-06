# RAG-YouTube

A RAG (Retrieval-Augmented Generation) system that builds searchable knowledge bases from YouTube channel videos. Downloads captions, processes them with embeddings, and provides a web interface for asking questions about the content.

## 🚀 Quick Start

### ⚡ Super Quick Setup (New Computer)

```bash
# 1. Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and setup
git clone [your-repo] rag-youtube-channelname
cd rag-youtube-channelname
uv sync

# 3. Configure API keys
cp .env.sample .env
# Edit .env: add GOOGLE_API_KEY and OPENAI_API_KEY

# 4. Test it works
make test
```

### Choose Your Setup

**Option 1: Lightweight OpenAI + FAISS (Recommended for Prototyping)**
- ✅ No GPU required
- ✅ Minimal dependencies 
- ✅ Fast setup
- ✅ Cost-effective for small datasets

**Option 2: Full ChromaDB + Local Embeddings (Production)**
- ✅ Complete privacy
- ✅ GPU-optimized performance
- ✅ No API costs for embeddings
- ✅ Better for large datasets

## 📁 Repository Structure

```
rag-youtube/
├── src/                    # Core Python modules
│   ├── agent_*.py         # Agent implementations (FAISS + ChromaDB versions)
│   ├── chain_*.py         # LangChain processing chains
│   ├── vector_store_*.py  # Vector store implementations
│   ├── app*.py           # Web applications
│   └── utils/            # Utility functions
├── test/                  # Comprehensive test suite
│   ├── test_basic_functionality.py  # ✅ Working integration test
│   ├── test_suite.py              # Full test runner
│   └── README.md                  # Test documentation
├── static/               # Future FastAPI web interface
├── prompts/             # Customizable LLM prompts
├── docs/                # Documentation
│   ├── faiss-rag/      # FastAPI migration plans
│   └── playlist/       # Playlist features
├── captions/           # Downloaded video captions (created on first run)
├── db/                 # Vector database storage (created on first run)
├── .env                # API keys configuration
└── rag-youtube.conf    # System configuration
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
GOOGLE_API_KEY=your_key uv run python src/list_videos.py VIDEO_ID_FROM_CHANNEL
```

### 2. Download Captions

```bash
# Download all video captions (may take 10+ minutes for large channels)
uv run python src/download_captions.py
```

### 3. Load Into Vector Database

```bash
# For FAISS setup
uv run python src/document_loader_faiss.py

# For ChromaDB setup  
uv run python src/document_loader.py
```

## 🧪 Testing Your Setup

### Quick Verification

```bash
# Test basic functionality (recommended first test)
uv run python test/test_basic_functionality.py

# Run minimal vector search test
uv run python test/test_minimal.py

# Run comprehensive test suite
uv run python test/test_suite.py
```

### Expected Test Output

```
Found 3 relevant documents:
1. Introduction to Options Greeks (score: 0.572)
   Source: https://www.youtube.com/watch?v=MWxM0QWaUfU
   Preview: of the stock this is marked by the label ATM...

Answer: In options trading, gamma is the "Greek" that measures...
```

## 🌐 Web Interface

**Current Status**: The old Bottle.py web interface has been removed. A new FastAPI-based interface is planned.

**For Now**: Use the command-line interface for testing:
```bash
# Test basic functionality
uv run python test/test_basic_functionality.py

# Or activate environment and use directly
uv shell
python test/test_basic_functionality.py
```

**Future**: See `docs/faiss-rag/` for the complete FastAPI implementation plan.

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

## 🔄 Migration Between Setups

Move from CPU (FAISS) to GPU (ChromaDB) setup:

```bash
# Migrate existing embeddings (preserves your work)
./src/migrate_faiss_to_chroma.py --source-dir db --target-dir db_chroma

# Update configuration to use local embeddings
# Update requirements.txt for ChromaDB dependencies
```

## 🎯 Current Status

### ✅ Working Features
- **SpotGamma Channel**: 341 videos processed, 192 with captions loaded
- **FAISS Vector Store**: 2,413 document chunks indexed
- **OpenAI Integration**: Q&A with GPT-4.1 model working (fixed o3 issues)
- **Basic RAG Pipeline**: Question answering with source attribution
- **Test Suite**: Comprehensive testing framework
- **Dual Architecture**: CPU (FAISS) and GPU (ChromaDB) support

### 🔄 In Development
- **FastAPI Migration**: Moving from Bottle to FastAPI for better async support (see docs/faiss-rag/)
- **Playlist-Aware Filtering**: Enhanced content organization (see docs/playlist/)
- **Simplified Architecture**: Removing complex LangChain chains for direct API calls

### ⚠️ Known Issues
- **No Web Interface**: Old Bottle setup removed, FastAPI replacement planned
- **Solution**: Complete FastAPI implementation documented in docs/faiss-rag/

### 📋 Example Queries
- "What is gamma in options trading?"
- "How do gamma squeezes work?"
- "What does SpotGamma say about 0DTE options?"
- "Explain dealer gamma positioning"

## 🤝 Contributing

1. **Test First**: Run `python3 test/test_basic_functionality.py`
2. **Follow Patterns**: Use existing FAISS/ChromaDB dual architecture
3. **Add Tests**: Include tests for new features
4. **Update Docs**: Keep documentation current

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