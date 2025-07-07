# FAISS-RAG System Documentation

## Overview

The FAISS-RAG system is the foundational architecture of RAG-YouTube, providing high-performance vector search and retrieval-augmented generation capabilities for YouTube video content.

## What is FAISS-RAG?

FAISS-RAG combines:
- **FAISS** (Facebook AI Similarity Search): Efficient vector similarity search
- **RAG** (Retrieval-Augmented Generation): Enhancing LLM responses with retrieved context
- **FastAPI**: Modern async web framework for the API layer

This creates a system that can quickly find relevant video segments and generate accurate answers based on actual content.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
│                   (HTML/CSS/JavaScript)                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/WebSocket
┌─────────────────────────▼───────────────────────────────────┐
│                    FastAPI Server                           │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │
│  │   Endpoints │  │   Models    │  │   RAG Engine     │   │
│  │   /ask      │  │   Pydantic  │  │   Question →     │   │
│  │   /stats    │  │   Schemas   │  │   Context →      │   │
│  │   /filters  │  │             │  │   Answer         │   │
│  └─────────────┘  └─────────────┘  └──────────────────┘   │
└─────────────────────────┬───────────────────────────────────┘
                          │
       ┌──────────────────┴──────────────┬─────────────────┐
       ▼                                 ▼                 ▼
┌──────────────┐              ┌──────────────┐   ┌──────────────┐
│ FAISS Index  │              │  OpenAI API  │   │  Metadata    │
│              │              │              │   │  Storage     │
│ • Embeddings │              │ • Embeddings │   │              │
│ • Vector     │              │ • GPT-4.1    │   │ • Video info │
│   Search     │              │   Generation │   │ • Captions   │
└──────────────┘              └──────────────┘   └──────────────┘
```

## Core Components

### 1. FAISS Vector Store (`src/vector_stores/faiss.py`)

The heart of the system, managing vector embeddings and similarity search.

**Key Features**:
- Persistent index storage (disk-based)
- OpenAI embedding integration
- Metadata co-storage with vectors
- Efficient similarity search with scores

**How it works**:
1. Documents are chunked into manageable segments
2. Each chunk is embedded using OpenAI's embedding model
3. Embeddings are stored in a FAISS index
4. Metadata is stored separately but linked by index

### 2. RAG Engine (`src/api/rag_engine.py`)

Orchestrates the retrieval and generation process.

**Key Features**:
- Document retrieval from vector store
- Context building from retrieved documents
- Answer generation using GPT-4.1
- Source attribution management

**Process Flow**:
1. Embed user question
2. Search FAISS index for similar documents
3. Build context from top-k results
4. Generate answer using context + question
5. Return answer with source citations

### 3. FastAPI Server (`src/api/main.py`)

Provides the web API interface.

**Endpoints**:
- `POST /api/ask`: Main Q&A endpoint
- `POST /api/ask/stream`: Streaming response variant
- `GET /api/stats`: System statistics
- `GET /api/filters/options`: Filter metadata
- `GET /api/health`: Health check

### 4. Document Processing Pipeline

Prepares YouTube content for the vector store.

**Components**:
- `list_videos.py`: Fetches channel video list
- `download_captions.py`: Downloads transcripts
- `document_loader_faiss.py`: Chunks and indexes content

## Data Flow

### Indexing Flow
```
YouTube API → Video List → Caption Download → Text Chunking → Embedding → FAISS Index
```

### Query Flow
```
User Question → Embedding → Vector Search → Document Retrieval → Context Building → LLM Generation → Response
```

## Configuration

### System Configuration (`rag-youtube.conf`)

```ini
[General]
llm=openai
openai_model=gpt-4.1-2025-04-14
port=8000

[Embeddings]
model=openai:text-embedding-3-small

[Search]
chunk_size=2500
chunk_overlap=500
search_type=similarity
document_count=4
```

### Environment Variables (`.env`)

```bash
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
```

## Performance Characteristics

### Speed
- **Embedding Generation**: ~100ms for typical question
- **Vector Search**: ~50ms for 2,500 documents
- **Answer Generation**: 2-5 seconds
- **Total Response Time**: < 5 seconds typical

### Scalability
- **Document Capacity**: Tested with 2,500+ chunks
- **Concurrent Users**: Async architecture supports multiple
- **Memory Usage**: ~500MB for typical deployment

### Accuracy
- **Semantic Search**: OpenAI embeddings capture meaning
- **Context Window**: 2,500 tokens per chunk
- **Source Attribution**: Direct links to original content

## Integration Points

The FAISS-RAG system provides a foundation for:

1. **Content Filtering**: Metadata-based filtering layer
2. **Playlist Organization**: YouTube playlist integration
3. **Quality Scoring**: Content density analysis
4. **Category Inference**: Automatic content classification

## API Usage

### Basic Question Answering

```python
POST /api/ask
{
    "question": "What is gamma in options trading?",
    "num_sources": 4,
    "stream": false
}
```

### Response Format

```json
{
    "answer": "Gamma is the rate of change of delta...",
    "sources": [
        {
            "content": "...",
            "metadata": {
                "title": "Understanding Options Greeks",
                "url": "https://youtube.com/watch?v=...",
                "score": 0.87
            }
        }
    ],
    "processing_time": 3.4
}
```

## Deployment

### Development
```bash
uv run uvicorn src.api.main:app --reload
```

### Production
```bash
./run_fastapi.sh
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/api/health
```

### System Statistics
```bash
curl http://localhost:8000/api/stats
```

Returns:
- Total documents indexed
- Embedding model in use
- Index size
- LLM configuration

## Troubleshooting

### Common Issues

1. **Slow responses**: Check OpenAI API latency
2. **No results**: Verify FAISS index exists in `db/`
3. **Poor relevance**: Consider re-embedding with different chunk size
4. **Memory issues**: Reduce chunk size or implement pagination

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

This FAISS-RAG foundation enables:
- Advanced filtering capabilities
- Multi-modal search (future)
- Custom ranking algorithms
- Hybrid search approaches

See [Content Filtering](../content-filtering/) for the filtering layer built on top of this foundation.

## Documentation

### Current System Documentation

1. **[Architecture Deep Dive](architecture.md)** - Technical details of component design and interactions
2. **[Setup Guide](setup-guide.md)** - Comprehensive installation and configuration instructions
3. **[API Reference](#api-usage)** - Endpoint documentation (above)

### Implementation History

These documents detail the original migration from LangChain to FAISS-RAG:

4. **[Design Document](faiss-design.md)** - Original system design and migration plan
5. **[Feature Specification](faiss-feature.md)** - MVP feature requirements
6. **[Implementation Details](faiss-implementation.md)** - Code-level implementation guide

The implementation history documents are preserved for reference but the current system documentation above reflects the production system.