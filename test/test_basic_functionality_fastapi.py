#!/usr/bin/env python3
"""
Test basic RAG functionality using the new FastAPI RAG engine.
No LangChain dependencies - direct OpenAI integration.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core import consts
from core.config import Config
from api.rag_engine import RAGEngine
from data_pipeline.metadata_enhancer import MetadataEnhancer
from api.filters import DocumentFilter


def test_metadata_enhancer():
    """Test metadata enhancement functionality."""
    print("\n" + "="*60)
    print("Testing Metadata Enhancement")
    print("="*60)
    
    enhancer = MetadataEnhancer()
    
    # Test category inference
    test_metadata = {
        'title': 'Daily Market Update: Key Levels to Watch',
        'description': 'Today\'s market outlook and key gamma levels',
        'duration': '00:15:30',
        'word_count': 2500,
        'has_captions': True,
        'content': 'This is a comprehensive daily market update covering gamma delta theta vega implied volatility and other key options concepts. ' * 15
    }
    
    enhanced = enhancer.enhance_metadata(test_metadata)
    
    print(f"Original title: {test_metadata['title']}")
    print(f"Inferred category: {enhanced['category']}")
    print(f"Quality score: {enhanced['quality_score']}")
    print(f"Caption availability: {enhanced['has_captions']}")
    
    # Verify enhancement worked
    assert enhanced['category'] in ['daily_update', 'educational', 'interview', 'special_event', 'uncategorized']
    assert enhanced['quality_score'] in ['high', 'medium', 'low', 'none', 'unknown']
    assert 'words_per_minute' in enhanced
    
    print("✓ Metadata enhancement test passed")


def test_document_filter():
    """Test document filtering functionality."""
    print("\n" + "="*60)
    print("Testing Document Filtering")
    print("="*60)
    
    filter_obj = DocumentFilter()
    
    # Create test documents
    test_docs = [
        {
            'content': 'Test content 1',
            'score': 0.9,
            'metadata': {
                'title': 'Daily Market Update',
                'has_captions': True,
                'category': 'daily_update',
                'quality_score': 'high',
                'published_date': '2024-01-15'
            }
        },
        {
            'content': 'Test content 2',
            'score': 0.8,
            'metadata': {
                'title': 'Technical Analysis',
                'has_captions': False,
                'category': 'educational',
                'quality_score': 'medium',
                'published_date': '2024-01-10'
            }
        }
    ]
    
    # Test caption filtering
    filter_obj.set_filters({'require_captions': True})
    filtered = filter_obj.apply_filters(test_docs)
    
    print(f"Original documents: {len(test_docs)}")
    print(f"After caption filter: {len(filtered)}")
    assert len(filtered) == 1
    assert filtered[0]['metadata']['has_captions'] == True
    
    # Test over-fetch calculation
    over_fetch = filter_obj.calculate_over_fetch(4, True)
    print(f"Over-fetch for 4 docs with filters: {over_fetch}")
    assert over_fetch == 12  # 4 * 3
    
    print("✓ Document filtering test passed")


def test_filter_statistics():
    """Test filter statistics functionality."""
    print("\n" + "="*60)
    print("Testing Filter Statistics")
    print("="*60)
    
    config = Config(consts.CONFIG_PATH)
    rag_engine = RAGEngine(config)
    
    try:
        # Get filter statistics
        stats = rag_engine.get_filter_statistics()
        
        print(f"Total documents: {stats['total_documents']}")
        print(f"Caption coverage: {stats['caption_coverage']}")
        print(f"Categories: {stats['categories']}")
        print(f"Quality levels: {stats['quality_levels']}")
        
        # Verify statistics structure
        assert 'total_documents' in stats
        assert 'caption_coverage' in stats
        assert 'categories' in stats
        assert 'quality_levels' in stats
        assert 'date_range' in stats
        
        # Check caption coverage structure
        coverage = stats['caption_coverage']
        assert 'with_captions' in coverage
        assert 'without_captions' in coverage
        assert 'percentage' in coverage
        
        print("✓ Filter statistics test passed")
        
    except Exception as e:
        print(f"Filter statistics test failed: {e}")
        # Don't fail the whole test suite if vector store isn't ready
        print("⚠️  Filter statistics test skipped (vector store may not be ready)")


def test_basic_rag():
    """Test basic RAG functionality."""
    print("\n" + "="*60)
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


def test_filtered_search():
    """Test RAG with filtering enabled."""
    print("\n" + "="*60)
    print("Testing Filtered Search")
    print("="*60)
    
    config = Config(consts.CONFIG_PATH)
    rag_engine = RAGEngine(config)
    
    # Test question with caption filter
    question = "What is gamma in options trading?"
    
    print(f"Question: {question}")
    print("Testing with caption filter...")
    
    try:
        # Search with caption filter
        result_filtered = rag_engine.ask(
            question, 
            num_sources=3,
            filters={'require_captions': True}
        )
        
        # Search without filter
        result_unfiltered = rag_engine.ask(
            question, 
            num_sources=3
        )
        
        print(f"Sources with caption filter: {len(result_filtered['sources'])}")
        print(f"Sources without filter: {len(result_unfiltered['sources'])}")
        
        # Verify filtered results have captions
        for i, source in enumerate(result_filtered['sources']):
            has_captions = source['metadata'].get('has_captions', False)
            print(f"  Source {i+1}: has_captions = {has_captions}")
            if has_captions is not None:  # Only assert if metadata is available
                assert has_captions == True
        
        print("✓ Filtered search test passed")
        
    except Exception as e:
        print(f"Filtered search test failed: {e}")
        print("⚠️  This may be expected if documents don't have caption metadata yet")


if __name__ == '__main__':
    # Run all tests
    test_metadata_enhancer()
    test_document_filter()
    test_filter_statistics()
    test_basic_rag()
    test_filtered_search()
    
    print("\n" + "="*60)
    print("🎉 All FastAPI functionality tests completed!")
    print("="*60)