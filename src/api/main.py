"""
FastAPI application for RAG-YouTube.
"""
import os
import sys
import json
import asyncio
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.config import Config
from core import consts
from api.config_fastapi import FastAPIConfig
from api.models import (
    QuestionRequest, AnswerResponse, StreamChunk,
    SystemStats, ErrorResponse, HealthResponse, Source,
    FilterOptions, CaptionCoverage, DateRange
)
from api.rag_engine import RAGEngine


# Global instances
rag_engine = None
config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global rag_engine, config
    
    # Startup
    print("Initializing RAG engine...")
    config = Config()
    rag_engine = RAGEngine(config)
    print("RAG engine initialized successfully")
    
    yield
    
    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title=FastAPIConfig.API_TITLE,
    description=FastAPIConfig.API_DESCRIPTION,
    version=FastAPIConfig.API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=FastAPIConfig.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def root():
    """Serve the main UI."""
    static_path = FastAPIConfig.get_static_path()
    index_path = os.path.join(static_path, "index.html")
    
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "RAG-YouTube API", "docs": "/docs"}


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Check vector store
        stats = rag_engine.get_stats()
        vector_store_ok = stats['total_documents'] > 0
        
        # Check LLM (could do a simple completion test)
        llm_ok = True  # Assume OK for now
        
        return HealthResponse(
            status="healthy" if vector_store_ok and llm_ok else "unhealthy",
            vector_store=vector_store_ok,
            llm=llm_ok,
            message=f"Service operational with {stats['total_documents']} documents"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            vector_store=False,
            llm=False,
            message=str(e)
        )


@app.get("/api/stats", response_model=SystemStats)
async def get_stats():
    """Get system statistics."""
    try:
        stats = rag_engine.get_stats()
        return SystemStats(
            total_documents=stats['total_documents'],
            embedding_dimension=stats['embedding_dimension'],
            index_size=stats['index_size'],
            model=stats['model'],
            embeddings_model=stats['embeddings_model'],
            version=FastAPIConfig.API_VERSION
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/filters/options", response_model=FilterOptions)
async def get_filter_options():
    """Get available filter options and statistics."""
    try:
        # Get filter statistics from RAG engine
        filter_stats = rag_engine.get_filter_statistics()
        
        # Convert to response model
        return FilterOptions(
            total_documents=filter_stats['total_documents'],
            categories=filter_stats['categories'],
            quality_levels=filter_stats['quality_levels'],
            caption_coverage=CaptionCoverage(
                with_captions=filter_stats['caption_coverage']['with_captions'],
                without_captions=filter_stats['caption_coverage']['without_captions'],
                percentage=filter_stats['caption_coverage']['percentage']
            ),
            date_range=DateRange(
                earliest=filter_stats['date_range']['earliest'],
                latest=filter_stats['date_range']['latest']
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/providers")
async def list_providers():
    """List available LLM providers."""
    try:
        available_providers = rag_engine.llm_manager.list_providers()
        current_provider = rag_engine.current_provider
        
        return {
            "available_providers": available_providers,
            "current_provider": current_provider,
            "total_providers": len(available_providers)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/providers/test")
async def test_providers():
    """Test all available LLM providers."""
    try:
        results = rag_engine.llm_manager.test_all_providers()
        
        return {
            "test_results": results,
            "working_providers": [provider for provider, success in results.items() if success],
            "failed_providers": [provider for provider, success in results.items() if not success]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question and get an answer with sources."""
    try:
        # Process the question
        result = await rag_engine.ask_async(
            question=request.question,
            num_sources=request.num_sources,
            temperature=request.temperature,
            filters=request.filters,
            provider=request.provider
        )
        
        # Convert sources to response model
        sources = []
        for source in result['sources']:
            sources.append(Source(
                content=source['content'],
                metadata=source['metadata'],
                score=source['score']
            ))
        
        return AnswerResponse(
            answer=result['answer'],
            sources=sources,
            question=result['question'],
            search_type=request.search_type,
            processing_time=result['processing_time']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask/stream")
async def ask_question_stream(request: QuestionRequest):
    """Stream the answer as it's generated."""
    async def generate():
        try:
            # First, send the sources
            sources = rag_engine.retrieve_sources(
                request.question, 
                request.num_sources,
                request.filters
            )
            
            for i, source in enumerate(sources):
                chunk = StreamChunk(
                    type="source",
                    content=json.dumps({
                        'index': i,
                        'content': source['content'],
                        'metadata': source['metadata'],
                        'score': source['score']
                    })
                )
                yield {"data": chunk.model_dump_json()}
            
            # Build context
            context = rag_engine.build_context(sources)
            
            # Stream the answer
            async for token in rag_engine.generate_answer_stream(
                request.question, 
                context, 
                request.temperature,
                request.provider
            ):
                chunk = StreamChunk(type="token", content=token)
                yield {"data": chunk.model_dump_json()}
            
            # Send done signal
            chunk = StreamChunk(type="done", content="")
            yield {"data": chunk.model_dump_json()}
            
        except Exception as e:
            chunk = StreamChunk(
                type="error", 
                content=str(e),
                metadata={"status_code": 500}
            )
            yield {"data": chunk.model_dump_json()}
    
    return EventSourceResponse(generate())


# Mount static files
static_path = FastAPIConfig.get_static_path()
if os.path.exists(static_path):
    app.mount(
        FastAPIConfig.STATIC_URL, 
        StaticFiles(directory=static_path), 
        name="static"
    )


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return ErrorResponse(
        error=exc.detail,
        status_code=exc.status_code,
        detail=str(exc)
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return ErrorResponse(
        error="Internal server error",
        status_code=500,
        detail=str(exc)
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=FastAPIConfig.HOST,
        port=FastAPIConfig.PORT,
        reload=FastAPIConfig.RELOAD,
        log_level=FastAPIConfig.LOG_LEVEL.lower()
    )