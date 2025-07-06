#!/usr/bin/env python3
"""
Test basic RAG functionality using the new FastAPI RAG engine.
No LangChain dependencies - direct OpenAI integration.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import consts
from config import Config
from api.rag_engine import RAGEngine


def test_basic_rag():
    """Test basic RAG functionality."""
    print("="*60)
    print("Testing Basic RAG Functionality (FastAPI Implementation)")
    print("="*60)
    
    # Initialize
    config = Config(consts.CONFIG_PATH)
    rag_engine = RAGEngine(config)
    
    # Test questions
    test_questions = [
        "What is gamma in options trading?",
        "How do gamma squeezes work?", 
        "What does SpotGamma say about 0DTE options?",
        "Explain dealer gamma positioning"
    ]
    
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}")
        
        try:
            # Ask the question using our new RAG engine
            result = rag_engine.ask(question, num_sources=3)
            
            print(f"\nFound {len(result['sources'])} relevant documents:\n")
            
            # Display sources
            for i, source in enumerate(result['sources'], 1):
                title = source['metadata'].get('title', 'Unknown title')
                url = source['metadata'].get('url', 'Unknown URL')
                score = source['score']
                preview = source['content'][:100] + "..."
                
                print(f"{i}. {title} (score: {score:.3f})")
                print(f"   Source: {url}")
                print(f"   Preview: {preview}\n")
            
            print("Generating answer...")
            print(f"\nAnswer: {result['answer']}")
            print(f"\nProcessing time: {result['processing_time']:.2f} seconds")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("Basic functionality test complete!")
    print(f"{'='*60}")
    
    # Display stats
    print("\n\nVector Store Statistics:")
    print("-"*30)
    stats = rag_engine.get_stats()
    print(f"Total documents: {stats['total_documents']}")
    print(f"Index size: {stats['index_size']}")
    print(f"Model: {stats['model']}")
    print(f"Embeddings model: {stats['embeddings_model']}")


if __name__ == '__main__':
    test_basic_rag()