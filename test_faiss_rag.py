#!/usr/bin/env python3
"""
Test script for FAISS RAG system with SpotGamma data.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import consts
from config import Config
from agent_qa_faiss import AgentQA
from chain_base import ChainParameters

def test_rag():
    print("Testing FAISS RAG System with SpotGamma data...\n")
    
    # Initialize
    config = Config(consts.CONFIG_PATH)
    agent = AgentQA(config)
    
    # Test questions
    test_questions = [
        "What is gamma in options trading?",
        "How do gamma squeezes work?",
        "What is SpotGamma's approach to market analysis?",
        "Explain the relationship between options flow and market movement",
        "What is 0DTE and why is it important?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {question}")
        print(f"{'='*60}")
        
        # Create parameters with config and overrides
        overrides = {
            'question': question,
            'document_count': '4',
            'search_type': 'similarity',
            'chain': 'qa_sources',
            'return_sources': 'true'
        }
        params = ChainParameters(config, overrides)
        params.question = question  # Add question separately
        
        try:
            # Ask the question
            response = agent.ask(params)
            
            print(f"\nAnswer: {response['answer'][:500]}...")
            
            if 'sources' in response and response['sources']:
                print(f"\nSources ({len(response['sources'])} found):")
                for j, source in enumerate(response['sources'][:3], 1):
                    title = source.get('metadata', {}).get('title', 'Unknown')
                    url = source.get('metadata', {}).get('url', '')
                    print(f"  {j}. {title}")
                    print(f"     URL: {url}")
        
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n\nTest complete!")

if __name__ == '__main__':
    test_rag()