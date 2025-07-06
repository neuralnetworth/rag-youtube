#!/usr/bin/env python3
"""
Helper functions for tests.
"""
from chain_base import ChainParameters

def create_qa_parameters(config, question, chain="qa_sources", **kwargs):
    """Create properly configured ChainParameters for QA testing."""
    overrides = {
        "chain": chain,
        **kwargs
    }
    params = ChainParameters(config, overrides)
    
    # Add required attributes for FAISS agent
    params.question = question
    params.llm_retriever_compression = kwargs.get("llm_retriever_compression", False)
    params.llm_retriever_multiquery = kwargs.get("llm_retriever_multiquery", False)
    params.memory = kwargs.get("memory", None)
    params.memory_window_size = kwargs.get("memory_window_size", 5)
    
    return params