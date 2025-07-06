#!/usr/bin/env python3
"""
Test chain functionality.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import unittest
import tempfile
import shutil
import consts
from config import Config
from chain_base import ChainParameters
from callback import CallbackHandler

class TestChains(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment."""
        self.config = Config(consts.CONFIG_PATH)
    
    def test_chain_parameters_initialization(self):
        """Test ChainParameters initialization and defaults."""
        # Test with empty overrides
        params = ChainParameters(self.config, {})
        
        self.assertEqual(params.llm, self.config.llm())
        self.assertEqual(params.llm_temperature, self.config.llm_temperature())
        self.assertEqual(params.document_count, self.config.document_count())
        
    def test_chain_parameters_overrides(self):
        """Test that overrides work properly."""
        overrides = {
            "llm": "openai",
            "openai_model": "gpt-4",
            "llm_temperature": "0.5",
            "document_count": "10",
            "search_type": "mmr",
            "custom_prompts": "true"
        }
        
        params = ChainParameters(self.config, overrides)
        
        self.assertEqual(params.llm, "openai")
        self.assertEqual(params.openai_model, "gpt-4")
        self.assertEqual(params.llm_temperature, 0.5)
        self.assertEqual(params.document_count, 10)
        self.assertEqual(params.search_type, "mmr")
        self.assertTrue(params.custom_prompts)
        
    def test_chain_parameters_to_dict(self):
        """Test parameter serialization."""
        overrides = {
            "llm": "openai",
            "document_count": "5"
        }
        
        params = ChainParameters(self.config, overrides)
        param_dict = params.to_dict()
        
        self.assertIn("llm", param_dict)
        self.assertIn("llm_model", param_dict)
        self.assertIn("document_count", param_dict)
        self.assertEqual(param_dict["llm"], "openai")
        self.assertEqual(param_dict["document_count"], 5)
    
    def test_callback_handler(self):
        """Test callback handler functionality."""
        question = "Test question"
        params = ChainParameters(self.config, {})
        params.question = question
        
        callback = CallbackHandler(question, params)
        
        # Test initialization
        self.assertEqual(callback.question, question)
        self.assertIsNotNone(callback.started_at)
        
        # Test setting sources
        sources = [
            {"id": "vid1", "title": "Test Video", "url": "https://youtube.com/watch?v=vid1"}
        ]
        callback.set_sources(sources)
        
        # Test to_dict
        result = callback.to_dict()
        self.assertIn("question", result)
        self.assertIn("sources", result) 
        self.assertIn("parameters", result)
        self.assertEqual(result["question"], question)
        self.assertEqual(len(result["sources"]), 1)
    
    def test_llm_model_selection(self):
        """Test LLM model selection based on provider."""
        # Test OpenAI
        params_openai = ChainParameters(self.config, {
            "llm": "openai",
            "openai_model": "o3-2025-04-16"
        })
        self.assertEqual(params_openai.llm_model(), "o3-2025-04-16")
        
        # Test Ollama
        params_ollama = ChainParameters(self.config, {
            "llm": "ollama",
            "ollama_model": "llama2"
        })
        self.assertEqual(params_ollama.llm_model(), "llama2")
    
    def test_utils_is_true(self):
        """Test the is_true utility function behavior."""
        params_true = ChainParameters(self.config, {
            "custom_prompts": "true",
            "return_sources": "1"
        })
        self.assertTrue(params_true.custom_prompts)
        self.assertTrue(params_true.return_sources)
        
        params_false = ChainParameters(self.config, {
            "custom_prompts": "false",
            "return_sources": "0"
        })
        self.assertFalse(params_false.custom_prompts)
        self.assertFalse(params_false.return_sources)
    
    def test_score_threshold(self):
        """Test score threshold parameter."""
        params = ChainParameters(self.config, {
            "search_type": "similarity_score_threshold",
            "score_threshold": "0.7"
        })
        
        self.assertEqual(params.search_type, "similarity_score_threshold")
        self.assertEqual(params.score_threshold, 0.7)
        self.assertIsInstance(params.score_threshold, float)
    
    def test_chain_type_variations(self):
        """Test different chain type configurations."""
        chain_types = ["base", "base_with_sources", "conversation"]
        
        for chain_type in chain_types:
            params = ChainParameters(self.config, {
                "chain_type": chain_type
            })
            self.assertEqual(params.chain_type, chain_type)

if __name__ == '__main__':
    unittest.main()