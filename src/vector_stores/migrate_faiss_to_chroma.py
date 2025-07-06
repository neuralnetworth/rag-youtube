#!/usr/bin/env python3
"""
Migration script to transfer embeddings from FAISS to ChromaDB.
This allows reusing already-computed embeddings when switching to GPU setup.

Usage:
    ./src/migrate_faiss_to_chroma.py [--source-dir db] [--target-dir db_chroma]
"""

import os
import sys
import json
import argparse
import numpy as np
from typing import List, Dict

def migrate_embeddings(source_dir: str = "db", target_dir: str = "db_chroma"):
    """
    Migrate embeddings from FAISS to ChromaDB format.
    
    Args:
        source_dir: Directory containing FAISS index and metadata
        target_dir: Directory where ChromaDB will be initialized
    """
    print(f"Migrating from FAISS ({source_dir}) to ChromaDB ({target_dir})...")
    
    # Check if source files exist
    docs_path = os.path.join(source_dir, "documents.json")
    meta_path = os.path.join(source_dir, "metadata.json")
    index_path = os.path.join(source_dir, "faiss.index")
    
    if not all(os.path.exists(p) for p in [docs_path, meta_path, index_path]):
        print(f"Error: Source FAISS files not found in {source_dir}")
        print("Required files: faiss.index, documents.json, metadata.json")
        return False
    
    try:
        # Import required libraries
        import faiss
        from langchain_community.vectorstores import Chroma
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain.schema import Document
        
        # Load FAISS data
        print("Loading FAISS data...")
        with open(docs_path, 'r') as f:
            documents = json.load(f)
        
        with open(meta_path, 'r') as f:
            metadata = json.load(f)
        
        # Load FAISS index
        index = faiss.read_index(index_path)
        
        print(f"Found {len(documents)} documents to migrate")
        
        # Extract embeddings from FAISS
        print("Extracting embeddings from FAISS index...")
        embeddings_array = np.zeros((index.ntotal, index.d), dtype=np.float32)
        for i in range(index.ntotal):
            embeddings_array[i] = index.reconstruct(i)
        
        # Create ChromaDB with dummy embeddings function
        # We'll add documents with pre-computed embeddings
        print("Initializing ChromaDB...")
        
        class PrecomputedEmbeddings:
            """Dummy embeddings class that returns pre-computed embeddings."""
            def __init__(self, embeddings_dict):
                self.embeddings_dict = embeddings_dict
                self.embed_documents_calls = 0
            
            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                """Return pre-computed embeddings for texts."""
                result = []
                for text in texts:
                    if text in self.embeddings_dict:
                        result.append(self.embeddings_dict[text])
                    else:
                        # This shouldn't happen in migration
                        raise ValueError(f"No pre-computed embedding for text: {text[:50]}...")
                return result
            
            def embed_query(self, text: str) -> List[float]:
                """For queries, we'll use the actual embedding model."""
                # This won't be called during migration
                raise NotImplementedError("Use actual embeddings for queries")
        
        # Create mapping of documents to embeddings
        embeddings_dict = {}
        for i, doc in enumerate(documents):
            if i < len(embeddings_array):
                embeddings_dict[doc] = embeddings_array[i].tolist()
        
        # Initialize ChromaDB with pre-computed embeddings
        embeddings_function = PrecomputedEmbeddings(embeddings_dict)
        
        # Create ChromaDB instance
        vectorstore = Chroma(
            persist_directory=target_dir,
            embedding_function=embeddings_function
        )
        
        # Add documents in batches
        batch_size = 100
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        print(f"Migrating documents in {total_batches} batches...")
        
        for batch_idx in range(0, len(documents), batch_size):
            batch_docs = documents[batch_idx:batch_idx + batch_size]
            batch_meta = metadata[batch_idx:batch_idx + batch_size]
            
            # Create LangChain documents
            langchain_docs = [
                Document(page_content=doc, metadata=meta)
                for doc, meta in zip(batch_docs, batch_meta)
            ]
            
            # Add to ChromaDB
            vectorstore.add_documents(langchain_docs)
            
            print(f"  Batch {batch_idx // batch_size + 1}/{total_batches} completed")
        
        # Persist ChromaDB
        vectorstore.persist()
        
        print(f"\n✅ Migration completed successfully!")
        print(f"ChromaDB initialized at: {target_dir}")
        print(f"Total documents migrated: {len(documents)}")
        
        # Save migration metadata
        migration_info = {
            "source": source_dir,
            "target": target_dir,
            "documents_count": len(documents),
            "embedding_dimension": index.d,
            "migration_date": str(np.datetime64('now'))
        }
        
        with open(os.path.join(target_dir, "migration_info.json"), 'w') as f:
            json.dump(migration_info, f, indent=2)
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nTo run migration, you need ChromaDB installed:")
        print("pip install chromadb langchain-community")
        return False
    
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Migrate embeddings from FAISS to ChromaDB"
    )
    parser.add_argument(
        "--source-dir",
        default="db",
        help="Source directory containing FAISS files (default: db)"
    )
    parser.add_argument(
        "--target-dir", 
        default="db_chroma",
        help="Target directory for ChromaDB (default: db_chroma)"
    )
    
    args = parser.parse_args()
    
    # Add src to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    success = migrate_embeddings(args.source_dir, args.target_dir)
    
    if success:
        print("\nNext steps:")
        print("1. Update your rag-youtube.conf:")
        print("   - Set embeddings model back to local (e.g., all-MiniLM-L6-v2)")
        print("   - Update db_persist_dir to", args.target_dir)
        print("2. Ensure ChromaDB dependencies are installed")
        print("3. Run the application normally")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()