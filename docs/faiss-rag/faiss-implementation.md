# FAISS RAG Implementation Guide

## Overview

This implementation guide provides step-by-step instructions for building the FastAPI-based FAISS RAG system. The guide includes code examples, best practices, and migration strategies from the existing system.

## Project Structure

```
rag-youtube-faiss/
├── src/
│   ├── main.py              # FastAPI application entry point
│   ├── rag_engine.py        # Core RAG logic and orchestration
│   ├── vector_store.py      # FAISS wrapper with async support
│   ├── models.py            # Pydantic models for validation
│   ├── config.py            # Configuration management
│   └── utils.py             # Utility functions
├── static/
│   ├── index.html           # Simple single-page UI
│   ├── style.css            # Minimal, modern styling
│   └── app.js               # Frontend JavaScript logic
├── tests/
│   ├── test_rag_engine.py   # RAG engine unit tests
│   ├── test_api.py          # API endpoint tests
│   └── test_integration.py  # End-to-end tests
├── requirements.txt         # Production dependencies
├── requirements-dev.txt     # Development dependencies
├── .env.example            # Environment variable template
└── README.md               # Setup and usage instructions
```

## Implementation Steps

### Step 1: Core RAG Engine

The RAG engine is the heart of the system, coordinating retrieval and generation.

#### File: `src/rag_engine.py`

```python
"""
Core RAG engine for question answering with FAISS retrieval.
"""
import asyncio
import json
from typing import List, Dict, Tuple, AsyncGenerator, Optional
from dataclasses import dataclass

from openai import AsyncOpenAI
import tiktoken

from vector_store import FAISSVectorStore, Document
from config import settings


@dataclass
class Source:
    """Represents a source document with metadata."""
    title: str
    url: str
    content: str
    score: float
    metadata: Dict


class RAGEngine:
    """Orchestrates retrieval and generation for question answering."""
    
    def __init__(self, vector_store: FAISSVectorStore):
        self.vector_store = vector_store
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id
        )
        self.encoding = tiktoken.encoding_for_model(settings.openai_model)
        
    async def answer_question(self, question: str, k: int = 4) -> Dict:
        """
        Answer a question using RAG.
        
        Args:
            question: The user's question
            k: Number of documents to retrieve
            
        Returns:
            Dictionary with answer and sources
        """
        # 1. Retrieve relevant documents
        documents = await self.vector_store.asearch(question, k=k)
        
        if not documents:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": []
            }
        
        # 2. Build context from documents
        context = self._build_context(documents)
        
        # 3. Create prompt
        prompt = self._create_prompt(question, context)
        
        # 4. Get completion from OpenAI
        response = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature
        )
        
        answer = response.choices[0].message.content
        
        # 5. Format sources
        sources = self._format_sources(documents)
        
        return {
            "answer": answer,
            "sources": sources,
            "metadata": {
                "documents_retrieved": len(documents),
                "model": settings.openai_model,
                "tokens_used": response.usage.total_tokens
            }
        }
    
    async def answer_stream(self, question: str, k: int = 4) -> AsyncGenerator[str, None]:
        """
        Stream answer generation for real-time display.
        
        Args:
            question: The user's question
            k: Number of documents to retrieve
            
        Yields:
            JSON strings with chunk data
        """
        # 1. Retrieve documents
        documents = await self.vector_store.asearch(question, k=k)
        
        if not documents:
            yield json.dumps({
                "type": "error",
                "content": "No relevant documents found"
            })
            return
        
        # 2. Send sources immediately
        sources = self._format_sources(documents)
        yield json.dumps({
            "type": "sources",
            "sources": sources
        })
        
        # 3. Build context and prompt
        context = self._build_context(documents)
        prompt = self._create_prompt(question, context)
        
        # 4. Stream completion
        stream = await self.client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield json.dumps({
                    "type": "content",
                    "content": chunk.choices[0].delta.content
                })
        
        # 5. Send completion signal
        yield json.dumps({
            "type": "done"
        })
    
    def _build_context(self, documents: List[Document]) -> str:
        """Build context from retrieved documents."""
        context_parts = []
        total_tokens = 0
        
        for i, doc in enumerate(documents):
            doc_text = f"[Document {i+1}]\n{doc.content}\n"
            doc_tokens = len(self.encoding.encode(doc_text))
            
            # Check if adding this document would exceed context limit
            if total_tokens + doc_tokens > settings.max_context_tokens:
                break
                
            context_parts.append(doc_text)
            total_tokens += doc_tokens
        
        return "\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create the prompt for the LLM."""
        return f"""Based on the following context from SpotGamma videos, please answer the question.

Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to fully answer the question, indicate what information is missing."""
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """You are a helpful assistant specializing in options trading and market analysis, with expertise in SpotGamma's content. 
You provide clear, accurate answers based on the provided context. You explain complex financial concepts in an accessible way while maintaining technical accuracy."""
    
    def _format_sources(self, documents: List[Document]) -> List[Dict]:
        """Format documents as sources with metadata."""
        sources = []
        for doc in documents:
            source = {
                "title": doc.metadata.get("title", "Unknown Title"),
                "url": doc.metadata.get("url", ""),
                "channel": doc.metadata.get("channel", "SpotGamma"),
                "published_date": doc.metadata.get("published_date", ""),
                "relevance_score": round(doc.score, 3),
                "preview": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
            }
            sources.append(source)
        return sources
```

### Step 2: Async FAISS Vector Store

Wrapper around FAISS with async support and metadata management.

#### File: `src/vector_store.py`

```python
"""
FAISS vector store with async support and metadata management.
"""
import asyncio
import json
import pickle
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import numpy as np

import faiss
from openai import AsyncOpenAI

from config import settings


@dataclass
class Document:
    """Represents a document with content and metadata."""
    content: str
    metadata: Dict
    embedding: Optional[np.ndarray] = None
    score: Optional[float] = None


class FAISSVectorStore:
    """Async wrapper for FAISS with metadata support."""
    
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.index = None
        self.metadata = {}
        self.client = AsyncOpenAI(
            api_key=settings.openai_api_key,
            organization=settings.openai_org_id
        )
        self._embedding_cache = {}
        
    def load_index(self, index_path: str, metadata_path: str):
        """Load existing FAISS index and metadata."""
        # Load FAISS index
        self.index = faiss.read_index(index_path)
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
            
        print(f"Loaded FAISS index with {self.index.ntotal} vectors")
        
    def save_index(self, index_path: str, metadata_path: str):
        """Save FAISS index and metadata to disk."""
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
            
    async def asearch(self, query: str, k: int = 4) -> List[Document]:
        """
        Async similarity search.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of documents with scores
        """
        # Get query embedding
        embedding = await self._get_embedding(query)
        
        # Run search in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        distances, indices = await loop.run_in_executor(
            None, 
            self._search_sync, 
            embedding, 
            k
        )
        
        # Build results with metadata
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx == -1:  # FAISS returns -1 for empty results
                continue
                
            # Convert L2 distance to similarity score (0-1)
            score = 1 / (1 + dist)
            
            # Get metadata
            meta = self.metadata.get(str(idx), {})
            
            doc = Document(
                content=meta.get("content", ""),
                metadata=meta,
                score=score
            )
            results.append(doc)
            
        return results
    
    def _search_sync(self, embedding: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Synchronous search operation."""
        # Ensure embedding is the right shape
        embedding = np.array(embedding).reshape(1, -1).astype('float32')
        
        # Search
        distances, indices = self.index.search(embedding, k)
        return distances, indices
    
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for text, with caching."""
        # Check cache
        if text in self._embedding_cache:
            return self._embedding_cache[text]
            
        # Get embedding from OpenAI
        response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=text
        )
        
        embedding = np.array(response.data[0].embedding)
        
        # Cache embedding (limit cache size)
        if len(self._embedding_cache) < 1000:
            self._embedding_cache[text] = embedding
            
        return embedding
    
    async def add_documents(self, documents: List[Document]):
        """Add documents to the index."""
        # Get embeddings for all documents
        embeddings = []
        for doc in documents:
            if doc.embedding is None:
                embedding = await self._get_embedding(doc.content)
                doc.embedding = embedding
            embeddings.append(doc.embedding)
            
        # Convert to numpy array
        embeddings_array = np.array(embeddings).astype('float32')
        
        # Add to index
        start_idx = self.index.ntotal
        self.index.add(embeddings_array)
        
        # Update metadata
        for i, doc in enumerate(documents):
            idx = start_idx + i
            self.metadata[str(idx)] = {
                "content": doc.content,
                **doc.metadata
            }
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store."""
        return {
            "total_vectors": self.index.ntotal if self.index else 0,
            "dimension": self.dimension,
            "index_type": type(self.index).__name__ if self.index else "None",
            "metadata_entries": len(self.metadata),
            "cache_size": len(self._embedding_cache)
        }
```

### Step 3: FastAPI Application

Main application with endpoints for question answering.

#### File: `src/main.py`

```python
"""
FastAPI application for FAISS RAG system.
"""
import asyncio
import json
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from models import QuestionRequest, QuestionResponse, StatsResponse
from rag_engine import RAGEngine
from vector_store import FAISSVectorStore
from config import settings


# Global instances
vector_store = None
rag_engine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global vector_store, rag_engine
    
    # Startup
    print("Loading FAISS index...")
    vector_store = FAISSVectorStore()
    vector_store.load_index(
        str(settings.faiss_index_path),
        str(settings.faiss_metadata_path)
    )
    
    rag_engine = RAGEngine(vector_store)
    print("RAG engine initialized")
    
    yield
    
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="SpotGamma RAG API",
    description="Retrieval-Augmented Generation for SpotGamma YouTube content",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main page."""
    with open("static/index.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.post("/api/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Answer a question using RAG.
    
    This endpoint performs retrieval-augmented generation to answer
    questions based on SpotGamma's YouTube content.
    """
    try:
        result = await rag_engine.answer_question(
            question=request.question,
            k=request.k or settings.default_k_documents
        )
        return QuestionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask/stream")
async def ask_question_stream(request: QuestionRequest):
    """
    Stream answer generation for real-time display.
    
    This endpoint uses Server-Sent Events to stream the answer
    as it's being generated.
    """
    async def event_generator():
        try:
            async for chunk in rag_engine.answer_stream(
                question=request.question,
                k=request.k or settings.default_k_documents
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        }
    )


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics and health information."""
    stats = vector_store.get_stats()
    return StatsResponse(
        vector_store_stats=stats,
        status="healthy",
        version="1.0.0"
    )


@app.get("/api/search")
async def search_documents(q: str, k: int = 4):
    """
    Direct similarity search without generation.
    
    Useful for testing retrieval quality.
    """
    documents = await vector_store.asearch(q, k=k)
    return {
        "query": q,
        "results": [
            {
                "content": doc.content[:500],
                "score": doc.score,
                "metadata": doc.metadata
            }
            for doc in documents
        ]
    }


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok"}


@app.get("/ready")
async def readiness_check():
    """Readiness check ensuring all components are loaded."""
    if vector_store is None or rag_engine is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    # Test vector store
    stats = vector_store.get_stats()
    if stats["total_vectors"] == 0:
        raise HTTPException(status_code=503, detail="Vector store empty")
    
    return {"status": "ready", "vectors": stats["total_vectors"]}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level
    )
```

### Step 4: Pydantic Models

Data validation models for API requests and responses.

#### File: `src/models.py`

```python
"""
Pydantic models for request/response validation.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class QuestionRequest(BaseModel):
    """Request model for question answering."""
    question: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="The question to answer"
    )
    k: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Number of documents to retrieve"
    )
    
    @validator('question')
    def clean_question(cls, v):
        """Clean and validate question."""
        # Strip whitespace
        v = v.strip()
        
        # Ensure it's a question (very basic check)
        if not v:
            raise ValueError("Question cannot be empty")
            
        return v


class Source(BaseModel):
    """Source document information."""
    title: str
    url: str
    channel: str = "SpotGamma"
    published_date: Optional[str] = None
    relevance_score: float = Field(..., ge=0, le=1)
    preview: Optional[str] = None


class QuestionResponse(BaseModel):
    """Response model for question answering."""
    answer: str
    sources: List[Source]
    metadata: Optional[Dict[str, Any]] = None


class StatsResponse(BaseModel):
    """Response model for system statistics."""
    vector_store_stats: Dict[str, Any]
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### Step 5: Configuration Management

Settings management using Pydantic.

#### File: `src/config.py`

```python
"""
Configuration management using Pydantic settings.
"""
from typing import List, Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # OpenAI Configuration
    openai_api_key: str
    openai_org_id: Optional[str] = None
    openai_model: str = "gpt-4.1-2025-04-14"
    embedding_model: str = "text-embedding-3-small"
    
    # FAISS Configuration
    faiss_index_path: Path = Path("./db/faiss.index")
    faiss_metadata_path: Path = Path("./db/metadata.json")
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"
    allowed_origins: List[str] = ["*"]
    
    # RAG Configuration
    max_context_tokens: int = 6000
    max_tokens: int = 1000
    temperature: float = 0.7
    default_k_documents: int = 4
    
    # Feature Flags
    enable_streaming: bool = True
    enable_metrics: bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    def validate_paths(self):
        """Ensure required paths exist."""
        if not self.faiss_index_path.exists():
            raise ValueError(f"FAISS index not found at {self.faiss_index_path}")
        if not self.faiss_metadata_path.exists():
            raise ValueError(f"Metadata file not found at {self.faiss_metadata_path}")


# Create global settings instance
settings = Settings()

# Validate on import
try:
    settings.validate_paths()
except ValueError as e:
    print(f"Warning: {e}")
```

### Step 6: Simple Frontend

Clean, minimal frontend without frameworks.

#### File: `static/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SpotGamma RAG - Ask About Options Trading</title>
    <link rel="stylesheet" href="/static/style.css">
    <link rel="icon" type="image/png" href="/static/favicon.png">
</head>
<body>
    <div class="container">
        <header>
            <h1>SpotGamma Knowledge Base</h1>
            <p class="subtitle">Ask questions about options trading and market analysis</p>
        </header>
        
        <main>
            <div class="input-section">
                <form id="question-form">
                    <div class="input-wrapper">
                        <input 
                            type="text" 
                            id="question-input" 
                            placeholder="What is gamma squeeze?"
                            maxlength="500"
                            autocomplete="off"
                            autofocus
                        >
                        <span class="char-count">0/500</span>
                    </div>
                    <div class="button-group">
                        <button type="submit" id="ask-button" class="primary-button">
                            Ask Question
                        </button>
                        <button type="button" id="cancel-button" class="secondary-button" style="display: none;">
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
            
            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <p id="loading-text">Searching knowledge base...</p>
                <div class="progress-bar">
                    <div class="progress-fill" id="progress"></div>
                </div>
            </div>
            
            <div id="results" class="results" style="display: none;">
                <div class="answer-section">
                    <h2>Answer</h2>
                    <div id="answer-content" class="answer-content"></div>
                </div>
                
                <div class="sources-section">
                    <h2>Sources</h2>
                    <div id="sources-list" class="sources-list"></div>
                </div>
            </div>
            
            <div id="error" class="error" style="display: none;">
                <p id="error-message"></p>
            </div>
        </main>
        
        <footer>
            <p>
                <a href="/api/stats" target="_blank">System Stats</a> • 
                <a href="https://github.com/yourusername/rag-youtube" target="_blank">GitHub</a>
            </p>
        </footer>
    </div>
    
    <script src="/static/app.js"></script>
</body>
</html>
```

#### File: `static/style.css`

```css
/* Modern, minimal styling */
:root {
    --primary-color: #2563eb;
    --primary-hover: #1d4ed8;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --background: #ffffff;
    --surface: #f9fafb;
    --border: #e5e7eb;
    --error: #ef4444;
    --success: #10b981;
    --warning: #f59e0b;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text-primary);
    background: var(--background);
}

.container {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

header {
    text-align: center;
    margin-bottom: 3rem;
}

h1 {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.subtitle {
    color: var(--text-secondary);
    font-size: 1.1rem;
}

main {
    flex: 1;
}

/* Input Section */
.input-section {
    margin-bottom: 2rem;
}

.input-wrapper {
    position: relative;
    margin-bottom: 1rem;
}

#question-input {
    width: 100%;
    padding: 1rem;
    font-size: 1rem;
    border: 2px solid var(--border);
    border-radius: 8px;
    outline: none;
    transition: border-color 0.2s;
}

#question-input:focus {
    border-color: var(--primary-color);
}

.char-count {
    position: absolute;
    right: 1rem;
    bottom: -1.5rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
}

.button-group {
    display: flex;
    gap: 1rem;
}

.primary-button, .secondary-button {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    font-weight: 500;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
}

.primary-button {
    background: var(--primary-color);
    color: white;
}

.primary-button:hover:not(:disabled) {
    background: var(--primary-hover);
}

.primary-button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.secondary-button {
    background: var(--surface);
    color: var(--text-primary);
    border: 1px solid var(--border);
}

.secondary-button:hover {
    background: var(--border);
}

/* Loading State */
.loading {
    text-align: center;
    padding: 2rem;
}

.spinner {
    width: 40px;
    height: 40px;
    margin: 0 auto 1rem;
    border: 3px solid var(--border);
    border-top-color: var(--primary-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.progress-bar {
    width: 100%;
    height: 4px;
    background: var(--border);
    border-radius: 2px;
    overflow: hidden;
    margin-top: 1rem;
}

.progress-fill {
    height: 100%;
    background: var(--primary-color);
    width: 0%;
    transition: width 0.3s ease;
}

/* Results */
.results {
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.answer-section {
    margin-bottom: 2rem;
}

.answer-section h2 {
    font-size: 1.25rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
}

.answer-content {
    background: var(--surface);
    padding: 1.5rem;
    border-radius: 8px;
    line-height: 1.8;
}

.answer-content p {
    margin-bottom: 1rem;
}

.answer-content p:last-child {
    margin-bottom: 0;
}

/* Sources */
.sources-section h2 {
    font-size: 1.25rem;
    margin-bottom: 1rem;
    color: var(--text-primary);
}

.sources-list {
    display: grid;
    gap: 1rem;
}

.source-item {
    background: var(--surface);
    padding: 1rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    transition: border-color 0.2s;
}

.source-item:hover {
    border-color: var(--primary-color);
}

.source-title {
    font-weight: 600;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.relevance-score {
    font-size: 0.875rem;
    color: var(--text-secondary);
    font-weight: normal;
}

.source-meta {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
}

.source-link {
    display: inline-block;
    color: var(--primary-color);
    text-decoration: none;
    font-size: 0.875rem;
    margin-top: 0.5rem;
}

.source-link:hover {
    text-decoration: underline;
}

/* Error State */
.error {
    background: #fef2f2;
    border: 1px solid #fecaca;
    color: var(--error);
    padding: 1rem;
    border-radius: 8px;
    margin-top: 1rem;
}

/* Footer */
footer {
    text-align: center;
    padding-top: 2rem;
    margin-top: 3rem;
    border-top: 1px solid var(--border);
    color: var(--text-secondary);
    font-size: 0.875rem;
}

footer a {
    color: var(--primary-color);
    text-decoration: none;
}

footer a:hover {
    text-decoration: underline;
}

/* Responsive */
@media (max-width: 640px) {
    .container {
        padding: 1rem;
    }
    
    h1 {
        font-size: 1.5rem;
    }
    
    .button-group {
        flex-direction: column;
    }
    
    .primary-button, .secondary-button {
        width: 100%;
    }
}
```

#### File: `static/app.js`

```javascript
/**
 * Frontend JavaScript for SpotGamma RAG
 */

// DOM Elements
const questionForm = document.getElementById('question-form');
const questionInput = document.getElementById('question-input');
const charCount = document.querySelector('.char-count');
const askButton = document.getElementById('ask-button');
const cancelButton = document.getElementById('cancel-button');
const loadingDiv = document.getElementById('loading');
const loadingText = document.getElementById('loading-text');
const progressBar = document.getElementById('progress');
const resultsDiv = document.getElementById('results');
const answerContent = document.getElementById('answer-content');
const sourcesList = document.getElementById('sources-list');
const errorDiv = document.getElementById('error');
const errorMessage = document.getElementById('error-message');

// State
let currentEventSource = null;
let currentAnswer = '';
let isGenerating = false;

// Event Listeners
questionForm.addEventListener('submit', handleSubmit);
questionInput.addEventListener('input', updateCharCount);
cancelButton.addEventListener('click', cancelGeneration);

// Initialize
updateCharCount();

/**
 * Handle form submission
 */
async function handleSubmit(e) {
    e.preventDefault();
    
    const question = questionInput.value.trim();
    if (!question) return;
    
    // Clear previous results
    hideAll();
    currentAnswer = '';
    
    // Update UI state
    isGenerating = true;
    askButton.disabled = true;
    cancelButton.style.display = 'inline-block';
    loadingDiv.style.display = 'block';
    progressBar.style.width = '10%';
    
    try {
        // Use streaming endpoint
        await streamAnswer(question);
    } catch (error) {
        showError(error.message);
    } finally {
        // Reset UI state
        isGenerating = false;
        askButton.disabled = false;
        cancelButton.style.display = 'none';
        loadingDiv.style.display = 'none';
    }
}

/**
 * Stream answer using Server-Sent Events
 */
async function streamAnswer(question) {
    const url = '/api/ask/stream';
    
    currentEventSource = new EventSource(
        url + '?' + new URLSearchParams({
            question: question
        })
    );
    
    currentEventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleStreamData(data);
    };
    
    currentEventSource.onerror = (error) => {
        currentEventSource.close();
        if (isGenerating) {
            showError('Connection error. Please try again.');
        }
    };
    
    // Alternative: Use fetch with POST
    const response = await fetch('/api/ask/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question })
    });
    
    if (!response.ok) {
        throw new Error('Failed to get response');
    }
    
    // Read streaming response
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let buffer = '';
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete SSE messages
        const messages = buffer.split('\n\n');
        buffer = messages.pop(); // Keep incomplete message in buffer
        
        for (const message of messages) {
            if (message.startsWith('data: ')) {
                const data = JSON.parse(message.slice(6));
                handleStreamData(data);
            }
        }
    }
}

/**
 * Handle streaming data
 */
function handleStreamData(data) {
    switch (data.type) {
        case 'sources':
            displaySources(data.sources);
            loadingText.textContent = 'Generating answer...';
            progressBar.style.width = '30%';
            break;
            
        case 'content':
            if (!resultsDiv.style.display || resultsDiv.style.display === 'none') {
                resultsDiv.style.display = 'block';
            }
            currentAnswer += data.content;
            answerContent.textContent = currentAnswer;
            progressBar.style.width = '60%';
            break;
            
        case 'done':
            loadingDiv.style.display = 'none';
            progressBar.style.width = '100%';
            if (currentEventSource) {
                currentEventSource.close();
            }
            break;
            
        case 'error':
            showError(data.content);
            break;
    }
}

/**
 * Display sources
 */
function displaySources(sources) {
    sourcesList.innerHTML = '';
    
    sources.forEach((source, index) => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'source-item';
        
        const score = Math.round(source.relevance_score * 100);
        
        sourceItem.innerHTML = `
            <div class="source-title">
                <span>${index + 1}. ${source.title}</span>
                <span class="relevance-score">${score}% relevant</span>
            </div>
            <div class="source-meta">
                ${source.channel} • ${formatDate(source.published_date)}
            </div>
            <a href="${source.url}" target="_blank" class="source-link">
                Watch on YouTube →
            </a>
        `;
        
        sourcesList.appendChild(sourceItem);
    });
}

/**
 * Cancel generation
 */
function cancelGeneration() {
    if (currentEventSource) {
        currentEventSource.close();
        currentEventSource = null;
    }
    isGenerating = false;
    loadingDiv.style.display = 'none';
    askButton.disabled = false;
    cancelButton.style.display = 'none';
}

/**
 * Update character count
 */
function updateCharCount() {
    const count = questionInput.value.length;
    charCount.textContent = `${count}/500`;
    
    if (count > 400) {
        charCount.style.color = 'var(--warning)';
    } else {
        charCount.style.color = 'var(--text-secondary)';
    }
}

/**
 * Show error message
 */
function showError(message) {
    hideAll();
    errorDiv.style.display = 'block';
    errorMessage.textContent = message;
}

/**
 * Hide all result sections
 */
function hideAll() {
    resultsDiv.style.display = 'none';
    errorDiv.style.display = 'none';
    answerContent.textContent = '';
    sourcesList.innerHTML = '';
}

/**
 * Format date
 */
function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays < 1) return 'Today';
    if (diffDays < 2) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
    if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`;
    
    return date.toLocaleDateString();
}

/**
 * Keyboard shortcuts
 */
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K to focus input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        questionInput.focus();
        questionInput.select();
    }
    
    // Escape to cancel
    if (e.key === 'Escape' && isGenerating) {
        cancelGeneration();
    }
});
```

## Migration from Current System

### Step 1: Export Existing FAISS Index

```python
# One-time migration script
import sys
sys.path.insert(0, 'src')

from vector_store_faiss import FAISSVectorStore as OldStore
from config import Config
import consts
import json

# Load old system
config = Config(consts.CONFIG_PATH)
old_store = OldStore(config, persist_directory="db")

# Export metadata
metadata = {}
for i in range(len(old_store.docstore._dict)):
    doc_id = f"{i}"
    if doc_id in old_store.docstore._dict:
        doc = old_store.docstore._dict[doc_id]
        metadata[str(i)] = {
            "content": doc.page_content,
            "title": doc.metadata.get("title", ""),
            "url": doc.metadata.get("source", ""),
            "channel": "SpotGamma",
            "published_date": doc.metadata.get("date", "")
        }

# Save metadata
with open("db/metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Exported {len(metadata)} documents")
```

### Step 2: Environment Setup

Create `.env` file:

```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_ORG_ID=org-...
OPENAI_MODEL=gpt-4.1-2025-04-14

# FAISS Configuration
FAISS_INDEX_PATH=./db/faiss.index
FAISS_METADATA_PATH=./db/metadata.json

# Server Configuration
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# Feature Configuration
MAX_CONTEXT_TOKENS=6000
DEFAULT_K_DOCUMENTS=4
```

### Step 3: Install Dependencies

```bash
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
openai==1.6.0
faiss-cpu==1.7.4
tiktoken==0.5.2
numpy==1.24.3
python-multipart==0.0.6

# requirements-dev.txt
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
black==23.12.0
ruff==0.1.8
```

### Step 4: Deployment

```bash
# Development
uvicorn main:app --reload

# Production with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Docker deployment
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Testing Strategy

### Unit Tests

```python
# tests/test_rag_engine.py
import pytest
from unittest.mock import Mock, AsyncMock

from rag_engine import RAGEngine
from vector_store import Document


@pytest.mark.asyncio
async def test_answer_question():
    # Mock vector store
    mock_store = Mock()
    mock_store.asearch = AsyncMock(return_value=[
        Document(
            content="Gamma is the rate of change of delta.",
            metadata={"title": "Understanding Gamma"},
            score=0.95
        )
    ])
    
    # Mock OpenAI client
    mock_client = Mock()
    
    # Test
    engine = RAGEngine(mock_store)
    engine.client = mock_client
    
    # ... test implementation
```

### Integration Tests

```python
# tests/test_integration.py
import pytest
from httpx import AsyncClient

from main import app


@pytest.mark.asyncio
async def test_ask_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/ask",
            json={"question": "What is gamma?"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
```

## Performance Optimization

### 1. Embedding Cache

```python
# In vector_store.py
import functools
import hashlib

@functools.lru_cache(maxsize=1000)
def get_cached_embedding(text_hash: str):
    # Cache embeddings by hash
    pass
```

### 2. Connection Pooling

```python
# In rag_engine.py
httpx_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=10)
)
```

### 3. Response Caching

```python
# In main.py
from fastapi_cache import FastAPICache
from fastapi_cache.decorator import cache

@cache(expire=300)  # 5 minute cache
async def ask_question(request: QuestionRequest):
    # ... implementation
```

## Monitoring and Observability

### Prometheus Metrics

```python
# src/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Metrics
questions_total = Counter('rag_questions_total', 'Total questions asked')
response_time = Histogram('rag_response_seconds', 'Response time')
active_requests = Gauge('rag_active_requests', 'Active requests')
```

### Structured Logging

```python
# src/logging_config.py
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            'timestamp': record.created,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module
        })
```

## Conclusion

This implementation provides a clean, performant, and maintainable RAG system using FastAPI and FAISS. The architecture is designed for clarity and extensibility while avoiding the complexity of the previous system. The migration path preserves existing data while modernizing the infrastructure for better performance and developer experience.