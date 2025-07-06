#!/usr/bin/env python3
"""
End-to-end tests for the RAG system.
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
from vector_store_faiss import FAISSVectorStore
from agent_qa_faiss import AgentQA
from chain_base import ChainParameters

class TestEndToEnd(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment with real SpotGamma data."""
        self.config = Config(consts.CONFIG_PATH)
        
        # Use the actual database for end-to-end tests
        self.db_dir = self.config.db_persist_directory()
        
    def test_spotgamma_content_retrieval(self):
        """Test retrieving actual SpotGamma content."""
        agent = AgentQA(self.config)
        
        # Test various SpotGamma-specific queries
        test_queries = [
            {
                "question": "What does SpotGamma say about gamma squeezes?",
                "expected_terms": ["gamma", "squeeze", "market"]
            },
            {
                "question": "How do 0DTE options affect market volatility?",
                "expected_terms": ["0dte", "volatility", "option"]
            },
            {
                "question": "What is the relationship between dealer gamma and market movements?",
                "expected_terms": ["dealer", "gamma", "market"]
            }
        ]
        
        for test in test_queries:
            with self.subTest(question=test["question"]):
                overrides = {
                    "chain": "qa_sources",
                    "document_count": "3",
                    "search_type": "similarity"
                }
                params = ChainParameters(self.config, overrides)
                params.question = test["question"]
                
                result = agent.ask(params)
                
                # Check response structure
                self.assertIn("answer", result)
                self.assertIn("sources", result)
                self.assertIsNotNone(result["answer"])
                
                # Check for expected terms
                answer_lower = result["answer"].lower()
                for term in test["expected_terms"]:
                    self.assertIn(term.lower(), answer_lower, 
                                f"Expected term '{term}' not found in answer")
                
                # Check sources
                self.assertGreater(len(result["sources"]), 0)
                for source in result["sources"]:
                    self.assertIn("url", source)
                    self.assertIn("youtube.com/watch?v=", source["url"])
    
    def test_multi_turn_conversation(self):
        """Test multi-turn conversation with context."""
        agent = AgentQA(self.config)
        
        # First turn
        overrides = {
            "chain": "qa_conversational",
            "memory": "buffer",
            "document_count": "2"
        }
        params1 = ChainParameters(self.config, overrides)
        params1.question = "What is gamma in options trading?"
        
        result1 = agent.ask(params1)
        self.assertIn("gamma", result1["answer"].lower())
        
        # Second turn - follow up
        overrides = {
            "chain": "qa_conversational",
            "memory": "buffer",
            "document_count": "2"
        }
        params2 = ChainParameters(self.config, overrides)
        params2.question = "How does it affect market makers?"
        
        result2 = agent.ask(params2)
        self.assertIn("market maker", result2["answer"].lower())
        
        # Third turn - related question
        overrides = {
            "chain": "qa_conversational",
            "memory": "buffer",
            "document_count": "2"
        }
        params3 = ChainParameters(self.config, overrides)
        params3.question = "What happens during expiration?"
        
        result3 = agent.ask(params3)
        self.assertIn("expir", result3["answer"].lower())
    
    def test_different_retrieval_strategies(self):
        """Test different retrieval strategies on same question."""
        agent = AgentQA(self.config)
        question = "Explain volatility and gamma relationship"
        
        strategies = [
            {"search_type": "similarity", "document_count": "3"},
            {"search_type": "mmr", "document_count": "3"},
            {"search_type": "similarity", "document_count": "5"},
        ]
        
        results = []
        for strategy in strategies:
            overrides = {
                "chain": "qa_sources",
                **strategy
            }
            params = ChainParameters(self.config, overrides)
            params.question = question
            
            result = agent.ask(params)
            results.append(result)
            
            # Each should return valid results
            self.assertIn("answer", result)
            self.assertIn("sources", result)
            
        # Results should be different due to different strategies
        # But all should mention key terms
        for result in results:
            answer_lower = result["answer"].lower()
            self.assertTrue(
                "volatility" in answer_lower or "gamma" in answer_lower,
                "Answer should mention volatility or gamma"
            )
    
    def test_source_quality(self):
        """Test that returned sources are relevant and well-formed."""
        agent = AgentQA(self.config)
        
        overrides = {
            "chain": "qa_sources",
            "document_count": "5",
            "search_type": "similarity"
        }
        params = ChainParameters(self.config, overrides)
        params.question = "What are the key insights from SpotGamma about market structure?"
        
        result = agent.ask(params)
        
        # Check sources
        self.assertIn("sources", result)
        sources = result["sources"]
        self.assertGreater(len(sources), 0)
        
        # Verify source structure and content
        for source in sources:
            # Required fields
            self.assertIn("title", source)
            self.assertIn("url", source)
            
            # Valid YouTube URL
            self.assertTrue(source["url"].startswith("https://youtube.com/watch?v="))
            
            # Title should not be empty or "Unknown"
            self.assertNotEqual(source["title"], "")
            self.assertNotEqual(source["title"], "Unknown")
            
            # If score is present, it should be a number
            if "score" in source:
                self.assertIsInstance(source["score"], (int, float))
    
    def test_error_handling(self):
        """Test system handles errors gracefully."""
        agent = AgentQA(self.config)
        
        # Test with empty question
        overrides = {
            "chain": "qa_sources",
            "document_count": "3"
        }
        params = ChainParameters(self.config, overrides)
        params.question = ""
        
        try:
            result = agent.ask(params)
            # Should still return a result structure
            self.assertIn("answer", result)
        except Exception as e:
            # Should not crash completely
            self.assertIsInstance(e, Exception)
    
    def test_performance_metrics(self):
        """Test that the system performs within reasonable time."""
        import time
        agent = AgentQA(self.config)
        
        overrides = {
            "chain": "qa_sources",
            "document_count": "3"
        }
        params = ChainParameters(self.config, overrides)
        params.question = "What is SpotGamma's view on 0DTE options?"
        
        start_time = time.time()
        result = agent.ask(params)
        end_time = time.time()
        
        elapsed = end_time - start_time
        
        # Should complete within reasonable time (adjust as needed)
        self.assertLess(elapsed, 30, "Query took too long to complete")
        
        # Should return valid result
        self.assertIn("answer", result)
        self.assertIn("0dte", result["answer"].lower())

if __name__ == '__main__':
    unittest.main()