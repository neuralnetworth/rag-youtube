# FAISS-RAG Architecture Deep Dive

## Introduction

This document provides a detailed technical exploration of the FAISS-RAG architecture, explaining how components interact and why specific design decisions were made.

## Core Design Principles

### 1. Simplicity Over Complexity

Unlike traditional LangChain-based RAG systems with complex chain orchestration, FAISS-RAG uses direct integration:

```python
# Traditional LangChain approach (NOT used)
chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    chain_type_kwargs=chain_type_kwargs
)

# FAISS-RAG approach (USED)
results = vector_store.similarity_search(query)
context = build_context(results)
answer = generate_answer(question, context)
```

### 2. Async-First Design

All I/O operations are async to maximize throughput:

```python
async def ask_async(self, question: str):
    # Parallel operations where possible
    sources = await asyncio.to_thread(self.retrieve_sources, question)
    answer = await self.generate_answer_async(question, context)
    return {"answer": answer, "sources": sources}
```

### 3. Stateless Architecture

No session state is maintained server-side:
- Each request is independent
- Enables horizontal scaling
- Simplifies deployment

## Component Architecture

### Vector Store Layer

#### FAISS Index Structure

```
faiss.index (Binary file)
├── Embedding vectors (1536 dimensions)
├── Index structure (IVF, HNSW, or Flat)
└── Metadata mappings

documents.json
├── Document texts
└── Document IDs

metadata.json
├── Video titles
├── URLs
├── Timestamps
└── Enhanced metadata (categories, quality, etc.)
```

#### Embedding Pipeline

```python
def embed_texts(self, texts: List[str]) -> np.ndarray:
    # 1. Clean texts (remove newlines for better embeddings)
    texts = [text.replace("\n", " ") for text in texts]
    
    # 2. Call OpenAI API
    response = self.client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    
    # 3. Extract embeddings
    embeddings = [item.embedding for item in response.data]
    
    # 4. Convert to numpy array for FAISS
    return np.array(embeddings, dtype=np.float32)
```

#### Search Algorithm

FAISS uses approximate nearest neighbor search:

```python
def similarity_search_with_score(self, query: str, k: int = 4):
    # 1. Embed query
    query_embedding = self.embed_texts([query])[0]
    
    # 2. Search FAISS index
    distances, indices = self.index.search(
        query_embedding.reshape(1, -1), k
    )
    
    # 3. Convert distances to similarity scores
    # L2 distance to similarity: 1 / (1 + distance)
    similarities = 1 / (1 + distances[0])
    
    # 4. Return documents with scores
    results = []
    for idx, similarity in zip(indices[0], similarities):
        if idx >= 0:  # Valid index
            results.append({
                "content": self.documents[idx],
                "metadata": self.metadata[idx],
                "score": float(similarity)
            })
    
    return results
```

### RAG Engine

#### Context Building Strategy

```python
def build_context(self, sources: List[Dict]) -> str:
    """Build context from retrieved sources."""
    context_parts = []
    
    for i, source in enumerate(sources, 1):
        # Format each source
        context_parts.append(
            f"Source {i}:\n"
            f"Title: {source['metadata'].get('title', 'Unknown')}\n"
            f"Content: {source['content']}\n"
        )
    
    return "\n---\n".join(context_parts)
```

#### Prompt Engineering

The system uses carefully crafted prompts:

```python
SYSTEM_PROMPT = """You are a helpful assistant answering questions about 
SpotGamma's YouTube content. Use the provided context to answer questions 
accurately. If the context doesn't contain relevant information, say so."""

USER_PROMPT = """Context:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above."""
```

#### Answer Generation

```python
async def generate_answer_async(self, question: str, context: str):
    response = await self.client.chat.completions.create(
        model="gpt-4.1-2025-04-14",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT.format(
                context=context, 
                question=question
            )}
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content
```

### API Layer

#### Request Flow

```
1. Request Validation (Pydantic)
   ↓
2. Rate Limiting Check
   ↓
3. Question Embedding
   ↓
4. Vector Search
   ↓
5. Filter Application (if enabled)
   ↓
6. Context Building
   ↓
7. LLM Generation
   ↓
8. Response Formatting
```

#### Streaming Implementation

For real-time responses:

```python
async def ask_stream(request: AskRequest):
    async def generate():
        # Send sources first
        sources = rag_engine.retrieve_sources(request.question)
        for source in sources:
            yield f"data: {json.dumps({'type': 'source', 'content': source})}\n\n"
        
        # Stream answer tokens
        async for token in rag_engine.generate_answer_stream(question, context):
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return EventSourceResponse(generate())
```

## Data Models

### Document Structure

```python
class Document:
    content: str           # Chunk text
    metadata: Dict[str, Any]
        video_id: str      # YouTube video ID
        title: str         # Video title
        url: str           # YouTube URL
        published_date: str # ISO date
        duration: int      # Seconds
        has_captions: bool # Transcript availability
        category: str      # Inferred category
        quality_score: str # Content quality
        chunk_index: int   # Position in video
```

### API Models

```python
class AskRequest(BaseModel):
    question: str = Field(..., max_length=1000)
    num_sources: int = Field(default=4, ge=1, le=10)
    temperature: float = Field(default=0.7, ge=0, le=1)
    stream: bool = Field(default=False)
    filters: Optional[Dict[str, Any]] = None

class AskResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
    question: str
    processing_time: float
```

## Performance Optimizations

### 1. Embedding Cache

Although not currently implemented, a simple cache would help:

```python
class EmbeddingCache:
    def __init__(self, max_size=1000):
        self.cache = {}
        self.access_order = []
        self.max_size = max_size
    
    def get(self, text: str) -> Optional[np.ndarray]:
        if text in self.cache:
            self.access_order.remove(text)
            self.access_order.append(text)
            return self.cache[text]
        return None
```

### 2. Index Optimization

FAISS supports various index types:

- **Flat**: Exact search, best quality, slower
- **IVF**: Inverted file index, good balance
- **HNSW**: Hierarchical navigable small world, fast

Current implementation uses Flat for quality.

### 3. Async I/O

All blocking operations wrapped in `asyncio.to_thread()`:

```python
# CPU-bound operation (FAISS search)
results = await asyncio.to_thread(
    self.vector_store.similarity_search_with_score,
    query, k
)

# I/O-bound operation (OpenAI API)
response = await self.client.chat.completions.create(...)
```

## Error Handling

### Graceful Degradation

```python
try:
    sources = self.retrieve_sources(question)
except Exception as e:
    logger.error(f"Search failed: {e}")
    # Return generic response
    return {
        "answer": "I'm having trouble searching right now.",
        "sources": [],
        "error": str(e)
    }
```

### Timeout Management

```python
async def with_timeout(coro, timeout=30):
    try:
        return await asyncio.wait_for(coro, timeout)
    except asyncio.TimeoutError:
        raise HTTPException(408, "Request timeout")
```

## Security Considerations

### Input Validation

- Question length limits (1000 chars)
- Sanitization of user inputs
- Rate limiting per IP

### API Security

- CORS configuration
- Optional API key authentication
- Request size limits

## Monitoring and Observability

### Metrics to Track

1. **Performance Metrics**
   - Query latency (p50, p95, p99)
   - Embedding generation time
   - LLM response time

2. **Quality Metrics**
   - Average similarity scores
   - Zero-result queries
   - User feedback (if implemented)

3. **System Metrics**
   - Memory usage
   - Index size growth
   - API request rate

### Logging Strategy

```python
logger.info("Search request", extra={
    "question_length": len(question),
    "num_sources": num_sources,
    "has_filters": bool(filters),
    "similarity_scores": [s["score"] for s in sources]
})
```

## Future Architecture Considerations

### 1. Distributed Architecture

For scaling beyond single instance:
- Redis for caching
- Multiple FAISS shards
- Load balancer with sticky sessions

### 2. Enhanced Search

Potential improvements:
- Hybrid search (keyword + semantic)
- Re-ranking with cross-encoders
- Query expansion

### 3. Multi-Modal Support

Architecture ready for:
- Image embeddings from video frames
- Audio analysis
- Transcript + visual alignment