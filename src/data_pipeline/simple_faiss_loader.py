#!/usr/bin/env python3
"""
Simple FAISS loader for document loading without legacy dependencies.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Dict, Any
from vector_stores.faiss import FAISSVectorStore


class SimpleFAISSLoader:
    """Simple FAISS loader for adding documents to the vector store."""
    
    def __init__(self, config):
        self.config = config
        self.vector_store = FAISSVectorStore(config, persist_directory=config.db_persist_directory())
        self.chunk_size = config.split_chunk_size()
        self.chunk_overlap = config.split_chunk_overlap()
    
    def add_text(self, content: str, metadata: Dict[str, Any]) -> None:
        """Add text content with metadata to the FAISS index."""
        # Simple text splitting - split by double newlines, then by size
        chunks = self._split_text(content)
        
        # Create metadata for each chunk
        metadatas = [metadata.copy() for _ in chunks]
        
        # Add to vector store
        self.vector_store.add_texts(chunks, metadatas)
    
    def _split_text(self, text: str) -> List[str]:
        """Simple text splitter without LangChain dependency."""
        # First split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk
            if current_chunk and len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                if len(current_chunk) > self.chunk_overlap:
                    overlap_text = current_chunk[-self.chunk_overlap:]
                    current_chunk = overlap_text + "\n\n" + paragraph
                else:
                    current_chunk = paragraph
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If we have very long chunks, split them further
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > self.chunk_size:
                # Split long chunks by sentence or at chunk_size
                words = chunk.split()
                current = ""
                for word in words:
                    if len(current) + len(word) + 1 > self.chunk_size:
                        if current:
                            final_chunks.append(current.strip())
                        current = word
                    else:
                        current += " " + word if current else word
                if current:
                    final_chunks.append(current.strip())
            else:
                final_chunks.append(chunk)
        
        return final_chunks