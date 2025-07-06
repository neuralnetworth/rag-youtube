#!/usr/bin/env python3
"""
Test AgentQA functionality.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import tempfile
import shutil
import json
import consts
from config import Config
from agent_qa_faiss import AgentQA
from chain_base import ChainParameters
from vector_store_faiss import FAISSVectorStore

class TestAgentQA(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        self.config = Config(consts.CONFIG_PATH)
        self.temp_dir = tempfile.mkdtemp()
        
        # Override db directory for tests
        self.original_db_dir = self.config.db_persist_directory()
        self.config.config['General']['db_persist_directory'] = self.temp_dir
        
        # Create test vector store with sample data
        self.setup_test_data()
        
    def tearDown(self):
        """Clean up test environment."""
        # Restore original config
        self.config.config['General']['db_persist_directory'] = self.original_db_dir
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def setup_test_data(self):
        """Add test documents to vector store."""
        store = FAISSVectorStore(self.config, persist_directory=self.temp_dir)
        
        texts = [
            "Gamma is the rate of change of an option's delta. When gamma is high, delta can change rapidly.",
            "A gamma squeeze occurs when market makers must buy shares to hedge their positions, driving prices higher.",
            "0DTE options expire the same day they are traded. They have high gamma risk.",
            "SpotGamma provides analytics on options flows and gamma exposure in the market.",
            "Volatility tends to increase when markets fall due to the leverage effect and fear.",
        ]
        
        metadatas = [
            {"source": "vid1", "title": "Understanding Gamma", "url": "https://youtube.com/watch?v=vid1"},
            {"source": "vid2", "title": "Gamma Squeezes Explained", "url": "https://youtube.com/watch?v=vid2"},
            {"source": "vid3", "title": "0DTE Trading", "url": "https://youtube.com/watch?v=vid3"},
            {"source": "vid4", "title": "SpotGamma Introduction", "url": "https://youtube.com/watch?v=vid4"},
            {"source": "vid5", "title": "Market Volatility", "url": "https://youtube.com/watch?v=vid5"},
        ]
        
        store.add_texts(texts, metadatas=metadatas)
    
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = AgentQA(self.config)
        self.assertIsNotNone(agent.vectorstore)
        self.assertIsNotNone(agent.database)
    
    def test_basic_query(self):
        """Test basic question answering."""
        agent = AgentQA(self.config)
        
        overrides = {
            "chain": "qa_sources",
            "document_count": "3",
            "search_type": "similarity"
        }
        parameters = ChainParameters(self.config, overrides)
        parameters.question = "What is gamma in options?"
        parameters.llm_retriever_compression = False
        parameters.llm_retriever_multiquery = False
        parameters.memory = None
        parameters.memory_window_size = 5
        
        result = agent.ask(parameters)
        
        self.assertIn("answer", result)
        self.assertIn("sources", result)
        self.assertIsNotNone(result["answer"])
        self.assertIn("gamma", result["answer"].lower())
    
    def test_sources_retrieval(self):
        """Test that sources are properly retrieved."""
        agent = AgentQA(self.config)
        
        overrides = {
            "chain": "qa_sources",
            "document_count": "2",
            "search_type": "similarity"
        }
        parameters = ChainParameters(self.config, overrides)
        parameters.question = "Tell me about gamma squeezes"
        parameters.llm_retriever_compression = False
        parameters.llm_retriever_multiquery = False
        parameters.memory = None
        parameters.memory_window_size = 5
        
        result = agent.ask(parameters)
        
        self.assertIn("sources", result)
        self.assertIsInstance(result["sources"], list)
        self.assertGreater(len(result["sources"]), 0)
        
        # Check source structure
        source = result["sources"][0]
        self.assertIn("title", source)
        self.assertIn("url", source)
        self.assertIn("youtube.com", source["url"])
    
    def test_different_search_types(self):
        """Test different search types."""
        agent = AgentQA(self.config)
        
        # Test similarity search
        overrides = {
            "chain": "qa_sources",
            "document_count": "2",
            "search_type": "similarity"
        }
        params_similarity = ChainParameters(self.config, overrides)
        params_similarity.question = "What are 0DTE options?"
        
        result_sim = agent.ask(params_similarity)
        self.assertIn("0dte", result_sim["answer"].lower())
        
        # Test MMR search
        overrides = {
            "chain": "qa_sources", 
            "document_count": "2",
            "search_type": "mmr"
        }
        params_mmr = ChainParameters(self.config, overrides)
        params_mmr.question = "What are 0DTE options?"
        
        result_mmr = agent.ask(params_mmr)
        self.assertIn("answer", result_mmr)
    
    def test_memory_types(self):
        """Test different memory configurations."""
        agent = AgentQA(self.config)
        
        # Test with buffer memory
        overrides = {
            "chain": "qa_basic",
            "memory": "buffer",
            "document_count": "2"
        }
        params = ChainParameters(self.config, overrides)
        params.question = "What is SpotGamma?"
        
        result = agent.ask(params)
        self.assertIn("spotgamma", result["answer"].lower())
        
        # Test conversation continuation
        overrides = {
            "chain": "qa_basic",
            "memory": "buffer",
            "document_count": "2"
        }
        params2 = ChainParameters(self.config, overrides)
        params2.question = "What do they analyze?"
        
        result2 = agent.ask(params2)
        self.assertIn("answer", result2)
    
    def test_empty_results(self):
        """Test handling of queries with no good matches."""
        agent = AgentQA(self.config)
        
        overrides = {
            "chain": "qa_sources",
            "document_count": "2",
            "search_type": "similarity"
        }
        parameters = ChainParameters(self.config, overrides)
        parameters.question = "Tell me about quantum computing"
        
        result = agent.ask(parameters)
        self.assertIn("answer", result)
        # Should still return an answer, even if not very relevant
    
    def test_parameter_overrides(self):
        """Test that parameter overrides work correctly."""
        agent = AgentQA(self.config)
        
        # Test with custom temperature
        overrides = {
            "chain": "qa_sources",
            "document_count": "1",
            "llm_temperature": "0.0"
        }
        params = ChainParameters(self.config, overrides)
        params.question = "Explain volatility"
        
        result = agent.ask(params)
        self.assertIn("answer", result)
        self.assertEqual(params.llm_temperature, 0.0)
    
    def test_conversational_chain(self):
        """Test conversational chain with memory."""
        agent = AgentQA(self.config)
        
        # First question
        overrides = {
            "chain": "qa_conversational",
            "memory": "buffer",
            "document_count": "2"
        }
        params1 = ChainParameters(self.config, overrides)
        params1.question = "What is gamma?"
        
        result1 = agent.ask(params1)
        self.assertIn("gamma", result1["answer"].lower())
        
        # Follow-up question
        overrides = {
            "chain": "qa_conversational",
            "memory": "buffer",
            "document_count": "2"
        }
        params2 = ChainParameters(self.config, overrides)
        params2.question = "How does it relate to squeezes?"
        
        result2 = agent.ask(params2)
        self.assertIn("answer", result2)

if __name__ == '__main__':
    unittest.main()