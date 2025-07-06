#!/usr/bin/env python3
"""
Simple test for FAISS RAG system.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import consts
from config import Config
from vector_store_faiss import FAISSVectorStore

def test_simple_retrieval():
    print("Testing FAISS Vector Store directly...\n")
    
    # Initialize
    config = Config(consts.CONFIG_PATH)
    
    # Create vector store
    vector_store = FAISSVectorStore(
        config=config,
        persist_directory=config.db_persist_directory()
    )
    
    # Test questions
    test_questions = [
        "What is gamma in options trading?",
        "How do gamma squeezes work?",
        "What is 0DTE?"
    ]
    
    for i, query in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {query}")
        print(f"{'='*60}")
        
        try:
            # Search
            results = vector_store.similarity_search(query, k=3)
            
            print(f"\nFound {len(results)} results:")
            for j, (content, metadata) in enumerate(results, 1):
                print(f"\n--- Result {j} ---")
                print(f"Video: {metadata.get('title', 'Unknown')}")
                print(f"URL: {metadata.get('url', '')}")
                print(f"Content snippet: {content[:200]}...")
        
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n\nDirect vector store test complete!")

if __name__ == '__main__':
    test_simple_retrieval()