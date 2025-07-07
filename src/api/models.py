"""
Pydantic models for FastAPI request/response schemas.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    """Request model for asking questions."""
    question: str = Field(..., min_length=1, max_length=1000, description="The question to ask")
    num_sources: int = Field(default=4, ge=1, le=10, description="Number of sources to retrieve")
    search_type: str = Field(default="similarity", pattern="^(similarity|mmr|similarity_score_threshold)$")
    temperature: float = Field(default=0.7, ge=0, le=2, description="LLM temperature")
    stream: bool = Field(default=False, description="Enable streaming response")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Document filters")


class Source(BaseModel):
    """Source document information."""
    content: str = Field(..., description="Text content of the source")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Source metadata")
    score: float = Field(..., ge=0, le=1, description="Relevance score")
    

class AnswerResponse(BaseModel):
    """Response model for answers."""
    answer: str = Field(..., description="The generated answer")
    sources: List[Source] = Field(default_factory=list, description="Source documents used")
    question: str = Field(..., description="The original question")
    search_type: str = Field(..., description="Search type used")
    processing_time: float = Field(..., description="Time taken to process in seconds")


class StreamChunk(BaseModel):
    """Model for streaming response chunks."""
    type: str = Field(..., pattern="^(token|source|done|error)$")
    content: str = Field(default="", description="Content of the chunk")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class SystemStats(BaseModel):
    """System statistics response."""
    total_documents: int = Field(..., description="Total documents in vector store")
    embedding_dimension: int = Field(..., description="Dimension of embeddings")
    index_size: int = Field(..., description="Size of FAISS index")
    model: str = Field(..., description="Current LLM model")
    embeddings_model: str = Field(..., description="Current embeddings model")
    version: str = Field(default="1.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(default=None, description="Detailed error information")
    status_code: int = Field(..., description="HTTP status code")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy", pattern="^(healthy|unhealthy)$")
    vector_store: bool = Field(..., description="Vector store availability")
    llm: bool = Field(..., description="LLM availability")
    message: str = Field(default="Service is operational")


class CaptionCoverage(BaseModel):
    """Caption coverage statistics."""
    with_captions: int = Field(..., description="Number of documents with captions")
    without_captions: int = Field(..., description="Number of documents without captions")
    percentage: float = Field(..., description="Percentage of documents with captions")


class DateRange(BaseModel):
    """Date range for filtering."""
    earliest: Optional[str] = Field(None, description="Earliest publication date (YYYY-MM-DD)")
    latest: Optional[str] = Field(None, description="Latest publication date (YYYY-MM-DD)")


class FilterOptions(BaseModel):
    """Available filter options and statistics."""
    total_documents: int = Field(..., description="Total number of documents")
    categories: Dict[str, int] = Field(..., description="Document count by category")
    quality_levels: Dict[str, int] = Field(..., description="Document count by quality level")
    caption_coverage: CaptionCoverage = Field(..., description="Caption availability statistics")
    date_range: DateRange = Field(..., description="Available date range for filtering")