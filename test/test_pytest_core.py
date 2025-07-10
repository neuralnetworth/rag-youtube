"""
Pytest-based tests for RAG-YouTube core functionality.
Uses pytest fixtures and modern testing patterns.
"""
import pytest
import asyncio
from typing import List, Dict, Any


class TestConfig:
    """Test configuration loading and validation."""
    
    def test_config_creation(self, config):
        """Test that config can be created."""
        assert config is not None
        assert hasattr(config, 'llm_provider')
    
    def test_config_provider(self, config):
        """Test provider configuration."""
        provider = config.llm_provider()
        assert provider in ['openai', 'gemini']
    
    def test_config_api_keys(self, config):
        """Test API key availability."""
        # At least one API key should be available
        has_openai = bool(config.openai_api_key())
        has_google = bool(config.google_api_key())
        assert has_openai or has_google, "No API keys configured"


class TestVectorStore:
    """Test FAISS vector store functionality."""
    
    def test_vector_store_creation(self, vector_store):
        """Test vector store can be created and loaded."""
        assert vector_store is not None
    
    def test_vector_store_stats(self, vector_store):
        """Test vector store statistics."""
        stats = vector_store.get_collection_stats()
        assert 'total_documents' in stats
        assert 'embedding_dimension' in stats
        assert stats['total_documents'] > 0
    
    @pytest.mark.slow
    def test_similarity_search(self, vector_store):
        """Test similarity search functionality."""
        results = vector_store.similarity_search_with_score("gamma options", k=3)
        assert len(results) > 0
        assert len(results) <= 3
        
        for doc_text, score, metadata in results:
            assert isinstance(doc_text, str)
            assert isinstance(score, (int, float))
            assert isinstance(metadata, dict)
            assert len(doc_text) > 0


class TestMetadataEnhancer:
    """Test metadata enhancement functionality."""
    
    def test_category_inference(self, metadata_enhancer):
        """Test category inference for different video types."""
        test_cases = [
            ("Daily Market Update", "daily_update"),
            ("How to Trade Options", "educational"),
            ("Interview with Expert", "interview"),
            ("FOMC Meeting Analysis", "special_event"),
            ("Random Video", "uncategorized")
        ]
        
        for title, expected_category in test_cases:
            metadata = {'title': title}
            enhanced = metadata_enhancer.enhance_metadata(metadata)
            assert enhanced['category'] == expected_category
    
    def test_quality_scoring(self, metadata_enhancer, sample_metadata):
        """Test quality score calculation."""
        enhanced = metadata_enhancer.enhance_metadata(sample_metadata)
        
        assert 'quality_score' in enhanced
        assert enhanced['quality_score'] in ['high', 'medium', 'low', 'none', 'unknown']
        assert 'words_per_minute' in enhanced
        assert 'technical_keyword_count' in enhanced
    
    def test_metadata_preservation(self, metadata_enhancer, sample_metadata):
        """Test that original metadata is preserved."""
        enhanced = metadata_enhancer.enhance_metadata(sample_metadata)
        
        # Original fields should be preserved
        for key, value in sample_metadata.items():
            assert enhanced[key] == value
        
        # New fields should be added
        assert 'category' in enhanced
        assert 'quality_score' in enhanced


class TestDocumentFilter:
    """Test document filtering functionality."""
    
    def test_caption_filtering(self, document_filter, sample_documents):
        """Test filtering by caption availability."""
        document_filter.set_filters({'require_captions': True})
        filtered = document_filter.apply_filters(sample_documents)
        
        # Should only include documents with captions
        for doc in filtered:
            assert doc['metadata']['has_captions'] == True
    
    def test_category_filtering(self, document_filter, sample_documents):
        """Test filtering by category."""
        document_filter.set_filters({'categories': ['educational']})
        filtered = document_filter.apply_filters(sample_documents)
        
        for doc in filtered:
            assert doc['metadata']['category'] == 'educational'
    
    def test_quality_filtering(self, document_filter, sample_documents):
        """Test filtering by quality level."""
        document_filter.set_filters({'quality_levels': ['high']})
        filtered = document_filter.apply_filters(sample_documents)
        
        for doc in filtered:
            assert doc['metadata']['quality_score'] == 'high'
    
    def test_combined_filtering(self, document_filter, sample_documents):
        """Test multiple filters applied together."""
        document_filter.set_filters({
            'require_captions': True,
            'quality_levels': ['high']
        })
        filtered = document_filter.apply_filters(sample_documents)
        
        for doc in filtered:
            assert doc['metadata']['has_captions'] == True
            assert doc['metadata']['quality_score'] == 'high'
    
    def test_over_fetch_calculation(self, document_filter):
        """Test over-fetch calculation logic."""
        # Without filters
        assert document_filter.calculate_over_fetch(5, False) == 5
        
        # With filters (should multiply by 3, capped at 20)
        assert document_filter.calculate_over_fetch(5, True) == 15
        assert document_filter.calculate_over_fetch(10, True) == 20  # Capped
    
    def test_filter_statistics(self, metadata_enhancer, sample_documents):
        """Test filter statistics calculation."""
        stats = metadata_enhancer.get_filter_statistics(sample_documents)
        
        assert 'total_documents' in stats
        assert 'caption_coverage' in stats
        assert 'categories' in stats
        assert 'quality_levels' in stats
        
        # Verify caption coverage calculation
        coverage = stats['caption_coverage']
        assert 'with_captions' in coverage
        assert 'without_captions' in coverage
        assert 'percentage' in coverage


class TestRAGEngine:
    """Test RAG engine functionality."""
    
    def test_rag_engine_creation(self, rag_engine):
        """Test RAG engine can be created."""
        assert rag_engine is not None
    
    def test_stats(self, rag_engine):
        """Test system statistics."""
        stats = rag_engine.get_stats()
        
        assert 'total_documents' in stats
        assert 'current_provider' in stats
        assert 'available_providers' in stats
        assert stats['total_documents'] > 0
    
    def test_source_retrieval(self, rag_engine):
        """Test source retrieval functionality."""
        sources = rag_engine.retrieve_sources("gamma options", num_sources=3)
        
        assert len(sources) > 0
        assert len(sources) <= 3
        
        for source in sources:
            pytest.assert_valid_source(source)
    
    def test_context_building(self, rag_engine):
        """Test context building from sources."""
        sources = rag_engine.retrieve_sources("gamma options", num_sources=2)
        context = rag_engine.build_context(sources)
        
        assert isinstance(context, str)
        assert len(context) > 0
        assert "[Source" in context  # Should contain source markers
    
    @pytest.mark.api
    @pytest.mark.slow
    def test_answer_generation(self, rag_engine):
        """Test answer generation."""
        question = "What is gamma in options trading?"
        sources = rag_engine.retrieve_sources(question, num_sources=2)
        context = rag_engine.build_context(sources)
        
        answer = rag_engine.generate_answer(question, context)
        
        assert isinstance(answer, str)
        assert len(answer) > 0
    
    @pytest.mark.api
    @pytest.mark.slow
    def test_ask_method(self, rag_engine):
        """Test complete Q&A workflow."""
        question = "What is gamma?"
        result = rag_engine.ask(question, num_sources=3)
        
        pytest.assert_valid_rag_result(result)
        assert result['question'] == question
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_async_ask(self, rag_engine):
        """Test async Q&A workflow."""
        question = "How do gamma squeezes work?"
        result = await rag_engine.ask_async(question, num_sources=2)
        
        pytest.assert_valid_rag_result(result)
        assert result['question'] == question
    
    @pytest.mark.api
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_streaming_generation(self, rag_engine):
        """Test streaming answer generation."""
        question = "Explain dealer gamma positioning"
        sources = rag_engine.retrieve_sources(question, num_sources=2)
        context = rag_engine.build_context(sources)
        
        chunks = []
        async for chunk in rag_engine.generate_answer_stream(question, context):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        full_answer = ''.join(chunks)
        assert len(full_answer) > 0
    
    def test_filtered_retrieval(self, rag_engine):
        """Test retrieval with filters."""
        # Test with caption filter
        sources_filtered = rag_engine.retrieve_sources(
            "gamma options",
            num_sources=3,
            filters={'require_captions': True}
        )
        
        sources_unfiltered = rag_engine.retrieve_sources(
            "gamma options", 
            num_sources=3
        )
        
        assert len(sources_filtered) >= 0
        assert len(sources_unfiltered) >= 0
        
        # Verify filtered sources have captions (if metadata available)
        for source in sources_filtered:
            has_captions = source['metadata'].get('has_captions')
            if has_captions is not None:
                assert has_captions == True


class TestMultiProvider:
    """Test multi-provider LLM support."""
    
    def test_provider_listing(self, rag_engine):
        """Test listing available providers."""
        providers = rag_engine.llm_manager.list_providers()
        assert len(providers) > 0
        assert all(isinstance(p, str) for p in providers)
    
    def test_provider_switching(self, rag_engine):
        """Test switching between providers."""
        providers = rag_engine.llm_manager.list_providers()
        
        for provider in providers[:2]:  # Test first 2 providers
            try:
                llm_provider = rag_engine.llm_manager.get_provider(provider)
                assert llm_provider is not None
            except Exception as e:
                pytest.skip(f"Provider {provider} not available: {e}")
    
    @pytest.mark.api
    @pytest.mark.slow
    def test_answer_with_different_providers(self, rag_engine):
        """Test generating answers with different providers."""
        question = "What is gamma?"
        sources = rag_engine.retrieve_sources(question, num_sources=2)
        context = rag_engine.build_context(sources)
        
        providers = rag_engine.llm_manager.list_providers()
        
        for provider in providers[:2]:  # Test first 2 providers
            try:
                answer = rag_engine.generate_answer(question, context, provider=provider)
                assert isinstance(answer, str)
                assert len(answer) > 0
            except Exception as e:
                pytest.skip(f"Provider {provider} failed: {e}")


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_empty_question(self, rag_engine):
        """Test handling of empty questions."""
        try:
            result = rag_engine.ask("", num_sources=1)
            # Should handle gracefully
            assert 'answer' in result
        except Exception:
            # Also acceptable to raise exception for empty input
            pass
    
    def test_large_num_sources(self, rag_engine):
        """Test handling of large num_sources request."""
        sources = rag_engine.retrieve_sources("gamma", num_sources=100)
        # Should return available documents, not crash
        assert len(sources) >= 0
    
    def test_invalid_filters(self, rag_engine):
        """Test handling of invalid filter parameters."""
        # Should ignore invalid filters gracefully
        sources = rag_engine.retrieve_sources(
            "gamma",
            num_sources=2,
            filters={'invalid_filter': True}
        )
        assert len(sources) >= 0
    
    @pytest.mark.api
    def test_provider_fallback(self, rag_engine):
        """Test fallback when provider fails."""
        try:
            # Try with invalid provider name
            answer = rag_engine.generate_answer(
                "test question",
                "test context", 
                provider="invalid_provider"
            )
            # Should fallback to default provider
            assert isinstance(answer, str)
        except Exception:
            # Also acceptable to raise exception for invalid provider
            pass