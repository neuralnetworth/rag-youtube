# RAG-YouTube Documentation

Welcome to the comprehensive documentation for RAG-YouTube, a modern RAG (Retrieval-Augmented Generation) system for YouTube content.

## 📚 Documentation Structure

### Core System Documentation

#### 1. [FAISS-RAG Foundation](faiss-rag/)
The foundational vector search and RAG architecture.

- **[Overview](faiss-rag/README.md)** - What is FAISS-RAG and how it works
- **[Architecture](faiss-rag/architecture.md)** - Deep technical dive into components
- **[Setup Guide](faiss-rag/setup-guide.md)** - Detailed installation instructions

#### 2. [Content Filtering System](content-filtering/)
Advanced filtering capabilities built on top of FAISS-RAG.

- **[Overview](content-filtering/overview.md)** - Architecture and filter types
- **[User Guide](content-filtering/user-guide.md)** - How to use filters effectively
- **[Implementation Guide](content-filtering/implementation-guide.md)** - Development details
- **[Technical Reference](content-filtering/technical-reference.md)** - API and configuration

#### 3. [Playlist Filtering](playlist-filtering/)
YouTube playlist integration for content organization.

- **[Implementation Summary](playlist-filtering/implementation-summary.md)** - What was built
- **[Testing Checklist](playlist-filtering/testing-checklist.md)** - Validation guide

## 🚀 Quick Start Guides

### For Users

1. **Getting Started**
   - Read the main [README](../README.md) for quick setup
   - Follow the [FAISS-RAG Setup Guide](faiss-rag/setup-guide.md) for detailed installation
   - Review the [Content Filtering User Guide](content-filtering/user-guide.md) for search tips

2. **Using the System**
   - Start with basic questions
   - Apply filters to refine results
   - Use playlist filters for specific content series

### For Developers

1. **Understanding the Architecture**
   - Start with [FAISS-RAG Overview](faiss-rag/README.md)
   - Deep dive into [Architecture Details](faiss-rag/architecture.md)
   - Understand [Content Filtering](content-filtering/overview.md)

2. **Extending the System**
   - Review [Implementation Guides](content-filtering/implementation-guide.md)
   - Check [Technical References](content-filtering/technical-reference.md)
   - Follow established patterns

## 📖 Reading Order

### New to RAG-YouTube?

1. [Main README](../README.md) - Project overview
2. [FAISS-RAG Overview](faiss-rag/README.md) - Core system understanding
3. [User Guide](content-filtering/user-guide.md) - How to use filters

### Setting Up a New Instance?

1. [Setup Guide](faiss-rag/setup-guide.md) - Complete installation
2. [Configuration Reference](content-filtering/technical-reference.md#configuration) - Fine-tuning
3. [Testing Checklist](playlist-filtering/testing-checklist.md) - Verification

### Contributing or Extending?

1. [Architecture Deep Dive](faiss-rag/architecture.md) - Technical foundation
2. [Implementation Guide](content-filtering/implementation-guide.md) - Development patterns
3. [CLAUDE.md](../CLAUDE.md) - AI assistant instructions

## 🔍 Feature Documentation

### Vector Search & RAG
- Semantic search using FAISS
- OpenAI embeddings (text-embedding-3-small)
- GPT-4.1 for answer generation
- Source attribution with YouTube links

### Content Filtering
- Caption availability filtering
- Category inference (daily updates, educational, interviews, special events)
- Quality scoring based on transcript density
- Date range filtering
- Playlist-based filtering

### Web Interface
- Real-time streaming responses
- Dark mode support
- Responsive design
- Filter statistics
- Example questions

## 🛠️ Technical Stack

- **Backend**: FastAPI (Python)
- **Vector Store**: FAISS
- **LLM**: OpenAI GPT-4.1
- **Embeddings**: OpenAI text-embedding-3-small
- **Frontend**: Vanilla JavaScript
- **Package Manager**: UV

## 📊 System Capabilities

- **Document Capacity**: 2,500+ chunks tested
- **Response Time**: < 5 seconds typical
- **Concurrent Users**: Async architecture
- **Filter Performance**: < 50ms overhead

## 🔗 Additional Resources

- **API Documentation**: http://localhost:8000/docs (when running)
- **Health Check**: http://localhost:8000/api/health
- **System Stats**: http://localhost:8000/api/stats
- **Filter Options**: http://localhost:8000/api/filters/options

## 📝 Documentation Maintenance

This documentation reflects the current production system. For historical context:
- Implementation history in [faiss-rag/faiss-design.md](faiss-rag/faiss-design.md)
- Original feature specs in [faiss-rag/faiss-feature.md](faiss-rag/faiss-feature.md)

Last updated: 2025-07-07