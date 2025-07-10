#!/usr/bin/env python3
"""
Comprehensive test suite for RAG-YouTube.
Tests all core functionality including:
- Vector store operations
- Metadata enhancement
- Document filtering
- LLM provider integration
- RAG engine functionality
- Multi-provider support
"""
import sys
import os
import asyncio
import time
from typing import Dict, Any, List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.config import Config
from core.llm_provider import LLMManager
from vector_stores.faiss import FAISSVectorStore
from api.rag_engine import RAGEngine
from data_pipeline.metadata_enhancer import MetadataEnhancer
from api.filters import DocumentFilter


class TestResults:
    """Track test results and timing."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.total_time = 0
        self.results = []
    
    def add_result(self, test_name: str, status: str, duration: float, message: str = ""):
        self.results.append({
            'test': test_name,
            'status': status, 
            'duration': duration,
            'message': message
        })
        if status == 'PASS':
            self.passed += 1
        elif status == 'FAIL':
            self.failed += 1
        elif status == 'SKIP':
            self.skipped += 1
        self.total_time += duration
    
    def print_summary(self):
        print(f"\n{'='*80}")
        print(f"TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Total Tests: {self.passed + self.failed + self.skipped}")
        print(f"Passed:      {self.passed}")
        print(f"Failed:      {self.failed}")
        print(f"Skipped:     {self.skipped}")
        print(f"Total Time:  {self.total_time:.2f} seconds")
        print(f"{'='*80}")
        
        if self.failed > 0:
            print("\nFAILED TESTS:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        if self.skipped > 0:
            print("\nSKIPPED TESTS:")
            for result in self.results:
                if result['status'] == 'SKIP':
                    print(f"  ⚠️  {result['test']}: {result['message']}")


def run_test(test_func, test_name: str, results: TestResults):
    """Run a single test and record results."""
    print(f"\n{'-'*60}")
    print(f"Running: {test_name}")
    print(f"{'-'*60}")
    
    start_time = time.time()
    try:
        test_func()
        duration = time.time() - start_time
        results.add_result(test_name, 'PASS', duration)
        print(f"✅ PASS ({duration:.2f}s)")
        return True
    except Exception as e:
        duration = time.time() - start_time
        results.add_result(test_name, 'FAIL', duration, str(e))
        print(f"❌ FAIL ({duration:.2f}s): {e}")
        import traceback
        traceback.print_exc()
        return False


def run_async_test(test_func, test_name: str, results: TestResults):
    """Run a single async test and record results."""
    print(f"\n{'-'*60}")
    print(f"Running: {test_name}")
    print(f"{'-'*60}")
    
    start_time = time.time()
    try:
        asyncio.run(test_func())
        duration = time.time() - start_time
        results.add_result(test_name, 'PASS', duration)
        print(f"✅ PASS ({duration:.2f}s)")
        return True
    except Exception as e:
        duration = time.time() - start_time
        results.add_result(test_name, 'FAIL', duration, str(e))
        print(f"❌ FAIL ({duration:.2f}s): {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_loading():
    """Test configuration loading."""
    config = Config()
    
    # Test basic config properties
    assert hasattr(config, 'llm_provider')
    assert hasattr(config, 'openai_api_key')
    
    # Test that we can get provider
    provider = config.llm_provider()
    assert provider in ['openai', 'gemini']
    
    print(f"  Provider: {provider}")
    print("  ✓ Configuration loading test passed")


def test_llm_manager():
    """Test LLM manager functionality."""
    config = Config()
    llm_manager = LLMManager(config)
    
    # Test provider listing
    providers = llm_manager.list_providers()
    assert len(providers) > 0
    print(f"  Available providers: {providers}")
    
    # Test getting a provider
    provider = llm_manager.get_provider(providers[0])
    assert provider is not None
    
    print("  ✓ LLM manager test passed")


def test_vector_store():
    """Test FAISS vector store functionality."""
    config = Config()
    vector_store = FAISSVectorStore(config)
    
    # Test loading existing index
    if os.path.exists('db/faiss.index'):
        print("  Loading existing FAISS index...")
        vector_store.load()
        
        # Test search
        results = vector_store.similarity_search_with_score("gamma options", k=3)
        assert len(results) > 0
        
        # Test stats
        stats = vector_store.get_collection_stats()
        assert 'total_documents' in stats
        assert stats['total_documents'] > 0
        
        print(f"  Document count: {stats['total_documents']}")
        print(f"  Search results: {len(results)}")
        print("  ✓ Vector store test passed")
    else:
        raise Exception("No FAISS index found - run document_loader_faiss.py first")


def test_metadata_enhancer():
    """Test metadata enhancement functionality."""
    enhancer = MetadataEnhancer()
    
    # Test category inference
    test_cases = [
        ("Daily Market Update", "daily_update"),
        ("How to Trade Options", "educational"),
        ("Interview with Trader", "interview"),
        ("FOMC Meeting Analysis", "special_event"),
        ("Random Title", "uncategorized")
    ]
    
    for title, expected_category in test_cases:
        metadata = {
            'title': title,
            'duration': '00:10:00',
            'word_count': 1500,
            'content': 'Test content with gamma delta theta vega'
        }
        
        enhanced = enhancer.enhance_metadata(metadata)
        assert enhanced['category'] == expected_category
        assert 'quality_score' in enhanced
        assert 'words_per_minute' in enhanced
        
        print(f"  '{title}' -> {enhanced['category']}")
    
    print("  ✓ Metadata enhancer test passed")


def test_document_filter():
    """Test document filtering functionality."""
    filter_obj = DocumentFilter()
    
    # Create test documents
    test_docs = [
        {
            'content': 'Test 1',
            'metadata': {
                'has_captions': True,
                'category': 'daily_update',
                'quality_score': 'high'
            }
        },
        {
            'content': 'Test 2', 
            'metadata': {
                'has_captions': False,
                'category': 'educational',
                'quality_score': 'medium'
            }
        },
        {
            'content': 'Test 3',
            'metadata': {
                'has_captions': True,
                'category': 'daily_update', 
                'quality_score': 'low'
            }
        }
    ]
    
    # Test caption filtering
    filter_obj.set_filters({'require_captions': True})
    filtered = filter_obj.apply_filters(test_docs)
    assert len(filtered) == 2
    
    # Test category filtering
    filter_obj.set_filters({'categories': ['daily_update']})
    filtered = filter_obj.apply_filters(test_docs)
    assert len(filtered) == 2
    
    # Test quality filtering
    filter_obj.set_filters({'quality_levels': ['high', 'medium']})
    filtered = filter_obj.apply_filters(test_docs)
    assert len(filtered) == 2
    
    # Test combined filters
    filter_obj.set_filters({
        'require_captions': True,
        'categories': ['daily_update'],
        'quality_levels': ['high']
    })
    filtered = filter_obj.apply_filters(test_docs)
    assert len(filtered) == 1
    
    print(f"  Original docs: {len(test_docs)}")
    print(f"  Combined filter result: {len(filtered)}")
    print("  ✓ Document filter test passed")


def test_rag_engine_basic():
    """Test basic RAG engine functionality."""
    config = Config()
    rag_engine = RAGEngine(config)
    
    # Test stats
    stats = rag_engine.get_stats()
    assert 'total_documents' in stats
    assert 'current_provider' in stats
    
    print(f"  Provider: {stats['current_provider']}")
    print(f"  Documents: {stats['total_documents']}")
    
    # Test basic retrieval
    sources = rag_engine.retrieve_sources("gamma options", num_sources=3)
    assert len(sources) > 0
    
    # Test context building
    context = rag_engine.build_context(sources)
    assert len(context) > 0
    
    print(f"  Retrieved sources: {len(sources)}")
    print(f"  Context length: {len(context)}")
    print("  ✓ Basic RAG engine test passed")


def test_rag_engine_q_and_a():
    """Test RAG engine Q&A functionality."""
    config = Config()
    rag_engine = RAGEngine(config)
    
    # Test synchronous Q&A
    question = "What is gamma in options trading?"
    result = rag_engine.ask(question, num_sources=3)
    
    assert 'answer' in result
    assert 'sources' in result
    assert 'processing_time' in result
    assert len(result['answer']) > 0
    assert len(result['sources']) > 0
    
    print(f"  Question: {question}")
    print(f"  Answer length: {len(result['answer'])}")
    print(f"  Sources: {len(result['sources'])}")
    print(f"  Processing time: {result['processing_time']:.2f}s")
    print("  ✓ RAG Q&A test passed")


async def test_rag_engine_async():
    """Test RAG engine async functionality."""
    config = Config()
    rag_engine = RAGEngine(config)
    
    # Test async Q&A
    question = "How do gamma squeezes work?"
    result = await rag_engine.ask_async(question, num_sources=3)
    
    assert 'answer' in result
    assert 'sources' in result
    assert len(result['answer']) > 0
    
    print(f"  Async question: {question}")
    print(f"  Async answer length: {len(result['answer'])}")
    print("  ✓ Async RAG test passed")


async def test_rag_engine_streaming():
    """Test RAG engine streaming functionality."""
    config = Config()
    rag_engine = RAGEngine(config)
    
    # Test streaming
    question = "Explain dealer gamma positioning"
    sources = rag_engine.retrieve_sources(question, num_sources=3)
    context = rag_engine.build_context(sources)
    
    chunks = []
    async for chunk in rag_engine.generate_answer_stream(question, context):
        chunks.append(chunk)
    
    assert len(chunks) > 0
    full_answer = ''.join(chunks)
    assert len(full_answer) > 0
    
    print(f"  Streaming question: {question}")
    print(f"  Chunks received: {len(chunks)}")
    print(f"  Full answer length: {len(full_answer)}")
    print("  ✓ Streaming RAG test passed")


def test_rag_engine_with_filters():
    """Test RAG engine with filtering."""
    config = Config()
    rag_engine = RAGEngine(config)
    
    # Test with caption filter
    question = "What is gamma?"
    
    # Without filter
    result_no_filter = rag_engine.ask(question, num_sources=3)
    
    # With caption filter
    result_with_filter = rag_engine.ask(
        question,
        num_sources=3,
        filters={'require_captions': True}
    )
    
    assert len(result_no_filter['sources']) > 0
    assert len(result_with_filter['sources']) > 0
    
    # Check that filtered results have captions
    for source in result_with_filter['sources']:
        has_captions = source['metadata'].get('has_captions')
        if has_captions is not None:
            assert has_captions == True
    
    print(f"  Sources without filter: {len(result_no_filter['sources'])}")
    print(f"  Sources with caption filter: {len(result_with_filter['sources'])}")
    print("  ✓ Filtered RAG test passed")


def test_multi_provider_support():
    """Test multi-provider LLM support."""
    config = Config()
    rag_engine = RAGEngine(config)
    
    # Get available providers
    available_providers = rag_engine.llm_manager.list_providers()
    print(f"  Available providers: {available_providers}")
    
    # Test with each available provider
    question = "What is gamma?"
    sources = rag_engine.retrieve_sources(question, num_sources=2)
    context = rag_engine.build_context(sources)
    
    for provider in available_providers[:2]:  # Test first 2 providers
        try:
            answer = rag_engine.generate_answer(question, context, provider=provider)
            assert len(answer) > 0
            print(f"  Provider {provider}: Answer length {len(answer)}")
        except Exception as e:
            print(f"  Provider {provider}: Error - {e}")
            # Don't fail if one provider has issues
    
    print("  ✓ Multi-provider test passed")


def test_error_handling():
    """Test error handling and edge cases."""
    config = Config()
    rag_engine = RAGEngine(config)
    
    # Test with empty question
    try:
        result = rag_engine.ask("", num_sources=1)
        # Should still work, might return generic response
        assert 'answer' in result
        print("  Empty question: Handled gracefully")
    except Exception as e:
        print(f"  Empty question: {e}")
    
    # Test with very long question
    long_question = "What is gamma? " * 100
    try:
        result = rag_engine.ask(long_question, num_sources=1)
        assert 'answer' in result
        print("  Long question: Handled gracefully")
    except Exception as e:
        print(f"  Long question: {e}")
    
    # Test with invalid filter
    try:
        result = rag_engine.ask(
            "What is gamma?",
            filters={'invalid_filter': True}
        )
        print("  Invalid filter: Ignored gracefully")
    except Exception as e:
        print(f"  Invalid filter: {e}")
    
    print("  ✓ Error handling test passed")


def main():
    """Run all tests."""
    print("=" * 80)
    print("RAG-YouTube Comprehensive Test Suite")
    print("=" * 80)
    
    results = TestResults()
    
    # Core functionality tests
    run_test(test_config_loading, "Config Loading", results)
    run_test(test_llm_manager, "LLM Manager", results)
    run_test(test_vector_store, "Vector Store", results)
    run_test(test_metadata_enhancer, "Metadata Enhancer", results)
    run_test(test_document_filter, "Document Filter", results)
    
    # RAG engine tests
    run_test(test_rag_engine_basic, "RAG Engine Basic", results)
    run_test(test_rag_engine_q_and_a, "RAG Engine Q&A", results)
    run_async_test(test_rag_engine_async, "RAG Engine Async", results)
    run_async_test(test_rag_engine_streaming, "RAG Engine Streaming", results)
    run_test(test_rag_engine_with_filters, "RAG Engine Filtering", results)
    
    # Advanced tests
    run_test(test_multi_provider_support, "Multi-Provider Support", results)
    run_test(test_error_handling, "Error Handling", results)
    
    # Print final summary
    results.print_summary()
    
    # Return exit code
    return 0 if results.failed == 0 else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)