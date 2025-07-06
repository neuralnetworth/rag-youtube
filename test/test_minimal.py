#!/usr/bin/env python3
"""
Minimal test to verify basic functionality.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import consts
from config import Config
from vector_store_faiss import FAISSVectorStore

def test_vector_store():
    print("Testing FAISS Vector Store...")
    
    config = Config(consts.CONFIG_PATH)
    store = FAISSVectorStore(config, persist_directory="db")
    
    # Test search
    results = store.similarity_search("What is gamma?", k=3)
    print(f"\nFound {len(results)} results")
    
    for i, (content, metadata) in enumerate(results):
        print(f"\nResult {i+1}:")
        print(f"Content: {content[:100]}...")
        print(f"Source: {metadata.get('source', 'Unknown')}")
        print(f"Title: {metadata.get('title', 'Unknown')}")
    
    # Test search with scores
    results_with_scores = store.similarity_search_with_score("0DTE options", k=2)
    print(f"\n\nSearch with scores found {len(results_with_scores)} results")
    
    for i, (content, score, metadata) in enumerate(results_with_scores):
        print(f"\nResult {i+1} (score: {score:.4f}):")
        print(f"Content: {content[:100]}...")
        print(f"Source: {metadata.get('source', 'Unknown')}")

def test_agent_qa():
    print("\n\n" + "="*60)
    print("Testing Agent QA...")
    
    from agent_qa_faiss import AgentQA
    from chain_base import ChainParameters
    
    config = Config(consts.CONFIG_PATH)
    agent = AgentQA(config)
    
    # Create parameters manually
    overrides = {
        "chain_type": "qa_sources",
        "document_count": "3",
        "search_type": "similarity"
    }
    params = ChainParameters(config, overrides)
    params.question = "What is gamma in options trading?"
    params.llm_retriever_compression = False
    params.llm_retriever_multiquery = False
    params.memory = None
    params.memory_window_size = 5
    
    try:
        result = agent.ask(params)
        print(f"\nQuestion: {params.question}")
        print(f"Answer: {result.get('answer', 'No answer')[:200]}...")
        print(f"Sources: {len(result.get('sources', []))} sources found")
        
        for source in result.get('sources', [])[:2]:
            print(f"  - {source.get('title', 'Unknown')}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_vector_store()
    test_agent_qa()