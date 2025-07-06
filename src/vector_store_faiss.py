#!/usr/bin/env python3
"""
Lightweight FAISS vector store for OpenAI embeddings.
This replaces ChromaDB for a minimal dependency setup.
"""

import os
import json
import numpy as np
import faiss
from typing import List, Dict, Tuple, Optional
from openai import OpenAI

class FAISSVectorStore:
    def __init__(self, config, persist_directory="db"):
        self.config = config
        self.persist_directory = persist_directory
        self.index = None
        self.documents = []
        self.metadata = []
        self.dimension = 1536  # OpenAI embedding dimension
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=config.openai_api_key(),
            organization=config.openai_org_id()
        )
        
        # Create persist directory if it doesn't exist
        os.makedirs(persist_directory, exist_ok=True)
        
        # File paths
        self.index_path = os.path.join(persist_directory, "faiss.index")
        self.docs_path = os.path.join(persist_directory, "documents.json")
        self.meta_path = os.path.join(persist_directory, "metadata.json")
        
        # Load existing index if available
        self.load()
    
    def load(self):
        """Load existing index and data from disk."""
        if os.path.exists(self.index_path):
            print(f"Loading existing FAISS index from {self.index_path}")
            self.index = faiss.read_index(self.index_path)
            
            if os.path.exists(self.docs_path):
                with open(self.docs_path, 'r') as f:
                    self.documents = json.load(f)
            
            if os.path.exists(self.meta_path):
                with open(self.meta_path, 'r') as f:
                    self.metadata = json.load(f)
        else:
            print("Creating new FAISS index")
            self.index = faiss.IndexFlatL2(self.dimension)
    
    def save(self):
        """Save index and data to disk."""
        print(f"Saving FAISS index to {self.index_path}")
        faiss.write_index(self.index, self.index_path)
        
        with open(self.docs_path, 'w') as f:
            json.dump(self.documents, f)
        
        with open(self.meta_path, 'w') as f:
            json.dump(self.metadata, f)
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using OpenAI API."""
        # OpenAI recommends removing newlines for better performance
        texts = [text.replace("\n", " ") for text in texts]
        
        # Get embeddings from OpenAI
        response = self.client.embeddings.create(
            model="text-embedding-3-small",  # Cheaper and faster than ada-002
            input=texts
        )
        
        # Extract embeddings
        embeddings = []
        for item in response.data:
            embeddings.append(item.embedding)
        
        return np.array(embeddings, dtype=np.float32)
    
    def add_texts(self, texts: List[str], metadatas: Optional[List[Dict]] = None):
        """Add texts with their embeddings to the vector store."""
        if not texts:
            return
        
        # Generate embeddings
        print(f"Generating embeddings for {len(texts)} texts...")
        embeddings = self.embed_texts(texts)
        
        # Add to FAISS index
        self.index.add(embeddings)
        
        # Store documents and metadata
        self.documents.extend(texts)
        if metadatas:
            self.metadata.extend(metadatas)
        else:
            self.metadata.extend([{}] * len(texts))
        
        # Save to disk
        self.save()
        
        print(f"Added {len(texts)} documents to vector store")
    
    def similarity_search(self, query: str, k: int = 4) -> List[Tuple[str, Dict]]:
        """Search for similar documents."""
        # Get query embedding
        query_embedding = self.embed_texts([query])[0]
        
        # Search in FAISS
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1), k
        )
        
        # Return documents with metadata
        results = []
        for idx in indices[0]:
            if idx >= 0 and idx < len(self.documents):
                results.append((
                    self.documents[idx],
                    self.metadata[idx] if idx < len(self.metadata) else {}
                ))
        
        return results
    
    def similarity_search_with_score(self, query: str, k: int = 4) -> List[Tuple[str, float, Dict]]:
        """Search for similar documents with similarity scores."""
        # Get query embedding
        query_embedding = self.embed_texts([query])[0]
        
        # Search in FAISS
        distances, indices = self.index.search(
            query_embedding.reshape(1, -1), k
        )
        
        # Return documents with scores and metadata
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.documents):
                # Convert L2 distance to similarity score (0-1)
                # Lower distance = higher similarity
                score = 1 / (1 + distances[0][i])
                results.append((
                    self.documents[idx],
                    score,
                    self.metadata[idx] if idx < len(self.metadata) else {}
                ))
        
        return results
    
    def delete_collection(self):
        """Delete the entire collection."""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []
        self.metadata = []
        
        # Remove files
        for path in [self.index_path, self.docs_path, self.meta_path]:
            if os.path.exists(path):
                os.remove(path)
        
        print("Collection deleted")
    
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection."""
        return {
            "total_documents": len(self.documents),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.dimension,
            "persist_directory": self.persist_directory
        }