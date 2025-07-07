"""
Simplified RAG engine for FastAPI implementation.
Direct integration with FAISS vector store and OpenAI.
"""
import os
import sys
import time
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
from openai import OpenAI, AsyncOpenAI

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from vector_stores.faiss import FAISSVectorStore
from core.config import Config
from api.models import Source
from data_pipeline.metadata_enhancer import MetadataEnhancer
from api.filters import DocumentFilter


class RAGEngine:
    """Simplified RAG engine for question answering."""
    
    def __init__(self, config: Config):
        self.config = config
        self.vector_store = FAISSVectorStore(config)
        self.metadata_enhancer = MetadataEnhancer()
        self.document_filter = DocumentFilter()
        
        # Initialize OpenAI clients
        self.client = OpenAI(
            api_key=config.openai_api_key(),
            organization=config.openai_org_id()
        )
        self.async_client = AsyncOpenAI(
            api_key=config.openai_api_key(),
            organization=config.openai_org_id()
        )
        
        # Model configuration
        self.model = config.openai_model()
        self.temperature = config.llm_temperature()
        
    def retrieve_sources(self, question: str, num_sources: int = 4, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant sources from vector store with optional filtering."""
        # Set filters if provided
        if filters:
            self.document_filter.set_filters(filters)
        
        # Calculate how many to fetch if filters are active
        fetch_count = num_sources
        if filters and self.document_filter.has_active_filters():
            fetch_count = self.document_filter.calculate_over_fetch(num_sources, True)
        
        # Get documents with scores
        results = self.vector_store.similarity_search_with_score(question, k=fetch_count)
        
        sources = []
        for doc_text, score, metadata in results:
            sources.append({
                'content': doc_text,
                'score': float(score),
                'metadata': metadata
            })
        
        # Apply filters if active
        if filters and self.document_filter.has_active_filters():
            sources = self.document_filter.apply_filters(sources)
            # Limit to requested number after filtering
            sources = sources[:num_sources]
        
        return sources
    
    def build_context(self, sources: List[Dict[str, Any]], max_tokens: int = 3000) -> str:
        """Build context from sources, respecting token limits."""
        context_parts = []
        current_tokens = 0
        
        # Simple token estimation (roughly 4 chars per token)
        for i, source in enumerate(sources):
            source_text = f"[Source {i+1}]\n{source['content']}\n"
            estimated_tokens = len(source_text) // 4
            
            if current_tokens + estimated_tokens > max_tokens:
                break
                
            context_parts.append(source_text)
            current_tokens += estimated_tokens
        
        return "\n".join(context_parts)
    
    def generate_answer(self, question: str, context: str, temperature: float = None) -> str:
        """Generate answer using OpenAI."""
        if temperature is None:
            temperature = self.temperature
            
        system_prompt = """You are a helpful assistant analyzing YouTube video content about financial markets and options trading.
Answer questions based on the provided context from video transcripts. If the answer isn't in the context, say so.
Be concise but comprehensive. Cite specific details from the sources when relevant."""

        user_prompt = f"""Context from video transcripts:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    async def generate_answer_async(self, question: str, context: str, temperature: float = None) -> str:
        """Async version of generate_answer."""
        if temperature is None:
            temperature = self.temperature
            
        system_prompt = """You are a helpful assistant analyzing YouTube video content about financial markets and options trading.
Answer questions based on the provided context from video transcripts. If the answer isn't in the context, say so.
Be concise but comprehensive. Cite specific details from the sources when relevant."""

        user_prompt = f"""Context from video transcripts:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above."""

        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    async def generate_answer_stream(
        self, 
        question: str, 
        context: str, 
        temperature: float = None
    ) -> AsyncGenerator[str, None]:
        """Stream answer generation using OpenAI."""
        if temperature is None:
            temperature = self.temperature
            
        system_prompt = """You are a helpful assistant analyzing YouTube video content about financial markets and options trading.
Answer questions based on the provided context from video transcripts. If the answer isn't in the context, say so.
Be concise but comprehensive. Cite specific details from the sources when relevant."""

        user_prompt = f"""Context from video transcripts:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above."""

        stream = await self.async_client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temperature,
            max_tokens=1000,
            stream=True
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    
    def ask(
        self, 
        question: str, 
        num_sources: int = 4, 
        temperature: float = None,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Simple synchronous Q&A method."""
        start_time = time.time()
        
        # Retrieve sources
        sources = self.retrieve_sources(question, num_sources, filters)
        
        # Build context
        context = self.build_context(sources)
        
        # Generate answer
        answer = self.generate_answer(question, context, temperature)
        
        processing_time = time.time() - start_time
        
        return {
            'answer': answer,
            'sources': sources,
            'question': question,
            'processing_time': processing_time
        }
    
    async def ask_async(
        self, 
        question: str, 
        num_sources: int = 4, 
        temperature: float = None,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Async Q&A method."""
        start_time = time.time()
        
        # Retrieve sources (sync for now, could be made async)
        sources = await asyncio.to_thread(self.retrieve_sources, question, num_sources, filters)
        
        # Build context
        context = self.build_context(sources)
        
        # Generate answer
        answer = await self.generate_answer_async(question, context, temperature)
        
        processing_time = time.time() - start_time
        
        return {
            'answer': answer,
            'sources': sources,
            'question': question,
            'processing_time': processing_time
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        stats = self.vector_store.get_collection_stats()
        return {
            'total_documents': stats['total_documents'],
            'embedding_dimension': stats['embedding_dimension'],
            'index_size': stats['index_size'],
            'model': self.model,
            'embeddings_model': 'text-embedding-3-small'
        }
    
    def get_filter_statistics(self) -> Dict[str, Any]:
        """Get filter statistics for available documents."""
        # Get all documents metadata from vector store
        # For now, we'll get a large sample to calculate statistics
        # In production, this could be cached or pre-calculated
        sample_size = 1000  # Get a good sample size
        results = self.vector_store.similarity_search_with_score("", k=sample_size)
        
        # Extract unique documents by video_id
        unique_docs = {}
        for doc_text, score, metadata in results:
            video_id = metadata.get('video_id', metadata.get('source', ''))
            if video_id and video_id not in unique_docs:
                unique_docs[video_id] = metadata
        
        # Convert to list for statistics calculation
        documents = [{'metadata': metadata} for metadata in unique_docs.values()]
        
        # Calculate statistics using metadata enhancer
        return self.metadata_enhancer.get_filter_statistics(documents)