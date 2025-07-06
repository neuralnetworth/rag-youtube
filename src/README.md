# Source Code Organization

## Directory Structure

```
src/
├── api/                    # FastAPI implementation (current production code)
│   ├── main.py            # FastAPI application
│   ├── rag_engine.py      # Simplified RAG logic
│   ├── models.py          # Pydantic schemas
│   └── config_fastapi.py  # API configuration
│
├── core/                   # Shared utilities used across the project
│   ├── config.py          # Configuration management
│   ├── consts.py          # Constants
│   ├── utils.py           # Utility functions
│   └── database.py        # Database operations
│
├── data_pipeline/          # Data ingestion and processing
│   ├── list_videos.py     # YouTube API video listing
│   ├── download_captions.py # Caption downloading
│   ├── downloader.py      # yt-dlp wrapper
│   └── document_loader_faiss.py # FAISS document loading
│
├── vector_stores/          # Vector store implementations
│   ├── faiss.py          # FAISS vector store
│   └── migrate_faiss_to_chroma.py # Migration utility
│
└── legacy/                 # Legacy LangChain implementations (deprecated)
    ├── agents/            # LangChain agents
    ├── chains/            # LangChain chains
    ├── callback.py        # LangChain callbacks
    └── document_loader.py # ChromaDB document loader
```

## Import Examples

After reorganization, imports should follow this pattern:

```python
# From API modules
from api.rag_engine import RAGEngine
from api.models import QuestionRequest

# From core utilities
from core.config import Config
from core import consts, utils

# From data pipeline
from data_pipeline.list_videos import get_channel_videos
from data_pipeline.document_loader_faiss import LoaderFAISS

# From vector stores
from vector_stores.faiss import FAISSVectorStore

# From legacy (if needed)
from legacy.agents.qa import AgentQA
from legacy.chains.base import ChainParameters
```

## Key Benefits

1. **Clear separation** between current (FastAPI) and legacy (LangChain) code
2. **Logical grouping** of related functionality
3. **Easy navigation** - know exactly where to find specific components
4. **Future-proof** - easy to remove legacy/ when no longer needed
5. **Better imports** - more explicit and organized module paths