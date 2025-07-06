#!/usr/bin/env python3
"""
Basic functionality test for SpotGamma RAG system.
Tests the core components without complex chain orchestration.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import consts
from config import Config
from vector_store_faiss import FAISSVectorStore
from langchain_openai import ChatOpenAI

def test_retrieval_and_qa():
    print("="*60)
    print("Testing Basic RAG Functionality with SpotGamma Data")
    print("="*60)
    
    # Initialize
    config = Config(consts.CONFIG_PATH)
    store = FAISSVectorStore(config, persist_directory="db")
    
    # Test queries
    test_queries = [
        "What is gamma in options trading?",
        "How do gamma squeezes work?",
        "What does SpotGamma say about 0DTE options?",
        "Explain dealer gamma positioning"
    ]
    
    # Initialize LLM (o3 doesn't support temperature)
    llm = ChatOpenAI(
        model=config.openai_model(),
        openai_api_key=config.openai_api_key(),
        openai_organization=config.openai_org_id(),
        max_completion_tokens=500
    )
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Question: {query}")
        print(f"{'='*60}")
        
        # Retrieve relevant documents
        results = store.similarity_search_with_score(query, k=3)
        
        print(f"\nFound {len(results)} relevant documents:")
        
        # Build context from results
        context_parts = []
        sources = []
        
        for i, (content, score, metadata) in enumerate(results):
            print(f"\n{i+1}. {metadata.get('title', 'Unknown')} (score: {score:.3f})")
            print(f"   Source: {metadata.get('url', 'Unknown')}")
            print(f"   Preview: {content[:100]}...")
            
            context_parts.append(f"Document {i+1}: {content}")
            sources.append({
                "title": metadata.get('title', 'Unknown'),
                "url": metadata.get('url', 'Unknown'),
                "score": score
            })
        
        # Create prompt
        context = "\n\n".join(context_parts)
        prompt = f"""Based on the following context, please answer the question.

Context:
{context}

Question: {query}

Answer:"""
        
        # Get answer from LLM
        print("\nGenerating answer...")
        try:
            response = llm.invoke(prompt)
            answer = response.content
            
            print(f"\nAnswer: {answer[:500]}{'...' if len(answer) > 500 else ''}")
            
        except Exception as e:
            print(f"\nError generating answer: {e}")
    
    print("\n\n" + "="*60)
    print("Basic functionality test complete!")
    print("="*60)

def test_vector_store_stats():
    print("\n\nVector Store Statistics:")
    print("-"*30)
    
    config = Config(consts.CONFIG_PATH)
    store = FAISSVectorStore(config, persist_directory="db")
    
    stats = store.get_collection_stats()
    print(f"Total documents: {stats['total_documents']}")
    print(f"Index size: {stats['index_size']}")
    if 'dimension' in stats:
        print(f"Dimension: {stats['dimension']}")

if __name__ == '__main__':
    test_retrieval_and_qa()
    test_vector_store_stats()